from __future__ import annotations

import importlib.util
import logging
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .models import AddonManifest, AddonSetupResult
from .registry import DEFAULT_ADDONS_DIR

logger = logging.getLogger(__name__)


def _get_addon_dir(manifest: AddonManifest) -> Path:
    """
    Resolve the root directory for this addon on disk.

    For now, we derive it directly from DEFAULT_ADDONS_DIR / manifest.id.
    """
    return DEFAULT_ADDONS_DIR / manifest.id


# ----------------------------
# Setup caching helpers
# ----------------------------

def _requirements_hash(addon_dir: Path) -> str:
    """
    Hash all requirements/*.txt files so we can detect changes and re-run setup only when needed.
    """
    req_dir = addon_dir / "requirements"
    if not req_dir.exists():
        return "no-requirements-dir"

    h = hashlib.sha256()

    # Hash file names + contents (stable ordering)
    files = sorted(req_dir.glob("*.txt"), key=lambda p: p.name)
    if not files:
        return "no-requirements-files"

    for p in files:
        h.update(p.name.encode("utf-8"))
        h.update(b"\n")
        h.update(p.read_bytes())
        h.update(b"\n")

    return h.hexdigest()


def _setup_stamp_path(addon_dir: Path) -> Path:
    """
    Store setup marker inside addon-local runtime.
    """
    return addon_dir / "runtime" / "meta" / "setup.stamp"


def _read_setup_stamp(addon_dir: Path) -> Dict[str, Any]:
    p = _setup_stamp_path(addon_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _write_setup_stamp(addon_dir: Path, payload: Dict[str, Any]) -> None:
    p = _setup_stamp_path(addon_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2))


def run_addon_setup(
    manifest: AddonManifest,
    *,
    timeout: int = 300,  # kept for signature compatibility; unused for now
    config: Optional[Dict[str, Any]] = None,
    force: bool = False,
) -> Optional[AddonSetupResult]:
    """
    Run the optional backend setup hook for an addon, if configured.

    Behavior:
    - If no backend/setup is configured: returns None
    - Otherwise:
      - Checks requirements hash + setup stamp and skips if already satisfied (unless force=True)
      - Dynamically imports the setup module from manifest.backend.setup
      - Calls run_setup(addon_id: str, addon_dir: Path, config: Dict[str, Any]) in-process
      - Interprets return value:
          * If it has attribute `.success` (bool) → use that
          * If it has attribute `.message` (str) → put into stdout on success, stderr on failure
          * If it returns None → treat as success

    Returns:
      - AddonSetupResult if setup is configured
      - None if no setup script is configured
    """
    backend = manifest.backend
    if backend is None or backend.setup is None:
        logger.info("No setup defined for addon '%s'; skipping.", manifest.id)
        return None

    addon_dir = _get_addon_dir(manifest)
    cfg = config or {}

    # Setup caching (skip if requirements unchanged and last setup succeeded)
    req_hash = _requirements_hash(addon_dir)
    stamp = _read_setup_stamp(addon_dir)

    if not force and stamp.get("success") is True and stamp.get("requirements_hash") == req_hash:
        logger.info(
            "Setup already satisfied for addon '%s' (requirements unchanged); skipping.",
            manifest.id,
        )
        return AddonSetupResult(
            success=True,
            exit_code=0,
            stdout="setup skipped (cached)",
            stderr="",
        )

    script_path = (addon_dir / backend.setup).resolve()

    logger.info(
        "Preparing to run setup for addon '%s' from %s",
        manifest.id,
        script_path,
    )

    if not script_path.is_file():
        msg = f"Setup file not found for addon '{manifest.id}': {script_path}"
        logger.warning(msg)

        _write_setup_stamp(
            addon_dir,
            {
                "success": False,
                "requirements_hash": req_hash,
                "checked_at": datetime.utcnow().isoformat(),
                "python": sys.executable,
                "error": msg,
            },
        )

        return AddonSetupResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=msg,
        )

    # Dynamically load the module
    module_name = f"synthia_addons.{manifest.id}.setup"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        msg = f"Failed to create module spec for setup of addon '{manifest.id}'"
        logger.error(msg)

        _write_setup_stamp(
            addon_dir,
            {
                "success": False,
                "requirements_hash": req_hash,
                "checked_at": datetime.utcnow().isoformat(),
                "python": sys.executable,
                "error": msg,
            },
        )

        return AddonSetupResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=msg,
        )

    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:
        msg = f"Exception while importing setup module for addon '{manifest.id}': {exc!r}"
        logger.exception(msg)

        _write_setup_stamp(
            addon_dir,
            {
                "success": False,
                "requirements_hash": req_hash,
                "checked_at": datetime.utcnow().isoformat(),
                "python": sys.executable,
                "error": msg,
            },
        )

        return AddonSetupResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=msg,
        )

    run_setup = getattr(module, "run_setup", None)
    if run_setup is None or not callable(run_setup):
        msg = (
            f"Setup module for addon '{manifest.id}' has no callable 'run_setup'; "
            f"skipping setup."
        )
        logger.warning(msg)

        _write_setup_stamp(
            addon_dir,
            {
                "success": False,
                "requirements_hash": req_hash,
                "checked_at": datetime.utcnow().isoformat(),
                "python": sys.executable,
                "error": msg,
            },
        )

        return AddonSetupResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=msg,
        )

    # Call the setup function with the agreed contract
    try:
        logger.info(
            "Calling run_setup(addon_id=%r, addon_dir=%r, config=%r) for addon '%s'",
            manifest.id,
            addon_dir,
            cfg,
            manifest.id,
        )

        result = run_setup(manifest.id, addon_dir, cfg)  # type: ignore[misc]

        # Interpret result
        success = True
        message: str = ""

        if result is None:
            success = True
            message = "run_setup returned None; treating as success."
        else:
            success_attr = getattr(result, "success", None)
            message_attr = getattr(result, "message", None)

            if isinstance(success_attr, bool):
                success = success_attr
            else:
                # If no explicit success flag, assume success if no exception was raised
                success = True

            if isinstance(message_attr, str):
                message = message_attr

        if success:
            logger.info(
                "Setup for addon '%s' completed successfully: %s",
                manifest.id,
                message,
            )

            _write_setup_stamp(
                addon_dir,
                {
                    "success": True,
                    "requirements_hash": req_hash,
                    "checked_at": datetime.utcnow().isoformat(),
                    "python": sys.executable,
                    "message": message,
                },
            )

            return AddonSetupResult(
                success=True,
                exit_code=0,
                stdout=message or "",
                stderr="",
            )
        else:
            logger.warning(
                "Setup for addon '%s' reported failure: %s",
                manifest.id,
                message,
            )

            _write_setup_stamp(
                addon_dir,
                {
                    "success": False,
                    "requirements_hash": req_hash,
                    "checked_at": datetime.utcnow().isoformat(),
                    "python": sys.executable,
                    "error": message or "Setup reported failure",
                },
            )

            return AddonSetupResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=message or "Setup reported failure",
            )

    except Exception as exc:
        msg = f"Exception while running setup for addon '{manifest.id}': {exc!r}"
        logger.exception(msg)

        _write_setup_stamp(
            addon_dir,
            {
                "success": False,
                "requirements_hash": req_hash,
                "checked_at": datetime.utcnow().isoformat(),
                "python": sys.executable,
                "error": msg,
            },
        )

        return AddonSetupResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=msg,
        )
