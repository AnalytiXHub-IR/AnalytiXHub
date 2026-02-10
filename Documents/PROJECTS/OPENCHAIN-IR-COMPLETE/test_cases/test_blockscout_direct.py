#!/usr/bin/env python3
import requests
import json

# Test BlockScout directly
addr = '0xbb5146F9Ab2e0105452AE3d52683FF15600e4150'

print("Testing BlockScout Polygon directly...\n")

try:
    url = f"https://polygon.blockscout.com/api/v2/addresses/{addr}/transactions"
    print(f"URL: {url}")
    print("Making request...")
    
    response = requests.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        print(f"✅ Got {len(items)} transactions from BlockScout Polygon!")
        if items:
            print(f"First TX: {items[0].get('hash')}")
    else:
        print(f"Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}")
