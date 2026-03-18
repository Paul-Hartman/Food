-- Schema: food.db
-- Source: C:\Users\paulh\Documents\lotus eater 2.0\Food\backend\food.db
-- Dumped: 2026-03-17T15:57:34.422690

-- Row counts:
--   achievements: 29
--   alchemy_ingredients: 63
--   anthropological_recipe_ingredients: 0
--   anthropological_recipes: 0
--   auto_journal_entries: 0
--   botanical_families: 15
--   brew_logs: 0
--   brewing_journal: 1
--   brewing_methods: 3
--   calendar_events: 1
--   completed_meal_dishes: 0
--   completed_meal_ingredients: 0
--   completed_meals: 0
--   cooked_meal_ingredients: 0
--   cooked_meals: 1
--   cooking_deck: 44
--   cooking_insights: 0
--   cooking_methods: 19
--   cooking_sessions: 1
--   cooking_skills: 17
--   cooking_steps: 613
--   cooking_streaks: 4
--   culture_eras: 59
--   culture_meal_patterns: 320
--   cultures: 340
--   daily_journal: 2
--   daily_micronutrients_log: 1
--   daily_nutrition_goals: 1
--   daily_nutrition_log: 1
--   daily_values_reference: 1
--   day_busyness: 0
--   decks: 28
--   diversity_summary: 0
--   diversity_tracking: 0
--   effect_triggers: 72
--   equipment_capabilities: 29
--   family_members: 3
--   fermentation_protocols: 9
--   folk_remedies: 0
--   food_culture_origins: 10139
--   food_ingredients_wiki: 9454
--   food_meal_types: 32009
--   food_pairings: 0
--   food_tags: 112660
--   foods: 26159
--   generic_ingredients: 32
--   herb_culinary_traditions: 0
--   herb_drug_interactions: 0
--   herb_historical_uses: 0
--   herb_monographs: 0
--   herb_preparations: 0
--   herb_system_classifications: 0
--   herbal_preparation_methods: 0
--   herbalism_journal: 0
--   infusion_check_ins: 0
--   infusion_tracking: 0
--   ingredient_botanical_classification: 31
--   ingredient_categories: 2441
--   ingredient_composition: 0
--   ingredient_cooking_profiles: 7
--   ingredient_interactions: 0
--   ingredient_nutrients: 7
--   ingredient_preparations: 19
--   ingredient_synergies: 20
--   ingredient_warnings: 26
--   ingredients: 95
--   interested_recipes: 2
--   journal_entries: 1
--   kitchen_tools: 43
--   kitchen_tools_inventory: 0
--   meal_log: 0
--   meal_plan_ingredients: 5
--   meal_plan_items: 1
--   meal_plans: 2
--   meal_quests: 0
--   meal_ratings: 0
--   meal_types: 15
--   medicine_systems: 0
--   member_achievements: 1
--   member_goals: 0
--   member_levels: 1
--   member_needs: 10
--   nutrition_cache: 17
--   nutrition_goals: 1
--   nutrition_goals_old: 1
--   nutrition_log: 0
--   nutrition_tracking: 1
--   pantry: 2
--   pantry_inventory: 2
--   pantry_products: 286
--   pantry_usage_history: 3
--   personal_targets: 0
--   potion_effects: 12
--   potion_recipes: 0
--   prep_method_effects: 7
--   preparation_chemistry_log: 0
--   recipe_collection: 1
--   recipe_ingredients: 151
--   recipe_preferences: 45
--   recipe_step_ingredients: 0
--   recipes: 140
--   recipes_large: 16021
--   scale_containers: 5
--   scale_measurements: 0
--   scheduled_meals: 1
--   shopping_list: 35
--   skill_tree_definitions: 17
--   test_builds: 2
--   test_cases: 96
--   test_results: 0
--   test_suites: 602
--   transformation_processes: 17
--   transformation_recipes: 11
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
            , has_monograph INTEGER DEFAULT 0, botanical_family_id INTEGER);

CREATE TABLE anthropological_recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                food_id INTEGER,
                ingredient_name TEXT NOT NULL,
                quantity TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES anthropological_recipes(id),
                FOREIGN KEY (food_id) REFERENCES foods(id)
            );

