"""
Food Catalog Data Quality Audit & Cleanup Script
Cleans the food.db SQLite database by:
1. Removing non-food entries (geographic features, industrial structures, entertainment, people, etc.)
2. Finding and merging duplicate entries
3. Tagging untagged foods based on their descriptions
4. Fixing miscategorized food_type/primary_category entries
5. Printing a summary report
"""

import sqlite3
import sys
import re

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "food.db"

BATCH_SIZE = 500


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


DEPENDENT_TABLES = [
    ("food_tags", "food_id"),
    ("food_culture_origins", "food_id"),
    ("anthropological_recipes", "food_id"),
    ("food_ingredients_wiki", "food_id"),
    ("food_pairings", "food_id"),
    ("food_pairings", "paired_food_id"),
    ("food_meal_types", "food_id"),
    ("anthropological_recipe_ingredients", "food_id"),
]


def delete_foods_by_ids(cur, ids):
    """Delete food entries and all dependent rows in batches."""
    for i in range(0, len(ids), BATCH_SIZE):
        batch = ids[i:i + BATCH_SIZE]
        placeholders = ",".join("?" * len(batch))
        # Delete from all dependent tables first
        for dep_table, dep_col in DEPENDENT_TABLES:
            try:
                cur.execute(f"DELETE FROM {dep_table} WHERE {dep_col} IN ({placeholders})", batch)
            except Exception:
                pass  # table might not exist in all versions
        # Now delete from foods
        cur.execute(f"DELETE FROM foods WHERE id IN ({placeholders})", batch)


# ---------------------------------------------------------------------------
# 1. REMOVE NON-FOOD ENTRIES
# ---------------------------------------------------------------------------

