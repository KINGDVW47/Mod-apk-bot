#!/usr/bin/env bash
# ============================================================
# Telegram APK Mod Bot — Full VPS Deploy Script
# Tested on Ubuntu 22.04+ / Debian 12+
# Installs deps, sets up systemd service for 24/7 operation
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[x]${NC} $*" >&2; }
info() { echo -e "${CYAN}[i]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="apk-mod-bot"
BOT_USER="${SUDO_USER:-$(whoami)}"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║    🤖 Telegram APK Mod Bot — VPS Deploy     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ---- 1. Check if running as root ----
if [ "$(id -u)" -ne 0 ]; then
    err "Script sa a bezwen kouri ak sudo. Tès: sudo bash deploy.sh"
    exit 1
fi

# ---- 2. System packages ----
log "Mete ajou apt..."
apt-get update -qq

log "Enstale dependans sistèm..."
apt-get install -y -qq \
    default-jdk \
    apktool \
    zipalign \
    apksigner \
    aapt \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    htop

# ---- 3. Python virtual environment ----
VENV_DIR="${SCRIPT_DIR}/venv"

if [ ! -d "$VENV_DIR" ]; then
    log "Kreye virtual environment Python..."
    python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

log "Enstale pakè Python..."
pip install --upgrade pip -q
pip install -r "${SCRIPT_DIR}/requirements.txt" -q

# ---- 4. Signing keystore ----
KEYSTORE="${SCRIPT_DIR}/keystore/release.keystore"
if [ ! -f "$KEYSTORE" ]; then
    log "Kreye signing keystore..."
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
    log "Keystore kreye: ${KEYSTORE}"
    warn "Modpas default: apkmod123 — chanje li nan pwodiksyon!"
else
    warn "Keystore deja egziste, nap rete sa."
fi

# ---- 5. States & tmp directories ----
mkdir -p "${SCRIPT_DIR}/states"
mkdir -p "${SCRIPT_DIR}/tmp"

# ---- 6. Create .env if not exists ----
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    warn "Fichye .env pa egziste!"
    info "Kreye .env ak token bot ou a..."
    echo "# Telegram Bot Token (from @BotFather)" > "${SCRIPT_DIR}/.env"
    echo "BOT_TOKEN=CHANGE_ME_TO_YOUR_TOKEN" >> "${SCRIPT_DIR}/.env"
    echo "" >> "${SCRIPT_DIR}/.env"
    echo "KEYSTORE_PASS=apkmod123" >> "${SCRIPT_DIR}/.env"
    echo "MAX_APK_SIZE_MB=50" >> "${SCRIPT_DIR}/.env"
    warn "⭐ OU DWE edit fichye .env la epi mete BOT_TOKEN ou a:"
    warn "   nano ${SCRIPT_DIR}/.env"
else
    log ".env deja egziste."
fi

# ---- 7. Install systemd service ----
log "Enstale systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Telegram APK Mod Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_USER}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal+console
StandardError=journal+console

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=${SCRIPT_DIR}/states ${SCRIPT_DIR}/tmp ${SCRIPT_DIR}/keystore

# Environment
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# ---- 8. Enable & start service ----
log "Reload systemd daemon..."
systemctl daemon-reload

log "Enable service pou demare otomatikman..."
systemctl enable ${SERVICE_NAME}

log "Demare bot la..."
systemctl start ${SERVICE_NAME}

# Wait a moment and check status
sleep 3

if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ✅ Bot la ap kouri avèk siksè!          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    info "Etap ki pase:"
    info "  📋 Wè logs:        journalctl -u ${SERVICE_NAME} -f"
    info "  📋 Wè status:      systemctl status ${SERVICE_NAME}"
    info "  🔄 Restart:        systemctl restart ${SERVICE_NAME}"
    info "  ⏹  Stop:           systemctl stop ${SERVICE_NAME}"
    info "  📝 Edit .env:      nano ${SCRIPT_DIR}/.env"
    echo ""
else
    err "Bot la pa demare kòrèkteman!"
    err "Tès: journalctl -u ${SERVICE_NAME} -n 20"
    echo ""
fi
