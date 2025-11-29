import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import urlparse
import json
import asyncio
import ipaddress
import dns.resolver
import ssl
import socket
from datetime import datetime

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

class AdvancedSiteChecker:
    """Advanced website analyzer for detecting captcha, security, gateways, and technologies"""
    
    def __init__(self):
        # Multiple user agents for better detection accuracy
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.headers = {
            'User-Agent': self.user_agents[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def is_safe_url(self, url):
        """Validate URL to prevent SSRF attacks (supports IPv4 and IPv6)"""
        try:
            import socket
            parsed = urlparse(url)
            
            # Only allow http/https
            if parsed.scheme not in ['http', 'https']:
                return False, "Only HTTP/HTTPS URLs are allowed"
            
            # Get hostname and port
            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid URL"
            
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            # Optionally restrict ports to standard web ports
            if port not in [80, 443, 8080, 8443]:
                return False, f"Port {port} is not allowed"
            
            # Resolve all IP addresses (IPv4 and IPv6)
            try:
                addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                
                for family, socktype, proto, canonname, sockaddr in addr_info:
                    ip = sockaddr[0]
                    ip_obj = ipaddress.ip_address(ip)
                    
                    # Block private/local/reserved/multicast IPs
                    if any([
                        ip_obj.is_private,
                        ip_obj.is_loopback,
                        ip_obj.is_link_local,
                        ip_obj.is_reserved,
                        ip_obj.is_multicast,
                        ip_obj.is_unspecified
                    ]):
                        return False, f"Blocked IP address: {ip}"
                    
                    # Block metadata endpoints
                    if ip in ['169.254.169.254', 'fd00:ec2::254']:
                        return False, "Metadata endpoints are not allowed"
                        
            except socket.gaierror:
                return False, "Cannot resolve hostname"
            
            return True, "OK"
        except Exception as e:
            return False, f"URL validation error: {str(e)}"
    
    def safe_request_with_redirects(self, url, max_redirects=5, max_retries=3):
        """Perform request with SSRF-safe redirect handling and retry logic"""
        import socket
        import time
        
        for retry in range(max_retries):
            try:
                for redirect_count in range(max_redirects + 1):
                    # Validate current URL
                    is_safe, reason = self.is_safe_url(url)
                    if not is_safe:
                        raise Exception(f"Blocked redirect to unsafe URL: {reason}")
                    
                    # Make request without auto-redirects with retry logic
                    try:
                        response = self.session.get(
                            url,
                            timeout=20,
                            allow_redirects=False,
                            verify=True
                        )
                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                        if retry < max_retries - 1:
                            time.sleep(2 ** retry)  # Exponential backoff
                            continue
                        raise Exception(f"Connection failed after {max_retries} retries: {str(e)}")
                    
                    # Check if it's a redirect
                    if response.status_code in [301, 302, 303, 307, 308]:
                        if redirect_count >= max_redirects:
                            raise Exception("Too many redirects")
                        
                        # Get redirect location
                        location = response.headers.get('Location')
                        if not location:
                            raise Exception("Redirect without Location header")
                        
                        # Handle relative redirects
                        from urllib.parse import urljoin
                        url = urljoin(url, location)
                    else:
                        # Not a redirect, return the response
                        response.raise_for_status()  # Raise error for bad status codes
                        return response
                
                raise Exception("Redirect loop detected")
            except requests.exceptions.RequestException as e:
                if retry < max_retries - 1:
                    time.sleep(2 ** retry)
                    continue
                raise
        
        raise Exception(f"Request failed after {max_retries} retries")
    
    def analyze_url(self, url):
        """Main analysis function with advanced multi-layer detection (blocking - use in executor)"""
        try:
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Make SSRF-safe request with redirect validation
            response = self.safe_request_with_redirects(url, max_redirects=5)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all content for comprehensive analysis
            all_scripts = ' '.join([str(script.get('src', '')) for script in soup.find_all('script')])
            all_script_content = ' '.join([str(script.string or '') for script in soup.find_all('script')])
            all_links = ' '.join([str(link.get('href', '')) for link in soup.find_all('link')])
            all_meta = ' '.join([str(meta.get('content', '')) + ' ' + str(meta.get('name', '')) for meta in soup.find_all('meta')])
            all_forms = ' '.join([str(form) for form in soup.find_all('form')])
            all_noscript = ' '.join([str(noscript) for noscript in soup.find_all('noscript')])
            all_iframes = ' '.join([str(iframe.get('src', '')) for iframe in soup.find_all('iframe')])
            
            # Get cookies for analysis
            cookies_str = ' '.join([f"{k}={v}" for k, v in response.cookies.items()])
            
            # Combine all content for maximum detection accuracy
            all_content = ' '.join([
                html_content,
                all_scripts,
                all_script_content,
                all_links,
                all_meta,
                all_forms,
                all_noscript,
                all_iframes,
                cookies_str,
                str(response.headers)
            ])
            
            # ENHANCED: Check if this is an ecommerce site, then also check checkout/cart pages
            is_ecommerce = bool(re.search(r'woocommerce|shopify|magento|prestashop|opencart|bigcommerce|/cart|/checkout|add.*to.*cart|shopping.*cart', all_content, re.I))
            
            checkout_content = ''
            payment_methods_soup = None
            
            if is_ecommerce:
                # Try to fetch checkout/cart/payment-methods pages for better gateway detection
                from urllib.parse import urljoin
                checkout_urls = [
                    urljoin(response.url, '/my-account/payment-methods/'),  # WooCommerce payment methods page (KEY!)
                    urljoin(response.url, '/checkout'),
                    urljoin(response.url, '/checkout/'),
                    urljoin(response.url, '/cart'),
                    urljoin(response.url, '/cart/'),
                    urljoin(response.url, '/basket'),
                    urljoin(response.url, '/order'),
                    urljoin(response.url, '/my-account/')  # My account page
                ]
                
                for checkout_url in checkout_urls:
                    try:
                        checkout_resp = self.safe_request_with_redirects(checkout_url, max_redirects=3)
                        if checkout_resp.status_code == 200:
                            checkout_soup = BeautifulSoup(checkout_resp.text, 'html.parser')
                            # Extract content from checkout page
                            checkout_scripts = ' '.join([str(script.get('src', '')) for script in checkout_soup.find_all('script')])
                            checkout_script_content = ' '.join([str(script.string or '') for script in checkout_soup.find_all('script')])
                            checkout_content += ' ' + checkout_resp.text + ' ' + checkout_scripts + ' ' + checkout_script_content
                            
                            # Store payment methods page soup separately for advanced detection
                            if 'payment-methods' in checkout_url:
                                payment_methods_soup = checkout_soup
                    except:
                        continue  # Silently skip if checkout page doesn't exist
            
            # Combine main page + checkout pages for better detection
            all_content = all_content + ' ' + checkout_content
            
            # Advanced multi-layer analysis with cookies and headers
            captcha = self.detect_captcha(all_content, soup, response.headers, response.cookies)
            security = self.detect_security(all_content, soup, response.headers, response.cookies)
            gateways = self.detect_gateways(all_content, soup)
            technology = self.detect_technology(all_content, soup, response.headers, response.cookies)
            cdn = self.detect_cdn(all_content, response.headers, response.url)
            analytics = self.detect_analytics(all_content, soup)
            chat_widgets = self.detect_chat_widgets(all_content)
            card_save_auth = self.detect_card_save_auth(all_content, soup)
            dns_info = self.get_dns_info(response.url)
            
            return {
                'url': response.url,
                'captcha': captcha,
                'security': security,
                'gateways': gateways,
                'technology': technology,
                'cdn': cdn,
                'analytics': analytics,
                'chat': chat_widgets,
                'card_save_auth': card_save_auth,
                'ip': dns_info['ips'][0] if dns_info['ips'] else 'Unknown',
                'status': 'success'
            }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'status': 'error'
            }
    
    def detect_captcha(self, html, soup, headers, cookies=None):
        """Detect CAPTCHA systems with maximum accuracy - multi-pattern detection"""
        captcha_types = []
        html_lower = html.lower()
        cookies_str = str(cookies).lower() if cookies else ''
        
        # reCAPTCHA detection (comprehensive patterns)
        recaptcha_patterns = [
            r'google\.com/recaptcha', r'grecaptcha', r'g-recaptcha',
            r'recaptcha/api\.js', r'recaptcha/api2', r'recaptcha__',
            r'data-sitekey=', r'6L[a-zA-Z0-9_-]{38}'
        ]
        if any(re.search(pattern, html, re.I) for pattern in recaptcha_patterns):
            if 'recaptcha/enterprise' in html_lower or 'grecaptcha.enterprise' in html_lower:
                captcha_types.append('reCAPTCHA Enterprise')
            elif 'grecaptcha.execute' in html_lower or 'action:' in html_lower and 'recaptcha' in html_lower:
                captcha_types.append('reCAPTCHA v3')
            elif 'g-recaptcha' in html_lower or 'recaptcha/api.js' in html_lower:
                captcha_types.append('reCAPTCHA v2')
            else:
                captcha_types.append('reCAPTCHA')
        
        # hCaptcha detection (enhanced)
        hcaptcha_patterns = [
            r'hcaptcha\.com', r'h-captcha', r'data-hcaptcha',
            r'hcaptcha/api\.js', r'hcaptcha\.render'
        ]
        if any(re.search(pattern, html, re.I) for pattern in hcaptcha_patterns):
            captcha_types.append('hCaptcha')
        
        # Cloudflare Turnstile (advanced detection)
        turnstile_patterns = [
            r'challenges\.cloudflare\.com/turnstile', r'cf-turnstile',
            r'turnstile/v0', r'_cf_chl_opt'
        ]
        if any(re.search(pattern, html, re.I) for pattern in turnstile_patterns):
            captcha_types.append('Cloudflare Turnstile')
        
        # Cloudflare Challenge (legacy detection)
        cf_challenge_patterns = [
            r'cf_chl_jschl', r'cf-challenge', r'__cf_chl_jschl_tk__',
            r'cf-challenge-body', r'challenge-platform'
        ]
        if any(re.search(pattern, html, re.I) for pattern in cf_challenge_patterns):
            if 'Cloudflare Turnstile' not in captcha_types:
                captcha_types.append('Cloudflare Challenge')
        
        # FriendlyCaptcha
        if any(re.search(pattern, html, re.I) for pattern in [r'friendlycaptcha', r'frc-captcha', r'friendly-challenge']):
            captcha_types.append('FriendlyCaptcha')
        
        # FunCaptcha/ArkoseLabs (enhanced)
        funcaptcha_patterns = [
            r'funcaptcha', r'arkoselabs', r'arkose',
            r'enforcement\.arkoselabs', r'api\.funcaptcha'
        ]
        if any(re.search(pattern, html, re.I) for pattern in funcaptcha_patterns):
            captcha_types.append('FunCaptcha/Arkose')
        
        # GeeTest
        if any(re.search(pattern, html, re.I) for pattern in [r'geetest\.com', r'gt-captcha', r'geetest_']):
            captcha_types.append('GeeTest')
        
        # AWS WAF Captcha
        if any(re.search(pattern, html, re.I) for pattern in [r'awswaf', r'aws-waf-token', r'AwsWafToken']):
            captcha_types.append('AWS WAF Captcha')
        
        # PerimeterX/HUMAN Captcha
        if any(re.search(pattern, html, re.I) for pattern in [r'perimeterx', r'px-captcha', r'human-security', r'/_px/']):
            captcha_types.append('PerimeterX/HUMAN')
        
        # DataDome
        if any(re.search(pattern, html, re.I) for pattern in [r'datadome\.co', r'dd-captcha', r'DataDome']):
            captcha_types.append('DataDome')
        
        # MTCaptcha
        if re.search(r'mtcaptcha|mt-captcha', html, re.I):
            captcha_types.append('MTCaptcha')
        
        # SimpleCaptcha
        if re.search(r'simplecaptcha|simple-captcha', html, re.I):
            captcha_types.append('SimpleCaptcha')
        
        # BotDetect
        if re.search(r'botdetect|captcha\.ashx', html, re.I):
            captcha_types.append('BotDetect')
        
        # Kasada Bot Detection
        if re.search(r'kasada|kpsdk', html, re.I) or '149e9513-01fa-4fb0-aad4-566afd725d1b' in cookies_str:
            captcha_types.append('Kasada')
        
        # KeyCAPTCHA
        if re.search(r'keycaptcha', html, re.I):
            captcha_types.append('KeyCAPTCHA')
        
        # SolveMedia (reCAPTCHA alternative)
        if re.search(r'solvemedia|adcopy', html, re.I):
            captcha_types.append('SolveMedia')
        
        # Capy Puzzle CAPTCHA
        if re.search(r'capy\.jp|puzzle-captcha', html, re.I):
            captcha_types.append('Capy Puzzle')
        
        # TencentCaptcha
        if re.search(r'tencent.*captcha|captcha\.qq\.com', html, re.I):
            captcha_types.append('Tencent Captcha')
        
        # Cookie-based captcha detection
        if 'cf_clearance' in cookies_str:
            if 'Cloudflare Turnstile' not in captcha_types and 'Cloudflare Challenge' not in captcha_types:
                captcha_types.append('Cloudflare Challenge')
        
        return captcha_types if captcha_types else ['None']
    
    def detect_security(self, html, soup, headers, cookies=None):
        """Detect security systems and WAF with advanced multi-vector analysis"""
        security_systems = []
        html_lower = html.lower()
        headers_str = str(headers).lower()
        cookies_str = str(cookies).lower() if cookies else ''
        
        # Cloudflare detection (comprehensive with cookies)
        cf_indicators = [
            'cloudflare' in headers_str,
            'cf-ray' in headers,
            'cf-cache-status' in headers,
            '__cfduid' in html_lower or '__cfduid' in cookies_str,
            'cloudflare' in html_lower,
            re.search(r'cdn-cgi/', html, re.I),
            re.search(r'cloudflare\.com|cloudflare-dns', html, re.I),
            'cf-request-id' in headers,
            '__cf_bm' in html_lower or '__cf_bm' in cookies_str,
            'cf_clearance' in cookies_str,
            '_cfuvid' in cookies_str
        ]
        if any(cf_indicators):
            if 'cf-mitigated' in headers or 'cf-bot-management' in headers_str or '__cfbm' in cookies_str:
                security_systems.append('CloudFlare Bot Management')
            else:
                security_systems.append('CloudFlare')
        
        # PerimeterX/HUMAN Security (enhanced with cookies)
        px_indicators = [
            re.search(r'perimeterx|_px\d+|px-captcha|pxvid|pxhd', html, re.I),
            'perimeterx.net' in html_lower,
            '/_px/' in html_lower,
            'px-cdn.net' in html_lower,
            '_px' in cookies_str or '_pxhd' in cookies_str or '_pxvid' in cookies_str
        ]
        if any(px_indicators):
            security_systems.append('PerimeterX/HUMAN')
        
        # Akamai (comprehensive detection with cookies)
        akamai_indicators = [
            'akamai' in headers_str,
            '_abck' in html_lower or '_abck' in cookies_str,
            'bm_sz' in html_lower or 'bm_sz' in cookies_str,
            'ak_bmsc' in html_lower or 'ak_bmsc' in cookies_str,
            re.search(r'akamai\.net|akamaicdn|akamaihd', html, re.I),
            'akamai-ghost' in headers_str,
            'bm_sv' in cookies_str or 'rt' in cookies_str
        ]
        if any(akamai_indicators):
            if '_abck' in cookies_str or 'bm_sz' in cookies_str:
                security_systems.append('Akamai Bot Manager')
            else:
                security_systems.append('Akamai')
        
        # Imperva/Incapsula (with cookie detection)
        imperva_indicators = [
            'incapsula' in headers_str,
            'incap_ses' in html_lower or 'incap_ses' in cookies_str,
            'visid_incap' in html_lower or 'visid_incap' in cookies_str,
            'incapsula.com' in html_lower,
            re.search(r'imperva|incapsula', html, re.I),
            'nlbi' in cookies_str or 'incap_' in cookies_str
        ]
        if any(imperva_indicators):
            security_systems.append('Imperva/Incapsula')
        
        # AWS WAF (enhanced)
        aws_indicators = [
            re.search(r'aws-waf|x-amzn-waf|awswaf', headers_str, re.I),
            'x-amzn-requestid' in headers_str and 'waf' in html_lower
        ]
        if any(aws_indicators):
            security_systems.append('AWS WAF')
        
        # Sucuri
        if any([re.search(r'sucuri|x-sucuri', html, re.I), 'sucuri' in headers_str]):
            security_systems.append('Sucuri')
        
        # Wordfence (WordPress security)
        if re.search(r'wordfence|wfwaf|wordfence-waf', html, re.I):
            security_systems.append('Wordfence')
        
        # DataDome (with cookie detection)
        if any([re.search(r'datadome\.co|datadome', html, re.I), 'datadome' in headers_str, 'datadome' in cookies_str]):
            security_systems.append('DataDome')
        
        # Shape Security (acquired by F5)
        if any([re.search(r'shape-security|shapesecurity', html, re.I), 'shapesecurity' in cookies_str]):
            security_systems.append('Shape Security')
        
        # Kasada
        if re.search(r'kasada|kpsdk', html, re.I) or '149e9513-01fa-4fb0-aad4-566afd725d1b' in cookies_str:
            security_systems.append('Kasada')
        
        # Distil Networks (now part of Imperva)
        if re.search(r'distil_|distilnetworks', html, re.I) or 'distil' in cookies_str:
            security_systems.append('Distil Networks')
        
        # Signal Sciences (now part of Fastly)
        if re.search(r'signal-?sciences|sigsci', html, re.I):
            security_systems.append('Signal Sciences')
        
        # Reblaze
        if re.search(r'reblaze|rbzid|reblaze\.com', html, re.I):
            security_systems.append('Reblaze')
        
        # Fastly WAF
        if 'fastly' in headers_str or 'fastly' in html_lower:
            security_systems.append('Fastly')
        
        # Radware
        if re.search(r'radware|x-cdn.*radware', html, re.I):
            security_systems.append('Radware')
        
        # F5 (BIG-IP)
        if any(['f5' in headers_str, 'bigip' in html_lower, re.search(r'TS[a-f0-9]{16}', html)]):
            security_systems.append('F5 BIG-IP')
        
        # Barracuda
        if re.search(r'barracuda', html, re.I):
            security_systems.append('Barracuda')
        
        # Fortinet FortiWeb
        if re.search(r'fortinet|fortiweb', html, re.I):
            security_systems.append('FortiWeb')
        
        # Cloudfront (AWS CDN with security)
        if 'cloudfront' in headers_str or 'cloudfront.net' in html_lower:
            security_systems.append('AWS CloudFront')
        
        return security_systems if security_systems else ['Unknown']
    
    def detect_gateways(self, html, soup):
        """Detect payment gateways with advanced pattern matching including WooCommerce plugins"""
        gateways = []
        html_lower = html.lower()
        
        # Stripe (comprehensive detection + WooCommerce + detailed patterns)
        stripe_patterns = [
            # Official Stripe.js
            r'js\.stripe\.com/v3|stripe\.com/v3',
            # Stripe API Keys
            r'pk_live_[\w]+|pk_test_[\w]+',
            # Stripe Elements
            r'stripe-card-element|stripe-cvc-element|wc-stripe-elements-field',
            # Stripe Tokens
            r'stripeToken|stripe\.createToken|stripe\.confirmCardPayment',
            # Stripe Checkout
            r'stripe-checkout|checkout\.stripe\.com',
            # WooCommerce Stripe Plugin
            r'woocommerce-gateway-stripe|wc-gateway-stripe',
            r'wc_stripe_params|stripe_params',
            r'payment_method_stripe',
            # Stripe source files
            r'/plugins/woocommerce-gateway-stripe/',
            # Stripe error containers
            r'stripe-source-errors',
            # Stripe Express Checkout
            r'wc-stripe-payment-request-button|wc-stripe-express-checkout'
        ]
        if any(re.search(pattern, html, re.I) for pattern in stripe_patterns):
            gateways.append('Stripe')
        
        # PayPal (enhanced)
        paypal_patterns = [
            r'paypal\.com|paypalobjects', r'paypal-button', r'paypal/sdk',
            r'paypal\.Buttons', r'payflow', r'braintreepayments.*paypal'
        ]
        if any(re.search(pattern, html, re.I) for pattern in paypal_patterns):
            gateways.append('PayPal')
        
        # Square
        square_patterns = [r'squareup\.com|square\.com', r'sq-payment', r'squarecdn', r'square-marketplace']
        if any(re.search(pattern, html, re.I) for pattern in square_patterns):
            gateways.append('Square')
        
        # Authorize.Net
        if re.search(r'authorize\.net|authorizenet', html, re.I):
            gateways.append('Authorize.Net')
        
        # Braintree
        if re.search(r'braintree|braintreegateway\.com|braintreepayments', html, re.I):
            gateways.append('Braintree')
        
        # Adyen
        if re.search(r'adyen\.com|adyen-checkout|adyen-encrypt', html, re.I):
            gateways.append('Adyen')
        
        # Razorpay
        if re.search(r'razorpay\.com|razorpay-checkout|checkout\.razorpay', html, re.I):
            gateways.append('Razorpay')
        
        # Mollie
        if re.search(r'mollie\.com|mollie-checkout|mollie\.api', html, re.I):
            gateways.append('Mollie')
        
        # 2Checkout (Verifone)
        if re.search(r'2checkout|2co\.com|verifone', html, re.I):
            gateways.append('2Checkout')
        
        # Amazon Pay
        if re.search(r'amazonpay|pay\.amazon|amazon-payments', html, re.I):
            gateways.append('Amazon Pay')
        
        # Apple Pay
        if re.search(r'apple-pay|applepay|ApplePaySession', html, re.I):
            gateways.append('Apple Pay')
        
        # Google Pay
        if re.search(r'google-pay|googlepay|pay\.google|google\.payments', html, re.I):
            gateways.append('Google Pay')
        
        # Klarna
        if re.search(r'klarna\.com|klarna-checkout|klarna-payments', html, re.I):
            gateways.append('Klarna')
        
        # Afterpay/Clearpay
        if re.search(r'afterpay\.com|afterpay-widget|clearpay', html, re.I):
            gateways.append('Afterpay')
        
        # Shop Pay (Shopify)
        if re.search(r'shop-pay|shoppay|shop\.app', html, re.I):
            gateways.append('Shop Pay')
        
        # Worldpay
        if re.search(r'worldpay|fisglobal', html, re.I):
            gateways.append('Worldpay')
        
        # Checkout.com
        if re.search(r'checkout\.com|checkout-sdk', html, re.I):
            gateways.append('Checkout.com')
        
        # PayU
        if re.search(r'payu\.com|payu-payment', html, re.I):
            gateways.append('PayU')
        
        # Skrill
        if re.search(r'skrill\.com|moneybookers', html, re.I):
            gateways.append('Skrill')
        
        # Payoneer
        if re.search(r'payoneer\.com', html, re.I):
            gateways.append('Payoneer')
        
        # Affirm
        if re.search(r'affirm\.com|affirm-checkout', html, re.I):
            gateways.append('Affirm')
        
        # Sezzle
        if re.search(r'sezzle\.com|sezzle-checkout', html, re.I):
            gateways.append('Sezzle')
        
        # Zip (QuadPay)
        if re.search(r'zip\.co|quadpay', html, re.I):
            gateways.append('Zip/QuadPay')
        
        # Mercado Pago
        if re.search(r'mercadopago|mercadolibre', html, re.I):
            gateways.append('Mercado Pago')
        
        # Paytm
        if re.search(r'paytm\.com|paytm-payment', html, re.I):
            gateways.append('Paytm')
        
        # Alipay
        if re.search(r'alipay\.com|alipay-checkout', html, re.I):
            gateways.append('Alipay')
        
        # WeChat Pay
        if re.search(r'wechatpay|wxpay|wechat-pay', html, re.I):
            gateways.append('WeChat Pay')
        
        # Coinbase Commerce (Crypto)
        if re.search(r'coinbase.*commerce|commerce\.coinbase', html, re.I):
            gateways.append('Coinbase Commerce')
        
        # BitPay (Bitcoin)
        if re.search(r'bitpay', html, re.I):
            gateways.append('BitPay')
        
        # PayFast (South Africa)
        if re.search(r'payfast\.co\.za|payfast', html, re.I):
            gateways.append('PayFast')
        
        # Flutterwave (Africa)
        if re.search(r'flutterwave|rave\.flutterwave', html, re.I):
            gateways.append('Flutterwave')
        
        # Paystack (Africa)
        if re.search(r'paystack', html, re.I):
            gateways.append('Paystack')
        
        # iyzico (Turkey)
        if re.search(r'iyzico|iyzipay', html, re.I):
            gateways.append('iyzico')
        
        # Paddle (SaaS payments)
        if re.search(r'paddle\.com|paddlejs|paddle-checkout', html, re.I):
            gateways.append('Paddle')
        
        # FastSpring
        if re.search(r'fastspring', html, re.I):
            gateways.append('FastSpring')
        
        # Gumroad
        if re.search(r'gumroad', html, re.I):
            gateways.append('Gumroad')
        
        return gateways if gateways else ['Unable to Fetch']
    
    def detect_card_save_auth(self, html, soup):
        """Advanced detection of card save/verification features (auth without charging)"""
        features = []
        html_lower = html.lower()
        detected = set()  # Avoid duplicates
        
        # ========== WOOCOMMERCE-SPECIFIC DETECTION ==========
        if re.search(r'woocommerce|wc-', html, re.I):
            # WooCommerce saved payment methods page (/my-account/payment-methods/)
            if re.search(r'/my-account/payment-methods|woocommerce-MyAccount.*payment.*methods', html, re.I):
                detected.add('WooCommerce Payment Methods Page (Card Save)')
            
            # WooCommerce saved payment methods table
            if re.search(r'woocommerce-SavedPaymentMethods|wc-saved-payment-methods|payment.*method.*table|saved.*cards.*table|shop_table.*payment_methods', html, re.I):
                detected.add('WooCommerce Saved Payment Methods')
            
            # WooCommerce tokenization
            if re.search(r'wc.*tokenization|woocommerce.*token|payment.*token.*wc|wc-.*-new-payment-method|WC_Payment_Token', html, re.I):
                detected.add('WooCommerce Payment Tokenization')
            
            # WooCommerce subscription with saved cards
            if re.search(r'woocommerce.*subscriptions?|wc.*subscription|wcs-payment-method', html, re.I):
                detected.add('WooCommerce Subscription (Auto-Billing)')
            
            # Payment method token inputs
            if re.search(r'woocommerce-SavedPaymentMethods-tokenInput|payment.*token.*id', html, re.I):
                detected.add('WooCommerce Token Storage')
        
        # ========== STRIPE DETECTION (Most Common) ==========
        stripe_detected = False
        if re.search(r'stripe\.com|stripe\.js|pk_live|pk_test|wc.*stripe|stripe-card-element', html, re.I):
            stripe_detected = True
            
            # Stripe SetupIntent (primary method for card verification)
            if re.search(r'setupIntent|SetupIntent|stripe\.confirmCardSetup|setup_intent', html, re.I):
                detected.add('Stripe SetupIntent (Card Auth)')
            
            # Stripe Payment Methods API
            if re.search(r'createPaymentMethod|attachPaymentMethod|payment_method|pm_\w+', html, re.I):
                detected.add('Stripe Payment Method Save')
            
            # Stripe Customer Portal / Saved Cards
            if re.search(r'customer\.invoice_settings|customer\.default_source|saved.*payment.*method.*stripe', html, re.I):
                detected.add('Stripe Customer Vault')
            
            # Stripe Elements with save option
            if re.search(r'stripe\.elements|wc-stripe-elements-field|stripe-card-element', html, re.I):
                if re.search(r'save|store|remember', html, re.I):
                    detected.add('Stripe Elements (Save Card)')
            
            # WooCommerce Stripe save checkbox
            if re.search(r'wc-stripe-new-payment-method|save.*card.*stripe', html, re.I):
                detected.add('Stripe WooCommerce Card Save')
        
        # ========== BRAINTREE DETECTION ==========
        braintree_detected = False
        if re.search(r'braintree|braintreegateway|braintreepayments', html, re.I):
            braintree_detected = True
            
            # Braintree Vault (tokenization)
            if re.search(r'vault|vaultManager|storeInVault|vaultCard', html, re.I):
                detected.add('Braintree Vault (Card Storage)')
            
            # Braintree Customer ID / Payment Methods
            if re.search(r'paymentMethodNonce|paymentMethodToken|customerId.*braintree', html, re.I):
                detected.add('Braintree Payment Token')
            
            # Braintree Hosted Fields
            if re.search(r'hostedFields.*create|braintree\.hostedFields', html, re.I):
                detected.add('Braintree Hosted Fields')
        
        # ========== AUTHORIZE.NET DETECTION ==========
        if re.search(r'authorize\.net|authorizenet', html, re.I):
            # CIM (Customer Information Manager)
            if re.search(r'customerProfileId|paymentProfileId|createCustomerProfile', html, re.I):
                detected.add('Authorize.Net CIM (Card Vault)')
            
            # Accept.js (tokenization)
            if re.search(r'accept\.js|acceptjs|dispatchData.*authData', html, re.I):
                detected.add('Authorize.Net Token')
        
        # ========== ADYEN DETECTION ==========
        if re.search(r'adyen\.com|adyen-checkout', html, re.I):
            # Adyen Tokenization
            if re.search(r'storePaymentMethod|recurringDetailReference|shopperReference', html, re.I):
                detected.add('Adyen Card Tokenization')
            
            # Adyen 3DS2 with save
            if re.search(r'enableStoreDetails|storeDetails.*true', html, re.I):
                detected.add('Adyen Store Details')
        
        # ========== SQUARE DETECTION ==========
        if re.search(r'squareup\.com|square\.com|sq-payment', html, re.I):
            # Square Card on File
            if re.search(r'card.*on.*file|customer.*card.*id|sq.*customerCardId', html, re.I):
                detected.add('Square Card on File')
            
            # Square Verify Buyer
            if re.search(r'verifyBuyer|sq-verify', html, re.I):
                detected.add('Square Verify Buyer')
        
        # ========== PAYPAL DETECTION ==========
        if re.search(r'paypal\.com|braintree.*paypal', html, re.I):
            # PayPal Vault
            if re.search(r'vault.*paypal|billing.*agreement|reference.*transaction', html, re.I):
                detected.add('PayPal Vault')
            
            # PayPal Subscriptions
            if re.search(r'subscription.*id.*paypal|billing.*plan', html, re.I):
                detected.add('PayPal Subscription Auth')
        
        # ========== RAZORPAY DETECTION ==========
        if re.search(r'razorpay', html, re.I):
            if re.search(r'customer.*token|saved.*card.*razorpay|token.*razorpay', html, re.I):
                detected.add('Razorpay Card Token')
        
        # ========== CHECKOUT.COM DETECTION ==========
        if re.search(r'checkout\.com|checkout-sdk', html, re.I):
            if re.search(r'customer.*id.*checkout|payment.*source.*id', html, re.I):
                detected.add('Checkout.com Card Storage')
        
        # ========== MOLLIE DETECTION ==========
        if re.search(r'mollie\.com', html, re.I):
            if re.search(r'mandateId|customerId.*mollie', html, re.I):
                detected.add('Mollie Mandate/Token')
        
        # ========== ZERO-DOLLAR AUTH DETECTION ==========
        zero_auth_patterns = [
            r'zero.*dollar.*authorization',
            r'\$0\.00.*auth|\$0.*verification',
            r'0\.00.*authorization|amount.*0.*verify',
            r'card.*verification.*value|CVV.*check',
            r'pre.*auth.*card|preauthorization',
            r'verify.*without.*charge|verify.*card.*valid'
        ]
        if any(re.search(pattern, html, re.I) for pattern in zero_auth_patterns):
            detected.add('Zero-Dollar Authorization')
        
        # ========== SUBSCRIPTION/RECURRING PATTERNS ==========
        if re.search(r'stripe|braintree|authorize\.net|adyen|square|checkout\.com|razorpay', html, re.I):
            recurring_patterns = [
                r'recurring.*billing.*setup',
                r'subscription.*payment.*method',
                r'auto.*billing|automatic.*payment',
                r'recurring.*charge.*authorization',
                r'billing.*agreement|payment.*agreement'
            ]
            if any(re.search(pattern, html, re.I) for pattern in recurring_patterns):
                detected.add('Recurring Billing Setup')
        
        # ========== API ENDPOINTS DETECTION ==========
        api_patterns = [
            r'/api/v\d+/payment[_-]?methods?/save',
            r'/api/v\d+/cards?/verify',
            r'/api/v\d+/customers?/cards?',
            r'/api/v\d+/vault',
            r'/api/v\d+/tokens?/card',
            r'payment[_-]?method[_-]?create',
            r'customer[_-]?profile',
            r'setupIntent.*create|setup[_-]?intents?'
        ]
        if any(re.search(pattern, html, re.I) for pattern in api_patterns):
            detected.add('Payment API (Card Storage)')
        
        # ========== FORM-BASED ADVANCED DETECTION ==========
        forms = soup.find_all('form')
        for form in forms:
            form_str = str(form).lower()
            
            # Check for save card checkbox with proper context
            has_save_option = bool(re.search(r'save.*this.*card|store.*payment.*method|remember.*card.*details|save.*for.*future|keep.*card.*on.*file', form_str, re.I))
            has_card_fields = bool(re.search(r'card[_-]?number|cardnumber|cc[_-]?number|credit[_-]?card|cvv|cvc|card[_-]?expiry', form_str, re.I))
            
            if has_save_option and has_card_fields:
                detected.add('Form-Based Card Save')
                break
        
        # ========== JAVASCRIPT TOKENIZATION LIBRARIES ==========
        tokenization_libs = [
            r'payment.*tokenize|tokenization\.js',
            r'card.*vault\.js|vaultjs',
            r'payment.*secure.*token',
            r'spreedly|spreedly-iframe',
            r'recurly\.js.*token',
            r'chargify.*token'
        ]
        if any(re.search(pattern, html, re.I) for pattern in tokenization_libs):
            detected.add('Third-Party Tokenization')
        
        # ========== CUSTOMER VAULT/PROFILE SYSTEMS ==========
        vault_patterns = [
            r'customer.*vault|vault.*customer',
            r'payment.*profile|billing.*profile',
            r'stored.*payment.*method',
            r'default.*payment.*source',
            r'manage.*saved.*cards',
            r'payment.*methods?.*on.*file'
        ]
        if any(re.search(pattern, html, re.I) for pattern in vault_patterns):
            # Only add if there's evidence of a payment gateway
            if re.search(r'stripe|braintree|authorize|adyen|square|paypal|checkout|razorpay|mollie', html, re.I):
                detected.add('Customer Payment Vault')
        
        # ========== ONE-CLICK CHECKOUT INDICATORS ==========
        if re.search(r'one.*click.*checkout|express.*checkout.*saved|instant.*checkout', html, re.I):
            if re.search(r'stripe|braintree|paypal|square', html, re.I):
                detected.add('One-Click Checkout (Saved Card)')
        
        # Convert set to sorted list
        features = sorted(list(detected))
        
        return features if features else ['Not Detected']
    
    def detect_technology(self, html, soup, headers, cookies=None):
        """Detect web technologies with comprehensive pattern analysis"""
        technologies = []
        html_lower = html.lower()
        headers_str = str(headers).lower()
        cookies_str = str(cookies).lower() if cookies else ''
        
        # WordPress (comprehensive)
        wp_patterns = [r'wp-content|wp-includes', r'/wp-json/', r'wordpress', r'wp-emoji']
        if any(re.search(pattern, html, re.I) for pattern in wp_patterns):
            technologies.append('WordPress')
        
        # WooCommerce
        woo_patterns = [r'woocommerce|wc-', r'product_cat|add-to-cart', r'woocommerce-', r'cart-fragments']
        if any(re.search(pattern, html, re.I) for pattern in woo_patterns):
            technologies.append('WooCommerce')
        
        # Shopify (enhanced)
        shopify_patterns = [
            'shopify.com' in html_lower, 'cdn.shopify' in html_lower, 'myshopify' in html_lower,
            'x-shopify' in headers_str, 'shopify-shop-id' in html_lower
        ]
        if any(shopify_patterns):
            technologies.append('Shopify')
        
        # Magento
        if re.search(r'magento|mage/cookies|catalogsearch|mage\.', html, re.I):
            technologies.append('Magento')
        
        # React (enhanced)
        react_patterns = [r'react|_react|__REACT', r'reactjs|react-dom', r'_reactRoot']
        if any(re.search(pattern, html, re.I) for pattern in react_patterns):
            technologies.append('React')
        
        # Vue.js (enhanced)
        vue_patterns = [r'vue\.js|vuejs', r'__vue__', r'v-if|v-for|v-model|v-bind', r'data-v-']
        if any(re.search(pattern, html, re.I) for pattern in vue_patterns):
            technologies.append('Vue.js')
        
        # Angular (comprehensive)
        angular_patterns = [r'angular', r'ng-app|ng-controller|ng-model', r'@angular/', r'_ngcontent']
        if any(re.search(pattern, html, re.I) for pattern in angular_patterns):
            technologies.append('Angular')
        
        # Next.js
        if re.search(r'next\.js|__next|_next/static|__NEXT_DATA__', html, re.I):
            technologies.append('Next.js')
        
        # Nuxt.js
        if re.search(r'nuxt\.js|__nuxt|_nuxt/|__NUXT__', html, re.I):
            technologies.append('Nuxt.js')
        
        # Django
        django_patterns = ['django' in headers_str, re.search(r'csrfmiddlewaretoken|django', html, re.I)]
        if any(django_patterns):
            technologies.append('Django')
        
        # Laravel
        if re.search(r'laravel|laravel_session|XSRF-TOKEN|laravel_token', html, re.I):
            technologies.append('Laravel')
        
        # Drupal
        if re.search(r'drupal|/sites/default|/sites/all|drupal-', html, re.I):
            technologies.append('Drupal')
        
        # Joomla
        if re.search(r'joomla|/components/com_|/modules/mod_', html, re.I):
            technologies.append('Joomla')
        
        # Wix
        if re.search(r'wix\.com|wixstatic|wix-|_wix', html, re.I):
            technologies.append('Wix')
        
        # Squarespace
        if re.search(r'squarespace|sqsp\.com|squarespace-cdn', html, re.I):
            technologies.append('Squarespace')
        
        # Webflow
        if re.search(r'webflow|wf-|webflow\.io|webflow\.com', html, re.I):
            technologies.append('Webflow')
        
        # PrestaShop
        if re.search(r'prestashop|ps_|presta-', html, re.I):
            technologies.append('PrestaShop')
        
        # OpenCart
        if re.search(r'opencart|route=product|catalog/view', html, re.I):
            technologies.append('OpenCart')
        
        # BigCommerce
        if re.search(r'bigcommerce|cdn\d+\.bigcommerce', html, re.I):
            technologies.append('BigCommerce')
        
        # Gatsby
        if re.search(r'gatsby|___gatsby', html, re.I):
            technologies.append('Gatsby')
        
        # Svelte/SvelteKit
        if re.search(r'svelte|__svelte|sveltekit', html, re.I):
            technologies.append('Svelte')
        
        # Express.js (Node.js)
        if 'x-powered-by' in headers and 'express' in headers_str:
            technologies.append('Express.js')
        
        # ASP.NET
        if re.search(r'__viewstate|__eventvalidation|asp\.net', html, re.I) or 'aspnet' in headers_str:
            technologies.append('ASP.NET')
        
        # Ruby on Rails
        if 'x-powered-by' in headers and 'phusion passenger' in headers_str or re.search(r'rails|_rails_', html, re.I):
            technologies.append('Ruby on Rails')
        
        # Flask/FastAPI (Python)
        if 'flask' in html_lower or 'fastapi' in html_lower:
            technologies.append('Python Framework')
        
        # jQuery
        if re.search(r'jquery|jQuery\.', html, re.I):
            technologies.append('jQuery')
        
        # Bootstrap
        if re.search(r'bootstrap|bs-|bootstrap\.min|col-md-|col-lg-', html, re.I):
            technologies.append('Bootstrap')
        
        # Tailwind CSS
        if re.search(r'tailwind|tw-|tailwindcss', html, re.I):
            technologies.append('Tailwind CSS')
        
        # Foundation
        if re.search(r'foundation|zurb', html, re.I):
            technologies.append('Foundation')
        
        # Materialize
        if re.search(r'materialize|materializecss', html, re.I):
            technologies.append('Materialize')
        
        # Bulma
        if re.search(r'bulma|bulma\.', html, re.I):
            technologies.append('Bulma')
        
        # Remix
        if re.search(r'remix\.run|__remix|_remix', html, re.I):
            technologies.append('Remix')
        
        # Astro
        if re.search(r'astro|_astro/', html, re.I):
            technologies.append('Astro')
        
        # SolidJS
        if re.search(r'solidjs|solid-js', html, re.I):
            technologies.append('SolidJS')
        
        # Qwik
        if re.search(r'qwik|builder\.io.*qwik', html, re.I):
            technologies.append('Qwik')
        
        # htmx
        if re.search(r'htmx|hx-get|hx-post|hx-swap', html, re.I):
            technologies.append('htmx')
        
        # Alpine.js
        if re.search(r'alpine\.?js|x-data|x-show|x-if', html, re.I):
            technologies.append('Alpine.js')
        
        # Ember.js
        if re.search(r'ember|emberjs|ember-', html, re.I):
            technologies.append('Ember.js')
        
        # Backbone.js
        if re.search(r'backbone|backbonejs', html, re.I):
            technologies.append('Backbone.js')
        
        # Strapi (Headless CMS)
        if re.search(r'strapi|x-powered-by.*strapi', headers_str, re.I):
            technologies.append('Strapi')
        
        # Ghost (CMS/Blog)
        if re.search(r'ghost\.org|ghost-|powered.*ghost', html, re.I):
            technologies.append('Ghost')
        
        # Contentful
        if re.search(r'contentful|ctfassets', html, re.I):
            technologies.append('Contentful')
        
        # Sanity
        if re.search(r'sanity\.io|cdn\.sanity', html, re.I):
            technologies.append('Sanity')
        
        # Vercel
        if re.search(r'vercel|\.vercel-analytics|x-vercel', html, re.I) or 'vercel' in headers_str:
            technologies.append('Vercel')
        
        # Netlify
        if 'netlify' in headers_str or 'netlify' in html_lower:
            technologies.append('Netlify')
        
        # Cloudflare Pages
        if 'cf-pages' in headers_str or 'pages.dev' in html_lower:
            technologies.append('Cloudflare Pages')
        
        return technologies if technologies else ['Undetected']
    
    def detect_cdn(self, html, headers, url):
        """Detect CDN providers"""
        cdns = []
        html_lower = html.lower()
        headers_str = str(headers).lower()
        
        # CloudFlare
        if any(['cloudflare' in headers_str, 'cf-ray' in headers, '__cfduid' in html_lower]):
            cdns.append('Cloudflare')
        
        # Akamai
        if any(['akamai' in headers_str, re.search(r'akamai\.net|akamaicdn', html, re.I)]):
            cdns.append('Akamai')
        
        # Cloudfront (AWS)
        if 'cloudfront' in headers_str or 'cloudfront.net' in html_lower:
            cdns.append('CloudFront')
        
        # Fastly
        if 'fastly' in headers_str or 'fastly.net' in html_lower:
            cdns.append('Fastly')
        
        # Cloudflare Pages/Workers
        if 'cf-pages' in headers_str or 'workers.dev' in html_lower:
            cdns.append('Cloudflare Pages')
        
        # KeyCDN
        if re.search(r'keycdn|kxcdn\.com', html, re.I):
            cdns.append('KeyCDN')
        
        # BunnyCDN
        if re.search(r'bunnycdn|b-cdn\.net', html, re.I):
            cdns.append('BunnyCDN')
        
        # StackPath
        if re.search(r'stackpath|stackpathcdn', html, re.I):
            cdns.append('StackPath')
        
        # Google Cloud CDN
        if 'ghs.google.com' in html_lower or 'googleusercontent.com' in html_lower:
            cdns.append('Google Cloud CDN')
        
        # Microsoft Azure CDN
        if re.search(r'azureedge\.net|azure\.com.*cdn', html, re.I):
            cdns.append('Azure CDN')
        
        # Vercel
        if 'vercel' in headers_str or '\.vercel\.app' in html_lower:
            cdns.append('Vercel')
        
        # Netlify
        if 'netlify' in headers_str or 'netlify.app' in html_lower:
            cdns.append('Netlify')
        
        return cdns if cdns else ['None']
    
    def detect_analytics(self, html, soup):
        """Detect analytics and tracking services"""
        analytics = []
        html_lower = html.lower()
        
        # Google Analytics
        ga_patterns = [r'google-analytics\.com|analytics\.js', r'gtag\.js|gtag\(', r'ga\(|_gaq', r'UA-\d+-\d+|G-[A-Z0-9]+']
        if any(re.search(pattern, html, re.I) for pattern in ga_patterns):
            if 'gtag' in html_lower or 'G-' in html:
                analytics.append('Google Analytics 4')
            else:
                analytics.append('Google Analytics')
        
        # Google Tag Manager
        if re.search(r'googletagmanager\.com|GTM-[A-Z0-9]+', html, re.I):
            analytics.append('Google Tag Manager')
        
        # Facebook Pixel
        if re.search(r'facebook\.com/tr|fbq\(|connect\.facebook\.net', html, re.I):
            analytics.append('Facebook Pixel')
        
        # Hotjar
        if re.search(r'hotjar\.com|hj\(|_hjSettings', html, re.I):
            analytics.append('Hotjar')
        
        # Mixpanel
        if re.search(r'mixpanel\.com|mixpanel\.', html, re.I):
            analytics.append('Mixpanel')
        
        # Segment
        if re.search(r'segment\.com|analytics\.js.*segment', html, re.I):
            analytics.append('Segment')
        
        # Amplitude
        if re.search(r'amplitude\.com|amplitude\.getInstance', html, re.I):
            analytics.append('Amplitude')
        
        # Matomo (Piwik)
        if re.search(r'matomo|piwik', html, re.I):
            analytics.append('Matomo')
        
        # Plausible
        if re.search(r'plausible\.io', html, re.I):
            analytics.append('Plausible')
        
        # Adobe Analytics
        if re.search(r'omniture|adobe.*analytics|s_code\.js', html, re.I):
            analytics.append('Adobe Analytics')
        
        # Heap Analytics
        if re.search(r'heap.*analytics|heapanalytics\.com', html, re.I):
            analytics.append('Heap')
        
        # Clicky
        if re.search(r'clicky\.com|clicky_site_ids', html, re.I):
            analytics.append('Clicky')
        
        # Yandex Metrica
        if re.search(r'yandex.*metrika|mc\.yandex', html, re.I):
            analytics.append('Yandex Metrica')
        
        # Crazy Egg
        if re.search(r'crazyegg\.com', html, re.I):
            analytics.append('Crazy Egg')
        
        return analytics if analytics else ['None']
    
    def detect_chat_widgets(self, html):
        """Detect live chat and support widgets"""
        widgets = []
        
        # Intercom
        if re.search(r'intercom\.io|intercomSettings', html, re.I):
            widgets.append('Intercom')
        
        # Zendesk
        if re.search(r'zendesk\.com|zdassets', html, re.I):
            widgets.append('Zendesk')
        
        # Drift
        if re.search(r'drift\.com|driftt', html, re.I):
            widgets.append('Drift')
        
        # LiveChat
        if re.search(r'livechatinc\.com|livechat', html, re.I):
            widgets.append('LiveChat')
        
        # Tawk.to
        if re.search(r'tawk\.to', html, re.I):
            widgets.append('Tawk.to')
        
        # Crisp
        if re.search(r'crisp\.chat|crisp\.im', html, re.I):
            widgets.append('Crisp')
        
        # Freshchat/Freshdesk
        if re.search(r'freshchat|freshdesk', html, re.I):
            widgets.append('Freshchat')
        
        # HubSpot Chat
        if re.search(r'hubspot.*chat|hs-chat', html, re.I):
            widgets.append('HubSpot Chat')
        
        # Olark
        if re.search(r'olark\.com', html, re.I):
            widgets.append('Olark')
        
        return widgets if widgets else ['None']
    
    def get_dns_info(self, url):
        """Get DNS and IP information"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return {'ips': [], 'nameservers': []}
            
            # Get IP addresses
            ips = []
            try:
                answers = dns.resolver.resolve(hostname, 'A')
                ips = [str(rdata) for rdata in answers]
            except:
                pass
            
            # Get nameservers
            nameservers = []
            try:
                # Get the domain (not subdomain)
                parts = hostname.split('.')
                if len(parts) >= 2:
                    domain = '.'.join(parts[-2:])
                    ns_answers = dns.resolver.resolve(domain, 'NS')
                    nameservers = [str(rdata) for rdata in ns_answers]
            except:
                pass
            
            return {'ips': ips, 'nameservers': nameservers}
        except:
            return {'ips': [], 'nameservers': []}

# Initialize checker
checker = AdvancedSiteChecker()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_message = """🌐 Toji Site Checker
@TOjiCHKBot
━━━━━━━━━━━━━━━━━━━━

🔍 Advanced Website Analyzer Bot

📝 Commands:
/site <url> - Analyze a website
.site <url> - Analyze a website
/msite <urls> - Mass check (direct or file)
.msite <urls> - Mass check (direct or file)

📁 Mass Check Methods:
1️⃣ Direct: /msite url1 url2 url3
2️⃣ File: Upload .txt file ➜ Reply with /msite

🎯 Features:
✓ CAPTCHA Detection (20+ systems)
✓ Security/WAF Analysis (15+ providers)
✓ Payment Gateway Detection (40+ gateways)
✓ Technology Stack (50+ frameworks)
✓ CDN Detection (10+ providers)
✓ Analytics & Chat Widgets
✓ DNS & IP Information

🚀 Most Accurate & Advanced Detection Engine!

━━━━━━━━━━━━━━━━━━━━
Developed by @mumiru"""
    
    await update.message.reply_text(welcome_message)

async def analyze_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze website handler"""
    message_text = update.message.text
    
    # Extract URL from command
    url = None
    if message_text.startswith('/site'):
        url = message_text.replace('/site', '').strip()
    elif message_text.startswith('.site'):
        url = message_text.replace('.site', '').strip()
    
    if not url:
        await update.message.reply_text("❌ Please provide a URL!\n\nUsage: /site <url> or .site <url>")
        return
    
    # Send analyzing message
    analyzing_msg = await update.message.reply_text("🔍 Analyzing website... Please wait.")
    
    # Perform analysis in thread pool to avoid blocking event loop
    result = await asyncio.to_thread(checker.analyze_url, url)
    
    if result['status'] == 'error':
        await analyzing_msg.edit_text(f"❌ Error analyzing website:\n{result['error']}")
        return
    
    # Format response
    captcha_list = ', '.join(result['captcha']) if isinstance(result['captcha'], list) else result['captcha']
    security_list = ', '.join(result['security']) if isinstance(result['security'], list) else result['security']
    gateways_list = ', '.join(result['gateways']) if isinstance(result['gateways'], list) else result['gateways']
    technology_list = ', '.join(result['technology']) if isinstance(result['technology'], list) else result['technology']
    cdn_list = ', '.join(result.get('cdn', ['None'])) if isinstance(result.get('cdn'), list) else result.get('cdn', 'None')
    analytics_list = ', '.join(result.get('analytics', ['None'])) if isinstance(result.get('analytics'), list) else result.get('analytics', 'None')
    chat_list = ', '.join(result.get('chat', ['None'])) if isinstance(result.get('chat'), list) else result.get('chat', 'None')
    card_save_list = ', '.join(result.get('card_save_auth', ['Not Detected'])) if isinstance(result.get('card_save_auth'), list) else result.get('card_save_auth', 'Not Detected')
    
    response = f"""🌐 Toji Site Checker
@TOjiCHKBot
━━━━━━━━━━━━━━━━━━━━
📊 ANALYSIS RESULTS

🔗 URL: {result['url']}
🌍 IP: {result.get('ip', 'Unknown')}

🔐 Captcha: {captcha_list}

🛡️ Security: {security_list}

🚀 CDN: {cdn_list}

💳 Gateways: {gateways_list}

⚙️ Technology: {technology_list}

💎 Card Save/Auth: {card_save_list}

📊 Analytics: {analytics_list}

💬 Chat: {chat_list}
━━━━━━━━━━━━━━━━━━━━
👤 Requested by @{update.message.from_user.username or 'User'}
Developed by @mumiru"""
    
    await analyzing_msg.edit_text(response)

async def analyze_mass_sites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mass analyze websites handler"""
    message_text = update.message.text
    url_list = []
    
    # Check if this is a reply to a document/file
    if update.message.reply_to_message and update.message.reply_to_message.document:
        try:
            # Get the file
            file = await update.message.reply_to_message.document.get_file()
            
            # Download file content
            file_content = await file.download_as_bytearray()
            
            # Decode and parse URLs from file
            try:
                text_content = file_content.decode('utf-8')
            except:
                text_content = file_content.decode('latin-1')
            
            # Extract URLs from file (line by line)
            for line in text_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Clean URL (remove any extra text)
                    urls_in_line = line.split()
                    for url in urls_in_line:
                        if url and ('.' in url or 'http' in url):
                            url_list.append(url.strip())
        except Exception as e:
            await update.message.reply_text(f"❌ Error reading file: {str(e)}\n\nPlease upload a text file with URLs.")
            return
    else:
        # Extract URLs from command text
        urls = None
        if message_text.startswith('/msite'):
            urls = message_text.replace('/msite', '').strip()
        elif message_text.startswith('.msite'):
            urls = message_text.replace('.msite', '').strip()
        
        if not urls:
            await update.message.reply_text("❌ Please provide URLs!\n\nUsage:\n• /msite <url1> <url2> <url3>\n• Upload a text file and reply with /msite")
            return
        
        # Parse URLs (space-separated or line-separated)
        if '\n' in urls:
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        else:
            url_list = [url.strip() for url in urls.split() if url.strip()]
    
    if not url_list:
        await update.message.reply_text("❌ No valid URLs found!\n\nUsage: /msite <url1> <url2> <url3>")
        return
    
    # Send analyzing message
    analyzing_msg = await update.message.reply_text(f"🔍 Mass analyzing {len(url_list)} websites with {min(20, len(url_list))} workers... Please wait.")
    
    # Analyze all URLs with multiple workers (parallel processing)
    MAX_WORKERS = 20  # Number of concurrent workers
    semaphore = asyncio.Semaphore(MAX_WORKERS)
    completed_count = [0]  # Use list to allow modification in nested function
    total_count = len(url_list)
    last_update_time = [0]  # Track last message update time
    
    async def analyze_with_semaphore(url, index):
        async with semaphore:
            try:
                # Perform analysis in thread pool
                result = await asyncio.to_thread(checker.analyze_url, url)
                
                # Update progress counter
                completed_count[0] += 1
                
                # Update progress message (but not too frequently to avoid rate limits)
                import time
                current_time = time.time()
                if current_time - last_update_time[0] >= 2:  # Update every 2 seconds
                    try:
                        await analyzing_msg.edit_text(
                            f"🔍 Analyzing websites... {completed_count[0]}/{total_count} completed\n"
                            f"⚡ {MAX_WORKERS} workers running in parallel"
                        )
                        last_update_time[0] = current_time
                    except:
                        pass  # Ignore rate limit errors
                
                return result
            except Exception as e:
                completed_count[0] += 1
                return {
                    'url': url,
                    'error': str(e),
                    'status': 'error'
                }
    
    # Run all analyses in parallel
    tasks = [analyze_with_semaphore(url, i) for i, url in enumerate(url_list)]
    results = await asyncio.gather(*tasks)
    
    # Format combined response
    response_parts = [
        "🌐 Toji Site Checker",
        "@TOjiCHKBot",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📊 MASS CHECK RESULTS ({len(url_list)} sites)",
        ""
    ]
    
    for i, result in enumerate(results, 1):
        if result['status'] == 'error':
            response_parts.append(f"{i}. ❌ {result['url']}")
            response_parts.append(f"   Error: {result['error'][:50]}")
        else:
            captcha_list = ', '.join(result['captcha']) if isinstance(result['captcha'], list) else result['captcha']
            security_list = ', '.join(result['security']) if isinstance(result['security'], list) else result['security']
            gateways_list = ', '.join(result['gateways']) if isinstance(result['gateways'], list) else result['gateways']
            technology_list = ', '.join(result['technology']) if isinstance(result['technology'], list) else result['technology']
            card_save_list = ', '.join(result.get('card_save_auth', ['Not Detected'])) if isinstance(result.get('card_save_auth'), list) else result.get('card_save_auth', 'Not Detected')
            
            response_parts.append(f"{i}. ✅ {result['url']}")
            response_parts.append(f"   🔐 {captcha_list}")
            response_parts.append(f"   🛡️ {security_list}")
            response_parts.append(f"   💳 {gateways_list}")
            response_parts.append(f"   ⚙️ {technology_list}")
            response_parts.append(f"   💎 {card_save_list}")
        response_parts.append("")
    
    response_parts.append("━━━━━━━━━━━━━━━━━━━━")
    response_parts.append(f"👤 Requested by @{update.message.from_user.username or 'User'}")
    response_parts.append("Developed by @mumiru")
    
    response = '\n'.join(response_parts)
    
    # Save results to file
    import tempfile
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mass_check_results_{len(url_list)}_sites_{timestamp}.txt"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
        temp_file.write(response)
        temp_filepath = temp_file.name
    
    # Send file to user
    await analyzing_msg.delete()
    await update.message.reply_document(
        document=open(temp_filepath, 'rb'),
        filename=filename,
        caption=f"✅ Mass check completed for {len(url_list)} sites!\n\n📄 Results saved to file."
    )
    
    # Clean up temp file
    import os
    os.unlink(temp_filepath)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    if update.message.text.startswith('.site'):
        await analyze_site(update, context)
    elif update.message.text.startswith('.msite'):
        await analyze_mass_sites(update, context)

def main():
    """Main function to run the bot"""
    # Validate BOT_TOKEN exists
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN environment variable is not set!")
        print("Please set your Telegram bot token in the Secrets tab.")
        return
    
    print("🤖 Starting Toji Site Checker Bot...")
    print("✓ Bot token configured")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("site", analyze_site))
    app.add_handler(CommandHandler("msite", analyze_mass_sites))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("✓ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
