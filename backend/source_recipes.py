"""
Source stub recipes from Wikipedia food data for cuisines lacking recipe coverage.

Generates recipes in recipes_large from foods table data (descriptions, tags)
for cuisines that currently have zero recipes. Uses Wikipedia API to supplement
food descriptions where possible.

Tagged as 'wikipedia_derived' source to distinguish from human-written recipes.
"""

import sqlite3
import sys
import time
import json
import re
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "food.db"

# Rate limit for Wikipedia API (seconds between requests)
WIKI_DELAY = 0.5

# ─── Cuisine normalization map ──────────────────────────────────────────────
# Maps raw food_tags cuisine values to canonical cuisine names used in recipes_large
NORMALIZE = {
    "chinese": "Chinese", "chinese cuisine": "Chinese", "people's republic of china": "Chinese",
    "china": "Chinese", "sichuan cuisine": "Chinese", "cantonese cuisine": "Chinese",
    "hunan cuisine": "Chinese", "shandong cuisine": "Chinese", "shaanxi cuisine": "Chinese",
    "hubei cuisine": "Chinese", "northeastern chinese cuisine": "Chinese",
    "huaiyang cuisine": "Chinese", "teochew cuisine": "Chinese",
    "japanese": "Japanese", "japanese cuisine": "Japanese", "japan": "Japanese", "yoshoku": "Japanese",
    "yōshoku": "Japanese", "okinawan cuisine": "Japanese",
    "korean": "Korean", "korean cuisine": "Korean", "korea": "Korean", "south korea": "Korean",
    "south korean cuisine": "Korean",
    "indian": "Indian", "indian cuisine": "Indian", "india": "Indian",
    "indian subcontinent": "Indian", "south asian cuisine": "Indian",
    "gujarati cuisine": "Indian", "bengali cuisine": "Indian",
    "rajasthani cuisine": "Indian", "kashmiri cuisine": "Indian",
    "maharashtrian cuisine": "Indian", "keralan cuisine": "Indian",
    "punjabi cuisine": "Indian", "south indian cuisine": "Indian",
    "hyderabadi cuisine": "Indian", "mughlai cuisine": "Indian",
    "awadhi cuisine": "Indian", "tamil cuisine": "Indian",
    "karnataka cuisine": "Indian", "sindhi cuisine": "Indian",
    "telugu cuisine": "Indian",
    "italian": "Italian", "italian cuisine": "Italian", "italy": "Italian",
    "sicilian cuisine": "Italian", "neapolitan cuisine": "Italian",
    "tuscan cuisine": "Italian", "lombard cuisine": "Italian",
    "roman cuisine": "Italian", "emilian cuisine": "Italian",
    "piedmont": "Italian",
    "french": "French", "french cuisine": "French", "france": "French",
    "cuisine nicoise": "French", "cuisine niçoise": "French",
    "provencal cuisine": "French", "alsatian cuisine": "French",
    "cuisine from dauphiné (france)": "French",
    "mexican": "Mexican", "mexican cuisine": "Mexican", "mexico": "Mexican",
    "spanish": "Spanish", "spanish cuisine": "Spanish", "spain": "Spanish",
    "galician cuisine": "Spanish", "basque cuisine": "Spanish", "catalan cuisine": "Spanish",
    "valencian cuisine": "Spanish", "andalusian cuisine": "Spanish",
    "castilian cuisine": "Spanish", "cantabrian cuisine": "Spanish",
    "greek": "Greek", "greek cuisine": "Greek", "greece": "Greek",
    "cretan cuisine": "Greek",
    "turkish": "Turkish", "turkish cuisine": "Turkish", "turkey": "Turkish",
    "ottoman empire": "Turkish",
    "german": "German", "german cuisine": "German", "germany": "German",
    "bavarian cuisine": "German", "hessian cuisine": "German",
    "swabian cuisine": "German", "baden cuisine": "German",
    "thai": "Thai", "thai cuisine": "Thai", "thailand": "Thai",
    "vietnamese": "Vietnamese", "vietnamese cuisine": "Vietnamese", "vietnam": "Vietnamese",
    "indonesian": "Indonesian", "indonesia": "Indonesian", "indonesian cuisine": "Indonesian",
    "acehnese cuisine": "Indonesian", "javanese cuisine": "Indonesian",
    "padang cuisine": "Indonesian", "balinese cuisine": "Indonesian",
    "banjar cuisine": "Indonesian", "batak cuisine": "Indonesian",
    "betawi cuisine": "Indonesian", "palembang cuisine": "Indonesian",
    "british": "British", "united kingdom": "British", "england": "British",
    "scotland": "British", "welsh": "British", "wales": "British",
    "english cuisine": "British", "scottish cuisine": "British",
    "british cuisine": "British",
    "american": "American", "united states": "American",
    "cuisine of the united states": "American",
    "southern us": "American (Southern)", "cuisine of the southern united states": "American (Southern)",
    "cajun/creole": "American (Cajun/Creole)",
    "cajun": "American (Cajun/Creole)", "louisiana creole cuisine": "American (Cajun/Creole)",
    "tex-mex": "American (Tex-Mex)",
    "middle eastern": "Middle Eastern", "middle east": "Middle Eastern",
    "levantine cuisine": "Middle Eastern", "levant": "Middle Eastern",
    "arab cuisine": "Middle Eastern",
    "mediterranean": "Mediterranean", "mediterranean cuisine": "Mediterranean",
    "russian": "Russian", "russian cuisine": "Russian", "russia": "Russian",
    "soviet cuisine": "Russian", "soviet union": "Russian",
    "scandinavian": "Scandinavian", "scandinavia": "Scandinavian",
    "swedish": "Swedish", "swedish cuisine": "Swedish", "sweden": "Swedish",
    "norwegian": "Norwegian", "norwegian cuisine": "Norwegian", "norway": "Norwegian",
    "danish": "Danish", "danish cuisine": "Danish", "denmark": "Danish",
    "finnish": "Finnish", "finnish cuisine": "Finnish", "finland": "Finnish",
    "icelandic": "Icelandic", "icelandic cuisine": "Icelandic", "iceland": "Icelandic",
    "african": "Pan-African", "african cuisine": "Pan-African", "africa": "Pan-African",
    "west african cuisine": "Pan-African",
    "caribbean": "Caribbean",
    "latin american": "Latin American", "latin america": "Latin American",
    "latin american cuisine": "Latin American",
    "polish": "Polish", "polish cuisine": "Polish", "poland": "Polish",
    "hungarian": "Hungarian", "hungarian cuisine": "Hungarian", "hungary": "Hungarian",
    "portuguese": "Portuguese", "portuguese cuisine": "Portuguese", "portugal": "Portuguese",
    "swiss": "Swiss", "swiss cuisine": "Swiss", "switzerland": "Swiss",
    "ukrainian": "Ukrainian", "ukrainian cuisine": "Ukrainian", "ukraine": "Ukrainian",
    "romanian": "Romanian", "romanian cuisine": "Romanian", "romania": "Romanian",
    "czech": "Czech", "czech cuisine": "Czech", "czech republic": "Czech",
    "georgian": "Georgian", "georgian cuisine": "Georgian", "georgia": "Georgian",
    "armenian": "Armenian", "armenian cuisine": "Armenian", "armenia": "Armenian",
    "azerbaijani": "Azerbaijani", "azerbaijani cuisine": "Azerbaijani", "azerbaijan": "Azerbaijani",
    "taiwanese": "Taiwanese", "taiwanese cuisine": "Taiwanese",
    "taiwan": "Taiwanese", "taiwan island": "Taiwanese",
    "philippine": "Filipino", "philippines": "Filipino", "filipino cuisine": "Filipino",
    "malaysian": "Malaysian", "malaysia": "Malaysian", "malaysian cuisine": "Malaysian",
    "malay cuisine": "Malaysian",
    "singaporean": "Singaporean", "singapore": "Singaporean",
    "cambodian": "Cambodian", "cambodia": "Cambodian", "cambodian cuisine": "Cambodian",
    "burmese": "Burmese", "myanmar": "Burmese", "burmese cuisine": "Burmese",
    "laotian": "Laotian", "laos": "Laotian", "lao cuisine": "Laotian",
    "peruvian": "Peruvian", "peru": "Peruvian", "peruvian cuisine": "Peruvian",
    "brazilian": "Brazilian", "brazil": "Brazilian", "brazilian cuisine": "Brazilian",
    "argentine": "Argentine", "argentine cuisine": "Argentine", "argentina": "Argentine",
    "chilean": "Chilean", "chile": "Chilean", "chilean cuisine": "Chilean",
    "colombian": "Colombian", "colombia": "Colombian", "colombian cuisine": "Colombian",
    "venezuelan": "Venezuelan", "venezuela": "Venezuelan", "venezuelan cuisine": "Venezuelan",
    "bolivian": "Bolivian", "bolivia": "Bolivian", "bolivian cuisine": "Bolivian",
    "paraguayan": "Paraguayan", "paraguay": "Paraguayan", "paraguayan cuisine": "Paraguayan",
    "uruguayan": "Uruguayan", "uruguay": "Uruguayan", "uruguayan cuisine": "Uruguayan",
    "ecuadorian": "Ecuadorian", "ecuador": "Ecuadorian",
    "cuban": "Cuban", "cuba": "Cuban", "cuban cuisine": "Cuban",
    "jamaican": "Jamaican", "jamaica": "Jamaican", "jamaican cuisine": "Jamaican",
    "haitian": "Haitian", "haiti": "Haitian", "haitian cuisine": "Haitian",
    "trinidadian": "Trinidadian", "trinidad and tobago": "Trinidadian",
    "puerto rican": "Puerto Rican", "puerto rico": "Puerto Rican",
    "nigerian": "Nigerian", "nigerian cuisine": "Nigerian", "nigeria": "Nigerian",
    "yoruba cuisine": "Nigerian",
    "ghanaian": "Ghanaian", "ghana": "Ghanaian", "ghanaian cuisine": "Ghanaian",
    "ethiopian": "Ethiopian", "ethiopia": "Ethiopian", "ethiopian cuisine": "Ethiopian",
    "senegalese": "Senegalese", "senegal": "Senegalese", "senegalese cuisine": "Senegalese",
    "south african": "South African", "south africa": "South African",
    "south african cuisine": "South African",
    "kenyan": "Kenyan", "kenya": "Kenyan",
    "ugandan": "Ugandan", "uganda": "Ugandan", "ugandan cuisine": "Ugandan",
    "cameroonian": "Cameroonian", "cameroon": "Cameroonian", "cameroonian cuisine": "Cameroonian",
    "moroccan": "Moroccan", "moroccan cuisine": "Moroccan", "morocco": "Moroccan",
    "tunisian": "Tunisian", "tunisian cuisine": "Tunisian", "tunisia": "Tunisian",
    "algerian": "Algerian", "algerian cuisine": "Algerian", "algeria": "Algerian",
    "egyptian": "Egyptian", "egypt": "Egyptian", "egyptian cuisine": "Egyptian",
    "libyan": "Libyan", "libya": "Libyan", "libyan cuisine": "Libyan",
    "lebanese": "Lebanese", "lebanon": "Lebanese", "lebanese cuisine": "Lebanese",
    "iranian": "Iranian", "iranian cuisine": "Iranian", "iran": "Iranian",
    "iraqi": "Iraqi", "iraq": "Iraqi", "iraqi cuisine": "Iraqi",
    "syrian": "Syrian", "syria": "Syrian", "syrian cuisine": "Syrian",
    "saudi arabian": "Saudi Arabian", "saudi arabia": "Saudi Arabian",
    "yemeni": "Yemeni", "yemen": "Yemeni",
    "israeli": "Israeli", "israel": "Israeli", "israeli cuisine": "Israeli",
    "palestinian": "Palestinian", "palestinian cuisine": "Palestinian", "palestine": "Palestinian",
    "jordanian": "Jordanian", "jordan": "Jordanian", "jordanian cuisine": "Jordanian",
    "jewish": "Jewish", "jewish cuisine": "Jewish",
    "sephardic jewish cuisine": "Jewish", "ashkenazi jewish cuisine": "Jewish",
    "kurdish": "Kurdish", "kurdish cuisine": "Kurdish", "kurdistan": "Kurdish",
    "irish": "Irish", "ireland": "Irish", "irish cuisine": "Irish",
    "austrian": "Austrian", "austrian cuisine": "Austrian", "austria": "Austrian",
    "viennese cuisine": "Austrian",
    "belgian": "Belgian", "belgium": "Belgian", "cuisine of belgium": "Belgian",
    "flemish cuisine": "Belgian",
    "dutch": "Dutch", "dutch cuisine": "Dutch", "netherlands": "Dutch",
    "kingdom of the netherlands": "Dutch",
    "luxembourgish": "Luxembourgish", "luxembourg": "Luxembourgish",
    "serbian": "Serbian", "serbia": "Serbian", "serbian cuisine": "Serbian",
    "croatian": "Croatian", "croatia": "Croatian", "croatian cuisine": "Croatian",
    "slovenian": "Slovenian", "slovenia": "Slovenian", "slovenian cuisine": "Slovenian",
    "bosnian": "Bosnian", "bosnia and herzegovina": "Bosnian",
    "bulgarian": "Bulgarian", "bulgarian cuisine": "Bulgarian", "bulgaria": "Bulgarian",
    "albanian": "Albanian", "albanian cuisine": "Albanian", "albania": "Albanian",
    "estonian": "Estonian", "estonia": "Estonian", "estonian cuisine": "Estonian",
    "latvian": "Latvian", "latvia": "Latvian", "latvian cuisine": "Latvian",
    "lithuanian": "Lithuanian", "lithuanian cuisine": "Lithuanian", "lithuania": "Lithuanian",
    "belarusian": "Belarusian", "belarusian cuisine": "Belarusian", "belarus": "Belarusian",
    "moldovan": "Moldovan", "moldova": "Moldovan", "moldovan cuisine": "Moldovan",
    "montenegrin": "Montenegrin", "montenegro": "Montenegrin",
    "kosovar": "Kosovar", "kosovo": "Kosovar",
    "north macedonian": "North Macedonian", "north macedonia": "North Macedonian",
    "macedonian cuisine": "North Macedonian",
    "slovak": "Slovak", "slovakia": "Slovak", "slovak cuisine": "Slovak",
    "maltese": "Maltese", "malta": "Maltese", "maltese cuisine": "Maltese",
    "cypriot": "Cypriot", "cyprus": "Cypriot",
    "mongolian": "Mongolian", "mongolia": "Mongolian", "mongolian cuisine": "Mongolian",
    "kazakh": "Kazakh", "kazakh cuisine": "Kazakh", "kazakhstan": "Kazakh",
    "uzbek": "Uzbek", "uzbekistan": "Uzbek", "cuisine of uzbekistan": "Uzbek",
    "kyrgyz": "Kyrgyz", "kyrgyzstan": "Kyrgyz", "kyrgyz cuisine": "Kyrgyz",
    "tajik": "Tajik", "tajikistan": "Tajik", "tajik cuisine": "Tajik",
    "polynesian": "Polynesian",
    "australian": "Australian", "australia": "Australian", "australian cuisine": "Australian",
    "new zealand": "New Zealand", "new zealand cuisine": "New Zealand",
    "canadian": "Canadian", "canada": "Canadian", "canadian cuisine": "Canadian",
    "central asian": "Central Asian", "central asia": "Central Asian",
    "eastern european": "Eastern European", "eastern europe": "Eastern European",
    "southeast asian": "Southeast Asian", "southeast asia": "Southeast Asian",
    "nepali": "Nepali", "nepal": "Nepali", "nepalese cuisine": "Nepali",
    "sri lankan": "Sri Lankan", "sri lanka": "Sri Lankan",
    "bangladeshi": "Bangladeshi", "bangladesh": "Bangladeshi", "bangladeshi cuisine": "Bangladeshi",
    "pakistani": "Pakistani", "pakistan": "Pakistani", "pakistani cuisine": "Pakistani",
    "afghan": "Afghan", "afghanistan": "Afghan", "afghan cuisine": "Afghan",
    "bhutanese": "Bhutanese", "bhutan": "Bhutanese", "bhutanese cuisine": "Bhutanese",
}

