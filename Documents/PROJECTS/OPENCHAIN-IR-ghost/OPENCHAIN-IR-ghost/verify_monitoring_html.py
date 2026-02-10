
import sys
import os
from app import app
from case_manager import CaseManager

sys.path.append(os.getcwd())

def verify_monitoring_html():
    print("[-] Verifying Monitoring HTML...")
    
    with app.test_client() as client:
        cm = CaseManager()
        cases = cm.list_cases()
        if not cases:
            print("[-] No cases found")
            return
            
        case_id = cases[0].case_id
        rv = client.get(f'/case/{case_id}/monitoring')
        
        html = rv.data.decode('utf-8')
        
        if "Live Transaction Monitoring" in html and "alert-table-body" in html:
            print("[+] Monitoring page rendered correctly with table structure")
        else:
            print("[-] Monitoring page missing key elements")
            
        if "fetchAlerts" in html:
             print("[+] JS Polling logic found")
        else:
             print("[-] JS logic missing")

if __name__ == "__main__":
    verify_monitoring_html()
