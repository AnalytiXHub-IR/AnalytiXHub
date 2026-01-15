import os
import requests
from dotenv import load_dotenv

# 1. Load the key
load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")

print(f"Testing Key: ...{api_key[-6:] if api_key else 'NONE'}")

# 2. Test Connection
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}
data = {
    "contents": [{"parts": [{"text": "Reply with the word Success."}]}]
}

try:
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("\n✅ SUCCESS! Your API Key is working perfectly.")
        print("Response:", response.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"\n❌ FAILED. Error Code: {response.status_code}")
        print("Reason:", response.text)
except Exception as e:
    print(f"\n❌ ERROR: {e}")