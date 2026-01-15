#!/usr/bin/env python3
from app import app

client = app.test_client()
data = {'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'chain': 'ethereum'}

response = client.post('/', data=data, follow_redirects=True)
html = response.data.decode('utf-8', errors='ignore')

# Find Transactions badge
idx = html.find('Transactions:')
if idx > 0:
    section = html[idx:idx+100]
    print("Transactions badge content:")
    print(section)
    print()

# Find the metric summary section
idx2 = html.find('Metric Summary')
if idx2 > 0:
    section2 = html[idx2:idx2+500]
    print("\nMetric Summary section:")
    print(section2[:400])
