# 🚀 VPS Deployment Guide — Telegram APK Mod Bot

Koman pou deploye bot la sou yon VPS pou li kouri 24/7.

---

## 📋 Ki sa ou bezwen

| Konpozan | Rekizisyon |
|----------|-----------|
| **VPS** | Ubuntu 22.04+ oswa Debian 12+ |
| **RAM** | Minimòm 1 GB |
| **Disk** | Minimòm 10 GB |
| **Bot Token** | Soti nan @BotFather sou Telegram |

### VPS Pwovasyonè rekòmande
- **Hetzner** (€3.50/mwa — CX11)
- **DigitalOcean** ($4/mwa — Basic Droplet)
- **Vultr** ($2.50/mwa — Regular Cloud Compute)
- **Linode** ($5/mwa — Nanode 1GB)

---

## 🔧 Koman pou deploye (4 etap)

### Etap 1: Konekte sou VPS ou a

```bash
ssh root@VPS_IP_ADRESS
```

### Etap 2: Klonnen oswa transfere kòd la

**Opsyon A: Klonnen ak Git**
```bash
git clone https://github.com/OU_REPO/telegram-apk-bot.git
cd telegram-apk-bot
```

**Opsyon B: Transfere ak SCP** (soti nan òdinatè ou)
```bash
scp -r telegram-apk-bot/ root@VPS_IP:/root/
ssh root@VPS_IP
cd telegram-apk-bot
```

### Etap 3: Mete BOT_TOKEN ou a

```bash
nano .env
```

Chanjman li ye a:
```
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

Pye `Ctrl+X` → `Y` → `Enter` pou sove.

### Etap 4: Kouri deploy script la

```bash
chmod +x deploy.sh
sudo bash deploy.sh
```

Sa pral:
1. ✅ Enstale tout dependans (Java, apktool, Python, etc.)
2. ✅ Kreye virtual environment Python
3. ✅ Enstale pakè Python
4. ✅ Kreye signing keystore
5. ✅ Enstale systemd service (24/7 otomatik)
6. ✅ Demare bot la

---

## 📊 Koman pou jere bot la

### Wè status bot la
```bash
systemctl status apk-mod-bot
```

### Wè logs an tan reyèl
```bash
journalctl -u apk-mod-bot -f
```

### Restart bot la
```bash
systemctl restart apk-mod-bot
```

### Stop bot la
```bash
systemctl stop apk-mod-bot
```

### Edit .env (chanje token oswa konfigirasyon)
```bash
nano /root/telegram-apk-bot/.env
systemctl restart apk-mod-bot
```

---

## 🔒 Sekirite (rekomandasyon)

### 1. Chanje modpas keystore
```bash
nano config.py
# Chanje KEYSTORE_PASS la
```

### 2. Limite access VPS
```bash
# Enstale fail2ban
apt install fail2ban -y
systemctl enable fail2ban
```

### 3. Configure firewall
```bash
ufw allow 22/tcp    # SSH
ufw enable
```

---

## ❗ Pwoblèm ak Solisyon

### Bot la pa demare
```bash
journalctl -u apk-mod-bot -n 50
```

### Bot token invalide
1. Verifie token ou a sou @BotFather
2. Edit `.env` epi mete token kòrèk la
3. Restart: `systemctl restart apk-mod-bot`

### Espas disk pase
```bash
# Tèmpe fichye yo otomatikman netwaye
systemctl restart apk-mod-bot
```

---

## 🔄 Update bot la

```bash
cd /root/telegram-apk-bot
git pull
source venv/bin/activate
pip install -r requirements.txt -q
systemctl restart apk-mod-bot
```
