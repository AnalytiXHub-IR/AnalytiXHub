import requests
import json

url = "https://zksync-mainnet.g.alchemy.com/v2/WCH8dVHq904bp09x4IFpn"

params = {
    "category": ["external", "erc20", "erc721", "erc1155"],
    "withMetadata": True,
    "excludeZeroValue": False,
    "maxCount": "0x3E8",
    "fromAddress": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
}

payload = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "alchemy_getAssetTransfers",
    "params": [params]
}

headers = {"accept": "application/json", "content-type": "application/json"}

print("Sending request to:", url)
response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Raw Response:")
try:
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Failed to parse JSON:", response.text)
