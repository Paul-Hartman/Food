"""
Seed cooking profiles for Priority 1 ingredients (molecular gastronomy system).

Priority 1 Ingredients (20 total):
- Vegetables: Tomatoes, Garlic, Onions, Bell Peppers, Broccoli, Carrots, Potatoes, Zucchini, Mushrooms, Spinach
- Proteins: Chicken Breast, Beef, Pork, Salmon, Shrimp, Eggs
- Aromatics/Others: Ginger, Fresh Basil, Rice, Pasta

Each ingredient gets 6-10 cooking profiles with detailed transformations.
"""

import sqlite3
import os

def get_db_path():
    """Get the database path."""
    return os.path.join(os.path.dirname(__file__), 'food.db')

def get_ingredient_id(cursor, name):
    """Get ingredient ID by name."""
    result = cursor.execute("SELECT id FROM ingredients WHERE name LIKE ?", (f"%{name}%",)).fetchone()
    return result[0] if result else None

def get_cooking_method_id(cursor, name):
    """Get cooking method ID by name."""
    result = cursor.execute("SELECT id FROM cooking_methods WHERE method_name = ?", (name,)).fetchone()
    return result[0] if result else None

def get_process_id(cursor, name):
    """Get transformation process ID by name."""
    result = cursor.execute("SELECT id FROM transformation_processes WHERE process_name LIKE ?", (f"%{name}%",)).fetchone()
    return result[0] if result else None

