import requests

key = 'TUWDXD7G5R3KE7K3UN1YD5F7RKKJIGXDEY'
addr = '0xbb5146F9Ab2e0105452AE3d52683FF15600e4150'

print("Testing address:", addr, "\n")

# Test Polygon v1 API
print("Polygonscan v1 API:")
r = requests.get('https://api.polygonscan.com/api', params={
    'module': 'account',
    'action': 'txlist',
    'address': addr,
    'apikey': key
})
print("Status:", r.status_code)
print("Response:", r.text[:300])
