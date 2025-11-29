# 🤖 TOJI CHK Bot - VPS Deployment Package

## 📦 What's Included

This package contains everything you need to deploy your Telegram bot to a VPS and run it 24/7!

### 📁 Files

| File | Description |
|------|-------------|
| `requirements.txt` | All Python dependencies |
| `install.sh` | Automated installer |
| `run_bot.sh` | Simple bot runner |
| `setup_systemd.sh` | **Auto-setup 24/7 service** |
| `toji-bot.service` | systemd service template |
| `.env.example` | Environment configuration template |
| `QUICK_START.md` | **⚡ 5-minute setup guide** |
| `VPS_COMPLETE_GUIDE.md` | **📚 Detailed A-Z guide** |

---

## 🚀 Choose Your Path

### ⚡ Path 1: Quick Setup (Recommended)

**For users who want to get started fast!**

1. Upload project to GitHub
2. Clone on VPS
3. Run `./install.sh`
4. Edit `.env` with your bot token
5. Run `./setup_systemd.sh`

**Done in 5 minutes!** → See **QUICK_START.md**

---

### 📚 Path 2: Detailed Setup

**For users who want to understand everything!**

Complete step-by-step guide covering:
- GitHub setup
- VPS preparation
- Installation
- 24/7 configuration
- Security best practices
- Troubleshooting

→ See **VPS_COMPLETE_GUIDE.md**

---

## 💡 Key Features

✅ **24/7 Operation** - Runs continuously, even after VPS reboot  
✅ **Auto-Restart** - Automatically restarts if it crashes  
✅ **Log Management** - All activity logged for debugging  
✅ **Easy Updates** - Simple `git pull` to update code  
✅ **Secure** - Environment variables keep tokens safe  
✅ **Production Ready** - Battle-tested systemd configuration  

---

## 📋 Requirements

- **VPS**: Ubuntu/Debian (20.04+ recommended)
- **Python**: 3.11 or higher
- **RAM**: Minimum 512MB
- **Disk**: ~100MB free space
- **Bot Token**: From [@BotFather](https://t.me/BotFather)

---

## 🎯 Quick Commands Reference

### Installation
```bash
./install.sh              # Install dependencies
./setup_systemd.sh        # Setup 24/7 service
```

### Management
```bash
sudo systemctl status toji-bot    # Check status
sudo systemctl restart toji-bot   # Restart bot
sudo journalctl -u toji-bot -f    # View logs
```

### Updates
```bash
cd ~/toji-chk-bot
git pull
sudo systemctl restart toji-bot
```

---

## 🆘 Get Help

1. **Quick issues?** → Check **QUICK_START.md** troubleshooting section
2. **Need details?** → See **VPS_COMPLETE_GUIDE.md** troubleshooting
3. **Check logs:** `sudo journalctl -u toji-bot -n 100`

---

## 🔐 Security Notes

- ✅ Bot token stored as environment variable (not in code)
- ✅ Safe to share on GitHub (token not committed)
- ✅ Access control enforces authorized groups
- ✅ Premium system for private access

**Never commit `.env` file to GitHub!** (it's in `.gitignore`)

---

## 📊 What Happens After Deployment

Your bot will:
1. Start automatically when VPS boots
2. Restart automatically if it crashes
3. Log all activity to `/var/log/toji-bot.log`
4. Run continuously 24/7

**Test it:** Restart your VPS and the bot will start automatically!

---

## 🎉 Success Checklist

- [ ] Code uploaded to GitHub
- [ ] Cloned on VPS
- [ ] Dependencies installed
- [ ] `.env` configured with bot token
- [ ] Bot responds to `/start` in Telegram
- [ ] systemd service running
- [ ] Bot shows as "active (running)" in status

**All checked?** You're production-ready! 🚀

---

## 🤝 Support

For bot-specific issues, check the logs:
```bash
sudo journalctl -u toji-bot -n 100
```

For VPS/system issues, consult your hosting provider.

---

**Made with ❤️ for seamless VPS deployment**
