# Advanced Hotmail/Outlook Account Checker

A powerful, fast, and feature-rich Python tool for checking Hotmail/Outlook accounts with full data capture capabilities.

## Features

✓ **Full Account Capture**
- User display name, country, birthdate
- Unread and total message counts
- Inbox, Sent, Draft, Deleted folder statistics
- Cookies and authentication tokens

✓ **Advanced OAuth & Token Extraction**
- Access tokens and refresh tokens
- OAuth 2.0 token capture
- Canary token extraction

✓ **Payment Information Capture**
- Account balance
- Payment methods (credit cards)
- PayPal email addresses
- Total order count

✓ **High Performance**
- Asynchronous multi-threaded checking
- Configurable concurrent threads
- Automatic retry logic
- Proxy rotation support

✓ **Beautiful Output**
- Rich terminal UI with colors
- Progress bars and statistics
- Organized result files
- JSON export for full data

## Installation

The required dependencies are already installed:
- httpx
- aiofiles
- colorama
- rich

## Usage

### Basic Usage

```bash
python advanced_hotmail_checker.py
```

Then follow the interactive prompts:
1. Enter combo file path (default: combos.txt)
2. Enter proxy file path (default: proxies.txt)
3. Enter concurrent threads (default: 50)
4. Enter timeout in seconds (default: 30)

### File Formats

**combos.txt** - One combo per line in email:password format:
```
user1@outlook.com:password123
user2@hotmail.com:mypassword
user3@live.com:secret456
```

**proxies.txt** - One proxy per line (http/https/socks5):
```
http://proxy1.com:8080
http://user:pass@proxy2.com:3128
socks5://proxy3.com:1080
```

## Output Files

All results are saved in the `results/` folder:

- **hits_TIMESTAMP.txt** - Successful logins with captured data
- **full_capture_TIMESTAMP.json** - Complete JSON data for all hits
- **2fa_TIMESTAMP.txt** - Accounts requiring two-factor authentication
- **stats_TIMESTAMP.json** - Session statistics

## Captured Data

For each successful account, the tool captures:

### Basic Information
- Email and password
- Account status
- Display name
- Country
- Birthdate

### Email Statistics
- Unread message count
- Total message count
- Inbox count
- Sent items count
- Draft count
- Deleted items count

### Authentication Data
- Session cookies
- OAuth access tokens
- Refresh tokens
- Canary tokens
- Client ID

### Payment Information
- Account balance
- Payment methods
- PayPal email
- Total order count

## Account Statuses

- **SUCCESS** - Valid credentials, full data captured
- **2FACTOR** - Valid credentials but 2FA required
- **INVALID_EMAIL** - Account doesn't exist
- **INVALID_PASSWORD** - Wrong password
- **TIMEOUT** - Connection timeout
- **ERROR** - Other errors

## Performance Tips

1. **Threads**: Start with 50 threads, increase for faster checking (up to 200)
2. **Proxies**: Use high-quality proxies to avoid rate limiting
3. **Timeout**: 30 seconds is recommended, lower for faster checking
4. **Retry Logic**: Built-in retry (2 attempts) for failed requests

## Statistics

The tool displays comprehensive statistics:
- Total accounts checked
- Success count
- 2FA required count
- Invalid email/password counts
- Timeout and error counts
- Success rate percentage
- Elapsed time
- CPM (Checks Per Minute)

## Advanced Features

### Automatic Retry
Failed requests are automatically retried up to 2 times with exponential backoff.

### Proxy Rotation
Proxies are randomly rotated for each request to distribute load.

### User Agent Rotation
Multiple modern user agents are rotated to avoid detection.

### Full Token Capture
Captures all authentication tokens including:
- Flow tokens (PPFT)
- OAuth tokens
- Refresh tokens
- Access tokens

## Based on SilverBullet Configs

This tool is inspired by and implements features from multiple SilverBullet configurations:
- Hotmail BY ɪᴀᴍɴᴏᴛᴀʜᴀᴄᴋᴇʀ
- Hotmail Full Capture By @YeatTheLegit
- Hotmail Capture v2
- Hotmail&Outlook - PSN

## Legal Disclaimer

This tool is for educational purposes only. Only use it on accounts you own or have explicit permission to test. Unauthorized access to accounts is illegal.

## Example Output

```
✓ SUCCESS user@outlook.com | John Doe | $50.00
⚠ 2FA user2@hotmail.com
✗ WRONG PASS user3@live.com

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Metric             ┃ Value    ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Total Checked      │ 100      │
│ ✓ Success          │ 25       │
│ ⚠ 2FA Required     │ 10       │
│ ✗ Invalid Email    │ 30       │
│ ✗ Invalid Password │ 30       │
│ Success Rate       │ 25.00%   │
│ Elapsed Time       │ 45.23s   │
│ CPM                │ 132.74   │
└────────────────────┴──────────┘
```
