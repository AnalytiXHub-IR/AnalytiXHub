import requests
import json

API_KEY = "81CGNLRY9ICK6HOK5D52XIG6D7RXG5"
BASE_URL = "https://api.breadcrumbs.one"

HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

TEST_ADDRESS = "13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94"
CHAIN = "bitcoin"

def test_variations():
    base = "https://api.breadcrumbs.one"
    
    # Valid-looking paths from previous run
    tests = [
        # Path 1: /risk/address (Body)
        ("/risk/address", "POST", {"address": TEST_ADDRESS, "chain": CHAIN}),
        # Path 2: /risk/address/{ADDR} (Body?)
        (f"/risk/address/{TEST_ADDRESS}", "POST", {}),
        # Path 3: The one from the user's list (maybe it was correct?)
        ("/risk/addressget", "POST", {"address": TEST_ADDRESS, "chain": CHAIN}),
        # Path 4: Transaction Post
        ("/smartexpand/transactionpost", "POST", {"address": TEST_ADDRESS, "chain": CHAIN, "limit": 10}),
        # Path 5: Transaction (Clean)
        ("/smartexpand/transaction", "POST", {"address": TEST_ADDRESS, "chain": CHAIN, "limit": 10})
    ]

    for path, method, payload in tests:
        url = f"{base}{path}"
        print(f"[*] Testing {method} {url}")
        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"[+] SUCCESS: {url}")
                print(json.dumps(response.json(), indent=2)[:500])
            else:
                print(f"[-] FAILED: {response.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 20)

if __name__ == "__main__":
    test_variations()



