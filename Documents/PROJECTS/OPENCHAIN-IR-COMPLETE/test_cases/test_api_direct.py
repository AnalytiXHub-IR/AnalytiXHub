#!/usr/bin/env python3
"""Test API connectivity"""
import os
from dotenv import load_dotenv
from eth_live import fetch_eth_address_with_counts

load_dotenv()
API_KEY = os.getenv('ETHERSCAN_API_KEY')

if not API_KEY:
    print("[ERROR] No API key found")
    exit(1)

# Test with Vitalik's address (known to have transactions)
test_addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

print(f"[*] Testing API with address: {test_addr}")
print(f"[*] Chain ID: 1 (Ethereum)")
print(f"[*] API Key exists: {bool(API_KEY)}")

try:
    txs, counts = fetch_eth_address_with_counts(test_addr, API_KEY, chain_id=1)
    print(f"\n[+] API Response received!")
    print(f"    Total txs: {len(txs)}")
    print(f"    Normal: {counts['normal']}")
    print(f"    Internal: {counts['internal']}")
    print(f"    Token: {counts['token']}")
    
    if len(txs) > 0:
        print(f"\n[+] SUCCESS! Got {len(txs)} transactions")
        print(f"    First tx: {txs[0]}")
    else:
        print(f"\n[-] ERROR: Got response but 0 transactions")
except Exception as e:
    print(f"\n[-] ERROR: {e}")
    import traceback
    traceback.print_exc()
