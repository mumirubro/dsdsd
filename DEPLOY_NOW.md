# 🚀 COPY-PASTE DEPLOYMENT GUIDE FOR MUMIRU

## STEP 1: SSH Into Your VPS

```bash
ssh root@YOUR_VPS_IP
```
Replace `YOUR_VPS_IP` with your actual VPS IP address (example: 123.45.67.89)

---

## STEP 2: Install Python & Git

```bash
apt update && apt upgrade -y && apt install python3 python3-pip git nano -y
```

---

## STEP 3: Clone Your Bot

```bash
cd /home && git clone https://github.com/mumirubro/tofdgdg.git && cd tofdgdg
```

---

## STEP 4: Install All Requirements (One Command)

```bash
pip3 install python-telegram-bot>=20.7 requests>=2.31.0 python-dotenv>=1.0.0 aiohttp>=3.9.0 fake-useragent>=1.4.0 beautifulsoup4>=4.12.0 faker>=22.0.0
```

---

## STEP 5: Create Environment File

```bash
nano .env
```

Paste this line (replace `YOUR_BOT_TOKEN_HERE` with your actual bot token from @BotFather):
```
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

---

## STEP 6: Test Run (Quick Check)

```bash
python3 main.py
```

If bot starts successfully (you'll see "Bot started successfully"), press `Ctrl+C` to stop it. Now let's set it up to run 24/7.

---

## STEP 7: Create 24/7 Service File

```bash
nano /etc/systemd/system/toji-bot.service
```

**COPY-PASTE THIS ENTIRE BLOCK** (already customized for MUMIRU):

```ini
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/tofdgdg
EnvironmentFile=/home/tofdgdg/.env
ExecStart=/usr/bin/python3 /home/tofdgdg/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

---

## STEP 8: Start Bot 24/7 (One Command)

```bash
systemctl daemon-reload && systemctl enable toji-bot && systemctl start toji-bot
```

---

## STEP 9: Check Bot Status

```bash
systemctl status toji-bot
```

You should see **"Active: active (running)"** in green! Press `Q` to exit.

---

## ✅ DONE! Bot is Running 24/7

Your bot will:
- ✅ Run forever (24/7)
- ✅ Auto-restart if it crashes
- ✅ Auto-start on VPS reboot

---

# 📱 USEFUL COMMANDS (COPY-PASTE READY)

## Check if bot is running:
```bash
systemctl status toji-bot
```

## View live bot logs:
```bash
journalctl -u toji-bot -f
```
Press `Ctrl+C` to stop viewing logs

## Restart bot:
```bash
systemctl restart toji-bot
```

## Stop bot:
```bash
systemctl stop toji-bot
```

## View last 100 log lines:
```bash
journalctl -u toji-bot -n 100
```

---

# 🔄 UPDATE BOT LATER

When you make changes on Replit and push to GitHub, run these on VPS:

```bash
cd /home/tofdgdg && git pull && systemctl restart toji-bot
```

Then check if it's running:
```bash
systemctl status toji-bot
```

---

# 🆘 TROUBLESHOOTING

**Bot won't start? See what went wrong:**
```bash
journalctl -u toji-bot -n 50
```

**Check if BOT_TOKEN is set correctly:**
```bash
cat /home/tofdgdg/.env
```

**Check Python version (need 3.8+):**
```bash
python3 --version
```

**Reinstall all requirements:**
```bash
cd /home/tofdgdg && pip3 install -r requirements.txt --upgrade && systemctl restart toji-bot
```

**Bot still not working? Check logs in real-time:**
```bash
journalctl -u toji-bot -f
```

---

# 📝 COMPLETE ONE-LINE INSTALL (Advanced)

After cloning repo, run this all at once:

```bash
cd /home/tofdgdg && pip3 install -r requirements.txt && nano .env
```

Add your BOT_TOKEN, save (Ctrl+X, Y, Enter), then run:

```bash
cat > /etc/systemd/system/toji-bot.service << 'EOF'
[Unit]
Description=TOJI CHK Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/tofdgdg
EnvironmentFile=/home/tofdgdg/.env
ExecStart=/usr/bin/python3 /home/tofdgdg/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl enable toji-bot && systemctl start toji-bot && systemctl status toji-bot
```

---

🎉 **Your TOJI bot is now running 24/7 on VPS!**

Test it by messaging your bot on Telegram: `/start`

**Repository:** https://github.com/mumirubro/tofdgdg
**Admin:** @MUMIRU
