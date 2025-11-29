# 🚀 ONE COMMAND INSTALLATION

## Copy & Paste This ONE Command Into Your VPS:

```bash
bash <(curl -s https://raw.githubusercontent.com/mumirubro/dsdfraffgdsgf/main/install_vps.sh)
```

### OR if curl doesn't work, use wget:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/mumirubro/dsdfraffgdsgf/main/install_vps.sh)
```

---

## If Above Doesn't Work, Use This Full Script:

**Copy EVERYTHING below and paste into VPS:**

```bash
#!/bin/bash
set -e
clear
echo "🚀 TOJI CHK BOT - ONE-COMMAND INSTALLER"
echo "=========================================="
echo ""

# Get user info
CURRENT_USER=$(whoami)
[ "$CURRENT_USER" = "root" ] && HOME_DIR="/root" || HOME_DIR="/home/$CURRENT_USER"

echo "✓ User: $CURRENT_USER"
echo "✓ Installing to: $HOME_DIR/dsdfraffgdsgf"
echo ""

# Update & install
echo "📦 Installing requirements..."
sudo apt update -qq && sudo apt install -y python3 python3-pip git > /dev/null 2>&1

# Clone repo
echo "📥 Downloading bot..."
cd $HOME_DIR
rm -rf dsdfraffgdsgf
git clone -q https://github.com/mumirubro/dsdfraffgdsgf.git
cd dsdfraffgdsgf

# Install packages
echo "📦 Installing Python packages..."
pip3 install -q -r requirements.txt

# Get token
echo ""
echo "🔑 Paste your bot token from @BotFather:"
read -p "TOKEN: " BOT_TOKEN
echo ""

# Create .env
cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_USERNAME=MUMIRU
EOF

# Test
echo "🧪 Quick test..."
timeout 3 python3 main.py > /dev/null 2>&1 || true

# Setup service
echo "⚙️ Setting up 24/7 service..."
sudo mkdir -p /var/log
sudo touch /var/log/toji-bot.log /var/log/toji-bot-error.log
sudo chmod 666 /var/log/toji-bot.log /var/log/toji-bot-error.log

sudo bash -c "cat > /etc/systemd/system/toji-bot.service" << EOF
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$HOME_DIR/dsdfraffgdsgf
EnvironmentFile=$HOME_DIR/dsdfraffgdsgf/.env
ExecStart=/usr/bin/python3 $HOME_DIR/dsdfraffgdsgf/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/toji-bot.log
StandardError=append:/var/log/toji-bot-error.log

[Install]
WantedBy=multi-user.target
EOF

# Start
sudo systemctl daemon-reload
sudo systemctl enable toji-bot > /dev/null 2>&1
sudo systemctl start toji-bot

echo ""
echo "=========================================="
echo "✅ INSTALLATION COMPLETE!"
echo "=========================================="
echo ""
echo "🎉 Your bot is now running 24/7!"
echo ""
echo "📋 Useful Commands:"
echo "  Check status: sudo systemctl status toji-bot"
echo "  View logs:    sudo journalctl -u toji-bot -f"
echo "  Restart:      sudo systemctl restart toji-bot"
echo ""
echo "Test your bot in Telegram now! ✨"
echo ""
```

---

## ✅ After Installation

### Check if running:
```bash
sudo systemctl status toji-bot
```

### View logs:
```bash
sudo journalctl -u toji-bot -f
```

### Restart:
```bash
sudo systemctl restart toji-bot
```

### Update bot:
```bash
cd ~/dsdfraffgdsgf && git pull && sudo systemctl restart toji-bot
```

---

**That's it! Just ONE command and you're done!** 🚀
