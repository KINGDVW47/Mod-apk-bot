#!/usr/bin/env bash
# ============================================================
# Telegram APK Mod Bot - Installation Script
# Tested on Ubuntu 22.04+ / Debian 12+
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[x]${NC} $*" >&2; }

# ---- 1. System packages ----
log "Updating apt…"
sudo apt-get update -qq

log "Installing system dependencies…"
sudo apt-get install -y -qq \
    default-jdk \
    apktool \
    zipalign \
    apksigner \
    aapt \
    python3 \
    python3-pip \
    python3-venv

# ---- 2. Python virtual environment ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

if [ ! -d "$VENV_DIR" ]; then
    log "Creating Python virtual environment…"
    python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

log "Installing Python packages…"
pip install --upgrade pip -q
pip install -r "${SCRIPT_DIR}/requirements.txt" -q

# ---- 3. Signing keystore ----
KEYSTORE="${SCRIPT_DIR}/keystore/release.keystore"
if [ ! -f "$KEYSTORE" ]; then
    log "Generating signing keystore…"
    mkdir -p "$(dirname "$KEYSTORE")"
    keytool -genkeypair \
        -alias release \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -keystore "$KEYSTORE" \
        -storepass apkmod123 \
        -keypass apkmod123 \
        -dname "CN=APK Mod Bot, OU=Dev, O=Local, L=Unknown, ST=Unknown, C=US"
    log "Keystore created at ${KEYSTORE}"
    warn "Default password: apkmod123  — change it in production!"
else
    warn "Keystore already exists, skipping generation."
fi

# ---- 4. States directory ----
mkdir -p "${SCRIPT_DIR}/states"
mkdir -p "${SCRIPT_DIR}/tmp"

log "Installation complete!"
echo ""
echo "  To run the bot:"
echo "    1. Copy .env.example to .env and add your BOT_TOKEN"
echo "    2. source venv/bin/activate"
echo "    3. python main.py"
echo ""
