import json
import os
import string
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

ACCESS_CONTROL_FILE = 'access_control.json'

def load_access_data() -> Dict:
    """Load access control data from file"""
    if not os.path.exists(ACCESS_CONTROL_FILE):
        return {
            "authorized_groups": {},
            "premium_keys": {},
            "premium_users": {}
        }
    
    try:
        with open(ACCESS_CONTROL_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {
            "authorized_groups": {},
            "premium_keys": {},
            "premium_users": {}
        }

def save_access_data(data: Dict) -> None:
    """Save access control data to file"""
    with open(ACCESS_CONTROL_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_authorized_group(group_id: int, invite_link: str, added_by: str) -> None:
    """Add a group to authorized list"""
    data = load_access_data()
    data['authorized_groups'][str(group_id)] = {
        'group_id': group_id,
        'invite_link': invite_link,
        'added_by': added_by,
        'added_at': datetime.now().strftime('%m/%d/%Y %I:%M %p')
    }
    save_access_data(data)

def is_group_authorized(group_id: int) -> bool:
    """Check if a group is authorized"""
    data = load_access_data()
    return str(group_id) in data['authorized_groups']

def get_authorized_groups() -> Dict:
    """Get all authorized groups"""
    data = load_access_data()
    return data['authorized_groups']

def generate_premium_key(quantity: int, days: int, created_by: str) -> str:
    """Generate a new premium key"""
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    key_code = f"premium_{random_part}"
    
    data = load_access_data()
    data['premium_keys'][key_code] = {
        'code': key_code,
        'quantity': quantity,
        'days_valid': days,
        'created_by': created_by,
        'created_at': datetime.now().strftime('%m/%d/%Y %I:%M %p'),
        'remaining_uses': quantity,
        'used_by': []
    }
    save_access_data(data)
    
    return key_code

def redeem_key(key_code: str, user_id: int, username: str) -> tuple[bool, str]:
    """
    Redeem a premium key for a user
    Returns (success: bool, message: str)
    """
    data = load_access_data()
    
    if key_code not in data['premium_keys']:
        return False, "❌ Invalid key!"
    
    key_info = data['premium_keys'][key_code]
    
    if key_info['remaining_uses'] <= 0:
        return False, "❌ This key has been fully used!"
    
    user_str = str(user_id)
    if user_str in key_info.get('used_by', []):
        return False, "❌ You have already used this key!"
    
    expires_at = datetime.now() + timedelta(days=key_info['days_valid'])
    
    if user_str in data['premium_users']:
        existing_expiry = datetime.fromisoformat(data['premium_users'][user_str]['expires_at'])
        if existing_expiry > datetime.now():
            expires_at = existing_expiry + timedelta(days=key_info['days_valid'])
    
    data['premium_users'][user_str] = {
        'user_id': user_id,
        'username': username,
        'expires_at': expires_at.isoformat(),
        'activated_at': datetime.now().strftime('%m/%d/%Y %I:%M %p')
    }
    
    key_info['remaining_uses'] -= 1
    key_info['used_by'].append(user_str)
    
    save_access_data(data)
    
    return True, f"✅ Premium activated! Valid until {expires_at.strftime('%m/%d/%Y %I:%M %p')}"

def is_premium_user(user_id: int) -> bool:
    """Check if a user has active premium"""
    data = load_access_data()
    user_str = str(user_id)
    
    if user_str not in data['premium_users']:
        return False
    
    user_info = data['premium_users'][user_str]
    expires_at = datetime.fromisoformat(user_info['expires_at'])
    
    if expires_at < datetime.now():
        del data['premium_users'][user_str]
        save_access_data(data)
        return False
    
    return True

def get_key_info(key_code: str) -> Optional[Dict]:
    """Get information about a specific key"""
    data = load_access_data()
    return data['premium_keys'].get(key_code)

def clean_expired_premium() -> None:
    """Remove expired premium users"""
    data = load_access_data()
    expired_users = []
    
    for user_id, user_info in data['premium_users'].items():
        expires_at = datetime.fromisoformat(user_info['expires_at'])
        if expires_at < datetime.now():
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del data['premium_users'][user_id]
    
    if expired_users:
        save_access_data(data)


def ban_user(user_id: int, username: str, banned_by: str) -> bool:
    """Ban a user from using the bot"""
    data = load_access_data()
    if 'banned_users' not in data:
        data['banned_users'] = {}
    
    data['banned_users'][str(user_id)] = {
        'user_id': user_id,
        'username': username,
        'banned_by': banned_by,
        'banned_at': datetime.now().strftime('%m/%d/%Y %I:%M %p')
    }
    save_access_data(data)
    return True


def unban_user(user_id: int) -> bool:
    """Unban a user"""
    data = load_access_data()
    if 'banned_users' not in data:
        return False
    
    user_str = str(user_id)
    if user_str in data['banned_users']:
        del data['banned_users'][user_str]
        save_access_data(data)
        return True
    return False


def is_user_banned(user_id: int) -> bool:
    """Check if a user is banned"""
    data = load_access_data()
    if 'banned_users' not in data:
        return False
    return str(user_id) in data['banned_users']


def get_banned_users() -> Dict:
    """Get all banned users"""
    data = load_access_data()
    return data.get('banned_users', {})


def remove_premium(user_id: int) -> bool:
    """Remove premium status from a user"""
    data = load_access_data()
    user_str = str(user_id)
    
    if user_str in data.get('premium_users', {}):
        del data['premium_users'][user_str]
        save_access_data(data)
        return True
    return False


def get_premium_users() -> Dict:
    """Get all premium users"""
    data = load_access_data()
    return data.get('premium_users', {})
