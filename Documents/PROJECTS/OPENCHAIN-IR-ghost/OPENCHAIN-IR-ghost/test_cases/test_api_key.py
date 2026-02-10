#!/usr/bin/env python3
import requests
import json

key = 'TUWDXD7G5R3KE7K3UN1YD5F7RKKJIGXDEY'
eth_addr = '0x098B716B8Aaf21512996dC57EB0615e2383E2f96'

# Test 1: Etherscan v1 API
print('Testing Etherscan v1 API:')
url = 'https://api.etherscan.io/api'
params = {
    'module': 'account',
    'action': 'txlist',
    'address': eth_addr,
    'startblock': 0,
    'endblock': 99999999,
    'apikey': key
}
try:
    r = requests.get(url, params=params, timeout=5)
    d = r.json()
    if d.get('status') == '1':
        txs = d.get('result', [])
        print(f'✅ Works! Returned {len(txs)} transactions')
    else:
        print(f'❌ Error: {d.get("message", "Unknown")}')
except Exception as e:
    print(f'❌ Exception: {e}')

print()

# Test 2: Try various Bitcoin APIs that don't need keys
print('Testing free Bitcoin APIs:')

# BlockDaemon/Infura alternatives - test if any public nodes work
bitcoin_tests = [
    ('Mempool v2', 'https://mempool.space/api/v1/address/1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD'),
    ('Mempool v2 stats', 'https://mempool.space/api/address/1A1z7agoat7G5Oj4QfNbGjPwnd2E7YwCD/txs/chain'),
]

for name, url in bitcoin_tests:
    try:
        r = requests.get(url, timeout=5)
        print(f'{name}: Status {r.status_code}')
    except Exception as e:
        print(f'{name}: {e}')
