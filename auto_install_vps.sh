#!/bin/bash

# ========================================
# TOJI CHK BOT - AUTO INSTALLER FOR VPS
# ========================================
# Just copy-paste this entire script into your VPS terminal!

set -e  # Exit on error

echo "=========================================="
echo "🚀 TOJI CHK BOT - AUTO INSTALLER"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current user
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    HOME_DIR="/root"
else
    HOME_DIR="/home/$CURRENT_USER"
fi

echo -e "${GREEN}✓${NC} Running as user: $CURRENT_USER"
echo -e "${GREEN}✓${NC} Home directory: $HOME_DIR"
echo ""

# Step 1: Update system
echo "=========================================="
echo "📦 Step 1: Updating system..."
echo "=========================================="
sudo apt update
sudo apt upgrade -y
echo -e "${GREEN}✓${NC} System updated!"
echo ""

# Step 2: Install requirements
echo "=========================================="
echo "📦 Step 2: Installing Python, pip, git..."
echo "=========================================="
sudo apt install python3 python3-pip git -y
echo -e "${GREEN}✓${NC} Requirements installed!"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION"

# Install Python 3.11 if needed
if ! python3 --version | grep -q "3.1[1-9]"; then
    echo -e "${YELLOW}⚠${NC} Python 3.11+ not found. Installing..."
    sudo apt install software-properties-common -y
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install python3.11 python3.11-venv python3-pip -y
    echo -e "${GREEN}✓${NC} Python 3.11 installed!"
fi
echo ""

# Step 3: Clone repository
echo "=========================================="
echo "📥 Step 3: Downloading bot from GitHub..."
echo "=========================================="
cd $HOME_DIR

# Remove old directory if exists
if [ -d "ghgg" ]; then
    echo -e "${YELLOW}⚠${NC} Removing old installation..."
    rm -rf ghgg
fi

git clone https://github.com/mumirubro/ghgg.git
cd ghgg
echo -e "${GREEN}✓${NC} Bot downloaded successfully!"
echo ""

# Step 4: Install Python dependencies
echo "=========================================="
echo "📦 Step 4: Installing Python packages..."
echo "=========================================="
pip3 install -r requirements.txt
echo -e "${GREEN}✓${NC} All packages installed!"
echo ""

# Step 5: Configure bot token
echo "=========================================="
echo "🔑 Step 5: Configure Bot Token"
echo "=========================================="
echo ""
echo "You need your Telegram Bot Token from @BotFather"
echo ""
read -p "Enter your BOT TOKEN: " BOT_TOKEN

# Create .env file
cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_USERNAME=MUMIRU
EOF

echo -e "${GREEN}✓${NC} Bot token configured!"
echo ""

# Step 6: Test bot
echo "=========================================="
echo "🧪 Step 6: Testing bot..."
echo "=========================================="
echo "Starting bot for 5 seconds to test..."
timeout 5 python3 main.py || true
echo ""
echo -e "${GREEN}✓${NC} If you saw 'Bot started successfully!' above, it's working!"
echo ""

# Step 7: Create systemd service
echo "=========================================="
echo "⚙️  Step 7: Setting up 24/7 auto-run..."
echo "=========================================="

# Create log files
sudo touch /var/log/toji-bot.log
sudo touch /var/log/toji-bot-error.log
sudo chmod 666 /var/log/toji-bot.log
sudo chmod 666 /var/log/toji-bot-error.log

# Create systemd service file
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

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable toji-bot
sudo systemctl start toji-bot

echo -e "${GREEN}✓${NC} Service created and started!"
echo ""

# Step 8: Check status
echo "=========================================="
echo "✅ INSTALLATION COMPLETE!"
echo "=========================================="
echo ""
sudo systemctl status toji-bot --no-pager
echo ""
echo "=========================================="
echo "🎉 YOUR BOT IS NOW RUNNING 24/7!"
echo "=========================================="
echo ""
echo "📋 USEFUL COMMANDS:"
echo "-------------------------------------------"
echo "Check status:    sudo systemctl status toji-bot"
echo "View logs:       sudo journalctl -u toji-bot -f"
echo "Restart bot:     sudo systemctl restart toji-bot"
echo "Stop bot:        sudo systemctl stop toji-bot"
echo "Start bot:       sudo systemctl start toji-bot"
echo "-------------------------------------------"
echo ""
echo "📂 Bot location: $HOME_DIR/ghgg"
echo "📝 Logs location: /var/log/toji-bot.log"
echo ""
echo "✅ Done! Test your bot in Telegram now!"
echo ""
