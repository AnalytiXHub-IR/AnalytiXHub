
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def check(feature_name, endpoint, method="GET", payload=None, expected_key=None):
    print(f"Testing {feature_name}...", end=" ")
    try:
        if method == "GET":
            r = requests.get(f"{BASE_URL}{endpoint}")
        else:
            r = requests.post(f"{BASE_URL}{endpoint}", json=payload)
            
        if r.status_code == 200:
            data = r.json()
            if expected_key and expected_key not in str(data):
                print(f"⚠️  Partial (Missing {expected_key})")
                return "PARTIAL"
            print("✅  PASS")
            return "PASS"
        elif r.status_code == 404:
             print("❌  Not Implemented (404)")
             return "FAIL"
        else:
            print(f"❌  Error {r.status_code}")
            return "FAIL"
    except Exception as e:
        print(f"❌  Connection Error: {e}")
        return "FAIL"

def run_audit():
    print("\n=== OPENCHAIN-IR FEATURE AUDIT ===\n")
    
    # 1. Real-Time Intelligence
    check("Live Mempool (Polling)", "/api/alerts", expected_key="id")
    check("Cross-Chain Tracking", "/api/tools/cross_chain/0x123", expected_key="chain") # Likely FAIL
    
    # 2. AI Attribution
    check("Behavioral Fingerprinting", "/api/ai/analyze/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", expected_key="predicted_type")
    
    # 3. Illicit Activity
    check("Scam/Rug Pull Detection", "/api/contract/scan", "POST", {"source_code": "selfdestruct(owner)"}, expected_key="Self Destruct")
    check("Mixer Tracing (Demixing)", "/api/tools/demix/0xMOCK_HASH", expected_key="is_coinjoin")
    
    # 4. Graph System
    check("Graph Visualization Data", "/api/graph/visualize/CASE_UNKNOWN", expected_key="data") # Might fail on unknown case
    check("Community Detection", "/api/graph/analyze/CASE_UNKNOWN", expected_key="communities")
    
    # 5. Alert & Response
    check("Smart Alert Engine", "/api/alerts", expected_key="severity")
    
    # 6. Smart Contract Forensics
    check("Contract Risk Classifier", "/api/contract/scan", "POST", {"source_code": "delegatecall"}, expected_key="Delegate Call")
    
    # 7. Off-Chain Intel
    check("Threat Intelligence (Seed)", "/api/intel/lookup/0x77696bb39917c91a5464507f3693fb6826372cae", expected_key="Tornado Cash")
    
    # 8. Privacy (ZK Proofs) - Not implemented
    check("ZK Risk Proofs", "/api/privacy/zk_proof", expected_key="proof") # Likely FAIL
    
    # 9. Predictive Analytics
    check("Predictive Models", "/api/ai/predict_movement", expected_key="prediction") # Likely FAIL

if __name__ == "__main__":
    run_audit()
