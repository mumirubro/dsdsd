"""
Stripe SK Key Checker Tool
Validates and checks Stripe secret keys by querying the balance API
"""

import re
import requests
import base64
from typing import Dict, Any


def validate_sk_format(sk_key: str) -> bool:
    """
    Validate if the SK key has the correct format
    
    Args:
        sk_key: The SK key to validate
    
    Returns:
        True if valid format, False otherwise
    """
    pattern = r'sk_(test|live)_[A-Za-z0-9]+'
    return bool(re.match(pattern, sk_key))


def mask_sk_key(sk_key: str) -> str:
    """
    Mask the SK key for display (show first 12 chars and last 4 chars)
    
    Args:
        sk_key: The full SK key
    
    Returns:
        Masked SK key
    """
    if len(sk_key) > 16:
        return f"{sk_key[:12]}_SWDQYL_{sk_key[-4:]}"
    return sk_key


def check_stripe_sk(sk_key: str) -> Dict[str, Any]:
    """
    Check Stripe SK key by querying the balance API and account info
    
    Args:
        sk_key: The Stripe secret key to check
    
    Returns:
        Dict containing check results or error information
    """
    try:
        if not validate_sk_format(sk_key):
            return {
                'success': False,
                'error': 'Enter Valid SK Key'
            }
        
        auth_string = base64.b64encode(sk_key.encode()).decode()
        headers = {
            'Authorization': f'Basic {auth_string}'
        }
        
        response = requests.get(
            'https://api.stripe.com/v1/balance',
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', "This SK Key isn't Valid")
                return {
                    'success': False,
                    'error': error_message
                }
            except:
                return {
                    'success': False,
                    'error': "This SK Key isn't Valid"
                }
        
        data = response.json()
        
        if 'error' in data:
            error_message = data['error'].get('message', "This SK Key isn't Valid")
            return {
                'success': False,
                'error': error_message
            }
        
        available = data.get('available', [{}])[0]
        pending = data.get('pending', [{}])[0]
        
        currency = available.get('currency', 'N/A').upper()
        available_amount = available.get('amount', 0)
        pending_amount = pending.get('amount', 0)
        
        available_display = available_amount / 100 if available_amount else 0
        pending_display = pending_amount / 100 if pending_amount else 0
        
        account_info = {}
        try:
            acc_response = requests.get(
                'https://api.stripe.com/v1/account',
                headers=headers,
                timeout=10
            )
            if acc_response.status_code == 200:
                acc_data = acc_response.json()
                account_info = {
                    'country': acc_data.get('country', 'N/A'),
                    'default_currency': acc_data.get('default_currency', 'N/A').upper(),
                    'business_type': acc_data.get('business_type', 'N/A'),
                    'payouts_enabled': acc_data.get('payouts_enabled', False),
                    'charges_enabled': acc_data.get('charges_enabled', False),
                    'email': acc_data.get('email', 'N/A'),
                    'business_name': acc_data.get('business_profile', {}).get('name', 'N/A'),
                }
        except:
            pass
        
        all_balances = []
        for bal in data.get('available', []):
            curr = bal.get('currency', 'N/A').upper()
            amt = bal.get('amount', 0) / 100
            all_balances.append({'currency': curr, 'amount': amt, 'type': 'available'})
        for bal in data.get('pending', []):
            curr = bal.get('currency', 'N/A').upper()
            amt = bal.get('amount', 0) / 100
            all_balances.append({'currency': curr, 'amount': amt, 'type': 'pending'})
        
        result = {
            'success': True,
            'data': {
                'sk_key': sk_key,
                'masked_sk': mask_sk_key(sk_key),
                'currency': currency,
                'available': available_display,
                'pending': pending_display,
                'available_raw': available_amount,
                'pending_raw': pending_amount,
                'is_live': 'live' in sk_key,
                'country': account_info.get('country', 'N/A'),
                'business_type': account_info.get('business_type', 'N/A'),
                'payouts_enabled': account_info.get('payouts_enabled', False),
                'charges_enabled': account_info.get('charges_enabled', False),
                'email': account_info.get('email', 'N/A'),
                'business_name': account_info.get('business_name', 'N/A'),
                'all_balances': all_balances
            }
        }
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timed out'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def format_sk_check_message(result: Dict[str, Any]) -> str:
    """
    Format the SK check result into a Telegram message with enhanced details
    
    Args:
        result: Result from check_stripe_sk()
    
    Returns:
        Formatted message string
    """
    if not result.get('success'):
        return (
            "╔═══════════════════════════════╗\n"
            "   ❌ 𝗦𝗞 𝗖𝗛𝗘𝗖𝗞 𝗙𝗔𝗜𝗟𝗘𝗗\n"
            "╚═══════════════════════════════╝\n\n"
            f"❌ <b>Error:</b> <i>{result.get('error', 'Unknown error')}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    
    data = result['data']
    key_type = "🟢 LIVE" if data.get('is_live') else "🟡 TEST"
    charges_status = "✅ Yes" if data.get('charges_enabled') else "❌ No"
    payouts_status = "✅ Yes" if data.get('payouts_enabled') else "❌ No"
    
    message = (
        "╔═══════════════════════════════╗\n"
        "   ✅ 𝗦𝗞 𝗞𝗘𝗬 𝗩𝗔𝗟𝗜𝗗\n"
        "╚═══════════════════════════════╝\n\n"
        f"🔑 <b>SK Key:</b> <code>{data['masked_sk']}</code>\n"
        f"📋 <b>Type:</b> {key_type}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Currency:</b> {data['currency']}\n"
        f"💵 <b>Available:</b> <code>{data['available']:.2f}</code> {data['currency']}\n"
        f"⏳ <b>Pending:</b> <code>{data['pending']:.2f}</code> {data['currency']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 <b>Region:</b> {data.get('country', 'N/A')}\n"
        f"🏢 <b>Business:</b> {data.get('business_name', 'N/A')}\n"
        f"📧 <b>Email:</b> {data.get('email', 'N/A')}\n"
        f"💳 <b>Charges:</b> {charges_status}\n"
        f"💸 <b>Payouts:</b> {payouts_status}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "𝐃𝐄𝐕 : @MUMIRU"
    )
    
    return message
