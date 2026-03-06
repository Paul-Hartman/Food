"""
Seed cooking methods for molecular gastronomy transformation system.

This creates the master list of cooking techniques that can be applied to ingredients,
along with corresponding transformation_processes entries for chemistry tracking.
"""

import sqlite3
import os

def get_db_path():
    """Get the database path."""
    return os.path.join(os.path.dirname(__file__), 'food.db')

def seed_cooking_methods():
    """Seed cooking methods and transformation processes."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define cooking methods with detailed properties
    cooking_methods = [
        # DRY-HEAT METHODS (direct heat, no water)
        {
            'method_name': 'Sauté',
            'method_category': 'dry-heat',
            'temp_range_min_f': 300,
            'temp_range_max_f': 400,
            'typical_duration_min': 3,
            'typical_duration_max': 15,
            'heat_transfer_type': 'conduction',
            'equipment_needed': 'sauté pan, skillet',
            'description': 'High-heat cooking in a small amount of fat with constant motion',
            'common_applications': 'vegetables, aromatics, thin proteins'
        },
        {
            'method_name': 'Pan-Fry',
            'method_category': 'dry-heat',
            'temp_range_min_f': 325,
            'temp_range_max_f': 375,
            'typical_duration_min': 5,
            'typical_duration_max': 20,
            'heat_transfer_type': 'conduction',
            'equipment_needed': 'frying pan, skillet',
            'description': 'Cooking in moderate amount of fat with minimal turning',
            'common_applications': 'proteins, breaded items, fritters'
        },
        {
            'method_name': 'Stir-Fry',
            'method_category': 'dry-heat',
            'temp_range_min_f': 400,
            'temp_range_max_f': 500,
            'typical_duration_min': 2,
            'typical_duration_max': 8,
            'heat_transfer_type': 'conduction',
            'equipment_needed': 'wok, high-heat burner',
            'description': 'Very high-heat cooking with constant stirring and tossing',
            'common_applications': 'Asian vegetables, proteins, noodles'
        },
        {
            'method_name': 'Deep-Fry',
            'method_category': 'dry-heat',
            'temp_range_min_f': 325,
            'temp_range_max_f': 375,
            'typical_duration_min': 3,
            'typical_duration_max': 12,
            'heat_transfer_type': 'conduction',
            'equipment_needed': 'deep fryer, thermometer, heavy pot',
            'description': 'Submerging food completely in hot oil',
            'common_applications': 'breaded proteins, potatoes, doughnuts'
        },
        {
            'method_name': 'Roast',
            'method_category': 'dry-heat',
            'temp_range_min_f': 325,
            'temp_range_max_f': 450,
            'typical_duration_min': 20,
            'typical_duration_max': 180,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'oven, roasting pan',
            'description': 'Dry-heat cooking in an oven with air circulation',
            'common_applications': 'large proteins, root vegetables, whole birds'
        },
        {
            'method_name': 'Bake',
            'method_category': 'dry-heat',
            'temp_range_min_f': 300,
            'temp_range_max_f': 450,
            'typical_duration_min': 15,
            'typical_duration_max': 90,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'oven, baking sheet/pan',
            'description': 'Dry-heat cooking in an oven, typically for structured dishes',
            'common_applications': 'breads, pastries, casseroles, gratins'
        },
        {
            'method_name': 'Broil',
            'method_category': 'dry-heat',
            'temp_range_min_f': 500,
            'temp_range_max_f': 550,
            'typical_duration_min': 3,
            'typical_duration_max': 15,
            'heat_transfer_type': 'radiation',
            'equipment_needed': 'oven with broiler, broiler pan',
            'description': 'High-heat cooking from above (top-down radiant heat)',
            'common_applications': 'thin proteins, gratins, finishing dishes'
        },
        {
            'method_name': 'Grill',
            'method_category': 'dry-heat',
            'temp_range_min_f': 400,
            'temp_range_max_f': 600,
            'typical_duration_min': 4,
            'typical_duration_max': 30,
            'heat_transfer_type': 'radiation',
            'equipment_needed': 'grill (gas/charcoal), grill grates',
            'description': 'High-heat cooking from below with direct flame or coals',
            'common_applications': 'proteins, vegetables, fruit'
        },

        # MOIST-HEAT METHODS (cooking in liquid/steam)
        {
            'method_name': 'Boil',
            'method_category': 'moist-heat',
            'temp_range_min_f': 212,
            'temp_range_max_f': 212,
            'typical_duration_min': 3,
            'typical_duration_max': 45,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'pot, water',
            'description': 'Cooking in rapidly bubbling water at 212°F',
            'common_applications': 'pasta, potatoes, eggs, grains'
        },
        {
            'method_name': 'Simmer',
            'method_category': 'moist-heat',
            'temp_range_min_f': 185,
            'temp_range_max_f': 205,
            'typical_duration_min': 15,
            'typical_duration_max': 240,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'pot, liquid',
            'description': 'Gentle cooking with small bubbles occasionally breaking surface',
            'common_applications': 'sauces, soups, stews, tough proteins'
        },
        {
            'method_name': 'Poach',
            'method_category': 'moist-heat',
            'temp_range_min_f': 160,
            'temp_range_max_f': 180,
            'typical_duration_min': 3,
            'typical_duration_max': 30,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'pot, sauté pan, poaching liquid',
            'description': 'Gentle cooking in liquid with no bubbles (below simmering)',
            'common_applications': 'eggs, delicate fish, fruit, chicken breast'
        },
        {
            'method_name': 'Blanch',
            'method_category': 'moist-heat',
            'temp_range_min_f': 212,
            'temp_range_max_f': 212,
            'typical_duration_min': 0.5,
            'typical_duration_max': 5,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'pot, boiling water, ice bath',
            'description': 'Brief boiling followed by ice bath to stop cooking',
            'common_applications': 'vegetables (color preservation), peeling tomatoes, shocking greens'
        },
        {
            'method_name': 'Steam',
            'method_category': 'moist-heat',
            'temp_range_min_f': 212,
            'temp_range_max_f': 212,
            'typical_duration_min': 3,
            'typical_duration_max': 30,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'steamer basket, pot with lid, bamboo steamer',
            'description': 'Cooking with water vapor without direct contact with liquid',
            'common_applications': 'vegetables, dumplings, fish, delicate proteins'
        },

        # COMBINATION METHODS (dry + moist)
        {
            'method_name': 'Braise',
            'method_category': 'combination',
            'temp_range_min_f': 275,
            'temp_range_max_f': 325,
            'typical_duration_min': 90,
            'typical_duration_max': 360,
            'heat_transfer_type': 'conduction and convection',
            'equipment_needed': 'Dutch oven, braising pan, oven',
            'description': 'Searing followed by slow cooking partially submerged in liquid',
            'common_applications': 'tough proteins, large cuts, root vegetables'
        },
        {
            'method_name': 'Stew',
            'method_category': 'combination',
            'temp_range_min_f': 180,
            'temp_range_max_f': 200,
            'typical_duration_min': 60,
            'typical_duration_max': 240,
            'heat_transfer_type': 'convection',
            'equipment_needed': 'pot, Dutch oven',
            'description': 'Simmering fully submerged in liquid (smaller pieces than braising)',
            'common_applications': 'stews, curries, tough meat chunks, legumes'
        },

        # RAW-PREP METHODS (no heat)
        {
            'method_name': 'Slice',
            'method_category': 'raw-prep',
            'temp_range_min_f': None,
            'temp_range_max_f': None,
            'typical_duration_min': 1,
            'typical_duration_max': 5,
            'heat_transfer_type': None,
            'equipment_needed': 'chef knife, cutting board',
            'description': 'Cutting into thin, flat pieces with moderate surface area exposure',
            'common_applications': 'garnishes, salads, sandwiches, visible pieces'
        },
        {
            'method_name': 'Dice',
            'method_category': 'raw-prep',
            'temp_range_min_f': None,
            'temp_range_max_f': None,
            'typical_duration_min': 2,
            'typical_duration_max': 8,
            'heat_transfer_type': None,
            'equipment_needed': 'chef knife, cutting board',
            'description': 'Cutting into uniform cubes (small/medium/large dice)',
            'common_applications': 'sauces, sautés, soups, even cooking'
        },
        {
            'method_name': 'Mince',
            'method_category': 'raw-prep',
            'temp_range_min_f': None,
            'temp_range_max_f': None,
            'typical_duration_min': 2,
            'typical_duration_max': 10,
            'heat_transfer_type': None,
            'equipment_needed': 'chef knife, cutting board',
            'description': 'Very fine chopping into tiny pieces (high enzyme exposure)',
            'common_applications': 'aromatics, herbs, maximum flavor release'
        },
        {
            'method_name': 'Crush',
            'method_category': 'raw-prep',
            'temp_range_min_f': None,
            'temp_range_max_f': None,
            'typical_duration_min': 0.5,
            'typical_duration_max': 2,
            'heat_transfer_type': None,
            'equipment_needed': 'knife flat, mortar and pestle, garlic press',
            'description': 'Breaking cell walls by smashing (maximum enzyme exposure)',
            'common_applications': 'garlic for aioli, ginger paste, herb pastes'
        },
    ]

    # Insert cooking methods
    print("Seeding cooking methods...")
    for method in cooking_methods:
        try:
            cursor.execute("""
                INSERT INTO cooking_methods (
                    method_name, method_category, temp_range_min_f, temp_range_max_f,
                    typical_duration_min, typical_duration_max, heat_transfer_type,
                    equipment_needed, description, common_applications
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                method['method_name'],
                method['method_category'],
                method['temp_range_min_f'],
                method['temp_range_max_f'],
                method['typical_duration_min'],
                method['typical_duration_max'],
                method['heat_transfer_type'],
                method['equipment_needed'],
                method['description'],
                method['common_applications']
            ))
            print(f"  [OK] {method['method_name']} ({method['method_category']})")
        except sqlite3.IntegrityError:
            print(f"  [SKIP] {method['method_name']} already exists")

    # Create transformation_processes for each cooking method
    # This reuses the existing chemistry tracking structure
    print("\nCreating transformation processes for cooking methods...")

    transformation_processes = [
        # Sauté
        {
            'name': 'Sautéing',
            'type': 'cooking-dry-heat',
            'temp_min': 300, 'temp_max': 400, 'temp_optimal': 375,
            'duration_min': 3, 'duration_max': 15,
            'ph_start': None, 'ph_end': None,
            'equipment': 'sauté pan, high heat, small amount of fat',
            'beginner': 'High heat quickly cooks food in a pan with a little oil, creating a browned surface while keeping the inside tender.',
            'chemistry': 'Heat triggers Maillard reaction (amino acids + sugars) at 300°F+, producing melanoidins (brown color) and hundreds of flavor compounds. Moisture evaporates rapidly, concentrating flavors.',
            'expert': 'Maillard reaction produces pyrazines, furans, and thiazoles. Protein denaturation at 140-160°F. Water evaporation concentrates solutes, lowering water activity (aw). Caramelization of sugars begins at 320°F.',
            'reactions': 'Maillard reaction (>300°F), protein denaturation, water evaporation, caramelization (>320°F)',
            'microorganisms': None,
            'flavor_changes': '{"before": "fresh, mild", "after": "concentrated, savory, caramelized", "intensity": "2-3x"}',
            'texture_changes': '{"before": "firm, high water", "after": "softened, browned surface, reduced moisture"}',
            'enzyme_activity': 'All enzymes deactivated above 180°F',
            'volatile_compounds': 'Pyrazines (nutty), furans (caramel), aldehydes (fruity)'
        },
        # Roast
        {
            'name': 'Roasting',
            'type': 'cooking-dry-heat',
            'temp_min': 325, 'temp_max': 450, 'temp_optimal': 400,
            'duration_min': 20, 'duration_max': 180,
            'ph_start': None, 'ph_end': None,
            'equipment': 'oven, roasting pan, dry heat circulation',
            'beginner': 'Cooking food in an oven with hot air circulating around it, creating a crispy outside and tender inside.',
            'chemistry': 'Extended dry heat (325-450°F) drives deep Maillard browning and caramelization. Water evaporates from surface while interior steams. Collagen converts to gelatin in proteins at 160°F+.',
            'expert': 'Surface reaches 300-400°F enabling extensive Maillard reaction. Interior temperature gradient: surface (dehydration, browning) vs. core (steaming, protein denaturation). Pectin breakdown in vegetables at 185°F. Starch gelatinization 185-212°F.',
            'reactions': 'Maillard reaction, caramelization, collagen→gelatin, starch gelatinization, pectin breakdown',
            'microorganisms': None,
            'flavor_changes': '{"before": "raw, mild", "after": "deeply caramelized, concentrated, umami-rich", "intensity": "3-5x"}',
            'texture_changes': '{"before": "firm, raw", "after": "crispy surface, tender interior, 40-60% moisture loss"}',
            'enzyme_activity': 'All enzymes deactivated',
            'volatile_compounds': 'Melanoidins, pyrazines, furans, thiophenes'
        },
        # Grill
        {
            'name': 'Grilling',
            'type': 'cooking-dry-heat',
            'temp_min': 400, 'temp_max': 600, 'temp_optimal': 500,
            'duration_min': 4, 'duration_max': 30,
            'ph_start': None, 'ph_end': None,
            'equipment': 'grill (gas/charcoal), grill grates, direct flame',
            'beginner': 'Cooking over high heat with flames or hot coals, creating char marks and smoky flavor.',
            'chemistry': 'Extremely high heat (400-600°F) causes rapid Maillard reaction and partial carbonization. Char creates bitter compounds. Smoke deposits polycyclic aromatic hydrocarbons (PAHs).',
            'expert': 'Direct radiation heat creates temperature spikes >600°F at contact points. Rapid surface dehydration and Maillard reaction. Char formation = incomplete combustion producing carbon particles and heterocyclic amines (HCAs). Smoke contains phenolic compounds.',
            'reactions': 'Maillard reaction, caramelization, char formation, smoke deposition',
            'microorganisms': None,
            'flavor_changes': '{"before": "raw", "after": "smoky, charred, intense savory", "intensity": "4-5x"}',
            'texture_changes': '{"before": "raw", "after": "charred exterior, juicy interior (if done right)"}',
            'enzyme_activity': 'All enzymes deactivated',
            'volatile_compounds': 'Smoke phenols, char compounds, PAHs, guaiacol, syringol'
        },
        # Blanch
        {
            'name': 'Blanching',
            'type': 'cooking-moist-heat',
            'temp_min': 212, 'temp_max': 212, 'temp_optimal': 212,
            'duration_min': 0.5, 'duration_max': 5,
            'ph_start': None, 'ph_end': None,
            'equipment': 'boiling water, ice bath, timer',
            'beginner': 'Briefly boiling vegetables then shocking in ice water to stop cooking and preserve bright color.',
            'chemistry': 'Brief heat (30 sec - 5 min) deactivates enzymes (polyphenol oxidase, peroxidase) that cause browning and nutrient loss. Ice bath stops residual heat. Chlorophyll is preserved.',
            'expert': 'Polyphenol oxidase deactivated at 180°F prevents enzymatic browning. Brief boiling preserves chlorophyll by removing air pockets from tissue. Ice bath halts pectin breakdown. Minimal nutrient loss if <3 minutes.',
            'reactions': 'Enzyme deactivation, chlorophyll preservation, minimal pectin breakdown',
            'microorganisms': None,
            'flavor_changes': '{"before": "raw", "after": "slightly softened, sweetened, bright", "intensity": "1.2x"}',
            'texture_changes': '{"before": "raw, firm", "after": "tender-crisp, bright color"}',
            'enzyme_activity': 'Polyphenol oxidase, peroxidase deactivated',
            'volatile_compounds': 'Minimal loss of fresh volatile compounds'
        },
        # Simmer
        {
            'name': 'Simmering',
            'type': 'cooking-moist-heat',
            'temp_min': 185, 'temp_max': 205, 'temp_optimal': 195,
            'duration_min': 15, 'duration_max': 240,
            'ph_start': None, 'ph_end': None,
            'equipment': 'pot, liquid (water, stock, sauce)',
            'beginner': 'Gentle cooking in liquid with small bubbles, used for sauces and tender foods that would fall apart with vigorous boiling.',
            'chemistry': 'Gentle heat (185-205°F) allows collagen to convert to gelatin without protein over-coagulation. Flavors infuse into liquid. Starches gelatinize. Vegetables soften via pectin breakdown.',
            'expert': 'Collagen (triple helix) denatures and hydrolyzes to gelatin at 160-180°F. Pectin hydrolysis (185°F) softens cell walls. Starch granules swell and gelatinize (185-212°F). Flavor compounds diffuse into cooking liquid.',
            'reactions': 'Collagen hydrolysis, pectin breakdown, starch gelatinization, flavor extraction',
            'microorganisms': None,
            'flavor_changes': '{"before": "raw", "after": "tender, flavor-infused, mellowed", "intensity": "1-2x"}',
            'texture_changes': '{"before": "firm", "after": "very tender, may fall apart if overcooked"}',
            'enzyme_activity': 'All enzymes deactivated',
            'volatile_compounds': 'Flavor compounds diffuse into liquid'
        },
        # Braise
        {
            'name': 'Braising',
            'type': 'cooking-combination',
            'temp_min': 275, 'temp_max': 325, 'temp_optimal': 300,
            'duration_min': 90, 'duration_max': 360,
            'ph_start': None, 'ph_end': None,
            'equipment': 'Dutch oven, braising liquid, oven or stovetop',
            'beginner': 'Browning food first, then slowly cooking it partially covered in liquid until incredibly tender.',
            'chemistry': 'Initial searing (Maillard reaction) adds flavor. Long, slow cooking (275-325°F) hydrolyzes collagen to gelatin. Partially submerged = browning + moisture. Flavors concentrate.',
            'expert': 'Two-phase reaction: (1) Searing at 350°F+ triggers Maillard reaction. (2) Low, moist heat (275-325°F) converts collagen to gelatin over 2-6 hours. Connective tissue becomes tender. Braising liquid reduces and concentrates.',
            'reactions': 'Maillard reaction (searing phase), collagen hydrolysis, flavor concentration, fat rendering',
            'microorganisms': None,
            'flavor_changes': '{"before": "raw, tough", "after": "deeply savory, rich, fall-apart tender", "intensity": "4-5x"}',
            'texture_changes': '{"before": "tough, chewy", "after": "melt-in-mouth tender, gelatinous"}',
            'enzyme_activity': 'All enzymes deactivated',
            'volatile_compounds': 'Concentrated Maillard products, reduced sauce aromatics'
        },
    ]

    for process in transformation_processes:
        try:
            cursor.execute("""
                INSERT INTO transformation_processes (
                    process_name, process_type,
                    temp_min_f, temp_max_f, temp_optimal_f,
                    duration_min_hours, duration_max_hours,
                    ph_start, ph_end,
                    required_equipment_category,
                    beginner_explanation, chemistry_explanation, expert_explanation,
                    chemical_reactions, microorganisms,
                    flavor_changes_json, texture_changes_json,
                    enzyme_activity, volatile_compounds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                process['name'], process['type'],
                process['temp_min'], process['temp_max'], process['temp_optimal'],
                process['duration_min'], process['duration_max'],
                process['ph_start'], process['ph_end'],
                process['equipment'],
                process['beginner'], process['chemistry'], process['expert'],
                process['reactions'], process['microorganisms'],
                process['flavor_changes'], process['texture_changes'],
                process['enzyme_activity'], process['volatile_compounds']
            ))
            print(f"  [OK] Process: {process['name']}")
        except sqlite3.IntegrityError:
            print(f"  [SKIP] Process {process['name']} already exists")

    conn.commit()
    conn.close()

    print("\n[SUCCESS] Cooking methods seed complete!")
    print(f"   Added {len(cooking_methods)} cooking methods")
    print(f"   Added {len(transformation_processes)} transformation processes")
    print("\nVerify with:")
    print("  SELECT * FROM cooking_methods;")
    print("  SELECT name, type FROM transformation_processes WHERE type LIKE 'cooking%';")

if __name__ == '__main__':
    seed_cooking_methods()
