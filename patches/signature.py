"""
Patch: Remove APK signature verification.

Many apps verify their own signature at runtime (anti-tamper).
This patch neutralizes those checks.

Strategy:
  - Override signature comparison methods to always match
  - Neutralize PackageManager.getPackageInfo signature flags
"""
from __future__ import annotations

import re
from pathlib import Path

from utils.smali import find_all_smali_files


def apply(decompiled_dir: Path) -> dict:
    """
    Remove/bypass signature verification.
    Returns {"files_changed": int, "description": str}.
    """
    changed = 0
    smali_files = find_all_smali_files(decompiled_dir)

    sig_patterns = [
        # Method that checks signatures - make it always return true
        (
            re.compile(
                r'(\.method.*checkSignature.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL,
            ),
            r'\1    const/4 v0, 0x1\n    return v0\n',
        ),
        (
            re.compile(
                r'(\.method.*verifySignature.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL,
            ),
            r'\1    const/4 v0, 0x1\n    return v0\n',
        ),
        (
            re.compile(
                r'(\.method.*isValidSignature.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL,
            ),
            r'\1    const/4 v0, 0x1\n    return v0\n',
        ),
        (
            re.compile(
                r'(\.method.*isSignatureValid.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL,
            ),
            r'\1    const/4 v0, 0x1\n    return v0\n',
        ),
        # Neutralize GET_SIGNING_CERTIFICATES flag (API 28+)
        (
            re.compile(r'const/(?:16|32)\s+v\d+,\s*0x(800|1080)0000\s*#.*GET_SIGNING'),
            "const/4 v0, 0x0  # signature flag cleared",
        ),
        # Neutralize comparison of signing info
        (
            re.compile(r'invoke.*MessageDigest.*->isEqual\(.*'),
            "const/4 v0, 0x1\n    return v0  # sig check bypassed",
        ),
    ]

    for sf in smali_files:
        try:
            content = sf.read_text(errors="replace")
            original = content

            for pattern, replacement in sig_patterns:
                content = pattern.sub(replacement, content)

            if content != original:
                sf.write_text(content)
                changed += 1
        except OSError:
            continue

    return {
        "files_changed": changed,
        "description": f"Signature verification bypassed in {changed} file(s)",
    }
