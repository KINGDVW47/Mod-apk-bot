"""
Handler: Receive APK file via document attachment.

Downloads the APK to a temp directory and transitions user to the menu.
"""
from __future__ import annotations

import logging
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import MAX_APK_SIZE_BYTES, TMP_DIR
from utils import state as user_state
from utils.files import create_work_dir

logger = logging.getLogger(__name__)

# Inline keyboard for the modification menu
def _build_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🏷️ Rename App", callback_data="menu:rename")],
        [InlineKeyboardButton("📧 Set Email/Phone", callback_data="menu:credentials")],
        [InlineKeyboardButton("--- PATCHES ---", callback_data="menu:noop")],
        [InlineKeyboardButton("🚫 Remove License (LVL)", callback_data="toggle:remove_license")],
        [InlineKeyboardButton("📢 Remove Ad SDKs", callback_data="toggle:remove_ads")],
        [InlineKeyboardButton("🔓 Remove Root Detection", callback_data="toggle:remove_root_detect")],
        [InlineKeyboardButton("✍️ Bypass Signature Check", callback_data="toggle:remove_signature")],
        [InlineKeyboardButton("🔔 Inject Toast", callback_data="toggle:inject_toast")],
        [InlineKeyboardButton("🌐 Server Bypass (Plan/Token/Credits)", callback_data="toggle:server_bypass")],
        [InlineKeyboardButton("--- BUILD ---", callback_data="menu:noop")],
        [InlineKeyboardButton("🔨 Build & Sign APK", callback_data="build:start")],
    ]
    return InlineKeyboardMarkup(keyboard)


def _patch_status_emoji(enabled: bool) -> str:
    return "✅" if enabled else "⬜"


async def receive_apk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming document — expect .apk files."""
    document = update.message.document
    user_id = update.effective_user.id

    # Validate file extension
    if not document.file_name or not document.file_name.lower().endswith(".apk"):
        await update.message.reply_text(
            "❌ Please send a valid `.apk` file.",
            parse_mode="Markdown",
        )
        return

    # Validate file size
    if document.file_size and document.file_size > MAX_APK_SIZE_BYTES:
        await update.message.reply_text(
            f"❌ File too large. Maximum size is **{MAX_APK_SIZE_BYTES // (1024*1024)} MB**.",
            parse_mode="Markdown",
        )
        return

    # Acknowledge and show progress
    status_msg = await update.message.reply_text("📥 Downloading APK…")

    try:
        # Create a fresh work directory
        work_dir = create_work_dir(f"apk_{user_id}")

        # Download the file
        tg_file = await context.bot.get_file(document.file_id)
        apk_path = work_dir / document.file_name
        await tg_file.download_to_drive(str(apk_path))

        # Update state
        state = user_state.load(user_id)
        state["step"] = "menu"
        state["apk_path"] = str(apk_path)
        state["work_dir"] = str(work_dir)
        state["original_filename"] = document.file_name
        user_state.save(user_id, state)

        # Build status text
        patches = state["patches"]
        status_text = (
            f"✅ **APK Received:** `{document.file_name}`\n"
            f"📦 Size: {document.file_size // 1024 if document.file_size else '?'} KB\n\n"
            "**Toggle patches below, then tap Build:**\n\n"
            f"{_patch_status_emoji(patches['remove_license'])} Remove License (LVL)\n"
            f"{_patch_status_emoji(patches['remove_ads'])} Remove Ad SDKs\n"
            f"{_patch_status_emoji(patches['remove_root_detect'])} Remove Root Detection\n"
            f"{_patch_status_emoji(patches['remove_signature'])} Bypass Signature Check\n"
            f"{_patch_status_emoji(patches['inject_toast'])} Inject Toast Notification\n"
        )

        await status_msg.edit_text(
            status_text,
            parse_mode="Markdown",
            reply_markup=_build_menu_keyboard(),
        )

    except Exception as e:
        logger.exception("Failed to process APK upload")
        await status_msg.edit_text(
            f"❌ Error processing file: `{str(e)[:200]}`",
            parse_mode="Markdown",
        )
