
import requests

url = "https://dogechain.info/address/DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    with open("debug_doge.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved debug_doge.html")
except Exception as e:
    print(f"Error: {e}")
