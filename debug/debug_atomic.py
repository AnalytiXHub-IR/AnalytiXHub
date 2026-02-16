
import requests
import json

address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
# Try V1 or V2? Usually V2.
url = f"https://doge.atomicwallet.io/api/v2/address/{address}"

print(f"Testing Atomic Wallet: {url}")
try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print("Success!")
        # Inspect structure
        print(json.dumps(data, indent=2)[:500])
        txs = data.get('transactions', [])
        print(f"Transactions found: {len(txs)}")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
