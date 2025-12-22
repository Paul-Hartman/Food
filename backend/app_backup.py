"""
Food App - Standalone meal planning with cooking cards
Mobile-first design for use while cooking
"""

import os
import sqlite3
from datetime import date, datetime

from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), "food.db")

# Aldi section order for shopping list
ALDI_SECTIONS = [
    "Produce",
    "Bakery",
    "Dairy & Eggs",
    "Meat & Seafood",
    "Frozen",
    "Pantry",
    "Snacks & Beverages",
]


def get_db():
    """Get database connection."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close database connection."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with schema."""
    with app.app_context():
        db = get_db()
        db.executescript(
            """
            -- Ingredients (can be in pantry or shopping list)
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                aldi_section TEXT,
                default_unit TEXT,
                calories_per_100g REAL DEFAULT 0,
                protein_per_100g REAL DEFAULT 0,
                carbs_per_100g REAL DEFAULT 0,
                fat_per_100g REAL DEFAULT 0,
                fiber_per_100g REAL DEFAULT 0,
                grams_per_unit REAL DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Recipes
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                cuisine TEXT,
                prep_time_min INTEGER DEFAULT 0,
                cook_time_min INTEGER DEFAULT 0,
                servings INTEGER DEFAULT 4,
                difficulty TEXT DEFAULT 'easy',
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Recipe ingredients (junction table)
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            );

            -- Cooking steps
            CREATE TABLE IF NOT EXISTS cooking_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                instruction TEXT NOT NULL,
                duration_min INTEGER,
                tips TEXT,
                timer_needed INTEGER DEFAULT 0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );

            -- Pantry (what user already has)
            CREATE TABLE IF NOT EXISTS pantry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                quantity REAL,
                unit TEXT,
                expires_at DATE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            );

            -- Shopping list
            CREATE TABLE IF NOT EXISTS shopping_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                checked INTEGER DEFAULT 0,
                added_from_recipe_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY (added_from_recipe_id) REFERENCES recipes(id)
            );

            -- Meal log (for nutritional tracking)
            CREATE TABLE IF NOT EXISTS meal_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                meal_type TEXT,
                servings_eaten REAL DEFAULT 1,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );

            -- Daily nutrition goals
            CREATE TABLE IF NOT EXISTS nutrition_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calories INTEGER DEFAULT 2000,
                protein_g REAL DEFAULT 50,
                carbs_g REAL DEFAULT 250,
                fat_g REAL DEFAULT 65,
                fiber_g REAL DEFAULT 25,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Insert default nutrition goals if not exists
            INSERT OR IGNORE INTO nutrition_goals (id, calories, protein_g, carbs_g, fat_g, fiber_g)
            VALUES (1, 2000, 50, 250, 65, 25);
        """
        )
        db.commit()


# ============================================================================
# PAGE ROUTES
# ============================================================================


@app.route("/")
def index():
    """Recipe browser homepage."""
    return render_template("index.html")


@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    """Recipe detail page."""
    return render_template("recipe.html", recipe_id=recipe_id)


@app.route("/cook/<int:recipe_id>")
def cook(recipe_id):
    """Step-by-step cooking cards."""
    return render_template("cook.html", recipe_id=recipe_id)


@app.route("/shopping")
def shopping():
    """Shopping list page."""
    return render_template("shopping.html")


@app.route("/pantry")
def pantry():
    """Pantry management page."""
    return render_template("pantry.html")


@app.route("/nutrition")
def nutrition():
    """Nutrition tracking page."""
    return render_template("nutrition.html")


# ============================================================================
# API ROUTES - RECIPES
# ============================================================================


@app.route("/api/recipes")
def api_recipes():
    """List all recipes with optional filters."""
    db = get_db()
    category = request.args.get("category")
    quick = request.args.get("quick")  # Under 30 min total

    query = """
        SELECT id, name, description, category, cuisine,
               prep_time_min, cook_time_min, servings, difficulty, image_url
        FROM recipes WHERE 1=1
    """
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if quick == "true":
        query += " AND (prep_time_min + cook_time_min) <= 30"

    query += " ORDER BY name"

    recipes = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in recipes])


@app.route("/api/recipes/<int:recipe_id>")
def api_recipe_detail(recipe_id):
    """Get recipe with ingredients and nutrition."""
    db = get_db()

    recipe = db.execute(
        """
        SELECT * FROM recipes WHERE id = ?
    """,
        [recipe_id],
    ).fetchone()

    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404

    ingredients = db.execute(
        """
        SELECT ri.*, i.name, i.aldi_section, i.calories_per_100g,
               i.protein_per_100g, i.carbs_per_100g, i.fat_per_100g,
               i.fiber_per_100g, i.grams_per_unit
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
        ORDER BY ri.id
    """,
        [recipe_id],
    ).fetchall()

    steps = db.execute(
        """
        SELECT * FROM cooking_steps
        WHERE recipe_id = ?
        ORDER BY step_number
    """,
        [recipe_id],
    ).fetchall()

    # Calculate nutrition per serving
    nutrition = calculate_recipe_nutrition(ingredients, recipe["servings"])

    return jsonify(
        {
            "recipe": dict(recipe),
            "ingredients": [dict(i) for i in ingredients],
            "steps": [dict(s) for s in steps],
            "nutrition_per_serving": nutrition,
        }
    )


