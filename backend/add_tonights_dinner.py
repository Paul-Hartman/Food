"""
Add Tonight's Dinner Recipes
Adds 3 simple recipes: Blackened Chicken Breast, Roasted Carrots, Sautéed Broccoli with Garlic
"""

import sqlite3


def add_tonights_dinner():
    conn = sqlite3.connect("food.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Recipe 1: Blackened Chicken Breast
    print("Adding Recipe 1: Blackened Chicken Breast...")
    cursor.execute(
        """
        INSERT INTO recipes (name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            "Blackened Chicken Breast",
            "Spicy cajun-seasoned chicken with crispy charred crust",
            "main",
            "cajun",
            5,
            15,
            2,
            "easy",
        ],
    )
    recipe1_id = cursor.lastrowid

    # Recipe 1 Ingredients
    ingredients1 = [
        {
            "name": "Chicken Breast",
            "quantity": 1.0,
            "unit": "lb",
            "notes": "2 large breasts, about 8oz each",
        },
        {
            "name": "Cajun Seasoning",
            "quantity": 2,
            "unit": "tbsp",
            "notes": "Store-bought or homemade",
        },
        {"name": "Olive Oil", "quantity": 2, "unit": "tbsp", "notes": "For coating"},
        {"name": "Butter", "quantity": 1, "unit": "tbsp", "notes": "For finishing"},
        {"name": "Lemon", "quantity": 0.5, "unit": "whole", "notes": "For serving, optional"},
    ]

    for ing in ingredients1:
        # Find or create ingredient
        cursor.execute("SELECT id FROM ingredients WHERE LOWER(name) = LOWER(?)", [ing["name"]])
        result = cursor.fetchone()

        if result:
            ing_id = result[0]
        else:
            print(f"  Creating new ingredient: {ing['name']}")
            # Auto-categorize
            category = (
                "spice"
                if "seasoning" in ing["name"].lower()
                else (
                    "fruit"
                    if "lemon" in ing["name"].lower()
                    else (
                        "protein"
                        if "chicken" in ing["name"].lower()
                        else "dairy" if "butter" in ing["name"].lower() else "pantry"
                    )
                )
            )

            aldi_section = (
                "Pantry"
                if category in ["spice", "pantry"]
                else (
                    "Produce"
                    if category == "fruit"
                    else "Meat & Seafood" if category == "protein" else "Dairy & Eggs"
                )
            )

            cursor.execute(
                """
                INSERT INTO ingredients (name, category, aldi_section, default_unit)
                VALUES (?, ?, ?, ?)
            """,
                [ing["name"], category, aldi_section, ing["unit"]],
            )
            ing_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            [recipe1_id, ing_id, ing["quantity"], ing["unit"], ing.get("notes")],
        )

    # Recipe 1 Steps
    steps1 = [
        {
            "step_number": 1,
            "title": "Prep Chicken",
            "instruction": "Pat chicken breasts dry with paper towels. If thick, pound to even 3/4 inch thickness for even cooking.",
            "duration_min": None,
            "tips": "Dry surface = better seasoning adhesion and sear",
            "timer_needed": 0,
            "step_type": "prep",
        },
        {
            "step_number": 2,
            "title": "Season Chicken",
            "instruction": "Brush both sides of chicken with olive oil. Coat generously with cajun seasoning, pressing it into the meat.",
            "duration_min": None,
            "tips": "Don't be shy with the seasoning - it creates the blackened crust",
            "timer_needed": 0,
            "step_type": "prep",
        },
        {
            "step_number": 3,
            "title": "Heat Pan",
            "instruction": "Heat a cast iron or heavy skillet over medium-high heat until very hot, about 3 minutes. No oil in pan yet.",
            "duration_min": 3,
            "tips": "Pan must be smoking hot for proper blackening",
            "timer_needed": 1,
            "step_type": "cook",
        },
        {
            "step_number": 4,
            "title": "Cook First Side",
            "instruction": "Place chicken in hot pan. DON'T MOVE IT. Cook 6-7 minutes until dark crust forms.",
            "duration_min": 7,
            "tips": "Resist the urge to flip early - crust needs time to form",
            "timer_needed": 1,
            "step_type": "cook",
        },
        {
            "step_number": 5,
            "title": "Flip and Finish",
            "instruction": "Flip chicken. Add butter to pan. Cook another 6-7 min until internal temp reaches 165F.",
            "duration_min": 7,
            "tips": "Use a meat thermometer - don't guess",
            "timer_needed": 1,
            "step_type": "cook",
        },
        {
            "step_number": 6,
            "title": "Rest and Serve",
            "instruction": "Remove to plate. Let rest 5 minutes before slicing. Squeeze lemon over top if desired.",
            "duration_min": 5,
            "tips": "Resting keeps the juices in the meat",
            "timer_needed": 1,
            "step_type": "serve",
        },
    ]

    for step in steps1:
        cursor.execute(
            """
            INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                recipe1_id,
                step["step_number"],
                step["title"],
                step["instruction"],
                step["duration_min"],
                step["tips"],
                step["timer_needed"],
                step["step_type"],
            ],
        )

    print(f"[OK] Recipe 1 added: ID {recipe1_id}")

    # Recipe 2: Roasted Carrots
    print("\nAdding Recipe 2: Roasted Carrots...")
    cursor.execute(
        """
        INSERT INTO recipes (name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            "Roasted Carrots",
            "Simple oven-roasted carrots with caramelized edges",
            "side",
            "american",
            5,
            25,
            4,
            "easy",
        ],
    )
    recipe2_id = cursor.lastrowid

    # Recipe 2 Ingredients
    ingredients2 = [
        {"name": "Carrots", "quantity": 1, "unit": "lb", "notes": "Peeled and cut into sticks"},
        {"name": "Olive Oil", "quantity": 2, "unit": "tbsp", "notes": ""},
        {"name": "Salt", "quantity": 0.5, "unit": "tsp", "notes": ""},
        {"name": "Black Pepper", "quantity": 0.25, "unit": "tsp", "notes": ""},
        {"name": "Honey", "quantity": 1, "unit": "tbsp", "notes": "Optional for glaze"},
        {"name": "Fresh Thyme", "quantity": 2, "unit": "sprigs", "notes": "Optional"},
    ]

    for ing in ingredients2:
        cursor.execute("SELECT id FROM ingredients WHERE LOWER(name) = LOWER(?)", [ing["name"]])
        result = cursor.fetchone()

        if result:
            ing_id = result[0]
        else:
            print(f"  Creating new ingredient: {ing['name']}")
            category = (
                "vegetable"
                if "carrot" in ing["name"].lower()
                else (
                    "pantry"
                    if any(x in ing["name"].lower() for x in ["oil", "salt", "pepper", "honey"])
                    else "spice"
                )
            )

            aldi_section = "Produce" if category == "vegetable" else "Pantry"

            cursor.execute(
                """
                INSERT INTO ingredients (name, category, aldi_section, default_unit)
                VALUES (?, ?, ?, ?)
            """,
                [ing["name"], category, aldi_section, ing["unit"]],
            )
            ing_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            [recipe2_id, ing_id, ing["quantity"], ing["unit"], ing.get("notes")],
        )

    # Recipe 2 Steps
    steps2 = [
        {
            "step_number": 1,
            "title": "Preheat Oven",
            "instruction": "Preheat oven to 425F (220C). Line a baking sheet with parchment paper.",
            "duration_min": None,
            "tips": "High heat = caramelization",
            "timer_needed": 0,
            "step_type": "prep",
        },
        {
            "step_number": 2,
            "title": "Prep Carrots",
            "instruction": "Peel carrots. Cut into 3-inch long sticks, about 1/2 inch thick. Try to keep sizes uniform.",
            "duration_min": None,
            "tips": "Uniform size = even cooking",
            "timer_needed": 0,
            "step_type": "prep",
        },
        {
            "step_number": 3,
            "title": "Season",
            "instruction": "Toss carrots with olive oil, salt, and pepper on the baking sheet. Spread in single layer.",
            "duration_min": None,
            "tips": "Don't overcrowd - they'll steam instead of roast",
            "timer_needed": 0,
            "step_type": "prep",
        },
        {
            "step_number": 4,
            "title": "Roast",
            "instruction": "Roast for 20-25 minutes, flipping halfway through, until tender and edges are caramelized.",
            "duration_min": 25,
            "tips": "Check at 20 min - you want golden edges, not burnt",
            "timer_needed": 1,
            "step_type": "cook",
        },
        {
            "step_number": 5,
            "title": "Optional Glaze",
            "instruction": "If using honey, drizzle over hot carrots and toss. Add fresh thyme leaves.",
            "duration_min": None,
            "tips": "Honey adds sweet caramelized flavor",
            "timer_needed": 0,
            "step_type": "serve",
        },
        {
            "step_number": 6,
            "title": "Serve",
            "instruction": "Transfer to serving dish. Serve immediately while hot.",
            "duration_min": None,
            "tips": "These reheat well for meal prep",
            "timer_needed": 0,
            "step_type": "serve",
        },
    ]

    for step in steps2:
        cursor.execute(
            """
            INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                recipe2_id,
                step["step_number"],
                step["title"],
                step["instruction"],
                step["duration_min"],
                step["tips"],
                step["timer_needed"],
                step["step_type"],
            ],
        )

    print(f"[OK] Recipe 2 added: ID {recipe2_id}")

    # Recipe 3: Sautéed Broccoli with Garlic
    print("\nAdding Recipe 3: Sautéed Broccoli with Garlic...")
    cursor.execute(
        """
        INSERT INTO recipes (name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            "Sautéed Broccoli with Garlic",
            "Quick sautéed broccoli with garlic and a hint of lemon",
            "side",
            "italian",
            5,
            8,
            4,
            "easy",
        ],
    )
    recipe3_id = cursor.lastrowid

    # Recipe 3 Ingredients
    ingredients3 = [
        {"name": "Broccoli", "quantity": 1, "unit": "lb", "notes": "Cut into florets"},
        {"name": "Garlic", "quantity": 3, "unit": "cloves", "notes": "Thinly sliced"},
        {"name": "Olive Oil", "quantity": 3, "unit": "tbsp", "notes": ""},
        {"name": "Salt", "quantity": 0.5, "unit": "tsp", "notes": ""},
        {
            "name": "Red Pepper Flakes",
            "quantity": 0.25,
            "unit": "tsp",
            "notes": "Optional for heat",
        },
        {"name": "Lemon", "quantity": 0.5, "unit": "whole", "notes": "For juice"},
    ]

    for ing in ingredients3:
        cursor.execute("SELECT id FROM ingredients WHERE LOWER(name) = LOWER(?)", [ing["name"]])
        result = cursor.fetchone()

        if result:
            ing_id = result[0]
        else:
            print(f"  Creating new ingredient: {ing['name']}")
            category = (
                "vegetable"
                if any(x in ing["name"].lower() for x in ["broccoli", "garlic"])
                else (
                    "fruit"
                    if "lemon" in ing["name"].lower()
                    else (
                        "spice"
                        if "pepper" in ing["name"].lower() or "flakes" in ing["name"].lower()
                        else "pantry"
                    )
                )
            )

            aldi_section = "Produce" if category in ["vegetable", "fruit"] else "Pantry"

            cursor.execute(
                """
                INSERT INTO ingredients (name, category, aldi_section, default_unit)
                VALUES (?, ?, ?, ?)
            """,
                [ing["name"], category, aldi_section, ing["unit"]],
            )
            ing_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            [recipe3_id, ing_id, ing["quantity"], ing["unit"], ing.get("notes")],
        )

    # Recipe 3 Steps
    steps3 = [
        {
            "step_number": 1,
            "title": "Prep Broccoli",
            "instruction": "Cut broccoli into bite-sized florets. Slice garlic thinly.",
            "duration_min": None,
            "tips": "Uniform florets cook evenly",
            "timer_needed": 0,
            "step_type": "prep",
        },
        {
            "step_number": 2,
            "title": "Blanch Broccoli",
            "instruction": "Bring a pot of salted water to boil. Blanch broccoli for 2 minutes, then drain well.",
            "duration_min": 2,
            "tips": "Blanching gives vibrant green color and head start on cooking",
            "timer_needed": 1,
            "step_type": "prep",
        },
        {
            "step_number": 3,
            "title": "Heat Oil",
            "instruction": "Heat olive oil in large skillet over medium heat. Add sliced garlic.",
            "duration_min": None,
            "tips": "Watch garlic closely - don't let it burn",
            "timer_needed": 0,
            "step_type": "cook",
        },
        {
            "step_number": 4,
            "title": "Toast Garlic",
            "instruction": "Cook garlic 30-60 seconds, stirring constantly, until fragrant and just golden.",
            "duration_min": 1,
            "tips": "Burnt garlic is bitter - remove from heat at first sign of color",
            "timer_needed": 1,
            "step_type": "cook",
        },
        {
            "step_number": 5,
            "title": "Sauté Broccoli",
            "instruction": "Add blanched broccoli and red pepper flakes. Toss well. Sauté 3-4 min until tender and slightly charred.",
            "duration_min": 4,
            "tips": "High heat creates those nice charred bits",
            "timer_needed": 1,
            "step_type": "cook",
        },
        {
            "step_number": 6,
            "title": "Finish and Serve",
            "instruction": "Season with salt. Squeeze lemon juice over top. Toss and serve immediately.",
            "duration_min": None,
            "tips": "Lemon brightens the flavor - don't skip it!",
            "timer_needed": 0,
            "step_type": "serve",
        },
    ]

    for step in steps3:
        cursor.execute(
            """
            INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                recipe3_id,
                step["step_number"],
                step["title"],
                step["instruction"],
                step["duration_min"],
                step["tips"],
                step["timer_needed"],
                step["step_type"],
            ],
        )

    print(f"[OK] Recipe 3 added: ID {recipe3_id}")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("SUCCESS! All 3 recipes added to database")
    print("=" * 60)
    print(f"Blackened Chicken Breast: Recipe ID {recipe1_id}")
    print(f"Roasted Carrots: Recipe ID {recipe2_id}")
    print(f"Sautéed Broccoli with Garlic: Recipe ID {recipe3_id}")
    print("=" * 60)


if __name__ == "__main__":
    add_tonights_dinner()
