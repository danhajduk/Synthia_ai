from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import subprocess
import sys
import shutil


class SetupResult:
    def __init__(self, success: bool, message: str | None = None) -> None:
        self.success = success
        self.message = message


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return p.returncode, p.stdout


def _pip_install_requirements(req_file: Path) -> tuple[bool, str]:
    if not req_file.exists():
        return True, f"{req_file.name} not present, skipping."

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "-r",
        str(req_file),
    ]
    code, out = _run(cmd, cwd=req_file.parent)
    return (code == 0), out


def _ensure_runtime_dirs(addon_dir: Path) -> None:
    runtime = addon_dir / "runtime"
    for sub in ["weather", "avatar", "gen", "published", "meta", "tmp"]:
        (runtime / sub).mkdir(parents=True, exist_ok=True)


def run_setup(addon_id: str, addon_dir: Path, config: Dict[str, Any]) -> SetupResult:
    print(f"[{addon_id}] setup called in {addon_dir}, config={config}")
    print(f"[{addon_id}] python = {sys.executable}")

    # Ensure pip exists
    if shutil.which("pip") is None:
        code, out = _run([sys.executable, "-m", "pip", "--version"])
        if code != 0:
            return SetupResult(False, f"pip not available:\n{out}")

    _ensure_runtime_dirs(addon_dir)

    req_dir = addon_dir / "requirements"

    steps = [
        req_dir / "base.txt",
    ]

    if config.get("enable_diffusion"):
        steps.append(req_dir / "diffusion.txt")

    if config.get("enable_upscale"):
        steps.append(req_dir / "upscale.txt")

    logs: list[str] = []

    for req in steps:
        ok, out = _pip_install_requirements(req)
        logs.append(f"--- {req.name} ---\n{out}")
        if not ok:
            return SetupResult(
                False,
                f"Failed installing {req.name}\n\n{out}",
            )

    # Sanity check (base deps)
    try:
        import PIL  # noqa
    except Exception as e:
        return SetupResult(False, f"Pillow import failed: {e}")

    return SetupResult(
        True,
        "setup ok\n"
        + "\n".join(logs)
    )
