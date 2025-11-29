"""
Playwright Web Automation - Spotify Login Script
Automates Spotify login process, extracts subscription status
Supports HTTP, SOCKS4, SOCKS5, and rotating proxies
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import json
import os
import getpass
import time


class SpotifyLoginAutomation:
    def __init__(self, headless=True, slow_mo=200, proxy_config=None):
        self.headless = headless
        self.slow_mo = slow_mo
        self.proxy_config = proxy_config
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.responses = []

    def _capture_response(self, response):
        try:
            response_data = {
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text,
            }
            if "application/json" in response.headers.get("content-type", ""):
                try:
                    response_data["body"] = response.json()
                except:
                    response_data["body"] = None
            self.responses.append(response_data)
            
            if response.status >= 400 or "login" in response.url.lower() or "account" in response.url.lower():
                print(f"   [{response.status}] {response.url[:80]}")
        except:
            pass

    def start(self):
        self.playwright = sync_playwright().start()
        
        launch_options = {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
        }
        
        if self.proxy_config:
            launch_options["proxy"] = self.proxy_config
            print(f"   Using proxy: {self.proxy_config.get('server', 'Unknown')}")
            
        self.browser = self.playwright.chromium.launch(**launch_options)
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="en-US"
        )
        self.page = self.context.new_page()
        self.page.on("response", self._capture_response)
        return self

    def stop(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def get_subscription_status(self):
        subscription_url = "https://www.spotify.com/np-en/account/subscription/manage/"
        
        print("\n[Subscription] Navigating to subscription page...")
        self.page.goto(subscription_url, wait_until="networkidle", timeout=30000)
        self.page.wait_for_timeout(3000)
        
        try:
            close_btn = self.page.locator('button:has-text("Done")').first
            if close_btn.is_visible(timeout=2000):
                close_btn.click()
                self.page.wait_for_timeout(1000)
        except:
            pass
        
        subscription_info = {
            "plan": "Unknown",
            "status": "Unknown",
            "features": []
        }
        
        try:
            plan_card_selectors = [
                'h2:has-text("Spotify")',
                'h3:has-text("Spotify")',
                '[class*="subscription"] h2',
                '[class*="plan"] h2',
                'main h2'
            ]
            
            for selector in plan_card_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if elem.is_visible(timeout=2000):
                        plan_text = elem.inner_text().strip()
                        if "Free" in plan_text:
                            subscription_info["plan"] = "Spotify Free"
                            subscription_info["status"] = "Active"
                            break
                        elif "Premium" in plan_text and "Individual" in plan_text:
                            subscription_info["plan"] = "Premium Individual"
                            subscription_info["status"] = "Active"
                            break
                        elif "Premium" in plan_text and "Duo" in plan_text:
                            subscription_info["plan"] = "Premium Duo"
                            subscription_info["status"] = "Active"
                            break
                        elif "Premium" in plan_text and "Family" in plan_text:
                            subscription_info["plan"] = "Premium Family"
                            subscription_info["status"] = "Active"
                            break
                        elif "Premium" in plan_text and "Student" in plan_text:
                            subscription_info["plan"] = "Premium Student"
                            subscription_info["status"] = "Active"
                            break
                        elif "Premium" in plan_text:
                            subscription_info["plan"] = "Premium"
                            subscription_info["status"] = "Active"
                            break
                except:
                    continue
            
            main_content = ""
            try:
                main_elem = self.page.locator('main').first
                if main_elem.is_visible(timeout=2000):
                    main_content = main_elem.inner_text()
            except:
                pass
            
            if subscription_info["plan"] == "Unknown" and main_content:
                lines = main_content.split('\n')
                for line in lines[:20]:
                    line = line.strip()
                    if line == "Spotify Free":
                        subscription_info["plan"] = "Spotify Free"
                        subscription_info["status"] = "Active"
                        break
                    elif "Premium Individual" in line and len(line) < 30:
                        subscription_info["plan"] = "Premium Individual"
                        subscription_info["status"] = "Active"
                        break
                    elif "Premium Duo" in line and len(line) < 30:
                        subscription_info["plan"] = "Premium Duo"
                        subscription_info["status"] = "Active"
                        break
                    elif "Premium Family" in line and len(line) < 30:
                        subscription_info["plan"] = "Premium Family"
                        subscription_info["status"] = "Active"
                        break
            
            feature_indicators = [
                "1 Free account",
                "1 Premium account",
                "2 Premium accounts",
                "6 Premium accounts",
                "Music listening with ad breaks",
                "Ad-free music listening",
                "Streaming only",
                "Download to listen offline",
                "Play songs in any order"
            ]
            
            for feature in feature_indicators:
                if feature.lower() in main_content.lower():
                    subscription_info["features"].append(feature)
                    
        except Exception as e:
            print(f"   Error extracting subscription info: {str(e)}")
        
        return subscription_info

    def spotify_login(self, email, password):
        url = "https://accounts.spotify.com/en/login?continue=https%3A%2F%2Fopen.spotify.com%2F"
        
        result = {
            "success": False,
            "message": "",
            "url_before": url,
            "url_after": None,
            "cookies": [],
            "responses": [],
            "subscription": None
        }
        
        try:
            self.responses = []
            
            print("\n[Step 1] Opening Spotify login page...")
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            self.page.wait_for_timeout(2000)
            print("[Step 1] Page loaded")
            
            print("\n[Step 2] Entering email...")
            email_field = self.page.locator('input[data-testid="login-username"]')
            email_field.wait_for(state="visible", timeout=10000)
            email_field.click()
            self.page.wait_for_timeout(500)
            email_field.fill(email)
            print(f"[Step 2] Email entered: {email[:3]}***")
            
            print("\n[Step 3] Clicking Continue...")
            continue_btn = self.page.locator('button[data-testid="login-button"]')
            continue_btn.wait_for(state="visible", timeout=5000)
            continue_btn.click()
            self.page.wait_for_timeout(4000)
            print("[Step 3] Continue clicked")
            
            print("\n[Step 4] Clicking 'Log in with a password'...")
            password_btn = self.page.locator('button[data-encore-id="buttonTertiary"]:has-text("Log in with a password")')
            
            try:
                password_btn.wait_for(state="visible", timeout=8000)
                password_btn.click()
                self.page.wait_for_timeout(2000)
                print("[Step 4] Password option selected")
            except:
                alt_selectors = [
                    'button:has-text("Log in with a password")',
                    'text=Log in with a password',
                    '[data-encore-id="buttonTertiary"]'
                ]
                for sel in alt_selectors:
                    try:
                        elem = self.page.locator(sel).first
                        if elem.is_visible(timeout=2000):
                            elem.click()
                            self.page.wait_for_timeout(2000)
                            print(f"[Step 4] Password option clicked")
                            break
                    except:
                        continue
            
            print("\n[Step 5] Entering password...")
            password_field = self.page.locator('input[data-testid="login-password"]')
            
            try:
                password_field.wait_for(state="visible", timeout=15000)
            except:
                password_field = self.page.locator('input[type="password"]').first
                password_field.wait_for(state="visible", timeout=15000)
            
            password_field.click()
            self.page.wait_for_timeout(500)
            password_field.fill(password)
            print("[Step 5] Password entered")
            
            print("\n[Step 6] Clicking Log In...")
            login_btn = self.page.locator('button[data-testid="login-button"]')
            
            try:
                login_btn.wait_for(state="visible", timeout=5000)
                login_btn.click()
            except:
                alt_login = self.page.locator('button:has-text("Log in")').first
                alt_login.click()
            
            print("[Step 6] Log In clicked")
            
            print("\n[Step 7] Checking result...")
            self.page.wait_for_timeout(5000)
            
            result["url_after"] = self.page.url
            result["cookies"] = self.context.cookies()
            result["responses"] = self.responses
            
            if "open.spotify.com" in result["url_after"]:
                result["success"] = True
                result["message"] = "Login successful!"
                print("[Step 7] LOGIN SUCCESSFUL!")
                
                print("\n[Step 8] Getting subscription...")
                subscription = self.get_subscription_status()
                result["subscription"] = subscription
                print("[Step 8] Done")
                
            elif "incorrect" in self.page.content().lower() or "wrong" in self.page.content().lower():
                result["success"] = False
                result["message"] = "Incorrect username or password"
                print("[Step 7] FAILED - wrong credentials")
            else:
                result["success"] = False
                result["message"] = f"Status unclear. URL: {result['url_after']}"
                print(f"[Step 7] Status unclear")
                
        except PlaywrightTimeout as e:
            result["message"] = f"Timeout: {str(e)}"
            print(f"\n[ERROR] Timeout: {str(e)}")
        except Exception as e:
            result["message"] = f"Error: {str(e)}"
            print(f"\n[ERROR] {str(e)}")
            
        return result


def get_proxy_config():
    print("\n" + "=" * 50)
    print("PROXY CONFIGURATION")
    print("=" * 50)
    
    use_proxy = input("\nUse proxy? (yes/no): ").strip().lower()
    
    if use_proxy not in ['yes', 'y']:
        print("   No proxy")
        return None
    
    print("\nProxy type:")
    print("  1. HTTP")
    print("  2. SOCKS4")
    print("  3. SOCKS5")
    print("  4. Rotating (HTTP)")
    print("  5. Rotating (SOCKS5)")
    
    proxy_type = input("\nChoice (1-5): ").strip()
    
    type_map = {'1': 'http', '2': 'socks4', '3': 'socks5', '4': 'http', '5': 'socks5'}
    
    if proxy_type not in type_map:
        print("   Invalid. No proxy.")
        return None
    
    protocol = type_map[proxy_type]
    
    print("\nFormat: host:port or host:port:user:pass")
    proxy_string = input("Proxy: ").strip()
    
    if not proxy_string:
        return None
    
    parts = proxy_string.split(":")
    
    if len(parts) >= 4:
        host, port, username, password = parts[0], parts[1], parts[2], ":".join(parts[3:])
        proxy_config = {
            "server": f"{protocol}://{host}:{port}",
            "username": username,
            "password": password
        }
    elif len(parts) == 2:
        host, port = parts[0], parts[1]
        proxy_config = {"server": f"{protocol}://{host}:{port}"}
    else:
        print("   Invalid format.")
        return None
    
    print(f"   Proxy: {proxy_config['server']}")
    return proxy_config


def main():
    print("=" * 50)
    print("   Spotify Login Automation")
    print("=" * 50)
    
    proxy_config = get_proxy_config()
    
    print("\n" + "=" * 50)
    print("SPOTIFY LOGIN")
    print("=" * 50)
    
    email = input("\nEmail: ")
    password = getpass.getpass("Password: ")
    
    if not email or not password:
        print("\n[ERROR] Email and password required!")
        return
    
    print("\n" + "=" * 50)
    print("Starting automation...")
    print("=" * 50)
    
    automation = SpotifyLoginAutomation(headless=True, slow_mo=200, proxy_config=proxy_config)
    
    try:
        automation.start()
        result = automation.spotify_login(email, password)
        
        print("\n" + "=" * 50)
        print("RESULT")
        print("=" * 50)
        
        if result.get("subscription"):
            sub = result["subscription"]
            print(f"\n  PLAN: {sub.get('plan', 'Unknown')}")
            print(f"  STATUS: {sub.get('status', 'Unknown')}")
            if sub.get("features"):
                print("  FEATURES:")
                for feature in sub["features"]:
                    print(f"    - {feature}")
        
        print(f"\n  Login: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"  Cookies: {len(result['cookies'])}")
        
        if proxy_config:
            print(f"  Proxy: {proxy_config['server']}")
        
        print("\n" + "=" * 50)
        print("API RESPONSES")
        print("=" * 50)
        for resp in result["responses"][-20:]:
            print(f"  [{resp['status']}] {resp['url'][:80]}")
            if resp.get('body'):
                body_str = json.dumps(resp['body'])[:100]
                print(f"       Body: {body_str}...")
        
        return result
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        return {"success": False, "message": str(e)}
    finally:
        automation.stop()


if __name__ == "__main__":
    main()
