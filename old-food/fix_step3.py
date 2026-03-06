import sqlite3

# Connect to database
conn = sqlite3.connect('backend/food.db')
cursor = conn.cursor()

# Update Step 3 with proper formatting
instruction = """In a separate bowl (or large measuring cup), use scale to measure:
360ml buttermilk (or 360g)
2 whole eggs (~100g)
50g melted butter
5ml vanilla extract

Tip: For liquids, 1ml ~ 1g for water-based ingredients."""

cursor.execute("""
    UPDATE cooking_steps
    SET instruction = ?
    WHERE recipe_id = 1125 AND step_number = 3
""", (instruction,))

conn.commit()

# Verify the update
cursor.execute("""
    SELECT instruction FROM cooking_steps
    WHERE recipe_id = 1125 AND step_number = 3
""")
result = cursor.fetchone()[0]

print("Updated Step 3 instruction:")
print(result)
print()

# Verify it contains "2 whole"
if "2 whole" in result:
    print("[OK] Step 3 now contains '2 whole eggs'")
else:
    print("[ERROR] Step 3 still doesn't have correct format")

conn.close()
