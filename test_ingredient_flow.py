"""
Test script to verify ingredient extraction and storage
"""

import os

import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_planner.settings")
django.setup()

from recipes.models import Product, ProductIngredient
from recipes.views import lookup_open_food_facts

# Test barcode (Coca-Cola)
test_barcode = "5449000000996"

print("=" * 60)
print("Testing Ingredient Extraction and Storage")
print("=" * 60)

# Step 1: Fetch data from Open Food Facts
print(f"\n1. Fetching product data for barcode: {test_barcode}")
food_data = lookup_open_food_facts(test_barcode)

if food_data:
    print(f"   [OK] Product found: {food_data['name']}")
    print(f"   [OK] Brand: {food_data.get('brand', 'N/A')}")
    print(f"   [OK] Ingredients extracted: {len(food_data.get('ingredients', []))}")
else:
    print("   [ERROR] Product not found")
    exit(1)

# Step 2: Create/Update product
print("\n2. Creating/Updating product in database")
product, created = Product.objects.get_or_create(
    barcode=test_barcode,
    defaults={
        "name": food_data["name"],
        "brand": food_data["brand"],
        "image_url": food_data["image_url"],
        "description": food_data.get("description", ""),
        "nutrition_data": food_data.get("nutrition", {}),
        "package_weight": food_data.get("package_weight"),
        "package_weight_unit": food_data.get("package_weight_unit", ""),
        "nutriscore": food_data.get("nutriscore", ""),
        "source": "openfoodfacts",
        "source_data": food_data.get("source_data", {}),
    },
)

if created:
    print(f"   [OK] New product created: {product.name}")
else:
    print(f"   [OK] Existing product found: {product.name}")

# Step 3: Save ingredients
print("\n3. Saving ingredients to database")
ingredients_data = food_data.get("ingredients", [])

# Clear existing ingredients
ProductIngredient.objects.filter(product=product).delete()
print(f"   [OK] Cleared existing ingredients")

# Create new ingredient records
ingredient_count = 0
for ing_data in ingredients_data:
    if ing_data.get("ingredient_id"):
        ProductIngredient.objects.create(
            product=product,
            ingredient_id=ing_data.get("ingredient_id", ""),
            text=ing_data.get("text", ""),
            percent_estimate=ing_data.get("percent_estimate"),
            percent_min=ing_data.get("percent_min"),
            percent_max=ing_data.get("percent_max"),
            vegan=ing_data.get("vegan", ""),
            vegetarian=ing_data.get("vegetarian", ""),
            order=ing_data.get("order", 0),
            source_data=ing_data.get("source_data", {}),
        )
        ingredient_count += 1

print(f"   [OK] Created {ingredient_count} ingredient records")

# Step 4: Verify ingredients were saved
print("\n4. Verifying ingredients in database")
saved_ingredients = ProductIngredient.objects.filter(product=product)
print(f"   [OK] Found {saved_ingredients.count()} ingredients in database")

print("\n5. Sample ingredients:")
for ing in saved_ingredients[:5]:
    percent = f"{ing.percent_estimate}%" if ing.percent_estimate else "N/A"
    print(f"   - {ing.text} ({percent})")
    if ing.vegan:
        print(f"     Vegan: {ing.vegan}")
    if ing.vegetarian:
        print(f"     Vegetarian: {ing.vegetarian}")

# Step 6: Test ingredient browser view
print("\n6. Testing ingredients browser view")
from collections import defaultdict

ingredients_dict = defaultdict(
    lambda: {
        "text": "",
        "products": [],
        "vegan": "",
        "vegetarian": "",
        "percent_estimates": [],
    }
)

all_ingredients = ProductIngredient.objects.select_related("product").all()
print(f"   [OK] Total ingredient records in database: {all_ingredients.count()}")

for ing in all_ingredients:
    ing_id = ing.ingredient_id
    if ing_id not in ingredients_dict or not ingredients_dict[ing_id]["text"]:
        ingredients_dict[ing_id]["text"] = ing.text
        ingredients_dict[ing_id]["vegan"] = ing.vegan
        ingredients_dict[ing_id]["vegetarian"] = ing.vegetarian

    ingredients_dict[ing_id]["products"].append(ing.product.name)
    if ing.percent_estimate:
        ingredients_dict[ing_id]["percent_estimates"].append(float(ing.percent_estimate))

print(f"   [OK] Unique ingredients: {len(ingredients_dict)}")

print("\n" + "=" * 60)
print("Test completed successfully!")
print("=" * 60)
print(f"\nYou can now view the ingredients at:")
print(f"http://localhost:8000/ingredients/")
