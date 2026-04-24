import requests
import json

url = "http://localhost:8000/api/settings/"
data = {"key": "uzum_api_token", "value": "test_token_1234567890"}
try:
    print(f"Posting to {url}...")
    r = requests.post(url, json=data, timeout=5)
    print(f"Status: {r.status_code}, Body: {r.text}")
except Exception as e:
    print(f"Error: {e}")
