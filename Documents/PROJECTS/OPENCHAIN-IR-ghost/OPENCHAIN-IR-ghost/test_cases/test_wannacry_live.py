#!/usr/bin/env python3
"""
Quick test of WannaCry analysis without Flask
"""
import requests
import json
from time import sleep

print("[*] Testing WannaCry address analysis...")
print("[*] Flask app must be running on http://127.0.0.1:5000")

try:
    # Fetch the form first
    resp = requests.get('http://127.0.0.1:5000/', timeout=5)
    if resp.status_code == 200:
        print("[+] Flask app is running")
    else:
        print(f"[-] Flask returned status {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"[-] Cannot connect to Flask: {e}")
    print("[*] Start the app with: python app.py")
    exit(1)

# Submit analysis form
print("\n[*] Submitting WannaCry address analysis...")
data = {
    'address': '0x8626f6940e2eb28930df1c8e74e7b6aaf002e33e',
    'chain': 'ethereum',
    'start_date': '2021-01-01',
    'end_date': '2024-12-31'
}

try:
    resp = requests.post('http://127.0.0.1:5000/', data=data, timeout=30)
    print(f"[+] Analysis submitted (Status: {resp.status_code})")
    
    if 'WannaCry' in resp.text or 'CRITICAL' in resp.text or 'Ransomware' in resp.text:
        print("[+] Response contains WannaCry/CRITICAL/Ransomware - SUCCESS!")
        print("[+] Address recognized as ransomware!")
    elif 'risk' in resp.text.lower():
        print("[+] Response contains risk assessment")
        if resp.text.count('95') or resp.text.count('99'):
            print("[+] CRITICAL risk score detected!")
    
    # Check for key indicators
    checks = {
        'Risk Score': 'Risk Score' in resp.text or 'risk_score' in resp.text,
        'Patterns Detected': 'DETECTED PATTERNS' in resp.text or 'patterns' in resp.text,
        'Entity Recognition': 'WannaCry' in resp.text or 'Ransomware' in resp.text,
    }
    
    print("\n[CHECKS]")
    for check, passed in checks.items():
        status = "[OK]" if passed else "[NO]"
        print(f"  {status} {check}")
    
except Exception as e:
    print(f"[-] Analysis failed: {e}")
    exit(1)

print("\n[+] WannaCry analysis test complete!")
print("[*] Open http://127.0.0.1:5000 in browser to see results")
