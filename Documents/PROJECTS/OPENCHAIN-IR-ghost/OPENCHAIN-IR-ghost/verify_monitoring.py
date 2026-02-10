
import requests
import time
from db_models import SessionLocal, Alert, datetime

BASE_URL = "http://127.0.0.1:5000"

def verify_monitoring():
    print("[-] Verifying Monitoring API...")
    
    # 1. Create a Fake Alert in DB
    db = SessionLocal()
    try:
        alert = Alert(
            case_id=1, # Assuming case 1 exists
            alert_type="test_alert",
            severity="high",
            address="0xTEST_ADDRESS",
            description="Test Alert Verification",
            is_acknowledged=False,
            created_at=datetime.utcnow()
        )
        db.add(alert)
        db.commit()
        print(f"[+] injected Test Alert for 0xTEST_ADDRESS")
    except Exception as e:
        print(f"[-] Failed to inject alert: {e}")
        return
    finally:
        db.close()
        
    # 2. Query API
    try:
        r = requests.get(f"{BASE_URL}/api/alerts")
        if r.status_code == 200:
            data = r.json()
            print(f"[+] API Returned {len(data)} alerts")
            found = False
            for a in data:
                if a['address'] == "0xTEST_ADDRESS":
                    print(f"    [MATCH] Found alert: {a['description']}")
                    found = True
                    break
            
            if not found:
                print("    [FAIL] Test alert not found in API response")
        else:
            print(f"[-] API Error: {r.status_code}")
    except Exception as e:
        print(f"[-] Request Failed: {e}")

if __name__ == "__main__":
    verify_monitoring()
