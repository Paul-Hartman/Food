"""
Import food data from Wikidata SPARQL + Wikipedia API.

Modes:
  --mode wikidata     Bulk import foods via Wikidata SPARQL queries
  --mode categories   Walk Wikipedia category trees for additional foods

Usage:
    python import_wikipedia_foods.py --mode wikidata
    python import_wikipedia_foods.py --mode categories
    python import_wikipedia_foods.py --mode all
"""

import argparse
import json
import re
import sqlite3
import time
import urllib.parse
from datetime import datetime

import requests

DB_PATH = "food.db"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Be polite to Wikimedia
HEADERS = {
    "User-Agent": "LotusEaterFoodApp/1.0 (paul@example.com) python-requests",
    "Accept": "application/json",
}

# Wikidata food-related classes (Q IDs)
# Each tuple: (qid, label, food_type, primary_category)
FOOD_CLASSES = [
    # Dishes & prepared foods
    ("Q746549", "dish", "dish", "prepared_food"),
    ("Q2095", "food", "ingredient", "food"),
    ("Q40050", "drink", "beverage", "beverage"),
    ("Q81799", "soup", "dish", "soup"),
    ("Q41415", "bread", "dish", "bread"),
    ("Q13276", "pasta", "dish", "pasta"),
    ("Q178", "pasta", "dish", "pasta"),
    ("Q12200", "salad", "dish", "salad"),
    ("Q182940", "sandwich", "dish", "sandwich"),
    ("Q477248", "stew", "dish", "stew"),
    ("Q131419", "pie", "dish", "pastry"),
    ("Q13360264", "dessert", "dish", "dessert"),
    ("Q19861951", "baked good", "dish", "baked_good"),
    ("Q1753", "beer", "beverage", "alcohol"),
    ("Q282", "wine", "beverage", "alcohol"),
    ("Q13228", "tea", "beverage", "hot_drink"),
    ("Q8778", "condiment", "condiment", "condiment"),
    ("Q2596997", "sauce", "condiment", "sauce"),
    ("Q185217", "cheese", "ingredient", "dairy"),
    ("Q10943", "curry", "dish", "curry"),
    ("Q178559", "sausage", "ingredient", "meat"),
    ("Q1411246", "dumpling", "dish", "dumpling"),
    ("Q16971", "noodle", "dish", "noodle"),
    ("Q13317", "rice dish", "dish", "rice"),
    ("Q28803", "confectionery", "dish", "confectionery"),
    ("Q36539", "spice", "ingredient", "spice"),
    ("Q11004", "vegetable", "ingredient", "vegetable"),
    ("Q3314483", "fruit", "ingredient", "fruit"),
    ("Q93189", "cake", "dish", "dessert"),
    ("Q13233", "cookie", "dish", "dessert"),
    ("Q5113", "porridge", "dish", "porridge"),
    ("Q1455989", "fermented food", "dish", "fermented"),
    ("Q170571", "breakfast cereal", "dish", "breakfast"),
    ("Q1431672", "street food", "dish", "street_food"),
    ("Q1778821", "fast food", "dish", "fast_food"),
    ("Q12905998", "flatbread", "dish", "bread"),
    ("Q854618", "smoothie", "beverage", "beverage"),
    ("Q13100073", "cocktail", "beverage", "alcohol"),
    ("Q374", "pizza", "dish", "pizza"),
    ("Q12199", "sushi", "dish", "sushi"),
    ("Q44541", "taco", "dish", "mexican"),
    ("Q192628", "kebab", "dish", "grilled"),
    ("Q15898", "dim sum", "dish", "dim_sum"),
]


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:200]


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
            resp.raise_for_status()
            return resp.json()["results"]["bindings"]
        except requests.exceptions.RequestException as e:
            print(f"  SPARQL error (attempt {attempt+1}/{retries}): {e}")
            time.sleep(5 * (attempt + 1))
    return []


