
import requests
from app import app
from case_manager import CaseManager
import sys
import os

sys.path.append(os.getcwd())

def verify_charts():
    print("[-] Verifying Chart API...")
    
    with app.test_client() as client:
        cm = CaseManager()
        cases = cm.list_cases()
        if not cases:
            print("[-] No cases found")
            return
            
        case_id = cases[0].case_id
        rv = client.get(f'/api/case/{case_id}/charts')
        
        if rv.status_code == 200:
            data = rv.json
            print("[+] API returned 200 OK")
            
            # Check keys
            if 'risk' in data and 'timeline' in data:
                print(f"[+] Risk Data: {data['risk']}")
                print(f"[+] Timeline Data Points: {len(data['timeline']['labels'])}")
            else:
                print("[-] Missing keys in response")
        else:
            print(f"[-] API Failed: {rv.status_code}")

if __name__ == "__main__":
    verify_charts()
