# 📝 SIMPLE COMMAND SHEET - COPY & PASTE

Use this as a quick reference. Just copy and paste the commands!

---

## 🔥 INITIAL SETUP (Do Once)

### 1. Connect to VPS
```bash
ssh root@YOUR_VPS_IP
```

### 2. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Requirements
```bash
sudo apt install python3 python3-pip git -y
```

### 4. Clone Bot from GitHub
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git
cd toji-chk-bot
```

### 5. Install Python Packages
```bash
pip3 install -r requirements.txt
```

### 6. Create .env File
```bash
nano .env
```

**Add this (replace with your token):**
```
BOT_TOKEN=your_actual_bot_token_here
ADMIN_USERNAME=mumiru
```

**Save:** `Ctrl+X` → `Y` → `Enter`

### 7. Test Bot
```bash
python3 main.py
```

**Press Ctrl+C to stop**

### 8. Set Up 24/7 Service
```bash
sudo nano /etc/systemd/system/toji-bot.service
```

**Paste this (replace YOUR_USERNAME with your actual username from `whoami`):**

```ini
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/toji-chk-bot
EnvironmentFile=/home/YOUR_USERNAME/toji-chk-bot/.env
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/toji-chk-bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/toji-bot.log
StandardError=append:/var/log/toji-bot-error.log

[Install]
WantedBy=multi-user.target
```

**Save:** `Ctrl+X` → `Y` → `Enter`

### 9. Create Log Files
```bash
sudo touch /var/log/toji-bot.log /var/log/toji-bot-error.log
sudo chmod 666 /var/log/toji-bot.log /var/log/toji-bot-error.log
```

### 10. Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable toji-bot
sudo systemctl start toji-bot
```

### 11. Check Status
```bash
sudo systemctl status toji-bot
```

✅ **DONE! Bot is running 24/7**

---

## 🔄 DAILY USE COMMANDS

### Check if bot is running
```bash
sudo systemctl status toji-bot
```

### Start bot
```bash
sudo systemctl start toji-bot
```

### Stop bot
```bash
sudo systemctl stop toji-bot
```

### Restart bot
```bash
sudo systemctl restart toji-bot
```

### View live logs
```bash
sudo journalctl -u toji-bot -f
```

### View last 50 log lines
```bash
sudo journalctl -u toji-bot -n 50
```

### View error log
```bash
sudo tail -50 /var/log/toji-bot-error.log
```

---

## 🔄 UPDATE BOT

### When you make code changes:

```bash
cd ~/toji-chk-bot
sudo systemctl stop toji-bot
git pull origin main
sudo systemctl restart toji-bot
sudo systemctl status toji-bot
```

---

## 🔐 SECURITY

### Enable firewall
```bash
sudo apt install ufw -y
sudo ufw allow ssh
sudo ufw enable
sudo ufw status
```

---

## 🆘 TROUBLESHOOTING

### View recent errors
```bash
sudo journalctl -u toji-bot --since "1 hour ago" | grep -i error
```

### Full error log
```bash
sudo tail -100 /var/log/toji-bot-error.log
```

### Check Python version
```bash
python3 --version
```

### Reinstall packages
```bash
cd ~/toji-chk-bot
pip3 install -r requirements.txt
```

### Fix permissions
```bash
sudo chown -R $USER:$USER ~/toji-chk-bot
```

---

## 📋 QUICK INFO

### Get your username
```bash
whoami
```

### Check disk space
```bash
df -h
```

### Check memory
```bash
free -h
```

### Exit SSH
```bash
exit
```

---

**That's it! Keep this file handy for quick copy-paste!** 🚀
