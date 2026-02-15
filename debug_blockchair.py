
import requests
import json

address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
url = f"https://api.blockchair.com/dogecoin/dashboards/address/{address}?limit=100"

print(f"Testing BlockChair: {url}")
try:
    # BlockChair sometimes requires User-Agent
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print("Success!")
        # BlockChair structure: data[address]['transactions']
        addr_data = data.get('data', {}).get(address, {})
        txs = addr_data.get('transactions', [])
        print(f"Transactions found: {len(txs)}")
        if txs:
            print(f"Sample Tx ID: {txs[0]}")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
