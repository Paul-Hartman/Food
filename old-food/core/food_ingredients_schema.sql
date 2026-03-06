-- Food Ingredients Database Schema
--
-- Comprehensive food ingredient database integrating:
-- - Scientific data (USDA nutrition, FlavorDB molecules, texture science)
-- - Traditional medicine (TCM, Ayurveda)
-- - Mystical properties (witchcraft correspondences)
-- - Chemical transformations (Maillard, caramelization, fermentation)
-- - Sensory perception (TRP receptors, taste receptors)
--
-- Author: Paul + Claude
-- Date: 2025-11-20

-- Schema version
CREATE TABLE IF NOT EXISTS food_schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO food_schema_version (version) VALUES (1);

-- =============================================================================
-- CORE INGREDIENTS
-- =============================================================================

-- Base ingredient data
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    scientific_name TEXT,  -- Allium sativum for garlic
    common_names TEXT,  -- JSON array of names in different languages
    category TEXT NOT NULL,  -- vegetable, fruit, protein, grain, dairy, spice, herb, etc.
    subcategory TEXT,  -- allium, nightshade, legume, etc.

    -- Basic properties
    description TEXT,
    origin_region TEXT,  -- Where it's traditionally from
    seasonality TEXT,  -- Spring, summer, fall, winter, year-round

    -- Availability and storage
    shelf_life_days INTEGER,  -- How long it lasts
    storage_method TEXT,  -- Refrigerate, room temp, freeze

    -- External IDs for data sources
    usda_fdc_id TEXT,  -- USDA FoodData Central ID
    flavordb_id TEXT,  -- FlavorDB ID

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ingredients_name (name),
    INDEX idx_ingredients_category (category),
    INDEX idx_ingredients_usda (usda_fdc_id)
);

-- =============================================================================
-- NUTRITIONAL PROPERTIES (USDA FoodData Central)
-- =============================================================================

-- Complete nutritional profile per 100g
CREATE TABLE IF NOT EXISTS nutritional_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL UNIQUE,

    -- Energy
    calories_kcal REAL,  -- Energy in kcal
    kilojoules_kj REAL,  -- Energy in kJ

    -- Macronutrients (grams)
    protein_g REAL,
    total_fat_g REAL,
    saturated_fat_g REAL,
    monounsaturated_fat_g REAL,
    polyunsaturated_fat_g REAL,
    omega3_g REAL,
    omega6_g REAL,
    trans_fat_g REAL,

    carbohydrate_g REAL,
    fiber_total_g REAL,
    fiber_soluble_g REAL,
    fiber_insoluble_g REAL,
    sugars_total_g REAL,
    starch_g REAL,

    water_g REAL,
    ash_g REAL,  -- Mineral content

    -- Vitamins
    vitamin_a_iu INTEGER,  -- International Units
    vitamin_a_rae_mcg REAL,  -- Retinol Activity Equivalent
    thiamin_b1_mg REAL,
    riboflavin_b2_mg REAL,
    niacin_b3_mg REAL,
    pantothenic_acid_b5_mg REAL,
    vitamin_b6_mg REAL,
    biotin_b7_mcg REAL,
    folate_b9_mcg REAL,
    vitamin_b12_mcg REAL,
    vitamin_c_mg REAL,
    vitamin_d_iu INTEGER,
    vitamin_e_mg REAL,
    vitamin_k_mcg REAL,

    -- Minerals (mg unless noted)
    calcium_mg REAL,
    iron_mg REAL,
    magnesium_mg REAL,
    phosphorus_mg REAL,
    potassium_mg REAL,
    sodium_mg REAL,
    zinc_mg REAL,
    copper_mg REAL,
    manganese_mg REAL,
    selenium_mcg REAL,
    iodine_mcg REAL,
    chromium_mcg REAL,
    molybdenum_mcg REAL,

    -- Amino acids (for proteins)
    amino_acids TEXT,  -- JSON object of amino acid content

    -- Metadata
    data_source TEXT DEFAULT 'USDA',
    measurement_method TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    INDEX idx_nutrition_ingredient (ingredient_id)
);

-- =============================================================================
-- FLAVOR MOLECULES (FlavorDB)
-- =============================================================================

