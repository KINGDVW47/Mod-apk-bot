"""
File-system helpers for temporary work directories.
"""
import shutil
import tempfile
from pathlib import Path

from config import TMP_DIR


def create_work_dir(label: str = "apkwork") -> Path:
    """Create a fresh temporary work directory inside TMP_DIR."""
    d = tempfile.mkdtemp(prefix=f"{label}_", dir=str(TMP_DIR))
    return Path(d)


def cleanup_work_dir(work_dir: Path) -> None:
    """Recursively remove a work directory, ignoring errors."""
    if work_dir and work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)


def cleanup_all_tmp() -> None:
    """Remove everything inside TMP_DIR (called on startup)."""
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR, ignore_errors=True)
        TMP_DIR.mkdir(exist_ok=True)
