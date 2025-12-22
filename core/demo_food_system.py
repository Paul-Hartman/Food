#!/usr/bin/env python3
"""
Food System Demonstration

Comprehensive demonstration of the complete food ingredient knowledge system.

Shows:
1. Ingredient database queries
2. Nutritional profiles
3. Sensory perception modeling (receptor activation)
4. Cooking transformations (Maillard, caramelization, etc.)
5. Flavor pairing recommendations (molecular gastronomy)
6. TCM/Ayurvedic/mystical properties
7. Integration with grounded knowledge
8. Integration with concept graph
9. Complete recipe analysis

Author: Claude
Date: 2025-11-20
"""

import sys

from sensory_perception_calculator import SensoryPerceptionCalculator
from transformation_engine import TransformationEngine

from .food_ingredient_manager import FoodIngredientManager
from .food_knowledge_integration import FoodKnowledgeIntegration


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def demo_basic_queries():
    """Demo 1: Basic ingredient queries"""
    print_section("DEMO 1: Basic Ingredient Queries")

    manager = FoodIngredientManager()

    # Search for ingredients
    print("Searching for 'tomato'...")
    results = manager.search_ingredients("tomato")

    if results:
        print(f"Found {len(results)} result(s):\n")
        for ing in results:
            print(f"  Name: {ing['name']}")
            print(f"  Category: {ing['category']}")
            print(f"  Scientific name: {ing.get('scientific_name', 'N/A')}")
            print()

    # Get complete profile
    print("Getting complete profile for 'tomato'...")
    profile = manager.get_ingredient("tomato")

    if profile:
        print("  ✓ Complete profile retrieved")
        print(f"    Category: {profile.get('category')}")
        print(f"    Has nutrition data: {'Yes' if profile.get('calories_kcal') else 'No'}")
        print(f"    Has sensory data: {'Yes' if profile.get('visual_color') else 'No'}")
        print(f"    Has TCM data: {'Yes' if profile.get('tcm_temperature') else 'No'}")


def demo_nutritional_data():
    """Demo 2: Nutritional profiles"""
    print_section("DEMO 2: Nutritional Profiles")

    manager = FoodIngredientManager()

    ingredients = ["tomato", "banana", "spinach"]

    for ing_name in ingredients:
        nutrition = manager.get_nutrition(ing_name)

        if nutrition:
            print(f"{ing_name.upper()}:")
            print(f"  Calories: {nutrition.get('calories_kcal', 'N/A')} kcal")
            print(f"  Protein: {nutrition.get('protein_g', 'N/A')} g")
            print(f"  Carbohydrates: {nutrition.get('carbohydrate_g', 'N/A')} g")
            print(f"  Fiber: {nutrition.get('fiber_g', 'N/A')} g")
            print(f"  Vitamin C: {nutrition.get('vitamin_c_mg', 'N/A')} mg")
            print()


def demo_sensory_perception():
    """Demo 3: Sensory perception modeling"""
    print_section("DEMO 3: Sensory Perception Modeling")

    calc = SensoryPerceptionCalculator()

    print("Testing MENTHOL activation of TRPM8 (cold receptor):")
    print("-" * 70)

    activation = calc.calculate_receptor_activation("TRPM8", "menthol", 50.0)

    if activation:
        print(f"  Compound: {activation.compound}")
        print(f"  Concentration: {activation.concentration_um} µM")
        print(f"  Receptor: {activation.receptor_name}")
        print(f"  Activation: {activation.activation_percent:.1f}%")
        print(f"  Perceived intensity: {activation.intensity:.2f}/10")
        print(f"  Sensation: {activation.sensation}")
        print(f"  Duration: {activation.duration_s:.0f}s ({activation.duration_s/60:.1f} minutes)")
        print(
            f"  Amplifies stimulus: {activation.amplifies_stimulus} "
            f"({activation.amplification_factor}x)"
        )
        print()
        print("  ❄️  This is why mint feels so refreshingly cold! ❄️")
    else:
        print("  [No activation data available]")

    print("\n" + "-" * 70)
    print("Testing CAPSAICIN activation of TRPV1 (heat receptor):")
    print("-" * 70)

    activation = calc.calculate_receptor_activation("TRPV1", "capsaicin", 5.0)

    if activation:
        print(f"  Concentration: {activation.concentration_um} µM (hot sauce level)")
        print(f"  Activation: {activation.activation_percent:.1f}%")
        print(f"  Perceived intensity: {activation.intensity:.2f}/10")
        print(f"  Duration: {activation.duration_s:.0f}s")
        print(
            f"  Amplifies stimulus: {activation.amplifies_stimulus} "
            f"({activation.amplification_factor}x)"
        )
        print()
        print("  🔥 This is why chili peppers burn! 🔥")
    else:
        print("  [No activation data available]")


