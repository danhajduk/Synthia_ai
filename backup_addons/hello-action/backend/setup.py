from pathlib import Path
from typing import Dict, Any


class SetupResult:
    def __init__(self, success: bool, message: str | None = None) -> None:
        self.success = success
        self.message = message


def run_setup(addon_id: str, addon_dir: Path, config: Dict[str, Any]) -> SetupResult:
    print(f"[{addon_id}] setup called in {addon_dir}, config={config}")
    return SetupResult(True, "demo setup ok")
