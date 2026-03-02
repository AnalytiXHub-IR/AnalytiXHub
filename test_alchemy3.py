import requests
import json

url = "https://opt-mainnet.g.alchemy.com/v2/WCH8dVHq904bp09x4IFpn"

# A known active address on Optimism/Base
address = "0x0000000000000000000000000000000000000000" # Zero address definitely has transfers

params1 = {
    "category": ["external", "erc20"],
    "fromAddress": address
}

payload1 = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "alchemy_getAssetTransfers",
    "params": [params1]
}

res = requests.post(url, json=payload1)
print("Address Check:")
print(res.json())