def remove_non_food_entries(conn):
    """Identify and delete entries that are not actual foods."""
    cur = conn.cursor()
    total_deleted = 0
    categories = {}

    # ---- 1a. Villages, townships, settlements, communities ----
    cur.execute("""
        SELECT id FROM foods WHERE
            description LIKE '%village in %'
            OR description LIKE '%village-level%'
            OR description LIKE '%village of %'
            OR description LIKE '%village near %'
            OR description LIKE '%village found in%'
            OR description LIKE '%village administered%'
            OR description LIKE '%village built by%'
            OR description LIKE '%administration village%'
            OR (description LIKE '%settlement%' AND description LIKE '%township%')
            OR description LIKE '%settlement (former township)%'
            OR (description LIKE '%former township%' AND description NOT LIKE '%food%' AND description NOT LIKE '%dish%')
            OR description LIKE '%township in %County%'
            OR description LIKE '%community in %China%'
            OR description LIKE '%community in %Hangzhou%'
            OR description LIKE '%residential area%'
            OR description LIKE '%Cultural heritage in%'
            OR description LIKE '%village-level division%'
            OR description LIKE '%Chinese village%'
            OR description LIKE '%abolished town%'
    """)
    village_ids = [r[0] for r in cur.fetchall()]

    # Filter out any that are actually food-related
    if village_ids:
        food_related = set()
        for i in range(0, len(village_ids), BATCH_SIZE):
            batch = village_ids[i:i + BATCH_SIZE]
            placeholders = ",".join("?" * len(batch))
            cur.execute(f"""
                SELECT id FROM foods WHERE id IN ({placeholders})
                AND (description LIKE '%dish%' OR description LIKE '%food%'
                     OR description LIKE '%cuisine%' OR description LIKE '%wine%'
                     OR description LIKE '%beer%' OR description LIKE '%tea%'
                     OR description LIKE '%sauce%' OR description LIKE '%bread%'
                     OR description LIKE '%dessert%' OR description LIKE '%drink%'
                     OR description LIKE '%cheese%' OR description LIKE '%noodle%'
                     OR description LIKE '%delicacy%' OR description LIKE '%ferment%'
                     OR description LIKE '%snack%' OR description LIKE '%pickle%'
                     OR description LIKE '%candy%' OR description LIKE '%cake%'
                     OR description LIKE '%rice%' OR description LIKE '%meat%'
                     OR description LIKE '%soup%' OR description LIKE '%stew%'
                     OR description LIKE '%recipe%' OR description LIKE '%cook%')
            """, batch)
            food_related.update(r[0] for r in cur.fetchall())
        village_ids = [vid for vid in village_ids if vid not in food_related]

    categories["Villages/townships/settlements"] = len(village_ids)
    if village_ids:
        delete_foods_by_ids(cur, village_ids)
        total_deleted += len(village_ids)
    conn.commit()

    # ---- 1b. Kilns, furnaces, industrial structures ----
    cur.execute("""
        SELECT id FROM foods WHERE
            (name LIKE '%kiln%' OR name LIKE '%Kiln%' OR name LIKE '%Limekiln%')
            OR (name LIKE '%Furnace%' OR name LIKE '%furnace%')
            OR (name LIKE '%Blast %' AND description LIKE '%furnace%')
            OR description LIKE '%lime kiln%'
            OR description LIKE '%pottery kiln%'
            OR description LIKE '%blast furnace%'
            OR description LIKE '%iron furnace%'
            OR description LIKE '%bloomery%'
            OR description LIKE '%smelting%'
            OR description LIKE '%ironwork%'
            OR description LIKE '%brickwork%'
            OR description LIKE '%limework%'
    """)
    kiln_ids = [r[0] for r in cur.fetchall()]

    if kiln_ids:
        food_related = set()
        for i in range(0, len(kiln_ids), BATCH_SIZE):
            batch = kiln_ids[i:i + BATCH_SIZE]
            placeholders = ",".join("?" * len(batch))
            cur.execute(f"""
                SELECT id FROM foods WHERE id IN ({placeholders})
                AND (description LIKE '%food%' OR description LIKE '%dish%'
                     OR description LIKE '%cuisine%' OR description LIKE '%beverage%'
                     OR description LIKE '%tea%' OR description LIKE '%spice%'
                     OR description LIKE '%herb%' OR description LIKE '%flavor%'
                     OR description LIKE '%edible%')
            """, batch)
            food_related.update(r[0] for r in cur.fetchall())
        kiln_ids = [kid for kid in kiln_ids if kid not in food_related]

    categories["Kilns/furnaces/industrial"] = len(kiln_ids)
    if kiln_ids:
        delete_foods_by_ids(cur, kiln_ids)
        total_deleted += len(kiln_ids)
    conn.commit()

    # ---- 1c. Bakehouses (buildings, not foods) ----
    cur.execute("""
        SELECT id FROM foods WHERE
            (name LIKE 'Bakehouse%' OR name LIKE 'Backhaus%' OR name LIKE 'Backofen%'
             OR name LIKE 'Bake house%' OR name LIKE 'Bakhuisje%')
            AND (description LIKE '%building%' OR description LIKE '%bakehouse%'
                 OR description LIKE '%listed%' OR description LIKE '%Grade %'
                 OR description LIKE '%half-timbered%' OR description LIKE '%oven in%'
                 OR description IS NULL)
    """)
    bakehouse_ids = [r[0] for r in cur.fetchall()]
    categories["Bakehouses (buildings)"] = len(bakehouse_ids)
    if bakehouse_ids:
        delete_foods_by_ids(cur, bakehouse_ids)
        total_deleted += len(bakehouse_ids)
    conn.commit()

    # ---- 1d. Other buildings & structures ----
    cur.execute("""
        SELECT id FROM foods WHERE
            (description LIKE '%architectural element%'
             OR description LIKE '%architectural structure%'
             OR description LIKE '%cement factory%'
             OR description LIKE '%iron factory%'
             OR description LIKE '%steam mill%'
             OR description LIKE '%historic site%'
             OR description LIKE '%archaeological site%'
             OR description LIKE '%industrial monument%'
             OR description LIKE '%industrial heritage%'
             OR description LIKE '%cultural monument%'
             OR description LIKE '%cultural heritage monument%'
             OR description LIKE '%historic iron%'
             OR description LIKE '%historic place%'
             OR description LIKE '%bridge in%'
             OR description LIKE '%fountain in%'
             OR description LIKE '%place in%Sant%'
             OR description LIKE '%communal oven%'
             OR description LIKE '%baking oven in%'
             OR description LIKE '%type of outdoor oven%'
             OR description LIKE '%stone oven in%'
             OR description LIKE '%heritage in Sweden%'
             OR description LIKE '%building in %'
             OR description LIKE '%listed building%')
            AND description NOT LIKE '%food%'
            AND description NOT LIKE '%dish%'
            AND description NOT LIKE '%cuisine%'
            AND description NOT LIKE '%restaurant%'
            AND description NOT LIKE '%bakery%'
            AND description NOT LIKE '%beer%'
            AND description NOT LIKE '%wine%'
            AND description NOT LIKE '%bread%'
            AND description NOT LIKE '%tea house%'
            AND description NOT LIKE '%chocolate%'
            AND description NOT LIKE '%dessert%'
            AND description NOT LIKE '%candy%'
            AND description NOT LIKE '%cake%'
    """)
    structure_ids = [r[0] for r in cur.fetchall()]
    categories["Other buildings/structures"] = len(structure_ids)
    if structure_ids:
        delete_foods_by_ids(cur, structure_ids)
        total_deleted += len(structure_ids)
    conn.commit()

    # ---- 1e. Songs ----
    cur.execute("""
        SELECT id FROM foods WHERE
            name LIKE '%(song)%'
            OR description LIKE '%is a song by%'
            OR description LIKE '%is the debut single%'
            OR description LIKE '%is a novelty dance song%'
            OR (description LIKE '%is a song%' AND description NOT LIKE '%food%' AND description NOT LIKE '%dish%')
    """)
    song_ids = [r[0] for r in cur.fetchall()]
    categories["Songs"] = len(song_ids)
    if song_ids:
        delete_foods_by_ids(cur, song_ids)
        total_deleted += len(song_ids)
    conn.commit()

    # ---- 1f. Films & TV shows ----
    cur.execute("""
        SELECT id FROM foods WHERE
            name LIKE '%(film)%'
            OR name LIKE '%(movie)%'
            OR description LIKE '%drama film directed%'
            OR description LIKE '%comedy film%directed%'
            OR description LIKE '%comedy-drama film%'
            OR description LIKE '%animated%film%directed%'
            OR description LIKE '%horror film%'
            OR description LIKE '%reality television series%'
            OR description LIKE '%American reality television%'
            OR description LIKE '%cooking television series%'
            OR description LIKE '%game show%cooking competition%'
            OR description LIKE '%animated television series%'
            OR description LIKE '%animated adventure-comedy film%'
            OR description LIKE '%erotic romantic drama film%'
            OR (description LIKE '%television series%' AND description NOT LIKE '%food%dish%'
                AND description NOT LIKE '%cuisine%' AND name NOT LIKE '%food%')
    """)
    film_ids = [r[0] for r in cur.fetchall()]
    if film_ids:
        food_related = set()
        for i in range(0, len(film_ids), BATCH_SIZE):
            batch = film_ids[i:i + BATCH_SIZE]
            placeholders = ",".join("?" * len(batch))
            cur.execute(f"""
                SELECT id FROM foods WHERE id IN ({placeholders})
                AND (description LIKE '%is a% food%' OR description LIKE '%is a% dish%'
                     OR description LIKE '%is a% beverage%' OR description LIKE '%is a% drink%'
                     OR description LIKE '%is a% dessert%' OR description LIKE '%is a% snack%')
            """, batch)
            food_related.update(r[0] for r in cur.fetchall())
        film_ids = [fid for fid in film_ids if fid not in food_related]

    categories["Films/TV shows"] = len(film_ids)
    if film_ids:
        delete_foods_by_ids(cur, film_ids)
        total_deleted += len(film_ids)
    conn.commit()

    # ---- 1g. People (singers, rappers, actors) ----
    cur.execute("""
        SELECT id FROM foods WHERE
            description LIKE '%is an Azerbaijani singer%'
            OR description LIKE '%is a% singer%represented%'
            OR description LIKE '%is a German Eurodance%'
            OR description LIKE '%is a% rapper%'
            OR description LIKE '%is a% footballer%'
            OR description LIKE '%is a% politician%'
            OR description LIKE '%is a% actor%'
            OR description LIKE '%is an American band%'
            OR (description LIKE '% born %' AND description LIKE '%singer%')
    """)
    people_ids = [r[0] for r in cur.fetchall()]
    categories["People"] = len(people_ids)
    if people_ids:
        delete_foods_by_ids(cur, people_ids)
        total_deleted += len(people_ids)
    conn.commit()

    # ---- 1h. Books (non-food) ----
    cur.execute("""
        SELECT id FROM foods WHERE
            (description LIKE '%children''s book%'
             OR description LIKE '%is a book %'
             OR description LIKE '%Discourse of Forest-Trees%'
             OR description LIKE '%arts project%')
            AND description NOT LIKE '%recipe%'
            AND description NOT LIKE '%cookbook%'
            AND description NOT LIKE '%food%'
    """)
    book_ids = [r[0] for r in cur.fetchall()]
    categories["Books/art projects"] = len(book_ids)
    if book_ids:
        delete_foods_by_ids(cur, book_ids)
        total_deleted += len(book_ids)
    conn.commit()

    # ---- 1i. List articles / meta content ----
    cur.execute("""
        SELECT id FROM foods WHERE
            name LIKE 'List of %'
            OR description LIKE 'Wikimedia list article%'
            OR description LIKE 'This is a list of %'
    """)
    list_ids = [r[0] for r in cur.fetchall()]
    categories["List/meta articles"] = len(list_ids)
    if list_ids:
        delete_foods_by_ids(cur, list_ids)
        total_deleted += len(list_ids)
    conn.commit()

    # ---- 1j. History articles ----
    cur.execute("""
        SELECT id FROM foods WHERE
            name LIKE 'History of %'
            OR name LIKE 'history of %'
    """)
    history_ids = [r[0] for r in cur.fetchall()]
    categories["History articles"] = len(history_ids)
    if history_ids:
        delete_foods_by_ids(cur, history_ids)
        total_deleted += len(history_ids)
    conn.commit()

    # ---- 1k. General concepts, not actual foods ----
    cur.execute("""
        SELECT id FROM foods WHERE
            description LIKE '%is a circular diagram%'
            OR description LIKE '%epidemiological observation%'
            OR description LIKE '%Latin phrase%'
            OR description LIKE '%Anglo-Saxon law%'
            OR description LIKE '%type of trial by ordeal%'
            OR description LIKE '%Jewish benediction%'
            OR description LIKE '%classification tool%'
            OR description LIKE '%Beer measurement%'
            OR description LIKE '%Fermentation is a type of anaerobic%'
            OR description LIKE '%cause-marketing campaign%'
            OR description LIKE '%tie-ins to films%'
            OR description LIKE '%personal vaporizer%'
            OR description LIKE '%ice cream van manufacturer%'
            OR description LIKE '%international festival promoting%'
            OR description LIKE '%mead competition%'
            OR description LIKE '%wine district in%'
            OR (name = 'Fermentation' AND description LIKE '%anaerobic metabolism%')
            OR (name = 'Aging of wine' AND description LIKE '%potentially able to improve%')
            OR (name = 'Aroma of wine' AND description LIKE '%more diverse than%')
            OR (name = 'Wine color' AND description LIKE '%one of the most easily%')
            OR (name = 'Beer measurement')
    """)
    concept_ids = [r[0] for r in cur.fetchall()]
    categories["General concepts (non-food)"] = len(concept_ids)
    if concept_ids:
        delete_foods_by_ids(cur, concept_ids)
        total_deleted += len(concept_ids)
    conn.commit()

    # ---- 1l. Leftover geographic entries miscategorized as alcohol ----
    cur.execute("""
        SELECT id FROM foods WHERE
            food_type = 'beverage' AND primary_category = 'alcohol'
            AND (description LIKE '%village%' OR description LIKE '%township%'
                 OR description LIKE '%community%' OR description LIKE '%settlement%')
            AND description NOT LIKE '%wine%' AND description NOT LIKE '%beer%'
            AND description NOT LIKE '%drink%' AND description NOT LIKE '%spirit%'
            AND description NOT LIKE '%alcohol%' AND description NOT LIKE '%brew%'
            AND description NOT LIKE '%distill%' AND description NOT LIKE '%ferment%'
    """)
    leftover_geo_ids = [r[0] for r in cur.fetchall()]
    categories["Leftover geographic (in alcohol category)"] = len(leftover_geo_ids)
    if leftover_geo_ids:
        delete_foods_by_ids(cur, leftover_geo_ids)
        total_deleted += len(leftover_geo_ids)
    conn.commit()

    return total_deleted, categories