-- Flavor molecule catalog
CREATE TABLE IF NOT EXISTS flavor_molecules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    molecule_name TEXT UNIQUE NOT NULL,
    cas_number TEXT,  -- Chemical Abstracts Service registry number
    pubchem_id TEXT,  -- PubChem compound ID

    -- Chemical properties
    chemical_class TEXT,  -- ester, aldehyde, terpene, pyrazine, etc.
    molecular_formula TEXT,  -- C10H16
    molecular_weight REAL,  -- g/mol

    -- Sensory descriptors
    odor_descriptor TEXT,  -- fruity, floral, nutty, earthy, etc.
    taste_descriptor TEXT,  -- sweet, bitter, umami, etc.

    -- Thresholds
    odor_threshold_ppb REAL,  -- Parts per billion (detection limit)
    taste_threshold_ppm REAL,  -- Parts per million

    -- Physical properties
    volatility TEXT,  -- high, medium, low
    stability TEXT,  -- stable, unstable
    boiling_point_c REAL,

    -- Metadata
    flavordb_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_molecules_name (molecule_name),
    INDEX idx_molecules_class (chemical_class)
);

-- Junction table: which molecules are in which ingredients
CREATE TABLE IF NOT EXISTS ingredient_flavor_molecules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    molecule_id INTEGER NOT NULL,

    -- Concentration
    concentration_ppm REAL,  -- Parts per million
    concentration_category TEXT,  -- trace, low, medium, high

    -- Contribution to overall flavor
    importance_score REAL,  -- 0.0 to 1.0 (how important to the ingredient's flavor)

    -- Conditions
    present_in_raw BOOLEAN DEFAULT 1,
    present_in_cooked BOOLEAN DEFAULT 1,
    heat_sensitive BOOLEAN DEFAULT 0,  -- Does it degrade with heat?

    -- Metadata
    detection_method TEXT,  -- GC-MS, LC-MS, etc.
    source TEXT,  -- FlavorDB, research paper, etc.

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    FOREIGN KEY (molecule_id) REFERENCES flavor_molecules(id),
    UNIQUE(ingredient_id, molecule_id),
    INDEX idx_ingred_mol_ingredient (ingredient_id),
    INDEX idx_ingred_mol_molecule (molecule_id)
);

-- Flavor pairing matrix (ingredients that share molecules)
CREATE TABLE IF NOT EXISTS flavor_pairings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_a_id INTEGER NOT NULL,
    ingredient_b_id INTEGER NOT NULL,

    -- Pairing metrics
    shared_molecules_count INTEGER,  -- How many molecules they share
    pairing_strength REAL,  -- 0.0 to 1.0 (based on shared molecules & importance)

    -- Shared molecules
    shared_molecule_ids TEXT,  -- JSON array of molecule IDs

    -- Culinary validation
    traditional_pairing BOOLEAN DEFAULT 0,  -- Is this a known traditional pairing?
    pairing_examples TEXT,  -- JSON array of dishes that use this pairing

    -- Metadata
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingredient_a_id) REFERENCES ingredients(id),
    FOREIGN KEY (ingredient_b_id) REFERENCES ingredients(id),
    UNIQUE(ingredient_a_id, ingredient_b_id),
    INDEX idx_pairings_a (ingredient_a_id),
    INDEX idx_pairings_b (ingredient_b_id),
    INDEX idx_pairings_strength (pairing_strength)
);

-- =============================================================================
-- TEXTURE PROPERTIES
-- =============================================================================

