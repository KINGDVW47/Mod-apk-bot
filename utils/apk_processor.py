"""
Core APK processing: decompile, rebuild, zipalign, sign.
Wraps apktool, zipalign, and apksigner CLI calls.
"""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from config import KEY_ALIAS, KEYSTORE_PASS, KEYSTORE_PATH


async def _run(cmd: list[str], check: bool = True) -> asyncio.subprocess.Process:
    """Run a shell command asynchronously."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stderr: {stderr.decode(errors='replace')}"
        )
    return proc


# ------------------------------------------------------------------
# Decompile
# ------------------------------------------------------------------
async def decompile(apk_path: Path, output_dir: Path) -> Path:
    """
    Decompile APK with apktool.
    Returns the output directory path.
    """
    out = output_dir / "decompiled"
    out.mkdir(parents=True, exist_ok=True)

    await _run([
        "apktool", "d", "-f", "-o", str(out), str(apk_path),
    ])
    return out


# ------------------------------------------------------------------
# Rebuild
# ------------------------------------------------------------------
async def rebuild(work_dir: Path) -> Path:
    """
    Rebuild APK from decompiled sources.
    Returns path to the unsigned APK.
    """
    decompiled = work_dir / "decompiled"
    output_apk = work_dir / "unsigned.apk"

    await _run([
        "apktool", "b", "-f",
        "-o", str(output_apk),
        str(decompiled),
    ])
    return output_apk


# ------------------------------------------------------------------
# Zipalign
# ------------------------------------------------------------------
async def zipalign(apk_path: Path, work_dir: Path) -> Path:
    """Align the APK and return the aligned file path."""
    aligned = work_dir / "aligned.apk"
    await _run([
        "zipalign", "-f", "-p", "4",
        str(apk_path), str(aligned),
    ])
    return aligned


# ------------------------------------------------------------------
# Sign
# ------------------------------------------------------------------
async def sign(apk_path: Path, work_dir: Path) -> Path:
    """Sign APK with apksigner and return the final path."""
    final = work_dir / "final.apk"

    await _run([
        "apksigner", "sign",
        "--ks", str(KEYSTORE_PATH),
        "--ks-key-alias", KEY_ALIAS,
        "--ks-pass", f"pass:{KEYSTORE_PASS}",
        "--key-pass", f"pass:{KEYSTORE_PASS}",
        "--out", str(final),
        str(apk_path),
    ])
    return final


# ------------------------------------------------------------------
# Full pipeline
# ------------------------------------------------------------------
async def full_pipeline(apk_path: Path, work_dir: Path) -> Path:
    """decompile → (patches applied externally) → rebuild → zipalign → sign."""
    decompiled = await decompile(apk_path, work_dir)
    rebuilt = await rebuild(work_dir)
    aligned = await zipalign(rebuilt, work_dir)
    final = await sign(aligned, work_dir)
    return final
