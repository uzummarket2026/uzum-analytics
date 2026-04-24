import requests
import json

ACCOUNT_TOKEN = "736d2998-16b1-436a-adc9-5dee44b341f8"
PROJECT_ID = "22dbc794-16d3-46ed-93ae-c55aa399adb1"
ENV_ID = "06518ea8-88a8-4a86-96f4-10f72d6011c9"
WORKER_ID = "768ea304-1074-4d2d-806a-95246c5160da"
API = "https://backboard.railway.app/graphql/v2"
HEADERS = {"Authorization": f"Bearer {ACCOUNT_TOKEN}", "Content-Type": "application/json"}

# Reset worker to build from source (not image)
# Actually, I'll just run 'railway up' from the backend directory but targeting the worker service.
pass
