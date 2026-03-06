-- Schema: food.db
-- Source: C:\Users\paulh\Documents\lotus eater 2.0\Food\food-app\food.db
-- Dumped: 2026-03-06T19:55:26.429570

-- Row counts:
--   achievements: 29
--   alchemy_ingredients: 63
--   auto_journal_entries: 0
--   brewing_journal: 1
--   brewing_methods: 3
--   calendar_events: 1
--   completed_meal_dishes: 0
--   completed_meal_ingredients: 0
--   completed_meals: 0
--   cooked_meal_ingredients: 0
--   cooked_meals: 1
--   cooking_deck: 8
--   cooking_insights: 0
--   cooking_sessions: 1
--   cooking_skills: 17
--   cooking_steps: 584
--   cooking_streaks: 4
--   daily_journal: 2
--   daily_micronutrients_log: 1
--   daily_nutrition_goals: 1
--   daily_nutrition_log: 1
--   daily_values_reference: 1
--   day_busyness: 0
--   decks: 28
--   effect_triggers: 72
--   family_members: 1
--   generic_ingredients: 32
--   ingredient_interactions: 0
--   ingredient_nutrients: 7
--   ingredient_synergies: 20
--   ingredient_warnings: 26
--   ingredients: 84
--   interested_recipes: 0
--   journal_entries: 1
--   kitchen_tools: 43
--   kitchen_tools_inventory: 0
--   meal_log: 0
--   meal_plan_ingredients: 5
--   meal_plan_items: 1
--   meal_plans: 1
--   meal_quests: 0
--   meal_ratings: 0
--   member_achievements: 1
--   member_goals: 0
--   member_levels: 1
--   member_needs: 10
--   nutrition_cache: 28
--   nutrition_goals: 1
--   nutrition_goals_old: 1
--   nutrition_log: 0
--   nutrition_tracking: 1
--   pantry: 0
--   pantry_inventory: 2
--   pantry_products: 286
--   personal_targets: 0
--   potion_effects: 12
--   potion_recipes: 0
--   recipe_collection: 1
--   recipe_ingredients: 125
--   recipe_preferences: 4
--   recipe_step_ingredients: 0
--   recipes: 136
--   recipes_large: 13496
--   scheduled_meals: 1
--   shopping_list: 35
--   skill_tree_definitions: 17
--   user_achievements: 0
--   user_preferences: 0

-- TABLES

