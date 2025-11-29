"""
Faker Tool - Generate fake identity information based on country code
Uses randomuser.me API to generate realistic fake user data
"""

import requests
from typing import Optional, Dict, Any


def get_country_name(country_code: str) -> str:
    """
    Convert country code to full country name
    """
    countries = {
        'AU': 'Australia',
        'BR': 'Brazil',
        'CA': 'Canada',
        'CH': 'Switzerland',
        'DE': 'Germany',
        'DK': 'Denmark',
        'ES': 'Spain',
        'FI': 'Finland',
        'FR': 'France',
        'GB': 'United Kingdom',
        'IE': 'Ireland',
        'IN': 'India',
        'IR': 'Iran',
        'MX': 'Mexico',
        'NL': 'Netherlands',
        'NO': 'Norway',
        'NZ': 'New Zealand',
        'RS': 'Serbia',
        'TR': 'Turkey',
        'UA': 'Ukraine',
        'US': 'United States'
    }
    return countries.get(country_code.upper(), country_code)


def get_flag(country_code: str) -> str:
    """
    Get flag emoji for country code
    """
    flags = {
        'AU': '🇦🇺', 'BR': '🇧🇷', 'CA': '🇨🇦', 'CH': '🇨🇭',
        'DE': '🇩🇪', 'DK': '🇩🇰', 'ES': '🇪🇸', 'FI': '🇫🇮',
        'FR': '🇫🇷', 'GB': '🇬🇧', 'IE': '🇮🇪', 'IN': '🇮🇳',
        'IR': '🇮🇷', 'MX': '🇲🇽', 'NL': '🇳🇱', 'NO': '🇳🇴',
        'NZ': '🇳🇿', 'RS': '🇷🇸', 'TR': '🇹🇷', 'UA': '🇺🇦',
        'US': '🇺🇸'
    }
    return flags.get(country_code.upper(), '🏳️')


def generate_fake_identity(nationality: str = 'US') -> Dict[str, Any]:
    """
    Generate fake identity using randomuser.me API
    
    Args:
        nationality: Country code (e.g., 'US', 'GB', 'CA')
    
    Returns:
        Dict containing fake user data or error information
    """
    try:
        # Call randomuser.me API
        url = f"https://randomuser.me/api/1.2/?nat={nationality.upper()}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': 'Failed to fetch data from API'
            }
        
        data = response.json()
        
        # Check if results exist
        if not data.get('results') or len(data['results']) == 0:
            return {
                'success': False,
                'error': 'Country code not found or invalid'
            }
        
        user = data['results'][0]
        
        # Extract data safely
        name = user.get('name', {}) if isinstance(user.get('name'), dict) else {}
        location = user.get('location', {}) if isinstance(user.get('location'), dict) else {}
        street = location.get('street', {}) if isinstance(location.get('street'), dict) else {}
        
        # Format street address
        if isinstance(street, dict):
            street_number = street.get('number', '')
            street_name = street.get('name', '')
            street_address = f"{street_number} {street_name}".strip()
        else:
            street_address = str(street) if street else ''
        
        # Extract nested data safely
        dob = user.get('dob', {}) if isinstance(user.get('dob'), dict) else {}
        login = user.get('login', {}) if isinstance(user.get('login'), dict) else {}
        picture = user.get('picture', {}) if isinstance(user.get('picture'), dict) else {}
        
        result = {
            'success': True,
            'data': {
                'title': str(name.get('title', '')).capitalize() if name else '',
                'first_name': str(name.get('first', '')).capitalize() if name else '',
                'last_name': str(name.get('last', '')).capitalize() if name else '',
                'email': str(user.get('email', '')),
                'phone': str(user.get('phone', '')),
                'cell': str(user.get('cell', '')),
                'street': street_address,
                'city': str(location.get('city', '')).capitalize() if location else '',
                'state': str(location.get('state', '')).capitalize() if location else '',
                'postcode': str(location.get('postcode', '')) if location else '',
                'country_code': str(user.get('nat', nationality.upper())),
                'country': get_country_name(user.get('nat', nationality.upper())),
                'flag': get_flag(user.get('nat', nationality.upper())),
                'dob': str(dob.get('date', '')) if dob else '',
                'age': str(dob.get('age', '')) if dob else '',
                'username': str(login.get('username', '')) if login else '',
                'password': str(login.get('password', '')) if login else '',
                'picture': str(picture.get('large', '')) if picture else ''
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


def format_fake_identity_message(result: Dict[str, Any]) -> str:
    """
    Format the fake identity data into a Telegram message
    
    Args:
        result: Result from generate_fake_identity()
    
    Returns:
        Formatted message string
    """
    if not result.get('success'):
        return f"[❌] <b>Error</b> → <i>{result.get('error', 'Unknown error')}</i>!"
    
    data = result['data']
    
    message = (
        f"[👤] <b>Name</b> ↯ <code>{data['title']}</code>. "
        f"<code>{data['first_name']}</code> <code>{data['last_name']}</code>\n\n"
        f"[📧] <b>Email</b> ↯ <code>{data['email']}</code>\n"
        f"[☎️] <b>Phone</b> ↯ <code>{data['phone']}</code>\n"
        f"[📱] <b>Cell</b> ↯ <code>{data['cell']}</code>\n\n"
        f"[🛣] <b>Street</b> ↯ <code>{data['street']}</code>\n"
        f"[🏙] <b>City</b> ↯ <code>{data['city']}</code>\n"
        f"[🗽] <b>State</b> ↯ <code>{data['state']}</code>\n"
        f"[📟] <b>Postal Code</b> ↯ <code>{data['postcode']}</code>\n"
        f"[🗺] <b>Country</b> ↯ <code>{data['country']}</code> [<code>{data['flag']}</code>]\n\n"
        f"[🎂] <b>Age</b> ↯ <code>{data['age']}</code>\n"
        f"[👨‍💻] <b>Username</b> ↯ <code>{data['username']}</code>\n"
        f"[🔑] <b>Password</b> ↯ <code>{data['password']}</code>"
    )
    
    return message
