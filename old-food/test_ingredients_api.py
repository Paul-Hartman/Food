import json

import requests

# Test with a common product barcode (Coca-Cola)
barcode = "5449000000996"

url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
response = requests.get(url, timeout=10)
data = response.json()

if data.get("status") == 1 and data.get("product"):
    product = data["product"]

    print("=== INGREDIENTS DATA ===\n")

    # Ingredients text
    print("1. ingredients_text:")
    print(product.get("ingredients_text", "N/A"))
    print("\n")

    # Ingredients list (structured)
    print("2. ingredients (structured list):")
    ingredients = product.get("ingredients", [])
    for i, ing in enumerate(ingredients[:5], 1):  # First 5 ingredients
        print(f"\n  Ingredient {i}:")
        print(f"    ID: {ing.get('id', 'N/A')}")
        print(f"    Text: {ing.get('text', 'N/A')}")
        print(f"    Percent: {ing.get('percent_estimate', 'N/A')}")
        print(f"    Vegan: {ing.get('vegan', 'N/A')}")
        print(f"    Vegetarian: {ing.get('vegetarian', 'N/A')}")

    print("\n")

    # Additives
    print("3. additives_tags:")
    print(product.get("additives_tags", []))
    print("\n")

    # Allergens
    print("4. allergens_tags:")
    print(product.get("allergens_tags", []))
    print("\n")

    # Save full product data for inspection
    with open("sample_product_data.json", "w", encoding="utf-8") as f:
        json.dump(product, f, indent=2, ensure_ascii=False)

    print("Full product data saved to sample_product_data.json")
else:
    print("Product not found")