CREATE TABLE anthropological_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_native TEXT,
    slug TEXT UNIQUE NOT NULL,
    culture_id INTEGER NOT NULL,
    culture_era_id INTEGER,
    food_id INTEGER,
    approximate_year INTEGER,
    description TEXT,
    historical_context TEXT,
    social_class TEXT,
    occasion TEXT,
    ingredients_historical TEXT,
    ingredients_modern TEXT,
    instructions_historical TEXT,
    instructions_modern TEXT,
    meal_type TEXT,
    difficulty TEXT DEFAULT 'medium',
    authenticity_level TEXT DEFAULT 'adapted',
    source_type TEXT DEFAULT 'literary',
    source_reference TEXT,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (culture_id) REFERENCES cultures(id),
    FOREIGN KEY (culture_era_id) REFERENCES culture_eras(id),
    FOREIGN KEY (food_id) REFERENCES foods(id)
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

CREATE TABLE botanical_families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_name TEXT UNIQUE NOT NULL,
                common_name TEXT,
                typical_compounds TEXT,
                microbiome_benefits TEXT,
                icon TEXT
            );

CREATE TABLE brew_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brew_method TEXT NOT NULL,  -- "pour_over", "french_press", "espresso", "aeropress"
  coffee_weight_g REAL NOT NULL,
  water_weight_g REAL NOT NULL,
  ratio REAL,  -- e.g., 16.0 for 1:16 ratio
  grind_size TEXT,
  brew_time_seconds INTEGER,
  water_temp_c REAL,
  rating INTEGER,  -- 1-5 stars
  notes TEXT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, pantry_item_id INTEGER, event_metadata TEXT,
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

CREATE TABLE cooking_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_name TEXT NOT NULL UNIQUE,
                method_category TEXT NOT NULL,  -- 'dry-heat', 'moist-heat', 'combination', 'raw-prep'
                temp_range_min_f INTEGER,
                temp_range_max_f INTEGER,
                typical_duration_min REAL,
                typical_duration_max REAL,
                heat_transfer_type TEXT,  -- 'conduction', 'convection', 'radiation', 'none'
                equipment_needed TEXT,
                description TEXT,
                common_applications TEXT
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
                step_type TEXT DEFAULT 'cook', process_id INTEGER REFERENCES transformation_processes(id),
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

CREATE TABLE culture_eras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    culture_id INTEGER NOT NULL,
    era_name TEXT NOT NULL,
    start_year INTEGER,
    end_year INTEGER,
    food_characteristics TEXT,
    trade_routes TEXT,
    social_structure_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (culture_id) REFERENCES cultures(id)
);

CREATE TABLE culture_meal_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            culture_id INTEGER REFERENCES cultures(id),
            meal_name TEXT NOT NULL,
            typical_time TEXT,
            description TEXT,
            typical_foods TEXT,
            social_context TEXT,
            UNIQUE(culture_id, meal_name)
        );

CREATE TABLE cultures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    culture_type TEXT NOT NULL DEFAULT 'civilization',
    parent_culture_id INTEGER,
    region TEXT,
    subregion TEXT,
    modern_countries TEXT,
    era_start_year INTEGER,
    era_end_year INTEGER,
    is_living_culture INTEGER DEFAULT 1,
    wikipedia_url TEXT,
    wikidata_qid TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, slug TEXT,
    FOREIGN KEY (parent_culture_id) REFERENCES cultures(id)
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

CREATE TABLE diversity_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_type TEXT,
                period_start_date DATE,
                unique_ingredients INTEGER,
                unique_families INTEGER,
                unique_plants INTEGER,
                unique_fermented INTEGER,
                goal_met INTEGER
            );

CREATE TABLE diversity_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER,
                family_id INTEGER,
                consumed_date DATE,
                week_start_date DATE,
                month_start_date DATE,
                is_plant_based INTEGER,
                is_fermented INTEGER,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY (family_id) REFERENCES botanical_families(id)
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

CREATE TABLE equipment_capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_category TEXT NOT NULL,
                capability_name TEXT NOT NULL,
                preset_name TEXT,
                temp_f INTEGER,
                duration_hours REAL,
                process_id INTEGER,
                success_rate INTEGER,
                FOREIGN KEY (process_id) REFERENCES transformation_processes(id)
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

