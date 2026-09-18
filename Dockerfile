============================================================
# Telegram APK Mod Bot — Docker Image for Railway
# ============================================================

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    default-jdk apktool zipalign apksigner aapt \
    python3 python3-pip python3-venv curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy from telegram-apk-bot/ (Railway context is repo root)
COPY telegram-apk-bot/requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY telegram-apk-bot/ .

RUN mkdir -p states tmp keystore

RUN if [ ! -f keystore/release.keystore ]; then \
        mkdir -p keystore && \
        keytool -genkeypair -alias release -keyalg RSA -keysize 2048 \
            -validity 10000 -keystore keystore/release.keystore \
            -storepass apkmod123 -keypass apkmod123 \
            -dname "CN=APK Mod Bot, OU=Dev, O=Local, L=Unknown, ST=Unknown, C=US"; \
    fi

ENV PYTHONUNBUFFERED=1
ENV BOT_TOKEN=""
CMD ["python3", "main.py"]
Klike Commit changes
Etap 2: Deploye sou Railway
Ale sou https://railway.app → Login with GitHub
Klike New Project → Deploy from GitHub Repo
Chwazi KINGDVW47/Mod-apk-bot
Nan Variables tab, ajoute:
Name: BOT_TOKEN
Value: 8935346667:AAEMQhL7oXDNItXzbk-4cNXkLCLNH6dWGjU
Done! Bot ap kouri 24/7!
Ou pa bezwen update lòt fichye yo pou Railway mache - Dockerfile a se sa ki enpòtan!


Update Dockerfile sou GitHub

Update bot.py ak start.py sou GitHub

Montre m kijan pou update tout fichye yo

Show less
Credits used: 6
(21)




Rewind

Boost

Auto-Fix
