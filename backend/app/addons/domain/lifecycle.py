# backend/app/addons/lifecycle.py
from enum import Enum


class AddonLifecycleStatus(str, Enum):
    """
    High-level lifecycle status for an addon.

    - available: addon exists on disk (manifest discovered), but not installed
      into the running system yet.

    - installed: addon is registered/installed (e.g. router/front-end wires
      created), but we haven't confirmed health yet.

    - ready: addon is installed and its health check reports OK.

    - error: addon is installed but its health check reports a failure
      (or we failed to talk to it).
    """

    AVAILABLE = "available"
    INSTALLED = "installed"
    READY = "ready"
    ERROR = "error"
