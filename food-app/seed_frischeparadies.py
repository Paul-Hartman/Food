#!/usr/bin/env python3
"""
Seed script to populate database with FrischeParadies products.
Products scraped from frischeparadies-shop.de
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "food.db")

# FrischeParadies products organized by category
FRISCHEPARADIES_PRODUCTS = {
    "fish_seafood": [
        {"name": "Premium Thunfischfilet", "price": 35.00, "weight_g": 500, "category": "fish"},
        {
            "name": "QSFP Glen Douglas Lachsfilet",
            "price": 45.90,
            "weight_g": 500,
            "category": "fish",
        },
        {"name": "QSFP Seeteufelfilet", "price": 45.00, "weight_g": 450, "category": "fish"},
        {
            "name": "ASC Dorade Royale ausgenommen",
            "price": 12.15,
            "weight_g": 450,
            "category": "fish",
        },
        {"name": "ASC Wolfsbarsch", "price": 12.00, "weight_g": 400, "category": "fish"},
        {"name": "MSC Miesmuscheln", "price": 9.99, "weight_g": 1500, "category": "seafood"},
        {
            "name": "Salicornes/Passe Pierre Algen",
            "price": 5.40,
            "weight_g": 200,
            "category": "seafood",
        },
        {"name": "Lachsloin", "price": 47.99, "weight_g": 600, "category": "fish"},
        {
            "name": "ASC Wolfsbarschfilet mit Haut",
            "price": 17.50,
            "weight_g": 350,
            "category": "fish",
        },
        {
            "name": "MSC High Pressure Lobster ganz",
            "price": 49.99,
            "weight_g": 500,
            "category": "seafood",
        },
        {"name": "Lachsfilet aus Island", "price": 40.99, "weight_g": 500, "category": "fish"},
        {"name": "Blinis 16 Stueck", "price": 3.49, "weight_g": 135, "category": "accompaniment"},
        {
            "name": "MSC High Pressure Lobster halbiert",
            "price": 46.99,
            "weight_g": 300,
            "category": "seafood",
        },
        {
            "name": "Austern Perles Mont St. Michel M",
            "price": 29.99,
            "weight_g": 300,
            "category": "seafood",
        },
        {"name": "Steinbuttfilet mit Haut", "price": 37.50, "weight_g": 500, "category": "fish"},
        {"name": "Graved Lachs geschnitten", "price": 12.99, "weight_g": 200, "category": "fish"},
        {"name": "Langustenschwanz", "price": 36.99, "weight_g": 260, "category": "seafood"},
        {"name": "QSFP Cadiz Wolfsbarsch", "price": 24.57, "weight_g": 850, "category": "fish"},
        {"name": "QSFP Kabeljauloin mit Haut", "price": 31.74, "weight_g": 600, "category": "fish"},
        {
            "name": "QSFP Glen Douglas Rauchlachs",
            "price": 16.99,
            "weight_g": 200,
            "category": "fish",
        },
        {
            "name": "Weisser Thunfisch in Olivenoel",
            "price": 15.99,
            "weight_g": 400,
            "category": "fish",
        },
        {
            "name": "QSFP Kabeljauloin ohne Haut",
            "price": 42.59,
            "weight_g": 600,
            "category": "fish",
        },
        {"name": "QSFP Cadiz Dorade Royale", "price": 24.57, "weight_g": 850, "category": "fish"},
        {
            "name": "MSC Nordseekrabbenfleisch",
            "price": 10.99,
            "weight_g": 100,
            "category": "seafood",
        },
    ],
    "meat_poultry": [
        {"name": "Taube bratfertig", "price": 14.99, "weight_g": 350, "category": "poultry"},
        {
            "name": "Gaensekeule Sous Vide Kochwerk",
            "price": 35.99,
            "weight_g": 900,
            "category": "poultry",
        },
        {
            "name": "Barbarie-Entenbrust weiblich",
            "price": 14.04,
            "weight_g": 390,
            "category": "poultry",
        },
        {
            "name": "Entenkeule Sous Vide Kochwerk",
            "price": 10.66,
            "weight_g": 260,
            "category": "poultry",
        },
        {
            "name": "Entenkeule Barberie maennlich",
            "price": 11.51,
            "weight_g": 640,
            "category": "poultry",
        },
        {
            "name": "Black Angus Rinderfilet Campo",
            "price": 127.03,
            "weight_g": 1650,
            "category": "beef",
        },
        {"name": "Maisstubenhueken", "price": 7.99, "weight_g": 450, "category": "poultry"},
        {
            "name": "Chateaubriand Filet Mittelstueck",
            "price": 31.50,
            "weight_g": 350,
            "category": "beef",
        },
        {
            "name": "Duroc Bratwurst THUERINGER",
            "price": 8.39,
            "weight_g": 600,
            "category": "sausage",
        },
        {"name": "Jumbo Wachteln", "price": 17.99, "weight_g": 840, "category": "poultry"},
        {"name": "Wachteloberkeule", "price": 6.60, "weight_g": 220, "category": "poultry"},
        {"name": "Wagyu Beef Burger", "price": 10.99, "weight_g": 250, "category": "beef"},
        {
            "name": "Duroc Schweinekarree mit Knochen",
            "price": 26.39,
            "weight_g": 1200,
            "category": "pork",
        },
        {
            "name": "QSFP Marensin Maishaehchenbrust Supreme",
            "price": 13.44,
            "weight_g": 420,
            "category": "poultry",
        },
        {"name": "Stubenhueken", "price": 6.49, "weight_g": 300, "category": "poultry"},
        {
            "name": "QSFP Marensin Maishaehnchenkeule ausgeloest",
            "price": 10.40,
            "weight_g": 400,
            "category": "poultry",
        },
        {
            "name": "Barbarie-Entenbrust maennlich",
            "price": 22.09,
            "weight_g": 650,
            "category": "poultry",
        },
        {
            "name": "Wachtelbrust Supreme 6er Pack",
            "price": 10.25,
            "weight_g": 250,
            "category": "poultry",
        },
        {"name": "Barbarie-Ente weiblich", "price": 17.48, "weight_g": 1400, "category": "poultry"},
        {
            "name": "Rindercarpaccio tiefgekuehlt",
            "price": 5.59,
            "weight_g": 160,
            "category": "beef",
        },
        {
            "name": "Black Angus Steakhuefte Mignon Campo",
            "price": 25.59,
            "weight_g": 800,
            "category": "beef",
        },
        {
            "name": "Perlhuhnoberkeule ausgeloest",
            "price": 12.00,
            "weight_g": 400,
            "category": "poultry",
        },
        {"name": "Ochsenbacken", "price": 31.99, "weight_g": 1000, "category": "beef"},
        {
            "name": "Maishaehchenbrust Supreme",
            "price": 18.39,
            "weight_g": 800,
            "category": "poultry",
        },
    ],
    "fruits_vegetables": [
        {"name": "Wilder Broccoli", "price": 9.49, "weight_g": 300, "category": "vegetable"},
        {"name": "Limetten frisch", "price": 0.59, "weight_g": 50, "category": "fruit"},
        {"name": "Flugmango Nam Dok Mai", "price": 11.99, "weight_g": 420, "category": "fruit"},
        {"name": "Avocado ready to eat", "price": 1.99, "weight_g": 230, "category": "fruit"},
        {
            "name": "Mini Spargelspitzen gruen",
            "price": 10.99,
            "weight_g": 250,
            "category": "vegetable",
        },
        {"name": "Honigtomaten mini", "price": 7.99, "weight_g": 180, "category": "vegetable"},
        {"name": "Karotten bunt mini", "price": 7.99, "weight_g": 200, "category": "vegetable"},
        {"name": "Kartoffeln Drillinge", "price": 2.99, "weight_g": 500, "category": "vegetable"},
        {"name": "Schalotten", "price": 2.99, "weight_g": 250, "category": "vegetable"},
        {
            "name": "Edamame Sojabohnen ungeschaelt tiefgekuehlt",
            "price": 9.99,
            "weight_g": 500,
            "category": "vegetable",
        },
        {"name": "Zitrone unbehandelt", "price": 1.85, "weight_g": 350, "category": "fruit"},
        {"name": "Wilder Blumenkohl", "price": 9.49, "weight_g": 300, "category": "vegetable"},
        {"name": "Zuckererbsen geputzt", "price": 3.49, "weight_g": 250, "category": "vegetable"},
        {"name": "Petersilie frisch", "price": 1.99, "weight_g": 25, "category": "herb"},
        {"name": "Basilikum frisch", "price": 1.99, "weight_g": 25, "category": "herb"},
        {"name": "Grapefruit", "price": 0.99, "weight_g": 100, "category": "fruit"},
        {"name": "Thymian frisch", "price": 1.99, "weight_g": 25, "category": "herb"},
        {"name": "Hokkaido Kuerbis", "price": 2.99, "weight_g": 1500, "category": "vegetable"},
        {"name": "Estragon", "price": 1.99, "weight_g": 25, "category": "herb"},
        {"name": "Koriander frisch", "price": 1.99, "weight_g": 25, "category": "herb"},
        {
            "name": "Paprika Pimientos de Padron",
            "price": 2.99,
            "weight_g": 200,
            "category": "vegetable",
        },
        {"name": "Wok Gemuese", "price": 7.99, "weight_g": 250, "category": "vegetable"},
        {"name": "Rosmarin frisch", "price": 1.99, "weight_g": 25, "category": "herb"},
        {"name": "Baby Spinat", "price": 5.89, "weight_g": 250, "category": "vegetable"},
    ],
    "pantry": [
        {"name": "BIO Amaranth", "price": 4.49, "weight_g": 500, "category": "grain"},
        {"name": "BIO Bohnen Borlotti", "price": 4.99, "weight_g": 500, "category": "legume"},
        {"name": "BIO Buchweizenmehl", "price": 5.49, "weight_g": 500, "category": "flour"},
        {"name": "BIO Bulgur Weizengruetze", "price": 3.99, "weight_g": 500, "category": "grain"},
        {"name": "BIO Camargue Reis rot", "price": 6.99, "weight_g": 500, "category": "rice"},
        {
            "name": "BIO Garbo Kichererbsen schwarz",
            "price": 7.99,
            "weight_g": 500,
            "category": "legume",
        },
        {"name": "BIO Kichererbsen", "price": 4.59, "weight_g": 500, "category": "legume"},
        {"name": "BIO Linsen gelb", "price": 5.49, "weight_g": 500, "category": "legume"},
        {"name": "BIO Linsen rot", "price": 4.69, "weight_g": 500, "category": "legume"},
        {
            "name": "BIO Polenta Maisgries instant",
            "price": 4.69,
            "weight_g": 500,
            "category": "grain",
        },
        {"name": "BIO Quinoa", "price": 5.99, "weight_g": 500, "category": "grain"},
        {"name": "BIO Quinoa rot", "price": 6.99, "weight_g": 500, "category": "grain"},
        {"name": "BIO Quinoa schwarz", "price": 7.99, "weight_g": 500, "category": "grain"},
        {"name": "Couscous", "price": 3.49, "weight_g": 500, "category": "grain"},
        {"name": "Flageolet Bohnen", "price": 5.89, "weight_g": 500, "category": "legume"},
        {"name": "Hagebuttenmark", "price": 4.49, "weight_g": 190, "category": "spread"},
        {"name": "Honig-Dill Senf Mari", "price": 4.99, "weight_g": 180, "category": "condiment"},
        {"name": "Mandelmark", "price": 7.69, "weight_g": 190, "category": "spread"},
        {"name": "Maronenmehl", "price": 10.99, "weight_g": 500, "category": "flour"},
        {"name": "Mohnsaat blau", "price": 5.49, "weight_g": 250, "category": "seed"},
        {"name": "Pecan Nusskerne", "price": 10.99, "weight_g": 200, "category": "nut"},
        {"name": "Perlgraupen", "price": 3.99, "weight_g": 500, "category": "grain"},
        {"name": "Pistazienkerne", "price": 11.99, "weight_g": 250, "category": "nut"},
        {"name": "Pistazienmark", "price": 21.99, "weight_g": 190, "category": "spread"},
    ],
    "delicatessen": [
        {"name": "Balsam Essig Apfel", "price": 14.99, "weight_g": 200, "category": "vinegar"},
        {
            "name": "Balsam Essig Granatapfel",
            "price": 15.49,
            "weight_g": 200,
            "category": "vinegar",
        },
        {
            "name": "Balsam Essig Holunderbeere",
            "price": 12.99,
            "weight_g": 200,
            "category": "vinegar",
        },
        {
            "name": "Balsam Essig Schwarze Johannisbeere",
            "price": 18.99,
            "weight_g": 500,
            "category": "vinegar",
        },
        {
            "name": "Balsam Essig Traditionell",
            "price": 9.49,
            "weight_g": 500,
            "category": "vinegar",
        },
        {"name": "Balsam Essig Weiss", "price": 9.49, "weight_g": 500, "category": "vinegar"},
        {
            "name": "BIO Olivenoel extra nativ Griechenland",
            "price": 12.99,
            "weight_g": 500,
            "category": "oil",
        },
        {"name": "BIO Urwaldpfeffer Dose", "price": 6.99, "weight_g": 45, "category": "spice"},
        {"name": "Blausalz Persien", "price": 6.99, "weight_g": 35, "category": "spice"},
        {"name": "Bunte Pfeffermischung", "price": 6.99, "weight_g": 45, "category": "spice"},
        {"name": "Chilifaeden", "price": 4.69, "weight_g": 10, "category": "spice"},
        {"name": "Englisches Curry", "price": 5.89, "weight_g": 50, "category": "spice"},
        {"name": "Fischcurry Gewuerz rot", "price": 6.49, "weight_g": 60, "category": "spice"},
        {"name": "Himbeer Balsam Essig", "price": 19.99, "weight_g": 500, "category": "vinegar"},
        {"name": "Koriandersamen ganz", "price": 5.49, "weight_g": 50, "category": "spice"},
        {"name": "Kraeuteressig", "price": 9.49, "weight_g": 500, "category": "vinegar"},
        {"name": "Kreuzk¨mmel gemahlen", "price": 5.89, "weight_g": 50, "category": "spice"},
        {"name": "Kurkuma gemahlen", "price": 4.79, "weight_g": 50, "category": "spice"},
    ],
    "sweets_snacks": [
        {
            "name": "Schokotoertchen mit weichem Kern",
            "price": 3.49,
            "weight_g": 200,
            "category": "dessert",
        },
        {"name": "Mini Kaesekuchen", "price": 4.29, "weight_g": 180, "category": "dessert"},
        {
            "name": "Milcheis Amarena Sauerkirscheis GIOLITO",
            "price": 7.99,
            "weight_g": 500,
            "category": "ice_cream",
        },
        {
            "name": "Milcheis Bourbon Vanille GIOLITO",
            "price": 6.99,
            "weight_g": 500,
            "category": "ice_cream",
        },
        {
            "name": "Milcheis Stracciatella GIOLITO",
            "price": 9.49,
            "weight_g": 500,
            "category": "ice_cream",
        },
        {"name": "Apfelstrudel Wiener Art", "price": 7.99, "weight_g": 600, "category": "dessert"},
        {
            "name": "Milcheis Pistazie GIOLITO",
            "price": 11.99,
            "weight_g": 500,
            "category": "ice_cream",
        },
        {
            "name": "Kartoffelchips mit weissem Trueffelgeschmack",
            "price": 4.69,
            "weight_g": 130,
            "category": "snack",
        },
        {
            "name": "Bruchschokolade Vollmilch-Haselnuss",
            "price": 10.99,
            "weight_g": 175,
            "category": "chocolate",
        },
        {
            "name": "Feine Pralinen Frischeparadies",
            "price": 6.49,
            "weight_g": 45,
            "category": "chocolate",
        },
        {"name": "Joghurteis GIOLITO", "price": 7.99, "weight_g": 500, "category": "ice_cream"},
        {"name": "Schokoladenmousse", "price": 8.99, "weight_g": 260, "category": "dessert"},
        {
            "name": "Schinken Crisps zart gerauchert",
            "price": 6.99,
            "weight_g": 35,
            "category": "snack",
        },
        {"name": "Mangosorbet GIOLITO", "price": 7.99, "weight_g": 500, "category": "ice_cream"},
        {"name": "Rote Gruetze DORFKRUG", "price": 2.89, "weight_g": 375, "category": "dessert"},
        {"name": "Vanillecreme", "price": 4.99, "weight_g": 500, "category": "dessert"},
        {
            "name": "Bruchschokolade gemischt",
            "price": 10.99,
            "weight_g": 175,
            "category": "chocolate",
        },
        {
            "name": "Milcheis Haselnuss GIOLITO",
            "price": 10.99,
            "weight_g": 500,
            "category": "ice_cream",
        },
        {
            "name": "Kartoffelchips mit spanischem Schinken",
            "price": 4.69,
            "weight_g": 130,
            "category": "snack",
        },
        {"name": "Himbeersorbet GIOLITO", "price": 7.99, "weight_g": 500, "category": "ice_cream"},
    ],
    "beverages": [
        {
            "name": "Weingut Engel Gris de Gris QbA",
            "price": 8.49,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Champagne Hubert de Gertale Brut AOC",
            "price": 25.99,
            "weight_g": 750,
            "category": "champagne",
        },
        {
            "name": "Chateau Haut Rian Entre deux Mers AOC",
            "price": 8.49,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Pomerols Picpoul de Pinet AOC Malassagne",
            "price": 8.49,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Rose des Plages IGP Pays dHerault",
            "price": 8.49,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Colle al Vento Carezza Primitivo di Manduria",
            "price": 12.99,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Louis Nobleray Cremant Rose AOC",
            "price": 11.99,
            "weight_g": 750,
            "category": "sparkling",
        },
        {
            "name": "Abbotts Delaunay Viognier Les Fleurs Sauvages",
            "price": 9.49,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Gratien Meyer Cremant de Loire Brut AOC",
            "price": 12.99,
            "weight_g": 750,
            "category": "sparkling",
        },
        {
            "name": "AIX Coteaux dAix en Provence AOC",
            "price": 19.99,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Sumarroca TUVI or not to be DO Penedes",
            "price": 9.49,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Olivier Leflaive Chardonnay Bourgogne AOP",
            "price": 29.99,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Greywacke Sauvignon Blanc Marlborough",
            "price": 17.99,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Alba de Vetus Albarino Rias Baixas DO",
            "price": 13.99,
            "weight_g": 750,
            "category": "wine",
        },
        {
            "name": "Ca dei Frati Lugana Frati DOC",
            "price": 15.99,
            "weight_g": 750,
            "category": "wine",
        },
        {"name": "Ultimate Provence Rose", "price": 20.99, "weight_g": 750, "category": "wine"},
        {
            "name": "Smoothie Ananas Banane Kokos",
            "price": 3.49,
            "weight_g": 250,
            "category": "smoothie",
        },
        {"name": "Smoothie Mango Orange", "price": 3.49, "weight_g": 250, "category": "smoothie"},
    ],
}


def seed_frischeparadies():
    """Insert FrischeParadies products into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count existing FrischeParadies products
    cursor.execute("SELECT COUNT(*) FROM pantry_products WHERE store = 'FrischeParadies'")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"Found {existing_count} existing FrischeParadies products. Updating prices...")
        # Update existing products
        for category, products in FRISCHEPARADIES_PRODUCTS.items():
            for product in products:
                cursor.execute(
                    """
                    UPDATE pantry_products
                    SET price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ? AND store = 'FrischeParadies'
                """,
                    (product["price"], product["name"]),
                )
        conn.commit()
        print("Prices updated!")

    inserted = 0
    updated = 0

    for category, products in FRISCHEPARADIES_PRODUCTS.items():
        for product in products:
            # Check if product exists
            cursor.execute(
                """
                SELECT id FROM pantry_products
                WHERE name = ? AND store = 'FrischeParadies'
            """,
                (product["name"],),
            )

            existing = cursor.fetchone()

            if existing:
                # Update price
                cursor.execute(
                    """
                    UPDATE pantry_products
                    SET price = ?, package_weight_g = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (product["price"], product["weight_g"], product["category"], existing[0]),
                )
                updated += 1
            else:
                # Insert new product
                cursor.execute(
                    """
                    INSERT INTO pantry_products (
                        name, store, category, package_weight_g, price, currency, data_source
                    ) VALUES (?, 'FrischeParadies', ?, ?, ?, 'EUR', 'web_scrape')
                """,
                    (product["name"], product["category"], product["weight_g"], product["price"]),
                )
                inserted += 1

    conn.commit()

    # Get counts
    cursor.execute("SELECT COUNT(*) FROM pantry_products WHERE store = 'FrischeParadies'")
    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT category, COUNT(*), SUM(price) / COUNT(*) as avg_price
        FROM pantry_products
        WHERE store = 'FrischeParadies'
        GROUP BY category
        ORDER BY COUNT(*) DESC
    """
    )

    print(f"\nFrischeParadies Products Summary:")
    print(f"  Inserted: {inserted}")
    print(f"  Updated: {updated}")
    print(f"  Total: {total}")
    print(f"\nBy Category:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} items (avg {row[2]:.2f} EUR)")

    # Show some price statistics
    cursor.execute(
        """
        SELECT MIN(price), MAX(price), AVG(price)
        FROM pantry_products
        WHERE store = 'FrischeParadies'
    """
    )
    min_price, max_price, avg_price = cursor.fetchone()
    print(f"\nPrice Range: {min_price:.2f} - {max_price:.2f} EUR (avg: {avg_price:.2f} EUR)")

    conn.close()
    return total


if __name__ == "__main__":
    count = seed_frischeparadies()
    print(f"\nDone! {count} FrischeParadies products in database.")
