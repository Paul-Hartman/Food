"""
Enrich foods with semantic tags from Wikidata properties + Wikipedia text analysis.

Tag categories produced:
  meal_type        - breakfast, lunch, dinner, snack, dessert, appetizer, etc.
  cuisine          - Japanese, Italian, Mexican, Indian, etc.
  season           - summer, winter, spring, autumn, year-round
  tradition        - Christmas, Thanksgiving, Ramadan, Lunar New Year, etc.
  cooking_method   - fried, baked, grilled, steamed, raw, fermented, etc.
  dietary          - vegetarian, vegan, gluten-free, halal, kosher, dairy-free
  temperature      - hot, cold, warm, frozen, room temperature
  course           - appetizer, main, side, dessert, soup, salad
  flavor_profile   - sweet, savory, spicy, sour, bitter, umami, tangy
  texture          - crispy, creamy, chewy, crunchy, smooth, flaky
  ingredient       - (linked to food_ingredients_wiki table too)
  region           - East Asia, South Asia, Mediterranean, etc.
  occasion         - party, picnic, comfort food, hangover, wedding, funeral
  time_of_day      - morning, afternoon, evening, late night
  preparation_time - quick (<30min), medium (30-60min), slow (1hr+)
  served_with      - paired foods (also in food_pairings table)

Usage:
    python enrich_food_tags.py --phase wikidata    # SPARQL enrichment
    python enrich_food_tags.py --phase text         # Description text extraction
    python enrich_food_tags.py --phase all          # Both phases
"""

import argparse
import re
import sqlite3
import time

import requests

DB_PATH = "food.db"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "LotusEaterFoodApp/1.0 (paul@example.com) python-requests",
    "Accept": "application/json",
}


