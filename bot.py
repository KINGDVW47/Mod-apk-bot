"""
Bot builder — assembles the Application and registers all handlers.
"""
from __future__ import annotations

import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN
from handlers.start import start, help_cmd, reset
from handlers.receive_apk import receive_apk
from handlers.menu import menu_callback
from handlers.text_router import text_router

logger = logging.getLogger(__name__)


def build_app() -> Application:
    """
    Build and return the configured Telegram Application.

    Uses long-polling (no webhook needed).
    """
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set. "
            "Copy .env.example to .env and add your token from @BotFather."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    # --- Command handlers ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset))

    # --- Document handler (APK uploads) ---
    app.add_handler(MessageHandler(filters.Document.ALL, receive_apk))

    # --- Inline keyboard callback handler ---
    app.add_handler(CallbackQueryHandler(menu_callback))

    # --- Text message handler (state-driven) ---
    # Must be LAST — catches all remaining text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    logger.info("Bot application built successfully.")
    return app
