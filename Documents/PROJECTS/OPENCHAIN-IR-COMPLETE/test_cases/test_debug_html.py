#!/usr/bin/env python3
"""
Debug: Show actual HTML response
"""

import os
from dotenv import load_dotenv
from app import app

load_dotenv()

client = app.test_client()

data = {
    'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    'chain': 'ethereum',
    'start_date': '',
    'end_date': '',
    'include_internal': 'off',
    'include_token_transfers': 'off'
}

print("Submitting form...")
response = client.post('/', data=data, follow_redirects=True)
html = response.data.decode('utf-8', errors='ignore')

# Find and print the overview section
start = html.find('id="overview"')
if start > 0:
    end = html.find('id="charts"', start)
    if end > 0:
        overview = html[start:end]
        print("\n=== OVERVIEW TAB HTML CONTENT ===\n")
        # Pretty print a snippet
        lines = overview.split('\n')
        for i, line in enumerate(lines[:40]):  # First 40 lines
            if line.strip():
                print(f"{i}: {line}")
else:
    print("Overview tab not found in HTML")
    # Check if summary data exists
    if "summary" in html.lower():
        print("\n✅ 'summary' found in HTML")
        start = html.find("summary")
        print(f"\nFirst occurrence at position {start}")
        print(f"Context: {html[start:start+200]}")
