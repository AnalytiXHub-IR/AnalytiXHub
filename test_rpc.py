import requests
import json

endpoints = [
    "https://solana-rpc.publicnode.com",
    "https://rpc.solana.com",
    "https://api.mainnet-beta.solana.com",
    "https://solana-mainnet.g.allnodes.com",
    "https://solana-mainnet.rpc.extrnode.com",
    "https://rpc.ankr.com/solana"
]

address = "ETpvxQ95mN2d6Xiob8tnrCRQvSZrNDA3UgFEzd1oaFF5"
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getSignaturesForAddress",
    "params": [address, {"limit": 1}]
}

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json"
}

results = []

for url in endpoints:
    line = f"Testing {url}..."
    print(line)
    results.append(line)
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        res_line = f"  Status: {resp.status_code}"
        print(res_line)
        results.append(res_line)
        if resp.status_code == 200:
            data = resp.json()
            if 'result' in data:
                success_line = "  SUCCESS! Result found."
                print(success_line)
                results.append(success_line)
            else:
                fail_line = f"  FAILED: {data.get('error', 'Unknown error')}"
                print(fail_line)
                results.append(fail_line)
        else:
            fail_line = f"  FAILED Code: {resp.status_code}, Body: {resp.text[:100]}"
            print(fail_line)
            results.append(fail_line)
    except Exception as e:
        err_line = f"  ERROR: {e}"
        print(err_line)
        results.append(err_line)

with open("rpc_results.txt", "w") as f:
    f.write("\n".join(results))
