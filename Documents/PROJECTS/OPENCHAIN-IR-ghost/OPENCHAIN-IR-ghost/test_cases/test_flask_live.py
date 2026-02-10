#!/usr/bin/env python3
"""Test Flask app"""
import requests
import time

time.sleep(2)  # Give Flask time to start

print("[*] Testing Flask at http://127.0.0.1:5000")

try:
    # Get form
    resp = requests.get('http://127.0.0.1:5000/', timeout=5)
    print(f"[+] GET / returned status {resp.status_code}")
    
    # Submit analysis for Vitalik (Ethereum)
    print("\n[*] Submitting Vitalik address for analysis...")
    data = {
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'chain': 'ethereum',
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'include_internal': 'on',
        'include_token_transfers': 'on'
    }
    
    resp = requests.post('http://127.0.0.1:5000/', data=data, timeout=60)
    print(f"[+] POST / returned status {resp.status_code}")
    
    # Check response content
    if 'Risk Score' in resp.text:
        print("[+] Response contains Risk Score ✓")
    if 'Volume' in resp.text or 'volume' in resp.text.lower():
        print("[+] Response contains volume data ✓")
    if '10000' in resp.text or '10,000' in resp.text:
        print("[+] Response contains transaction count ✓")
    if '0' in resp.text and 'transaction' in resp.text.lower():
        print("[-] Response may indicate 0 transactions")
        
    # Save response to file for inspection
    with open('flask_response.html', 'w') as f:
        f.write(resp.text)
    print("\n[+] Response saved to flask_response.html")
    
    # Look for transaction counts in response
    if 'Total Transactions:' in resp.text:
        idx = resp.text.find('Total Transactions:')
        print(f"\nFound in response: {resp.text[idx:idx+100]}")
    
except requests.exceptions.ConnectionError as e:
    print(f"[-] Cannot connect to Flask: {e}")
    print("[*] Make sure Flask is running: python app.py")
except Exception as e:
    print(f"[-] Error: {e}")