CREATE TABLE fermentation_protocols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol_name TEXT NOT NULL,
                base_ingredient_id INTEGER,
                microorganism_species TEXT,
                culture_source TEXT,
                temp_optimal_f INTEGER,
                ph_target REAL,
                brine_salinity_percent REAL,
                duration_days INTEGER,
                container_requirements TEXT,
                safety_notes TEXT,
                probiotic_species TEXT,
                FOREIGN KEY (base_ingredient_id) REFERENCES ingredients(id)
            );

CREATE TABLE folk_remedies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy_name TEXT NOT NULL,
                origin_culture TEXT,
                medicine_system_id INTEGER,
                condition_treated TEXT,
                ingredients_json TEXT NOT NULL,
                preparation_method_id INTEGER,
                preparation_instructions TEXT,
                historical_narrative TEXT,
                scientific_validation TEXT,
                safety_rating TEXT DEFAULT 'generally_safe',
                discovery_xp INTEGER DEFAULT 25,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (medicine_system_id) REFERENCES medicine_systems(id),
                FOREIGN KEY (preparation_method_id) REFERENCES herbal_preparation_methods(id)
            );

CREATE TABLE food_culture_origins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    culture_id INTEGER NOT NULL,
    culture_era_id INTEGER,
    origin_type TEXT DEFAULT 'native',
    significance TEXT DEFAULT 'everyday',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id),
    FOREIGN KEY (culture_id) REFERENCES cultures(id),
    UNIQUE(food_id, culture_id)
);

CREATE TABLE food_ingredients_wiki (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    ingredient_name TEXT NOT NULL,
    wikidata_qid TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id),
    UNIQUE(food_id, ingredient_name)
);

CREATE TABLE food_meal_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    meal_type_id INTEGER NOT NULL,
    culture_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id),
    FOREIGN KEY (meal_type_id) REFERENCES meal_types(id),
    FOREIGN KEY (culture_id) REFERENCES cultures(id),
    UNIQUE(food_id, meal_type_id, culture_id)
);

CREATE TABLE food_pairings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    paired_food_name TEXT NOT NULL,
    paired_food_id INTEGER,
    pairing_type TEXT DEFAULT 'served_with',
    source TEXT DEFAULT 'wikidata',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id),
    FOREIGN KEY (paired_food_id) REFERENCES foods(id),
    UNIQUE(food_id, paired_food_name)
);

CREATE TABLE food_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    tag_category TEXT NOT NULL,
    tag_value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'wikidata',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id),
    UNIQUE(food_id, tag_category, tag_value)
);

CREATE TABLE foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_native TEXT,
    slug TEXT UNIQUE NOT NULL,
    food_type TEXT DEFAULT 'dish',
    primary_category TEXT,
    subcategory TEXT,
    wikipedia_url TEXT,
    wikidata_qid TEXT,
    image_url TEXT,
    is_vegetarian INTEGER DEFAULT 0,
    is_vegan INTEGER DEFAULT 0,
    is_gluten_free INTEGER DEFAULT 0,
    typical_prep_method TEXT,
    serving_temperature TEXT,
    description TEXT,
    data_source TEXT DEFAULT 'seed',
    data_quality TEXT DEFAULT 'high',
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

CREATE TABLE herb_culinary_traditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alchemy_ingredient_id INTEGER NOT NULL,
                cuisine_tradition TEXT NOT NULL,
                culinary_role TEXT,
                common_dishes TEXT,
                food_as_medicine_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alchemy_ingredient_id) REFERENCES alchemy_ingredients(id)
            );

CREATE TABLE herb_drug_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alchemy_ingredient_id INTEGER NOT NULL,
                drug_name TEXT NOT NULL,
                drug_class TEXT,
                interaction_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                mechanism TEXT,
                clinical_evidence TEXT,
                management TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alchemy_ingredient_id) REFERENCES alchemy_ingredients(id)
            );

CREATE TABLE herb_historical_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alchemy_ingredient_id INTEGER NOT NULL,
                culture_name TEXT NOT NULL,
                region TEXT,
                period_start_year INTEGER,
                period_end_year INTEGER,
                use_category TEXT DEFAULT 'medicinal',
                preparation_method TEXT,
                social_context TEXT,
                primary_source TEXT,
                archaeological_evidence TEXT,
                trade_route TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alchemy_ingredient_id) REFERENCES alchemy_ingredients(id)
            );