-- Mechanical and rheological texture properties
CREATE TABLE IF NOT EXISTS texture_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    preparation_state TEXT NOT NULL,  -- raw, blanched, cooked, roasted, etc.

    -- Mechanical properties (Texture Profile Analysis)
    hardness_n REAL,  -- Force to compress (Newtons)
    cohesiveness REAL,  -- 0-1 ratio
    springiness REAL,  -- 0-1 ratio (recovery after compression)
    chewiness_j REAL,  -- Work to chew (Joules)
    adhesiveness_j REAL,  -- Work to pull apart (Joules)
    elasticity REAL,  -- 0-1 ratio

    -- Rheological properties (for liquids/semi-solids)
    viscosity_pas REAL,  -- Pascal-seconds
    yield_stress_pa REAL,  -- Pascal
    elasticity_modulus_pa REAL,  -- Pascal

    -- Descriptive texture
    descriptive_terms TEXT,  -- JSON array: crispy, creamy, crunchy, chewy, tender, tough, smooth, grainy

    -- Acoustic properties
    crispness_db REAL,  -- Sound level during fracture (decibels)
    crunchiness_db REAL,

    -- Mouthfeel
    mouthfeel_terms TEXT,  -- JSON array: oily, astringent, coating, dry, refreshing
    particle_size_mm REAL,  -- Average particle size

    -- Metadata
    measurement_method TEXT,  -- TPA, sensory panel, instrumental
    temperature_c REAL,  -- Temperature during measurement
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    UNIQUE(ingredient_id, preparation_state),
    INDEX idx_texture_ingredient (ingredient_id)
);

-- =============================================================================
-- SENSORY RECEPTORS & PERCEPTION
-- =============================================================================

-- Sensory receptor catalog
CREATE TABLE IF NOT EXISTS sensory_receptors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receptor_name TEXT UNIQUE NOT NULL,
    receptor_type TEXT NOT NULL,  -- TRP channel, taste receptor, etc.

    -- Receptor details
    gene_name TEXT,  -- TRPV1, TRPM8, TAS1R2, etc.
    receptor_family TEXT,  -- TRP, taste, olfactory

    -- Activation
    activators TEXT,  -- JSON array of molecules/stimuli that activate
    threshold REAL,  -- Activation threshold

    -- Sensation
    sensation TEXT,  -- heat, cooling, pain, sweet, bitter, etc.
    perception_description TEXT,  -- What you feel/taste when activated

    -- Amplification
    amplifies_stimulus TEXT,  -- e.g., "cold" for TRPM8, "heat" for TRPV1
    amplification_factor REAL,  -- How much it amplifies (multiplier)

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_receptors_type (receptor_type),
    INDEX idx_receptors_name (receptor_name)
);

-- Which ingredients activate which receptors
CREATE TABLE IF NOT EXISTS ingredient_receptor_activation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    receptor_id INTEGER NOT NULL,

    -- Activation details
    activating_compound TEXT,  -- Specific molecule that activates (capsaicin, menthol, etc.)
    activation_strength REAL,  -- 0.0 to 1.0 (weak to strong activation)
    activation_duration TEXT,  -- immediate, lingering, delayed

    -- Concentration dependency
    min_concentration_ppm REAL,  -- Minimum to activate
    max_effect_concentration_ppm REAL,  -- Plateau of effect

    -- Conditions
    requires_preparation TEXT,  -- crushing, heating, etc.
    temperature_dependent BOOLEAN DEFAULT 0,

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    FOREIGN KEY (receptor_id) REFERENCES sensory_receptors(id),
    UNIQUE(ingredient_id, receptor_id),
    INDEX idx_activation_ingredient (ingredient_id),
    INDEX idx_activation_receptor (receptor_id)
);

-- =============================================================================
-- CHEMICAL PROPERTIES
-- =============================================================================

-- Chemical composition and properties
CREATE TABLE IF NOT EXISTS chemical_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL UNIQUE,

    -- pH and acidity
    ph_value REAL,  -- pH scale 0-14
    acidity_category TEXT,  -- very acidic, acidic, neutral, alkaline, very alkaline

    -- Composition percentages
    water_percent REAL,
    dry_matter_percent REAL,

    -- Protein
    protein_type TEXT,  -- JSON array: gluten, casein, albumin, etc.

    -- Starch
    starch_type TEXT,  -- waxy, normal, high-amylose
    amylose_percent REAL,  -- Amylose content
    amylopectin_percent REAL,  -- Amylopectin content
    gelatinization_temp_c REAL,  -- Starch gelatinization temperature

    -- Fat
    fat_composition TEXT,  -- JSON object with fatty acid profile
    melting_point_c REAL,
    smoke_point_c REAL,  -- For oils/fats

    -- Enzymatic
    enzymes_present TEXT,  -- JSON array: polyphenol oxidase, alliinase, myrosinase, etc.
    enzyme_activity TEXT,  -- high, medium, low, none

    -- Antioxidants
    antioxidant_capacity_orac REAL,  -- ORAC value
    phenolic_compounds TEXT,  -- JSON array
    anthocyanins_mg REAL,  -- For berries, red/purple produce

    -- Pigments
    chlorophyll_content TEXT,  -- For green vegetables
    carotenoid_content TEXT,  -- For orange/yellow produce
    betalain_content TEXT,  -- For beets

    -- Other
    pectin_content_percent REAL,  -- For fruits (gelling)
    capsaicin_shu INTEGER,  -- Scoville Heat Units for chili peppers

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    INDEX idx_chemical_ingredient (ingredient_id)
);

