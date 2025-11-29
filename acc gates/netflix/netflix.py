import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response
import json
import re


class NetflixAutomation:
    def __init__(self, debug: bool = False, headless: bool = True, proxy: Optional[Dict[str, str]] = None):
        self.debug = debug
        self.headless = headless
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies: Dict[str, str] = {}
        self.flow_data: Dict[str, str] = {}
        self.country_code = "us"
        self.phone_code = "1"
        self.playwright: Any = None

    @staticmethod
    def parse_proxy(proxy_string: str) -> Optional[Dict[str, str]]:
        """
        Parse proxy string in various formats:
        - ip:port
        - ip:port:username:password
        - protocol://ip:port
        - protocol://username:password@ip:port
        
        Supported protocols: http, https, socks4, socks5
        """
        if not proxy_string or proxy_string.strip() == '':
            return None
        
        proxy_string = proxy_string.strip()
        
        protocol = 'http'
        username = None
        password = None
        host = None
        port = None
        
        if '://' in proxy_string:
            protocol, rest = proxy_string.split('://', 1)
            protocol = protocol.lower()
        else:
            rest = proxy_string
        
        if '@' in rest:
            auth_part, host_part = rest.rsplit('@', 1)
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
            host_port = host_part
        else:
            host_port = rest
        
        parts = host_port.split(':')
        
        if len(parts) == 2:
            host, port = parts[0], parts[1]
        elif len(parts) == 4 and username is None:
            host, port, username, password = parts
        elif len(parts) >= 2:
            host, port = parts[0], parts[1]
        else:
            return None
        
        if protocol in ['socks4', 'socks5']:
            server = f"socks5://{host}:{port}" if protocol == 'socks5' else f"socks4://{host}:{port}"
        else:
            server = f"http://{host}:{port}"
        
        proxy_config = {'server': server}
        
        if username and password:
            proxy_config['username'] = username
            proxy_config['password'] = password
        
        return proxy_config

    def log_debug(self, message):
        if self.debug:
            print(f"[DEBUG] {message}")

    async def initialize_browser(self):
        self.log_debug("Initializing Playwright browser")
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Ch-Ua': '"Not:A-Brand";v="24", "Chromium";v="134"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
        }
        
        if self.proxy:
            context_options['proxy'] = self.proxy
            self.log_debug(f"Using proxy: {self.proxy.get('server')}")
        
        self.context = await self.browser.new_context(**context_options)
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = {
                runtime: {}
            };
        """)
        
        self.page = await self.context.new_page()
        self.log_debug("Browser initialized successfully")

    async def get_geolocation(self):
        self.log_debug("Getting geolocation data")
        
        try:
            response = await self.page.goto(
                "https://geolocation.onetrust.com/cookieconsentpub/v1/geo/location",
                wait_until='networkidle',
                timeout=30000
            )
            
            content = await response.text()
            
            try:
                data = json.loads(content)
            except:
                match = re.search(r'{\s*"country"\s*:\s*"([^"]+)"', content)
                if match:
                    data = {'country': match.group(1)}
                else:
                    raise Exception("Could not parse geolocation response")
            
            self.country_code = data.get('country', 'us').lower()
            self.log_debug(f"Detected country: {self.country_code}")
            
            country_codes = {
                "np": "977",
                "us": "1",
                "in": "91",
                "gb": "44",
                "ca": "1",
                "au": "61",
                "de": "49",
                "fr": "33",
                "es": "34",
                "it": "39",
                "br": "55",
                "mx": "52",
                "jp": "81",
                "kr": "82",
            }
            self.phone_code = country_codes.get(self.country_code, "1")
            
        except Exception as e:
            self.log_debug(f"Geolocation failed, using default US settings: {str(e)}")
            self.country_code = "us"
            self.phone_code = "1"

    async def get_initial_cookies(self):
        self.log_debug("Getting initial Netflix cookies")
        url = f"https://www.netflix.com/{self.country_code}/"
        
        await self.page.goto(url, wait_until='networkidle', timeout=60000)
        
        cookies = await self.context.cookies()
        self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        self.log_debug(f"Initial cookies: {list(self.cookies.keys())}")
        
        return await self.page.content()

    async def get_login_page(self):
        self.log_debug("Navigating to login page")
        url = f"https://www.netflix.com/{self.country_code}-fr/login"
        
        await self.page.goto(url, wait_until='networkidle', timeout=60000)
        
        cookies = await self.context.cookies()
        self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        
        content = await self.page.content()
        
        patterns = [
            r'"flowSessionId\\":\\"([^"]+)\\"',
            r'"flowSessionId":"([^"]+)"',
            r'flowSessionId[=:]["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            flow_match = re.search(pattern, content)
            if flow_match:
                self.flow_data['flowSessionId'] = flow_match.group(1)
                break
        
        patterns = [
            r'"clcsSessionId\\":\\"([^"]+)\\"',
            r'"clcsSessionId":"([^"]+)"',
            r'clcsSessionId[=:]["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            clcs_match = re.search(pattern, content)
            if clcs_match:
                self.flow_data['clcsSessionId'] = clcs_match.group(1)
                break
        
        if self.flow_data.get('flowSessionId'):
            self.log_debug(f"Extracted flowSessionId: {self.flow_data['flowSessionId']}")
        if self.flow_data.get('clcsSessionId'):
            self.log_debug(f"Extracted clcsSessionId: {self.flow_data['clcsSessionId']}")
        
        return content

    async def perform_login(self, email, password):
        self.log_debug("Performing login via browser automation")
        
        try:
            await self.page.wait_for_selector('input[name="userLoginId"], input[id="id_userLoginId"], input[data-uia="login-field"]', timeout=15000)
            
            email_selectors = [
                'input[name="userLoginId"]',
                'input[id="id_userLoginId"]',
                'input[data-uia="login-field"]',
                'input[type="email"]',
                'input[autocomplete="email"]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_input = await self.page.query_selector(selector)
                    if email_input:
                        await email_input.click()
                        await email_input.fill('')
                        await email_input.type(email, delay=50)
                        email_filled = True
                        self.log_debug(f"Filled email using selector: {selector}")
                        break
                except Exception as e:
                    self.log_debug(f"Failed with selector {selector}: {str(e)}")
                    continue
            
            if not email_filled:
                raise Exception("Could not find email input field")
            
            await asyncio.sleep(0.5)
            
            password_selectors = [
                'input[name="password"]',
                'input[id="id_password"]',
                'input[data-uia="password-field"]',
                'input[type="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_input = await self.page.query_selector(selector)
                    if password_input:
                        await password_input.click()
                        await password_input.fill('')
                        await password_input.type(password, delay=50)
                        password_filled = True
                        self.log_debug(f"Filled password using selector: {selector}")
                        break
                except Exception as e:
                    self.log_debug(f"Failed with selector {selector}: {str(e)}")
                    continue
            
            if not password_filled:
                raise Exception("Could not find password input field")
            
            remember_me_selectors = [
                'input[name="rememberMe"]',
                'input[data-uia="rememberMe"]',
                'input[type="checkbox"]'
            ]
            
            for selector in remember_me_selectors:
                try:
                    checkbox = await self.page.query_selector(selector)
                    if checkbox:
                        is_checked = await checkbox.is_checked()
                        if not is_checked:
                            await checkbox.click()
                            self.log_debug("Checked 'Remember Me' checkbox")
                        break
                except:
                    continue
            
            await asyncio.sleep(0.5)
            
            submit_selectors = [
                'button[data-uia="login-submit-button"]',
                'button[type="submit"]',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                '.login-button',
                'button.btn'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit_button = await self.page.query_selector(selector)
                    if submit_button:
                        await submit_button.click()
                        submitted = True
                        self.log_debug(f"Clicked submit using selector: {selector}")
                        break
                except Exception as e:
                    self.log_debug(f"Failed submit with selector {selector}: {str(e)}")
                    continue
            
            if not submitted:
                await self.page.keyboard.press('Enter')
                self.log_debug("Pressed Enter to submit form")
            
            self.log_debug("Waiting for login response...")
            
            await asyncio.sleep(3)
            
            try:
                await self.page.wait_for_url('**/browse**', timeout=15000)
                
                cookies = await self.context.cookies()
                self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                
                self.log_debug("Login successful - redirected to browse page")
                return {
                    'status': 'success',
                    'cookies': self.cookies,
                    'message': 'Login successful'
                }
                
            except Exception as timeout_error:
                self.log_debug(f"Browse redirect timeout: {str(timeout_error)}")
                
                current_url = self.page.url
                self.log_debug(f"Current URL after login attempt: {current_url}")
                
                if '/browse' in current_url or '/profiles' in current_url:
                    cookies = await self.context.cookies()
                    self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                    return {
                        'status': 'success',
                        'cookies': self.cookies,
                        'message': 'Login successful'
                    }
                
                page_content = await self.page.content()
                
                error_selectors = [
                    '.ui-message-contents',
                    '[data-uia="error-message-container"]',
                    '.login-error',
                    '.error-message',
                    '[class*="error"]'
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = await self.page.query_selector(selector)
                        if error_element:
                            error_text = await error_element.inner_text()
                            if error_text.strip():
                                self.log_debug(f"Found error message: {error_text}")
                                return {
                                    'status': 'error',
                                    'message': error_text.strip()
                                }
                    except:
                        continue
                
                error_patterns = {
                    'Invalid credentials': 'Invalid email or password',
                    'incorrect password': 'Incorrect password',
                    'cannot find an account': 'Account not found',
                    'too many attempts': 'Too many attempts, please try again later',
                    'throttling': 'Too many attempts, please try again later',
                    'unrecognized_email': 'Email not recognized',
                    'FORMER_MEMBER': 'Former member account',
                    'NEVER_MEMBER': 'Account does not exist',
                    'subscription': 'Subscription required',
                    'payment': 'Payment required',
                    'membership': 'Membership issue',
                    'expired': 'Account expired',
                    'plan': 'Plan selection required',
                    'billing': 'Billing issue',
                    'restart your membership': 'Membership needs restart',
                    'finish signing up': 'Signup not completed',
                    'choose a plan': 'Plan selection required'
                }
                
                for pattern, message in error_patterns.items():
                    if pattern.lower() in page_content.lower():
                        return {
                            'status': 'error',
                            'message': message
                        }
                
                if '/login' in current_url:
                    return {
                        'status': 'error',
                        'message': 'Login failed - still on login page'
                    }
                
                return {
                    'status': 'unknown',
                    'message': 'Login status unclear - please check manually',
                    'current_url': current_url
                }
                
        except Exception as e:
            self.log_debug(f"Login error: {str(e)}")
            return {
                'status': 'error',
                'message': f'Login process failed: {str(e)}'
            }

    async def login(self, email, password):
        try:
            await self.initialize_browser()
            await self.get_geolocation()
            await self.get_initial_cookies()
            await self.get_login_page()
            return await self.perform_login(email, password)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Login process failed: {str(e)}'
            }
        finally:
            await self.cleanup()

    async def cleanup(self):
        self.log_debug("Cleaning up browser resources")
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.log_debug(f"Cleanup error: {str(e)}")

    async def take_screenshot(self, path="screenshot.png"):
        if self.page:
            await self.page.screenshot(path=path, full_page=True)
            self.log_debug(f"Screenshot saved to {path}")

    async def get_current_cookies(self):
        if self.context:
            cookies = await self.context.cookies()
            return {cookie['name']: cookie['value'] for cookie in cookies}
        return {}


async def main():
    print("Netflix Login Automation (Playwright)")
    print("--------------------------------------")
    
    use_proxy = input("Do you want to use a proxy? (y/n): ").strip().lower()
    
    proxy = None
    if use_proxy == 'y' or use_proxy == 'yes':
        print("\nProxy formats supported:")
        print("  - ip:port")
        print("  - ip:port:username:password")
        print("  - http://ip:port")
        print("  - http://username:password@ip:port")
        print("  - socks5://ip:port")
        print("  - socks5://username:password@ip:port")
        print("  - socks4://ip:port")
        
        proxy_string = input("\nEnter your proxy: ").strip()
        proxy = NetflixAutomation.parse_proxy(proxy_string)
        
        if proxy:
            print(f"Proxy configured: {proxy.get('server')}")
            if proxy.get('username'):
                print(f"With authentication: {proxy.get('username')}:****")
        else:
            print("Invalid proxy format. Continuing without proxy.")
    
    print()
    email = input("Enter your Netflix email: ")
    password = input("Enter your Netflix password: ")

    netflix = NetflixAutomation(debug=True, headless=True, proxy=proxy)
    result = await netflix.login(email, password)

    print("\nResult:")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")

    if result.get('status') == 'success':
        print("\nLogin successful! Cookies obtained:")
        for name, value in result.get('cookies', {}).items():
            print(f"{name}: {value[:50]}..." if len(value) > 50 else f"{name}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
