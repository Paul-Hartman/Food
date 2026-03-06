#!/usr/bin/env python3
"""
Seed kitchen tools database with common items from German stores.
Run: python seed_kitchen_tools.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "food.db")

# Kitchen tools from various stores
KITCHEN_TOOLS = [
    # ============================================
    # COOKWARE - Pans
    # ============================================
    {
        "name": "Bratpfanne 28cm",
        "brand": "Crofton",
        "store": "aldi",
        "category": "cookware",
        "subcategory": "pan",
        "material": "non_stick",
        "size": "28cm",
        "price": 12.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Edelstahl Bratpfanne",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "cookware",
        "subcategory": "pan",
        "material": "stainless_steel",
        "size": "28cm",
        "price": 14.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 260,
    },
    {
        "name": "Gusseisen Pfanne",
        "brand": "WMF",
        "store": "rewe",
        "category": "cookware",
        "subcategory": "pan",
        "material": "cast_iron",
        "size": "26cm",
        "price": 49.99,
        "dishwasher_safe": 0,
        "oven_safe": 1,
        "max_temp_c": 300,
    },
    {
        "name": "Crepe Pfanne",
        "brand": "Crofton",
        "store": "aldi",
        "category": "cookware",
        "subcategory": "pan",
        "material": "non_stick",
        "size": "25cm",
        "price": 9.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Wok Pfanne",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "cookware",
        "subcategory": "wok",
        "material": "non_stick",
        "size": "30cm",
        "price": 19.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    # ============================================
    # COOKWARE - Pots
    # ============================================
    {
        "name": "Kochtopf Set 4-teilig",
        "brand": "Crofton",
        "store": "aldi",
        "category": "cookware",
        "subcategory": "pot",
        "material": "stainless_steel",
        "size": "16-24cm",
        "price": 29.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Suppentopf",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "cookware",
        "subcategory": "pot",
        "material": "stainless_steel",
        "size": "8L",
        "price": 24.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Schnellkochtopf",
        "brand": "WMF",
        "store": "rewe",
        "category": "cookware",
        "subcategory": "pressure_cooker",
        "material": "stainless_steel",
        "size": "6L",
        "price": 89.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Milchtopf",
        "brand": "Crofton",
        "store": "aldi",
        "category": "cookware",
        "subcategory": "pot",
        "material": "stainless_steel",
        "size": "1.5L",
        "price": 8.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Schmortopf",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "cookware",
        "subcategory": "dutch_oven",
        "material": "cast_iron",
        "size": "4L",
        "price": 34.99,
        "dishwasher_safe": 0,
        "oven_safe": 1,
        "max_temp_c": 250,
    },
    # ============================================
    # CUTLERY - Knives
    # ============================================
    {
        "name": "Kochmesser",
        "brand": "Crofton",
        "store": "aldi",
        "category": "cutlery",
        "subcategory": "chef_knife",
        "material": "stainless_steel",
        "size": "20cm",
        "price": 7.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Santoku Messer",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "cutlery",
        "subcategory": "santoku",
        "material": "stainless_steel",
        "size": "18cm",
        "price": 9.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Messerset 6-teilig",
        "brand": "WMF",
        "store": "rewe",
        "category": "cutlery",
        "subcategory": "knife_set",
        "material": "stainless_steel",
        "size": "mixed",
        "price": 59.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Brotmesser",
        "brand": "Crofton",
        "store": "aldi",
        "category": "cutlery",
        "subcategory": "bread_knife",
        "material": "stainless_steel",
        "size": "22cm",
        "price": 6.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Gemüsemesser Set",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "cutlery",
        "subcategory": "paring_knife",
        "material": "stainless_steel",
        "size": "3-teilig",
        "price": 5.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Filetiermesser",
        "brand": "WMF",
        "store": "rewe",
        "category": "cutlery",
        "subcategory": "fillet_knife",
        "material": "stainless_steel",
        "size": "16cm",
        "price": 24.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    # ============================================
    # UTENSILS - Spatulas, spoons, etc.
    # ============================================
    {
        "name": "Pfannenwender",
        "brand": "Crofton",
        "store": "aldi",
        "category": "utensils",
        "subcategory": "spatula",
        "material": "silicone",
        "size": "standard",
        "price": 3.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Kochlöffel Set",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "utensils",
        "subcategory": "wooden_spoon",
        "material": "wood",
        "size": "3-teilig",
        "price": 4.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Schneebesen",
        "brand": "WMF",
        "store": "rewe",
        "category": "utensils",
        "subcategory": "whisk",
        "material": "stainless_steel",
        "size": "25cm",
        "price": 12.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Schöpflöffel",
        "brand": "Crofton",
        "store": "aldi",
        "category": "utensils",
        "subcategory": "ladle",
        "material": "stainless_steel",
        "size": "standard",
        "price": 4.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Zange",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "utensils",
        "subcategory": "tongs",
        "material": "stainless_steel",
        "size": "30cm",
        "price": 5.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Silikonspatel Set",
        "brand": "WMF",
        "store": "rewe",
        "category": "utensils",
        "subcategory": "spatula",
        "material": "silicone",
        "size": "3-teilig",
        "price": 14.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 230,
    },
    {
        "name": "Kartoffelstampfer",
        "brand": "Crofton",
        "store": "aldi",
        "category": "utensils",
        "subcategory": "masher",
        "material": "stainless_steel",
        "size": "standard",
        "price": 5.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Sparschäler",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "utensils",
        "subcategory": "peeler",
        "material": "stainless_steel",
        "size": "standard",
        "price": 2.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    # ============================================
    # APPLIANCES
    # ============================================
    {
        "name": "Stabmixer",
        "brand": "Quigg",
        "store": "aldi",
        "category": "appliances",
        "subcategory": "immersion_blender",
        "material": "plastic",
        "size": "600W",
        "price": 19.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Standmixer",
        "brand": "SilverCrest",
        "store": "lidl",
        "category": "appliances",
        "subcategory": "blender",
        "material": "plastic",
        "size": "1.5L",
        "price": 29.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Küchenmaschine",
        "brand": "KitchenAid",
        "store": "rewe",
        "category": "appliances",
        "subcategory": "stand_mixer",
        "material": "metal",
        "size": "4.8L",
        "price": 449.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Toaster",
        "brand": "Quigg",
        "store": "aldi",
        "category": "appliances",
        "subcategory": "toaster",
        "material": "stainless_steel",
        "size": "2-Scheiben",
        "price": 14.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Wasserkocher",
        "brand": "SilverCrest",
        "store": "lidl",
        "category": "appliances",
        "subcategory": "kettle",
        "material": "stainless_steel",
        "size": "1.7L",
        "price": 19.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "Kaffeemaschine",
        "brand": "Melitta",
        "store": "rewe",
        "category": "appliances",
        "subcategory": "coffee_maker",
        "material": "plastic",
        "size": "10 Tassen",
        "price": 34.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    # ============================================
    # BAKEWARE
    # ============================================
    {
        "name": "Backblech Set",
        "brand": "Crofton",
        "store": "aldi",
        "category": "bakeware",
        "subcategory": "baking_sheet",
        "material": "non_stick",
        "size": "2-teilig",
        "price": 9.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 230,
    },
    {
        "name": "Springform",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "bakeware",
        "subcategory": "springform",
        "material": "non_stick",
        "size": "26cm",
        "price": 7.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 230,
    },
    {
        "name": "Muffinform",
        "brand": "Kaiser",
        "store": "rewe",
        "category": "bakeware",
        "subcategory": "muffin_tin",
        "material": "non_stick",
        "size": "12er",
        "price": 14.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 230,
    },
    {
        "name": "Kastenform",
        "brand": "Crofton",
        "store": "aldi",
        "category": "bakeware",
        "subcategory": "loaf_pan",
        "material": "non_stick",
        "size": "30cm",
        "price": 6.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 230,
    },
    {
        "name": "Auflaufform",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "bakeware",
        "subcategory": "casserole",
        "material": "ceramic",
        "size": "3L",
        "price": 12.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 250,
    },
    {
        "name": "Pizzablech",
        "brand": "Kaiser",
        "store": "rewe",
        "category": "bakeware",
        "subcategory": "pizza_pan",
        "material": "non_stick",
        "size": "32cm",
        "price": 9.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 250,
    },
    # ============================================
    # STORAGE
    # ============================================
    {
        "name": "Frischhaltedosen Set",
        "brand": "Crofton",
        "store": "aldi",
        "category": "storage",
        "subcategory": "container",
        "material": "plastic",
        "size": "10-teilig",
        "price": 7.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    {
        "name": "Glasdosen Set",
        "brand": "Ernesto",
        "store": "lidl",
        "category": "storage",
        "subcategory": "container",
        "material": "glass",
        "size": "5-teilig",
        "price": 14.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 200,
    },
    {
        "name": "Vorratsdosen Set",
        "brand": "Emsa",
        "store": "rewe",
        "category": "storage",
        "subcategory": "canister",
        "material": "plastic",
        "size": "4-teilig",
        "price": 19.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
    # ============================================
    # IKEA items (common in German kitchens)
    # ============================================
    {
        "name": "VARDAGEN Bratpfanne",
        "brand": "IKEA",
        "store": "ikea",
        "category": "cookware",
        "subcategory": "pan",
        "material": "cast_iron",
        "size": "28cm",
        "price": 29.99,
        "dishwasher_safe": 0,
        "oven_safe": 1,
        "max_temp_c": 250,
    },
    {
        "name": "KONCIS Auflaufform",
        "brand": "IKEA",
        "store": "ikea",
        "category": "bakeware",
        "subcategory": "casserole",
        "material": "stainless_steel",
        "size": "34x24cm",
        "price": 14.99,
        "dishwasher_safe": 1,
        "oven_safe": 1,
        "max_temp_c": 250,
    },
    {
        "name": "365+ Kochlöffel Set",
        "brand": "IKEA",
        "store": "ikea",
        "category": "utensils",
        "subcategory": "wooden_spoon",
        "material": "wood",
        "size": "3-teilig",
        "price": 4.99,
        "dishwasher_safe": 0,
        "oven_safe": 0,
    },
    {
        "name": "PRUTA Frischhaltedosen",
        "brand": "IKEA",
        "store": "ikea",
        "category": "storage",
        "subcategory": "container",
        "material": "plastic",
        "size": "17-teilig",
        "price": 6.99,
        "dishwasher_safe": 1,
        "oven_safe": 0,
    },
]

# Store brand colors (for reference in app)
STORE_COLORS = {
    "aldi": {"primary": "#00005f", "name": "ALDI"},
    "lidl": {"primary": "#0050aa", "name": "Lidl"},
    "rewe": {"primary": "#cc0000", "name": "REWE"},
    "ikea": {"primary": "#0058a3", "name": "IKEA"},
    "wmf": {"primary": "#000000", "name": "WMF"},
}


def seed_kitchen_tools():
    """Insert all kitchen tools into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS kitchen_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            store TEXT,
            category TEXT NOT NULL,
            subcategory TEXT,
            material TEXT,
            size TEXT,
            image_url TEXT,
            price REAL,
            currency TEXT DEFAULT 'EUR',
            condition TEXT DEFAULT 'good',
            purchase_date DATE,
            warranty_until DATE,
            dishwasher_safe INTEGER DEFAULT 0,
            oven_safe INTEGER DEFAULT 0,
            max_temp_c INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    inserted = 0
    skipped = 0

    for tool in KITCHEN_TOOLS:
        # Check if already exists
        cursor.execute(
            "SELECT id FROM kitchen_tools WHERE name = ? AND brand = ? AND store = ?",
            (tool["name"], tool.get("brand"), tool.get("store")),
        )
        if cursor.fetchone():
            store_tag = f"[{tool.get('store', '?')[0].upper()}]"
            print(f"  [!] Skipping duplicate: {store_tag} {tool['name']}")
            skipped += 1
            continue

        cursor.execute(
            """
            INSERT INTO kitchen_tools (
                name, brand, store, category, subcategory, material, size,
                price, currency, dishwasher_safe, oven_safe, max_temp_c
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EUR', ?, ?, ?)
        """,
            (
                tool["name"],
                tool.get("brand"),
                tool.get("store"),
                tool["category"],
                tool.get("subcategory"),
                tool.get("material"),
                tool.get("size"),
                tool.get("price"),
                tool.get("dishwasher_safe", 0),
                tool.get("oven_safe", 0),
                tool.get("max_temp_c"),
            ),
        )

        store_tag = f"[{tool.get('store', '?')[0].upper()}]"
        print(f"  [+] Added: {store_tag} {tool['name']} - {tool['category']}")
        inserted += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"Kitchen Tools Seeding Complete!")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped:  {skipped}")
    print(f"{'='*50}")

    # Print summary by category
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT category, COUNT(*) as count
        FROM kitchen_tools
        GROUP BY category
        ORDER BY count DESC
    """
    )
    print("\nBy Category:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} items")

    cursor.execute(
        """
        SELECT store, COUNT(*) as count
        FROM kitchen_tools
        GROUP BY store
        ORDER BY count DESC
    """
    )
    print("\nBy Store:")
    for row in cursor.fetchall():
        store_name = STORE_COLORS.get(row[0], {}).get("name", row[0])
        print(f"  {store_name}: {row[1]} items")

    conn.close()


if __name__ == "__main__":
    print("Seeding Kitchen Tools Database...")
    print("=" * 50)
    seed_kitchen_tools()
