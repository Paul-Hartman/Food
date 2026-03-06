import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test recipe API
response = requests.get('http://192.168.2.38:5025/api/recipes/1125')
data = response.json()

print(f"[OK] Recipe: {data['recipe']['name']}")
print(f"[OK] Total Ingredients: {len(data['ingredients'])}")

print("\nDRY BOWL (Step 1):")
for ing in sorted(data['ingredients'], key=lambda x: -x['quantity'] if 'Dry' in x.get('notes', '') else 0):
    if 'Dry' in ing.get('notes', ''):
        print(f"  - {ing['quantity']}{ing['unit']} {ing['name']}")

print("\nWET BOWL (Step 3):")
for ing in sorted(data['ingredients'], key=lambda x: -x['quantity']):
    if 'Wet' in ing.get('notes', '') or 'Melted' in ing.get('notes', ''):
        print(f"  - {ing['quantity']}{ing['unit']} {ing['name']}")

print(f"\n[OK] Total Steps: {len(data['steps'])}")
timer_steps = [s for s in data['steps'] if s['timer_needed']]
print(f"[OK] Timer Steps: {len(timer_steps)} (Steps {', '.join(str(s['step_number']) for s in timer_steps)})")

print("\n" + "="*50)
print("RECIPE IS READY!")
