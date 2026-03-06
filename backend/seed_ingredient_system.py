"""
Seed data for the Ingredient Transformation System (Molecular Gastronomy)

This script populates:
- Botanical families (scientific plant classification)
- Transformation processes (chemistry of cooking)
- Equipment capabilities (instant pot, air fryer, oven presets)
- Ingredient preparations (wheat → flour, bread, pasta, etc.)
- Fermentation protocols (yogurt, kimchi, kombucha, skyr, ACV)
- Links existing ingredients to botanical families

Usage:
    python seed_ingredient_system.py
"""

import sqlite3
from datetime import datetime

# Database path
DB_PATH = "food.db"


def seed_botanical_families(conn):
    """Seed 15+ botanical families for diversity tracking."""
    print("Seeding botanical families...")

    families = [
        # Grains & Grasses
        ('Poaceae', 'Grasses (Grains)', 'Fiber, B vitamins, silicon, resistant starch', 'Butyrate production, fiber fermentation, SCFA synthesis', '🌾'),

        # Vegetables
        ('Brassicaceae', 'Crucifers (Cabbage family)', 'Glucosinolates, sulforaphane, isothiocyanates', 'Detoxification, anti-inflammatory, cancer prevention', '🥦'),
        ('Solanaceae', 'Nightshades', 'Alkaloids, lycopene, capsaicin, vitamin C', 'Antioxidants, anti-inflammatory, cardiovascular health', '🍅'),
        ('Apiaceae', 'Umbrellifers (Carrot family)', 'Terpenes, coumarins, polyacetylenes, fiber', 'Digestive support, anti-inflammatory, prebiotic', '🥕'),
        ('Cucurbitaceae', 'Gourds (Squash family)', 'Cucurbitacins, carotenoids, high water content', 'Hydration, fiber, anti-inflammatory, antioxidants', '🥒'),
        ('Amaranthaceae', 'Amaranths (Beet family)', 'Complete proteins, minerals, betacyanins, betalains', 'Protein diversity, mineral absorption, antioxidants', '🌿'),
        ('Allium', 'Onion family', 'Organosulfur compounds, prebiotics, quercetin', 'Immune support, gut health, cardiovascular health', '🧅'),

        # Legumes
        ('Fabaceae', 'Legumes (Bean family)', 'Protein, resistant starch, phytates, isoflavones', 'SCFA production, protein diversity, cholesterol reduction', '🫘'),

        # Fruits
        ('Rosaceae', 'Rose family', 'Polyphenols, pectin, vitamin C, quercetin', 'Prebiotic fiber, antioxidants, cardiovascular health', '🍓'),
        ('Rutaceae', 'Citrus family', 'Vitamin C, flavonoids, limonene, hesperidin', 'Antioxidants, immune support, anti-inflammatory', '🍊'),
        ('Musaceae', 'Banana family', 'Resistant starch, potassium, prebiotics, vitamin B6', 'Digestive health, SCFA production, electrolyte balance', '🍌'),

        # Nuts & Seeds
        ('Juglandaceae', 'Walnut family', 'Omega-3 ALA, polyphenols, minerals, vitamin E', 'Brain health, anti-inflammatory, cardiovascular support', '🥜'),

        # Fungi (not plants, but important for diversity)
        ('Agaricaceae', 'Button mushroom family', 'Beta-glucans, ergothioneine, vitamin D precursors', 'Immune modulation, antioxidants, prebiotic fiber', '🍄'),

        # Herbs & Spices
        ('Lamiaceae', 'Mint family', 'Terpenes, polyphenols, rosmarinic acid', 'Anti-inflammatory, antioxidants, digestive support', '🌿'),
        ('Zingiberaceae', 'Ginger family', 'Gingerols, curcumin, volatile oils', 'Anti-inflammatory, digestive support, antioxidants', '🫚'),
    ]

    cursor = conn.cursor()
    for family in families:
        cursor.execute("""
            INSERT OR IGNORE INTO botanical_families
            (family_name, common_name, typical_compounds, microbiome_benefits, icon)
            VALUES (?, ?, ?, ?, ?)
        """, family)

    conn.commit()
    print(f"[OK] Inserted {len(families)} botanical families")


