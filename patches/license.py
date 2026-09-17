"""
Patch: Remove Google License Verification Library (LVL) checks.

Strategy:
  - Comment out / replace license-checking method calls in smali
  - Neutralize LicenseChecker, LICENSE_RESULT, checkLicense patterns
"""
from __future__ import annotations

import re
from pathlib import Path

from utils.smali import find_all_smali_files


def apply(decompiled_dir: Path) -> dict:
    """
    Neutralize LVL license checks.
    Returns {"files_changed": int, "description": str}.
    """
    changed = 0
    smali_files = find_all_smali_files(decompiled_dir)

    # Patterns that indicate license verification
    lvl_patterns = [
        # Google Play licensing service callbacks
        (re.compile(r'invoke.*LicenseChecker.*->check.*'), "# LVL patch"),
        (re.compile(r'invoke.*LicenseCheckerCallback.*->allow.*'), "invoke-static {}, Landroid/os/Process;->myPid()I\n    return-void"),
        (re.compile(r'invoke.*LicenseCheckerCallback.*->dontAllow.*'), "invoke-static {}, Landroid/os/Process;->myPid()I\n    return-void"),
        # Common LVL response codes
        (re.compile(r'const/4\s+v\d+,\s*0x1\s*# LICENSE_RESULT_LICENSED'), "const/4 v0, 0x1"),
    ]

    for sf in smali_files:
        try:
            content = sf.read_text(errors="replace")
            original = content

            for pattern, replacement in lvl_patterns:
                if pattern.search(content):
                    content = pattern.sub(replacement, content)

            if content != original:
                sf.write_text(content)
                changed += 1
        except OSError:
            continue

    return {
        "files_changed": changed,
        "description": f"LVL license check removed from {changed} file(s)",
    }