def fetch_wikipedia_extracts(titles, batch_size=20):
    """Fetch short Wikipedia extracts for a batch of article titles."""
    extracts = {}
    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageimages",
            "exintro": True,
            "explaintext": True,
            "exsectionformat": "plain",
            "piprop": "original",
            "titles": "|".join(batch),
        }
        try:
            resp = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                title = page.get("title", "")
                extract = page.get("extract", "")
                image = page.get("original", {}).get("source", "")
                if extract:
                    # Truncate to first 500 chars
                    if len(extract) > 500:
                        extract = extract[:497] + "..."
                    extracts[title] = {"extract": extract, "image": image}
        except requests.exceptions.RequestException as e:
            print(f"  Wikipedia API error: {e}")
        time.sleep(0.5)  # Be polite
    return extracts


def import_foods_for_class(conn, qid, class_label, food_type, primary_category, offset=0, limit=500):
    """Import foods that are instances of a Wikidata class."""

    query = f"""
    SELECT DISTINCT ?item ?itemLabel ?itemDescription ?article ?image ?countryLabel WHERE {{
      ?item wdt:P31/wdt:P279* wd:{qid} .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
      OPTIONAL {{ ?item schema:description ?itemDescription . FILTER(LANG(?itemDescription) = "en") }}
      OPTIONAL {{ ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . }}
      OPTIONAL {{ ?item wdt:P18 ?image . }}
      OPTIONAL {{ ?item wdt:P495 ?country . ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel) = "en") }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    ORDER BY ?itemLabel
    LIMIT {limit}
    OFFSET {offset}
    """

    results = sparql_query(query)
    if not results:
        return 0

    cursor = conn.cursor()
    inserted = 0
    skipped = 0

    for row in results:
        name = row.get("itemLabel", {}).get("value", "").strip()
        if not name or name.startswith("Q"):  # Skip items without English labels
            continue

        item_uri = row.get("item", {}).get("value", "")
        wikidata_qid = item_uri.split("/")[-1] if item_uri else None
        description = row.get("itemDescription", {}).get("value", "")
        wiki_url = row.get("article", {}).get("value", "")
        image_url = row.get("image", {}).get("value", "")
        country = row.get("countryLabel", {}).get("value", "")

        slug = slugify(name)
        if not slug:
            continue

        # Check for duplicate slug
        existing = cursor.execute("SELECT id FROM foods WHERE slug = ?", (slug,)).fetchone()
        if existing:
            skipped += 1
            continue

        try:
            cursor.execute(
                """INSERT INTO foods
                   (name, slug, food_type, primary_category, wikipedia_url,
                    wikidata_qid, image_url, description, data_source, data_quality)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'wikidata', 'medium')""",
                (
                    name,
                    slug,
                    food_type,
                    primary_category,
                    wiki_url or None,
                    wikidata_qid,
                    image_url or None,
                    description[:500] if description else None,
                ),
            )
            inserted += 1

            # Link to culture if country is known
            if country:
                _link_food_to_culture(cursor, cursor.lastrowid, country)

        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    return inserted


def _link_food_to_culture(cursor, food_id, country_name):
    """Link a food to a culture, creating the culture if needed."""
    # Find or create culture
    culture = cursor.execute(
        "SELECT id FROM cultures WHERE name = ?", (country_name,)
    ).fetchone()

    if not culture:
        cursor.execute(
            """INSERT OR IGNORE INTO cultures (name, culture_type, region)
               VALUES (?, 'nation', ?)""",
            (country_name, _guess_region(country_name)),
        )
        culture_id = cursor.lastrowid
    else:
        culture_id = culture[0]

    if culture_id:
        cursor.execute(
            """INSERT OR IGNORE INTO food_culture_origins (food_id, culture_id, origin_type)
               VALUES (?, ?, 'native')""",
            (food_id, culture_id),
        )