def seed_tomato_profiles(cursor):
    """Seed cooking profiles for tomatoes."""
    print("\n  Tomatoes:")
    ingredient_id = get_ingredient_id(cursor, "Tomato")
    if not ingredient_id:
        print("    [ERROR] Tomato not found in database")
        return 0

    # First, update base ingredient profile
    cursor.execute("""
        UPDATE ingredients SET
            base_flavor_profile = ?,
            base_texture = ?,
            key_flavor_compounds = ?,
            enzyme_systems = ?
        WHERE id = ?
    """, (
        "sweet, acidic, fruity, mild umami (glutamate)",
        "firm, crisp skin, high water content (95%), intact cell walls",
        "glutamate (umami), lycopene (red pigment), citric acid, fructose, pectin",
        "pectin methylesterase (cell wall breakdown), polyphenol oxidase (browning when damaged)",
        ingredient_id
    ))

    profiles = [
        # Sauté
        {
            'method': 'Sauté',
            'process': 'Sautéing',
            'flavor_before': 'sweet, acidic, fresh, mild umami',
            'flavor_after': 'concentrated sweet-savory, intense umami, caramelized edges',
            'flavor_compounds': 'Maillard products (pyrazines, furans), caramelized sugars, concentrated glutamate',
            'flavor_intensity': '1x → 3x',
            'texture_before': 'firm, crisp, 95% water, intact cell walls',
            'texture_after': 'soft, collapsed, 80% water, broken pectin',
            'water_activity': '0.98 → 0.85',
            'cell_structure': 'Heat denatures pectin, collapses cells, releases juice',
            'reactions': 'Maillard reaction (>300°F), caramelization (>320°F), pectin hydrolysis (185°F)',
            'enzymes_activated': None,
            'enzymes_deactivated': 'polyphenol oxidase (>180°F)',
            'optimal_temp': 375,
            'optimal_duration': 8,
            'technique': 'High heat, don\'t crowd pan (traps steam), season AFTER cooking (salt draws water)',
            'scientific_notes': 'Heat denatures pectin (cell wall polysaccharide), causing cell collapse. Maillard reaction between amino acids (glutamate) and fructose creates savory browning. Lycopene becomes more bioavailable.',
            'chef_tips': 'Cut tomatoes in half, sear cut-side down first. Don\'t stir for 3-4 minutes to develop fond. Season after cooking to prevent water release.'
        },
        # Roast
        {
            'method': 'Roast',
            'process': 'Roasting',
            'flavor_before': 'sweet, acidic, fresh',
            'flavor_after': 'deeply caramelized, concentrated sweetness, rich umami',
            'flavor_compounds': 'Extensive Maillard products, caramelized sugars, melanoidins, 5x concentrated glutamate',
            'flavor_intensity': '1x → 5x',
            'texture_before': 'firm, 95% water',
            'texture_after': 'jammy, collapsed, 60% water, concentrated pulp',
            'water_activity': '0.98 → 0.75',
            'cell_structure': 'Complete pectin breakdown, cells fully collapsed',
            'reactions': 'Maillard reaction, extensive caramelization, lycopene isomerization (cis → trans)',
            'enzymes_activated': None,
            'enzymes_deactivated': 'all enzymes',
            'optimal_temp': 425,
            'optimal_duration': 30,
            'technique': 'Cut in half, drizzle olive oil, roast cut-side up. Don\'t overcrowd pan.',
            'scientific_notes': 'Extended dry heat (20-40 min) evaporates 35-40% water weight. Lycopene isomerizes to trans-form (more bioavailable). Maillard reaction produces hundreds of flavor compounds.',
            'chef_tips': 'Roast at 400-450°F for best caramelization. Cherry tomatoes burst and concentrate beautifully. Add garlic in last 10 minutes.'
        },
        # Grill
        {
            'method': 'Grill',
            'process': 'Grilling',
            'flavor_before': 'sweet, acidic, fresh',
            'flavor_after': 'charred, smoky, intense sweet-savory',
            'flavor_compounds': 'Char compounds, smoke phenols, caramelization, concentrated sugars',
            'flavor_intensity': '1x → 5x',
            'texture_before': 'firm, 95% water',
            'texture_after': 'charred surface, soft interior, 75% water',
            'water_activity': '0.98 → 0.80',
            'cell_structure': 'Charred outer cells, softened interior',
            'reactions': 'Maillard reaction, char formation (incomplete combustion), smoke deposition',
            'enzymes_activated': None,
            'enzymes_deactivated': 'all enzymes',
            'optimal_temp': 500,
            'optimal_duration': 8,
            'technique': 'Cut in half, grill cut-side down first over direct heat. Flip once.',
            'scientific_notes': 'High heat (500-600°F) creates char = carbon particles + heterocyclic amines. Smoke deposits phenolic compounds (guaiacol, syringol).',
            'chef_tips': 'Oil the grill, not the tomatoes. Grill cut-side down for 4-5 minutes, then flip for 2-3 minutes. Don\'t move them around.'
        },
        # Simmer (in sauce)
        {
            'method': 'Simmer',
            'process': 'Simmering',
            'flavor_before': 'sweet, acidic',
            'flavor_after': 'mellow, rounded, less acidic, sweet-savory',
            'flavor_compounds': 'Acid reduction, sugar concentration, glutamate release',
            'flavor_intensity': '1x → 2x',
            'texture_before': 'firm, intact',
            'texture_after': 'completely broken down, sauce consistency',
            'water_activity': '0.98 → 0.92',
            'cell_structure': 'Cells completely disintegrated, pectin dissolved',
            'reactions': 'Pectin breakdown, acid buffering, flavor melding',
            'enzymes_activated': None,
            'enzymes_deactivated': 'all enzymes',
            'optimal_temp': 195,
            'optimal_duration': 45,
            'technique': 'Crush or dice tomatoes, simmer gently. Stir occasionally to prevent sticking.',
            'scientific_notes': 'Gentle heat (185-205°F) breaks down pectin without violent boiling. Acids mellow as volatile compounds evaporate. Flavors meld over time.',
            'chef_tips': 'For marinara: simmer crushed tomatoes 30-45 minutes. Longer = sweeter (acid reduction). Add basil at end (volatile oils).'
        },
        # Blanch
        {
            'method': 'Blanch',
            'process': 'Blanching',
            'flavor_before': 'sweet, acidic, fresh',
            'flavor_after': 'slightly sweetened, less acidic, bright',
            'flavor_compounds': 'Minimal change, slight sugar concentration',
            'flavor_intensity': '1x → 1.2x',
            'texture_before': 'firm, skin intact',
            'texture_after': 'tender, skin loosened (easy to peel)',
            'water_activity': '0.98 → 0.97',
            'cell_structure': 'Minimal pectin breakdown, skin detaches from flesh',
            'reactions': 'Brief pectin softening, polyphenol oxidase deactivation',
            'enzymes_activated': None,
            'enzymes_deactivated': 'polyphenol oxidase',
            'optimal_temp': 212,
            'optimal_duration': 1,
            'technique': 'Score an X on bottom, boil 30-60 seconds, ice bath immediately.',
            'scientific_notes': 'Brief boiling (30-60 sec) loosens skin via thermal expansion. Ice bath stops cooking immediately. Enzymes deactivated.',
            'chef_tips': 'Used for peeling tomatoes for sauces. Score the bottom first. Don\'t leave in too long or they\'ll get mushy.'
        },
    ]

    count = 0
    for profile in profiles:
        method_id = get_cooking_method_id(cursor, profile['method'])
        process_id = get_process_id(cursor, profile['process'])

        try:
            cursor.execute("""
                INSERT INTO ingredient_cooking_profiles (
                    ingredient_id, cooking_method_id, process_id,
                    flavor_before, flavor_after, flavor_compounds_formed, flavor_intensity_change,
                    texture_before, texture_after, water_activity_change, cell_structure_change,
                    primary_reactions, enzymes_activated, enzymes_deactivated,
                    optimal_temp_f, optimal_duration_min, recommended_technique,
                    scientific_notes, chef_tips
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ingredient_id, method_id, process_id,
                profile['flavor_before'], profile['flavor_after'], profile['flavor_compounds'], profile['flavor_intensity'],
                profile['texture_before'], profile['texture_after'], profile['water_activity'], profile['cell_structure'],
                profile['reactions'], profile['enzymes_activated'], profile['enzymes_deactivated'],
                profile['optimal_temp'], profile['optimal_duration'], profile['technique'],
                profile['scientific_notes'], profile['chef_tips']
            ))
            print(f"    [OK] {profile['method']}")
            count += 1
        except sqlite3.IntegrityError:
            print(f"    [SKIP] {profile['method']} already exists")

    return count

def seed_tomato_prep_methods(cursor):
    """Seed prep method variations for tomatoes."""
    ingredient_id = get_ingredient_id(cursor, "Tomato")
    if not ingredient_id:
        return 0

    prep_methods = [
        {
            'prep_method': 'Sliced',
            'surface_area_ratio': 2.0,
            'flavor_intensity': 'mild',
            'enzyme_exposure': 'minimal',
            'compounds_released': 'minimal cell damage, fresh flavor preserved',
            'cooking_time_impact': 'moderate',
            'texture_distribution': 'visible slices, maintains structure',
            'best_for': 'salads, sandwiches, garnishes',
            'example_dishes': 'Caprese salad, BLT sandwich, burger topping'
        },
        {
            'prep_method': 'Diced',
            'surface_area_ratio': 5.0,
            'flavor_intensity': 'medium',
            'enzyme_exposure': 'moderate',
            'compounds_released': 'moderate cell damage, juice release, some enzyme activation',
            'cooking_time_impact': 'fast (breaks down quickly)',
            'texture_distribution': 'uniform pieces, good for sauces',
            'best_for': 'sauces, salsas, soups',
            'example_dishes': 'Pico de gallo, bruschetta, tomato sauce'
        },
        {
            'prep_method': 'Crushed',
            'surface_area_ratio': 20.0,
            'flavor_intensity': 'intense',
            'enzyme_exposure': 'maximum',
            'compounds_released': 'extensive cell damage, immediate flavor release, enzymes fully active',
            'cooking_time_impact': 'very fast (breaks down immediately)',
            'texture_distribution': 'rustic, chunky texture',
            'best_for': 'quick sauces, marinara base, rustic preparations',
            'example_dishes': 'Quick marinara, pizza sauce, arrabbiata'
        },
    ]

    count = 0
    for prep in prep_methods:
        try:
            cursor.execute("""
                INSERT INTO prep_method_effects (
                    ingredient_id, prep_method,
                    surface_area_ratio, flavor_intensity, enzyme_exposure,
                    compounds_released, cooking_time_impact, texture_distribution,
                    best_for, example_dishes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ingredient_id, prep['prep_method'],
                prep['surface_area_ratio'], prep['flavor_intensity'], prep['enzyme_exposure'],
                prep['compounds_released'], prep['cooking_time_impact'], prep['texture_distribution'],
                prep['best_for'], prep['example_dishes']
            ))
            print(f"    [OK] Prep: {prep['prep_method']}")
            count += 1
        except sqlite3.IntegrityError:
            print(f"    [SKIP] Prep: {prep['prep_method']} already exists")

    return count

