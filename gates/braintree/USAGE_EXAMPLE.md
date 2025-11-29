# 💡 Usage Examples

## Basic Usage

### Step 1: Run the Script
```bash
python main.py
```

### Step 2: Enter Website URL
```
🌐 Enter the target site URL: https://example.com
```

Or without https:
```
🌐 Enter the target site URL: example.com
```

### Step 3: Enter Card Data
Format: `cardnumber|mm|yy|cvv`

```
💳 Enter card data: 4111111111111111|12|25|123
```

## Example Session

```
============================================================
🚀 BRAINTREE AUTOMATED GATEWAY CHECKER
============================================================

This tool will automatically:
  1. Register account (if needed)
  2. Add billing address
  3. Extract Braintree tokens
  4. Tokenize credit card
  5. Submit payment method
  6. Analyze result

============================================================

🌐 Enter the target site URL: https://www.example.com

💳 Enter card data (format: cardnumber|mm|yy|cvv): 4111111111111111|12|25|123

============================================================
🔍 BRAINTREE AUTOMATED CHECKER
============================================================

🌐 Target Site: https://www.example.com
💳 Card: 4111111111111111|12|25|123

------------------------------------------------------------
📝 Normalized: 411111******1111|12|2025|***

[STEP 1] Attempting to register new account...
   ✅ Account created: john1234@gmail.com

[STEP 2] Adding billing address...
   ✅ Billing address added

[STEP 3] Fetching Braintree client token...
   ✅ Token found at /my-account/add-payment-method/
   ✅ Token decoded successfully
   ✅ Authorization fingerprint extracted

[STEP 4] Tokenizing credit card...
   ✅ Card tokenized successfully

[STEP 5] Submitting payment method...
   ✅ Payment method submitted

============================================================
📊 FINAL RESULT
============================================================

✅ APPROVED - CVV Declined (Card Live)

============================================================
```

## What the Script Does Automatically

### 1. Account Creation
- Generates random fake user data (name, email, address, phone)
- Attempts to register a new account on the site
- Uses realistic data from the Faker library
- Falls back to guest checkout if registration isn't available

### 2. Address Management
- Automatically adds billing address with generated data
- Uses US addresses by default (can be modified in code)
- Handles different WooCommerce address formats

### 3. Token Extraction
- Searches multiple common endpoints for Braintree tokens
- Tries various token patterns and formats
- Attempts AJAX token retrieval if needed
- Decodes base64-encoded tokens

### 4. Card Processing
- Normalizes card data (adds leading zeros, formats year)
- Tokenizes card via Braintree GraphQL API
- Generates unique session IDs and device data
- Handles all Braintree API responses

### 5. Payment Submission
- Finds the correct submission endpoint
- Extracts necessary nonces and CSRF tokens
- Submits payment method with proper headers
- Follows redirects automatically

### 6. Result Analysis
- Parses HTML responses for error messages
- Identifies specific decline reasons
- Distinguishes between hard declines and live cards
- Provides clear, actionable results

## Common Card Formats

```
# Visa
4111111111111111|12|25|123

# MasterCard
5555555555554444|06|26|456

# American Express
378282246310005|03|27|7893

# Discover
6011111111111117|09|28|234

# With 2-digit year
4111111111111111|12|25|123

# With single-digit month (will be auto-padded)
4111111111111111|6|26|456
```

## Result Interpretation

| Result | Meaning | Card Status |
|--------|---------|-------------|
| ✅ CVV Declined | CVV mismatch but card is valid | **Live Card** |
| ✅ Insufficient Funds | Card valid but no balance | **Live Card** |
| ✅ Payment Added | Successfully added payment | **Live Card** |
| ❌ Call Issuer | Bank declined the transaction | Dead Card |
| ❌ Expired Card | Card expiration date has passed | Dead Card |
| ❌ Invalid Card | Card number is not valid | Dead Card |
| ❌ Do Not Honor | Bank refuses the transaction | Dead Card |
| ⚠️ Unknown Response | Need to check manually | Unknown |

## Tips

1. **Site Selection**: Works best with WooCommerce sites using Braintree
2. **Rate Limiting**: Add delays between checks to avoid detection
3. **Proxies**: Modify the code to add proxy support if needed
4. **Sessions**: Each run creates a fresh session with new account
5. **Errors**: If token extraction fails, the site might not use Braintree

## Troubleshooting

### "No Braintree token found"
- Site may not use Braintree gateway
- Site may use a different payment processor
- Token extraction patterns may need updating

### "Card tokenization failed"
- Check if card format is correct
- Verify authorization fingerprint was extracted
- Check internet connection

### "Unknown response"
- Check the site manually
- Response parsing may need adjustment
- New error message format on the site

## Advanced: Batch Processing

To check multiple cards, create a file `cards.txt`:
```
4111111111111111|12|25|123
5555555555554444|06|26|456
378282246310005|03|27|789
```

Then modify the script or create a wrapper to process them all.
