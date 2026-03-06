"""
Expanded Transformation Recipes - Complete Crafting System

This creates the full transformation graph where every ingredient shows
"what can I make with this?" - a discovery tool for home food production.

Transformations include:
- Milk → Yogurt, Kefir, Butter, Cheese, Cream, etc.
- Wheat → Flour → Bread, Pasta, Crackers, etc.
- Cream → Butter, Whipped Cream, Ice Cream
- And many more...

Usage:
    python seed_transformations_expanded.py
"""

import sqlite3
import json

DB_PATH = "food.db"


def get_ingredient_id(conn, name_pattern):
    """Get ingredient ID by name pattern (case-insensitive search)."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM ingredients WHERE LOWER(name) LIKE ? LIMIT 1", (f"%{name_pattern.lower()}%",))
    result = cursor.fetchone()
    return result[0] if result else None


def get_preparation_id(conn, name):
    """Get preparation ID by exact name."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM ingredient_preparations WHERE preparation_name = ?", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_process_id(conn, name):
    """Get process ID by exact name."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transformation_processes WHERE process_name = ?", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_equipment_id(conn, category):
    """Get first kitchen_tools ID matching category."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM kitchen_tools WHERE LOWER(name) LIKE ? LIMIT 1", (f"%{category.lower()}%",))
    result = cursor.fetchone()
    return result[0] if result else None


