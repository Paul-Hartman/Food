"""
Add placeholder images to all recipes
Uses Unsplash Source for food images
"""

import sqlite3

DATABASE = "food.db"

def add_images():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Adding recipe images...")

    # Get all recipes
    recipes = cursor.execute("SELECT id, name, category, cuisine FROM recipes").fetchall()

    # Map of cuisine/category to specific food keywords
    cuisine_keywords = {
        'mexican': 'tacos',
        'italian': 'pasta',
        'asian': 'noodles',
        'american': 'burger',
    }

    category_keywords = {
        'main': 'dinner',
        'side': 'salad',
        'breakfast': 'breakfast',
        'drink': 'smoothie',
    }

    for recipe_id, name, category, cuisine in recipes:
        # Determine best keyword for image
        keyword = cuisine_keywords.get(cuisine) or category_keywords.get(category) or 'food'

        # Use Unsplash Source with a seed based on recipe ID for consistency
        image_url = f"https://source.unsplash.com/400x300/?{keyword},food&sig={recipe_id}"

        cursor.execute(
            "UPDATE recipes SET image_url = ? WHERE id = ?",
            (image_url, recipe_id)
        )
        print(f"  {recipe_id}: {name} -> {keyword}")

    conn.commit()
    conn.close()

    print(f"\nUpdated {len(recipes)} recipes with placeholder images")
    print("Images will load from Unsplash Source")

if __name__ == "__main__":
    add_images()
