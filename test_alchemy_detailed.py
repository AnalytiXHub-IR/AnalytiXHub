import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('ALCHEMY_API_KEY', 'WCH8dVHq904bp09x4IFpn')

# Test on Base or Opt since user mentioned ETH.BASE
url = f"https://base-mainnet.g.alchemy.com/v2/{api_key}"

address = "0xdd186D9E0c6A0EC8731E183a853EFB1eeC8438ec"

# Payload 1: Our current payload
params1 = {
    "category": ["external", "erc20", "erc721", "erc1155"],
    "withMetadata": True,
    "excludeZeroValue": False,
    "maxCount": "0x3E8",
    "fromAddress": address
}
payload1 = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "alchemy_getAssetTransfers",
    "params": [params1]
}

# Payload 2: User suggested payload
params2 = {
    "fromBlock": "0x0",
    "toBlock": "latest",
    "category": ["external", "erc20", "erc721", "erc1155"],
    "excludeZeroValue": False,
    "maxCount": "0x3E8",
    "fromAddress": address
}
payload2 = {
    "id": 2,
    "jsonrpc": "2.0",
    "method": "alchemy_getAssetTransfers",
    "params": [params2]
}

print("=== OUR PAYLOAD ===")
res1 = requests.post(url, json=payload1)
print(res1.status_code)
try:
    data1 = res1.json()
    if 'error' in data1:
        print("ERROR:", data1['error'])
    else:
        txs = data1.get('result', {}).get('transfers', [])
        print(f"Count: {len(txs)}")
        if txs:
            print(json.dumps(txs[0], indent=2))
except Exception as e:
    print(e)
    
print("\n=== USER PAYLOAD ===")
res2 = requests.post(url, json=payload2)
print(res2.status_code)
try:
    data2 = res2.json()
    if 'error' in data2:
        print("ERROR:", data2['error'])
    else:
        txs = data2.get('result', {}).get('transfers', [])
        print(f"Count: {len(txs)}")
        if txs:
            print(json.dumps(txs[0], indent=2))
except Exception as e:
    print(e)

