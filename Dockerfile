# ============================================================
# Telegram APK Mod Bot — Docker Image for Railway
# Includes all system deps: Java, apktool, zipalign, apksigner
# ============================================================

FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# ---- 1. Install system dependencies ----
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    default-jdk \
    apktool \
    zipalign \
    apksigner \
    aapt \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---- 2. Create app directory ----
WORKDIR /app

# ---- 3. Copy requirements and install Python deps ----
COPY telegram-apk-bot/requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# ---- 4. Copy all bot files ----
COPY telegram-apk-bot/ .

# ---- 5. Create necessary directories ----
RUN mkdir -p states tmp keystore

# ---- 6. Generate signing keystore if not exists ----
RUN if [ ! -f keystore/release.keystore ]; then \
        mkdir -p keystore && \
        keytool -genkeypair \
            -alias release \
            -keyalg RSA \
            -keysize 2048 \
            -validity 10000 \
            -keystore keystore/release.keystore \
            -storepass apkmod123 \
            -keypass apkmod123 \
            -dname "CN=APK Mod Bot, OU=Dev, O=Local, L=Unknown, ST=Unknown, C=US"; \
    fi

# ---- 7. Set environment variables ----
ENV PYTHONUNBUFFERED=1
ENV BOT_TOKEN=""

# ---- 8. Run the bot ----
CMD ["python3", "main.py"]
