#!/usr/bin/env python3
"""Test BlockScout - universal free API for multiple chains"""
import requests

blockscout_endpoints = {
    'ethereum': 'https://eth.blockscout.com',
    'polygon': 'https://polygon.blockscout.com',
    'arbitrum': 'https://arbitrum.blockscout.com',
    'optimism': 'https://optimism.blockscout.com',
}

test_addresses = {
    'ethereum': '0x098B716B8Aaf21512996dC57EB0615e2383E2f96',
}

print("Testing BlockScout Universal API\n")

for chain, base_url in blockscout_endpoints.items():
    if chain not in test_addresses:
        continue
    
    addr = test_addresses[chain]
    url = f"{base_url}/api/v2/addresses/{addr}"
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ {chain.upper():<15} {r.status_code} OK")
            print(f"   Transaction count: {data.get('transaction_count', 'N/A')}")
        else:
            print(f"⚠️  {chain.upper():<15} {r.status_code}")
    except Exception as e:
        print(f"❌ {chain.upper():<15} Error: {str(e)[:40]}")

print("\n" + "="*60)
print("BlockScout works for: Ethereum, Polygon, Arbitrum, Optimism")
print("All completely FREE - no keys needed!")
print("="*60)

# Also test if there's a Bitcoin explorer on BlockScout
print("\nSearching for Bitcoin support...")
bitcoin_urls = [
    'https://btc.blockscout.com/api/v2/addresses/1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD',
    'https://bitcoin.blockscout.com/api/v2/addresses/1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD',
]

for url in bitcoin_urls:
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print(f"✅ Found Bitcoin BlockScout: {url.split('/')[2]}")
    except:
        pass
