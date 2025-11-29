"""
Example: Batch Card Checking Script
This shows how to check multiple cards programmatically
"""

from main import BraintreeAutomatedChecker

def check_multiple_cards(site_url, cards):
    """
    Check multiple cards on the same site
    
    Args:
        site_url: The target website URL
        cards: List of card data strings in format "cardnumber|mm|yy|cvv"
    """
    print("\n" + "="*60)
    print("🔄 BATCH CARD CHECKER")
    print("="*60)
    print(f"\n🌐 Target Site: {site_url}")
    print(f"💳 Total Cards: {len(cards)}")
    print("\n" + "="*60)
    
    results = []
    
    for i, card in enumerate(cards, 1):
        print(f"\n\n{'='*60}")
        print(f"📊 CHECKING CARD {i}/{len(cards)}")
        print(f"{'='*60}")
        
        checker = BraintreeAutomatedChecker()
        
        result = checker.check_card(site_url, card)
        
        results.append({
            'card': card,
            'result': result
        })
        
        print("\n" + "-"*60)
        print(f"Result: {result}")
        print("-"*60)
        
        # Optional: Add delay between checks to avoid rate limiting
        # import time
        # time.sleep(5)
    
    print("\n\n" + "="*60)
    print("📋 FINAL SUMMARY")
    print("="*60)
    
    for i, item in enumerate(results, 1):
        masked_card = item['card'].split('|')[0][:6] + "******" + item['card'].split('|')[0][-4:]
        print(f"\n{i}. {masked_card}")
        print(f"   Result: {item['result']}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    # Example usage
    
    site = "https://example.com"
    
    cards_to_check = [
        "4111111111111111|12|25|123",
        "5555555555554444|06|26|456",
        "378282246310005|03|27|789"
    ]
    
    check_multiple_cards(site, cards_to_check)
