#!/usr/bin/env python3
from app import app

client = app.test_client()
data = {'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'chain': 'ethereum'}

response = client.post('/', data=data, follow_redirects=True)
html = response.data.decode('utf-8', errors='ignore')

checks = {
    'Chain name (ETHEREUM)': 'ETHEREUM',
    'Chain ID': 'Chain ID: 1',
    'Total Transactions': 'Transactions: 10000',
    'Total Inflow badge': 'Total Inflow',
    'Total Outflow badge': 'Total Outflow',
    'Net Flow badge': 'Net Flow',
    'Overview tab': 'id="overview"',
    'Metric Summary': 'Metric Summary',
    'Live Data': 'Live Blockchain Data',
}

print("✅ OVERVIEW TAB DATA VERIFICATION\n")
print("="*60)

all_pass = True
for name, search_term in checks.items():
    if search_term in html:
        print(f"✅ {name:30} FOUND")
    else:
        print(f"❌ {name:30} NOT FOUND")
        all_pass = False

print("="*60)

if all_pass:
    print("\n✅ ALL DATA FIELDS PRESENT IN OVERVIEW TAB")
    print("   The overview tab is rendering correctly!")
else:
    print("\n❌ Some fields are missing")

# Show actual values rendered
print("\n📊 SAMPLE OUTPUT FROM OVERVIEW:")
idx = html.find('Metric Summary')
if idx > 0:
    section = html[idx:idx+700]
    lines = section.split('\n')
    for line in lines[:20]:
        if line.strip() and ('badge' in line or 'stat' in line or 'Metric' in line):
            print(f"  {line.strip()[:80]}")
