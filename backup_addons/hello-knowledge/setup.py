
from pydantic import BaseModel
from pathlib import Path
from typing import Any, Dict


class AddonSetupContext(BaseModel):
  addon_id: str
  addon_dir: Path
  config: Dict[str, Any]


class AddonSetupResult(BaseModel):
  success: bool
  message: str | None = None


def run_setup(ctx: AddonSetupContext) -> AddonSetupResult:
  # For now, just pretend everything is fine.
  # Later you can:
  # - validate ctx.config (e.g. required API keys)
  # - create DB tables
  # - ping external services, etc.
  return AddonSetupResult(success=True, message="Hello Knowledge setup OK")