def seed_milk_transformations(conn):
    """Seed complete milk transformation tree."""
    print("Seeding milk transformations...")

    cursor = conn.cursor()

    # Get IDs
    milk_id = get_ingredient_id(conn, "milk")
    if not milk_id:
        print("  [SKIP] Milk ingredient not found")
        return

    # Get existing preparation IDs
    yogurt_id = get_preparation_id(conn, "Yogurt (plain)")
    greek_yogurt_id = get_preparation_id(conn, "Greek Yogurt")
    skyr_id = get_preparation_id(conn, "Skyr")
    kefir_id = get_preparation_id(conn, "Kefir")

    # Get process IDs
    lacto_ferment_id = get_process_id(conn, "Lactic Acid Fermentation")
    skyr_ferment_id = get_process_id(conn, "Skyr Fermentation (Icelandic)")

    # Get equipment IDs
    instant_pot_id = get_equipment_id(conn, "instant pot")

    transformations = [
        # Milk → Yogurt
        (
            "Instant Pot Yogurt",
            milk_id,
            yogurt_id,
            lacto_ferment_id,
            instant_pot_id,
            100,  # yield %
            json.dumps({
                "steps": [
                    "Pour 1 gallon milk into Instant Pot",
                    "Press Yogurt button, adjust to 'boil' (optional: creates thicker yogurt)",
                    "Heat milk to 180°F (optional step)",
                    "Cool milk to 110°F",
                    "Add 2-3 tbsp yogurt starter with live cultures",
                    "Press Yogurt button, set to 8-10 hours",
                    "Refrigerate 4+ hours to set"
                ],
                "additional_ingredients": ["2-3 tbsp yogurt starter with live cultures"],
                "equipment_needed": ["Instant Pot with Yogurt function", "Thermometer"],
                "time_active": "15 minutes",
                "time_passive": "8-10 hours",
                "difficulty": "Easy",
                "chemistry": "Lactobacillus converts lactose to lactic acid, lowering pH from 6.5 to 4.5, which denatures casein proteins creating thick texture"
            }),
            "Thickness, tanginess (taste after 8hrs, 10hrs, 12hrs)"
        ),

        # Yogurt → Greek Yogurt (chaining!)
        (
            "Greek Yogurt (Strained)",
            yogurt_id if yogurt_id else milk_id,  # Can start from yogurt OR milk
            greek_yogurt_id,
            None,  # No fermentation, just straining
            None,
            50,  # yield % (half the volume after straining)
            json.dumps({
                "steps": [
                    "Line colander with cheesecloth or use Greek yogurt strainer",
                    "Pour yogurt into strainer",
                    "Place over bowl to catch whey",
                    "Refrigerate 4-6 hours (longer = thicker)",
                    "Discard whey OR save for baking/smoothies",
                    "Store strained yogurt in container"
                ],
                "additional_ingredients": [],
                "equipment_needed": ["Cheesecloth or Greek yogurt strainer", "Colander", "Bowl"],
                "time_active": "5 minutes",
                "time_passive": "4-6 hours",
                "difficulty": "Very Easy",
                "chemistry": "Removing whey (liquid) concentrates protein and creates thicker texture. Whey contains lactose, minerals, vitamins."
            }),
            "Thickness (strain 2hrs = medium, 6hrs = ultra-thick)"
        ),

        # Milk → Kefir
        (
            "Kefir (Probiotic Drink)",
            milk_id,
            kefir_id,
            lacto_ferment_id,  # Similar process but different microbes
            None,
            100,
            json.dumps({
                "steps": [
                    "Add 1-2 tbsp kefir grains to glass jar",
                    "Pour 2 cups milk over grains",
                    "Cover with cloth/coffee filter (breathable)",
                    "Leave at room temp 24 hours",
                    "Strain out kefir grains (reuse for next batch)",
                    "Refrigerate kefir, drink within 1 week"
                ],
                "additional_ingredients": ["1-2 tbsp kefir grains (reusable culture)"],
                "equipment_needed": ["Glass jar", "Cloth cover", "Strainer"],
                "time_active": "5 minutes",
                "time_passive": "24 hours",
                "difficulty": "Very Easy",
                "chemistry": "Kefir grains contain 30+ species of bacteria and yeast. Produces lactic acid, CO2, trace alcohol. More probiotic diversity than yogurt."
            }),
            "Tanginess, thickness, slight fizz"
        ),

        # Milk → Skyr
        (
            "Skyr (Icelandic Yogurt)",
            milk_id,
            skyr_id,
            skyr_ferment_id,
            instant_pot_id,
            50,  # Very thick, half the volume
            json.dumps({
                "steps": [
                    "Heat 1 gallon skim milk to 195°F (higher than yogurt)",
                    "Cool to 100°F",
                    "Add 3 tbsp skyr starter OR Icelandic yogurt",
                    "Add 2-3 drops liquid rennet (diluted in 1 tbsp water)",
                    "Instant Pot Yogurt mode, 12-24 hours",
                    "Strain through cheesecloth 4-6 hours until ultra-thick",
                    "Refrigerate"
                ],
                "additional_ingredients": ["Skyr starter culture", "Rennet (2-3 drops)", "Skim milk (traditional)"],
                "equipment_needed": ["Instant Pot", "Thermometer", "Cheesecloth", "Strainer"],
                "time_active": "20 minutes",
                "time_passive": "12-24 hours + 4-6 hours straining",
                "difficulty": "Moderate",
                "chemistry": "Rennet (enzyme chymosin) cleaves κ-casein, destabilizing micelles. Combined with acid coagulation creates ultra-thick texture. Straining removes whey."
            }),
            "Thickness, protein content (should be 2x protein of yogurt)"
        ),
    ]

    for t in transformations:
        cursor.execute("""
            INSERT OR IGNORE INTO transformation_recipes
            (recipe_name, base_ingredient_id, output_preparation_id, process_id,
             equipment_id, yield_percent, instructions_json, quality_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, t)

    conn.commit()
    print(f"  [OK] Inserted {len(transformations)} milk transformations")


def seed_additional_dairy_transformations(conn):
    """Seed butter, cream, cheese transformations."""
    print("Seeding additional dairy transformations...")

    cursor = conn.cursor()
    milk_id = get_ingredient_id(conn, "milk")

    if not milk_id:
        print("  [SKIP] Milk not found")
        return

    # Create new preparation entries for products we don't have yet
    new_preparations = [
        (milk_id, "Heavy Cream", None, None, 340, 2.1, 2.8, 36.0, 0),
        (milk_id, "Butter (unsalted)", None, None, 717, 0.9, 0.1, 81.1, 0),
        (milk_id, "Buttermilk", None, None, 40, 3.3, 4.8, 0.9, 0),
        (milk_id, "Whole Milk Mozzarella", None, None, 280, 28.0, 3.1, 17.0, 0),
        (milk_id, "Ricotta Cheese", None, None, 174, 11.0, 3.0, 13.0, 0),
        (milk_id, "Paneer (Indian Cheese)", None, None, 265, 18.0, 1.2, 20.8, 0),
        (milk_id, "Whipped Cream", None, None, 257, 2.2, 3.3, 28.0, 0),
    ]

    for prep in new_preparations:
        cursor.execute("""
            INSERT OR IGNORE INTO ingredient_preparations
            (base_ingredient_id, preparation_name, parent_preparation_id, hydration_percent,
             calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, prep)

    conn.commit()

    # Get new IDs
    cream_id = get_preparation_id(conn, "Heavy Cream")
    butter_id = get_preparation_id(conn, "Butter (unsalted)")
    buttermilk_id = get_preparation_id(conn, "Buttermilk")
    mozzarella_id = get_preparation_id(conn, "Whole Milk Mozzarella")
    ricotta_id = get_preparation_id(conn, "Ricotta Cheese")
    paneer_id = get_preparation_id(conn, "Paneer (Indian Cheese)")
    whipped_cream_id = get_preparation_id(conn, "Whipped Cream")

    transformations = [
        # Milk → Cream (separation)
        (
            "Cream Separation",
            milk_id,
            cream_id,
            None,
            None,
            10,  # Small yield
            json.dumps({
                "steps": [
                    "Let whole milk sit 24 hours in fridge",
                    "Cream rises to top (if unhomogenized milk)",
                    "Skim cream layer off with spoon",
                    "OR use cream separator (mechanical)"
                ],
                "additional_ingredients": ["Whole milk (unhomogenized preferred)"],
                "equipment_needed": ["Glass jar OR cream separator"],
                "note": "Most store milk is homogenized (cream won't separate). Buy unhomogenized from local dairy.",
                "difficulty": "Easy (if you have right milk)",
                "chemistry": "Fat globules less dense than water, rise via gravity. Homogenization breaks globules preventing separation."
            }),
            "Fat content (should be 36%+)"
        ),

        # Cream → Butter
        (
            "Churning Butter",
            cream_id,
            butter_id,
            None,
            None,
            40,  # Cream is ~40% butter by weight
            json.dumps({
                "steps": [
                    "Pour heavy cream into jar or stand mixer",
                    "Shake/mix vigorously for 10-15 minutes",
                    "Cream will turn to whipped cream, then suddenly separate",
                    "Butter solids will clump, buttermilk will separate",
                    "Drain buttermilk (save for baking)",
                    "Rinse butter under cold water, kneading to remove excess buttermilk",
                    "Add salt if desired (optional)",
                    "Shape into block, refrigerate"
                ],
                "additional_ingredients": ["Heavy cream", "Salt (optional)"],
                "equipment_needed": ["Stand mixer OR jar with lid OR butter churn"],
                "time_active": "15 minutes",
                "difficulty": "Easy",
                "chemistry": "Agitation ruptures fat globule membranes, fat coalesces. Buttermilk (aqueous phase) separates from fat (butter)."
            }),
            "Color (yellow = grass-fed cows), taste, texture"
        ),

        # Milk → Paneer (easiest cheese!)
        (
            "Paneer (Indian Cheese)",
            milk_id,
            paneer_id,
            None,
            None,
            20,  # 1 gallon milk → ~1.5 cups paneer
            json.dumps({
                "steps": [
                    "Heat 1 gallon whole milk to 200°F (almost boiling)",
                    "Remove from heat",
                    "Add 1/4 cup lemon juice or vinegar, stir gently",
                    "Curds will separate from whey immediately",
                    "Let sit 5 minutes",
                    "Strain through cheesecloth",
                    "Rinse curds under cold water (removes acid taste)",
                    "Squeeze out excess whey",
                    "Wrap in cheesecloth, press under weight 30 minutes",
                    "Unwrap, cut into cubes, refrigerate"
                ],
                "additional_ingredients": ["1/4 cup lemon juice or vinegar"],
                "equipment_needed": ["Large pot", "Thermometer", "Cheesecloth", "Heavy object for pressing"],
                "time_active": "20 minutes",
                "time_passive": "30 minutes pressing",
                "difficulty": "Easy",
                "chemistry": "Acid lowers pH to 4.6 (isoelectric point of casein), causing coagulation. No rennet needed!"
            }),
            "Firmness (press longer = firmer), taste (rinse well to avoid sour)"
        ),

        # Milk → Ricotta
        (
            "Ricotta Cheese",
            milk_id,
            ricotta_id,
            None,
            None,
            15,
            json.dumps({
                "steps": [
                    "Heat 4 cups whole milk + 1 cup heavy cream to 200°F",
                    "Remove from heat",
                    "Add 3 tbsp lemon juice or vinegar",
                    "Let sit 10 minutes (curds will form)",
                    "Gently ladle curds into cheesecloth-lined strainer",
                    "Let drain 1 hour (longer = drier ricotta)",
                    "Add salt to taste",
                    "Refrigerate, use within 3 days"
                ],
                "additional_ingredients": ["Heavy cream", "Lemon juice or vinegar", "Salt"],
                "equipment_needed": ["Pot", "Thermometer", "Cheesecloth", "Strainer"],
                "time_active": "15 minutes",
                "time_passive": "1 hour draining",
                "difficulty": "Easy",
                "chemistry": "Acid coagulation of whey proteins (albumin, globulin) as well as casein. Traditional ricotta uses whey from cheesemaking."
            }),
            "Texture (drain 30min = creamy, 2hrs = dry), grain size"
        ),

        # Cream → Whipped Cream
        (
            "Whipped Cream",
            cream_id,
            whipped_cream_id,
            None,
            None,
            200,  # Doubles in volume
            json.dumps({
                "steps": [
                    "Chill bowl and beaters in freezer 10 minutes",
                    "Pour heavy cream into chilled bowl",
                    "Add 1-2 tbsp sugar (optional)",
                    "Beat on high speed 2-3 minutes",
                    "Stop when soft peaks form (don't overbeat or you'll make butter!)",
                    "Use immediately"
                ],
                "additional_ingredients": ["Sugar (optional)", "Vanilla (optional)"],
                "equipment_needed": ["Stand mixer or hand mixer", "Chilled bowl"],
                "time_active": "3 minutes",
                "difficulty": "Very Easy",
                "chemistry": "Air bubbles trapped in fat globule network. Agglomeration of fat droplets creates foam structure. Overbeating → butter."
            }),
            "Stiffness (soft peaks vs stiff peaks)"
        ),
    ]

    for t in transformations:
        cursor.execute("""
            INSERT OR IGNORE INTO transformation_recipes
            (recipe_name, base_ingredient_id, output_preparation_id, process_id,
             equipment_id, yield_percent, instructions_json, quality_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, t)

    conn.commit()
    print(f"  [OK] Inserted {len(transformations)} additional dairy transformations")


def seed_grain_transformations(conn):
    """Seed wheat/grain transformation tree."""
    print("Seeding grain transformations...")

    cursor = conn.cursor()
    wheat_id = get_ingredient_id(conn, "wheat")

    if not wheat_id:
        print("  [SKIP] Wheat ingredient not found")
        return

    # Get existing flour/bread prep IDs
    flour_id = get_preparation_id(conn, "Whole Wheat Flour")
    bread_id = get_preparation_id(conn, "Whole Wheat Bread")
    pasta_id = get_preparation_id(conn, "Whole Wheat Pasta")

    # Get process ID
    baking_id = get_process_id(conn, "Bread Baking (Maillard + Gelatinization)")
    sourdough_id = get_process_id(conn, "Sourdough Fermentation")

    # Get equipment
    oven_id = get_equipment_id(conn, "oven")

    transformations = [
        # Wheat grain → Flour
        (
            "Grinding Wheat to Flour",
            wheat_id,
            flour_id,
            None,
            None,
            95,  # ~5% loss to bran that escapes
            json.dumps({
                "steps": [
                    "Pour wheat berries into grain mill",
                    "Set to desired fineness (fine = bread flour, coarse = pastry)",
                    "Grind wheat berries",
                    "Sift if desired (removes bran for white flour)",
                    "Store in airtight container"
                ],
                "additional_ingredients": [],
                "equipment_needed": ["Grain mill (electric or manual)", "Sifter (optional)"],
                "time_active": "10 minutes per cup",
                "difficulty": "Easy",
                "chemistry": "Mechanical breakdown of wheat kernels. Bran (outer layer), germ (embryo), endosperm (starchy center).",
                "note": "Fresh-ground flour has more nutrients but shorter shelf life (oils in germ go rancid). Use within 1 month or freeze."
            }),
            "Fineness (fine = cake flour, medium = bread flour, coarse = pastry)"
        ),

        # Flour → Bread (simple no-knead)
        (
            "No-Knead Bread",
            flour_id if flour_id else wheat_id,
            bread_id,
            baking_id,
            oven_id,
            150,  # Bread weighs more due to water
            json.dumps({
                "steps": [
                    "Mix 3 cups flour + 1.5 cups warm water + 1/4 tsp yeast + 1 tsp salt",
                    "Stir until shaggy dough forms (don't knead!)",
                    "Cover bowl, let rise 12-18 hours at room temp",
                    "Dough will be bubbly and risen",
                    "Fold dough a few times on floured surface",
                    "Shape into ball, let rest 30 minutes",
                    "Preheat Dutch oven in 450°F oven (30 min)",
                    "Place dough in hot Dutch oven, cover",
                    "Bake 30 minutes covered, 15 minutes uncovered",
                    "Cool on rack 1 hour before slicing"
                ],
                "additional_ingredients": ["Water", "Yeast", "Salt"],
                "equipment_needed": ["Dutch oven or covered pot", "Oven"],
                "time_active": "30 minutes",
                "time_passive": "12-18 hours rise + 45 min bake",
                "difficulty": "Easy",
                "chemistry": "Long fermentation develops gluten without kneading. Yeast produces CO2 (rise) and alcohol (flavor). High heat + steam = crispy crust."
            }),
            "Crust (crispy, golden), crumb (open holes), taste (tangy from long fermentation)"
        ),
    ]

    for t in transformations:
        cursor.execute("""
            INSERT OR IGNORE INTO transformation_recipes
            (recipe_name, base_ingredient_id, output_preparation_id, process_id,
             equipment_id, yield_percent, instructions_json, quality_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, t)

    conn.commit()
    print(f"  [OK] Inserted {len(transformations)} grain transformations")


def main():
    """Main seed function."""
    print("\n" + "="*60)
    print("SEEDING EXPANDED TRANSFORMATIONS")
    print("="*60 + "\n")

    conn = sqlite3.connect(DB_PATH)

    try:
        seed_milk_transformations(conn)
        seed_additional_dairy_transformations(conn)
        seed_grain_transformations(conn)

        print("\n" + "="*60)
        print("[SUCCESS] EXPANDED TRANSFORMATIONS COMPLETE!")
        print("="*60)
        print("\nWhat you can now discover:")
        print("- Milk → Yogurt, Greek Yogurt, Kefir, Skyr, Butter, Cream, Paneer, Ricotta")
        print("- Cream → Butter, Whipped Cream")
        print("- Wheat → Flour → Bread")
        print("\nNext: Build /api/ingredients/<id>/transformations endpoint")
        print("\n")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
