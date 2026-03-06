"""
Download and process the RecipeNLG dataset (2.2M recipes) from HuggingFace.
Then export to SQLite for the food app.
"""

import json
import os
import sqlite3

from datasets import load_dataset

DATABASE = os.path.join(os.path.dirname(__file__), "food.db")

# Categories for auto-tagging based on keywords in title/ingredients
CATEGORY_KEYWORDS = {
    "breakfast": [
        "breakfast",
        "pancake",
        "waffle",
        "omelet",
        "omelette",
        "scrambled",
        "french toast",
        "muffin",
        "bagel",
        "cereal",
        "granola",
        "smoothie bowl",
        "eggs benedict",
        "hash brown",
    ],
    "lunch": ["sandwich", "wrap", "salad", "soup", "burger", "panini", "quesadilla"],
    "dinner": ["roast", "steak", "casserole", "pasta", "lasagna", "stir fry", "curry", "grilled"],
    "dessert": [
        "cake",
        "cookie",
        "brownie",
        "pie",
        "tart",
        "ice cream",
        "pudding",
        "cheesecake",
        "chocolate",
        "fudge",
        "candy",
        "truffle",
        "mousse",
        "custard",
        "tiramisu",
    ],
    "appetizer": [
        "appetizer",
        "starter",
        "dip",
        "bruschetta",
        "crostini",
        "deviled egg",
        "spring roll",
    ],
    "side": [
        "side dish",
        "coleslaw",
        "mashed potato",
        "rice pilaf",
        "sauteed",
        "roasted vegetable",
    ],
    "beverage": [
        "cocktail",
        "smoothie",
        "shake",
        "lemonade",
        "punch",
        "tea",
        "coffee drink",
        "margarita",
    ],
}

CUISINE_KEYWORDS = {
    "italian": [
        "pasta",
        "pizza",
        "risotto",
        "lasagna",
        "gnocchi",
        "bruschetta",
        "tiramisu",
        "parmigiana",
        "carbonara",
        "bolognese",
        "pesto",
        "alfredo",
    ],
    "mexican": [
        "taco",
        "burrito",
        "enchilada",
        "quesadilla",
        "guacamole",
        "salsa",
        "fajita",
        "tamale",
        "churro",
        "mexican",
        "tortilla",
    ],
    "chinese": [
        "stir fry",
        "fried rice",
        "lo mein",
        "kung pao",
        "sweet and sour",
        "dim sum",
        "dumpling",
        "wonton",
        "szechuan",
        "teriyaki",
        "chinese",
    ],
    "japanese": [
        "sushi",
        "ramen",
        "tempura",
        "teriyaki",
        "miso",
        "udon",
        "sashimi",
        "japanese",
        "edamame",
        "gyoza",
    ],
    "indian": [
        "curry",
        "masala",
        "tikka",
        "tandoori",
        "biryani",
        "naan",
        "samosa",
        "chutney",
        "dal",
        "paneer",
        "indian",
    ],
    "thai": [
        "pad thai",
        "tom yum",
        "green curry",
        "red curry",
        "thai",
        "coconut curry",
        "satay",
        "spring roll",
    ],
    "french": [
        "croissant",
        "quiche",
        "souffle",
        "crepe",
        "ratatouille",
        "bouillabaisse",
        "french",
        "coq au vin",
        "bechamel",
    ],
    "american": [
        "burger",
        "bbq",
        "mac and cheese",
        "fried chicken",
        "hot dog",
        "buffalo",
        "american",
        "clam chowder",
    ],
    "greek": [
        "gyro",
        "tzatziki",
        "moussaka",
        "souvlaki",
        "greek salad",
        "feta",
        "baklava",
        "greek",
    ],
    "korean": ["kimchi", "bibimbap", "bulgogi", "korean", "gochujang", "korean bbq"],
    "vietnamese": ["pho", "banh mi", "spring roll", "vietnamese", "nuoc mam"],
    "mediterranean": ["hummus", "falafel", "tabbouleh", "mediterranean", "olive oil"],
}