# ---------------------------------------------------------------------------
# 2. FIND AND MERGE DUPLICATES
# ---------------------------------------------------------------------------

def find_and_merge_duplicates(conn):
    """Find entries with very similar names and merge them."""
    cur = conn.cursor()
    merged_count = 0
    merge_details = []

    # Exact case-insensitive duplicates
    cur.execute("""
        SELECT LOWER(TRIM(name)) as lname, GROUP_CONCAT(id) as ids, COUNT(*) as cnt
        FROM foods GROUP BY lname HAVING cnt > 1
    """)
    exact_dupes = cur.fetchall()

    for lname, ids_str, cnt in exact_dupes:
        ids = [int(x) for x in ids_str.split(",")]
        keep_id = ids[0]
        remove_ids = ids[1:]

        cur.execute(f"SELECT id, description FROM foods WHERE id IN ({','.join('?' * len(ids))})", ids)
        rows = cur.fetchall()
        best_desc = None
        best_id = keep_id
        for rid, desc in rows:
            if desc and (best_desc is None or len(desc) > len(best_desc)):
                best_desc = desc
                best_id = rid

        if best_id != keep_id:
            keep_id = best_id
            remove_ids = [x for x in ids if x != keep_id]

        for rid in remove_ids:
            cur.execute("""
                INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source)
                SELECT ?, tag_category, tag_value, confidence, source FROM food_tags WHERE food_id = ?
            """, (keep_id, rid))
            delete_foods_by_ids(cur, [rid])
            merged_count += 1

        merge_details.append(f"  Merged '{lname}': kept id={keep_id}, removed ids={remove_ids}")

    # Near-duplicates: normalize dashes/underscores/spaces
    cur.execute("""
        SELECT LOWER(REPLACE(REPLACE(REPLACE(TRIM(name), '-', ' '), '_', ' '), '  ', ' ')) as norm,
               GROUP_CONCAT(id) as ids, COUNT(*) as cnt
        FROM foods GROUP BY norm HAVING cnt > 1
    """)
    near_dupes = cur.fetchall()

    for norm, ids_str, cnt in near_dupes:
        ids = [int(x) for x in ids_str.split(",")]
        keep_id = ids[0]
        remove_ids = ids[1:]

        cur.execute(f"SELECT id, description, name FROM foods WHERE id IN ({','.join('?' * len(ids))})", ids)
        rows = cur.fetchall()
        best_desc = None
        best_id = keep_id
        for rid, desc, name in rows:
            if desc and (best_desc is None or len(desc) > len(best_desc)):
                best_desc = desc
                best_id = rid

        if best_id != keep_id:
            keep_id = best_id
            remove_ids = [x for x in ids if x != keep_id]

        for rid in remove_ids:
            cur.execute("""
                INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source)
                SELECT ?, tag_category, tag_value, confidence, source FROM food_tags WHERE food_id = ?
            """, (keep_id, rid))
            delete_foods_by_ids(cur, [rid])
            merged_count += 1

        merge_details.append(f"  Merged '{norm}': kept id={keep_id}, removed ids={remove_ids}")

    conn.commit()
    return merged_count, merge_details