CREATE TABLE achievements (
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

CREATE TABLE alchemy_ingredients (
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

CREATE TABLE auto_journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date DATE NOT NULL,
                entry_type TEXT NOT NULL,        -- 'meal_cooked', 'quest_completed', 'achievement'
                title TEXT NOT NULL,
                content TEXT,
                metadata TEXT,                   -- JSON
                synced_to_journal INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE brewing_journal (
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

CREATE TABLE brewing_methods (
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

CREATE TABLE calendar_events (
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

CREATE TABLE completed_meal_dishes (
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

CREATE TABLE completed_meal_ingredients (
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

CREATE TABLE completed_meals (
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

CREATE TABLE cooked_meal_ingredients (
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

CREATE TABLE cooked_meals (
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

CREATE TABLE cooking_deck (
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

CREATE TABLE cooking_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT NOT NULL,  -- pattern, recommendation, milestone
            insight_title TEXT NOT NULL,
            insight_text TEXT NOT NULL,
            data_json TEXT,  -- supporting data
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE cooking_sessions (
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

CREATE TABLE cooking_skills (
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
                FOREIGN KEY (parent_skill_id) REFERENCES cooking_skills(id)
            );

CREATE TABLE cooking_steps (
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

CREATE TABLE cooking_streaks (
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

CREATE TABLE daily_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_date DATE NOT NULL UNIQUE,
                summary TEXT,
                mood INTEGER,
                energy_level INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE daily_micronutrients_log (
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

CREATE TABLE daily_nutrition_goals (
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

CREATE TABLE daily_nutrition_log (
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

CREATE TABLE daily_values_reference (
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

CREATE TABLE day_busyness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                event_count INTEGER DEFAULT 0,
                total_hours REAL DEFAULT 0,
                busyness_score INTEGER,       -- 1-10
                suggested_complexity INTEGER, -- max recipe complexity
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE decks (
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

CREATE TABLE effect_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                effect_id INTEGER NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_field TEXT NOT NULL,
                trigger_value TEXT,
                min_threshold REAL,
                strength_weight REAL DEFAULT 1.0,
                FOREIGN KEY (effect_id) REFERENCES potion_effects(id)
            );

CREATE TABLE family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#6366f1',
                avatar_emoji TEXT DEFAULT '👤',
                dietary_restrictions TEXT,  -- JSON array
                calorie_target INTEGER,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE generic_ingredients (
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

CREATE TABLE ingredient_interactions (
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

CREATE TABLE ingredient_nutrients (
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

CREATE TABLE ingredient_synergies (
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

CREATE TABLE ingredient_warnings (
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

CREATE TABLE ingredients (
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

CREATE TABLE interested_recipes (
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

CREATE TABLE journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_date DATE NOT NULL,
                entry_type TEXT NOT NULL,
                entry_data TEXT NOT NULL,
                source_app TEXT,
                source_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE kitchen_tools (
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

CREATE TABLE kitchen_tools_inventory (
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

CREATE TABLE meal_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                meal_type TEXT,
                servings_eaten REAL DEFAULT 1,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );

CREATE TABLE meal_plan_ingredients (
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

CREATE TABLE meal_plan_items (
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

CREATE TABLE meal_plans (
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

CREATE TABLE meal_quests (
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

CREATE TABLE meal_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id TEXT NOT NULL,
            recipe_name TEXT,
            rating INTEGER NOT NULL,  -- 1-5 stars
            would_make_again INTEGER DEFAULT 1,
            notes TEXT,
            tags TEXT,  -- JSON array: quick, comfort, healthy, etc
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE member_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,          -- Has user been notified?
                UNIQUE(family_member_id, achievement_id),
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id)
            );

CREATE TABLE member_goals (
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

CREATE TABLE member_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_member_id INTEGER NOT NULL UNIQUE,
                total_xp INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                xp_to_next_level INTEGER DEFAULT 100,
                title TEXT DEFAULT 'Kitchen Novice',  -- Changes with level
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
            );

CREATE TABLE member_needs (
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

CREATE TABLE nutrition_cache (
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

CREATE TABLE nutrition_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Energy
            calories INTEGER DEFAULT 2000,

            -- Macronutrients
            protein_g REAL DEFAULT 50,
            carbs_g REAL DEFAULT 275,
            fat_g REAL DEFAULT 78,
            saturated_fat_g REAL DEFAULT 20,
            fiber_g REAL DEFAULT 28,
            sugar_g REAL DEFAULT 50,

            -- Water
            water_ml INTEGER DEFAULT 2000,

            -- Fat-Soluble Vitamins
            vitamin_a_mcg REAL DEFAULT 900,      -- RAE (Retinol Activity Equivalents)
            vitamin_d_mcg REAL DEFAULT 20,
            vitamin_e_mg REAL DEFAULT 15,
            vitamin_k_mcg REAL DEFAULT 120,

            -- Water-Soluble Vitamins (B Complex)
            vitamin_b1_mg REAL DEFAULT 1.2,      -- Thiamin
            vitamin_b2_mg REAL DEFAULT 1.3,      -- Riboflavin
            vitamin_b3_mg REAL DEFAULT 16,       -- Niacin
            vitamin_b5_mg REAL DEFAULT 5,        -- Pantothenic Acid
            vitamin_b6_mg REAL DEFAULT 1.7,      -- Pyridoxine
            vitamin_b7_mcg REAL DEFAULT 30,      -- Biotin
            vitamin_b9_mcg REAL DEFAULT 400,     -- Folate/Folic Acid
            vitamin_b12_mcg REAL DEFAULT 2.4,    -- Cobalamin
            vitamin_c_mg REAL DEFAULT 90,        -- Ascorbic Acid

            -- Major Minerals
            calcium_mg REAL DEFAULT 1000,
            phosphorus_mg REAL DEFAULT 700,
            magnesium_mg REAL DEFAULT 420,
            sodium_mg REAL DEFAULT 2300,
            potassium_mg REAL DEFAULT 3400,
            chloride_mg REAL DEFAULT 2300,

            -- Trace Minerals
            iron_mg REAL DEFAULT 18,
            zinc_mg REAL DEFAULT 11,
            copper_mg REAL DEFAULT 0.9,
            manganese_mg REAL DEFAULT 2.3,
            selenium_mcg REAL DEFAULT 55,
            iodine_mcg REAL DEFAULT 150,
            chromium_mcg REAL DEFAULT 35,
            molybdenum_mcg REAL DEFAULT 45,

            -- Other Important Nutrients
            omega3_g REAL DEFAULT 1.6,           -- ALA + EPA + DHA
            cholesterol_mg REAL DEFAULT 300,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE "nutrition_goals_old" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calories INTEGER DEFAULT 2000,
                protein_g REAL DEFAULT 50,
                carbs_g REAL DEFAULT 250,
                fat_g REAL DEFAULT 65,
                fiber_g REAL DEFAULT 25,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE nutrition_log (
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
        );

CREATE TABLE nutrition_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE DEFAULT (date('now')) UNIQUE,

            -- Energy
            calories REAL DEFAULT 0,

            -- Macronutrients
            protein_g REAL DEFAULT 0,
            carbs_g REAL DEFAULT 0,
            fat_g REAL DEFAULT 0,
            saturated_fat_g REAL DEFAULT 0,
            fiber_g REAL DEFAULT 0,
            sugar_g REAL DEFAULT 0,

            -- Water
            water_ml REAL DEFAULT 0,

            -- Fat-Soluble Vitamins
            vitamin_a_mcg REAL DEFAULT 0,
            vitamin_d_mcg REAL DEFAULT 0,
            vitamin_e_mg REAL DEFAULT 0,
            vitamin_k_mcg REAL DEFAULT 0,

            -- Water-Soluble Vitamins
            vitamin_b1_mg REAL DEFAULT 0,
            vitamin_b2_mg REAL DEFAULT 0,
            vitamin_b3_mg REAL DEFAULT 0,
            vitamin_b5_mg REAL DEFAULT 0,
            vitamin_b6_mg REAL DEFAULT 0,
            vitamin_b7_mcg REAL DEFAULT 0,
            vitamin_b9_mcg REAL DEFAULT 0,
            vitamin_b12_mcg REAL DEFAULT 0,
            vitamin_c_mg REAL DEFAULT 0,

            -- Major Minerals
            calcium_mg REAL DEFAULT 0,
            phosphorus_mg REAL DEFAULT 0,
            magnesium_mg REAL DEFAULT 0,
            sodium_mg REAL DEFAULT 0,
            potassium_mg REAL DEFAULT 0,
            chloride_mg REAL DEFAULT 0,

            -- Trace Minerals
            iron_mg REAL DEFAULT 0,
            zinc_mg REAL DEFAULT 0,
            copper_mg REAL DEFAULT 0,
            manganese_mg REAL DEFAULT 0,
            selenium_mcg REAL DEFAULT 0,
            iodine_mcg REAL DEFAULT 0,
            chromium_mcg REAL DEFAULT 0,
            molybdenum_mcg REAL DEFAULT 0,

            -- Other Important Nutrients
            omega3_g REAL DEFAULT 0,
            cholesterol_mg REAL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE pantry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                quantity REAL,
                unit TEXT,
                expires_at DATE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            );

CREATE TABLE pantry_inventory (
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

CREATE TABLE pantry_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT NOT NULL,
                brand TEXT,
                category TEXT,                  -- 'pantry', 'spice', 'fridge', 'freezer'
                image_url TEXT,
                -- Nutrition per 100g
                calories REAL DEFAULT 0,
                protein REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                fiber REAL DEFAULT 0,
                sodium REAL DEFAULT 0,
                sugar REAL DEFAULT 0,
                -- Product details
                serving_size TEXT,
                serving_size_g REAL,
                package_weight_g REAL,          -- Total weight when full
                price REAL,                     -- Price in dollars
                price_source TEXT,              -- 'aldi', 'manual', etc.
                -- Source tracking
                data_source TEXT,               -- 'open_food_facts', 'usda', 'manual'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            , store TEXT, store_product_id TEXT, ingredient_id INTEGER, subcategory TEXT, storage_type TEXT DEFAULT 'pantry', saturated_fat REAL DEFAULT 0, package_unit TEXT, price_per_kg REAL, currency TEXT DEFAULT 'EUR', last_price_update DATE);

CREATE TABLE personal_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT NOT NULL,  -- daily_calories, weekly_variety, monthly_new_recipes
            target_value REAL NOT NULL,
            current_value REAL DEFAULT 0,
            start_date DATE,
            end_date DATE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE potion_effects (
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

CREATE TABLE potion_recipes (
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

CREATE TABLE recipe_collection (
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

CREATE TABLE recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            );

CREATE TABLE recipe_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT NOT NULL,
                recipe_source TEXT DEFAULT 'mealdb',
                action TEXT NOT NULL,
                category TEXT,
                cuisine TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE recipe_step_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                ingredient_name TEXT NOT NULL,
                amount_g REAL,
                amount_display TEXT,  -- "2 tbsp", "1 lb", etc.
                is_required INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE recipes (
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

CREATE TABLE recipes_large (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            ingredients TEXT,
            instructions TEXT,
            cleaned_ingredients TEXT,
            image_name TEXT,
            category TEXT,
            cuisine TEXT,
            source TEXT DEFAULT 'epicurious',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE scheduled_meals (
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

CREATE TABLE shopping_list (
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

CREATE TABLE skill_tree_definitions (
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

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notified INTEGER DEFAULT 0,
            FOREIGN KEY (achievement_id) REFERENCES achievements(id)
        );

CREATE TABLE user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_type TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

-- INDEXS

CREATE UNIQUE INDEX idx_member_skill ON cooking_skills(family_member_id, skill_name);

CREATE INDEX idx_recipes_large_category ON recipes_large(category);

CREATE INDEX idx_recipes_large_cuisine ON recipes_large(cuisine);

CREATE INDEX idx_recipes_large_title ON recipes_large(title);
