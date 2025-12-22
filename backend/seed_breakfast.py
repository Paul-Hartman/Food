"""Seed the breakfast recipe: Sunny Side Up Eggs with Cheese on Toast"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "food.db")

# Ingredient IDs from the ingredients table
INGREDIENT_IDS = {
    "eggs": 26,
    "cheddar_cheese": 31,
    "bread": 64,
    "butter": 27,
    "salt": 52,
    "black_pepper": 53,
}


def seed_breakfast_recipe():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if recipe already exists
    cursor.execute(
        "SELECT id FROM recipes WHERE name = ?", ["Sunny Side Up Eggs with Cheese on Toast"]
    )
    existing = cursor.fetchone()

    if existing:
        print(f"Recipe already exists with ID: {existing[0]}")
        recipe_id = existing[0]
    else:
        # Insert the recipe
        cursor.execute(
            """
            INSERT INTO recipes (name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                "Sunny Side Up Eggs with Cheese on Toast",
                "A classic quick breakfast: two perfectly fried eggs with melted cheddar on crispy toast",
                "Breakfast",
                "American",
                2,  # prep time
                8,  # cook time
                1,  # servings
                "easy",
                "/static/images/breakfast_eggs_toast.jpg",
            ],
        )
        recipe_id = cursor.lastrowid
        print(f"Created recipe with ID: {recipe_id}")

    # Clear existing ingredients for this recipe
    cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", [recipe_id])

    # Add ingredients (recipe_id, ingredient_id, quantity, unit, notes)
    ingredients = [
        (recipe_id, INGREDIENT_IDS["eggs"], 2, "whole", "Large eggs"),
        (recipe_id, INGREDIENT_IDS["bread"], 2, "slices", "White or whole wheat"),
        (recipe_id, INGREDIENT_IDS["cheddar_cheese"], 28, "g", "About 1 slice"),
        (recipe_id, INGREDIENT_IDS["butter"], 15, "g", "1 tbsp for frying"),
        (recipe_id, INGREDIENT_IDS["salt"], 1, "pinch", "To taste"),
        (recipe_id, INGREDIENT_IDS["black_pepper"], 1, "pinch", "To taste"),
    ]

    cursor.executemany(
        """
        INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
        VALUES (?, ?, ?, ?, ?)
    """,
        ingredients,
    )
    print(f"Added {len(ingredients)} ingredients")

    # Clear existing steps
    cursor.execute("DELETE FROM cooking_steps WHERE recipe_id = ?", [recipe_id])

    # Add cooking steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
    steps = [
        (
            recipe_id,
            1,
            "Prep the toast",
            "Put your bread slices in the toaster and toast until golden brown. Set aside.",
            2,
            "Use medium setting for best results",
            0,
            "prep",
        ),
        (
            recipe_id,
            2,
            "Heat the pan",
            "Place a non-stick pan over medium-low heat. Add butter and let it melt completely, coating the pan.",
            1,
            "Low heat is key for perfect sunny side up eggs",
            0,
            "prep",
        ),
        (
            recipe_id,
            3,
            "Crack the eggs",
            "Crack both eggs gently into the pan, keeping them separate. Season with a pinch of salt and pepper.",
            1,
            "Crack into a small bowl first to avoid shell fragments",
            0,
            "cook",
        ),
        (
            recipe_id,
            4,
            "Cook sunny side up",
            "Let the eggs cook undisturbed for 3-4 minutes until the whites are set but the yolks are still runny.",
            4,
            "Cover with a lid for faster cooking if desired",
            1,
            "cook",
        ),
        (
            recipe_id,
            5,
            "Add cheese to toast",
            "While eggs cook, place the cheddar slices on the warm toast. The residual heat will start melting it.",
            1,
            "For extra melty cheese, put toast under broiler for 30 seconds",
            0,
            "assemble",
        ),
        (
            recipe_id,
            6,
            "Plate and serve",
            "Carefully slide the eggs onto the cheesy toast. Season with additional pepper if desired. Serve immediately!",
            1,
            "Runny yolk + melted cheese = perfection",
            0,
            "serve",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        steps,
    )
    print(f"Added {len(steps)} cooking steps")

    conn.commit()
    conn.close()

    print(f"\nBreakfast recipe seeded successfully!")
    print(f"Recipe ID: {recipe_id}")
    print(f"Total time: 10 minutes")
    return recipe_id


if __name__ == "__main__":
    recipe_id = seed_breakfast_recipe()