# ---------------------------------------------------------------------------
# 3. TAG UNTAGGED FOODS
# ---------------------------------------------------------------------------

def tag_untagged_foods(conn):
    """Find foods with no tags and add tags based on their descriptions."""
    cur = conn.cursor()
    tagged_count = 0

    cur.execute("""
        SELECT f.id, f.name, f.description, f.food_type, f.primary_category,
               f.is_vegetarian, f.is_vegan, f.is_gluten_free,
               f.typical_prep_method, f.serving_temperature
        FROM foods f
        LEFT JOIN food_tags ft ON f.id = ft.food_id
        WHERE ft.id IS NULL AND f.description IS NOT NULL AND f.description != ''
    """)
    untagged = cur.fetchall()

    cuisine_keywords = {
        "japanese": "Japanese", "chinese": "Chinese", "korean": "Korean",
        "thai": "Thai", "indian": "Indian", "italian": "Italian",
        "french": "French", "mexican": "Mexican", "spanish": "Spanish",
        "german": "German", "greek": "Greek", "turkish": "Turkish",
        "vietnamese": "Vietnamese", "indonesian": "Indonesian",
        "filipino": "Filipino", "brazilian": "Brazilian", "persian": "Persian",
        "iranian": "Iranian", "moroccan": "Moroccan", "ethiopian": "Ethiopian",
        "nigerian": "Nigerian", "russian": "Russian", "polish": "Polish",
        "bengali": "Bengali", "sri lankan": "Sri Lankan",
        "british": "British", "american": "American", "australian": "Australian",
        "portuguese": "Portuguese", "swedish": "Swedish", "norwegian": "Norwegian",
        "danish": "Danish", "dutch": "Dutch", "belgian": "Belgian",
        "swiss": "Swiss", "austrian": "Austrian", "hungarian": "Hungarian",
        "czech": "Czech", "romanian": "Romanian", "lebanese": "Lebanese",
        "egyptian": "Egyptian", "tunisian": "Tunisian", "arab": "Arab",
        "caribbean": "Caribbean", "jamaican": "Jamaican", "cuban": "Cuban",
        "peruvian": "Peruvian", "argentinian": "Argentinian", "colombian": "Colombian",
        "polynesian": "Polynesian", "hawaiian": "Hawaiian",
        "catalan": "Catalan", "basque": "Basque", "sicilian": "Sicilian",
        "bavarian": "Bavarian", "cantonese": "Cantonese", "sichuan": "Sichuan",
        "szechuan": "Sichuan", "malay": "Malay", "singaporean": "Singaporean",
        "taiwanese": "Taiwanese", "tibetan": "Tibetan", "nepalese": "Nepalese",
        "pakistani": "Pakistani", "afghan": "Afghan",
    }

    course_keywords = {
        "dessert": "dessert", "appetizer": "appetizer", "starter": "appetizer",
        "main course": "main_course", "side dish": "side_dish",
        "snack": "snack", "condiment": "condiment", "sauce": "sauce",
        "soup": "soup", "stew": "stew", "salad": "salad",
        "breakfast": "breakfast", "brunch": "brunch",
    }

    cooking_method_keywords = {
        "fried": "fried", "deep-fried": "deep_fried", "deep fried": "deep_fried",
        "baked": "baked", "grilled": "grilled", "steamed": "steamed",
        "boiled": "boiled", "roasted": "roasted", "smoked": "smoked",
        "fermented": "fermented", "pickled": "pickled", "braised": "braised",
        "sauteed": "sauteed", "saut\u00e9ed": "sauteed", "stir-fried": "stir_fried",
        "stir fried": "stir_fried", "pan-fried": "pan_fried",
        "slow-cooked": "slow_cooked", "marinated": "marinated",
        "poached": "poached", "blanched": "blanched", "cured": "cured",
        "dried": "dried", "raw": "raw",
    }

    dietary_keywords = {
        "vegetarian": "vegetarian", "vegan": "vegan",
        "gluten-free": "gluten_free", "gluten free": "gluten_free",
        "halal": "halal", "kosher": "kosher",
        "dairy-free": "dairy_free", "dairy free": "dairy_free",
    }

    ingredient_keywords = {
        "chicken": "chicken", "beef": "beef", "pork": "pork",
        "lamb": "lamb", "fish": "fish", "shrimp": "shrimp",
        "rice": "rice", "wheat": "wheat", "corn": "corn",
        "potato": "potato", "tomato": "tomato", "onion": "onion",
        "garlic": "garlic", "ginger": "ginger", "coconut": "coconut",
        "chocolate": "chocolate", "sugar": "sugar", "honey": "honey",
        "egg": "egg", "milk": "milk", "cream": "cream",
        "cheese": "cheese", "butter": "butter", "yogurt": "yogurt",
        "tofu": "tofu", "soybean": "soybean", "lentil": "lentil",
        "bean": "bean", "chickpea": "chickpea", "peanut": "peanut",
        "almond": "almond", "walnut": "walnut", "sesame": "sesame",
        "chili": "chili", "pepper": "pepper", "cinnamon": "cinnamon",
        "cumin": "cumin", "turmeric": "turmeric", "saffron": "saffron",
        "noodle": "noodle", "pasta": "pasta", "flour": "flour",
    }

    for food_id, name, desc, food_type, primary_cat, is_veg, is_vegan_flag, is_gf, prep_method, temp in untagged:
        desc_lower = desc.lower() if desc else ""
        name_lower = name.lower()
        tags_to_add = []

        # Cuisine tags
        for keyword, tag_val in cuisine_keywords.items():
            if keyword in desc_lower or keyword in name_lower:
                tags_to_add.append(("cuisine", tag_val, 0.8))

        # Course tags
        for keyword, tag_val in course_keywords.items():
            if keyword in desc_lower:
                tags_to_add.append(("course", tag_val, 0.8))

        # Cooking method tags
        for keyword, tag_val in cooking_method_keywords.items():
            if keyword in desc_lower:
                tags_to_add.append(("cooking_method", tag_val, 0.7))

        # Dietary tags
        for keyword, tag_val in dietary_keywords.items():
            if keyword in desc_lower:
                tags_to_add.append(("dietary", tag_val, 0.7))

        # Ingredient tags (only add top 5)
        ingredient_tags = []
        for keyword, tag_val in ingredient_keywords.items():
            pattern = r'\b' + re.escape(keyword) + r's?\b'
            if re.search(pattern, desc_lower):
                ingredient_tags.append(("ingredient", tag_val, 0.7))
        tags_to_add.extend(ingredient_tags[:5])

        # Food type tag from the food_type column
        if food_type:
            tags_to_add.append(("food_type", food_type, 0.9))

        # Temperature tag
        if temp:
            tags_to_add.append(("temperature", temp, 0.9))

        if tags_to_add:
            for cat, val, conf in tags_to_add:
                try:
                    cur.execute("""
                        INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source)
                        VALUES (?, ?, ?, ?, 'auto_cleanup')
                    """, (food_id, cat, val, conf))
                except sqlite3.IntegrityError:
                    pass
            tagged_count += 1

    conn.commit()

    cur.execute("""
        SELECT COUNT(*) FROM foods f
        LEFT JOIN food_tags ft ON f.id = ft.food_id
        WHERE ft.id IS NULL
    """)
    still_untagged = cur.fetchone()[0]

    return tagged_count, still_untagged


