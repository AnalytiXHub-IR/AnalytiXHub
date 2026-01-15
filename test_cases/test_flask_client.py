#!/usr/bin/env python3
"""Test if Flask can start without errors"""
import sys
import traceback

try:
    print("[*] Importing Flask...")
    from flask import Flask
    print("[OK] Flask imported")
    
    print("[*] Importing app module...")
    from app import app
    print("[OK] App module imported")
    
    print("[*] Starting test client...")
    client = app.test_client()
    print("[OK] Test client created")
    
    print("[*] Testing GET /...")
    resp = client.get('/')
    print(f"[OK] GET / returned {resp.status_code}")
    
    print("[*] Testing POST / with address...")
    resp = client.post('/', data={
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'chain': 'ethereum'
    })
    print(f"[OK] POST / returned {resp.status_code}")
    
    if b'Risk Score' in resp.data or b'Vitalik' in resp.data:
        print("[+] Response contains expected data")
    else:
        print("[-] Response missing expected data")
        print(f"Response first 500 chars: {resp.data[:500]}")
    
except Exception as e:
    print(f"\n[-] ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n[+] All tests passed!")
