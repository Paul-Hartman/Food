"""Add Super Shake and Chicken Mole meal recipes to the database."""

import os
import sqlite3

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "food.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ============ SUPER SHAKE ============
print("Creating Super Shake recipe...")
cursor.execute(
    """
    INSERT OR REPLACE INTO recipes (id, name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty, image_url)
    VALUES (1001, 'Post-Workout Super Shake', 'High-protein recovery shake with creatine and greens', 'drink', 'american', 5, 0, 1, 'easy', NULL)
"""
)

# Delete existing steps for this recipe
cursor.execute("DELETE FROM cooking_steps WHERE recipe_id = 1001")

super_shake_steps = [
    (
        1,
        "Gather Ingredients",
        "Get out: protein powder, creatine, greens powder, frozen banana, almond milk, peanut butter",
        None,
        None,
        0,
        "prep",
    ),
    (
        2,
        "Add Liquids First",
        "Pour 12oz almond milk (or milk of choice) into blender",
        None,
        "Always add liquids first for better blending",
        0,
        "prep",
    ),
    (
        3,
        "Add Protein & Supplements",
        "Add 1 scoop whey protein, 5g creatine monohydrate, 1 scoop greens powder",
        None,
        "Take creatine daily for best results",
        0,
        "prep",
    ),
    (
        4,
        "Add Frozen Banana",
        "Break frozen banana into chunks and add to blender",
        None,
        "Frozen makes it thick and cold - no ice needed",
        0,
        "prep",
    ),
    (
        5,
        "Add Peanut Butter",
        "Add 2 tbsp peanut butter for healthy fats and flavor",
        None,
        "Can substitute almond butter",
        0,
        "prep",
    ),
    (
        6,
        "Blend Until Smooth",
        "Blend on high for 45-60 seconds until completely smooth",
        1,
        "If too thick, add a splash more liquid",
        1,
        "cook",
    ),
    (
        7,
        "Pour and Enjoy!",
        "Pour into your shaker or tall glass. Drink within 30 min of workout for best recovery.",
        None,
        "~400 calories, 40g protein",
        0,
        "serve",
    ),
]

for step in super_shake_steps:
    cursor.execute(
        """
        INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
        VALUES (1001, ?, ?, ?, ?, ?, ?, ?)
    """,
        step,
    )

print("Super Shake created with 7 steps!")

# ============ CHICKEN MOLE ============
print("\nCreating Chicken Mole recipe...")
cursor.execute(
    """
    INSERT OR REPLACE INTO recipes (id, name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty, image_url)
    VALUES (1002, 'Chicken Mole (Dona Maria)', 'Rich and complex mole sauce over crispy chicken thighs', 'main', 'mexican', 10, 35, 4, 'easy', NULL)
"""
)

cursor.execute("DELETE FROM cooking_steps WHERE recipe_id = 1002")

chicken_mole_steps = [
    (
        1,
        "Prep Ingredients",
        "Take chicken out of fridge 20 min before cooking. Open Dona Maria mole jar. Warm 2 cups chicken broth in microwave.",
        None,
        "Room temp chicken browns better",
        0,
        "prep",
    ),
    (
        2,
        "Season Chicken",
        "Pat chicken thighs dry with paper towels. Season generously with salt on both sides.",
        None,
        "Dry skin = crispy skin",
        0,
        "prep",
    ),
    (
        3,
        "Brown Chicken",
        "Heat 2 tbsp oil in large skillet over medium-high. Add chicken skin-side down. Cook 4-5 min until golden and crispy.",
        5,
        "Don't move the chicken - let it develop a crust",
        1,
        "cook",
    ),
    (
        4,
        "Flip Chicken",
        "Flip chicken thighs. Cook another 4 min on second side. Remove to plate.",
        4,
        "Chicken doesn't need to be cooked through yet",
        1,
        "cook",
    ),
    (
        5,
        "Make Mole Sauce",
        "In same pan (don't clean it!), add half jar of Dona Maria mole paste. Slowly whisk in warm chicken broth until smooth.",
        None,
        "Keep heat at medium to avoid burning",
        0,
        "cook",
    ),
    (
        6,
        "Add Chocolate",
        "Add 1oz semi-sweet chocolate (or 2 tbsp chips). Stir until melted and incorporated.",
        None,
        "The chocolate adds depth and richness",
        0,
        "cook",
    ),
    (
        7,
        "Simmer Chicken",
        "Nestle chicken back into sauce, skin-side up (keep it above sauce for crispiness). Cover and simmer 25-30 min.",
        25,
        "Internal temp should reach 165F",
        1,
        "cook",
    ),
    (
        8,
        "Rest and Serve",
        "Let rest 5 min. Serve garnished with sesame seeds and fresh cilantro over rice and beans.",
        None,
        "The sauce will thicken as it rests",
        0,
        "serve",
    ),
]

for step in chicken_mole_steps:
    cursor.execute(
        """
        INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
        VALUES (1002, ?, ?, ?, ?, ?, ?, ?)
    """,
        step,
    )

