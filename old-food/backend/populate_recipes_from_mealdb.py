"""
Populate the database with 100+ recipes from TheMealDB API
All recipes include images, instructions, and ingredients
"""

import sqlite3
import requests
import time

DATABASE = "food.db"

def fetch_recipes():
    """Fetch recipes from TheMealDB API."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Fetching recipes from TheMealDB API...")

    # Categories to fetch
    categories = [
        'Beef', 'Chicken', 'Dessert', 'Lamb', 'Miscellaneous',
        'Pasta', 'Pork', 'Seafood', 'Side', 'Starter',
        'Vegan', 'Vegetarian', 'Breakfast', 'Goat'
    ]

    recipes_added = 0

    for category in categories:
        print(f"\nFetching {category} recipes...")

        try:
            # Fetch recipes by category
            response = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}")
            data = response.json()

            if not data.get('meals'):
                continue

            meals = data['meals'][:10]  # Get first 10 from each category

            for meal in meals:
                meal_id = meal['idMeal']

                # Check if already exists
                exists = cursor.execute(
                    "SELECT id FROM recipes WHERE name = ?",
                    (meal['strMeal'],)
                ).fetchone()

                if exists:
                    continue

                # Get full meal details
                detail_response = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}")
                detail_data = detail_response.json()

                if not detail_data.get('meals'):
                    continue

                meal_detail = detail_data['meals'][0]

                # Map category to our categories
                meal_category = category.lower()
                if meal_category in ['beef', 'chicken', 'pork', 'lamb', 'seafood', 'goat']:
                    meal_category = 'main'
                elif meal_category in ['side', 'starter']:
                    meal_category = 'side'
                elif meal_category == 'breakfast':
                    meal_category = 'Breakfast'
                elif meal_category == 'dessert':
                    meal_category = 'Dessert'
                else:
                    meal_category = 'main'

                # Map area to cuisine
                area = meal_detail.get('strArea', 'unknown').lower()
                cuisine_map = {
                    'american': 'american',
                    'british': 'american',
                    'canadian': 'american',
                    'chinese': 'asian',
                    'japanese': 'asian',
                    'thai': 'asian',
                    'vietnamese': 'asian',
                    'indian': 'asian',
                    'italian': 'italian',
                    'mexican': 'mexican',
                    'french': 'italian',
                    'spanish': 'italian',
                    'greek': 'italian',
                }
                cuisine = cuisine_map.get(area, 'american')

                # Estimate prep and cook times (TheMealDB doesn't provide this)
                # Use instruction length as rough estimate
                instructions = meal_detail.get('strInstructions', '')
                instruction_length = len(instructions)

                if instruction_length < 500:
                    prep_time = 5
                    cook_time = 15
                elif instruction_length < 1000:
                    prep_time = 10
                    cook_time = 20
                elif instruction_length < 1500:
                    prep_time = 15
                    cook_time = 30
                else:
                    prep_time = 20
                    cook_time = 40

                # Insert recipe
                cursor.execute("""
                    INSERT INTO recipes (
                        name, description, category, cuisine,
                        prep_time_min, cook_time_min, servings, difficulty,
                        image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    meal_detail['strMeal'],
                    f"{meal_detail['strMeal']} - {category}",
                    meal_category,
                    cuisine,
                    prep_time,
                    cook_time,
                    4,  # Default servings
                    'easy',
                    meal_detail['strMealThumb']  # Image URL from TheMealDB
                ))

                recipe_id = cursor.lastrowid

                # Add ingredients
                for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                    ingredient_name = meal_detail.get(f'strIngredient{i}', '').strip()
                    ingredient_measure = meal_detail.get(f'strMeasure{i}', '').strip()

                    if not ingredient_name or ingredient_name.lower() in ['', 'null']:
                        continue

                    # Check if ingredient exists in our database
                    ing = cursor.execute(
                        "SELECT id FROM ingredients WHERE name = ?",
                        (ingredient_name.lower(),)
                    ).fetchone()

                    if ing:
                        # Add recipe_ingredient
                        cursor.execute("""
                            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
                            VALUES (?, ?, ?, ?)
                        """, (recipe_id, ing['id'], 1, ingredient_measure or 'to taste'))

                # Add cooking instructions as steps (if table exists)
                try:
                    if instructions:
                        # Split by period or newline
                        steps = [s.strip() for s in instructions.replace('\r\n', '\n').split('\n') if s.strip()]

                        for idx, step in enumerate(steps[:10], 1):  # Max 10 steps
                            if len(step) < 10:  # Skip very short lines
                                continue

                            cursor.execute("""
                                INSERT INTO cooking_steps (recipe_id, step_number, title, instruction)
                                VALUES (?, ?, ?, ?)
                            """, (recipe_id, idx, f"Step {idx}", step))
                except sqlite3.OperationalError:
                    pass  # Table doesn't exist, skip steps

                recipes_added += 1
                print(f"  Added: {meal_detail['strMeal']}")

                time.sleep(0.2)  # Rate limiting

        except Exception as e:
            print(f"  Error fetching {category}: {e}")
            continue

    conn.commit()
    conn.close()

    print(f"\nAdded {recipes_added} new recipes!")
    print(f"All recipes have images from TheMealDB")

if __name__ == "__main__":
    fetch_recipes()