# ---------------------------------------------------------------------------
# 4. FIX MISCATEGORIZED ENTRIES
# ---------------------------------------------------------------------------

def fix_categories(conn):
    """Check and fix food_type and primary_category for misclassified entries."""
    cur = conn.cursor()
    fixes = {}

    # ---- 4a. Beverages classified as dishes ----
    cur.execute("""
        UPDATE foods SET food_type = 'beverage'
        WHERE food_type = 'dish'
        AND (description LIKE '%is a% beverage%'
             OR description LIKE '%is a% drink%'
             OR description LIKE '%is a cocktail%'
             OR description LIKE '%is a% tea%'
             OR description LIKE '%is a% coffee%'
             OR description LIKE '%is a% juice%'
             OR description LIKE '%is a% smoothie%'
             OR description LIKE '%is a% milkshake%'
             OR description LIKE '%lemonade%'
             OR (description LIKE '%carbonated%' AND description LIKE '%drink%'))
        AND description NOT LIKE '%is a% dish%'
        AND description NOT LIKE '%is a% food%'
    """)
    fixes["Dishes reclassified as beverages"] = cur.rowcount

    # ---- 4b. Ingredients classified as dishes ----
    cur.execute("""
        UPDATE foods SET food_type = 'ingredient'
        WHERE food_type = 'dish'
        AND (description LIKE '%is a spice%'
             OR description LIKE '%is a herb%'
             OR description LIKE '%is an herb%'
             OR description LIKE '%is a% grain%'
             OR description LIKE '%is a species of%'
             OR description LIKE '%is a variety of%fruit%'
             OR description LIKE '%is a% vegetable%'
             OR description LIKE '%volatile oil%'
             OR description LIKE '%essential oil%')
        AND description NOT LIKE '%is a% dish%'
        AND description NOT LIKE '%is a% recipe%'
    """)
    fixes["Dishes reclassified as ingredients"] = cur.rowcount

    # ---- 4c. Condiments classified as dishes ----
    cur.execute("""
        UPDATE foods SET food_type = 'condiment'
        WHERE food_type = 'dish'
        AND (description LIKE '%is a% sauce%'
             OR description LIKE '%is a% condiment%'
             OR description LIKE '%is a% seasoning%'
             OR description LIKE '%dipping sauce%'
             OR description LIKE '%is a% relish%'
             OR description LIKE '%is a% chutney%')
        AND description NOT LIKE '%dish%served%'
        AND description NOT LIKE '%main course%'
    """)
    fixes["Dishes reclassified as condiments"] = cur.rowcount

    # ---- 4d. Fix primary_category for soups ----
    cur.execute("""
        UPDATE foods SET primary_category = 'soup'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% soup%' OR description LIKE '%is a% broth%'
             OR description LIKE '%soup dish%' OR name LIKE '%soup%' OR name LIKE '%Soup%')
        AND description NOT LIKE '%noodle%dish%'
    """)
    fixes["Prepared foods recategorized as soup"] = cur.rowcount

    # ---- 4e. Fix primary_category for desserts ----
    cur.execute("""
        UPDATE foods SET primary_category = 'dessert'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% dessert%' OR description LIKE '%is a% pastry%'
             OR description LIKE '%is a% cake%' OR description LIKE '%is a% cookie%'
             OR description LIKE '%is a% candy%' OR description LIKE '%is a% sweet%'
             OR description LIKE '%is a% pudding%' OR description LIKE '%is a% confection%'
             OR description LIKE '%is a% ice cream%')
    """)
    fixes["Prepared foods recategorized as dessert"] = cur.rowcount

    # ---- 4f. Fix primary_category for breads ----
    cur.execute("""
        UPDATE foods SET primary_category = 'bread'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% bread%' OR description LIKE '%flatbread%'
             OR description LIKE '%is a type of bread%')
        AND description NOT LIKE '%sandwich%'
    """)
    fixes["Prepared foods recategorized as bread"] = cur.rowcount

    # ---- 4g. Fix primary_category for pasta ----
    cur.execute("""
        UPDATE foods SET primary_category = 'pasta'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% pasta%' OR description LIKE '%is a% noodle%'
             OR description LIKE '%noodle dish%' OR description LIKE '%pasta dish%')
    """)
    fixes["Prepared foods recategorized as pasta"] = cur.rowcount

    # ---- 4h. Fix primary_category for salads ----
    cur.execute("""
        UPDATE foods SET primary_category = 'salad'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% salad%' OR description LIKE '%salad dish%')
    """)
    fixes["Prepared foods recategorized as salad"] = cur.rowcount

    # ---- 4i. Fix primary_category for sandwiches ----
    cur.execute("""
        UPDATE foods SET primary_category = 'sandwich'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% sandwich%' OR description LIKE '%sandwich%type%')
    """)
    fixes["Prepared foods recategorized as sandwich"] = cur.rowcount

    # ---- 4j. Fix primary_category for rice dishes ----
    cur.execute("""
        UPDATE foods SET primary_category = 'rice'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% rice dish%' OR description LIKE '%fried rice%'
             OR description LIKE '%rice cake%' OR description LIKE '%rice porridge%')
    """)
    fixes["Prepared foods recategorized as rice"] = cur.rowcount

    # ---- 4k. Fix primary_category for stews ----
    cur.execute("""
        UPDATE foods SET primary_category = 'stew'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% stew%' OR description LIKE '%stew dish%')
        AND description NOT LIKE '%soup%'
    """)
    fixes["Prepared foods recategorized as stew"] = cur.rowcount

    # ---- 4l. Fix primary_category for dumplings ----
    cur.execute("""
        UPDATE foods SET primary_category = 'dumpling'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% dumpling%' OR description LIKE '%dumpling dish%'
             OR description LIKE '%filled dumpling%')
    """)
    fixes["Prepared foods recategorized as dumpling"] = cur.rowcount

    # ---- 4m. Fix primary_category for curries ----
    cur.execute("""
        UPDATE foods SET primary_category = 'curry'
        WHERE primary_category = 'prepared_food'
        AND (description LIKE '%is a% curry%' OR description LIKE '%curry dish%')
        AND description NOT LIKE '%paste%'
    """)
    fixes["Prepared foods recategorized as curry"] = cur.rowcount

    # ---- 4n. Fix beverage subcategories ----
    cur.execute("""
        UPDATE foods SET primary_category = 'beverage'
        WHERE primary_category = 'prepared_food'
        AND food_type = 'beverage'
    """)
    fixes["Beverage type with prepared_food category fixed"] = cur.rowcount

    conn.commit()
    return fixes


