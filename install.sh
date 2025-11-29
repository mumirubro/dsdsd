#!/bin/bash

echo "════════════════════════════════════════"
echo "   🤖 TOJI CHK BOT - Auto Installer"
echo "════════════════════════════════════════"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.11 or higher first:"
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-pip -y"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Install pip if not available
if ! command -v pip3 &> /dev/null; then
    echo "📦 Installing pip..."
    sudo apt install python3-pip -y
fi

# Install required packages
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies!"
    echo "Trying alternative installation method..."
    pip3 install python-telegram-bot requests python-dotenv aiohttp fake-useragent beautifulsoup4 faker
fi

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your bot token!"
    echo ""
    echo "Please run:"
    echo "  nano .env"
    echo ""
    echo "Replace 'your_bot_token_here' with your actual token from @BotFather"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "════════════════════════════════════════"
echo "   ✅ Installation Complete!"
echo "════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo "  1. Edit .env file: nano .env"
echo "  2. Add your bot token from @BotFather"
echo "  3. Run the bot: ./run_bot.sh"
echo ""
echo "Or use systemd for production (see VPS_DEPLOYMENT.md)"
echo ""
