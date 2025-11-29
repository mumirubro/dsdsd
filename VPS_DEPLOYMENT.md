# 🚀 VPS Deployment Guide - Complete Setup

## 📋 Prerequisites

- Ubuntu/Debian VPS (20.04+ recommended)
- Python 3.11 or higher
- Git installed
- Your Telegram Bot Token from @BotFather

---

## 🎯 Method 1: Quick Installation (Recommended)

### Step 1: Clone from GitHub

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Clone the repository
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git
cd toji-chk-bot
```

### Step 2: Run Auto-Installer

```bash
# Make installer executable
chmod +x install.sh

# Run automated installation
./install.sh
```

This will:
- Check for Python 3
- Install all dependencies from requirements.txt
- Create .env file from template

### Step 3: Configure Bot Token

```bash
# Edit .env file
nano .env

# Replace this line:
# BOT_TOKEN=your_bot_token_here
# With your actual token:
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

### Step 4: Start the Bot

```bash
# Run the bot
./run_bot.sh
```

✅ Your bot is now running!

---

## 🔄 Method 2: Production Setup with systemd (Auto-restart)

For production use, set up the bot to run 24/7 and auto-restart on crashes:

### Create systemd service file:

```bash
sudo nano /etc/systemd/system/toji-bot.service
```

Paste this configuration (update paths and token):

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

### Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable toji-bot
sudo systemctl start toji-bot
sudo systemctl status toji-bot
```

### Useful systemd commands:

```bash
# Check bot status
sudo systemctl status toji-bot

# Stop the bot
sudo systemctl stop toji-bot

# Restart the bot
sudo systemctl restart toji-bot

# View logs
sudo journalctl -u toji-bot -f

# View error logs
tail -f /var/log/toji-bot-error.log
```

---

## 📦 Manual Installation (Alternative)

If auto-installer fails:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip git -y

# Clone repository
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git
cd toji-chk-bot

# Install dependencies manually
pip3 install python-telegram-bot>=20.7
pip3 install requests>=2.31.0
pip3 install python-dotenv>=1.0.0
pip3 install aiohttp>=3.9.0
pip3 install fake-useragent>=1.4.0
pip3 install beautifulsoup4>=4.12.0
pip3 install faker>=22.0.0

# Create and edit .env file
cp .env.example .env
nano .env
# Add your bot token

# Run the bot
chmod +x run_bot.sh
./run_bot.sh
```

### Step 4: Configure Admin Access
The bot is already set up with admin username `mumiru`. You can use all commands anywhere!

---

## 🎯 How to Use the Bot

### For Admins:

1. **Add Authorized Groups**
   ```
   /addgroup
   Bot asks: "Send group invite link"
   You send: https://t.me/+abc123
   Bot asks: "Send group ID"
   You send: -1001234567890
   ```

2. **Generate Premium Keys**
   ```
   /key 5 30
   (Creates 5 keys valid for 30 days)
   ```

3. **You can use bot ANYWHERE** - private or any group!

### For Regular Users:

1. **In Authorized Groups ONLY**
   - Users can use all bot commands in groups you added via /addgroup
   
2. **In Private (Need Premium)**
   ```
   /redeem premium_abc123xyz456
   (After redeeming, they can use bot in private for the key's duration)
   ```

3. **If Not Authorized:**
   - Bot will say "Contact @MUMIRU to use bot in this group"
   - Or "You can't use this bot in private!"

---

## 🔧 Available Commands

### Admin Commands:
- `/addgroup` - Add authorized group (conversation flow)
- `/key <quantity> <days>` - Generate premium keys
- All gate commands work everywhere

### User Commands (in authorized groups or private with premium):
- `/start` - Start bot
- `/register` - Register account
- `/cmd` - Show commands menu
- `/chk` - Check Stripe card
- `/mchk` - Mass check Stripe (up to 10)
- `/sh` - Check Shopify card
- `/msh` - Mass check Shopify
- `/br` - Check Braintree card
- `/cr` - Check Crunchyroll account
- `/redeem <key>` - Redeem premium key
- And many more...

---

## 🔐 Security Notes

✅ **Bot token is stored as environment variable** (not in code)
✅ **Access control enforces group-only usage**
✅ **Premium system for private access**
✅ **Admin can operate anywhere**

**IMPORTANT:** If you ever share your code publicly (GitHub, etc.), the environment variable approach ensures your token stays secret!

---

## 📊 Files Created by Bot

- `access_control.json` - Stores authorized groups, keys, premium users
- `users.json` - User registrations
- `bot_settings.json` - Stripe settings
- `bot_data.json` - Braintree/Shopify settings

These files are automatically created when needed.

---

## 🆘 Troubleshooting

**Bot won't start?**
- Make sure BOT_TOKEN is set: `echo $BOT_TOKEN`
- Check Python version: `python --version` (need 3.11+)

**Users can't use bot?**
- Did you add the group with `/addgroup`?
- Check group ID matches exactly

**Need to rotate token?**
1. Go to @BotFather → /mybots → Your Bot → Revoke Token
2. Get new token
3. Update environment variable with new token
4. Restart bot

---

🎉 **Your bot is production-ready!**
