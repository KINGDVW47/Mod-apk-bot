# 🆓 Gratis VPS / Cloud Deploy Options

Si ou pa gen VPS, gen anpil opsyon **gratis** pou kouri bot la 24/7.

---

## 🔥 Op 1: Oracle Cloud Free Tier (REKÒMANDE)

**100% gratis pou toujou** — 1GB RAM, 20GB disk, ARM CPU

### Koman pou kreye:
1. Ală: https://cloud.oracle.com/free
2. Kreye yon kont gratis
3. Kreye yon **VM Instance** (ARM, Ubuntu 22.04)
4. SSH connecte sou li
5. Kouri `deploy.sh`

```bash
# Sou Oracle VM ou a:
wget https://raw.githubusercontent.com/YOU/repo/main/deploy.sh
sudo bash deploy.sh
```

---

## ☁️ Op 2: Render.com (Gratis)

**Gratis pou toujours** — 512MB RAM, auto-sleep

### Koman pou kreye:
1. Ală: https://render.com
2. Connecte GitHub ou a
3. Kreye yon **Background Worker**
4. Mete environment variable `BOT_TOKEN`
5. Deploy automatik

Fichye `render.yaml` pou Render:
```yaml
services:
  - type: worker
    name: apk-mod-bot
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: BOT_TOKEN
        sync: false
```

---

## 🚂 Op 3: Railway.app (Gratis $5 credit)

### Koman pou kreye:
1. Ală: https://railway.app
2. Connecte GitHub
3. New Project → Deploy from GitHub
4. Ajoute env var: `BOT_TOKEN`
5. Deploy!

---

## 🐳 Op 4: Kouri sou òdinatè ou a (lokal)

Si ou gen yon òdinatè ki toujou allume:

```bash
# Enstale dependans
sudo apt install default-jdk apktool zipalign apksigner aapt python3-pip

# Klonnen kòd la
git clone https://github.com/OU/telegram-apk-bot.git
cd telegram-apk-bot

# Enstale pakè Python
pip install -r requirements.txt

# Kreye .env
echo "BOT_TOKEN=8935346667:AAEMQhL7oXDNItXzbk-4cNXkLCLNH6dWGjU" > .env
echo "KEYSTORE_PASS=apkmod123" >> .env
echo "MAX_APK_SIZE_MB=50" >> .env

# Kouri bot la
python3 main.py
```

### Pou kouri li 24/7 sou òdinatè:
```bash
# Kouri ak screen (rekomande)
screen -S apk-bot
python3 main.py

# Detache: Ctrl+A, D
# Wè log: screen -r apk-bot
```

---

## 📊 Konparasyon

| Opsyon | Pri | RAM | 24/7? | Difisil? |
|--------|-----|-----|-------|----------|
| Oracle Cloud | Gratis | 1GB | ✅ Wi | Mwayen |
| Render.com | Gratis | 512MB | ⚠️ Sleep | Fasil |
| Railway | $5 gratis | 1GB | ✅ Wi | Fasil |
| Lokal | Gratis | Limitasyon ou | ⚠️ Dwe alume | Trè fasil |
