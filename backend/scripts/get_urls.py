import requests
import json

ACCOUNT_TOKEN = "736d2998-16b1-436a-adc9-5dee44b341f8"
ENV_ID = "06518ea8-88a8-4a86-96f4-10f72d6011c9"
API = "https://backboard.railway.app/graphql/v2"
HEADERS = {"Authorization": f"Bearer {ACCOUNT_TOKEN}", "Content-Type": "application/json"}

query = """
query($environmentId: String!) {
  environment(id: $environmentId) {
    serviceInstances {
      edges {
        node {
          serviceName
          domains {
            domain
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
print(resp.text)
