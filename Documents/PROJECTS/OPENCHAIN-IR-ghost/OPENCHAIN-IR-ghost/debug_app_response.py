
import sys
import os
from app import app
from db_models import init_db

# Ensure we can import app
sys.path.append(os.getcwd())

def debug_response():
    print("[-] Debugging App Response...")
    
    # Create test client
    with app.test_client() as client:
        # Request Index
        print("\n[Requesting /]")
        rv = client.get('/')
        print(f"Status Code: {rv.status_code}")
        print(f"Content-Type: {rv.content_type}")
        print("Data Snippet (First 500 chars):")
        print(rv.data.decode('utf-8')[:500])
        
        # Check if it looks like JSON
        if rv.content_type == 'application/json':
            print("ALERT: Content-Type is JSON!")
        
        if rv.data.strip().startswith(b'{') or rv.data.strip().startswith(b'['):
             print("ALERT: Body looks like JSON!")
             
        # Request Dashboard if we can find a case
        # retrieving case via DB
        from case_manager import CaseManager
        cm = CaseManager()
        cases = cm.list_cases()
        if cases:
            case_id = cases[0].case_id
            print(f"\n[Requesting /case/{case_id}/dashboard]")
            rv = client.get(f'/case/{case_id}/dashboard')
            print(f"Status Code: {rv.status_code}")
            print(f"Content-Type: {rv.content_type}")
            print("Data Snippet (First 500 chars):")
            print(rv.data.decode('utf-8')[:500])
        else:
            print("\n[No cases found to test dashboard]")

if __name__ == "__main__":
    debug_response()
