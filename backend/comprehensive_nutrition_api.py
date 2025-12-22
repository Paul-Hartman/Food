"""
Comprehensive Nutrition API Endpoints
Add these routes to app.py for full micronutrient tracking
"""

from flask import Blueprint, jsonify, request
from datetime import date
import sqlite3

def get_db():
    conn = sqlite3.connect('food.db')
    conn.row_factory = sqlite3.Row
    return conn

comprehensive_nutrition = Blueprint('comprehensive_nutrition', __name__)

@comprehensive_nutrition.route("/api/nutrition/comprehensive/today")
def get_comprehensive_today():
    """Get today's comprehensive nutrition with all vitamins, minerals, and water."""
    db = get_db()
    today = date.today().isoformat()

    # Get goals
    goals = db.execute("SELECT * FROM nutrition_goals WHERE id = 1").fetchone()

    # Get or create today's tracking
    tracking = db.execute(
        "SELECT * FROM nutrition_tracking WHERE date = ?", (today,)
    ).fetchone()

    if not tracking:
        db.execute("INSERT INTO nutrition_tracking (date) VALUES (?)", (today,))
        db.commit()
        tracking = db.execute(
            "SELECT * FROM nutrition_tracking WHERE date = ?", (today,)
        ).fetchone()

    return jsonify({
        "date": today,
        "goals": dict(goals) if goals else {},
        "consumed": dict(tracking) if tracking else {}
    })


@comprehensive_nutrition.route("/api/nutrition/comprehensive/goals", methods=["GET"])
def get_comprehensive_goals():
    """Get comprehensive nutrition goals."""
    db = get_db()
    goals = db.execute("SELECT * FROM nutrition_goals WHERE id = 1").fetchone()
    return jsonify(dict(goals) if goals else {})


@comprehensive_nutrition.route("/api/nutrition/comprehensive/goals", methods=["PUT"])
def update_comprehensive_goals():
    """Update comprehensive nutrition goals."""
    db = get_db()
    data = request.json

    # Build dynamic UPDATE query
    fields = []
    values = []

    for key, value in data.items():
        if key != 'id' and value is not None:
            fields.append(f"{key} = ?")
            values.append(value)

    if fields:
        query = f"UPDATE nutrition_goals SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = 1"
        db.execute(query, values)
        db.commit()

    return jsonify({"success": True})


@comprehensive_nutrition.route("/api/nutrition/comprehensive/log-water", methods=["POST"])
def log_water():
    """Log water intake for today."""
    db = get_db()
    today = date.today().isoformat()
    data = request.json

    ml = data.get("ml", 0)

    # Get or create today's tracking
    tracking = db.execute(
        "SELECT * FROM nutrition_tracking WHERE date = ?", (today,)
    ).fetchone()

    if not tracking:
        db.execute("INSERT INTO nutrition_tracking (date, water_ml) VALUES (?, ?)", (today, ml))
    else:
        new_total = tracking["water_ml"] + ml
        db.execute(
            "UPDATE nutrition_tracking SET water_ml = ?, updated_at = CURRENT_TIMESTAMP WHERE date = ?",
            (new_total, today)
        )

    db.commit()
    return jsonify({"success": True})


@comprehensive_nutrition.route("/api/nutrition/comprehensive/log-nutrients", methods=["POST"])
def log_nutrients():
    """Manually log nutrients (from external tracking, supplements, etc)."""
    db = get_db()
    today = date.today().isoformat()
    data = request.json

    # Get or create today's tracking
    tracking = db.execute(
        "SELECT * FROM nutrition_tracking WHERE date = ?", (today,)
    ).fetchone()

    if not tracking:
        db.execute("INSERT INTO nutrition_tracking (date) VALUES (?)", (today,))
        db.commit()
        tracking = db.execute(
            "SELECT * FROM nutrition_tracking WHERE date = ?", (today,)
        ).fetchone()

    # Update each nutrient
    fields = []
    values = []

    for key, value in data.items():
        if key in dir(tracking) and value is not None:
            # Add to existing value
            current = tracking[key] if tracking[key] else 0
            fields.append(f"{key} = ?")
            values.append(current + value)

    if fields:
        query = f"UPDATE nutrition_tracking SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE date = ?"
        values.append(today)
        db.execute(query, values)
        db.commit()

    return jsonify({"success": True})
