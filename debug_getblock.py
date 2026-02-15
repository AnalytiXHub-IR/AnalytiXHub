
import requests
import json
import traceback

# User provided endpoint
# Attempts:
# 1. Direct use of go.getblock.io (might be a relay)
# 2. Standard format with token extracted
token = "b39e26d0ec0240a7b25b914ac2f53f13"
urls = [
    "https://go.getblock.io/b39e26d0ec0240a7b25b914ac2f53f13",
    f"https://doge.getblock.io/{token}/mainnet/",
    f"https://doge.getblock.io/mainnet/?api_key={token}"
]

headers = {'Content-Type': 'application/json'}
address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"

def rpc(url, method, params=[]):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, f"Status: {resp.status_code}, Text: {resp.text}"
    except Exception as e:
        return None, str(e)

print(f"Testing GetBlock Token: {token}")

found_working = False
for u in urls:
    print(f"\n--- Checking URL: {u} ---")
    res, err = rpc(u, "getblockchaininfo")
    
    if res and 'result' in res:
        print("✅ CONNECTION SUCCESS!")
        print(f"Info: {json.dumps(res['result'], indent=2)[:200]}")
        found_working = True
        
        # Now verify capabilities on this working URL
        # 1. Search Raw Transactions (Requires txindex)
        print("\n[Test] searchrawtransactions ...")
        # params: address, verbose=1, skip=0, count=5
        tx_res, tx_err = rpc(u, "searchrawtransactions", [address, 1, 0, 5])
        
        if tx_res:
            if 'error' in tx_res and tx_res['error']:
                 print(f"❌ searchrawtransactions Error: {tx_res['error']}")
            else:
                 print("✅ searchrawtransactions SUPPORTED!")
                 print(json.dumps(tx_res, indent=2)[:500])
        else:
            print(f"❌ call failed: {tx_err}")
            
        # 2. Check getscantxoutset (Often disabled, but checks UTXOs)
        # print("\n[Test] getscantxoutset ...")
        # scan_res, scan_err = rpc(u, "getscantxoutset", ["start", [f"addr({address})"]])
        # print(f"Scan Result: {scan_res if scan_res else scan_err}")
        
        break # Sticking with the first working one
    else:
        print(f"❌ Connection Failed: {err if err else 'Unknown Error'}")

if not found_working:
    print("\n[CRITICAL] No working GetBlock endpoint found.")
