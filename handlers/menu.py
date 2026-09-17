"""
Handler: Menu interactions (inline keyboard callbacks).

Handles:
  - Toggle patches on/off
  - Rename app
  - Set credentials
  - Build pipeline
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import Update, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils import state as user_state
from utils.files import cleanup_work_dir
from utils.apk_processor import decompile, rebuild, zipalign, sign
from utils.smali import (
    patch_package_name,
    patch_strings_xml,
    find_launcher_activity_smali,
    inject_toast_after_super,
)
from patches import license as p_license
from patches import ads as p_ads
from patches import root as p_root
from patches import signature as p_signature
from patches import toast as p_toast
from patches import server as p_server

logger = logging.getLogger(__name__)


def _patch_status_emoji(enabled: bool) -> str:
    return "✅" if enabled else "⬜"


def _build_menu_keyboard(patches: dict) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🏷️ Rename App", callback_data="menu:rename")],
        [InlineKeyboardButton("📧 Set Email/Phone", callback_data="menu:credentials")],
        [InlineKeyboardButton("--- PATCHES ---", callback_data="menu:noop")],
        [
            InlineKeyboardButton(
                f"{_patch_status_emoji(patches['remove_license'])} License (LVL)",
                callback_data="toggle:remove_license",
            )
        ],
        [
            InlineKeyboardButton(
                f"{_patch_status_emoji(patches['remove_ads'])} Ad SDKs",
                callback_data="toggle:remove_ads",
            )
        ],
        [
            InlineKeyboardButton(
                f"{_patch_status_emoji(patches['remove_root_detect'])} Root Detection",
                callback_data="toggle:remove_root_detect",
            )
        ],
        [
            InlineKeyboardButton(
                f"{_patch_status_emoji(patches['remove_signature'])} Signature Check",
                callback_data="toggle:remove_signature",
            )
        ],
        [
            InlineKeyboardButton(
                f"{_patch_status_emoji(patches['inject_toast'])} Toast Notification",
                callback_data="toggle:inject_toast",
            )
        ],
        [
            InlineKeyboardButton(
                f"{_patch_status_emoji(patches['server_bypass'])} Server Bypass (Plan/Token/Credits)",
                callback_data="toggle:server_bypass",
            )
        ],
        [InlineKeyboardButton("--- BUILD ---", callback_data="menu:noop")],
        [InlineKeyboardButton("🔨 Build & Sign APK", callback_data="build:start")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline keyboard callbacks."""
    query: CallbackQuery = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    state = user_state.load(user_id)

    if state["step"] != "menu":
        await query.edit_message_text("⚠️ Session expired. Send a new `.apk` file.")
        return

    patches = state["patches"]

    # --- Toggle patch ---
    if data.startswith("toggle:"):
        key = data.split(":", 1)[1]
        if key in patches:
            patches[key] = not patches[key]
            user_state.save(user_id, state)

            # Refresh the menu
            apk_name = Path(state["apk_path"]).name if state["apk_path"] else "unknown"
            status_text = (
                f"✅ **APK:** `{apk_name}`\n\n"
                "**Toggle patches below, then tap Build:**\n\n"
                f"{_patch_status_emoji(patches['remove_license'])} Remove License (LVL)\n"
                f"{_patch_status_emoji(patches['remove_ads'])} Remove Ad SDKs\n"
                f"{_patch_status_emoji(patches['remove_root_detect'])} Remove Root Detection\n"
                f"{_patch_status_emoji(patches['remove_signature'])} Bypass Signature Check\n"
                f"{_patch_status_emoji(patches['inject_toast'])} Inject Toast Notification\n"
                f"{_patch_status_emoji(patches['server_bypass'])} Server Bypass (Plan/Token/Credits)\n"
            )

            # Show email/phone if set
            if state.get("email") or state.get("phone"):
                status_text += "\n**Custom credentials:**\n"
                if state.get("email"):
                    status_text += f"📧 {state['email']}\n"
                if state.get("phone"):
                    status_text += f"📱 {state['phone']}\n"
            if state.get("app_name"):
                status_text += f"\n🏷️ New name: **{state['app_name']}**\n"

            await query.edit_message_text(
                status_text,
                parse_mode="Markdown",
                reply_markup=_build_menu_keyboard(patches),
            )
        return

    # --- Rename ---
    if data == "menu:rename":
        state["step"] = "renaming"
        user_state.save(user_id, state)
        await query.edit_message_text(
            "🏷️ **Enter the new app name:**\n\n"
            "Allowed: letters, numbers, spaces, hyphens (max 50 chars)\n"
            "Send /cancel to go back.",
            parse_mode="Markdown",
        )
        return

    # --- Credentials ---
    if data == "menu:credentials":
        state["step"] = "waiting_email"
        user_state.save(user_id, state)
        await query.edit_message_text(
            "📧 **Enter your email address:**\n\n"
            "This will be saved as a custom resource in the APK.\n"
            "Send /cancel to skip.",
            parse_mode="Markdown",
        )
        return

    # --- Build ---
    if data == "build:start":
        await _run_build(query, state, user_id, context)
        return


