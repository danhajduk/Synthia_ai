from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Tuple, Dict, Any

from fastapi import UploadFile
from pydantic import ValidationError

from ..domain.models import AddonManifest, AddonInstallResult
from .registry import reload_registry, DEFAULT_ADDONS_DIR
from .setup_runner import run_addon_setup


def _find_manifest(root: Path) -> Tuple[Path | None, Path | None]:
    """
    Try to find manifest.json in the extracted ZIP.

    Returns (manifest_path, addon_root_dir).
    - addon_root_dir is the folder that should become /addons/<id>.
    """
    # Case 1: manifest.json at root
    direct_manifest = root / "manifest.json"
    if direct_manifest.exists():
        return direct_manifest, root

    # Case 2: single top-level directory with manifest.json inside
    children = [p for p in root.iterdir() if p.is_dir()]
    if len(children) == 1:
        candidate = children[0] / "manifest.json"
        if candidate.exists():
            return candidate, children[0]

    return None, None


async def install_addon_from_zip(
    file: UploadFile,
    addons_dir: Path | None = None,
    *,
    config: Dict[str, Any] | None = None,
) -> AddonInstallResult:
    """
    Install an addon from an uploaded ZIP file.

    - Extracts to temp dir
    - Validates manifest.json
    - Moves to /addons/<id>
    - Runs addon setup (installs deps) if configured
    - Reloads registry

    Very opinionated v1: no overwrite, no uninstall, no git.
    """
    if addons_dir is None:
        addons_dir = DEFAULT_ADDONS_DIR

    addons_dir.mkdir(parents=True, exist_ok=True)
    cfg = config or {}

    # 1) Save ZIP to temp file
    tmp_dir = Path(tempfile.mkdtemp(prefix="synthia-addon-upload-"))
    tmp_zip_path = tmp_dir / "addon.zip"

    try:
        with tmp_zip_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

        # 2) Extract ZIP
        extract_dir = tmp_dir / "unpacked"
        extract_dir.mkdir()
        try:
            with zipfile.ZipFile(tmp_zip_path, "r") as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            return AddonInstallResult(
                status="failed",
                errors=["Uploaded file is not a valid ZIP archive"],
            )

        # 3) Find manifest
        manifest_path, addon_root = _find_manifest(extract_dir)
        if manifest_path is None or addon_root is None:
            return AddonInstallResult(
                status="failed",
                errors=[
                    "Could not find manifest.json in ZIP. "
                    "Expected at root or inside a single top-level folder."
                ],
            )

        # 4) Load and validate manifest
        raw = manifest_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return AddonInstallResult(
                status="failed",
                errors=[f"manifest.json is not valid JSON: {e}"],
            )

        try:
            manifest = AddonManifest.model_validate(data)
        except ValidationError as e:
            return AddonInstallResult(
                status="failed",
                errors=[f"manifest.json is invalid: {e}"],
            )

        # 5) Move addon directory into /addons/<id>
        target_dir = addons_dir / manifest.id
        if target_dir.exists():
            return AddonInstallResult(
                status="failed",
                errors=[f"Addon '{manifest.id}' already exists at {target_dir}"],
            )

        shutil.move(str(addon_root), str(target_dir))

        # Attach root_dir for manifest consumers
        manifest.root_dir = target_dir

        # 6) Run setup if configured (installs dependencies)
        # Important: run_addon_setup uses DEFAULT_ADDONS_DIR/manifest.id, which now exists.
        setup_result = run_addon_setup(manifest, config=cfg)

        if setup_result is not None and not setup_result.success:
            # Roll back install (keep system consistent)
            shutil.rmtree(target_dir, ignore_errors=True)

            return AddonInstallResult(
                status="failed",
                errors=[
                    f"Addon setup failed for '{manifest.id}' (exit_code={setup_result.exit_code}).",
                    setup_result.stderr or setup_result.stdout or "Unknown setup failure",
                ],
            )

        # 7) Reload registry after successful setup
        reload_registry(addons_dir)

        return AddonInstallResult(
            status="installed",
            manifest=manifest,
            warnings=[],
        )

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
