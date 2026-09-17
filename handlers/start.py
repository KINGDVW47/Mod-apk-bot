"""
Handler: /start and /help commands.
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils import state as user_state


HELP_TEXT = """\
🤖 **APK Mod Bot** — Modular Android APK Modifier

**Commands:**
/start — Start the bot & show main menu
/help  — Show this help message
/reset — Reset your session & start fresh

**Workflow:**
1️⃣ Send a `.apk` file (max 50 MB)
2️⃣ Choose modifications from the menu
3️⃣ Tap **🔨 Build** to process and receive your APK

**Available Patches:**
• 🏷️ Rename app
• 📧 Set custom email/phone
• 🚫 Remove Google License (LVL)
• 📢 Remove Ad SDKs (AdMob, FB, Unity…)
• 🔓 Remove Root Detection
• ✍️ Bypass Signature Verification
• 🔔 Inject Toast Notification
• 🌐 Server Bypass (Plan/Token/Credits)

**Note:** This tool is for legitimate app development testing.
Use responsibly on apps you own or have rights to modify.
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    user_state.reset(user_id)

    welcome = (
        f"👋 Welcome **{update.effective_user.first_name}**!\n\n"
        "I help you modify Android APK files.\n\n"
        "📌 **Send me a `.apk` file** to get started,\n"
        "or type /help for full instructions."
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset command — clear all user state."""
    user_id = update.effective_user.id
    user_state.reset(user_id)

    await update.message.reply_text(
        "✅ Session reset. Send me a `.apk` file to start again.",
        parse_mode="Markdown",
    )
