# ⚡ Quick Start Guide - VPS Deployment

## 🎯 Super Fast Setup (5 Minutes)

### 1️⃣ Prepare on Local Computer

1. **Upload to GitHub:**
   - Go to [GitHub.com](https://github.com) → New Repository
   - Name: `toji-chk-bot`
   - Upload all your project files
   - Copy the repository URL

### 2️⃣ On Your VPS

**Connect to VPS:**
```bash
ssh root@YOUR_VPS_IP
```

**Install & Run:**
```bash
# Install requirements
sudo apt update && sudo apt install python3 python3-pip git -y

# Clone your repo (replace with your GitHub URL)
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git
cd toji-chk-bot

# Install dependencies
pip3 install -r requirements.txt

# Configure bot token
cp .env.example .env
nano .env  # Add your BOT_TOKEN from @BotFather

# Test the bot
chmod +x run_bot.sh
./run_bot.sh
```

If bot responds to `/start` in Telegram, press `Ctrl+C` to stop.

**Set up 24/7 running:**
```bash
# Run the auto-setup script
chmod +x setup_systemd.sh
./setup_systemd.sh
```

**Done! ✅** Your bot is now running 24/7!

---

## 🔧 Essential Commands

```bash
# Check if bot is running
sudo systemctl status toji-bot

# View live logs
sudo journalctl -u toji-bot -f

# Restart bot
sudo systemctl restart toji-bot

# Stop bot
sudo systemctl stop toji-bot
```

---

## 📚 Need More Details?

See **VPS_COMPLETE_GUIDE.md** for comprehensive step-by-step instructions.

---

## 🆘 Quick Troubleshooting

**Bot won't start?**
```bash
# Check what went wrong
sudo journalctl -u toji-bot -n 50
```

**Update bot code:**
```bash
cd ~/toji-chk-bot
git pull
sudo systemctl restart toji-bot
```

**Check if token is set:**
```bash
cat .env | grep BOT_TOKEN
```

---

## 🎉 First Steps After Setup

1. **Register yourself:**
   - Send `/start` to your bot
   - Send `/register`

2. **Add your group:**
   - Send `/addgroup`
   - Follow the prompts

3. **Generate premium keys:**
   - Send `/key 5 30` (creates 5 keys, valid 30 days)

**You're ready to go! 🚀**
