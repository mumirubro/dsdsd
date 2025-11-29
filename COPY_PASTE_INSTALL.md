# 🚀 ONE-COMMAND VPS INSTALLATION

## Step 1: Connect to Your VPS

```bash
ssh root@YOUR_VPS_IP
```

Or:

```bash
ssh username@YOUR_VPS_IP
```

---

## Step 2: Copy-Paste This ENTIRE Command

**Copy everything below (all lines) and paste into your VPS terminal:**

```bash
curl -s https://raw.githubusercontent.com/mumirubro/ghgg/main/auto_install_vps.sh | bash
```

**OR if you prefer wget:**

```bash
wget -qO- https://raw.githubusercontent.com/mumirubro/ghgg/main/auto_install_vps.sh | bash
```

---

## Step 3: Enter Your Bot Token

When prompted, paste your bot token from @BotFather

That's it! ✅

---

## ALTERNATIVE METHOD (Manual Copy-Paste)

If the above doesn't work, copy-paste this **ENTIRE SCRIPT** into your VPS:

```bash
#!/bin/bash

set -e

echo "=========================================="
echo "🚀 TOJI CHK BOT - AUTO INSTALLER"
echo "=========================================="

CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    HOME_DIR="/root"
else
    HOME_DIR="/home/$CURRENT_USER"
fi

echo "Running as: $CURRENT_USER"
echo ""

# Update system
echo "📦 Updating system..."
sudo apt update && sudo apt upgrade -y

# Install requirements
echo "📦 Installing Python, pip, git..."
sudo apt install python3 python3-pip git -y

# Clone repository
echo "📥 Downloading bot..."
cd $HOME_DIR
rm -rf ghgg
git clone https://github.com/mumirubro/ghgg.git
cd ghgg

# Install packages
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

# Get bot token
echo ""
echo "🔑 Enter your BOT TOKEN from @BotFather:"
read -p "TOKEN: " BOT_TOKEN

# Create .env
cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_USERNAME=MUMIRU
EOF

# Test bot
echo "🧪 Testing bot..."
timeout 5 python3 main.py || true

# Create service
echo "⚙️ Setting up 24/7 service..."
sudo touch /var/log/toji-bot.log /var/log/toji-bot-error.log
sudo chmod 666 /var/log/toji-bot.log /var/log/toji-bot-error.log

sudo tee /etc/systemd/system/toji-bot.service > /dev/null << EOF
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$HOME_DIR/ghgg
EnvironmentFile=$HOME_DIR/ghgg/.env
ExecStart=/usr/bin/python3 $HOME_DIR/ghgg/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/toji-bot.log
StandardError=append:/var/log/toji-bot-error.log

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable toji-bot
sudo systemctl start toji-bot

echo ""
echo "✅ INSTALLATION COMPLETE!"
echo ""
sudo systemctl status toji-bot --no-pager
echo ""
echo "🎉 BOT IS RUNNING 24/7!"
echo ""
echo "Commands:"
echo "  Status:  sudo systemctl status toji-bot"
echo "  Logs:    sudo journalctl -u toji-bot -f"
echo "  Restart: sudo systemctl restart toji-bot"
echo ""
```

---

## 📋 Daily Commands (After Installation)

### Check if bot is running:
```bash
sudo systemctl status toji-bot
```

### View live logs:
```bash
sudo journalctl -u toji-bot -f
```

### Restart bot:
```bash
sudo systemctl restart toji-bot
```

### Stop bot:
```bash
sudo systemctl stop toji-bot
```

### Update bot (when you make changes):
```bash
cd ~/ghgg
sudo systemctl stop toji-bot
git pull origin main
sudo systemctl restart toji-bot
```

---

## ✅ You're Done!

Your bot is now:
- ✅ Running 24/7
- ✅ Auto-restarts on crash
- ✅ Auto-starts on VPS reboot

Test it in Telegram! 🎉