def _guess_region(country):
    """Rough region mapping for countries."""
    regions = {
        "East Asia": ["China", "Japan", "South Korea", "North Korea", "Taiwan", "Mongolia"],
        "Southeast Asia": ["Thailand", "Vietnam", "Indonesia", "Philippines", "Malaysia",
                          "Myanmar", "Cambodia", "Laos", "Singapore", "Brunei", "Timor-Leste"],
        "South Asia": ["India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal", "Bhutan", "Afghanistan"],
        "Central Asia": ["Kazakhstan", "Uzbekistan", "Turkmenistan", "Tajikistan", "Kyrgyzstan"],
        "Middle East": ["Iran", "Iraq", "Turkey", "Syria", "Lebanon", "Israel", "Palestine",
                        "Jordan", "Saudi Arabia", "Yemen", "Oman", "UAE", "Kuwait", "Bahrain", "Qatar"],
        "North Africa": ["Egypt", "Morocco", "Tunisia", "Algeria", "Libya"],
        "Sub-Saharan Africa": ["Nigeria", "Ethiopia", "Kenya", "Ghana", "Senegal", "South Africa",
                               "Tanzania", "Congo", "Cameroon", "Uganda", "Mozambique", "Mali"],
        "Western Europe": ["France", "Germany", "Italy", "Spain", "Portugal", "Netherlands",
                          "Belgium", "Switzerland", "Austria", "United Kingdom", "Ireland"],
        "Northern Europe": ["Sweden", "Norway", "Denmark", "Finland", "Iceland"],
        "Eastern Europe": ["Russia", "Poland", "Ukraine", "Czech Republic", "Hungary",
                          "Romania", "Bulgaria", "Serbia", "Croatia", "Slovakia", "Belarus",
                          "Lithuania", "Latvia", "Estonia", "Slovenia", "Bosnia and Herzegovina",
                          "North Macedonia", "Albania", "Moldova", "Montenegro", "Kosovo"],
        "Southern Europe": ["Greece", "Cyprus", "Malta"],
        "North America": ["United States of America", "Canada", "Mexico", "United States"],
        "Central America": ["Guatemala", "Belize", "Honduras", "El Salvador", "Nicaragua",
                           "Costa Rica", "Panama"],
        "Caribbean": ["Cuba", "Jamaica", "Haiti", "Dominican Republic", "Trinidad and Tobago",
                      "Puerto Rico", "Barbados"],
        "South America": ["Brazil", "Argentina", "Colombia", "Peru", "Chile", "Venezuela",
                         "Ecuador", "Bolivia", "Paraguay", "Uruguay"],
        "Oceania": ["Australia", "New Zealand", "Fiji", "Papua New Guinea", "Samoa"],
    }
    for region, countries in regions.items():
        if country in countries:
            return region
    return "Other"


def enrich_with_wikipedia(conn, batch_size=50):
    """Fetch Wikipedia extracts for foods that have Wikipedia URLs but no description."""
    cursor = conn.cursor()
    rows = cursor.execute(
        """SELECT id, name, wikipedia_url FROM foods
           WHERE wikipedia_url IS NOT NULL
           AND wikipedia_url != ''
           AND (description IS NULL OR description = '')
           LIMIT ?""",
        (batch_size * 10,),
    ).fetchall()

    if not rows:
        print("  No foods need Wikipedia enrichment")
        return 0

    # Extract titles from URLs
    title_map = {}  # title -> food_id
    for food_id, name, url in rows:
        if url:
            title = urllib.parse.unquote(url.split("/wiki/")[-1]).replace("_", " ")
            title_map[title] = food_id

    titles = list(title_map.keys())
    print(f"  Fetching Wikipedia extracts for {len(titles)} foods...")

    extracts = fetch_wikipedia_extracts(titles)
    updated = 0

    for title, data in extracts.items():
        food_id = title_map.get(title)
        if food_id and data.get("extract"):
            cursor.execute(
                "UPDATE foods SET description = ? WHERE id = ? AND (description IS NULL OR description = '')",
                (data["extract"], food_id),
            )
            if data.get("image") and not cursor.execute(
                "SELECT image_url FROM foods WHERE id = ? AND image_url IS NOT NULL", (food_id,)
            ).fetchone():
                cursor.execute("UPDATE foods SET image_url = ? WHERE id = ?", (data["image"], food_id))
            updated += 1

    conn.commit()
    print(f"  Enriched {updated} foods with Wikipedia descriptions")
    return updated


