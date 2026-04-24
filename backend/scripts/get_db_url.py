import requests
import json

ACCOUNT_TOKEN = "736d2998-16b1-436a-adc9-5dee44b341f8"
PROJECT_ID = "22dbc794-16d3-46ed-93ae-c55aa399adb1"
ENV_ID = "06518ea8-88a8-4a86-96f4-10f72d6011c9"
BACKEND_ID = "c2a247d8-4238-4b74-9074-1dee63bb0016"
API = "https://backboard.railway.app/graphql/v2"
HEADERS = {"Authorization": f"Bearer {ACCOUNT_TOKEN}", "Content-Type": "application/json"}

query = """
query($projectId: String!, $environmentId: String!, $serviceId: String!) {
  variables(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId)
}
"""
resp = requests.post(API, headers=HEADERS, json={
    "query": query,
    "variables": {"projectId": PROJECT_ID, "environmentId": ENV_ID, "serviceId": BACKEND_ID}
})
vars = resp.json()["data"]["variables"]
print(vars.get("DATABASE_URL"))
