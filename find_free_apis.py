#!/usr/bin/env python3
"""
Find free blockchain APIs that work without keys or payment
"""
import requests
import time

print("Testing FREE Blockchain APIs (No Keys, No Payment)...\n")

tests = [
    # Bitcoin
    ('Bitcoin - Mempool (basic)', 'https://mempool.space/api/address/1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD'),
    ('Bitcoin - Blockchair Free', 'https://api.blockchair.com/bitcoin/addresses?addresses=1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD&key=test'),
    
    # Ethereum
    ('Ethereum - BlockScout', 'https://eth.blockscout.com/api/v2/addresses/0x098B716B8Aaf21512996dC57EB0615e2383E2f96'),
    ('Ethereum - Alchemy Free', 'https://eth-mainnet.alchemy.com/v2/demo'),
    
    # Litecoin
    ('Litecoin - Blockchair', 'https://api.blockchair.com/litecoin/addresses?addresses=LaddysDCjnTtAN6LEJwhmoHQ47GJaWDanH&key=test'),
    
    # Dogecoin  
    ('Dogecoin - Blockchair', 'https://api.blockchair.com/dogecoin/addresses?addresses=DBJRmBfwKFdXf8U84gHwTHEtmA9tSNkUSj&key=test'),
    
    # XRP
    ('XRP - XRPL.ws', 'https://xrpl.ws'),
    
    # Price data
    ('CoinGecko - Free', 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'),
]

for name, url in tests:
    try:
        response = requests.get(url, timeout=5)
        status = response.status_code
        
        # Check for common error indicators
        text = response.text[:200]
        
        if status == 200:
            print(f"✅ {name:<40} {status} OK")
        elif 'free' in text.lower() or 'payment' in text.lower() or 'upgrade' in text.lower():
            print(f"💳 {name:<40} {status} (REQUIRES PAYMENT)")
        elif 'unauthorized' in text.lower() or 'forbidden' in text.lower():
            print(f"🔐 {name:<40} {status} (KEY REQUIRED)")
        else:
            print(f"⚠️  {name:<40} {status}")
    except Exception as e:
        print(f"❌ {name:<40} {str(e)[:30]}")
    
    time.sleep(0.5)  # Rate limit friendly

print("\n" + "="*60)
print("ANALYSIS: Which APIs work 100% free with no registration?")
print("="*60)
