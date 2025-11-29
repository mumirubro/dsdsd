# 📦 GitHub + VPS Deployment Guide

Complete step-by-step guide to deploy your bot from GitHub to VPS.

---

## 🎯 Step 1: Upload to GitHub

### 1.1 Create a New Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `toji-chk-bot` (or your preferred name)
3. Description: "Advanced Telegram bot for card checking and account validation"
4. **Important:** Choose **PRIVATE** repository (to protect your setup)
5. Don't initialize with README (we already have one)
6. Click "Create repository"

### 1.2 Push Your Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit your code
git commit -m "Initial commit - TOJI CHK Bot"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/toji-chk-bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

✅ Your code is now on GitHub!

---

## 🚀 Step 2: Deploy to VPS

### 2.1 Get a VPS

Recommended providers:
- **DigitalOcean** - $4-6/month
- **Vultr** - $3.50-6/month  
- **Linode** - $5/month
- **Hetzner** - €3.50/month
- **Contabo** - €4/month

Requirements:
- OS: Ubuntu 20.04+ or Debian 11+
- RAM: 512MB minimum (1GB recommended)
- Storage: 10GB minimum

### 2.2 Connect to Your VPS

```bash
ssh root@YOUR_VPS_IP
# or
ssh username@YOUR_VPS_IP
```

### 2.3 Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and Git
sudo apt install python3 python3-pip git -y

# Verify installations
python3 --version  # Should be 3.11 or higher
git --version
```

### 2.4 Clone Your Repository

```bash
# Clone from GitHub (for public repos)
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git

# For private repos, use SSH or token
# Option 1: With SSH key (recommended)
git clone git@github.com:YOUR_USERNAME/toji-chk-bot.git

# Option 2: With personal access token
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/toji-chk-bot.git

# Navigate to directory
cd toji-chk-bot
```

### 2.5 Run One-Command Installation

```bash
# Make installer executable
chmod +x install.sh

# Run automated installer
./install.sh
```

This will:
- ✅ Check Python version
- ✅ Install all dependencies
- ✅ Create .env file

### 2.6 Configure Your Bot Token

```bash
# Edit .env file
nano .env
```

Replace `your_bot_token_here` with your actual bot token from @BotFather:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_USERNAME=mumiru
```

**To get your bot token:**
1. Open Telegram
2. Search for @BotFather
3. Send `/mybots`
4. Select your bot
5. Click "API Token"

Save the file: `Ctrl+X` → `Y` → `Enter`

### 2.7 Start Your Bot

```bash
# Start the bot
./run_bot.sh
```

✅ **Your bot is now running!**

Press `Ctrl+C` to stop.

---

## 🔄 Step 3: Production Setup (Keep Bot Running 24/7)

For production, use systemd to run your bot as a service:

### 3.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/toji-bot.service
```

Paste this configuration:

```ini
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/toji-chk-bot
EnvironmentFile=/home/YOUR_USERNAME/toji-chk-bot/.env
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/toji-bot.log
StandardError=append:/var/log/toji-bot-error.log

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `YOUR_USERNAME` with your actual username (run `whoami` to check)

### 3.2 Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable toji-bot

# Start the bot
sudo systemctl start toji-bot

# Check status
sudo systemctl status toji-bot
```

✅ Your bot now runs 24/7 and auto-restarts on crashes!

### 3.3 Useful Commands

```bash
# Check if bot is running
sudo systemctl status toji-bot

# Stop bot
sudo systemctl stop toji-bot

# Restart bot
sudo systemctl restart toji-bot

# View live logs
sudo journalctl -u toji-bot -f

# View recent logs
sudo journalctl -u toji-bot -n 100

# View error log
tail -f /var/log/toji-bot-error.log
```

---

## 🔄 Step 4: Updating Your Bot

When you make changes and want to update:

```bash
# SSH to VPS
ssh username@YOUR_VPS_IP

# Navigate to bot directory
cd toji-chk-bot

# Stop the bot
sudo systemctl stop toji-bot

# Pull latest changes
git pull origin main

# Restart the bot
sudo systemctl start toji-bot

# Check status
sudo systemctl status toji-bot
```

---

## 🔐 Security Best Practices

### ✅ DO:
- ✅ Use environment variables for tokens (never hardcode)
- ✅ Keep your repository PRIVATE on GitHub
- ✅ Use SSH keys for GitHub authentication
- ✅ Regularly update your VPS: `sudo apt update && sudo apt upgrade`
- ✅ Use a firewall: `sudo ufw enable && sudo ufw allow 22`
- ✅ Regular backups of `users.json` and `access_control.json`

### ❌ DON'T:
- ❌ Never commit .env file to GitHub
- ❌ Never share your bot token publicly
- ❌ Never run as root user in production
- ❌ Never expose unnecessary ports

---

## 🆘 Troubleshooting

### Bot won't start

```bash
# Check if BOT_TOKEN is set
cat .env | grep BOT_TOKEN

# Check Python version
python3 --version  # Must be 3.11+

# Check logs
sudo journalctl -u toji-bot -n 50

# Test manually
./run_bot.sh
```

### Can't clone from GitHub

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH keys → New SSH key
```

### Dependencies won't install

```bash
# Try pip3 directly
pip3 install --user -r requirements.txt

# Or install individually
pip3 install --user python-telegram-bot requests python-dotenv
```

---

## 📊 File Structure

```
toji-chk-bot/
├── main.py                 # Main bot file
├── access_control.py       # Access control system
├── requirements.txt        # Python dependencies
├── install.sh             # Auto-installer script
├── run_bot.sh             # Bot startup script
├── .env                   # Your bot token (NOT in git)
├── .env.example           # Template for .env
├── .gitignore             # Files to exclude from git
├── VPS_DEPLOYMENT.md      # This guide
├── README.md              # Project documentation
└── gates/                 # Payment gateway modules
    ├── stripe/
    ├── shopify/
    └── braintree/
```

---

## 🎉 Success Checklist

- [ ] Bot token obtained from @BotFather
- [ ] Code pushed to GitHub
- [ ] VPS set up and accessible
- [ ] Repository cloned to VPS
- [ ] Dependencies installed via `install.sh`
- [ ] .env file configured with token
- [ ] Bot tested with `./run_bot.sh`
- [ ] Systemd service configured (optional but recommended)
- [ ] Bot running 24/7

---

## 📞 Support

If you encounter issues:
1. Check logs: `sudo journalctl -u toji-bot -f`
2. Verify .env file has correct token
3. Ensure Python 3.11+ is installed
4. Check firewall isn't blocking connections

**Your bot is now deployed and running on VPS! 🚀**