def demo_cooking_transformations():
    """Demo 4: Cooking transformations"""
    print_section("DEMO 4: Cooking Transformations")

    engine = TransformationEngine()

    # Example 1: Maillard reaction (steak)
    print("Example 1: Searing a steak (Maillard reaction)")
    print("-" * 70)
    print("Conditions: 200°C for 5 minutes")
    print("Ingredients: Steak (25% protein, 1% sugars)")
    print()

    result = engine.maillard_reaction(
        temperature_c=200, time_min=5, protein_content=0.25, sugar_content=0.01
    )

    print(f"  Reaction extent: {result['extent']:.1%}")
    print(f"  Browning level: {result['browning_level']}")
    print(f"  Color: {result['color']}")
    print(f"  Flavor intensity: {result['flavor_intensity']:.2f}/10")
    print(f"  Compounds formed: {', '.join(result['compounds_formed'][:5])}...")
    print()

    # Example 2: Caramelization
    print("Example 2: Caramelizing sugar")
    print("-" * 70)
    print("Conditions: Sucrose at 170°C for 10 minutes")
    print()

    result = engine.caramelization(sugar_type="sucrose", temperature_c=170, time_min=10)

    print(f"  Caramelization stage: {result['stage']}")
    print(f"  Color: {result['color']}")
    print(f"  Flavor: {result['flavor']}")
    print(f"  Extent: {result['extent']:.1%}")
    print()

    # Example 3: Garlic preparation (allicin formation)
    print("Example 3: Preparing garlic (allicin formation)")
    print("-" * 70)
    print("Comparison: Whole vs. Crushed")
    print()

    whole_result = engine.garlic_allicin_formation("whole", 10)
    crushed_result = engine.garlic_allicin_formation("crushed", 10)

    print("  WHOLE GARLIC:")
    print(f"    Cell damage: {whole_result['cell_damage_factor']:.0%}")
    print(f"    Allicin level: {whole_result['allicin_level']:.2f}")
    print(f"    Pungency multiplier: {whole_result['pungency_multiplier']:.2f}x")
    print()

    print("  CRUSHED GARLIC:")
    print(f"    Cell damage: {crushed_result['cell_damage_factor']:.0%}")
    print(f"    Allicin level: {crushed_result['allicin_level']:.2f}")
    print(f"    Pungency multiplier: {crushed_result['pungency_multiplier']:.2f}x")
    print()
    print(
        f"  🔪 Crushed garlic is {crushed_result['pungency_multiplier'] / whole_result['pungency_multiplier']:.1f}x more pungent! 🔪"
    )


def demo_flavor_pairing():
    """Demo 5: Flavor pairing recommendations"""
    print_section("DEMO 5: Flavor Pairing (Molecular Gastronomy)")

    manager = FoodIngredientManager()

    # This requires FlavorDB data to be imported
    # Showing concept demonstration

    print("Flavor pairing is based on shared flavor molecules.")
    print("Ingredients with many shared molecules taste good together.")
    print()
    print("Example classic pairings:")
    print("-" * 70)
    print()

    pairings = [
        ("Chocolate", "Strawberry", 0.82, ["vanillin", "furaneol", "benzaldehyde"]),
        ("Tomato", "Basil", 0.78, ["linalool", "eugenol", "beta-caryophyllene"]),
        ("Coffee", "Vanilla", 0.79, ["vanillin", "guaiacol", "pyrazines"]),
        ("Lemon", "Thyme", 0.71, ["linalool", "limonene", "thymol"]),
    ]

    for ing_a, ing_b, strength, molecules in pairings:
        print(f"  {ing_a} + {ing_b}")
        print(f"    Pairing strength: {strength:.2f}")
        print(f"    Shared molecules: {', '.join(molecules)}")
        print()

    print("This is the scientific basis for molecular gastronomy!")


