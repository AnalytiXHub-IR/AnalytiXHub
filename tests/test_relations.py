import requests

s = requests.Session()
# Login
resp = s.post('http://127.0.0.1:5000/login', data={'username': 'admin', 'password': 'password'})
print(f"Login status: {resp.status_code}")

# Get relations
res = s.get('http://127.0.0.1:5000/api/relations?source=0x742d35Cc6634C0532925a3b844Bc454e4438f44e&target=0x2&chain=ethereum')
print(f"API status: {res.status_code}")
print(f"API response: {res.text}")
