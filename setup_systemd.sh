#!/bin/bash

echo "════════════════════════════════════════"
echo "   🚀 TOJI BOT - systemd Setup"
echo "════════════════════════════════════════"
echo ""

# Get current user and directory
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

echo "📋 Configuration:"
echo "  User: $CURRENT_USER"
echo "  Directory: $CURRENT_DIR"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please run ./install.sh first and configure your .env file"
    exit 1
fi

# Check if BOT_TOKEN is set in .env
if ! grep -q "BOT_TOKEN=" .env || grep -q "your_bot_token_here" .env; then
    echo "❌ Error: BOT_TOKEN not configured in .env!"
    echo "Please edit .env and add your bot token from @BotFather"
    exit 1
fi

echo "✅ .env file found and configured"
echo ""

# Create service file
echo "📝 Creating systemd service file..."

cat > toji-bot.service << EOF
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
EnvironmentFile=$CURRENT_DIR/.env
ExecStart=/usr/bin/python3 $CURRENT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/toji-bot.log
StandardError=append:/var/log/toji-bot-error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created"
echo ""

# Install service
echo "📦 Installing service (requires sudo)..."

sudo cp toji-bot.service /etc/systemd/system/
sudo touch /var/log/toji-bot.log
sudo touch /var/log/toji-bot-error.log
sudo chmod 666 /var/log/toji-bot.log
sudo chmod 666 /var/log/toji-bot-error.log

echo "✅ Service installed"
echo ""

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "⚡ Enabling service..."
sudo systemctl enable toji-bot

# Start service
echo "🚀 Starting service..."
sudo systemctl start toji-bot

# Wait a moment
sleep 2

# Check status
echo ""
echo "════════════════════════════════════════"
echo "   📊 Service Status"
echo "════════════════════════════════════════"
sudo systemctl status toji-bot --no-pager

echo ""
echo "════════════════════════════════════════"
echo "   ✅ Setup Complete!"
echo "════════════════════════════════════════"
echo ""
echo "📋 Useful Commands:"
echo "  Check status:  sudo systemctl status toji-bot"
echo "  View logs:     sudo journalctl -u toji-bot -f"
echo "  Restart bot:   sudo systemctl restart toji-bot"
echo "  Stop bot:      sudo systemctl stop toji-bot"
echo ""
echo "🎉 Your bot is now running 24/7!"
echo ""
