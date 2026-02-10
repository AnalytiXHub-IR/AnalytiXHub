#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from app import app

load_dotenv()

client = app.test_client()
data = {
    'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    'chain': 'ethereum',
}

response = client.post('/', data=data, follow_redirects=True)
html = response.data.decode('utf-8', errors='ignore')

print("Data in HTML response:")
print(f"✅ Chain ID: {'chain_id' in html or 'Chain ID' in html}")
print(f"✅ Risk Score: {'risk_score' in html or 'Risk Score' in html}")
print(f"✅ Overview: {'Metric Summary' in html}")
print(f"✅ Transactions: {'total_transactions' in html or 'Total Txs' in html}")

# Find pattern
pattern = 'Chain ID'
if pattern in html:
    idx = html.find(pattern)
    print(f"\nFound '{pattern}' at position {idx}")
    print(f"Context: {html[max(0,idx-50):idx+100]}")
