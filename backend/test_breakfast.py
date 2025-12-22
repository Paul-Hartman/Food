import json

import requests

data = {
    "meal_name": "Sunny Side Up Eggs with Cheese on Toast",
    "meal_type": "breakfast",
    "ingredients": [
        {"name": "egg fried", "amount_g": 92},
        {"name": "cheddar cheese", "amount_g": 28},
        {"name": "bread white", "amount_g": 50},
    ],
}

try:
    response = requests.post(
        "http://localhost:5020/api/nutrition/quick-meal", json=data, timeout=60
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:2000]}")
except Exception as e:
    print(f"Error: {e}")
