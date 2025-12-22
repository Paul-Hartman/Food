#!/usr/bin/env python3
"""
Backfill product images for existing pantry items from pantry_products table
"""

import sqlite3
import sys


def backfill_images():
    """Update pantry items with images from pantry_products table"""
    db = sqlite3.connect("backend/food.db")
    db.row_factory = sqlite3.Row

    # Get all pantry items without images
    items = db.execute(
        """
        SELECT p.id, i.name, i.id as ingredient_id
        FROM pantry p
        JOIN ingredients i ON p.ingredient_id = i.id
        WHERE p.image_url IS NULL OR p.image_url = ''
    """
    ).fetchall()

    print(f"Found {len(items)} pantry items without images")

    updated = 0
    for item in items:
        # Try to find matching product by name
        product = db.execute(
            """
            SELECT image_url FROM pantry_products
            WHERE name = ? AND image_url IS NOT NULL AND image_url != ''
            LIMIT 1
        """,
            [item["name"]],
        ).fetchone()

        if product and product["image_url"]:
            db.execute(
                """
                UPDATE pantry SET image_url = ? WHERE id = ?
            """,
                [product["image_url"], item["id"]],
            )
            print(f"[OK] Updated: {item['name']} -> {product['image_url'][:50]}...")
            updated += 1

    db.commit()
    db.close()

    print(f"\nUpdated {updated} out of {len(items)} items")


if __name__ == "__main__":
    backfill_images()
