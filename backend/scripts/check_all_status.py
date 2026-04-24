import requests
import json

ACCOUNT_TOKEN = "736d2998-16b1-436a-adc9-5dee44b341f8"
ENV_ID = "06518ea8-88a8-4a86-96f4-10f72d6011c9"
API = "https://backboard.railway.app/graphql/v2"
HEADERS = {"Authorization": f"Bearer {ACCOUNT_TOKEN}", "Content-Type": "application/json"}

# List service instances in this environment
query = """
query($environmentId: String!) {
  environment(id: $environmentId) {
    serviceInstances {
      edges {
        node {
          serviceName
          latestDeployment {
            status
            createdAt
          }
        }
      }
    }
  }
}
"""
resp = requests.post(API, headers=HEADERS, json={
    "query": query,
    "variables": {"environmentId": ENV_ID}
})
instances = resp.json()["data"]["environment"]["serviceInstances"]["edges"]

print("\n--- JORIY HOZIRGI HOLAT (DEPLOYMENT STATUS) ---")
for inst in instances:
    node = inst["node"]
    status = node['latestDeployment']['status']
    time = node['latestDeployment']['createdAt']
    print(f"[{node['serviceName'].upper()}]: {status} (Yangilangan: {time})")
