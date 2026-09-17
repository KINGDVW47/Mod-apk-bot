"""
Per-user conversation state manager backed by JSON files.

Each user gets a state file:  states/<user_id>.json

State schema:
{
    "step":          "idle" | "waiting_apk" | "menu" | "renaming" | ...
    "apk_path":      "/path/to/original.apk",
    "work_dir":      "/path/to/decompiled/",
    "app_name":      "new display name or null",
    "email":         "user@example.com or null",
    "phone":         "+1234567890 or null",
    "patches": {
        "remove_license":     false,
        "remove_ads":         false,
        "remove_root_detect": false,
        "remove_signature":   false,
        "inject_toast":       false,
        "server_bypass":      false
    },
    "report": []
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import STATES_DIR

# Default fresh state
_DEFAULT: dict[str, Any] = {
    "step": "idle",
    "apk_path": None,
    "work_dir": None,
    "app_name": None,
    "email": None,
    "phone": None,
    "patches": {
        "remove_license": False,
        "remove_ads": False,
        "remove_root_detect": False,
        "remove_signature": False,
        "inject_toast": False,
        "server_bypass": False,
    },
    "report": [],
}


def _path(user_id: int) -> Path:
    return STATES_DIR / f"{user_id}.json"


def load(user_id: int) -> dict[str, Any]:
    """Load state for *user_id*, returning a fresh state if none exists."""
    p = _path(user_id)
    if p.exists():
        try:
            with open(p) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return json.loads(json.dumps(_DEFAULT))  # deep copy


def save(user_id: int, state: dict[str, Any]) -> None:
    """Persist state to disk."""
    p = _path(user_id)
    with open(p, "w") as f:
        json.dump(state, f, indent=2)


def reset(user_id: int) -> dict[str, Any]:
    """Reset state back to defaults and return it."""
    fresh = json.loads(json.dumps(_DEFAULT))
    save(user_id, fresh)
    return fresh
