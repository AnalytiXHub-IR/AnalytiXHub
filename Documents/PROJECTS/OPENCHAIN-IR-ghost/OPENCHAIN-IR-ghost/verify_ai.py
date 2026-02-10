
import requests
import sys
import os

BASE_URL = "http://127.0.0.1:5000"

def verify_ai():
    print("[-] Verifying AI Analysis API...")
    
    # Test with a dummy address
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # Vitalik
    
    try:
        r = requests.get(f"{BASE_URL}/api/ai/analyze/{addr}")
        if r.status_code == 200:
            data = r.json()
            print("[+] API Returned Data:")
            print(f"    Risk Score: {data.get('risk_score')}")
            print(f"    Predicted Type: {data.get('predicted_type')}")
            print(f"    Is Anomaly: {data.get('is_anomaly')}")
        else:
            print(f"[-] API Error: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"[-] Request Failed: {e}")

def verify_graph():
    print("\n[-] Verifying Graph Intelligence API...")
    # Fetch a case ID first? Assumes case 1 exists
    case_id = "CASE_20260210_133327" # Example, but better to list cases
    # Let's just list cases to get a valid ID
    try:
        r = requests.get(f"{BASE_URL}/")
        # Parsing HTML is hard, let's just guess or use a known one.
        # Actually, let's use the DB or just try standard format if we preserved it.
        pass
    except:
        pass

    # Try to hit the endpoint with a dummy ID, expecting empty or error but 200 OK structure
    try:
        # We need a valid case ID for DB query.
        # Let's insert a dummy logic or just rely on manual check? 
        # Better: Import CaseManager and get an ID.
        from case_manager import CaseManager
        cm = CaseManager()
        cases = cm.list_cases()
        if cases:
            case_id = cases[0].case_id
            print(f"[*] using case_id: {case_id}")
            r = requests.get(f"{BASE_URL}/api/graph/analyze/{case_id}")
            if r.status_code == 200:
                data = r.json()
                print("[+] Graph API Returned Data:")
                print(f"    Communities Found: {len(data.get('communities', []))}")
            else:
                print(f"[-] Graph API Error: {r.status_code}")
        else:
            print("[-] No cases found to test Graph API")
            
    except Exception as e:
        print(f"[-] Graph Verification Failed: {e}")

if __name__ == "__main__":
    verify_ai()
    verify_graph()
