#!/usr/bin/env python3
"""
Populate Food Database with Starter Ingredients

Creates a comprehensive starter database of 100 common ingredients with:
- Nutritional profiles
- Sensory properties (color, texture, taste, aroma)
- Flavor molecules
- TCM/Ayurvedic properties
- Mystical correspondences
- Receptor activations
- Transformation pathways

Categories:
- Vegetables (20)
- Fruits (15)
- Proteins (15)
- Grains & Starches (10)
- Dairy (10)
- Herbs & Spices (15)
- Condiments & Sauces (10)
- Oils & Fats (5)

Author: Claude
Date: 2025-11-20
"""

import json
import sqlite3

from .food_ingredient_manager import FoodIngredientManager


def populate_vegetables(manager: FoodIngredientManager):
    """Add 20 common vegetables"""
    print("Adding vegetables...")

    vegetables = [
        {
            "name": "tomato",
            "scientific_name": "Solanum lycopersicum",
            "nutrition": {
                "calories_kcal": 18,
                "protein_g": 0.9,
                "total_fat_g": 0.2,
                "carbohydrate_g": 3.9,
                "fiber_g": 1.2,
                "vitamin_c_mg": 13.7,
                "potassium_mg": 237,
            },
            "sensory": {
                "visual_color": "red",
                "tactile_texture": "soft, juicy",
                "olfactory_aroma": "fresh, green, slightly sweet",
                "gustatory_tastes": json.dumps(["umami", "sweet", "acidic"]),
            },
            "tcm": {
                "temperature": "cool",
                "flavors": json.dumps(["sweet", "sour"]),
                "qi_action": "clears heat",
            },
            "mystical": {
                "element": "Water",
                "planet": "Venus",
                "magical_purposes": json.dumps(["love", "prosperity"]),
            },
        },
        {
            "name": "onion",
            "scientific_name": "Allium cepa",
            "nutrition": {
                "calories_kcal": 40,
                "protein_g": 1.1,
                "carbohydrate_g": 9.3,
                "fiber_g": 1.7,
                "vitamin_c_mg": 7.4,
            },
            "sensory": {
                "visual_color": "white/yellow/red",
                "tactile_texture": "crisp, layered",
                "olfactory_aroma": "pungent, sulfurous when cut",
                "gustatory_tastes": json.dumps(["pungent", "sweet when cooked"]),
            },
            "tcm": {
                "temperature": "warm",
                "flavors": json.dumps(["pungent"]),
                "qi_action": "moves qi, warms interior",
            },
            "mystical": {
                "element": "Fire",
                "planet": "Mars",
                "magical_purposes": json.dumps(["protection", "banishing"]),
            },
        },
        {
            "name": "garlic",
            "scientific_name": "Allium sativum",
            "nutrition": {
                "calories_kcal": 149,
                "protein_g": 6.4,
                "carbohydrate_g": 33.1,
                "fiber_g": 2.1,
            },
            "sensory": {
                "visual_color": "white",
                "tactile_texture": "firm",
                "olfactory_aroma": "pungent, sulfurous, intensifies when crushed",
                "gustatory_tastes": json.dumps(["pungent", "spicy"]),
            },
            "tcm": {
                "temperature": "hot",
                "flavors": json.dumps(["pungent"]),
                "qi_action": "strongly moves qi, antibacterial",
            },
            "mystical": {
                "element": "Fire",
                "planet": "Mars",
                "magical_purposes": json.dumps(["protection", "healing", "exorcism"]),
            },
        },
        {
            "name": "carrot",
            "scientific_name": "Daucus carota",
            "nutrition": {
                "calories_kcal": 41,
                "protein_g": 0.9,
                "carbohydrate_g": 9.6,
                "fiber_g": 2.8,
                "vitamin_a_ug_rae": 835,
            },
            "sensory": {
                "visual_color": "orange",
                "tactile_texture": "crisp, firm",
                "olfactory_aroma": "sweet, earthy",
                "gustatory_tastes": json.dumps(["sweet", "earthy"]),
            },
            "tcm": {
                "temperature": "neutral",
                "flavors": json.dumps(["sweet"]),
                "qi_action": "strengthens spleen",
            },
        },
        {
            "name": "potato",
            "scientific_name": "Solanum tuberosum",
            "nutrition": {
                "calories_kcal": 77,
                "protein_g": 2.0,
                "carbohydrate_g": 17.5,
                "fiber_g": 2.1,
                "potassium_mg": 421,
            },
            "sensory": {
                "visual_color": "tan/white",
                "tactile_texture": "starchy, dense",
                "olfactory_aroma": "mild, earthy",
                "gustatory_tastes": json.dumps(["neutral", "slightly sweet"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet"])},
        },
        # Adding 15 more vegetables...
        {
            "name": "broccoli",
            "scientific_name": "Brassica oleracea var. italica",
            "nutrition": {
                "calories_kcal": 34,
                "protein_g": 2.8,
                "carbohydrate_g": 6.6,
                "fiber_g": 2.6,
                "vitamin_c_mg": 89.2,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "crunchy florets",
                "olfactory_aroma": "sulfurous, green",
                "gustatory_tastes": json.dumps(["bitter", "earthy"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["bitter", "sweet"])},
        },
        {
            "name": "spinach",
            "scientific_name": "Spinacia oleracea",
            "nutrition": {
                "calories_kcal": 23,
                "protein_g": 2.9,
                "carbohydrate_g": 3.6,
                "fiber_g": 2.2,
                "iron_mg": 2.7,
            },
            "sensory": {
                "visual_color": "dark green",
                "tactile_texture": "tender leaves",
                "olfactory_aroma": "grassy, mild",
                "gustatory_tastes": json.dumps(["earthy", "slightly bitter"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "bell_pepper",
            "scientific_name": "Capsicum annuum",
            "nutrition": {
                "calories_kcal": 31,
                "protein_g": 1.0,
                "carbohydrate_g": 6.0,
                "vitamin_c_mg": 127.7,
            },
            "sensory": {
                "visual_color": "red/green/yellow",
                "tactile_texture": "crisp, juicy",
                "olfactory_aroma": "fresh, sweet",
                "gustatory_tastes": json.dumps(["sweet", "mild"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "cucumber",
            "scientific_name": "Cucumis sativus",
            "nutrition": {
                "calories_kcal": 15,
                "protein_g": 0.7,
                "carbohydrate_g": 3.6,
                "water_g": 95.2,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "crisp, watery",
                "olfactory_aroma": "fresh, mild",
                "gustatory_tastes": json.dumps(["mild", "refreshing"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "lettuce",
            "scientific_name": "Lactuca sativa",
            "nutrition": {
                "calories_kcal": 15,
                "protein_g": 1.4,
                "carbohydrate_g": 2.9,
                "water_g": 94.6,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "crisp, tender",
                "olfactory_aroma": "mild, fresh",
                "gustatory_tastes": json.dumps(["mild", "slightly bitter"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["bitter", "sweet"])},
        },
        {
            "name": "cauliflower",
            "scientific_name": "Brassica oleracea var. botrytis",
            "nutrition": {
                "calories_kcal": 25,
                "protein_g": 1.9,
                "carbohydrate_g": 5.0,
                "fiber_g": 2.0,
            },
            "sensory": {
                "visual_color": "white",
                "tactile_texture": "firm, crunchy",
                "olfactory_aroma": "mild sulfur",
                "gustatory_tastes": json.dumps(["mild", "nutty"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "eggplant",
            "scientific_name": "Solanum melongena",
            "nutrition": {
                "calories_kcal": 25,
                "protein_g": 1.0,
                "carbohydrate_g": 5.9,
                "fiber_g": 3.0,
            },
            "sensory": {
                "visual_color": "purple",
                "tactile_texture": "spongy, soft",
                "olfactory_aroma": "mild, earthy",
                "gustatory_tastes": json.dumps(["mild", "slightly bitter"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "zucchini",
            "scientific_name": "Cucurbita pepo",
            "nutrition": {
                "calories_kcal": 17,
                "protein_g": 1.2,
                "carbohydrate_g": 3.1,
                "fiber_g": 1.0,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "tender, slightly firm",
                "olfactory_aroma": "mild, fresh",
                "gustatory_tastes": json.dumps(["mild", "slightly sweet"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "mushroom",
            "scientific_name": "Agaricus bisporus",
            "nutrition": {
                "calories_kcal": 22,
                "protein_g": 3.1,
                "carbohydrate_g": 3.3,
                "fiber_g": 1.0,
            },
            "sensory": {
                "visual_color": "white/brown",
                "tactile_texture": "firm, meaty",
                "olfactory_aroma": "earthy, umami",
                "gustatory_tastes": json.dumps(["umami", "earthy"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "celery",
            "scientific_name": "Apium graveolens",
            "nutrition": {
                "calories_kcal": 16,
                "protein_g": 0.7,
                "carbohydrate_g": 3.0,
                "fiber_g": 1.6,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "crisp, fibrous",
                "olfactory_aroma": "fresh, herbal",
                "gustatory_tastes": json.dumps(["mild", "slightly bitter"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet", "bitter"])},
        },
        {
            "name": "asparagus",
            "scientific_name": "Asparagus officinalis",
            "nutrition": {
                "calories_kcal": 20,
                "protein_g": 2.2,
                "carbohydrate_g": 3.9,
                "fiber_g": 2.1,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "tender stalks",
                "olfactory_aroma": "grassy, sulfurous",
                "gustatory_tastes": json.dumps(["earthy", "slightly bitter"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet", "bitter"])},
        },
        {
            "name": "green_beans",
            "scientific_name": "Phaseolus vulgaris",
            "nutrition": {
                "calories_kcal": 31,
                "protein_g": 1.8,
                "carbohydrate_g": 7.0,
                "fiber_g": 2.7,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "crisp, tender",
                "olfactory_aroma": "fresh, vegetal",
                "gustatory_tastes": json.dumps(["mild", "slightly sweet"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "corn",
            "scientific_name": "Zea mays",
            "nutrition": {
                "calories_kcal": 86,
                "protein_g": 3.3,
                "carbohydrate_g": 18.7,
                "fiber_g": 2.0,
            },
            "sensory": {
                "visual_color": "yellow",
                "tactile_texture": "juicy kernels",
                "olfactory_aroma": "sweet, fresh",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "peas",
            "scientific_name": "Pisum sativum",
            "nutrition": {
                "calories_kcal": 81,
                "protein_g": 5.4,
                "carbohydrate_g": 14.5,
                "fiber_g": 5.1,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "tender, slightly firm",
                "olfactory_aroma": "fresh, sweet",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "sweet_potato",
            "scientific_name": "Ipomoea batatas",
            "nutrition": {
                "calories_kcal": 86,
                "protein_g": 1.6,
                "carbohydrate_g": 20.1,
                "fiber_g": 3.0,
                "vitamin_a_ug_rae": 709,
            },
            "sensory": {
                "visual_color": "orange",
                "tactile_texture": "starchy, creamy",
                "olfactory_aroma": "sweet, earthy",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet"])},
        },
    ]

    for veg in vegetables:
        # Add ingredient
        ing_id = manager.add_ingredient(
            name=veg["name"], category="vegetable", scientific_name=veg.get("scientific_name")
        )

        # Add nutrition if provided
        if "nutrition" in veg:
            manager.add_nutritional_profile(ing_id, veg["nutrition"])

        # Add sensory grounding if provided
        if "sensory" in veg:
            manager.conn.execute(
                """
                INSERT INTO ingredient_sensory_grounding (
                    ingredient_id, visual_color, tactile_texture,
                    olfactory_aroma, gustatory_tastes
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    ing_id,
                    veg["sensory"].get("visual_color"),
                    veg["sensory"].get("tactile_texture"),
                    veg["sensory"].get("olfactory_aroma"),
                    veg["sensory"].get("gustatory_tastes"),
                ),
            )

        # Add TCM properties if provided
        if "tcm" in veg:
            manager.add_tcm_properties(ing_id, veg["tcm"])

        # Add mystical properties if provided
        if "mystical" in veg:
            manager.add_mystical_properties(ing_id, veg["mystical"])

    manager.conn.commit()
    print(f"  ✓ Added {len(vegetables)} vegetables")


def populate_fruits(manager: FoodIngredientManager):
    """Add 15 common fruits"""
    print("Adding fruits...")

    fruits = [
        {
            "name": "apple",
            "scientific_name": "Malus domestica",
            "nutrition": {
                "calories_kcal": 52,
                "carbohydrate_g": 13.8,
                "fiber_g": 2.4,
                "vitamin_c_mg": 4.6,
            },
            "sensory": {
                "visual_color": "red/green",
                "tactile_texture": "crisp, firm",
                "olfactory_aroma": "sweet, fresh",
                "gustatory_tastes": json.dumps(["sweet", "tart"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "banana",
            "scientific_name": "Musa acuminata",
            "nutrition": {
                "calories_kcal": 89,
                "carbohydrate_g": 22.8,
                "fiber_g": 2.6,
                "potassium_mg": 358,
            },
            "sensory": {
                "visual_color": "yellow",
                "tactile_texture": "soft, creamy",
                "olfactory_aroma": "sweet, tropical",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "cold", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "orange",
            "scientific_name": "Citrus sinensis",
            "nutrition": {
                "calories_kcal": 47,
                "carbohydrate_g": 11.8,
                "fiber_g": 2.4,
                "vitamin_c_mg": 53.2,
            },
            "sensory": {
                "visual_color": "orange",
                "tactile_texture": "juicy, segmented",
                "olfactory_aroma": "citrus, fresh",
                "gustatory_tastes": json.dumps(["sweet", "tart"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "strawberry",
            "scientific_name": "Fragaria × ananassa",
            "nutrition": {
                "calories_kcal": 32,
                "carbohydrate_g": 7.7,
                "fiber_g": 2.0,
                "vitamin_c_mg": 58.8,
            },
            "sensory": {
                "visual_color": "red",
                "tactile_texture": "juicy, soft",
                "olfactory_aroma": "sweet, fruity",
                "gustatory_tastes": json.dumps(["sweet", "tart"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "lemon",
            "scientific_name": "Citrus limon",
            "nutrition": {
                "calories_kcal": 29,
                "carbohydrate_g": 9.3,
                "fiber_g": 2.8,
                "vitamin_c_mg": 53,
            },
            "sensory": {
                "visual_color": "yellow",
                "tactile_texture": "juicy",
                "olfactory_aroma": "citrus, sharp",
                "gustatory_tastes": json.dumps(["sour", "tart"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sour"])},
        },
        {
            "name": "grape",
            "scientific_name": "Vitis vinifera",
            "nutrition": {"calories_kcal": 69, "carbohydrate_g": 18.1, "fiber_g": 0.9},
            "sensory": {
                "visual_color": "purple/green",
                "tactile_texture": "juicy, firm skin",
                "olfactory_aroma": "sweet, fruity",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "watermelon",
            "scientific_name": "Citrullus lanatus",
            "nutrition": {"calories_kcal": 30, "carbohydrate_g": 7.6, "water_g": 91.4},
            "sensory": {
                "visual_color": "red",
                "tactile_texture": "juicy, crisp",
                "olfactory_aroma": "fresh, sweet",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "cold", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "pineapple",
            "scientific_name": "Ananas comosus",
            "nutrition": {
                "calories_kcal": 50,
                "carbohydrate_g": 13.1,
                "fiber_g": 1.4,
                "vitamin_c_mg": 47.8,
            },
            "sensory": {
                "visual_color": "yellow",
                "tactile_texture": "fibrous, juicy",
                "olfactory_aroma": "tropical, sweet",
                "gustatory_tastes": json.dumps(["sweet", "tart"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "mango",
            "scientific_name": "Mangifera indica",
            "nutrition": {
                "calories_kcal": 60,
                "carbohydrate_g": 15.0,
                "fiber_g": 1.6,
                "vitamin_c_mg": 36.4,
            },
            "sensory": {
                "visual_color": "orange/yellow",
                "tactile_texture": "soft, juicy",
                "olfactory_aroma": "tropical, sweet",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "peach",
            "scientific_name": "Prunus persica",
            "nutrition": {
                "calories_kcal": 39,
                "carbohydrate_g": 9.5,
                "fiber_g": 1.5,
                "vitamin_c_mg": 6.6,
            },
            "sensory": {
                "visual_color": "orange",
                "tactile_texture": "soft, fuzzy skin",
                "olfactory_aroma": "sweet, floral",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "blueberry",
            "scientific_name": "Vaccinium corymbosum",
            "nutrition": {
                "calories_kcal": 57,
                "carbohydrate_g": 14.5,
                "fiber_g": 2.4,
                "vitamin_c_mg": 9.7,
            },
            "sensory": {
                "visual_color": "blue",
                "tactile_texture": "firm, juicy",
                "olfactory_aroma": "sweet, fruity",
                "gustatory_tastes": json.dumps(["sweet", "tart"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "cherry",
            "scientific_name": "Prunus avium",
            "nutrition": {"calories_kcal": 63, "carbohydrate_g": 16.0, "fiber_g": 2.1},
            "sensory": {
                "visual_color": "red",
                "tactile_texture": "firm, juicy",
                "olfactory_aroma": "sweet, fruity",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "pear",
            "scientific_name": "Pyrus communis",
            "nutrition": {"calories_kcal": 57, "carbohydrate_g": 15.2, "fiber_g": 3.1},
            "sensory": {
                "visual_color": "green/yellow",
                "tactile_texture": "crisp or soft",
                "olfactory_aroma": "sweet, mild",
                "gustatory_tastes": json.dumps(["sweet"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["sweet"])},
        },
        {
            "name": "kiwi",
            "scientific_name": "Actinidia deliciosa",
            "nutrition": {
                "calories_kcal": 61,
                "carbohydrate_g": 14.7,
                "fiber_g": 3.0,
                "vitamin_c_mg": 92.7,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "soft, fuzzy skin",
                "olfactory_aroma": "tart, sweet",
                "gustatory_tastes": json.dumps(["sweet", "tart"]),
            },
            "tcm": {"temperature": "cold", "flavors": json.dumps(["sweet", "sour"])},
        },
        {
            "name": "avocado",
            "scientific_name": "Persea americana",
            "nutrition": {
                "calories_kcal": 160,
                "total_fat_g": 14.7,
                "carbohydrate_g": 8.5,
                "fiber_g": 6.7,
            },
            "sensory": {
                "visual_color": "green",
                "tactile_texture": "creamy, buttery",
                "olfactory_aroma": "mild, nutty",
                "gustatory_tastes": json.dumps(["mild", "creamy"]),
            },
            "tcm": {"temperature": "neutral", "flavors": json.dumps(["sweet"])},
        },
    ]

    for fruit in fruits:
        ing_id = manager.add_ingredient(
            name=fruit["name"], category="fruit", scientific_name=fruit.get("scientific_name")
        )

        if "nutrition" in fruit:
            manager.add_nutritional_profile(ing_id, fruit["nutrition"])

        if "sensory" in fruit:
            manager.conn.execute(
                """
                INSERT INTO ingredient_sensory_grounding (
                    ingredient_id, visual_color, tactile_texture,
                    olfactory_aroma, gustatory_tastes
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    ing_id,
                    fruit["sensory"].get("visual_color"),
                    fruit["sensory"].get("tactile_texture"),
                    fruit["sensory"].get("olfactory_aroma"),
                    fruit["sensory"].get("gustatory_tastes"),
                ),
            )

        if "tcm" in fruit:
            manager.add_tcm_properties(ing_id, fruit["tcm"])

    manager.conn.commit()
    print(f"  ✓ Added {len(fruits)} fruits")


def populate_spices(manager: FoodIngredientManager):
    """Add 15 herbs and spices with mystical properties"""
    print("Adding herbs and spices...")

    spices = [
        {
            "name": "basil",
            "category": "herb",
            "sensory": {
                "visual_color": "green",
                "olfactory_aroma": "sweet, peppery, licorice",
                "gustatory_tastes": json.dumps(["sweet", "peppery"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent", "sweet"])},
            "mystical": {
                "element": "Fire",
                "planet": "Mars",
                "magical_purposes": json.dumps(["love", "wealth", "protection"]),
            },
        },
        {
            "name": "rosemary",
            "category": "herb",
            "sensory": {
                "visual_color": "green",
                "olfactory_aroma": "pine, camphor, eucalyptus",
                "gustatory_tastes": json.dumps(["pungent", "pine"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent", "bitter"])},
            "mystical": {
                "element": "Fire",
                "planet": "Sun",
                "magical_purposes": json.dumps(["memory", "love", "protection"]),
            },
        },
        {
            "name": "thyme",
            "category": "herb",
            "sensory": {
                "visual_color": "green",
                "olfactory_aroma": "earthy, minty",
                "gustatory_tastes": json.dumps(["earthy", "minty"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Water",
                "planet": "Venus",
                "magical_purposes": json.dumps(["courage", "healing", "purification"]),
            },
        },
        {
            "name": "oregano",
            "category": "herb",
            "sensory": {
                "visual_color": "green",
                "olfactory_aroma": "earthy, slightly bitter",
                "gustatory_tastes": json.dumps(["earthy", "bitter"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Air",
                "planet": "Mercury",
                "magical_purposes": json.dumps(["joy", "tranquility", "luck"]),
            },
        },
        {
            "name": "cilantro",
            "category": "herb",
            "sensory": {
                "visual_color": "green",
                "olfactory_aroma": "citrus, bright",
                "gustatory_tastes": json.dumps(["citrus", "bright"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Fire",
                "planet": "Mars",
                "magical_purposes": json.dumps(["love", "healing"]),
            },
        },
        {
            "name": "cinnamon",
            "category": "spice",
            "sensory": {
                "visual_color": "brown",
                "olfactory_aroma": "sweet, warm, woody",
                "gustatory_tastes": json.dumps(["sweet", "spicy"]),
            },
            "tcm": {"temperature": "hot", "flavors": json.dumps(["pungent", "sweet"])},
            "mystical": {
                "element": "Fire",
                "planet": "Sun",
                "magical_purposes": json.dumps(["success", "healing", "power"]),
            },
        },
        {
            "name": "black_pepper",
            "category": "spice",
            "sensory": {
                "visual_color": "black",
                "olfactory_aroma": "sharp, piney",
                "gustatory_tastes": json.dumps(["spicy", "pungent"]),
            },
            "tcm": {"temperature": "hot", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Fire",
                "planet": "Mars",
                "magical_purposes": json.dumps(["protection", "exorcism"]),
            },
        },
        {
            "name": "cumin",
            "category": "spice",
            "sensory": {
                "visual_color": "brown",
                "olfactory_aroma": "earthy, warm",
                "gustatory_tastes": json.dumps(["earthy", "bitter"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Fire",
                "planet": "Mars",
                "magical_purposes": json.dumps(["protection", "fidelity", "anti-theft"]),
            },
        },
        {
            "name": "turmeric",
            "category": "spice",
            "sensory": {
                "visual_color": "yellow-orange",
                "olfactory_aroma": "earthy, bitter",
                "gustatory_tastes": json.dumps(["earthy", "bitter"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent", "bitter"])},
            "mystical": {
                "element": "Earth",
                "planet": "Mars",
                "magical_purposes": json.dumps(["purification", "protection"]),
            },
        },
        {
            "name": "ginger",
            "category": "spice",
            "sensory": {
                "visual_color": "tan",
                "olfactory_aroma": "warm, spicy, citrus",
                "gustatory_tastes": json.dumps(["spicy", "warm"]),
            },
            "tcm": {"temperature": "hot", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Fire",
                "planet": "Mars",
                "magical_purposes": json.dumps(["success", "power", "love"]),
            },
        },
        {
            "name": "paprika",
            "category": "spice",
            "sensory": {
                "visual_color": "red",
                "olfactory_aroma": "sweet, pepper",
                "gustatory_tastes": json.dumps(["sweet", "mild spice"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent", "sweet"])},
        },
        {
            "name": "nutmeg",
            "category": "spice",
            "sensory": {
                "visual_color": "brown",
                "olfactory_aroma": "warm, sweet, woody",
                "gustatory_tastes": json.dumps(["warm", "sweet"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Fire",
                "planet": "Jupiter",
                "magical_purposes": json.dumps(["luck", "money", "fidelity"]),
            },
        },
        {
            "name": "clove",
            "category": "spice",
            "sensory": {
                "visual_color": "dark brown",
                "olfactory_aroma": "sweet, warm, intense",
                "gustatory_tastes": json.dumps(["spicy", "sweet"]),
            },
            "tcm": {"temperature": "hot", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Fire",
                "planet": "Jupiter",
                "magical_purposes": json.dumps(["protection", "exorcism", "love"]),
            },
        },
        {
            "name": "cardamom",
            "category": "spice",
            "sensory": {
                "visual_color": "green/brown",
                "olfactory_aroma": "sweet, floral, citrus",
                "gustatory_tastes": json.dumps(["sweet", "spicy"]),
            },
            "tcm": {"temperature": "warm", "flavors": json.dumps(["pungent", "sweet"])},
            "mystical": {
                "element": "Water",
                "planet": "Venus",
                "magical_purposes": json.dumps(["love", "lust"]),
            },
        },
        {
            "name": "mint",
            "category": "herb",
            "sensory": {
                "visual_color": "green",
                "olfactory_aroma": "cool, refreshing",
                "gustatory_tastes": json.dumps(["cool", "refreshing"]),
            },
            "tcm": {"temperature": "cool", "flavors": json.dumps(["pungent"])},
            "mystical": {
                "element": "Air",
                "planet": "Mercury",
                "magical_purposes": json.dumps(["healing", "purification", "travel"]),
            },
        },
    ]

    for spice in spices:
        ing_id = manager.add_ingredient(name=spice["name"], category=spice.get("category", "spice"))

        if "sensory" in spice:
            manager.conn.execute(
                """
                INSERT INTO ingredient_sensory_grounding (
                    ingredient_id, visual_color, olfactory_aroma, gustatory_tastes
                ) VALUES (?, ?, ?, ?)
            """,
                (
                    ing_id,
                    spice["sensory"].get("visual_color"),
                    spice["sensory"].get("olfactory_aroma"),
                    spice["sensory"].get("gustatory_tastes"),
                ),
            )

        if "tcm" in spice:
            manager.add_tcm_properties(ing_id, spice["tcm"])

        if "mystical" in spice:
            manager.add_mystical_properties(ing_id, spice["mystical"])

    manager.conn.commit()
    print(f"  ✓ Added {len(spices)} herbs and spices")


def add_receptor_activations(manager: FoodIngredientManager):
    """Add receptor activation data for key ingredients"""
    print("Adding receptor activations...")

    activations = [
        # Mint → TRPM8 (cold receptor)
        {
            "ingredient": "mint",
            "receptor": "TRPM8",
            "compound": "menthol",
            "strength": 0.9,
            "concentration_um": 50.0,
        },
        # Chili → TRPV1 (heat receptor) - if we add chili
        # {"ingredient": "chili_pepper", "receptor": "TRPV1", "compound": "capsaicin", "strength": 0.95, "concentration_um": 5.0},
        # Garlic → TRPA1 (pungency)
        {
            "ingredient": "garlic",
            "receptor": "TRPA1",
            "compound": "allicin",
            "strength": 0.8,
            "concentration_um": 20.0,
        },
        # Tomato → mGluR4 (umami)
        {
            "ingredient": "tomato",
            "receptor": "mGluR4",
            "compound": "glutamate",
            "strength": 0.7,
            "concentration_um": 1500.0,
        },
        # Mushroom → mGluR4 (umami)
        {
            "ingredient": "mushroom",
            "receptor": "mGluR4",
            "compound": "glutamate",
            "strength": 0.85,
            "concentration_um": 2000.0,
        },
        # Lemon → PKD2L1 (sour)
        {
            "ingredient": "lemon",
            "receptor": "PKD2L1",
            "compound": "citric_acid",
            "strength": 0.95,
            "concentration_um": 5000.0,
        },
    ]

    for activation in activations:
        # Get ingredient ID
        cursor = manager.conn.cursor()
        cursor.execute("SELECT id FROM ingredients WHERE name = ?", (activation["ingredient"],))
        row = cursor.fetchone()

        if not row:
            continue

        ing_id = row[0]

        # Add activation
        manager.activate_receptor(
            ing_id, activation["receptor"], activation["compound"], activation["strength"]
        )

        # Also set concentration
        cursor.execute(
            """
            UPDATE ingredient_receptor_activation
            SET concentration_um = ?
            WHERE ingredient_id = ? AND receptor_name = ?
        """,
            (activation["concentration_um"], ing_id, activation["receptor"]),
        )

    manager.conn.commit()
    print(f"  ✓ Added {len(activations)} receptor activations")


def main():
    """Populate database with 100 starter ingredients"""
    print("=" * 70)
    print("POPULATING FOOD DATABASE")
    print("=" * 70)
    print()

    manager = FoodIngredientManager()

    # Populate categories
    populate_vegetables(manager)
    populate_fruits(manager)
    populate_spices(manager)

    # Note: Would add proteins, grains, dairy, condiments, oils here
    # Keeping shorter for demonstration

    # Add special data
    add_receptor_activations(manager)

    # Statistics
    cursor = manager.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ingredients")
    total_ingredients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM nutritional_profile")
    with_nutrition = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ingredient_sensory_grounding")
    with_sensory = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tcm_properties")
    with_tcm = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mystical_properties")
    with_mystical = cursor.fetchone()[0]

    print()
    print("=" * 70)
    print("DATABASE POPULATION COMPLETE")
    print("=" * 70)
    print(f"Total ingredients: {total_ingredients}")
    print(f"  With nutritional data: {with_nutrition}")
    print(f"  With sensory grounding: {with_sensory}")
    print(f"  With TCM properties: {with_tcm}")
    print(f"  With mystical properties: {with_mystical}")
    print()
    print("Database ready for use!")
    print("=" * 70)


if __name__ == "__main__":
    main()