CREATE TABLE herb_monographs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alchemy_ingredient_id INTEGER UNIQUE NOT NULL,
                latin_name TEXT,
                common_names TEXT,
                botanical_family TEXT,
                plant_description TEXT,
                habitat TEXT,
                parts_used TEXT,
                key_constituents TEXT,
                pharmacology TEXT,
                clinical_evidence_summary TEXT,
                safety_profile TEXT,
                dosage_forms TEXT,
                quality_markers TEXT,
                evidence_quality TEXT DEFAULT 'moderate',
                monograph_sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alchemy_ingredient_id) REFERENCES alchemy_ingredients(id)
            );

CREATE TABLE herb_preparations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alchemy_ingredient_id INTEGER NOT NULL,
                preparation_method_id INTEGER NOT NULL,
                plant_part_used TEXT,
                herb_to_solvent_ratio TEXT,
                specific_instructions TEXT,
                dosage TEXT,
                best_for TEXT,
                key_compounds_extracted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alchemy_ingredient_id) REFERENCES alchemy_ingredients(id),
                FOREIGN KEY (preparation_method_id) REFERENCES herbal_preparation_methods(id),
                UNIQUE(alchemy_ingredient_id, preparation_method_id)
            );

CREATE TABLE herb_system_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alchemy_ingredient_id INTEGER NOT NULL,
                medicine_system_id INTEGER NOT NULL,
                temperature_quality TEXT,
                taste_qualities TEXT,
                system_properties_json TEXT,
                therapeutic_actions TEXT,
                traditional_indications TEXT,
                traditional_preparations TEXT,
                contraindications_in_system TEXT,
                classical_formula_references TEXT,
                dosage_traditional TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alchemy_ingredient_id) REFERENCES alchemy_ingredients(id),
                FOREIGN KEY (medicine_system_id) REFERENCES medicine_systems(id),
                UNIQUE(alchemy_ingredient_id, medicine_system_id)
            );

CREATE TABLE herbal_preparation_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_code TEXT UNIQUE NOT NULL,
                method_name TEXT NOT NULL,
                solvent TEXT,
                duration_range TEXT,
                temperature_range TEXT,
                extraction_properties TEXT,
                shelf_life TEXT,
                equipment_needed TEXT,
                general_instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE herbalism_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                herbalist_level INTEGER DEFAULT 1,
                herbalist_xp INTEGER DEFAULT 0,
                herbalist_title TEXT DEFAULT 'Herb Gatherer',
                preparations_made INTEGER DEFAULT 0,
                systems_explored TEXT DEFAULT '[]',
                remedies_discovered TEXT DEFAULT '[]',
                herbs_studied INTEGER DEFAULT 0,
                monographs_read TEXT DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE infusion_check_ins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  infusion_id INTEGER NOT NULL,
  day_number INTEGER NOT NULL,
  weight_g REAL NOT NULL,
  temperature_c REAL,
  notes TEXT,
  logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (infusion_id) REFERENCES infusion_tracking(id) ON DELETE CASCADE
);

CREATE TABLE infusion_tracking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT,  -- "alcohol", "oil", "coffee", "tea"
  start_date DATE NOT NULL,
  target_duration_days INTEGER,
  initial_weight_g REAL NOT NULL,
  current_weight_g REAL,
  reminder_interval_days INTEGER DEFAULT 3,
  next_reminder_date DATE,
  status TEXT DEFAULT 'active',  -- "active", "completed", "discarded"
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ingredient_botanical_classification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER,
                family_id INTEGER,
                genus TEXT,
                species TEXT,
                plant_part TEXT,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY (family_id) REFERENCES botanical_families(id)
            );

CREATE TABLE ingredient_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE ingredient_composition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prepared_ingredient_id INTEGER,
                component_ingredient_id INTEGER,
                quantity_per_100g REAL,
                component_role TEXT,
                FOREIGN KEY (prepared_ingredient_id) REFERENCES ingredient_preparations(id),
                FOREIGN KEY (component_ingredient_id) REFERENCES ingredients(id)
            );

