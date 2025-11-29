# 🛒 Braintree Card Checker Telegram Bot

A Telegram bot for checking Braintree cards with admin controls, global site/proxy management, and fancy formatted responses with BIN lookup.

## 🎯 Features

- Single and batch card checking with fancy formatted results
- BIN information lookup (brand, type, country, bank)
- Global URL management (admin)
- Proxy support with status checking
- Site validation and mass site checking
- Admin-only commands for system configuration
- Response time tracking

## 👤 Admin

- **Admin ID:** 1805944073
- **Admin Name:** MUMIRU
- **Admin Username:** @Mumiru

## 📚 Commands

### Normal User Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show welcome message and command list | `/start` |
| `/br` | Check a single card | `/br 4532123456789012\|12\|25\|123` |
| `/mbr` | Check multiple cards (max 10) | `/mbr card1\|12\|25\|123 card2\|01\|26\|456` |

### Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/setburl` | Set global Shopify domain | `/setburl example.braintree.com` |
| `/myburl` | Show current global domain | `/myburl` |
| `/rmburl` | Remove global URL | `/rmburl` |
| `/baddp` | Add global proxy | `/baddp http://user:pass@host:port` |
| `/brp` | Remove active proxy | `/brp` |
| `/blp` | List all proxies | `/blp` |
| `/bcp` | Check proxy status | `/bcp` |
| `/chkburl` | Test if a Shopify site works | `/chkburl example.com` |
| `/mbchku` | Mass check multiple sites | `/mbchku site1.com site2.com site3.com` |

## 🔧 Setup

1. **Bot Token**: Already configured in secrets as `BOT_TOKEN`
2. **Start the bot**: The bot runs automatically via the workflow

## 🌐 Global Settings

The bot uses a global URL and proxy system:

- **Global URL**: Set by admin using `/setburl`, used by all users for card checking
- **Global Proxy**: Set by admin using `/baddp`, used for all card checks
- All users benefit from the admin's configuration

## 💳 Card Format

Cards must be provided in the format: `cardnumber|mm|yy|cvv`

Examples:
- `4532123456789012|12|25|123`
- `5555555555554444|06|26|456`
- `378282246310005|03|27|789`

## 📊 Response Format

The bot responds with a fancy formatted message including:
- Masked card number
- Status (✅ or ❌)
- Response message
- BIN information (type, country, bank)
- Time taken
- Proxy status
- Requester username
- Developer credit

## 🔒 Security

- Bot token is stored securely in environment variables
- Card numbers are masked in responses
- Admin commands are restricted to the configured admin ID

## 📊 How It Works

1. Admin sets a global URL using `/setburl`
2. Users send card data using `/br` or `/mbr`
3. Bot uses the BraintreeAutomatedChecker to test cards
4. Results are returned with masked card numbers

## 🚀 Running the Bot

The bot is configured to run automatically. To start manually:

```bash
python bot.py
```

## 📁 Data Storage

Bot settings are stored in `bot_data.json`:
- Global URL
- Proxy list
- Active proxy

This file is created automatically when the bot first runs.
