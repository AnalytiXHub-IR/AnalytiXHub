
import requests

address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
# No token parameter
url = f"https://api.blockcypher.com/v1/doge/main/addrs/{address}/full?limit=5"

print(f"Requesting (No Token): {url}")
try:
    resp = requests.get(url, timeout=15)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Transactions found: {len(data.get('txs', []))}")
    else:
        print("Response Text:")
        print(resp.text[:500])
except Exception as e:
    print(f"Exception: {e}")
