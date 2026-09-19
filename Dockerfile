# =============================================================================
# Dockerfile — APK Mod Bot (pou Railway / Render / Docker)
#
# Bati yon imaj ki gen tout zouti nesesè:
#   - Python 3.11 + python-telegram-bot
#   - Java (default-jre) pou apktool
#   - apktool, zipalign, apksigner, aapt/aapt2
#
# Kijan pou konstwi:  docker build -t apk-mod-bot .
# =============================================================================

FROM python:3.11-slim

# ---- Vèsyon apktool (dènye vèsyon) ----
ENV APKTOOL_VERSION=2.10.0

# ---- Enstale depandans sistèm ----
# Nou sèvi ak openjdk (jre) olye default-jre paske imaj slim la pa gen apt
# repozitwa konplè default-jdk. openjdk-21-jre-headless ap ase pou apktool.
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-21-jre-headless \
        curl \
        unzip \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---- Enstale apktool (dènye vèsyon GitHub) ----
RUN curl -L -o /usr/local/bin/apktool.jar \
        "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar" \
    && printf '#!/usr/bin/env bash\njava -jar /usr/local/bin/apktool.jar "$@"\n' > /usr/local/bin/apktool \
    && chmod +x /usr/local/bin/apktool

# ---- Enstale zipalign + apksigner + aapt/aapt2 ----
# Zouti sa yo soti nan Android SDK build-tools. Nou telechaje yon vèsyon
# build-tools konpatib epi nou ekstrè zouti nesesè yo nan /usr/local/bin.
ENV BUILD_TOOLS_VERSION=34
# Nou kenbe tout katab build-tools la ansanm (binèr + lib) paske zipalign,
# aapt ak apksigner bezwen bibliyotèk yo (lib/libc++.so) ki nan MENM katab.
# Nou mete katab la nan PATH pou zouti yo jwenn lib yo otomatikman.
RUN curl -L -o /tmp/build-tools.zip \
        "https://dl.google.com/android/repository/build-tools_r${BUILD_TOOLS_VERSION}-linux.zip" \
    && mkdir -p /opt/android-sdk/build-tools \
    && unzip -q /tmp/build-tools.zip -d /opt/android-sdk/build-tools \
    && BT_DIR="/opt/android-sdk/build-tools/android-14" \
    && chmod +x "$BT_DIR/aapt" "$BT_DIR/aapt2" "$BT_DIR/zipalign" "$BT_DIR/apksigner" \
    && ln -sf "$BT_DIR/aapt" /usr/local/bin/aapt \
    && ln -sf "$BT_DIR/aapt2" /usr/local/bin/aapt2 \
    && ln -sf "$BT_DIR/zipalign" /usr/local/bin/zipalign \
    && ln -sf "$BT_DIR/apksigner" /usr/local/bin/apksigner \
    && rm -rf /tmp/build-tools.zip

# ---- Depandans Python ----
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Kopiye kòd aplikasyon an ----
COPY . .

# ---- Kreye repèrtwar travay yo ----
RUN mkdir -p work uploads state keys

# ---- Varyab anviwònman (Railway pral mete BOT_TOKEN isit la) ----
ENV BOT_TOKEN=""

# ---- Kòmand demaraj: enstale keystore si absent, epi lanse bot la ----
CMD ["bash", "start.sh"]
