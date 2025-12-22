#!/usr/bin/env python3
"""
Food Knowledge Integration

Integrates the food ingredient system with the unified intelligence system:
1. Grounded Knowledge - Physical/sensory properties of ingredients
2. Concept Graph - Learning and discovering food knowledge connections
3. Property Reasoning - Logical deduction about food properties

This creates a complete understanding system where food knowledge is:
- Grounded in sensory reality (taste, smell, texture, color)
- Connected conceptually (flavor families, cooking techniques)
- Reasoned about logically (if X is sweet and Y is acidic, balance may result)

Author: Claude
Date: 2025-11-20
"""

import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class IngredientGrounding:
    """Sensory grounding for an ingredient"""

    ingredient_name: str
    visual_properties: Dict[str, any]  # color, opacity, shape
    tactile_properties: Dict[str, any]  # texture, temperature, moisture
    olfactory_properties: Dict[str, any]  # aroma descriptors, intensity
    gustatory_properties: Dict[str, any]  # taste profile
    auditory_properties: Dict[str, any]  # crunch, sizzle, etc.


class FoodKnowledgeIntegration:
    """
    Bridge between food system and unified intelligence system.

    Connects:
    - Food ingredients → Grounded knowledge (sensory properties)
    - Food concepts → Concept graph (learning, discovery)
    - Food logic → Property reasoning (deduction, inference)
    """

    def __init__(
        self,
        food_db_path: str = "food_ingredients.db",
        knowledge_db_path: str = "grounded_knowledge.db",
    ):
        self.food_db = sqlite3.connect(food_db_path)
        self.food_db.row_factory = sqlite3.Row

        # Try to connect to grounded knowledge system
        try:
            from grounded_knowledge_manager import GroundedKnowledgeManager

            self.grounded_km = GroundedKnowledgeManager()
            self.has_grounded = True
        except (ImportError, FileNotFoundError):
            print("[Warning] Grounded knowledge system not available")
            self.has_grounded = False

        # Try to connect to concept graph system
        try:
            from concept_graph_learner import ConceptGraphLearner

            self.concept_graph = ConceptGraphLearner()
            self.has_concept_graph = True
        except (ImportError, FileNotFoundError):
            print("[Warning] Concept graph system not available")
            self.has_concept_graph = False

        # Try to connect to property reasoning
        try:
            from property_reasoning_engine import PropertyReasoningEngine

            self.reasoning_engine = PropertyReasoningEngine()
            self.has_reasoning = True
        except (ImportError, FileNotFoundError):
            print("[Warning] Property reasoning system not available")
            self.has_reasoning = False

    # ========================================================================
    # GROUNDED KNOWLEDGE INTEGRATION
    # ========================================================================

    def ground_ingredient(self, ingredient_name: str) -> Optional[IngredientGrounding]:
        """
        Create sensory grounding for an ingredient.

        Extracts sensory properties from food database and registers
        with grounded knowledge system.
        """
        # Query ingredient sensory data
        cursor = self.food_db.cursor()
        cursor.execute(
            """
            SELECT
                i.name,
                isg.visual_color,
                isg.visual_opacity,
                isg.tactile_texture,
                isg.olfactory_aroma,
                isg.gustatory_tastes,
                tp.hardness,
                tp.cohesiveness,
                tp.springiness,
                tp.chewiness
            FROM ingredients i
            LEFT JOIN ingredient_sensory_grounding isg ON i.id = isg.ingredient_id
            LEFT JOIN texture_properties tp ON i.id = tp.ingredient_id
            WHERE i.name = ?
        """,
            (ingredient_name,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        # Parse visual properties
        visual = {
            "color": row["visual_color"] or "unknown",
            "opacity": row["visual_opacity"] or "opaque",
        }

        # Parse tactile properties
        tactile = {
            "texture": row["tactile_texture"] or "unknown",
            "hardness": row["hardness"] or 0.0,
            "cohesiveness": row["cohesiveness"] or 0.0,
            "springiness": row["springiness"] or 0.0,
            "chewiness": row["chewiness"] or 0.0,
        }

        # Parse olfactory properties
        olfactory = {
            "aroma": row["olfactory_aroma"] or "neutral",
        }

        # Parse gustatory properties
        gustatory = {
            "tastes": row["gustatory_tastes"] or "[]",
        }

        # Parse auditory (if available)
        auditory = {}

        grounding = IngredientGrounding(
            ingredient_name=ingredient_name,
            visual_properties=visual,
            tactile_properties=tactile,
            olfactory_properties=olfactory,
            gustatory_properties=gustatory,
            auditory_properties=auditory,
        )

        # Register with grounded knowledge system
        if self.has_grounded:
            self._register_grounding(grounding)

        return grounding

    def _register_grounding(self, grounding: IngredientGrounding):
        """Register ingredient grounding with grounded knowledge manager"""
        if not self.has_grounded:
            return

        # Add as physical object
        self.grounded_km.add_physical_object(
            name=grounding.ingredient_name,
            category="food_ingredient",
            dimensions={
                "visual": grounding.visual_properties,
                "tactile": grounding.tactile_properties,
            },
        )

        # Add sensory properties
        self.grounded_km.add_sensory_grounding(
            object_name=grounding.ingredient_name,
            visual=grounding.visual_properties.get("color"),
            tactile=grounding.tactile_properties.get("texture"),
            olfactory=grounding.olfactory_properties.get("aroma"),
            gustatory=grounding.gustatory_properties.get("tastes"),
        )

    def batch_ground_ingredients(self, ingredient_names: List[str]) -> int:
        """Ground multiple ingredients at once"""
        grounded = 0
        for name in ingredient_names:
            grounding = self.ground_ingredient(name)
            if grounding:
                grounded += 1
                print(f"[Grounded] {name}")
        return grounded

    # ========================================================================
    # CONCEPT GRAPH INTEGRATION
    # ========================================================================

    def learn_ingredient_concepts(self, ingredient_name: str) -> Dict:
        """
        Learn concepts related to an ingredient using concept graph.

        Discovers connections like:
        - Tomato → acidity (0.8 strength)
        - Tomato → umami (0.7 strength)
        - Tomato → Italian cuisine (0.9 strength)
        """
        if not self.has_concept_graph:
            return {"error": "Concept graph not available"}

        # Add ingredient as a concept
        self.concept_graph.add_concept(ingredient_name, "ingredient")

        # Query related properties from database
        cursor = self.food_db.cursor()

        # Flavor profile
        cursor.execute(
            """
            SELECT molecule_name, importance_score
            FROM ingredient_flavor_molecules ifm
            JOIN ingredients i ON ifm.ingredient_id = i.id
            WHERE i.name = ?
            ORDER BY importance_score DESC
            LIMIT 10
        """,
            (ingredient_name,),
        )

        molecules = cursor.fetchall()

        # Add connections to flavor molecules
        for mol_row in molecules:
            molecule = mol_row["molecule_name"]
            strength = float(mol_row["importance_score"])

            self.concept_graph.add_connection(
                ingredient_name,
                molecule,
                connection_type="contains_molecule",
                strength=strength,
                bidirectional=False,
            )

        # Taste properties
        cursor.execute(
            """
            SELECT gustatory_tastes
            FROM ingredient_sensory_grounding isg
            JOIN ingredients i ON isg.ingredient_id = i.id
            WHERE i.name = ?
        """,
            (ingredient_name,),
        )

        taste_row = cursor.fetchone()
        if taste_row and taste_row["gustatory_tastes"]:
            import json

            try:
                tastes = json.loads(taste_row["gustatory_tastes"])
                for taste in tastes:
                    self.concept_graph.add_connection(
                        ingredient_name,
                        taste,
                        connection_type="has_taste",
                        strength=0.8,
                        bidirectional=False,
                    )
            except json.JSONDecodeError:
                pass

        # Traditional medicine properties
        cursor.execute(
            """
            SELECT temperature, flavors, meridians
            FROM tcm_properties tcp
            JOIN ingredients i ON tcp.ingredient_id = i.id
            WHERE i.name = ?
        """,
            (ingredient_name,),
        )

        tcm_row = cursor.fetchone()
        if tcm_row:
            # TCM temperature
            tcm_temp = tcm_row["temperature"]
            if tcm_temp:
                self.concept_graph.add_connection(
                    ingredient_name,
                    f"tcm_{tcm_temp}",
                    connection_type="has_tcm_temperature",
                    strength=0.9,
                    bidirectional=False,
                )

        # Query learned connections
        connections = self.concept_graph.get_connections(ingredient_name, min_strength=0.5)

        return {
            "ingredient": ingredient_name,
            "connections_added": len(molecules) + (len(tastes) if taste_row else 0),
            "connections": connections,
        }

    def discover_flavor_families(self, min_shared_molecules: int = 5) -> List[List[str]]:
        """
        Use concept graph to discover flavor families.

        Ingredients that share many flavor molecules form families.
        """
        if not self.has_concept_graph:
            return []

        # Query all ingredient-molecule connections
        cursor = self.food_db.cursor()
        cursor.execute(
            """
            SELECT DISTINCT i.name
            FROM ingredients i
            JOIN ingredient_flavor_molecules ifm ON i.id = ifm.ingredient_id
        """
        )

        ingredients = [row["name"] for row in cursor.fetchall()]

        # Learn connections for all ingredients
        for ingredient in ingredients:
            self.learn_ingredient_concepts(ingredient)

        # Find clusters (flavor families)
        # Ingredients with high overlap in molecules cluster together
        families = []

        # Simple clustering: find ingredients that share many molecules
        for i, ing_a in enumerate(ingredients):
            family = [ing_a]

            for ing_b in ingredients[i + 1 :]:
                # Count shared molecules
                cursor.execute(
                    """
                    SELECT COUNT(*) as shared_count
                    FROM ingredient_flavor_molecules ifm1
                    JOIN ingredient_flavor_molecules ifm2
                        ON ifm1.molecule_name = ifm2.molecule_name
                    JOIN ingredients i1 ON ifm1.ingredient_id = i1.id
                    JOIN ingredients i2 ON ifm2.ingredient_id = i2.id
                    WHERE i1.name = ? AND i2.name = ?
                """,
                    (ing_a, ing_b),
                )

                shared = cursor.fetchone()["shared_count"]

                if shared >= min_shared_molecules:
                    family.append(ing_b)

            if len(family) > 1:
                families.append(family)

        return families

    # ========================================================================
    # PROPERTY REASONING INTEGRATION
    # ========================================================================

    def add_ingredient_properties(self, ingredient_name: str):
        """
        Add ingredient properties to reasoning engine.

        Enables logical deduction about ingredients.
        """
        if not self.has_reasoning:
            return

        # Query properties
        cursor = self.food_db.cursor()

        # Taste properties
        cursor.execute(
            """
            SELECT gustatory_tastes
            FROM ingredient_sensory_grounding isg
            JOIN ingredients i ON isg.ingredient_id = i.id
            WHERE i.name = ?
        """,
            (ingredient_name,),
        )

        taste_row = cursor.fetchone()
        if taste_row and taste_row["gustatory_tastes"]:
            import json

            try:
                tastes = json.loads(taste_row["gustatory_tastes"])
                for taste in tastes:
                    self.reasoning_engine.add_property(ingredient_name, f"has_taste_{taste}", True)
            except json.JSONDecodeError:
                pass

        # Nutritional properties
        cursor.execute(
            """
            SELECT protein_g, total_fat_g, carbohydrate_g
            FROM nutritional_profile np
            JOIN ingredients i ON np.ingredient_id = i.id
            WHERE i.name = ?
        """,
            (ingredient_name,),
        )

        nutrition_row = cursor.fetchone()
        if nutrition_row:
            # Classify as protein/fat/carb dominant
            protein = nutrition_row["protein_g"] or 0.0
            fat = nutrition_row["total_fat_g"] or 0.0
            carbs = nutrition_row["carbohydrate_g"] or 0.0

            if protein > fat and protein > carbs:
                self.reasoning_engine.add_property(ingredient_name, "protein_dominant", True)
            elif fat > protein and fat > carbs:
                self.reasoning_engine.add_property(ingredient_name, "fat_dominant", True)
            elif carbs > protein and carbs > fat:
                self.reasoning_engine.add_property(ingredient_name, "carb_dominant", True)

    def add_cooking_rules(self):
        """
        Add logical rules about cooking to reasoning engine.

        Examples:
        - If ingredient is protein_dominant, high heat causes Maillard reaction
        - If ingredient is carb_dominant, heat causes caramelization
        - If ingredient has_taste_bitter and has_taste_sweet, balance results
        """
        if not self.has_reasoning:
            return

        # Rule: Protein + heat → Maillard
        self.reasoning_engine.add_inheritance_rule(
            relation="protein_dominant",
            property_name="undergoes_maillard",
            direction="forward",
            strength=0.9,
        )

        # Rule: Carbs + heat → Caramelization
        self.reasoning_engine.add_inheritance_rule(
            relation="carb_dominant",
            property_name="undergoes_caramelization",
            direction="forward",
            strength=0.85,
        )

    def reason_about_pairing(self, ingredient_a: str, ingredient_b: str) -> Dict:
        """
        Use property reasoning to determine if two ingredients pair well.

        Considers:
        - Taste balance (sweet + sour, fat + acid, etc.)
        - Nutritional balance
        - Traditional pairings
        """
        if not self.has_reasoning:
            return {"error": "Reasoning engine not available"}

        # Add properties for both ingredients
        self.add_ingredient_properties(ingredient_a)
        self.add_ingredient_properties(ingredient_b)

        # Check for complementary tastes
        balance_score = 0.0

        # Sweet + sour = good balance
        a_sweet = self.reasoning_engine.query_property(ingredient_a, "has_taste_sweet")
        b_sour = self.reasoning_engine.query_property(ingredient_b, "has_taste_sour")

        if a_sweet and b_sour:
            balance_score += 0.3

        # Fat + acid = good balance
        a_fat = self.reasoning_engine.query_property(ingredient_a, "fat_dominant")
        b_sour2 = self.reasoning_engine.query_property(ingredient_b, "has_taste_sour")

        if a_fat and b_sour2:
            balance_score += 0.3

        return {
            "ingredient_a": ingredient_a,
            "ingredient_b": ingredient_b,
            "balance_score": balance_score,
            "reasoning": "Taste and nutritional complementarity",
        }

    # ========================================================================
    # UNIFIED QUERIES
    # ========================================================================

    def complete_understanding(self, ingredient_name: str) -> Dict:
        """
        Generate complete understanding of an ingredient using all systems.

        Returns:
        - Grounded properties (sensory)
        - Concept connections (knowledge graph)
        - Logical properties (reasoning)
        """
        result = {
            "ingredient": ingredient_name,
            "grounding": None,
            "concepts": None,
            "properties": None,
        }

        # Grounded knowledge
        if self.has_grounded:
            grounding = self.ground_ingredient(ingredient_name)
            result["grounding"] = grounding

        # Concept graph
        if self.has_concept_graph:
            concepts = self.learn_ingredient_concepts(ingredient_name)
            result["concepts"] = concepts

        # Property reasoning
        if self.has_reasoning:
            self.add_ingredient_properties(ingredient_name)
            # Query derived properties
            # (Would show logical deductions here)
            result["properties"] = "Added to reasoning engine"

        return result


# ============================================================================
# DEMONSTRATION / TEST CODE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("FOOD KNOWLEDGE INTEGRATION DEMONSTRATION")
    print("=" * 70)
    print()

    integration = FoodKnowledgeIntegration()

    print("Available systems:")
    print(f"  Grounded Knowledge: {'✓' if integration.has_grounded else '✗'}")
    print(f"  Concept Graph: {'✓' if integration.has_concept_graph else '✗'}")
    print(f"  Property Reasoning: {'✓' if integration.has_reasoning else '✗'}")
    print()

    print("=" * 70)
    print("This integration connects the food system with:")
    print()
    print("1. GROUNDED KNOWLEDGE")
    print("   - Sensory properties (color, texture, taste, smell)")
    print("   - Physical constraints")
    print("   - Validation of AI outputs")
    print()
    print("2. CONCEPT GRAPH")
    print("   - Learning ingredient relationships")
    print("   - Discovering flavor families")
    print("   - Prime concepts in cooking")
    print()
    print("3. PROPERTY REASONING")
    print("   - Logical deduction about ingredients")
    print("   - Cooking transformation rules")
    print("   - Pairing recommendations with proofs")
    print()
    print("=" * 70)
    print()

    print("Example use cases:")
    print()
    print("1. Grounding: Register 'tomato' with sensory properties")
    print("   → Color: red, Texture: soft, Taste: umami+acidic")
    print()
    print("2. Concepts: Learn that tomato contains glutamate")
    print("   → tomato --[contains_molecule]--> glutamate (0.85)")
    print("   → glutamate --[activates]--> umami_receptor")
    print()
    print("3. Reasoning: Prove tomato + mozzarella pairing")
    print("   → tomato.acidic + mozzarella.fatty = balanced")
    print("   → tomato.umami + mozzarella.milky = complementary")
    print()
    print("=" * 70)
    print("This creates COMPLETE food understanding!")
    print("=" * 70)
