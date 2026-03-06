"""Targeted SPARQL queries for specific food categorizations."""
import sqlite3
import time

import requests

DB_PATH = "food.db"
SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "LotusEaterFoodApp/1.0 python-requests", "Accept": "application/json"}


def sparql(q, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(SPARQL_URL, params={"query": q, "format": "json"}, headers=HEADERS, timeout=120)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", 60)))
                continue
            if r.status_code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()["results"]["bindings"]
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(5 * (attempt + 1))
    return []


def tag_foods(cursor, conn, results, tag_category, tag_value, extra_tags=None):
    """Tag foods from SPARQL results."""
    count = 0
    for r in results:
        name = r.get("itemLabel", {}).get("value", "")
        qid = r.get("item", {}).get("value", "").split("/")[-1]
        if not name or name.startswith("Q"):
            continue
        fid = cursor.execute("SELECT id FROM foods WHERE wikidata_qid = ?", (qid,)).fetchone()
        if fid:
            cursor.execute(
                'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, ?, ?, "wikidata")',
                (fid[0], tag_category, tag_value),
            )
            count += cursor.rowcount
            if extra_tags:
                for cat, val in extra_tags:
                    v = r.get(val, {}).get("value", "") if val in r else val
                    if v and not v.startswith("Q") and not v.startswith("http"):
                        cursor.execute(
                            'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, ?, ?, "wikidata")',
                            (fid[0], cat, v),
                        )
    conn.commit()
    return count


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # 1. Christmas foods (Q5765741)
    print("Fetching Christmas foods...")
    results = sparql("""
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31/wdt:P279* wd:Q5765741 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
    } LIMIT 500
    """)
    n = tag_foods(cursor, conn, results, "tradition", "Christmas")
    print(f"  Christmas: {n} tagged")
    time.sleep(2)

    # 2. Easter foods (Q5765813)
    print("Fetching Easter foods...")
    results = sparql("""
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31/wdt:P279* wd:Q5765813 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
    } LIMIT 500
    """)
    n = tag_foods(cursor, conn, results, "tradition", "Easter")
    print(f"  Easter: {n} tagged")
    time.sleep(2)

    # 3. Breakfast foods (Q79892266)
    print("Fetching breakfast foods...")
    results = sparql("""
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31/wdt:P279* wd:Q79892266 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
    } LIMIT 1000
    """)
    n = tag_foods(cursor, conn, results, "meal_type", "breakfast")
    print(f"  Breakfast: {n} tagged")
    time.sleep(2)

    # 4. National dishes (Q2943)
    print("Fetching national dishes...")
    results = sparql("""
    SELECT ?item ?itemLabel ?countryLabel WHERE {
      ?item wdt:P31 wd:Q2943 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
      OPTIONAL { ?item wdt:P17 ?country . ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel) = "en") }
    } LIMIT 500
    """)
    n = tag_foods(cursor, conn, results, "tradition", "national dish")
    print(f"  National dishes: {n} tagged")
    # Also tag with country cuisine
    for r in results:
        qid = r.get("item", {}).get("value", "").split("/")[-1]
        country = r.get("countryLabel", {}).get("value", "")
        if country and not country.startswith("Q"):
            fid = cursor.execute("SELECT id FROM foods WHERE wikidata_qid = ?", (qid,)).fetchone()
            if fid:
                cursor.execute(
                    'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, "cuisine", ?, "wikidata")',
                    (fid[0], country),
                )
    conn.commit()
    time.sleep(2)

    # 5. Vegetarian dishes (Q2138557)
    print("Fetching vegetarian dishes...")
    results = sparql("""
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31/wdt:P279* wd:Q2138557 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
    } LIMIT 1000
    """)
    n = tag_foods(cursor, conn, results, "dietary", "vegetarian")
    for r in results:
        qid = r.get("item", {}).get("value", "").split("/")[-1]
        fid = cursor.execute("SELECT id FROM foods WHERE wikidata_qid = ?", (qid,)).fetchone()
        if fid:
            cursor.execute("UPDATE foods SET is_vegetarian = 1 WHERE id = ?", (fid[0],))
    conn.commit()
    print(f"  Vegetarian: {n} tagged")
    time.sleep(2)

    # 6. Fermented foods (Q1455989)
    print("Fetching fermented foods...")
    results = sparql("""
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31/wdt:P279* wd:Q1455989 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
    } LIMIT 1000
    """)
    n = tag_foods(cursor, conn, results, "cooking_method", "fermented")
    print(f"  Fermented: {n} tagged")
    time.sleep(2)

    # 7. Desserts (Q182940 and Q13360264)
    print("Fetching dessert classification...")
    results = sparql("""
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31/wdt:P279* wd:Q13360264 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
    } LIMIT 2000
    """)
    n = tag_foods(cursor, conn, results, "meal_type", "dessert")
    print(f"  Desserts: {n} tagged")
    time.sleep(2)

    # 8. Soups (Q81799)
    print("Fetching soups...")
    results = sparql("""
    SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31/wdt:P279* wd:Q81799 .
      ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
    } LIMIT 1000
    """)
    n = tag_foods(cursor, conn, results, "course", "soup")
    print(f"  Soups: {n} tagged")
    time.sleep(2)

    # 9. Specific cuisine queries via P361 (part of cuisine)
    cuisines = [
        ("Q35600", "Chinese"), ("Q182311", "Japanese"), ("Q728986", "Korean"),
        ("Q1042974", "Thai"), ("Q837615", "Indian"), ("Q826599", "Italian"),
        ("Q6924790", "French"), ("Q822764", "Mexican"), ("Q738582", "Turkish"),
        ("Q1364460", "Vietnamese"), ("Q2359461", "Greek"), ("Q1067766", "Spanish"),
        ("Q1039309", "German"), ("Q814694", "Brazilian"), ("Q1200105", "Indonesian"),
        ("Q2619684", "Ethiopian"), ("Q4415078", "Russian"), ("Q751397", "American"),
        ("Q861898", "Peruvian"), ("Q1047415", "Lebanese"), ("Q5764958", "Moroccan"),
        ("Q1040654", "Filipino"), ("Q2197884", "Argentine"), ("Q1362498", "Portuguese"),
        ("Q757588", "Taiwanese"), ("Q2517682", "Nigerian"), ("Q1051691", "Caribbean"),
        ("Q1189847", "Polish"), ("Q2487636", "Jamaican"),
    ]

    print("\nFetching cuisine-specific dishes...")
    for cuisine_qid, cuisine_name in cuisines:
        results = sparql(f"""
        SELECT ?item ?itemLabel WHERE {{
          ?item wdt:P361 wd:{cuisine_qid} .
          ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
        }} LIMIT 500
        """)
        n = tag_foods(cursor, conn, results, "cuisine", cuisine_name)
        print(f"  {cuisine_name}: {n} tagged")
        time.sleep(1.5)

    # 10. Served with (P1909) - do smaller batches to avoid timeouts
    print("\nFetching 'served with' pairings (top foods only)...")
    # Only query foods that are likely dishes (not ingredients/drinks)
    top_foods = cursor.execute("""
        SELECT f.id, f.wikidata_qid FROM foods f
        WHERE f.wikidata_qid IS NOT NULL
        AND f.food_type = 'dish'
        AND f.primary_category IN ('prepared_food', 'soup', 'bread', 'pasta', 'rice',
            'salad', 'sandwich', 'curry', 'dumpling', 'noodle', 'pizza', 'sushi')
        LIMIT 5000
    """).fetchall()

    total_pairings = 0
    for i in range(0, len(top_foods), 50):
        batch = top_foods[i:i+50]
        values_clause = " ".join(f"wd:{qid}" for _, qid in batch)
        qid_to_id = {qid: fid for fid, qid in batch}

        results = sparql(f"""
        SELECT ?item ?pairedLabel WHERE {{
          VALUES ?item {{ {values_clause} }}
          ?item wdt:P1909 ?paired .
          ?paired rdfs:label ?pairedLabel . FILTER(LANG(?pairedLabel) = "en")
        }}
        """)

        for r in results:
            qid = r.get("item", {}).get("value", "").split("/")[-1]
            paired = r.get("pairedLabel", {}).get("value", "")
            food_id = qid_to_id.get(qid)
            if food_id and paired and not paired.startswith("Q"):
                cursor.execute(
                    'INSERT OR IGNORE INTO food_pairings (food_id, paired_food_name, pairing_type, source) VALUES (?, ?, "served_with", "wikidata")',
                    (food_id, paired),
                )
                cursor.execute(
                    'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, source) VALUES (?, "served_with", ?, "wikidata")',
                    (food_id, paired.lower()),
                )
                total_pairings += 1

        conn.commit()
        if i % 200 == 0:
            print(f"  Pairings: {i}/{len(top_foods)} processed, {total_pairings} found")
        time.sleep(1)

    print(f"  Total pairings: {total_pairings}")

    # Final stats
    cursor.execute("SELECT COUNT(*) FROM food_tags")
    print(f"\nTotal tags now: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM food_pairings")
    print(f"Total pairings: {cursor.fetchone()[0]}")
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
