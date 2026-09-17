"""
Global configuration for the Telegram APK Mod Bot.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent / ".env")

# --- Telegram ---
BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent
KEYSTORE_PATH = PROJECT_ROOT / "keystore" / "release.keystore"
KEYSTORE_PASS = os.environ.get("KEYSTORE_PASS", "apkmod123")
KEY_ALIAS = "release"
TMP_DIR = PROJECT_ROOT / "tmp"
STATES_DIR = PROJECT_ROOT / "states"

# --- Limits ---
MAX_APK_SIZE_MB: int = int(os.environ.get("MAX_APK_SIZE_MB", "50"))
MAX_APK_SIZE_BYTES = MAX_APK_SIZE_MB * 1024 * 1024

# Ensure directories exist
TMP_DIR.mkdir(exist_ok=True)
STATES_DIR.mkdir(exist_ok=True)