-- =============================================================================
-- TRANSFORMATIONS & COOKING PROCESSES
-- =============================================================================

-- Types of transformations
CREATE TABLE IF NOT EXISTS transformation_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transformation_name TEXT UNIQUE NOT NULL,
    transformation_category TEXT NOT NULL,  -- heat, mechanical, time, chemical

    -- Description
    description TEXT,
    mechanism TEXT,  -- How it works chemically/physically

    -- Conditions required
    requires_heat BOOLEAN DEFAULT 0,
    requires_time BOOLEAN DEFAULT 0,
    requires_mechanical_action BOOLEAN DEFAULT 0,
    requires_chemical_addition BOOLEAN DEFAULT 0,

    -- Examples
    examples TEXT,  -- JSON array of examples

    INDEX idx_trans_types_category (transformation_category)
);

-- Specific transformations for ingredients
CREATE TABLE IF NOT EXISTS ingredient_transformations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    transformation_type_id INTEGER NOT NULL,

    -- State change
    initial_state TEXT NOT NULL,  -- raw, whole, fresh, etc.
    final_state TEXT NOT NULL,  -- cooked, minced, fermented, etc.

    -- Conditions
    temperature_min_c REAL,
    temperature_max_c REAL,
    time_min_minutes REAL,
    time_max_minutes REAL,

    -- Changes in properties
    flavor_change TEXT,  -- Description of flavor change
    texture_change TEXT,  -- Description of texture change
    color_change TEXT,  -- Description of color change
    nutritional_change TEXT,  -- JSON object of nutrient changes

    -- Quantitative changes
    pungency_multiplier REAL,  -- e.g., 3.0 for minced garlic
    sweetness_multiplier REAL,  -- e.g., 5.0 for caramelized onions
    bitterness_multiplier REAL,

    -- Reversibility
    reversible BOOLEAN DEFAULT 0,

    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    FOREIGN KEY (transformation_type_id) REFERENCES transformation_types(id),
    INDEX idx_trans_ingredient (ingredient_id),
    INDEX idx_trans_type (transformation_type_id)
);

-- Specific chemical reactions during cooking
CREATE TABLE IF NOT EXISTS transformation_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reaction_name TEXT UNIQUE NOT NULL,
    reaction_type TEXT NOT NULL,  -- maillard, caramelization, denaturation, oxidation, etc.

    -- Reactants and products
    precursors TEXT,  -- JSON array of chemical precursors
    products TEXT,  -- JSON array of products formed

    -- Conditions
    temperature_range_c TEXT,  -- "140-165" for Maillard
    ph_required TEXT,  -- Optimal pH range
    catalysts TEXT,  -- JSON array of catalysts (enzymes, metals, etc.)

    -- Kinetics
    activation_energy_kj_mol REAL,  -- Arrhenius activation energy
    rate_constant TEXT,  -- Description of rate

    -- Sensory impact
    flavor_compounds_formed TEXT,  -- JSON array of flavor molecules created
    color_formed TEXT,  -- Brown, golden, dark, etc.
    aroma_created TEXT,  -- Description of aromas

    -- Examples
    example_ingredients TEXT,  -- JSON array of ingredients where this occurs

    INDEX idx_reactions_type (reaction_type)
);

