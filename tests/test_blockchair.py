
import requests
import json

def test_blockchair(address):
    print(f"Testing Blockchair for {address}...")
    url = f"https://api.blockchair.com/dogecoin/dashboards/address/{address}?limit=100"
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # Blockchair structure: data -> [address] -> transactions
            addr_data = data.get('data', {}).get(address, {})
            txs = addr_data.get('transactions', [])
            print(f"Transactions found: {len(txs)}")
            if txs:
                print("Sample Tx:", txs[0])
        else:
            print("Error:", resp.text[:200])
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_blockchair("DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L")
