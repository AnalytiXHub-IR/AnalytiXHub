import requests

addr = '0xe5277AA484C6d11601932bfFE553A55E37dC04Cf'
key = 'TUWDXD7G5R3KE7K3UN1YD5F7RKKJIGXDEY'

# Test: https://api.polygonscan.com/api with chainid param
url = 'https://api.polygonscan.com/api'

# v2 format: include chainid param
params = {
    'chainid': 137,
    'module': 'account', 
    'action': 'txlist', 
    'address': addr, 
    'apikey': key
}

print("Testing v2 format WITH chainid param...")
r = requests.get(url, params=params, timeout=10)
print("Status Code:", r.status_code)
data = r.json()
print("Response Status:", data.get('status'))
msg = data.get('message')
if isinstance(msg, str):
    print("Message:", msg[:100])
else:
    print("Message:", msg)

result = data.get('result')
if isinstance(result, list):
    print(f"RESULT: List with {len(result)} items")
    if result:
        import json
        print("First TX:", json.dumps(result[0], indent=2))
else:
    print(f"RESULT type: {type(result)}")
    print(f"RESULT: {str(result)[:200]}")