-- Preparation method effects (size-dependent)
CREATE TABLE IF NOT EXISTS preparation_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    method_name TEXT NOT NULL,  -- mincing, chopping, crushing, slicing, grating, etc.

    -- Size characteristics
    particle_size_mm REAL,  -- Average resulting particle size
    surface_area_multiplier REAL,  -- Increase in surface area

    -- Chemical effects
    enzyme_activation BOOLEAN DEFAULT 0,  -- Does it activate enzymes?
    enzyme_name TEXT,  -- Which enzyme (alliinase, myrosinase, etc.)

    -- Flavor changes
    pungency_change_multiplier REAL,  -- e.g., 3.0 for minced garlic
    bitterness_change_multiplier REAL,
    aroma_intensity_multiplier REAL,

    -- Time dependency
    optimal_wait_time_minutes REAL,  -- e.g., 10 min for minced garlic to peak
    degradation_time_minutes REAL,  -- When does effect diminish?

    -- Texture impact
    texture_change TEXT,  -- Description of texture change

    -- Example
    culinary_uses TEXT,  -- When to use this preparation

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    UNIQUE(ingredient_id, method_name),
    INDEX idx_prep_ingredient (ingredient_id)
);

-- Time-based transformations (fermentation, aging, ripening)
CREATE TABLE IF NOT EXISTS aging_fermentation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    process_type TEXT NOT NULL,  -- fermentation, aging, ripening, curing

    -- Time parameters
    duration_min_days INTEGER,
    duration_max_days INTEGER,
    optimal_duration_days INTEGER,

    -- Conditions
    temperature_range_c TEXT,  -- "20-25"
    humidity_percent TEXT,  -- "60-70"
    ph_change TEXT,  -- "7.0 -> 4.5"

    -- Microbial involvement
    microorganisms TEXT,  -- JSON array: LAB, yeasts, molds
    culture_required BOOLEAN DEFAULT 0,
    spontaneous_fermentation BOOLEAN DEFAULT 1,

    -- Chemical changes
    compounds_produced TEXT,  -- JSON array: alcohol, lactic acid, CO2, etc.
    compounds_degraded TEXT,  -- JSON array

    -- Sensory changes
    flavor_evolution TEXT,  -- Description
    texture_evolution TEXT,  -- Description
    color_evolution TEXT,  -- Description

    -- Nutritional changes
    probiotic_content TEXT,  -- Added beneficial bacteria
    vitamin_changes TEXT,  -- JSON object
    digestibility_change TEXT,  -- Improved, reduced, unchanged

    -- Examples
    product_examples TEXT,  -- Kimchi, sauerkraut, aged cheese, etc.

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    INDEX idx_aging_ingredient (ingredient_id),
    INDEX idx_aging_process (process_type)
);

-- =============================================================================
-- INGREDIENT COMBINATIONS & REACTIONS
-- =============================================================================

-- Chemical reactions between ingredients
CREATE TABLE IF NOT EXISTS ingredient_combinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_a_id INTEGER NOT NULL,
    ingredient_b_id INTEGER NOT NULL,

    -- Reaction type
    reaction_type TEXT NOT NULL,  -- curdling, emulsion, leavening, browning_enhancement, etc.

    -- Conditions for reaction
    requires_heat BOOLEAN DEFAULT 0,
    temperature_range_c TEXT,
    requires_mixing BOOLEAN DEFAULT 1,
    requires_time BOOLEAN DEFAULT 0,
    time_required_minutes REAL,

    -- Products
    product_description TEXT,  -- What forms
    product_name TEXT,  -- Paneer, mayonnaise, etc.

    -- Mechanism
    chemical_mechanism TEXT,  -- Acid denatures protein, etc.

    -- Sensory result
    texture_result TEXT,
    flavor_result TEXT,
    color_result TEXT,

    -- Examples
    culinary_applications TEXT,  -- JSON array of dishes/uses

    -- Cautions
    warnings TEXT,  -- Don't heat too high, don't add all at once, etc.

    FOREIGN KEY (ingredient_a_id) REFERENCES ingredients(id),
    FOREIGN KEY (ingredient_b_id) REFERENCES ingredients(id),
    UNIQUE(ingredient_a_id, ingredient_b_id, reaction_type),
    INDEX idx_combos_a (ingredient_a_id),
    INDEX idx_combos_b (ingredient_b_id)
);