# ---------------------------------------------------------------------------
# 5. SUMMARY REPORT
# ---------------------------------------------------------------------------

def print_report(deleted_count, deleted_categories, merged_count, merge_details,
                 tagged_count, still_untagged, category_fixes):
    """Print a comprehensive summary report."""
    print("=" * 70)
    print("  FOOD CATALOG DATA QUALITY AUDIT & CLEANUP REPORT")
    print("=" * 70)

    print("\n1. NON-FOOD ENTRIES REMOVED")
    print("-" * 40)
    for cat, count in sorted(deleted_categories.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"   {cat}: {count}")
    print(f"   TOTAL DELETED: {deleted_count}")

    print("\n2. DUPLICATE ENTRIES MERGED")
    print("-" * 40)
    if merge_details:
        for detail in merge_details[:20]:
            print(detail)
        if len(merge_details) > 20:
            print(f"   ... and {len(merge_details) - 20} more")
    else:
        print("   No duplicates found.")
    print(f"   TOTAL MERGED: {merged_count}")

    print("\n3. UNTAGGED FOODS AUTO-TAGGED")
    print("-" * 40)
    print(f"   Foods newly tagged: {tagged_count}")
    print(f"   Foods still untagged: {still_untagged}")

    print("\n4. CATEGORY FIXES")
    print("-" * 40)
    total_cat_fixes = 0
    for fix, count in sorted(category_fixes.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"   {fix}: {count}")
            total_cat_fixes += count
    if total_cat_fixes == 0:
        print("   No category fixes needed.")
    print(f"   TOTAL CATEGORY FIXES: {total_cat_fixes}")

    conn_tmp = sqlite3.connect(DB_PATH)
    c = conn_tmp.cursor()
    c.execute("SELECT COUNT(*) FROM foods")
    total_foods = c.fetchone()[0]
    c.execute("SELECT food_type, COUNT(*) FROM foods GROUP BY food_type ORDER BY COUNT(*) DESC")
    type_dist = c.fetchall()
    c.execute("SELECT primary_category, COUNT(*) FROM foods GROUP BY primary_category ORDER BY COUNT(*) DESC")
    cat_dist = c.fetchall()
    conn_tmp.close()

    print(f"\n5. FINAL DATABASE STATS")
    print("-" * 40)
    print(f"   Total foods remaining: {total_foods}")
    print(f"\n   Food type distribution:")
    for ft, cnt in type_dist:
        print(f"     {ft}: {cnt}")
    print(f"\n   Primary category distribution (top 20):")
    for pc, cnt in cat_dist[:20]:
        print(f"     {pc}: {cnt}")
    if len(cat_dist) > 20:
        print(f"     ... and {len(cat_dist) - 20} more categories")

    print("\n" + "=" * 70)
    print("  CLEANUP COMPLETE")
    print("=" * 70)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    conn = get_conn()

    print("Starting food catalog cleanup...")
    print()

    print("[1/4] Removing non-food entries...")
    deleted_count, deleted_categories = remove_non_food_entries(conn)
    print(f"      Removed {deleted_count} non-food entries.")

    print("[2/4] Finding and merging duplicates...")
    merged_count, merge_details = find_and_merge_duplicates(conn)
    print(f"      Merged {merged_count} duplicate entries.")

    print("[3/4] Tagging untagged foods...")
    tagged_count, still_untagged = tag_untagged_foods(conn)
    print(f"      Tagged {tagged_count} previously untagged foods.")

    print("[4/4] Fixing miscategorized entries...")
    category_fixes = fix_categories(conn)
    total_fixes = sum(category_fixes.values())
    print(f"      Fixed {total_fixes} category assignments.")

    conn.close()

    print()
    print_report(deleted_count, deleted_categories, merged_count, merge_details,
                 tagged_count, still_untagged, category_fixes)


if __name__ == "__main__":
    main()
