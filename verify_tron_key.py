
import requests
import os

# Key from .env / source code
TRON_API_KEY = "72ac1d93-4497-4664-a844-f730b2b5e606"
GRID_BASE_URL = "https://api.trongrid.io"

def test_key():
    print(f"Testing TronGrid Key: {TRON_API_KEY}")
    headers = {"TRON-PRO-API-KEY": TRON_API_KEY}
    url = f"{GRID_BASE_URL}/v1/accounts/TF18S4mgJPjejwEygWQWqtbEppuJ2fJLUR/transactions"
    
    try:
        response = requests.get(url, headers=headers, params={'limit': 1}, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            print("✅ Key is VALID.")
        elif response.status_code == 401:
            print("❌ Key is INVALID (Unauthorized).")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_key()
