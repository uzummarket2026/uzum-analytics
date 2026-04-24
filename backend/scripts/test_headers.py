import requests

token = "rNLRZ0wGhitgYIaGTW1BOCUVTXa7LjA70i7QH9OWYrI="
base_url = "https://api-seller.uzum.uz/api/seller-openapi"

print("--- Testing with Bearer ---")
headers = {"Authorization": f"Bearer {token}"}
r = requests.get(f"{base_url}/v1/shops", headers=headers)
print(f"Status: {r.status_code}, Body: {r.text}")

print("\n--- Testing without Bearer ---")
headers = {"Authorization": token}
r = requests.get(f"{base_url}/v1/shops", headers=headers)
print(f"Status: {r.status_code}, Body: {r.text}")
