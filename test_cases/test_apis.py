#!/usr/bin/env python3
"""Test which blockchain APIs work without keys"""
import requests
import json

# Test Mempool Bitcoin API
print('=== Testing Blockchain APIs ===\n')

print('1. Mempool Space (Bitcoin):')
try:
    r = requests.get('https://mempool.space/api/address/1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD', timeout=5)
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        d = r.json()
        if 'chain_stats' in d:
            print(f'   Transactions: {d["chain_stats"].get("tx_count", 0)}')
            print(f'   Result: ✅ WORKS')
except Exception as e:
    print(f'   ERROR: {e}')

print()

# Test Blockchair without API key
print('2. Blockchair (Bitcoin - no key):')
try:
    r = requests.get('https://blockchair.com/api/v1/bitcoin/addresses/1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD', timeout=5)
    print(f'   Status: {r.status_code}')
    resp_text = r.text[:150]
    print(f'   Response: {resp_text}...')
    if 'error' in resp_text.lower():
        print(f'   Result: ❌ REQUIRES API KEY')
    elif r.status_code == 200:
        print(f'   Result: ✅ WORKS')
except Exception as e:
    print(f'   ERROR: {e}')

print()

# Test BlockScout
print('3. BlockScout (Ethereum):')
try:
    r = requests.get('https://eth.blockscout.com/api/v2/addresses/0x098B716B8Aaf21512996dC57EB0615e2383E2f96', timeout=5)
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        d = r.json()
        print(f'   Result: ✅ WORKS')
except Exception as e:
    print(f'   ERROR: {e}')

print()

# Test BlockExperts
print('4. BlockExperts (Litecoin):')
try:
    r = requests.get('https://blockexplorer.one/api/ltc/address/Vc41YvLFEUCKyqAVawXmJs3QBccQ4wEqGL', timeout=5)
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        print(f'   Result: ✅ WORKS')
except Exception as e:
    print(f'   ERROR: {e}')

print()

# Test SoChain (supports multiple chains)
print('5. SoChain (Multi-chain - free API):')
chains = [
    ('BTC', '1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD'),
    ('LTC', 'Vc41YvLFEUCKyqAVawXmJs3QBccQ4wEqGL'),
    ('DOGE', 'DBJRmBfwKFdXf8U84gHwTHEtmA9tSNkUSj'),
]
for chain, addr in chains:
    try:
        r = requests.get(f'https://chain.so/api/v2/address/{chain}/{addr}', timeout=5)
        if r.status_code == 200:
            d = r.json()
            print(f'   {chain}: ✅ WORKS - {d.get("data", {}).get("total_txs", 0)} txs')
        else:
            print(f'   {chain}: ❌ {r.status_code}')
    except Exception as e:
        print(f'   {chain}: ERROR - {str(e)[:30]}')

print()

# Test BlockDaemon (might have free tier)
print('6. MerlinChain (Ethereum):')
try:
    r = requests.get('https://api.etherscan.io/api?module=account&action=txlist&address=0x098B716B8Aaf21512996dC57EB0615e2383E2f96&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken', timeout=5)
    print(f'   Status: {r.status_code}')
except Exception as e:
    print(f'   ERROR: {e}')