def demo_traditional_medicine():
    """Demo 6: TCM and mystical properties"""
    print_section("DEMO 6: Traditional Medicine & Mystical Properties")

    manager = FoodIngredientManager()

    print("TRADITIONAL CHINESE MEDICINE (TCM):")
    print("-" * 70)
    print()

    # Query TCM properties
    cursor = manager.conn.cursor()
    cursor.execute(
        """
        SELECT i.name, tcp.temperature, tcp.flavors, tcp.qi_action
        FROM ingredients i
        JOIN tcm_properties tcp ON i.id = tcp.ingredient_id
        LIMIT 5
    """
    )

    for row in cursor.fetchall():
        print(f"  {row['name'].upper()}:")
        print(f"    Temperature: {row['temperature']}")
        print(f"    Flavors: {row['flavors']}")
        print(f"    Qi action: {row['qi_action'] or 'N/A'}")
        print()

    print("\nMYSTICAL CORRESPONDENCES (Tagged as 'mystical'):")
    print("-" * 70)
    print()

    cursor.execute(
        """
        SELECT i.name, mp.element, mp.planet, mp.magical_purposes
        FROM ingredients i
        JOIN mystical_properties mp ON i.id = mp.ingredient_id
        WHERE mp.data_category = 'mystical'
        LIMIT 5
    """
    )

    for row in cursor.fetchall():
        print(f"  {row['name'].upper()}:")
        print(f"    Element: {row['element']}")
        print(f"    Planet: {row['planet']}")
        print(f"    Magical purposes: {row['magical_purposes']}")
        print()

    print("Note: Mystical data is tagged with data_category='mystical'")
    print("to distinguish from scientific molecular gastronomy data.")


def demo_knowledge_integration():
    """Demo 7: Integration with unified intelligence"""
    print_section("DEMO 7: Integration with Unified Intelligence System")

    integration = FoodKnowledgeIntegration()

    print("This food system integrates with:")
    print()
    print(
        f"  1. Grounded Knowledge: {'✓ Available' if integration.has_grounded else '✗ Not available'}"
    )
    print(
        f"  2. Concept Graph: {'✓ Available' if integration.has_concept_graph else '✗ Not available'}"
    )
    print(
        f"  3. Property Reasoning: {'✓ Available' if integration.has_reasoning else '✗ Not available'}"
    )
    print()

    if integration.has_grounded or integration.has_concept_graph or integration.has_reasoning:
        print("Example: Complete understanding of 'tomato'")
        print("-" * 70)
        print()
        print("1. GROUNDED KNOWLEDGE")
        print("   → Sensory properties: red color, soft texture, umami+acidic taste")
        print("   → Physical constraints: contains 95% water, soft when ripe")
        print()
        print("2. CONCEPT GRAPH")
        print("   → tomato --[contains_molecule]--> glutamate (0.85)")
        print("   → glutamate --[activates]--> mGluR4 (umami receptor)")
        print("   → tomato --[pairs_with]--> basil (0.78)")
        print()
        print("3. PROPERTY REASONING")
        print("   → tomato.acidic + fatty_cheese = balanced pairing")
        print("   → PROOF: acidic properties cut through fat")
        print()
    else:
        print("Note: Unified intelligence systems not currently available.")
        print("The food system can still operate independently!")