CREATE TABLE ingredient_cooking_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                cooking_method_id INTEGER NOT NULL,
                process_id INTEGER,  -- Links to transformation_processes for detailed chemistry

                -- Flavor transformation
                flavor_before TEXT,
                flavor_after TEXT,
                flavor_compounds_formed TEXT,
                flavor_intensity_change TEXT,  -- '1x → 3x'

                -- Texture transformation
                texture_before TEXT,
                texture_after TEXT,
                water_activity_change TEXT,
                cell_structure_change TEXT,

                -- Chemical reactions
                primary_reactions TEXT,
                enzymes_activated TEXT,
                enzymes_deactivated TEXT,

                -- Optimal conditions
                optimal_temp_f INTEGER,
                optimal_duration_min REAL,
                recommended_technique TEXT,

                -- Notes
                scientific_notes TEXT,
                chef_tips TEXT,

                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY (cooking_method_id) REFERENCES cooking_methods(id),
                FOREIGN KEY (process_id) REFERENCES transformation_processes(id),
                UNIQUE(ingredient_id, cooking_method_id)
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

CREATE TABLE ingredient_preparations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_ingredient_id INTEGER,
                preparation_name TEXT NOT NULL,
                parent_preparation_id INTEGER,
                hydration_percent REAL,
                calories_per_100g REAL,
                protein_per_100g REAL,
                carbs_per_100g REAL,
                fat_per_100g REAL,
                fiber_per_100g REAL,
                FOREIGN KEY (base_ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY (parent_preparation_id) REFERENCES ingredient_preparations(id)
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
            , base_flavor_profile TEXT, base_texture TEXT, key_flavor_compounds TEXT, enzyme_systems TEXT);

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

CREATE TABLE meal_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medicine_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_code TEXT UNIQUE NOT NULL,
                system_name TEXT NOT NULL,
                origin_region TEXT,
                foundational_text TEXT,
                core_philosophy TEXT,
                classification_axes TEXT,
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
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, price REAL DEFAULT NULL, is_daily_use INTEGER DEFAULT 0, daily_usage_rate REAL DEFAULT 0, restock_threshold_days INTEGER DEFAULT 3, last_depletion_date DATE, image_url TEXT,
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, measured_by_scale INTEGER DEFAULT 0,
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

CREATE TABLE pantry_usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pantry_item_id INTEGER NOT NULL,
                quantity_change REAL NOT NULL,
                quantity_before REAL NOT NULL,
                quantity_after REAL NOT NULL,
                change_type TEXT NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pantry_item_id) REFERENCES pantry(id) ON DELETE CASCADE
            );

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

CREATE TABLE prep_method_effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                prep_method TEXT NOT NULL,  -- 'sliced', 'minced', 'crushed', 'whole', 'diced', 'julienned'

                -- Surface area impact
                surface_area_ratio REAL,  -- 1.0 (whole) → 10.0 (minced) → 50.0 (crushed)

                -- Flavor release
                flavor_intensity TEXT,
                enzyme_exposure TEXT,
                compounds_released TEXT,

                -- Cooking implications
                cooking_time_impact TEXT,
                texture_distribution TEXT,

                -- Use cases
                best_for TEXT,
                example_dishes TEXT,

                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
                UNIQUE(ingredient_id, prep_method)
            );

CREATE TABLE preparation_chemistry_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_name TEXT NOT NULL,
                transformation_recipe_id INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                ph_readings TEXT,
                temp_readings TEXT,
                observations TEXT,
                success INTEGER,
                quality_rating INTEGER,
                lessons_learned TEXT,
                FOREIGN KEY (transformation_recipe_id) REFERENCES transformation_recipes(id)
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