@app.route("/api/recipes/<int:recipe_id>/steps")
def api_recipe_steps(recipe_id):
    """Get cooking steps for card view."""
    db = get_db()

    recipe = db.execute("SELECT name FROM recipes WHERE id = ?", [recipe_id]).fetchone()
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404

    steps = db.execute(
        """
        SELECT step_number, title, instruction, duration_min, tips, timer_needed
        FROM cooking_steps
        WHERE recipe_id = ?
        ORDER BY step_number
    """,
        [recipe_id],
    ).fetchall()

    return jsonify(
        {
            "recipe_name": recipe["name"],
            "steps": [dict(s) for s in steps],
            "total_steps": len(steps),
        }
    )


def calculate_recipe_nutrition(ingredients, servings):
    """Calculate per-serving nutrition from ingredients."""
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}

    for ing in ingredients:
        # Estimate grams from quantity and unit
        grams = estimate_grams(ing["quantity"], ing["unit"], ing["grams_per_unit"])

        totals["calories"] += (ing["calories_per_100g"] or 0) * grams / 100
        totals["protein"] += (ing["protein_per_100g"] or 0) * grams / 100
        totals["carbs"] += (ing["carbs_per_100g"] or 0) * grams / 100
        totals["fat"] += (ing["fat_per_100g"] or 0) * grams / 100
        totals["fiber"] += (ing["fiber_per_100g"] or 0) * grams / 100

    # Divide by servings
    return {k: round(v / servings, 1) for k, v in totals.items()}


def estimate_grams(quantity, unit, grams_per_unit):
    """Estimate grams from quantity and unit."""
    unit = unit.lower()

    # Common conversions
    conversions = {
        "lb": 454,
        "oz": 28,
        "cup": 240,
        "tbsp": 15,
        "tsp": 5,
        "clove": 5,
        "cloves": 5,
        "medium": grams_per_unit or 150,
        "large": (grams_per_unit or 150) * 1.3,
        "small": (grams_per_unit or 150) * 0.7,
        "g": 1,
        "kg": 1000,
        "ml": 1,
        "can": 400,
        "slice": 30,
        "piece": grams_per_unit or 100,
    }

    multiplier = conversions.get(unit, grams_per_unit or 100)
    return quantity * multiplier


# ============================================================================
# API ROUTES - SHOPPING LIST
# ============================================================================


@app.route("/api/shopping")
def api_shopping():
    """Get shopping list grouped by Aldi section."""
    db = get_db()

    items = db.execute(
        """
        SELECT sl.*, i.name, i.aldi_section, r.name as recipe_name
        FROM shopping_list sl
        JOIN ingredients i ON sl.ingredient_id = i.id
        LEFT JOIN recipes r ON sl.added_from_recipe_id = r.id
        ORDER BY i.aldi_section, i.name
    """
    ).fetchall()

    # Group by section
    grouped = {section: [] for section in ALDI_SECTIONS}
    grouped["Other"] = []

    for item in items:
        section = item["aldi_section"] or "Other"
        if section not in grouped:
            section = "Other"
        grouped[section].append(dict(item))

    # Remove empty sections
    grouped = {k: v for k, v in grouped.items() if v}

    return jsonify(
        {
            "sections": grouped,
            "section_order": [s for s in ALDI_SECTIONS if s in grouped]
            + (["Other"] if "Other" in grouped else []),
        }
    )