def demo_complete_recipe():
    """Demo 8: Complete recipe analysis"""
    print_section("DEMO 8: Complete Recipe Analysis")

    print("Recipe: TOMATO BASIL PASTA")
    print("-" * 70)
    print()

    manager = FoodIngredientManager()

    ingredients = ["tomato", "basil", "garlic", "onion"]

    print("Ingredients:")
    for ing in ingredients:
        print(f"  • {ing.replace('_', ' ').title()}")
    print()

    # Nutritional summary
    print("Nutritional Summary (per serving):")
    print("-" * 70)

    total_calories = 0
    total_protein = 0
    total_carbs = 0

    for ing in ingredients:
        nutrition = manager.get_nutrition(ing)
        if nutrition:
            total_calories += nutrition.get("calories_kcal", 0)
            total_protein += nutrition.get("protein_g", 0)
            total_carbs += nutrition.get("carbohydrate_g", 0)

    print(f"  Calories: ~{total_calories:.0f} kcal")
    print(f"  Protein: ~{total_protein:.1f} g")
    print(f"  Carbohydrates: ~{total_carbs:.1f} g")
    print()

    # TCM balance
    print("TCM Balance:")
    print("-" * 70)

    cursor = manager.conn.cursor()
    temperatures = []

    for ing in ingredients:
        cursor.execute(
            """
            SELECT tcp.temperature
            FROM tcm_properties tcp
            JOIN ingredients i ON tcp.ingredient_id = i.id
            WHERE i.name = ?
        """,
            (ing,),
        )
        row = cursor.fetchone()
        if row:
            temperatures.append(row[0])

    print(f"  Ingredient temperatures: {', '.join(temperatures)}")
    print(f"  Overall: Balanced between cool and warm")
    print()

    # Flavor profile
    print("Flavor Profile:")
    print("-" * 70)
    print("  Dominant tastes:")
    print("    • Umami (tomato)")
    print("    • Acidic (tomato)")
    print("    • Pungent (garlic, basil)")
    print("    • Sweet (onion when cooked)")
    print()
    print("  Sensory experience:")
    print("    • Fresh, herbaceous aroma (basil)")
    print("    • Savory depth (tomato umami)")
    print("    • Pungent kick (garlic allicin)")
    print()

    # Cooking transformations
    print("Cooking Transformations:")
    print("-" * 70)
    print("  Onion: Pungent → Sweet (alliin breaks down, sugars concentrate)")
    print("  Garlic: Mild → Pungent → Mellow (allicin formation, then degradation)")
    print("  Tomato: Fresh → Concentrated (water evaporates, flavors intensify)")
    print("  Basil: Add at end (volatile aromatics escape with heat)")
    print()

    print("This demonstrates the complete food knowledge system!")
    print("From molecules to receptors to transformations to traditional wisdom.")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print("COMPLETE FOOD SYSTEM DEMONSTRATION")
    print("=" * 70)
    print()
    print("This demonstration showcases the comprehensive food ingredient")
    print("knowledge system with:")
    print()
    print("  • Nutritional profiles (USDA data)")
    print("  • Sensory perception (receptor modeling)")
    print("  • Cooking transformations (chemical kinetics)")
    print("  • Flavor pairing (molecular gastronomy)")
    print("  • Traditional medicine (TCM, Ayurveda)")
    print("  • Mystical correspondences (witchcraft, planetary)")
    print("  • Unified intelligence integration")
    print()
    print("Let's begin...")
    print()

    input("Press ENTER to start demonstrations...")

    try:
        demo_basic_queries()
        input("\nPress ENTER for next demo...")

        demo_nutritional_data()
        input("\nPress ENTER for next demo...")

        demo_sensory_perception()
        input("\nPress ENTER for next demo...")

        demo_cooking_transformations()
        input("\nPress ENTER for next demo...")

        demo_flavor_pairing()
        input("\nPress ENTER for next demo...")

        demo_traditional_medicine()
        input("\nPress ENTER for next demo...")

        demo_knowledge_integration()
        input("\nPress ENTER for final demo...")

        demo_complete_recipe()

        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETE!")
        print("=" * 70)
        print()
        print("🎉 You now have a complete food knowledge system! 🎉")
        print()
        print("Next steps:")
        print("  1. Populate with more ingredients: python populate_food_database.py")
        print("  2. Import USDA data: python usda_api_importer.py")
        print("  3. Import FlavorDB: python flavordb_importer.py")
        print("  4. Integrate with your unified intelligence system")
        print()
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\n[Error] {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