def import_from_wikipedia_categories(conn):
    """Walk Wikipedia food category trees to find additional food articles."""
    SEED_CATEGORIES = [
        "Category:Foods by nationality",
        "Category:Fermented foods",
        "Category:Breakfast foods",
        "Category:Street food",
        "Category:Desserts",
        "Category:Soups",
        "Category:Salads",
        "Category:Breads",
        "Category:Dumplings",
        "Category:Noodle dishes",
        "Category:Rice dishes",
        "Category:Cheese",
        "Category:Sausages",
        "Category:Condiments",
        "Category:Spices",
        "Category:Sauces",
        "Category:Pies",
        "Category:Stews",
        "Category:Sandwiches",
        "Category:Kebabs",
        "Category:Curries",
        "Category:Pasta dishes",
        "Category:Pickles",
        "Category:Confectionery",
        "Category:Porridges",
        "Category:Flatbreads",
        "Category:Baked goods",
        "Category:Seafood dishes",
        "Category:Meat dishes",
        "Category:Vegetarian dishes",
        "Category:Vegan cuisine",
    ]

    total_inserted = 0
    visited_categories = set()
    cursor = conn.cursor()

    for seed_cat in SEED_CATEGORIES:
        inserted = _walk_category(conn, cursor, seed_cat, visited_categories, depth=0, max_depth=2)
        total_inserted += inserted
        print(f"  {seed_cat}: +{inserted} foods")

    conn.commit()
    return total_inserted


def _walk_category(conn, cursor, category, visited, depth=0, max_depth=2):
    """Recursively walk a Wikipedia category, extracting food articles."""
    if category in visited or depth > max_depth:
        return 0
    visited.add(category)

    # Skip obviously non-food categories
    skip_patterns = ["stub", "template", "image", "list of", "wikipedia", "commons",
                     "wikiproject", "portal", "user", "redirect", "disambiguation"]
    cat_lower = category.lower()
    if any(pat in cat_lower for pat in skip_patterns):
        return 0

    inserted = 0
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": 500,
        "cmtype": "page|subcat",
    }

    try:
        resp = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        members = resp.json().get("query", {}).get("categorymembers", [])
    except requests.exceptions.RequestException as e:
        print(f"    Category API error for {category}: {e}")
        return 0

    subcats = []
    page_titles = []

    for member in members:
        ns = member.get("ns", 0)
        title = member.get("title", "")

        if ns == 14:  # Subcategory
            subcats.append(title)
        elif ns == 0:  # Article
            page_titles.append(title)

    # Insert articles as foods
    for title in page_titles:
        slug = slugify(title)
        if not slug:
            continue

        existing = cursor.execute("SELECT id FROM foods WHERE slug = ?", (slug,)).fetchone()
        if existing:
            continue

        # Guess category from the parent category name
        food_type, primary_cat = _guess_food_type_from_category(category)
        wiki_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"

        try:
            cursor.execute(
                """INSERT OR IGNORE INTO foods
                   (name, slug, food_type, primary_category, wikipedia_url,
                    data_source, data_quality)
                   VALUES (?, ?, ?, ?, ?, 'wikipedia_category', 'low')""",
                (title, slug, food_type, primary_cat, wiki_url),
            )
            if cursor.rowcount > 0:
                inserted += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    time.sleep(0.3)  # Be polite

    # Recurse into subcategories
    for subcat in subcats:
        inserted += _walk_category(conn, cursor, subcat, visited, depth + 1, max_depth)

    return inserted


