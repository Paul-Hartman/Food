"""Add more common cooking ingredients to FrischeParadies database."""

import sqlite3

conn = sqlite3.connect("food.db")
cursor = conn.cursor()

# Add more common cooking ingredients with German names and English keywords for matching
more_products = [
    # Basic cooking items (name, store, category, weight_g, price, keywords)
    ("Spanische Zwiebeln Premium", "FrischeParadies", "vegetable", 500, 2.49),
    ("Knoblauch Frisch", "FrischeParadies", "vegetable", 200, 3.99),
    ("Bio Olivenoel Extra Virgin", "FrischeParadies", "oil", 500, 12.99),
    ("Rapsoel Premium", "FrischeParadies", "oil", 1000, 7.99),
    ("Sonnenblumenoel", "FrischeParadies", "oil", 1000, 4.99),
    ("Meersalz Fleur de Sel", "FrischeParadies", "spice", 125, 8.99),
    ("Schwarzer Pfeffer gemahlen", "FrischeParadies", "spice", 50, 4.99),
    ("Gemusebruehe Bio", "FrischeParadies", "pantry", 500, 5.99),
    ("Rinderbruehe Fond", "FrischeParadies", "pantry", 500, 8.99),
    ("Huhnerbruehe Bio", "FrischeParadies", "pantry", 500, 6.99),
    # Cheese
    ("Parmigiano Reggiano 24M", "FrischeParadies", "cheese", 200, 12.99),
    ("Mozzarella di Bufala", "FrischeParadies", "cheese", 125, 5.99),
    ("Gorgonzola DOP", "FrischeParadies", "cheese", 200, 8.99),
    ("Emmentaler Schweiz", "FrischeParadies", "cheese", 250, 6.99),
    ("Gouda Holland", "FrischeParadies", "cheese", 250, 5.49),
    # Asian ingredients
    ("Sojasauce Premium", "FrischeParadies", "asian", 250, 6.99),
    ("Austernsosse", "FrischeParadies", "asian", 250, 5.99),
    ("Sesamoel Gerostet", "FrischeParadies", "asian", 200, 7.99),
    ("Reisessig", "FrischeParadies", "asian", 500, 4.99),
    ("Misopaste Rot", "FrischeParadies", "asian", 300, 9.99),
    ("Sriracha Sauce", "FrischeParadies", "asian", 435, 5.99),
    # Herbs and spices
    ("Oregano getrocknet Bio", "FrischeParadies", "spice", 30, 3.99),
    ("Kreuzkummel Cumin gemahlen", "FrischeParadies", "spice", 50, 4.49),
    ("Chili Flocken", "FrischeParadies", "spice", 50, 3.99),
    ("Frischer Basilikum", "FrischeParadies", "herb", 30, 2.99),
    ("Frischer Rosmarin", "FrischeParadies", "herb", 30, 2.99),
    ("Frischer Thymian", "FrischeParadies", "herb", 30, 2.99),
    ("Petersilie glatt", "FrischeParadies", "herb", 50, 2.49),
    # More vegetables
    ("Rote Paprika", "FrischeParadies", "vegetable", 200, 1.99),
    ("Gelbe Paprika", "FrischeParadies", "vegetable", 200, 1.99),
    ("Ingwer Frisch", "FrischeParadies", "vegetable", 100, 2.99),
    ("Champignons Weiss", "FrischeParadies", "vegetable", 300, 3.49),
    ("Shiitake Pilze", "FrischeParadies", "vegetable", 150, 5.99),
    ("Karotten Bio", "FrischeParadies", "vegetable", 500, 2.49),
    ("Sellerie Stangen", "FrischeParadies", "vegetable", 400, 2.99),
    ("Spinat Baby", "FrischeParadies", "vegetable", 125, 3.49),
    ("Zucchini", "FrischeParadies", "vegetable", 300, 2.49),
    # Meat cuts
    ("Rinderfilet Premium", "FrischeParadies", "beef", 500, 39.99),
    ("Rinder Sirloin Steak", "FrischeParadies", "beef", 300, 24.99),
    ("Rinderhack", "FrischeParadies", "beef", 400, 9.99),
    ("Schweinefilet", "FrischeParadies", "pork", 400, 15.99),
    ("Lammkeule Ohne Knochen", "FrischeParadies", "lamb", 800, 35.99),
    ("Hahnchenfilet Bio", "FrischeParadies", "chicken", 400, 12.99),
    ("Entenbrustfilet", "FrischeParadies", "poultry", 400, 18.99),
    # Pantry staples
    ("Speisestarke Mais", "FrischeParadies", "pantry", 250, 2.49),
    ("Tomatenmark doppelt konzentriert", "FrischeParadies", "pantry", 200, 2.99),
    ("Passierte Tomaten", "FrischeParadies", "pantry", 500, 2.99),
    ("Kokosmilch", "FrischeParadies", "asian", 400, 3.49),
    ("Sahne 30%", "FrischeParadies", "dairy", 200, 1.99),
    ("Butter Irland", "FrischeParadies", "dairy", 250, 4.99),
    ("Eier Bio Freiland 10er", "FrischeParadies", "dairy", 600, 5.99),
    # Pasta & Rice
    ("Spaghetti Bronze", "FrischeParadies", "pasta", 500, 3.99),
    ("Rigatoni", "FrischeParadies", "pasta", 500, 3.99),
    ("Arborio Risotto Reis", "FrischeParadies", "rice", 500, 4.99),
    ("Basmati Reis", "FrischeParadies", "rice", 1000, 5.99),
    ("Jasmin Reis", "FrischeParadies", "rice", 1000, 6.99),
    # Wine & Alcohol for cooking
    ("Sherry Fino", "FrischeParadies", "wine", 750, 12.99),
    ("Weisswein Kochen", "FrischeParadies", "wine", 750, 6.99),
    ("Rotwein Kochen", "FrischeParadies", "wine", 750, 6.99),
    # English-named common items for better matching
    ("Olive Oil Extra Virgin", "FrischeParadies", "oil", 500, 11.99),
    ("Garlic Fresh", "FrischeParadies", "vegetable", 200, 3.49),
    ("Onion Yellow", "FrischeParadies", "vegetable", 500, 1.99),
    ("Salt Sea Coarse", "FrischeParadies", "spice", 500, 2.99),
    ("Pepper Black Ground", "FrischeParadies", "spice", 50, 3.99),
    ("Beef Stock Cube", "FrischeParadies", "pantry", 80, 2.99),
    ("Chicken Stock Cube", "FrischeParadies", "pantry", 80, 2.99),
    ("Soy Sauce Dark", "FrischeParadies", "asian", 250, 5.99),
    ("Oyster Sauce", "FrischeParadies", "asian", 250, 4.99),
    ("Cornstarch", "FrischeParadies", "pantry", 200, 1.99),
    ("Cheese Parmesan", "FrischeParadies", "cheese", 200, 11.99),
    ("Cheese Cheddar", "FrischeParadies", "cheese", 250, 6.99),
    ("Red Pepper Bell", "FrischeParadies", "vegetable", 200, 1.49),
    ("Oregano Dried", "FrischeParadies", "spice", 30, 2.99),
    ("Cumin Ground", "FrischeParadies", "spice", 50, 3.49),
    ("Dry Sherry Cooking", "FrischeParadies", "wine", 375, 8.99),
    ("Sirloin Steak Beef", "FrischeParadies", "beef", 300, 22.99),
    ("Ground Beef", "FrischeParadies", "beef", 500, 9.99),
]

count = 0
for name, store, category, weight, price in more_products:
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO pantry_products (name, store, category, package_weight_g, price, currency)
            VALUES (?, ?, ?, ?, ?, 'EUR')
        """,
            (name, store, category, weight, price),
        )
        if cursor.rowcount > 0:
            count += 1
    except Exception as e:
        print(f"Error adding {name}: {e}")

conn.commit()

# Get total count
cursor.execute('SELECT COUNT(*) FROM pantry_products WHERE store = "FrischeParadies" AND price > 0')
total = cursor.fetchone()[0]

print(f"Added {count} new products")
print(f"Total FrischeParadies products: {total}")

conn.close()
