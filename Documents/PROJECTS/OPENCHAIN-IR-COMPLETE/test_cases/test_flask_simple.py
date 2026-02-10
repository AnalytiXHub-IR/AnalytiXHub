#!/usr/bin/env python3
"""Test Flask connectivity"""
import sys
import time
import requests

# Give Flask time to start
time.sleep(2)

try:
    # Test GET
    print("[*] Testing GET request...")
    resp = requests.get('http://127.0.0.1:5000/', timeout=5)
    print(f"[OK] GET returned {resp.status_code}")
    
    # Test POST
    print("[*] Testing POST request with test address...")
    data = {
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  # Vitalik
        'chain': 'ethereum',
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
    resp = requests.post('http://127.0.0.1:5000/', data=data, timeout=60)
    print(f"[OK] POST returned {resp.status_code}")
    
    # Check if we got transaction data
    if 'transactions' in resp.text.lower() or 'risk' in resp.text.lower():
        print("[OK] Response contains analysis data")
        # Count transactions mentioned
        if '0' in resp.text and 'transactions' in resp.text.lower():
            print("[!] WARNING: Response shows 0 transactions - API issue?")
    else:
        print("[!] Response does not contain expected analysis data")
        
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
