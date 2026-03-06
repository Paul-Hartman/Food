"""
Food Ingredient Manager

Comprehensive food ingredient database manager integrating:
- Scientific data (USDA nutrition, FlavorDB molecules)
- Traditional medicine (TCM, Ayurveda)
- Mystical properties (witchcraft correspondences)
- Chemical transformations
- Sensory perception

Author: Paul + Claude
Date: 2025-11-20
"""

import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class FoodIngredientManager:
    """Manages the comprehensive food ingredient database"""

    def __init__(self, db_path: str = "food_ingredients.db"):
        """Initialize the food ingredient manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries

        # Initialize database schema if it doesn't exist
        self._initialize_schema()

        # Initialize predefined data
        self._initialize_sensory_receptors()
        self._initialize_transformation_types()

    def _initialize_schema(self):
        """Initialize database schema from SQL file"""
        schema_path = Path(__file__).parent / "food_ingredients_schema.sql"

        if schema_path.exists():
            with open(schema_path, "r") as f:
                schema_sql = f.read()
                self.conn.executescript(schema_sql)
                self.conn.commit()

    def _initialize_sensory_receptors(self):
        """Initialize common sensory receptors if not present"""
        cursor = self.conn.cursor()

        receptors = [
            {
                "receptor_name": "TRPV1",
                "receptor_type": "TRP_channel",
                "gene_name": "TRPV1",
                "receptor_family": "TRP",
                "activators": json.dumps(["capsaicin", "heat >42°C", "black pepper", "ginger"]),
                "sensation": "heat, burning, pain",
                "perception_description": "Burning sensation, heat perception",
                "amplifies_stimulus": "heat",
                "amplification_factor": 2.5,
            },
            {
                "receptor_name": "TRPM8",
                "receptor_type": "TRP_channel",
                "gene_name": "TRPM8",
                "receptor_family": "TRP",
                "activators": json.dumps(["menthol", "eucalyptol", "cold <26°C"]),
                "sensation": "cooling, cold",
                "perception_description": "Cooling sensation, cold perception",
                "amplifies_stimulus": "cold",
                "amplification_factor": 3.0,
            },
            {
                "receptor_name": "TRPA1",
                "receptor_type": "TRP_channel",
                "gene_name": "TRPA1",
                "receptor_family": "TRP",
                "activators": json.dumps(["allyl isothiocyanate", "cinnamaldehyde", "allicin"]),
                "sensation": "pungency, irritation",
                "perception_description": "Pungent, sharp, irritating sensation (wasabi, mustard)",
                "amplifies_stimulus": None,
                "amplification_factor": 1.0,
            },
            {
                "receptor_name": "T1R2_T1R3",
                "receptor_type": "taste_receptor",
                "gene_name": "TAS1R2/TAS1R3",
                "receptor_family": "taste",
                "activators": json.dumps(["sugars", "artificial sweeteners"]),
                "sensation": "sweetness",
                "perception_description": "Sweet taste",
                "amplifies_stimulus": None,
                "amplification_factor": 1.0,
            },
            {
                "receptor_name": "T2R",
                "receptor_type": "taste_receptor",
                "gene_name": "TAS2R",
                "receptor_family": "taste",
                "activators": json.dumps(["alkaloids", "phenols", "glucosinolates"]),
                "sensation": "bitterness",
                "perception_description": "Bitter taste (protective against toxins)",
                "amplifies_stimulus": None,
                "amplification_factor": 1.0,
            },
            {
                "receptor_name": "PKD2L1",
                "receptor_type": "taste_receptor",
                "gene_name": "PKD2L1",
                "receptor_family": "taste",
                "activators": json.dumps(["acids", "H+ ions"]),
                "sensation": "sourness",
                "perception_description": "Sour taste",
                "amplifies_stimulus": None,
                "amplification_factor": 1.0,
            },
            {
                "receptor_name": "ENaC",
                "receptor_type": "taste_receptor",
                "gene_name": "SCNN1A",
                "receptor_family": "taste",
                "activators": json.dumps(["sodium chloride", "sodium ions"]),
                "sensation": "saltiness",
                "perception_description": "Salty taste",
                "amplifies_stimulus": None,
                "amplification_factor": 1.0,
            },
            {
                "receptor_name": "mGluR4",
                "receptor_type": "taste_receptor",
                "gene_name": "GRM4",
                "receptor_family": "taste",
                "activators": json.dumps(["glutamate", "aspartate", "nucleotides"]),
                "sensation": "umami",
                "perception_description": "Savory, meaty taste",
                "amplifies_stimulus": None,
                "amplification_factor": 1.0,
            },
        ]

        for receptor in receptors:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO sensory_receptors (
                        receptor_name, receptor_type, gene_name, receptor_family,
                        activators, sensation, perception_description,
                        amplifies_stimulus, amplification_factor
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        receptor["receptor_name"],
                        receptor["receptor_type"],
                        receptor["gene_name"],
                        receptor["receptor_family"],
                        receptor["activators"],
                        receptor["sensation"],
                        receptor["perception_description"],
                        receptor["amplifies_stimulus"],
                        receptor["amplification_factor"],
                    ),
                )
            except sqlite3.IntegrityError:
                pass  # Receptor already exists

        self.conn.commit()

    def _initialize_transformation_types(self):
        """Initialize common transformation types"""
        cursor = self.conn.cursor()

        transformations = [
            {
                "transformation_name": "Maillard Reaction",
                "transformation_category": "heat",
                "description": "Non-enzymatic browning between amino acids and reducing sugars",
                "mechanism": "Complex cascade creating 100s of flavor compounds and brown color",
                "requires_heat": 1,
                "requires_time": 1,
                "requires_mechanical_action": 0,
                "requires_chemical_addition": 0,
                "examples": json.dumps(
                    ["bread crust", "roasted meat", "coffee roasting", "chocolate"]
                ),
            },
            {
                "transformation_name": "Caramelization",
                "transformation_category": "heat",
                "description": "Thermal decomposition of sugars",
                "mechanism": "Dehydration and polymerization of sugars at high heat",
                "requires_heat": 1,
                "requires_time": 1,
                "requires_mechanical_action": 0,
                "requires_chemical_addition": 0,
                "examples": json.dumps(["caramelized onions", "caramel sauce", "crème brûlée"]),
            },
            {
                "transformation_name": "Protein Denaturation",
                "transformation_category": "heat",
                "description": "Unfolding of protein structure",
                "mechanism": "Heat breaks hydrogen bonds, proteins unfold and aggregate",
                "requires_heat": 1,
                "requires_time": 0,
                "requires_mechanical_action": 0,
                "requires_chemical_addition": 0,
                "examples": json.dumps(["cooked eggs", "seared meat", "curdled milk"]),
            },
            {
                "transformation_name": "Enzymatic Browning",
                "transformation_category": "chemical",
                "description": "Enzyme-catalyzed oxidation of phenolic compounds",
                "mechanism": "Polyphenol oxidase + oxygen → brown melanin pigments",
                "requires_heat": 0,
                "requires_time": 1,
                "requires_mechanical_action": 1,
                "requires_chemical_addition": 0,
                "examples": json.dumps(
                    ["cut apples browning", "bruised bananas", "sliced potatoes"]
                ),
            },
            {
                "transformation_name": "Fermentation",
                "transformation_category": "time",
                "description": "Microbial transformation of sugars and proteins",
                "mechanism": "Bacteria/yeast metabolize sugars → acids, alcohol, CO2",
                "requires_heat": 0,
                "requires_time": 1,
                "requires_mechanical_action": 0,
                "requires_chemical_addition": 0,
                "examples": json.dumps(["kimchi", "yogurt", "sauerkraut", "beer", "bread"]),
            },
            {
                "transformation_name": "Gelatinization",
                "transformation_category": "heat",
                "description": "Starch granules absorb water and swell",
                "mechanism": "Heat + water disrupts starch crystalline structure",
                "requires_heat": 1,
                "requires_time": 1,
                "requires_mechanical_action": 0,
                "requires_chemical_addition": 1,  # Requires water
                "examples": json.dumps(["thickened sauce", "cooked rice", "pudding"]),
            },
            {
                "transformation_name": "Emulsification",
                "transformation_category": "mechanical",
                "description": "Stable mixture of oil and water",
                "mechanism": "Emulsifier molecules bridge oil-water interface",
                "requires_heat": 0,
                "requires_time": 0,
                "requires_mechanical_action": 1,
                "requires_chemical_addition": 1,  # Requires emulsifier
                "examples": json.dumps(["mayonnaise", "vinaigrette", "hollandaise"]),
            },
        ]

        for trans in transformations:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO transformation_types (
                        transformation_name, transformation_category, description,
                        mechanism, requires_heat, requires_time,
                        requires_mechanical_action, requires_chemical_addition, examples
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        trans["transformation_name"],
                        trans["transformation_category"],
                        trans["description"],
                        trans["mechanism"],
                        trans["requires_heat"],
                        trans["requires_time"],
                        trans["requires_mechanical_action"],
                        trans["requires_chemical_addition"],
                        trans["examples"],
                    ),
                )
            except sqlite3.IntegrityError:
                pass

        self.conn.commit()

    # =========================================================================
    # INGREDIENT CRUD OPERATIONS
    # =========================================================================

    def add_ingredient(self, name: str, category: str, **kwargs) -> int:
        """Add a new ingredient to the database

        Args:
            name: Ingredient name
            category: Category (vegetable, fruit, protein, etc.)
            **kwargs: Additional fields (scientific_name, common_names, etc.)

        Returns:
            Ingredient ID
        """
        cursor = self.conn.cursor()

        # Prepare fields
        fields = ["name", "category"]
        values = [name, category]

        for key, value in kwargs.items():
            if key in [
                "scientific_name",
                "common_names",
                "subcategory",
                "description",
                "origin_region",
                "seasonality",
                "shelf_life_days",
                "storage_method",
                "usda_fdc_id",
                "flavordb_id",
            ]:
                fields.append(key)
                values.append(json.dumps(value) if isinstance(value, (list, dict)) else value)

        placeholders = ", ".join(["?"] * len(fields))
        field_names = ", ".join(fields)

        cursor.execute(
            f"""
            INSERT INTO ingredients ({field_names})
            VALUES ({placeholders})
        """,
            values,
        )

        self.conn.commit()
        return cursor.lastrowid

    def get_ingredient(self, ingredient_name: str) -> Optional[Dict]:
        """Get complete ingredient profile

        Args:
            ingredient_name: Name of ingredient

        Returns:
            Dictionary with all ingredient data, or None if not found
        """
        cursor = self.conn.cursor()

        # Use the complete profile view
        cursor.execute(
            """
            SELECT * FROM ingredient_complete_profile
            WHERE name = ?
        """,
            (ingredient_name,),
        )

        row = cursor.fetchone()
        return dict(row) if row else None

    def search_ingredients(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search for ingredients by name or category

        Args:
            query: Search query (name)
            category: Optional category filter

        Returns:
            List of matching ingredients
        """
        cursor = self.conn.cursor()

        if category:
            cursor.execute(
                """
                SELECT * FROM ingredients
                WHERE name LIKE ? AND category = ?
                ORDER BY name
            """,
                (f"%{query}%", category),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM ingredients
                WHERE name LIKE ?
                ORDER BY name
            """,
                (f"%{query}%",),
            )

        return [dict(row) for row in cursor.fetchall()]

    # =========================================================================
    # NUTRITIONAL DATA
    # =========================================================================

    def add_nutritional_profile(self, ingredient_id: int, nutrition_data: Dict) -> int:
        """Add nutritional profile for an ingredient

        Args:
            ingredient_id: Ingredient ID
            nutrition_data: Dictionary of nutritional values

        Returns:
            Profile ID
        """
        cursor = self.conn.cursor()

        # Build dynamic INSERT
        fields = ["ingredient_id"]
        values = [ingredient_id]

        for key, value in nutrition_data.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["?"] * len(fields))
        field_names = ", ".join(fields)

        cursor.execute(
            f"""
            INSERT OR REPLACE INTO nutritional_profile ({field_names})
            VALUES ({placeholders})
        """,
            values,
        )

        self.conn.commit()
        return cursor.lastrowid

    def get_nutrition(self, ingredient_name: str) -> Optional[Dict]:
        """Get nutritional profile for an ingredient

        Args:
            ingredient_name: Name of ingredient

        Returns:
            Nutritional data dictionary
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT n.* FROM nutritional_profile n
            JOIN ingredients i ON n.ingredient_id = i.id
            WHERE i.name = ?
        """,
            (ingredient_name,),
        )

        row = cursor.fetchone()
        return dict(row) if row else None

    # =========================================================================
    # FLAVOR MOLECULES & PAIRINGS
    # =========================================================================

    def add_flavor_molecule(self, molecule_name: str, **kwargs) -> int:
        """Add a flavor molecule to the database

        Args:
            molecule_name: Name of the molecule
            **kwargs: Chemical properties, descriptors, etc.

        Returns:
            Molecule ID
        """
        cursor = self.conn.cursor()

        fields = ["molecule_name"]
        values = [molecule_name]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["?"] * len(fields))
        field_names = ", ".join(fields)

        cursor.execute(
            f"""
            INSERT OR IGNORE INTO flavor_molecules ({field_names})
            VALUES ({placeholders})
        """,
            values,
        )

        self.conn.commit()
        return cursor.lastrowid

    def link_ingredient_molecule(
        self,
        ingredient_id: int,
        molecule_id: int,
        concentration_ppm: float,
        importance_score: float,
    ) -> int:
        """Link an ingredient to a flavor molecule

        Args:
            ingredient_id: Ingredient ID
            molecule_id: Molecule ID
            concentration_ppm: Concentration in parts per million
            importance_score: Importance to overall flavor (0-1)

        Returns:
            Link ID
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO ingredient_flavor_molecules
            (ingredient_id, molecule_id, concentration_ppm, importance_score)
            VALUES (?, ?, ?, ?)
        """,
            (ingredient_id, molecule_id, concentration_ppm, importance_score),
        )

        self.conn.commit()
        return cursor.lastrowid

    def calculate_flavor_pairing(self, ingredient_a: str, ingredient_b: str) -> float:
        """Calculate flavor pairing strength based on shared molecules

        Args:
            ingredient_a: First ingredient name
            ingredient_b: Second ingredient name

        Returns:
            Pairing strength (0.0 to 1.0)
        """
        cursor = self.conn.cursor()

        # Get shared molecules
        cursor.execute(
            """
            SELECT
                fm.molecule_name,
                ifm_a.importance_score AS importance_a,
                ifm_b.importance_score AS importance_b
            FROM ingredient_flavor_molecules ifm_a
            JOIN ingredient_flavor_molecules ifm_b ON ifm_a.molecule_id = ifm_b.molecule_id
            JOIN flavor_molecules fm ON ifm_a.molecule_id = fm.id
            JOIN ingredients i_a ON ifm_a.ingredient_id = i_a.id
            JOIN ingredients i_b ON ifm_b.ingredient_id = i_b.id
            WHERE i_a.name = ? AND i_b.name = ?
        """,
            (ingredient_a, ingredient_b),
        )

        shared_molecules = cursor.fetchall()

        if not shared_molecules:
            return 0.0

        # Calculate pairing strength as weighted average of importance scores
        total_importance = sum(
            (row["importance_a"] * row["importance_b"]) for row in shared_molecules
        )

        # Normalize by number of molecules and take square root
        # (so having more shared molecules matters)
        pairing_strength = math.sqrt(total_importance / len(shared_molecules))

        return min(1.0, pairing_strength)

    def suggest_pairings(self, ingredient_name: str, min_strength: float = 0.5) -> List[Dict]:
        """Suggest ingredients that pair well with the given ingredient

        Args:
            ingredient_name: Ingredient to find pairings for
            min_strength: Minimum pairing strength threshold

        Returns:
            List of pairing suggestions with strengths
        """
        cursor = self.conn.cursor()

        # Get all ingredients
        cursor.execute("SELECT name FROM ingredients WHERE name != ?", (ingredient_name,))
        all_ingredients = [row["name"] for row in cursor.fetchall()]

        # Calculate pairing for each
        pairings = []
        for other_ingredient in all_ingredients:
            strength = self.calculate_flavor_pairing(ingredient_name, other_ingredient)
            if strength >= min_strength:
                pairings.append({"ingredient": other_ingredient, "pairing_strength": strength})

        # Sort by strength
        pairings.sort(key=lambda x: x["pairing_strength"], reverse=True)

        return pairings

    # =========================================================================
    # TRANSFORMATIONS
    # =========================================================================

    def add_transformation(
        self,
        ingredient_id: int,
        transformation_type_id: int,
        initial_state: str,
        final_state: str,
        **kwargs,
    ) -> int:
        """Add a transformation for an ingredient

        Args:
            ingredient_id: Ingredient ID
            transformation_type_id: Type of transformation
            initial_state: Starting state (raw, whole, etc.)
            final_state: End state (cooked, minced, etc.)
            **kwargs: Additional parameters (temperature, time, multipliers, etc.)

        Returns:
            Transformation ID
        """
        cursor = self.conn.cursor()

        fields = ["ingredient_id", "transformation_type_id", "initial_state", "final_state"]
        values = [ingredient_id, transformation_type_id, initial_state, final_state]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)

        placeholders = ", ".join(["?"] * len(fields))
        field_names = ", ".join(fields)

        cursor.execute(
            f"""
            INSERT INTO ingredient_transformations ({field_names})
            VALUES ({placeholders})
        """,
            values,
        )

        self.conn.commit()
        return cursor.lastrowid

    def calculate_transformation(
        self, ingredient_name: str, initial_state: str, final_state: str
    ) -> Optional[Dict]:
        """Calculate the result of transforming an ingredient

        Args:
            ingredient_name: Ingredient to transform
            initial_state: Starting state
            final_state: Desired end state

        Returns:
            Dictionary with transformation details and changed properties
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT it.*, tt.transformation_name, tt.mechanism
            FROM ingredient_transformations it
            JOIN transformation_types tt ON it.transformation_type_id = tt.id
            JOIN ingredients i ON it.ingredient_id = i.id
            WHERE i.name = ? AND it.initial_state = ? AND it.final_state = ?
        """,
            (ingredient_name, initial_state, final_state),
        )

        row = cursor.fetchone()

        if not row:
            return None

        transformation = dict(row)

        # Calculate property changes
        result = {
            "transformation": transformation["transformation_name"],
            "mechanism": transformation["mechanism"],
            "conditions": {
                "temperature_range_c": f"{transformation.get('temperature_min_c', 'N/A')}-{transformation.get('temperature_max_c', 'N/A')}",
                "time_range_min": f"{transformation.get('time_min_minutes', 'N/A')}-{transformation.get('time_max_minutes', 'N/A')}",
            },
            "changes": {
                "flavor": transformation.get("flavor_change", ""),
                "texture": transformation.get("texture_change", ""),
                "color": transformation.get("color_change", ""),
            },
            "multipliers": {
                "pungency": transformation.get("pungency_multiplier", 1.0),
                "sweetness": transformation.get("sweetness_multiplier", 1.0),
                "bitterness": transformation.get("bitterness_multiplier", 1.0),
            },
        }

        return result

    # =========================================================================
    # TRADITIONAL MEDICINE
    # =========================================================================

    def add_tcm_properties(self, ingredient_id: int, tcm_data: Dict) -> int:
        """Add Traditional Chinese Medicine properties

        Args:
            ingredient_id: Ingredient ID
            tcm_data: TCM property dictionary

        Returns:
            TCM properties ID
        """
        cursor = self.conn.cursor()

        # Convert lists/dicts to JSON
        for key in ["flavors", "meridians", "qi_action", "actions", "treats", "avoid_in"]:
            if key in tcm_data and isinstance(tcm_data[key], (list, dict)):
                tcm_data[key] = json.dumps(tcm_data[key])

        fields = ["ingredient_id"] + list(tcm_data.keys())
        values = [ingredient_id] + list(tcm_data.values())

        placeholders = ", ".join(["?"] * len(fields))
        field_names = ", ".join(fields)

        cursor.execute(
            f"""
            INSERT OR REPLACE INTO tcm_properties ({field_names})
            VALUES ({placeholders})
        """,
            values,
        )

        self.conn.commit()
        return cursor.lastrowid

    def add_ayurvedic_properties(self, ingredient_id: int, ayur_data: Dict) -> int:
        """Add Ayurvedic properties

        Args:
            ingredient_id: Ingredient ID
            ayur_data: Ayurvedic property dictionary

        Returns:
            Ayurvedic properties ID
        """
        cursor = self.conn.cursor()

        # Convert lists to JSON
        for key in ["rasa", "gunas", "therapeutic_actions", "indications", "contraindications"]:
            if key in ayur_data and isinstance(ayur_data[key], (list, dict)):
                ayur_data[key] = json.dumps(ayur_data[key])

        fields = ["ingredient_id"] + list(ayur_data.keys())
        values = [ingredient_id] + list(ayur_data.values())

        placeholders = ", ".join(["?"] * len(fields))
        field_names = ", ".join(fields)

        cursor.execute(
            f"""
            INSERT OR REPLACE INTO ayurvedic_properties ({field_names})
            VALUES ({placeholders})
        """,
            values,
        )

        self.conn.commit()
        return cursor.lastrowid

    def add_mystical_properties(self, ingredient_id: int, mystical_data: Dict) -> int:
        """Add mystical/witchcraft properties

        Args:
            ingredient_id: Ingredient ID
            mystical_data: Mystical property dictionary

        Returns:
            Mystical properties ID
        """
        cursor = self.conn.cursor()

        # Convert lists to JSON
        for key in [
            "secondary_elements",
            "secondary_planets",
            "zodiac",
            "chakras",
            "magical_purposes",
            "deities",
            "sabbats",
            "spell_uses",
        ]:
            if key in mystical_data and isinstance(mystical_data[key], (list, dict)):
                mystical_data[key] = json.dumps(mystical_data[key])

        fields = ["ingredient_id"] + list(mystical_data.keys())
        values = [ingredient_id] + list(mystical_data.values())

        placeholders = ", ".join(["?"] * len(fields))
        field_names = ", ".join(fields)

        cursor.execute(
            f"""
            INSERT OR REPLACE INTO mystical_properties ({field_names})
            VALUES ({placeholders})
        """,
            values,
        )

        self.conn.commit()
        return cursor.lastrowid

    # =========================================================================
    # SENSORY PERCEPTION
    # =========================================================================

    def activate_receptor(
        self,
        ingredient_id: int,
        receptor_name: str,
        activating_compound: str,
        activation_strength: float,
    ) -> int:
        """Record that an ingredient activates a sensory receptor

        Args:
            ingredient_id: Ingredient ID
            receptor_name: Name of receptor (TRPV1, TRPM8, etc.)
            activating_compound: Specific molecule that activates
            activation_strength: Strength of activation (0-1)

        Returns:
            Activation record ID
        """
        cursor = self.conn.cursor()

        # Get receptor ID
        cursor.execute("SELECT id FROM sensory_receptors WHERE receptor_name = ?", (receptor_name,))
        receptor = cursor.fetchone()

        if not receptor:
            raise ValueError(f"Receptor '{receptor_name}' not found")

        receptor_id = receptor["id"]

        cursor.execute(
            """
            INSERT OR REPLACE INTO ingredient_receptor_activation
            (ingredient_id, receptor_id, activating_compound, activation_strength)
            VALUES (?, ?, ?, ?)
        """,
            (ingredient_id, receptor_id, activating_compound, activation_strength),
        )

        self.conn.commit()
        return cursor.lastrowid

    def get_sensory_perception(self, ingredient_name: str) -> Dict:
        """Get complete sensory perception profile for an ingredient

        Args:
            ingredient_name: Ingredient name

        Returns:
            Dictionary with all sensory perceptions and receptor activations
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                sr.receptor_name,
                sr.sensation,
                sr.perception_description,
                sr.amplifies_stimulus,
                sr.amplification_factor,
                ira.activating_compound,
                ira.activation_strength
            FROM ingredient_receptor_activation ira
            JOIN sensory_receptors sr ON ira.receptor_id = sr.id
            JOIN ingredients i ON ira.ingredient_id = i.id
            WHERE i.name = ?
        """,
            (ingredient_name,),
        )

        activations = cursor.fetchall()

        result = {"ingredient": ingredient_name, "receptor_activations": [], "sensory_effects": []}

        for row in activations:
            activation = {
                "receptor": row["receptor_name"],
                "compound": row["activating_compound"],
                "strength": row["activation_strength"],
                "sensation": row["sensation"],
                "description": row["perception_description"],
            }

            result["receptor_activations"].append(activation)

            # Add amplification effects
            if row["amplifies_stimulus"]:
                effect = f"Amplifies {row['amplifies_stimulus']} sensation by {row['amplification_factor']}x"
                result["sensory_effects"].append(effect)

        return result

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def close(self):
        """Close database connection"""
        self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Test
if __name__ == "__main__":
    print("Testing Food Ingredient Manager\n")

    manager = FoodIngredientManager()

    # Test adding an ingredient
    print("=" * 70)
    print("TEST: Adding garlic")
    print("=" * 70)

    garlic_id = manager.add_ingredient(
        name="garlic",
        scientific_name="Allium sativum",
        category="vegetable",
        subcategory="allium",
        common_names=json.dumps(["ajo", "ail", "aglio"]),
        description="Pungent bulb used as flavoring",
        origin_region="Central Asia",
        seasonality="year-round",
    )

    print(f"Added garlic with ID: {garlic_id}")

    # Test transformation
    print("\n" + "=" * 70)
    print("TEST: Adding garlic mincing transformation")
    print("=" * 70)

    # First, get Maillard reaction type ID
    cursor = manager.conn.cursor()
    cursor.execute(
        "SELECT id FROM transformation_types WHERE transformation_name = ?", ("Maillard Reaction",)
    )
    trans_type = cursor.fetchone()

    if trans_type:
        trans_id = manager.add_transformation(
            ingredient_id=garlic_id,
            transformation_type_id=trans_type["id"],
            initial_state="whole",
            final_state="minced",
            flavor_change="Pungency increases 3x due to allicin formation",
            pungency_multiplier=3.0,
            time_min_minutes=0,
            time_max_minutes=10,
        )
        print(f"Added transformation with ID: {trans_id}")

    # Test receptor activation
    print("\n" + "=" * 70)
    print("TEST: Adding TRPA1 receptor activation")
    print("=" * 70)

    activation_id = manager.activate_receptor(
        ingredient_id=garlic_id,
        receptor_name="TRPA1",
        activating_compound="allicin",
        activation_strength=0.8,
    )
    print(f"Added receptor activation with ID: {activation_id}")

    # Get sensory perception
    perception = manager.get_sensory_perception("garlic")
    print(f"\nSensory perception for garlic:")
    print(f"Receptor activations: {len(perception['receptor_activations'])}")
    if perception["receptor_activations"]:
        print(
            f"  - {perception['receptor_activations'][0]['receptor']}: {perception['receptor_activations'][0]['sensation']}"
        )

    print("\n" + "=" * 70)
    print("✅ Food Ingredient Manager working!")
    print("=" * 70)

    manager.close()
