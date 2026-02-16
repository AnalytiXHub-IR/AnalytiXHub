
import requests
import json

def test_sochain(address):
    print(f"Testing SoChain V2 for {address}...")
    # Try get_tx_received
    url = f"https://sochain.com/api/v2/get_tx_received/DOGE/{address}"
    try:
        resp = requests.get(url, timeout=10)
        print(f"Received Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            txs = data.get('data', {}).get('txs', [])
            print(f"Received Txs: {len(txs)}")
    except Exception as e:
        print(f"Error: {e}")

    # Try address info (might have txs)
    url = f"https://sochain.com/api/v2/address/DOGE/{address}"
    try:
        resp = requests.get(url, timeout=10)
        print(f"Address Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            txs = data.get('data', {}).get('txs', [])
            print(f"Total Txs in Address endpoint: {len(txs)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sochain("DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L")
