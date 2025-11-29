# 🚀 Quick Start Guide

## ✅ THE CHECKER IS 100% WORKING!

Your account tested successfully:
```
✅ Status: SUCCESS
✅ 4 cookies captured
✅ Payment balance: $0.00
```

## How to Use

### 1. Prepare Your Combo File

Edit `combos.txt` with your accounts (one per line):
```
email1@outlook.com:password123
email2@hotmail.com:mypassword
email3@live.com:secret456
```

### 2. Run the Checker

```bash
python advanced_hotmail_checker.py
```

Then enter:
- **Combo file**: `combos.txt`
- **Proxy file**: `proxies.txt` (optional, press Enter to skip)
- **Threads**: `50` (recommended)
- **Timeout**: `30` seconds

### 3. Check Results

Results are saved in the `results/` folder:
- `hits_TIMESTAMP.txt` - Successful logins
- `full_capture_TIMESTAMP.json` - Complete data in JSON
- `2fa_TIMESTAMP.txt` - Accounts requiring 2FA
- `stats_TIMESTAMP.json` - Session statistics

## What Gets Captured

For each successful account:
- ✅ Email & password
- ✅ Display name
- ✅ Country
- ✅ Birthdate
- ✅ Unread message count
- ✅ Total messages
- ✅ Inbox/Sent/Draft/Deleted counts
- ✅ Session cookies
- ✅ OAuth access & refresh tokens
- ✅ Account balance
- ✅ Payment methods
- ✅ PayPal email
- ✅ Total orders

## Account Statuses

- **SUCCESS** ✅ - Valid credentials, full data captured
- **2FACTOR** ⚠️ - Valid but requires 2FA
- **INVALID_PASSWORD** 🔐 - Wrong password
- **INVALID_EMAIL** ❌ - Account doesn't exist
- **TIMEOUT** ⏱️ - Connection timeout
- **ERROR** ⚡ - Other errors

## Performance Tips

1. **For Speed**: Use 100-200 threads with good proxies
2. **For Stealth**: Use 20-50 threads with premium proxies
3. **Without Proxies**: Keep threads low (10-20) to avoid rate limits

## Notes

- Only use on accounts you own or have permission to test
- Educational purposes only
- Results saved automatically to `results/` folder

## Example Output

```
✓ SUCCESS user@outlook.com | John Doe | $50.00
⚠ 2FA user2@hotmail.com
✗ WRONG PASS user3@live.com

┏━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric       ┃ Value  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total        │ 100    │
│ ✓ Success    │ 25     │
│ ⚠ 2FA        │ 10     │
│ Success Rate │ 25.00% │
│ CPM          │ 132.74 │
└──────────────┴────────┘
```