def seed_transformation_processes(conn):
    """Seed transformation processes with chemistry explanations."""
    print("Seeding transformation processes...")

    processes = [
        # Fermentation
        (
            'Lactic Acid Fermentation',
            'fermentation',
            95, 115, 110,  # temp_min, max, optimal (°F)
            6.0, 12.0,     # duration_min, max (hours)
            6.5, 4.5,      # pH start, end
            'instant-pot',
            'Lactose → Lactic acid + CO2 (Lactobacillus)',
            'Lactobacillus bulgaricus, Streptococcus thermophilus',
            'Bacteria convert lactose to lactic acid through glycolysis, lowering pH which denatures milk proteins (casein), creating thick texture. Acetaldehyde and diacetyl produce tangy flavor.',
            'Bacteria eat the sugar in milk and make it thick and tangy',
            'Lactobacillus ferments lactose via Embden-Meyerhof pathway: C12H22O11 + H2O → 4 CH3CH(OH)COOH. pH 6.5→4.5 denatures casein micelles at isoelectric point (pH 4.6), causing coagulation.'
        ),

        # Baking
        (
            'Bread Baking (Maillard + Gelatinization)',
            'baking',
            350, 475, 425,  # temp range
            0.5, 2.0,       # duration range
            6.0, 5.5,       # pH (slight drop from fermentation)
            'oven',
            'Maillard reaction: Reducing sugars + amino acids → melanoidins (browning). Starch gelatinization at 185°F',
            'Saccharomyces cerevisiae (yeast)',
            'At 300°F+, Maillard reaction browns crust. At 185°F, starch granules absorb water and gelatinize. Yeast CO2 creates air pockets. Gluten network (gliadin + glutenin) provides structure.',
            'Heat makes dough rise and turn golden brown. The inside becomes soft and fluffy',
            'Maillard: R-NH2 + R-CHO → Schiff base → Amadori product → melanoidins. Starch gelatinization: amylose leaches at 85°C. Gluten: disulfide bonds cross-link glutenin polymers.'
        ),

        # Dehydration
        (
            'Low-Temperature Dehydration',
            'dehydration',
            140, 165, 155,
            3.0, 8.0,
            None, None,     # pH doesn't change significantly
            'air-fryer',
            'Water evaporation concentrates flavors and preserves via low water activity (aw)',
            None,
            'Low heat removes moisture without destroying nutrients. Water activity below 0.6 prevents microbial growth. Enzymes remain active, so blanching may be needed.',
            'Gentle heat dries food slowly to keep flavors concentrated',
            'Evaporation rate depends on vapor pressure gradient. Target aw < 0.6 for shelf stability. Maillard reaction minimal at <165°F.'
        ),

        # Pressure Cooking
        (
            'High-Pressure Extraction',
            'pressure-cooking',
            240, 250, 250,
            1.0, 4.0,
            None, None,
            'instant-pot',
            'Pressure raises boiling point to 250°F, extracting collagen → gelatin',
            None,
            'At 15 PSI, water boils at 250°F instead of 212°F. Higher temp breaks down collagen (triple helix) into gelatin (random coil), creating rich broth. Extracts minerals from bones.',
            'High pressure and heat make tough meat tender and pull nutrients from bones',
            'Pressure-temp relationship: Clausius-Clapeyron equation. Collagen (Gly-X-Y)n denatures at 160-180°F under pressure, hydrolyzing to gelatin.'
        ),

        # Congee/Porridge
        (
            'Starch Gelatinization (Congee)',
            'boiling',
            200, 212, 212,
            0.25, 1.0,
            None, None,
            'instant-pot',
            'Starch granules absorb water, swell, and gelatinize at 185°F+',
            None,
            'Starch granules swell as amylose leaches out, creating creamy texture. Long cooking breaks down grain structure. High water ratio (1:6+) creates porridge consistency.',
            'Grains absorb lots of water and become soft and creamy',
            'Amylose (α-1,4-glycosidic bonds) leaches at 85°C. Amylopectin swells but remains in granule. Continued heating breaks down granules → viscous sol.'
        ),

        # Black Garlic
        (
            'Enzymatic Browning (Black Garlic)',
            'fermentation',
            135, 145, 140,
            240.0, 336.0,  # 10-14 days
            6.0, 4.0,
            'instant-pot',
            'Alliin → Allicin → S-allyl cysteine. Maillard reaction without microbes',
            None,
            'Heat and humidity trigger enzymes (alliinase) and Maillard reactions over 10-14 days. Sugars caramelize, proteins denature. Result: sweet, umami, black cloves.',
            'Garlic slowly cooks for 2 weeks, turning black and sweet',
            'Alliinase converts alliin to allicin at 60°C. Prolonged heat + humidity → Maillard (amino acids + reducing sugars) and caramelization. pH drops from 6.0 to 4.0.'
        ),

        # Kimchi Fermentation
        (
            'Wild Lacto-Fermentation (Kimchi)',
            'fermentation',
            55, 75, 65,
            72.0, 168.0,   # 3-7 days
            6.5, 3.5,
            None,
            'Sugars → Lactic acid + CO2 (wild fermentation with salt brine)',
            'Lactobacillus plantarum, Leuconostoc mesenteroides',
            'Salt brine (2-3%) creates anaerobic environment. LAB (lactic acid bacteria) ferment sugars, producing lactic acid, CO2, and flavor compounds. pH drops prevent spoilage.',
            'Salt and bacteria preserve cabbage, making it tangy and probiotic-rich',
            'Heterofermentative: Glucose → Lactate + Ethanol + CO2. Homofermentative: Glucose → 2 Lactate. Brine salinity 2-3% selects for halotolerant LAB. pH 6.5→3.5.'
        ),

        # Kombucha
        (
            'Symbiotic Fermentation (Kombucha)',
            'fermentation',
            68, 85, 75,
            168.0, 336.0,  # 7-14 days
            4.5, 2.5,
            None,
            'Sucrose → Ethanol + Acetic acid + CO2 + Gluconic acid (SCOBY)',
            'Saccharomyces cerevisiae, Acetobacter aceti, Gluconacetobacter kombuchae',
            'SCOBY (Symbiotic Culture of Bacteria and Yeast) ferments sweet tea. Yeast converts sugar to ethanol. Bacteria oxidize ethanol to acetic acid. Creates tangy, slightly fizzy drink.',
            'Bacteria and yeast team up to turn sweet tea into tangy probiotic drink',
            'Two-stage: (1) Yeast: C12H22O11 → 4 C2H5OH + 4 CO2. (2) Bacteria: C2H5OH + O2 → CH3COOH + H2O. Cellulose pellicle forms at air interface. pH 4.5→2.5.'
        ),

        # Sourdough Fermentation
        (
            'Sourdough Fermentation',
            'fermentation',
            70, 85, 78,
            8.0, 24.0,
            6.0, 4.5,
            None,
            'Wild yeast + LAB ferment flour, producing CO2 (rise) and acids (flavor)',
            'Wild Saccharomyces, Lactobacillus sanfranciscensis',
            'Wild yeast produces CO2 for rise. LAB produces lactic and acetic acid for sour flavor. Long fermentation breaks down phytates, improving digestibility.',
            'Wild yeast and bacteria make dough rise slowly and develop tangy flavor',
            'Yeast: C6H12O6 → 2 C2H5OH + 2 CO2. LAB: C6H12O6 → 2 CH3CH(OH)COOH. Ratio lactic:acetic affects sourness. Amylase breaks starch to maltose.'
        ),

        # Skyr
        (
            'Skyr Fermentation (Icelandic)',
            'fermentation',
            95, 105, 100,
            12.0, 24.0,
            6.5, 4.3,
            'instant-pot',
            'Ultra-thick yogurt: Lactose → Lactic acid + rennet coagulation',
            'Streptococcus thermophilus, Lactobacillus delbrueckii subsp. bulgaricus',
            'Similar to yogurt but uses rennet and strains whey, creating ultra-thick texture. Higher protein concentration. Traditional Icelandic cultures.',
            'Icelandic yogurt culture makes extra-thick, high-protein yogurt',
            'Rennet (chymosin) cleaves κ-casein, destabilizing micelles. Acid coagulation at pH 4.6. Whey removed → concentrated protein (casein + whey).'
        ),

        # ACV
        (
            'Apple Cider Vinegar Fermentation',
            'fermentation',
            60, 80, 70,
            672.0, 1008.0, # 4-6 weeks
            3.5, 2.5,
            None,
            'Apples → Alcohol (yeast) → Acetic acid (bacteria)',
            'Saccharomyces cerevisiae, Acetobacter aceti',
            'Two-stage: (1) Yeast ferments apple sugars to alcohol (~5-7%). (2) Acetobacter oxidizes ethanol to acetic acid. "Mother" (cellulose + bacteria) forms.',
            'Yeast turns apple juice to alcohol, then bacteria turn it to vinegar',
            'Stage 1: C6H12O6 → 2 C2H5OH + 2 CO2. Stage 2: C2H5OH + O2 → CH3COOH + H2O. Target acidity: 4-5% acetic acid. Mother = Acetobacter + cellulose biofilm.'
        ),
    ]

    cursor = conn.cursor()
    for process in processes:
        cursor.execute("""
            INSERT OR IGNORE INTO transformation_processes
            (process_name, process_type, temp_min_f, temp_max_f, temp_optimal_f,
             duration_min_hours, duration_max_hours, ph_start, ph_end,
             required_equipment_category, chemical_reactions, microorganisms,
             chemistry_explanation, beginner_explanation, expert_explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, process)

    conn.commit()
    print(f"[OK] Inserted {len(processes)} transformation processes")


def seed_equipment_capabilities(conn):
    """Seed equipment capabilities with presets."""
    print("Seeding equipment capabilities...")

    # First get process IDs
    cursor = conn.cursor()
    cursor.execute("SELECT id, process_name FROM transformation_processes")
    process_map = {name: id for id, name in cursor.fetchall()}

    capabilities = [
        # Instant Pot
        ('instant-pot', 'Yogurt fermentation', 'Yogurt', 110, 8.0, process_map.get('Lactic Acid Fermentation'), 95),
        ('instant-pot', 'Rice congee', 'Porridge', 212, 0.33, process_map.get('Starch Gelatinization (Congee)'), 98),
        ('instant-pot', 'Oat congee', 'Porridge', 212, 0.25, process_map.get('Starch Gelatinization (Congee)'), 98),
        ('instant-pot', 'Quinoa congee', 'Porridge', 212, 0.25, process_map.get('Starch Gelatinization (Congee)'), 95),
        ('instant-pot', 'Black garlic fermentation', 'Keep Warm', 140, 336.0, process_map.get('Enzymatic Browning (Black Garlic)'), 85),
        ('instant-pot', 'Bone broth extraction', 'High Pressure', 250, 3.0, process_map.get('High-Pressure Extraction'), 92),
        ('instant-pot', 'Steel-cut oat porridge', 'Porridge', 212, 0.33, process_map.get('Starch Gelatinization (Congee)'), 98),
        ('instant-pot', 'Barley congee', 'Porridge', 212, 0.5, process_map.get('Starch Gelatinization (Congee)'), 95),
        ('instant-pot', 'Millet porridge', 'Porridge', 212, 0.25, process_map.get('Starch Gelatinization (Congee)'), 95),
        ('instant-pot', 'Brown rice congee', 'Porridge', 212, 0.67, process_map.get('Starch Gelatinization (Congee)'), 95),
        ('instant-pot', 'Skyr fermentation', 'Yogurt', 100, 12.0, process_map.get('Skyr Fermentation (Icelandic)'), 90),

        # Air Fryer
        ('air-fryer', 'Beef jerky dehydration', 'Dehydrate', 160, 4.0, process_map.get('Low-Temperature Dehydration'), 90),
        ('air-fryer', 'Kale chips', 'Air Fry', 375, 0.08, process_map.get('Low-Temperature Dehydration'), 88),
        ('air-fryer', 'Apple chips', 'Dehydrate', 135, 6.0, process_map.get('Low-Temperature Dehydration'), 92),
        ('air-fryer', 'Banana chips', 'Dehydrate', 135, 4.0, process_map.get('Low-Temperature Dehydration'), 90),
        ('air-fryer', 'Sweet potato chips', 'Air Fry', 400, 0.25, process_map.get('Low-Temperature Dehydration'), 93),
        ('air-fryer', 'Dried mushrooms', 'Dehydrate', 125, 6.0, process_map.get('Low-Temperature Dehydration'), 88),
        ('air-fryer', 'Herb drying (basil, oregano)', 'Dehydrate', 95, 4.0, process_map.get('Low-Temperature Dehydration'), 95),

        # Oven
        ('oven', 'Sourdough baking', 'Bake', 450, 0.67, process_map.get('Bread Baking (Maillard + Gelatinization)'), 80),
        ('oven', 'Whole wheat bread', 'Bake', 375, 0.75, process_map.get('Bread Baking (Maillard + Gelatinization)'), 85),
        ('oven', 'Granola toasting', 'Bake', 325, 0.5, process_map.get('Low-Temperature Dehydration'), 95),
        ('oven', 'Roasted vegetables (Maillard)', 'Roast', 425, 0.5, process_map.get('Bread Baking (Maillard + Gelatinization)'), 90),
        ('oven', 'Slow-roasted tomatoes', 'Roast', 275, 3.0, process_map.get('Low-Temperature Dehydration'), 92),
        ('oven', 'Focaccia bread', 'Bake', 425, 0.33, process_map.get('Bread Baking (Maillard + Gelatinization)'), 88),

        # Countertop / No Equipment
        ('countertop', 'Kimchi fermentation', 'Room temp + jar', 65, 120.0, process_map.get('Wild Lacto-Fermentation (Kimchi)'), 85),
        ('countertop', 'Kombucha brewing', 'Room temp + jar', 75, 240.0, process_map.get('Symbiotic Fermentation (Kombucha)'), 80),
        ('countertop', 'Sourdough starter feeding', 'Room temp', 78, 12.0, process_map.get('Sourdough Fermentation'), 90),
        ('countertop', 'Sauerkraut fermentation', 'Room temp + jar', 65, 168.0, process_map.get('Wild Lacto-Fermentation (Kimchi)'), 88),
        ('countertop', 'Apple cider vinegar', 'Room temp + jar', 70, 720.0, process_map.get('Apple Cider Vinegar Fermentation'), 75),
    ]

    for cap in capabilities:
        cursor.execute("""
            INSERT OR IGNORE INTO equipment_capabilities
            (equipment_category, capability_name, preset_name, temp_f, duration_hours, process_id, success_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, cap)

    conn.commit()
    print(f"[OK] Inserted {len(capabilities)} equipment capabilities")


def seed_ingredient_preparations(conn):
    """Seed common ingredient preparations (transformations)."""
    print("Seeding ingredient preparations...")

    # We'll add preparations for common base ingredients
    # Note: base_ingredient_id will need to be updated once we link real ingredients

    preparations = [
        # Wheat transformations (assuming wheat = ingredient id 7 based on earlier exploration)
        (7, 'Whole Wheat Flour', None, None, 364, 13.2, 72.0, 1.9, 12.2),
        (7, 'Whole Wheat Bread', None, None, 247, 13.0, 41.0, 3.5, 6.0),
        (7, 'Whole Wheat Pasta', None, None, 124, 5.0, 26.0, 0.5, 3.5),
        (7, 'Bulgur Wheat', None, None, 342, 12.3, 75.9, 1.3, 12.5),

        # Oat transformations (id 8)
        (8, 'Steel-Cut Oats (cooked)', None, 300, 71, 2.5, 12.0, 1.5, 1.7),
        (8, 'Oat Porridge/Congee', None, 500, 68, 2.4, 12.0, 1.4, 1.7),
        (8, 'Granola (oats + nuts)', None, None, 489, 14.0, 53.0, 24.0, 8.9),
        (8, 'Oat Milk', None, 900, 47, 1.0, 7.0, 1.5, 0.8),

        # Milk transformations (id 12)
        (12, 'Yogurt (plain)', None, None, 61, 3.5, 4.7, 3.3, 0),
        (12, 'Greek Yogurt', None, None, 97, 10.0, 3.6, 5.0, 0),
        (12, 'Skyr', None, None, 63, 11.0, 4.0, 0.2, 0),
        (12, 'Kefir', None, None, 41, 3.3, 4.5, 1.0, 0),
    ]

    cursor = conn.cursor()
    for prep in preparations:
        cursor.execute("""
            INSERT OR IGNORE INTO ingredient_preparations
            (base_ingredient_id, preparation_name, parent_preparation_id, hydration_percent,
             calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, prep)

    conn.commit()
    print(f"[OK] Inserted {len(preparations)} ingredient preparations")


def seed_fermentation_protocols(conn):
    """Seed fermentation protocols with detailed instructions."""
    print("Seeding fermentation protocols...")

    protocols = [
        (
            'Instant Pot Yogurt (Basic)',
            12,  # milk
            'Lactobacillus bulgaricus, Streptococcus thermophilus',
            'Store-bought yogurt with live cultures OR commercial yogurt starter',
            110,  # temp
            4.5,  # pH target
            None,  # no brine for yogurt
            1,    # duration 8-12 hours (stored as days, so 0.5 = 12 hours)
            'Instant Pot with Yogurt function OR any pot that maintains 110°F',
            'Use pasteurized milk. Heat to 180°F to denature whey proteins (optional but creates thicker yogurt). Cool to 110°F before adding starter. Avoid metal spoons (can inhibit bacteria).',
            'L. bulgaricus, S. thermophilus (100M+ CFU/g)'
        ),
        (
            'Greek Yogurt (Strained)',
            12,  # milk
            'Lactobacillus bulgaricus, Streptococcus thermophilus',
            'Regular yogurt starter',
            110,
            4.5,
            None,
            1,  # 8-12 hours + 4 hours straining
            'Instant Pot + Cheesecloth or Greek yogurt strainer',
            'Make regular yogurt, then strain through cheesecloth for 4+ hours to remove whey. Results in 2x protein concentration. Save whey for baking or smoothies.',
            'L. bulgaricus, S. thermophilus'
        ),
        (
            'Kimchi (Napa Cabbage)',
            None,  # cabbage not in our ingredient list yet
            'Lactobacillus plantarum, Leuconostoc mesenteroides (wild fermentation)',
            'Salt brine (natural fermentation)',
            65,
            3.5,
            2.5,  # 2-3% salt brine
            7,    # 3-7 days
            'Glass jar, ceramic crock, or food-safe plastic container',
            'Use non-iodized salt. Keep vegetables submerged under brine. Burp jar daily to release CO2. Refrigerate when sour enough to slow fermentation.',
            'L. plantarum, L. brevis, Weissella (wild LAB)'
        ),
        (
            'Kombucha (Sweet Tea)',
            None,  # tea not in our ingredient list
            'Saccharomyces cerevisiae, Acetobacter aceti, Gluconacetobacter kombuchae',
            'SCOBY (Symbiotic Culture of Bacteria and Yeast) + starter tea',
            75,
            2.5,
            None,
            14,  # 7-14 days
            'Glass jar (no metal), breathable cloth cover',
            'Brew sweet tea (black or green), cool to room temp. Add SCOBY + 1-2 cups starter tea. Cover with cloth. Ferment 7-14 days. Taste daily after day 7. Bottle with fruit for 2nd ferment (carbonation).',
            'S. cerevisiae, A. aceti, G. kombuchae, Zygosaccharomyces'
        ),
        (
            'Skyr (Icelandic Yogurt)',
            12,  # milk
            'Streptococcus thermophilus, Lactobacillus delbrueckii subsp. bulgaricus',
            'Skyr culture OR Icelandic yogurt starter + rennet',
            100,
            4.3,
            None,
            1,  # 12-24 hours
            'Instant Pot + cheesecloth',
            'Heat milk to 195°F (higher than yogurt). Cool to 100°F. Add starter + 2-3 drops rennet. Incubate 12-24 hours. Strain through cheesecloth until ultra-thick. Traditional Icelandic uses skim milk.',
            'S. thermophilus, L. bulgaricus subsp. bulgaricus'
        ),
        (
            'Apple Cider Vinegar (ACV)',
            None,  # apples not in our ingredient list
            'Saccharomyces cerevisiae, Acetobacter aceti',
            'Wild fermentation OR "mother" from unpasteurized ACV',
            70,
            2.5,
            None,
            42,  # 4-6 weeks
            'Glass jar, breathable cloth cover',
            'Chop apples + cores. Cover with water + 1 tbsp sugar per apple. Ferment 2 weeks (alcohol stage). Strain, ferment 2-4 more weeks until vinegary. "Mother" (cellulose film) will form. Save for next batch.',
            'S. cerevisiae, A. aceti, A. pasteurianus'
        ),
        (
            'Sourdough Starter',
            7,  # wheat flour
            'Wild Saccharomyces, Lactobacillus sanfranciscensis',
            'Wild fermentation (flour + water only)',
            78,
            4.5,
            None,
            7,  # 5-7 days to establish, then maintain forever
            'Glass or plastic container (no metal)',
            'Day 1: Mix equal parts flour + water. Days 2-7: Discard half, feed equal parts flour + water daily. Starter is ready when it doubles in 4-8 hours and smells yeasty/tangy. Feed weekly if refrigerated, daily if countertop.',
            'Wild Saccharomyces spp., L. sanfranciscensis, L. brevis'
        ),
        (
            'Sauerkraut (Cabbage)',
            None,  # cabbage
            'Lactobacillus plantarum, Leuconostoc mesenteroides',
            'Salt (2% by weight)',
            65,
            3.5,
            2.0,
            14,  # 1-4 weeks
            'Glass jar or ceramic crock',
            'Shred cabbage, massage with 2% salt until liquid releases. Pack tightly in jar. Keep submerged under brine. Ferment 1-4 weeks. Refrigerate when tangy enough.',
            'L. plantarum, L. brevis, Leuconostoc mesenteroides'
        ),
        (
            'Miso Paste (Soybean)',
            None,  # soybeans
            'Aspergillus oryzae (koji), Lactobacillus, Saccharomyces',
            'Koji (Aspergillus oryzae spores on rice/barley) + salt',
            75,
            5.5,
            12.0,  # 10-15% salt
            180,  # 6-12 months
            'Crock or jar with weight to keep submerged',
            'Cook soybeans, mash. Mix with koji + salt. Pack tightly. Ferment 6-12 months. Long fermentation = darker, stronger flavor. White miso = 3 months, red miso = 1+ year.',
            'A. oryzae (koji), L. plantarum, S. rouxii, Tetragenococcus'
        ),
    ]

    cursor = conn.cursor()
    for protocol in protocols:
        cursor.execute("""
            INSERT OR IGNORE INTO fermentation_protocols
            (protocol_name, base_ingredient_id, microorganism_species, culture_source,
             temp_optimal_f, ph_target, brine_salinity_percent, duration_days,
             container_requirements, safety_notes, probiotic_species)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, protocol)

    conn.commit()
    print(f"[OK] Inserted {len(protocols)} fermentation protocols")


def link_ingredients_to_families(conn):
    """Link existing ingredients to botanical families."""
    print("Linking existing ingredients to botanical families...")

    cursor = conn.cursor()

    # Get family IDs
    cursor.execute("SELECT id, family_name FROM botanical_families")
    family_map = {name: id for id, name in cursor.fetchall()}

    # Define ingredient→family mappings
    # These are educated guesses based on common ingredients
    # Format: (ingredient_name_pattern, family_id, genus, species, plant_part)
    mappings = [
        # Grains (Poaceae)
        ('rice', family_map.get('Poaceae'), 'Oryza', 'sativa', 'seed'),
        ('oat', family_map.get('Poaceae'), 'Avena', 'sativa', 'seed'),
        ('wheat', family_map.get('Poaceae'), 'Triticum', 'aestivum', 'seed'),
        ('barley', family_map.get('Poaceae'), 'Hordeum', 'vulgare', 'seed'),
        ('corn', family_map.get('Poaceae'), 'Zea', 'mays', 'seed'),
        ('quinoa', family_map.get('Amaranthaceae'), 'Chenopodium', 'quinoa', 'seed'),

        # Brassicas
        ('broccoli', family_map.get('Brassicaceae'), 'Brassica', 'oleracea var. italica', 'flower'),
        ('cabbage', family_map.get('Brassicaceae'), 'Brassica', 'oleracea var. capitata', 'leaf'),
        ('kale', family_map.get('Brassicaceae'), 'Brassica', 'oleracea var. sabellica', 'leaf'),

        # Nightshades
        ('tomato', family_map.get('Solanaceae'), 'Solanum', 'lycopersicum', 'fruit'),
        ('potato', family_map.get('Solanaceae'), 'Solanum', 'tuberosum', 'tuber'),
        ('pepper', family_map.get('Solanaceae'), 'Capsicum', 'annuum', 'fruit'),

        # Legumes
        ('chickpea', family_map.get('Fabaceae'), 'Cicer', 'arietinum', 'seed'),
        ('lentil', family_map.get('Fabaceae'), 'Lens', 'culinaris', 'seed'),
        ('bean', family_map.get('Fabaceae'), 'Phaseolus', 'vulgaris', 'seed'),
        ('soy', family_map.get('Fabaceae'), 'Glycine', 'max', 'seed'),

        # Alliums
        ('onion', family_map.get('Allium'), 'Allium', 'cepa', 'bulb'),
        ('garlic', family_map.get('Allium'), 'Allium', 'sativum', 'bulb'),
        ('leek', family_map.get('Allium'), 'Allium', 'ampeloprasum', 'leaf'),

        # Apiaceae (carrots, celery, etc.)
        ('carrot', family_map.get('Apiaceae'), 'Daucus', 'carota', 'root'),
        ('celery', family_map.get('Apiaceae'), 'Apium', 'graveolens', 'stalk'),

        # Cucurbits
        ('cucumber', family_map.get('Cucurbitaceae'), 'Cucumis', 'sativus', 'fruit'),
        ('zucchini', family_map.get('Cucurbitaceae'), 'Cucurbita', 'pepo', 'fruit'),
        ('pumpkin', family_map.get('Cucurbitaceae'), 'Cucurbita', 'pepo', 'fruit'),

        # Rosaceae (berries, stone fruits)
        ('strawberry', family_map.get('Rosaceae'), 'Fragaria', 'ananassa', 'fruit'),
        ('apple', family_map.get('Rosaceae'), 'Malus', 'domestica', 'fruit'),

        # Citrus
        ('orange', family_map.get('Rutaceae'), 'Citrus', 'sinensis', 'fruit'),
        ('lemon', family_map.get('Rutaceae'), 'Citrus', 'limon', 'fruit'),

        # Bananas
        ('banana', family_map.get('Musaceae'), 'Musa', 'acuminata', 'fruit'),

        # Fungi
        ('mushroom', family_map.get('Agaricaceae'), 'Agaricus', 'bisporus', 'fruiting body'),

        # Lamiaceae (herbs)
        ('basil', family_map.get('Lamiaceae'), 'Ocimum', 'basilicum', 'leaf'),
        ('mint', family_map.get('Lamiaceae'), 'Mentha', 'spicata', 'leaf'),
        ('oregano', family_map.get('Lamiaceae'), 'Origanum', 'vulgare', 'leaf'),

        # Ginger family
        ('ginger', family_map.get('Zingiberaceae'), 'Zingiber', 'officinale', 'rhizome'),
        ('turmeric', family_map.get('Zingiberaceae'), 'Curcuma', 'longa', 'rhizome'),
    ]

    # Get all ingredients
    cursor.execute("SELECT id, name FROM ingredients")
    ingredients = cursor.fetchall()

    links_created = 0
    for ing_id, ing_name in ingredients:
        ing_name_lower = ing_name.lower()

        # Find matching family
        for pattern, family_id, genus, species, plant_part in mappings:
            if pattern in ing_name_lower:
                cursor.execute("""
                    INSERT OR IGNORE INTO ingredient_botanical_classification
                    (ingredient_id, family_id, genus, species, plant_part)
                    VALUES (?, ?, ?, ?, ?)
                """, (ing_id, family_id, genus, species, plant_part))
                links_created += 1
                break  # Only link to one family per ingredient

    conn.commit()
    print(f"[OK] Linked {links_created} ingredients to botanical families")


def main():
    """Main seed function."""
    print("\n" + "="*60)
    print("SEEDING INGREDIENT TRANSFORMATION SYSTEM")
    print("="*60 + "\n")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    try:
        # Seed all data
        seed_botanical_families(conn)
        seed_transformation_processes(conn)
        seed_equipment_capabilities(conn)
        seed_ingredient_preparations(conn)
        seed_fermentation_protocols(conn)
        link_ingredients_to_families(conn)

        print("\n" + "="*60)
        print("[SUCCESS] SEEDING COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Restart Flask app to load new tables")
        print("2. Check /api/equipment/instant-pot/capabilities")
        print("3. Check /api/diversity/weekly")
        print("4. Visit /diversity-dashboard to see botanical families")
        print("\n")

    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
