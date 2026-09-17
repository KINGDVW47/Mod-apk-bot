"""
Patch: Remove root detection mechanisms.

Common libraries targeted:
  - RootBeer (com.scottyab.rootbeer)
  - RootDetection (various)
  - SafetyNet attestation bypass
  - Common root check patterns (su binary, root management apps)

Strategy:
  - Neutralize root-check methods to always return false / safe
"""
from __future__ import annotations

import re
from pathlib import Path

from utils.smali import find_all_smali_files


def apply(decompiled_dir: Path) -> dict:
    """
    Remove/bypass root detection.
    Returns {"files_changed": int, "description": str}.
    """
    changed = 0
    smali_files = find_all_smali_files(decompiled_dir)

    # Root detection patterns and their replacements
    root_patterns = [
        # RootBeer library - isRooted always returns false
        (
            re.compile(
                r'(\.method.*isRooted.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL,
            ),
            r'\1    const/4 v0, 0x0\n    return v0\n',
        ),
        # Common root check: Runtime.exec("su")
        (
            re.compile(r'invoke.*Runtime.*->exec\(.*"su".*\)'),
            "nop  # root check removed",
        ),
        # Check for su binary
        (
            re.compile(r'invoke.*File.*->exists\(\).*#.*su'),
            "nop  # su check removed",
        ),
        # SafetyNet / Play Integrity
        (
            re.compile(r'invoke.*SafetyNet.*->attest.*'),
            "nop  # SafetyNet removed",
        ),
        (
            re.compile(r'invoke.*PlayIntegrity.*->requestIntegrity.*'),
            "nop  # Play Integrity removed",
        ),
        # Root management app checks (SuperSU, Magisk, etc.)
        (
            re.compile(r'invoke.*PackageManager.*->getPackageInfo\(.*"com\.noshufou\.android\.su".*\)'),
            "goto :root_safe\n",
        ),
        (
            re.compile(r'invoke.*PackageManager.*->getPackageInfo\(.*"eu\.chainfire\.supersu".*\)'),
            "goto :root_safe\n",
        ),
        (
            re.compile(r'invoke.*PackageManager.*->getPackageInfo\(.*"com\.topjohnwu\.magisk".*\)'),
            "goto :root_safe\n",
        ),
        # Generic "isDeviceRooted" method
        (
            re.compile(
                r'(\.method.*isDeviceRooted.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL,
            ),
            r'\1    const/4 v0, 0x0\n    return v0\n',
        ),
        # Generic "checkRoot" method
        (
            re.compile(
                r'(\.method.*checkRoot.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL,
            ),
            r'\1    const/4 v0, 0x0\n    return v0\n',
        ),
    ]

    for sf in smali_files:
        try:
            content = sf.read_text(errors="replace")
            original = content

            for pattern, replacement in root_patterns:
                content = pattern.sub(replacement, content)

            if content != original:
                sf.write_text(content)
                changed += 1
        except OSError:
            continue

    return {
        "files_changed": changed,
        "description": f"Root detection neutralized in {changed} file(s)",
    }
