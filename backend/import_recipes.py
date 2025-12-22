"""
Import recipes from the 13k-recipes.csv into SQLite database.
Also adds cuisine/category classification based on keywords.
"""

import ast
import csv
import json
import os
import re
import sqlite3

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
        "bacon and eggs",
        "morning",
        "brunch",
    ],
    "lunch": ["sandwich", "wrap", "salad", "soup", "burger", "panini", "quesadilla", "lunch"],
    "dinner": [
        "roast",
        "steak",
        "casserole",
        "lasagna",
        "stir fry",
        "curry",
        "grilled",
        "braised",
        "pot roast",
        "dinner",
    ],
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
        "parfait",
        "crumble",
        "cobbler",
        "sorbet",
        "gelato",
    ],
    "appetizer": [
        "appetizer",
        "starter",
        "dip",
        "bruschetta",
        "crostini",
        "deviled egg",
        "spring roll",
        "bite",
        "canape",
        "hors d'oeuvre",
    ],
    "side": [
        "side dish",
        "coleslaw",
        "mashed potato",
        "rice pilaf",
        "sauteed",
        "roasted vegetable",
        "green beans",
        "corn",
        "biscuit",
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
        "mojito",
        "sangria",
        "hot chocolate",
    ],
    "snack": ["snack", "popcorn", "chip", "cracker", "trail mix", "granola bar", "energy ball"],
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
        "marinara",
        "prosciutto",
        "pancetta",
        "ravioli",
        "fettuccine",
        "spaghetti",
        "linguine",
        "italian",
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
        "jalapeno",
        "chipotle",
        "carnitas",
        "carne asada",
        "pozole",
        "mole",
        "nachos",
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
        "chinese",
        "chow mein",
        "general tso",
        "orange chicken",
        "egg roll",
        "mu shu",
        "hoisin",
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
        "katsu",
        "yakitori",
        "dashi",
        "wasabi",
        "ponzu",
        "tonkatsu",
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
        "vindaloo",
        "korma",
        "saag",
        "pakora",
        "raita",
        "ghee",
        "garam masala",
        "turmeric",
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
        "basil chicken",
        "panang",
        "massaman",
        "som tam",
        "fish sauce",
        "lemongrass",
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
        "hollandaise",
        "bearnaise",
        "au gratin",
        "confit",
        "cassoulet",
        "beurre blanc",
        "tarte",
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
        "gumbo",
        "cornbread",
        "pulled pork",
        "ribs",
        "brisket",
        "coleslaw",
        "apple pie",
        "pot pie",
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
        "spanakopita",
        "dolma",
        "hummus",
        "pita",
        "tahini",
        "kalamata",
    ],
    "korean": [
        "kimchi",
        "bibimbap",
        "bulgogi",
        "korean",
        "gochujang",
        "korean bbq",
        "japchae",
        "tteokbokki",
        "samgyeopsal",
        "galbi",
        "doenjang",
    ],
    "vietnamese": [
        "pho",
        "banh mi",
        "spring roll",
        "vietnamese",
        "nuoc mam",
        "bun",
        "vermicelli",
        "lemongrass",
    ],
    "mediterranean": [
        "hummus",
        "falafel",
        "tabbouleh",
        "mediterranean",
        "olive oil",
        "tahini",
        "shawarma",
        "kebab",
        "pita",
    ],
    "cajun": [
        "cajun",
        "jambalaya",
        "gumbo",
        "creole",
        "andouille",
        "blackened",
        "etouffee",
        "crawfish",
    ],
    "german": ["schnitzel", "bratwurst", "sauerkraut", "german", "pretzel", "strudel", "spaetzle"],
    "british": [
        "fish and chips",
        "shepherd's pie",
        "british",
        "bangers",
        "yorkshire pudding",
        "scone",
        "trifle",
    ],
    "middle eastern": [
        "shawarma",
        "falafel",
        "tahini",
        "baba ganoush",
        "kebab",
        "baklava",
        "za'atar",
        "sumac",
        "harissa",
    ],
}


