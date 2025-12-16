"""Test login directly"""
import requests
import json

url = "http://localhost:8000/api/auth/login"
data = {
    "email": "admin@skillboard.com",
    "password": "admin123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Login successful!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n❌ Login failed with status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")