-- =============================================================================
-- TRADITIONAL MEDICINE PROPERTIES
-- =============================================================================

-- Traditional Chinese Medicine properties
CREATE TABLE IF NOT EXISTS tcm_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL UNIQUE,

    -- Temperature nature
    temperature TEXT NOT NULL,  -- cold, cool, neutral, warm, hot

    -- Moisture
    moisture_effect TEXT,  -- drying, neutral, dampening

    -- Five flavors
    flavors TEXT,  -- JSON array: bitter, sweet, sour, salty, pungent
    primary_flavor TEXT,  -- Main flavor

    -- Meridians entered
    meridians TEXT,  -- JSON array: liver, heart, spleen, lung, kidney, etc.

    -- Yin/Yang
    yin_yang TEXT,  -- yin, yang, neutral

    -- Qi effects
    qi_action TEXT,  -- JSON array: tonifying, moving, descending, ascending

    -- Therapeutic actions
    actions TEXT,  -- JSON array: dispels cold, clears heat, generates fluids, etc.

    -- Indications
    treats TEXT,  -- JSON array of conditions treated

    -- Contraindications
    avoid_in TEXT,  -- JSON array: yin deficiency with heat, pregnancy, etc.

    -- Dosage
    typical_dosage TEXT,  -- Daily amount in grams or culinary use

    -- Notes
    notes TEXT,
    data_source TEXT,  -- Book reference, practitioner, etc.

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    INDEX idx_tcm_ingredient (ingredient_id),
    INDEX idx_tcm_temperature (temperature)
);

-- Ayurvedic properties
CREATE TABLE IF NOT EXISTS ayurvedic_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL UNIQUE,

    -- Dosha effects
    vata_effect TEXT,  -- increases, decreases, neutral
    pitta_effect TEXT,
    kapha_effect TEXT,

    -- Six tastes
    rasa TEXT,  -- JSON array: sweet, sour, salty, pungent, bitter, astringent
    primary_rasa TEXT,

    -- Potency
    virya TEXT,  -- heating or cooling

    -- Post-digestive effect
    vipaka TEXT,  -- sweet, sour, pungent

    -- Qualities (Gunas)
    gunas TEXT,  -- JSON array: heavy, light, hot, cold, oily, dry, smooth, rough, dense, liquid

    -- Therapeutic uses
    therapeutic_actions TEXT,  -- JSON array
    indications TEXT,  -- JSON array of conditions

    -- Contraindications
    contraindications TEXT,  -- JSON array

    -- Dosage and preparation
    preparation_notes TEXT,
    typical_usage TEXT,

    -- Notes
    notes TEXT,
    data_source TEXT,

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    INDEX idx_ayur_ingredient (ingredient_id)
);

-- =============================================================================
-- MYSTICAL PROPERTIES (Tagged separately from scientific data)
-- =============================================================================

-- Witchcraft and magical correspondences
CREATE TABLE IF NOT EXISTS mystical_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL UNIQUE,

    -- ⚠️ IMPORTANT: This is traditional/folkloric knowledge, not scientific
    -- Tagged separately for filtering
    data_category TEXT DEFAULT 'mystical',  -- Always 'mystical'

    -- Elemental associations
    element TEXT,  -- Earth, Air, Fire, Water, Spirit
    secondary_elements TEXT,  -- JSON array if multiple

    -- Planetary rulership
    planet TEXT,  -- Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn
    secondary_planets TEXT,  -- JSON array

    -- Gender energy
    gender TEXT,  -- masculine (projective) or feminine (receptive)

    -- Zodiac signs
    zodiac TEXT,  -- JSON array: Aries, Taurus, etc.

    -- Chakras
    chakras TEXT,  -- JSON array: root, sacral, solar plexus, heart, throat, third eye, crown

    -- Magical intentions
    magical_purposes TEXT,  -- JSON array: love, prosperity, protection, healing, psychic ability, etc.
    primary_purpose TEXT,  -- Main magical use

    -- Deity associations
    deities TEXT,  -- JSON array of associated gods/goddesses

    -- Sabbats
    sabbats TEXT,  -- JSON array: Samhain, Yule, Imbolc, Ostara, Beltane, Litha, Lughnasadh, Mabon

    -- Spell work
    spell_uses TEXT,  -- JSON array: burn for cleansing, carry for protection, etc.
    preparation_for_magic TEXT,  -- How to prepare for magical use

    -- Folklore
    folklore TEXT,  -- Traditional beliefs and stories
    historical_use TEXT,  -- Historical magical/medicinal use

    -- Notes and sources
    notes TEXT,
    data_source TEXT,  -- Cunningham's Encyclopedia, etc.
    tradition TEXT,  -- Wicca, Hoodoo, European folk magic, etc.

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    INDEX idx_mystical_ingredient (ingredient_id),
    INDEX idx_mystical_element (element),
    INDEX idx_mystical_purpose (primary_purpose)
);