def parse_ingredients(ingredients_str):
    """Parse the ingredients string which is a Python list literal."""
    if not ingredients_str or ingredients_str == "":
        return []
    try:
        # It's stored as a Python list literal string
        return ast.literal_eval(ingredients_str)
    except:
        # Fallback: try to split by common delimiters
        return [ingredients_str]


def classify_recipe(title, ingredients_list):
    """Classify recipe into category and cuisine based on keywords."""
    title_lower = title.lower()
    ingredients_text = " ".join(ingredients_list).lower() if ingredients_list else ""
    all_text = f"{title_lower} {ingredients_text}"

    # Determine category
    category = "main"  # default
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                category = cat
                break
        if category != "main":
            break

    # If still main, check ingredients for clues
    if category == "main":
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in all_text[:1000]:
                    category = cat
                    break
            if category != "main":
                break

    # Determine cuisine
    cuisine = None
    for cuis, keywords in CUISINE_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                cuisine = cuis
                break
        if cuisine:
            break

    # Check ingredients if no cuisine found from title
    if not cuisine:
        for cuis, keywords in CUISINE_KEYWORDS.items():
            for kw in keywords:
                if kw in all_text[:1000]:
                    cuisine = cuis
                    break
            if cuisine:
                break

    return category, cuisine


def import_csv():
    """Import the 13k-recipes.csv into SQLite."""
    csv_path = os.path.join(os.path.dirname(__file__), "13k-recipes.csv")

    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found!")
        print("Please download it first:")
        print(
            "  curl -L -o 13k-recipes.csv https://github.com/josephrmartinez/recipe-dataset/raw/main/13k-recipes.csv"
        )
        return 0

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create recipes_large table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recipes_large (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            ingredients TEXT,
            instructions TEXT,
            cleaned_ingredients TEXT,
            image_name TEXT,
            category TEXT,
            cuisine TEXT,
            source TEXT DEFAULT 'epicurious',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create indexes
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

    # Read and import CSV
    print(f"Reading {csv_path}...")
    count = 0
    batch = []
    batch_size = 1000

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        for row in reader:
            title = row.get("Title", "").strip()
            if not title:
                continue

            ingredients_str = row.get("Ingredients", "")
            instructions = row.get("Instructions", "")
            cleaned_ingredients = row.get("Cleaned_Ingredients", "")
            image_name = row.get("Image_Name", "")

            # Parse ingredients list
            ingredients_list = parse_ingredients(ingredients_str)

            # Classify
            category, cuisine = classify_recipe(title, ingredients_list)

            batch.append(
                (
                    title,
                    json.dumps(ingredients_list) if ingredients_list else None,
                    instructions,
                    cleaned_ingredients,
                    image_name,
                    category,
                    cuisine,
                )
            )

            if len(batch) >= batch_size:
                cursor.executemany(
                    """
                    INSERT INTO recipes_large (title, ingredients, instructions, cleaned_ingredients, image_name, category, cuisine)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    batch,
                )
                conn.commit()
                count += len(batch)
                print(f"Imported {count} recipes...")
                batch = []

    # Insert remaining
    if batch:
        cursor.executemany(
            """
            INSERT INTO recipes_large (title, ingredients, instructions, cleaned_ingredients, image_name, category, cuisine)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            batch,
        )
        count += len(batch)

    conn.commit()

    # Print stats
    cursor.execute("SELECT COUNT(*) FROM recipes_large")
    total = cursor.fetchone()[0]

    print(f"\n=== Import Complete ===")
    print(f"Total recipes: {total:,}")

    print("\nBy Category:")
    cursor.execute(
        "SELECT category, COUNT(*) as cnt FROM recipes_large GROUP BY category ORDER BY cnt DESC"
    )
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    print("\nBy Cuisine (top 15):")
    cursor.execute(
        "SELECT cuisine, COUNT(*) as cnt FROM recipes_large WHERE cuisine IS NOT NULL GROUP BY cuisine ORDER BY cnt DESC LIMIT 15"
    )
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    cursor.execute("SELECT COUNT(*) FROM recipes_large WHERE cuisine IS NULL")
    no_cuisine = cursor.fetchone()[0]
    print(f"  (unclassified): {no_cuisine:,}")

    conn.close()
    return total


if __name__ == "__main__":
    import_csv()