print("Chicken Mole created with 8 steps!")

# ============ MEXICAN RICE ============
print("\nCreating Mexican Rice recipe...")
cursor.execute(
    """
    INSERT OR REPLACE INTO recipes (id, name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty, image_url)
    VALUES (1003, 'Mexican Rice', 'Authentic restaurant-style Mexican rice', 'side', 'mexican', 5, 25, 6, 'easy', NULL)
"""
)

cursor.execute("DELETE FROM cooking_steps WHERE recipe_id = 1003")

mexican_rice_steps = [
    (
        1,
        "Toast the Rice",
        "Heat 2 tbsp oil in medium saucepan over medium heat. Add 1.5 cups rice. Stir constantly for 4-5 min until rice turns golden.",
        5,
        "Don't walk away - rice can burn quickly",
        1,
        "cook",
    ),
    (
        2,
        "Add Aromatics",
        "Push rice to sides. Add diced onion (1/4 cup) and 2 minced garlic cloves to center. Cook 1 min until fragrant.",
        1,
        "The toasted rice will smell nutty",
        1,
        "cook",
    ),
    (
        3,
        "Add Liquids",
        "Add 8oz tomato sauce + 2 cups water + 1 tsp chicken bouillon + 1/2 tsp cumin + 1/2 tsp salt. Stir to combine.",
        None,
        "Careful - it will sizzle!",
        0,
        "cook",
    ),
    (4, "Bring to Boil", "Increase heat to high. Bring to a rolling boil.", None, None, 0, "cook"),
    (
        5,
        "Cover and Simmer",
        "Reduce heat to LOW. Cover with tight-fitting lid. Simmer exactly 18 minutes. DO NOT LIFT THE LID!",
        18,
        "Seriously, don't peek - steam escaping = mushy rice",
        1,
        "cook",
    ),
    (
        6,
        "Rest",
        "Remove from heat. Keep covered and let rest 5 minutes.",
        5,
        "This finishes cooking and makes it fluffy",
        1,
        "cook",
    ),
    (
        7,
        "Fluff and Serve",
        "Remove lid. Fluff gently with fork. Taste and adjust salt. Garnish with cilantro if desired.",
        None,
        "Perfect fluffy rice!",
        0,
        "serve",
    ),
]

for step in mexican_rice_steps:
    cursor.execute(
        """
        INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
        VALUES (1003, ?, ?, ?, ?, ?, ?, ?)
    """,
        step,
    )

print("Mexican Rice created with 7 steps!")

# ============ REFRIED BEANS ============
print("\nCreating Refried Beans recipe...")
cursor.execute(
    """
    INSERT OR REPLACE INTO recipes (id, name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty, image_url)
    VALUES (1004, 'Refried Beans', 'Creamy, flavorful refried pinto beans', 'side', 'mexican', 2, 10, 6, 'easy', NULL)
"""
)

cursor.execute("DELETE FROM cooking_steps WHERE recipe_id = 1004")

beans_steps = [
    (
        1,
        "Heat the Fat",
        "Melt 2 tbsp lard (or bacon fat, or vegetable oil) in a large skillet over medium heat.",
        None,
        "Lard gives the most authentic flavor",
        0,
        "cook",
    ),
    (
        2,
        "Add Beans",
        "Drain pinto beans but SAVE 1/4 cup of the liquid. Add beans to skillet.",
        None,
        "The bean liquid adds creaminess",
        0,
        "cook",
    ),
    (
        3,
        "Mash Beans",
        "Using a potato masher or large fork, mash beans to desired consistency. Add reserved bean liquid as needed.",
        None,
        "Leave some chunks for texture or mash completely smooth - your choice!",
        0,
        "cook",
    ),
    (
        4,
        "Season",
        "Add 1/2 tsp cumin, 1/4 tsp garlic powder, salt to taste. Stir well.",
        None,
        None,
        0,
        "cook",
    ),
    (
        5,
        "Simmer",
        "Cook 5-8 min, stirring occasionally, until beans are creamy and slightly thickened.",
        5,
        "Add more bean liquid if too thick",
        1,
        "cook",
    ),
    (
        6,
        "Serve",
        "Transfer to serving bowl. Top with crumbled cotija cheese and a drizzle of cream if desired.",
        None,
        "These will thicken as they cool - add liquid when reheating",
        0,
        "serve",
    ),
]

for step in beans_steps:
    cursor.execute(
        """
        INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
        VALUES (1004, ?, ?, ?, ?, ?, ?, ?)
    """,
        step,
    )

print("Refried Beans created with 6 steps!")

conn.commit()
conn.close()

print("\n" + "=" * 50)
print("All 4 recipes created successfully!")
print("=" * 50)
print("  - Super Shake (ID: 1001) - 7 steps")
print("  - Chicken Mole (ID: 1002) - 8 steps")
print("  - Mexican Rice (ID: 1003) - 7 steps")
print("  - Refried Beans (ID: 1004) - 6 steps")
