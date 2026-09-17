"""
Patch: Inject a Toast notification in the launcher activity's onCreate().

This is a simple visible modification to prove the APK was modded.
"""
from __future__ import annotations

from pathlib import Path

from utils.smali import find_launcher_activity_smali, inject_toast_after_super


def apply(decompiled_dir: Path, toast_text: str = "Modded by APK Bot") -> dict:
    """
    Inject Toast.makeText(this, "...", LENGTH_SHORT).show() into onCreate().
    Returns {"success": bool, "file": str, "description": str}.
    """
    smali_path = find_launcher_activity_smali(decompiled_dir)

    if smali_path is None:
        return {
            "success": False,
            "file": None,
            "description": "Could not locate launcher activity smali file",
        }

    success = inject_toast_after_super(smali_path, toast_text)

    return {
        "success": success,
        "file": str(smali_path) if smali_path else None,
        "description": (
            f"Toast injected into {smali_path.name}"
            if success
            else "Failed to inject Toast (no invoke-super found in onCreate)"
        ),
    }
