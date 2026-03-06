"""
Migrate database to support comprehensive nutrition tracking
- All vitamins (A, B1-B12, C, D, E, K)
- All minerals (Calcium, Iron, Magnesium, Phosphorus, Potassium, Sodium, Zinc, etc.)
- Water intake
- Enhanced macros (saturated fat, unsaturated fat, omega-3, cholesterol)
"""

import sqlite3

DATABASE = "food.db"

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Migrating to comprehensive nutrition tracking...")

    # Drop old nutrition_goals table
    cursor.execute("DROP TABLE IF EXISTS nutrition_goals_old")
    cursor.execute("ALTER TABLE nutrition_goals RENAME TO nutrition_goals_old")

    # Create comprehensive nutrition_goals table
    cursor.execute("""
        CREATE TABLE nutrition_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Energy
            calories INTEGER DEFAULT 2000,

            -- Macronutrients
            protein_g REAL DEFAULT 50,
            carbs_g REAL DEFAULT 275,
            fat_g REAL DEFAULT 78,
            saturated_fat_g REAL DEFAULT 20,
            fiber_g REAL DEFAULT 28,
            sugar_g REAL DEFAULT 50,

            -- Water
            water_ml INTEGER DEFAULT 2000,

            -- Fat-Soluble Vitamins
            vitamin_a_mcg REAL DEFAULT 900,      -- RAE (Retinol Activity Equivalents)
            vitamin_d_mcg REAL DEFAULT 20,
            vitamin_e_mg REAL DEFAULT 15,
            vitamin_k_mcg REAL DEFAULT 120,

            -- Water-Soluble Vitamins (B Complex)
            vitamin_b1_mg REAL DEFAULT 1.2,      -- Thiamin
            vitamin_b2_mg REAL DEFAULT 1.3,      -- Riboflavin
            vitamin_b3_mg REAL DEFAULT 16,       -- Niacin
            vitamin_b5_mg REAL DEFAULT 5,        -- Pantothenic Acid
            vitamin_b6_mg REAL DEFAULT 1.7,      -- Pyridoxine
            vitamin_b7_mcg REAL DEFAULT 30,      -- Biotin
            vitamin_b9_mcg REAL DEFAULT 400,     -- Folate/Folic Acid
            vitamin_b12_mcg REAL DEFAULT 2.4,    -- Cobalamin
            vitamin_c_mg REAL DEFAULT 90,        -- Ascorbic Acid

            -- Major Minerals
            calcium_mg REAL DEFAULT 1000,
            phosphorus_mg REAL DEFAULT 700,
            magnesium_mg REAL DEFAULT 420,
            sodium_mg REAL DEFAULT 2300,
            potassium_mg REAL DEFAULT 3400,
            chloride_mg REAL DEFAULT 2300,

            -- Trace Minerals
            iron_mg REAL DEFAULT 18,
            zinc_mg REAL DEFAULT 11,
            copper_mg REAL DEFAULT 0.9,
            manganese_mg REAL DEFAULT 2.3,
            selenium_mcg REAL DEFAULT 55,
            iodine_mcg REAL DEFAULT 150,
            chromium_mcg REAL DEFAULT 35,
            molybdenum_mcg REAL DEFAULT 45,

            -- Other Important Nutrients
            omega3_g REAL DEFAULT 1.6,           -- ALA + EPA + DHA
            cholesterol_mg REAL DEFAULT 300,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default goals
    cursor.execute("""
        INSERT INTO nutrition_goals (id, calories, protein_g, carbs_g, fat_g, fiber_g)
        VALUES (1, 2000, 50, 275, 78, 28)
    """)

    # Create comprehensive daily tracking table
    cursor.execute("DROP TABLE IF EXISTS nutrition_tracking")
    cursor.execute("""
        CREATE TABLE nutrition_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE DEFAULT (date('now')) UNIQUE,

            -- Energy
            calories REAL DEFAULT 0,

            -- Macronutrients
            protein_g REAL DEFAULT 0,
            carbs_g REAL DEFAULT 0,
            fat_g REAL DEFAULT 0,
            saturated_fat_g REAL DEFAULT 0,
            fiber_g REAL DEFAULT 0,
            sugar_g REAL DEFAULT 0,

            -- Water
            water_ml REAL DEFAULT 0,

            -- Fat-Soluble Vitamins
            vitamin_a_mcg REAL DEFAULT 0,
            vitamin_d_mcg REAL DEFAULT 0,
            vitamin_e_mg REAL DEFAULT 0,
            vitamin_k_mcg REAL DEFAULT 0,

            -- Water-Soluble Vitamins
            vitamin_b1_mg REAL DEFAULT 0,
            vitamin_b2_mg REAL DEFAULT 0,
            vitamin_b3_mg REAL DEFAULT 0,
            vitamin_b5_mg REAL DEFAULT 0,
            vitamin_b6_mg REAL DEFAULT 0,
            vitamin_b7_mcg REAL DEFAULT 0,
            vitamin_b9_mcg REAL DEFAULT 0,
            vitamin_b12_mcg REAL DEFAULT 0,
            vitamin_c_mg REAL DEFAULT 0,

            -- Major Minerals
            calcium_mg REAL DEFAULT 0,
            phosphorus_mg REAL DEFAULT 0,
            magnesium_mg REAL DEFAULT 0,
            sodium_mg REAL DEFAULT 0,
            potassium_mg REAL DEFAULT 0,
            chloride_mg REAL DEFAULT 0,

            -- Trace Minerals
            iron_mg REAL DEFAULT 0,
            zinc_mg REAL DEFAULT 0,
            copper_mg REAL DEFAULT 0,
            manganese_mg REAL DEFAULT 0,
            selenium_mcg REAL DEFAULT 0,
            iodine_mcg REAL DEFAULT 0,
            chromium_mcg REAL DEFAULT 0,
            molybdenum_mcg REAL DEFAULT 0,

            -- Other Important Nutrients
            omega3_g REAL DEFAULT 0,
            cholesterol_mg REAL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    print("Migration complete!")
    print("Comprehensive nutrition tracking enabled")
    print("   - 13 vitamins (A, B1-B12, C, D, E, K)")
    print("   - 14 minerals (Calcium, Iron, Magnesium, Zinc, etc.)")
    print("   - Water tracking")
    print("   - Enhanced macros (saturated fat, omega-3, cholesterol)")

if __name__ == "__main__":
    migrate()