@app.route("/api/shopping/generate", methods=["POST"])
def api_generate_shopping():
    """Generate shopping list from selected recipes."""
    db = get_db()
    data = request.json
    recipe_ids = data.get("recipe_ids", [])
    clear_existing = data.get("clear_existing", True)
    subtract_pantry = data.get("subtract_pantry", True)

    if clear_existing:
        db.execute("DELETE FROM shopping_list")

    # Aggregate ingredients from all recipes
    needed = {}
    for recipe_id in recipe_ids:
        ingredients = db.execute(
            """
            SELECT ri.*, i.name, i.aldi_section
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        """,
            [recipe_id],
        ).fetchall()

        for ing in ingredients:
            key = (ing["ingredient_id"], ing["unit"])
            if key in needed:
                needed[key]["quantity"] += ing["quantity"]
            else:
                needed[key] = {
                    "ingredient_id": ing["ingredient_id"],
                    "quantity": ing["quantity"],
                    "unit": ing["unit"],
                    "recipe_id": recipe_id,
                }

    # Subtract pantry items if requested
    if subtract_pantry:
        pantry_items = db.execute("SELECT ingredient_id, quantity, unit FROM pantry").fetchall()
        for p in pantry_items:
            key = (p["ingredient_id"], p["unit"])
            if key in needed:
                needed[key]["quantity"] -= p["quantity"]

    # Insert items with quantity > 0
    for item in needed.values():
        if item["quantity"] > 0:
            db.execute(
                """
                INSERT INTO shopping_list (ingredient_id, quantity, unit, added_from_recipe_id)
                VALUES (?, ?, ?, ?)
            """,
                [item["ingredient_id"], item["quantity"], item["unit"], item["recipe_id"]],
            )

    db.commit()
    return jsonify(
        {"success": True, "items_added": len([i for i in needed.values() if i["quantity"] > 0])}
    )


