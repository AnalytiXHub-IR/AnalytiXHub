#!/usr/bin/env python3
"""
Test Flask app form submission and response
"""

import os
import json
from dotenv import load_dotenv
from app import app

load_dotenv()

def test_flask_routes():
    """Test that Flask routes work without errors"""
    print("\n" + "="*80)
    print("TESTING FLASK ROUTES")
    print("="*80)
    
    client = app.test_client()
    
    # Test 1: GET / should show form
    print("\n[1/2] Testing GET / (Load form)...", end=" ")
    response = client.get('/')
    if response.status_code == 200 and b'chain' in response.data:
        print("✅")
    else:
        print(f"❌ Status: {response.status_code}")
        return False
    
    # Test 2: POST / with Ethereum address
    print("\n[2/2] Testing POST / (Ethereum analysis)...", end=" ")
    data = {
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'chain': 'ethereum',
        'start_date': '',
        'end_date': '',
        'include_internal': 'off',
        'include_token_transfers': 'off'
    }
    
    try:
        response = client.post('/', data=data, follow_redirects=True)
        if response.status_code == 200:
            # Check that response contains summary data
            if b'total_transactions' in response.data or b'Total Txs' in response.data or b'Overview' in response.data:
                print("✅")
                return True
            else:
                print("❌ Response missing expected data")
                return False
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 FLASK APP TEST")
    
    try:
        if test_flask_routes():
            print("\n" + "="*80)
            print("✅ FLASK TESTS PASSED")
            print("="*80)
            exit(0)
        else:
            print("\n" + "="*80)
            print("❌ FLASK TESTS FAILED")
            print("="*80)
            exit(1)
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