def sparql_query(query, retries=3):
    """Execute SPARQL query against Wikidata."""
    for attempt in range(retries):
        try:
            resp = requests.get(
                WIKIDATA_SPARQL,
                params={"query": query, "format": "json"},
                headers=HEADERS,
                timeout=120,
            )
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 60))
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 500 or resp.status_code == 504:
                print(f"  Server error {resp.status_code}, retrying...")
                time.sleep(10 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()["results"]["bindings"]
        except requests.exceptions.RequestException as e:
            print(f"  SPARQL error (attempt {attempt+1}/{retries}): {e}")
            time.sleep(5 * (attempt + 1))
    return []


# ============================================================================
# PHASE 1: WIKIDATA SPARQL ENRICHMENT
# ============================================================================

def enrich_ingredients_from_wikidata(conn, batch_size=80):
    """Fetch ingredient data (P186 = made from material) for foods with QIDs."""
    print("\n--- Enriching ingredients from Wikidata (P186) ---")
    cursor = conn.cursor()

    qids = cursor.execute(
        "SELECT id, wikidata_qid FROM foods WHERE wikidata_qid IS NOT NULL AND wikidata_qid != ''"
    ).fetchall()

    total_inserted = 0
    for i in range(0, len(qids), batch_size):
        batch = qids[i:i + batch_size]
        values_clause = " ".join(f"wd:{qid}" for _, qid in batch)
        qid_to_id = {qid: fid for fid, qid in batch}

        query = f"""
        SELECT ?item ?ingredientLabel ?ingredient WHERE {{
          VALUES ?item {{ {values_clause} }}
          ?item wdt:P186 ?ingredient .
          ?ingredient rdfs:label ?ingredientLabel . FILTER(LANG(?ingredientLabel) = "en")
        }}
        """

        results = sparql_query(query)
        for row in results:
            item_uri = row.get("item", {}).get("value", "")
            qid = item_uri.split("/")[-1]
            food_id = qid_to_id.get(qid)
            ing_name = row.get("ingredientLabel", {}).get("value", "")
            ing_qid = row.get("ingredient", {}).get("value", "").split("/")[-1]

            if food_id and ing_name and not ing_name.startswith("Q"):
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO food_ingredients_wiki (food_id, ingredient_name, wikidata_qid) VALUES (?, ?, ?)",
                        (food_id, ing_name, ing_qid)
                    )
                    cursor.execute(
                        "INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, 'ingredient', ?, 'wikidata')",
                        (food_id, ing_name.lower())
                    )
                    total_inserted += cursor.rowcount
                except sqlite3.IntegrityError:
                    pass

        conn.commit()
        if (i // batch_size) % 10 == 0:
            print(f"  Processed {i + len(batch)}/{len(qids)} foods, {total_inserted} ingredient tags so far")
        time.sleep(1)

    print(f"  [OK] {total_inserted} ingredient tags added")
    return total_inserted


def enrich_cuisine_from_wikidata(conn, batch_size=80):
    """Fetch cuisine (P2012) and country of origin (P495) for food classification."""
    print("\n--- Enriching cuisine from Wikidata (P2012, P495) ---")
    cursor = conn.cursor()

    qids = cursor.execute(
        "SELECT id, wikidata_qid FROM foods WHERE wikidata_qid IS NOT NULL AND wikidata_qid != ''"
    ).fetchall()

    total_inserted = 0
    for i in range(0, len(qids), batch_size):
        batch = qids[i:i + batch_size]
        values_clause = " ".join(f"wd:{qid}" for _, qid in batch)
        qid_to_id = {qid: fid for fid, qid in batch}

        query = f"""
        SELECT ?item ?cuisineLabel ?countryLabel ?regionLabel WHERE {{
          VALUES ?item {{ {values_clause} }}
          OPTIONAL {{ ?item wdt:P2012 ?cuisine . ?cuisine rdfs:label ?cuisineLabel . FILTER(LANG(?cuisineLabel) = "en") }}
          OPTIONAL {{ ?item wdt:P495 ?country . ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel) = "en") }}
          OPTIONAL {{ ?item wdt:P131 ?region . ?region rdfs:label ?regionLabel . FILTER(LANG(?regionLabel) = "en") }}
        }}
        """

        results = sparql_query(query)
        for row in results:
            item_uri = row.get("item", {}).get("value", "")
            qid = item_uri.split("/")[-1]
            food_id = qid_to_id.get(qid)
            if not food_id:
                continue

            cuisine = row.get("cuisineLabel", {}).get("value", "")
            country = row.get("countryLabel", {}).get("value", "")
            region = row.get("regionLabel", {}).get("value", "")

            for tag_cat, val in [("cuisine", cuisine), ("cuisine", country), ("region", region)]:
                if val and not val.startswith("Q"):
                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, ?, ?, 'wikidata')",
                            (food_id, tag_cat, val)
                        )
                        total_inserted += cursor.rowcount
                    except sqlite3.IntegrityError:
                        pass

        conn.commit()
        if (i // batch_size) % 10 == 0:
            print(f"  Processed {i + len(batch)}/{len(qids)} foods, {total_inserted} cuisine/region tags")
        time.sleep(1)

    print(f"  [OK] {total_inserted} cuisine/region tags added")
    return total_inserted


def enrich_served_with_from_wikidata(conn, batch_size=80):
    """Fetch 'typically served with' (P1909) and 'has part' (P527) relationships."""
    print("\n--- Enriching pairings from Wikidata (P1909, P527) ---")
    cursor = conn.cursor()

    qids = cursor.execute(
        "SELECT id, wikidata_qid FROM foods WHERE wikidata_qid IS NOT NULL AND wikidata_qid != ''"
    ).fetchall()

    total_inserted = 0
    for i in range(0, len(qids), batch_size):
        batch = qids[i:i + batch_size]
        values_clause = " ".join(f"wd:{qid}" for _, qid in batch)
        qid_to_id = {qid: fid for fid, qid in batch}

        # P1909 = typically served with, P527 = has part (components)
        query = f"""
        SELECT ?item ?pairedLabel ?paired ?rel WHERE {{
          VALUES ?item {{ {values_clause} }}
          {{
            ?item wdt:P1909 ?paired .
            BIND("served_with" AS ?rel)
          }} UNION {{
            ?item wdt:P527 ?paired .
            BIND("component" AS ?rel)
          }}
          ?paired rdfs:label ?pairedLabel . FILTER(LANG(?pairedLabel) = "en")
        }}
        """

        results = sparql_query(query)
        for row in results:
            item_uri = row.get("item", {}).get("value", "")
            qid = item_uri.split("/")[-1]
            food_id = qid_to_id.get(qid)
            paired_name = row.get("pairedLabel", {}).get("value", "")
            rel_type = row.get("rel", {}).get("value", "served_with")

            if food_id and paired_name and not paired_name.startswith("Q"):
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO food_pairings (food_id, paired_food_name, pairing_type, source) VALUES (?, ?, ?, 'wikidata')",
                        (food_id, paired_name, rel_type)
                    )
                    cursor.execute(
                        "INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, 'served_with', ?, 'wikidata')",
                        (food_id, paired_name.lower())
                    )
                    total_inserted += cursor.rowcount
                except sqlite3.IntegrityError:
                    pass

        conn.commit()
        if (i // batch_size) % 10 == 0:
            print(f"  Processed {i + len(batch)}/{len(qids)} foods, {total_inserted} pairing tags")
        time.sleep(1)

    print(f"  [OK] {total_inserted} pairing tags added")
    return total_inserted


def enrich_occasions_from_wikidata(conn, batch_size=80):
    """Fetch occasion/use (P366), significant event (P793), time of year properties."""
    print("\n--- Enriching occasions from Wikidata (P366, P793, P3080) ---")
    cursor = conn.cursor()

    qids = cursor.execute(
        "SELECT id, wikidata_qid FROM foods WHERE wikidata_qid IS NOT NULL AND wikidata_qid != ''"
    ).fetchall()

    total_inserted = 0
    for i in range(0, len(qids), batch_size):
        batch = qids[i:i + batch_size]
        values_clause = " ".join(f"wd:{qid}" for _, qid in batch)
        qid_to_id = {qid: fid for fid, qid in batch}

        query = f"""
        SELECT ?item ?useLabel ?eventLabel ?seasonLabel WHERE {{
          VALUES ?item {{ {values_clause} }}
          OPTIONAL {{ ?item wdt:P366 ?use . ?use rdfs:label ?useLabel . FILTER(LANG(?useLabel) = "en") }}
          OPTIONAL {{ ?item wdt:P793 ?event . ?event rdfs:label ?eventLabel . FILTER(LANG(?eventLabel) = "en") }}
          OPTIONAL {{ ?item wdt:P3080 ?season . ?season rdfs:label ?seasonLabel . FILTER(LANG(?seasonLabel) = "en") }}
        }}
        """

        results = sparql_query(query)
        for row in results:
            item_uri = row.get("item", {}).get("value", "")
            qid = item_uri.split("/")[-1]
            food_id = qid_to_id.get(qid)
            if not food_id:
                continue

            use_val = row.get("useLabel", {}).get("value", "")
            event_val = row.get("eventLabel", {}).get("value", "")
            season_val = row.get("seasonLabel", {}).get("value", "")

            for cat, val in [("occasion", use_val), ("tradition", event_val), ("season", season_val)]:
                if val and not val.startswith("Q"):
                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, ?, ?, 'wikidata')",
                            (food_id, cat, val)
                        )
                        total_inserted += cursor.rowcount
                    except sqlite3.IntegrityError:
                        pass

        conn.commit()
        if (i // batch_size) % 10 == 0:
            print(f"  Processed {i + len(batch)}/{len(qids)} foods, {total_inserted} occasion/tradition tags")
        time.sleep(1)

    print(f"  [OK] {total_inserted} occasion/tradition tags added")
    return total_inserted


def enrich_classification_from_wikidata(conn, batch_size=80):
    """Fetch subclass hierarchy (P279) and instance-of (P31) for deep classification."""
    print("\n--- Enriching classification from Wikidata (P31, P279) ---")
    cursor = conn.cursor()

    qids = cursor.execute(
        "SELECT id, wikidata_qid FROM foods WHERE wikidata_qid IS NOT NULL AND wikidata_qid != ''"
    ).fetchall()

    total_inserted = 0
    for i in range(0, len(qids), batch_size):
        batch = qids[i:i + batch_size]
        values_clause = " ".join(f"wd:{qid}" for _, qid in batch)
        qid_to_id = {qid: fid for fid, qid in batch}

        query = f"""
        SELECT ?item ?classLabel WHERE {{
          VALUES ?item {{ {values_clause} }}
          {{ ?item wdt:P31 ?class }} UNION {{ ?item wdt:P279 ?class }}
          ?class rdfs:label ?classLabel . FILTER(LANG(?classLabel) = "en")
        }}
        """

        results = sparql_query(query)
        for row in results:
            item_uri = row.get("item", {}).get("value", "")
            qid = item_uri.split("/")[-1]
            food_id = qid_to_id.get(qid)
            class_label = row.get("classLabel", {}).get("value", "")

            if food_id and class_label and not class_label.startswith("Q"):
                # Map classification to useful tag categories
                tag_cat, tag_val = _classify_wikidata_class(class_label)
                if tag_cat:
                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, ?, ?, 'wikidata')",
                            (food_id, tag_cat, tag_val)
                        )
                        total_inserted += cursor.rowcount
                    except sqlite3.IntegrityError:
                        pass

        conn.commit()
        if (i // batch_size) % 10 == 0:
            print(f"  Processed {i + len(batch)}/{len(qids)} foods, {total_inserted} classification tags")
        time.sleep(1)

    print(f"  [OK] {total_inserted} classification tags added")
    return total_inserted


def _classify_wikidata_class(class_label):
    """Map a Wikidata class label to a tag category + value."""
    cl = class_label.lower()

    # Meal type mappings
    meal_keywords = {
        "breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner",
        "supper": "supper", "brunch": "brunch", "snack": "snack",
        "dessert": "dessert", "appetizer": "appetizer", "starter": "appetizer",
        "side dish": "side dish", "main course": "main course",
        "street food": "street food", "fast food": "fast food",
        "finger food": "finger food", "comfort food": "comfort food",
    }
    for kw, val in meal_keywords.items():
        if kw in cl:
            return "meal_type", val

    # Cooking method
    method_keywords = {
        "fried": "fried", "deep-fried": "deep-fried", "baked": "baked",
        "grilled": "grilled", "steamed": "steamed", "boiled": "boiled",
        "roasted": "roasted", "smoked": "smoked", "raw": "raw",
        "fermented": "fermented", "pickled": "pickled", "cured": "cured",
        "braised": "braised", "stir-fried": "stir-fried", "sauteed": "sauteed",
        "poached": "poached", "blanched": "blanched", "dried": "dried",
        "marinated": "marinated", "stewed": "stewed",
    }
    for kw, val in method_keywords.items():
        if kw in cl:
            return "cooking_method", val

    # Course type
    course_keywords = {
        "soup": "soup", "salad": "salad", "sandwich": "sandwich",
        "stew": "stew", "curry": "curry", "pie": "pie", "cake": "cake",
        "bread": "bread", "pasta": "pasta", "noodle": "noodle",
        "rice dish": "rice dish", "dumpling": "dumpling", "kebab": "kebab",
        "sausage": "sausage", "cheese": "cheese", "sauce": "sauce",
        "condiment": "condiment", "confectionery": "confectionery",
        "pastry": "pastry", "porridge": "porridge", "flatbread": "flatbread",
        "beverage": "beverage", "cocktail": "cocktail", "beer": "beer",
        "wine": "wine", "tea": "tea", "coffee": "coffee", "juice": "juice",
        "smoothie": "smoothie", "spirit": "spirit", "liqueur": "liqueur",
    }
    for kw, val in course_keywords.items():
        if kw in cl:
            return "course", val

    # Dietary
    dietary_keywords = {
        "vegetarian": "vegetarian", "vegan": "vegan",
        "gluten-free": "gluten-free", "halal": "halal", "kosher": "kosher",
        "dairy-free": "dairy-free", "organic": "organic",
    }
    for kw, val in dietary_keywords.items():
        if kw in cl:
            return "dietary", val

    # Food type (broad)
    type_keywords = {
        "fruit": "fruit", "vegetable": "vegetable", "meat": "meat",
        "seafood": "seafood", "fish": "fish", "poultry": "poultry",
        "grain": "grain", "legume": "legume", "nut": "nut",
        "dairy": "dairy", "egg": "egg", "herb": "herb", "spice": "spice",
        "mushroom": "mushroom", "seaweed": "seaweed",
    }
    for kw, val in type_keywords.items():
        if kw in cl:
            return "food_type", val

    return None, None


# ============================================================================
# PHASE 2: TEXT-BASED TAG EXTRACTION FROM DESCRIPTIONS
# ============================================================================

# Keyword patterns for each tag category
TAG_PATTERNS = {
    "meal_type": {
        "breakfast": r"\b(breakfast|morning meal|morning food)\b",
        "lunch": r"\b(lunch|lunchtime|midday meal|noon meal)\b",
        "dinner": r"\b(dinner|supper|evening meal)\b",
        "snack": r"\b(snack|nibble|between.?meal|finger food)\b",
        "dessert": r"\b(dessert|sweet course|after.?dinner|sweet treat)\b",
        "appetizer": r"\b(appetizer|starter|hors d.oeuvre|antipast[oi]|entr[eé]e|amuse.?bouche|meze|tapas)\b",
        "side dish": r"\b(side dish|accompaniment|garnish|side order)\b",
        "street food": r"\b(street food|street vendor|food stall|hawker)\b",
        "brunch": r"\b(brunch)\b",
    },
    "cooking_method": {
        "fried": r"\b(fried|frying|pan.?fried)\b",
        "deep-fried": r"\b(deep.?fr[iy]|battered and fried)\b",
        "baked": r"\b(baked|baking|oven.?baked)\b",
        "grilled": r"\b(grilled|grilling|barbecue[d]?|bbq|char.?grilled|broiled)\b",
        "steamed": r"\b(steamed|steaming)\b",
        "boiled": r"\b(boiled|boiling|simmered|simmering)\b",
        "roasted": r"\b(roasted|roasting|spit.?roast)\b",
        "smoked": r"\b(smoked|smoking|smoke.?cured)\b",
        "raw": r"\b(raw|uncooked|fresh|ceviche|tartare|sashimi)\b",
        "fermented": r"\b(fermented|fermentation|cultured|lacto.?ferment)\b",
        "pickled": r"\b(pickled|pickling|brined|vinegar.?cured)\b",
        "braised": r"\b(braised|braising|pot.?roast)\b",
        "stir-fried": r"\b(stir.?fr[iy]|wok.?fried)\b",
        "stewed": r"\b(stewed|stewing|slow.?cook)\b",
        "poached": r"\b(poached|poaching)\b",
        "cured": r"\b(cured|curing|salt.?cured|dry.?cured)\b",
        "dried": r"\b(dried|sun.?dried|air.?dried|dehydrated)\b",
        "marinated": r"\b(marinated|marinating|marinade)\b",
    },
    "flavor_profile": {
        "sweet": r"\b(sweet|sugary|honey|syrup|caramel|candy)\b",
        "savory": r"\b(savory|savoury|umami|salty)\b",
        "spicy": r"\b(spicy|hot|chili|chilli|pepper|piquant|fiery)\b",
        "sour": r"\b(sour|tart|tangy|acidic|vinegar)\b",
        "bitter": r"\b(bitter|bittersweet)\b",
        "rich": r"\b(rich|creamy|buttery|decadent)\b",
        "mild": r"\b(mild|subtle|delicate|light flavor)\b",
        "smoky": r"\b(smoky|smoke.?flavor)\b",
    },
    "texture": {
        "crispy": r"\b(crispy|crunchy|crisp)\b",
        "creamy": r"\b(creamy|smooth|velvety|silky)\b",
        "chewy": r"\b(chewy|chewiness|elastic|springy)\b",
        "flaky": r"\b(flaky|flakey|layered|laminated)\b",
        "soft": r"\b(soft|tender|melt.?in.?mouth|fluffy)\b",
        "thick": r"\b(thick|hearty|chunky|dense)\b",
        "thin": r"\b(thin|wafer|paper.?thin|light)\b",
        "moist": r"\b(moist|juicy|succulent)\b",
    },
    "temperature": {
        "hot": r"\b(hot|warm|heated|piping hot)\b",
        "cold": r"\b(cold|chilled|iced|frozen|cool)\b",
        "room temperature": r"\b(room temperature|ambient)\b",
    },
    "season": {
        "summer": r"\b(summer|summertime|hot weather|warm season)\b",
        "winter": r"\b(winter|wintertime|cold weather|cold season|warming)\b",
        "spring": r"\b(spring|springtime|vernal)\b",
        "autumn": r"\b(autumn|fall|harvest|october|november)\b",
    },
    "tradition": {
        "Christmas": r"\b(christmas|xmas|yule|holiday season|advent)\b",
        "Easter": r"\b(easter|lent|lenten|paschal)\b",
        "Thanksgiving": r"\b(thanksgiving)\b",
        "Ramadan": r"\b(ramadan|iftar|suhoor|eid)\b",
        "Lunar New Year": r"\b(lunar new year|chinese new year|tet|seollal)\b",
        "Diwali": r"\b(diwali|deepavali)\b",
        "Hanukkah": r"\b(hanukkah|chanukah)\b",
        "Midsummer": r"\b(midsummer|solstice)\b",
        "Day of the Dead": r"\b(day of the dead|d[ií]a de los muertos)\b",
        "wedding": r"\b(wedding|bridal|marriage|nuptial)\b",
        "funeral": r"\b(funeral|mourning|memorial|wake)\b",
        "New Year": r"\b(new year|new year's|hogmanay)\b",
        "harvest festival": r"\b(harvest|harvest festival|sukkot)\b",
        "religious": r"\b(religious|ritual|sacred|offering|ceremonial|temple)\b",
        "national day": r"\b(national day|independence day|national holiday)\b",
        "carnival": r"\b(carnival|carnivale|mardi gras|fasching)\b",
    },
    "occasion": {
        "party": r"\b(party|parties|celebration|festive|gathering)\b",
        "picnic": r"\b(picnic|outdoor|al fresco)\b",
        "comfort food": r"\b(comfort food|soul food|homestyle|homemade|grandmother|grandma)\b",
        "hangover": r"\b(hangover|morning after)\b",
        "children": r"\b(children|kids|child|school lunch)\b",
        "formal": r"\b(formal|elegant|fine dining|gourmet|haute)\b",
    },
    "dietary": {
        "vegetarian": r"\b(vegetarian|meatless|meat.?free)\b",
        "vegan": r"\b(vegan|plant.?based|dairy.?free and egg.?free)\b",
        "gluten-free": r"\b(gluten.?free|celiac|coeliac)\b",
        "dairy-free": r"\b(dairy.?free|lactose.?free|non.?dairy)\b",
        "halal": r"\b(halal)\b",
        "kosher": r"\b(kosher|pareve|parve)\b",
    },
    "time_of_day": {
        "morning": r"\b(morning|dawn|early|a\.m\.)\b",
        "afternoon": r"\b(afternoon|midday|noon|tea time)\b",
        "evening": r"\b(evening|dusk|p\.m\.)\b",
        "late night": r"\b(late night|midnight|after hours|late.?night)\b",
    },
}

# Additional cuisine patterns from description text
CUISINE_PATTERNS = {
    "Japanese": r"\b(japan|japanese|tokyo|osaka|nihon)\b",
    "Chinese": r"\b(chin(?:a|ese)|beijing|cantonese|sichuan|szechuan|hunan|shanghai|guangdong|mandarin)\b",
    "Korean": r"\b(korea[n]?|seoul)\b",
    "Thai": r"\b(thai|bangkok|siamese)\b",
    "Vietnamese": r"\b(vietnam|vietnamese|hanoi|saigon)\b",
    "Indian": r"\b(india[n]?|hindi|punjab|tamil|bengal|kerala|gujarati|rajasthani|mughlai)\b",
    "Italian": r"\b(ital(?:y|ian)|rome|naples|sicil|tuscan|roman|neapolitan|venetian)\b",
    "French": r"\b(french|france|paris|provenc|alsatian|normandy|breton|lyonnaise)\b",
    "Mexican": r"\b(mexic(?:o|an)|oaxaca[n]?|yucatan|jalisco)\b",
    "Spanish": r"\b(spain|spanish|catalan|andalusi|basque|galician|castilian)\b",
    "Greek": r"\b(greek|greece|athen|hellenic|cretan)\b",
    "Turkish": r"\b(turk(?:ey|ish)|ottoman|anatolian|istanbul)\b",
    "Middle Eastern": r"\b(middle east|levant|arab|persian|iranian)\b",
    "Mediterranean": r"\b(mediterranean)\b",
    "African": r"\b(african|west african|east african|north african|ethiopian|nigerian|moroccan|senegalese|ghanaian)\b",
    "Caribbean": r"\b(caribbean|jamaican|cuban|trinidadian|creole)\b",
    "Latin American": r"\b(latin american|south american|peruvian|brazilian|colombian|argentine|chilean)\b",
    "German": r"\b(german|bavarian|austria[n]?|swiss|alsace)\b",
    "British": r"\b(british|english|scottish|welsh|irish|uk)\b",
    "Scandinavian": r"\b(scandinavian|swedish|norwegian|danish|finnish|nordic|icelandic)\b",
    "Southeast Asian": r"\b(southeast asia[n]?|malay|indonesian|filipino|burmese|cambodian|laotian|singaporean)\b",
    "Central Asian": r"\b(central asia[n]?|uzbek|kazakh|turkmen|tajik|kyrgyz)\b",
    "Eastern European": r"\b(eastern europe|polish|russian|ukrainian|hungarian|czech|romanian|bulgarian|serbian|croatian)\b",
    "Polynesian": r"\b(polynesian|hawaiian|samoan|maori)\b",
    "Jewish": r"\b(jewish|ashkenazi|sephardi|israeli)\b",
    "Cajun/Creole": r"\b(cajun|creole|louisiana[n]?|bayou)\b",
    "Southern US": r"\b(southern|soul food|dixie|appalachian)\b",
    "Tex-Mex": r"\b(tex.?mex)\b",
}


def extract_tags_from_descriptions(conn, batch_size=1000):
    """Extract semantic tags from food descriptions using keyword patterns."""
    print("\n--- Extracting tags from descriptions ---")
    cursor = conn.cursor()

    total_foods = cursor.execute(
        "SELECT COUNT(*) FROM foods WHERE description IS NOT NULL AND description != ''"
    ).fetchone()[0]
    print(f"  {total_foods} foods with descriptions to process")

    offset = 0
    total_tags = 0

    while offset < total_foods:
        rows = cursor.execute(
            """SELECT id, name, description, food_type, primary_category
               FROM foods
               WHERE description IS NOT NULL AND description != ''
               ORDER BY id
               LIMIT ? OFFSET ?""",
            (batch_size, offset),
        ).fetchall()

        if not rows:
            break

        for food_id, name, desc, food_type, primary_cat in rows:
            text = f"{name} {desc}".lower()

            # Extract from keyword patterns
            for tag_category, patterns in TAG_PATTERNS.items():
                for tag_value, pattern in patterns.items():
                    if re.search(pattern, text, re.IGNORECASE):
                        confidence = 0.9 if re.search(pattern, desc.lower()) else 0.6
                        try:
                            cursor.execute(
                                """INSERT OR IGNORE INTO food_tags
                                   (food_id, tag_category, tag_value, confidence, source)
                                   VALUES (?, ?, ?, ?, 'text_analysis')""",
                                (food_id, tag_category, tag_value, confidence),
                            )
                            total_tags += cursor.rowcount
                        except sqlite3.IntegrityError:
                            pass

            # Extract cuisine patterns
            for cuisine, pattern in CUISINE_PATTERNS.items():
                if re.search(pattern, text, re.IGNORECASE):
                    try:
                        cursor.execute(
                            """INSERT OR IGNORE INTO food_tags
                               (food_id, tag_category, tag_value, confidence, source)
                               VALUES (?, 'cuisine', ?, 0.8, 'text_analysis')""",
                            (food_id, cuisine),
                        )
                        total_tags += cursor.rowcount
                    except sqlite3.IntegrityError:
                        pass

        conn.commit()
        offset += batch_size
        print(f"  Processed {min(offset, total_foods)}/{total_foods} foods, {total_tags} tags extracted")

    print(f"  [OK] {total_tags} tags from text analysis")
    return total_tags


def tag_from_existing_metadata(conn):
    """Generate tags from existing food metadata (food_type, primary_category, culture links)."""
    print("\n--- Tagging from existing metadata ---")
    cursor = conn.cursor()
    total = 0

    # Tag from primary_category
    rows = cursor.execute(
        "SELECT id, food_type, primary_category FROM foods WHERE primary_category IS NOT NULL"
    ).fetchall()

    category_to_tags = {
        "soup": [("course", "soup")],
        "salad": [("course", "salad")],
        "sandwich": [("course", "sandwich")],
        "bread": [("course", "bread"), ("food_type", "grain")],
        "pasta": [("course", "pasta"), ("food_type", "grain")],
        "noodle": [("course", "noodle"), ("food_type", "grain")],
        "rice": [("course", "rice dish"), ("food_type", "grain")],
        "dessert": [("meal_type", "dessert"), ("flavor_profile", "sweet")],
        "confectionery": [("meal_type", "snack"), ("flavor_profile", "sweet")],
        "dairy": [("food_type", "dairy")],
        "meat": [("food_type", "meat")],
        "seafood": [("food_type", "seafood")],
        "vegetable": [("food_type", "vegetable")],
        "fruit": [("food_type", "fruit")],
        "spice": [("food_type", "spice")],
        "condiment": [("course", "condiment")],
        "sauce": [("course", "sauce")],
        "beverage": [("meal_type", "beverage")],
        "alcohol": [("meal_type", "beverage"), ("dietary", "contains alcohol")],
        "hot_drink": [("meal_type", "beverage"), ("temperature", "hot")],
        "baked_good": [("cooking_method", "baked")],
        "fermented": [("cooking_method", "fermented")],
        "grilled": [("cooking_method", "grilled")],
        "street_food": [("meal_type", "street food")],
        "fast_food": [("meal_type", "fast food")],
        "breakfast": [("meal_type", "breakfast")],
        "porridge": [("meal_type", "breakfast"), ("course", "porridge"), ("temperature", "hot")],
        "pizza": [("course", "pizza"), ("meal_type", "dinner")],
        "sushi": [("course", "sushi"), ("cuisine", "Japanese")],
        "mexican": [("cuisine", "Mexican")],
        "curry": [("course", "curry")],
        "dumpling": [("course", "dumpling")],
        "dim_sum": [("course", "dim sum"), ("cuisine", "Chinese")],
        "pastry": [("course", "pastry"), ("cooking_method", "baked")],
        "vegetarian": [("dietary", "vegetarian")],
    }

    for food_id, food_type, primary_cat in rows:
        tags = category_to_tags.get(primary_cat, [])
        # Also tag food_type
        if food_type == "beverage":
            tags.append(("meal_type", "beverage"))
        elif food_type == "condiment":
            tags.append(("course", "condiment"))

        for tag_cat, tag_val in tags:
            try:
                cursor.execute(
                    """INSERT OR IGNORE INTO food_tags
                       (food_id, tag_category, tag_value, confidence, source)
                       VALUES (?, ?, ?, 1.0, 'metadata')""",
                    (food_id, tag_cat, tag_val),
                )
                total += cursor.rowcount
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    print(f"  [OK] {total} tags from existing metadata")

    # Tag cuisine from culture links
    culture_tags = cursor.execute("""
        SELECT fco.food_id, c.name, c.region
        FROM food_culture_origins fco
        JOIN cultures c ON c.id = fco.culture_id
    """).fetchall()

    culture_total = 0
    for food_id, culture_name, region in culture_tags:
        for cat, val in [("cuisine", culture_name), ("region", region)]:
            if val:
                try:
                    cursor.execute(
                        """INSERT OR IGNORE INTO food_tags
                           (food_id, tag_category, tag_value, confidence, source)
                           VALUES (?, ?, ?, 1.0, 'metadata')""",
                        (food_id, cat, val),
                    )
                    culture_total += cursor.rowcount
                except sqlite3.IntegrityError:
                    pass

    conn.commit()
    print(f"  [OK] {culture_total} cuisine/region tags from culture links")
    return total + culture_total


def link_meal_types(conn):
    """Populate food_meal_types junction from food_tags meal_type entries."""
    print("\n--- Linking foods to meal_types table ---")
    cursor = conn.cursor()

    # Get meal type IDs
    meal_types = cursor.execute("SELECT id, slug, name FROM meal_types").fetchall()
    mt_map = {}
    for mt_id, slug, name in meal_types:
        mt_map[slug] = mt_id
        mt_map[name.lower()] = mt_id

    # Get all meal_type tags
    tags = cursor.execute(
        "SELECT food_id, tag_value FROM food_tags WHERE tag_category = 'meal_type'"
    ).fetchall()

    total = 0
    for food_id, tag_value in tags:
        mt_id = mt_map.get(tag_value.lower()) or mt_map.get(tag_value.replace(" ", "_").lower())
        if mt_id:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO food_meal_types (food_id, meal_type_id) VALUES (?, ?)",
                    (food_id, mt_id),
                )
                total += cursor.rowcount
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    print(f"  [OK] {total} food-meal_type links created")
    return total