def seed_garlic_profiles(cursor):
    """Seed cooking profiles for garlic."""
    print("\n  Garlic:")
    ingredient_id = get_ingredient_id(cursor, "Garlic")
    if not ingredient_id:
        print("    [ERROR] Garlic not found in database")
        return 0

    # Update base ingredient profile
    cursor.execute("""
        UPDATE ingredients SET
            base_flavor_profile = ?,
            base_texture = ?,
            key_flavor_compounds = ?,
            enzyme_systems = ?
        WHERE id = ?
    """, (
        "pungent, sulfurous, sharp (raw), becomes sweet and mellow when cooked",
        "firm, crisp, low moisture",
        "alliin (precursor), allicin (formed when crushed), diallyl disulfide, sulfur compounds",
        "alliinase (converts alliin to allicin when cells are damaged)",
        ingredient_id
    ))

    profiles = [
        # Roast (whole cloves)
        {
            'method': 'Roast',
            'process': 'Roasting',
            'flavor_before': 'pungent, sharp, sulfurous',
            'flavor_after': 'sweet, nutty, caramelized, mellow, buttery',
            'flavor_compounds': 'Sulfur compounds break down, sugars caramelize, new nutty compounds form',
            'flavor_intensity': '5x pungent → 1x sweet',
            'texture_before': 'firm, crisp',
            'texture_after': 'soft, spreadable, creamy paste',
            'water_activity': '0.65 → 0.55',
            'cell_structure': 'Cells soften completely, starches convert to sugars',
            'reactions': 'Allicin breakdown (heat deactivates alliinase), Maillard reaction, caramelization',
            'enzymes_activated': None,
            'enzymes_deactivated': 'alliinase (>150°F)',
            'optimal_temp': 375,
            'optimal_duration': 35,
            'technique': 'Roast whole head, cut top off, drizzle olive oil, wrap in foil. 35-40 min.',
            'scientific_notes': 'Heat (>150°F) deactivates alliinase, preventing allicin formation. Sulfur compounds break down. Sugars caramelize. Texture becomes paste-like from starch conversion.',
            'chef_tips': 'Roasted garlic loses pungency completely. Great for spreading on bread or mixing into mashed potatoes. Can roast at 375°F for 30-40 min.'
        },
        # Sauté (whole cloves)
        {
            'method': 'Sauté',
            'process': 'Sautéing',
            'flavor_before': 'pungent (if crushed beforehand), mild (if whole)',
            'flavor_after': 'sweet, slightly nutty, golden, mellow',
            'flavor_compounds': 'Maillard browning, partial sulfur breakdown',
            'flavor_intensity': '3x → 1.5x',
            'texture_before': 'firm',
            'texture_after': 'softened, golden',
            'water_activity': '0.65 → 0.60',
            'cell_structure': 'Softened, slight browning',
            'reactions': 'Maillard reaction, alliinase deactivation, sugar caramelization',
            'enzymes_activated': None,
            'enzymes_deactivated': 'alliinase',
            'optimal_temp': 300,
            'optimal_duration': 3,
            'technique': 'Sliced/smashed garlic, medium heat, cook until golden (not brown). Remove if browning too fast.',
            'scientific_notes': 'Garlic burns easily (high sugar content). Overcooked garlic tastes bitter. Cook at lower temp than onions.',
            'chef_tips': 'Add garlic AFTER onions (cooks faster). If burning, add splash of water to cool pan. Golden = sweet, brown = bitter.'
        },
    ]

    count = 0
    for profile in profiles:
        method_id = get_cooking_method_id(cursor, profile['method'])
        process_id = get_process_id(cursor, profile['process'])

        try:
            cursor.execute("""
                INSERT INTO ingredient_cooking_profiles (
                    ingredient_id, cooking_method_id, process_id,
                    flavor_before, flavor_after, flavor_compounds_formed, flavor_intensity_change,
                    texture_before, texture_after, water_activity_change, cell_structure_change,
                    primary_reactions, enzymes_activated, enzymes_deactivated,
                    optimal_temp_f, optimal_duration_min, recommended_technique,
                    scientific_notes, chef_tips
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ingredient_id, method_id, process_id,
                profile['flavor_before'], profile['flavor_after'], profile['flavor_compounds'], profile['flavor_intensity'],
                profile['texture_before'], profile['texture_after'], profile['water_activity'], profile['cell_structure'],
                profile['reactions'], profile['enzymes_activated'], profile['enzymes_deactivated'],
                profile['optimal_temp'], profile['optimal_duration'], profile['technique'],
                profile['scientific_notes'], profile['chef_tips']
            ))
            print(f"    [OK] {profile['method']}")
            count += 1
        except sqlite3.IntegrityError:
            print(f"    [SKIP] {profile['method']} already exists")

    return count

def seed_garlic_prep_methods(cursor):
    """Seed prep method variations for garlic (THIS IS THE KEY DIFFERENTIATOR)."""
    ingredient_id = get_ingredient_id(cursor, "Garlic")
    if not ingredient_id:
        return 0

    prep_methods = [
        {
            'prep_method': 'Whole',
            'surface_area_ratio': 1.0,
            'flavor_intensity': 'very mild',
            'enzyme_exposure': 'none (cells intact)',
            'compounds_released': 'minimal - no allicin unless cells damaged',
            'cooking_time_impact': 'very slow',
            'texture_distribution': 'intact clove',
            'best_for': 'roasting, infusing oils, mild garlic essence',
            'example_dishes': 'roasted garlic, garlic confit, 40-clove chicken, infused olive oil'
        },
        {
            'prep_method': 'Sliced',
            'surface_area_ratio': 3.0,
            'flavor_intensity': 'mild',
            'enzyme_exposure': 'minimal (few cut surfaces)',
            'compounds_released': 'low allicin production, gentle garlic flavor',
            'cooking_time_impact': 'slower',
            'texture_distribution': 'visible slices, even distribution',
            'best_for': 'stir-fries, garnish, visible pieces, moderate garlic flavor',
            'example_dishes': 'aglio e olio, stir-fry dishes, garlic chips'
        },
        {
            'prep_method': 'Minced',
            'surface_area_ratio': 15.0,
            'flavor_intensity': 'medium-strong',
            'enzyme_exposure': 'high (many cut surfaces)',
            'compounds_released': 'significant allicin production (alliinase enzyme activated)',
            'cooking_time_impact': 'fast',
            'texture_distribution': 'fine pieces, distributed throughout',
            'best_for': 'sauces, sautés, most cooking applications',
            'example_dishes': 'garlic bread, pasta sauces, marinades, stir-fries'
        },
        {
            'prep_method': 'Crushed',
            'surface_area_ratio': 50.0,
            'flavor_intensity': 'very intense',
            'enzyme_exposure': 'maximum (cells completely ruptured)',
            'compounds_released': 'maximum allicin production (3-5x more than mincing)',
            'cooking_time_impact': 'very fast',
            'texture_distribution': 'paste-like, intense flavor concentration',
            'best_for': 'raw applications, aioli, marinades, maximum flavor impact',
            'example_dishes': 'aioli, garlic mayo, hummus, raw dressings, Caesar dressing'
        },
    ]

    count = 0
    for prep in prep_methods:
        try:
            cursor.execute("""
                INSERT INTO prep_method_effects (
                    ingredient_id, prep_method,
                    surface_area_ratio, flavor_intensity, enzyme_exposure,
                    compounds_released, cooking_time_impact, texture_distribution,
                    best_for, example_dishes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ingredient_id, prep['prep_method'],
                prep['surface_area_ratio'], prep['flavor_intensity'], prep['enzyme_exposure'],
                prep['compounds_released'], prep['cooking_time_impact'], prep['texture_distribution'],
                prep['best_for'], prep['example_dishes']
            ))
            print(f"    [OK] Prep: {prep['prep_method']}")
            count += 1
        except sqlite3.IntegrityError:
            print(f"    [SKIP] Prep: {prep['prep_method']} already exists")

    return count

def seed_all():
    """Seed all Priority 1 ingredient profiles."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Seeding Priority 1 Ingredient Cooking Profiles...")
    print("=" * 60)

    total_cooking = 0
    total_prep = 0

    # Tomatoes
    total_cooking += seed_tomato_profiles(cursor)
    total_prep += seed_tomato_prep_methods(cursor)

    # Garlic
    total_cooking += seed_garlic_profiles(cursor)
    total_prep += seed_garlic_prep_methods(cursor)

    # Commit and close
    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print(f"[SUCCESS] Seeded {total_cooking} cooking profiles")
    print(f"[SUCCESS] Seeded {total_prep} prep method variations")
    print("\nVerify with:")
    print("  SELECT i.name, cm.method_name, icp.flavor_intensity_change")
    print("  FROM ingredient_cooking_profiles icp")
    print("  JOIN ingredients i ON i.id = icp.ingredient_id")
    print("  JOIN cooking_methods cm ON cm.id = icp.cooking_method_id;")

if __name__ == '__main__':
    seed_all()
