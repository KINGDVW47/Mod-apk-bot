"""
Handler: Text message router.

Routes incoming text messages based on the user's current state step.
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from utils import state as user_state
from utils.validators import is_valid_app_name, is_valid_email, is_valid_phone
from utils.files import cleanup_work_dir
from pathlib import Path

logger = logging.getLogger(__name__)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route text messages based on the user's current conversation step.
    """
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = user_state.load(user_id)
    step = state.get("step", "idle")

    # Handle /cancel at any step
    if text.lower() == "/cancel":
        if state.get("work_dir"):
            cleanup_work_dir(Path(state["work_dir"]))
        state = user_state.reset(user_id)
        await update.message.reply_text(
            "↩️ Cancelled. Send a new `.apk` to start again.",
            parse_mode="Markdown",
        )
        return

    # --- Renaming state ---
    if step == "renaming":
        if is_valid_app_name(text):
            state["app_name"] = text
            state["step"] = "menu"
            user_state.save(user_id, state)

            await update.message.reply_text(
                f"🏷️ App name set to: **{text}**\n\n"
                "Return to the menu to continue.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "❌ Invalid name. Use letters, numbers, spaces, hyphens (max 50 chars).\n"
                "Or send /cancel to go back.",
            )
        return

    # --- Waiting for email ---
    if step == "waiting_email":
        if text.lower() == "skip":
            state["email"] = None
            state["step"] = "waiting_phone"
            user_state.save(user_id, state)
            await update.message.reply_text(
                "📱 **Enter phone number** (or /skip to skip):",
                parse_mode="Markdown",
            )
            return

        if is_valid_email(text):
            state["email"] = text
            state["step"] = "waiting_phone"
            user_state.save(user_id, state)
            await update.message.reply_text(
                "📱 **Enter phone number** (or /skip to skip):",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "❌ Invalid email format. Try again or /skip.",
            )
        return

    # --- Waiting for phone ---
    if step == "waiting_phone":
        if text.lower() == "skip":
            state["phone"] = None
            state["step"] = "menu"
            user_state.save(user_id, state)
            await update.message.reply_text(
                "✅ Credentials saved. Return to the menu to continue.",
                parse_mode="Markdown",
            )
            return

        if is_valid_phone(text):
            state["phone"] = text
            state["step"] = "menu"
            user_state.save(user_id, state)
            await update.message.reply_text(
                "✅ Credentials saved (email + phone). Return to the menu to continue.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "❌ Invalid phone number. Use format +1234567890 (7-15 digits).\n"
                "Or send /skip to skip.",
            )
        return

    # --- Idle or menu: tell them to send APK ---
    if step in ("idle", "menu"):
        await update.message.reply_text(
            "📌 Send me a `.apk` file to get started, or type /help.",
            parse_mode="Markdown",
        )
        return

    # Fallback
    await update.message.reply_text(
        "🤔 I didn't understand that. Type /help for commands.",
    )
