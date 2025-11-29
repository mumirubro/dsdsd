import json
import os
import asyncio
from typing import Optional, Dict, Any

CONFIG_FILE = 'bot_config.json'
_lock = asyncio.Lock()

class BotConfig:
    def __init__(self):
        self.stripe_url: Optional[str] = None
        self.auth_mode: int = 1  # 1=new account, 2=shared account, 3=skip auth
        self.shared_email: Optional[str] = None
        self.shared_password: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stripe_url': self.stripe_url,
            'auth_mode': self.auth_mode,
            'shared_email': self.shared_email,
            'shared_password': self.shared_password
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        self.stripe_url = data.get('stripe_url')
        self.auth_mode = data.get('auth_mode', 1)
        self.shared_email = data.get('shared_email')
        self.shared_password = data.get('shared_password')

# Global config instance
config = BotConfig()

def load_config_sync():
    """Load configuration from file synchronously at module import"""
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                config.from_dict(data)
        except Exception as e:
            print(f"Error loading config: {e}")
    return config

load_config_sync()

async def load_config() -> BotConfig:
    """Load configuration from file"""
    global config
    async with _lock:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    config.from_dict(data)
            except Exception as e:
                print(f"Error loading config: {e}")
        return config

async def save_config() -> None:
    """Save configuration to file"""
    global config
    async with _lock:
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

async def update_url(url: Optional[str]) -> None:
    """Update stripe URL"""
    global config
    config.stripe_url = url
    await save_config()

async def update_auth_mode(mode: int, email: Optional[str] = None, password: Optional[str] = None) -> None:
    """Update authentication mode and credentials"""
    global config
    config.auth_mode = mode
    if mode == 2:
        config.shared_email = email
        config.shared_password = password
    else:
        config.shared_email = None
        config.shared_password = None
    await save_config()

def get_config() -> BotConfig:
    """Get current configuration"""
    return config
