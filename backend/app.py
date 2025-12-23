"""
Food App - Standalone meal planning with cooking cards
Mobile-first design for use while cooking
Enhanced with multi-timer, barcode scanner, and search
"""

import atexit
import json
import os
import re
import sqlite3
import sys
import uuid
from datetime import date, datetime, timedelta
from threading import Lock

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, g, jsonify, render_template, request
from flask_cors import CORS

# Add lotus-core to path for profile client
# Note: lotus-core uses hyphen, so we add the profile directory directly
_lotus_core_path = os.path.join(os.path.dirname(__file__), "..", "..", "lotus-core", "profile")
sys.path.insert(0, _lotus_core_path)
try:
    from profile_client import ProfileClient

    PROFILE_AVAILABLE = True
    print(f"Profile client loaded from {_lotus_core_path}")
except ImportError as e:
    PROFILE_AVAILABLE = False
    print(f"Warning: Profile client not available ({e}) - data won't sync to profile service")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
DATABASE = os.path.join(os.path.dirname(__file__), "food.db")

# In-memory timer storage for multi-timer support
active_timers = {}
timer_lock = Lock()

# Background scheduler for daily pantry depletion
scheduler = BackgroundScheduler(daemon=True)


def init_scheduler():
    """Initialize background scheduler for daily depletion."""
    # Midnight depletion job
    scheduler.add_job(
        func=daily_depletion_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="daily_depletion",
        name="Deplete daily-use pantry items",
        replace_existing=True,
    )

    # Startup catch-up job (handles server restarts)
    scheduler.add_job(
        func=catchup_depletion_job,
        trigger="date",
        id="catchup_depletion",
        name="Catch up missed depletions",
    )

    # Weekly auto-learning
    scheduler.add_job(
        func=auto_learning_job,
        trigger=CronTrigger(day_of_week="sun", hour=1, minute=0),
        id="auto_learning",
        name="Adjust usage rates",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] APScheduler started")
    atexit.register(lambda: scheduler.shutdown())


# Home Assistant configuration for Meater integration
HA_URL = "http://jungledirector.local:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2JjZGU4Y2JmZmI0YzJiYTYxOWEzODkyYzQxNWMzZCIsImlhdCI6MTc2MjM1OTM0OCwiZXhwIjoyMDc3NzE5MzQ4fQ.eU1jarzwPUaSEGATlSpBdburAL-1Etx5he0Li6hviEM"

# Meater entity IDs in Home Assistant
MEATER_ENTITIES = {
    "internal_temp": "sensor.meater_probe_internal_temperature",
    "ambient_temp": "sensor.meater_probe_ambient_temperature",
    "target_temp": "sensor.meater_probe_target_temperature",
    "peak_temp": "sensor.meater_probe_peak_temperature",
    "time_remaining": "sensor.meater_probe_time_remaining",
    "time_elapsed": "sensor.meater_probe_time_elapsed",
    "cook_state": "sensor.meater_probe_cook_state",
    "cooking": "sensor.meater_probe_cooking",
}

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

# Profile client for syncing to unified profile service
_profile_client = None


def get_profile_client():
    """Get or create profile client instance (lazy initialization)."""
    global _profile_client
    if not PROFILE_AVAILABLE:
        return None
    if _profile_client is None:
        try:
            _profile_client = ProfileClient()
            print(f"Profile client connected to {_profile_client.base_url}")
        except Exception as e:
            print(f"Warning: Could not connect to profile service: {e}")
            return None
    return _profile_client


def sync_to_profile(action: str, **kwargs):
    """Sync data to profile service (non-blocking, errors logged)."""
    profile = get_profile_client()
    if not profile:
        return False
    try:
        if action == "pantry_add":
            profile.add_to_pantry(
                name=kwargs.get("name"),
                category=kwargs.get("category"),
                quantity=kwargs.get("quantity"),
                unit=kwargs.get("unit"),
                barcode=kwargs.get("barcode"),
                brand=kwargs.get("brand"),
                location=kwargs.get("location", "pantry"),
            )
        elif action == "meal_log":
            profile.log_meal(
                recipe_name=kwargs.get("recipe_name"),
                meal_type=kwargs.get("meal_type", "meal"),
                recipe_id=kwargs.get("recipe_id"),
                servings=kwargs.get("servings", 1),
                calories=kwargs.get("calories"),
                protein=kwargs.get("protein"),
                carbs=kwargs.get("carbs"),
                fat=kwargs.get("fat"),
                ingredients=kwargs.get("ingredients"),
                notes=kwargs.get("notes"),
            )
        print(f"Profile sync: {action} successful")
        return True
    except Exception as e:
        print(f"Profile sync failed ({action}): {e}")
        return False


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
                barcode TEXT,
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
                step_type TEXT DEFAULT 'cook',
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

            -- ================================================================
            -- TINDER SWIPE DISCOVERY TABLES
            -- ================================================================

            -- User profile/preferences for filtering
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_type TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Recipe swipe history (for recommendation algorithm)
            CREATE TABLE IF NOT EXISTS recipe_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT NOT NULL,
                recipe_source TEXT DEFAULT 'mealdb',
                action TEXT NOT NULL,
                category TEXT,
                cuisine TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Interested recipes list (swipe right saves here)
            CREATE TABLE IF NOT EXISTS interested_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT NOT NULL UNIQUE,
                recipe_source TEXT DEFAULT 'mealdb',
                name TEXT,
                image_url TEXT,
                category TEXT,
                cuisine TEXT,
                tags TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Cooking deck (swipe up adds here - tonight's meals)
            CREATE TABLE IF NOT EXISTS cooking_deck (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT NOT NULL,
                recipe_source TEXT DEFAULT 'mealdb',
                name TEXT,
                image_url TEXT,
                meal_type TEXT NOT NULL,
                scheduled_date DATE DEFAULT CURRENT_DATE,
                position INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Dynamic deck definitions
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                deck_type TEXT NOT NULL,
                filter_category TEXT,
                filter_cuisine TEXT,
                filter_tags TEXT,
                icon TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ================================================================
            -- NUTRITION CACHE (from USDA FoodData Central)
            -- ================================================================
            CREATE TABLE IF NOT EXISTS nutrition_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_name TEXT NOT NULL UNIQUE,
                calories REAL DEFAULT 0,
                protein REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                fiber REAL DEFAULT 0,
                sodium REAL DEFAULT 0,
                sugar REAL DEFAULT 0,
                serving_size_g REAL DEFAULT 100,
                usda_fdc_id TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ================================================================
            -- PANTRY PRODUCTS (barcode scanned items)
            -- ================================================================
            -- ================================================================
            -- GENERIC INGREDIENTS (for recipe linking)
            -- Example: "milk", "flour", "eggs" - abstract concepts
            -- ================================================================
            CREATE TABLE IF NOT EXISTS generic_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,      -- 'milk', 'whole milk', 'flour'
                category TEXT,                  -- 'dairy', 'grain', 'produce', 'meat', 'spice'
                default_unit TEXT,              -- 'ml', 'g', 'piece'
                -- Average nutrition per 100g (for recipe calculations)
                avg_calories REAL DEFAULT 0,
                avg_protein REAL DEFAULT 0,
                avg_carbs REAL DEFAULT 0,
                avg_fat REAL DEFAULT 0,
                aliases TEXT,                   -- JSON array: ["whole milk", "vollmilch", "lait entier"]
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pantry_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT NOT NULL,
                brand TEXT,
                -- Store information
                store TEXT,                     -- 'aldi', 'lidl', 'rewe', 'edeka', etc.
                store_product_id TEXT,          -- Store's internal product ID if known
                -- Link to generic ingredient
                ingredient_id INTEGER,          -- FK to generic_ingredients
                category TEXT,                  -- 'dairy', 'produce', 'meat', 'bakery', 'frozen', 'pantry', 'spice', 'beverage'
                subcategory TEXT,               -- 'milk', 'cheese', 'yogurt' etc.
                storage_type TEXT DEFAULT 'pantry', -- 'pantry', 'fridge', 'freezer', 'spice_rack'
                image_url TEXT,
                -- Nutrition per 100g
                calories REAL DEFAULT 0,
                protein REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                fiber REAL DEFAULT 0,
                sodium REAL DEFAULT 0,
                sugar REAL DEFAULT 0,
                saturated_fat REAL DEFAULT 0,
                -- Product details
                serving_size TEXT,
                serving_size_g REAL,
                package_weight_g REAL,          -- Total weight when full
                package_unit TEXT,              -- 'ml', 'g', 'pieces'
                price REAL,                     -- Price in EUR
                price_per_kg REAL,              -- Price per kg for comparison
                currency TEXT DEFAULT 'EUR',
                -- Source tracking
                data_source TEXT,               -- 'open_food_facts', 'store_api', 'manual'
                last_price_update DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES generic_ingredients(id)
            );

            -- ================================================================
            -- PANTRY INVENTORY (actual items in your pantry)
            -- ================================================================
            CREATE TABLE IF NOT EXISTS pantry_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                location TEXT DEFAULT 'pantry', -- 'pantry', 'spice_rack', 'fridge', 'freezer'
                current_weight_g REAL,          -- How much is left
                purchase_date DATE,
                expiry_date DATE,
                opened_date DATE,
                is_opened INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES pantry_products(id)
            );

            -- ================================================================
            -- KITCHEN TOOLS (pans, knives, utensils, appliances)
            -- ================================================================
            CREATE TABLE IF NOT EXISTS kitchen_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT,
                store TEXT,                     -- 'aldi', 'lidl', 'rewe', 'ikea', 'wmf', 'amazon'
                category TEXT NOT NULL,         -- 'cookware', 'cutlery', 'utensils', 'appliances', 'bakeware', 'storage'
                subcategory TEXT,               -- 'pan', 'pot', 'knife', 'spatula', 'blender', etc.
                material TEXT,                  -- 'stainless_steel', 'cast_iron', 'non_stick', 'wood', 'silicone'
                size TEXT,                      -- '28cm', 'large', '5L', etc.
                image_url TEXT,
                price REAL,
                currency TEXT DEFAULT 'EUR',
                -- Condition tracking
                condition TEXT DEFAULT 'good',  -- 'new', 'good', 'fair', 'needs_replacement'
                purchase_date DATE,
                warranty_until DATE,
                -- Usage info
                dishwasher_safe INTEGER DEFAULT 0,
                oven_safe INTEGER DEFAULT 0,
                max_temp_c INTEGER,             -- Max temperature if oven safe
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- My owned kitchen tools inventory
            CREATE TABLE IF NOT EXISTS kitchen_tools_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id INTEGER NOT NULL,
                location TEXT DEFAULT 'kitchen', -- 'kitchen', 'drawer', 'cabinet', 'countertop', 'storage'
                quantity INTEGER DEFAULT 1,
                condition TEXT DEFAULT 'good',
                last_used DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tool_id) REFERENCES kitchen_tools(id)
            );

            -- ================================================================
            -- DAILY JOURNAL / LIFE TRACKING TABLES
            -- ================================================================

            -- Cooked meals with ingredients used from pantry
            CREATE TABLE IF NOT EXISTS cooked_meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_name TEXT NOT NULL,
                meal_type TEXT,
                servings INTEGER DEFAULT 1,
                recipe_id TEXT,
                recipe_source TEXT DEFAULT 'custom',
                notes TEXT,
                image_url TEXT,
                cooked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Ingredients used in a cooked meal (links to pantry inventory)
            CREATE TABLE IF NOT EXISTS cooked_meal_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cooked_meal_id INTEGER NOT NULL,
                inventory_id INTEGER,
                product_id INTEGER,
                ingredient_name TEXT NOT NULL,
                amount_used_g REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cooked_meal_id) REFERENCES cooked_meals(id),
                FOREIGN KEY (inventory_id) REFERENCES pantry_inventory(id),
                FOREIGN KEY (product_id) REFERENCES pantry_products(id)
            );

            -- Daily journal aggregates data from multiple apps
            CREATE TABLE IF NOT EXISTS daily_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_date DATE NOT NULL UNIQUE,
                summary TEXT,
                mood INTEGER,
                energy_level INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Journal entries - individual entries of different types
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_date DATE NOT NULL,
                entry_type TEXT NOT NULL,
                entry_data TEXT NOT NULL,
                source_app TEXT,
                source_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ================================================================
            -- NUTRITION & DAILY GOALS TRACKING
            -- ================================================================

            -- Daily nutrition goals (user's targets)
            CREATE TABLE IF NOT EXISTS daily_nutrition_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calories INTEGER DEFAULT 2000,
                protein_g REAL DEFAULT 50,
                carbs_g REAL DEFAULT 250,
                fat_g REAL DEFAULT 65,
                fiber_g REAL DEFAULT 25,
                sodium_mg REAL DEFAULT 2300,
                sugar_g REAL DEFAULT 50,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Daily nutrition consumed (aggregated from meals)
            CREATE TABLE IF NOT EXISTS daily_nutrition_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date DATE NOT NULL UNIQUE,
                calories INTEGER DEFAULT 0,
                protein_g REAL DEFAULT 0,
                carbs_g REAL DEFAULT 0,
                fat_g REAL DEFAULT 0,
                fiber_g REAL DEFAULT 0,
                sodium_mg REAL DEFAULT 0,
                sugar_g REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Comprehensive daily values (FDA 2020 reference values)
            -- All micronutrients your body needs daily
            CREATE TABLE IF NOT EXISTS daily_values_reference (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                -- Macronutrients
                calories INTEGER DEFAULT 2000,
                total_fat_g REAL DEFAULT 78,
                saturated_fat_g REAL DEFAULT 20,
                trans_fat_g REAL DEFAULT 0,
                cholesterol_mg REAL DEFAULT 300,
                sodium_mg REAL DEFAULT 2300,
                total_carbs_g REAL DEFAULT 275,
                fiber_g REAL DEFAULT 28,
                total_sugars_g REAL DEFAULT 50,
                added_sugars_g REAL DEFAULT 50,
                protein_g REAL DEFAULT 50,
                -- Fat-Soluble Vitamins
                vitamin_a_mcg REAL DEFAULT 900,
                vitamin_d_mcg REAL DEFAULT 20,
                vitamin_e_mg REAL DEFAULT 15,
                vitamin_k_mcg REAL DEFAULT 120,
                -- Water-Soluble Vitamins
                vitamin_c_mg REAL DEFAULT 90,
                thiamin_mg REAL DEFAULT 1.2,
                riboflavin_mg REAL DEFAULT 1.3,
                niacin_mg REAL DEFAULT 16,
                vitamin_b6_mg REAL DEFAULT 1.7,
                folate_mcg REAL DEFAULT 400,
                vitamin_b12_mcg REAL DEFAULT 2.4,
                biotin_mcg REAL DEFAULT 30,
                pantothenic_acid_mg REAL DEFAULT 5,
                choline_mg REAL DEFAULT 550,
                -- Minerals
                calcium_mg REAL DEFAULT 1300,
                iron_mg REAL DEFAULT 18,
                phosphorus_mg REAL DEFAULT 1250,
                iodine_mcg REAL DEFAULT 150,
                magnesium_mg REAL DEFAULT 420,
                zinc_mg REAL DEFAULT 11,
                selenium_mcg REAL DEFAULT 55,
                copper_mg REAL DEFAULT 0.9,
                manganese_mg REAL DEFAULT 2.3,
                chromium_mcg REAL DEFAULT 35,
                molybdenum_mcg REAL DEFAULT 45,
                chloride_mg REAL DEFAULT 2300,
                potassium_mg REAL DEFAULT 4700,
                -- Additional useful nutrients
                omega_3_g REAL DEFAULT 1.6,
                omega_6_g REAL DEFAULT 17,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Micronutrient cache for ingredients (from USDA FoodData Central)
            CREATE TABLE IF NOT EXISTS ingredient_nutrients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_name TEXT NOT NULL,
                fdc_id INTEGER,
                -- Per 100g values
                calories REAL,
                protein_g REAL,
                total_fat_g REAL,
                saturated_fat_g REAL,
                trans_fat_g REAL,
                cholesterol_mg REAL,
                sodium_mg REAL,
                total_carbs_g REAL,
                fiber_g REAL,
                total_sugars_g REAL,
                -- Vitamins (per 100g)
                vitamin_a_mcg REAL,
                vitamin_c_mg REAL,
                vitamin_d_mcg REAL,
                vitamin_e_mg REAL,
                vitamin_k_mcg REAL,
                thiamin_mg REAL,
                riboflavin_mg REAL,
                niacin_mg REAL,
                vitamin_b6_mg REAL,
                folate_mcg REAL,
                vitamin_b12_mcg REAL,
                biotin_mcg REAL,
                pantothenic_acid_mg REAL,
                choline_mg REAL,
                -- Minerals (per 100g)
                calcium_mg REAL,
                iron_mg REAL,
                phosphorus_mg REAL,
                iodine_mcg REAL,
                magnesium_mg REAL,
                zinc_mg REAL,
                selenium_mcg REAL,
                copper_mg REAL,
                manganese_mg REAL,
                chromium_mcg REAL,
                molybdenum_mcg REAL,
                potassium_mg REAL,
                -- Metadata
                data_source TEXT DEFAULT 'usda',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ingredient_name)
            );

            -- Daily micronutrient tracking (what you consumed today)
            CREATE TABLE IF NOT EXISTS daily_micronutrients_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date DATE NOT NULL UNIQUE,
                -- Vitamins consumed
                vitamin_a_mcg REAL DEFAULT 0,
                vitamin_c_mg REAL DEFAULT 0,
                vitamin_d_mcg REAL DEFAULT 0,
                vitamin_e_mg REAL DEFAULT 0,
                vitamin_k_mcg REAL DEFAULT 0,
                thiamin_mg REAL DEFAULT 0,
                riboflavin_mg REAL DEFAULT 0,
                niacin_mg REAL DEFAULT 0,
                vitamin_b6_mg REAL DEFAULT 0,
                folate_mcg REAL DEFAULT 0,
                vitamin_b12_mcg REAL DEFAULT 0,
                biotin_mcg REAL DEFAULT 0,
                pantothenic_acid_mg REAL DEFAULT 0,
                choline_mg REAL DEFAULT 0,
                -- Minerals consumed
                calcium_mg REAL DEFAULT 0,
                iron_mg REAL DEFAULT 0,
                phosphorus_mg REAL DEFAULT 0,
                iodine_mcg REAL DEFAULT 0,
                magnesium_mg REAL DEFAULT 0,
                zinc_mg REAL DEFAULT 0,
                selenium_mcg REAL DEFAULT 0,
                copper_mg REAL DEFAULT 0,
                manganese_mg REAL DEFAULT 0,
                chromium_mcg REAL DEFAULT 0,
                molybdenum_mcg REAL DEFAULT 0,
                potassium_mg REAL DEFAULT 0,
                cholesterol_mg REAL DEFAULT 0,
                saturated_fat_g REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Completed meals (the fused meal card - combines multiple dishes)
            CREATE TABLE IF NOT EXISTS completed_meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_name TEXT NOT NULL,
                meal_type TEXT,
                servings INTEGER DEFAULT 1,
                -- Combined nutrition for the meal
                total_calories INTEGER DEFAULT 0,
                total_protein_g REAL DEFAULT 0,
                total_carbs_g REAL DEFAULT 0,
                total_fat_g REAL DEFAULT 0,
                total_fiber_g REAL DEFAULT 0,
                total_sodium_mg REAL DEFAULT 0,
                total_sugar_g REAL DEFAULT 0,
                -- User feedback
                rating INTEGER,
                notes TEXT,
                changes_for_next_time TEXT,
                image_url TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Individual dishes in a completed meal
            CREATE TABLE IF NOT EXISTS completed_meal_dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                completed_meal_id INTEGER NOT NULL,
                dish_name TEXT NOT NULL,
                dish_type TEXT,  -- 'main', 'side', 'dessert', etc.
                recipe_id TEXT,
                recipe_source TEXT,
                -- Per-dish nutrition
                calories INTEGER DEFAULT 0,
                protein_g REAL DEFAULT 0,
                carbs_g REAL DEFAULT 0,
                fat_g REAL DEFAULT 0,
                fiber_g REAL DEFAULT 0,
                sodium_mg REAL DEFAULT 0,
                sugar_g REAL DEFAULT 0,
                FOREIGN KEY (completed_meal_id) REFERENCES completed_meals(id)
            );

            -- Ingredients used in a completed meal dish (with amounts deducted)
            CREATE TABLE IF NOT EXISTS completed_meal_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                completed_meal_id INTEGER NOT NULL,
                dish_id INTEGER,
                inventory_id INTEGER,
                product_id INTEGER,
                ingredient_name TEXT NOT NULL,
                amount_used_g REAL,
                step_id TEXT,  -- Which recipe step used this
                -- Nutrition contribution from this ingredient
                calories INTEGER DEFAULT 0,
                protein_g REAL DEFAULT 0,
                carbs_g REAL DEFAULT 0,
                fat_g REAL DEFAULT 0,
                FOREIGN KEY (completed_meal_id) REFERENCES completed_meals(id),
                FOREIGN KEY (dish_id) REFERENCES completed_meal_dishes(id),
                FOREIGN KEY (inventory_id) REFERENCES pantry_inventory(id),
                FOREIGN KEY (product_id) REFERENCES pantry_products(id)
            );

            -- Recipe step ingredient requirements (for drag-drop matching)
            CREATE TABLE IF NOT EXISTS recipe_step_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                ingredient_name TEXT NOT NULL,
                amount_g REAL,
                amount_display TEXT,  -- "2 tbsp", "1 lb", etc.
                is_required INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ================================================================
            -- MEAL PLANNING (day/week/month planning with budget)
            -- ================================================================

            -- Meal plans (a plan for day/week/month)
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                plan_type TEXT NOT NULL,           -- 'day', 'week', 'month'
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                -- Budget settings
                budget_total REAL,                  -- Total budget for the plan in EUR
                budget_remaining REAL,
                -- Meal requirements
                meals_per_day INTEGER DEFAULT 3,    -- breakfast, lunch, dinner
                include_snacks INTEGER DEFAULT 0,
                -- Progress
                status TEXT DEFAULT 'planning',     -- 'planning', 'shopping', 'prepping', 'active', 'completed'
                breakfasts_needed INTEGER DEFAULT 0,
                lunches_needed INTEGER DEFAULT 0,
                dinners_needed INTEGER DEFAULT 0,
                snacks_needed INTEGER DEFAULT 0,
                breakfasts_selected INTEGER DEFAULT 0,
                lunches_selected INTEGER DEFAULT 0,
                dinners_selected INTEGER DEFAULT 0,
                snacks_selected INTEGER DEFAULT 0,
                -- Stats
                total_estimated_cost REAL DEFAULT 0,
                ingredient_overlap_score REAL DEFAULT 0,  -- Higher = more shared ingredients = easier prep
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Meals in a plan
            CREATE TABLE IF NOT EXISTS meal_plan_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                recipe_id TEXT NOT NULL,            -- local_<id> or mealdb_<id>
                recipe_source TEXT DEFAULT 'local',
                recipe_title TEXT NOT NULL,
                meal_type TEXT NOT NULL,            -- 'breakfast', 'lunch', 'dinner', 'snack'
                day_number INTEGER DEFAULT 1,       -- 1-31 for which day in the plan
                meal_date DATE,
                servings INTEGER DEFAULT 2,
                -- Cost estimate based on ingredients
                estimated_cost REAL DEFAULT 0,
                -- Prep info
                can_meal_prep INTEGER DEFAULT 0,    -- Can this be prepped ahead?
                prep_day INTEGER,                   -- Which day to prep this meal
                -- Status
                is_cooked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE
            );

            -- Ingredient requirements for a meal plan (aggregated from all recipes)
            CREATE TABLE IF NOT EXISTS meal_plan_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                ingredient_name TEXT NOT NULL,
                total_amount_g REAL DEFAULT 0,
                total_amount_display TEXT,
                -- How many recipes use this ingredient
                recipe_count INTEGER DEFAULT 1,
                -- Cost and availability
                estimated_cost REAL,
                store_product_id INTEGER,           -- Matched FrischeParadies product
                in_pantry INTEGER DEFAULT 0,
                pantry_amount_g REAL DEFAULT 0,
                need_to_buy_g REAL DEFAULT 0,
                -- Prep info
                can_prep_ahead INTEGER DEFAULT 0,   -- e.g., dice onions Sunday for the week
                prep_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
                FOREIGN KEY (store_product_id) REFERENCES pantry_products(id)
            );

            -- ================================================================
            -- FAMILY/HOUSEHOLD MANAGEMENT (Lotus-Eater Integration)
            -- ================================================================

            -- Family members with color coding
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#6366f1',
                avatar_emoji TEXT DEFAULT '👤',
                dietary_restrictions TEXT,  -- JSON array
                calorie_target INTEGER,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Calendar events (unified for all sources)
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT NOT NULL,     -- 'meal', 'appointment', 'reminder', 'external'
                source TEXT DEFAULT 'manual', -- 'manual', 'google', 'apple', 'food_app'
                start_datetime TIMESTAMP NOT NULL,
                end_datetime TIMESTAMP,
                all_day INTEGER DEFAULT 0,
                family_member_id INTEGER,
                color TEXT,
                recurrence_rule TEXT,         -- iCal RRULE
                external_id TEXT,             -- Google/Apple event ID
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id)
            );

            -- Scheduled meals (links recipes to calendar)
            CREATE TABLE IF NOT EXISTS scheduled_meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calendar_event_id INTEGER NOT NULL,
                recipe_id TEXT NOT NULL,
                recipe_source TEXT DEFAULT 'local',
                recipe_name TEXT,
                meal_type TEXT NOT NULL,      -- breakfast/lunch/dinner/snack
                servings INTEGER DEFAULT 2,
                complexity_score INTEGER,     -- 1-10
                chef_member_id INTEGER,
                is_cooked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (calendar_event_id) REFERENCES calendar_events(id) ON DELETE CASCADE,
                FOREIGN KEY (chef_member_id) REFERENCES family_members(id)
            );

            -- Day busyness tracking
            CREATE TABLE IF NOT EXISTS day_busyness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                event_count INTEGER DEFAULT 0,
                total_hours REAL DEFAULT 0,
                busyness_score INTEGER,       -- 1-10
                suggested_complexity INTEGER, -- max recipe complexity
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Track quests created from meals (Quest System integration)
            CREATE TABLE IF NOT EXISTS meal_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_meal_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,          -- UUID from Quest System
                quest_type TEXT DEFAULT 'daily', -- daily/main/boss
                xp_reward INTEGER DEFAULT 50,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                xp_earned INTEGER,
                FOREIGN KEY (scheduled_meal_id) REFERENCES scheduled_meals(id) ON DELETE CASCADE
            );

            -- Auto-generated journal entries (Lotus Journal integration)
            CREATE TABLE IF NOT EXISTS auto_journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date DATE NOT NULL,
                entry_type TEXT NOT NULL,        -- 'meal_cooked', 'quest_completed', 'achievement'
                title TEXT NOT NULL,
                content TEXT,
                metadata TEXT,                   -- JSON
                synced_to_journal INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ================================================================
            -- SIMS-STYLE GAMIFICATION SYSTEM
            -- ================================================================

            -- Family member needs/stats (Sims-style meters)
            CREATE TABLE IF NOT EXISTS member_needs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                -- Core needs (0-100 scale, decay over time)
                hunger INTEGER DEFAULT 50,           -- Decreases over time, increases when eating
                energy INTEGER DEFAULT 75,           -- Decreases during day, increases with sleep
                nutrition_balance INTEGER DEFAULT 50, -- Based on micronutrient coverage
                social INTEGER DEFAULT 50,           -- Increases with shared meals
                fun INTEGER DEFAULT 50,              -- Increases with variety/new recipes
                budget_satisfaction INTEGER DEFAULT 75, -- Based on staying within budget
                -- Decay rates (points per hour)
                hunger_decay_rate REAL DEFAULT 4.0,   -- Loses ~16 points per meal gap
                energy_decay_rate REAL DEFAULT 2.0,
                -- Timestamps
                last_meal_at TIMESTAMP,
                last_social_meal_at TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
            );

            -- Cooking skills tree
            CREATE TABLE IF NOT EXISTS cooking_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                skill_category TEXT NOT NULL,        -- 'knife', 'baking', 'grilling', 'world', 'technique'
                level INTEGER DEFAULT 1,             -- 1-10
                xp INTEGER DEFAULT 0,                -- XP towards next level
                xp_to_next_level INTEGER DEFAULT 100,
                unlocked INTEGER DEFAULT 0,          -- Is this skill unlocked?
                parent_skill_id INTEGER,             -- For skill tree dependencies
                icon TEXT,                           -- Emoji or icon name
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_skill_id) REFERENCES cooking_skills(id),
                UNIQUE(family_member_id, skill_name) -- Prevent duplicate skills per member
            );

            -- Define the skill tree structure
            CREATE TABLE IF NOT EXISTS skill_tree_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL UNIQUE,
                skill_category TEXT NOT NULL,
                parent_skill_name TEXT,              -- NULL for root skills
                icon TEXT,
                description TEXT,
                unlock_recipe_count INTEGER DEFAULT 0, -- Recipes needed to unlock
                unlock_cuisine TEXT,                 -- Cuisine type needed (optional)
                base_xp_per_recipe INTEGER DEFAULT 10
            );

            -- Achievements and badges
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT,                           -- Emoji or icon
                category TEXT NOT NULL,              -- 'cooking', 'streak', 'variety', 'social', 'budget', 'health'
                rarity TEXT DEFAULT 'common',        -- 'common', 'uncommon', 'rare', 'epic', 'legendary'
                xp_reward INTEGER DEFAULT 50,
                -- Unlock conditions (JSON)
                unlock_condition TEXT,               -- JSON: {"type": "cook_count", "value": 10}
                hidden INTEGER DEFAULT 0,            -- Hidden achievements
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Earned achievements per member
            CREATE TABLE IF NOT EXISTS member_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,          -- Has user been notified?
                UNIQUE(family_member_id, achievement_id),
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id)
            );

            -- Cooking streaks
            CREATE TABLE IF NOT EXISTS cooking_streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                streak_type TEXT NOT NULL,           -- 'daily_cook', 'healthy_meals', 'budget', 'variety'
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_activity_date DATE,
                streak_multiplier REAL DEFAULT 1.0,  -- XP multiplier based on streak
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(family_member_id, streak_type),
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
            );

            -- Recipe collection (collectible card game style)
            CREATE TABLE IF NOT EXISTS recipe_collection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                recipe_id TEXT NOT NULL,
                recipe_source TEXT DEFAULT 'local',  -- 'local', 'mealdb', 'custom'
                recipe_name TEXT,
                cuisine TEXT,
                -- Collection metadata
                times_cooked INTEGER DEFAULT 0,
                first_cooked_at TIMESTAMP,
                last_cooked_at TIMESTAMP,
                is_favorite INTEGER DEFAULT 0,
                is_mastered INTEGER DEFAULT 0,       -- Cooked 5+ times
                rarity TEXT DEFAULT 'common',        -- Based on complexity/ingredients
                card_style TEXT DEFAULT 'standard',  -- Visual style unlocked
                -- Rating
                personal_rating INTEGER,             -- 1-5 stars
                notes TEXT,
                UNIQUE(family_member_id, recipe_id, recipe_source),
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
            );

            -- Weekly/daily goals
            CREATE TABLE IF NOT EXISTS member_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                goal_type TEXT NOT NULL,             -- 'daily', 'weekly', 'monthly'
                goal_category TEXT NOT NULL,         -- 'cooking', 'nutrition', 'budget', 'variety'
                target_value INTEGER NOT NULL,
                current_value INTEGER DEFAULT 0,
                description TEXT,
                xp_reward INTEGER DEFAULT 25,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
            );

            -- Cooking session log (for XP calculation)
            CREATE TABLE IF NOT EXISTS cooking_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                recipe_id TEXT NOT NULL,
                recipe_source TEXT DEFAULT 'local',
                recipe_name TEXT,
                cuisine TEXT,
                complexity INTEGER DEFAULT 5,        -- 1-10
                -- Session stats
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                duration_minutes INTEGER,
                servings_made INTEGER,
                -- XP earned
                base_xp INTEGER DEFAULT 0,
                streak_bonus_xp INTEGER DEFAULT 0,
                complexity_bonus_xp INTEGER DEFAULT 0,
                first_time_bonus_xp INTEGER DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                -- Needs impact
                hunger_restored INTEGER DEFAULT 0,
                social_restored INTEGER DEFAULT 0,
                fun_restored INTEGER DEFAULT 0,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
            );

            -- Level progression
            CREATE TABLE IF NOT EXISTS member_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL UNIQUE,
                total_xp INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                xp_to_next_level INTEGER DEFAULT 100,
                title TEXT DEFAULT 'Kitchen Novice',  -- Changes with level
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
            );

            -- ================================================================
            -- POTION ALCHEMY SYSTEM TABLES
            -- ================================================================

            -- Health effect definitions (the "potion effects")
            CREATE TABLE IF NOT EXISTS potion_effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                effect_name TEXT UNIQUE NOT NULL,
                effect_code TEXT UNIQUE NOT NULL,
                body_system TEXT NOT NULL,
                icon TEXT,
                color_hex TEXT,
                description TEXT,
                scientific_basis TEXT,
                potion_name_word TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- What nutrients/properties trigger which effects
            CREATE TABLE IF NOT EXISTS effect_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                effect_id INTEGER NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_field TEXT NOT NULL,
                trigger_value TEXT,
                min_threshold REAL,
                strength_weight REAL DEFAULT 1.0,
                FOREIGN KEY (effect_id) REFERENCES potion_effects(id)
            );

            -- Synergistic ingredient combinations
            CREATE TABLE IF NOT EXISTS ingredient_synergies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ingredient_a TEXT NOT NULL,
                ingredient_b TEXT NOT NULL,
                ingredient_c TEXT,
                effect_multiplier REAL DEFAULT 2.0,
                affected_effect_code TEXT,
                mechanism TEXT,
                discovery_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Brewing/preparation methods
            CREATE TABLE IF NOT EXISTS brewing_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                code TEXT UNIQUE NOT NULL,
                temp_category TEXT NOT NULL,
                icon TEXT,
                description TEXT,
                instructions TEXT,
                vitamin_c_retention REAL DEFAULT 1.0,
                fiber_preservation REAL DEFAULT 0.0,
                volatile_retention REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Saved potion recipes
            CREATE TABLE IF NOT EXISTS potion_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                auto_name TEXT,
                brewing_method_id INTEGER NOT NULL,
                ingredients_json TEXT NOT NULL,
                effects_json TEXT,
                synergies_json TEXT,
                times_brewed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brewing_method_id) REFERENCES brewing_methods(id)
            );

            -- User brewing progress (XP, discoveries)
            CREATE TABLE IF NOT EXISTS brewing_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_xp INTEGER DEFAULT 0,
                brewer_level INTEGER DEFAULT 1,
                brewer_title TEXT DEFAULT 'Apprentice Alchemist',
                potions_brewed INTEGER DEFAULT 0,
                recipes_discovered INTEGER DEFAULT 0,
                synergies_found TEXT DEFAULT '[]',
                achievements TEXT DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Alchemy ingredients with full health data
            CREATE TABLE IF NOT EXISTS alchemy_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                icon TEXT,
                color_hex TEXT,
                image_url TEXT,
                -- Default amounts
                default_amount_g REAL DEFAULT 10,
                max_daily_g REAL,
                typical_serving_g REAL,
                -- Macronutrients per 100g
                calories REAL DEFAULT 0,
                protein_g REAL DEFAULT 0,
                carbs_g REAL DEFAULT 0,
                fat_g REAL DEFAULT 0,
                fiber_g REAL DEFAULT 0,
                sugar_g REAL DEFAULT 0,
                -- Key vitamins per 100g
                vitamin_c_mg REAL DEFAULT 0,
                vitamin_a_mcg REAL DEFAULT 0,
                vitamin_d_mcg REAL DEFAULT 0,
                vitamin_e_mg REAL DEFAULT 0,
                vitamin_k_mcg REAL DEFAULT 0,
                vitamin_b1_mg REAL DEFAULT 0,
                vitamin_b2_mg REAL DEFAULT 0,
                vitamin_b6_mg REAL DEFAULT 0,
                vitamin_b12_mcg REAL DEFAULT 0,
                folate_mcg REAL DEFAULT 0,
                -- Key minerals per 100g
                calcium_mg REAL DEFAULT 0,
                iron_mg REAL DEFAULT 0,
                magnesium_mg REAL DEFAULT 0,
                zinc_mg REAL DEFAULT 0,
                potassium_mg REAL DEFAULT 0,
                sodium_mg REAL DEFAULT 0,
                selenium_mcg REAL DEFAULT 0,
                -- Health properties
                tcm_temperature TEXT,
                primary_effects TEXT,
                secondary_effects TEXT,
                bioactive_compounds TEXT,
                -- Flavor profile
                flavor_notes TEXT,
                pairs_well_with TEXT,
                avoid_with TEXT,
                -- Brewing properties
                best_brewing_method TEXT,
                steep_time_minutes REAL,
                water_temp_celsius REAL,
                -- Safety
                caffeine_mg REAL DEFAULT 0,
                is_adaptogen INTEGER DEFAULT 0,
                pregnancy_safe INTEGER DEFAULT 1,
                breastfeeding_safe INTEGER DEFAULT 1,
                -- Health scoring (Yuka-style 0-100)
                health_score INTEGER DEFAULT 80,
                -- Metadata
                description TEXT,
                scientific_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Safety warnings and contraindications
            CREATE TABLE IF NOT EXISTS ingredient_warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_name TEXT NOT NULL,
                warning_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                condition_or_medication TEXT,
                warning_text TEXT NOT NULL,
                scientific_basis TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Drug interactions
            CREATE TABLE IF NOT EXISTS ingredient_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_a TEXT NOT NULL,
                ingredient_b TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                effect_description TEXT,
                mechanism TEXT,
                recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ================================================================
            -- TESTING SYSTEM (for mobile app feature testing)
            -- ================================================================

            -- Test suites (groups of related tests by screen/feature)
            CREATE TABLE IF NOT EXISTS test_suites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suite_name TEXT NOT NULL,           -- "RecipesScreen", "PantryScreen", etc.
                description TEXT,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Test cases (individual tests within a suite)
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suite_id INTEGER NOT NULL,
                test_name TEXT NOT NULL,            -- "Recipe list loads"
                test_description TEXT NOT NULL,     -- "Verify recipe grid displays on launch"
                category TEXT,                      -- "ui", "api", "offline", "edge_case"
                platform TEXT DEFAULT 'both',       -- "web", "mobile", "both"
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
            );

            -- Test builds (versions of the app being tested)
            CREATE TABLE IF NOT EXISTS test_builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,       -- "1.0.1", "1.0.2"
                build_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                total_tests INTEGER DEFAULT 0,
                passed INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                needs_improvement INTEGER DEFAULT 0,
                not_tested INTEGER DEFAULT 0
            );

            -- Test results (outcomes of running tests on specific builds)
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id INTEGER NOT NULL,
                test_case_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('not_tested', 'pass', 'fail', 'needs_improvement')),
                notes TEXT,
                github_issue_url TEXT,
                tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tested_by TEXT DEFAULT 'manual',
                FOREIGN KEY (build_id) REFERENCES test_builds(id) ON DELETE CASCADE,
                FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
                UNIQUE(build_id, test_case_id)
            );

            -- Seed test suites (matching mobile app screens)
            INSERT OR IGNORE INTO test_suites (suite_name, description, display_order) VALUES
                ('RecipesScreen', 'Recipe browsing and search', 1),
                ('MealPlanScreen', 'Weekly meal planning', 2),
                ('ShoppingScreen', 'Shopping list management', 3),
                ('PantryScreen', 'Pantry inventory tracking', 4),
                ('NutritionScreen', 'Nutrition tracking and analytics', 5),
                ('CalendarScreen', 'Meal calendar view', 6),
                ('CookingScreen', 'Active cooking mode with timers', 7),
                ('EnhancedRecipeDetailScreen', 'Recipe detail page', 8),
                ('BulkReviewScreen', 'Bulk recipe review/approval', 9),
                ('DecksScreen', 'Recipe collections', 10),
                ('PantryProductDetailScreen', 'Product detail pages', 11),
                ('OfflineFunctionality', 'Offline data sync tests', 12),
                ('APIIntegration', 'MealDB and Flask API tests', 13),
                ('EdgeCases', 'Error handling and edge cases', 14);

            -- Create initial build version for current TestFlight app
            INSERT OR IGNORE INTO test_builds (version, notes) VALUES ('1.0.1', 'Initial TestFlight release');

            -- Insert default nutrition goals if not exists
            INSERT OR IGNORE INTO daily_nutrition_goals (id) VALUES (1);

            -- Insert FDA 2020 Daily Values reference (defaults used for % calculations)
            INSERT OR IGNORE INTO daily_values_reference (id, name) VALUES (1, 'FDA_2020');
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


@app.route("/recipe/mealdb/<meal_id>")
def recipe_detail_mealdb(meal_id):
    """Recipe detail page for MealDB recipes."""
    return render_template("recipe_mealdb.html", meal_id=meal_id)


@app.route("/ingredient/<ingredient_name>")
def ingredient_detail_page(ingredient_name):
    """Ingredient detail page."""
    return render_template("ingredient.html", ingredient_name=ingredient_name)


@app.route("/cook/mealdb/<meal_id>")
def cook_mealdb(meal_id):
    """Cooking page for MealDB recipes."""
    return render_template("cook_mealdb.html", meal_id=meal_id)


@app.route("/cook/<int:recipe_id>")
def cook(recipe_id):
    """Step-by-step cooking cards."""
    return render_template("cook.html", recipe_id=recipe_id)


@app.route("/shopping")
def shopping():
    """Shopping list page."""
    return render_template("shopping.html")


@app.route("/scanner")
def scanner():
    """Barcode scanner page."""
    return render_template("scanner.html")


@app.route("/pantry")
def pantry():
    """Pantry management page."""
    return render_template("pantry.html")


@app.route("/nutrition")
def nutrition():
    """Nutrition tracking page."""
    return render_template("nutrition.html")


@app.route("/meal")
def meal_planner():
    """Meal planner page."""
    return render_template("meal.html")


@app.route("/cook/meal")
def cook_meal():
    """Interleaved cooking view for multiple recipes."""
    recipe_ids = request.args.get("recipes", "")
    return render_template("cook_meal.html", recipe_ids=recipe_ids)


@app.route("/meal_plan")
def meal_plan_view():
    """Weekly meal planning page."""
    return render_template("meal_plan.html")


@app.route("/calendar_month")
def calendar_month_view():
    """Monthly calendar view."""
    return render_template("calendar_month.html")


@app.route("/calendar_week")
def calendar_week_view():
    """Weekly calendar view."""
    return render_template("calendar_week.html")


@app.route("/cook")
def cook_view():
    """Cooking mode default page."""
    return render_template("cook.html")


@app.route("/swipe")
def swipe_view():
    """Recipe swipe/review page."""
    return render_template("swipe.html")


@app.route("/discover_deck")
def discover_deck_view():
    """Recipe collections/decks page."""
    return render_template("discover_deck.html")


@app.route("/meal_prep")
def meal_prep_view():
    """Meal prep planning page."""
    return render_template("meal_prep.html")


@app.route("/family")
def family_view():
    """Family meal planning page."""
    return render_template("family.html")


@app.route("/game_dashboard")
def game_dashboard_view():
    """Gamification dashboard."""
    return render_template("game_dashboard.html")


@app.route("/alchemy")
def alchemy_view():
    """Recipe creation lab."""
    return render_template("alchemy.html")


@app.route("/personal_dashboard")
def personal_dashboard_view():
    """Personal analytics dashboard."""
    return render_template("personal_dashboard.html")


# ============================================================================
# API ROUTES - THEMEALDB (Real Recipe API)
# ============================================================================

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"


@app.route("/api/mealdb/search")
def api_mealdb_search():
    """Search TheMealDB for recipes."""
    query = request.args.get("q", "")
    try:
        response = requests.get(f"{MEALDB_BASE}/search.php?s={query}", timeout=10)
        data = response.json()
        meals = data.get("meals") or []
        return jsonify([format_mealdb_recipe(m) for m in meals])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mealdb/batch-random")
def api_mealdb_batch_random():
    """Get multiple random recipes in parallel - faster loading."""
    import concurrent.futures

    count = min(int(request.args.get("count", 8)), 12)

    def fetch_random():
        try:
            response = requests.get(f"{MEALDB_BASE}/random.php", timeout=5)
            data = response.json()
            if data.get("meals"):
                return format_mealdb_recipe(data["meals"][0])
        except:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(fetch_random) for _ in range(count)]
        recipes = [f.result() for f in concurrent.futures.as_completed(futures)]

    return jsonify([r for r in recipes if r])


@app.route("/api/mealdb/ingredient/<ingredient_name>")
def api_mealdb_ingredient(ingredient_name):
    """Get ingredient details from TheMealDB."""
    try:
        # Get ingredient image and basic info
        ingredient_data = {
            "name": ingredient_name,
            "image_url": f"https://www.themealdb.com/images/ingredients/{ingredient_name}.png",
            "image_small": f"https://www.themealdb.com/images/ingredients/{ingredient_name}-Small.png",
            "attributes": detect_ingredient_attributes(ingredient_name),
            "nutrition": estimate_nutrition(ingredient_name),
        }
        return jsonify(ingredient_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def detect_ingredient_attributes(name):
    """Detect ingredient attributes based on name."""
    name_lower = name.lower()
    attributes = []

    # Dietary attributes
    dairy = [
        "milk",
        "cheese",
        "cream",
        "butter",
        "yogurt",
        "yoghurt",
        "parmesan",
        "mozzarella",
        "cheddar",
        "feta",
    ]
    if any(d in name_lower for d in dairy):
        attributes.append({"name": "Dairy", "color": "#3498db"})

    meat = ["chicken", "beef", "pork", "lamb", "bacon", "sausage", "ham", "turkey", "duck", "veal"]
    if any(m in name_lower for m in meat):
        attributes.append({"name": "Meat", "color": "#e74c3c"})

    seafood = [
        "fish",
        "salmon",
        "tuna",
        "shrimp",
        "prawn",
        "cod",
        "crab",
        "lobster",
        "mussel",
        "clam",
        "anchov",
    ]
    if any(s in name_lower for s in seafood):
        attributes.append({"name": "Seafood", "color": "#1abc9c"})

    spicy = [
        "chilli",
        "chili",
        "pepper",
        "jalapeno",
        "cayenne",
        "paprika",
        "sriracha",
        "hot sauce",
        "wasabi",
    ]
    if any(s in name_lower for s in spicy):
        attributes.append({"name": "Spicy", "color": "#e67e22"})

    sweet = ["sugar", "honey", "maple", "chocolate", "vanilla", "caramel", "syrup", "molasses"]
    if any(s in name_lower for s in sweet):
        attributes.append({"name": "Sweet", "color": "#9b59b6"})

    nuts = ["almond", "walnut", "peanut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia"]
    if any(n in name_lower for n in nuts):
        attributes.append({"name": "Nuts", "color": "#795548"})

    gluten = ["flour", "bread", "pasta", "noodle", "wheat", "barley", "rye", "couscous"]
    if any(g in name_lower for g in gluten):
        attributes.append({"name": "Gluten", "color": "#ff9800"})

    vegan = ["tofu", "tempeh", "seitan", "nutritional yeast"]
    if any(v in name_lower for v in vegan):
        attributes.append({"name": "Vegan Protein", "color": "#4caf50"})

    # Vegetable/Fruit
    veggies = [
        "carrot",
        "onion",
        "garlic",
        "tomato",
        "potato",
        "lettuce",
        "spinach",
        "broccoli",
        "celery",
        "cucumber",
    ]
    if any(v in name_lower for v in veggies):
        attributes.append({"name": "Vegetable", "color": "#27ae60"})

    fruits = [
        "apple",
        "orange",
        "lemon",
        "lime",
        "banana",
        "berry",
        "mango",
        "pineapple",
        "grape",
        "melon",
    ]
    if any(f in name_lower for f in fruits):
        attributes.append({"name": "Fruit", "color": "#f39c12"})

    return attributes if attributes else [{"name": "Ingredient", "color": "#95a5a6"}]


def estimate_nutrition(name):
    """Estimate nutrition per 100g based on ingredient type."""
    name_lower = name.lower()

    # Default values
    nutrition = {"calories": 50, "protein": 2, "carbs": 10, "fat": 1, "fiber": 2}

    # Proteins
    if any(m in name_lower for m in ["chicken", "turkey"]):
        nutrition = {"calories": 165, "protein": 31, "carbs": 0, "fat": 4, "fiber": 0}
    elif any(m in name_lower for m in ["beef", "steak"]):
        nutrition = {"calories": 250, "protein": 26, "carbs": 0, "fat": 17, "fiber": 0}
    elif any(m in name_lower for m in ["pork", "bacon"]):
        nutrition = {"calories": 242, "protein": 27, "carbs": 0, "fat": 14, "fiber": 0}
    elif any(m in name_lower for m in ["salmon", "tuna", "fish"]):
        nutrition = {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0}
    elif "egg" in name_lower:
        nutrition = {"calories": 155, "protein": 13, "carbs": 1, "fat": 11, "fiber": 0}

    # Dairy
    elif any(d in name_lower for d in ["milk"]):
        nutrition = {"calories": 42, "protein": 3, "carbs": 5, "fat": 1, "fiber": 0}
    elif any(d in name_lower for d in ["cheese", "parmesan", "cheddar"]):
        nutrition = {"calories": 402, "protein": 25, "carbs": 1, "fat": 33, "fiber": 0}
    elif "butter" in name_lower:
        nutrition = {"calories": 717, "protein": 1, "carbs": 0, "fat": 81, "fiber": 0}

    # Carbs
    elif any(c in name_lower for c in ["rice"]):
        nutrition = {"calories": 130, "protein": 3, "carbs": 28, "fat": 0, "fiber": 0}
    elif any(c in name_lower for c in ["pasta", "noodle", "spaghetti"]):
        nutrition = {"calories": 131, "protein": 5, "carbs": 25, "fat": 1, "fiber": 2}
    elif any(c in name_lower for c in ["bread", "flour"]):
        nutrition = {"calories": 265, "protein": 9, "carbs": 49, "fat": 3, "fiber": 3}
    elif "potato" in name_lower:
        nutrition = {"calories": 77, "protein": 2, "carbs": 17, "fat": 0, "fiber": 2}

    # Vegetables
    elif any(v in name_lower for v in ["onion", "garlic"]):
        nutrition = {"calories": 40, "protein": 1, "carbs": 9, "fat": 0, "fiber": 2}
    elif any(v in name_lower for v in ["tomato"]):
        nutrition = {"calories": 18, "protein": 1, "carbs": 4, "fat": 0, "fiber": 1}
    elif any(v in name_lower for v in ["carrot"]):
        nutrition = {"calories": 41, "protein": 1, "carbs": 10, "fat": 0, "fiber": 3}
    elif any(v in name_lower for v in ["broccoli", "spinach", "lettuce"]):
        nutrition = {"calories": 25, "protein": 3, "carbs": 4, "fat": 0, "fiber": 3}

    # Oils/Fats
    elif any(o in name_lower for o in ["oil", "olive"]):
        nutrition = {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0}

    # Sugars
    elif "sugar" in name_lower:
        nutrition = {"calories": 387, "protein": 0, "carbs": 100, "fat": 0, "fiber": 0}
    elif "honey" in name_lower:
        nutrition = {"calories": 304, "protein": 0, "carbs": 82, "fat": 0, "fiber": 0}

    return nutrition


@app.route("/api/mealdb/random")
def api_mealdb_random():
    """Get random recipes from TheMealDB."""
    count = int(request.args.get("count", 10))
    recipes = []
    try:
        for _ in range(count):
            response = requests.get(f"{MEALDB_BASE}/random.php", timeout=5)
            data = response.json()
            if data.get("meals"):
                recipes.append(format_mealdb_recipe(data["meals"][0]))
        return jsonify(recipes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mealdb/categories")
def api_mealdb_categories():
    """Get all meal categories from TheMealDB."""
    try:
        response = requests.get(f"{MEALDB_BASE}/categories.php", timeout=10)
        data = response.json()
        return jsonify(data.get("categories") or [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mealdb/filter/<filter_type>/<value>")
def api_mealdb_filter(filter_type, value):
    """Filter recipes by category, area, or ingredient."""
    filter_map = {"category": "c", "area": "a", "ingredient": "i"}
    param = filter_map.get(filter_type, "c")
    try:
        response = requests.get(f"{MEALDB_BASE}/filter.php?{param}={value}", timeout=10)
        data = response.json()
        meals = data.get("meals") or []
        return jsonify(
            [
                {"id": m["idMeal"], "name": m["strMeal"], "image_url": m["strMealThumb"]}
                for m in meals
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mealdb/recipe/<meal_id>")
def api_mealdb_recipe(meal_id):
    """Get full recipe details from TheMealDB."""
    try:
        response = requests.get(f"{MEALDB_BASE}/lookup.php?i={meal_id}", timeout=10)
        data = response.json()
        if data.get("meals"):
            return jsonify(format_mealdb_recipe_full(data["meals"][0]))
        return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mealdb/areas")
def api_mealdb_areas():
    """Get all cuisine areas from TheMealDB."""
    try:
        response = requests.get(f"{MEALDB_BASE}/list.php?a=list", timeout=10)
        data = response.json()
        return jsonify(data.get("meals") or [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def format_mealdb_recipe(meal):
    """Format TheMealDB meal to our recipe format."""
    return {
        "id": meal["idMeal"],
        "name": meal["strMeal"],
        "description": (
            meal.get("strInstructions", "")[:200] + "..." if meal.get("strInstructions") else ""
        ),
        "category": meal.get("strCategory", ""),
        "cuisine": meal.get("strArea", ""),
        "image_url": meal.get("strMealThumb", ""),
        "youtube_url": meal.get("strYoutube", ""),
        "source_url": meal.get("strSource", ""),
        "tags": meal.get("strTags", "").split(",") if meal.get("strTags") else [],
        "is_mealdb": True,
    }


def format_mealdb_recipe_full(meal):
    """Format full TheMealDB meal with ingredients and steps."""
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            ingredients.append(
                {
                    "name": ing.strip(),
                    "quantity": measure.strip() if measure else "",
                    "image_url": f"https://www.themealdb.com/images/ingredients/{ing.strip()}.png",
                }
            )

    # Estimate servings based on meal type and name
    def estimate_servings(meal_name, category):
        """Intelligently estimate servings based on recipe type."""
        name_lower = meal_name.lower()

        # Cakes, pies, large desserts: 8-12 servings
        if any(word in name_lower for word in ["cake", "pie", "tart", "crumble", "cheesecake"]):
            return 10

        # Cookies, small desserts, individual items: 12-24 pieces
        if any(
            word in name_lower for word in ["cookie", "biscuit", "muffin", "cupcake", "brownie"]
        ):
            return 16

        # Desserts: typically 6-8 servings
        if category == "Dessert":
            return 8

        # Soups, stews, casseroles: 6-8 servings
        if any(word in name_lower for word in ["soup", "stew", "chili", "casserole", "curry"]):
            return 6

        # Pasta dishes: 6 servings (family-sized)
        if any(
            word in name_lower for word in ["pasta", "spaghetti", "lasagna", "ravioli", "penne"]
        ):
            return 6

        # Default main meals: 4 servings
        return 4

    # Better instruction parsing
    instructions = meal.get("strInstructions", "")

    # Clean up the text
    instructions = instructions.replace("\r\n", "\n").replace("\r", "\n")

    # Split by common patterns
    steps = []

    # Try splitting by "STEP X" pattern first
    step_pattern = re.split(r"STEP\s*\d+[:\.]?\s*", instructions, flags=re.IGNORECASE)
    step_pattern = [s.strip() for s in step_pattern if s.strip()]

    if len(step_pattern) > 1:
        # Recipe uses STEP numbering
        for i, step_text in enumerate(step_pattern):
            if step_text:
                steps.append(
                    {
                        "step_number": i + 1,
                        "title": f"Step {i + 1}",
                        "instruction": step_text.strip(),
                        "timer_needed": any(
                            word in step_text.lower()
                            for word in ["minute", "hour", "seconds", "mins", "hrs"]
                        ),
                    }
                )
    else:
        # Try splitting by numbered steps (1. 2. 3. etc)
        numbered = re.split(r"\n\s*\d+[.)\s]+", instructions)
        numbered = [s.strip() for s in numbered if s.strip()]

        if len(numbered) > 1:
            for i, step_text in enumerate(numbered):
                if step_text:
                    steps.append(
                        {
                            "step_number": i + 1,
                            "title": f"Step {i + 1}",
                            "instruction": step_text.strip(),
                            "timer_needed": any(
                                word in step_text.lower()
                                for word in ["minute", "hour", "seconds", "mins", "hrs"]
                            ),
                        }
                    )
        else:
            # Split by sentences/paragraphs for recipes with paragraph format
            paragraphs = [p.strip() for p in instructions.split("\n\n") if p.strip()]

            if len(paragraphs) > 1:
                for i, para in enumerate(paragraphs):
                    steps.append(
                        {
                            "step_number": i + 1,
                            "title": f"Step {i + 1}",
                            "instruction": para.strip(),
                            "timer_needed": any(
                                word in para.lower()
                                for word in ["minute", "hour", "seconds", "mins", "hrs"]
                            ),
                        }
                    )
            else:
                # Split long text by sentences, grouping 2-3 sentences per step
                sentences = re.split(r"(?<=[.!?])\s+", instructions)
                sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]

                # Group sentences (2-3 per step)
                step_num = 1
                current_step = []
                for sent in sentences:
                    current_step.append(sent)
                    if len(current_step) >= 2 or len(" ".join(current_step)) > 200:
                        steps.append(
                            {
                                "step_number": step_num,
                                "title": f"Step {step_num}",
                                "instruction": " ".join(current_step),
                                "timer_needed": any(
                                    word in " ".join(current_step).lower()
                                    for word in ["minute", "hour", "seconds", "mins", "hrs"]
                                ),
                            }
                        )
                        step_num += 1
                        current_step = []

                # Don't forget the last group
                if current_step:
                    steps.append(
                        {
                            "step_number": step_num,
                            "title": f"Step {step_num}",
                            "instruction": " ".join(current_step),
                            "timer_needed": any(
                                word in " ".join(current_step).lower()
                                for word in ["minute", "hour", "seconds", "mins", "hrs"]
                            ),
                        }
                    )

    # Fallback: if still no steps, create one
    if not steps and instructions:
        steps = [
            {
                "step_number": 1,
                "title": "Instructions",
                "instruction": instructions,
                "timer_needed": False,
            }
        ]

    return {
        "recipe": {
            "id": meal["idMeal"],
            "name": meal["strMeal"],
            "description": (
                meal.get("strInstructions", "")[:300] + "..."
                if len(meal.get("strInstructions", "")) > 300
                else meal.get("strInstructions", "")
            ),
            "category": meal.get("strCategory", ""),
            "cuisine": meal.get("strArea", ""),
            "image_url": meal.get("strMealThumb", ""),
            "youtube_url": meal.get("strYoutube", ""),
            "source_url": meal.get("strSource", ""),
            "tags": meal.get("strTags", "").split(",") if meal.get("strTags") else [],
            "servings": estimate_servings(meal["strMeal"], meal.get("strCategory", "")),
            "prep_time_min": 15,
            "cook_time_min": 30,
        },
        "ingredients": ingredients,
        "steps": steps,
        "nutrition_per_serving": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
        "is_mealdb": True,
    }


@app.route("/api/recipes")
def api_recipes():
    """List all recipes with optional filters."""
    db = get_db()
    category = request.args.get("category")
    cuisine = request.args.get("cuisine")
    difficulty = request.args.get("difficulty")
    quick = request.args.get("quick")  # Under 30 min total
    search = request.args.get("search")

    query = """
        SELECT id, name, description, category, cuisine,
               prep_time_min, cook_time_min, servings, difficulty, image_url
        FROM recipes WHERE 1=1
    """
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if cuisine:
        query += " AND cuisine = ?"
        params.append(cuisine)

    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)

    if quick == "true":
        query += " AND (prep_time_min + cook_time_min) <= 30"

    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY name"

    recipes = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in recipes])


@app.route("/api/recipes/categories")
def api_recipe_categories():
    """Get all recipe categories with counts."""
    db = get_db()
    categories = db.execute(
        """
        SELECT category, COUNT(*) as count
        FROM recipes
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    """
    ).fetchall()
    return jsonify([dict(c) for c in categories])


@app.route("/api/recipes/cuisines")
def api_recipe_cuisines():
    """Get all cuisines with counts."""
    db = get_db()
    cuisines = db.execute(
        """
        SELECT cuisine, COUNT(*) as count
        FROM recipes
        WHERE cuisine IS NOT NULL
        GROUP BY cuisine
        ORDER BY count DESC
    """
    ).fetchall()
    return jsonify([dict(c) for c in cuisines])


@app.route("/api/recipes/stats")
def api_recipe_stats():
    """Get recipe database statistics."""
    db = get_db()

    total_recipes = db.execute("SELECT COUNT(*) as count FROM recipes").fetchone()["count"]
    total_ingredients = db.execute("SELECT COUNT(*) as count FROM ingredients").fetchone()["count"]

    categories = db.execute(
        """
        SELECT category, COUNT(*) as count
        FROM recipes WHERE category IS NOT NULL
        GROUP BY category ORDER BY count DESC
    """
    ).fetchall()

    cuisines = db.execute(
        """
        SELECT cuisine, COUNT(*) as count
        FROM recipes WHERE cuisine IS NOT NULL
        GROUP BY cuisine ORDER BY count DESC
    """
    ).fetchall()

    quick_recipes = db.execute(
        """
        SELECT COUNT(*) as count FROM recipes
        WHERE (prep_time_min + cook_time_min) <= 30
    """
    ).fetchone()["count"]

    return jsonify(
        {
            "total_recipes": total_recipes,
            "total_ingredients": total_ingredients,
            "categories": [dict(c) for c in categories],
            "cuisines": [dict(c) for c in cuisines],
            "quick_recipes": quick_recipes,
        }
    )


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


def parse_ingredients_from_text(text):
    """Parse ingredients and amounts from instruction text.

    Handles formats like:
    - "10g chia seeds"
    - "5-7g walnuts"
    - "1 scoop whey protein"
    - "2 tbsp peanut butter"
    """
    ingredients = []

    # Pattern: amount (with optional range) + unit + ingredient name
    # Matches: "10g chia seeds", "5-7g walnuts", "150-200g milk", "1 scoop protein"
    patterns = [
        r"(\d+(?:-\d+)?)\s*(g|ml|oz|tbsp|tsp|cup|scoop|cups|jar)\s+([a-zA-Z][a-zA-Z\s]+?)(?:,|$|\.|and\s)",
        r"(\d+(?:\.\d+)?)\s*(g|ml|oz|tbsp|tsp|cup|scoop|cups)\s+([a-zA-Z][a-zA-Z\s]+?)(?:,|$|\.|and\s)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            amount_str, unit, name = match
            # Handle ranges like "5-7" by taking the higher value
            if "-" in amount_str:
                amount = float(amount_str.split("-")[1])
            else:
                amount = float(amount_str)

            # Clean up the ingredient name
            name = name.strip().rstrip(",").strip()
            if name and len(name) > 2:
                ingredients.append(
                    {
                        "name": name,
                        "amount": amount,
                        "unit": unit.lower(),
                        "amount_g": amount if unit.lower() == "g" else None,
                    }
                )

    return ingredients


# Helper functions for recipe creation
def auto_categorize_ingredient(name):
    """Auto-categorize ingredient based on name keywords."""
    name_lower = name.lower()

    CATEGORY_MAPPING = {
        "spice": [
            "seasoning",
            "paprika",
            "cumin",
            "cayenne",
            "pepper",
            "salt",
            "oregano",
            "thyme",
            "basil",
            "cajun",
            "flakes",
        ],
        "protein": ["chicken", "beef", "pork", "fish", "turkey", "lamb", "shrimp", "salmon"],
        "vegetable": [
            "broccoli",
            "carrot",
            "onion",
            "garlic",
            "spinach",
            "kale",
            "pepper",
            "tomato",
            "lettuce",
        ],
        "fruit": ["apple", "banana", "lemon", "lime", "orange", "berry", "grape"],
        "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "sour cream"],
        "pantry": ["oil", "vinegar", "honey", "sugar", "flour", "rice", "pasta", "bread"],
    }

    for category, keywords in CATEGORY_MAPPING.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    return "other"


def auto_map_aldi_section(category):
    """Map category to Aldi section."""
    ALDI_SECTION_MAP = {
        "protein": "Meat & Seafood",
        "vegetable": "Produce",
        "fruit": "Produce",
        "dairy": "Dairy & Eggs",
        "spice": "Pantry",
        "pantry": "Pantry",
        "frozen": "Frozen",
        "bakery": "Bakery",
        "other": "Pantry",
    }
    return ALDI_SECTION_MAP.get(category, "Pantry")


def auto_default_unit(category):
    """Determine default unit for category."""
    DEFAULT_UNIT_MAP = {
        "protein": "lb",
        "vegetable": "medium",
        "fruit": "medium",
        "spice": "tsp",
        "dairy": "cup",
        "pantry": "cup",
        "other": "item",
    }
    return DEFAULT_UNIT_MAP.get(category, "item")


def find_or_create_ingredient(cursor, name, category=None, aldi_section=None, default_unit=None):
    """Find ingredient by name or create if not exists. Returns ingredient_id."""
    # Search case-insensitive
    cursor.execute("SELECT id FROM ingredients WHERE LOWER(name) = LOWER(?)", [name])
    result = cursor.fetchone()

    if result:
        return result["id"]

    # Auto-categorize if not provided
    if not category:
        category = auto_categorize_ingredient(name)
    if not aldi_section:
        aldi_section = auto_map_aldi_section(category)
    if not default_unit:
        default_unit = auto_default_unit(category)

    cursor.execute(
        """
        INSERT INTO ingredients (name, category, aldi_section, default_unit)
        VALUES (?, ?, ?, ?)
    """,
        [name, category, aldi_section, default_unit],
    )

    return cursor.lastrowid


def validate_recipe_data(data):
    """Validate recipe request data. Returns list of errors or empty list if valid."""
    errors = []

    if "recipe" not in data:
        errors.append("Missing 'recipe' object")
        return errors

    recipe = data["recipe"]

    if not recipe.get("name"):
        errors.append("Recipe name is required")

    if "ingredients" not in data or not data["ingredients"]:
        errors.append("At least one ingredient is required")

    if "steps" not in data or not data["steps"]:
        errors.append("At least one cooking step is required")

    if recipe.get("difficulty") and recipe["difficulty"] not in ["easy", "medium", "hard"]:
        errors.append("Difficulty must be: easy, medium, or hard")

    return errors


@app.route("/api/recipes", methods=["POST"])
def create_recipe():
    """Create a new recipe with ingredients and cooking steps."""
    try:
        data = request.get_json()

        # Validate input
        errors = validate_recipe_data(data)
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        db = get_db()
        cursor = db.cursor()

        # Insert recipe
        recipe_data = data["recipe"]
        cursor.execute(
            """
            INSERT INTO recipes (name, description, category, cuisine,
                               prep_time_min, cook_time_min, servings, difficulty, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                recipe_data["name"],
                recipe_data.get("description"),
                recipe_data.get("category", "main"),
                recipe_data.get("cuisine"),
                recipe_data.get("prep_time_min", 0),
                recipe_data.get("cook_time_min", 0),
                recipe_data.get("servings", 4),
                recipe_data.get("difficulty", "easy"),
                recipe_data.get("image_url"),
            ],
        )

        recipe_id = cursor.lastrowid

        # Insert ingredients
        ingredient_count = 0
        for ing in data.get("ingredients", []):
            ing_id = find_or_create_ingredient(
                cursor,
                ing["name"],
                ing.get("category"),
                ing.get("aldi_section"),
                ing.get("default_unit"),
            )

            cursor.execute(
                """
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
                VALUES (?, ?, ?, ?, ?)
            """,
                [recipe_id, ing_id, ing["quantity"], ing["unit"], ing.get("notes")],
            )
            ingredient_count += 1

        # Insert cooking steps
        step_count = 0
        for step in data.get("steps", []):
            cursor.execute(
                """
                INSERT INTO cooking_steps (recipe_id, step_number, title, instruction,
                                          duration_min, tips, timer_needed, step_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    recipe_id,
                    step["step_number"],
                    step["title"],
                    step["instruction"],
                    step.get("duration_min"),
                    step.get("tips"),
                    step.get("timer_needed", 0),
                    step.get("step_type", "cook"),
                ],
            )
            step_count += 1

        db.commit()

        return (
            jsonify(
                {
                    "recipe_id": recipe_id,
                    "name": recipe_data["name"],
                    "ingredients_added": ingredient_count,
                    "steps_added": step_count,
                    "message": "Recipe created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/recipes/<int:recipe_id>/steps")
def api_recipe_steps(recipe_id):
    """Get cooking steps for card view."""
    db = get_db()

    recipe = db.execute("SELECT name FROM recipes WHERE id = ?", [recipe_id]).fetchone()
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404

    steps = db.execute(
        """
        SELECT step_number, title, instruction, duration_min, tips, timer_needed, step_type
        FROM cooking_steps
        WHERE recipe_id = ?
        ORDER BY step_number
    """,
        [recipe_id],
    ).fetchall()

    # Parse ingredients from each step and try to match with pantry
    steps_with_ingredients = []
    for step in steps:
        step_dict = dict(step)
        parsed = parse_ingredients_from_text(step["instruction"])

        # Try to match parsed ingredients with pantry inventory
        matched_ingredients = []
        for ing in parsed:
            # Search pantry products for a match
            product = db.execute(
                """
                SELECT pp.id as product_id, pp.name, pp.package_weight_g,
                       pi.id as inventory_id, pi.current_weight_g, pi.location
                FROM pantry_products pp
                LEFT JOIN pantry_inventory pi ON pp.id = pi.product_id
                WHERE LOWER(pp.name) LIKE ?
                ORDER BY pi.current_weight_g DESC
                LIMIT 1
                """,
                [f"%{ing['name'].lower()}%"],
            ).fetchone()

            if product:
                matched_ingredients.append(
                    {
                        "name": ing["name"],
                        "display_name": product["name"],
                        "amount": ing["amount"],
                        "unit": ing["unit"],
                        "amount_g": ing["amount_g"],
                        "product_id": product["product_id"],
                        "inventory_id": product["inventory_id"],
                        "in_stock": (
                            product["current_weight_g"] if product["current_weight_g"] else 0
                        ),
                    }
                )
            else:
                matched_ingredients.append(
                    {
                        "name": ing["name"],
                        "display_name": ing["name"].title(),
                        "amount": ing["amount"],
                        "unit": ing["unit"],
                        "amount_g": ing["amount_g"],
                        "product_id": None,
                        "inventory_id": None,
                        "in_stock": 0,
                    }
                )

        step_dict["ingredients"] = matched_ingredients
        steps_with_ingredients.append(step_dict)

    return jsonify(
        {
            "recipe_name": recipe["name"],
            "steps": steps_with_ingredients,
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
# API ROUTES - MEAL PLANNING
# ============================================================================


@app.route("/api/meal/recipes")
def api_meal_recipes():
    """Get recipes grouped by category for meal planning."""
    db = get_db()

    mains = db.execute(
        """
        SELECT id, name, description, prep_time_min, cook_time_min, servings, difficulty, image_url
        FROM recipes WHERE category = 'main'
        ORDER BY name
    """
    ).fetchall()

    sides = db.execute(
        """
        SELECT id, name, description, prep_time_min, cook_time_min, servings, difficulty, image_url
        FROM recipes WHERE category = 'side'
        ORDER BY name
    """
    ).fetchall()

    return jsonify({"mains": [dict(r) for r in mains], "sides": [dict(r) for r in sides]})


@app.route("/api/meal/schedule", methods=["POST"])
def api_meal_schedule():
    """Generate interleaved cooking schedule for multiple recipes."""
    db = get_db()
    data = request.json
    recipe_ids = data.get("recipe_ids", [])

    if not recipe_ids:
        return jsonify({"error": "No recipes provided"}), 400

    recipes_data = []
    all_ingredients = []

    for recipe_id in recipe_ids:
        recipe = db.execute("SELECT * FROM recipes WHERE id = ?", [recipe_id]).fetchone()
        if not recipe:
            continue

        steps = db.execute(
            """
            SELECT step_number, title, instruction, duration_min, tips, timer_needed, step_type
            FROM cooking_steps WHERE recipe_id = ?
            ORDER BY step_number
        """,
            [recipe_id],
        ).fetchall()

        ingredients = db.execute(
            """
            SELECT ri.quantity, ri.unit, ri.notes, i.name
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        """,
            [recipe_id],
        ).fetchall()

        total_time = sum(s["duration_min"] or 0 for s in steps)

        recipes_data.append(
            {
                "recipe": dict(recipe),
                "steps": [dict(s) for s in steps],
                "total_time": total_time,
                "ingredients": [dict(i) for i in ingredients],
            }
        )

        for ing in ingredients:
            all_ingredients.append(
                {
                    "name": ing["name"],
                    "quantity": ing["quantity"],
                    "unit": ing["unit"],
                    "notes": ing["notes"],
                    "recipe_name": recipe["name"],
                }
            )

    # Calculate start offsets (work backwards from serve time)
    max_time = max(r["total_time"] for r in recipes_data)

    for r in recipes_data:
        r["start_offset"] = max_time - r["total_time"]

    # Build interleaved timeline
    timeline = []

    for r in recipes_data:
        current_time = r["start_offset"]
        recipe = r["recipe"]

        for step in r["steps"]:
            timeline.append(
                {
                    "start_time": current_time,
                    "duration": step["duration_min"] or 0,
                    "title": step["title"],
                    "instruction": step["instruction"],
                    "tips": step["tips"],
                    "timer_needed": step["timer_needed"],
                    "step_type": step["step_type"] or "cook",
                    "recipe_id": recipe["id"],
                    "recipe_name": recipe["name"],
                    "step_number": step["step_number"],
                }
            )
            current_time += step["duration_min"] or 0

    # Sort by start time, then by recipe order for same-time steps
    timeline.sort(key=lambda x: (x["start_time"], recipe_ids.index(x["recipe_id"])))

    # Add step indices for display
    for i, step in enumerate(timeline):
        step["index"] = i + 1

    return jsonify(
        {
            "recipes": [
                {
                    "id": r["recipe"]["id"],
                    "name": r["recipe"]["name"],
                    "total_time": r["total_time"],
                    "start_offset": r["start_offset"],
                }
                for r in recipes_data
            ],
            "total_time": max_time,
            "timeline": timeline,
            "all_ingredients": all_ingredients,
        }
    )


# ============================================================================
# API ROUTES - MULTI-TIMER SYSTEM
# ============================================================================


@app.route("/api/timers", methods=["GET"])
def api_get_timers():
    """Get all active timers."""
    with timer_lock:
        now = datetime.now().timestamp()
        timers_list = []
        for timer_id, timer in active_timers.items():
            remaining = 0
            if timer["status"] == "running":
                elapsed = now - timer["started_at"]
                remaining = max(0, timer["duration"] - elapsed)
            elif timer["status"] == "paused":
                remaining = timer["remaining"]

            timers_list.append(
                {
                    "id": timer_id,
                    "name": timer["name"],
                    "duration": timer["duration"],
                    "remaining": round(remaining),
                    "status": timer["status"],
                    "recipe_id": timer.get("recipe_id"),
                    "step_number": timer.get("step_number"),
                }
            )
        return jsonify(timers_list)


@app.route("/api/timers", methods=["POST"])
def api_create_timer():
    """Create a new timer."""
    data = request.json
    timer_id = str(uuid.uuid4())[:8]

    with timer_lock:
        active_timers[timer_id] = {
            "name": data.get("name", "Timer"),
            "duration": data["duration"],  # in seconds
            "remaining": data["duration"],
            "status": "created",
            "started_at": None,
            "recipe_id": data.get("recipe_id"),
            "step_number": data.get("step_number"),
        }

    return jsonify({"id": timer_id, "success": True})


@app.route("/api/timers/<timer_id>/start", methods=["POST"])
def api_start_timer(timer_id):
    """Start or resume a timer."""
    with timer_lock:
        if timer_id not in active_timers:
            return jsonify({"error": "Timer not found"}), 404

        timer = active_timers[timer_id]
        if timer["status"] == "paused":
            timer["duration"] = timer["remaining"]
        timer["started_at"] = datetime.now().timestamp()
        timer["status"] = "running"

    return jsonify({"success": True})


@app.route("/api/timers/<timer_id>/pause", methods=["POST"])
def api_pause_timer(timer_id):
    """Pause a running timer."""
    with timer_lock:
        if timer_id not in active_timers:
            return jsonify({"error": "Timer not found"}), 404

        timer = active_timers[timer_id]
        if timer["status"] == "running":
            elapsed = datetime.now().timestamp() - timer["started_at"]
            timer["remaining"] = max(0, timer["duration"] - elapsed)
            timer["status"] = "paused"

    return jsonify({"success": True})


@app.route("/api/timers/<timer_id>/stop", methods=["POST"])
def api_stop_timer(timer_id):
    """Stop and remove a timer."""
    with timer_lock:
        if timer_id in active_timers:
            del active_timers[timer_id]
    return jsonify({"success": True})


@app.route("/api/timers/clear", methods=["POST"])
def api_clear_timers():
    """Clear all timers."""
    with timer_lock:
        active_timers.clear()
    return jsonify({"success": True})


# ============================================================================
# API ROUTES - MEATER SMART THERMOMETER (via Home Assistant)
# ============================================================================


def get_ha_entity_state(entity_id):
    """Fetch a single entity state from Home Assistant."""
    try:
        response = requests.get(
            f"{HA_URL}/api/states/{entity_id}",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"HA API error for {entity_id}: {e}")
        return None


@app.route("/api/meater/status")
def api_meater_status():
    """Get current Meater probe status from Home Assistant."""
    result = {
        "connected": False,
        "cooking": False,
        "internal_temp_c": None,
        "internal_temp_f": None,
        "ambient_temp_c": None,
        "ambient_temp_f": None,
        "target_temp_c": None,
        "target_temp_f": None,
        "peak_temp_c": None,
        "peak_temp_f": None,
        "time_remaining": None,
        "time_remaining_seconds": None,
        "time_elapsed": None,
        "cook_state": None,
        "cook_state_display": None,
    }

    # Fetch all Meater entities
    for key, entity_id in MEATER_ENTITIES.items():
        state_data = get_ha_entity_state(entity_id)
        if not state_data:
            continue

        state = state_data.get("state")
        if state == "unavailable" or state == "unknown":
            continue

        # Mark as connected if we get any valid data
        result["connected"] = True

        if key == "internal_temp":
            try:
                temp_c = float(state)
                result["internal_temp_c"] = round(temp_c, 1)
                result["internal_temp_f"] = round(temp_c * 9 / 5 + 32, 1)
            except (ValueError, TypeError):
                pass

        elif key == "ambient_temp":
            try:
                temp_c = float(state)
                result["ambient_temp_c"] = round(temp_c, 1)
                result["ambient_temp_f"] = round(temp_c * 9 / 5 + 32, 1)
            except (ValueError, TypeError):
                pass

        elif key == "target_temp":
            try:
                temp_c = float(state)
                result["target_temp_c"] = round(temp_c, 1)
                result["target_temp_f"] = round(temp_c * 9 / 5 + 32, 1)
            except (ValueError, TypeError):
                pass

        elif key == "peak_temp":
            try:
                temp_c = float(state)
                result["peak_temp_c"] = round(temp_c, 1)
                result["peak_temp_f"] = round(temp_c * 9 / 5 + 32, 1)
            except (ValueError, TypeError):
                pass

        elif key == "time_remaining":
            # This is a timestamp, parse to get seconds remaining
            result["time_remaining"] = state
            try:
                # Parse ISO timestamp and calculate seconds from now
                if state and state != "unknown":
                    from datetime import timezone

                    target_time = datetime.fromisoformat(state.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    remaining = (target_time - now).total_seconds()
                    result["time_remaining_seconds"] = max(0, int(remaining))
            except Exception as e:
                print(f"Time remaining parse error: {e}")

        elif key == "time_elapsed":
            result["time_elapsed"] = state

        elif key == "cook_state":
            result["cook_state"] = state
            # Human-friendly cook state
            state_map = {
                "not_started": "Not Started",
                "configured": "Configured",
                "started": "Cooking",
                "ready_for_resting": "Ready to Rest",
                "resting": "Resting",
                "slightly_underdone": "Slightly Underdone",
                "finished": "Done!",
                "slightly_overdone": "Slightly Overdone",
                "overcooked": "Overcooked",
            }
            result["cook_state_display"] = state_map.get(state, state)

        elif key == "cooking":
            result["cooking"] = state.lower() in ("on", "true", "1", "cooking")

    return jsonify(result)


@app.route("/api/meater/test")
def api_meater_test():
    """Test Home Assistant connection."""
    try:
        response = requests.get(
            f"{HA_URL}/api/",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        if response.status_code == 200:
            return jsonify(
                {
                    "success": True,
                    "message": "Connected to Home Assistant",
                    "ha_info": response.json(),
                }
            )
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                }
            ),
            response.status_code,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                }
            ),
            500,
        )


# ============================================================================
# API ROUTES - BARCODE SCANNER (Legacy - redirects to new pantry API)
# ============================================================================

# NOTE: Main barcode API is at /api/barcode/<barcode> in PANTRY section below


@app.route("/api/ingredients/barcode", methods=["POST"])
def api_add_ingredient_from_barcode():
    """Add ingredient to database from barcode lookup."""
    data = request.json
    barcode = data.get("barcode")

    if not barcode:
        return jsonify({"error": "Barcode required"}), 400

    # First look up the barcode
    try:
        response = requests.get(
            f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=5
        )
        off_data = response.json()

        if off_data.get("status") != 1:
            return jsonify({"error": "Product not found in OpenFoodFacts"}), 404

        product = off_data["product"]
        nutriments = product.get("nutriments", {})

        db = get_db()

        # Check if ingredient with this barcode already exists
        existing = db.execute(
            "SELECT id, name FROM ingredients WHERE barcode = ?", [barcode]
        ).fetchone()
        if existing:
            return jsonify(
                {
                    "success": True,
                    "ingredient_id": existing["id"],
                    "name": existing["name"],
                    "message": "Ingredient already exists",
                }
            )

        name = product.get("product_name", "Unknown Product")

        db.execute(
            """
            INSERT INTO ingredients (name, category, barcode, calories_per_100g,
                protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                name,
                "scanned",
                barcode,
                nutriments.get("energy-kcal_100g", 0),
                nutriments.get("proteins_100g", 0),
                nutriments.get("carbohydrates_100g", 0),
                nutriments.get("fat_100g", 0),
                nutriments.get("fiber_100g", 0),
            ],
        )
        db.commit()

        ingredient_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        return jsonify({"success": True, "ingredient_id": ingredient_id, "name": name})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        SELECT p.*, i.name, i.category, i.aldi_section,
               CAST(julianday(p.expires_at) - julianday('now') AS INTEGER) as days_until_expiry
        FROM pantry p
        JOIN ingredients i ON p.ingredient_id = i.id
        ORDER BY p.expires_at ASC NULLS LAST, i.category, i.name
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
        # Update quantity and image_url (if we have a new one and existing is NULL)
        new_image = data.get("image_url")
        if new_image:
            db.execute(
                "UPDATE pantry SET quantity = quantity + ?, image_url = COALESCE(image_url, ?) WHERE id = ?",
                [data.get("quantity", 1), new_image, existing["id"]],
            )
        else:
            db.execute(
                "UPDATE pantry SET quantity = quantity + ? WHERE id = ?",
                [data.get("quantity", 1), existing["id"]],
            )
        pantry_item_id = existing["id"]
    else:
        db.execute(
            """
            INSERT INTO pantry (ingredient_id, quantity, unit, expires_at, price, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            [
                ingredient_id,
                data.get("quantity", 1),
                data.get("unit", "item"),
                data.get("expires_at"),
                data.get("price"),
                data.get("image_url"),
            ],
        )
        pantry_item_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    db.commit()

    # Sync to profile service
    sync_to_profile(
        "pantry_add",
        name=data["name"],
        category=data.get("category", "pantry"),
        quantity=data.get("quantity", 1),
        unit=data.get("unit", "item"),
    )

    return jsonify({"success": True, "id": pantry_item_id})


@app.route("/api/pantry/<int:item_id>", methods=["PUT"])
def api_update_pantry(item_id):
    """Update pantry item quantity, expiry date, and price."""
    db = get_db()
    data = request.json

    # Get current quantity for history logging
    current = db.execute("SELECT quantity FROM pantry WHERE id = ?", [item_id]).fetchone()
    old_quantity = current["quantity"]
    new_quantity = data["quantity"]

    # Build update query based on provided fields
    update_fields = ["quantity = ?"]
    params = [new_quantity]

    if "expires_at" in data:
        update_fields.append("expires_at = ?")
        params.append(data.get("expires_at"))

    if "price" in data:
        update_fields.append("price = ?")
        params.append(data.get("price"))

    params.append(item_id)
    db.execute(f"UPDATE pantry SET {', '.join(update_fields)} WHERE id = ?", params)

    # Log to history
    quantity_change = new_quantity - old_quantity
    change_type = "restock" if quantity_change > 50 else "manual_update"

    db.execute(
        """
        INSERT INTO pantry_usage_history
        (pantry_item_id, quantity_change, quantity_before, quantity_after, change_type)
        VALUES (?, ?, ?, ?, ?)
    """,
        [item_id, quantity_change, old_quantity, new_quantity, change_type],
    )

    # If restocked, delete restock event
    if quantity_change > 50:
        db.execute(
            """
            DELETE FROM calendar_events
            WHERE pantry_item_id = ? AND event_type = 'restock'
        """,
            [item_id],
        )

    db.commit()
    return jsonify({"success": True})


@app.route("/api/pantry/<int:item_id>", methods=["DELETE"])
def api_delete_pantry(item_id):
    """Remove item from pantry."""
    db = get_db()
    db.execute("DELETE FROM pantry WHERE id = ?", [item_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/pantry/total-value")
def api_pantry_total_value():
    """Get total value of pantry items."""
    db = get_db()
    result = db.execute(
        """
        SELECT
            SUM(p.price) as total,
            COUNT(*) as items_with_price
        FROM pantry p
        WHERE p.price IS NOT NULL
    """
    ).fetchone()
    return jsonify({"total": result["total"] or 0, "items_with_price": result["items_with_price"]})


# ============================================================================
# PANTRY DEPLETION LOGIC
# ============================================================================


def daily_depletion_job():
    """Run at midnight to deplete all daily-use pantry items."""
    with app.app_context():
        db = get_db()
        today = date.today().isoformat()

        items = db.execute(
            """
            SELECT p.*, i.name, i.default_unit
            FROM pantry p
            JOIN ingredients i ON p.ingredient_id = i.id
            WHERE p.is_daily_use = 1
              AND (p.last_depletion_date IS NULL OR p.last_depletion_date != ?)
              AND p.quantity > 0
        """,
            [today],
        ).fetchall()

        for item in items:
            process_depletion(item, today)

        db.commit()
        print(f"[Depletion] Processed {len(items)} items")


def process_depletion(item, today):
    """Process depletion for a single item."""
    db = get_db()

    # Calculate new quantity
    new_quantity = max(0, item["quantity"] - item["daily_usage_rate"])

    # Log to history
    db.execute(
        """
        INSERT INTO pantry_usage_history
        (pantry_item_id, quantity_change, quantity_before, quantity_after, change_type)
        VALUES (?, ?, ?, ?, 'auto_depletion')
    """,
        [item["id"], -item["daily_usage_rate"], item["quantity"], new_quantity],
    )

    # Update pantry
    db.execute(
        """
        UPDATE pantry SET quantity = ?, last_depletion_date = ? WHERE id = ?
    """,
        [new_quantity, today, item["id"]],
    )

    # Check if restock needed
    days_remaining = (
        new_quantity / item["daily_usage_rate"] if item["daily_usage_rate"] > 0 else 999
    )

    if days_remaining <= item["restock_threshold_days"]:
        create_restock_event(item, days_remaining, new_quantity)


def create_restock_event(item, days_remaining, current_quantity):
    """Create or update calendar event for restocking."""
    db = get_db()

    # Check existing
    existing = db.execute(
        """
        SELECT id FROM calendar_events
        WHERE pantry_item_id = ? AND event_type = 'restock'
    """,
        [item["id"]],
    ).fetchone()

    description = f"Running low - {days_remaining:.1f} days remaining ({current_quantity:.0f}{item['unit']} left)"
    metadata = json.dumps({"days_remaining": days_remaining, "current_quantity": current_quantity})

    if existing:
        # Update existing event
        db.execute(
            """
            UPDATE calendar_events SET description = ?, event_metadata = ? WHERE id = ?
        """,
            [description, metadata, existing["id"]],
        )
    else:
        # Create new event for tomorrow 9am
        tomorrow = datetime.now() + timedelta(days=1)
        event_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

        db.execute(
            """
            INSERT INTO calendar_events
            (title, description, event_type, source, start_datetime, all_day, color, pantry_item_id, event_metadata)
            VALUES (?, ?, 'restock', 'food_app', ?, 0, '#ff5722', ?, ?)
        """,
            [f"Restock {item['name']}", description, event_time.isoformat(), item["id"], metadata],
        )


def catchup_depletion_job():
    """Catch up on missed depletions from server downtime."""
    with app.app_context():
        db = get_db()
        today = date.today()

        items = db.execute(
            """
            SELECT p.*, i.name, i.default_unit
            FROM pantry p
            JOIN ingredients i ON p.ingredient_id = i.id
            WHERE p.is_daily_use = 1
        """
        ).fetchall()

        for item in items:
            if not item["last_depletion_date"]:
                last_date = today - timedelta(days=1)
            else:
                last_date = date.fromisoformat(item["last_depletion_date"])

            days_missed = (today - last_date).days

            if days_missed > 0:
                total_depletion = item["daily_usage_rate"] * days_missed
                new_quantity = max(0, item["quantity"] - total_depletion)

                db.execute(
                    """
                    UPDATE pantry SET quantity = ?, last_depletion_date = ? WHERE id = ?
                """,
                    [new_quantity, today.isoformat(), item["id"]],
                )

                db.execute(
                    """
                    INSERT INTO pantry_usage_history
                    (pantry_item_id, quantity_change, quantity_before, quantity_after, change_type)
                    VALUES (?, ?, ?, ?, 'auto_depletion')
                """,
                    [item["id"], -total_depletion, item["quantity"], new_quantity],
                )

        db.commit()


def auto_learning_job():
    """Weekly: adjust usage rates based on restock history."""
    with app.app_context():
        db = get_db()
        cutoff = (date.today() - timedelta(days=30)).isoformat()

        items = db.execute(
            """
            SELECT DISTINCT pantry_item_id
            FROM pantry_usage_history
            WHERE logged_at >= ? AND change_type = 'restock'
        """,
            [cutoff],
        ).fetchall()

        for item_row in items:
            # Get restock history
            restocks = db.execute(
                """
                SELECT quantity_change, logged_at
                FROM pantry_usage_history
                WHERE pantry_item_id = ? AND change_type = 'restock'
                  AND logged_at >= ?
                ORDER BY logged_at ASC
            """,
                [item_row["pantry_item_id"], cutoff],
            ).fetchall()

            if len(restocks) >= 2:
                # Calculate average interval between restocks
                dates = [datetime.fromisoformat(r["logged_at"]) for r in restocks]
                intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                avg_days = sum(intervals) / len(intervals)
                avg_qty = sum(r["quantity_change"] for r in restocks) / len(restocks)

                calc_rate = avg_qty / avg_days

                item = db.execute(
                    "SELECT * FROM pantry WHERE id = ?", [item_row["pantry_item_id"]]
                ).fetchone()

                # Blend 70% new, 30% old (weighted learning)
                new_rate = (calc_rate * 0.7) + (item["daily_usage_rate"] * 0.3)

                db.execute(
                    """
                    UPDATE pantry SET daily_usage_rate = ? WHERE id = ?
                """,
                    [new_rate, item_row["pantry_item_id"]],
                )

        db.commit()


# ============================================================================
# API ROUTES - PANTRY DAILY-USE
# ============================================================================


@app.route("/api/pantry/<int:item_id>/daily-use", methods=["PUT"])
def api_toggle_daily_use(item_id):
    """Enable/disable daily-use tracking."""
    db = get_db()
    data = request.json

    update_fields = ["is_daily_use = ?"]
    params = [1 if data.get("is_daily_use") else 0]

    if "daily_usage_rate" in data:
        update_fields.append("daily_usage_rate = ?")
        params.append(data["daily_usage_rate"])

    if "restock_threshold_days" in data:
        update_fields.append("restock_threshold_days = ?")
        params.append(data["restock_threshold_days"])

    params.append(item_id)
    db.execute(f"UPDATE pantry SET {', '.join(update_fields)} WHERE id = ?", params)
    db.commit()

    return jsonify({"success": True})


@app.route("/api/pantry/daily-use", methods=["GET"])
def api_get_daily_use_items():
    """Get all daily-use items with projections."""
    db = get_db()
    items = db.execute(
        """
        SELECT p.*, i.name, i.default_unit
        FROM pantry p
        JOIN ingredients i ON p.ingredient_id = i.id
        WHERE p.is_daily_use = 1
        ORDER BY i.name
    """
    ).fetchall()

    result = []
    for item in items:
        days_remaining = (
            item["quantity"] / item["daily_usage_rate"] if item["daily_usage_rate"] > 0 else 999
        )
        depletion_date = date.today() + timedelta(days=int(days_remaining))

        result.append(
            {
                "id": item["id"],
                "name": item["name"],
                "quantity": item["quantity"],
                "unit": item["unit"] or item["default_unit"],
                "daily_usage_rate": item["daily_usage_rate"],
                "days_remaining": round(days_remaining, 1),
                "projected_depletion_date": depletion_date.isoformat(),
                "restock_threshold_days": item["restock_threshold_days"],
                "needs_restock": days_remaining <= item["restock_threshold_days"],
            }
        )

    return jsonify(result)


@app.route("/api/pantry/<int:item_id>/usage-history", methods=["GET"])
def api_usage_history(item_id):
    """Get usage history for an item."""
    db = get_db()
    history = db.execute(
        """
        SELECT h.*, i.name, i.default_unit
        FROM pantry_usage_history h
        JOIN pantry p ON h.pantry_item_id = p.id
        JOIN ingredients i ON p.ingredient_id = i.id
        WHERE h.pantry_item_id = ? AND h.logged_at >= datetime('now', '-30 days')
        ORDER BY h.logged_at DESC
        LIMIT 50
    """,
        [item_id],
    ).fetchall()

    return jsonify([dict(h) for h in history])


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

    # Get recipe name for profile sync
    recipe_name = "Unknown Recipe"
    if data.get("recipe_id"):
        recipe = db.execute("SELECT name FROM recipes WHERE id = ?", [data["recipe_id"]]).fetchone()
        if recipe:
            recipe_name = recipe["name"]

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

    # Sync to profile service
    sync_to_profile(
        "meal_log",
        recipe_name=recipe_name,
        meal_type=data.get("meal_type", "meal"),
        recipe_id=data.get("recipe_id"),
        servings=data.get("servings_eaten", 1),
        notes=data.get("notes"),
    )

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
# PAGE ROUTES - TINDER DISCOVERY
# ============================================================================


@app.route("/discover")
def discover():
    """Meal selection page - entry point for Tinder swiping."""
    return render_template("discover.html")


@app.route("/discover/<meal_type>")
def discover_deck(meal_type):
    """Deck selection page - choose cuisine, diet, or type."""
    return render_template("discover_deck.html", meal_type=meal_type)


@app.route("/discover/<meal_type>/<int:deck_id>")
def swipe(meal_type, deck_id):
    """Tinder-style swipe interface for a specific deck."""
    return render_template("swipe.html", meal_type=meal_type, deck_id=deck_id)


@app.route("/swipe/<meal_type>")
def swipe_meal(meal_type):
    """Simplified Tinder-style swipe interface - all recipes for a meal type."""
    return render_template("swipe_simple.html", meal_type=meal_type)


@app.route("/interested")
def interested():
    """View saved/interested recipes."""
    return render_template("interested.html")


@app.route("/cooking-deck")
def cooking_deck_page():
    """View tonight's cooking deck."""
    return render_template("cooking_deck.html")


@app.route("/tonights-menu")
def tonights_menu():
    """QR code menu for tonight's recipes."""
    return render_template("tonights_menu.html")


# ============================================================================
# API ROUTES - TINDER DISCOVERY
# ============================================================================


@app.route("/api/decks")
def api_decks():
    """Get all available decks grouped by type."""
    db = get_db()
    decks = db.execute(
        """
        SELECT id, name, deck_type, filter_category, filter_cuisine, filter_tags, icon, sort_order
        FROM decks WHERE is_active = 1
        ORDER BY deck_type, sort_order
    """
    ).fetchall()

    # Group by deck_type
    grouped = {}
    for deck in decks:
        dtype = deck["deck_type"]
        if dtype not in grouped:
            grouped[dtype] = []
        grouped[dtype].append(dict(deck))

    return jsonify({"decks": grouped, "type_order": ["culture", "diet", "type", "smart"]})


@app.route("/api/decks/<int:deck_id>")
def api_deck_detail(deck_id):
    """Get deck details."""
    db = get_db()
    deck = db.execute("SELECT * FROM decks WHERE id = ?", [deck_id]).fetchone()
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    return jsonify(dict(deck))


@app.route("/api/decks/<int:deck_id>/recipes")
def api_deck_recipes(deck_id):
    """Get recipes for a deck, excluding already-swiped ones."""
    db = get_db()
    deck = db.execute("SELECT * FROM decks WHERE id = ?", [deck_id]).fetchone()
    if not deck:
        return jsonify({"error": "Deck not found"}), 404

    # Get already-swiped recipe IDs
    swiped = db.execute("SELECT recipe_id FROM recipe_preferences").fetchall()
    swiped_ids = set(r["recipe_id"] for r in swiped)

    # Fetch from TheMealDB based on deck filters
    recipes = []
    try:
        if deck["filter_cuisine"]:
            # Filter by area/cuisine
            response = requests.get(
                f'{MEALDB_BASE}/filter.php?a={deck["filter_cuisine"]}', timeout=10
            )
            data = response.json()
            meals = data.get("meals") or []
        elif deck["filter_category"]:
            # Filter by category
            response = requests.get(
                f'{MEALDB_BASE}/filter.php?c={deck["filter_category"]}', timeout=10
            )
            data = response.json()
            meals = data.get("meals") or []
        elif deck["filter_tags"] and "random" in deck["filter_tags"]:
            # Random mix - get batch of random recipes
            import concurrent.futures

            def fetch_random():
                try:
                    resp = requests.get(f"{MEALDB_BASE}/random.php", timeout=5)
                    d = resp.json()
                    if d.get("meals"):
                        return d["meals"][0]
                except:
                    pass
                return None

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(fetch_random) for _ in range(10)]
                meals = [f.result() for f in concurrent.futures.as_completed(futures)]
                meals = [m for m in meals if m]
        else:
            meals = []

        # Filter out already-swiped and format
        for meal in meals:
            meal_id = meal.get("idMeal")
            if meal_id and meal_id not in swiped_ids:
                recipes.append(
                    {
                        "id": meal_id,
                        "name": meal.get("strMeal", ""),
                        "image_url": meal.get("strMealThumb", ""),
                        "category": deck.get("filter_category") or "",
                        "cuisine": deck.get("filter_cuisine") or "",
                    }
                )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"deck": dict(deck), "recipes": recipes[:20]})  # Limit to 20 at a time


@app.route("/api/recipes/swipe/<meal_type>")
def api_recipes_for_swipe(meal_type):
    """Get recipes for swiping based on meal type from local database (13k+ recipes).

    Meal type mappings to categories in recipes_large:
    - breakfast: breakfast category
    - lunch: lunch, main categories
    - dinner: dinner, main categories
    - snack: dessert, appetizer, snack, beverage categories
    """
    import random

    db = get_db()

    # Get already-swiped recipe IDs
    swiped = db.execute("SELECT recipe_id, recipe_source FROM recipe_preferences").fetchall()
    swiped_ids = set((r["recipe_id"], r["recipe_source"]) for r in swiped)

    # Map meal types to local categories
    meal_categories = {
        "breakfast": ["breakfast", "Breakfast"],
        "lunch": ["lunch", "Lunch", "main", "Main", "side", "Side"],
        "dinner": ["dinner", "Dinner", "main", "Main"],
        "snack": [
            "dessert",
            "Dessert",
            "appetizer",
            "Appetizer",
            "snack",
            "Snack",
            "beverage",
            "Beverage",
            "side",
            "Side",
        ],
    }

    categories = meal_categories.get(meal_type, ["main", "Main"])

    recipes = []

    try:
        # First, include custom recipes from the 'recipes' table (these have detailed cooking steps)
        custom_placeholders = ",".join("?" * len(categories))
        custom_query = f"""
            SELECT id, name, description, category, cuisine, image_url,
                   prep_time_min, cook_time_min, difficulty
            FROM recipes
            WHERE category IN ({custom_placeholders})
        """
        custom_rows = db.execute(custom_query, categories).fetchall()

        for row in custom_rows:
            recipe_id = str(row["id"])
            if (recipe_id, "custom") not in swiped_ids:
                image_url = (
                    row["image_url"]
                    or f"https://source.unsplash.com/400x300/?food,{row['category'] or 'dish'}"
                )
                recipes.append(
                    {
                        "id": recipe_id,
                        "name": row["name"],
                        "image_url": image_url,
                        "category": row["category"] or "main",
                        "cuisine": row["cuisine"] or "",
                        "source": "custom",
                        "description": row["description"],
                        "prep_time": row["prep_time_min"],
                        "cook_time": row["cook_time_min"],
                        "difficulty": row["difficulty"],
                        "has_steps": True,  # Custom recipes have detailed cooking steps
                    }
                )

        # Then, add recipes from recipes_large table
        large_placeholders = ",".join("?" * len(categories))
        query = f"""
            SELECT id, title, ingredients, category, cuisine, image_name
            FROM recipes_large
            WHERE LOWER(category) IN ({large_placeholders})
            ORDER BY RANDOM()
            LIMIT 100
        """
        lower_categories = [c.lower() for c in categories]
        rows = db.execute(query, lower_categories).fetchall()

        for row in rows:
            recipe_id = f"local_{row['id']}"
            if (recipe_id, "local") not in swiped_ids:
                image_url = f"https://source.unsplash.com/400x300/?food,{row['category'] or 'dish'}"
                recipes.append(
                    {
                        "id": recipe_id,
                        "name": row["title"],
                        "image_url": image_url,
                        "category": row["category"] or "main",
                        "cuisine": row["cuisine"] or "",
                        "source": "local",
                    }
                )

        # Put custom recipes first, then shuffle the rest
        custom_recipes = [r for r in recipes if r.get("source") == "custom"]
        other_recipes = [r for r in recipes if r.get("source") != "custom"]
        random.shuffle(other_recipes)
        recipes = custom_recipes + other_recipes

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(
        {
            "meal_type": meal_type,
            "recipes": recipes[:50],  # Return up to 50 recipes
            "total_available": len(recipes),
            "source": "local_database",
        }
    )


@app.route("/api/recipes/local/<int:recipe_id>")
def api_local_recipe_detail(recipe_id):
    """Get full details for a local recipe from recipes_large."""
    db = get_db()

    row = db.execute(
        """
        SELECT id, title, ingredients, instructions, cleaned_ingredients,
               image_name, category, cuisine, source
        FROM recipes_large WHERE id = ?
    """,
        [recipe_id],
    ).fetchone()

    if not row:
        return jsonify({"error": "Recipe not found"}), 404

    # Parse ingredients JSON
    try:
        ingredients = json.loads(row["ingredients"]) if row["ingredients"] else []
    except:
        ingredients = []

    return jsonify(
        {
            "id": row["id"],
            "title": row["title"],
            "ingredients": ingredients,
            "instructions": row["instructions"],
            "cleaned_ingredients": row["cleaned_ingredients"],
            "image_name": row["image_name"],
            "category": row["category"],
            "cuisine": row["cuisine"],
            "source": row["source"],
            "image_url": f"https://source.unsplash.com/400x300/?food,{row['category'] or 'dish'}",
        }
    )


@app.route("/api/swipe/left", methods=["POST"])
def api_swipe_left():
    """Record a dislike (swipe left)."""
    db = get_db()
    data = request.json

    db.execute(
        """
        INSERT INTO recipe_preferences (recipe_id, recipe_source, action, category, cuisine, tags)
        VALUES (?, ?, 'disliked', ?, ?, ?)
    """,
        [
            data["recipe_id"],
            data.get("recipe_source", "mealdb"),
            data.get("category"),
            data.get("cuisine"),
            data.get("tags"),
        ],
    )
    db.commit()

    return jsonify({"success": True})


@app.route("/api/swipe/right", methods=["POST"])
def api_swipe_right():
    """Record a like (swipe right) - add to interested list."""
    db = get_db()
    data = request.json

    # Record the preference
    db.execute(
        """
        INSERT INTO recipe_preferences (recipe_id, recipe_source, action, category, cuisine, tags)
        VALUES (?, ?, 'liked', ?, ?, ?)
    """,
        [
            data["recipe_id"],
            data.get("recipe_source", "mealdb"),
            data.get("category"),
            data.get("cuisine"),
            data.get("tags"),
        ],
    )

    # Add to interested list
    try:
        db.execute(
            """
            INSERT OR IGNORE INTO interested_recipes (recipe_id, recipe_source, name, image_url, category, cuisine, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                data["recipe_id"],
                data.get("recipe_source", "mealdb"),
                data.get("name"),
                data.get("image_url"),
                data.get("category"),
                data.get("cuisine"),
                data.get("tags"),
            ],
        )
    except:
        pass  # Ignore if already exists

    db.commit()
    return jsonify({"success": True})


@app.route("/api/swipe/up", methods=["POST"])
def api_swipe_up():
    """Record cook tonight (swipe up) - add to cooking deck."""
    db = get_db()
    data = request.json

    # Record the preference
    db.execute(
        """
        INSERT INTO recipe_preferences (recipe_id, recipe_source, action, category, cuisine, tags)
        VALUES (?, ?, 'cook_tonight', ?, ?, ?)
    """,
        [
            data["recipe_id"],
            data.get("recipe_source", "mealdb"),
            data.get("category"),
            data.get("cuisine"),
            data.get("tags"),
        ],
    )

    # Get next position
    pos = db.execute(
        """
        SELECT COALESCE(MAX(position), 0) + 1 as next_pos
        FROM cooking_deck WHERE scheduled_date = date('now') AND meal_type = ?
    """,
        [data["meal_type"]],
    ).fetchone()["next_pos"]

    # Add to cooking deck
    db.execute(
        """
        INSERT INTO cooking_deck (recipe_id, recipe_source, name, image_url, meal_type, position)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        [
            data["recipe_id"],
            data.get("recipe_source", "mealdb"),
            data.get("name"),
            data.get("image_url"),
            data["meal_type"],
            pos,
        ],
    )

    db.commit()
    return jsonify({"success": True, "position": pos})


@app.route("/api/interested")
def api_interested():
    """Get all interested (liked) recipes."""
    db = get_db()
    recipes = db.execute(
        """
        SELECT * FROM interested_recipes ORDER BY added_at DESC
    """
    ).fetchall()
    return jsonify([dict(r) for r in recipes])


@app.route("/api/interested/<recipe_id>", methods=["DELETE"])
def api_delete_interested(recipe_id):
    """Remove recipe from interested list."""
    db = get_db()
    db.execute("DELETE FROM interested_recipes WHERE recipe_id = ?", [recipe_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/cooking-deck")
def api_cooking_deck():
    """Get today's cooking deck, optionally filtered by meal type."""
    db = get_db()
    meal_type = request.args.get("meal_type")

    if meal_type:
        recipes = db.execute(
            """
            SELECT * FROM cooking_deck
            WHERE scheduled_date = date('now') AND meal_type = ?
            ORDER BY position
        """,
            [meal_type],
        ).fetchall()
    else:
        recipes = db.execute(
            """
            SELECT * FROM cooking_deck
            WHERE scheduled_date = date('now')
            ORDER BY meal_type, position
        """
        ).fetchall()

    # Group by meal type
    grouped = {}
    for r in recipes:
        mt = r["meal_type"]
        if mt not in grouped:
            grouped[mt] = []
        grouped[mt].append(dict(r))

    return jsonify({"meals": grouped, "meal_order": ["breakfast", "lunch", "dinner", "snack"]})


@app.route("/api/cooking-deck/<int:item_id>", methods=["DELETE"])
def api_delete_cooking_deck_item(item_id):
    """Remove item from cooking deck."""
    db = get_db()
    db.execute("DELETE FROM cooking_deck WHERE id = ?", [item_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/cooking-deck/<int:item_id>/complete", methods=["POST"])
def api_complete_cooking_deck_item(item_id):
    """Mark cooking deck item as completed."""
    db = get_db()
    db.execute("UPDATE cooking_deck SET completed = 1 WHERE id = ?", [item_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/preferences", methods=["GET"])
def api_get_preferences():
    """Get user preferences."""
    db = get_db()
    prefs = db.execute("SELECT * FROM user_preferences ORDER BY preference_type").fetchall()

    # Group by type
    grouped = {}
    for p in prefs:
        ptype = p["preference_type"]
        if ptype not in grouped:
            grouped[ptype] = []
        grouped[ptype].append(p["value"])

    return jsonify(grouped)


@app.route("/api/preferences", methods=["POST"])
def api_set_preferences():
    """Set user preferences."""
    db = get_db()
    data = request.json

    # Clear existing of this type and add new
    ptype = data["preference_type"]
    values = data["values"] if isinstance(data["values"], list) else [data["values"]]

    db.execute("DELETE FROM user_preferences WHERE preference_type = ?", [ptype])
    for val in values:
        db.execute(
            "INSERT INTO user_preferences (preference_type, value) VALUES (?, ?)", [ptype, val]
        )

    db.commit()
    return jsonify({"success": True})


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.route("/health")
@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "app": "food-app", "version": "2.0"})


# ============================================================================
# NUTRITION API (USDA FoodData Central)
# ============================================================================

# USDA FoodData Central API (free, no key required for basic search)
USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"
# You can get a free API key at https://fdc.nal.usda.gov/api-key-signup.html
# For now, we'll use the demo key which has rate limits
USDA_API_KEY = "DEMO_KEY"


def get_cached_nutrition(ingredient_name):
    """Get nutrition from local cache."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM nutrition_cache WHERE LOWER(ingredient_name) = LOWER(?)", (ingredient_name,)
    ).fetchone()
    if row:
        return dict(row)
    return None


def cache_nutrition(ingredient_name, nutrition_data):
    """Save nutrition to local cache."""
    db = get_db()
    try:
        db.execute(
            """
            INSERT OR REPLACE INTO nutrition_cache
            (ingredient_name, calories, protein, carbs, fat, fiber, sodium, sugar, serving_size_g, usda_fdc_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ingredient_name.lower(),
                nutrition_data.get("calories", 0),
                nutrition_data.get("protein", 0),
                nutrition_data.get("carbs", 0),
                nutrition_data.get("fat", 0),
                nutrition_data.get("fiber", 0),
                nutrition_data.get("sodium", 0),
                nutrition_data.get("sugar", 0),
                nutrition_data.get("serving_size_g", 100),
                nutrition_data.get("fdc_id", ""),
            ),
        )
        db.commit()
    except Exception as e:
        print(f"Error caching nutrition for {ingredient_name}: {e}")


def fetch_usda_nutrition(ingredient_name):
    """Fetch nutrition data from USDA FoodData Central API."""
    try:
        # Search for the ingredient
        search_url = f"{USDA_API_BASE}/foods/search"
        params = {
            "api_key": USDA_API_KEY,
            "query": ingredient_name,
            "pageSize": 5,
            "dataType": ["Foundation", "SR Legacy"],  # Prefer standard reference foods
        }

        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        foods = data.get("foods", [])

        if not foods:
            return None

        # Get the first (best) match
        food = foods[0]
        fdc_id = food.get("fdcId")

        # Extract nutrients from foodNutrients array
        nutrients = {}
        for nutrient in food.get("foodNutrients", []):
            name = nutrient.get("nutrientName", "").lower()
            value = nutrient.get("value", 0)

            if "energy" in name or "calories" in name:
                nutrients["calories"] = value
            elif name == "protein":
                nutrients["protein"] = value
            elif "carbohydrate" in name:
                nutrients["carbs"] = value
            elif "total lipid" in name or name == "fat":
                nutrients["fat"] = value
            elif "fiber" in name:
                nutrients["fiber"] = value
            elif "sodium" in name:
                nutrients["sodium"] = value
            elif "sugars" in name and "total" in name:
                nutrients["sugar"] = value

        nutrients["fdc_id"] = str(fdc_id)
        nutrients["serving_size_g"] = 100  # USDA values are per 100g
        nutrients["description"] = food.get("description", ingredient_name)

        return nutrients

    except Exception as e:
        print(f"Error fetching USDA data for {ingredient_name}: {e}")
        return None


def estimate_nutrition(ingredient_name):
    """Fallback nutrition estimates when USDA data not available.
    Returns estimated values per 100g based on ingredient category."""
    ing = ingredient_name.lower()

    # Category-based estimates (per 100g)
    if any(x in ing for x in ["chicken", "turkey", "poultry"]):
        return {
            "calories": 165,
            "protein": 31,
            "carbs": 0,
            "fat": 3.6,
            "fiber": 0,
            "sodium": 74,
            "sugar": 0,
        }
    elif any(x in ing for x in ["beef", "steak", "lamb", "pork"]):
        return {
            "calories": 250,
            "protein": 26,
            "carbs": 0,
            "fat": 15,
            "fiber": 0,
            "sodium": 72,
            "sugar": 0,
        }
    elif any(x in ing for x in ["fish", "salmon", "tuna", "cod", "haddock", "shrimp", "prawn"]):
        return {
            "calories": 140,
            "protein": 25,
            "carbs": 0,
            "fat": 4,
            "fiber": 0,
            "sodium": 500,
            "sugar": 0,
        }
    elif any(x in ing for x in ["egg"]):
        return {
            "calories": 155,
            "protein": 13,
            "carbs": 1.1,
            "fat": 11,
            "fiber": 0,
            "sodium": 124,
            "sugar": 1.1,
        }
    elif any(x in ing for x in ["milk", "cream"]):
        return {
            "calories": 60,
            "protein": 3.4,
            "carbs": 5,
            "fat": 3.2,
            "fiber": 0,
            "sodium": 40,
            "sugar": 5,
        }
    elif any(x in ing for x in ["cheese", "cheddar", "parmesan"]):
        return {
            "calories": 400,
            "protein": 25,
            "carbs": 1.3,
            "fat": 33,
            "fiber": 0,
            "sodium": 620,
            "sugar": 0.5,
        }
    elif any(x in ing for x in ["butter"]):
        return {
            "calories": 717,
            "protein": 0.9,
            "carbs": 0.1,
            "fat": 81,
            "fiber": 0,
            "sodium": 11,
            "sugar": 0.1,
        }
    elif any(x in ing for x in ["oil", "olive", "vegetable oil", "sunflower"]):
        return {
            "calories": 884,
            "protein": 0,
            "carbs": 0,
            "fat": 100,
            "fiber": 0,
            "sodium": 0,
            "sugar": 0,
        }
    elif any(x in ing for x in ["rice", "pasta", "noodle", "spaghetti"]):
        return {
            "calories": 130,
            "protein": 2.7,
            "carbs": 28,
            "fat": 0.3,
            "fiber": 0.4,
            "sodium": 1,
            "sugar": 0,
        }
    elif any(x in ing for x in ["bread", "toast"]):
        return {
            "calories": 265,
            "protein": 9,
            "carbs": 49,
            "fat": 3.2,
            "fiber": 2.7,
            "sodium": 491,
            "sugar": 5,
        }
    elif any(x in ing for x in ["flour"]):
        return {
            "calories": 364,
            "protein": 10,
            "carbs": 76,
            "fat": 1,
            "fiber": 2.7,
            "sodium": 2,
            "sugar": 0.3,
        }
    elif any(x in ing for x in ["sugar", "honey", "syrup"]):
        return {
            "calories": 387,
            "protein": 0,
            "carbs": 100,
            "fat": 0,
            "fiber": 0,
            "sodium": 0,
            "sugar": 100,
        }
    elif any(x in ing for x in ["onion", "garlic", "leek", "shallot"]):
        return {
            "calories": 40,
            "protein": 1.1,
            "carbs": 9,
            "fat": 0.1,
            "fiber": 1.7,
            "sodium": 4,
            "sugar": 4.2,
        }
    elif any(
        x in ing
        for x in [
            "tomato",
            "pepper",
            "capsicum",
            "cucumber",
            "courgette",
            "zucchini",
            "aubergine",
            "eggplant",
        ]
    ):
        return {
            "calories": 20,
            "protein": 1,
            "carbs": 4,
            "fat": 0.2,
            "fiber": 1.2,
            "sodium": 5,
            "sugar": 2.6,
        }
    elif any(x in ing for x in ["carrot", "potato", "parsnip", "turnip", "swede", "beetroot"]):
        return {
            "calories": 77,
            "protein": 2,
            "carbs": 17,
            "fat": 0.1,
            "fiber": 2.2,
            "sodium": 6,
            "sugar": 0.8,
        }
    elif any(
        x in ing for x in ["spinach", "lettuce", "kale", "cabbage", "broccoli", "cauliflower"]
    ):
        return {
            "calories": 25,
            "protein": 2.9,
            "carbs": 3.6,
            "fat": 0.4,
            "fiber": 2.2,
            "sodium": 79,
            "sugar": 0.4,
        }
    elif any(
        x in ing
        for x in [
            "apple",
            "pear",
            "orange",
            "banana",
            "grape",
            "berry",
            "strawberry",
            "lemon",
            "lime",
        ]
    ):
        return {
            "calories": 52,
            "protein": 0.3,
            "carbs": 14,
            "fat": 0.2,
            "fiber": 2.4,
            "sodium": 1,
            "sugar": 10,
        }
    elif any(
        x in ing
        for x in [
            "salt",
            "pepper",
            "spice",
            "curry",
            "cumin",
            "paprika",
            "chili",
            "coriander",
            "turmeric",
        ]
    ):
        return {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "sodium": 500,
            "sugar": 0,
        }
    elif any(x in ing for x in ["stock", "broth", "water"]):
        return {
            "calories": 5,
            "protein": 0.5,
            "carbs": 0.5,
            "fat": 0,
            "fiber": 0,
            "sodium": 300,
            "sugar": 0,
        }
    else:
        # Generic fallback
        return {
            "calories": 50,
            "protein": 2,
            "carbs": 8,
            "fat": 1,
            "fiber": 1,
            "sodium": 10,
            "sugar": 2,
        }


@app.route("/api/nutrition/ingredient/<ingredient_name>")
def api_nutrition_ingredient(ingredient_name):
    """Get nutrition data for a single ingredient (per 100g)."""
    # Check cache first
    cached = get_cached_nutrition(ingredient_name)
    if cached:
        return jsonify(
            {
                "source": "cache",
                "ingredient": ingredient_name,
                "per_100g": {
                    "calories": cached["calories"],
                    "protein": cached["protein"],
                    "carbs": cached["carbs"],
                    "fat": cached["fat"],
                    "fiber": cached["fiber"],
                    "sodium": cached["sodium"],
                    "sugar": cached["sugar"],
                },
            }
        )

    # Fetch from USDA
    usda_data = fetch_usda_nutrition(ingredient_name)
    if usda_data:
        # Cache it for future use
        cache_nutrition(ingredient_name, usda_data)
        return jsonify(
            {
                "source": "usda",
                "ingredient": ingredient_name,
                "usda_description": usda_data.get("description", ""),
                "per_100g": {
                    "calories": usda_data.get("calories", 0),
                    "protein": usda_data.get("protein", 0),
                    "carbs": usda_data.get("carbs", 0),
                    "fat": usda_data.get("fat", 0),
                    "fiber": usda_data.get("fiber", 0),
                    "sodium": usda_data.get("sodium", 0),
                    "sugar": usda_data.get("sugar", 0),
                },
            }
        )

    # Fallback to estimate
    estimated = estimate_nutrition(ingredient_name)
    return jsonify({"source": "estimate", "ingredient": ingredient_name, "per_100g": estimated})


@app.route("/api/nutrition/recipe", methods=["POST"])
def api_nutrition_recipe():
    """Calculate total nutrition for a recipe given ingredients list.

    Expects JSON body:
    {
        "ingredients": [
            {"name": "chicken breast", "quantity": "200g"},
            {"name": "rice", "quantity": "1 cup"},
            ...
        ],
        "servings": 4
    }

    Returns nutrition per serving.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    ingredients = data.get("ingredients", [])
    servings = data.get("servings", 4)

    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400

    # Measurement conversions to grams
    measurement_to_grams = {
        "cup": 240,
        "cups": 240,
        "tablespoon": 15,
        "tablespoons": 15,
        "tbsp": 15,
        "tbs": 15,
        "tblsp": 15,
        "teaspoon": 5,
        "teaspoons": 5,
        "tsp": 5,
        "ml": 1,
        "l": 1000,
        "liter": 1000,
        "litre": 1000,
        "g": 1,
        "gram": 1,
        "grams": 1,
        "kg": 1000,
        "kilogram": 1000,
        "oz": 28,
        "ounce": 28,
        "ounces": 28,
        "lb": 454,
        "lbs": 454,
        "pound": 454,
        "pounds": 454,
        "piece": 100,
        "pieces": 100,
        "slice": 30,
        "slices": 30,
        "clove": 3,
        "cloves": 3,
        "medium": 100,
        "large": 150,
        "small": 50,
        "pinch": 1,  # ~1 gram per pinch
        "dash": 0.5,
        "stick": 5,
        "pod": 1,
        "pods": 1,
    }

    # Ingredient-specific weights when no unit given (grams per item)
    ingredient_weights = {
        "egg": 50,
        "onion": 150,
        "garlic": 3,
        "lemon": 60,
        "lime": 60,
        "tomato": 120,
        "potato": 150,
        "carrot": 60,
        "apple": 180,
        "banana": 120,
        "chicken breast": 200,
        "pepper": 150,
        # Small items that shouldn't use size defaults
        "cinnamon stick": 3,
        "cinnamon": 3,
        "bay leaf": 0.5,
        "bay": 0.5,
        "cardamom": 1,
        "clove": 0.5,
        "star anise": 2,
        "peppercorn": 0.1,
        "vanilla pod": 5,
        "vanilla bean": 5,
        "chili": 10,
        "chilli": 10,
    }

    def parse_quantity(qty_str):
        """Parse quantity string to (number, unit)."""
        if not qty_str:
            return None, ""
        qty_str = qty_str.strip().lower()

        # Strip modifiers
        for mod in ["chopped", "diced", "sliced", "minced", "fresh", "dried", "ground"]:
            qty_str = qty_str.replace(mod, "").strip()

        # Handle fractions
        frac_match = re.match(r"^(\d+)?\s*(\d+)/(\d+)\s*(.*)$", qty_str)
        if frac_match:
            whole = int(frac_match.group(1)) if frac_match.group(1) else 0
            num = int(frac_match.group(2))
            denom = int(frac_match.group(3))
            return whole + num / denom, frac_match.group(4).strip()

        # Handle decimals/whole numbers
        num_match = re.match(r"^([\d.]+)\s*(.*)$", qty_str)
        if num_match:
            return float(num_match.group(1)), num_match.group(2).strip()

        return None, qty_str

    def convert_to_grams(quantity, ingredient_name):
        """Convert quantity to grams."""
        number, unit = parse_quantity(quantity)
        if number is None:
            return 1  # Minimal for "to taste" etc

        ing_lower = ingredient_name.lower()

        # Check ingredient-specific weights FIRST (for spices, herbs, small items)
        # This prevents "1 small cinnamon stick" from being parsed as 50g
        ing_specific_weight = None
        for key, weight in ingredient_weights.items():
            if key in ing_lower:
                ing_specific_weight = weight
                break

        # Try exact unit match (g, kg, cup, tbsp, etc.)
        grams_per_unit = measurement_to_grams.get(unit)

        # Try partial match on unit
        if not grams_per_unit:
            for key in measurement_to_grams:
                if key in unit:
                    grams_per_unit = measurement_to_grams[key]
                    break

        # If unit matched a SIZE word (small/medium/large) but we have ingredient-specific weight,
        # use ingredient weight instead (a "small cinnamon stick" is ~3g, not 50g)
        if grams_per_unit and unit in ["small", "medium", "large"] and ing_specific_weight:
            grams_per_unit = ing_specific_weight
        # If no unit matched, use ingredient-specific weight
        elif not grams_per_unit and ing_specific_weight:
            grams_per_unit = ing_specific_weight

        # Default for completely unknown
        if not grams_per_unit:
            grams_per_unit = 30

        return number * grams_per_unit

    # Calculate totals
    totals = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "fiber": 0,
        "sodium": 0,
        "sugar": 0,
    }
    ingredient_details = []

    for ing in ingredients:
        name = ing.get("name", "")
        quantity = ing.get("quantity", "")

        if not name:
            continue

        grams = convert_to_grams(quantity, name)

        # Get nutrition (cache or USDA or estimate)
        cached = get_cached_nutrition(name)
        if cached:
            nutrition = {
                "calories": cached["calories"],
                "protein": cached["protein"],
                "carbs": cached["carbs"],
                "fat": cached["fat"],
                "fiber": cached["fiber"],
                "sodium": cached["sodium"],
                "sugar": cached["sugar"],
            }
            source = "cache"
        else:
            usda_data = fetch_usda_nutrition(name)
            if usda_data:
                cache_nutrition(name, usda_data)
                nutrition = {
                    "calories": usda_data.get("calories", 0),
                    "protein": usda_data.get("protein", 0),
                    "carbs": usda_data.get("carbs", 0),
                    "fat": usda_data.get("fat", 0),
                    "fiber": usda_data.get("fiber", 0),
                    "sodium": usda_data.get("sodium", 0),
                    "sugar": usda_data.get("sugar", 0),
                }
                source = "usda"
            else:
                nutrition = estimate_nutrition(name)
                source = "estimate"

        # Scale by grams (nutrition is per 100g)
        factor = grams / 100

        ing_contribution = {
            "name": name,
            "quantity": quantity,
            "grams": round(grams, 1),
            "source": source,
            "contribution": {
                "calories": round(nutrition["calories"] * factor, 1),
                "protein": round(nutrition["protein"] * factor, 1),
                "carbs": round(nutrition["carbs"] * factor, 1),
                "fat": round(nutrition["fat"] * factor, 1),
                "fiber": round(nutrition["fiber"] * factor, 1),
                "sodium": round(nutrition["sodium"] * factor, 1),
                "sugar": round(nutrition["sugar"] * factor, 1),
            },
        }
        ingredient_details.append(ing_contribution)

        for key in totals:
            totals[key] += nutrition[key] * factor

    # Calculate per serving
    per_serving = {k: round(v / servings, 1) for k, v in totals.items()}

    # Daily value percentages (based on 2000 cal diet)
    daily_values = {
        "calories": 2000,
        "protein": 50,
        "carbs": 275,
        "fat": 78,
        "fiber": 28,
        "sodium": 2300,
        "sugar": 50,
    }

    dv_percent = {k: round((per_serving[k] / daily_values[k]) * 100) for k in daily_values}

    return jsonify(
        {
            "servings": servings,
            "total_recipe": {k: round(v, 1) for k, v in totals.items()},
            "per_serving": per_serving,
            "percent_daily_value": dv_percent,
            "ingredients": ingredient_details,
        }
    )


# ============================================================================
# PANTRY & BARCODE SCANNER API
# ============================================================================


def fetch_open_food_facts(barcode):
    """Fetch product info from Open Food Facts API."""
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                nutriments = product.get("nutriments", {})
                return {
                    "found": True,
                    "source": "open_food_facts",
                    "barcode": barcode,
                    "name": product.get("product_name", "Unknown Product"),
                    "brand": product.get("brands", ""),
                    "image_url": product.get("image_url", ""),
                    "category": (
                        product.get("categories_tags", [""])[0].replace("en:", "")
                        if product.get("categories_tags")
                        else ""
                    ),
                    "serving_size": product.get("serving_size", ""),
                    "serving_size_g": nutriments.get("serving_size", 100),
                    "package_weight_g": product.get("product_quantity", None),
                    # Nutrition per 100g
                    "calories": nutriments.get("energy-kcal_100g", 0),
                    "protein": nutriments.get("proteins_100g", 0),
                    "carbs": nutriments.get("carbohydrates_100g", 0),
                    "fat": nutriments.get("fat_100g", 0),
                    "fiber": nutriments.get("fiber_100g", 0),
                    "sodium": (
                        nutriments.get("sodium_100g", 0) * 1000
                        if nutriments.get("sodium_100g")
                        else 0
                    ),  # Convert g to mg
                    "sugar": nutriments.get("sugars_100g", 0),
                }
        return {"found": False, "barcode": barcode}
    except Exception as e:
        print(f"Open Food Facts error: {e}")
        return {"found": False, "barcode": barcode, "error": str(e)}


@app.route("/api/barcode/<barcode>")
def lookup_barcode(barcode):
    """Look up a barcode - check local DB first, then Open Food Facts."""
    db = get_db()

    # Check local database first
    product = db.execute("SELECT * FROM pantry_products WHERE barcode = ?", (barcode,)).fetchone()

    if product:
        return jsonify({"found": True, "source": "local", "product": dict(product)})

    # Try Open Food Facts
    off_result = fetch_open_food_facts(barcode)
    return jsonify(off_result)


@app.route("/api/pantry/products", methods=["GET"])
def get_pantry_products():
    """Get all pantry products (the product catalog)."""
    db = get_db()
    products = db.execute("SELECT * FROM pantry_products ORDER BY name").fetchall()
    return jsonify([dict(p) for p in products])


@app.route("/api/pantry/products", methods=["POST"])
def add_pantry_product():
    """Add a new product to the catalog (from barcode scan or manual entry)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    db = get_db()

    # Check if barcode already exists
    if data.get("barcode"):
        existing = db.execute(
            "SELECT id FROM pantry_products WHERE barcode = ?", (data["barcode"],)
        ).fetchone()
        if existing:
            return (
                jsonify(
                    {
                        "error": "Product with this barcode already exists",
                        "product_id": existing["id"],
                    }
                ),
                409,
            )

    cursor = db.execute(
        """
        INSERT INTO pantry_products (
            barcode, name, brand, category, image_url,
            calories, protein, carbs, fat, fiber, sodium, sugar,
            serving_size, serving_size_g, package_weight_g,
            price, price_source, data_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data.get("barcode"),
            data.get("name", "Unknown Product"),
            data.get("brand", ""),
            data.get("category", "pantry"),
            data.get("image_url", ""),
            data.get("calories", 0),
            data.get("protein", 0),
            data.get("carbs", 0),
            data.get("fat", 0),
            data.get("fiber", 0),
            data.get("sodium", 0),
            data.get("sugar", 0),
            data.get("serving_size", ""),
            data.get("serving_size_g", 100),
            data.get("package_weight_g"),
            data.get("price"),
            data.get("price_source", "manual"),
            data.get("data_source", "manual"),
        ),
    )
    db.commit()

    # Sync to profile service
    sync_to_profile(
        "pantry_add",
        name=data.get("name", "Unknown Product"),
        category=data.get("category", "pantry"),
        barcode=data.get("barcode"),
        brand=data.get("brand"),
    )

    return jsonify({"success": True, "product_id": cursor.lastrowid})


@app.route("/api/pantry/products/<int:product_id>", methods=["PUT"])
def update_pantry_product(product_id):
    """Update a product in the catalog."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    db = get_db()
    db.execute(
        """
        UPDATE pantry_products SET
            name = COALESCE(?, name),
            brand = COALESCE(?, brand),
            category = COALESCE(?, category),
            image_url = COALESCE(?, image_url),
            calories = COALESCE(?, calories),
            protein = COALESCE(?, protein),
            carbs = COALESCE(?, carbs),
            fat = COALESCE(?, fat),
            fiber = COALESCE(?, fiber),
            sodium = COALESCE(?, sodium),
            sugar = COALESCE(?, sugar),
            serving_size = COALESCE(?, serving_size),
            serving_size_g = COALESCE(?, serving_size_g),
            package_weight_g = COALESCE(?, package_weight_g),
            price = COALESCE(?, price),
            price_source = COALESCE(?, price_source),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (
            data.get("name"),
            data.get("brand"),
            data.get("category"),
            data.get("image_url"),
            data.get("calories"),
            data.get("protein"),
            data.get("carbs"),
            data.get("fat"),
            data.get("fiber"),
            data.get("sodium"),
            data.get("sugar"),
            data.get("serving_size"),
            data.get("serving_size_g"),
            data.get("package_weight_g"),
            data.get("price"),
            data.get("price_source"),
            product_id,
        ),
    )
    db.commit()
    return jsonify({"success": True})


@app.route("/api/pantry/inventory", methods=["GET"])
def get_pantry_inventory():
    """Get all items in inventory with product details."""
    location = request.args.get("location")  # Optional filter

    db = get_db()
    query = """
        SELECT
            i.*,
            p.name, p.brand, p.category, p.subcategory, p.storage_type,
            p.store, p.currency, p.price_per_kg,
            p.image_url,
            p.calories, p.protein, p.carbs, p.fat, p.fiber, p.sodium, p.sugar,
            p.saturated_fat,
            p.serving_size, p.serving_size_g, p.package_weight_g, p.package_unit,
            p.price, p.barcode,
            p.ingredient_id,
            CASE
                WHEN p.package_weight_g > 0 AND i.current_weight_g IS NOT NULL
                THEN ROUND((i.current_weight_g / p.package_weight_g) * 100, 1)
                ELSE NULL
            END as percent_remaining
        FROM pantry_inventory i
        JOIN pantry_products p ON i.product_id = p.id
    """

    if location:
        query += " WHERE i.location = ?"
        items = db.execute(query + " ORDER BY p.name", (location,)).fetchall()
    else:
        items = db.execute(query + " ORDER BY i.location, p.name").fetchall()

    return jsonify([dict(item) for item in items])


@app.route("/api/pantry/inventory", methods=["POST"])
def add_to_inventory():
    """Add a product to inventory (e.g., after scanning)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    product_id = data.get("product_id")
    if not product_id:
        return jsonify({"error": "product_id required"}), 400

    db = get_db()

    # Get product's package weight as default current weight
    product = db.execute(
        "SELECT package_weight_g FROM pantry_products WHERE id = ?", (product_id,)
    ).fetchone()

    default_weight = product["package_weight_g"] if product else None

    cursor = db.execute(
        """
        INSERT INTO pantry_inventory (
            product_id, location, current_weight_g,
            purchase_date, expiry_date, notes
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            product_id,
            data.get("location", "pantry"),
            data.get("current_weight_g", default_weight),
            data.get("purchase_date"),
            data.get("expiry_date"),
            data.get("notes", ""),
        ),
    )
    db.commit()

    return jsonify({"success": True, "inventory_id": cursor.lastrowid})


@app.route("/api/pantry/inventory/<int:inventory_id>", methods=["PUT"])
def update_inventory_item(inventory_id):
    """Update an inventory item (e.g., update current weight)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    db = get_db()
    db.execute(
        """
        UPDATE pantry_inventory SET
            location = COALESCE(?, location),
            current_weight_g = COALESCE(?, current_weight_g),
            expiry_date = COALESCE(?, expiry_date),
            opened_date = COALESCE(?, opened_date),
            is_opened = COALESCE(?, is_opened),
            notes = COALESCE(?, notes),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (
            data.get("location"),
            data.get("current_weight_g"),
            data.get("expiry_date"),
            data.get("opened_date"),
            data.get("is_opened"),
            data.get("notes"),
            inventory_id,
        ),
    )
    db.commit()
    return jsonify({"success": True})


@app.route("/api/pantry/inventory/<int:inventory_id>", methods=["DELETE"])
def delete_inventory_item(inventory_id):
    """Remove an item from inventory (used it up)."""
    db = get_db()
    db.execute("DELETE FROM pantry_inventory WHERE id = ?", (inventory_id,))
    db.commit()
    return jsonify({"success": True})


@app.route("/api/pantry/search")
def search_pantry_products():
    """Search for products by name (for autocomplete)."""
    query = request.args.get("q", "")
    if len(query) < 2:
        return jsonify([])

    db = get_db()

    # Search local products first
    local = db.execute(
        """
        SELECT id, name, brand, barcode, image_url, category
        FROM pantry_products
        WHERE name LIKE ? OR brand LIKE ?
        ORDER BY name
        LIMIT 20
    """,
        (f"%{query}%", f"%{query}%"),
    ).fetchall()

    results = [dict(p) for p in local]

    # Also search USDA for common ingredients
    try:
        usda_url = f"https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "api_key": "DEMO_KEY",
            "query": query,
            "dataType": ["Foundation", "SR Legacy"],
            "pageSize": 10,
        }
        response = requests.get(usda_url, params=params, timeout=5)
        if response.status_code == 200:
            usda_data = response.json()
            for food in usda_data.get("foods", [])[:5]:
                results.append(
                    {
                        "id": None,
                        "name": food.get("description", ""),
                        "brand": "USDA",
                        "barcode": None,
                        "image_url": None,
                        "category": "ingredient",
                        "source": "usda",
                        "fdc_id": food.get("fdcId"),
                    }
                )
    except:
        pass  # USDA search is optional

    return jsonify(results)


@app.route("/api/pantry/stats")
def get_pantry_stats():
    """Get pantry statistics."""
    db = get_db()

    stats = {
        "total_items": db.execute("SELECT COUNT(*) FROM pantry_inventory").fetchone()[0],
        "by_location": {},
        "low_stock": [],
        "expiring_soon": [],
    }

    # Count by location
    locations = db.execute(
        """
        SELECT location, COUNT(*) as count
        FROM pantry_inventory
        GROUP BY location
    """
    ).fetchall()
    stats["by_location"] = {loc["location"]: loc["count"] for loc in locations}

    # Low stock items (< 25% remaining)
    low = db.execute(
        """
        SELECT
            i.id, p.name, p.brand, i.current_weight_g, p.package_weight_g,
            ROUND((i.current_weight_g / p.package_weight_g) * 100, 1) as percent
        FROM pantry_inventory i
        JOIN pantry_products p ON i.product_id = p.id
        WHERE p.package_weight_g > 0
            AND i.current_weight_g IS NOT NULL
            AND (i.current_weight_g / p.package_weight_g) < 0.25
        ORDER BY percent ASC
        LIMIT 10
    """
    ).fetchall()
    stats["low_stock"] = [dict(item) for item in low]

    # Expiring soon (within 7 days)
    expiring = db.execute(
        """
        SELECT
            i.id, p.name, p.brand, i.expiry_date
        FROM pantry_inventory i
        JOIN pantry_products p ON i.product_id = p.id
        WHERE i.expiry_date IS NOT NULL
            AND i.expiry_date <= date('now', '+7 days')
            AND i.expiry_date >= date('now')
        ORDER BY i.expiry_date ASC
        LIMIT 10
    """
    ).fetchall()
    stats["expiring_soon"] = [dict(item) for item in expiring]

    return jsonify(stats)


# ============================================================================
# KITCHEN TOOLS API
# ============================================================================


@app.route("/api/kitchen/tools", methods=["GET"])
def get_kitchen_tools():
    """Get all kitchen tools (catalog)."""
    db = get_db()

    category = request.args.get("category")
    store = request.args.get("store")

    query = "SELECT * FROM kitchen_tools WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if store:
        query += " AND store = ?"
        params.append(store)

    query += " ORDER BY category, name"

    tools = db.execute(query, params).fetchall()
    return jsonify([dict(tool) for tool in tools])


@app.route("/api/kitchen/tools", methods=["POST"])
def add_kitchen_tool():
    """Add a new kitchen tool to catalog."""
    db = get_db()
    data = request.json

    required = ["name", "category"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "name and category required"}), 400

    cursor = db.execute(
        """
        INSERT INTO kitchen_tools (
            name, brand, store, category, subcategory, material, size,
            image_url, price, currency, condition, purchase_date, warranty_until,
            dishwasher_safe, oven_safe, max_temp_c, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data.get("name"),
            data.get("brand"),
            data.get("store"),
            data.get("category"),
            data.get("subcategory"),
            data.get("material"),
            data.get("size"),
            data.get("image_url"),
            data.get("price"),
            data.get("currency", "EUR"),
            data.get("condition", "good"),
            data.get("purchase_date"),
            data.get("warranty_until"),
            data.get("dishwasher_safe", 0),
            data.get("oven_safe", 0),
            data.get("max_temp_c"),
            data.get("notes"),
        ),
    )
    db.commit()

    return jsonify({"id": cursor.lastrowid, "message": "Tool added"})


@app.route("/api/kitchen/tools/<int:tool_id>", methods=["PUT"])
def update_kitchen_tool(tool_id):
    """Update a kitchen tool."""
    db = get_db()
    data = request.json

    db.execute(
        """
        UPDATE kitchen_tools SET
            name = COALESCE(?, name),
            brand = COALESCE(?, brand),
            store = COALESCE(?, store),
            category = COALESCE(?, category),
            subcategory = COALESCE(?, subcategory),
            material = COALESCE(?, material),
            size = COALESCE(?, size),
            image_url = COALESCE(?, image_url),
            price = COALESCE(?, price),
            condition = COALESCE(?, condition),
            dishwasher_safe = COALESCE(?, dishwasher_safe),
            oven_safe = COALESCE(?, oven_safe),
            max_temp_c = COALESCE(?, max_temp_c),
            notes = COALESCE(?, notes),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (
            data.get("name"),
            data.get("brand"),
            data.get("store"),
            data.get("category"),
            data.get("subcategory"),
            data.get("material"),
            data.get("size"),
            data.get("image_url"),
            data.get("price"),
            data.get("condition"),
            data.get("dishwasher_safe"),
            data.get("oven_safe"),
            data.get("max_temp_c"),
            data.get("notes"),
            tool_id,
        ),
    )
    db.commit()

    return jsonify({"message": "Tool updated"})


@app.route("/api/kitchen/tools/<int:tool_id>", methods=["DELETE"])
def delete_kitchen_tool(tool_id):
    """Delete a kitchen tool."""
    db = get_db()
    db.execute("DELETE FROM kitchen_tools WHERE id = ?", (tool_id,))
    db.commit()
    return jsonify({"message": "Tool deleted"})


@app.route("/api/kitchen/inventory", methods=["GET"])
def get_kitchen_inventory():
    """Get my owned kitchen tools."""
    db = get_db()

    location = request.args.get("location")
    category = request.args.get("category")

    query = """
        SELECT
            i.*,
            t.name, t.brand, t.store, t.category, t.subcategory,
            t.material, t.size, t.image_url, t.price, t.currency,
            t.dishwasher_safe, t.oven_safe, t.max_temp_c
        FROM kitchen_tools_inventory i
        JOIN kitchen_tools t ON i.tool_id = t.id
        WHERE 1=1
    """
    params = []

    if location:
        query += " AND i.location = ?"
        params.append(location)

    if category:
        query += " AND t.category = ?"
        params.append(category)

    query += " ORDER BY t.category, t.name"

    items = db.execute(query, params).fetchall()
    return jsonify([dict(item) for item in items])


@app.route("/api/kitchen/inventory", methods=["POST"])
def add_to_kitchen_inventory():
    """Add a tool to my inventory."""
    db = get_db()
    data = request.json

    tool_id = data.get("tool_id")
    if not tool_id:
        return jsonify({"error": "tool_id required"}), 400

    cursor = db.execute(
        """
        INSERT INTO kitchen_tools_inventory (
            tool_id, location, quantity, condition, notes
        ) VALUES (?, ?, ?, ?, ?)
    """,
        (
            tool_id,
            data.get("location", "kitchen"),
            data.get("quantity", 1),
            data.get("condition", "good"),
            data.get("notes"),
        ),
    )
    db.commit()

    return jsonify({"id": cursor.lastrowid, "message": "Added to inventory"})


@app.route("/api/kitchen/inventory/<int:inventory_id>", methods=["PUT"])
def update_kitchen_inventory(inventory_id):
    """Update a tool in my inventory."""
    db = get_db()
    data = request.json

    db.execute(
        """
        UPDATE kitchen_tools_inventory SET
            location = COALESCE(?, location),
            quantity = COALESCE(?, quantity),
            condition = COALESCE(?, condition),
            last_used = COALESCE(?, last_used),
            notes = COALESCE(?, notes),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (
            data.get("location"),
            data.get("quantity"),
            data.get("condition"),
            data.get("last_used"),
            data.get("notes"),
            inventory_id,
        ),
    )
    db.commit()

    return jsonify({"message": "Inventory updated"})


@app.route("/api/kitchen/inventory/<int:inventory_id>", methods=["DELETE"])
def delete_kitchen_inventory(inventory_id):
    """Remove a tool from my inventory."""
    db = get_db()
    db.execute("DELETE FROM kitchen_tools_inventory WHERE id = ?", (inventory_id,))
    db.commit()
    return jsonify({"message": "Removed from inventory"})


@app.route("/api/kitchen/stats")
def get_kitchen_stats():
    """Get kitchen tools statistics."""
    db = get_db()

    stats = {
        "total_tools": db.execute("SELECT COUNT(*) FROM kitchen_tools").fetchone()[0],
        "owned_tools": db.execute("SELECT COUNT(*) FROM kitchen_tools_inventory").fetchone()[0],
        "by_category": {},
        "by_store": {},
    }

    # Count by category
    categories = db.execute(
        """
        SELECT category, COUNT(*) as count
        FROM kitchen_tools
        GROUP BY category
        ORDER BY count DESC
    """
    ).fetchall()
    stats["by_category"] = {cat["category"]: cat["count"] for cat in categories}

    # Count by store
    stores = db.execute(
        """
        SELECT store, COUNT(*) as count
        FROM kitchen_tools
        WHERE store IS NOT NULL
        GROUP BY store
        ORDER BY count DESC
    """
    ).fetchall()
    stats["by_store"] = {s["store"]: s["count"] for s in stores}

    return jsonify(stats)


# ============================================================================
# COOKED MEALS & JOURNAL API
# ============================================================================


@app.route("/api/meals/cooked", methods=["GET"])
def get_cooked_meals():
    """Get all cooked meals with their ingredients."""
    db = get_db()
    date_filter = request.args.get("date")

    if date_filter:
        meals = db.execute(
            """
            SELECT * FROM cooked_meals
            WHERE DATE(cooked_at) = ?
            ORDER BY cooked_at DESC
        """,
            (date_filter,),
        ).fetchall()
    else:
        meals = db.execute(
            """
            SELECT * FROM cooked_meals
            ORDER BY cooked_at DESC
            LIMIT 50
        """
        ).fetchall()

    result = []
    for meal in meals:
        meal_dict = dict(meal)
        # Get ingredients for this meal
        ingredients = db.execute(
            """
            SELECT cmi.*, pp.name as product_name, pp.image_url
            FROM cooked_meal_ingredients cmi
            LEFT JOIN pantry_products pp ON cmi.product_id = pp.id
            WHERE cmi.cooked_meal_id = ?
        """,
            (meal["id"],),
        ).fetchall()
        meal_dict["ingredients"] = [dict(ing) for ing in ingredients]
        result.append(meal_dict)

    return jsonify(result)


@app.route("/api/meals/cooked", methods=["POST"])
def log_cooked_meal():
    """Log a cooked meal with ingredients used from pantry."""
    data = request.json
    db = get_db()

    # Create the meal record
    cursor = db.execute(
        """
        INSERT INTO cooked_meals (meal_name, meal_type, servings, recipe_id, recipe_source, notes, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data.get("meal_name"),
            data.get("meal_type", "dinner"),
            data.get("servings", 1),
            data.get("recipe_id"),
            data.get("recipe_source", "custom"),
            data.get("notes"),
            data.get("image_url"),
        ),
    )
    meal_id = cursor.lastrowid

    # Add ingredients used
    ingredients = data.get("ingredients", [])
    for ing in ingredients:
        db.execute(
            """
            INSERT INTO cooked_meal_ingredients (cooked_meal_id, inventory_id, product_id, ingredient_name, amount_used_g)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                meal_id,
                ing.get("inventory_id"),
                ing.get("product_id"),
                ing.get("ingredient_name"),
                ing.get("amount_used_g"),
            ),
        )

        # Optionally reduce inventory weight
        if ing.get("inventory_id") and ing.get("amount_used_g"):
            db.execute(
                """
                UPDATE pantry_inventory
                SET current_weight_g = MAX(0, COALESCE(current_weight_g, 0) - ?)
                WHERE id = ?
            """,
                (ing["amount_used_g"], ing["inventory_id"]),
            )

    # Add to journal
    today = datetime.now().strftime("%Y-%m-%d")
    db.execute(
        """
        INSERT INTO journal_entries (journal_date, entry_type, entry_data, source_app, source_id)
        VALUES (?, 'meal_cooked', ?, 'food', ?)
    """,
        (
            today,
            json.dumps({"meal_name": data.get("meal_name"), "meal_type": data.get("meal_type")}),
            meal_id,
        ),
    )

    db.commit()

    # Sync to profile service
    ingredient_names = [
        ing.get("ingredient_name") for ing in ingredients if ing.get("ingredient_name")
    ]
    sync_to_profile(
        "meal_log",
        recipe_name=data.get("meal_name"),
        meal_type=data.get("meal_type", "dinner"),
        recipe_id=data.get("recipe_id"),
        servings=data.get("servings", 1),
        ingredients=ingredient_names,
        notes=data.get("notes"),
    )

    return jsonify({"message": "Meal logged!", "meal_id": meal_id})


@app.route("/api/meals/cooked/<int:meal_id>", methods=["GET"])
def get_cooked_meal(meal_id):
    """Get a single cooked meal with details."""
    db = get_db()
    meal = db.execute("SELECT * FROM cooked_meals WHERE id = ?", (meal_id,)).fetchone()

    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    meal_dict = dict(meal)
    ingredients = db.execute(
        """
        SELECT cmi.*, pp.name as product_name, pp.image_url, pp.store
        FROM cooked_meal_ingredients cmi
        LEFT JOIN pantry_products pp ON cmi.product_id = pp.id
        WHERE cmi.cooked_meal_id = ?
    """,
        (meal_id,),
    ).fetchall()
    meal_dict["ingredients"] = [dict(ing) for ing in ingredients]

    return jsonify(meal_dict)


@app.route("/api/journal/today")
def get_today_journal():
    """Get all journal entries for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    return get_journal_for_date(today)


@app.route("/api/journal/<date>")
def get_journal_for_date(date):
    """Get all journal entries for a specific date."""
    db = get_db()

    # Get or create daily journal
    journal = db.execute("SELECT * FROM daily_journal WHERE journal_date = ?", (date,)).fetchone()

    if not journal:
        db.execute("INSERT INTO daily_journal (journal_date) VALUES (?)", (date,))
        db.commit()
        journal = db.execute(
            "SELECT * FROM daily_journal WHERE journal_date = ?", (date,)
        ).fetchone()

    result = dict(journal)

    # Get all entries for this date
    entries = db.execute(
        """
        SELECT * FROM journal_entries
        WHERE journal_date = ?
        ORDER BY created_at DESC
    """,
        (date,),
    ).fetchall()

    result["entries"] = [dict(e) for e in entries]

    # Group entries by type
    result["by_type"] = {}
    for entry in result["entries"]:
        entry_type = entry["entry_type"]
        if entry_type not in result["by_type"]:
            result["by_type"][entry_type] = []
        result["by_type"][entry_type].append(entry)

    # Get meals cooked today
    meals = db.execute(
        """
        SELECT cm.*,
               (SELECT COUNT(*) FROM cooked_meal_ingredients WHERE cooked_meal_id = cm.id) as ingredient_count
        FROM cooked_meals cm
        WHERE DATE(cm.cooked_at) = ?
        ORDER BY cm.cooked_at DESC
    """,
        (date,),
    ).fetchall()
    result["meals_cooked"] = [dict(m) for m in meals]

    # Get items added to pantry today
    pantry_added = db.execute(
        """
        SELECT pi.*, pp.name as product_name, pp.store, pp.image_url
        FROM pantry_inventory pi
        JOIN pantry_products pp ON pi.product_id = pp.id
        WHERE DATE(pi.created_at) = ?
        ORDER BY pi.created_at DESC
    """,
        (date,),
    ).fetchall()
    result["pantry_added"] = [dict(p) for p in pantry_added]

    return jsonify(result)


@app.route("/api/journal/entry", methods=["POST"])
def add_journal_entry():
    """Add a generic journal entry."""
    data = request.json
    db = get_db()

    journal_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    db.execute(
        """
        INSERT INTO journal_entries (journal_date, entry_type, entry_data, source_app, source_id)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            journal_date,
            data.get("entry_type"),
            json.dumps(data.get("entry_data", {})),
            data.get("source_app"),
            data.get("source_id"),
        ),
    )
    db.commit()

    return jsonify({"message": "Entry added!"})


@app.route("/api/journal/update", methods=["POST"])
def update_daily_journal():
    """Update daily journal summary, mood, energy."""
    data = request.json
    db = get_db()

    journal_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Get or create
    existing = db.execute(
        "SELECT id FROM daily_journal WHERE journal_date = ?", (journal_date,)
    ).fetchone()

    if existing:
        db.execute(
            """
            UPDATE daily_journal SET
                summary = COALESCE(?, summary),
                mood = COALESCE(?, mood),
                energy_level = COALESCE(?, energy_level),
                updated_at = CURRENT_TIMESTAMP
            WHERE journal_date = ?
        """,
            (
                data.get("summary"),
                data.get("mood"),
                data.get("energy_level"),
                journal_date,
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO daily_journal (journal_date, summary, mood, energy_level)
            VALUES (?, ?, ?, ?)
        """,
            (
                journal_date,
                data.get("summary"),
                data.get("mood"),
                data.get("energy_level"),
            ),
        )

    db.commit()
    return jsonify({"message": "Journal updated!"})


# ============================================================================
# NUTRITION & DAILY GOALS API
# ============================================================================


@app.route("/api/nutrition/goals", methods=["GET"])
def get_nutrition_goals():
    """Get user's daily nutrition goals."""
    db = get_db()
    goals = db.execute("SELECT * FROM daily_nutrition_goals WHERE id = 1").fetchone()
    if goals:
        return jsonify(dict(goals))
    return jsonify(
        {
            "calories": 2000,
            "protein_g": 50,
            "carbs_g": 250,
            "fat_g": 65,
            "fiber_g": 25,
            "sodium_mg": 2300,
            "sugar_g": 50,
        }
    )


@app.route("/api/nutrition/goals", methods=["PUT"])
def update_nutrition_goals():
    """Update user's daily nutrition goals."""
    data = request.json
    db = get_db()
    db.execute(
        """
        UPDATE daily_nutrition_goals SET
            calories = COALESCE(?, calories),
            protein_g = COALESCE(?, protein_g),
            carbs_g = COALESCE(?, carbs_g),
            fat_g = COALESCE(?, fat_g),
            fiber_g = COALESCE(?, fiber_g),
            sodium_mg = COALESCE(?, sodium_mg),
            sugar_g = COALESCE(?, sugar_g),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """,
        (
            data.get("calories"),
            data.get("protein_g"),
            data.get("carbs_g"),
            data.get("fat_g"),
            data.get("fiber_g"),
            data.get("sodium_mg"),
            data.get("sugar_g"),
        ),
    )
    db.commit()
    return jsonify({"message": "Goals updated!"})


@app.route("/api/nutrition/today")
def get_today_nutrition():
    """Get today's nutrition consumed vs goals."""
    from datetime import date

    today = date.today().isoformat()
    db = get_db()

    # Get goals
    goals = db.execute("SELECT * FROM daily_nutrition_goals WHERE id = 1").fetchone()

    # Get today's log or create if not exists
    log = db.execute("SELECT * FROM daily_nutrition_log WHERE log_date = ?", (today,)).fetchone()

    if not log:
        db.execute("INSERT INTO daily_nutrition_log (log_date) VALUES (?)", (today,))
        db.commit()
        log = db.execute(
            "SELECT * FROM daily_nutrition_log WHERE log_date = ?", (today,)
        ).fetchone()

    return jsonify(
        {
            "date": today,
            "goals": dict(goals) if goals else {},
            "consumed": dict(log) if log else {},
            "progress": {
                "calories": (
                    round((log["calories"] / goals["calories"]) * 100, 1)
                    if goals and goals["calories"]
                    else 0
                ),
                "protein_g": (
                    round((log["protein_g"] / goals["protein_g"]) * 100, 1)
                    if goals and goals["protein_g"]
                    else 0
                ),
                "carbs_g": (
                    round((log["carbs_g"] / goals["carbs_g"]) * 100, 1)
                    if goals and goals["carbs_g"]
                    else 0
                ),
                "fat_g": (
                    round((log["fat_g"] / goals["fat_g"]) * 100, 1)
                    if goals and goals["fat_g"]
                    else 0
                ),
            },
        }
    )


@app.route("/api/nutrition/<log_date>")
def get_nutrition_for_date(log_date):
    """Get nutrition for a specific date."""
    db = get_db()
    goals = db.execute("SELECT * FROM daily_nutrition_goals WHERE id = 1").fetchone()
    log = db.execute("SELECT * FROM daily_nutrition_log WHERE log_date = ?", (log_date,)).fetchone()

    return jsonify(
        {
            "date": log_date,
            "goals": dict(goals) if goals else {},
            "consumed": (
                dict(log) if log else {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
            ),
        }
    )


# ============================================================================
# COMPREHENSIVE MICRONUTRIENT API (USDA FoodData Central)
# ============================================================================

# USDA FoodData Central nutrient IDs mapping
USDA_NUTRIENT_MAP = {
    # Macros
    1008: "calories",
    1003: "protein_g",
    1004: "total_fat_g",
    1258: "saturated_fat_g",
    1257: "trans_fat_g",
    1253: "cholesterol_mg",
    1093: "sodium_mg",
    1005: "total_carbs_g",
    1079: "fiber_g",
    2000: "total_sugars_g",
    # Vitamins
    1106: "vitamin_a_mcg",  # RAE
    1162: "vitamin_c_mg",
    1114: "vitamin_d_mcg",
    1109: "vitamin_e_mg",
    1185: "vitamin_k_mcg",
    1165: "thiamin_mg",
    1166: "riboflavin_mg",
    1167: "niacin_mg",
    1175: "vitamin_b6_mg",
    1177: "folate_mcg",
    1178: "vitamin_b12_mcg",
    1176: "biotin_mcg",
    1170: "pantothenic_acid_mg",
    1180: "choline_mg",
    # Minerals
    1087: "calcium_mg",
    1089: "iron_mg",
    1091: "phosphorus_mg",
    1100: "iodine_mcg",
    1090: "magnesium_mg",
    1095: "zinc_mg",
    1103: "selenium_mcg",
    1098: "copper_mg",
    1101: "manganese_mg",
    1096: "chromium_mcg",
    1102: "molybdenum_mcg",
    1092: "potassium_mg",
}


def fetch_usda_nutrients(ingredient_name, amount_g=100):
    """
    Fetch comprehensive nutrient data from USDA FoodData Central.
    Returns nutrients scaled to the given amount (default 100g).
    Uses Foundation Foods or SR Legacy for best data quality.
    """
    import urllib.parse
    import urllib.request

    db = get_db()

    # Check cache first
    cached = db.execute(
        "SELECT * FROM ingredient_nutrients WHERE ingredient_name = ? COLLATE NOCASE",
        (ingredient_name,),
    ).fetchone()

    if cached:
        # Scale from 100g to requested amount
        scale = amount_g / 100.0
        result = dict(cached)
        for key in result:
            if (
                key not in ("id", "ingredient_name", "fdc_id", "data_source", "last_updated")
                and result[key]
            ):
                result[key] = round(result[key] * scale, 3)
        result["amount_g"] = amount_g
        result["from_cache"] = True
        return result

    # Search USDA FoodData Central (prefer Foundation Foods)
    search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key=DEMO_KEY&query={urllib.parse.quote(ingredient_name)}&pageSize=5&dataType=Foundation,SR%20Legacy"

    try:
        with urllib.request.urlopen(search_url, timeout=10) as response:
            data = json.loads(response.read().decode())

        if not data.get("foods"):
            return {
                "error": f'No USDA data found for "{ingredient_name}"',
                "ingredient_name": ingredient_name,
            }

        # Use first result
        food = data["foods"][0]
        fdc_id = food.get("fdcId")

        # Extract nutrients per 100g
        nutrients = {"ingredient_name": ingredient_name, "fdc_id": fdc_id, "data_source": "usda"}

        for nutrient in food.get("foodNutrients", []):
            nutrient_id = nutrient.get("nutrientId")
            if nutrient_id in USDA_NUTRIENT_MAP:
                field = USDA_NUTRIENT_MAP[nutrient_id]
                value = nutrient.get("value", 0)
                nutrients[field] = value

        # Cache the result (per 100g)
        columns = ", ".join(nutrients.keys())
        placeholders = ", ".join(["?" for _ in nutrients])
        db.execute(
            f"INSERT OR REPLACE INTO ingredient_nutrients ({columns}) VALUES ({placeholders})",
            list(nutrients.values()),
        )
        db.commit()

        # Scale to requested amount
        scale = amount_g / 100.0
        for key in nutrients:
            if key not in ("ingredient_name", "fdc_id", "data_source") and nutrients[key]:
                nutrients[key] = round(nutrients[key] * scale, 3)

        nutrients["amount_g"] = amount_g
        nutrients["from_cache"] = False
        nutrients["usda_description"] = food.get("description", "")

        return nutrients

    except Exception as e:
        return {"error": str(e), "ingredient_name": ingredient_name}


@app.route("/api/nutrition/micronutrients/ingredient/<ingredient_name>")
def get_ingredient_micronutrients(ingredient_name):
    """
    Get comprehensive micronutrient data for a single ingredient.
    Optional query param: amount_g (default 100)
    """
    amount_g = float(request.args.get("amount_g", 100))
    nutrients = fetch_usda_nutrients(ingredient_name, amount_g)

    if "error" in nutrients:
        return jsonify(nutrients), 404

    return jsonify(nutrients)


@app.route("/api/nutrition/micronutrients/recipe", methods=["POST"])
def get_recipe_micronutrients():
    """
    Calculate comprehensive micronutrients for a recipe.
    Body: { "ingredients": [{"name": "chicken breast", "amount_g": 200}, ...], "servings": 4 }
    Returns total and per-serving micronutrient breakdown.
    """
    data = request.json
    ingredients = data.get("ingredients", [])
    servings = data.get("servings", 1)

    # Initialize totals
    totals = {
        "calories": 0,
        "protein_g": 0,
        "total_fat_g": 0,
        "saturated_fat_g": 0,
        "cholesterol_mg": 0,
        "sodium_mg": 0,
        "total_carbs_g": 0,
        "fiber_g": 0,
        "total_sugars_g": 0,
        # Vitamins
        "vitamin_a_mcg": 0,
        "vitamin_c_mg": 0,
        "vitamin_d_mcg": 0,
        "vitamin_e_mg": 0,
        "vitamin_k_mcg": 0,
        "thiamin_mg": 0,
        "riboflavin_mg": 0,
        "niacin_mg": 0,
        "vitamin_b6_mg": 0,
        "folate_mcg": 0,
        "vitamin_b12_mcg": 0,
        "biotin_mcg": 0,
        "pantothenic_acid_mg": 0,
        "choline_mg": 0,
        # Minerals
        "calcium_mg": 0,
        "iron_mg": 0,
        "phosphorus_mg": 0,
        "iodine_mcg": 0,
        "magnesium_mg": 0,
        "zinc_mg": 0,
        "selenium_mcg": 0,
        "copper_mg": 0,
        "manganese_mg": 0,
        "chromium_mcg": 0,
        "molybdenum_mcg": 0,
        "potassium_mg": 0,
    }

    ingredient_results = []
    errors = []

    for ing in ingredients:
        name = ing.get("name", "")
        amount_g = float(ing.get("amount_g", 100))

        nutrients = fetch_usda_nutrients(name, amount_g)

        if "error" in nutrients:
            errors.append({"ingredient": name, "error": nutrients["error"]})
            continue

        ingredient_results.append({"name": name, "amount_g": amount_g, "nutrients": nutrients})

        # Add to totals
        for key in totals:
            if key in nutrients and nutrients[key]:
                totals[key] += nutrients[key]

    # Calculate per serving
    per_serving = {key: round(val / servings, 2) for key, val in totals.items()}

    # Get daily values for % calculation
    db = get_db()
    daily_values = db.execute("SELECT * FROM daily_values_reference WHERE id = 1").fetchone()

    # Calculate % daily value per serving
    percent_dv = {}
    if daily_values:
        dv = dict(daily_values)
        for key in per_serving:
            dv_key = key
            if dv_key in dv and dv[dv_key] and dv[dv_key] > 0:
                percent_dv[key] = round((per_serving[key] / dv[dv_key]) * 100, 1)

    return jsonify(
        {
            "servings": servings,
            "total": {key: round(val, 2) for key, val in totals.items()},
            "per_serving": per_serving,
            "percent_daily_value": percent_dv,
            "ingredients": ingredient_results,
            "errors": errors if errors else None,
        }
    )


@app.route("/api/nutrition/daily-values")
def get_daily_values():
    """
    Get FDA Daily Values reference (all 40+ nutrients).
    This is what your body needs in a day.
    """
    db = get_db()
    dv = db.execute("SELECT * FROM daily_values_reference WHERE id = 1").fetchone()

    if not dv:
        return jsonify({"error": "Daily values not initialized"}), 500

    dv_dict = dict(dv)

    # Organize by category for better display
    return jsonify(
        {
            "macronutrients": {
                "calories": {"value": dv_dict.get("calories", 2000), "unit": "kcal"},
                "total_fat": {"value": dv_dict.get("total_fat_g", 78), "unit": "g"},
                "saturated_fat": {"value": dv_dict.get("saturated_fat_g", 20), "unit": "g"},
                "trans_fat": {
                    "value": dv_dict.get("trans_fat_g", 0),
                    "unit": "g",
                    "note": "As low as possible",
                },
                "cholesterol": {"value": dv_dict.get("cholesterol_mg", 300), "unit": "mg"},
                "sodium": {"value": dv_dict.get("sodium_mg", 2300), "unit": "mg"},
                "total_carbs": {"value": dv_dict.get("total_carbs_g", 275), "unit": "g"},
                "fiber": {"value": dv_dict.get("fiber_g", 28), "unit": "g"},
                "total_sugars": {"value": dv_dict.get("total_sugars_g", 50), "unit": "g"},
                "added_sugars": {"value": dv_dict.get("added_sugars_g", 50), "unit": "g"},
                "protein": {"value": dv_dict.get("protein_g", 50), "unit": "g"},
            },
            "vitamins": {
                "vitamin_a": {"value": dv_dict.get("vitamin_a_mcg", 900), "unit": "mcg RAE"},
                "vitamin_c": {"value": dv_dict.get("vitamin_c_mg", 90), "unit": "mg"},
                "vitamin_d": {"value": dv_dict.get("vitamin_d_mcg", 20), "unit": "mcg"},
                "vitamin_e": {"value": dv_dict.get("vitamin_e_mg", 15), "unit": "mg"},
                "vitamin_k": {"value": dv_dict.get("vitamin_k_mcg", 120), "unit": "mcg"},
                "thiamin_b1": {"value": dv_dict.get("thiamin_mg", 1.2), "unit": "mg"},
                "riboflavin_b2": {"value": dv_dict.get("riboflavin_mg", 1.3), "unit": "mg"},
                "niacin_b3": {"value": dv_dict.get("niacin_mg", 16), "unit": "mg NE"},
                "vitamin_b6": {"value": dv_dict.get("vitamin_b6_mg", 1.7), "unit": "mg"},
                "folate_b9": {"value": dv_dict.get("folate_mcg", 400), "unit": "mcg DFE"},
                "vitamin_b12": {"value": dv_dict.get("vitamin_b12_mcg", 2.4), "unit": "mcg"},
                "biotin_b7": {"value": dv_dict.get("biotin_mcg", 30), "unit": "mcg"},
                "pantothenic_acid_b5": {
                    "value": dv_dict.get("pantothenic_acid_mg", 5),
                    "unit": "mg",
                },
                "choline": {"value": dv_dict.get("choline_mg", 550), "unit": "mg"},
            },
            "minerals": {
                "calcium": {"value": dv_dict.get("calcium_mg", 1300), "unit": "mg"},
                "iron": {"value": dv_dict.get("iron_mg", 18), "unit": "mg"},
                "phosphorus": {"value": dv_dict.get("phosphorus_mg", 1250), "unit": "mg"},
                "iodine": {"value": dv_dict.get("iodine_mcg", 150), "unit": "mcg"},
                "magnesium": {"value": dv_dict.get("magnesium_mg", 420), "unit": "mg"},
                "zinc": {"value": dv_dict.get("zinc_mg", 11), "unit": "mg"},
                "selenium": {"value": dv_dict.get("selenium_mcg", 55), "unit": "mcg"},
                "copper": {"value": dv_dict.get("copper_mg", 0.9), "unit": "mg"},
                "manganese": {"value": dv_dict.get("manganese_mg", 2.3), "unit": "mg"},
                "chromium": {"value": dv_dict.get("chromium_mcg", 35), "unit": "mcg"},
                "molybdenum": {"value": dv_dict.get("molybdenum_mcg", 45), "unit": "mcg"},
                "chloride": {"value": dv_dict.get("chloride_mg", 2300), "unit": "mg"},
                "potassium": {"value": dv_dict.get("potassium_mg", 4700), "unit": "mg"},
            },
            "additional": {
                "omega_3": {
                    "value": dv_dict.get("omega_3_g", 1.6),
                    "unit": "g",
                    "note": "ALA equivalent",
                },
                "omega_6": {"value": dv_dict.get("omega_6_g", 17), "unit": "g"},
            },
            "source": "FDA 2020 Daily Values",
            "reference_url": "https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels",
        }
    )


@app.route("/api/nutrition/micronutrients/today")
def get_micronutrients_today():
    """
    Get today's micronutrient consumption vs daily values.
    Shows what you've eaten and what you still need.
    """
    from datetime import date

    db = get_db()
    today = date.today().isoformat()

    # Get today's log
    log = db.execute(
        "SELECT * FROM daily_micronutrients_log WHERE log_date = ?", (today,)
    ).fetchone()

    # Get daily values
    dv = db.execute("SELECT * FROM daily_values_reference WHERE id = 1").fetchone()

    consumed = dict(log) if log else {}
    daily_values = dict(dv) if dv else {}

    # Calculate progress for each nutrient
    progress = {}
    nutrients_list = [
        "vitamin_a_mcg",
        "vitamin_c_mg",
        "vitamin_d_mcg",
        "vitamin_e_mg",
        "vitamin_k_mcg",
        "thiamin_mg",
        "riboflavin_mg",
        "niacin_mg",
        "vitamin_b6_mg",
        "folate_mcg",
        "vitamin_b12_mcg",
        "biotin_mcg",
        "pantothenic_acid_mg",
        "choline_mg",
        "calcium_mg",
        "iron_mg",
        "phosphorus_mg",
        "iodine_mcg",
        "magnesium_mg",
        "zinc_mg",
        "selenium_mcg",
        "copper_mg",
        "manganese_mg",
        "chromium_mcg",
        "molybdenum_mcg",
        "potassium_mg",
        "cholesterol_mg",
        "saturated_fat_g",
    ]

    for nutrient in nutrients_list:
        consumed_val = consumed.get(nutrient, 0) or 0
        dv_val = daily_values.get(nutrient, 0) or 0

        progress[nutrient] = {
            "consumed": round(consumed_val, 2),
            "daily_value": dv_val,
            "percent": round((consumed_val / dv_val * 100) if dv_val > 0 else 0, 1),
            "remaining": round(max(0, dv_val - consumed_val), 2),
            "status": (
                "good"
                if consumed_val >= dv_val * 0.8
                else ("low" if consumed_val < dv_val * 0.3 else "moderate")
            ),
        }

    # Group by category
    vitamins = {
        k: progress[k]
        for k in progress
        if "vitamin" in k
        or k
        in [
            "thiamin_mg",
            "riboflavin_mg",
            "niacin_mg",
            "folate_mcg",
            "biotin_mcg",
            "pantothenic_acid_mg",
            "choline_mg",
        ]
    }
    minerals = {
        k: progress[k]
        for k in progress
        if k not in vitamins and k not in ["cholesterol_mg", "saturated_fat_g"]
    }

    return jsonify(
        {
            "date": today,
            "vitamins": vitamins,
            "minerals": minerals,
            "cholesterol": progress.get("cholesterol_mg"),
            "saturated_fat": progress.get("saturated_fat_g"),
            "summary": {
                "vitamins_met": sum(1 for v in vitamins.values() if v["status"] == "good"),
                "vitamins_total": len(vitamins),
                "minerals_met": sum(1 for v in minerals.values() if v["status"] == "good"),
                "minerals_total": len(minerals),
            },
        }
    )


@app.route("/api/nutrition/micronutrients/log", methods=["POST"])
def log_micronutrients():
    """
    Add micronutrients from a meal to today's log.
    Body: { "nutrients": { "vitamin_c_mg": 45, "calcium_mg": 200, ... } }
    """
    from datetime import date

    data = request.json
    nutrients = data.get("nutrients", {})

    db = get_db()
    today = date.today().isoformat()

    # Get or create today's log
    existing = db.execute(
        "SELECT * FROM daily_micronutrients_log WHERE log_date = ?", (today,)
    ).fetchone()

    if existing:
        # Update existing - add to current values
        updates = []
        values = []
        for key, value in nutrients.items():
            if value and isinstance(value, (int, float)):
                updates.append(f"{key} = {key} + ?")
                values.append(value)

        if updates:
            values.append(today)
            db.execute(
                f"UPDATE daily_micronutrients_log SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE log_date = ?",
                values,
            )
    else:
        # Create new log
        columns = ["log_date"] + list(nutrients.keys())
        values = [today] + list(nutrients.values())
        placeholders = ", ".join(["?" for _ in values])
        db.execute(
            f"INSERT INTO daily_micronutrients_log ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )

    db.commit()

    return jsonify({"success": True, "date": today, "logged": nutrients})


@app.route("/api/nutrition/quick-meal", methods=["POST"])
def log_quick_meal():
    """
    Quick log a meal by ingredients - fetches USDA data and logs everything.
    Body: {
        "meal_name": "Eggs with cheese on toast",
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "egg", "amount_g": 100},
            {"name": "cheddar cheese", "amount_g": 30},
            {"name": "bread", "amount_g": 60}
        ]
    }
    Returns full nutrition breakdown with micronutrients.
    """
    from datetime import date

    data = request.json
    meal_name = data.get("meal_name", "Quick Meal")
    meal_type = data.get("meal_type", "snack")
    ingredients = data.get("ingredients", [])

    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400

    db = get_db()
    today = date.today().isoformat()

    # Fetch and aggregate all nutrients
    total_nutrients = {
        "calories": 0,
        "protein_g": 0,
        "carbohydrate_g": 0,
        "total_fat_g": 0,
        "fiber_g": 0,
        "sodium_mg": 0,
        "sugar_g": 0,
        "cholesterol_mg": 0,
        "saturated_fat_g": 0,
        "vitamin_a_mcg": 0,
        "vitamin_c_mg": 0,
        "vitamin_d_mcg": 0,
        "vitamin_e_mg": 0,
        "vitamin_k_mcg": 0,
        "thiamin_mg": 0,
        "riboflavin_mg": 0,
        "niacin_mg": 0,
        "vitamin_b6_mg": 0,
        "folate_mcg": 0,
        "vitamin_b12_mcg": 0,
        "pantothenic_acid_mg": 0,
        "choline_mg": 0,
        "calcium_mg": 0,
        "iron_mg": 0,
        "magnesium_mg": 0,
        "phosphorus_mg": 0,
        "potassium_mg": 0,
        "zinc_mg": 0,
        "copper_mg": 0,
        "manganese_mg": 0,
        "selenium_mcg": 0,
    }

    ingredient_details = []

    for ing in ingredients:
        name = ing.get("name", "")
        amount = ing.get("amount_g", 100)

        # Fetch from USDA
        nutrients = fetch_usda_nutrients(name, amount)
        if nutrients:
            ingredient_details.append({"name": name, "amount_g": amount, "nutrients": nutrients})

            # Aggregate
            for key in total_nutrients:
                if key in nutrients and nutrients[key]:
                    total_nutrients[key] += nutrients[key]

    # Log macros to daily_nutrition_log
    existing = db.execute(
        "SELECT * FROM daily_nutrition_log WHERE log_date = ?", (today,)
    ).fetchone()

    if existing:
        db.execute(
            """
            UPDATE daily_nutrition_log SET
                calories = calories + ?,
                protein_g = protein_g + ?,
                carbs_g = carbs_g + ?,
                fat_g = fat_g + ?,
                fiber_g = COALESCE(fiber_g, 0) + ?,
                sodium_mg = COALESCE(sodium_mg, 0) + ?,
                sugar_g = COALESCE(sugar_g, 0) + ?
            WHERE log_date = ?
        """,
            (
                total_nutrients["calories"],
                total_nutrients["protein_g"],
                total_nutrients["carbohydrate_g"],
                total_nutrients["total_fat_g"],
                total_nutrients["fiber_g"],
                total_nutrients["sodium_mg"],
                total_nutrients["sugar_g"],
                today,
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO daily_nutrition_log
            (log_date, calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg, sugar_g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                today,
                total_nutrients["calories"],
                total_nutrients["protein_g"],
                total_nutrients["carbohydrate_g"],
                total_nutrients["total_fat_g"],
                total_nutrients["fiber_g"],
                total_nutrients["sodium_mg"],
                total_nutrients["sugar_g"],
            ),
        )

    # Log micronutrients to daily_micronutrients_log
    micro_keys = [
        "vitamin_a_mcg",
        "vitamin_c_mg",
        "vitamin_d_mcg",
        "vitamin_e_mg",
        "vitamin_k_mcg",
        "thiamin_mg",
        "riboflavin_mg",
        "niacin_mg",
        "vitamin_b6_mg",
        "folate_mcg",
        "vitamin_b12_mcg",
        "pantothenic_acid_mg",
        "choline_mg",
        "calcium_mg",
        "iron_mg",
        "magnesium_mg",
        "phosphorus_mg",
        "potassium_mg",
        "zinc_mg",
        "copper_mg",
        "manganese_mg",
        "selenium_mcg",
        "cholesterol_mg",
        "saturated_fat_g",
    ]

    micro_existing = db.execute(
        "SELECT * FROM daily_micronutrients_log WHERE log_date = ?", (today,)
    ).fetchone()

    if micro_existing:
        updates = []
        values = []
        for key in micro_keys:
            val = total_nutrients.get(key, 0)
            if val:
                updates.append(f"{key} = COALESCE({key}, 0) + ?")
                values.append(val)
        if updates:
            values.append(today)
            db.execute(
                f"UPDATE daily_micronutrients_log SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE log_date = ?",
                values,
            )
    else:
        columns = ["log_date"]
        values = [today]
        for key in micro_keys:
            val = total_nutrients.get(key, 0)
            if val:
                columns.append(key)
                values.append(val)
        placeholders = ", ".join(["?" for _ in values])
        db.execute(
            f"INSERT INTO daily_micronutrients_log ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )

    db.commit()

    # Sync to profile service
    ingredient_names = [ing.get("name") for ing in ingredients if ing.get("name")]
    sync_to_profile(
        "meal_log",
        recipe_name=meal_name,
        meal_type=meal_type,
        calories=total_nutrients.get("calories"),
        protein=total_nutrients.get("protein_g"),
        carbs=total_nutrients.get("carbohydrate_g"),
        fat=total_nutrients.get("total_fat_g"),
        ingredients=ingredient_names,
    )

    return jsonify(
        {
            "success": True,
            "meal_name": meal_name,
            "meal_type": meal_type,
            "date": today,
            "ingredients": ingredient_details,
            "totals": total_nutrients,
        }
    )


# ============================================================================
# COMPLETED MEALS API (Fused meal cards)
# ============================================================================


@app.route("/api/meals/complete", methods=["POST"])
def complete_meal():
    """
    Complete a meal - fuse all dish and ingredient cards together.
    Deducts ingredients from inventory and adds nutrition to daily log.
    """
    data = request.json
    db = get_db()
    from datetime import date

    today = date.today().isoformat()

    # Calculate total nutrition from all dishes
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    total_fiber = 0
    total_sodium = 0
    total_sugar = 0

    dishes = data.get("dishes", [])
    for dish in dishes:
        total_calories += dish.get("calories", 0)
        total_protein += dish.get("protein_g", 0)
        total_carbs += dish.get("carbs_g", 0)
        total_fat += dish.get("fat_g", 0)
        total_fiber += dish.get("fiber_g", 0)
        total_sodium += dish.get("sodium_mg", 0)
        total_sugar += dish.get("sugar_g", 0)

    # Create the completed meal
    cursor = db.execute(
        """
        INSERT INTO completed_meals (
            meal_name, meal_type, servings,
            total_calories, total_protein_g, total_carbs_g, total_fat_g,
            total_fiber_g, total_sodium_mg, total_sugar_g,
            rating, notes, changes_for_next_time, image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data.get("meal_name"),
            data.get("meal_type", "dinner"),
            data.get("servings", 1),
            total_calories,
            total_protein,
            total_carbs,
            total_fat,
            total_fiber,
            total_sodium,
            total_sugar,
            data.get("rating"),
            data.get("notes"),
            data.get("changes_for_next_time"),
            data.get("image_url"),
        ),
    )
    meal_id = cursor.lastrowid

    # Insert individual dishes
    for dish in dishes:
        dish_cursor = db.execute(
            """
            INSERT INTO completed_meal_dishes (
                completed_meal_id, dish_name, dish_type, recipe_id, recipe_source,
                calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg, sugar_g
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                meal_id,
                dish.get("dish_name"),
                dish.get("dish_type"),
                dish.get("recipe_id"),
                dish.get("recipe_source"),
                dish.get("calories", 0),
                dish.get("protein_g", 0),
                dish.get("carbs_g", 0),
                dish.get("fat_g", 0),
                dish.get("fiber_g", 0),
                dish.get("sodium_mg", 0),
                dish.get("sugar_g", 0),
            ),
        )
        dish_id = dish_cursor.lastrowid

        # Insert ingredients for this dish
        for ing in dish.get("ingredients", []):
            db.execute(
                """
                INSERT INTO completed_meal_ingredients (
                    completed_meal_id, dish_id, inventory_id, product_id,
                    ingredient_name, amount_used_g, step_id,
                    calories, protein_g, carbs_g, fat_g
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    meal_id,
                    dish_id,
                    ing.get("inventory_id"),
                    ing.get("product_id"),
                    ing.get("ingredient_name"),
                    ing.get("amount_used_g"),
                    ing.get("step_id"),
                    ing.get("calories", 0),
                    ing.get("protein_g", 0),
                    ing.get("carbs_g", 0),
                    ing.get("fat_g", 0),
                ),
            )

            # Deduct from inventory if inventory_id provided
            if ing.get("inventory_id") and ing.get("amount_used_g"):
                db.execute(
                    """
                    UPDATE pantry_inventory
                    SET current_weight_g = MAX(0, COALESCE(current_weight_g, 0) - ?)
                    WHERE id = ?
                """,
                    (ing["amount_used_g"], ing["inventory_id"]),
                )

    # Update daily nutrition log
    existing = db.execute(
        "SELECT id FROM daily_nutrition_log WHERE log_date = ?", (today,)
    ).fetchone()

    if existing:
        db.execute(
            """
            UPDATE daily_nutrition_log SET
                calories = calories + ?,
                protein_g = protein_g + ?,
                carbs_g = carbs_g + ?,
                fat_g = fat_g + ?,
                fiber_g = fiber_g + ?,
                sodium_mg = sodium_mg + ?,
                sugar_g = sugar_g + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE log_date = ?
        """,
            (
                total_calories,
                total_protein,
                total_carbs,
                total_fat,
                total_fiber,
                total_sodium,
                total_sugar,
                today,
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO daily_nutrition_log (
                log_date, calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg, sugar_g
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                today,
                total_calories,
                total_protein,
                total_carbs,
                total_fat,
                total_fiber,
                total_sodium,
                total_sugar,
            ),
        )

    # Add journal entry for the completed meal
    db.execute(
        """
        INSERT INTO journal_entries (journal_date, entry_type, entry_data, source_app, source_id)
        VALUES (?, 'meal_completed', ?, 'food_app', ?)
    """,
        (
            today,
            json.dumps(
                {
                    "meal_name": data.get("meal_name"),
                    "dishes": [d.get("dish_name") for d in dishes],
                    "calories": total_calories,
                    "protein_g": total_protein,
                    "rating": data.get("rating"),
                }
            ),
            meal_id,
        ),
    )

    db.commit()

    return jsonify(
        {
            "meal_id": meal_id,
            "message": "Meal completed!",
            "nutrition_added": {
                "calories": total_calories,
                "protein_g": total_protein,
                "carbs_g": total_carbs,
                "fat_g": total_fat,
            },
        }
    )


@app.route("/api/meals/complete/<int:meal_id>", methods=["GET"])
def get_completed_meal(meal_id):
    """Get a completed meal with all its dishes and ingredients."""
    db = get_db()
    meal = db.execute("SELECT * FROM completed_meals WHERE id = ?", (meal_id,)).fetchone()

    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    dishes = db.execute(
        "SELECT * FROM completed_meal_dishes WHERE completed_meal_id = ?", (meal_id,)
    ).fetchall()

    dishes_with_ingredients = []
    for dish in dishes:
        ingredients = db.execute(
            "SELECT * FROM completed_meal_ingredients WHERE dish_id = ?", (dish["id"],)
        ).fetchall()
        dishes_with_ingredients.append(
            {**dict(dish), "ingredients": [dict(i) for i in ingredients]}
        )

    return jsonify({**dict(meal), "dishes": dishes_with_ingredients})


@app.route("/api/meals/complete/<int:meal_id>/rate", methods=["PUT"])
def rate_completed_meal(meal_id):
    """Update rating and notes for a completed meal."""
    data = request.json
    db = get_db()

    db.execute(
        """
        UPDATE completed_meals SET
            rating = COALESCE(?, rating),
            notes = COALESCE(?, notes),
            changes_for_next_time = COALESCE(?, changes_for_next_time)
        WHERE id = ?
    """,
        (data.get("rating"), data.get("notes"), data.get("changes_for_next_time"), meal_id),
    )
    db.commit()

    return jsonify({"message": "Meal rated!"})


@app.route("/api/meals/complete/history")
def get_completed_meal_history():
    """Get history of completed meals."""
    limit = request.args.get("limit", 20, type=int)
    db = get_db()

    meals = db.execute(
        """
        SELECT * FROM completed_meals
        ORDER BY completed_at DESC
        LIMIT ?
    """,
        (limit,),
    ).fetchall()

    return jsonify([dict(m) for m in meals])


@app.route("/api/pantry/inventory/<int:item_id>/deduct", methods=["POST"])
def deduct_from_inventory(item_id):
    """Deduct an amount from a pantry item (when used in cooking)."""
    data = request.json
    amount_g = data.get("amount_g", 0)

    db = get_db()
    db.execute(
        """
        UPDATE pantry_inventory
        SET current_weight_g = MAX(0, COALESCE(current_weight_g, 0) - ?)
        WHERE id = ?
    """,
        (amount_g, item_id),
    )
    db.commit()

    # Get updated item
    item = db.execute("SELECT * FROM pantry_inventory WHERE id = ?", (item_id,)).fetchone()

    return jsonify(
        {"message": f"Deducted {amount_g}g", "remaining_g": item["current_weight_g"] if item else 0}
    )


# ============================================================================
# INVENTORY UNIT TRACKING & AGGREGATION
# ============================================================================


@app.route("/api/pantry/inventory/grouped")
def get_grouped_inventory():
    """Get inventory grouped by product with total quantities and unit breakdown.

    Returns products with:
    - Total quantity across all units
    - Individual unit cards with their own expiry/fullness
    - Earliest expiry date (for warning)
    """
    db = get_db()
    location = request.args.get("location")

    # Get all inventory items with product details
    query = """
        SELECT
            i.id as unit_id,
            i.product_id,
            i.current_weight_g,
            i.expiry_date,
            i.purchase_date,
            i.opened_date,
            i.is_opened,
            i.location,
            i.notes as unit_notes,
            i.created_at as unit_created_at,
            p.name as product_name,
            p.brand,
            p.barcode,
            p.category,
            p.subcategory,
            p.storage_type,
            p.image_url,
            p.package_weight_g,
            p.package_unit,
            p.calories,
            p.protein,
            p.carbs,
            p.fat
        FROM pantry_inventory i
        JOIN pantry_products p ON i.product_id = p.id
    """

    if location:
        query += " WHERE i.location = ?"
        items = db.execute(query + " ORDER BY p.name, i.expiry_date", (location,)).fetchall()
    else:
        items = db.execute(query + " ORDER BY p.name, i.expiry_date").fetchall()

    # Group by product
    grouped = {}
    for item in items:
        pid = item["product_id"]
        if pid not in grouped:
            grouped[pid] = {
                "product_id": pid,
                "product_name": item["product_name"],
                "brand": item["brand"],
                "barcode": item["barcode"],
                "category": item["category"],
                "subcategory": item["subcategory"],
                "storage_type": item["storage_type"],
                "image_url": item["image_url"],
                "package_weight_g": item["package_weight_g"],
                "package_unit": item["package_unit"],
                "nutrition": {
                    "calories": item["calories"],
                    "protein": item["protein"],
                    "carbs": item["carbs"],
                    "fat": item["fat"],
                },
                "total_weight_g": 0,
                "unit_count": 0,
                "earliest_expiry": None,
                "has_expired": False,
                "expires_soon": False,  # Within 3 days
                "units": [],
            }

        # Add unit
        unit_weight = item["current_weight_g"] or 0
        package_weight = item["package_weight_g"] or 1000
        fullness_pct = (unit_weight / package_weight * 100) if package_weight > 0 else 0

        unit = {
            "unit_id": item["unit_id"],
            "current_weight_g": unit_weight,
            "fullness_percent": round(fullness_pct, 1),
            "expiry_date": item["expiry_date"],
            "purchase_date": item["purchase_date"],
            "opened_date": item["opened_date"],
            "is_opened": item["is_opened"],
            "location": item["location"],
            "notes": item["unit_notes"],
        }

        grouped[pid]["units"].append(unit)
        grouped[pid]["total_weight_g"] += unit_weight
        grouped[pid]["unit_count"] += 1

        # Track earliest expiry
        if item["expiry_date"]:
            if (
                grouped[pid]["earliest_expiry"] is None
                or item["expiry_date"] < grouped[pid]["earliest_expiry"]
            ):
                grouped[pid]["earliest_expiry"] = item["expiry_date"]

            # Check if expired or expiring soon
            from datetime import datetime, timedelta

            try:
                exp_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d")
                today = datetime.now()
                if exp_date < today:
                    grouped[pid]["has_expired"] = True
                elif exp_date < today + timedelta(days=3):
                    grouped[pid]["expires_soon"] = True
            except:
                pass

    return jsonify(list(grouped.values()))


@app.route("/api/pantry/product/<int:product_id>/units")
def get_product_units(product_id):
    """Get all inventory units for a specific product."""
    db = get_db()

    units = db.execute(
        """
        SELECT
            i.*,
            p.name as product_name,
            p.brand,
            p.package_weight_g,
            p.package_unit
        FROM pantry_inventory i
        JOIN pantry_products p ON i.product_id = p.id
        WHERE i.product_id = ?
        ORDER BY i.expiry_date
    """,
        (product_id,),
    ).fetchall()

    result = []
    for u in units:
        package_weight = u["package_weight_g"] or 1000
        current_weight = u["current_weight_g"] or 0
        fullness_pct = (current_weight / package_weight * 100) if package_weight > 0 else 0

        result.append(
            {
                **dict(u),
                "fullness_percent": round(fullness_pct, 1),
            }
        )

    return jsonify(result)


@app.route("/api/pantry/inventory/<int:unit_id>/update", methods=["PUT"])
def update_inventory_unit(unit_id):
    """Update a specific inventory unit (fullness, expiry, etc.)."""
    data = request.json
    db = get_db()

    updates = []
    params = []

    if "current_weight_g" in data:
        updates.append("current_weight_g = ?")
        params.append(data["current_weight_g"])

    if "fullness_percent" in data:
        # Convert percentage to weight using package_weight
        item = db.execute(
            """
            SELECT i.*, p.package_weight_g
            FROM pantry_inventory i
            JOIN pantry_products p ON i.product_id = p.id
            WHERE i.id = ?
        """,
            (unit_id,),
        ).fetchone()

        if item and item["package_weight_g"]:
            weight = (data["fullness_percent"] / 100) * item["package_weight_g"]
            updates.append("current_weight_g = ?")
            params.append(weight)

    if "expiry_date" in data:
        updates.append("expiry_date = ?")
        params.append(data["expiry_date"])

    if "is_opened" in data:
        updates.append("is_opened = ?")
        params.append(1 if data["is_opened"] else 0)
        if data["is_opened"]:
            updates.append("opened_date = DATE('now')")

    if "location" in data:
        updates.append("location = ?")
        params.append(data["location"])

    if "notes" in data:
        updates.append("notes = ?")
        params.append(data["notes"])

    updates.append("updated_at = CURRENT_TIMESTAMP")

    if updates:
        params.append(unit_id)
        db.execute(f"UPDATE pantry_inventory SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()

    # Return updated unit
    unit = db.execute("SELECT * FROM pantry_inventory WHERE id = ?", (unit_id,)).fetchone()
    return jsonify(dict(unit) if unit else {})


@app.route("/api/pantry/inventory/add-unit", methods=["POST"])
def add_inventory_unit():
    """Add another unit of an existing product (e.g., another carton of milk)."""
    data = request.json
    product_id = data.get("product_id")

    if not product_id:
        return jsonify({"error": "product_id required"}), 400

    db = get_db()

    # Get product to determine default weight
    product = db.execute("SELECT * FROM pantry_products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Set weight: use provided value, fullness percentage, or default to package weight (full)
    current_weight = data.get("current_weight_g")
    if current_weight is None and "fullness_percent" in data:
        package_weight = product["package_weight_g"] or 1000
        current_weight = (data["fullness_percent"] / 100) * package_weight
    elif current_weight is None:
        current_weight = product["package_weight_g"]  # Full by default

    cursor = db.execute(
        """
        INSERT INTO pantry_inventory (
            product_id, location, current_weight_g, purchase_date, expiry_date,
            is_opened, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """,
        (
            product_id,
            data.get("location", product["storage_type"] or "fridge"),
            current_weight,
            data.get("purchase_date"),
            data.get("expiry_date"),
            1 if data.get("is_opened") else 0,
            data.get("notes"),
        ),
    )
    db.commit()

    return jsonify(
        {
            "unit_id": cursor.lastrowid,
            "product_id": product_id,
            "product_name": product["name"],
            "current_weight_g": current_weight,
            "message": f"Added new unit of {product['name']}",
        }
    )


@app.route("/api/pantry/inventory/<int:unit_id>", methods=["DELETE"])
def delete_inventory_unit(unit_id):
    """Delete a specific inventory unit (e.g., finished carton)."""
    db = get_db()

    unit = db.execute("SELECT * FROM pantry_inventory WHERE id = ?", (unit_id,)).fetchone()
    if not unit:
        return jsonify({"error": "Unit not found"}), 404

    db.execute("DELETE FROM pantry_inventory WHERE id = ?", (unit_id,))
    db.commit()

    return jsonify({"message": "Unit deleted", "unit_id": unit_id})


# ============================================================================
# OCR EXPIRATION DATE SCANNING - Using EasyOCR (much better than Tesseract)
# ============================================================================

# Global EasyOCR reader (lazy loaded to avoid slow startup)
_easyocr_reader = None
_easyocr_available = None  # Track if EasyOCR is working


def get_easyocr_reader():
    """Lazy load EasyOCR reader for German and English. Returns None if unavailable."""
    global _easyocr_reader, _easyocr_available
    if _easyocr_available is False:
        return None  # Already failed, don't retry
    if _easyocr_reader is None:
        try:
            import easyocr

            _easyocr_reader = easyocr.Reader(["de", "en"], gpu=False)
            _easyocr_available = True
        except Exception as e:
            print(f"EasyOCR not available, falling back to pytesseract: {e}")
            _easyocr_available = False
            return None
    return _easyocr_reader


def perform_ocr_with_boxes(image):
    """
    Perform OCR on image and return text with bounding boxes.
    Tries EasyOCR first, falls back to pytesseract.
    Returns: (text, boxes_list, ocr_engine_used)
    """
    import numpy as np
    from PIL import Image, ImageEnhance

    original_width, original_height = image.size

    # Try EasyOCR first (better accuracy)
    reader = get_easyocr_reader()
    if reader is not None:
        try:
            img_array = np.array(image)
            results = reader.readtext(img_array, detail=1, paragraph=False)

            all_text_parts = []
            all_boxes = []

            for bbox, text, conf in results:
                if text.strip():
                    all_text_parts.append(text.strip())
                    # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                    x1, y1 = bbox[0]
                    x2, y2 = bbox[2]
                    all_boxes.append(
                        {
                            "text": text.strip(),
                            "x_pct": (float(x1) / original_width) * 100,
                            "y_pct": (float(y1) / original_height) * 100,
                            "w_pct": (float(x2 - x1) / original_width) * 100,
                            "h_pct": (float(y2 - y1) / original_height) * 100,
                            "conf": int(conf * 100),
                        }
                    )

            return " ".join(all_text_parts), all_boxes, "easyocr"
        except Exception as e:
            print(f"EasyOCR failed, falling back to pytesseract: {e}")

    # Fallback to pytesseract
    import pytesseract

    # Preprocess for better OCR
    enhancer = ImageEnhance.Contrast(image)
    img_processed = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(img_processed)
    img_processed = enhancer.enhance(1.5)

    # Get detailed OCR data with word bounding boxes
    data = pytesseract.image_to_data(
        img_processed, lang="deu+eng", output_type=pytesseract.Output.DICT
    )

    all_text_parts = []
    all_boxes = []

    for i, text in enumerate(data["text"]):
        if text.strip() and data["conf"][i] > 20:  # Filter low confidence
            all_text_parts.append(text.strip())
            all_boxes.append(
                {
                    "text": text.strip(),
                    "x_pct": (data["left"][i] / original_width) * 100,
                    "y_pct": (data["top"][i] / original_height) * 100,
                    "w_pct": (data["width"][i] / original_width) * 100,
                    "h_pct": (data["height"][i] / original_height) * 100,
                    "conf": data["conf"][i],
                }
            )

    return " ".join(all_text_parts), all_boxes, "pytesseract"


@app.route("/api/ocr/expiry-date", methods=["POST"])
def ocr_expiry_date():
    """
    Extract expiration date from an image using EasyOCR (better than Tesseract).
    Supports German date formats: DD.MM.YYYY, DD.MM.YY, DD/MM/YYYY, etc.
    Returns detected text with bounding boxes for live visual feedback.

    German MHD (Mindesthaltbarkeitsdatum) formats:
    - "mindestens haltbar bis DD.MM.YYYY" (short shelf life <3 months)
    - "mindestens haltbar bis Ende MM/YYYY" (medium shelf life 3-18 months)
    - "MHD: DD.MM.YY" (abbreviated)
    - Just "DD.MM.YYYY" or "DD/MM/YY" printed
    """
    import re
    from datetime import datetime

    if "image" not in request.files and "image_base64" not in request.json:
        return jsonify({"error": "No image provided"}), 400

    try:
        import base64
        import io

        from PIL import Image

        # Get image from file upload or base64
        if "image" in request.files:
            image = Image.open(request.files["image"])
        else:
            image_data = base64.b64decode(request.json["image_base64"])
            image = Image.open(io.BytesIO(image_data))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        original_width, original_height = image.size

        # Use unified OCR helper (tries EasyOCR, falls back to pytesseract)
        text, all_boxes, ocr_engine = perform_ocr_with_boxes(image)

        # German date patterns (most specific first)
        patterns = [
            # DD.MM.YYYY or DD.MM.YY (German standard) - more flexible spacing
            r"(\d{1,2})\s*[.\s/]\s*(\d{1,2})\s*[.\s/]\s*(20\d{2}|\d{2})",
            # "mindestens haltbar bis" followed by date
            r"(?:haltbar\s*bis|MHD)[:\s]*(\d{1,2})\s*[.\s/]\s*(\d{1,2})\s*[.\s/]\s*(20\d{2}|\d{2})",
            # YYYY-MM-DD (ISO format)
            r"(20\d{2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})",
            # Month name format: "15. März 2025" or "15 Mar 2025"
            r"(\d{1,2})\s*[.\s]*\s*(Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Mar(?:ch)?|Apr(?:il)?|Mai|May|Jun(?:e|i)?|Jul(?:y|i)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Okt(?:ober)?|Oct(?:ober)?|Nov(?:ember)?|Dez(?:ember)?|Dec(?:ember)?)\s*[.\s]*\s*(20\d{2}|\d{2})",
            # Ende MM/YYYY format (medium shelf life)
            r"Ende\s+(\d{1,2})\s*[./]\s*(20\d{2})",
        ]

        # Month name mapping for German and English
        month_map = {
            "jan": 1,
            "januar": 1,
            "january": 1,
            "feb": 2,
            "februar": 2,
            "february": 2,
            "mär": 3,
            "märz": 3,
            "mar": 3,
            "march": 3,
            "apr": 4,
            "april": 4,
            "mai": 5,
            "may": 5,
            "jun": 6,
            "juni": 6,
            "june": 6,
            "jul": 7,
            "juli": 7,
            "july": 7,
            "aug": 8,
            "august": 8,
            "sep": 9,
            "sept": 9,
            "september": 9,
            "okt": 10,
            "oktober": 10,
            "oct": 10,
            "october": 10,
            "nov": 11,
            "november": 11,
            "dez": 12,
            "dezember": 12,
            "dec": 12,
            "december": 12,
        }

        found_dates = []

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) == 2:
                        # Ende MM/YYYY format
                        month = int(match[0])
                        year = int(match[1])
                        day = 1  # Default to first of month
                    elif len(match) == 3:
                        g1, g2, g3 = match

                        # Check if it's ISO format (year first)
                        if len(str(g1)) == 4 and str(g1).startswith("20"):
                            year = int(g1)
                            month = int(g2)
                            day = int(g3)
                        # Check if month is a name
                        elif str(g2).lower()[:3] in month_map:
                            day = int(g1)
                            month = month_map[str(g2).lower()[:3]]
                            year = int(g3)
                            if year < 100:
                                year += 2000
                        else:
                            # DD.MM.YYYY format
                            day = int(g1)
                            month = int(g2)
                            year = int(g3)
                            if year < 100:
                                year += 2000
                    else:
                        continue

                    # Validate date
                    if 1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2035:
                        date_obj = datetime(year, month, day)
                        found_dates.append(
                            {
                                "date": date_obj.strftime("%Y-%m-%d"),
                                "display": date_obj.strftime("%d.%m.%Y"),
                                "confidence": (
                                    "high"
                                    if "haltbar" in text.lower() or "mhd" in text.lower()
                                    else "medium"
                                ),
                            }
                        )
                except (ValueError, IndexError, TypeError):
                    continue

        # all_boxes already normalized by perform_ocr_with_boxes()

        # Return best match
        if found_dates:
            # Prefer dates with "haltbar" context, deduplicate
            seen = set()
            unique_dates = []
            for d in found_dates:
                if d["date"] not in seen:
                    seen.add(d["date"])
                    unique_dates.append(d)

            high_conf = [d for d in unique_dates if d["confidence"] == "high"]
            best = high_conf[0] if high_conf else unique_dates[0]

            return jsonify(
                {
                    "success": True,
                    "expiry_date": best["date"],
                    "display_date": best["display"],
                    "confidence": best["confidence"],
                    "raw_text": text[:500],
                    "all_dates": unique_dates,
                    "detected_boxes": all_boxes[:20],
                    "ocr_engine": ocr_engine,
                    "image_size": {"width": original_width, "height": original_height},
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "No date found in image",
                    "raw_text": text[:500],
                    "detected_boxes": all_boxes[:20],
                    "ocr_engine": ocr_engine,
                    "image_size": {"width": original_width, "height": original_height},
                }
            )

    except ImportError as e:
        return jsonify(
            {
                "success": False,
                "error": "EasyOCR not installed",
                "message": "Install EasyOCR: pip install easyocr",
                "manual_entry": True,
            }
        )
    except Exception as e:
        import traceback

        return jsonify(
            {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "manual_entry": True,
            }
        )


@app.route("/api/ocr/scale-weight", methods=["POST"])
def ocr_scale_weight():
    """
    Read weight from a kitchen scale with LCD/7-segment display.
    Uses EasyOCR (better than Tesseract for this) with special preprocessing.
    Returns the weight in grams plus bounding boxes for visual feedback.
    """
    import re

    if "image_base64" not in request.json:
        return jsonify({"error": "No image provided"}), 400

    try:
        import base64
        import io

        import numpy as np
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        # Decode image
        image_data = base64.b64decode(request.json["image_base64"])
        image = Image.open(io.BytesIO(image_data))
        original_width, original_height = image.size

        # Convert to RGB for EasyOCR
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Also keep grayscale for preprocessing experiments
        gray = image.convert("L")
        avg_brightness = sum(gray.getdata()) / len(list(gray.getdata()))

        all_text_results = []
        all_boxes = []
        ocr_engine_used = "unknown"

        # Prepare multiple image variants to maximize detection
        image_variants = []

        # 1. Original image
        image_variants.append(("original", image.convert("RGB")))

        # 2. High contrast preprocessed
        processed = gray.copy()
        if avg_brightness < 128:
            processed = ImageOps.invert(processed)
        enhancer = ImageEnhance.Contrast(processed)
        processed = enhancer.enhance(4.0)
        enhancer = ImageEnhance.Brightness(processed)
        processed = enhancer.enhance(1.5)
        processed = processed.filter(ImageFilter.SHARPEN)
        processed_rgb = processed.convert("RGB")
        image_variants.append(("high_contrast", processed_rgb))

        # 3. Inverted high contrast
        inverted = ImageOps.invert(gray)
        enhancer = ImageEnhance.Contrast(inverted)
        inverted = enhancer.enhance(3.5)
        inverted_rgb = inverted.convert("RGB")
        image_variants.append(("inverted", inverted_rgb))

        # 4. Thresholded (binary)
        binary = gray.point(lambda p: 255 if p > 128 else 0)
        if avg_brightness < 128:
            binary = ImageOps.invert(binary)
        binary_rgb = binary.convert("RGB")
        image_variants.append(("binary", binary_rgb))

        # Try EasyOCR first, then fall back to pytesseract
        reader = get_easyocr_reader()

        if reader is not None:
            ocr_engine_used = "easyocr"
            for variant_name, variant_img in image_variants:
                try:
                    img_array = np.array(variant_img)
                    results = reader.readtext(
                        img_array,
                        detail=1,
                        paragraph=False,
                        allowlist="0123456789.gGkK ",
                        width_ths=0.7,
                        contrast_ths=0.1,
                    )
                    for bbox, text, conf in results:
                        if text.strip():
                            all_text_results.append(text.strip())
                            x1, y1 = bbox[0]
                            x2, y2 = bbox[2]
                            all_boxes.append(
                                {
                                    "text": text.strip(),
                                    "x": float(x1),
                                    "y": float(y1),
                                    "w": float(x2 - x1),
                                    "h": float(y2 - y1),
                                    "conf": int(conf * 100),
                                    "variant": variant_name,
                                }
                            )
                except Exception as e:
                    pass

        # Fallback to pytesseract if EasyOCR unavailable or returned nothing
        if not all_text_results:
            import pytesseract

            ocr_engine_used = "pytesseract"
            for variant_name, variant_img in image_variants:
                try:
                    data = pytesseract.image_to_data(
                        variant_img,
                        lang="eng",
                        output_type=pytesseract.Output.DICT,
                        config="--psm 7 -c tessedit_char_whitelist=0123456789.gGkK ",
                    )
                    for i, text in enumerate(data["text"]):
                        if text.strip() and data["conf"][i] > 20:
                            all_text_results.append(text.strip())
                            all_boxes.append(
                                {
                                    "text": text.strip(),
                                    "x": data["left"][i],
                                    "y": data["top"][i],
                                    "w": data["width"][i],
                                    "h": data["height"][i],
                                    "conf": data["conf"][i],
                                    "variant": variant_name,
                                }
                            )
                except Exception as e:
                    pass

        # Combine all results
        all_text = " ".join(all_text_results)

        # Normalize bounding boxes to percentages
        normalized_boxes = []
        seen_texts = set()
        for box in all_boxes:
            # Dedupe similar boxes
            key = f"{box['text']}_{int(box['x']/10)}_{int(box['y']/10)}"
            if key not in seen_texts:
                seen_texts.add(key)
                normalized_boxes.append(
                    {
                        "text": box["text"],
                        "x_pct": (box["x"] / original_width) * 100,
                        "y_pct": (box["y"] / original_height) * 100,
                        "w_pct": (box["w"] / original_width) * 100,
                        "h_pct": (box["h"] / original_height) * 100,
                        "conf": box["conf"],
                    }
                )

        # Extract weight patterns - order matters (most specific first)
        patterns = [
            (r"(\d+\.?\d*)\s*[kK][gG]", "kg"),  # kg format: 1.5kg, 2kg
            (r"(\d+\.?\d*)\s*[gG](?![a-z])", "g"),  # g format: 500g, 123.4g
            (r"(\d+\.\d+)", "decimal"),  # Numbers with decimal
            (r"(\d{2,4})", "int"),  # 2-4 digit integers (typical scale readings)
        ]

        weights_found = []
        for pattern, ptype in patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                try:
                    num = float(match)
                    if ptype == "kg":
                        if 0.001 <= num <= 20:  # Reasonable kg range
                            weights_found.append(
                                {"weight_g": num * 1000, "raw": match + "kg", "conf": "high"}
                            )
                    elif ptype == "g":
                        if 1 <= num <= 10000:
                            weights_found.append(
                                {"weight_g": num, "raw": match + "g", "conf": "high"}
                            )
                    elif ptype == "decimal":
                        # Could be kg or g - prefer kg if small
                        if num < 10:
                            weights_found.append(
                                {"weight_g": num * 1000, "raw": match, "conf": "medium"}
                            )
                        else:
                            weights_found.append({"weight_g": num, "raw": match, "conf": "medium"})
                    else:
                        # Integer - assume grams if 2-4 digits
                        if 10 <= num <= 9999:
                            weights_found.append({"weight_g": num, "raw": match, "conf": "low"})
                except:
                    pass

        if weights_found:
            # Prefer high confidence matches, then by reasonableness (100-2000g most common)
            high_conf = [w for w in weights_found if w["conf"] == "high"]
            if high_conf:
                best = high_conf[0]
            else:
                # Pick the most "reasonable" weight (kitchen scale typical range)
                best = min(weights_found, key=lambda w: abs(w["weight_g"] - 300))

            return jsonify(
                {
                    "success": True,
                    "weight_g": best["weight_g"],
                    "raw_value": best["raw"],
                    "raw_text": all_text[:300],
                    "all_weights": weights_found[:5],
                    "detected_boxes": normalized_boxes[:15],
                    "image_size": {"width": original_width, "height": original_height},
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "No weight found in image",
                    "raw_text": all_text[:300],
                    "detected_boxes": normalized_boxes[:15],
                    "image_size": {"width": original_width, "height": original_height},
                }
            )

    except ImportError as e:
        return jsonify(
            {
                "success": False,
                "error": "EasyOCR not installed",
                "message": "Install EasyOCR: pip install easyocr",
                "manual_entry": True,
            }
        )
    except Exception as e:
        import traceback

        return jsonify(
            {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "manual_entry": True,
            }
        )


# ============================================================================
# SHOPPING LIST & MEAL PLANNING
# ============================================================================


@app.route("/api/shopping-list/generate", methods=["POST"])
def generate_shopping_list():
    """
    Generate a shopping list from selected recipes.
    Compares recipe ingredients against pantry inventory.
    Returns items to buy with prices from FrischeParadies.

    Request body:
    {
        "recipe_ids": ["52772", "52773"],  // TheMealDB IDs
        "servings": 2,
        "store": "FrischeParadies"  // Optional - default FrischeParadies
    }
    """
    data = request.get_json() or {}
    recipe_ids = data.get("recipe_ids", [])
    servings = data.get("servings", 2)
    store = data.get("store", "FrischeParadies")

    if not recipe_ids:
        return jsonify({"error": "No recipe_ids provided"}), 400

    db = get_db()
    cursor = db.cursor()

    # Get all ingredients from selected recipes via TheMealDB
    all_ingredients = []
    recipes_info = []

    for recipe_id in recipe_ids:
        try:
            response = requests.get(
                f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}", timeout=10
            )
            data = response.json()
            if data.get("meals"):
                meal = data["meals"][0]
                recipes_info.append(
                    {"id": recipe_id, "name": meal["strMeal"], "image": meal["strMealThumb"]}
                )

                # Extract ingredients (1-20)
                for i in range(1, 21):
                    ingredient = meal.get(f"strIngredient{i}", "").strip()
                    measure = meal.get(f"strMeasure{i}", "").strip()
                    if ingredient:
                        all_ingredients.append(
                            {
                                "name": ingredient.lower(),
                                "measure": measure,
                                "recipe_id": recipe_id,
                                "recipe_name": meal["strMeal"],
                            }
                        )
        except:
            pass

    # Get pantry inventory
    cursor.execute(
        """
        SELECT pp.name, SUM(pi.current_weight_g) as total_g
        FROM pantry_inventory pi
        JOIN pantry_products pp ON pi.product_id = pp.id
        WHERE pi.current_weight_g > 0
        GROUP BY pp.name
    """
    )
    pantry_items = {row["name"].lower(): row["total_g"] for row in cursor.fetchall()}

    # Get store products with prices
    cursor.execute(
        """
        SELECT name, price, package_weight_g, category
        FROM pantry_products
        WHERE store = ? AND price > 0
    """,
        (store,),
    )
    store_products = {}
    for row in cursor.fetchall():
        store_products[row["name"].lower()] = {
            "name": row["name"],
            "price": row["price"],
            "weight_g": row["package_weight_g"],
            "category": row["category"],
        }

    # Build shopping list
    shopping_list = []
    have_in_pantry = []
    total_cost = 0.0

    # Consolidate ingredients by name
    consolidated = {}
    for ing in all_ingredients:
        name = ing["name"]
        if name not in consolidated:
            consolidated[name] = {"name": name, "measures": [], "recipes": []}
        consolidated[name]["measures"].append(ing["measure"])
        if ing["recipe_name"] not in consolidated[name]["recipes"]:
            consolidated[name]["recipes"].append(ing["recipe_name"])

    for name, ing_data in consolidated.items():
        # Check if in pantry
        if name in pantry_items and pantry_items[name] > 50:  # More than 50g
            have_in_pantry.append(
                {"name": name, "in_pantry_g": pantry_items[name], "needed_for": ing_data["recipes"]}
            )
            continue

        # Find matching product in store
        best_match = None
        best_score = 0

        # Try exact match first
        if name in store_products:
            best_match = store_products[name]
            best_score = 100
        else:
            # Fuzzy match
            name_words = set(name.split())
            for product_name, product_data in store_products.items():
                product_words = set(product_name.lower().split())
                common_words = name_words & product_words
                if common_words:
                    score = len(common_words) / len(name_words) * 100
                    if score > best_score:
                        best_score = score
                        best_match = product_data

        if best_match and best_score >= 30:
            item = {
                "ingredient": name,
                "product": best_match["name"],
                "price": best_match["price"],
                "weight_g": best_match["weight_g"],
                "category": best_match["category"],
                "needed_for": ing_data["recipes"],
                "match_score": best_score,
            }
            shopping_list.append(item)
            total_cost += best_match["price"]
        else:
            # No match found - add as generic item
            shopping_list.append(
                {
                    "ingredient": name,
                    "product": None,
                    "price": None,
                    "needed_for": ing_data["recipes"],
                    "no_match": True,
                }
            )

    # Sort by category
    shopping_list.sort(key=lambda x: (x.get("category") or "zzz", x.get("ingredient", "")))

    return jsonify(
        {
            "recipes": recipes_info,
            "servings": servings,
            "store": store,
            "shopping_list": shopping_list,
            "have_in_pantry": have_in_pantry,
            "total_estimated_cost": round(total_cost, 2),
            "items_to_buy": len([x for x in shopping_list if not x.get("no_match")]),
            "items_no_match": len([x for x in shopping_list if x.get("no_match")]),
            "items_in_pantry": len(have_in_pantry),
        }
    )


@app.route("/api/stores/products", methods=["GET"])
def get_store_products():
    """Get all products from a specific store with prices."""
    store = request.args.get("store", "FrischeParadies")
    category = request.args.get("category")
    search = request.args.get("search")
    limit = int(request.args.get("limit", 100))

    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT id, name, store, category, package_weight_g, price, currency
        FROM pantry_products
        WHERE store = ? AND price > 0
    """
    params = [store]

    if category:
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY category, name LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    products = [dict(row) for row in cursor.fetchall()]

    # Get category summary
    cursor.execute(
        """
        SELECT category, COUNT(*) as count, AVG(price) as avg_price
        FROM pantry_products
        WHERE store = ? AND price > 0
        GROUP BY category
        ORDER BY count DESC
    """,
        (store,),
    )
    categories = [dict(row) for row in cursor.fetchall()]

    return jsonify(
        {"store": store, "products": products, "categories": categories, "total": len(products)}
    )


@app.route("/api/meal-plan", methods=["POST"])
def create_meal_plan():
    """
    Create a meal plan and generate shopping list.

    Request body:
    {
        "meals": [
            {"type": "breakfast", "recipe_id": "52965"},
            {"type": "lunch", "recipe_id": "52772"},
            {"type": "dinner", "recipe_id": "52773"}
        ],
        "date": "2025-12-13",
        "servings": 2
    }
    """
    data = request.get_json() or {}
    meals = data.get("meals", [])
    plan_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    servings = data.get("servings", 2)

    if not meals:
        return jsonify({"error": "No meals provided"}), 400

    # Get recipe IDs
    recipe_ids = [m["recipe_id"] for m in meals if m.get("recipe_id")]

    # Generate shopping list using existing endpoint logic
    shopping_data = {"recipe_ids": recipe_ids, "servings": servings, "store": "FrischeParadies"}

    # Get shopping list
    with app.test_request_context(json=shopping_data):
        shopping_response = generate_shopping_list()
        shopping_list = shopping_response.get_json()

    return jsonify(
        {"plan_date": plan_date, "meals": meals, "servings": servings, "shopping": shopping_list}
    )


@app.route("/api/recipes/search-by-ingredients", methods=["GET"])
def search_recipes_by_ingredients():
    """
    Search for recipes that use ingredients available at FrischeParadies.
    Returns recipes sorted by how many ingredients are available.
    """
    ingredient = request.args.get("ingredient", "")
    category = request.args.get("category")  # e.g., 'Beef', 'Chicken'
    limit = int(request.args.get("limit", 10))

    db = get_db()
    cursor = db.cursor()

    # Get FrischeParadies products
    cursor.execute(
        """
        SELECT DISTINCT name, category, price
        FROM pantry_products
        WHERE store = 'FrischeParadies' AND price > 0
    """
    )
    fp_products = {row["name"].lower(): dict(row) for row in cursor.fetchall()}

    # Search TheMealDB
    recipes = []

    if ingredient:
        try:
            response = requests.get(
                f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingredient}", timeout=10
            )
            data = response.json()
            if data.get("meals"):
                recipes.extend(data["meals"][: limit * 2])
        except:
            pass

    if category:
        try:
            response = requests.get(
                f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}", timeout=10
            )
            data = response.json()
            if data.get("meals"):
                recipes.extend(data["meals"][: limit * 2])
        except:
            pass

    # Get full recipe details and check ingredient availability
    detailed_recipes = []
    for recipe in recipes[: limit * 2]:
        try:
            response = requests.get(
                f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe["idMeal"]}',
                timeout=5,
            )
            data = response.json()
            if data.get("meals"):
                meal = data["meals"][0]

                # Extract ingredients
                ingredients = []
                available_count = 0
                total_cost = 0

                for i in range(1, 21):
                    ing_name = meal.get(f"strIngredient{i}", "").strip()
                    measure = meal.get(f"strMeasure{i}", "").strip()
                    if ing_name:
                        # Check if available at FrischeParadies
                        ing_lower = ing_name.lower()
                        available = ing_lower in fp_products
                        if not available:
                            # Fuzzy match
                            for fp_name in fp_products:
                                if ing_lower in fp_name or fp_name in ing_lower:
                                    available = True
                                    if fp_products.get(fp_name, {}).get("price"):
                                        total_cost += fp_products[fp_name]["price"]
                                    break

                        if available:
                            available_count += 1

                        ingredients.append(
                            {"name": ing_name, "measure": measure, "available_at_fp": available}
                        )

                availability_score = (
                    (available_count / len(ingredients) * 100) if ingredients else 0
                )

                detailed_recipes.append(
                    {
                        "id": meal["idMeal"],
                        "name": meal["strMeal"],
                        "category": meal["strCategory"],
                        "cuisine": meal["strArea"],
                        "image": meal["strMealThumb"],
                        "ingredients": ingredients,
                        "ingredient_count": len(ingredients),
                        "available_at_fp": available_count,
                        "availability_score": round(availability_score, 1),
                        "estimated_cost": round(total_cost, 2),
                    }
                )
        except:
            pass

    # Sort by availability score
    detailed_recipes.sort(key=lambda x: x["availability_score"], reverse=True)

    return jsonify(
        {
            "recipes": detailed_recipes[:limit],
            "search": {"ingredient": ingredient, "category": category},
        }
    )


@app.route("/api/recipes/search-by-ingredients", methods=["POST"])
def search_local_recipes_by_ingredients():
    """
    Search local database recipes ranked by ingredient availability.

    POST body:
    {
      "ingredients": ["chicken", "rice", "onion"]
    }

    Returns recipes sorted by availability score.
    """
    data = request.json
    user_ingredients = [i.lower().strip() for i in data.get("ingredients", [])]

    if not user_ingredients:
        return jsonify([]), 200

    db = get_db()
    cursor = db.cursor()

    # Get all recipes with their ingredients from local database
    cursor.execute(
        """
        SELECT DISTINCT r.id, r.name, r.description, r.category, r.cuisine,
               r.prep_time_min, r.cook_time_min, r.servings, r.difficulty,
               r.image_url, GROUP_CONCAT(ing.name, '||') as ingredient_list
        FROM recipes r
        LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        LEFT JOIN ingredients ing ON ri.ingredient_id = ing.id
        GROUP BY r.id
    """
    )

    recipes = cursor.fetchall()
    results = []

    for recipe in recipes:
        if not recipe["ingredient_list"]:
            continue

        recipe_ingredients = [i.lower().strip() for i in recipe["ingredient_list"].split("||")]

        # Calculate matches using fuzzy matching
        matched = []
        for recipe_ing in recipe_ingredients:
            if any(
                user_ing in recipe_ing or recipe_ing in user_ing for user_ing in user_ingredients
            ):
                matched.append(recipe_ing)

        missing = [i for i in recipe_ingredients if i not in matched]

        availability_score = len(matched) / len(recipe_ingredients) if recipe_ingredients else 0

        # Only include recipes with at least 30% match
        if availability_score < 0.3:
            continue

        results.append(
            {
                "id": recipe["id"],
                "name": recipe["name"],
                "description": recipe["description"],
                "category": recipe["category"],
                "cuisine": recipe["cuisine"],
                "prep_time_min": recipe["prep_time_min"],
                "cook_time_min": recipe["cook_time_min"],
                "servings": recipe["servings"],
                "difficulty": recipe["difficulty"],
                "image_url": recipe["image_url"],
                "availabilityScore": round(availability_score, 2),
                "matchedIngredients": matched,
                "missingIngredients": missing,
            }
        )

    # Sort by availability score (descending)
    results.sort(key=lambda x: x["availabilityScore"], reverse=True)

    return jsonify(results), 200


@app.route("/shopping")
def shopping_page():
    """Shopping list page."""
    return render_template("shopping.html")


# ============================================================================
# MEAL PLANNING API - Day/Week/Month planning with budget
# ============================================================================


@app.route("/api/meal-plans", methods=["GET"])
def list_meal_plans():
    """Get all meal plans."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT * FROM meal_plans
        ORDER BY created_at DESC
    """
    )
    plans = cursor.fetchall()
    return jsonify([dict(p) for p in plans])


@app.route("/api/meal-plans", methods=["POST"])
def new_meal_plan():
    """Create a new meal plan for day/week/month."""
    data = request.get_json()
    plan_type = data.get("plan_type", "week")  # day, week, month
    budget = data.get("budget")  # Optional budget in EUR
    include_snacks = data.get("include_snacks", False)
    start_date = data.get("start_date", datetime.now().strftime("%Y-%m-%d"))

    # Calculate days and meals needed
    days_map = {"day": 1, "week": 7, "month": 30}
    days = days_map.get(plan_type, 7)

    from datetime import timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = start + timedelta(days=days - 1)

    # Meals needed
    breakfasts = days
    lunches = days
    dinners = days
    snacks = days * 2 if include_snacks else 0

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO meal_plans (
            name, plan_type, start_date, end_date,
            budget_total, budget_remaining, include_snacks,
            breakfasts_needed, lunches_needed, dinners_needed, snacks_needed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            f"{plan_type.title()} Plan - {start.strftime('%b %d')}",
            plan_type,
            start_date,
            end.strftime("%Y-%m-%d"),
            budget,
            budget,
            1 if include_snacks else 0,
            breakfasts,
            lunches,
            dinners,
            snacks,
        ),
    )
    db.commit()
    plan_id = cursor.lastrowid

    return jsonify(
        {
            "plan_id": plan_id,
            "plan_type": plan_type,
            "days": days,
            "start_date": start_date,
            "end_date": end.strftime("%Y-%m-%d"),
            "budget": budget,
            "meals_needed": {
                "breakfast": breakfasts,
                "lunch": lunches,
                "dinner": dinners,
                "snack": snacks,
            },
        }
    )


@app.route("/api/meal-plans/<int:plan_id>")
def get_meal_plan(plan_id):
    """Get a specific meal plan with all its items."""
    db = get_db()
    cursor = db.cursor()

    # Get plan details
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    # Get plan items
    cursor.execute(
        """
        SELECT * FROM meal_plan_items
        WHERE plan_id = ?
        ORDER BY day_number,
        CASE meal_type
            WHEN 'breakfast' THEN 1
            WHEN 'lunch' THEN 2
            WHEN 'dinner' THEN 3
            WHEN 'snack' THEN 4
        END
    """,
        (plan_id,),
    )
    items = cursor.fetchall()

    # Get aggregated ingredients
    cursor.execute(
        """
        SELECT * FROM meal_plan_ingredients
        WHERE plan_id = ?
        ORDER BY recipe_count DESC, ingredient_name
    """,
        (plan_id,),
    )
    ingredients = cursor.fetchall()

    plan_dict = dict(plan)
    plan_dict["items"] = [dict(i) for i in items]
    plan_dict["ingredients"] = [dict(i) for i in ingredients]

    return jsonify(plan_dict)


@app.route("/api/meal-plans/<int:plan_id>/add-recipe", methods=["POST"])
def add_recipe_to_plan(plan_id):
    """Add a swiped-right recipe to the meal plan."""
    data = request.get_json()
    recipe_id = data.get("recipe_id")
    recipe_title = data.get("recipe_title")
    meal_type = data.get("meal_type")  # breakfast, lunch, dinner, snack
    day_number = data.get("day_number", 1)
    servings = data.get("servings", 2)
    ingredients = data.get("ingredients", [])  # List of ingredient strings

    db = get_db()
    cursor = db.cursor()

    # Get plan
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    # Estimate cost from FrischeParadies products
    total_cost = 0
    matched_ingredients = []
    for ing in ingredients:
        # Simple fuzzy match to store products
        ing_lower = ing.lower()
        cursor.execute(
            """
            SELECT id, name, price FROM pantry_products
            WHERE store = 'FrischeParadies'
            AND (LOWER(name) LIKE ? OR ? LIKE '%' || LOWER(name) || '%')
            LIMIT 1
        """,
            (f"%{ing_lower.split()[0]}%", ing_lower),
        )
        product = cursor.fetchone()
        if product:
            # Rough estimate: assume 1/4 of product per recipe
            cost_estimate = (product["price"] or 0) / 4
            total_cost += cost_estimate
            matched_ingredients.append(
                {
                    "name": ing,
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "cost_estimate": cost_estimate,
                }
            )
        else:
            matched_ingredients.append(
                {
                    "name": ing,
                    "product_id": None,
                    "cost_estimate": 2.0,  # Default estimate for unknown
                }
            )
            total_cost += 2.0

    # Calculate meal date
    from datetime import timedelta

    start = datetime.strptime(plan["start_date"], "%Y-%m-%d")
    meal_date = (start + timedelta(days=day_number - 1)).strftime("%Y-%m-%d")

    # Add item
    cursor.execute(
        """
        INSERT INTO meal_plan_items (
            plan_id, recipe_id, recipe_source, recipe_title,
            meal_type, day_number, meal_date, servings, estimated_cost
        ) VALUES (?, ?, 'local', ?, ?, ?, ?, ?, ?)
    """,
        (plan_id, recipe_id, recipe_title, meal_type, day_number, meal_date, servings, total_cost),
    )

    # Update plan progress
    progress_field = f"{meal_type}s_selected"
    cursor.execute(
        f"""
        UPDATE meal_plans
        SET {progress_field} = {progress_field} + 1,
            total_estimated_cost = total_estimated_cost + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (total_cost, plan_id),
    )

    # Update/insert ingredient aggregates
    for ing in ingredients:
        ing_name = ing.lower().split(",")[0].strip()  # Clean up ingredient name
        cursor.execute(
            """
            SELECT id, recipe_count, total_amount_g FROM meal_plan_ingredients
            WHERE plan_id = ? AND LOWER(ingredient_name) = ?
        """,
            (plan_id, ing_name),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE meal_plan_ingredients
                SET recipe_count = recipe_count + 1
                WHERE id = ?
            """,
                (existing["id"],),
            )
        else:
            cursor.execute(
                """
                INSERT INTO meal_plan_ingredients (plan_id, ingredient_name, recipe_count)
                VALUES (?, ?, 1)
            """,
                (plan_id, ing_name),
            )

    db.commit()

    # Check if plan is complete
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    updated_plan = cursor.fetchone()

    is_complete = (
        updated_plan["breakfasts_selected"] >= updated_plan["breakfasts_needed"]
        and updated_plan["lunches_selected"] >= updated_plan["lunches_needed"]
        and updated_plan["dinners_selected"] >= updated_plan["dinners_needed"]
        and updated_plan["snacks_selected"] >= updated_plan["snacks_needed"]
    )

    return jsonify(
        {
            "success": True,
            "item_id": cursor.lastrowid,
            "estimated_cost": total_cost,
            "total_plan_cost": updated_plan["total_estimated_cost"],
            "budget_remaining": (
                (updated_plan["budget_total"] or 0) - updated_plan["total_estimated_cost"]
                if updated_plan["budget_total"]
                else None
            ),
            "progress": {
                "breakfast": f"{updated_plan['breakfasts_selected']}/{updated_plan['breakfasts_needed']}",
                "lunch": f"{updated_plan['lunches_selected']}/{updated_plan['lunches_needed']}",
                "dinner": f"{updated_plan['dinners_selected']}/{updated_plan['dinners_needed']}",
                "snack": f"{updated_plan['snacks_selected']}/{updated_plan['snacks_needed']}",
            },
            "is_complete": is_complete,
            "matched_ingredients": matched_ingredients,
        }
    )


@app.route("/api/meal-plans/<int:plan_id>/smart-recipes")
def get_smart_recipes_for_plan(plan_id):
    """Get recipes optimized for ingredient overlap with existing plan items.

    Prioritizes recipes that share ingredients with already-selected meals
    for easier meal prep and less food waste.
    """
    meal_type = request.args.get("meal_type", "dinner")
    limit = int(request.args.get("limit", 20))

    db = get_db()
    cursor = db.cursor()

    # Get plan
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    # Get ingredients already in the plan
    cursor.execute(
        """
        SELECT ingredient_name, recipe_count
        FROM meal_plan_ingredients
        WHERE plan_id = ?
    """,
        (plan_id,),
    )
    existing_ingredients = {
        row["ingredient_name"].lower(): row["recipe_count"] for row in cursor.fetchall()
    }

    # Get recipes from local database
    category_map = {
        "breakfast": ["breakfast"],
        "lunch": ["lunch", "main", "side"],
        "dinner": ["dinner", "main"],
        "snack": ["dessert", "appetizer", "snack", "beverage", "side"],
    }
    categories = category_map.get(meal_type, ["main"])
    placeholders = ",".join(["?" for _ in categories])

    cursor.execute(
        f"""
        SELECT id, title, ingredients, category, cuisine
        FROM recipes_large
        WHERE category IN ({placeholders})
        ORDER BY RANDOM()
        LIMIT 200
    """,
        categories,
    )
    recipes = cursor.fetchall()

    # Score recipes by ingredient overlap
    scored_recipes = []
    for recipe in recipes:
        try:
            ingredients = json.loads(recipe["ingredients"]) if recipe["ingredients"] else []
        except:
            ingredients = []

        # Calculate overlap score
        overlap_score = 0
        overlap_ingredients = []
        for ing in ingredients:
            ing_clean = ing.lower().split(",")[0].split("(")[0].strip()
            for word in ing_clean.split():
                if word in existing_ingredients:
                    overlap_score += existing_ingredients[word]
                    overlap_ingredients.append(word)
                    break

        scored_recipes.append(
            {
                "id": f"local_{recipe['id']}",
                "title": recipe["title"],
                "ingredients": ingredients,
                "category": recipe["category"],
                "cuisine": recipe["cuisine"],
                "overlap_score": overlap_score,
                "overlap_ingredients": list(set(overlap_ingredients)),
                "image_url": f"https://source.unsplash.com/400x300/?food,{recipe['category']}",
            }
        )

    # Sort by overlap score (higher is better for meal prep)
    scored_recipes.sort(key=lambda x: x["overlap_score"], reverse=True)

    # Get budget status
    budget_remaining = None
    if plan["budget_total"]:
        budget_remaining = plan["budget_total"] - (plan["total_estimated_cost"] or 0)

    return jsonify(
        {
            "plan_id": plan_id,
            "meal_type": meal_type,
            "recipes": scored_recipes[:limit],
            "existing_ingredients": list(existing_ingredients.keys()),
            "budget_remaining": budget_remaining,
            "progress": {
                "breakfast": f"{plan['breakfasts_selected']}/{plan['breakfasts_needed']}",
                "lunch": f"{plan['lunches_selected']}/{plan['lunches_needed']}",
                "dinner": f"{plan['dinners_selected']}/{plan['dinners_needed']}",
                "snack": f"{plan['snacks_selected']}/{plan['snacks_needed']}",
            },
        }
    )


@app.route("/api/meal-plans/<int:plan_id>/swipe", methods=["POST"])
def swipe_recipe_in_plan(plan_id):
    """Handle swipe actions during meal planning.

    - LEFT: skip recipe (no action)
    - RIGHT: add to plan for next available slot
    - UP: add to plan AND mark as meal-prep friendly
    """
    data = request.get_json()
    direction = data.get("direction")  # 'left', 'right', 'up'
    recipe_id = data.get("recipe_id")
    recipe_title = data.get("recipe_title")
    meal_type = data.get("meal_type")
    ingredients = data.get("ingredients", [])

    if direction == "left":
        # Record dislike for future filtering
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO recipe_preferences (recipe_id, action, category)
            VALUES (?, 'disliked', ?)
        """,
            (recipe_id, meal_type),
        )
        db.commit()
        return jsonify({"success": True, "action": "skipped"})

    # RIGHT or UP - add to plan
    db = get_db()
    cursor = db.cursor()

    # Get plan and find next available day
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    # Find next available day for this meal type
    selected_field = f"{meal_type}s_selected"
    needed_field = f"{meal_type}s_needed"
    current_selected = plan[selected_field]

    if current_selected >= plan[needed_field]:
        return (
            jsonify(
                {
                    "error": f"All {meal_type}s already selected",
                    "progress": f"{current_selected}/{plan[needed_field]}",
                }
            ),
            400,
        )

    # Calculate which day this should be (allowing repeats)
    days_in_plan = {"day": 1, "week": 7, "month": 30}.get(plan["plan_type"], 7)
    day_number = (current_selected % days_in_plan) + 1

    # If UP swipe, mark as meal-prep friendly
    can_meal_prep = 1 if direction == "up" else 0

    # Add to plan (reuse the add-recipe logic)
    result = add_recipe_to_plan_internal(
        plan_id,
        recipe_id,
        recipe_title,
        meal_type,
        day_number,
        ingredients,
        can_meal_prep,
        cursor,
        db,
    )

    return jsonify(
        {
            "success": True,
            "action": "added" if direction == "right" else "added_for_prep",
            "day_number": day_number,
            "can_meal_prep": bool(can_meal_prep),
            **result,
        }
    )


def add_recipe_to_plan_internal(
    plan_id, recipe_id, recipe_title, meal_type, day_number, ingredients, can_meal_prep, cursor, db
):
    """Internal helper to add recipe to plan."""

    # Get plan
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()

    # Estimate cost from FrischeParadies products
    total_cost = 0
    for ing in ingredients:
        ing_lower = ing.lower()
        cursor.execute(
            """
            SELECT price FROM pantry_products
            WHERE store = 'FrischeParadies'
            AND (LOWER(name) LIKE ? OR ? LIKE '%' || LOWER(name) || '%')
            LIMIT 1
        """,
            (f"%{ing_lower.split()[0]}%", ing_lower),
        )
        product = cursor.fetchone()
        if product:
            total_cost += (product["price"] or 0) / 4
        else:
            total_cost += 2.0

    # Calculate meal date
    from datetime import timedelta

    start = datetime.strptime(plan["start_date"], "%Y-%m-%d")
    meal_date = (start + timedelta(days=day_number - 1)).strftime("%Y-%m-%d")

    # Add item
    cursor.execute(
        """
        INSERT INTO meal_plan_items (
            plan_id, recipe_id, recipe_source, recipe_title,
            meal_type, day_number, meal_date, servings, estimated_cost, can_meal_prep
        ) VALUES (?, ?, 'local', ?, ?, ?, ?, 2, ?, ?)
    """,
        (
            plan_id,
            recipe_id,
            recipe_title,
            meal_type,
            day_number,
            meal_date,
            total_cost,
            can_meal_prep,
        ),
    )

    # Update plan progress
    progress_field = f"{meal_type}s_selected"
    cursor.execute(
        f"""
        UPDATE meal_plans
        SET {progress_field} = {progress_field} + 1,
            total_estimated_cost = total_estimated_cost + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (total_cost, plan_id),
    )

    # Update ingredient aggregates
    for ing in ingredients:
        ing_name = ing.lower().split(",")[0].strip()
        cursor.execute(
            """
            INSERT INTO meal_plan_ingredients (plan_id, ingredient_name, recipe_count)
            VALUES (?, ?, 1)
            ON CONFLICT DO NOTHING
        """,
            (plan_id, ing_name),
        )
        cursor.execute(
            """
            UPDATE meal_plan_ingredients
            SET recipe_count = recipe_count + 1
            WHERE plan_id = ? AND LOWER(ingredient_name) = ?
        """,
            (plan_id, ing_name),
        )

    db.commit()

    # Get updated plan
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    updated_plan = cursor.fetchone()

    is_complete = (
        updated_plan["breakfasts_selected"] >= updated_plan["breakfasts_needed"]
        and updated_plan["lunches_selected"] >= updated_plan["lunches_needed"]
        and updated_plan["dinners_selected"] >= updated_plan["dinners_needed"]
        and updated_plan["snacks_selected"] >= updated_plan["snacks_needed"]
    )

    return {
        "estimated_cost": total_cost,
        "total_plan_cost": updated_plan["total_estimated_cost"],
        "budget_remaining": (
            (updated_plan["budget_total"] or 0) - updated_plan["total_estimated_cost"]
            if updated_plan["budget_total"]
            else None
        ),
        "progress": {
            "breakfast": f"{updated_plan['breakfasts_selected']}/{updated_plan['breakfasts_needed']}",
            "lunch": f"{updated_plan['lunches_selected']}/{updated_plan['lunches_needed']}",
            "dinner": f"{updated_plan['dinners_selected']}/{updated_plan['dinners_needed']}",
            "snack": f"{updated_plan['snacks_selected']}/{updated_plan['snacks_needed']}",
        },
        "is_complete": is_complete,
    }


@app.route("/api/meal-plans/<int:plan_id>/shopping-list")
def get_plan_shopping_list(plan_id):
    """Generate shopping list for a meal plan, accounting for pantry inventory."""
    db = get_db()
    cursor = db.cursor()

    # Get plan with ingredients
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    # Get aggregated ingredients
    cursor.execute(
        """
        SELECT ingredient_name, recipe_count
        FROM meal_plan_ingredients
        WHERE plan_id = ?
        ORDER BY recipe_count DESC
    """,
        (plan_id,),
    )
    plan_ingredients = cursor.fetchall()

    # Get pantry inventory
    cursor.execute(
        """
        SELECT pp.name, SUM(pi.current_weight_g) as total_g
        FROM pantry_inventory pi
        JOIN pantry_products pp ON pi.product_id = pp.id
        GROUP BY pp.id
    """
    )
    pantry = {row["name"].lower(): row["total_g"] for row in cursor.fetchall()}

    # Build shopping list
    shopping_items = []
    total_cost = 0

    for ing in plan_ingredients:
        ing_name = ing["ingredient_name"]

        # Check pantry
        in_pantry = any(ing_name in p for p in pantry.keys())

        # Find store product
        cursor.execute(
            """
            SELECT id, name, price, price_per_kg
            FROM pantry_products
            WHERE store = 'FrischeParadies'
            AND (LOWER(name) LIKE ? OR ? LIKE '%' || LOWER(name) || '%')
            ORDER BY price ASC
            LIMIT 1
        """,
            (f"%{ing_name}%", ing_name),
        )
        product = cursor.fetchone()

        item = {
            "ingredient": ing_name,
            "recipe_count": ing["recipe_count"],
            "in_pantry": in_pantry,
            "need_to_buy": not in_pantry,
        }

        if product:
            item["store_product"] = {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "price_per_kg": product["price_per_kg"],
            }
            if not in_pantry:
                total_cost += product["price"] or 0
        else:
            item["store_product"] = None
            if not in_pantry:
                total_cost += 3.0  # Estimate

        shopping_items.append(item)

    # Sort: need to buy first, then by recipe count
    shopping_items.sort(key=lambda x: (-x["need_to_buy"], -x["recipe_count"]))

    return jsonify(
        {
            "plan_id": plan_id,
            "plan_type": plan["plan_type"],
            "budget_total": plan["budget_total"],
            "estimated_total": total_cost,
            "budget_remaining": (
                (plan["budget_total"] or 0) - total_cost if plan["budget_total"] else None
            ),
            "over_budget": total_cost > plan["budget_total"] if plan["budget_total"] else False,
            "items": shopping_items,
            "items_to_buy": len([i for i in shopping_items if i["need_to_buy"]]),
            "items_in_pantry": len([i for i in shopping_items if i["in_pantry"]]),
        }
    )


@app.route("/api/meal-plans/<int:plan_id>/prep-schedule")
def get_prep_schedule(plan_id):
    """Generate a meal prep schedule for the plan.

    Groups ingredients by prep type (can prep ahead vs day-of)
    and suggests prep batching for efficiency.
    """
    db = get_db()
    cursor = db.cursor()

    # Get plan items marked for meal prep
    cursor.execute(
        """
        SELECT * FROM meal_plan_items
        WHERE plan_id = ? AND can_meal_prep = 1
        ORDER BY day_number
    """,
        (plan_id,),
    )
    prep_items = cursor.fetchall()

    # Get high-overlap ingredients (used in 3+ recipes)
    cursor.execute(
        """
        SELECT ingredient_name, recipe_count
        FROM meal_plan_ingredients
        WHERE plan_id = ? AND recipe_count >= 2
        ORDER BY recipe_count DESC
    """,
        (plan_id,),
    )
    batch_ingredients = cursor.fetchall()

    # Categorize prep tasks
    prep_tasks = {
        "proteins": [],  # Marinate, portion, pre-cook
        "vegetables": [],  # Wash, chop, portion
        "grains": [],  # Cook in bulk
        "sauces": [],  # Make ahead
        "other": [],
    }

    protein_words = ["chicken", "beef", "pork", "fish", "tofu", "lamb", "turkey", "shrimp"]
    veg_words = [
        "onion",
        "garlic",
        "pepper",
        "carrot",
        "celery",
        "tomato",
        "lettuce",
        "spinach",
        "broccoli",
        "potato",
    ]
    grain_words = ["rice", "pasta", "quinoa", "couscous", "noodle", "bread"]

    for ing in batch_ingredients:
        name = ing["ingredient_name"].lower()
        task = {"name": name, "recipe_count": ing["recipe_count"]}

        if any(p in name for p in protein_words):
            task["prep_suggestion"] = f"Portion and marinate {name} for {ing['recipe_count']} meals"
            prep_tasks["proteins"].append(task)
        elif any(v in name for v in veg_words):
            task["prep_suggestion"] = f"Wash and chop {name} in bulk"
            prep_tasks["vegetables"].append(task)
        elif any(g in name for g in grain_words):
            task["prep_suggestion"] = f"Cook {name} in large batch, portion and refrigerate"
            prep_tasks["grains"].append(task)
        else:
            task["prep_suggestion"] = f"Prepare {name} ahead"
            prep_tasks["other"].append(task)

    return jsonify(
        {
            "plan_id": plan_id,
            "prep_day_suggestion": "Sunday" if len(prep_items) > 3 else "Day before",
            "meals_to_prep": [dict(item) for item in prep_items],
            "batch_ingredients": [dict(i) for i in batch_ingredients],
            "prep_tasks": prep_tasks,
            "time_estimate_minutes": len(batch_ingredients) * 10 + len(prep_items) * 15,
        }
    )


@app.route("/plan")
def meal_plan_page():
    """Meal planning page."""
    return render_template("meal_plan.html")


@app.route("/plan/<int:plan_id>/swipe/<meal_type>")
def meal_plan_swipe_page(plan_id, meal_type):
    """Swipe interface for meal planning."""
    return render_template("meal_plan_swipe.html", plan_id=plan_id, meal_type=meal_type)


# ============================================================================
# MEAL PREP MODE - Aggregate mise en place and batch cooking
# ============================================================================


@app.route("/api/meal-plans/<int:plan_id>/prep-tasks")
def generate_prep_tasks(plan_id):
    """
    Generate a comprehensive meal prep task list from all recipes in a plan.

    Aggregates all mise en place steps, groups by task type (chop, measure, marinate, etc.),
    and creates an optimized workflow for batch preparation.
    """
    db = get_db()
    cursor = db.cursor()

    # Get plan
    cursor.execute("SELECT * FROM meal_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    # Get all recipes in the plan
    cursor.execute(
        """
        SELECT mpi.*, rl.ingredients, rl.instructions, rl.title
        FROM meal_plan_items mpi
        LEFT JOIN recipes_large rl ON mpi.recipe_id = 'local_' || rl.id
        WHERE mpi.plan_id = ?
        ORDER BY mpi.day_number, mpi.meal_type
    """,
        (plan_id,),
    )
    items = cursor.fetchall()

    # Prep task categories with keywords to detect them
    task_patterns = {
        "chop": ["chop", "dice", "mince", "cut", "slice", "julienne", "cube", "quarter", "halve"],
        "measure_dry": [
            "cup",
            "tablespoon",
            "teaspoon",
            "tbsp",
            "tsp",
            "oz",
            "ounce",
            "pound",
            "lb",
        ],
        "measure_wet": ["cup", "tablespoon", "teaspoon", "ml", "liter", "fl oz"],
        "wash": ["wash", "rinse", "clean"],
        "peel": ["peel", "skin", "hull", "stem"],
        "marinate": ["marinate", "marinade", "brine", "soak"],
        "toast": ["toast", "roast", "dry roast"],
        "cook_grain": [
            "rice",
            "quinoa",
            "pasta",
            "noodle",
            "couscous",
            "farro",
            "barley",
            "bulgur",
        ],
        "cook_protein": ["chicken", "beef", "pork", "fish", "tofu", "shrimp", "lamb", "turkey"],
        "make_sauce": ["sauce", "dressing", "vinaigrette", "glaze", "marinade"],
        "blanch": ["blanch", "parboil"],
        "zest": ["zest", "grate"],
    }

    # Vegetables that need chopping (expanded list)
    chop_vegetables = [
        "onion",
        "garlic",
        "pepper",
        "carrot",
        "celery",
        "tomato",
        "potato",
        "broccoli",
        "cauliflower",
        "zucchini",
        "mushroom",
        "cabbage",
        "leek",
        "shallot",
        "ginger",
        "scallion",
        "green onion",
        "cucumber",
        "eggplant",
        "spinach",
        "kale",
        "lettuce",
        "arugula",
        "watercress",
        "chard",
        "beet",
        "radish",
        "turnip",
        "parsnip",
        "squash",
        "pumpkin",
        "asparagus",
        "corn",
        "pea",
        "bean",
        "artichoke",
        "fennel",
        "bok choy",
        "sprout",
        "okra",
        "sun-dried tomato",
        "sundried tomato",
        "salad",
    ]

    # Proteins that can be pre-portioned/marinated (expanded)
    proteins = [
        "chicken",
        "beef",
        "pork",
        "fish",
        "salmon",
        "shrimp",
        "tofu",
        "lamb",
        "turkey",
        "steak",
        "ground meat",
        "sausage",
        "bacon",
        "ham",
        "prosciutto",
        "duck",
        "venison",
        "tuna",
        "cod",
        "halibut",
        "tilapia",
        "scallop",
        "crab",
        "lobster",
        "mussel",
        "clam",
        "oyster",
        "anchov",
        "egg",
    ]

    # Grains that can be batch cooked (expanded)
    grains = [
        "rice",
        "quinoa",
        "pasta",
        "couscous",
        "farro",
        "barley",
        "bulgur",
        "noodles",
        "orzo",
        "oat",
        "polenta",
        "grits",
        "bread",
        "tortilla",
        "pita",
        "naan",
        "millet",
        "wheat",
    ]

    # Storage info
    storage_guidelines = {
        "chopped_veg": {
            "container": "airtight container",
            "fridge_days": 4,
            "tips": "Store in paper towel to absorb moisture",
        },
        "cooked_grain": {
            "container": "airtight container",
            "fridge_days": 5,
            "tips": "Let cool completely before storing",
        },
        "marinated_protein": {
            "container": "zip-lock bag or container",
            "fridge_days": 2,
            "tips": "Marinate minimum 30min, max 24hr",
        },
        "cooked_protein": {
            "container": "airtight container",
            "fridge_days": 4,
            "tips": "Slice after cooling for sandwiches",
        },
        "sauce": {"container": "glass jar", "fridge_days": 7, "tips": "Shake before use"},
        "blanched_veg": {
            "container": "airtight container with paper towel",
            "fridge_days": 5,
            "tips": "Ice bath immediately after blanching",
        },
    }

    # Aggregate ingredients across all recipes
    all_ingredients = {}
    recipe_map = {}  # ingredient -> which recipes use it

    for item in items:
        recipe_id = item["recipe_id"]
        recipe_title = item["recipe_title"] or item["title"]
        meal_type = item["meal_type"]
        day = item["day_number"]

        try:
            ingredients = json.loads(item["ingredients"]) if item["ingredients"] else []
        except:
            ingredients = []

        for ing in ingredients:
            ing_lower = ing.lower()
            ing_key = ing_lower.split(",")[0].split("(")[0].strip()[:50]  # Normalize

            if ing_key not in all_ingredients:
                all_ingredients[ing_key] = {"original": ing, "count": 0, "recipes": []}
            all_ingredients[ing_key]["count"] += 1
            all_ingredients[ing_key]["recipes"].append(
                {"title": recipe_title, "meal_type": meal_type, "day": day}
            )

    # Generate prep tasks
    prep_tasks = {
        "vegetables": {
            "icon": "🥕",
            "title": "Vegetables - Wash, Peel & Chop",
            "description": "Prep all vegetables at once. Store in labeled containers.",
            "tasks": [],
            "storage": storage_guidelines["chopped_veg"],
            "estimated_time": 0,
        },
        "proteins": {
            "icon": "🥩",
            "title": "Proteins - Portion & Marinate",
            "description": "Portion proteins, prepare marinades. Marinated proteins last 1-2 days.",
            "tasks": [],
            "storage": storage_guidelines["marinated_protein"],
            "estimated_time": 0,
        },
        "grains": {
            "icon": "🍚",
            "title": "Grains - Batch Cook",
            "description": "Cook grains in bulk. They reheat perfectly all week.",
            "tasks": [],
            "storage": storage_guidelines["cooked_grain"],
            "estimated_time": 0,
        },
        "sauces": {
            "icon": "🥣",
            "title": "Sauces & Dressings",
            "description": "Make sauces ahead - they often taste better after a day.",
            "tasks": [],
            "storage": storage_guidelines["sauce"],
            "estimated_time": 0,
        },
        "other": {
            "icon": "📦",
            "title": "Other Prep",
            "description": "Miscellaneous prep tasks.",
            "tasks": [],
            "storage": None,
            "estimated_time": 0,
        },
    }

    # Categorize ingredients into prep tasks
    for ing_key, data in all_ingredients.items():
        # Check both the normalized key AND the original ingredient text
        ing_lower = ing_key.lower()
        orig_lower = data["original"].lower()
        combined_text = ing_lower + " " + orig_lower

        # Determine category
        category = "other"
        task_type = "prep"
        time_estimate = 2  # minutes

        # Check if vegetable
        for veg in chop_vegetables:
            if veg in combined_text:
                category = "vegetables"
                task_type = "chop"
                time_estimate = 3 * data["count"]  # 3 min per recipe using it
                break

        # Check if protein (only if not already categorized)
        if category == "other":
            for prot in proteins:
                if prot in combined_text:
                    category = "proteins"
                    task_type = "portion"
                    time_estimate = 5 * data["count"]
                    break

        # Check if grain (only if not already categorized)
        if category == "other":
            for grain in grains:
                if grain in combined_text:
                    category = "grains"
                    task_type = "cook"
                    time_estimate = 20  # Cooking time is fixed
                    break

        # Check if sauce-related
        if category == "other" and any(
            s in combined_text for s in ["sauce", "dressing", "vinaigrette", "glaze"]
        ):
            category = "sauces"
            task_type = "make"
            time_estimate = 10

        # Build task description
        recipe_list = ", ".join(
            [f"{r['title'][:20]}... (Day {r['day']})" for r in data["recipes"][:3]]
        )
        if len(data["recipes"]) > 3:
            recipe_list += f" +{len(data['recipes']) - 3} more"

        task = {
            "ingredient": data["original"],
            "normalized": ing_key,
            "action": task_type,
            "quantity": f"For {data['count']} recipe(s)",
            "used_in": recipe_list,
            "recipe_count": data["count"],
            "time_estimate": time_estimate,
            "done": False,
        }

        # Add to category if significant (used in 1+ recipes or is a core ingredient)
        if data["count"] >= 1 and category in prep_tasks:
            prep_tasks[category]["tasks"].append(task)
            prep_tasks[category]["estimated_time"] += time_estimate

    # Sort tasks by recipe count (most used ingredients first)
    for category in prep_tasks:
        prep_tasks[category]["tasks"].sort(key=lambda x: -x["recipe_count"])

    # Calculate total time
    total_time = sum(cat["estimated_time"] for cat in prep_tasks.values())

    # Generate optimized workflow sequence
    workflow = []

    # 1. Start grains first (they take longest)
    if prep_tasks["grains"]["tasks"]:
        workflow.append(
            {
                "phase": 1,
                "title": "Start Grains Cooking",
                "icon": "🍚",
                "description": "Start grains first - they cook while you prep other items",
                "tasks": [t["ingredient"] for t in prep_tasks["grains"]["tasks"]],
                "duration": "20-30 min (passive)",
            }
        )

    # 2. Prep vegetables (while grains cook)
    if prep_tasks["vegetables"]["tasks"]:
        workflow.append(
            {
                "phase": 2,
                "title": "Wash & Chop Vegetables",
                "icon": "🥕",
                "description": "Batch chop all vegetables. Group similar cuts together.",
                "tasks": [t["ingredient"] for t in prep_tasks["vegetables"]["tasks"][:10]],
                "duration": f"{prep_tasks['vegetables']['estimated_time']} min",
            }
        )

    # 3. Prep proteins (while grains finish)
    if prep_tasks["proteins"]["tasks"]:
        workflow.append(
            {
                "phase": 3,
                "title": "Portion & Marinate Proteins",
                "icon": "🥩",
                "description": "Cut proteins to size, apply marinades or seasonings",
                "tasks": [t["ingredient"] for t in prep_tasks["proteins"]["tasks"]],
                "duration": f"{prep_tasks['proteins']['estimated_time']} min",
            }
        )

    # 4. Make sauces
    if prep_tasks["sauces"]["tasks"]:
        workflow.append(
            {
                "phase": 4,
                "title": "Prepare Sauces & Dressings",
                "icon": "🥣",
                "description": "Blend or mix sauces - they improve with time",
                "tasks": [t["ingredient"] for t in prep_tasks["sauces"]["tasks"]],
                "duration": f"{prep_tasks['sauces']['estimated_time']} min",
            }
        )

    # 5. Pack and label
    workflow.append(
        {
            "phase": len(workflow) + 1,
            "title": "Pack & Label Containers",
            "icon": "📦",
            "description": "Transfer to containers, label with contents and date",
            "tasks": [
                "Label containers with day/meal",
                "Stack by meal day",
                "Note any reheating instructions",
            ],
            "duration": "10-15 min",
        }
    )

    # Container suggestions based on prep
    containers_needed = []
    if prep_tasks["vegetables"]["tasks"]:
        containers_needed.append(
            {
                "type": "Small containers (1-2 cup)",
                "quantity": len(prep_tasks["vegetables"]["tasks"]),
                "for": "Chopped vegetables",
            }
        )
    if prep_tasks["grains"]["tasks"]:
        containers_needed.append(
            {
                "type": "Medium containers (3-4 cup)",
                "quantity": len(prep_tasks["grains"]["tasks"]),
                "for": "Cooked grains",
            }
        )
    if prep_tasks["proteins"]["tasks"]:
        containers_needed.append(
            {
                "type": "Zip-lock bags or containers",
                "quantity": len(prep_tasks["proteins"]["tasks"]),
                "for": "Marinated proteins",
            }
        )
    if prep_tasks["sauces"]["tasks"]:
        containers_needed.append(
            {
                "type": "Small jars (8-12 oz)",
                "quantity": len(prep_tasks["sauces"]["tasks"]),
                "for": "Sauces and dressings",
            }
        )

    return jsonify(
        {
            "plan_id": plan_id,
            "plan_type": plan["plan_type"],
            "total_recipes": len(items),
            "total_prep_time_minutes": total_time,
            "total_prep_time_display": (
                f"{total_time // 60}h {total_time % 60}m"
                if total_time >= 60
                else f"{total_time} min"
            ),
            "prep_tasks": prep_tasks,
            "workflow": workflow,
            "containers_needed": containers_needed,
            "tips": [
                "Start with the longest cooking items (grains, roasted proteins)",
                "Group similar cuts together - dice all onions at once",
                "Use a damp paper towel under your cutting board to prevent slipping",
                "Clean as you go - wash prep bowls between ingredients",
                "Label containers with day and meal for easy grabbing",
                "Cooked grains freeze well for up to 3 months",
            ],
        }
    )


@app.route("/api/meal-plans/<int:plan_id>/prep-tasks/complete", methods=["POST"])
def complete_prep_task(plan_id):
    """Mark a prep task as complete."""
    data = request.get_json()
    task_id = data.get("task_id")
    # In a full implementation, this would update a database
    # For now, just acknowledge
    return jsonify({"success": True, "task_id": task_id})


@app.route("/plan/<int:plan_id>/prep")
def meal_prep_page(plan_id):
    """Meal prep view page."""
    return render_template("meal_prep.html", plan_id=plan_id)


# ============================================================================
# HOUSEHOLD MANAGEMENT - Family, Calendar, Scheduling (Lotus-Eater Integration)
# ============================================================================


# ----- HELPER FUNCTIONS -----


def calculate_day_busyness(date_str):
    """Calculate busyness score for a date (1-10)."""
    db = get_db()
    events = db.execute(
        """
        SELECT COUNT(*) as count,
               SUM(
                   CASE WHEN end_datetime IS NOT NULL
                   THEN (julianday(end_datetime) - julianday(start_datetime)) * 24
                   ELSE 1 END
               ) as hours
        FROM calendar_events
        WHERE date(start_datetime) = ?
    """,
        [date_str],
    ).fetchone()

    event_count = events["count"] or 0
    total_hours = events["hours"] or 0

    # Score: 1 event = 1, each hour = 0.5
    score = min(10, event_count + (total_hours * 0.5))
    suggested_complexity = max(1, 10 - int(score))

    return {
        "date": date_str,
        "event_count": event_count,
        "total_hours": round(total_hours, 1) if total_hours else 0,
        "busyness_score": int(score),
        "suggested_complexity": suggested_complexity,
    }


def create_auto_journal_entry(entry_type, source_id, data):
    """Create auto-journal entry for syncing to Lotus Journal."""
    db = get_db()

    if entry_type == "meal_cooked":
        title = f"Cooked {data.get('recipe_name', 'a meal')}"
        content = f"Prepared {data.get('meal_type', 'meal')} - {data.get('recipe_name', '')} for {data.get('servings', 2)} servings."
    elif entry_type == "quest_completed":
        title = f"Quest Complete: {data.get('title', 'Cooking Quest')}"
        content = f"Earned {data.get('xp_earned', 0)} XP!"
    else:
        title = data.get("title", "Activity")
        content = data.get("content", "")

    db.execute(
        """
        INSERT INTO auto_journal_entries (entry_date, entry_type, title, content, metadata)
        VALUES (date('now'), ?, ?, ?, ?)
    """,
        [entry_type, title, content, json.dumps(data)],
    )
    db.commit()

    # Try to sync to Lotus Journal (optional - fails silently if journal not running)
    try:
        sync_to_lotus_journal(title, content, entry_type)
    except Exception:
        pass  # Will sync later

    return True


def sync_to_lotus_journal(title, content, entry_type):
    """Sync entry to Lotus Journal via API."""
    payload = {
        "title": title,
        "content": content,
        "mood": "good",
        "type": "normal",
        "tags": ["auto", entry_type],
        "source": "food_app",
    }

    try:
        response = requests.post("http://localhost:8000/api/v1/entries", json=payload, timeout=5)
        return response.ok
    except requests.RequestException:
        return False


def create_meal_quest(scheduled_meal):
    """Create quest in Quest System when meal is scheduled."""
    db = get_db()

    # Calculate XP based on complexity
    base_xp = 50
    complexity = scheduled_meal.get("complexity_score", 5) or 5
    complexity_bonus = complexity * 10
    batch_bonus = 25 if scheduled_meal.get("servings", 2) >= 4 else 0
    total_xp = base_xp + complexity_bonus + batch_bonus

    quest_payload = {
        "title": f"Cook {scheduled_meal.get('recipe_name', 'meal')}",
        "description": f"Prepare {scheduled_meal.get('meal_type', 'meal')} for the family",
        "type": "DAILY",
        "difficulty": complexity,
        "xpReward": {"base": total_xp, "bonus": 0, "multiplier": 1.0, "total": total_xp},
        "metadata": {
            "tags": ["cooking", scheduled_meal.get("meal_type", "meal")],
            "source": "food_app",
            "sourceId": str(scheduled_meal.get("id", "")),
        },
    }

    # POST to Quest System
    try:
        response = requests.post("http://localhost:3002/api/quests", json=quest_payload, timeout=5)
        if response.ok:
            quest_data = response.json()
            db.execute(
                """
                INSERT INTO meal_quests (scheduled_meal_id, quest_id, quest_type, xp_reward)
                VALUES (?, ?, ?, ?)
            """,
                [scheduled_meal["id"], quest_data.get("id", str(uuid.uuid4())), "daily", total_xp],
            )
            db.commit()
            return quest_data
    except requests.RequestException:
        pass  # Quest System offline, continue without quest

    return None


# ----- FAMILY MEMBERS API -----


@app.route("/api/family/members", methods=["GET"])
def get_family_members():
    """Get all family members."""
    db = get_db()
    members = db.execute(
        """
        SELECT id, name, color, avatar_emoji, dietary_restrictions,
               calorie_target, is_primary, created_at
        FROM family_members
        ORDER BY is_primary DESC, name ASC
    """
    ).fetchall()

    return jsonify(
        {
            "members": [
                {
                    "id": m["id"],
                    "name": m["name"],
                    "color": m["color"],
                    "avatar_emoji": m["avatar_emoji"],
                    "dietary_restrictions": (
                        json.loads(m["dietary_restrictions"]) if m["dietary_restrictions"] else []
                    ),
                    "calorie_target": m["calorie_target"],
                    "is_primary": bool(m["is_primary"]),
                    "created_at": m["created_at"],
                }
                for m in members
            ]
        }
    )


@app.route("/api/family/members", methods=["POST"])
def create_family_member():
    """Create a new family member."""
    db = get_db()
    data = request.get_json()

    name = data.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400

    color = data.get("color", "#6366f1")
    avatar_emoji = data.get("avatar_emoji", "👤")
    dietary_restrictions = json.dumps(data.get("dietary_restrictions", []))
    calorie_target = data.get("calorie_target")
    is_primary = 1 if data.get("is_primary") else 0

    cursor = db.execute(
        """
        INSERT INTO family_members (name, color, avatar_emoji, dietary_restrictions, calorie_target, is_primary)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        [name, color, avatar_emoji, dietary_restrictions, calorie_target, is_primary],
    )
    db.commit()

    return jsonify(
        {
            "success": True,
            "member": {
                "id": cursor.lastrowid,
                "name": name,
                "color": color,
                "avatar_emoji": avatar_emoji,
                "dietary_restrictions": data.get("dietary_restrictions", []),
                "calorie_target": calorie_target,
                "is_primary": bool(is_primary),
            },
        }
    )


@app.route("/api/family/members/<int:member_id>", methods=["PUT"])
def update_family_member(member_id):
    """Update a family member."""
    db = get_db()
    data = request.get_json()

    updates = []
    params = []

    if "name" in data:
        updates.append("name = ?")
        params.append(data["name"])
    if "color" in data:
        updates.append("color = ?")
        params.append(data["color"])
    if "avatar_emoji" in data:
        updates.append("avatar_emoji = ?")
        params.append(data["avatar_emoji"])
    if "dietary_restrictions" in data:
        updates.append("dietary_restrictions = ?")
        params.append(json.dumps(data["dietary_restrictions"]))
    if "calorie_target" in data:
        updates.append("calorie_target = ?")
        params.append(data["calorie_target"])
    if "is_primary" in data:
        updates.append("is_primary = ?")
        params.append(1 if data["is_primary"] else 0)

    if not updates:
        return jsonify({"error": "No fields to update"}), 400

    params.append(member_id)
    db.execute(f"UPDATE family_members SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()

    return jsonify({"success": True, "member_id": member_id})


@app.route("/api/family/members/<int:member_id>", methods=["DELETE"])
def delete_family_member(member_id):
    """Delete a family member."""
    db = get_db()
    db.execute("DELETE FROM family_members WHERE id = ?", [member_id])
    db.commit()
    return jsonify({"success": True})


# ----- CALENDAR EVENTS API -----


@app.route("/api/calendar/events", methods=["GET"])
def get_calendar_events():
    """Get calendar events with optional date range filter."""
    db = get_db()
    start = request.args.get("start")
    end = request.args.get("end")
    member_id = request.args.get("member_id")

    query = """
        SELECT ce.*, fm.name as member_name, fm.color as member_color
        FROM calendar_events ce
        LEFT JOIN family_members fm ON ce.family_member_id = fm.id
        WHERE 1=1
    """
    params = []

    if start:
        query += " AND date(ce.start_datetime) >= ?"
        params.append(start)
    if end:
        query += " AND date(ce.start_datetime) <= ?"
        params.append(end)
    if member_id:
        query += " AND ce.family_member_id = ?"
        params.append(member_id)

    query += " ORDER BY ce.start_datetime ASC"
    events = db.execute(query, params).fetchall()

    return jsonify(
        {
            "events": [
                {
                    "id": e["id"],
                    "title": e["title"],
                    "description": e["description"],
                    "event_type": e["event_type"],
                    "source": e["source"],
                    "start_datetime": e["start_datetime"],
                    "end_datetime": e["end_datetime"],
                    "all_day": bool(e["all_day"]),
                    "family_member_id": e["family_member_id"],
                    "member_name": e["member_name"],
                    "color": e["color"] or e["member_color"],
                    "recurrence_rule": e["recurrence_rule"],
                    "external_id": e["external_id"],
                }
                for e in events
            ]
        }
    )


@app.route("/api/calendar/events", methods=["POST"])
def create_calendar_event():
    """Create a new calendar event."""
    db = get_db()
    data = request.get_json()

    title = data.get("title")
    if not title:
        return jsonify({"error": "Title is required"}), 400

    event_type = data.get("event_type", "appointment")
    start_datetime = data.get("start_datetime")
    if not start_datetime:
        return jsonify({"error": "start_datetime is required"}), 400

    cursor = db.execute(
        """
        INSERT INTO calendar_events
        (title, description, event_type, source, start_datetime, end_datetime,
         all_day, family_member_id, color, recurrence_rule, external_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            title,
            data.get("description"),
            event_type,
            data.get("source", "manual"),
            start_datetime,
            data.get("end_datetime"),
            1 if data.get("all_day") else 0,
            data.get("family_member_id"),
            data.get("color"),
            data.get("recurrence_rule"),
            data.get("external_id"),
        ],
    )
    db.commit()

    return jsonify({"success": True, "event_id": cursor.lastrowid})


@app.route("/api/calendar/events/<int:event_id>", methods=["PUT"])
def update_calendar_event(event_id):
    """Update a calendar event."""
    db = get_db()
    data = request.get_json()

    updates = []
    params = []

    fields = [
        "title",
        "description",
        "event_type",
        "start_datetime",
        "end_datetime",
        "all_day",
        "family_member_id",
        "color",
        "recurrence_rule",
    ]

    for field in fields:
        if field in data:
            updates.append(f"{field} = ?")
            if field == "all_day":
                params.append(1 if data[field] else 0)
            else:
                params.append(data[field])

    if not updates:
        return jsonify({"error": "No fields to update"}), 400

    params.append(event_id)
    db.execute(f"UPDATE calendar_events SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()

    return jsonify({"success": True, "event_id": event_id})


@app.route("/api/calendar/events/<int:event_id>", methods=["DELETE"])
def delete_calendar_event(event_id):
    """Delete a calendar event (cascades to scheduled_meals)."""
    db = get_db()
    db.execute("DELETE FROM calendar_events WHERE id = ?", [event_id])
    db.commit()
    return jsonify({"success": True})


@app.route("/api/calendar/week")
def get_calendar_week():
    """Get calendar events for a week view."""
    from datetime import timedelta

    date_str = request.args.get("date")
    if date_str:
        start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        start_date = date.today()

    # Get start of week (Monday)
    start_of_week = start_date - timedelta(days=start_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    db = get_db()

    # Get events for the week
    events = db.execute(
        """
        SELECT ce.*, fm.name as member_name, fm.color as member_color,
               sm.recipe_name, sm.meal_type, sm.complexity_score, sm.is_cooked
        FROM calendar_events ce
        LEFT JOIN family_members fm ON ce.family_member_id = fm.id
        LEFT JOIN scheduled_meals sm ON ce.id = sm.calendar_event_id
        WHERE date(ce.start_datetime) BETWEEN ? AND ?
        ORDER BY ce.start_datetime ASC
    """,
        [start_of_week.isoformat(), end_of_week.isoformat()],
    ).fetchall()

    # Group events by day
    days = {}
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        day_str = day.isoformat()
        days[day_str] = {
            "date": day_str,
            "day_name": day.strftime("%A"),
            "day_short": day.strftime("%a"),
            "day_number": day.day,
            "events": [],
            "meals": {"breakfast": None, "lunch": None, "dinner": None, "snack": None},
            "busyness": calculate_day_busyness(day_str),
        }

    for e in events:
        event_date = e["start_datetime"][:10]
        if event_date in days:
            event_data = {
                "id": e["id"],
                "title": e["title"],
                "event_type": e["event_type"],
                "start_time": e["start_datetime"][11:16] if len(e["start_datetime"]) > 10 else None,
                "end_time": (
                    e["end_datetime"][11:16]
                    if e["end_datetime"] and len(e["end_datetime"]) > 10
                    else None
                ),
                "color": e["color"] or e["member_color"],
                "member_name": e["member_name"],
                "recipe_name": e["recipe_name"],
                "meal_type": e["meal_type"],
                "complexity_score": e["complexity_score"],
                "is_cooked": bool(e["is_cooked"]) if e["is_cooked"] is not None else None,
            }
            days[event_date]["events"].append(event_data)

            # If it's a meal event, add to meals dict
            if e["meal_type"] and e["meal_type"] in days[event_date]["meals"]:
                days[event_date]["meals"][e["meal_type"]] = event_data

    return jsonify(
        {
            "start_date": start_of_week.isoformat(),
            "end_date": end_of_week.isoformat(),
            "days": list(days.values()),
        }
    )


@app.route("/api/calendar/month")
def get_calendar_month():
    """Get calendar events for a month view."""
    import calendar as cal
    from datetime import timedelta

    year = request.args.get("year", type=int) or date.today().year
    month = request.args.get("month", type=int) or date.today().month

    first_day = date(year, month, 1)
    last_day = date(year, month, cal.monthrange(year, month)[1])

    db = get_db()

    # Get events for the month
    events = db.execute(
        """
        SELECT ce.*, fm.name as member_name, fm.color as member_color,
               sm.recipe_name, sm.meal_type, sm.is_cooked
        FROM calendar_events ce
        LEFT JOIN family_members fm ON ce.family_member_id = fm.id
        LEFT JOIN scheduled_meals sm ON ce.id = sm.calendar_event_id
        WHERE date(ce.start_datetime) BETWEEN ? AND ?
        ORDER BY ce.start_datetime ASC
    """,
        [first_day.isoformat(), last_day.isoformat()],
    ).fetchall()

    # Group by day
    days = {}
    current = first_day
    while current <= last_day:
        day_str = current.isoformat()
        days[day_str] = {
            "date": day_str,
            "day_number": current.day,
            "day_name": current.strftime("%a"),
            "event_count": 0,
            "has_breakfast": False,
            "has_lunch": False,
            "has_dinner": False,
            "has_snack": False,
            "busyness": calculate_day_busyness(day_str),
        }
        current += timedelta(days=1)

    for e in events:
        event_date = e["start_datetime"][:10]
        if event_date in days:
            days[event_date]["event_count"] += 1
            if e["meal_type"]:
                days[event_date][f"has_{e['meal_type']}"] = True

    return jsonify(
        {
            "year": year,
            "month": month,
            "month_name": cal.month_name[month],
            "days": list(days.values()),
        }
    )


# ----- MEAL SCHEDULING API -----


@app.route("/api/meals/schedule", methods=["GET"])
def get_scheduled_meals():
    """Get scheduled meals for a date."""
    date_str = request.args.get("date")
    if not date_str:
        date_str = date.today().isoformat()

    db = get_db()
    meals = db.execute(
        """
        SELECT sm.*, ce.start_datetime, ce.end_datetime, fm.name as chef_name, fm.color as chef_color
        FROM scheduled_meals sm
        JOIN calendar_events ce ON sm.calendar_event_id = ce.id
        LEFT JOIN family_members fm ON sm.chef_member_id = fm.id
        WHERE date(ce.start_datetime) = ?
        ORDER BY
            CASE sm.meal_type
                WHEN 'breakfast' THEN 1
                WHEN 'lunch' THEN 2
                WHEN 'dinner' THEN 3
                WHEN 'snack' THEN 4
            END
    """,
        [date_str],
    ).fetchall()

    return jsonify(
        {
            "date": date_str,
            "meals": [
                {
                    "id": m["id"],
                    "calendar_event_id": m["calendar_event_id"],
                    "recipe_id": m["recipe_id"],
                    "recipe_source": m["recipe_source"],
                    "recipe_name": m["recipe_name"],
                    "meal_type": m["meal_type"],
                    "servings": m["servings"],
                    "complexity_score": m["complexity_score"],
                    "chef_member_id": m["chef_member_id"],
                    "chef_name": m["chef_name"],
                    "chef_color": m["chef_color"],
                    "is_cooked": bool(m["is_cooked"]),
                    "start_time": (
                        m["start_datetime"][11:16]
                        if m["start_datetime"] and len(m["start_datetime"]) > 10
                        else None
                    ),
                }
                for m in meals
            ],
        }
    )


@app.route("/api/meals/schedule", methods=["POST"])
def schedule_meal():
    """Schedule a meal on the calendar."""
    db = get_db()
    data = request.get_json()

    recipe_id = data.get("recipe_id")
    meal_type = data.get("meal_type")
    scheduled_date = data.get("scheduled_date")

    if not all([recipe_id, meal_type, scheduled_date]):
        return jsonify({"error": "recipe_id, meal_type, and scheduled_date are required"}), 400

    recipe_name = data.get("recipe_name", f"Recipe {recipe_id}")
    recipe_source = data.get("recipe_source", "local")
    servings = data.get("servings", 2)
    chef_member_id = data.get("chef_member_id")

    # Calculate complexity from prep+cook time if available
    complexity_score = data.get("complexity_score")
    if not complexity_score:
        complexity_score = 5  # Default

    # Default meal times
    meal_times = {"breakfast": "08:00", "lunch": "12:00", "dinner": "18:00", "snack": "15:00"}
    scheduled_time = data.get("scheduled_time") or meal_times.get(meal_type, "12:00")
    start_datetime = f"{scheduled_date} {scheduled_time}:00"

    # Get family member color if assigned
    color = None
    if chef_member_id:
        member = db.execute(
            "SELECT color FROM family_members WHERE id = ?", [chef_member_id]
        ).fetchone()
        if member:
            color = member["color"]

    # Create calendar event first
    cursor = db.execute(
        """
        INSERT INTO calendar_events
        (title, description, event_type, source, start_datetime, family_member_id, color)
        VALUES (?, ?, 'meal', 'food_app', ?, ?, ?)
    """,
        [
            f"{meal_type.title()}: {recipe_name}",
            f"Cook {recipe_name} ({servings} servings)",
            start_datetime,
            chef_member_id,
            color,
        ],
    )
    calendar_event_id = cursor.lastrowid

    # Create scheduled meal
    cursor = db.execute(
        """
        INSERT INTO scheduled_meals
        (calendar_event_id, recipe_id, recipe_source, recipe_name, meal_type,
         servings, complexity_score, chef_member_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            calendar_event_id,
            recipe_id,
            recipe_source,
            recipe_name,
            meal_type,
            servings,
            complexity_score,
            chef_member_id,
        ],
    )
    scheduled_meal_id = cursor.lastrowid
    db.commit()

    # Create quest if Quest System is available
    scheduled_meal = {
        "id": scheduled_meal_id,
        "recipe_name": recipe_name,
        "meal_type": meal_type,
        "complexity_score": complexity_score,
        "servings": servings,
    }
    quest = create_meal_quest(scheduled_meal)

    return jsonify(
        {
            "success": True,
            "scheduled_meal_id": scheduled_meal_id,
            "calendar_event_id": calendar_event_id,
            "quest_created": quest is not None,
        }
    )


@app.route("/api/meals/schedule/<int:meal_id>", methods=["PUT"])
def update_scheduled_meal(meal_id):
    """Update a scheduled meal."""
    db = get_db()
    data = request.get_json()

    updates = []
    params = []

    fields = [
        "recipe_id",
        "recipe_source",
        "recipe_name",
        "meal_type",
        "servings",
        "complexity_score",
        "chef_member_id",
        "is_cooked",
    ]

    for field in fields:
        if field in data:
            updates.append(f"{field} = ?")
            if field == "is_cooked":
                params.append(1 if data[field] else 0)
            else:
                params.append(data[field])

    if updates:
        params.append(meal_id)
        db.execute(f"UPDATE scheduled_meals SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()

    return jsonify({"success": True, "meal_id": meal_id})


@app.route("/api/meals/schedule/<int:meal_id>", methods=["DELETE"])
def delete_scheduled_meal(meal_id):
    """Delete a scheduled meal (and its calendar event)."""
    db = get_db()

    # Get calendar event ID first
    meal = db.execute(
        "SELECT calendar_event_id FROM scheduled_meals WHERE id = ?", [meal_id]
    ).fetchone()
    if meal:
        db.execute("DELETE FROM calendar_events WHERE id = ?", [meal["calendar_event_id"]])
        db.commit()

    return jsonify({"success": True})


@app.route("/api/meals/schedule/<int:meal_id>/complete", methods=["POST"])
def complete_scheduled_meal(meal_id):
    """Mark a scheduled meal as cooked."""
    db = get_db()

    # Mark as cooked
    db.execute("UPDATE scheduled_meals SET is_cooked = 1 WHERE id = ?", [meal_id])

    # Get meal details for logging
    meal = db.execute(
        """
        SELECT sm.*, mq.quest_id
        FROM scheduled_meals sm
        LEFT JOIN meal_quests mq ON sm.id = mq.scheduled_meal_id
        WHERE sm.id = ?
    """,
        [meal_id],
    ).fetchone()

    if meal:
        # Create journal entry
        create_auto_journal_entry(
            "meal_cooked",
            meal_id,
            {
                "recipe_name": meal["recipe_name"],
                "meal_type": meal["meal_type"],
                "servings": meal["servings"],
            },
        )

        # If there's a quest, mark it complete
        if meal["quest_id"]:
            db.execute(
                """
                UPDATE meal_quests
                SET completed = 1, completed_at = datetime('now')
                WHERE scheduled_meal_id = ?
            """,
                [meal_id],
            )

    db.commit()

    return jsonify({"success": True, "meal_id": meal_id})


# ----- BUSY DAY & SUGGESTIONS API -----


@app.route("/api/meals/suggestions")
def get_meal_suggestions():
    """Get recipe suggestions based on day busyness."""
    date_str = request.args.get("date")
    if not date_str:
        date_str = date.today().isoformat()

    meal_type = request.args.get("meal_type")

    busyness = calculate_day_busyness(date_str)
    max_complexity = busyness["suggested_complexity"]
    # For busy days (high busyness), suggest meals that take less time
    max_total_time = max_complexity * 15  # 1 = 15min, 10 = 150min

    db = get_db()
    recipes = []

    # First, try local recipes (which have proper timing data)
    query = """
        SELECT id, name, category, cuisine,
               COALESCE(prep_time_min, 0) as prep_time,
               COALESCE(cook_time_min, 0) as cook_time,
               servings, difficulty, image_url,
               CASE
                   WHEN (COALESCE(prep_time_min, 0) + COALESCE(cook_time_min, 0)) / 15 > 10 THEN 10
                   WHEN (COALESCE(prep_time_min, 0) + COALESCE(cook_time_min, 0)) / 15 < 1 THEN 1
                   ELSE (COALESCE(prep_time_min, 0) + COALESCE(cook_time_min, 0)) / 15
               END as complexity,
               'local' as source
        FROM recipes
        WHERE (COALESCE(prep_time_min, 0) + COALESCE(cook_time_min, 0)) <= ?
    """
    params = [max_total_time]

    if meal_type:
        query += " AND LOWER(category) LIKE ?"
        params.append(f"%{meal_type}%")

    query += " ORDER BY RANDOM() LIMIT 5"
    recipes = db.execute(query, params).fetchall()

    # Also get some from recipes_large (using random selection since no timing data)
    large_query = """
        SELECT id, title as name, category, cuisine,
               0 as prep_time,
               0 as cook_time,
               4 as servings,
               'medium' as difficulty,
               NULL as image_url,
               5 as complexity,
               'large' as source
        FROM recipes_large
    """
    large_params = []

    if meal_type:
        large_query += " WHERE LOWER(category) LIKE ?"
        large_params.append(f"%{meal_type}%")

    large_query += " ORDER BY RANDOM() LIMIT 5"
    large_recipes = db.execute(large_query, large_params).fetchall()

    # Combine both sources
    all_recipes = list(recipes) + list(large_recipes)

    return jsonify(
        {
            "date": date_str,
            "busyness": busyness,
            "max_complexity_suggested": max_complexity,
            "max_time_minutes": max_total_time,
            "suggestions": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "category": r["category"],
                    "cuisine": r["cuisine"],
                    "prep_time": r["prep_time"],
                    "cook_time": r["cook_time"],
                    "total_time": (r["prep_time"] or 0) + (r["cook_time"] or 0),
                    "servings": r["servings"],
                    "difficulty": r["difficulty"],
                    "image_url": r["image_url"],
                    "complexity": int(r["complexity"]) if r["complexity"] else 5,
                    "source": r["source"],
                }
                for r in all_recipes
            ],
        }
    )


@app.route("/api/calendar/busyness")
def get_busyness():
    """Get busyness score for a date."""
    date_str = request.args.get("date")
    if not date_str:
        date_str = date.today().isoformat()

    return jsonify(calculate_day_busyness(date_str))


# ----- INTEGRATION WEBHOOKS -----


@app.route("/api/webhooks/quest-completed", methods=["POST"])
def handle_quest_completed():
    """Called by Quest System when a cooking quest is completed."""
    db = get_db()
    data = request.get_json()
    quest_id = data.get("quest_id")
    xp_earned = data.get("xp_earned", 0)

    # Update meal_quests
    db.execute(
        """
        UPDATE meal_quests
        SET completed = 1, completed_at = datetime('now'), xp_earned = ?
        WHERE quest_id = ?
    """,
        [xp_earned, quest_id],
    )

    # Get scheduled meal to mark as cooked
    meal_quest = db.execute(
        """
        SELECT scheduled_meal_id FROM meal_quests WHERE quest_id = ?
    """,
        [quest_id],
    ).fetchone()

    if meal_quest:
        db.execute(
            """
            UPDATE scheduled_meals SET is_cooked = 1 WHERE id = ?
        """,
            [meal_quest["scheduled_meal_id"]],
        )

        # Get meal details
        meal = db.execute(
            """
            SELECT recipe_name, meal_type, servings FROM scheduled_meals WHERE id = ?
        """,
            [meal_quest["scheduled_meal_id"]],
        ).fetchone()

        if meal:
            create_auto_journal_entry(
                "quest_completed",
                quest_id,
                {
                    "title": f"Cook {meal['recipe_name']}",
                    "xp_earned": xp_earned,
                    "recipe_name": meal["recipe_name"],
                    "meal_type": meal["meal_type"],
                },
            )

    db.commit()

    return jsonify({"success": True})


@app.route("/api/journal/auto-entries")
def get_auto_journal_entries():
    """Get auto-generated journal entries."""
    db = get_db()
    limit = request.args.get("limit", 20, type=int)
    synced_only = request.args.get("synced_only", type=bool)

    query = "SELECT * FROM auto_journal_entries"
    params = []

    if synced_only is not None:
        query += " WHERE synced_to_journal = ?"
        params.append(1 if synced_only else 0)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    entries = db.execute(query, params).fetchall()

    return jsonify(
        {
            "entries": [
                {
                    "id": e["id"],
                    "entry_date": e["entry_date"],
                    "entry_type": e["entry_type"],
                    "title": e["title"],
                    "content": e["content"],
                    "metadata": json.loads(e["metadata"]) if e["metadata"] else None,
                    "synced_to_journal": bool(e["synced_to_journal"]),
                    "created_at": e["created_at"],
                }
                for e in entries
            ]
        }
    )


@app.route("/api/journal/sync", methods=["POST"])
def sync_journal_entries():
    """Sync unsynced entries to Lotus Journal."""
    db = get_db()

    unsynced = db.execute(
        """
        SELECT * FROM auto_journal_entries WHERE synced_to_journal = 0
    """
    ).fetchall()

    synced_count = 0
    for entry in unsynced:
        if sync_to_lotus_journal(entry["title"], entry["content"], entry["entry_type"]):
            db.execute(
                """
                UPDATE auto_journal_entries SET synced_to_journal = 1 WHERE id = ?
            """,
                [entry["id"]],
            )
            synced_count += 1

    db.commit()

    return jsonify({"success": True, "synced_count": synced_count, "total_pending": len(unsynced)})


# ----- PAGE ROUTES FOR HOUSEHOLD MANAGEMENT -----


@app.route("/calendar")
@app.route("/calendar/week")
def calendar_week_page():
    """Calendar week view page."""
    return render_template("calendar_week.html")


@app.route("/calendar/month")
def calendar_month_page():
    """Calendar month view page."""
    return render_template("calendar_month.html")


@app.route("/family")
def family_page():
    """Family member management page."""
    return render_template("family.html")


@app.route("/schedule")
def schedule_page():
    """Meal scheduler page."""
    return render_template("meal_scheduler.html")


# ============================================================================
# SIMS-STYLE GAMIFICATION API
# ============================================================================

# Level titles based on XP progression
LEVEL_TITLES = {
    1: "Kitchen Novice",
    2: "Prep Cook",
    3: "Line Cook",
    4: "Station Chef",
    5: "Sous Chef",
    6: "Chef de Partie",
    7: "Head Chef",
    8: "Executive Chef",
    9: "Master Chef",
    10: "Culinary Legend",
}


# XP required for each level (exponential growth)
def xp_for_level(level):
    """Calculate XP needed to reach a level."""
    return int(100 * (1.5 ** (level - 1)))


# Default skill tree definitions
DEFAULT_SKILLS = [
    # Root skills (always unlocked)
    {
        "name": "Basic Cooking",
        "category": "technique",
        "parent": None,
        "icon": "🍳",
        "desc": "Fundamental cooking techniques",
        "recipes": 0,
    },
    # Knife skills branch
    {
        "name": "Knife Skills",
        "category": "knife",
        "parent": "Basic Cooking",
        "icon": "🔪",
        "desc": "Cutting and chopping proficiency",
        "recipes": 5,
    },
    {
        "name": "Julienne Master",
        "category": "knife",
        "parent": "Knife Skills",
        "icon": "🥕",
        "desc": "Perfect thin strips every time",
        "recipes": 15,
    },
    {
        "name": "Speed Chopping",
        "category": "knife",
        "parent": "Knife Skills",
        "icon": "⚡",
        "desc": "Quick and precise cuts",
        "recipes": 20,
    },
    # Baking branch
    {
        "name": "Baking Basics",
        "category": "baking",
        "parent": "Basic Cooking",
        "icon": "🥖",
        "desc": "Bread, pastry, and dough",
        "recipes": 5,
    },
    {
        "name": "Pastry Chef",
        "category": "baking",
        "parent": "Baking Basics",
        "icon": "🥐",
        "desc": "Flaky crusts and delicate pastries",
        "recipes": 15,
    },
    {
        "name": "Artisan Baker",
        "category": "baking",
        "parent": "Pastry Chef",
        "icon": "🍞",
        "desc": "Complex breads and fermentation",
        "recipes": 30,
    },
    # Grilling branch
    {
        "name": "Grill Master",
        "category": "grilling",
        "parent": "Basic Cooking",
        "icon": "🔥",
        "desc": "BBQ and grilling techniques",
        "recipes": 5,
    },
    {
        "name": "Smoke & Fire",
        "category": "grilling",
        "parent": "Grill Master",
        "icon": "💨",
        "desc": "Smoking and indirect heat",
        "recipes": 15,
    },
    {
        "name": "BBQ Legend",
        "category": "grilling",
        "parent": "Smoke & Fire",
        "icon": "🍖",
        "desc": "Competition-level BBQ",
        "recipes": 30,
    },
    # World cuisines branch
    {
        "name": "World Explorer",
        "category": "world",
        "parent": "Basic Cooking",
        "icon": "🌍",
        "desc": "International cooking styles",
        "recipes": 10,
    },
    {
        "name": "Italian Master",
        "category": "world",
        "parent": "World Explorer",
        "icon": "🇮🇹",
        "desc": "Pasta, risotto, and more",
        "recipes": 20,
        "cuisine": "italian",
    },
    {
        "name": "Asian Fusion",
        "category": "world",
        "parent": "World Explorer",
        "icon": "🥢",
        "desc": "Pan-Asian techniques",
        "recipes": 20,
        "cuisine": "asian",
    },
    {
        "name": "French Technique",
        "category": "world",
        "parent": "World Explorer",
        "icon": "🇫🇷",
        "desc": "Classical French methods",
        "recipes": 20,
        "cuisine": "french",
    },
    {
        "name": "Mexican Heat",
        "category": "world",
        "parent": "World Explorer",
        "icon": "🌮",
        "desc": "Authentic Mexican flavors",
        "recipes": 20,
        "cuisine": "mexican",
    },
    # Advanced techniques
    {
        "name": "Sauce Wizard",
        "category": "technique",
        "parent": "Basic Cooking",
        "icon": "🥄",
        "desc": "Master of mother sauces",
        "recipes": 15,
    },
    {
        "name": "Molecular Gastronomy",
        "category": "technique",
        "parent": "Sauce Wizard",
        "icon": "🧪",
        "desc": "Science meets cooking",
        "recipes": 40,
    },
]

# Default achievements
DEFAULT_ACHIEVEMENTS = [
    # Cooking milestones
    {
        "name": "First Steps",
        "desc": "Cook your first meal",
        "icon": "👶",
        "cat": "cooking",
        "rarity": "common",
        "xp": 25,
        "cond": {"type": "cook_count", "value": 1},
    },
    {
        "name": "Getting Started",
        "desc": "Cook 5 meals",
        "icon": "🏃",
        "cat": "cooking",
        "rarity": "common",
        "xp": 50,
        "cond": {"type": "cook_count", "value": 5},
    },
    {
        "name": "Home Chef",
        "desc": "Cook 25 meals",
        "icon": "👨‍🍳",
        "cat": "cooking",
        "rarity": "uncommon",
        "xp": 100,
        "cond": {"type": "cook_count", "value": 25},
    },
    {
        "name": "Kitchen Veteran",
        "desc": "Cook 100 meals",
        "icon": "🎖️",
        "cat": "cooking",
        "rarity": "rare",
        "xp": 250,
        "cond": {"type": "cook_count", "value": 100},
    },
    {
        "name": "Master Chef",
        "desc": "Cook 500 meals",
        "icon": "👑",
        "cat": "cooking",
        "rarity": "legendary",
        "xp": 1000,
        "cond": {"type": "cook_count", "value": 500},
    },
    # Streak achievements
    {
        "name": "Consistent Cook",
        "desc": "7-day cooking streak",
        "icon": "🔥",
        "cat": "streak",
        "rarity": "uncommon",
        "xp": 75,
        "cond": {"type": "streak", "value": 7},
    },
    {
        "name": "Two Week Warrior",
        "desc": "14-day cooking streak",
        "icon": "💪",
        "cat": "streak",
        "rarity": "rare",
        "xp": 150,
        "cond": {"type": "streak", "value": 14},
    },
    {
        "name": "Monthly Master",
        "desc": "30-day cooking streak",
        "icon": "📅",
        "cat": "streak",
        "rarity": "epic",
        "xp": 300,
        "cond": {"type": "streak", "value": 30},
    },
    {
        "name": "Year of Flavor",
        "desc": "365-day cooking streak",
        "icon": "🏆",
        "cat": "streak",
        "rarity": "legendary",
        "xp": 2000,
        "cond": {"type": "streak", "value": 365},
        "hidden": 1,
    },
    # Variety achievements
    {
        "name": "Curious Cook",
        "desc": "Try 10 different recipes",
        "icon": "🔍",
        "cat": "variety",
        "rarity": "common",
        "xp": 50,
        "cond": {"type": "unique_recipes", "value": 10},
    },
    {
        "name": "Recipe Explorer",
        "desc": "Try 50 different recipes",
        "icon": "🗺️",
        "cat": "variety",
        "rarity": "uncommon",
        "xp": 150,
        "cond": {"type": "unique_recipes", "value": 50},
    },
    {
        "name": "Culinary Adventurer",
        "desc": "Try 100 different recipes",
        "icon": "🌟",
        "cat": "variety",
        "rarity": "rare",
        "xp": 300,
        "cond": {"type": "unique_recipes", "value": 100},
    },
    {
        "name": "Recipe Completionist",
        "desc": "Try 500 different recipes",
        "icon": "📚",
        "cat": "variety",
        "rarity": "legendary",
        "xp": 1500,
        "cond": {"type": "unique_recipes", "value": 500},
    },
    # Cuisine achievements
    {
        "name": "Italian Enthusiast",
        "desc": "Cook 10 Italian dishes",
        "icon": "🇮🇹",
        "cat": "variety",
        "rarity": "uncommon",
        "xp": 100,
        "cond": {"type": "cuisine_count", "cuisine": "italian", "value": 10},
    },
    {
        "name": "Asian Explorer",
        "desc": "Cook 10 Asian dishes",
        "icon": "🥢",
        "cat": "variety",
        "rarity": "uncommon",
        "xp": 100,
        "cond": {"type": "cuisine_count", "cuisine": "asian", "value": 10},
    },
    {
        "name": "World Traveler",
        "desc": "Cook from 5 different cuisines",
        "icon": "✈️",
        "cat": "variety",
        "rarity": "rare",
        "xp": 200,
        "cond": {"type": "cuisine_variety", "value": 5},
    },
    # Social achievements
    {
        "name": "Family Dinner",
        "desc": "Cook a meal for 4+ people",
        "icon": "👨‍👩‍👧‍👦",
        "cat": "social",
        "rarity": "common",
        "xp": 50,
        "cond": {"type": "servings", "value": 4},
    },
    {
        "name": "Party Host",
        "desc": "Cook a meal for 8+ people",
        "icon": "🎉",
        "cat": "social",
        "rarity": "uncommon",
        "xp": 100,
        "cond": {"type": "servings", "value": 8},
    },
    {
        "name": "Feast Master",
        "desc": "Cook a meal for 12+ people",
        "icon": "🏰",
        "cat": "social",
        "rarity": "rare",
        "xp": 200,
        "cond": {"type": "servings", "value": 12},
    },
    # Health achievements
    {
        "name": "Balanced Eater",
        "desc": "Meet all vitamin goals in a day",
        "icon": "💚",
        "cat": "health",
        "rarity": "uncommon",
        "xp": 100,
        "cond": {"type": "vitamins_met", "value": 14},
    },
    {
        "name": "Mineral Master",
        "desc": "Meet all mineral goals in a day",
        "icon": "💎",
        "cat": "health",
        "rarity": "uncommon",
        "xp": 100,
        "cond": {"type": "minerals_met", "value": 12},
    },
    {
        "name": "Perfect Nutrition",
        "desc": "Meet all micronutrient goals",
        "icon": "🌈",
        "cat": "health",
        "rarity": "rare",
        "xp": 250,
        "cond": {"type": "all_nutrients_met", "value": 1},
    },
    # Budget achievements
    {
        "name": "Budget Conscious",
        "desc": "Stay under budget for a week",
        "icon": "💰",
        "cat": "budget",
        "rarity": "common",
        "xp": 50,
        "cond": {"type": "budget_week", "value": 1},
    },
    {
        "name": "Frugal Chef",
        "desc": "Stay under budget for a month",
        "icon": "🏦",
        "cat": "budget",
        "rarity": "uncommon",
        "xp": 150,
        "cond": {"type": "budget_month", "value": 1},
    },
    # Meal prep achievements
    {
        "name": "Prep Pro",
        "desc": "Complete your first meal prep session",
        "icon": "📦",
        "cat": "cooking",
        "rarity": "common",
        "xp": 50,
        "cond": {"type": "meal_prep", "value": 1},
    },
    {
        "name": "Batch Master",
        "desc": "Prep meals for a full week",
        "icon": "🗓️",
        "cat": "cooking",
        "rarity": "uncommon",
        "xp": 100,
        "cond": {"type": "meal_prep_week", "value": 1},
    },
    # Hidden achievements
    {
        "name": "Night Owl",
        "desc": "Cook a meal after midnight",
        "icon": "🦉",
        "cat": "cooking",
        "rarity": "uncommon",
        "xp": 50,
        "cond": {"type": "time_of_day", "value": "night"},
        "hidden": 1,
    },
    {
        "name": "Early Bird",
        "desc": "Cook breakfast before 6am",
        "icon": "🐦",
        "cat": "cooking",
        "rarity": "uncommon",
        "xp": 50,
        "cond": {"type": "time_of_day", "value": "early"},
        "hidden": 1,
    },
    {
        "name": "Weekend Warrior",
        "desc": "Cook 3 different meals in one day",
        "icon": "⚔️",
        "cat": "cooking",
        "rarity": "rare",
        "xp": 150,
        "cond": {"type": "meals_per_day", "value": 3},
        "hidden": 1,
    },
]


def init_gamification_data():
    """Initialize default gamification data (skills, achievements)."""
    db = get_db()

    # Insert default skill tree definitions
    for skill in DEFAULT_SKILLS:
        db.execute(
            """
            INSERT OR IGNORE INTO skill_tree_definitions
            (skill_name, skill_category, parent_skill_name, icon, description, unlock_recipe_count, unlock_cuisine)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                skill["name"],
                skill["category"],
                skill.get("parent"),
                skill["icon"],
                skill["desc"],
                skill.get("recipes", 0),
                skill.get("cuisine"),
            ],
        )

    # Insert default achievements
    for ach in DEFAULT_ACHIEVEMENTS:
        db.execute(
            """
            INSERT OR IGNORE INTO achievements
            (name, description, icon, category, rarity, xp_reward, unlock_condition, hidden)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                ach["name"],
                ach["desc"],
                ach["icon"],
                ach["cat"],
                ach["rarity"],
                ach["xp"],
                json.dumps(ach["cond"]),
                ach.get("hidden", 0),
            ],
        )

    db.commit()


def ensure_member_gamification(member_id):
    """Ensure a family member has gamification records initialized."""
    db = get_db()

    # Create member_needs if not exists
    db.execute(
        """
        INSERT OR IGNORE INTO member_needs (family_member_id) VALUES (?)
    """,
        [member_id],
    )

    # Create member_levels if not exists
    db.execute(
        """
        INSERT OR IGNORE INTO member_levels (family_member_id) VALUES (?)
    """,
        [member_id],
    )

    # Create default streaks
    for streak_type in ["daily_cook", "healthy_meals", "budget", "variety"]:
        db.execute(
            """
            INSERT OR IGNORE INTO cooking_streaks (family_member_id, streak_type) VALUES (?, ?)
        """,
            [member_id, streak_type],
        )

    # Initialize skills from skill tree definitions
    skill_defs = db.execute("SELECT * FROM skill_tree_definitions").fetchall()
    for skill_def in skill_defs:
        # Root skills start unlocked
        unlocked = 1 if skill_def["parent_skill_name"] is None else 0
        db.execute(
            """
            INSERT OR IGNORE INTO cooking_skills
            (family_member_id, skill_name, skill_category, icon, description, unlocked)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            [
                member_id,
                skill_def["skill_name"],
                skill_def["skill_category"],
                skill_def["icon"],
                skill_def["description"],
                unlocked,
            ],
        )

    db.commit()


def calculate_needs_decay(member_id):
    """Calculate and apply needs decay based on time since last update."""
    db = get_db()

    needs = db.execute(
        """
        SELECT * FROM member_needs WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchone()

    if not needs:
        return None

    last_updated = (
        datetime.fromisoformat(needs["last_updated"]) if needs["last_updated"] else datetime.now()
    )
    hours_passed = (datetime.now() - last_updated).total_seconds() / 3600

    if hours_passed < 0.1:  # Less than 6 minutes
        return dict(needs)

    # Apply decay
    new_hunger = max(0, needs["hunger"] - int(hours_passed * needs["hunger_decay_rate"]))
    new_energy = max(0, needs["energy"] - int(hours_passed * needs["energy_decay_rate"]))

    # Update database
    db.execute(
        """
        UPDATE member_needs
        SET hunger = ?, energy = ?, last_updated = datetime('now')
        WHERE family_member_id = ?
    """,
        [new_hunger, new_energy, member_id],
    )
    db.commit()

    return {
        "hunger": new_hunger,
        "energy": needs["energy"],  # Energy decays differently
        "nutrition_balance": needs["nutrition_balance"],
        "social": needs["social"],
        "fun": needs["fun"],
        "budget_satisfaction": needs["budget_satisfaction"],
    }


def award_xp(member_id, xp_amount, source="cooking"):
    """Award XP to a member and handle level ups."""
    db = get_db()

    levels = db.execute(
        """
        SELECT * FROM member_levels WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchone()

    if not levels:
        ensure_member_gamification(member_id)
        levels = db.execute(
            """
            SELECT * FROM member_levels WHERE family_member_id = ?
        """,
            [member_id],
        ).fetchone()

    new_total_xp = levels["total_xp"] + xp_amount
    current_level = levels["current_level"]
    xp_needed = levels["xp_to_next_level"]

    # Check for level up
    leveled_up = False
    while new_total_xp >= xp_needed and current_level < 10:
        current_level += 1
        xp_needed = xp_for_level(current_level + 1)
        leveled_up = True

    new_title = LEVEL_TITLES.get(current_level, "Culinary Legend")

    db.execute(
        """
        UPDATE member_levels
        SET total_xp = ?, current_level = ?, xp_to_next_level = ?, title = ?
        WHERE family_member_id = ?
    """,
        [new_total_xp, current_level, xp_needed, new_title, member_id],
    )
    db.commit()

    return {
        "xp_awarded": xp_amount,
        "total_xp": new_total_xp,
        "current_level": current_level,
        "xp_to_next_level": xp_needed,
        "title": new_title,
        "leveled_up": leveled_up,
    }


def check_achievements(member_id):
    """Check and award any newly earned achievements."""
    db = get_db()
    newly_earned = []

    # Get member stats
    cook_count = db.execute(
        """
        SELECT COUNT(*) as count FROM cooking_sessions WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchone()["count"]

    unique_recipes = db.execute(
        """
        SELECT COUNT(DISTINCT recipe_id) as count FROM recipe_collection WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchone()["count"]

    current_streak = db.execute(
        """
        SELECT current_streak FROM cooking_streaks
        WHERE family_member_id = ? AND streak_type = 'daily_cook'
    """,
        [member_id],
    ).fetchone()
    streak_days = current_streak["current_streak"] if current_streak else 0

    # Get all unearned achievements
    unearned = db.execute(
        """
        SELECT a.* FROM achievements a
        WHERE a.id NOT IN (
            SELECT achievement_id FROM member_achievements WHERE family_member_id = ?
        )
    """,
        [member_id],
    ).fetchall()

    for ach in unearned:
        condition = json.loads(ach["unlock_condition"]) if ach["unlock_condition"] else {}
        earned = False

        if condition.get("type") == "cook_count" and cook_count >= condition.get("value", 0):
            earned = True
        elif condition.get("type") == "unique_recipes" and unique_recipes >= condition.get(
            "value", 0
        ):
            earned = True
        elif condition.get("type") == "streak" and streak_days >= condition.get("value", 0):
            earned = True

        if earned:
            db.execute(
                """
                INSERT INTO member_achievements (family_member_id, achievement_id)
                VALUES (?, ?)
            """,
                [member_id, ach["id"]],
            )

            # Award XP for achievement
            award_xp(member_id, ach["xp_reward"], "achievement")

            newly_earned.append(
                {
                    "name": ach["name"],
                    "description": ach["description"],
                    "icon": ach["icon"],
                    "rarity": ach["rarity"],
                    "xp_reward": ach["xp_reward"],
                }
            )

    db.commit()
    return newly_earned


def update_streak(member_id, streak_type="daily_cook"):
    """Update cooking streak for a member."""
    db = get_db()
    today = datetime.now().date().isoformat()

    streak = db.execute(
        """
        SELECT * FROM cooking_streaks
        WHERE family_member_id = ? AND streak_type = ?
    """,
        [member_id, streak_type],
    ).fetchone()

    if not streak:
        db.execute(
            """
            INSERT INTO cooking_streaks (family_member_id, streak_type, current_streak, last_activity_date)
            VALUES (?, ?, 1, ?)
        """,
            [member_id, streak_type, today],
        )
        db.commit()
        return {"current_streak": 1, "longest_streak": 1, "multiplier": 1.0}

    last_date = streak["last_activity_date"]
    current = streak["current_streak"]
    longest = streak["longest_streak"]

    if last_date == today:
        # Already updated today
        return {
            "current_streak": current,
            "longest_streak": longest,
            "multiplier": streak["streak_multiplier"],
        }

    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()

    if last_date == yesterday:
        # Streak continues!
        current += 1
        if current > longest:
            longest = current
    else:
        # Streak broken
        current = 1

    # Calculate streak multiplier (max 2.0x at 30+ days)
    multiplier = min(2.0, 1.0 + (current * 0.033))

    db.execute(
        """
        UPDATE cooking_streaks
        SET current_streak = ?, longest_streak = ?, last_activity_date = ?, streak_multiplier = ?
        WHERE family_member_id = ? AND streak_type = ?
    """,
        [current, longest, today, multiplier, member_id, streak_type],
    )
    db.commit()

    return {"current_streak": current, "longest_streak": longest, "multiplier": multiplier}


# ============================================================================
# GAMIFICATION API ENDPOINTS
# ============================================================================


@app.route("/api/game/member/<int:member_id>/dashboard")
def get_member_dashboard(member_id):
    """Get complete gamification dashboard for a family member."""
    db = get_db()

    # Ensure member has gamification records
    ensure_member_gamification(member_id)

    # Get member info
    member = db.execute("SELECT * FROM family_members WHERE id = ?", [member_id]).fetchone()
    if not member:
        return jsonify({"error": "Member not found"}), 404

    # Get needs (with decay calculation)
    needs = calculate_needs_decay(member_id)

    # Get level info
    levels = db.execute(
        """
        SELECT * FROM member_levels WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchone()

    # Get streaks
    streaks = db.execute(
        """
        SELECT streak_type, current_streak, longest_streak, streak_multiplier
        FROM cooking_streaks WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchall()

    # Get recent achievements
    achievements = db.execute(
        """
        SELECT a.name, a.description, a.icon, a.rarity, ma.earned_at
        FROM member_achievements ma
        JOIN achievements a ON ma.achievement_id = a.id
        WHERE ma.family_member_id = ?
        ORDER BY ma.earned_at DESC
        LIMIT 5
    """,
        [member_id],
    ).fetchall()

    # Get active goals
    today = datetime.now().date().isoformat()
    goals = db.execute(
        """
        SELECT * FROM member_goals
        WHERE family_member_id = ? AND end_date >= ? AND completed = 0
        ORDER BY end_date ASC
    """,
        [member_id, today],
    ).fetchall()

    # Get collection stats
    collection_stats = db.execute(
        """
        SELECT
            COUNT(*) as total_recipes,
            SUM(CASE WHEN is_mastered = 1 THEN 1 ELSE 0 END) as mastered,
            SUM(CASE WHEN is_favorite = 1 THEN 1 ELSE 0 END) as favorites,
            SUM(times_cooked) as total_cooks
        FROM recipe_collection
        WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchone()

    return jsonify(
        {
            "member": {
                "id": member["id"],
                "name": member["name"],
                "avatar_emoji": member["avatar_emoji"],
                "color": member["color"],
            },
            "level": {
                "current": levels["current_level"] if levels else 1,
                "title": levels["title"] if levels else "Kitchen Novice",
                "total_xp": levels["total_xp"] if levels else 0,
                "xp_to_next": levels["xp_to_next_level"] if levels else 100,
                "progress_percent": (
                    int(
                        (levels["total_xp"] % xp_for_level(levels["current_level"] + 1))
                        / xp_for_level(levels["current_level"] + 1)
                        * 100
                    )
                    if levels
                    else 0
                ),
            },
            "needs": {
                "hunger": {
                    "value": needs["hunger"] if needs else 50,
                    "status": (
                        "good"
                        if (needs and needs["hunger"] > 60)
                        else "warning" if (needs and needs["hunger"] > 30) else "critical"
                    ),
                },
                "energy": {
                    "value": needs["energy"] if needs else 75,
                    "status": (
                        "good"
                        if (needs and needs["energy"] > 60)
                        else "warning" if (needs and needs["energy"] > 30) else "critical"
                    ),
                },
                "nutrition": {
                    "value": needs["nutrition_balance"] if needs else 50,
                    "status": "good" if (needs and needs["nutrition_balance"] > 60) else "warning",
                },
                "social": {
                    "value": needs["social"] if needs else 50,
                    "status": "good" if (needs and needs["social"] > 60) else "warning",
                },
                "fun": {
                    "value": needs["fun"] if needs else 50,
                    "status": "good" if (needs and needs["fun"] > 60) else "warning",
                },
                "budget": {
                    "value": needs["budget_satisfaction"] if needs else 75,
                    "status": (
                        "good" if (needs and needs["budget_satisfaction"] > 60) else "warning"
                    ),
                },
            },
            "streaks": {
                s["streak_type"]: {
                    "current": s["current_streak"],
                    "longest": s["longest_streak"],
                    "multiplier": s["streak_multiplier"],
                }
                for s in streaks
            },
            "recent_achievements": [dict(a) for a in achievements],
            "active_goals": [dict(g) for g in goals],
            "collection": (
                dict(collection_stats)
                if collection_stats
                else {"total_recipes": 0, "mastered": 0, "favorites": 0, "total_cooks": 0}
            ),
        }
    )


@app.route("/api/game/member/<int:member_id>/needs")
def get_member_needs(member_id):
    """Get current needs/stats for a family member (Sims-style meters)."""
    ensure_member_gamification(member_id)
    needs = calculate_needs_decay(member_id)

    if not needs:
        return jsonify({"error": "Member not found"}), 404

    # Return needs with color-coded status
    def get_status(value):
        if value >= 70:
            return {"status": "green", "label": "Great"}
        elif value >= 40:
            return {"status": "yellow", "label": "OK"}
        elif value >= 20:
            return {"status": "orange", "label": "Low"}
        else:
            return {"status": "red", "label": "Critical"}

    return jsonify(
        {
            "hunger": {**get_status(needs["hunger"]), "value": needs["hunger"], "icon": "🍽️"},
            "energy": {**get_status(needs["energy"]), "value": needs["energy"], "icon": "⚡"},
            "nutrition": {
                **get_status(needs["nutrition_balance"]),
                "value": needs["nutrition_balance"],
                "icon": "🥗",
            },
            "social": {**get_status(needs["social"]), "value": needs["social"], "icon": "👥"},
            "fun": {**get_status(needs["fun"]), "value": needs["fun"], "icon": "🎮"},
            "budget": {
                **get_status(needs["budget_satisfaction"]),
                "value": needs["budget_satisfaction"],
                "icon": "💰",
            },
        }
    )


@app.route("/api/game/member/<int:member_id>/skills")
def get_member_skills(member_id):
    """Get skill tree for a family member."""
    db = get_db()
    ensure_member_gamification(member_id)

    skills = db.execute(
        """
        SELECT cs.*, std.parent_skill_name, std.unlock_recipe_count
        FROM cooking_skills cs
        LEFT JOIN skill_tree_definitions std ON cs.skill_name = std.skill_name
        WHERE cs.family_member_id = ?
        ORDER BY std.skill_category, cs.level DESC
    """,
        [member_id],
    ).fetchall()

    # Organize into tree structure
    skill_tree = {}
    for skill in skills:
        cat = skill["skill_category"]
        if cat not in skill_tree:
            skill_tree[cat] = []
        skill_tree[cat].append(
            {
                "name": skill["skill_name"],
                "level": skill["level"],
                "xp": skill["xp"],
                "xp_to_next": skill["xp_to_next_level"],
                "unlocked": bool(skill["unlocked"]),
                "icon": skill["icon"],
                "description": skill["description"],
                "parent": skill["parent_skill_name"],
                "unlock_requires": skill["unlock_recipe_count"],
            }
        )

    return jsonify(skill_tree)


@app.route("/api/game/member/<int:member_id>/achievements")
def get_member_achievements(member_id):
    """Get all achievements with earned status for a member."""
    db = get_db()
    ensure_member_gamification(member_id)

    # Get all achievements with earned status
    achievements = db.execute(
        """
        SELECT
            a.*,
            ma.earned_at,
            CASE WHEN ma.id IS NOT NULL THEN 1 ELSE 0 END as earned
        FROM achievements a
        LEFT JOIN member_achievements ma ON a.id = ma.achievement_id AND ma.family_member_id = ?
        WHERE a.hidden = 0 OR ma.id IS NOT NULL
        ORDER BY a.category, a.rarity DESC
    """,
        [member_id],
    ).fetchall()

    # Group by category
    by_category = {}
    for ach in achievements:
        cat = ach["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(
            {
                "name": ach["name"],
                "description": ach["description"],
                "icon": ach["icon"],
                "rarity": ach["rarity"],
                "xp_reward": ach["xp_reward"],
                "earned": bool(ach["earned"]),
                "earned_at": ach["earned_at"],
            }
        )

    # Calculate totals
    total = len(achievements)
    earned = sum(1 for a in achievements if a["earned"])

    return jsonify(
        {
            "achievements": by_category,
            "summary": {
                "total": total,
                "earned": earned,
                "percent": int(earned / total * 100) if total > 0 else 0,
            },
        }
    )


@app.route("/api/game/member/<int:member_id>/collection")
def get_member_collection(member_id):
    """Get recipe collection (collectible card game style)."""
    db = get_db()

    collection = db.execute(
        """
        SELECT * FROM recipe_collection
        WHERE family_member_id = ?
        ORDER BY last_cooked_at DESC
    """,
        [member_id],
    ).fetchall()

    # Group by rarity
    by_rarity = {"common": [], "uncommon": [], "rare": [], "epic": [], "legendary": []}
    for recipe in collection:
        rarity = recipe["rarity"] or "common"
        by_rarity[rarity].append(
            {
                "recipe_id": recipe["recipe_id"],
                "name": recipe["recipe_name"],
                "cuisine": recipe["cuisine"],
                "times_cooked": recipe["times_cooked"],
                "is_mastered": bool(recipe["is_mastered"]),
                "is_favorite": bool(recipe["is_favorite"]),
                "rating": recipe["personal_rating"],
                "card_style": recipe["card_style"],
                "first_cooked": recipe["first_cooked_at"],
            }
        )

    return jsonify(
        {
            "collection": by_rarity,
            "stats": {
                "total": len(collection),
                "mastered": sum(1 for r in collection if r["is_mastered"]),
                "favorites": sum(1 for r in collection if r["is_favorite"]),
                "by_rarity": {k: len(v) for k, v in by_rarity.items()},
            },
        }
    )


@app.route("/api/game/member/<int:member_id>/cook", methods=["POST"])
def record_cooking_session(member_id):
    """Record a cooking session and award XP, update needs, check achievements."""
    db = get_db()
    data = request.get_json()

    ensure_member_gamification(member_id)

    recipe_id = data.get("recipe_id")
    recipe_name = data.get("recipe_name", "Unknown Recipe")
    recipe_source = data.get("recipe_source", "local")
    cuisine = data.get("cuisine", "other")
    complexity = data.get("complexity", 5)
    servings = data.get("servings", 2)
    duration = data.get("duration_minutes", 30)
    is_social = data.get("is_social_meal", False)

    # Check if first time cooking this recipe
    existing = db.execute(
        """
        SELECT * FROM recipe_collection
        WHERE family_member_id = ? AND recipe_id = ? AND recipe_source = ?
    """,
        [member_id, recipe_id, recipe_source],
    ).fetchone()

    is_first_time = existing is None

    # Calculate XP
    base_xp = 25  # Base XP for any cook
    complexity_bonus = complexity * 5  # Up to 50 XP for complex recipes
    first_time_bonus = 50 if is_first_time else 0
    servings_bonus = max(0, (servings - 2) * 10)  # Bonus for cooking for more people

    # Get streak multiplier
    streak_info = update_streak(member_id, "daily_cook")
    multiplier = streak_info["multiplier"]

    streak_bonus = int((base_xp + complexity_bonus) * (multiplier - 1))
    total_xp = int((base_xp + complexity_bonus + first_time_bonus + servings_bonus + streak_bonus))

    # Record cooking session
    db.execute(
        """
        INSERT INTO cooking_sessions
        (family_member_id, recipe_id, recipe_source, recipe_name, cuisine, complexity,
         started_at, completed_at, duration_minutes, servings_made,
         base_xp, streak_bonus_xp, complexity_bonus_xp, first_time_bonus_xp, total_xp)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now', ?), datetime('now'), ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            member_id,
            recipe_id,
            recipe_source,
            recipe_name,
            cuisine,
            complexity,
            f"-{duration} minutes",
            duration,
            servings,
            base_xp,
            streak_bonus,
            complexity_bonus,
            first_time_bonus,
            total_xp,
        ],
    )

    # Update or create recipe collection entry
    if is_first_time:
        # Determine rarity based on complexity
        rarity = "common"
        if complexity >= 8:
            rarity = "legendary"
        elif complexity >= 6:
            rarity = "epic"
        elif complexity >= 4:
            rarity = "rare"
        elif complexity >= 2:
            rarity = "uncommon"

        db.execute(
            """
            INSERT INTO recipe_collection
            (family_member_id, recipe_id, recipe_source, recipe_name, cuisine,
             times_cooked, first_cooked_at, last_cooked_at, rarity)
            VALUES (?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'), ?)
        """,
            [member_id, recipe_id, recipe_source, recipe_name, cuisine, rarity],
        )
    else:
        times = existing["times_cooked"] + 1
        is_mastered = 1 if times >= 5 else 0
        db.execute(
            """
            UPDATE recipe_collection
            SET times_cooked = ?, last_cooked_at = datetime('now'), is_mastered = ?
            WHERE family_member_id = ? AND recipe_id = ? AND recipe_source = ?
        """,
            [times, is_mastered, member_id, recipe_id, recipe_source],
        )

    # Update needs
    hunger_restore = min(100, 30 + (servings * 5))  # More food = more hunger restoration
    social_restore = 20 if is_social else 5
    fun_restore = 15 if is_first_time else 5  # New recipes are more fun

    db.execute(
        """
        UPDATE member_needs
        SET hunger = MIN(100, hunger + ?),
            social = MIN(100, social + ?),
            fun = MIN(100, fun + ?),
            last_meal_at = datetime('now'),
            last_updated = datetime('now')
        WHERE family_member_id = ?
    """,
        [hunger_restore, social_restore, fun_restore, member_id],
    )

    if is_social:
        db.execute(
            """
            UPDATE member_needs SET last_social_meal_at = datetime('now')
            WHERE family_member_id = ?
        """,
            [member_id],
        )

    db.commit()

    # Award XP
    level_info = award_xp(member_id, total_xp, "cooking")

    # Check for new achievements
    new_achievements = check_achievements(member_id)

    return jsonify(
        {
            "success": True,
            "xp": {
                "base": base_xp,
                "complexity_bonus": complexity_bonus,
                "first_time_bonus": first_time_bonus,
                "servings_bonus": servings_bonus,
                "streak_bonus": streak_bonus,
                "streak_multiplier": multiplier,
                "total": total_xp,
            },
            "level": level_info,
            "streak": streak_info,
            "needs_restored": {
                "hunger": hunger_restore,
                "social": social_restore,
                "fun": fun_restore,
            },
            "new_achievements": new_achievements,
            "is_first_time": is_first_time,
        }
    )


@app.route("/api/game/member/<int:member_id>/goals", methods=["GET", "POST"])
def member_goals(member_id):
    """Get or create goals for a member."""
    db = get_db()
    ensure_member_gamification(member_id)

    if request.method == "GET":
        today = datetime.now().date().isoformat()
        goals = db.execute(
            """
            SELECT * FROM member_goals
            WHERE family_member_id = ? AND end_date >= ?
            ORDER BY completed ASC, end_date ASC
        """,
            [member_id, today],
        ).fetchall()

        return jsonify([dict(g) for g in goals])

    else:  # POST - create new goal
        data = request.get_json()

        goal_type = data.get("goal_type", "weekly")
        goal_category = data.get("category", "cooking")
        target = data.get("target", 5)
        description = data.get("description", "")
        xp_reward = data.get("xp_reward", 50)

        # Calculate dates based on goal type
        start_date = datetime.now().date()
        if goal_type == "daily":
            end_date = start_date
        elif goal_type == "weekly":
            end_date = start_date + timedelta(days=7)
        else:  # monthly
            end_date = start_date + timedelta(days=30)

        db.execute(
            """
            INSERT INTO member_goals
            (family_member_id, goal_type, goal_category, target_value, description, xp_reward, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                member_id,
                goal_type,
                goal_category,
                target,
                description,
                xp_reward,
                start_date.isoformat(),
                end_date.isoformat(),
            ],
        )
        db.commit()

        return jsonify({"success": True, "message": "Goal created"})


@app.route("/api/game/member/<int:member_id>/auto-goals", methods=["POST"])
def generate_auto_goals(member_id):
    """Auto-generate weekly goals based on member's stats."""
    db = get_db()
    ensure_member_gamification(member_id)

    # Get member's cooking stats
    cook_count = db.execute(
        """
        SELECT COUNT(*) as count FROM cooking_sessions
        WHERE family_member_id = ? AND completed_at > datetime('now', '-7 days')
    """,
        [member_id],
    ).fetchone()["count"]

    unique_cuisines = db.execute(
        """
        SELECT COUNT(DISTINCT cuisine) as count FROM cooking_sessions
        WHERE family_member_id = ?
    """,
        [member_id],
    ).fetchone()["count"]

    # Generate personalized goals
    start_date = datetime.now().date().isoformat()
    end_date = (datetime.now().date() + timedelta(days=7)).isoformat()

    goals = []

    # Cooking goal (based on last week's activity + 20%)
    cook_target = max(3, int(cook_count * 1.2))
    goals.append(
        {
            "goal_type": "weekly",
            "goal_category": "cooking",
            "target_value": cook_target,
            "description": f"Cook {cook_target} meals this week",
            "xp_reward": cook_target * 10,
        }
    )

    # Variety goal
    if unique_cuisines < 3:
        goals.append(
            {
                "goal_type": "weekly",
                "goal_category": "variety",
                "target_value": 2,
                "description": "Try 2 new cuisines",
                "xp_reward": 75,
            }
        )

    # Insert goals
    for goal in goals:
        db.execute(
            """
            INSERT INTO member_goals
            (family_member_id, goal_type, goal_category, target_value, description, xp_reward, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                member_id,
                goal["goal_type"],
                goal["goal_category"],
                goal["target_value"],
                goal["description"],
                goal["xp_reward"],
                start_date,
                end_date,
            ],
        )

    db.commit()

    return jsonify({"success": True, "goals_created": len(goals), "goals": goals})


@app.route("/api/game/leaderboard")
def get_leaderboard():
    """Get family leaderboard."""
    db = get_db()

    leaderboard = db.execute(
        """
        SELECT
            fm.id, fm.name, fm.avatar_emoji, fm.color,
            ml.total_xp, ml.current_level, ml.title,
            (SELECT COUNT(*) FROM cooking_sessions WHERE family_member_id = fm.id) as total_cooks,
            (SELECT current_streak FROM cooking_streaks
             WHERE family_member_id = fm.id AND streak_type = 'daily_cook') as streak
        FROM family_members fm
        LEFT JOIN member_levels ml ON fm.id = ml.family_member_id
        ORDER BY ml.total_xp DESC
    """
    ).fetchall()

    return jsonify(
        [
            {
                "rank": i + 1,
                "member_id": m["id"],
                "name": m["name"],
                "avatar": m["avatar_emoji"],
                "color": m["color"],
                "level": m["current_level"] or 1,
                "title": m["title"] or "Kitchen Novice",
                "total_xp": m["total_xp"] or 0,
                "total_cooks": m["total_cooks"] or 0,
                "streak": m["streak"] or 0,
            }
            for i, m in enumerate(leaderboard)
        ]
    )


@app.route("/api/game/init", methods=["POST"])
def init_game_data():
    """Initialize gamification data (run once or to reset)."""
    init_gamification_data()

    # Initialize all existing family members
    db = get_db()
    members = db.execute("SELECT id FROM family_members").fetchall()
    for m in members:
        ensure_member_gamification(m["id"])

    return jsonify({"success": True, "message": "Gamification data initialized"})


# ============================================================================
# AUTO MEAL PLAN GENERATION (Eat This Much style)
# ============================================================================


@app.route("/api/meal-plans/auto-generate", methods=["POST"])
def auto_generate_meal_plan():
    """Auto-generate a meal plan based on preferences and nutrition goals."""
    db = get_db()
    data = request.get_json()

    plan_type = data.get("plan_type", "week")
    budget = data.get("budget", 100)
    calorie_target = data.get("calories", 2000)
    include_snacks = data.get("include_snacks", False)
    dietary_restrictions = data.get("dietary_restrictions", [])  # vegetarian, vegan, gluten-free
    preferred_cuisines = data.get("cuisines", [])
    max_prep_time = data.get("max_prep_time", 60)  # minutes

    # Determine number of days
    days = {"day": 1, "week": 7, "month": 30}.get(plan_type, 7)
    meals_per_day = 4 if include_snacks else 3

    # Create the meal plan
    cursor = db.execute(
        """
        INSERT INTO meal_plans
        (plan_type, budget_total, budget_remaining, breakfasts_needed, lunches_needed, dinners_needed, snacks_needed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        [plan_type, budget, budget, days, days, days, days if include_snacks else 0],
    )
    plan_id = cursor.lastrowid

    # Get available recipes
    recipes = db.execute(
        """
        SELECT id, title, ingredients
        FROM recipes_large
        ORDER BY RANDOM()
        LIMIT 500
    """
    ).fetchall()

    # Simple categorization (in reality, you'd want better metadata)
    breakfast_keywords = [
        "egg",
        "pancake",
        "waffle",
        "oatmeal",
        "cereal",
        "toast",
        "muffin",
        "breakfast",
        "morning",
    ]
    lunch_keywords = ["salad", "sandwich", "soup", "wrap", "bowl", "light"]
    dinner_keywords = ["chicken", "beef", "pork", "fish", "pasta", "rice", "steak", "roast"]

    def categorize_recipe(recipe):
        title_lower = recipe["title"].lower()
        ingredients_lower = (recipe["ingredients"] or "").lower()

        for kw in breakfast_keywords:
            if kw in title_lower or kw in ingredients_lower:
                return "breakfast"
        for kw in lunch_keywords:
            if kw in title_lower:
                return "lunch"
        for kw in dinner_keywords:
            if kw in title_lower or kw in ingredients_lower:
                return "dinner"
        return "dinner"  # Default to dinner

    # Categorize recipes
    categorized = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
    for recipe in recipes:
        cat = categorize_recipe(recipe)
        categorized[cat].append(recipe)

    # Assign recipes to days
    import random

    selected_items = []

    for day in range(1, days + 1):
        # Breakfast
        if categorized["breakfast"]:
            recipe = random.choice(categorized["breakfast"])
            selected_items.append(
                {
                    "recipe_id": f"local_{recipe['id']}",
                    "recipe_title": recipe["title"],
                    "meal_type": "breakfast",
                    "day_number": day,
                }
            )

        # Lunch
        if categorized["lunch"]:
            recipe = random.choice(categorized["lunch"])
        else:
            recipe = random.choice(categorized["dinner"])
        selected_items.append(
            {
                "recipe_id": f"local_{recipe['id']}",
                "recipe_title": recipe["title"],
                "meal_type": "lunch",
                "day_number": day,
            }
        )

        # Dinner
        if categorized["dinner"]:
            recipe = random.choice(categorized["dinner"])
            selected_items.append(
                {
                    "recipe_id": f"local_{recipe['id']}",
                    "recipe_title": recipe["title"],
                    "meal_type": "dinner",
                    "day_number": day,
                }
            )

    # Insert items
    for item in selected_items:
        db.execute(
            """
            INSERT INTO meal_plan_items
            (plan_id, recipe_id, recipe_title, meal_type, day_number)
            VALUES (?, ?, ?, ?, ?)
        """,
            [
                plan_id,
                item["recipe_id"],
                item["recipe_title"],
                item["meal_type"],
                item["day_number"],
            ],
        )

    # Update plan counts
    db.execute(
        """
        UPDATE meal_plans SET
            breakfasts_selected = (SELECT COUNT(*) FROM meal_plan_items WHERE plan_id = ? AND meal_type = 'breakfast'),
            lunches_selected = (SELECT COUNT(*) FROM meal_plan_items WHERE plan_id = ? AND meal_type = 'lunch'),
            dinners_selected = (SELECT COUNT(*) FROM meal_plan_items WHERE plan_id = ? AND meal_type = 'dinner')
        WHERE id = ?
    """,
        [plan_id, plan_id, plan_id, plan_id],
    )

    db.commit()

    return jsonify(
        {
            "success": True,
            "plan_id": plan_id,
            "plan_type": plan_type,
            "days": days,
            "meals_generated": len(selected_items),
            "items": selected_items,
        }
    )


# ============================================================================
# GAMIFICATION PAGE ROUTES
# ============================================================================


@app.route("/game")
def game_dashboard():
    """Main gamification dashboard."""
    return render_template("game_dashboard.html")


@app.route("/game/member/<int:member_id>")
def member_game_profile(member_id):
    """Individual member's game profile."""
    return render_template("game_profile.html", member_id=member_id)


@app.route("/game/skills/<int:member_id>")
def member_skill_tree(member_id):
    """Skill tree visualization for a member."""
    return render_template("skill_tree.html", member_id=member_id)


@app.route("/game/achievements")
def achievements_page():
    """Achievements showcase."""
    return render_template("achievements.html")


@app.route("/game/collection/<int:member_id>")
def recipe_collection_page(member_id):
    """Recipe collection (card game style)."""
    return render_template("recipe_collection.html", member_id=member_id)


# ============================================================================
# PERSONAL ANALYTICS & INDIVIDUAL DATA TRACKING
# ============================================================================


def ensure_personal_tracking_tables():
    """Create tables for individual-focused data tracking."""
    db = get_db()

    # Personal nutrition log - tracks what you actually ate
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS nutrition_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date DATE NOT NULL,
            meal_type TEXT NOT NULL,  -- breakfast/lunch/dinner/snack
            recipe_id TEXT,
            recipe_name TEXT,
            calories INTEGER,
            protein_g REAL,
            carbs_g REAL,
            fat_g REAL,
            fiber_g REAL,
            sodium_mg REAL,
            servings REAL DEFAULT 1,
            notes TEXT,
            mood_before TEXT,  -- track how you felt
            mood_after TEXT,
            energy_level INTEGER,  -- 1-10
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Personal goals & targets (individual focused)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS personal_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT NOT NULL,  -- daily_calories, weekly_variety, monthly_new_recipes
            target_value REAL NOT NULL,
            current_value REAL DEFAULT 0,
            start_date DATE,
            end_date DATE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Cooking insights - auto-generated observations
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS cooking_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT NOT NULL,  -- pattern, recommendation, milestone
            insight_title TEXT NOT NULL,
            insight_text TEXT NOT NULL,
            data_json TEXT,  -- supporting data
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Meal ratings - rate what you cook
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id TEXT NOT NULL,
            recipe_name TEXT,
            rating INTEGER NOT NULL,  -- 1-5 stars
            would_make_again INTEGER DEFAULT 1,
            notes TEXT,
            tags TEXT,  -- JSON array: quick, comfort, healthy, etc
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # User achievements - individual achievement tracking
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notified INTEGER DEFAULT 0,
            FOREIGN KEY (achievement_id) REFERENCES achievements(id)
        )
    """
    )

    db.commit()


@app.route("/api/personal/analytics")
def get_personal_analytics():
    """Get comprehensive personal cooking analytics."""
    db = get_db()
    ensure_personal_tracking_tables()

    # Time period (default last 30 days)
    days = request.args.get("days", 30, type=int)

    # Cooking frequency analysis
    cooking_stats = db.execute(
        """
        SELECT
            COUNT(*) as total_sessions,
            COUNT(DISTINCT date(completed_at)) as unique_days,
            AVG(total_xp) as avg_xp,
            SUM(total_xp) as total_xp,
            COUNT(DISTINCT recipe_id) as unique_recipes,
            COUNT(DISTINCT cuisine) as unique_cuisines
        FROM cooking_sessions
        WHERE completed_at > datetime('now', ?)
    """,
        [f"-{days} days"],
    ).fetchone()

    # Day of week patterns
    day_patterns = db.execute(
        """
        SELECT
            strftime('%w', completed_at) as day_of_week,
            COUNT(*) as count
        FROM cooking_sessions
        WHERE completed_at > datetime('now', ?)
        GROUP BY day_of_week
        ORDER BY day_of_week
    """,
        [f"-{days} days"],
    ).fetchall()

    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    day_stats = {day_names[int(d["day_of_week"])]: d["count"] for d in day_patterns}

    # Time of day patterns
    time_patterns = db.execute(
        """
        SELECT
            CASE
                WHEN CAST(strftime('%H', completed_at) AS INTEGER) < 10 THEN 'morning'
                WHEN CAST(strftime('%H', completed_at) AS INTEGER) < 14 THEN 'lunch'
                WHEN CAST(strftime('%H', completed_at) AS INTEGER) < 18 THEN 'afternoon'
                ELSE 'evening'
            END as time_slot,
            COUNT(*) as count
        FROM cooking_sessions
        WHERE completed_at > datetime('now', ?)
        GROUP BY time_slot
    """,
        [f"-{days} days"],
    ).fetchall()

    # Top cuisines
    top_cuisines = db.execute(
        """
        SELECT cuisine, COUNT(*) as count
        FROM cooking_sessions
        WHERE cuisine IS NOT NULL AND completed_at > datetime('now', ?)
        GROUP BY cuisine
        ORDER BY count DESC
        LIMIT 5
    """,
        [f"-{days} days"],
    ).fetchall()

    # Most cooked recipes
    top_recipes = db.execute(
        """
        SELECT recipe_name, COUNT(*) as times_cooked, AVG(total_xp) as avg_xp
        FROM cooking_sessions
        WHERE completed_at > datetime('now', ?)
        GROUP BY recipe_id
        ORDER BY times_cooked DESC
        LIMIT 5
    """,
        [f"-{days} days"],
    ).fetchall()

    # Weekly trend
    weekly_trend = db.execute(
        """
        SELECT
            strftime('%Y-%W', completed_at) as week,
            COUNT(*) as sessions,
            SUM(total_xp) as xp
        FROM cooking_sessions
        WHERE completed_at > datetime('now', ?)
        GROUP BY week
        ORDER BY week
    """,
        [f"-{days} days"],
    ).fetchall()

    # Nutrition summary (if logged)
    nutrition_summary = db.execute(
        """
        SELECT
            AVG(calories) as avg_calories,
            AVG(protein_g) as avg_protein,
            AVG(carbs_g) as avg_carbs,
            AVG(fat_g) as avg_fat,
            COUNT(*) as logged_meals
        FROM nutrition_log
        WHERE log_date > date('now', ?)
    """,
        [f"-{days} days"],
    ).fetchone()

    return jsonify(
        {
            "period_days": days,
            "summary": {
                "total_sessions": cooking_stats["total_sessions"] or 0,
                "cooking_days": cooking_stats["unique_days"] or 0,
                "unique_recipes": cooking_stats["unique_recipes"] or 0,
                "unique_cuisines": cooking_stats["unique_cuisines"] or 0,
                "total_xp": cooking_stats["total_xp"] or 0,
                "avg_xp_per_session": round(cooking_stats["avg_xp"] or 0, 1),
            },
            "patterns": {
                "by_day": day_stats,
                "by_time": {t["time_slot"]: t["count"] for t in time_patterns},
                "favorite_day": max(day_stats, key=day_stats.get) if day_stats else None,
            },
            "top_cuisines": [{"cuisine": c["cuisine"], "count": c["count"]} for c in top_cuisines],
            "top_recipes": [
                {
                    "name": r["recipe_name"],
                    "times": r["times_cooked"],
                    "avg_xp": round(r["avg_xp"] or 0, 1),
                }
                for r in top_recipes
            ],
            "weekly_trend": [
                {"week": w["week"], "sessions": w["sessions"], "xp": w["xp"]} for w in weekly_trend
            ],
            "nutrition": {
                "logged_meals": nutrition_summary["logged_meals"] or 0,
                "avg_calories": round(nutrition_summary["avg_calories"] or 0),
                "avg_protein": round(nutrition_summary["avg_protein"] or 0, 1),
                "avg_carbs": round(nutrition_summary["avg_carbs"] or 0, 1),
                "avg_fat": round(nutrition_summary["avg_fat"] or 0, 1),
            },
        }
    )


@app.route("/api/personal/nutrition", methods=["GET", "POST"])
def personal_nutrition():
    """Log or retrieve personal nutrition data."""
    db = get_db()
    ensure_personal_tracking_tables()

    if request.method == "GET":
        # Get nutrition log for date range
        start_date = request.args.get(
            "start", (datetime.now() - timedelta(days=7)).date().isoformat()
        )
        end_date = request.args.get("end", datetime.now().date().isoformat())

        logs = db.execute(
            """
            SELECT * FROM nutrition_log
            WHERE log_date BETWEEN ? AND ?
            ORDER BY log_date DESC, created_at DESC
        """,
            [start_date, end_date],
        ).fetchall()

        # Calculate daily totals
        daily_totals = db.execute(
            """
            SELECT
                log_date,
                SUM(calories * servings) as total_calories,
                SUM(protein_g * servings) as total_protein,
                SUM(carbs_g * servings) as total_carbs,
                SUM(fat_g * servings) as total_fat,
                COUNT(*) as meal_count
            FROM nutrition_log
            WHERE log_date BETWEEN ? AND ?
            GROUP BY log_date
            ORDER BY log_date DESC
        """,
            [start_date, end_date],
        ).fetchall()

        return jsonify(
            {"logs": [dict(l) for l in logs], "daily_totals": [dict(d) for d in daily_totals]}
        )

    else:  # POST - log nutrition
        data = request.get_json()

        db.execute(
            """
            INSERT INTO nutrition_log
            (log_date, meal_type, recipe_id, recipe_name, calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg, servings, notes, mood_before, mood_after, energy_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                data.get("date", datetime.now().date().isoformat()),
                data.get("meal_type", "meal"),
                data.get("recipe_id"),
                data.get("recipe_name"),
                data.get("calories"),
                data.get("protein"),
                data.get("carbs"),
                data.get("fat"),
                data.get("fiber"),
                data.get("sodium"),
                data.get("servings", 1),
                data.get("notes"),
                data.get("mood_before"),
                data.get("mood_after"),
                data.get("energy_level"),
            ],
        )
        db.commit()

        return jsonify({"success": True, "message": "Nutrition logged"})


@app.route("/api/personal/insights")
def get_personal_insights():
    """Generate smart insights about cooking patterns."""
    db = get_db()
    ensure_personal_tracking_tables()

    insights = []

    # Streak insight
    streak = db.execute(
        """
        SELECT current_streak, longest_streak, streak_multiplier
        FROM cooking_streaks WHERE streak_type = 'daily_cook'
        ORDER BY current_streak DESC LIMIT 1
    """
    ).fetchone()

    if streak and streak["current_streak"] > 0:
        if streak["current_streak"] >= streak["longest_streak"] and streak["current_streak"] > 3:
            insights.append(
                {
                    "type": "milestone",
                    "title": "Personal Best Streak!",
                    "text": f"You're on your longest cooking streak ever: {streak['current_streak']} days! Keep it up!",
                    "icon": "🔥",
                }
            )
        elif streak["current_streak"] >= 7:
            insights.append(
                {
                    "type": "achievement",
                    "title": "Week-Long Chef",
                    "text": f"{streak['current_streak']} day streak! Your {round(streak['streak_multiplier'], 2)}x XP multiplier is maxing out.",
                    "icon": "⭐",
                }
            )

    # Variety insight
    variety = db.execute(
        """
        SELECT COUNT(DISTINCT cuisine) as cuisines, COUNT(DISTINCT recipe_id) as recipes
        FROM cooking_sessions
        WHERE completed_at > datetime('now', '-30 days')
    """
    ).fetchone()

    if variety["cuisines"] < 3:
        insights.append(
            {
                "type": "recommendation",
                "title": "Try Something New",
                "text": f"You've cooked {variety['cuisines']} cuisine(s) this month. Try a new cuisine for bonus XP!",
                "icon": "🌍",
            }
        )
    elif variety["cuisines"] >= 5:
        insights.append(
            {
                "type": "achievement",
                "title": "Culinary Explorer",
                "text": f"{variety['cuisines']} different cuisines this month! You're building a diverse palate.",
                "icon": "🗺️",
            }
        )

    # Cooking time pattern
    best_time = db.execute(
        """
        SELECT
            CASE
                WHEN CAST(strftime('%H', completed_at) AS INTEGER) < 10 THEN 'morning'
                WHEN CAST(strftime('%H', completed_at) AS INTEGER) < 14 THEN 'lunch'
                WHEN CAST(strftime('%H', completed_at) AS INTEGER) < 18 THEN 'afternoon'
                ELSE 'evening'
            END as time_slot,
            COUNT(*) as count
        FROM cooking_sessions
        WHERE completed_at > datetime('now', '-30 days')
        GROUP BY time_slot
        ORDER BY count DESC
        LIMIT 1
    """
    ).fetchone()

    if best_time:
        insights.append(
            {
                "type": "pattern",
                "title": "Your Cooking Prime Time",
                "text": f"You cook most often in the {best_time['time_slot']} ({best_time['count']} sessions this month).",
                "icon": "⏰",
            }
        )

    # XP progress insight
    level_info = db.execute(
        """
        SELECT current_level, total_xp, title FROM member_levels ORDER BY total_xp DESC LIMIT 1
    """
    ).fetchone()

    if level_info:
        xp_thresholds = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500, 10000]
        current_level = level_info["current_level"]
        if current_level < 10:
            xp_to_next = xp_thresholds[current_level] - level_info["total_xp"]
            insights.append(
                {
                    "type": "progress",
                    "title": f"Level {current_level}: {level_info['title']}",
                    "text": f"{xp_to_next} XP to reach Level {current_level + 1}!",
                    "icon": "📊",
                }
            )

    # Recipe mastery
    most_cooked = db.execute(
        """
        SELECT recipe_name, COUNT(*) as times
        FROM cooking_sessions
        WHERE recipe_name IS NOT NULL
        GROUP BY recipe_id
        ORDER BY times DESC
        LIMIT 1
    """
    ).fetchone()

    if most_cooked and most_cooked["times"] >= 3:
        insights.append(
            {
                "type": "mastery",
                "title": "Signature Dish",
                "text": f"You've made {most_cooked['recipe_name']} {most_cooked['times']} times. It's becoming your specialty!",
                "icon": "👨‍🍳",
            }
        )

    return jsonify({"insights": insights, "generated_at": datetime.now().isoformat()})


@app.route("/api/personal/targets", methods=["GET", "POST", "PUT"])
def personal_targets():
    """Manage personal cooking/nutrition targets."""
    db = get_db()
    ensure_personal_tracking_tables()

    if request.method == "GET":
        targets = db.execute(
            """
            SELECT * FROM personal_targets WHERE is_active = 1
        """
        ).fetchall()

        # Calculate current values
        result = []
        for t in targets:
            target = dict(t)

            # Calculate progress based on target type
            if target["target_type"] == "daily_calories":
                current = db.execute(
                    """
                    SELECT COALESCE(SUM(calories * servings), 0) as val
                    FROM nutrition_log WHERE log_date = date('now')
                """
                ).fetchone()["val"]
            elif target["target_type"] == "weekly_cooking":
                current = db.execute(
                    """
                    SELECT COUNT(*) as val FROM cooking_sessions
                    WHERE completed_at > datetime('now', '-7 days')
                """
                ).fetchone()["val"]
            elif target["target_type"] == "monthly_new_recipes":
                current = db.execute(
                    """
                    SELECT COUNT(DISTINCT recipe_id) as val FROM cooking_sessions
                    WHERE completed_at > datetime('now', '-30 days')
                """
                ).fetchone()["val"]
            elif target["target_type"] == "weekly_variety":
                current = db.execute(
                    """
                    SELECT COUNT(DISTINCT cuisine) as val FROM cooking_sessions
                    WHERE completed_at > datetime('now', '-7 days')
                """
                ).fetchone()["val"]
            else:
                current = 0

            target["current_value"] = current
            target["progress_pct"] = (
                min(100, round((current / target["target_value"]) * 100))
                if target["target_value"]
                else 0
            )
            result.append(target)

        return jsonify(result)

    elif request.method == "POST":
        data = request.get_json()

        db.execute(
            """
            INSERT INTO personal_targets (target_type, target_value, start_date, end_date)
            VALUES (?, ?, date('now'), ?)
        """,
            [data.get("type"), data.get("target"), data.get("end_date")],
        )
        db.commit()

        return jsonify({"success": True})

    else:  # PUT - update target
        data = request.get_json()
        target_id = data.get("id")

        db.execute(
            """
            UPDATE personal_targets SET target_value = ?, is_active = ?
            WHERE id = ?
        """,
            [data.get("target"), data.get("is_active", 1), target_id],
        )
        db.commit()

        return jsonify({"success": True})


@app.route("/api/personal/meal-rating", methods=["POST"])
def rate_meal():
    """Rate a meal you cooked."""
    db = get_db()
    ensure_personal_tracking_tables()

    data = request.get_json()

    db.execute(
        """
        INSERT INTO meal_ratings (recipe_id, recipe_name, rating, would_make_again, notes, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        [
            data.get("recipe_id"),
            data.get("recipe_name"),
            data.get("rating", 3),
            data.get("would_make_again", 1),
            data.get("notes"),
            json.dumps(data.get("tags", [])),
        ],
    )
    db.commit()

    return jsonify({"success": True})


@app.route("/api/personal/favorites")
def get_favorites():
    """Get favorite and highly rated recipes."""
    db = get_db()
    ensure_personal_tracking_tables()

    # Top rated
    top_rated = db.execute(
        """
        SELECT recipe_id, recipe_name, AVG(rating) as avg_rating, COUNT(*) as times_rated
        FROM meal_ratings
        GROUP BY recipe_id
        HAVING times_rated >= 1
        ORDER BY avg_rating DESC, times_rated DESC
        LIMIT 10
    """
    ).fetchall()

    # Would make again
    make_again = db.execute(
        """
        SELECT DISTINCT recipe_id, recipe_name, rating
        FROM meal_ratings
        WHERE would_make_again = 1
        ORDER BY rating DESC
        LIMIT 10
    """
    ).fetchall()

    # Most cooked (frequency = preference)
    most_cooked = db.execute(
        """
        SELECT recipe_id, recipe_name, COUNT(*) as times
        FROM cooking_sessions
        WHERE recipe_name IS NOT NULL
        GROUP BY recipe_id
        ORDER BY times DESC
        LIMIT 10
    """
    ).fetchall()

    return jsonify(
        {
            "top_rated": [dict(r) for r in top_rated],
            "would_make_again": [dict(r) for r in make_again],
            "most_cooked": [dict(r) for r in most_cooked],
        }
    )


@app.route("/api/personal/smart-suggestions")
def get_smart_suggestions():
    """Get personalized recipe suggestions based on your data."""
    db = get_db()

    suggestions = []

    # Get your top cuisines
    top_cuisines = db.execute(
        """
        SELECT cuisine FROM cooking_sessions
        WHERE cuisine IS NOT NULL
        GROUP BY cuisine ORDER BY COUNT(*) DESC LIMIT 3
    """
    ).fetchall()
    cuisine_list = [c["cuisine"] for c in top_cuisines]

    # Suggest recipes from your favorite cuisines you haven't made
    if cuisine_list:
        # Get recipe IDs you've already made
        made_recipes = db.execute(
            """
            SELECT DISTINCT recipe_id FROM cooking_sessions
        """
        ).fetchall()
        made_ids = [r["recipe_id"] for r in made_recipes]

        # Find new recipes in your favorite cuisines
        placeholders = ",".join(["?" for _ in cuisine_list])
        new_in_fav_cuisine = db.execute(
            f"""
            SELECT id, title, category
            FROM recipes_large
            WHERE category IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT 5
        """,
            cuisine_list,
        ).fetchall()

        for r in new_in_fav_cuisine:
            if f"local_{r['id']}" not in made_ids:
                suggestions.append(
                    {
                        "type": "favorite_cuisine",
                        "reason": f"Because you love {r['category']}",
                        "recipe_id": r["id"],
                        "recipe_name": r["title"],
                    }
                )

    # Suggest based on day of week patterns
    today_dow = datetime.now().strftime("%w")
    typical_cuisine = db.execute(
        """
        SELECT cuisine, COUNT(*) as cnt FROM cooking_sessions
        WHERE strftime('%w', completed_at) = ? AND cuisine IS NOT NULL
        GROUP BY cuisine ORDER BY cnt DESC LIMIT 1
    """,
        [today_dow],
    ).fetchone()

    if typical_cuisine:
        suggestions.append(
            {
                "type": "day_pattern",
                "reason": f"You typically cook {typical_cuisine['cuisine']} on {datetime.now().strftime('%As')}",
                "cuisine": typical_cuisine["cuisine"],
            }
        )

    # Quick meal suggestions for busy days
    suggestions.append(
        {"type": "quick_meal", "reason": "Need something fast?", "filter": {"max_time": 30}}
    )

    return jsonify({"suggestions": suggestions[:5], "generated_for": datetime.now().isoformat()})


@app.route("/api/personal/dashboard")
def get_personal_dashboard():
    """Get unified personal dashboard data - individual focused."""
    db = get_db()
    ensure_personal_tracking_tables()

    # Today's stats
    today = datetime.now().date().isoformat()
    today_meals = db.execute(
        """
        SELECT COUNT(*) as count FROM nutrition_log WHERE log_date = ?
    """,
        [today],
    ).fetchone()["count"]

    today_calories = db.execute(
        """
        SELECT COALESCE(SUM(calories * servings), 0) as total
        FROM nutrition_log WHERE log_date = ?
    """,
        [today],
    ).fetchone()["total"]

    # Current streak
    streak = db.execute(
        """
        SELECT current_streak, longest_streak, streak_multiplier
        FROM cooking_streaks WHERE streak_type = 'daily_cook'
        ORDER BY current_streak DESC LIMIT 1
    """
    ).fetchone()

    # Level info
    level = db.execute(
        """
        SELECT current_level, total_xp, title, xp_to_next_level
        FROM member_levels ORDER BY total_xp DESC LIMIT 1
    """
    ).fetchone()

    # This week's cooking
    week_cooking = db.execute(
        """
        SELECT COUNT(*) as sessions, COALESCE(SUM(total_xp), 0) as xp
        FROM cooking_sessions
        WHERE completed_at > datetime('now', '-7 days')
    """
    ).fetchone()

    # Recent achievements
    recent_achievements = db.execute(
        """
        SELECT a.name, a.description, a.icon, ua.unlocked_at
        FROM user_achievements ua
        JOIN achievements a ON ua.achievement_id = a.id
        ORDER BY ua.unlocked_at DESC
        LIMIT 3
    """
    ).fetchall()

    # Active targets
    targets = db.execute(
        """
        SELECT target_type, target_value FROM personal_targets WHERE is_active = 1
    """
    ).fetchall()

    return jsonify(
        {
            "today": {"meals_logged": today_meals, "calories": today_calories, "date": today},
            "streak": {
                "current": streak["current_streak"] if streak else 0,
                "longest": streak["longest_streak"] if streak else 0,
                "multiplier": round(streak["streak_multiplier"], 2) if streak else 1.0,
            },
            "level": {
                "current": level["current_level"] if level else 1,
                "title": level["title"] if level else "Kitchen Novice",
                "total_xp": level["total_xp"] if level else 0,
                "xp_to_next": level["xp_to_next_level"] if level else 100,
            },
            "this_week": {
                "cooking_sessions": week_cooking["sessions"],
                "xp_earned": week_cooking["xp"],
            },
            "recent_achievements": [dict(a) for a in recent_achievements],
            "active_targets": [dict(t) for t in targets],
        }
    )


# Personal dashboard page route
@app.route("/me")
def personal_dashboard_page():
    """Personal dashboard page - individual focused."""
    return render_template("personal_dashboard.html")


# ============================================================================
# POTION ALCHEMY SYSTEM
# ============================================================================

# Alchemy Effect Data - Scientific health effects with magical naming
POTION_EFFECTS_DATA = [
    (
        "Fortify Digestion",
        "FORTIFY_DIGESTION",
        "digestion",
        "🌿",
        "#4CAF50",
        "Improves gut health and digestive regularity",
        "Fiber promotes healthy bowel movements and feeds beneficial gut bacteria",
        "Harmony",
    ),
    (
        "Fortify Mind",
        "FORTIFY_MIND",
        "brain",
        "🧠",
        "#9C27B0",
        "Supports cognitive function and mental clarity",
        "Omega-3s and curcumin reduce neuroinflammation and support neural health",
        "Clarity",
    ),
    (
        "Fortify Skin",
        "FORTIFY_SKIN",
        "skin",
        "✨",
        "#E91E63",
        "Promotes skin elasticity and radiant appearance",
        "Vitamin C enables collagen synthesis; biotin supports skin cell renewal",
        "Radiance",
    ),
    (
        "Restore Energy",
        "RESTORE_ENERGY",
        "energy",
        "⚡",
        "#FF9800",
        "Boosts natural energy levels and reduces fatigue",
        "B-vitamins are essential cofactors in cellular energy production",
        "Vitality",
    ),
    (
        "Calm Spirit",
        "CALM_SPIRIT",
        "sleep",
        "🌙",
        "#3F51B5",
        "Promotes relaxation and restful sleep",
        "Chamomile and lavender contain compounds that modulate GABA receptors",
        "Serenity",
    ),
    (
        "Fortify Immunity",
        "FORTIFY_IMMUNITY",
        "immunity",
        "🛡️",
        "#00BCD4",
        "Strengthens immune system defenses",
        "Vitamin C and zinc are critical for immune cell function",
        "Shield",
    ),
    (
        "Cleanse Body",
        "CLEANSE_BODY",
        "detox",
        "💧",
        "#009688",
        "Supports natural detoxification processes",
        "Fiber binds toxins; citrus supports liver enzyme activity",
        "Purity",
    ),
    (
        "Warm Core",
        "WARM_CORE",
        "circulation",
        "🔥",
        "#F44336",
        "Improves circulation and creates warming sensation",
        "Gingerols and capsaicin activate TRPV1 thermoreceptors",
        "Ember",
    ),
    (
        "Cool Essence",
        "COOL_ESSENCE",
        "inflammation",
        "❄️",
        "#2196F3",
        "Reduces inflammation and creates cooling sensation",
        "Menthol activates TRPM8 cold receptors; anti-inflammatory compounds",
        "Frost",
    ),
    (
        "Balance Flow",
        "BALANCE_FLOW",
        "hormones",
        "☯️",
        "#607D8B",
        "Supports hormonal balance and adaptogenic effects",
        "Adaptogens like ashwagandha modulate cortisol and stress response",
        "Equilibrium",
    ),
    (
        "Strengthen Bones",
        "STRENGTHEN_BONES",
        "skeletal",
        "🦴",
        "#795548",
        "Supports bone density and skeletal health",
        "Calcium, vitamin D, and magnesium are essential for bone matrix",
        "Foundation",
    ),
    (
        "Brighten Mood",
        "BRIGHTEN_MOOD",
        "mood",
        "☀️",
        "#FFEB3B",
        "Elevates mood and supports emotional wellbeing",
        "Cacao contains theobromine and phenylethylamine; saffron modulates serotonin",
        "Sunshine",
    ),
]

# Brewing Methods Data
BREWING_METHODS_DATA = [
    (
        "Hot Infusion",
        "HOT_INFUSION",
        "hot",
        "☕",
        "Steep ingredients in hot water to extract compounds",
        "Bring water to 80-100°C. Add ingredients and steep 3-10 minutes. Strain and serve.",
        0.7,
        0.0,
        0.8,
    ),  # vitamin_c_retention, fiber_preservation, volatile_retention
    (
        "Cold Brew",
        "COLD_BREW",
        "cold",
        "💧",
        "Infuse ingredients in cold water over time",
        "Add ingredients to cold water. Refrigerate 4-12 hours. Strain and serve.",
        1.0,
        0.0,
        0.9,
    ),
    (
        "Smoothie Blend",
        "SMOOTHIE_BLEND",
        "blend",
        "🥤",
        "Blend whole ingredients to retain all nutrients",
        "Add all ingredients to blender. Blend until smooth. Serve immediately.",
        0.9,
        1.0,
        0.6,
    ),
]

# Synergy Data - Real scientific synergies!
SYNERGIES_DATA = [
    (
        "Golden Absorption",
        "turmeric",
        "black pepper",
        None,
        20.0,
        "FORTIFY_MIND",
        "Piperine inhibits glucuronidation of curcumin, increasing bioavailability by 2000%",
        "You discovered the Golden Synergy! Piperine unlocks turmeric's full potential!",
    ),
    (
        "Fiber Harmony",
        "psyllium husk",
        "oat bran",
        None,
        2.0,
        "FORTIFY_DIGESTION",
        "Soluble and insoluble fiber work together for optimal digestive regularity",
        "Fiber Harmony discovered! These fibers complement each other perfectly!",
    ),
    (
        "Iron Catalyst",
        "spinach",
        "lemon",
        None,
        3.0,
        "FORTIFY_IMMUNITY",
        "Vitamin C converts non-heme iron to more absorbable form",
        "Iron Catalyst unlocked! Citrus supercharges iron absorption!",
    ),
    (
        "Fat-Soluble Unlock",
        "carrot",
        "coconut",
        None,
        2.5,
        "FORTIFY_SKIN",
        "Fat is required for absorption of vitamin A and other fat-soluble nutrients",
        "Fat-Soluble Unlock! The healthy fats enable vitamin absorption!",
    ),
    (
        "Warming Cascade",
        "ginger",
        "cinnamon",
        "black pepper",
        2.0,
        "WARM_CORE",
        "Multiple TRPV1 activators create compound warming effect",
        "Warming Cascade ignited! A triple-fire combination!",
    ),
    (
        "Cooling Wave",
        "mint",
        "cucumber",
        "lemon",
        1.8,
        "COOL_ESSENCE",
        "TRPM8 activation combined with cooling TCM properties",
        "Cooling Wave activated! Maximum refreshment achieved!",
    ),
    (
        "Protein Power",
        "whey protein",
        "creatine",
        None,
        1.5,
        "RESTORE_ENERGY",
        "Creatine enhances ATP regeneration supporting muscle protein synthesis",
        "Protein Power engaged! Optimal muscle fuel combination!",
    ),
    (
        "Collagen Boost",
        "collagen",
        "vitamin c",
        None,
        2.0,
        "FORTIFY_SKIN",
        "Vitamin C is a required cofactor for collagen synthesis",
        "Collagen Boost activated! Your skin will thank you!",
    ),
    (
        "Calm Cascade",
        "chamomile",
        "lavender",
        "honey",
        1.8,
        "CALM_SPIRIT",
        "Multiple GABAergic compounds create synergistic calming effect",
        "Calm Cascade flowing! Deep relaxation incoming!",
    ),
    (
        "Brain Boost",
        "blueberry",
        "omega-3",
        "turmeric",
        2.5,
        "FORTIFY_MIND",
        "Anthocyanins, omega-3s, and curcumin provide neuroprotective synergy",
        "Brain Boost unlocked! Maximum cognitive support!",
    ),
]

# Effect Triggers - What nutrients/properties trigger which effects
EFFECT_TRIGGERS_DATA = [
    # Digestion
    ("FORTIFY_DIGESTION", "nutrient", "fiber_g", None, 3.0, 1.0),
    ("FORTIFY_DIGESTION", "ingredient", "psyllium", None, None, 2.0),
    ("FORTIFY_DIGESTION", "ingredient", "oat bran", None, None, 1.5),
    # Mind
    ("FORTIFY_MIND", "ingredient", "turmeric", None, None, 2.0),
    ("FORTIFY_MIND", "ingredient", "blueberry", None, None, 1.5),
    ("FORTIFY_MIND", "ingredient", "omega-3", None, None, 2.0),
    # Skin
    ("FORTIFY_SKIN", "nutrient", "vitamin_c_mg", None, 15.0, 1.0),
    ("FORTIFY_SKIN", "ingredient", "collagen", None, None, 2.5),
    # Energy
    ("RESTORE_ENERGY", "nutrient", "vitamin_b1_mg", None, 0.1, 0.8),
    ("RESTORE_ENERGY", "nutrient", "vitamin_b2_mg", None, 0.1, 0.8),
    ("RESTORE_ENERGY", "nutrient", "iron_mg", None, 1.0, 1.0),
    ("RESTORE_ENERGY", "ingredient", "caffeine", None, None, 1.5),
    # Sleep
    ("CALM_SPIRIT", "ingredient", "chamomile", None, None, 2.0),
    ("CALM_SPIRIT", "ingredient", "lavender", None, None, 1.8),
    ("CALM_SPIRIT", "nutrient", "magnesium_mg", None, 30.0, 1.0),
    # Immunity
    ("FORTIFY_IMMUNITY", "nutrient", "vitamin_c_mg", None, 20.0, 1.5),
    ("FORTIFY_IMMUNITY", "nutrient", "zinc_mg", None, 2.0, 1.2),
    ("FORTIFY_IMMUNITY", "ingredient", "ginger", None, None, 1.5),
    # Detox
    ("CLEANSE_BODY", "ingredient", "dandelion", None, None, 2.0),
    ("CLEANSE_BODY", "ingredient", "lemon", None, None, 1.5),
    ("CLEANSE_BODY", "nutrient", "fiber_g", None, 2.0, 0.8),
    # Warm
    ("WARM_CORE", "ingredient", "ginger", None, None, 2.0),
    ("WARM_CORE", "ingredient", "cinnamon", None, None, 1.8),
    ("WARM_CORE", "ingredient", "cayenne", None, None, 2.0),
    ("WARM_CORE", "ingredient", "black pepper", None, None, 1.2),
    # Cool
    ("COOL_ESSENCE", "ingredient", "mint", None, None, 2.0),
    ("COOL_ESSENCE", "ingredient", "cucumber", None, None, 1.5),
    ("COOL_ESSENCE", "ingredient", "aloe", None, None, 1.8),
    # Hormones
    ("BALANCE_FLOW", "ingredient", "maca", None, None, 2.0),
    ("BALANCE_FLOW", "ingredient", "ashwagandha", None, None, 2.2),
    # Bones
    ("STRENGTHEN_BONES", "nutrient", "calcium_mg", None, 100.0, 1.0),
    ("STRENGTHEN_BONES", "nutrient", "vitamin_d_mcg", None, 5.0, 1.2),
    ("STRENGTHEN_BONES", "nutrient", "magnesium_mg", None, 50.0, 0.8),
    # Mood
    ("BRIGHTEN_MOOD", "ingredient", "cacao", None, None, 2.0),
    ("BRIGHTEN_MOOD", "ingredient", "saffron", None, None, 2.5),
    ("BRIGHTEN_MOOD", "ingredient", "banana", None, None, 1.0),
]

# XP and Level System
BREWER_LEVELS = [
    (1, 0, "Apprentice Alchemist"),
    (2, 100, "Novice Brewer"),
    (3, 300, "Journeyman Herbalist"),
    (4, 600, "Adept Alchemist"),
    (5, 1000, "Master Brewer"),
    (6, 1500, "Grand Alchemist"),
    (7, 2500, "Legendary Elixirist"),
]

# ============================================================================
# ALCHEMY INGREDIENTS DATA - 60+ Ingredients with Full Health Data
# Includes Yuka-style health scores (0-100), nutrition, effects, warnings
# ============================================================================

# Format: (name, display_name, category, subcategory, icon, color_hex,
#          default_amount_g, max_daily_g, typical_serving_g,
#          calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g,
#          vitamin_c_mg, vitamin_a_mcg, magnesium_mg, iron_mg, calcium_mg, potassium_mg, zinc_mg,
#          tcm_temperature, primary_effects, secondary_effects, bioactive_compounds,
#          flavor_notes, pairs_well_with, avoid_with,
#          best_brewing_method, caffeine_mg, is_adaptogen, pregnancy_safe, breastfeeding_safe,
#          health_score, description, scientific_name)

ALCHEMY_INGREDIENTS_DATA = [
    # ===== HERBS & BOTANICALS =====
    (
        "ginger",
        "Ginger Root",
        "herbs",
        "warming",
        "🫚",
        "#F4A460",
        5,
        4,
        10,  # amounts
        80,
        1.8,
        18,
        0.8,
        2.0,
        1.7,  # macros
        5,
        0,
        43,
        0.6,
        16,
        415,
        0.34,  # vitamins/minerals
        "hot",
        "WARM_CORE,FORTIFY_IMMUNITY",
        "FORTIFY_DIGESTION",
        "gingerols,shogaols,zingerone",
        "spicy,warm,citrusy",
        "turmeric,lemon,honey,cinnamon",
        "blood thinners",
        "HOT_INFUSION",
        0,
        0,
        1,
        1,
        92,
        "Powerful warming root with anti-nausea and anti-inflammatory properties",
        "Zingiber officinale",
    ),
    (
        "turmeric",
        "Turmeric Root",
        "herbs",
        "warming",
        "🟡",
        "#FFD700",
        3,
        3,
        5,
        312,
        9.7,
        67,
        3.3,
        22.7,
        3.2,
        0,
        0,
        208,
        55,
        168,
        2080,
        4.5,
        "warm",
        "FORTIFY_MIND,COOL_ESSENCE",
        "FORTIFY_SKIN",
        "curcumin,turmerone,demethoxycurcumin",
        "earthy,bitter,peppery",
        "black pepper,ginger,coconut",
        "gallbladder issues",
        "HOT_INFUSION",
        0,
        0,
        0,
        0,
        95,
        "Golden anti-inflammatory powerhouse - requires black pepper for absorption",
        "Curcuma longa",
    ),
    (
        "cinnamon",
        "Ceylon Cinnamon",
        "herbs",
        "warming",
        "🟤",
        "#D2691E",
        2,
        4,
        3,
        247,
        4,
        81,
        1.2,
        53,
        2.2,
        3.8,
        15,
        60,
        8.3,
        1002,
        431,
        1.8,
        "hot",
        "WARM_CORE,BALANCE_FLOW",
        "FORTIFY_DIGESTION",
        "cinnamaldehyde,eugenol,coumarin",
        "sweet,warm,spicy",
        "ginger,honey,apple,turmeric",
        "liver conditions if cassia",
        "HOT_INFUSION",
        0,
        0,
        1,
        1,
        88,
        "Blood sugar balancing warming spice - Ceylon variety is safer than Cassia",
        "Cinnamomum verum",
    ),
    (
        "black pepper",
        "Black Pepper",
        "herbs",
        "warming",
        "⚫",
        "#1C1C1C",
        1,
        2,
        1,
        255,
        10.4,
        64,
        3.3,
        25,
        0.6,
        21,
        27,
        171,
        9.7,
        443,
        1329,
        1.2,
        "hot",
        "WARM_CORE",
        "FORTIFY_DIGESTION",
        "piperine,chavicine,piperidine",
        "sharp,spicy,pungent",
        "turmeric,ginger,all foods",
        None,
        "HOT_INFUSION",
        0,
        0,
        1,
        1,
        85,
        "Bioavailability enhancer - boosts absorption of turmeric by 2000%",
        "Piper nigrum",
    ),
    (
        "cayenne",
        "Cayenne Pepper",
        "herbs",
        "warming",
        "🌶️",
        "#FF4500",
        0.5,
        2,
        1,
        318,
        12,
        57,
        17,
        27,
        10,
        76,
        2081,
        152,
        7.8,
        148,
        2014,
        2.5,
        "hot",
        "WARM_CORE,RESTORE_ENERGY",
        "FORTIFY_IMMUNITY",
        "capsaicin,capsanthin,carotenoids",
        "fiery,hot,sharp",
        "lemon,ginger,honey",
        "digestive ulcers",
        "HOT_INFUSION",
        0,
        0,
        0,
        0,
        78,
        "Metabolism-boosting heat - activates TRPV1 thermoreceptors",
        "Capsicum annuum",
    ),
    (
        "mint",
        "Peppermint Leaf",
        "herbs",
        "cooling",
        "🌿",
        "#98FB98",
        3,
        10,
        5,
        70,
        3.8,
        15,
        0.9,
        8,
        0,
        31,
        212,
        80,
        5.1,
        243,
        569,
        1.1,
        "cool",
        "COOL_ESSENCE,FORTIFY_DIGESTION",
        "CALM_SPIRIT",
        "menthol,menthone,limonene",
        "cool,fresh,crisp",
        "lemon,cucumber,chamomile",
        None,
        "COLD_BREW",
        0,
        0,
        1,
        0,
        90,
        "Cooling digestive aid - activates TRPM8 cold receptors",
        "Mentha piperita",
    ),
    (
        "chamomile",
        "Chamomile Flowers",
        "herbs",
        "calming",
        "🌼",
        "#FFFACD",
        3,
        10,
        5,
        1,
        0,
        0.2,
        0,
        0.1,
        0,
        0,
        0,
        2,
        0.1,
        2,
        9,
        0,
        "neutral",
        "CALM_SPIRIT",
        "FORTIFY_DIGESTION,FORTIFY_SKIN",
        "apigenin,bisabolol,chamazulene",
        "floral,honey,apple-like",
        "lavender,honey,lemon",
        "ragweed allergy",
        "HOT_INFUSION",
        0,
        0,
        1,
        1,
        94,
        "Gentle calming flower - apigenin binds to GABA receptors",
        "Matricaria chamomilla",
    ),
    (
        "lavender",
        "Lavender Flowers",
        "herbs",
        "calming",
        "💜",
        "#E6E6FA",
        2,
        5,
        3,
        49,
        4,
        6.6,
        0.7,
        3.8,
        0,
        0,
        0,
        26,
        2.5,
        95,
        219,
        0.4,
        "cool",
        "CALM_SPIRIT",
        "BRIGHTEN_MOOD",
        "linalool,linalyl acetate,camphor",
        "floral,sweet,herbal",
        "chamomile,honey,lemon",
        None,
        "HOT_INFUSION",
        0,
        0,
        1,
        1,
        91,
        "Aromatic calming herb - linalool has anxiolytic effects",
        "Lavandula angustifolia",
    ),
    (
        "dandelion",
        "Dandelion Root",
        "herbs",
        "detox",
        "🌻",
        "#FFE135",
        5,
        15,
        10,
        45,
        2.7,
        9.2,
        0.7,
        3.5,
        0,
        35,
        508,
        36,
        3.1,
        187,
        397,
        0.4,
        "cool",
        "CLEANSE_BODY,FORTIFY_DIGESTION",
        None,
        "taraxacin,inulin,sesquiterpene lactones",
        "bitter,earthy,roasted",
        "burdock,ginger,lemon",
        "gallbladder disease",
        "HOT_INFUSION",
        0,
        0,
        0,
        0,
        87,
        "Liver-supporting bitter root - rich in prebiotic inulin",
        "Taraxacum officinale",
    ),
    (
        "nettle",
        "Stinging Nettle",
        "herbs",
        "mineral-rich",
        "🌱",
        "#228B22",
        5,
        15,
        10,
        42,
        2.7,
        7.5,
        0.1,
        6.9,
        0.3,
        30,
        101,
        71,
        1.6,
        481,
        334,
        0.3,
        "cool",
        "CLEANSE_BODY,FORTIFY_IMMUNITY",
        "BALANCE_FLOW",
        "chlorophyll,silica,formic acid",
        "grassy,spinach-like,mineral",
        "mint,lemon,raspberry leaf",
        None,
        "HOT_INFUSION",
        0,
        0,
        0,
        0,
        89,
        "Mineral-rich detox herb - high in iron and silica",
        "Urtica dioica",
    ),
    # ===== ADAPTOGENS =====
    (
        "ashwagandha",
        "Ashwagandha Root",
        "adaptogens",
        "stress",
        "🌿",
        "#8B4513",
        3,
        6,
        5,
        245,
        3.9,
        49.9,
        0.3,
        32.3,
        1.2,
        3.7,
        0,
        0,
        3.3,
        23,
        0,
        0,
        "warm",
        "BALANCE_FLOW,CALM_SPIRIT",
        "RESTORE_ENERGY",
        "withanolides,withaferin,sitoindosides",
        "earthy,bitter,horsey",
        "milk,honey,cinnamon",
        "thyroid conditions,pregnancy",
        "HOT_INFUSION",
        0,
        1,
        0,
        0,
        88,
        "Premier adaptogen for stress and cortisol - KSM-66 is best studied extract",
        "Withania somnifera",
    ),
    (
        "maca",
        "Maca Root",
        "adaptogens",
        "energy",
        "🥔",
        "#DEB887",
        5,
        10,
        5,
        325,
        14.3,
        71.4,
        1.6,
        8.5,
        28.6,
        285,
        0,
        70,
        14.8,
        250,
        2000,
        3.8,
        "neutral",
        "BALANCE_FLOW,RESTORE_ENERGY",
        "BRIGHTEN_MOOD",
        "macamides,macaenes,glucosinolates",
        "malty,butterscotch,earthy",
        "cacao,banana,vanilla",
        "hormone-sensitive conditions",
        "SMOOTHIE_BLEND",
        0,
        1,
        0,
        0,
        85,
        "Peruvian energy root - supports hormonal balance and stamina",
        "Lepidium meyenii",
    ),
    (
        "rhodiola",
        "Rhodiola Rosea",
        "adaptogens",
        "energy",
        "🌹",
        "#DB7093",
        2,
        5,
        3,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "cool",
        "RESTORE_ENERGY,FORTIFY_MIND",
        "BALANCE_FLOW",
        "rosavins,salidroside,tyrosol",
        "rose-like,bitter,astringent",
        "ginseng,eleuthero",
        "bipolar disorder",
        "HOT_INFUSION",
        0,
        1,
        0,
        0,
        86,
        "Arctic adaptogen - increases mental performance and reduces fatigue",
        "Rhodiola rosea",
    ),
    (
        "reishi",
        "Reishi Mushroom",
        "adaptogens",
        "immune",
        "🍄",
        "#8B0000",
        3,
        9,
        5,
        345,
        7.7,
        75.4,
        1.8,
        25.9,
        0,
        0,
        0,
        8,
        4.5,
        5,
        254,
        1.9,
        "neutral",
        "FORTIFY_IMMUNITY,CALM_SPIRIT",
        "BALANCE_FLOW",
        "beta-glucans,triterpenes,ganoderic acids",
        "bitter,woody,earthy",
        "chaga,lions mane,cacao",
        "blood thinners,immunosuppressants",
        "HOT_INFUSION",
        0,
        1,
        0,
        0,
        90,
        "Mushroom of immortality - immune modulator and sleep support",
        "Ganoderma lucidum",
    ),
    (
        "lions mane",
        "Lions Mane Mushroom",
        "adaptogens",
        "brain",
        "🦁",
        "#FFEFD5",
        3,
        6,
        5,
        35,
        2.5,
        7,
        0.3,
        3,
        0,
        0,
        0,
        12,
        0.7,
        2,
        443,
        0.5,
        "neutral",
        "FORTIFY_MIND",
        "FORTIFY_IMMUNITY",
        "hericenones,erinacines,beta-glucans",
        "mild,seafood-like,sweet",
        "reishi,chaga,cacao",
        None,
        "HOT_INFUSION",
        0,
        1,
        0,
        0,
        92,
        "Brain-boosting mushroom - promotes NGF synthesis for neural health",
        "Hericium erinaceus",
    ),
    # ===== FIBER & DIGESTIVE =====
    (
        "psyllium husk",
        "Psyllium Husk",
        "fiber",
        "soluble",
        "🌾",
        "#F5DEB3",
        5,
        15,
        7,
        40,
        2.5,
        83.5,
        0.6,
        80,
        0,
        0,
        0,
        0,
        5,
        8,
        0,
        0,
        "neutral",
        "FORTIFY_DIGESTION,CLEANSE_BODY",
        None,
        "mucilage,arabinoxylan",
        "neutral,gelatinous",
        "oat bran,flaxseed,water",
        "intestinal obstruction",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        94,
        "Premium soluble fiber - forms gel to slow digestion and feed gut bacteria",
        "Plantago ovata",
    ),
    (
        "oat bran",
        "Oat Bran",
        "fiber",
        "soluble",
        "🌾",
        "#C4A35A",
        15,
        50,
        30,
        246,
        17.3,
        66,
        7,
        15.4,
        1.5,
        0,
        0,
        235,
        5.4,
        58,
        566,
        3.1,
        "neutral",
        "FORTIFY_DIGESTION",
        "STRENGTHEN_BONES",
        "beta-glucan,avenanthramides",
        "mild,nutty,oaty",
        "psyllium husk,banana,cinnamon",
        "celiac disease",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        93,
        "Heart-healthy insoluble fiber - beta-glucan lowers cholesterol",
        "Avena sativa",
    ),
    (
        "flaxseed",
        "Ground Flaxseed",
        "fiber",
        "omega",
        "🫘",
        "#8B6914",
        10,
        30,
        15,
        534,
        18.3,
        29,
        42,
        27,
        1.5,
        0.6,
        0,
        392,
        5.7,
        255,
        813,
        4.3,
        "neutral",
        "FORTIFY_DIGESTION,FORTIFY_MIND",
        "BALANCE_FLOW",
        "lignans,ALA omega-3,mucilage",
        "nutty,earthy",
        "chia,banana,berries",
        "blood thinners",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        91,
        "Omega-3 rich seeds - must be ground for nutrient absorption",
        "Linum usitatissimum",
    ),
    (
        "chia seeds",
        "Chia Seeds",
        "fiber",
        "omega",
        "⚫",
        "#2F4F4F",
        10,
        30,
        15,
        486,
        17,
        42,
        31,
        34,
        0,
        1.6,
        54,
        335,
        7.7,
        631,
        407,
        4.6,
        "neutral",
        "FORTIFY_DIGESTION,FORTIFY_MIND",
        "RESTORE_ENERGY",
        "ALA omega-3,mucilage,quercetin",
        "mild,neutral,gel-forming",
        "berries,banana,coconut",
        None,
        "COLD_BREW",
        0,
        0,
        1,
        1,
        95,
        "Aztec superfood - absorbs 10x weight in water, excellent for hydration",
        "Salvia hispanica",
    ),
    # ===== FRUITS =====
    (
        "lemon",
        "Lemon Juice",
        "fruits",
        "citrus",
        "🍋",
        "#FFF44F",
        30,
        100,
        50,
        29,
        1.1,
        9.3,
        0.3,
        2.8,
        2.5,
        53,
        1,
        8,
        0.6,
        26,
        138,
        0.1,
        "cool",
        "FORTIFY_IMMUNITY,CLEANSE_BODY",
        "FORTIFY_SKIN",
        "vitamin C,limonene,citric acid",
        "sour,bright,citrusy",
        "ginger,honey,mint,turmeric",
        "tooth enamel erosion",
        "COLD_BREW",
        0,
        0,
        1,
        1,
        96,
        "Vitamin C powerhouse - enhances iron absorption and liver detox",
        "Citrus limon",
    ),
    (
        "blueberry",
        "Blueberries",
        "fruits",
        "berries",
        "🫐",
        "#4169E1",
        50,
        150,
        100,
        57,
        0.7,
        14.5,
        0.3,
        2.4,
        10,
        9.7,
        3,
        6,
        0.3,
        6,
        77,
        0.2,
        "cool",
        "FORTIFY_MIND,FORTIFY_SKIN",
        "COOL_ESSENCE",
        "anthocyanins,pterostilbene,resveratrol",
        "sweet,tangy,fruity",
        "omega-3,turmeric,spinach",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        97,
        "Brain berry - anthocyanins cross blood-brain barrier for neuroprotection",
        "Vaccinium corymbosum",
    ),
    (
        "banana",
        "Banana",
        "fruits",
        "tropical",
        "🍌",
        "#FFE135",
        100,
        300,
        120,
        89,
        1.1,
        23,
        0.3,
        2.6,
        12,
        8.7,
        3,
        27,
        0.3,
        5,
        358,
        0.2,
        "neutral",
        "BRIGHTEN_MOOD,RESTORE_ENERGY",
        "FORTIFY_DIGESTION",
        "tryptophan,potassium,resistant starch",
        "sweet,creamy,mild",
        "cacao,peanut butter,berries",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        88,
        "Mood-lifting fruit - tryptophan converts to serotonin",
        "Musa acuminata",
    ),
    (
        "goji berry",
        "Goji Berries",
        "fruits",
        "berries",
        "🔴",
        "#FF6347",
        10,
        30,
        20,
        349,
        14.3,
        77,
        0.4,
        13,
        46,
        48,
        787,
        0,
        6.8,
        190,
        1130,
        0,
        "neutral",
        "FORTIFY_IMMUNITY,FORTIFY_SKIN",
        "BRIGHTEN_MOOD",
        "zeaxanthin,polysaccharides,betaine",
        "sweet,slightly bitter,tangy",
        "cacao,nuts,honey",
        "blood thinners,diabetes meds",
        "COLD_BREW",
        0,
        0,
        0,
        0,
        89,
        "Longevity berry - highest zeaxanthin content for eye health",
        "Lycium barbarum",
    ),
    (
        "acai",
        "Acai Berry",
        "fruits",
        "berries",
        "🟣",
        "#4B0082",
        15,
        30,
        20,
        70,
        1.5,
        6,
        5,
        3,
        0,
        0.5,
        15,
        17,
        0.6,
        35,
        105,
        0.2,
        "cool",
        "FORTIFY_SKIN,FORTIFY_MIND",
        "RESTORE_ENERGY",
        "anthocyanins,omega fatty acids,fiber",
        "berry,chocolate,earthy",
        "banana,honey,granola",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        90,
        "Amazonian antioxidant - ORAC score higher than most berries",
        "Euterpe oleracea",
    ),
    # ===== VEGETABLES =====
    (
        "spinach",
        "Baby Spinach",
        "vegetables",
        "greens",
        "🥬",
        "#2E8B57",
        50,
        200,
        100,
        23,
        2.9,
        3.6,
        0.4,
        2.2,
        0.4,
        28,
        469,
        79,
        2.7,
        99,
        558,
        0.5,
        "cool",
        "FORTIFY_IMMUNITY,STRENGTHEN_BONES",
        "FORTIFY_SKIN",
        "lutein,zeaxanthin,iron,oxalates",
        "mild,earthy,slightly bitter",
        "lemon,garlic,berries",
        "kidney stones",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        94,
        "Iron-rich green - pair with vitamin C to enhance absorption",
        "Spinacia oleracea",
    ),
    (
        "kale",
        "Curly Kale",
        "vegetables",
        "greens",
        "🥬",
        "#006400",
        50,
        150,
        75,
        49,
        4.3,
        9,
        0.9,
        3.6,
        2.3,
        120,
        500,
        47,
        1.5,
        150,
        491,
        0.6,
        "cool",
        "FORTIFY_IMMUNITY,CLEANSE_BODY",
        "STRENGTHEN_BONES",
        "sulforaphane,kaempferol,quercetin",
        "earthy,slightly bitter,green",
        "lemon,garlic,banana",
        "thyroid conditions",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        93,
        "Cruciferous superfood - sulforaphane activates detox pathways",
        "Brassica oleracea",
    ),
    (
        "cucumber",
        "Cucumber",
        "vegetables",
        "hydrating",
        "🥒",
        "#90EE90",
        100,
        500,
        200,
        15,
        0.7,
        3.6,
        0.1,
        0.5,
        1.7,
        2.8,
        5,
        13,
        0.3,
        16,
        147,
        0.2,
        "cold",
        "COOL_ESSENCE",
        "FORTIFY_SKIN",
        "cucurbitacins,lignans,silica",
        "fresh,mild,watery",
        "mint,lemon,dill",
        None,
        "COLD_BREW",
        0,
        0,
        1,
        1,
        92,
        "Hydrating coolant - 95% water with silica for skin and joints",
        "Cucumis sativus",
    ),
    (
        "celery",
        "Celery Stalks",
        "vegetables",
        "hydrating",
        "🥬",
        "#7CFC00",
        100,
        500,
        150,
        14,
        0.7,
        3,
        0.2,
        1.6,
        1.3,
        3.1,
        22,
        11,
        0.2,
        40,
        260,
        0.1,
        "cool",
        "COOL_ESSENCE,CLEANSE_BODY",
        "BALANCE_FLOW",
        "apigenin,luteolin,phthalides",
        "crisp,mild,slightly salty",
        "apple,ginger,lemon",
        None,
        "COLD_BREW",
        0,
        0,
        1,
        1,
        88,
        "Alkalizing vegetable - phthalides support blood pressure regulation",
        "Apium graveolens",
    ),
    (
        "beet",
        "Beetroot",
        "vegetables",
        "root",
        "🟤",
        "#8B0000",
        75,
        200,
        100,
        43,
        1.6,
        10,
        0.2,
        2.8,
        7,
        4.9,
        2,
        23,
        0.8,
        16,
        325,
        0.4,
        "neutral",
        "RESTORE_ENERGY,CLEANSE_BODY",
        "FORTIFY_IMMUNITY",
        "betalains,nitrates,folate",
        "earthy,sweet,mineral",
        "carrot,apple,ginger",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        91,
        "Nitrate-rich root - converts to nitric oxide for blood flow and endurance",
        "Beta vulgaris",
    ),
    (
        "carrot",
        "Carrot",
        "vegetables",
        "root",
        "🥕",
        "#FF8C00",
        75,
        200,
        100,
        41,
        0.9,
        10,
        0.2,
        2.8,
        4.7,
        5.9,
        835,
        12,
        0.3,
        33,
        320,
        0.2,
        "neutral",
        "FORTIFY_SKIN,FORTIFY_IMMUNITY",
        None,
        "beta-carotene,falcarinol,polyacetylenes",
        "sweet,earthy,crunchy",
        "coconut,ginger,orange",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        95,
        "Beta-carotene champion - fat needed for vitamin A conversion",
        "Daucus carota",
    ),
    # ===== PROTEINS & SUPPLEMENTS =====
    (
        "whey protein",
        "Whey Protein Isolate",
        "proteins",
        "dairy",
        "🥛",
        "#FFFAF0",
        25,
        50,
        30,
        370,
        80,
        5,
        2,
        0,
        3,
        0,
        0,
        90,
        0.5,
        120,
        350,
        0.8,
        "neutral",
        "RESTORE_ENERGY,STRENGTHEN_BONES",
        None,
        "BCAAs,lactoferrin,immunoglobulins",
        "mild,creamy,vanilla-like",
        "banana,berries,cacao",
        "lactose intolerance",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        82,
        "Fast-absorbing complete protein - ideal post-workout",
        "Whey protein isolate",
    ),
    (
        "collagen",
        "Collagen Peptides",
        "proteins",
        "connective",
        "✨",
        "#FFF5EE",
        10,
        20,
        15,
        360,
        90,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "neutral",
        "FORTIFY_SKIN,STRENGTHEN_BONES",
        None,
        "glycine,proline,hydroxyproline",
        "neutral,dissolves easily",
        "vitamin c,berries,citrus",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        85,
        "Skin and joint support - requires vitamin C for synthesis",
        "Hydrolyzed collagen",
    ),
    (
        "hemp seeds",
        "Hemp Hearts",
        "proteins",
        "plant",
        "🌿",
        "#556B2F",
        20,
        50,
        30,
        553,
        31.6,
        8.7,
        48.8,
        4,
        1.5,
        0,
        11,
        700,
        7.95,
        70,
        1200,
        9.9,
        "neutral",
        "FORTIFY_MIND,BALANCE_FLOW",
        "FORTIFY_SKIN",
        "GLA,arginine,edestin protein",
        "nutty,mild,slightly earthy",
        "berries,banana,cacao",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        94,
        "Complete plant protein with perfect omega 3:6 ratio",
        "Cannabis sativa",
    ),
    (
        "spirulina",
        "Spirulina Powder",
        "proteins",
        "algae",
        "🌊",
        "#008080",
        5,
        10,
        5,
        290,
        57,
        24,
        8,
        3.6,
        3,
        10,
        29,
        195,
        28.5,
        120,
        1363,
        2,
        "cool",
        "FORTIFY_IMMUNITY,RESTORE_ENERGY",
        "CLEANSE_BODY",
        "phycocyanin,chlorophyll,GLA",
        "oceanic,earthy,strong",
        "banana,mango,pineapple",
        "autoimmune conditions",
        "SMOOTHIE_BLEND",
        0,
        0,
        0,
        0,
        88,
        "Protein-dense algae - 60% protein with iron and B12",
        "Arthrospira platensis",
    ),
    (
        "creatine",
        "Creatine Monohydrate",
        "proteins",
        "supplement",
        "💪",
        "#F0F8FF",
        5,
        5,
        5,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "neutral",
        "RESTORE_ENERGY",
        None,
        "creatine phosphate",
        "neutral,dissolves easily",
        "whey protein,carbs",
        "kidney disease",
        "SMOOTHIE_BLEND",
        0,
        0,
        0,
        0,
        80,
        "ATP regeneration for strength and power - most studied sports supplement",
        "Creatine monohydrate",
    ),
    # ===== SWEETENERS & FLAVOR =====
    (
        "honey",
        "Raw Honey",
        "sweeteners",
        "natural",
        "🍯",
        "#FFD700",
        15,
        50,
        20,
        304,
        0.3,
        82,
        0,
        0.2,
        82,
        0.5,
        0,
        2,
        0.4,
        6,
        52,
        0.2,
        "neutral",
        "CALM_SPIRIT,FORTIFY_IMMUNITY",
        "RESTORE_ENERGY",
        "enzymes,phenolic acids,flavonoids",
        "sweet,floral,complex",
        "lemon,ginger,cinnamon,chamomile",
        "infants under 1 year",
        "HOT_INFUSION",
        0,
        0,
        1,
        1,
        75,
        "Medicinal sweetener - antibacterial and prebiotic when raw",
        "Apis mellifera honey",
    ),
    (
        "maple syrup",
        "Pure Maple Syrup",
        "sweeteners",
        "natural",
        "🍁",
        "#D2691E",
        15,
        50,
        20,
        260,
        0,
        67,
        0.1,
        0,
        60,
        0,
        0,
        21,
        0.1,
        102,
        212,
        1.5,
        "neutral",
        "RESTORE_ENERGY",
        None,
        "quebecol,manganese,zinc",
        "rich,caramel,maple",
        "banana,oats,cinnamon",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        70,
        "Antioxidant-rich sweetener - contains unique quebecol compound",
        "Acer saccharum sap",
    ),
    (
        "cacao",
        "Raw Cacao Powder",
        "flavoring",
        "chocolate",
        "🍫",
        "#3D2B1F",
        10,
        30,
        15,
        228,
        19.6,
        58,
        13.7,
        33,
        1.8,
        0,
        0,
        499,
        13.9,
        128,
        1524,
        6.8,
        "neutral",
        "BRIGHTEN_MOOD,FORTIFY_MIND",
        "RESTORE_ENERGY",
        "theobromine,phenylethylamine,anandamide",
        "rich,bitter,chocolate",
        "banana,vanilla,mint,maca",
        "caffeine sensitivity",
        "SMOOTHIE_BLEND",
        230,
        0,
        1,
        1,
        86,
        "Bliss molecule source - theobromine is milder than caffeine",
        "Theobroma cacao",
    ),
    (
        "vanilla",
        "Vanilla Extract",
        "flavoring",
        "aromatic",
        "🍦",
        "#F5F5DC",
        5,
        10,
        5,
        288,
        0.1,
        12.7,
        0.1,
        0,
        12.7,
        0,
        0,
        12,
        0.1,
        11,
        148,
        0.1,
        "warm",
        "CALM_SPIRIT,BRIGHTEN_MOOD",
        None,
        "vanillin,p-hydroxybenzaldehyde",
        "sweet,warm,floral",
        "cacao,banana,berries",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        80,
        "Calming aromatherapy - vanillin has anxiolytic properties",
        "Vanilla planifolia",
    ),
    (
        "matcha",
        "Matcha Green Tea",
        "teas",
        "caffeinated",
        "🍵",
        "#90EE90",
        3,
        6,
        3,
        324,
        30.6,
        38.9,
        5.3,
        38.5,
        0,
        60,
        2126,
        230,
        17,
        420,
        2700,
        6.3,
        "cool",
        "FORTIFY_MIND,RESTORE_ENERGY",
        "CALM_SPIRIT",
        "L-theanine,EGCG,catechins,caffeine",
        "grassy,umami,slightly sweet",
        "honey,vanilla,milk",
        "caffeine sensitivity",
        "HOT_INFUSION",
        70,
        0,
        0,
        0,
        89,
        "Calm focus tea - L-theanine balances caffeine for smooth energy",
        "Camellia sinensis",
    ),
    (
        "green tea",
        "Green Tea Leaves",
        "teas",
        "caffeinated",
        "🍵",
        "#228B22",
        3,
        10,
        5,
        0,
        0,
        0.5,
        0,
        0,
        0,
        0,
        0,
        2,
        0.1,
        3,
        8,
        0,
        "cool",
        "FORTIFY_MIND,FORTIFY_IMMUNITY",
        "RESTORE_ENERGY",
        "EGCG,catechins,theanine",
        "grassy,vegetal,astringent",
        "lemon,mint,honey",
        "iron absorption",
        "HOT_INFUSION",
        35,
        0,
        1,
        1,
        91,
        "Antioxidant-rich tea - EGCG supports metabolism and brain health",
        "Camellia sinensis",
    ),
    # ===== FATS & OILS =====
    (
        "coconut",
        "Coconut Oil",
        "fats",
        "MCT",
        "🥥",
        "#FFFAF0",
        15,
        30,
        15,
        862,
        0,
        0,
        100,
        0,
        0,
        0,
        0,
        0,
        0.04,
        1,
        0,
        0,
        "warm",
        "RESTORE_ENERGY",
        "FORTIFY_SKIN",
        "MCTs,lauric acid,caprylic acid",
        "coconut,sweet,tropical",
        "cacao,vanilla,turmeric",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        78,
        "Medium-chain triglycerides for quick energy - bypasses normal fat digestion",
        "Cocos nucifera",
    ),
    (
        "avocado",
        "Avocado",
        "fats",
        "MUFA",
        "🥑",
        "#568203",
        75,
        200,
        100,
        160,
        2,
        9,
        15,
        7,
        0.7,
        10,
        7,
        29,
        0.6,
        12,
        485,
        0.6,
        "cool",
        "FORTIFY_SKIN,FORTIFY_MIND",
        "RESTORE_ENERGY",
        "oleic acid,lutein,potassium",
        "creamy,mild,buttery",
        "cacao,banana,spinach",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        93,
        "Healthy fat source - monounsaturated fats for nutrient absorption",
        "Persea americana",
    ),
    (
        "omega-3",
        "Fish Oil / Algae Omega-3",
        "fats",
        "essential",
        "🐟",
        "#4682B4",
        3,
        5,
        3,
        900,
        0,
        0,
        100,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "neutral",
        "FORTIFY_MIND,COOL_ESSENCE",
        "BRIGHTEN_MOOD",
        "EPA,DHA",
        "fishy or neutral if algae",
        "lemon,blueberry,turmeric",
        "blood thinners",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        92,
        "Essential brain fats - DHA is 40% of brain phospholipids",
        "Fish oil / Algae oil",
    ),
    # ===== DAIRY & ALTERNATIVES =====
    (
        "almond milk",
        "Unsweetened Almond Milk",
        "dairy_alt",
        "nut",
        "🥛",
        "#FFFDD0",
        240,
        1000,
        240,
        17,
        0.6,
        1.4,
        1.4,
        0.5,
        0,
        0,
        37,
        7,
        0.3,
        184,
        67,
        0.2,
        "neutral",
        None,
        "STRENGTHEN_BONES",
        "vitamin E,calcium (fortified)",
        "mild,nutty,watery",
        "banana,cacao,berries",
        "nut allergy",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        82,
        "Low-calorie base - often fortified with calcium and vitamin D",
        "Prunus dulcis",
    ),
    (
        "oat milk",
        "Oat Milk",
        "dairy_alt",
        "grain",
        "🥛",
        "#F5F5DC",
        240,
        1000,
        240,
        50,
        1,
        9,
        1.5,
        1,
        4,
        0,
        0,
        5,
        0.3,
        120,
        100,
        0.2,
        "neutral",
        "FORTIFY_DIGESTION",
        "CALM_SPIRIT",
        "beta-glucan,avenanthramides",
        "creamy,oaty,slightly sweet",
        "cacao,coffee,matcha",
        "celiac disease",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        79,
        "Creamy plant milk - beta-glucan fiber for heart health",
        "Avena sativa",
    ),
    (
        "coconut milk",
        "Coconut Milk",
        "dairy_alt",
        "tropical",
        "🥥",
        "#FFFAF0",
        100,
        250,
        100,
        230,
        2.3,
        6,
        24,
        2.2,
        3.3,
        2.8,
        0,
        37,
        1.6,
        16,
        263,
        0.7,
        "warm",
        "RESTORE_ENERGY",
        "FORTIFY_SKIN",
        "MCTs,lauric acid",
        "rich,creamy,coconut",
        "turmeric,mango,cacao",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        76,
        "Rich tropical base - high in saturated fat but MCT-rich",
        "Cocos nucifera",
    ),
    (
        "kefir",
        "Plain Kefir",
        "dairy",
        "fermented",
        "🥛",
        "#FFFFF0",
        240,
        500,
        240,
        63,
        3.8,
        4.6,
        3.5,
        0,
        4.6,
        0.2,
        34,
        12,
        0.1,
        130,
        164,
        0.5,
        "cool",
        "FORTIFY_DIGESTION,FORTIFY_IMMUNITY",
        "STRENGTHEN_BONES",
        "probiotics,kefiran,tryptophan",
        "tangy,creamy,effervescent",
        "berries,honey,vanilla",
        "lactose intolerance",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        90,
        "Probiotic powerhouse - 61 strains vs yogurt 1-5",
        "Fermented milk",
    ),
    (
        "greek yogurt",
        "Greek Yogurt",
        "dairy",
        "fermented",
        "🥛",
        "#FFFAF0",
        150,
        500,
        200,
        59,
        10,
        3.6,
        0.7,
        0,
        3.2,
        0,
        7,
        11,
        0.1,
        110,
        141,
        0.5,
        "cool",
        "FORTIFY_DIGESTION,STRENGTHEN_BONES",
        None,
        "probiotics,casein,whey",
        "tangy,thick,creamy",
        "berries,honey,granola",
        "lactose intolerance",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        88,
        "Protein-rich probiotic base - 2x protein of regular yogurt",
        "Fermented milk",
    ),
    # ===== SPECIAL ADDITIONS =====
    (
        "aloe vera",
        "Aloe Vera Gel",
        "special",
        "cooling",
        "🌵",
        "#90EE90",
        30,
        100,
        50,
        4,
        0,
        1,
        0,
        0,
        0,
        3.8,
        0,
        1,
        0.1,
        8,
        8,
        0,
        "cold",
        "COOL_ESSENCE,FORTIFY_SKIN",
        "FORTIFY_DIGESTION",
        "acemannan,anthraquinones,polysaccharides",
        "mild,slightly bitter,gel-like",
        "lemon,mint,cucumber",
        "blood sugar meds",
        "COLD_BREW",
        0,
        0,
        0,
        0,
        84,
        "Internal cooling gel - acemannan supports gut lining",
        "Aloe barbadensis",
    ),
    (
        "apple cider vinegar",
        "Apple Cider Vinegar",
        "special",
        "fermented",
        "🍎",
        "#D2691E",
        15,
        30,
        15,
        21,
        0,
        0.9,
        0,
        0,
        0.4,
        0,
        0,
        5,
        0.2,
        7,
        73,
        0,
        "warm",
        "FORTIFY_DIGESTION,BALANCE_FLOW",
        "CLEANSE_BODY",
        "acetic acid,pectin,probiotics",
        "sharp,tangy,apple",
        "honey,lemon,ginger",
        "tooth enamel,low potassium",
        "COLD_BREW",
        0,
        0,
        1,
        1,
        78,
        "Digestive tonic - acetic acid may improve insulin sensitivity",
        "Fermented apple cider",
    ),
    (
        "bee pollen",
        "Bee Pollen Granules",
        "special",
        "superfood",
        "🐝",
        "#FFD700",
        5,
        15,
        10,
        314,
        22.4,
        54.4,
        5.3,
        10.6,
        35,
        10,
        20,
        54,
        4.3,
        75,
        614,
        1.6,
        "warm",
        "RESTORE_ENERGY,FORTIFY_IMMUNITY",
        "BALANCE_FLOW",
        "polyphenols,enzymes,amino acids",
        "sweet,floral,slightly bitter",
        "honey,smoothies,acai",
        "bee/pollen allergy",
        "SMOOTHIE_BLEND",
        0,
        0,
        0,
        0,
        83,
        "Nature complete food - contains all essential amino acids",
        "Mixed flower pollen",
    ),
    (
        "saffron",
        "Saffron Threads",
        "special",
        "precious",
        "🧡",
        "#FF4500",
        0.1,
        0.3,
        0.1,
        310,
        11.4,
        65,
        5.9,
        3.9,
        0,
        80.8,
        27,
        264,
        11.1,
        111,
        1724,
        1.1,
        "neutral",
        "BRIGHTEN_MOOD,FORTIFY_MIND",
        "FORTIFY_SKIN",
        "crocin,safranal,picrocrocin",
        "honey,floral,metallic",
        "milk,honey,cardamom",
        "pregnancy (high doses)",
        "HOT_INFUSION",
        0,
        0,
        0,
        0,
        87,
        "Golden antidepressant - as effective as fluoxetine in studies",
        "Crocus sativus",
    ),
    (
        "moringa",
        "Moringa Leaf Powder",
        "special",
        "superfood",
        "🌿",
        "#228B22",
        5,
        15,
        10,
        64,
        9.4,
        8.3,
        1.4,
        2,
        0,
        51.7,
        378,
        147,
        4,
        185,
        337,
        0.6,
        "warm",
        "FORTIFY_IMMUNITY,RESTORE_ENERGY",
        "FORTIFY_SKIN",
        "isothiocyanates,quercetin,chlorogenic acid",
        "green,slightly bitter,spinach-like",
        "banana,mango,honey",
        "blood sugar meds",
        "SMOOTHIE_BLEND",
        0,
        0,
        0,
        0,
        91,
        "Miracle tree - 7x vitamin C of oranges, 4x calcium of milk",
        "Moringa oleifera",
    ),
    # ===== ADDITIONAL SHAKE INGREDIENTS =====
    (
        "wheat bran",
        "Wheat Bran",
        "fiber",
        "insoluble",
        "🌾",
        "#D2B48C",
        10,
        30,
        15,
        216,
        15.6,
        64.5,
        4.3,
        42.8,
        0.4,
        0,
        0,
        611,
        10.6,
        73,
        1182,
        7.3,
        "neutral",
        "FORTIFY_DIGESTION",
        "CLEANSE_BODY",
        "ferulic acid,phytic acid,lignans",
        "nutty,earthy,grain",
        "oat bran,psyllium,banana",
        "gluten sensitivity",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        82,
        "Insoluble fiber powerhouse - promotes regularity and gut motility",
        "Triticum aestivum",
    ),
    (
        "optifiber",
        "OptiFiber PHGG",
        "fiber",
        "prebiotic",
        "🧪",
        "#E0E0E0",
        5,
        10,
        5,
        10,
        0,
        5,
        0,
        4.5,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "neutral",
        "FORTIFY_DIGESTION",
        "CALM_SPIRIT",
        "galactomannan,prebiotic fiber",
        "neutral,mild",
        "any liquid,smoothies",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        88,
        "Partially hydrolyzed guar gum - gentle prebiotic fiber, IBS-friendly",
        "Cyamopsis tetragonoloba",
    ),
    (
        "cacao nibs",
        "Raw Cacao Nibs",
        "superfoods",
        "antioxidant",
        "🍫",
        "#3D1F0D",
        10,
        30,
        15,
        528,
        13.9,
        34.7,
        46.3,
        33,
        0,
        0,
        0,
        272,
        13.9,
        160,
        830,
        6.8,
        "warm",
        "BRIGHTEN_MOOD,RESTORE_ENERGY",
        "FORTIFY_MIND",
        "theobromine,epicatechin,anandamide",
        "bitter,chocolatey,intense",
        "banana,honey,coconut",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        89,
        "Pure cacao crunch - highest food source of theobromine and magnesium",
        "Theobroma cacao",
    ),
    (
        "walnuts",
        "Walnuts",
        "nuts",
        "omega-3",
        "🥜",
        "#8B4513",
        10,
        30,
        15,
        654,
        15.2,
        13.7,
        65.2,
        6.7,
        2.6,
        1.3,
        1,
        158,
        2.9,
        98,
        441,
        3.1,
        "warm",
        "FORTIFY_MIND",
        "BALANCE_FLOW",
        "ALA omega-3,ellagic acid,melatonin",
        "buttery,earthy,slightly bitter",
        "banana,honey,oats",
        "tree nut allergy",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        90,
        "Brain-shaped brain food - highest plant omega-3 and melatonin content",
        "Juglans regia",
    ),
    (
        "lecithin",
        "Sunflower Lecithin",
        "supplements",
        "emulsifier",
        "🌻",
        "#FFD700",
        5,
        10,
        5,
        763,
        0,
        0,
        100,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "neutral",
        "FORTIFY_MIND",
        "FORTIFY_SKIN",
        "phosphatidylcholine,phosphatidylserine,inositol",
        "mild,nutty",
        "any smoothie",
        None,
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        85,
        "Natural emulsifier rich in choline - supports brain cell membranes",
        "Helianthus annuus",
    ),
    (
        "milk",
        "Whole Milk",
        "dairy",
        "base",
        "🥛",
        "#FFFAF0",
        200,
        500,
        250,
        61,
        3.2,
        4.8,
        3.3,
        0,
        5.1,
        0,
        46,
        10,
        0,
        113,
        132,
        0.4,
        "neutral",
        "STRENGTHEN_BONES",
        "RESTORE_ENERGY",
        "casein,whey,lactose,CLA",
        "creamy,mild,sweet",
        "everything",
        "lactose intolerance",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        75,
        "Complete protein source - natural blend of casein and whey",
        "Bos taurus",
    ),
    (
        "mct oil",
        "MCT Coconut Oil",
        "fats",
        "energy",
        "🥥",
        "#FFFDD0",
        5,
        15,
        10,
        862,
        0,
        0,
        100,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "neutral",
        "RESTORE_ENERGY,FORTIFY_MIND",
        None,
        "caprylic acid C8,capric acid C10",
        "neutral,light coconut",
        "coffee,smoothies,keto",
        "digestive upset if new",
        "SMOOTHIE_BLEND",
        0,
        0,
        1,
        1,
        82,
        "Instant brain fuel - MCTs convert directly to ketones for energy",
        "Cocos nucifera",
    ),
]

# Ingredient Warnings Data - Safety contraindications
# Format: (ingredient_name, warning_type, severity, condition_or_medication, warning_text, scientific_basis, source)
INGREDIENT_WARNINGS_DATA = [
    # Blood Thinners
    (
        "turmeric",
        "drug_interaction",
        "moderate",
        "Warfarin/Blood thinners",
        "May enhance anticoagulant effects and increase bleeding risk",
        "Curcumin inhibits platelet aggregation and has anticoagulant properties",
        "NIH National Library of Medicine",
    ),
    (
        "ginger",
        "drug_interaction",
        "moderate",
        "Warfarin/Blood thinners",
        "May increase bleeding risk when combined with anticoagulants",
        "Gingerols inhibit thromboxane synthesis affecting platelet function",
        "Mayo Clinic",
    ),
    (
        "omega-3",
        "drug_interaction",
        "moderate",
        "Warfarin/Blood thinners",
        "High doses may increase bleeding time",
        "EPA and DHA reduce platelet aggregation",
        "American Heart Association",
    ),
    (
        "goji berry",
        "drug_interaction",
        "moderate",
        "Warfarin/Blood thinners",
        "May interact with warfarin and increase bleeding risk",
        "Contains compounds that may affect vitamin K metabolism",
        "Memorial Sloan Kettering",
    ),
    # Blood Sugar
    (
        "cinnamon",
        "drug_interaction",
        "mild",
        "Diabetes medications",
        "May enhance blood sugar lowering effects",
        "Cinnamaldehyde improves insulin sensitivity",
        "Diabetes Care Journal",
    ),
    (
        "aloe vera",
        "drug_interaction",
        "moderate",
        "Diabetes medications",
        "May cause hypoglycemia when combined with diabetes drugs",
        "Aloe reduces blood glucose levels through multiple mechanisms",
        "Journal of Clinical Pharmacy",
    ),
    (
        "moringa",
        "drug_interaction",
        "mild",
        "Diabetes medications",
        "May enhance blood sugar lowering effects",
        "Contains isothiocyanates that affect glucose metabolism",
        "Phytotherapy Research",
    ),
    # Pregnancy
    (
        "turmeric",
        "condition",
        "caution",
        "Pregnancy",
        "Avoid therapeutic doses during pregnancy - culinary amounts OK",
        "High doses may stimulate uterine contractions",
        "American Pregnancy Association",
    ),
    (
        "ashwagandha",
        "condition",
        "avoid",
        "Pregnancy",
        "Do not use during pregnancy",
        "May have abortifacient effects at high doses",
        "NIH Office of Dietary Supplements",
    ),
    (
        "saffron",
        "condition",
        "caution",
        "Pregnancy",
        "Avoid therapeutic doses during pregnancy",
        "High doses may stimulate uterine contractions",
        "Evidence-Based Complementary Medicine",
    ),
    (
        "cayenne",
        "condition",
        "caution",
        "Pregnancy",
        "Use only small culinary amounts during pregnancy",
        "Capsaicin in large amounts may cause stomach irritation",
        "American Pregnancy Association",
    ),
    # Thyroid
    (
        "ashwagandha",
        "condition",
        "caution",
        "Thyroid conditions",
        "May affect thyroid hormone levels - consult doctor",
        "Can increase T3 and T4 levels, may be problematic in hyperthyroidism",
        "Thyroid Research Journal",
    ),
    (
        "kale",
        "condition",
        "mild",
        "Hypothyroidism",
        "Large raw amounts may affect thyroid - cooking reduces goitrogens",
        "Contains goitrogens that can interfere with iodine uptake",
        "Linus Pauling Institute",
    ),
    # Autoimmune
    (
        "spirulina",
        "condition",
        "avoid",
        "Autoimmune conditions",
        "May stimulate immune system and worsen autoimmune conditions",
        "Stimulates immune cell activity which may exacerbate autoimmune response",
        "NIH National Library of Medicine",
    ),
    (
        "reishi",
        "drug_interaction",
        "moderate",
        "Immunosuppressants",
        "May counteract immunosuppressant medications",
        "Beta-glucans stimulate immune function",
        "Memorial Sloan Kettering",
    ),
    # Allergies
    (
        "chamomile",
        "allergy",
        "moderate",
        "Ragweed allergy",
        "Cross-reactivity with ragweed - may cause allergic reaction",
        "Chamomile is in the same plant family as ragweed (Asteraceae)",
        "JACI Journal",
    ),
    (
        "bee pollen",
        "allergy",
        "severe",
        "Bee/Pollen allergy",
        "May cause severe allergic reaction including anaphylaxis",
        "Contains proteins from multiple plant sources and bee secretions",
        "Allergy and Asthma Proceedings",
    ),
    (
        "psyllium husk",
        "allergy",
        "moderate",
        "Psyllium allergy",
        "Can cause allergic reactions in sensitive individuals",
        "Contains proteins that may trigger IgE-mediated reactions",
        "Annals of Allergy",
    ),
    # Digestive
    (
        "cayenne",
        "condition",
        "avoid",
        "Peptic ulcer/GERD",
        "May irritate digestive tract and worsen symptoms",
        "Capsaicin can irritate stomach lining and increase acid production",
        "Gastroenterology Journal",
    ),
    (
        "dandelion",
        "condition",
        "avoid",
        "Gallbladder disease",
        "May stimulate bile flow and worsen gallbladder conditions",
        "Increases bile production which may be problematic with gallstones",
        "Phytotherapy Research",
    ),
    # Mental Health
    (
        "rhodiola",
        "condition",
        "caution",
        "Bipolar disorder",
        "May trigger manic episodes in bipolar disorder",
        "Stimulating adaptogens may destabilize mood in bipolar patients",
        "Journal of Alternative Medicine",
    ),
    # Kidney
    (
        "creatine",
        "condition",
        "avoid",
        "Kidney disease",
        "Do not use with existing kidney conditions",
        "Kidneys must process creatinine - may strain compromised kidneys",
        "Clinical Journal of Sport Medicine",
    ),
    (
        "spinach",
        "condition",
        "caution",
        "Kidney stones",
        "High oxalate content may contribute to kidney stones",
        "Oxalates bind to calcium and can form calcium oxite stones",
        "Journal of the American Society of Nephrology",
    ),
    # Caffeine Interactions
    (
        "matcha",
        "condition",
        "caution",
        "Caffeine sensitivity",
        "Contains caffeine - may cause jitters, anxiety, or sleep issues",
        "70mg caffeine per serving - higher than regular green tea",
        "Food Chemistry Journal",
    ),
    (
        "cacao",
        "condition",
        "mild",
        "Caffeine sensitivity",
        "Contains theobromine and some caffeine",
        "Theobromine is milder than caffeine but still stimulating",
        "Nutrients Journal",
    ),
    # Breastfeeding
    (
        "mint",
        "condition",
        "caution",
        "Breastfeeding",
        "Large amounts may reduce milk supply",
        "Menthol may decrease prolactin levels and milk production",
        "Journal of Human Lactation",
    ),
]


def init_alchemy_data():
    """Initialize alchemy system with default data."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Check if potion_effects already populated
        effects_count = cursor.execute("SELECT COUNT(*) FROM potion_effects").fetchone()[0]

        # Check if alchemy_ingredients already populated
        ingredients_count = cursor.execute("SELECT COUNT(*) FROM alchemy_ingredients").fetchone()[0]

        # If both are populated, we're done
        if effects_count > 0 and ingredients_count > 0:
            return  # Already fully populated

        # Insert potion effects (if not already)
        for effect in POTION_EFFECTS_DATA:
            cursor.execute(
                """
                INSERT OR IGNORE INTO potion_effects
                (effect_name, effect_code, body_system, icon, color_hex, description, scientific_basis, potion_name_word)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                effect,
            )

        # Insert brewing methods
        for method in BREWING_METHODS_DATA:
            cursor.execute(
                """
                INSERT OR IGNORE INTO brewing_methods
                (name, code, temp_category, icon, description, instructions, vitamin_c_retention, fiber_preservation, volatile_retention)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                method,
            )

        # Insert synergies
        for synergy in SYNERGIES_DATA:
            cursor.execute(
                """
                INSERT OR IGNORE INTO ingredient_synergies
                (name, ingredient_a, ingredient_b, ingredient_c, effect_multiplier, affected_effect_code, mechanism, discovery_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                synergy,
            )

        # Insert effect triggers
        for trigger in EFFECT_TRIGGERS_DATA:
            # Get effect_id from effect_code
            effect = cursor.execute(
                "SELECT id FROM potion_effects WHERE effect_code = ?", (trigger[0],)
            ).fetchone()
            if effect:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO effect_triggers
                    (effect_id, trigger_type, trigger_field, trigger_value, min_threshold, strength_weight)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (effect[0], trigger[1], trigger[2], trigger[3], trigger[4], trigger[5]),
                )

        # Initialize brewing journal
        cursor.execute("INSERT OR IGNORE INTO brewing_journal (id) VALUES (1)")

        # Insert alchemy ingredients
        for ing in ALCHEMY_INGREDIENTS_DATA:
            cursor.execute(
                """
                INSERT OR IGNORE INTO alchemy_ingredients
                (name, display_name, category, subcategory, icon, color_hex,
                 default_amount_g, max_daily_g, typical_serving_g,
                 calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g,
                 vitamin_c_mg, vitamin_a_mcg, magnesium_mg, iron_mg, calcium_mg, potassium_mg, zinc_mg,
                 tcm_temperature, primary_effects, secondary_effects, bioactive_compounds,
                 flavor_notes, pairs_well_with, avoid_with,
                 best_brewing_method, caffeine_mg, is_adaptogen, pregnancy_safe, breastfeeding_safe,
                 health_score, description, scientific_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                ing,
            )

        # Insert ingredient warnings
        for warning in INGREDIENT_WARNINGS_DATA:
            cursor.execute(
                """
                INSERT OR IGNORE INTO ingredient_warnings
                (ingredient_name, warning_type, severity, condition_or_medication, warning_text, scientific_basis, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                warning,
            )

        db.commit()
        print("Alchemy system initialized with data!")


def calculate_potion_effects(ingredients_with_amounts, brewing_method_code):
    """
    Calculate all effects for a potion based on ingredients and brewing method.

    Args:
        ingredients_with_amounts: List of dicts with 'name' and 'amount_g'
        brewing_method_code: 'HOT_INFUSION', 'COLD_BREW', or 'SMOOTHIE_BLEND'

    Returns:
        Dict with effects, synergies, and auto-generated name
    """
    db = get_db()

    # Get brewing method modifiers
    method = db.execute(
        "SELECT * FROM brewing_methods WHERE code = ?", (brewing_method_code,)
    ).fetchone()

    if not method:
        return {"error": "Invalid brewing method"}

    # Get all effect triggers
    triggers = db.execute(
        """
        SELECT et.*, pe.effect_code, pe.effect_name, pe.icon, pe.color_hex, pe.potion_name_word
        FROM effect_triggers et
        JOIN potion_effects pe ON et.effect_id = pe.id
    """
    ).fetchall()

    # Calculate effect strengths
    effect_scores = {}
    ingredient_names = [i["name"].lower() for i in ingredients_with_amounts]

    for trigger in triggers:
        effect_code = trigger["effect_code"]
        if effect_code not in effect_scores:
            effect_scores[effect_code] = {
                "code": effect_code,
                "name": trigger["effect_name"],
                "icon": trigger["icon"],
                "color": trigger["color_hex"],
                "potion_word": trigger["potion_name_word"],
                "score": 0,
                "synergy_multiplier": 1.0,
            }

        # Check if trigger matches
        if trigger["trigger_type"] == "ingredient":
            # Check if ingredient is present
            trigger_name = trigger["trigger_field"].lower()
            for ing in ingredients_with_amounts:
                if trigger_name in ing["name"].lower():
                    # Scale by amount (base is 10g)
                    amount_factor = min(ing["amount_g"] / 10.0, 3.0)
                    effect_scores[effect_code]["score"] += (
                        trigger["strength_weight"] * amount_factor
                    )

        elif trigger["trigger_type"] == "nutrient":
            # Would need to look up nutrition data - simplified for now
            # This would integrate with existing USDA nutrition system
            pass

    # Detect synergies
    synergies = db.execute("SELECT * FROM ingredient_synergies").fetchall()
    discovered_synergies = []

    for synergy in synergies:
        ing_a = synergy["ingredient_a"].lower()
        ing_b = synergy["ingredient_b"].lower()
        ing_c = synergy["ingredient_c"].lower() if synergy["ingredient_c"] else None

        # Check if all required ingredients are present
        has_a = any(ing_a in name for name in ingredient_names)
        has_b = any(ing_b in name for name in ingredient_names)
        has_c = ing_c is None or any(ing_c in name for name in ingredient_names)

        if has_a and has_b and has_c:
            # Synergy detected!
            discovered_synergies.append(
                {
                    "name": synergy["name"],
                    "multiplier": synergy["effect_multiplier"],
                    "mechanism": synergy["mechanism"],
                    "discovery_text": synergy["discovery_text"],
                    "affected_effect": synergy["affected_effect_code"],
                }
            )

            # Apply multiplier to affected effect
            affected = synergy["affected_effect_code"]
            if affected in effect_scores:
                effect_scores[affected]["synergy_multiplier"] *= synergy["effect_multiplier"]

    # Calculate final scores (0-100%)
    effects = []
    for code, data in effect_scores.items():
        if data["score"] > 0:
            final_score = min(100, data["score"] * data["synergy_multiplier"] * 20)
            tier = (
                1 if final_score < 30 else 2 if final_score < 60 else 3 if final_score < 90 else 4
            )
            effects.append(
                {
                    "code": code,
                    "name": data["name"],
                    "icon": data["icon"],
                    "color": data["color"],
                    "potion_word": data["potion_word"],
                    "strength": round(final_score, 1),
                    "tier": tier,
                    "synergy_boost": data["synergy_multiplier"] > 1.0,
                }
            )

    # Sort by strength
    effects.sort(key=lambda x: x["strength"], reverse=True)

    # Generate potion name
    auto_name = generate_potion_name(effects, discovered_synergies, brewing_method_code)

    return {
        "effects": effects,
        "synergies": discovered_synergies,
        "auto_name": auto_name,
        "brewing_method": dict(method),
    }


def generate_potion_name(effects, synergies, method_code):
    """Generate a magical-sounding potion name based on effects."""
    prefixes = {
        "HOT_INFUSION": ["Brew", "Decoction", "Infusion", "Tea"],
        "COLD_BREW": ["Elixir", "Tonic", "Essence", "Potion"],
        "SMOOTHIE_BLEND": ["Smoothie", "Blend", "Shake", "Nectar"],
    }

    import random

    prefix = random.choice(prefixes.get(method_code, ["Potion"]))

    if not effects:
        return f"{prefix} of Mystery"

    primary = effects[0]["potion_word"]

    if synergies:
        return f"Synergistic {prefix} of {primary}"

    if len(effects) >= 2:
        secondary = effects[1]["potion_word"]
        return f"{prefix} of {primary} and {secondary}"

    return f"{prefix} of {primary}"


# Alchemy API Routes


@app.route("/alchemy")
def alchemy_page():
    """Potion alchemy brewing interface."""
    return render_template("alchemy.html")


@app.route("/api/alchemy/effects")
def get_alchemy_effects():
    """Get all potion effects."""
    db = get_db()
    effects = db.execute(
        "SELECT * FROM potion_effects ORDER BY body_system, effect_name"
    ).fetchall()
    return jsonify([dict(e) for e in effects])


@app.route("/api/alchemy/methods")
def get_brewing_methods():
    """Get all brewing methods."""
    db = get_db()
    methods = db.execute("SELECT * FROM brewing_methods ORDER BY id").fetchall()
    return jsonify([dict(m) for m in methods])


@app.route("/api/alchemy/synergies")
def get_all_synergies():
    """Get all ingredient synergies."""
    db = get_db()
    synergies = db.execute("SELECT * FROM ingredient_synergies ORDER BY name").fetchall()
    return jsonify([dict(s) for s in synergies])


@app.route("/api/alchemy/ingredients")
def get_alchemy_ingredients():
    """Get ingredients suitable for alchemy with their effect associations and full health data."""
    db = get_db()
    category = request.args.get("category")  # Optional filter by category

    # Get all ingredients from alchemy_ingredients table
    if category:
        ingredients = db.execute(
            """
            SELECT * FROM alchemy_ingredients WHERE category = ? ORDER BY display_name
        """,
            (category,),
        ).fetchall()
    else:
        ingredients = db.execute(
            """
            SELECT * FROM alchemy_ingredients ORDER BY category, display_name
        """
        ).fetchall()

    # Get warnings for all ingredients
    warnings = db.execute(
        """
        SELECT * FROM ingredient_warnings
    """
    ).fetchall()

    # Group warnings by ingredient
    warnings_by_ingredient = {}
    for w in warnings:
        name = w["ingredient_name"]
        if name not in warnings_by_ingredient:
            warnings_by_ingredient[name] = []
        warnings_by_ingredient[name].append(
            {
                "type": w["warning_type"],
                "severity": w["severity"],
                "condition": w["condition_or_medication"],
                "text": w["warning_text"],
                "basis": w["scientific_basis"],
                "source": w["source"],
            }
        )

    # Build response with Yuka-style health scoring
    result = []
    for ing in ingredients:
        # Calculate health score category (Yuka-style)
        score = ing["health_score"] or 80
        if score >= 75:
            score_category = "excellent"
            score_color = "#22c55e"  # green
        elif score >= 50:
            score_category = "good"
            score_color = "#84cc16"  # lime
        elif score >= 25:
            score_category = "poor"
            score_color = "#f97316"  # orange
        else:
            score_category = "bad"
            score_color = "#ef4444"  # red

        result.append(
            {
                "id": ing["id"],
                "name": ing["name"],
                "display_name": ing["display_name"],
                "category": ing["category"],
                "subcategory": ing["subcategory"],
                "icon": ing["icon"],
                "color": ing["color_hex"],
                # Amounts
                "default_amount_g": ing["default_amount_g"],
                "max_daily_g": ing["max_daily_g"],
                "typical_serving_g": ing["typical_serving_g"],
                # Nutrition (macros)
                "nutrition": {
                    "calories": ing["calories"],
                    "protein_g": ing["protein_g"],
                    "carbs_g": ing["carbs_g"],
                    "fat_g": ing["fat_g"],
                    "fiber_g": ing["fiber_g"],
                    "sugar_g": ing["sugar_g"],
                },
                # Vitamins & minerals
                "micronutrients": {
                    "vitamin_c_mg": ing["vitamin_c_mg"],
                    "vitamin_a_mcg": ing["vitamin_a_mcg"],
                    "magnesium_mg": ing["magnesium_mg"],
                    "iron_mg": ing["iron_mg"],
                    "calcium_mg": ing["calcium_mg"],
                    "potassium_mg": ing["potassium_mg"],
                    "zinc_mg": ing["zinc_mg"],
                },
                # Properties
                "tcm_temperature": ing["tcm_temperature"],
                "primary_effects": (
                    ing["primary_effects"].split(",") if ing["primary_effects"] else []
                ),
                "secondary_effects": (
                    ing["secondary_effects"].split(",") if ing["secondary_effects"] else []
                ),
                "bioactive_compounds": (
                    ing["bioactive_compounds"].split(",") if ing["bioactive_compounds"] else []
                ),
                # Flavor & pairing
                "flavor_notes": ing["flavor_notes"].split(",") if ing["flavor_notes"] else [],
                "pairs_well_with": (
                    ing["pairs_well_with"].split(",") if ing["pairs_well_with"] else []
                ),
                "avoid_with": ing["avoid_with"],
                # Brewing
                "best_brewing_method": ing["best_brewing_method"],
                "caffeine_mg": ing["caffeine_mg"],
                "is_adaptogen": bool(ing["is_adaptogen"]),
                # Safety
                "pregnancy_safe": bool(ing["pregnancy_safe"]),
                "breastfeeding_safe": bool(ing["breastfeeding_safe"]),
                "warnings": warnings_by_ingredient.get(ing["name"], []),
                # Health scoring (Yuka-style)
                "health_score": score,
                "health_category": score_category,
                "health_color": score_color,
                # Description
                "description": ing["description"],
                "scientific_name": ing["scientific_name"],
            }
        )

    return jsonify(
        {
            "ingredients": result,
            "categories": list(set(i["category"] for i in result)),
            "total": len(result),
        }
    )


@app.route("/api/alchemy/preview", methods=["POST"])
def preview_potion():
    """Preview potion effects before brewing."""
    data = request.get_json()
    ingredients = data.get("ingredients", [])  # [{name, amount_g}, ...]
    method = data.get("brewing_method", "HOT_INFUSION")

    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400

    result = calculate_potion_effects(ingredients, method)
    return jsonify(result)


@app.route("/api/alchemy/brew", methods=["POST"])
def brew_potion():
    """Brew and optionally save a potion recipe."""
    data = request.get_json()
    ingredients = data.get("ingredients", [])
    method = data.get("brewing_method", "HOT_INFUSION")
    save_recipe = data.get("save", False)
    custom_name = data.get("name")

    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400

    # Calculate effects
    result = calculate_potion_effects(ingredients, method)

    # Update brewing journal
    db = get_db()
    journal = db.execute("SELECT * FROM brewing_journal WHERE id = 1").fetchone()

    # Calculate XP
    xp_breakdown = {"base": 10}
    total_xp = 10

    # Bonus for synergies discovered
    for synergy in result["synergies"]:
        synergies_found = json.loads(journal["synergies_found"]) if journal else []
        if synergy["name"] not in synergies_found:
            xp_breakdown["synergy_" + synergy["name"]] = 100
            total_xp += 100
            synergies_found.append(synergy["name"])
            db.execute(
                "UPDATE brewing_journal SET synergies_found = ? WHERE id = 1",
                (json.dumps(synergies_found),),
            )

    # Bonus for high-tier effects
    for effect in result["effects"]:
        if effect["tier"] >= 3 and "tier3_bonus" not in xp_breakdown:
            xp_breakdown["tier3_bonus"] = 75
            total_xp += 75

    # Update journal
    new_xp = (journal["total_xp"] if journal else 0) + total_xp
    new_potions = (journal["potions_brewed"] if journal else 0) + 1

    # Calculate new level
    new_level = 1
    new_title = "Apprentice Alchemist"
    for level, xp_required, title in BREWER_LEVELS:
        if new_xp >= xp_required:
            new_level = level
            new_title = title

    db.execute(
        """
        UPDATE brewing_journal
        SET total_xp = ?, potions_brewed = ?, brewer_level = ?, brewer_title = ?, updated_at = datetime('now')
        WHERE id = 1
    """,
        (new_xp, new_potions, new_level, new_title),
    )

    # Save recipe if requested
    recipe_id = None
    if save_recipe:
        method_row = db.execute(
            "SELECT id FROM brewing_methods WHERE code = ?", (method,)
        ).fetchone()
        cursor = db.execute(
            """
            INSERT INTO potion_recipes (name, auto_name, brewing_method_id, ingredients_json, effects_json, synergies_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                custom_name or result["auto_name"],
                result["auto_name"],
                method_row["id"],
                json.dumps(ingredients),
                json.dumps(result["effects"]),
                json.dumps(result["synergies"]),
            ),
        )
        recipe_id = cursor.lastrowid

        # New recipe bonus
        xp_breakdown["new_recipe"] = 50
        total_xp += 50
        db.execute(
            "UPDATE brewing_journal SET total_xp = total_xp + 50, recipes_discovered = recipes_discovered + 1 WHERE id = 1"
        )

    db.commit()

    return jsonify(
        {
            "success": True,
            "potion": result,
            "xp": {
                "earned": total_xp,
                "breakdown": xp_breakdown,
                "new_total": new_xp + (50 if save_recipe else 0),
            },
            "level": {"current": new_level, "title": new_title},
            "recipe_id": recipe_id,
        }
    )


@app.route("/api/alchemy/recipes")
def get_potion_recipes():
    """Get saved potion recipes."""
    db = get_db()
    recipes = db.execute(
        """
        SELECT pr.*, bm.name as method_name, bm.icon as method_icon
        FROM potion_recipes pr
        JOIN brewing_methods bm ON pr.brewing_method_id = bm.id
        ORDER BY pr.created_at DESC
    """
    ).fetchall()

    result = []
    for r in recipes:
        recipe = dict(r)
        recipe["ingredients"] = json.loads(r["ingredients_json"])
        recipe["effects"] = json.loads(r["effects_json"]) if r["effects_json"] else []
        recipe["synergies"] = json.loads(r["synergies_json"]) if r["synergies_json"] else []
        result.append(recipe)

    return jsonify(result)


@app.route("/api/alchemy/journal")
def get_brewing_journal():
    """Get user's brewing progress."""
    db = get_db()
    journal = db.execute("SELECT * FROM brewing_journal WHERE id = 1").fetchone()

    if not journal:
        return jsonify(
            {
                "total_xp": 0,
                "level": 1,
                "title": "Apprentice Alchemist",
                "potions_brewed": 0,
                "recipes_discovered": 0,
                "synergies_found": [],
                "next_level_xp": 100,
            }
        )

    # Find XP needed for next level
    next_level_xp = 100
    for level, xp_required, _ in BREWER_LEVELS:
        if level > journal["brewer_level"]:
            next_level_xp = xp_required
            break

    return jsonify(
        {
            "total_xp": journal["total_xp"],
            "level": journal["brewer_level"],
            "title": journal["brewer_title"],
            "potions_brewed": journal["potions_brewed"],
            "recipes_discovered": journal["recipes_discovered"],
            "synergies_found": json.loads(journal["synergies_found"]),
            "next_level_xp": next_level_xp,
            "xp_progress": journal["total_xp"] / next_level_xp * 100 if next_level_xp > 0 else 100,
        }
    )


@app.route("/api/alchemy/init", methods=["POST"])
def init_alchemy_endpoint():
    """Initialize alchemy data (for setup)."""
    init_alchemy_data()
    return jsonify({"success": True, "message": "Alchemy system initialized"})


# ============================================================================
# COMPREHENSIVE NUTRITION TRACKING (with vitamins, minerals, water)
# ============================================================================


@app.route("/api/nutrition/comprehensive/today")
def get_comprehensive_today():
    """Get today's comprehensive nutrition with all vitamins, minerals, and water."""
    db = get_db()
    today = date.today().isoformat()

    # Get goals
    goals = db.execute("SELECT * FROM nutrition_goals WHERE id = 1").fetchone()

    # Get or create today's tracking
    tracking = db.execute("SELECT * FROM nutrition_tracking WHERE date = ?", (today,)).fetchone()

    if not tracking:
        db.execute("INSERT INTO nutrition_tracking (date) VALUES (?)", (today,))
        db.commit()
        tracking = db.execute(
            "SELECT * FROM nutrition_tracking WHERE date = ?", (today,)
        ).fetchone()

    return jsonify(
        {
            "date": today,
            "goals": dict(goals) if goals else {},
            "consumed": dict(tracking) if tracking else {},
        }
    )


@app.route("/api/nutrition/comprehensive/goals", methods=["GET"])
def get_comprehensive_goals():
    """Get comprehensive nutrition goals."""
    db = get_db()
    goals = db.execute("SELECT * FROM nutrition_goals WHERE id = 1").fetchone()
    return jsonify(dict(goals) if goals else {})


@app.route("/api/nutrition/comprehensive/goals", methods=["PUT"])
def update_comprehensive_goals():
    """Update comprehensive nutrition goals."""
    db = get_db()
    data = request.json

    # Build dynamic UPDATE query
    fields = []
    values = []

    for key, value in data.items():
        if key != "id" and value is not None:
            fields.append(f"{key} = ?")
            values.append(value)

    if fields:
        query = f"UPDATE nutrition_goals SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = 1"
        db.execute(query, values)
        db.commit()

    return jsonify({"success": True})


@app.route("/api/nutrition/comprehensive/log-water", methods=["POST"])
def log_water():
    """Log water intake for today."""
    db = get_db()
    today = date.today().isoformat()
    data = request.json

    ml = data.get("ml", 0)

    # Get or create today's tracking
    tracking = db.execute("SELECT * FROM nutrition_tracking WHERE date = ?", (today,)).fetchone()

    if not tracking:
        db.execute("INSERT INTO nutrition_tracking (date, water_ml) VALUES (?, ?)", (today, ml))
    else:
        new_total = tracking["water_ml"] + ml
        db.execute(
            "UPDATE nutrition_tracking SET water_ml = ?, updated_at = CURRENT_TIMESTAMP WHERE date = ?",
            (new_total, today),
        )

    db.commit()
    return jsonify({"success": True})


@app.route("/api/nutrition/comprehensive/log-nutrients", methods=["POST"])
def log_nutrients():
    """Manually log nutrients (from external tracking, supplements, etc)."""
    db = get_db()
    today = date.today().isoformat()
    data = request.json

    # Get or create today's tracking
    tracking = db.execute("SELECT * FROM nutrition_tracking WHERE date = ?", (today,)).fetchone()

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
        if key in ["date", "id", "created_at", "updated_at"]:
            continue
        if value is not None:
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


# ============================================================================
# BUG FLAGGING - Report bugs from mobile app
# ============================================================================

FEATURES_JSON_PATH = os.path.join(os.path.dirname(__file__), "FEATURES.json")


@app.route("/api/bugs/flag", methods=["POST"])
def flag_bug():
    """Flag a bug from the mobile app. Saves to FEATURES.json."""
    data = request.get_json()

    # Load existing FEATURES.json
    features_data = {}
    if os.path.exists(FEATURES_JSON_PATH):
        with open(FEATURES_JSON_PATH, "r") as f:
            features_data = json.load(f)

    # Initialize bugs array if not present
    if "bugs" not in features_data:
        features_data["bugs"] = []

    # Add the new bug
    bug = {
        "screen": data.get("screen", "Unknown"),
        "description": data.get("description", ""),
        "severity": data.get("severity", "medium"),
        "status": "open",
        "timestamp": data.get("timestamp") or datetime.now().isoformat(),
        # New fields for enhanced error reporting
        "errorType": data.get("errorType"),
        "barcode": data.get("barcode"),
        "context": data.get("context"),
        "source": data.get("source"),
    }

    features_data["bugs"].append(bug)

    # Save back to FEATURES.json
    with open(FEATURES_JSON_PATH, "w") as f:
        json.dump(features_data, f, indent=2)

    return jsonify(
        {"success": True, "message": "Bug reported", "bug_id": len(features_data["bugs"]) - 1}
    )


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Submit comprehensive feedback after bulk scanning or other features."""
    data = request.get_json()

    # Load existing FEATURES.json
    features_data = {}
    if os.path.exists(FEATURES_JSON_PATH):
        with open(FEATURES_JSON_PATH, "r") as f:
            features_data = json.load(f)

    # Initialize feedback array if not present
    if "feedback" not in features_data:
        features_data["feedback"] = []

    # Create feedback entry
    feedback = {
        "sessionId": data.get("sessionId"),
        "satisfaction": data.get("satisfaction"),  # 1-5 star rating
        "whatWorkedWell": data.get("whatWorkedWell", ""),
        "whatCouldImprove": data.get("whatCouldImprove", ""),
        "bugDescription": data.get("bugDescription", ""),
        "wouldRecommend": data.get("wouldRecommend"),  # boolean
        "context": data.get("context", {}),  # feature name, item count, etc.
        "timestamp": datetime.now().isoformat(),
    }

    features_data["feedback"].append(feedback)

    # If bug description provided, also add to bugs array
    if feedback["bugDescription"]:
        if "bugs" not in features_data:
            features_data["bugs"] = []

        bug = {
            "screen": data.get("context", {}).get("feature", "Unknown"),
            "description": feedback["bugDescription"],
            "severity": "medium",
            "status": "open",
            "timestamp": datetime.now().isoformat(),
            "source": "feedback_form",
        }
        features_data["bugs"].append(bug)

    # Save back to FEATURES.json
    with open(FEATURES_JSON_PATH, "w") as f:
        json.dump(features_data, f, indent=2)

    return jsonify({"success": True, "message": "Feedback submitted"})


@app.route("/api/feedback/stats", methods=["GET"])
def get_feedback_stats():
    """Get feedback statistics."""
    if not os.path.exists(FEATURES_JSON_PATH):
        return jsonify(
            {
                "totalResponses": 0,
                "avgSatisfaction": 0,
                "recommendYes": 0,
                "recommendNo": 0,
                "recentFeedback": [],
            }
        )

    with open(FEATURES_JSON_PATH, "r") as f:
        features_data = json.load(f)
        feedback_list = features_data.get("feedback", [])

        if not feedback_list:
            return jsonify(
                {
                    "totalResponses": 0,
                    "avgSatisfaction": 0,
                    "recommendYes": 0,
                    "recommendNo": 0,
                    "recentFeedback": [],
                }
            )

        # Calculate stats
        total = len(feedback_list)
        satisfaction_scores = [
            f.get("satisfaction", 0) for f in feedback_list if f.get("satisfaction")
        ]
        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        )

        recommend_yes = sum(1 for f in feedback_list if f.get("wouldRecommend") is True)
        recommend_no = sum(1 for f in feedback_list if f.get("wouldRecommend") is False)

        # Get recent feedback (last 10)
        recent = feedback_list[-10:] if len(feedback_list) > 10 else feedback_list

        return jsonify(
            {
                "totalResponses": total,
                "avgSatisfaction": round(avg_satisfaction, 2),
                "recommendYes": recommend_yes,
                "recommendNo": recommend_no,
                "recentFeedback": recent,
            }
        )


@app.route("/api/bugs", methods=["GET"])
def get_bugs():
    """Get all reported bugs."""
    if os.path.exists(FEATURES_JSON_PATH):
        with open(FEATURES_JSON_PATH, "r") as f:
            features_data = json.load(f)
            return jsonify(features_data.get("bugs", []))
    return jsonify([])


# ============================================================================
# GERMAN GROCERY INTEGRATION - Phase 1: Budget Tracking
# ============================================================================

from grocery.ocr.receipt_ocr import ReceiptOCR


@app.route("/api/grocery/receipt/scan", methods=["POST"])
def scan_receipt():
    """Upload and OCR a receipt.

    Form data:
        image: File upload (required)
        store: Store hint - 'aldi', 'rewe', 'lidl', 'other' (optional)

    Returns:
        {
            receipt_id: int,
            store: str,
            date: str (YYYY-MM-DD),
            total: float,
            items: [{name: str, price: float, qty: float}],
            confidence: float (0-1)
        }
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    store_hint = request.form.get("store")

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Save uploaded file temporarily
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads", "receipts")
    os.makedirs(uploads_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(uploads_dir, filename)
    file.save(filepath)

    try:
        # OCR the receipt
        ocr = ReceiptOCR(provider="tesseract")
        receipt_data = ocr.scan_receipt(filepath, store_hint)

        # Save to database
        receipt_id = ocr.save_to_db(receipt_data, filepath)

        return jsonify(
            {
                "receipt_id": receipt_id,
                "store": receipt_data["store"],
                "date": receipt_data["date"],
                "total": receipt_data["total"],
                "items": receipt_data["items"],
                "confidence": receipt_data.get("confidence", 0.7),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/grocery/receipts", methods=["GET"])
def get_receipts():
    """Get receipt history.

    Query params:
        limit: Max number of receipts (default 30)
        offset: Number to skip (default 0)
        month: Filter by month YYYY-MM (optional)

    Returns:
        [{id, store, date, total, item_count}]
    """
    limit = min(int(request.args.get("limit", 30)), 100)
    offset = int(request.args.get("offset", 0))
    month_filter = request.args.get("month")

    conn = get_db()
    cursor = conn.cursor()

    # Build query
    query = """
        SELECT
            r.id,
            r.store,
            r.purchase_date as date,
            r.total_amount as total,
            COUNT(ri.id) as item_count,
            r.source,
            r.ocr_confidence
        FROM grocery_receipts r
        LEFT JOIN grocery_receipt_items ri ON r.id = ri.receipt_id
    """

    params = []
    if month_filter:
        query += " WHERE strftime('%Y-%m', r.purchase_date) = ?"
        params.append(month_filter)

    query += " GROUP BY r.id ORDER BY r.purchase_date DESC, r.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    receipts = []
    for row in rows:
        receipts.append(
            {
                "id": row[0],
                "store": row[1],
                "date": row[2],
                "total": row[3],
                "itemCount": row[4],
                "source": row[5],
                "confidence": row[6],
            }
        )

    return jsonify(receipts)


@app.route("/api/grocery/receipt/<int:receipt_id>", methods=["GET"])
def get_receipt_detail(receipt_id):
    """Get full receipt with line items.

    Returns:
        {
            id, store, date, total, receiptNumber, source,
            items: [{id, name, quantity, unitPrice, totalPrice}]
        }
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get receipt
    cursor.execute(
        """
        SELECT id, store, purchase_date, total_amount, receipt_number,
               source, ocr_confidence, image_path
        FROM grocery_receipts
        WHERE id = ?
    """,
        (receipt_id,),
    )

    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "Receipt not found"}), 404

    receipt = {
        "id": row[0],
        "store": row[1],
        "date": row[2],
        "total": row[3],
        "receiptNumber": row[4],
        "source": row[5],
        "confidence": row[6],
        "imagePath": row[7],
    }

    # Get items
    cursor.execute(
        """
        SELECT id, name_on_receipt, quantity, unit_price, total_price, category_guess
        FROM grocery_receipt_items
        WHERE receipt_id = ?
        ORDER BY id
    """,
        (receipt_id,),
    )

    items = []
    for item_row in cursor.fetchall():
        items.append(
            {
                "id": item_row[0],
                "name": item_row[1],
                "quantity": item_row[2],
                "unitPrice": item_row[3],
                "totalPrice": item_row[4],
                "category": item_row[5],
            }
        )

    receipt["items"] = items

    return jsonify(receipt)


@app.route("/api/grocery/budget/status", methods=["GET"])
def get_budget_status():
    """Get current month's budget status.

    Query params:
        month: YYYY-MM (default current month)

    Returns:
        {
            month, planned, actual, forecast,
            byStore: [{store, amount, percentage}],
            byCategory: [{category, amount, percentage}],
            recentReceipts: [{id, store, date, total}]
        }
    """
    month_param = request.args.get("month")

    if month_param:
        month = month_param + "-01"
    else:
        month = datetime.now().strftime("%Y-%m-01")

    conn = get_db()
    cursor = conn.cursor()

    # Get budget
    cursor.execute(
        """
        SELECT planned_budget, spent_aldi, spent_lidl, spent_rewe, spent_other, forecast_end_of_month
        FROM grocery_budget
        WHERE month = ?
    """,
        (month,),
    )

    budget_row = cursor.fetchone()

    if not budget_row:
        # No budget yet, return empty
        return jsonify(
            {
                "month": month[:7],
                "planned": 0,
                "actual": 0,
                "forecast": 0,
                "byStore": [],
                "byCategory": [],
                "recentReceipts": [],
            }
        )

    planned, spent_aldi, spent_lidl, spent_rewe, spent_other, forecast = budget_row
    total_spent = spent_aldi + spent_lidl + spent_rewe + spent_other

    # Build by-store breakdown
    by_store = []
    if spent_aldi > 0:
        by_store.append(
            {
                "store": "aldi",
                "amount": spent_aldi,
                "percentage": round((spent_aldi / total_spent) * 100, 1) if total_spent > 0 else 0,
            }
        )
    if spent_lidl > 0:
        by_store.append(
            {
                "store": "lidl",
                "amount": spent_lidl,
                "percentage": round((spent_lidl / total_spent) * 100, 1) if total_spent > 0 else 0,
            }
        )
    if spent_rewe > 0:
        by_store.append(
            {
                "store": "rewe",
                "amount": spent_rewe,
                "percentage": round((spent_rewe / total_spent) * 100, 1) if total_spent > 0 else 0,
            }
        )
    if spent_other > 0:
        by_store.append(
            {
                "store": "other",
                "amount": spent_other,
                "percentage": round((spent_other / total_spent) * 100, 1) if total_spent > 0 else 0,
            }
        )

    # Get recent receipts for this month
    cursor.execute(
        """
        SELECT id, store, purchase_date, total_amount
        FROM grocery_receipts
        WHERE strftime('%Y-%m', purchase_date) = ?
        ORDER BY purchase_date DESC, created_at DESC
        LIMIT 10
    """,
        (month[:7],),
    )

    recent_receipts = []
    for r in cursor.fetchall():
        recent_receipts.append({"id": r[0], "store": r[1], "date": r[2], "total": r[3]})

    # Calculate forecast if not set
    if forecast is None:
        # Simple forecast: current daily rate * days in month
        days_elapsed = datetime.now().day
        daily_rate = total_spent / days_elapsed if days_elapsed > 0 else 0
        days_in_month = 30  # Simplified
        forecast = daily_rate * days_in_month

    return jsonify(
        {
            "month": month[:7],
            "planned": planned,
            "actual": total_spent,
            "forecast": round(forecast, 2),
            "byStore": by_store,
            "byCategory": [],  # TODO: Category breakdown in Phase 2
            "recentReceipts": recent_receipts,
        }
    )


@app.route("/api/grocery/budget/set", methods=["POST"])
def set_monthly_budget():
    """Set budget for a month.

    Body:
        {month: 'YYYY-MM', amount: float}

    Returns:
        {success: bool}
    """
    data = request.get_json()
    month = data.get("month") + "-01"
    amount = float(data.get("amount", 600))

    conn = get_db()
    cursor = conn.cursor()

    # Insert or update budget
    cursor.execute(
        """
        INSERT INTO grocery_budget (month, planned_budget)
        VALUES (?, ?)
        ON CONFLICT(month) DO UPDATE SET planned_budget = excluded.planned_budget
    """,
        (month, amount),
    )

    conn.commit()

    return jsonify({"success": True})


@app.route("/api/grocery/budget/forecast", methods=["GET"])
def get_budget_forecast():
    """Predict end-of-month spending.

    Returns:
        {
            currentSpent: float,
            forecastTotal: float,
            daysRemaining: int,
            dailyAverage: float,
            onTrack: bool
        }
    """
    current_month = datetime.now().strftime("%Y-%m-01")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT planned_budget, spent_aldi, spent_lidl, spent_rewe, spent_other
        FROM grocery_budget
        WHERE month = ?
    """,
        (current_month,),
    )

    row = cursor.fetchone()

    if not row:
        return jsonify(
            {
                "currentSpent": 0,
                "forecastTotal": 0,
                "daysRemaining": 0,
                "dailyAverage": 0,
                "onTrack": True,
            }
        )

    planned, spent_aldi, spent_lidl, spent_rewe, spent_other = row
    total_spent = spent_aldi + spent_lidl + spent_rewe + spent_other

    # Calculate forecast
    days_elapsed = datetime.now().day
    daily_average = total_spent / days_elapsed if days_elapsed > 0 else 0

    # Days remaining in month
    import calendar

    _, days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)
    days_remaining = days_in_month - days_elapsed

    forecast_total = daily_average * days_in_month
    on_track = forecast_total <= planned

    return jsonify(
        {
            "currentSpent": round(total_spent, 2),
            "forecastTotal": round(forecast_total, 2),
            "daysRemaining": days_remaining,
            "dailyAverage": round(daily_average, 2),
            "onTrack": on_track,
        }
    )


# ============================================================================
# TESTING DASHBOARD ROUTES
# ============================================================================


@app.route("/testing")
def testing_dashboard():
    """Render testing dashboard page."""
    return render_template("testing.html")


@app.route("/api/testing/builds", methods=["GET"])
def get_test_builds():
    """Get all build versions with stats."""
    db = get_db()
    builds = db.execute(
        """
        SELECT id, version, build_date, notes,
               total_tests, passed, failed, needs_improvement, not_tested
        FROM test_builds
        ORDER BY build_date DESC
    """
    ).fetchall()

    result = []
    for build in builds:
        total = build["total_tests"] or 0
        tested = (build["passed"] or 0) + (build["failed"] or 0) + (build["needs_improvement"] or 0)
        completion = round((tested / total * 100) if total > 0 else 0, 1)

        result.append(
            {
                "id": build["id"],
                "version": build["version"],
                "build_date": build["build_date"],
                "notes": build["notes"],
                "total_tests": total,
                "passed": build["passed"] or 0,
                "failed": build["failed"] or 0,
                "needs_improvement": build["needs_improvement"] or 0,
                "not_tested": build["not_tested"] or 0,
                "completion_percent": completion,
            }
        )

    return jsonify(result)


@app.route("/api/testing/builds/<version>", methods=["GET"])
def get_build_details(version):
    """Get detailed test results for a specific build."""
    db = get_db()

    # Get build info
    build = db.execute(
        """
        SELECT id, version, build_date, notes,
               total_tests, passed, failed, needs_improvement, not_tested
        FROM test_builds
        WHERE version = ?
    """,
        (version,),
    ).fetchone()

    if not build:
        return jsonify({"error": "Build not found"}), 404

    # Get all test suites with their cases and results
    suites = db.execute(
        """
        SELECT id, suite_name, description
        FROM test_suites
        ORDER BY display_order
    """
    ).fetchall()

    result_suites = []
    for suite in suites:
        test_cases = db.execute(
            """
            SELECT tc.id, tc.test_name, tc.test_description, tc.category,
                   tr.status, tr.notes, tr.github_issue_url, tr.tested_at
            FROM test_cases tc
            LEFT JOIN test_results tr ON tc.id = tr.test_case_id AND tr.build_id = ?
            WHERE tc.suite_id = ?
            ORDER BY tc.display_order
        """,
            (build["id"], suite["id"]),
        ).fetchall()

        cases = []
        for case in test_cases:
            cases.append(
                {
                    "id": case["id"],
                    "test_name": case["test_name"],
                    "test_description": case["test_description"],
                    "category": case["category"],
                    "result": {
                        "status": case["status"] or "not_tested",
                        "notes": case["notes"],
                        "github_issue_url": case["github_issue_url"],
                        "tested_at": case["tested_at"],
                    },
                }
            )

        result_suites.append(
            {
                "id": suite["id"],
                "suite_name": suite["suite_name"],
                "description": suite["description"],
                "test_cases": cases,
            }
        )

    return jsonify(
        {
            "build": {
                "id": build["id"],
                "version": build["version"],
                "build_date": build["build_date"],
                "notes": build["notes"],
                "stats": {
                    "total": build["total_tests"] or 0,
                    "passed": build["passed"] or 0,
                    "failed": build["failed"] or 0,
                    "needs_improvement": build["needs_improvement"] or 0,
                    "not_tested": build["not_tested"] or 0,
                },
            },
            "suites": result_suites,
        }
    )


@app.route("/api/testing/builds", methods=["POST"])
def create_build():
    """Create a new build version."""
    data = request.json
    version = data.get("version")
    notes = data.get("notes", "")

    if not version:
        return jsonify({"error": "Version required"}), 400

    db = get_db()

    # Count total test cases
    total_tests = db.execute("SELECT COUNT(*) as count FROM test_cases").fetchone()["count"]

    try:
        cursor = db.execute(
            """
            INSERT INTO test_builds (version, notes, total_tests, not_tested)
            VALUES (?, ?, ?, ?)
        """,
            (version, notes, total_tests, total_tests),
        )
        db.commit()

        return jsonify({"success": True, "build_id": cursor.lastrowid, "version": version})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Version already exists"}), 400


@app.route("/api/testing/builds/<version>/tests", methods=["POST"])
def submit_test_result(version):
    """Submit a test result for a specific build."""
    data = request.json
    test_case_id = data.get("test_case_id")
    status = data.get("status")
    notes = data.get("notes", "")

    if not test_case_id or not status:
        return jsonify({"error": "test_case_id and status required"}), 400

    if status not in ["not_tested", "pass", "fail", "needs_improvement"]:
        return jsonify({"error": "Invalid status"}), 400

    db = get_db()

    # Get build ID
    build = db.execute("SELECT id FROM test_builds WHERE version = ?", (version,)).fetchone()
    if not build:
        return jsonify({"error": "Build not found"}), 404

    build_id = build["id"]

    # Check if result already exists
    existing = db.execute(
        """
        SELECT id, status FROM test_results
        WHERE build_id = ? AND test_case_id = ?
    """,
        (build_id, test_case_id),
    ).fetchone()

    if existing:
        # Update existing result
        old_status = existing["status"]
        db.execute(
            """
            UPDATE test_results
            SET status = ?, notes = ?, tested_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (status, notes, existing["id"]),
        )
        result_id = existing["id"]
    else:
        # Insert new result
        old_status = "not_tested"
        cursor = db.execute(
            """
            INSERT INTO test_results (build_id, test_case_id, status, notes)
            VALUES (?, ?, ?, ?)
        """,
            (build_id, test_case_id, status, notes),
        )
        result_id = cursor.lastrowid

    # Update build stats
    update_build_stats(db, build_id, old_status, status)
    db.commit()

    return jsonify({"success": True, "result_id": result_id})


@app.route("/api/testing/builds/<version>/tests/<int:test_case_id>", methods=["PUT"])
def update_test_result(version, test_case_id):
    """Update an existing test result."""
    data = request.json
    status = data.get("status")
    notes = data.get("notes", "")
    github_issue_url = data.get("github_issue_url")

    if not status:
        return jsonify({"error": "status required"}), 400

    db = get_db()

    # Get build ID
    build = db.execute("SELECT id FROM test_builds WHERE version = ?", (version,)).fetchone()
    if not build:
        return jsonify({"error": "Build not found"}), 404

    build_id = build["id"]

    # Get existing result
    existing = db.execute(
        """
        SELECT id, status FROM test_results
        WHERE build_id = ? AND test_case_id = ?
    """,
        (build_id, test_case_id),
    ).fetchone()

    if not existing:
        return jsonify({"error": "Test result not found"}), 404

    old_status = existing["status"]

    # Update result
    db.execute(
        """
        UPDATE test_results
        SET status = ?, notes = ?, github_issue_url = ?, tested_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (status, notes, github_issue_url, existing["id"]),
    )

    # Update build stats
    update_build_stats(db, build_id, old_status, status)
    db.commit()

    return jsonify({"success": True, "result_id": existing["id"]})


@app.route("/api/testing/export/<version>", methods=["GET"])
def export_failed_tests(version):
    """Export failed tests as markdown checklist."""
    db = get_db()

    # Get build
    build = db.execute("SELECT id FROM test_builds WHERE version = ?", (version,)).fetchone()
    if not build:
        return jsonify({"error": "Build not found"}), 404

    # Get failed and needs_improvement tests grouped by suite
    results = db.execute(
        """
        SELECT ts.suite_name, tc.test_name, tc.test_description, tr.notes, tr.status
        FROM test_results tr
        JOIN test_cases tc ON tr.test_case_id = tc.id
        JOIN test_suites ts ON tc.suite_id = ts.id
        WHERE tr.build_id = ? AND tr.status IN ('fail', 'needs_improvement')
        ORDER BY ts.display_order, tc.display_order
    """,
        (build["id"],),
    ).fetchall()

    # Generate markdown
    markdown = f"# Test Failures - v{version}\n\n"
    markdown += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    current_suite = None
    for result in results:
        if result["suite_name"] != current_suite:
            current_suite = result["suite_name"]
            markdown += f"\n## {current_suite}\n\n"

        status_label = "Fix" if result["status"] == "fail" else "Improve"
        markdown += f"- [ ] {status_label}: {result['test_name']}"
        if result["notes"]:
            markdown += f"\n  - Notes: {result['notes']}"
        markdown += f"\n  - Description: {result['test_description']}\n"

    if not results:
        markdown += "\nNo failed tests! All tests passed or need testing.\n"

    # Create dev-docs directory path
    dev_docs_dir = os.path.join(
        os.path.dirname(__file__), "..", ".claude", "dev-docs", f"testing-fixes-v{version}"
    )
    file_path = os.path.join(dev_docs_dir, "tasks.md")

    return jsonify(
        {"success": True, "markdown": markdown, "file_path": file_path, "count": len(results)}
    )


@app.route("/api/testing/github-issue", methods=["POST"])
def create_github_issue():
    """Create GitHub issue for failed test."""
    data = request.json
    test_case_id = data.get("test_case_id")
    build_version = data.get("build_version")
    notes = data.get("notes", "")

    if not test_case_id or not build_version:
        return jsonify({"error": "test_case_id and build_version required"}), 400

    db = get_db()

    # Get test case details
    test_case = db.execute(
        """
        SELECT tc.test_name, tc.test_description, ts.suite_name
        FROM test_cases tc
        JOIN test_suites ts ON tc.suite_id = ts.id
        WHERE tc.id = ?
    """,
        (test_case_id,),
    ).fetchone()

    if not test_case:
        return jsonify({"error": "Test case not found"}), 404

    # Prepare issue content
    title = f"[Test Failure] {test_case['suite_name']}: {test_case['test_name']}"

    # Escape quotes in body for shell command
    body = f"""## Test Failure Report

**Build Version**: {build_version}
**Test Suite**: {test_case['suite_name']}
**Test Case**: {test_case['test_name']}

### Description
{test_case['test_description']}

### Notes
{notes or 'No additional notes provided'}

### Steps to Reproduce
1. Build version {build_version}
2. Navigate to {test_case['suite_name']}
3. Execute test: {test_case['test_name']}

---
*Auto-generated from testing dashboard*
"""

    # Use GitHub CLI (gh) to create issue
    try:
        # Escape quotes for shell command
        escaped_title = title.replace('"', '\\"')
        escaped_body = body.replace('"', '\\"').replace("\n", "\\n")

        cmd = f'gh issue create --title "{escaped_title}" --body "{escaped_body}" --label "bug,testing"'
        result = os.popen(cmd).read()

        # Parse issue URL from output (gh returns URL on last line)
        lines = result.strip().split("\n")
        issue_url = lines[-1] if lines else ""

        if not issue_url.startswith("http"):
            return jsonify({"error": f"GitHub CLI failed: {result}"}), 500

        issue_number = issue_url.split("/")[-1]

        # Update test result with GitHub URL
        build = db.execute(
            "SELECT id FROM test_builds WHERE version = ?", (build_version,)
        ).fetchone()
        if build:
            db.execute(
                """
                UPDATE test_results
                SET github_issue_url = ?
                WHERE build_id = ? AND test_case_id = ?
            """,
                (issue_url, build["id"], test_case_id),
            )
            db.commit()

        return jsonify({"success": True, "issue_url": issue_url, "issue_number": issue_number})
    except Exception as e:
        return jsonify({"error": f"GitHub CLI failed: {str(e)}"}), 500


def update_build_stats(db, build_id, old_status, new_status):
    """Update build statistics when a test result changes."""
    # Decrement old status count
    if old_status == "pass":
        db.execute("UPDATE test_builds SET passed = passed - 1 WHERE id = ?", (build_id,))
    elif old_status == "fail":
        db.execute("UPDATE test_builds SET failed = failed - 1 WHERE id = ?", (build_id,))
    elif old_status == "needs_improvement":
        db.execute(
            "UPDATE test_builds SET needs_improvement = needs_improvement - 1 WHERE id = ?",
            (build_id,),
        )
    elif old_status == "not_tested":
        db.execute("UPDATE test_builds SET not_tested = not_tested - 1 WHERE id = ?", (build_id,))

    # Increment new status count
    if new_status == "pass":
        db.execute("UPDATE test_builds SET passed = passed + 1 WHERE id = ?", (build_id,))
    elif new_status == "fail":
        db.execute("UPDATE test_builds SET failed = failed + 1 WHERE id = ?", (build_id,))
    elif new_status == "needs_improvement":
        db.execute(
            "UPDATE test_builds SET needs_improvement = needs_improvement + 1 WHERE id = ?",
            (build_id,),
        )
    elif new_status == "not_tested":
        db.execute("UPDATE test_builds SET not_tested = not_tested + 1 WHERE id = ?", (build_id,))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    init_db()
    init_scheduler()
    print("\n" + "=" * 50)
    print("Food App v2.0 starting!")
    print("=" * 50)
    print(f"Local: http://localhost:5020")
    print(f"Network: http://0.0.0.0:5020")
    print("Access from phone using your PC's IP address")
    print("")
    print("New Features:")
    print("  - Multi-timer system: /api/timers")
    print("  - Barcode scanner: /api/barcode/<code>")
    print("  - Recipe search & filters")
    print("  - Category/cuisine stats")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5025, debug=True, use_reloader=False)
