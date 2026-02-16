
import requests
import os
import json

token = "ba0c6f917baf4f5186ac1e5e62acc475"
address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
url = f"https://api.blockcypher.com/v1/doge/main/addrs/{address}/full?token={token}&limit=50"

print(f"Requesting: {url}")
try:
    resp = requests.get(url, timeout=15)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total Txs (n_tx): {data.get('n_tx')}")
        print(f"Returned Txs: {len(data.get('txs', []))}")
        if data.get('txs'):
            print(f"First Tx Block Height: {data['txs'][0].get('block_height')}")
    else:
        print("Response Text:")
        print(resp.text[:500])
except Exception as e:
    print(f"Exception: {e}")
