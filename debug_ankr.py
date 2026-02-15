
import requests
import json

url = "https://rpc.ankr.com/dogecoin"
headers = {'Content-Type': 'application/json'}

# 1. Basic Check
payload = {
    "jsonrpc": "2.0",
    "method": "getblockchaininfo",
    "params": [],
    "id": 1
}

print(f"Testing Ankr RPC: {url}")
try:
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("Success! Blockchain Info:")
        print(json.dumps(resp.json(), indent=2)[:500])
        
        # 2. Check for Address capability (often missing on public RPCs)
        # Try 'getaddressinfo' or similar? Core doesnt really have it without indexer.
        # But maybe Ankr has it?
        # Let's try 'scantxoutset'? No too heavy.
        # usually public RPCs assume you use an indexer.
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
