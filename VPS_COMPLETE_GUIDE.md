# 🚀 Complete VPS Deployment Guide - Step by Step

## 📌 What You'll Need

1. **VPS Server** (Ubuntu/Debian recommended)
2. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
3. **Basic knowledge of SSH** (we'll guide you!)

---

## 🎯 PART 1: Prepare Your Code for GitHub

### Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and log in
2. Click the **"+"** icon → **New repository**
3. Name it: `toji-chk-bot` (or any name you like)
4. Set it to **Private** (recommended) or Public
5. Click **Create repository**

### Step 2: Upload Your Code to GitHub

**Option A: Upload via GitHub Website (Easier)**

1. On your repository page, click **"uploading an existing file"**
2. Drag and drop ALL your project files
3. Click **Commit changes**

**Option B: Upload via Git Command Line (if you have git installed locally)**

```bash
# In your project folder
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/toji-chk-bot.git
git push -u origin main
```

✅ Your code is now on GitHub!

---

## 🎯 PART 2: Set Up Your VPS Server

### Step 1: Connect to Your VPS

Open your terminal (or PuTTY on Windows) and connect:

```bash
ssh root@YOUR_VPS_IP
# or
ssh username@YOUR_VPS_IP
```

Enter your password when prompted.

### Step 2: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 3: Install Required Software

```bash
# Install Python 3.11+, pip, and git
sudo apt install python3 python3-pip python3-venv git -y

# Verify installation
python3 --version  # Should show 3.11 or higher
pip3 --version
git --version
```

If Python version is less than 3.11, install Python 3.11:

```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y
```

---

## 🎯 PART 3: Clone and Install Bot

### Step 1: Clone from GitHub

```bash
# Go to home directory
cd ~

# Clone your repository (replace with your GitHub username/repo)
git clone https://github.com/YOUR_USERNAME/toji-chk-bot.git

# Enter the directory
cd toji-chk-bot

# List files to verify
ls -la
```

### Step 2: Install Python Dependencies

```bash
# Install all required packages
pip3 install -r requirements.txt

# Or if you want to use a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit the .env file
nano .env
```

**In the editor, add your bot token:**

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-123456
ADMIN_USERNAME=mumiru
```

**To save:**
- Press `Ctrl + X`
- Press `Y` (yes)
- Press `Enter`

### Step 4: Test the Bot

```bash
# Make the run script executable
chmod +x run_bot.sh

# Test run the bot
./run_bot.sh
```

You should see:
```
🤖 Starting TOJI CHK Bot...
INFO:__main__:Bot started successfully!
```

**Test in Telegram:**
1. Open your bot in Telegram
2. Send `/start`
3. If it responds, it's working! ✅

**Stop the bot** (press `Ctrl + C`)

---

## 🎯 PART 4: Set Up 24/7 Running (systemd)

This will make your bot run automatically even after VPS restart!

### Step 1: Edit the Service File

```bash
# Open the service file template
nano toji-bot.service
```

**Replace these placeholders:**
- `YOUR_USERNAME` → Your VPS username (run `whoami` to check)
- Update paths if needed

**Example for user "ubuntu":**

```ini
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/toji-chk-bot
EnvironmentFile=/home/ubuntu/toji-chk-bot/.env
ExecStart=/usr/bin/python3 /home/ubuntu/toji-chk-bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/toji-bot.log
StandardError=append:/var/log/toji-bot-error.log

[Install]
WantedBy=multi-user.target
```

If you used virtual environment, change `ExecStart` to:
```
ExecStart=/home/ubuntu/toji-chk-bot/venv/bin/python /home/ubuntu/toji-chk-bot/main.py
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

### Step 2: Install the Service

```bash
# Copy service file to systemd directory
sudo cp toji-bot.service /etc/systemd/system/

# Create log files
sudo touch /var/log/toji-bot.log
sudo touch /var/log/toji-bot-error.log
sudo chmod 666 /var/log/toji-bot.log
sudo chmod 666 /var/log/toji-bot-error.log

# Reload systemd
sudo systemctl daemon-reload

# Enable the service (start on boot)
sudo systemctl enable toji-bot

# Start the service
sudo systemctl start toji-bot

# Check status
sudo systemctl status toji-bot
```

You should see:
```
● toji-bot.service - TOJI CHK Telegram Bot
   Loaded: loaded (/etc/systemd/system/toji-bot.service; enabled)
   Active: active (running) since...
```

✅ **Your bot is now running 24/7!**

---

## 🎯 PART 5: Essential Commands

### Check Bot Status

```bash
sudo systemctl status toji-bot
```

### View Live Logs

```bash
# View all logs
sudo journalctl -u toji-bot -f

# View only errors
sudo tail -f /var/log/toji-bot-error.log

# View regular output
sudo tail -f /var/log/toji-bot.log
```

### Restart Bot

```bash
sudo systemctl restart toji-bot
```

### Stop Bot

```bash
sudo systemctl stop toji-bot
```

### Disable Auto-Start

```bash
sudo systemctl disable toji-bot
```

### Update Bot Code

```bash
cd ~/toji-chk-bot
git pull origin main
sudo systemctl restart toji-bot
```

---

## 🎯 PART 6: Configure Bot Access

### For Admin (You)

You can use the bot anywhere! All commands work for you.

### Add Authorized Groups

1. Go to your Telegram bot in private
2. Send: `/addgroup`
3. Bot asks: "Send the group invite link"
4. Send your group invite link (e.g., `https://t.me/+abc123`)
5. Bot asks: "Send the group ID"
6. Get group ID:
   - Add [@userinfobot](https://t.me/userinfobot) to your group
   - It will show the group ID like `-1001234567890`
   - Send this ID to your bot

Now users can use the bot in that group for free!

### Generate Premium Keys (For Private Use)

```
/key 10 30
```

This creates 10 premium keys valid for 30 days. Users redeem with `/redeem <key>`

---

## 🔐 Security Best Practices

### 1. Use Firewall

```bash
# Install UFW
sudo apt install ufw -y

# Allow SSH (IMPORTANT - don't lock yourself out!)
sudo ufw allow ssh

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 2. Keep Bot Updated

```bash
cd ~/toji-chk-bot
git pull
sudo systemctl restart toji-bot
```

### 3. Regular Backups

```bash
# Backup your data files
cp ~/toji-chk-bot/users.json ~/backup_users_$(date +%Y%m%d).json
cp ~/toji-chk-bot/access_control.json ~/backup_access_$(date +%Y%m%d).json
```

### 4. Monitor Logs

```bash
# Check for errors daily
sudo journalctl -u toji-bot --since "24 hours ago" | grep -i error
```

---

## 🆘 Troubleshooting

### Bot Won't Start

**Check logs:**
```bash
sudo journalctl -u toji-bot -n 50
```

**Common issues:**

1. **Wrong Bot Token**
   - Edit `.env` file and check token
   - Get new token from @BotFather if needed

2. **Python Version Too Old**
   ```bash
   python3 --version  # Must be 3.11+
   ```

3. **Missing Dependencies**
   ```bash
   cd ~/toji-chk-bot
   pip3 install -r requirements.txt
   ```

4. **Permission Issues**
   ```bash
   sudo chown -R $USER:$USER ~/toji-chk-bot
   chmod +x ~/toji-chk-bot/run_bot.sh
   ```

### Bot Keeps Crashing

```bash
# View crash logs
sudo journalctl -u toji-bot --since "1 hour ago"

# Check error log
sudo tail -100 /var/log/toji-bot-error.log
```

### Can't Connect to VPS

```bash
# From your local machine
ping YOUR_VPS_IP

# Check if SSH is running on VPS (if you have console access)
sudo systemctl status ssh
```

### Users Can't Use Bot

1. **In Groups:**
   - Make sure you added the group with `/addgroup`
   - Verify group ID matches exactly
   - Make bot is admin in the group

2. **In Private:**
   - User needs premium key
   - Use `/redeem <key>` to activate

---

## 📊 Quick Reference

| Command | Description |
|---------|-------------|
| `sudo systemctl start toji-bot` | Start bot |
| `sudo systemctl stop toji-bot` | Stop bot |
| `sudo systemctl restart toji-bot` | Restart bot |
| `sudo systemctl status toji-bot` | Check status |
| `sudo journalctl -u toji-bot -f` | Live logs |
| `cd ~/toji-chk-bot && git pull` | Update code |

---

## ✅ You're All Set!

Your bot is now:
- ✅ Running 24/7
- ✅ Auto-restarts on crash
- ✅ Starts automatically after VPS reboot
- ✅ Logging all activity
- ✅ Secure and production-ready

**Need help?** Check the logs first, then review this guide!

🎉 **Happy Bot Running!**
