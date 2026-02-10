
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def log(name, success, msg=""):
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {name}: {msg}")

def verify_full_system():
    print("=== STARTING SYSTEM HEALTH CHECK ===")
    
    # 1. AI Engine
    try:
        r = requests.get(f"{BASE_URL}/api/ai/analyze/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        if r.status_code == 200 and "risk_score" in r.json():
            log("AI Engine", True, f"Score: {r.json()['risk_score']}")
        else:
            log("AI Engine", False, f"Status {r.status_code}")
    except Exception as e:
        log("AI Engine", False, str(e))

    # 2. Threat Intel (Seeded Check)
    try:
        # Tornado Cash address seeded in threat_intel.py
        r = requests.get(f"{BASE_URL}/api/intel/lookup/0x77696bb39917c91a5464507f3693fb6826372cae")
        data = r.json()
        if r.status_code == 200 and data.get("entity") == "Mixer: Tornado Cash":
            log("Threat Intel", True, "Successfully identified Tornado Cash")
        else:
            log("Threat Intel", False, f"Failed to identify seed. Got: {data}")
    except Exception as e:
        log("Threat Intel", False, str(e))

    # 3. Contract Scanner
    try:
        payload = {"source_code": "contract Test { function withdraw() public onlyOwner { selfdestruct(owner); } }"}
        r = requests.post(f"{BASE_URL}/api/contract/scan", json=payload)
        data = r.json()
        if r.status_code == 200 and "Self Destruct" in str(data.get("findings")):
            log("Contract Scanner", True, "Detected Self Destruct")
        else:
            log("Contract Scanner", False, f"Failed detection. Got: {data}")
    except Exception as e:
        log("Contract Scanner", False, str(e))

    # 4. Tracer / Graph API
    try:
        # Need a case ID. Listing cases first.
        # This is tricky without case_manager, but let's try a lucky guess or skipping specific ID check logic
        # and just checking if endpoint responds 404/500/200 
        r = requests.get(f"{BASE_URL}/api/graph/visualize/CASE_UNKNOWN_TEST")
        # Should return 200 with empty list or 404/500 if error
        if r.status_code == 200:
             log("Graph API", True, "Endpoint active")
        else:
             log("Graph API", False, f"Status {r.status_code}")
    except Exception as e:
        log("Graph API", False, str(e))

    print("=== CHECK COMPLETE ===")

if __name__ == "__main__":
    verify_full_system()