def classify_recipe(title, ingredients, ner_tags):
    """Classify recipe into category and cuisine based on keywords."""
    title_lower = title.lower()
    ingredients_lower = " ".join(ingredients).lower() if ingredients else ""
    ner_lower = " ".join(ner_tags).lower() if ner_tags else ""
    all_text = f"{title_lower} {ingredients_lower} {ner_lower}"

    category = "main"  # default
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower or kw in all_text[:500]:
                category = cat
                break

    cuisine = None
    for cuis, keywords in CUISINE_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower or kw in all_text[:500]:
                cuisine = cuis
                break
        if cuisine:
            break

    return category, cuisine


def download_and_import(limit=None, batch_size=10000):
    """Download RecipeNLG and import to SQLite."""
    print("Loading RecipeNLG dataset from HuggingFace (2.2M recipes)...")
    print("This may take a while on first run as it downloads ~600MB...")

    # Load with trust_remote_code since it uses custom script
    dataset = load_dataset("mbien/recipe_nlg", split="train", trust_remote_code=True)

    total = len(dataset)
    if limit:
        total = min(limit, total)

    print(f"Dataset loaded: {len(dataset)} recipes")
    print(f"Will import: {total} recipes")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create new recipes_large table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recipes_large (
            id INTEGER PRIMARY KEY,
            source_id INTEGER,
            title TEXT NOT NULL,
            ingredients TEXT,
            directions TEXT,
            ner_tags TEXT,
            category TEXT,
            cuisine TEXT,
            source_url TEXT,
            source_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create indexes for faster searching
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_recipes_large_category ON recipes_large(category)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipes_large_cuisine ON recipes_large(cuisine)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipes_large_title ON recipes_large(title)")

    # Check existing count
    cursor.execute("SELECT COUNT(*) FROM recipes_large")
    existing = cursor.fetchone()[0]
    if existing > 0:
        print(f"Table already has {existing} recipes. Clearing...")
        cursor.execute("DELETE FROM recipes_large")

    conn.commit()

    # Insert in batches
    count = 0
    batch = []

    for i, recipe in enumerate(dataset):
        if limit and i >= limit:
            break

        title = recipe.get("title", "")
        ingredients = recipe.get("ingredients", [])
        directions = recipe.get("directions", [])
        ner_tags = recipe.get("ner", [])
        source_url = recipe.get("link", "")
        source_name = "Gathered" if recipe.get("source", 0) == 0 else "Recipe1M+"

        category, cuisine = classify_recipe(title, ingredients, ner_tags)

        batch.append(
            (
                recipe.get("id", i),
                title,
                json.dumps(ingredients),
                json.dumps(directions),
                json.dumps(ner_tags),
                category,
                cuisine,
                source_url,
                source_name,
            )
        )

        if len(batch) >= batch_size:
            cursor.executemany(
                """
                INSERT INTO recipes_large (source_id, title, ingredients, directions, ner_tags, category, cuisine, source_url, source_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                batch,
            )
            conn.commit()
            count += len(batch)
            print(f"Imported {count}/{total} recipes ({100*count/total:.1f}%)")
            batch = []

    # Insert remaining
    if batch:
        cursor.executemany(
            """
            INSERT INTO recipes_large (source_id, title, ingredients, directions, ner_tags, category, cuisine, source_url, source_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            batch,
        )
        count += len(batch)

    conn.commit()

    # Stats
    cursor.execute("SELECT COUNT(*) FROM recipes_large")
    total_imported = cursor.fetchone()[0]

    cursor.execute(
        "SELECT category, COUNT(*) FROM recipes_large GROUP BY category ORDER BY COUNT(*) DESC"
    )
    print(f"\nCategory distribution:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    cursor.execute(
        "SELECT cuisine, COUNT(*) FROM recipes_large WHERE cuisine IS NOT NULL GROUP BY cuisine ORDER BY COUNT(*) DESC LIMIT 15"
    )
    print(f"\nTop cuisines:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    conn.close()

    print(f"\n=== DONE ===")
    print(f"Total recipes imported: {total_imported:,}")
    return total_imported


if __name__ == "__main__":
    import sys

    # Default: import 100k recipes (manageable size)
    # Use 'all' argument to import all 2.2M
    limit = 100000

    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            limit = None
            print("Importing ALL 2.2M recipes...")
        else:
            try:
                limit = int(sys.argv[1])
            except:
                pass

    download_and_import(limit=limit)