CREATE TABLE scale_containers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  tare_weight_g REAL NOT NULL,
  color_hex TEXT,
  icon_emoji TEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scale_measurements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER,
  pantry_inventory_id INTEGER,
  gross_weight_g REAL NOT NULL,
  tare_weight_g REAL DEFAULT 0,
  net_weight_g REAL NOT NULL,
  container_id INTEGER,
  measurement_type TEXT,  -- "recipe_ingredient", "add_to_pantry", "manual"
  recipe_id INTEGER,
  notes TEXT,
  measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (product_id) REFERENCES pantry_products(id),
  FOREIGN KEY (pantry_inventory_id) REFERENCES pantry_inventory(id),
  FOREIGN KEY (container_id) REFERENCES scale_containers(id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
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

CREATE TABLE test_builds (
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

CREATE TABLE test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suite_id INTEGER NOT NULL,
                test_name TEXT NOT NULL,            -- "Recipe list loads"
                test_description TEXT NOT NULL,     -- "Verify recipe grid displays on launch"
                category TEXT,                      -- "ui", "api", "offline", "edge_case"
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, platform TEXT DEFAULT 'both',
                FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
            );

CREATE TABLE test_results (
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

CREATE TABLE test_suites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suite_name TEXT NOT NULL,           -- "RecipesScreen", "PantryScreen", etc.
                description TEXT,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE transformation_processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name TEXT NOT NULL,
                process_type TEXT,
                temp_min_f INTEGER,
                temp_max_f INTEGER,
                temp_optimal_f INTEGER,
                duration_min_hours REAL,
                duration_max_hours REAL,
                ph_start REAL,
                ph_end REAL,
                required_equipment_category TEXT,
                chemical_reactions TEXT,
                microorganisms TEXT,
                chemistry_explanation TEXT,
                beginner_explanation TEXT,
                expert_explanation TEXT
            , flavor_changes_json TEXT, texture_changes_json TEXT, enzyme_activity TEXT, volatile_compounds TEXT);

CREATE TABLE transformation_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_name TEXT NOT NULL,
                base_ingredient_id INTEGER,
                output_preparation_id INTEGER,
                process_id INTEGER,
                equipment_id INTEGER,
                yield_percent REAL,
                instructions_json TEXT,
                quality_metrics TEXT,
                FOREIGN KEY (base_ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY (output_preparation_id) REFERENCES ingredient_preparations(id),
                FOREIGN KEY (process_id) REFERENCES transformation_processes(id),
                FOREIGN KEY (equipment_id) REFERENCES kitchen_tools(id)
            );

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

CREATE INDEX idx_brew_logs_created_at ON brew_logs(created_at);

CREATE INDEX idx_brew_logs_method ON brew_logs(brew_method);

CREATE INDEX idx_brew_logs_rating ON brew_logs(rating);

CREATE INDEX idx_fco_culture ON food_culture_origins(culture_id);

CREATE INDEX idx_fmt_culture ON food_meal_types(culture_id);

CREATE INDEX idx_fmt_meal_culture ON food_meal_types(meal_type_id, culture_id);

CREATE INDEX idx_food_tags_cat_val ON food_tags(tag_category, tag_value);

CREATE INDEX idx_food_tags_category ON food_tags(tag_category);

CREATE INDEX idx_food_tags_food ON food_tags(food_id);

CREATE INDEX idx_food_tags_value ON food_tags(tag_value);

CREATE INDEX idx_ft_cuisine ON food_tags(tag_category, tag_value) WHERE tag_category = 'cuisine';

CREATE INDEX idx_ic_ingredient ON ingredient_categories(ingredient_name);

CREATE INDEX idx_infusion_check_ins_day ON infusion_check_ins(day_number);

CREATE INDEX idx_infusion_check_ins_infusion ON infusion_check_ins(infusion_id);

CREATE INDEX idx_infusion_next_reminder ON infusion_tracking(next_reminder_date);

CREATE INDEX idx_infusion_status ON infusion_tracking(status);

CREATE UNIQUE INDEX idx_member_skill ON cooking_skills(family_member_id, skill_name);

CREATE INDEX idx_pantry_image_url ON pantry(image_url);

CREATE INDEX idx_recipes_large_category ON recipes_large(category);

CREATE INDEX idx_recipes_large_cuisine ON recipes_large(cuisine);

CREATE INDEX idx_recipes_large_title ON recipes_large(title);

CREATE INDEX idx_scale_containers_name ON scale_containers(name);

CREATE INDEX idx_scale_measurements_measured_at ON scale_measurements(measured_at);

CREATE INDEX idx_scale_measurements_product ON scale_measurements(product_id);

CREATE INDEX idx_scale_measurements_type ON scale_measurements(measurement_type);

CREATE INDEX idx_usage_history_item_date
            ON pantry_usage_history(pantry_item_id, logged_at)
        ;
