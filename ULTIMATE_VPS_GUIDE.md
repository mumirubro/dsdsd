# 🚀 ULTIMATE A-Z VPS DEPLOYMENT GUIDE

**Follow this guide STEP BY STEP to run your bot 24/7 on a VPS**

---

## 📋 WHAT YOU NEED BEFORE STARTING

1. ✅ A VPS server (Ubuntu/Debian) - Get from DigitalOcean, Vultr, Linode, etc.
2. ✅ Your Telegram Bot Token from [@BotFather](https://t.me/botfather)
3. ✅ A GitHub account
4. ✅ Your VPS IP address and password

---

# 🎯 PART 1: UPLOAD YOUR BOT TO GITHUB

## Step 1.1: Create GitHub Repository

1. Go to **https://github.com/new**
2. Repository name: `toji-chk-bot` (or any name you want)
3. **Make it PRIVATE** (to protect your code)
4. Click **"Create repository"**

## Step 1.2: Upload Files to GitHub

**EASIEST WAY (Upload via GitHub Website):**

1. Download ALL your bot files to your computer
2. Go to your repository on GitHub
3. Click **"uploading an existing file"** link
4. Drag and drop ALL files EXCEPT:
   - `.env` file (DON'T upload this - it has your secret token!)
   - `users.json`, `access_control.json` (user data files)
5. Click **"Commit changes"**

**ALTERNATIVE (Using Git Command Line - if you know how):**

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/toji-chk-bot.git
git push -u origin main
```

✅ **Done!** Your code is on GitHub!

---

# 🎯 PART 2: SET UP YOUR VPS

## Step 2.1: Connect to VPS

Open Terminal (Mac/Linux) or PuTTY (Windows):

```bash
ssh root@YOUR_VPS_IP
```

Or if you have a username:

```bash
ssh username@YOUR_VPS_IP
```

Type your password (you won't see it typing - that's normal!)

## Step 2.2: Update VPS System

Copy and paste this command:

```bash
sudo apt update && sudo apt upgrade -y
```

Wait for it to finish (1-3 minutes).

## Step 2.3: Install Python, Pip, and Git

Copy and paste this:

```bash
sudo apt install python3 python3-pip git -y
```

Check if installation worked:

```bash
python3 --version
```

Should show version 3.11 or higher. If lower, run:

```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y
```

---

# 🎯 PART 3: DOWNLOAD BOT FROM GITHUB TO VPS

## Step 3.1: Clone Your Repository

Replace `YOUR_USERNAME` with your GitHub username:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git
```

**If repository is PRIVATE**, GitHub will ask for credentials:
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your password)
  - Get token from: https://github.com/settings/tokens
  - Click "Generate new token (classic)"
  - Check "repo" permission
  - Copy the token and use it as password

Enter the bot directory:

```bash
cd toji-chk-bot
```

Check files are there:

```bash
ls
```

You should see: `main.py`, `requirements.txt`, `README.md`, etc.

---

# 🎯 PART 4: INSTALL BOT DEPENDENCIES

## Step 4.1: Install All Python Packages

```bash
pip3 install -r requirements.txt
```

Wait 1-2 minutes for installation to complete.

---

# 🎯 PART 5: CONFIGURE BOT TOKEN

## Step 5.1: Create .env File

```bash
nano .env
```

## Step 5.2: Add Your Bot Token

Type this (replace with YOUR actual bot token):

```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_USERNAME=mumiru
```

**How to get your bot token:**
1. Open Telegram
2. Search `@BotFather`
3. Send `/mybots`
4. Select your bot
5. Click "API Token"
6. Copy it

## Step 5.3: Save the File

- Press `Ctrl + X`
- Press `Y` (yes to save)
- Press `Enter`

---

# 🎯 PART 6: TEST THE BOT

## Step 6.1: Run Test

```bash
python3 main.py
```

You should see:

```
INFO - Bot started successfully!
```

## Step 6.2: Test in Telegram

1. Open Telegram
2. Find your bot
3. Send `/start`
4. If bot responds → **IT WORKS!** ✅

## Step 6.3: Stop the Test

Press `Ctrl + C` to stop the bot.

---

# 🎯 PART 7: SET UP 24/7 AUTO-RUN (systemd)

This makes your bot:
- ✅ Run 24/7 non-stop
- ✅ Auto-restart if it crashes
- ✅ Auto-start when VPS reboots

## Step 7.1: Find Your Username

```bash
whoami
```

Remember this username (e.g., `root`, `ubuntu`, `admin`, etc.)

## Step 7.2: Create Service File

```bash
sudo nano /etc/systemd/system/toji-bot.service
```

## Step 7.3: Paste This Configuration

**IMPORTANT:** Replace `YOUR_USERNAME` with the username from Step 7.1

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

**If your username is `root`, use:**
- WorkingDirectory=`/root/toji-chk-bot`
- EnvironmentFile=`/root/toji-chk-bot/.env`
- ExecStart=`/usr/bin/python3 /root/toji-chk-bot/main.py`

Save file: `Ctrl+X` → `Y` → `Enter`

## Step 7.4: Create Log Files

```bash
sudo touch /var/log/toji-bot.log
sudo touch /var/log/toji-bot-error.log
sudo chmod 666 /var/log/toji-bot.log
sudo chmod 666 /var/log/toji-bot-error.log
```

## Step 7.5: Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable toji-bot
sudo systemctl start toji-bot
```

## Step 7.6: Check Status

```bash
sudo systemctl status toji-bot
```

You should see:
```
● toji-bot.service - TOJI CHK Telegram Bot
   Active: active (running)
```

✅ **YOUR BOT IS NOW RUNNING 24/7!** 🎉

---

# 🎯 PART 8: IMPORTANT COMMANDS

## Check if Bot is Running

```bash
sudo systemctl status toji-bot
```

## View Live Logs (What Bot is Doing)

```bash
sudo journalctl -u toji-bot -f
```

Press `Ctrl+C` to exit logs.

## Restart Bot (After Making Changes)

```bash
sudo systemctl restart toji-bot
```

## Stop Bot

```bash
sudo systemctl stop toji-bot
```

## Start Bot

```bash
sudo systemctl start toji-bot
```

## View Error Logs

```bash
sudo tail -50 /var/log/toji-bot-error.log
```

---

# 🎯 PART 9: UPDATE BOT (When You Make Changes)

## Step 9.1: Update Code on GitHub

1. Make changes to your code locally
2. Upload to GitHub (or use `git push`)

## Step 9.2: Update on VPS

```bash
cd ~/toji-chk-bot
sudo systemctl stop toji-bot
git pull origin main
sudo systemctl start toji-bot
sudo systemctl status toji-bot
```

---

# 🆘 TROUBLESHOOTING

## Problem: Bot Won't Start

**Check logs:**

```bash
sudo journalctl -u toji-bot -n 50
```

**Common fixes:**

1. **Wrong bot token** - Edit .env file:
   ```bash
   nano .env
   ```

2. **Python version too old:**
   ```bash
   python3 --version  # Must be 3.11+
   ```

3. **Missing packages:**
   ```bash
   cd ~/toji-chk-bot
   pip3 install -r requirements.txt
   ```

## Problem: Bot Keeps Crashing

View crash details:

```bash
sudo journalctl -u toji-bot --since "1 hour ago"
```

Or check error log:

```bash
sudo tail -100 /var/log/toji-bot-error.log
```

## Problem: Can't Clone from GitHub (Private Repo)

Create GitHub token:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select "repo" permission
4. Copy token

Use token when cloning:

```bash
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/toji-chk-bot.git
```

## Problem: Permission Denied

Fix permissions:

```bash
sudo chown -R $USER:$USER ~/toji-chk-bot
chmod +x ~/toji-chk-bot/*.sh
```

---

# 🔐 SECURITY TIPS

## 1. Enable Firewall

```bash
sudo apt install ufw -y
sudo ufw allow ssh
sudo ufw enable
```

## 2. Never Share These:
- ❌ Your bot token
- ❌ Your .env file
- ❌ Your VPS password

## 3. Regular Backups

```bash
cp ~/toji-chk-bot/users.json ~/backup_$(date +%Y%m%d).json
```

---

# ✅ QUICK REFERENCE

| What | Command |
|------|---------|
| **Start bot** | `sudo systemctl start toji-bot` |
| **Stop bot** | `sudo systemctl stop toji-bot` |
| **Restart bot** | `sudo systemctl restart toji-bot` |
| **Check status** | `sudo systemctl status toji-bot` |
| **Live logs** | `sudo journalctl -u toji-bot -f` |
| **Error logs** | `sudo tail -50 /var/log/toji-bot-error.log` |
| **Update code** | `cd ~/toji-chk-bot && git pull` |

---

# 🎉 CONGRATULATIONS!

Your bot is now:
- ✅ Running 24/7 on VPS
- ✅ Auto-restarts if it crashes
- ✅ Starts automatically when VPS reboots
- ✅ Logging everything for debugging
- ✅ Ready for production use

**Questions? Check the logs first!**

```bash
sudo journalctl -u toji-bot -f
```

---

**Made with ❤️ for TOJI CHK Bot**

**Support:** @MUMIRU