def _guess_food_type_from_category(category):
    """Guess food_type and primary_category from a Wikipedia category name."""
    cat = category.lower()
    mappings = [
        (["dessert", "cake", "cookie", "pastry", "confection", "sweet"], "dish", "dessert"),
        (["soup"], "dish", "soup"),
        (["bread", "flatbread", "baked"], "dish", "bread"),
        (["beverage", "drink", "tea", "coffee", "juice"], "beverage", "beverage"),
        (["condiment", "sauce", "dip"], "condiment", "condiment"),
        (["cheese"], "ingredient", "dairy"),
        (["spice", "herb"], "ingredient", "spice"),
        (["vegetable"], "ingredient", "vegetable"),
        (["fruit"], "ingredient", "fruit"),
        (["salad"], "dish", "salad"),
        (["sandwich"], "dish", "sandwich"),
        (["pasta", "noodle"], "dish", "pasta"),
        (["rice"], "dish", "rice"),
        (["stew"], "dish", "stew"),
        (["pie"], "dish", "pastry"),
        (["dumpling"], "dish", "dumpling"),
        (["sausage", "meat"], "ingredient", "meat"),
        (["seafood", "fish"], "dish", "seafood"),
        (["ferment", "pickle"], "dish", "fermented"),
        (["breakfast", "cereal", "porridge"], "dish", "breakfast"),
        (["street food"], "dish", "street_food"),
        (["kebab", "grill"], "dish", "grilled"),
        (["curry"], "dish", "curry"),
        (["vegetarian", "vegan"], "dish", "vegetarian"),
    ]
    for keywords, food_type, primary_cat in mappings:
        if any(kw in cat for kw in keywords):
            return food_type, primary_cat
    return "dish", "prepared_food"


def run_wikidata_import(conn):
    """Run the full Wikidata SPARQL import."""
    print("\n" + "=" * 60)
    print("WIKIDATA FOOD IMPORT")
    print("=" * 60)

    total = 0
    for qid, label, food_type, primary_category in FOOD_CLASSES:
        print(f"\nImporting {label} (wd:{qid})...")

        # Fetch in pages of 500
        offset = 0
        class_total = 0
        while True:
            count = import_foods_for_class(
                conn, qid, label, food_type, primary_category,
                offset=offset, limit=500
            )
            class_total += count
            if count < 100:  # Less than 100 new = probably exhausted
                break
            offset += 500
            time.sleep(2)  # Respect rate limits

        print(f"  -> {class_total} new foods from {label}")
        total += class_total

    # Enrich with Wikipedia descriptions
    print("\nEnriching with Wikipedia descriptions...")
    enrich_with_wikipedia(conn)

    cursor = conn.cursor()
    food_count = cursor.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
    culture_count = cursor.execute("SELECT COUNT(*) FROM cultures").fetchone()[0]

    print(f"\n{'=' * 60}")
    print(f"IMPORT COMPLETE")
    print(f"  Total foods in DB: {food_count}")
    print(f"  Total cultures: {culture_count}")
    print(f"  New foods added this run: {total}")
    print(f"{'=' * 60}")

    return total


def run_category_import(conn):
    """Run the Wikipedia category tree walker."""
    print("\n" + "=" * 60)
    print("WIKIPEDIA CATEGORY IMPORT")
    print("=" * 60)

    total = import_from_wikipedia_categories(conn)

    # Enrich new entries
    print("\nEnriching new entries with Wikipedia descriptions...")
    enrich_with_wikipedia(conn)

    cursor = conn.cursor()
    food_count = cursor.execute("SELECT COUNT(*) FROM foods").fetchone()[0]

    print(f"\n{'=' * 60}")
    print(f"CATEGORY IMPORT COMPLETE")
    print(f"  Total foods in DB: {food_count}")
    print(f"  New foods from categories: {total}")
    print(f"{'=' * 60}")

    return total


def main():
    parser = argparse.ArgumentParser(description="Import food data from Wikipedia/Wikidata")
    parser.add_argument("--mode", choices=["wikidata", "categories", "all"], default="all")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        if args.mode in ("wikidata", "all"):
            run_wikidata_import(conn)

        if args.mode in ("categories", "all"):
            run_category_import(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
