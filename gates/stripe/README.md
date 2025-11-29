# TOJI CHK Bot - Advanced Stripe Card Checker

A Telegram bot for checking Stripe payment cards with advanced authentication modes.

## Features

### 🔐 Three Authentication Modes

1. **Mode 1: Create New Account** (Default)
   - Creates a new temporary account for each check
   - No credentials required
   - Best for sites that don't block new registrations

2. **Mode 2: Shared Account Login**
   - Uses admin-configured credentials for all users
   - All users share the same account
   - Best for sites that block frequent registrations
   - Requires admin to set email:password

3. **Mode 3: Skip Authentication** (Direct Stripe API)
   - Bypasses WooCommerce login/registration
   - Uses direct Stripe API for card validation
   - Searches for Stripe public key on public pages (checkout, cart, homepage)
   - **Note:** Falls back to Mode 1 if Stripe key not found on public pages
   - Best for sites with Stripe key exposed on public pages

### 📋 User Commands

- `/start` - Display welcome message and command list
- `/chk <card|mm|yy|cvv>` - Check single card
- `/mchk <card1> <card2> ...` - Check multiple cards (max 10)

### 🔧 Admin Commands

- `/setsurl <domain>` - Configure Stripe URL and authentication mode
- `/mysurl` - View current configuration
- `/rmsurl` - Remove current configuration
- `/chkurl <domain>` - Test a Stripe site
- `/mschku <domain1> <domain2> ...` - Test multiple sites

## Setup

### Prerequisites

- Python 3.10+
- Telegram Bot Token
- Required packages: `python-telegram-bot`, `aiohttp`, `fake-useragent`

### Installation

1. Install dependencies:
```bash
pip install python-telegram-bot aiohttp fake-useragent
```

2. Set environment variable:
```bash
export BOT_TOKEN='your_telegram_bot_token'
```

3. Run the bot:
```bash
python main.py
```

## Configuration Guide

### Setting Up Authentication Mode

1. Admin sends: `/setsurl example.com`
2. Bot responds with auth mode options
3. Admin selects mode (1, 2, or 3)
4. If mode 2 selected, bot asks for credentials
5. Admin sends: `email:password`
6. Configuration is saved

### Example Configuration Flow

```
Admin: /setsurl myshop.com

Bot: 🌐 URL received: https://myshop.com/my-account/
     🔐 Choose Authentication Mode:
     1 - Create new account every time (default)
     2 - Login from same account every time
     3 - Skip login/register (direct CC check)
     Reply with 1, 2, or 3

Admin: 2

Bot: 📧 Please send login credentials in this format:
     email:password
     Example: user@example.com:mypassword

Admin: testuser@example.com:SecurePass123

Bot: ✅ Configuration saved!
     🌐 URL: https://myshop.com/my-account/
     🔐 Auth Mode: Login from same account
     📧 Email: testuser@example.com
     🔑 Password: ***************
     All users will now use this setup for card checking.
```

## Usage Examples

### Check Single Card

```
/chk 4532123456789012|12|25|123
```

### Check Multiple Cards

```
/mchk 4532123456789012|12|25|123 5500000000000004|01|26|456
```

### Test a Site

```
/chkurl myshop.com
```

## Features

- ✅ Works with all Stripe versions (old and new)
- ✅ Multiple fallback methods for nonce/key extraction
- ✅ Persistent configuration storage
- ✅ Support for 3 authentication modes
- ✅ BIN lookup integration
- ✅ Beautiful formatted responses
- ✅ Admin-only configuration
- ✅ Conversation-based setup

## Security Notes

- Configuration is stored locally in `bot_config.json`
- Admin IDs are hardcoded in `main.py` (modify `ADMIN_IDS` variable)
- Credentials for mode 2 are stored in plain text (consider encryption for production)
- Only admins can configure the bot

## Compatibility

This bot is designed to work with:
- WooCommerce + Stripe plugin (all versions)
- Custom Stripe implementations
- Various Stripe API versions
- Multiple endpoint variations

## Troubleshooting

### Bot doesn't start
- Check if `BOT_TOKEN` environment variable is set
- Verify your bot token is valid

### Card checks fail
- Test the URL first with `/chkurl`
- Try different authentication modes
- Check if credentials are correct (for mode 2)

### Configuration not persisting
- Ensure write permissions for `bot_config.json`
- Check file system permissions
- Configuration is loaded automatically on bot startup

### Mode 3 not working
- Mode 3 requires Stripe public key to be exposed on public pages
- If not available, bot automatically falls back to Mode 1
- Try /chkurl to test if a site supports Mode 3

## Credits

**Developer:** @mumiru
**Version:** 2.0
**License:** Private Use

## Support

For issues or questions, contact the developer.
