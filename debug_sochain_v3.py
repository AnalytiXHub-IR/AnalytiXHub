
import requests
import json

address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
url = f"https://chain.so/api/v3/transactions/DOGE/{address}/1"

print(f"Requesting SoChain V3: {url}")
try:
    # SoChain often requires User-Agent
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        status = data.get('status')
        print(f"API Status: {status}")
        
        if status == 'success':
            txs = data.get('data', {}).get('txs', [])
            print(f"Transactions found: {len(txs)}")
            if txs:
                print(f"Sample Tx: {txs[0]}")
        else:
            print("API returned failure status")
    else:
        print(f"Error Body: {resp.text[:500]}")
        
except Exception as e:
    print(f"Exception: {e}")
