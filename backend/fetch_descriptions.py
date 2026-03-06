"""Fetch Wikipedia descriptions for foods that have URLs but no description."""
import sqlite3
import time
import urllib.parse

import requests

DB_PATH = "food.db"
HEADERS = {"User-Agent": "LotusEaterFoodApp/1.0 python-requests"}
API = "https://en.wikipedia.org/w/api.php"


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    rows = cursor.execute(
        """SELECT id, wikipedia_url FROM foods
           WHERE wikipedia_url IS NOT NULL AND wikipedia_url != ''
           AND (description IS NULL OR description = '')"""
    ).fetchall()

    print(f"Fetching descriptions for {len(rows)} foods...")

    title_map = {}
    for food_id, url in rows:
        if url and "/wiki/" in url:
            title = urllib.parse.unquote(url.split("/wiki/")[-1]).replace("_", " ")
            title_map[title] = food_id

    titles = list(title_map.keys())
    updated = 0

    for i in range(0, len(titles), 20):
        batch = titles[i : i + 20]
        try:
            resp = requests.get(
                API,
                params={
                    "action": "query",
                    "format": "json",
                    "prop": "extracts|pageimages",
                    "exintro": True,
                    "explaintext": True,
                    "piprop": "original",
                    "titles": "|".join(batch),
                },
                headers=HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                title = page.get("title", "")
                extract = page.get("extract", "")
                image = page.get("original", {}).get("source", "")
                fid = title_map.get(title)
                if fid and extract:
                    if len(extract) > 500:
                        extract = extract[:497] + "..."
                    cursor.execute(
                        "UPDATE foods SET description = ? WHERE id = ?", (extract, fid)
                    )
                    if image:
                        cursor.execute(
                            "UPDATE foods SET image_url = COALESCE(image_url, ?) WHERE id = ?",
                            (image, fid),
                        )
                    updated += 1
        except Exception:
            pass

        if i % 500 == 0:
            conn.commit()
            print(f"  {i}/{len(titles)}, {updated} descriptions")
        time.sleep(0.3)

    conn.commit()
    print(f"Done: {updated} descriptions added")

    # Stats
    total_desc = cursor.execute(
        "SELECT COUNT(*) FROM foods WHERE description IS NOT NULL AND description != ''"
    ).fetchone()[0]
    print(f"Total foods with descriptions: {total_desc}")
    conn.close()


if __name__ == "__main__":
    main()
