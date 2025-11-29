# 🚀 START HERE - Deploy Your Bot to VPS

## 📌 What You Have Now

✅ **requirements.txt** - All dependencies listed  
✅ **install.sh** - Auto-installer script  
✅ **setup_systemd.sh** - Auto-setup for 24/7 running  
✅ **toji-bot.service** - Service configuration  
✅ **.env.example** - Configuration template  
✅ **Complete guides** - Step-by-step documentation  

**Everything is ready to deploy!**

---

## 🎯 YOUR DEPLOYMENT PATH (Choose One)

### ⚡ Option 1: SUPER QUICK (5 Minutes) ⚡

**Perfect if you just want it working NOW!**

👉 **Follow: QUICK_START.md**

**What you'll do:**
1. Upload to GitHub (2 min)
2. Clone on VPS (1 min)
3. Run automated setup (2 min)
4. Done! ✅

---

### 📚 Option 2: DETAILED GUIDE (15 Minutes)

**Perfect if you want to understand everything!**

👉 **Follow: VPS_COMPLETE_GUIDE.md**

**What you'll learn:**
- Complete GitHub setup
- VPS preparation
- Security best practices
- Troubleshooting
- Maintenance commands

---

## 🎬 What Happens Next

### STEP 1: Upload to GitHub

1. Go to [github.com](https://github.com)
2. Create new repository: `toji-chk-bot`
3. Upload ALL your project files
4. Copy the repository URL

**✅ Your code is now on GitHub!**

### STEP 2: On Your VPS

**Connect:**
```bash
ssh root@YOUR_VPS_IP
```

**Quick Setup:**
```bash
# Install basics
sudo apt update && sudo apt install python3 python3-pip git -y

# Clone your repo (use YOUR GitHub URL)
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git
cd toji-chk-bot

# Install dependencies
pip3 install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your BOT_TOKEN

# Setup 24/7 running (automated!)
chmod +x setup_systemd.sh
./setup_systemd.sh
```

**✅ Your bot is now running 24/7!**

---

## 🔑 Get Your Bot Token

Before you start, get your Telegram bot token:

1. Open Telegram
2. Message [@BotFather](https://t.me/BotFather)
3. Send `/newbot` (or use existing bot with `/mybots`)
4. Follow the prompts
5. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Save this token - you'll need it in `.env` file!**

---

## 📁 Files Explained

| File | What It Does |
|------|-------------|
| **QUICK_START.md** | ⚡ Fast 5-minute setup |
| **VPS_COMPLETE_GUIDE.md** | 📚 Detailed A-Z guide |
| **README_DEPLOYMENT.md** | 📦 Package overview |
| **requirements.txt** | 📋 Python packages needed |
| **install.sh** | 🔧 Installs dependencies |
| **setup_systemd.sh** | 🚀 Sets up 24/7 running |
| **run_bot.sh** | ▶️ Simple test runner |

---

## ✅ Quick Test Checklist

After deployment, verify:

- [ ] Bot responds to `/start` in Telegram
- [ ] Command `sudo systemctl status toji-bot` shows "active (running)"
- [ ] Logs are being written: `sudo journalctl -u toji-bot -f`
- [ ] Bot restarts after VPS reboot (test it!)

**All green?** Perfect! 🎉

---

## 🎯 Essential Commands

```bash
# Check if bot is running
sudo systemctl status toji-bot

# View live logs
sudo journalctl -u toji-bot -f

# Restart bot
sudo systemctl restart toji-bot

# Update bot code
cd ~/toji-chk-bot && git pull && sudo systemctl restart toji-bot
```

---

## 🆘 Something Wrong?

**Check the logs:**
```bash
sudo journalctl -u toji-bot -n 50
```

**Common fixes:**
- Bot token wrong? Edit `.env` file
- Dependencies missing? Run `pip3 install -r requirements.txt`
- Permission issues? Run `sudo chown -R $USER:$USER ~/toji-chk-bot`

---

## 🎓 Learning Path

1. **Just want it working?** → Follow **QUICK_START.md**
2. **Want to understand?** → Read **VPS_COMPLETE_GUIDE.md**
3. **Need command reference?** → Check **README_DEPLOYMENT.md**

---

## 🎉 You're Ready!

Pick your path:
- ⚡ **Quick Setup** → QUICK_START.md
- 📚 **Detailed Guide** → VPS_COMPLETE_GUIDE.md

Both paths lead to the same destination: **Your bot running 24/7 on VPS!**

**Let's do this! 🚀**
