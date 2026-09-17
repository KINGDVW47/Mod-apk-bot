# 🤖 Telegram APK Mod Bot

A fully-featured Telegram bot for APK modification, built with Python 3.10+ and python-telegram-bot v20 (async). Runs on Linux using long-polling (no webhook server needed).

## Features

| Feature | Description |
|---------|-------------|
| 📥 APK Upload | Receive `.apk` files via Telegram (max 50 MB) |
| 🔨 Decompile | Decompiles APK using `apktool d -f` |
| 🏷️ Rename App | Changes `android:label` in AndroidManifest.xml + strings.xml |
| 📧 Custom Credentials | Adds `mod_email` and `mod_phone` as string resources |
| 🔔 Toast Injection | Injects `Toast.makeText()` in launcher `onCreate()` smali |
| 🚫 License Removal | Neutralizes Google LVL license checks |
| 📢 Ad Removal | Removes AdMob, Facebook, Unity, AppLovin, IronSource, and more |
| 🔓 Root Detection | Bypasses RootBeer, Magisk, SuperSU detection |
| ✍️ Signature Bypass | Disables runtime APK signature verification |
| 🌐 Server Bypass | Bypass subscription, plan, token & credit checks |
| 📦 Build & Sign | Rebuilds with apktool, zipalign, apksigner |
| 📊 Build Report | Shows which patches were applied and files modified |
| 💾 Session State | Per-user JSON state persistence |
| 🧹 Auto Cleanup | Temp files cleaned after each operation |

## Architecture

```
telegram-apk-bot/
├── main.py                    # Entry point
├── bot.py                     # Bot builder & handler registration
├── config.py                  # Configuration (env vars, paths)
├── requirements.txt           # Python dependencies
├── install.sh                 # System + Python installer
├── deploy.sh                  # VPS deploy script (systemd 24/7)
├── Dockerfile                 # Docker image for Railway/cloud
├── railway.toml               # Railway configuration
├── Procfile                   # Heroku/Railway fallback
├── .env.example               # Template for environment variables
├── handlers/                  # Telegram update handlers
│   ├── start.py               #   /start, /help, /reset commands
│   ├── receive_apk.py         #   APK file download & validation
│   ├── menu.py                #   Inline keyboard, toggle patches, build pipeline
│   └── text_router.py         #   State-driven text message routing
├── patches/                   # APK modification modules
│   ├── license.py             #   Google LVL removal
│   ├── ads.py                 #   Ad SDK removal
│   ├── root.py                #   Root detection bypass
│   ├── signature.py           #   Signature verification bypass
│   ├── toast.py               #   Toast notification injection
│   └── server.py              #   Server-side subscription/token/credit bypass
├── utils/                     # Shared utilities
│   ├── validators.py          #   Email, phone, app name validation
│   ├── state.py               #   Per-user JSON state management
│   ├── files.py               #   Temp directory management
│   ├── apk_processor.py       #   apktool, zipalign, apksigner wrappers
│   └── smali.py               #   Smali file manipulation helpers
├── states/                    # User session data (auto-created)
├── tmp/                       # Temporary work directories (auto-cleaned)
└── keystore/                  # Signing keystore (auto-generated)
```

## Requirements

- **OS:** Linux (Ubuntu 22.04+ / Debian 12+)
- **Python:** 3.10+
- **System:** default-jdk, apktool, zipalign, apksigner, aapt

## 🚀 Deploy on Railway (Gratis)

Railway gen yon plan gratis ($5 kredi/chak mwa). Koman pou deploye:

### Etap 1: Kreye Railway Account
1. Ală: https://railway.app
2. Connecte ak GitHub ou a

### Etap 2: Kreye Project
1. Click **New Project** → **Deploy from GitHub Repo**
2. Chwazi repozitwa `telegram-apk-bot` ou a

### Etap 3: Konfigire Environment Variables
Nan Railway dashboard, ale nan **Variables** epi ajoute:

| Variable | Valè |
|----------|------|
| `BOT_TOKEN` | Token bot ou a soti nan @BotFather |

### Etap 4: Deploy!
Railway pral otomatikman:
1. Build Docker image ak tout dependans (Java, apktool, etc.)
2. Kouri bot la
3. Bot la ap kouri 24/7 otomatikman!

### Wè Logs
Nan Railway dashboard → **Deployments** → click sou latest → **View Logs**

### Fichye Konfigirasyon
- `Dockerfile` — Docker image ak tout dependans sistèm
- `railway.toml` — Railway konfigirasyon
- `Procfile` — fallback start command

---

## Installation (Local / VPS)

```bash
# 1. Clone or copy this directory
cd telegram-apk-bot

# 2. Run the installer (installs system packages + Python deps + keystore)
chmod +x install.sh
./install.sh

# 3. Configure your bot token
cp .env.example .env
# Edit .env and set BOT_TOKEN from @BotFather

# 4. Activate the virtual environment
source venv/bin/activate

# 5. Start the bot
python main.py
```

## Usage

1. Open Telegram and find your bot
2. Send `/start` to begin
3. Upload an `.apk` file
4. Use the inline keyboard to toggle patches:
   - 🏷️ **Rename App** — Enter a new display name
   - 📧 **Set Email/Phone** — Add custom credentials as resources
   - Toggle each patch on/off (✅ = active, ⬜ = inactive)
5. Tap **🔨 Build & Sign APK**
6. Wait for the build to complete
7. Receive the modified APK + build report

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot, show welcome message |
| `/help` | Show detailed help with all features |
| `/reset` | Clear session state, start fresh |
| `/cancel` | Cancel current input step |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | — | Telegram bot token from @BotFather |
| `KEYSTORE_PASS` | `apkmod123` | Signing keystore password |
| `MAX_APK_SIZE_MB` | `50` | Maximum APK file size in MB |

## How Patches Work

### License Removal (LVL)
Finds and neutralizes `LicenseChecker`, `LicenseCheckerCallback` calls in smali code, making license-check methods return "licensed" or become no-ops.

### Ad SDK Removal
Removes entire smali directory trees for known ad SDK packages (AdMob, Facebook, Unity, etc.), then patches remaining ad-related method calls to `nop`.

### Root Detection Bypass
Overrides `isRooted()`, `checkRoot()`, `isDeviceRooted()` methods to always return `false`. Removes SafetyNet/Play Integrity attestation calls.

### Signature Verification Bypass
Makes `checkSignature()`, `verifySignature()`, `isSignatureValid()` always return `true`. Clears `GET_SIGNING_CERTIFICATES` flags.

### Toast Injection
Locates the launcher activity's smali file (from AndroidManifest.xml), finds the `onCreate` method's `invoke-super`, and injects a `Toast.makeText(this, "...", LENGTH_SHORT).show()` call.

## Error Handling

- File size validation before download
- APK extension check
- Individual patch modules catch exceptions gracefully
- Build pipeline reports errors with details
- Temp directories cleaned up even on failure
- Per-user state prevents cross-user interference

## License

For legitimate app development and testing purposes. Use responsibly.
