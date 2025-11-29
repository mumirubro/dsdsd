# 🚀 Braintree Automated Gateway Checker

A comprehensive automated tool to check credit cards on any Braintree payment gateway website.

## ✨ Features

- **Fully Automated**: Handles the entire process from A to Z
- **Universal**: Works with ANY Braintree gateway site
- **Smart Account Creation**: Automatically registers accounts when needed
- **Address Management**: Adds billing addresses automatically
- **Token Extraction**: Dynamically finds and extracts all Braintree tokens
- **Comprehensive Testing**: Tokenizes cards and submits payment methods
- **Detailed Analysis**: Provides clear results for each transaction

## 🔧 Installation

All dependencies are already installed! Just run the script.

## 📖 How to Use

1. Run the script:
```bash
python main.py
```

2. Enter the target website URL when prompted:
```
🌐 Enter the target site URL: https://example.com
```

3. Enter the card details in the format: `cardnumber|mm|yy|cvv`
```
💳 Enter card data: 4111111111111111|12|25|123
```

4. The script will automatically:
   - ✅ Register a new account (if required)
   - ✅ Add billing address
   - ✅ Extract Braintree client token
   - ✅ Decode authorization fingerprint
   - ✅ Tokenize the credit card
   - ✅ Submit payment method
   - ✅ Analyze and display the result

## 📊 Result Types

- ✅ **APPROVED - CVV Declined**: Card is live but CVV mismatch
- ✅ **APPROVED - Insufficient Funds**: Card is live but has no balance
- ✅ **APPROVED - Payment Method Added**: Successfully added
- ❌ **DECLINED - Call Issuer**: Card declined by bank
- ❌ **DECLINED - Expired Card**: Card has expired
- ❌ **DECLINED - Invalid Card**: Card number is invalid
- ⚠️ **Unknown Response**: Manual check required

## 🔒 Security Features

- No hardcoded credentials
- Automatically generates fake user data using Faker library
- Secure session management
- SSL verification disabled for testing (can be enabled)

## 🛠️ Technical Details

The script performs these steps automatically:

1. **Account Registration**: Creates random accounts with realistic data
2. **Session Management**: Maintains cookies and session data
3. **Token Extraction**: Finds Braintree tokens using multiple patterns
4. **Token Decoding**: Base64 decodes and extracts authorization fingerprints
5. **Card Tokenization**: Sends card data to Braintree GraphQL API
6. **Payment Submission**: Posts tokenized card to the website
7. **Result Analysis**: Parses response and determines card status

## ⚙️ Configuration

You can modify the script to:
- Change user agent strings
- Add custom headers
- Modify timeout settings
- Add proxy support
- Customize fake data generation

## 📝 Card Format

Always use this format: `cardnumber|mm|yy|cvv`

Examples:
- `4111111111111111|12|25|123`
- `5555555555554444|06|26|456`
- `378282246310005|03|27|789`

## ⚠️ Disclaimer

This tool is for educational and testing purposes only. Use it responsibly and only on websites you own or have explicit permission to test.

## 🤝 Support

For issues or questions, check the code comments or modify the script as needed.
