"""
Second-pass enrichment: broader historical period and trade route tagging.

The first pass (enrich_anthropology.py) matched food names in Wikipedia article text,
but most food names are too specific to appear in broad history articles.

This script takes the reverse approach: tag foods based on their OWN descriptions and
existing cuisine/culture tags with historical context from known culinary history.
"""
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "food.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # ========================================================================
    # 1. Tag historical periods from food descriptions
    # ========================================================================
    print("=== Tagging historical periods from food descriptions ===")

    period_patterns = {
        "ancient": [
            r"\b(ancient|antiquity|bronze age|iron age)\b",
            r"\b(roman empire|ancient (rome|greece|egypt|china|india|persia))\b",
            r"\b(pharaoh|ptolem|hellenistic|achaemenid|han dynasty|maurya)\b",
            r"\bbc[e]?\b",
            r"\b\d+(st|nd|rd|th) century bc\b",
        ],
        "medieval": [
            r"\b(medieval|middle ages|feudal|dark ages)\b",
            r"\b(crusade|byzantine|caliphate|abbasid|umayyad)\b",
            r"\b(viking|norman|saxon|carolingian|ottonian)\b",
            r"\b(tang dynasty|song dynasty|mughal|seljuk|mamluk)\b",
            r"\b(1[0-4]\d{2}|[5-9]\d{2})\b.*\b(century|origin|creat|invent|develop)\b",
        ],
        "colonial/age of exploration": [
            r"\b(colonial|colonialism|plantation)\b",
            r"\b(east india company|voc|dutch east india)\b",
            r"\b(columbian exchange|age of (discovery|exploration))\b",
            r"\b(1[5-7]\d{2})\b.*\b(introduc|brought|arriv|import|spread)\b",
            r"\b(spanish|portuguese|dutch|british|french).{0,20}(colon|empire|trade)\b",
        ],
        "industrial era": [
            r"\b(industrial revolution|industrializ|factory|mass produc)\b",
            r"\b(18\d{2}|19[0-3]\d)\b.*\b(invent|patent|commercial|factory)\b",
            r"\b(canning|pasteuriz|refrigerat|mechaniz)\b",
        ],
        "modern/contemporary": [
            r"\b(modern|contemporary|20th century|21st century)\b",
            r"\b(molecular gastronomy|nouvelle cuisine|fusion)\b",
            r"\b(world war|post.?war|globalization)\b",
            r"\b(19[4-9]\d|20[0-2]\d)\b.*\b(popular|creat|invent|develop|introduc)\b",
        ],
    }

    rows = cursor.execute(
        "SELECT id, name, description FROM foods WHERE description IS NOT NULL AND description != ''"
    ).fetchall()

    period_count = 0
    for fid, name, desc in rows:
        text = f"{name} {desc}".lower()
        for period, patterns in period_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    cursor.execute(
                        'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "historical_period", ?, 0.7, "text_analysis")',
                        (fid, period),
                    )
                    period_count += cursor.rowcount
                    break

    conn.commit()
    print(f"  Tagged {period_count} historical period associations")

    # ========================================================================
    # 2. Tag trade routes based on cuisine + ingredient origin combinations
    # ========================================================================
    print("\n=== Tagging trade route associations ===")

    # Foods from certain cuisine+ingredient combos imply trade routes
    trade_route_rules = [
        # Silk Road: Central/East Asian foods with western spices or vice versa
        ("Silk Road", """
            SELECT DISTINCT ft.food_id FROM food_tags ft
            WHERE (ft.tag_category = 'cuisine' AND ft.tag_value IN ('Chinese', 'Indian', 'Persian', 'Turkish', 'Central Asian', 'Uzbek', 'Afghan'))
            AND ft.food_id IN (
                SELECT food_id FROM food_tags WHERE tag_category = 'ingredient'
                AND tag_value IN ('cumin', 'coriander', 'saffron', 'cinnamon', 'cardamom', 'sesame', 'ginger', 'turmeric')
            )
        """),
        # Spice Route: SE Asian/Indian foods with clove/nutmeg/pepper
        ("Spice Route", """
            SELECT DISTINCT ft.food_id FROM food_tags ft
            WHERE (ft.tag_category = 'cuisine' AND ft.tag_value IN ('Indonesian', 'Indian', 'Malaysian', 'Thai', 'Sri Lankan', 'Dutch', 'Portuguese', 'British'))
            AND ft.food_id IN (
                SELECT food_id FROM food_tags WHERE tag_category = 'ingredient'
                AND tag_value IN ('nutmeg', 'clove', 'mace', 'black pepper', 'pepper', 'cinnamon')
            )
        """),
        # Columbian Exchange: Old World cuisines using New World ingredients
        ("Columbian Exchange", """
            SELECT DISTINCT ft.food_id FROM food_tags ft
            WHERE ft.tag_category = 'cuisine'
            AND ft.tag_value IN ('Italian', 'Indian', 'Chinese', 'Thai', 'Korean', 'Hungarian', 'Spanish', 'Turkish', 'West African', 'Ethiopian')
            AND ft.food_id IN (
                SELECT food_id FROM food_tags WHERE tag_category = 'origin_hemisphere'
                AND tag_value = 'New World (Americas)'
            )
        """),
        # Columbian Exchange also: New World cuisines using Old World ingredients
        ("Columbian Exchange", """
            SELECT DISTINCT ft.food_id FROM food_tags ft
            WHERE ft.tag_category = 'cuisine'
            AND ft.tag_value IN ('Mexican', 'Peruvian', 'Brazilian', 'Argentine', 'Colombian', 'Caribbean', 'Cuban', 'American')
            AND ft.food_id IN (
                SELECT food_id FROM food_tags WHERE tag_category = 'origin_hemisphere'
                AND tag_value = 'Old World (Afro-Eurasia)'
            )
        """),
        # Trans-Saharan: West African foods with North African influences
        ("Trans-Saharan Trade", """
            SELECT DISTINCT ft.food_id FROM food_tags ft
            WHERE ft.tag_category = 'cuisine'
            AND ft.tag_value IN ('Nigerian', 'Ghanaian', 'Senegalese', 'Malian', 'West African', 'Moroccan', 'Tunisian', 'Algerian')
            AND ft.food_id IN (
                SELECT food_id FROM food_tags WHERE tag_category = 'ingredient'
                AND tag_value IN ('millet', 'sorghum', 'peanut', 'salt', 'dates', 'palm oil')
            )
        """),
        # Atlantic/Slave Trade: Caribbean/Brazilian/American Southern with African ingredients/techniques
        ("Atlantic Trade", """
            SELECT DISTINCT ft.food_id FROM food_tags ft
            WHERE ft.tag_category = 'cuisine'
            AND ft.tag_value IN ('Caribbean', 'Brazilian', 'Cuban', 'Jamaican', 'American (Cajun/Creole)', 'American (Southern)', 'Trinidadian', 'Haitian')
            AND ft.food_id IN (
                SELECT food_id FROM food_tags WHERE tag_category = 'ingredient'
                AND tag_value IN ('okra', 'black-eyed peas', 'palm oil', 'yam', 'plantain', 'rice', 'peanut')
            )
        """),
        # Maritime SE Asia: Foods reflecting Indian Ocean / Malay trade
        ("Maritime Southeast Asian Trade", """
            SELECT DISTINCT ft.food_id FROM food_tags ft
            WHERE ft.tag_category = 'cuisine'
            AND ft.tag_value IN ('Indonesian', 'Malaysian', 'Filipino', 'Singaporean', 'Thai', 'Vietnamese', 'Cambodian')
            AND ft.food_id IN (
                SELECT food_id FROM food_tags WHERE tag_category = 'ingredient'
                AND tag_value IN ('coconut', 'shrimp paste', 'fish sauce', 'lemongrass', 'galangal', 'tamarind', 'palm sugar')
            )
        """),
    ]

    trade_count = 0
    for route_name, query in trade_route_rules:
        food_ids = cursor.execute(query).fetchall()
        for (fid,) in food_ids:
            cursor.execute(
                'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "trade_route", ?, 0.7, "cross_reference")',
                (fid, route_name),
            )
            trade_count += cursor.rowcount

    conn.commit()
    print(f"  Tagged {trade_count} trade route associations")

    # ========================================================================
    # 3. Tag foods with description-based trade route mentions
    # ========================================================================
    print("\n=== Tagging trade routes from descriptions ===")

    desc_trade_patterns = {
        "Silk Road": r"\b(silk road|silk route|central asia.{0,30}(trade|spice)|along the.{0,20}silk)\b",
        "Spice Route": r"\b(spice (route|trade|island)|spice.{0,20}(trade|import|export)|moluccas|maluku)\b",
        "Columbian Exchange": r"\b(columbian exchange|new world|old world|brought.{0,30}(americas|europe)|from.{0,20}americas)\b",
        "Trans-Saharan Trade": r"\b(trans.?saharan|caravan.{0,20}(trade|route)|saharan trade|salt.{0,20}gold)\b",
        "Atlantic Trade": r"\b(atlantic (trade|slave)|middle passage|plantation|slave trade|brought.{0,30}africa)\b",
        "Mediterranean Trade": r"\b(mediterranean (trade|sea)|mare nostrum|phoenician|venetian.{0,20}trade)\b",
    }

    desc_trade_count = 0
    for fid, name, desc in rows:
        text = f"{name} {desc}".lower()
        for route, pattern in desc_trade_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                cursor.execute(
                    'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "trade_route", ?, 0.8, "text_analysis")',
                    (fid, route),
                )
                desc_trade_count += cursor.rowcount

    conn.commit()
    print(f"  Tagged {desc_trade_count} trade route associations from descriptions")

    # ========================================================================
    # 4. Tag cultural meal patterns
    # ========================================================================
    print("\n=== Tagging cultural meal patterns ===")

    # Create culture_meal_patterns table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS culture_meal_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            culture_id INTEGER REFERENCES cultures(id),
            meal_name TEXT NOT NULL,
            typical_time TEXT,
            description TEXT,
            typical_foods TEXT,
            social_context TEXT,
            UNIQUE(culture_id, meal_name)
        )
    """)

    # Get culture IDs
    cultures = {}
    for row in cursor.execute("SELECT id, name FROM cultures WHERE culture_type = 'civilization'").fetchall():
        cultures[row[1]] = row[0]

    meal_patterns = [
        # Chinese
        ("Chinese civilization", [
            ("zaocan (breakfast)", "7-9 AM", "Light but filling - congee, youtiao, jianbing, baozi, soymilk, tea eggs", "Congee, dumplings, steamed buns, soymilk", "Often eaten quickly; regional variations enormous"),
            ("wufan (lunch)", "11:30-1 PM", "Main meal in many regions - rice/noodles with multiple dishes", "Rice, stir-fries, soup, vegetables", "Often social meal with coworkers; food courts popular"),
            ("wanfan (dinner)", "6-8 PM", "Family gathering meal - multiple shared dishes around table", "Shared plates, rice, soup, meat, vegetables", "Round table symbolizes unity; lazy susan common; guest always served first"),
            ("xiaoye (late night snack)", "9-11 PM", "Night market culture - BBQ skewers, hot pot, noodles", "Chuanr skewers, hot pot, noodle soup", "Social bonding; beer culture accompanies"),
        ]),
        # Japanese
        ("Japanese civilization", [
            ("asa-gohan (breakfast)", "6-8 AM", "Traditional ichiju-sansai: rice, miso soup, pickles, grilled fish, egg", "Rice, miso soup, grilled fish, pickles, natto", "Traditional breakfast declining; Western style (toast, coffee) common among youth"),
            ("hiru-gohan (lunch)", "12-1 PM", "Bento culture - balanced box meals, or ramen/udon/soba shops", "Bento, ramen, udon, soba, donburi", "Bento-making is cultural art; convenience store onigiri hugely popular"),
            ("ban-gohan (dinner)", "7-9 PM", "Most elaborate meal - multiple courses or home-cooked ichiju-sansai", "Grilled fish, rice, miso soup, pickled vegetables, seasonal items", "Itadakimasu/gochisousama rituals frame meal; seasonal awareness (shun)"),
            ("nomikai (drinking party)", "evening", "Izakaya culture - small plates with beer/sake/shochu", "Edamame, yakitori, sashimi, karaage, beer/sake", "Crucial social bonding; first pour is always by someone else"),
        ]),
        # Indian
        ("Indian civilization", [
            ("nashta (breakfast)", "7-9 AM", "Regional: South Indian idli/dosa/upma, North Indian paratha/poha/chhole bhature", "Idli, dosa, paratha, upma, poha, chai", "Strong regional identity; chai/coffee divides North/South"),
            ("dopahar ka khana (lunch)", "12:30-2 PM", "Thali tradition - complete meal on one plate with rice/roti, dal, vegetables, pickle, yogurt", "Thali, dal, rice, roti, sabzi, raita, pickle", "Thali is nutritionally complete; eating with right hand traditional"),
            ("raat ka khana (dinner)", "8-10 PM", "Similar to lunch but often lighter; family meal", "Rice/roti, dal, curry, vegetable, dessert", "Late dinner is norm; fasting days (Ekadashi, Navratri) alter patterns completely"),
            ("chai time", "4-5 PM", "Tea and snacks - samosa, pakora, biscuits", "Chai, samosa, pakora, biscuits, mixture", "British introduced tea but India made it its own; chai wallah culture"),
        ]),
        # Italian
        ("Italian civilization", [
            ("colazione (breakfast)", "7-8 AM", "Light - espresso or cappuccino with cornetto (croissant) at bar", "Espresso, cappuccino, cornetto, biscotti", "Standing at bar is ritual; cappuccino ONLY at breakfast (never after 11am rule)"),
            ("pranzo (lunch)", "12:30-2:30 PM", "Traditionally the main meal: primo (pasta/risotto), secondo (meat/fish), contorno (vegetable), dolce", "Pasta, risotto, meat/fish, salad, wine", "Pranzo della domenica (Sunday lunch) is sacred family event; 2-3 hours"),
            ("aperitivo", "6-8 PM", "Pre-dinner drinks with snacks - Aperol Spritz, Negroni with olives, chips, small bites", "Spritz, Negroni, olives, chips, bruschetta", "Social institution; Milan's aperitivo culture can replace dinner"),
            ("cena (dinner)", "8-9:30 PM", "Lighter than lunch in modern Italy, but still multi-course for occasions", "Lighter pasta, fish, salad, cheese", "Later in South than North; never rush through a meal"),
        ]),
        # French
        ("French civilization", [
            ("petit déjeuner", "7-8 AM", "Light - tartine (bread+butter+jam) or croissant with café au lait", "Baguette, butter, jam, croissant, café au lait", "Simplest meal; dipping bread in coffee is traditional"),
            ("déjeuner", "12-2 PM", "Structured meal: entrée (starter), plat (main), fromage (cheese), dessert", "Multi-course, wine, bread, cheese course", "Sacred lunch break; 1-2 hours minimum; no eating at desk culture"),
            ("goûter", "4 PM", "Children's snack - pain au chocolat, tartine, fruit", "Pain au chocolat, tartine, fruit", "Mostly for children; adults may have café and petit gâteau"),
            ("dîner", "7:30-9 PM", "Similar structure to lunch but can be lighter on weeknights", "Soup, quiche, salad, cheese, wine", "Apéritif before dinner is ritual; meals are social events, not refueling"),
        ]),
        # Mexican
        ("Mesoamerican civilization", [
            ("desayuno", "7-10 AM", "Hearty - chilaquiles, huevos rancheros, tamales, atole, café de olla", "Chilaquiles, huevos rancheros, tamales, atole", "Big breakfast tradition; street food breakfast (tamales, atole) common"),
            ("comida (main meal)", "2-4 PM", "THE main meal: soup/rice first, then main dish, then dessert, agua fresca", "Sopa, arroz, mole/guisado, tortillas, frijoles, agua fresca", "Longest meal; siesta after; family gathering; 2-3 courses minimum"),
            ("merienda", "6-7 PM", "Light - pan dulce with coffee/chocolate, or tamales/quesadillas", "Pan dulce, café, chocolate, tamales", "Sweet bread tradition; hot chocolate with pan dulce is comfort ritual"),
            ("cena", "8-10 PM", "Very light - tacos, quesadillas, cereal, or leftovers from comida", "Tacos, quesadillas, cereal, fruit", "Lightest meal; street tacos (cenadurías) for those who eat out"),
        ]),
        # Korean
        ("Korean civilization", [
            ("achim (breakfast)", "7-8 AM", "Full meal: rice, soup, kimchi, banchan - similar to other meals", "Rice, doenjang-jjigae, kimchi, banchan, egg", "Koreans eat a full meal for breakfast; no 'breakfast food' category"),
            ("jeomshim (lunch)", "12-1 PM", "Quick but complete: bibimbap, jjigae, or kimbap with banchan", "Bibimbap, jjigae, kimbap, banchan", "Company cafeterias serve full Korean meals; no sandwich culture"),
            ("jeonyeok (dinner)", "6:30-8 PM", "Social meal - KBBQ, chimaek (chicken+beer), jjigae, or samgyeopsal", "KBBQ, samgyeopsal, chimaek, jjigae", "Highly social; soju culture; wrapping meat in lettuce leaves is communal"),
            ("yaeshik (late night)", "10 PM+", "Fried chicken + beer (chimaek), ramyeon, tteokbokki", "Chimaek, ramyeon, tteokbokki, sundae", "Post-soju snacking; delivery culture; PC bang food culture"),
        ]),
        # Turkish
        ("Turkish/Ottoman civilization", [
            ("kahvalti (breakfast)", "8-10 AM", "Most elaborate breakfast in the world: 15-20 small plates, tea, simit, eggs", "Cheese varieties, olives, honey, kaymak, simit, eggs, tomato, cucumber, tea", "Weekend kahvaltı can last 3 hours; serpme kahvaltı (spread breakfast) is art form"),
            ("öğle yemeği (lunch)", "12-1 PM", "Home-cooked or lokanta (restaurant): meat/vegetable stew, rice/bulgur, salad", "Kebab, pide, stew, rice, ayran", "Lokanta culture: choose from pre-made dishes displayed in window"),
            ("akşam yemeği (dinner)", "7-8 PM", "Family meal or meze+raki evening with friends", "Meze, grilled meats, raki, salad, bread", "Raki-meze evening is Turkish institution; slow pace, much conversation"),
            ("çay saati (tea time)", "all day", "Tea is consumed all day - with simit, börek, or pastries", "Çay, simit, börek, poğaça, baklava", "Turkey drinks more tea per capita than anywhere; tulip-shaped glass is iconic"),
        ]),
    ]

    patterns_added = 0
    for culture_name, meals in meal_patterns:
        cid = cultures.get(culture_name)
        if not cid:
            print(f"  WARNING: Culture '{culture_name}' not found")
            continue
        for meal_name, typical_time, description, typical_foods, social_context in meals:
            cursor.execute("""
                INSERT OR IGNORE INTO culture_meal_patterns
                (culture_id, meal_name, typical_time, description, typical_foods, social_context)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cid, meal_name, typical_time, description, typical_foods, social_context))
            patterns_added += cursor.rowcount

    conn.commit()
    print(f"  Added {patterns_added} cultural meal patterns")

    # ========================================================================
    # 5. Final stats
    # ========================================================================
    print("\n" + "=" * 70)
    print("HISTORY TAG ENRICHMENT COMPLETE")
    print("=" * 70)

    for cat in ["historical_period", "trade_route"]:
        cursor.execute(
            "SELECT tag_value, COUNT(*) FROM food_tags WHERE tag_category = ? GROUP BY tag_value ORDER BY COUNT(*) DESC",
            (cat,),
        )
        results = cursor.fetchall()
        total = sum(r[1] for r in results)
        print(f"\n{cat} ({total} total):")
        for val, count in results:
            print(f"  {val:40s}: {count:,}")

    cursor.execute("SELECT COUNT(*) FROM culture_meal_patterns")
    print(f"\nCultural meal patterns: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM food_tags")
    print(f"Total food tags: {cursor.fetchone()[0]:,}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
