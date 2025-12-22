"""
Seed default decks for the Tinder-style recipe discovery interface.
Run this after initializing the database.
"""

import os
import sqlite3

DATABASE = os.path.join(os.path.dirname(__file__), "food.db")

# Default deck definitions
DEFAULT_DECKS = [
    # By Culture (TheMealDB areas)
    {
        "name": "Italian",
        "deck_type": "culture",
        "filter_cuisine": "Italian",
        "icon": "🇮🇹",
        "sort_order": 1,
    },
    {
        "name": "Mexican",
        "deck_type": "culture",
        "filter_cuisine": "Mexican",
        "icon": "🇲🇽",
        "sort_order": 2,
    },
    {
        "name": "Japanese",
        "deck_type": "culture",
        "filter_cuisine": "Japanese",
        "icon": "🇯🇵",
        "sort_order": 3,
    },
    {
        "name": "Indian",
        "deck_type": "culture",
        "filter_cuisine": "Indian",
        "icon": "🇮🇳",
        "sort_order": 4,
    },
    {
        "name": "Chinese",
        "deck_type": "culture",
        "filter_cuisine": "Chinese",
        "icon": "🇨🇳",
        "sort_order": 5,
    },
    {
        "name": "Thai",
        "deck_type": "culture",
        "filter_cuisine": "Thai",
        "icon": "🇹🇭",
        "sort_order": 6,
    },
    {
        "name": "French",
        "deck_type": "culture",
        "filter_cuisine": "French",
        "icon": "🇫🇷",
        "sort_order": 7,
    },
    {
        "name": "American",
        "deck_type": "culture",
        "filter_cuisine": "American",
        "icon": "🇺🇸",
        "sort_order": 8,
    },
    {
        "name": "British",
        "deck_type": "culture",
        "filter_cuisine": "British",
        "icon": "🇬🇧",
        "sort_order": 9,
    },
    {
        "name": "Greek",
        "deck_type": "culture",
        "filter_cuisine": "Greek",
        "icon": "🇬🇷",
        "sort_order": 10,
    },
    {
        "name": "Spanish",
        "deck_type": "culture",
        "filter_cuisine": "Spanish",
        "icon": "🇪🇸",
        "sort_order": 11,
    },
    {
        "name": "Moroccan",
        "deck_type": "culture",
        "filter_cuisine": "Moroccan",
        "icon": "🇲🇦",
        "sort_order": 12,
    },
    {
        "name": "Vietnamese",
        "deck_type": "culture",
        "filter_cuisine": "Vietnamese",
        "icon": "🇻🇳",
        "sort_order": 13,
    },
    # By Diet (TheMealDB categories)
    {
        "name": "Vegetarian",
        "deck_type": "diet",
        "filter_category": "Vegetarian",
        "icon": "🥬",
        "sort_order": 1,
    },
    {
        "name": "Vegan",
        "deck_type": "diet",
        "filter_category": "Vegan",
        "icon": "🌱",
        "sort_order": 2,
    },
    {
        "name": "Seafood",
        "deck_type": "diet",
        "filter_category": "Seafood",
        "icon": "🐟",
        "sort_order": 3,
    },
    {
        "name": "Pasta",
        "deck_type": "diet",
        "filter_category": "Pasta",
        "icon": "🍝",
        "sort_order": 4,
    },
    # By Type (TheMealDB categories)
    {"name": "Beef", "deck_type": "type", "filter_category": "Beef", "icon": "🥩", "sort_order": 1},
    {
        "name": "Chicken",
        "deck_type": "type",
        "filter_category": "Chicken",
        "icon": "🍗",
        "sort_order": 2,
    },
    {"name": "Lamb", "deck_type": "type", "filter_category": "Lamb", "icon": "🍖", "sort_order": 3},
    {"name": "Pork", "deck_type": "type", "filter_category": "Pork", "icon": "🐷", "sort_order": 4},
    {"name": "Goat", "deck_type": "type", "filter_category": "Goat", "icon": "🐐", "sort_order": 5},
    {
        "name": "Sides",
        "deck_type": "type",
        "filter_category": "Side",
        "icon": "🥗",
        "sort_order": 6,
    },
    {
        "name": "Desserts",
        "deck_type": "type",
        "filter_category": "Dessert",
        "icon": "🍰",
        "sort_order": 7,
    },
    {
        "name": "Breakfast",
        "deck_type": "type",
        "filter_category": "Breakfast",
        "icon": "🍳",
        "sort_order": 8,
    },
    {
        "name": "Starters",
        "deck_type": "type",
        "filter_category": "Starter",
        "icon": "🥟",
        "sort_order": 9,
    },
    {
        "name": "Miscellaneous",
        "deck_type": "type",
        "filter_category": "Miscellaneous",
        "icon": "🍽️",
        "sort_order": 10,
    },
    # Smart Decks (use tags for filtering - implemented in API)
    {
        "name": "Random Mix",
        "deck_type": "smart",
        "filter_tags": '["random"]',
        "icon": "🎲",
        "sort_order": 1,
    },
]


def seed_decks():
    """Insert default decks into the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if decks already exist
    cursor.execute("SELECT COUNT(*) FROM decks")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"Decks table already has {count} entries. Skipping seed.")
        conn.close()
        return

    # Insert decks
    for deck in DEFAULT_DECKS:
        cursor.execute(
            """
            INSERT INTO decks (name, deck_type, filter_category, filter_cuisine, filter_tags, icon, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                deck["name"],
                deck["deck_type"],
                deck.get("filter_category"),
                deck.get("filter_cuisine"),
                deck.get("filter_tags"),
                deck["icon"],
                deck["sort_order"],
            ],
        )

    conn.commit()
    print(f"Seeded {len(DEFAULT_DECKS)} decks into the database.")
    conn.close()


if __name__ == "__main__":
    seed_decks()
