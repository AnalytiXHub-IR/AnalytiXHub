
import requests

BASE_URL = "http://127.0.0.1:5000"

def verify_phase7():
    print("Verifying Phase 7 (Gap Filling)...")
    
    # 1. Cross Chain (Polygon Bridge)
    try:
        # Polygon Bridge Address
        r = requests.get(f"{BASE_URL}/api/tools/cross_chain/0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf")
        if r.status_code == 200 and r.json().get("is_cross_chain"):
            print("✅ Cross-Chain Tracker: PASS")
        else:
            print(f"❌ Cross-Chain Tracker: FAIL (Got {r.json()})")
    except Exception as e:
        print(f"❌ Cross-Chain Tracker: Error {e}")

    # 2. Predictive Analytics (Using seed address)
    try:
        r = requests.get(f"{BASE_URL}/api/predict/movement/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        if r.status_code == 200:
            print(f"✅ Predictive Analytics: PASS ({r.json()})")
        else:
            print(f"❌ Predictive Analytics: FAIL (Status {r.status_code})")
    except Exception as e:
        print(f"❌ Predictive Analytics: Error {e}")

if __name__ == "__main__":
    verify_phase7()