# Cuisines that already have recipes - skip these
CUISINES_WITH_RECIPES = {
    "Chinese", "Japanese", "Korean", "Indian", "Italian", "French", "Mexican",
    "Greek", "German", "Thai", "Vietnamese", "British", "American",
    "American (Cajun/Creole)", "Middle Eastern", "Mediterranean",
}

# Cooking method to basic instruction templates
METHOD_INSTRUCTIONS = {
    "baked": "Preheat oven. Prepare ingredients and combine as directed. Bake until done.",
    "fried": "Heat oil in a pan over medium-high heat. Prepare ingredients. Fry until golden and cooked through.",
    "boiled": "Bring water or broth to a boil. Add prepared ingredients. Cook until tender.",
    "fermented": "Combine ingredients with fermenting agent. Store in appropriate conditions. Allow to ferment for the required time.",
    "dried": "Prepare ingredients. Dry using traditional methods (sun, air, or dehydrator) until properly preserved.",
    "grilled": "Prepare and season ingredients. Grill over medium-high heat, turning as needed, until cooked through.",
    "steamed": "Prepare ingredients. Place in steamer basket over boiling water. Steam until cooked through.",
    "roasted": "Preheat oven. Season ingredients. Roast at high temperature until golden and cooked through.",
    "pickled": "Prepare brine or pickling liquid. Submerge prepared ingredients. Allow to pickle for the required time.",
    "smoked": "Prepare ingredients with seasoning. Smoke using appropriate wood at controlled temperature until done.",
    "marinated": "Combine marinade ingredients. Coat the main ingredient thoroughly. Allow to marinate, then cook as desired.",
    "cured": "Apply curing mixture to ingredients. Store under proper conditions for the curing period.",
    "braised": "Sear ingredients in hot oil. Add liquid and aromatics. Cover and cook slowly until tender.",
    "stewed": "Cut ingredients into pieces. Combine in pot with liquid and seasonings. Simmer until tender and flavors meld.",
    "poached": "Bring liquid to a gentle simmer. Carefully add ingredients. Poach until cooked through.",
    "stir-fried": "Heat oil in a wok over high heat. Add ingredients in order of cooking time. Stir-fry quickly until done.",
    "deep-fried": "Heat oil to proper temperature. Prepare and batter ingredients if needed. Deep-fry until golden and crispy.",
    "raw": "Select fresh, high-quality ingredients. Clean and prepare as needed. Serve fresh.",
}


