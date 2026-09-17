#!/usr/bin/env python3
"""
Telegram APK Mod Bot — Entry Point

Usage:
    python main.py

Before running:
    1. Run ./install.sh to install dependencies
    2. Copy .env.example to .env and set BOT_TOKEN
    3. Activate venv: source venv/bin/activate
    4. Run: python main.py
"""
import logging
import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import build_app
from utils.files import cleanup_all_tmp
from config import BOT_TOKEN

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Quieten noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


def main() -> None:
    """Start the bot with long-polling."""
    # Validate config
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Copy .env.example to .env and add your token.")
        sys.exit(1)

    # Clean up leftover temp files from previous runs
    cleanup_all_tmp()
    logger.info("Cleaned up temporary directories.")

    # Build and run
    app = build_app()
    logger.info("Starting APK Mod Bot (long-polling)…")
    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
        ],
        drop_pending_updates=True,  # Ignore messages sent while bot was offline
    )


if __name__ == "__main__":
    main()