-- =============================================================================
-- INTEGRATION WITH EXISTING SYSTEMS
-- =============================================================================

-- Link to grounded_knowledge system for sensory properties
CREATE TABLE IF NOT EXISTS ingredient_sensory_grounding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,

    -- Visual properties
    visual_color TEXT,  -- JSON array of colors
    visual_shape TEXT,
    visual_size_cm TEXT,  -- Range
    visual_surface TEXT,  -- smooth, rough, shiny, matte, etc.

    -- Tactile properties
    tactile_texture TEXT,
    tactile_temperature TEXT,  -- Typical temperature when touched
    tactile_weight TEXT,  -- light, medium, heavy for size
    tactile_firmness TEXT,

    -- Olfactory properties
    olfactory_aroma TEXT,  -- JSON array of aroma descriptors
    olfactory_intensity TEXT,  -- mild, moderate, strong, pungent
    olfactory_compounds TEXT,  -- JSON array of main aroma molecules

    -- Gustatory properties
    gustatory_tastes TEXT,  -- JSON array: sweet, salty, sour, bitter, umami
    gustatory_mouthfeel TEXT,
    gustatory_aftertaste TEXT,

    -- Auditory properties (when applicable)
    auditory_sound TEXT,  -- crunch, snap, sizzle, etc.

    -- Links to grounded_knowledge tables
    grounded_object_id INTEGER,  -- FK to physical_objects table if exists

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    UNIQUE(ingredient_id),
    INDEX idx_grounding_ingredient (ingredient_id)
);

-- Link to concept_graph system for relationships
CREATE TABLE IF NOT EXISTS ingredient_concept_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,

    -- Concept graph node ID
    concept_id INTEGER,  -- FK to concepts table in concept_graph

    -- Relationship types
    relationship_type TEXT,  -- is_a, part_of, similar_to, pairs_with, etc.

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    INDEX idx_concept_mapping_ingredient (ingredient_id),
    INDEX idx_concept_mapping_concept (concept_id)
);

-- =============================================================================
-- VIEWS FOR CONVENIENT QUERYING
-- =============================================================================

-- Complete ingredient profile view
CREATE VIEW IF NOT EXISTS ingredient_complete_profile AS
SELECT
    i.id,
    i.name,
    i.scientific_name,
    i.category,
    i.subcategory,

    -- Nutritional
    n.calories_kcal,
    n.protein_g,
    n.total_fat_g,
    n.carbohydrate_g,

    -- Chemical
    c.ph_value,
    c.water_percent,

    -- TCM
    tcm.temperature AS tcm_temperature,
    tcm.primary_flavor AS tcm_flavor,

    -- Ayurvedic
    ay.primary_rasa AS ayur_taste,
    ay.virya AS ayur_potency,

    -- Mystical
    m.element AS mystical_element,
    m.primary_purpose AS mystical_purpose

FROM ingredients i
LEFT JOIN nutritional_profile n ON i.id = n.ingredient_id
LEFT JOIN chemical_properties c ON i.id = c.ingredient_id
LEFT JOIN tcm_properties tcm ON i.id = tcm.ingredient_id
LEFT JOIN ayurvedic_properties ay ON i.id = ay.ingredient_id
LEFT JOIN mystical_properties m ON i.id = m.ingredient_id;

-- Schema complete!
