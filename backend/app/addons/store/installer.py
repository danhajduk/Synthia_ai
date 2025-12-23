from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from ..models import AddonManifest, AddonInstallResult, AddonSetupResult


def _run(cmd: list[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def _looks_like_commit(ref: str) -> bool:
    r = ref.strip()
    return len(r) in (7, 8, 40) and all(c in "0123456789abcdef" for c in r.lower())


def _git_clone(repo: str, ref: str, dest: Path) -> Tuple[bool, str]:
    """
    Clone repo into dest. Supports branch/tag OR commit-ish.
    Returns (ok, error_message).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if _looks_like_commit(ref):
        # Clone default branch shallow, then checkout commit
        cp = _run(["git", "clone", "--depth", "1", repo, str(dest)])
        if cp.returncode != 0:
            return False, cp.stderr.strip() or cp.stdout.strip() or "git clone failed"

        cp2 = _run(["git", "checkout", ref], cwd=dest)
        if cp2.returncode != 0:
            return False, cp2.stderr.strip() or cp2.stdout.strip() or "git checkout failed"

        return True, ""

    # branch/tag
    cp = _run(["git", "clone", "--depth", "1", "--branch", ref, "--single-branch", repo, str(dest)])
    if cp.returncode != 0:
        # Fall back to clone then checkout (covers some tag edge cases)
        cp2 = _run(["git", "clone", "--depth", "1", repo, str(dest)])
        if cp2.returncode != 0:
            return False, cp2.stderr.strip() or cp2.stdout.strip() or "git clone failed"
        cp3 = _run(["git", "checkout", ref], cwd=dest)
        if cp3.returncode != 0:
            return False, cp3.stderr.strip() or cp3.stdout.strip() or "git checkout failed"

    return True, ""


def _read_manifest(addon_root: Path) -> AddonManifest:
    manifest_path = addon_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found at {manifest_path}")

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    return AddonManifest.parse_obj(raw)


def _run_setup(addon_root: Path, manifest: AddonManifest) -> AddonSetupResult:
    if not manifest.backend or not manifest.backend.setup:
        return AddonSetupResult(success=True, exit_code=0, stdout="", stderr="")

    setup_rel = manifest.backend.setup
    setup_path = (addon_root / setup_rel).resolve()

    if not setup_path.exists():
        return AddonSetupResult(
            success=False,
            exit_code=127,
            stdout="",
            stderr=f"setup script not found: {setup_rel}",
        )

    # Run setup in isolated subprocess
    cp = _run(["python", str(setup_path)], cwd=addon_root)
    return AddonSetupResult(
        success=(cp.returncode == 0),
        exit_code=cp.returncode,
        stdout=cp.stdout or "",
        stderr=cp.stderr or "",
    )


def install_addon_from_repo(
    *,
    addon_id: str,
    repo: str,
    ref: str,
    path_in_repo: str,
    core_root: Path,
    force: bool = False,
) -> AddonInstallResult:
    """
    Installs addon repo into data/addons/<id> and symlinks into core /addons/<id>.
    Does NOT hot-load backend routes yet; returns warnings for restart/sync.
    """

    data_dir = core_root / "data" / "addons"
    target_dir = data_dir / addon_id
    link_dir = core_root / "addons" / addon_id

    errors: list[str] = []
    warnings: list[str] = []

    # Ensure base dirs exist
    data_dir.mkdir(parents=True, exist_ok=True)
    (core_root / "addons").mkdir(parents=True, exist_ok=True)

    # Handle existing install
    if target_dir.exists():
        if not force:
            return AddonInstallResult(status="failed", errors=[f"Addon already installed at {target_dir} (use force=true)"])
        shutil.rmtree(target_dir)

    # Clone to temp, then move into place
    tmp_base = Path(tempfile.mkdtemp(prefix=f"synthia-install-{addon_id}-"))
    repo_dir = tmp_base / "repo"

    ok, err = _git_clone(repo, ref, repo_dir)
    if not ok:
        shutil.rmtree(tmp_base, ignore_errors=True)
        return AddonInstallResult(status="failed", errors=[err])

    addon_root = (repo_dir / path_in_repo).resolve()
    if not addon_root.exists():
        shutil.rmtree(tmp_base, ignore_errors=True)
        return AddonInstallResult(status="failed", errors=[f"Addon path not found in repo: {path_in_repo}"])

    # Copy addon into data/addons/<id>
    shutil.copytree(addon_root, target_dir)

    # Read manifest from installed location (truth after install)
    try:
        manifest = _read_manifest(target_dir)
    except Exception as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        shutil.rmtree(tmp_base, ignore_errors=True)
        return AddonInstallResult(status="failed", errors=[str(e)])

    # Run setup if present
    setup_result = _run_setup(target_dir, manifest)
    if not setup_result.success:
        # rollback install on setup failure
        errors.append("Addon setup failed")
        if setup_result.stderr:
            errors.append(setup_result.stderr.strip())
        shutil.rmtree(target_dir, ignore_errors=True)
        shutil.rmtree(tmp_base, ignore_errors=True)
        return AddonInstallResult(status="failed", manifest=manifest, errors=errors)

    # Ensure symlink exists: core/addons/<id> -> data/addons/<id>
    try:
        if link_dir.exists() or link_dir.is_symlink():
            link_dir.unlink()
        os.symlink(str(target_dir), str(link_dir))
    except Exception as e:
        # Not fatal, but loader might not see it yet
        warnings.append(f"Could not create symlink {link_dir} -> {target_dir}: {e}")

    # Cleanup temp
    shutil.rmtree(tmp_base, ignore_errors=True)

    # Warnings for current architecture
    warnings.append("Backend routes are loaded on startup; restart Synthia to activate this addon backend (for now).")
    warnings.append("Frontend addon UI sync may be required (depending on your build flow).")

    return AddonInstallResult(status="installed", manifest=manifest, warnings=warnings)