@app.route("/api/shopping/item/<int:item_id>/check", methods=["POST"])
def api_check_shopping_item(item_id):
    """Toggle item checked status."""
    db = get_db()
    db.execute("UPDATE shopping_list SET checked = NOT checked WHERE id = ?", [item_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/shopping/item/<int:item_id>", methods=["DELETE"])
def api_delete_shopping_item(item_id):
    """Remove item from shopping list."""
    db = get_db()
    db.execute("DELETE FROM shopping_list WHERE id = ?", [item_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/shopping/clear-checked", methods=["POST"])
def api_clear_checked():
    """Clear all checked items."""
    db = get_db()
    db.execute("DELETE FROM shopping_list WHERE checked = 1")
    db.commit()
    return jsonify({"success": True})


@app.route("/api/shopping/add", methods=["POST"])
def api_add_shopping_item():
    """Add item to shopping list manually."""
    db = get_db()
    data = request.json

    # Find or create ingredient
    ingredient = db.execute("SELECT id FROM ingredients WHERE name = ?", [data["name"]]).fetchone()
    if not ingredient:
        db.execute(
            """
            INSERT INTO ingredients (name, category, aldi_section, default_unit)
            VALUES (?, ?, ?, ?)
        """,
            [
                data["name"],
                data.get("category", "other"),
                data.get("aldi_section", "Pantry"),
                data.get("unit", "item"),
            ],
        )
        ingredient_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    else:
        ingredient_id = ingredient["id"]

    db.execute(
        """
        INSERT INTO shopping_list (ingredient_id, quantity, unit)
        VALUES (?, ?, ?)
    """,
        [ingredient_id, data.get("quantity", 1), data.get("unit", "item")],
    )
    db.commit()

    return jsonify({"success": True})


# ============================================================================
# API ROUTES - PANTRY
# ============================================================================


@app.route("/api/pantry")
def api_pantry():
    """List pantry items."""
    db = get_db()
    items = db.execute(
        """
        SELECT p.*, i.name, i.category, i.aldi_section
        FROM pantry p
        JOIN ingredients i ON p.ingredient_id = i.id
        ORDER BY i.category, i.name
    """
    ).fetchall()
    return jsonify([dict(i) for i in items])


@app.route("/api/pantry/add", methods=["POST"])
def api_add_pantry():
    """Add item to pantry."""
    db = get_db()
    data = request.json

    # Find or create ingredient
    ingredient = db.execute("SELECT id FROM ingredients WHERE name = ?", [data["name"]]).fetchone()
    if not ingredient:
        db.execute(
            """
            INSERT INTO ingredients (name, category, aldi_section, default_unit)
            VALUES (?, ?, ?, ?)
        """,
            [
                data["name"],
                data.get("category", "pantry"),
                data.get("aldi_section", "Pantry"),
                data.get("unit", "item"),
            ],
        )
        ingredient_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    else:
        ingredient_id = ingredient["id"]

    # Check if already in pantry
    existing = db.execute(
        "SELECT id, quantity FROM pantry WHERE ingredient_id = ? AND unit = ?",
        [ingredient_id, data.get("unit", "item")],
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE pantry SET quantity = quantity + ? WHERE id = ?",
            [data.get("quantity", 1), existing["id"]],
        )
    else:
        db.execute(
            """
            INSERT INTO pantry (ingredient_id, quantity, unit, expires_at)
            VALUES (?, ?, ?, ?)
        """,
            [
                ingredient_id,
                data.get("quantity", 1),
                data.get("unit", "item"),
                data.get("expires_at"),
            ],
        )

    db.commit()
    return jsonify({"success": True})


@app.route("/api/pantry/<int:item_id>", methods=["PUT"])
def api_update_pantry(item_id):
    """Update pantry item quantity."""
    db = get_db()
    data = request.json
    db.execute("UPDATE pantry SET quantity = ? WHERE id = ?", [data["quantity"], item_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/pantry/<int:item_id>", methods=["DELETE"])
def api_delete_pantry(item_id):
    """Remove item from pantry."""
    db = get_db()
    db.execute("DELETE FROM pantry WHERE id = ?", [item_id])
    db.commit()
    return jsonify({"success": True})


# ============================================================================
# API ROUTES - NUTRITION
# ============================================================================


@app.route("/api/nutrition/today")
def api_nutrition_today():
    """Get today's nutrition totals."""
    db = get_db()
    today = date.today().isoformat()

    # Get logged meals for today
    meals = db.execute(
        """
        SELECT ml.*, r.name as recipe_name, r.servings
        FROM meal_log ml
        JOIN recipes r ON ml.recipe_id = r.id
        WHERE date(ml.logged_at) = ?
    """,
        [today],
    ).fetchall()

    # Calculate totals
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    meal_list = []

    for meal in meals:
        # Get recipe ingredients
        ingredients = db.execute(
            """
            SELECT ri.*, i.calories_per_100g, i.protein_per_100g, i.carbs_per_100g,
                   i.fat_per_100g, i.fiber_per_100g, i.grams_per_unit
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        """,
            [meal["recipe_id"]],
        ).fetchall()

        nutrition = calculate_recipe_nutrition(ingredients, meal["servings"])

        # Multiply by servings eaten
        for key in totals:
            totals[key] += nutrition[key] * meal["servings_eaten"]

        meal_list.append(
            {
                "id": meal["id"],
                "recipe_name": meal["recipe_name"],
                "meal_type": meal["meal_type"],
                "servings_eaten": meal["servings_eaten"],
                "nutrition": {
                    k: round(v * meal["servings_eaten"], 1) for k, v in nutrition.items()
                },
                "logged_at": meal["logged_at"],
            }
        )

    # Get goals
    goals = db.execute("SELECT * FROM nutrition_goals WHERE id = 1").fetchone()

    return jsonify(
        {
            "date": today,
            "totals": {k: round(v, 1) for k, v in totals.items()},
            "goals": dict(goals) if goals else {},
            "meals": meal_list,
        }
    )


@app.route("/api/nutrition/log", methods=["POST"])
def api_log_meal():
    """Log a meal eaten."""
    db = get_db()
    data = request.json

    db.execute(
        """
        INSERT INTO meal_log (recipe_id, meal_type, servings_eaten, notes)
        VALUES (?, ?, ?, ?)
    """,
        [
            data["recipe_id"],
            data.get("meal_type", "meal"),
            data.get("servings_eaten", 1),
            data.get("notes"),
        ],
    )
    db.commit()

    return jsonify({"success": True})


@app.route("/api/nutrition/goals", methods=["GET"])
def api_get_goals():
    """Get nutrition goals."""
    db = get_db()
    goals = db.execute("SELECT * FROM nutrition_goals WHERE id = 1").fetchone()
    return jsonify(dict(goals) if goals else {})


@app.route("/api/nutrition/goals", methods=["PUT"])
def api_update_goals():
    """Update nutrition goals."""
    db = get_db()
    data = request.json

    db.execute(
        """
        UPDATE nutrition_goals SET
            calories = ?, protein_g = ?, carbs_g = ?, fat_g = ?, fiber_g = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """,
        [data["calories"], data["protein_g"], data["carbs_g"], data["fat_g"], data["fiber_g"]],
    )
    db.commit()

    return jsonify({"success": True})


@app.route("/api/nutrition/history")
def api_nutrition_history():
    """Get last 7 days nutrition summary."""
    db = get_db()

    # This would require more complex aggregation - simplified for MVP
    return jsonify({"message": "Coming soon"})


# ============================================================================
# API ROUTES - INGREDIENTS (for autocomplete)
# ============================================================================


@app.route("/api/ingredients")
def api_ingredients():
    """List all ingredients for autocomplete."""
    db = get_db()
    search = request.args.get("search", "")

    if search:
        ingredients = db.execute(
            """
            SELECT id, name, category, aldi_section, default_unit
            FROM ingredients WHERE name LIKE ?
            ORDER BY name LIMIT 20
        """,
            [f"%{search}%"],
        ).fetchall()
    else:
        ingredients = db.execute(
            """
            SELECT id, name, category, aldi_section, default_unit
            FROM ingredients ORDER BY name
        """
        ).fetchall()

    return jsonify([dict(i) for i in ingredients])


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "app": "food-app"})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 50)
    print("Food App starting!")
    print("=" * 50)
    print(f"Local: http://localhost:5020")
    print(f"Network: http://0.0.0.0:5020")
    print("Access from phone using your PC's IP address")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5020, debug=True)
