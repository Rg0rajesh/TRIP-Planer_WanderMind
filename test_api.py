import requests
import json

url = "http://127.0.0.1:5000/api/plan"
data = {
    "origin": "Mumbai",
    "destination": "Goa",
    "budget": "500",
    "duration": "3",
    "interests": "beaches, food",
    "travel_style": "budget"
}

print(f"Testing {url}...")
try:
    response = requests.post(url, json=data, timeout=300)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success! Response received.")
        print(json.dumps(response.json(), indent=2)[:500] + "...")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection failed: {e}")
