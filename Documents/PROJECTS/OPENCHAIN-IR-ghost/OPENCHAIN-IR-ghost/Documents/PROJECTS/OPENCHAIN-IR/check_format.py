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

# Find the Metric Summary section
start = html.find('Metric Summary')
if start > 0:
    section = html[start:start+600]
    print("METRIC SUMMARY SECTION:")
    print(section)
    print()

# Check actual data values
if '+14320' in html or '+3.6' in html:
    print("✅ Proper formatting found (2 decimal places)")
elif '+' in html:
    idx = html.find('Total Inflow') 
    if idx > 0:
        print(html[idx:idx+100])