def update_food_dietary_flags(conn):
    """Update is_vegetarian, is_vegan, is_gluten_free on foods table from tags."""
    print("\n--- Updating dietary flags on foods ---")
    cursor = conn.cursor()

    for flag, tag_value in [
        ("is_vegetarian", "vegetarian"),
        ("is_vegan", "vegan"),
        ("is_gluten_free", "gluten-free"),
    ]:
        cursor.execute(f"""
            UPDATE foods SET {flag} = 1
            WHERE id IN (
                SELECT food_id FROM food_tags
                WHERE tag_category = 'dietary' AND tag_value = ?
            )
        """, (tag_value,))
        print(f"  {flag}: {cursor.rowcount} foods updated")

    conn.commit()


def print_stats(conn):
    """Print comprehensive tag stats."""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("FOOD TAG STATISTICS")
    print("=" * 60)

    total = cursor.execute("SELECT COUNT(*) FROM food_tags").fetchone()[0]
    foods_tagged = cursor.execute("SELECT COUNT(DISTINCT food_id) FROM food_tags").fetchone()[0]
    total_foods = cursor.execute("SELECT COUNT(*) FROM foods").fetchone()[0]

    print(f"\nTotal tags: {total:,}")
    print(f"Foods with at least 1 tag: {foods_tagged:,} / {total_foods:,} ({100*foods_tagged//total_foods}%)")

    print("\n--- Tags by category ---")
    rows = cursor.execute("""
        SELECT tag_category, COUNT(*) as cnt, COUNT(DISTINCT food_id) as foods
        FROM food_tags GROUP BY tag_category ORDER BY cnt DESC
    """).fetchall()
    for cat, cnt, foods in rows:
        print(f"  {cat:20s}: {cnt:>6,} tags across {foods:>6,} foods")

    print("\n--- Top values per category ---")
    for cat, _, _ in rows[:12]:
        top = cursor.execute("""
            SELECT tag_value, COUNT(*) as cnt FROM food_tags
            WHERE tag_category = ? GROUP BY tag_value ORDER BY cnt DESC LIMIT 5
        """, (cat,)).fetchall()
        vals = ", ".join(f"{v}({c})" for v, c in top)
        print(f"  {cat}: {vals}")

    print("\n--- Meal type distribution ---")
    mt_rows = cursor.execute("""
        SELECT mt.name, COUNT(*) as cnt
        FROM food_meal_types fmt
        JOIN meal_types mt ON mt.id = fmt.meal_type_id
        GROUP BY mt.id ORDER BY cnt DESC
    """).fetchall()
    for name, cnt in mt_rows:
        print(f"  {name}: {cnt:,}")

    ings = cursor.execute("SELECT COUNT(*) FROM food_ingredients_wiki").fetchone()[0]
    pairs = cursor.execute("SELECT COUNT(*) FROM food_pairings").fetchone()[0]
    print(f"\nIngredient links: {ings:,}")
    print(f"Food pairings: {pairs:,}")
    print("=" * 60)


def run_wikidata_enrichment(conn):
    """Run all Wikidata SPARQL enrichment queries."""
    print("\n" + "=" * 60)
    print("PHASE 1: WIKIDATA SPARQL ENRICHMENT")
    print("=" * 60)

    enrich_ingredients_from_wikidata(conn)
    enrich_cuisine_from_wikidata(conn)
    enrich_served_with_from_wikidata(conn)
    enrich_occasions_from_wikidata(conn)
    enrich_classification_from_wikidata(conn)


def run_text_enrichment(conn):
    """Run text-based tag extraction."""
    print("\n" + "=" * 60)
    print("PHASE 2: TEXT-BASED TAG EXTRACTION")
    print("=" * 60)

    tag_from_existing_metadata(conn)
    extract_tags_from_descriptions(conn)
    link_meal_types(conn)
    update_food_dietary_flags(conn)


def main():
    parser = argparse.ArgumentParser(description="Enrich foods with semantic tags")
    parser.add_argument("--phase", choices=["wikidata", "text", "all"], default="all")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        if args.phase in ("wikidata", "all"):
            run_wikidata_enrichment(conn)

        if args.phase in ("text", "all"):
            run_text_enrichment(conn)

        print_stats(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