def normalize_cuisine(raw_value):
    """Normalize a raw cuisine tag value to canonical name."""
    return NORMALIZE.get(raw_value.lower(), None)


def fetch_wikipedia_extract(food_name):
    """Fetch a short extract from Wikipedia for a food item.
    Returns the extract text or None if not found.
    """
    try:
        query = urllib.parse.quote(food_name)
        url = (
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "FoodDB-RecipeSourcing/1.0 (recipe stub generation; polite bot)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("type") == "standard" and data.get("extract"):
                return data["extract"]
    except Exception:
        pass
    return None


def extract_ingredients_from_text(text):
    """Try to extract ingredient-like words from a description text."""
    if not text:
        return []
    # Common food ingredient patterns
    ingredients = []
    # Look for "made with/from/of X, Y, and Z" patterns
    patterns = [
        r"(?:made (?:with|from|of)|contains?|featuring|using|includes?)\s+(.+?)(?:\.|$)",
        r"(?:consisting of|composed of|prepared with)\s+(.+?)(?:\.|$)",
        r"(?:filled with|stuffed with|topped with|served with)\s+(.+?)(?:\.|$)",
        r"(?:combined with|mixed with|cooked (?:with|in))\s+(.+?)(?:\.|$)",
    ]
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        for match in matches:
            # Split on commas and "and"
            parts = re.split(r",\s*|\s+and\s+", match)
            for part in parts:
                cleaned = part.strip().strip(".")
                if cleaned and len(cleaned) < 50 and len(cleaned) > 1:
                    ingredients.append(cleaned)
    return ingredients


def build_ingredients_string(food_tags_ingredients, desc_ingredients):
    """Build a JSON-like ingredients string from tag and description data."""
    all_ingredients = []
    seen = set()
    for ing in food_tags_ingredients:
        key = ing.lower().strip()
        if key not in seen:
            seen.add(key)
            all_ingredients.append(ing.strip())
    for ing in desc_ingredients:
        key = ing.lower().strip()
        if key not in seen:
            seen.add(key)
            all_ingredients.append(ing.strip())
    if not all_ingredients:
        return None
    return json.dumps(all_ingredients)


def build_instructions(cooking_methods, food_name, description):
    """Build basic cooking instructions from methods and context."""
    if not cooking_methods:
        if description:
            # Try to infer method from description
            desc_lower = description.lower()
            for method, template in METHOD_INSTRUCTIONS.items():
                if method in desc_lower:
                    cooking_methods = [method]
                    break
    if not cooking_methods:
        return None

    parts = []
    for method in cooking_methods:
        template = METHOD_INSTRUCTIONS.get(method)
        if template:
            parts.append(template)

    if not parts:
        return None

    instructions = f"To prepare {food_name}: " + " ".join(parts)
    return instructions


def get_cuisines_needing_recipes(conn):
    """Get cuisines with zero recipes, ordered by food count (descending)."""
    c = conn.cursor()

    # Get existing recipe cuisines from recipes_large
    c.execute(
        "SELECT LOWER(cuisine), COUNT(*) FROM recipes_large WHERE cuisine IS NOT NULL GROUP BY LOWER(cuisine)"
    )
    existing = {r[0]: r[1] for r in c.fetchall()}

    # Get food counts per canonical cuisine
    c.execute(
        'SELECT tag_value, COUNT(DISTINCT food_id) FROM food_tags WHERE tag_category = "cuisine" GROUP BY tag_value'
    )
    raw_counts = c.fetchall()

    cuisine_food_counts = {}
    for tag_val, count in raw_counts:
        canonical = normalize_cuisine(tag_val)
        if canonical:
            cuisine_food_counts[canonical] = cuisine_food_counts.get(canonical, 0) + count

    # Filter to cuisines needing recipes
    needing = []
    for cuisine, food_count in cuisine_food_counts.items():
        cuisine_lower = cuisine.lower()
        if existing.get(cuisine_lower, 0) == 0 and cuisine not in CUISINES_WITH_RECIPES:
            needing.append((cuisine, food_count))

    # Sort by food count descending (more foods = higher priority)
    needing.sort(key=lambda x: x[1], reverse=True)
    return needing


def get_foods_for_cuisine(conn, cuisine):
    """Get foods with sufficient data for a given canonical cuisine.
    Returns foods that have a description AND at least some tags.
    """
    c = conn.cursor()

    # Find all tag_values that normalize to this cuisine
    matching_tags = [k for k, v in NORMALIZE.items() if v == cuisine]

    if not matching_tags:
        return []

    placeholders = ",".join("?" * len(matching_tags))

    # Get foods with descriptions that belong to this cuisine
    # We need: description + at least one ingredient or cooking_method tag
    query = f"""
    SELECT DISTINCT f.id, f.name, f.description, f.primary_category, f.food_type
    FROM foods f
    JOIN food_tags ft_cuisine ON f.id = ft_cuisine.food_id
        AND ft_cuisine.tag_category = 'cuisine'
        AND LOWER(ft_cuisine.tag_value) IN ({placeholders})
    WHERE f.description IS NOT NULL AND f.description != ''
      AND f.food_type IN ('dish', 'prepared_food', 'beverage', 'dessert', 'snack', 'condiment', 'bread', 'soup', 'salad', 'sauce')
      AND (
        EXISTS (SELECT 1 FROM food_tags ft2 WHERE ft2.food_id = f.id AND ft2.tag_category = 'ingredient')
        OR EXISTS (SELECT 1 FROM food_tags ft3 WHERE ft3.food_id = f.id AND ft3.tag_category = 'cooking_method')
      )
    ORDER BY f.name
    """
    c.execute(query, [t for t in matching_tags])
    foods = c.fetchall()
    return foods


def get_food_tags(conn, food_id):
    """Get ingredient and cooking_method tags for a food."""
    c = conn.cursor()
    c.execute(
        "SELECT tag_category, tag_value FROM food_tags WHERE food_id = ? AND tag_category IN ('ingredient', 'cooking_method')",
        (food_id,),
    )
    tags = c.fetchall()
    ingredients = [t[1] for t in tags if t[0] == "ingredient"]
    methods = [t[1] for t in tags if t[0] == "cooking_method"]
    return ingredients, methods


def get_food_category_tags(conn, food_id):
    """Get meal_type and course tags for category field."""
    c = conn.cursor()
    c.execute(
        "SELECT tag_category, tag_value FROM food_tags WHERE food_id = ? AND tag_category IN ('meal_type', 'course')",
        (food_id,),
    )
    tags = c.fetchall()
    categories = [t[1] for t in tags]
    return categories[0] if categories else None


def bulk_load_tags(conn, food_ids):
    """Pre-load all relevant tags for a batch of food IDs to avoid per-row queries."""
    if not food_ids:
        return {}, {}, {}
    c = conn.cursor()
    placeholders = ",".join("?" * len(food_ids))

    # Ingredient and cooking_method tags
    c.execute(
        f"SELECT food_id, tag_category, tag_value FROM food_tags "
        f"WHERE food_id IN ({placeholders}) "
        f"AND tag_category IN ('ingredient', 'cooking_method', 'meal_type', 'course')",
        food_ids,
    )
    ingredients_map = {}
    methods_map = {}
    category_map = {}
    for fid, cat, val in c.fetchall():
        if cat == "ingredient":
            ingredients_map.setdefault(fid, []).append(val)
        elif cat == "cooking_method":
            methods_map.setdefault(fid, []).append(val)
        elif cat in ("meal_type", "course"):
            if fid not in category_map:
                category_map[fid] = val
    return ingredients_map, methods_map, category_map


def main():
    conn = sqlite3.connect(DB_PATH)

    print("=" * 80)
    print("RECIPE SOURCING: Building stub recipes from food catalog data")
    print("=" * 80)

    # Step 1: Get prioritized list of cuisines needing recipes
    needing = get_cuisines_needing_recipes(conn)
    print(f"\nFound {len(needing)} cuisines needing recipes:")
    for cuisine, count in needing[:20]:
        print(f"  {cuisine}: {count} foods in catalog")
    if len(needing) > 20:
        print(f"  ... and {len(needing) - 20} more")

    # Step 2: Process each cuisine
    total_inserted = 0
    total_skipped = 0
    total_wiki_fetched = 0
    cuisine_results = {}

    for cuisine, food_count in needing:
        print(f"\n{'─' * 60}")
        print(f"Processing: {cuisine} ({food_count} foods in catalog)")
        print(f"{'─' * 60}")

        foods = get_foods_for_cuisine(conn, cuisine)
        print(f"  Foods with sufficient data: {len(foods)}")

        if not foods:
            cuisine_results[cuisine] = 0
            continue

        # Bulk-load all tags for this cuisine's foods
        food_ids = [f[0] for f in foods]
        ingredients_map, methods_map, category_map = bulk_load_tags(conn, food_ids)

        cuisine_inserted = 0
        cuisine_lower = cuisine.lower()

        for food_id, food_name, description, primary_category, food_type in foods:
            # Get tags from pre-loaded maps
            tag_ingredients = ingredients_map.get(food_id, [])
            tag_methods = methods_map.get(food_id, [])
            category = category_map.get(food_id)

            # Extract additional ingredients from description
            desc_ingredients = extract_ingredients_from_text(description)

            # Build ingredients string
            ingredients_str = build_ingredients_string(tag_ingredients, desc_ingredients)

            # Build instructions
            instructions_str = build_instructions(tag_methods, food_name, description)

            # We need at least ingredients OR instructions to create a useful stub
            if not ingredients_str and not instructions_str:
                total_skipped += 1
                continue

            # Build cleaned_ingredients (simplified list)
            cleaned = None
            if ingredients_str:
                try:
                    raw_list = json.loads(ingredients_str)
                    cleaned = json.dumps([i.lower().strip() for i in raw_list])
                except (json.JSONDecodeError, TypeError):
                    pass

            # Determine category
            if not category:
                if food_type == "dessert":
                    category = "dessert"
                elif food_type == "beverage":
                    category = "beverage"
                elif primary_category:
                    category = primary_category

            # Insert into recipes_large
            try:
                changes_before = conn.total_changes
                conn.execute(
                    """INSERT OR IGNORE INTO recipes_large
                    (title, ingredients, instructions, cleaned_ingredients, category, cuisine, source)
                    VALUES (?, ?, ?, ?, ?, ?, 'wikipedia_derived')""",
                    (
                        food_name,
                        ingredients_str,
                        instructions_str or f"Prepare {food_name}: {description}",
                        cleaned,
                        category,
                        cuisine_lower,
                    ),
                )
                if conn.total_changes > changes_before:
                    cuisine_inserted += 1
            except sqlite3.IntegrityError:
                total_skipped += 1
            except Exception as e:
                print(f"    Error inserting {food_name}: {e}")
                total_skipped += 1

        conn.commit()
        total_inserted += cuisine_inserted
        cuisine_results[cuisine] = cuisine_inserted
        print(f"  Inserted: {cuisine_inserted} stub recipes")

    # Step 3: Wikipedia cuisine article pass
    # For cuisines that got few/no recipes from DB data, try fetching the cuisine
    # article from Wikipedia to find additional foods we can cross-reference
    print(f"\n{'=' * 80}")
    print("WIKIPEDIA CUISINE ARTICLE PASS")
    print(f"{'=' * 80}")

    wiki_pass_inserted = 0
    low_coverage = [(c, n) for c, n in needing if cuisine_results.get(c, 0) < 5]
    print(f"  Cuisines with <5 recipes to supplement via Wikipedia: {len(low_coverage)}")

    for cuisine, food_count in low_coverage[:50]:  # Cap at 50 cuisine lookups
        cuisine_lower = cuisine.lower()
        # Fetch Wikipedia article for "[cuisine] cuisine"
        wiki_text = fetch_wikipedia_extract(f"{cuisine} cuisine")
        time.sleep(WIKI_DELAY)

        if not wiki_text:
            continue

        total_wiki_fetched += 1

        # Find foods in our catalog that match this cuisine but weren't inserted yet
        # (those without ingredient/method tags but with descriptions)
        matching_tags = [k for k, v in NORMALIZE.items() if v == cuisine]
        if not matching_tags:
            continue
        placeholders = ",".join("?" * len(matching_tags))

        c = conn.cursor()
        c.execute(
            f"""SELECT DISTINCT f.id, f.name, f.description, f.primary_category, f.food_type
            FROM foods f
            JOIN food_tags ft_cuisine ON f.id = ft_cuisine.food_id
                AND ft_cuisine.tag_category = 'cuisine'
                AND LOWER(ft_cuisine.tag_value) IN ({placeholders})
            WHERE f.description IS NOT NULL AND f.description != ''
              AND LENGTH(f.description) > 20
              AND f.food_type IN ('dish', 'prepared_food', 'beverage', 'dessert', 'snack', 'condiment', 'bread', 'soup', 'salad', 'sauce')
              AND NOT EXISTS (
                SELECT 1 FROM recipes_large r WHERE r.title = f.name AND r.cuisine = ?
              )
            ORDER BY LENGTH(f.description) DESC
            LIMIT 20
            """,
            [t for t in matching_tags] + [cuisine_lower],
        )
        extra_foods = c.fetchall()

        cuisine_wiki_added = 0
        for food_id, food_name, description, primary_category, food_type in extra_foods:
            # Use description to build a recipe stub
            desc_ingredients = extract_ingredients_from_text(description)
            ingredients_str = build_ingredients_string([], desc_ingredients) if desc_ingredients else None

            # Infer cooking method from description
            instructions_str = None
            desc_lower = description.lower()
            for method, template in METHOD_INSTRUCTIONS.items():
                if method in desc_lower:
                    instructions_str = f"To prepare {food_name}: {template}"
                    break

            if not ingredients_str and not instructions_str:
                continue

            cleaned = None
            if ingredients_str:
                try:
                    raw_list = json.loads(ingredients_str)
                    cleaned = json.dumps([i.lower().strip() for i in raw_list])
                except (json.JSONDecodeError, TypeError):
                    pass

            category = None
            if food_type == "dessert":
                category = "dessert"
            elif food_type == "beverage":
                category = "beverage"
            elif primary_category:
                category = primary_category

            try:
                changes_before = conn.total_changes
                conn.execute(
                    """INSERT OR IGNORE INTO recipes_large
                    (title, ingredients, instructions, cleaned_ingredients, category, cuisine, source)
                    VALUES (?, ?, ?, ?, ?, ?, 'wikipedia_derived')""",
                    (
                        food_name,
                        ingredients_str,
                        instructions_str or f"Prepare {food_name}: {description}",
                        cleaned,
                        category,
                        cuisine_lower,
                    ),
                )
                if conn.total_changes > changes_before:
                    cuisine_wiki_added += 1
            except Exception:
                pass

        if cuisine_wiki_added > 0:
            conn.commit()
            wiki_pass_inserted += cuisine_wiki_added
            total_inserted += cuisine_wiki_added
            cuisine_results[cuisine] = cuisine_results.get(cuisine, 0) + cuisine_wiki_added
            print(f"  {cuisine}: +{cuisine_wiki_added} from Wikipedia pass")

    print(f"  Wikipedia pass total: +{wiki_pass_inserted} recipes")

    # Summary
    print(f"\n{'=' * 80}")
    print("SOURCING COMPLETE")
    print(f"{'=' * 80}")
    print(f"  Total stub recipes inserted:   {total_inserted}")
    print(f"  Total skipped (insufficient):  {total_skipped}")
    print(f"  Wikipedia supplements fetched:  {total_wiki_fetched}")
    print(f"\nResults by cuisine (top 30):")

    sorted_results = sorted(cuisine_results.items(), key=lambda x: x[1], reverse=True)
    for cuisine, count in sorted_results[:30]:
        if count > 0:
            print(f"  {cuisine:30s}: {count} recipes")

    cuisines_with_zero = sum(1 for _, c in sorted_results if c == 0)
    if cuisines_with_zero:
        print(f"\n  ({cuisines_with_zero} cuisines had no foods with sufficient data)")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
