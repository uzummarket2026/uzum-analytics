import requests
import json
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ACCOUNT_TOKEN = "736d2998-16b1-436a-adc9-5dee44b341f8"
ENV_ID = "06518ea8-88a8-4a86-96f4-10f72d6011c9"
API = "https://backboard.railway.app/graphql/v2"
HEADERS = {"Authorization": f"Bearer {ACCOUNT_TOKEN}", "Content-Type": "application/json"}

# Get current service instance latest deployment ID
query = """
query($environmentId: String!) {
  environment(id: $environmentId) {
    serviceInstances {
      edges {
        node {
          serviceName
          latestDeployment {
            id
            status
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

backend_dep_id = None
for inst in instances:
    if inst["node"]["serviceName"] == "backend":
        backend_dep_id = inst["node"]["latestDeployment"]["id"]
        status = inst["node"]["latestDeployment"]["status"]
        print(f"Active Backend Deployment ID: {backend_dep_id} (Status: {status})")
        break

if backend_dep_id:
    logs_query = "query($id: String!) { deploymentLogs(deploymentId: $id) { message } }"
    l_resp = requests.post(API, headers=HEADERS, json={"query": logs_query, "variables": {"id": backend_dep_id}})
    logs = l_resp.json().get("data", {}).get("deploymentLogs", [])
    print("--- LOGS START ---")
    for log in logs[-100:]:
        print(log.get("message", ""))
    print("--- LOGS END ---")
else:
    print("Backend service instance not found.")