async def _run_build(query, state, user_id, context):
    """Execute the full build pipeline."""
    await query.edit_message_text("🔨 **Building…** This may take a few minutes.\n\n⏳ Decompiling…", parse_mode="Markdown")

    apk_path = Path(state["apk_path"])
    work_dir = Path(state["work_dir"])
    report: list[str] = []

    try:
        # 1. Decompile
        decompiled = await decompile(apk_path, work_dir)
        report.append("✅ APK decompiled successfully")

        # 2. Apply patches
        patches = state["patches"]

        if patches.get("remove_license"):
            result = p_license.apply(decompiled)
            report.append(f"✅ {result['description']}")

        if patches.get("remove_ads"):
            result = p_ads.apply(decompiled)
            report.append(f"✅ {result['description']}")

        if patches.get("remove_root_detect"):
            result = p_root.apply(decompiled)
            report.append(f"✅ {result['description']}")

        if patches.get("remove_signature"):
            result = p_signature.apply(decompiled)
            report.append(f"✅ {result['description']}")

        if patches.get("inject_toast"):
            result = p_toast.apply(decompiled)
            report.append(f"✅ {result['description']}")

        if patches.get("server_bypass"):
            result = p_server.apply(decompiled)
            report.append(f"✅ {result['description']}")

        # 3. Rename app if requested
        if state.get("app_name"):
            manifest = decompiled / "AndroidManifest.xml"
            patch_package_name(manifest, state["app_name"])

            strings = decompiled / "res" / "values" / "strings.xml"
            patch_strings_xml(
                strings,
                app_name=state["app_name"],
                mod_name=state.get("mod_name", ""),
                mod_email=state.get("email", ""),
                mod_phone=state.get("phone", ""),
            )
            report.append(f"✅ App renamed to: {state['app_name']}")

        # 4. Set credentials as resources
        if state.get("email") or state.get("phone"):
            strings = decompiled / "res" / "values" / "strings.xml"
            patch_strings_xml(
                strings,
                app_name=state.get("app_name", ""),
                mod_email=state.get("email", ""),
                mod_phone=state.get("phone", ""),
            )
            report.append("✅ Custom email/phone resources added")

        # 5. Rebuild
        await query.edit_message_text(
            "🔨 **Building…**\n\n⏳ Rebuilding APK…",
            parse_mode="Markdown",
        )
        rebuilt = await rebuild(work_dir)
        report.append("✅ APK rebuilt")

        # 6. Zipalign
        aligned = await zipalign(rebuilt, work_dir)
        report.append("✅ APK aligned")

        # 7. Sign
        final = await sign(aligned, work_dir)
        report.append("✅ APK signed")

        # 8. Send back to user
        original_name = state.get("original_filename", "app.apk")
        mod_name = Path(original_name).stem + "_mod.apk"

        await query.edit_message_text(
            "🔨 **Building…**\n\n📤 Sending file…",
            parse_mode="Markdown",
        )

        with open(final, "rb") as f:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=f,
                filename=mod_name,
                caption="✅ **APK Modified Successfully!**\n\nSee report below.",
                parse_mode="Markdown",
            )

        # Send report
        report_text = "📊 **Build Report**\n\n" + "\n".join(report)
        await query.message.reply_text(report_text, parse_mode="Markdown")

        # Reset state
        user_state.reset(user_id)

    except Exception as e:
        logger.exception("Build failed")
        error_text = str(e)[:500]
        report.append(f"❌ **Error:** {error_text}")
        await query.edit_message_text(
            f"❌ **Build Failed**\n\n```\n{error_text}\n```",
            parse_mode="Markdown",
        )
    finally:
        # Cleanup temp files
        cleanup_work_dir(work_dir)
