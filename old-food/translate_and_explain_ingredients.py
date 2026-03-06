"""
Script to translate German ingredient names to English and add educational info
"""

import os
import sys

import django

# Setup Django
sys.path.append("C:\\Users\\paulh\\Documents\\Lotus-Eater Machine\\Food")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_planner.settings")
django.setup()

from recipes.models import Ingredient, ProductIngredient

# Translation mappings
ingredient_translations = {
    "Milch": "Milk",
    "Salz": "Salt",
    "Senf": "Mustard",
    "Zucker": "Sugar",
    "Wasser": "Water",
    "Orangen-Direktsaft mit Fruchtfleisch": "Orange Juice with Pulp",
    "Butter Streichzart gesalzen - Vorteilspack": "Soft Salted Butter",
}

product_ingredient_translations = {
    "Rapsöl": "Rapeseed Oil",
    "Eigelb": "Egg Yolk",
    "Branntweinessig": "Spirit Vinegar",
    "Zucker": "Sugar",
    "Salz": "Salt",
    "Senf": "Mustard",
    "Säuerungsmittel": "Acidifying Agent",
    "Antioxidationsmittel": "Antioxidant",
    "Milch": "Milk",
    "Lab": "Rennet",
    "Konservierungsstoff": "Preservative",
}

# Functional ingredient educational information
functional_ingredients_info = {
    "Antioxidant": {
        "fun_facts": "Antioxidants are the food industry's time machines! They prevent fats and oils from going rancid by stopping oxidation - the same chemical process that makes metal rust. Common antioxidants include vitamin E, vitamin C (ascorbic acid), and rosemary extract. Without them, your chips would taste like cardboard in days!",
        "cultural_significance": "Before synthetic antioxidants, people used natural preservation methods like smoking, salting, and adding spices. Many traditional spice blends (like curry powder) are loaded with natural antioxidants. Ancient Egyptians used honey and wine as antioxidant preservatives!",
        "ritual_uses": "While antioxidants themselves aren't used in rituals, many antioxidant-rich foods like pomegranates, wine, and olive oil have been central to religious ceremonies for millennia.",
    },
    "Acidifying Agent": {
        "fun_facts": "Acidifying agents are pH balancers that make food safer and tastier! They lower pH to create an environment where harmful bacteria can't survive. Common ones include citric acid (from citrus), lactic acid (from fermentation), and acetic acid (vinegar). They also enhance flavors and help preserve color!",
        "cultural_significance": "Humans have used acidic preservation for thousands of years - pickling, fermenting, and adding vinegar or citrus. Korean kimchi, German sauerkraut, and Indian pickles all rely on acidifying agents. The sour flavor is one of the five basic tastes recognized across all cultures.",
        "ritual_uses": "Fermented foods with natural acids (like wine, bread, and cheese) play central roles in religious ceremonies worldwide. The transformation through fermentation was often seen as mystical or divine.",
    },
    "Preservative": {
        "fun_facts": "Preservatives are the guardians against food spoilage! They prevent mold, yeast, and bacteria from growing. Salt and sugar were the first preservatives used by humans. Modern preservatives include sodium benzoate, potassium sorbate, and sulfites. Without preservatives, food waste would be astronomical!",
        "cultural_significance": 'The quest to preserve food shaped human civilization. Salt was so valuable it was used as currency (hence "salary" from Latin "salarium"). Trade routes, wars, and empires were built around preservatives like salt, sugar, and spices. Refrigeration only became common in the 20th century!',
        "ritual_uses": "Salt is used in purification rituals across many religions. Preserved foods like wine, cheese, and bread are sacred in various traditions. The Japanese preserve foods for New Year celebrations as a spiritual practice.",
    },
    "Rennet": {
        "fun_facts": "Rennet is the magical ingredient that transforms liquid milk into solid cheese! It contains enzymes (chymosin) that curdle milk by clumping milk proteins together. Traditionally sourced from calf stomach lining, but now also made from microbial or vegetable sources. It's been used for over 4,000 years!",
        "cultural_significance": "Legend says rennet was discovered when a traveler stored milk in a pouch made from a calf's stomach and found it had turned into cheese! Cheese-making with rennet spread across Europe and became central to many cultures - Parmigiano-Reggiano, Cheddar, Gouda all require it.",
        "ritual_uses": "Cheese has been offered to gods in ancient Greece and Rome. Some Jewish communities debate whether microbial rennet makes cheese kosher. Cheese wheels are blessed in traditional Alpine ceremonies.",
    },
    "Spirit Vinegar": {
        "fun_facts": 'Spirit vinegar is made by fermenting grain alcohol - it\'s basically vodka that went sour! With 5-10% acetic acid, it\'s one of the strongest vinegars. The word "vinegar" comes from French "vin aigre" meaning "sour wine". It\'s a powerful preservative and flavor enhancer!',
        "cultural_significance": 'Vinegar has been used since ancient times - Babylonians made it from dates in 5000 BC! Romans gave soldiers "posca" (vinegar water) to drink. In medieval times, vinegar was used as medicine and to preserve food through harsh winters.',
        "ritual_uses": "In Christian tradition, Jesus was offered vinegar on the cross. Jewish Passover includes vinegar in charoset. Many cultures use vinegar in cleansing rituals due to its purifying properties.",
    },
    "Rapeseed Oil": {
        "fun_facts": 'Rapeseed oil (also called canola oil in North America) comes from the bright yellow rapeseed flower! It\'s one of the healthiest oils with the lowest saturated fat content. "Canola" stands for "Canadian oil, low acid" - developed in Canada in the 1970s. It has a neutral taste and high smoke point, making it perfect for cooking!',
        "cultural_significance": "Rapeseed has been cultivated for 4,000 years in Asia and 500 years in Europe. During WWII, it was crucial as a lubricant for steam engines. After the war, Canadian scientists bred a safer edible version that became today's canola oil, revolutionizing healthy cooking.",
        "ritual_uses": "While the oil itself isn't used ritually, the bright yellow rapeseed fields are celebrated in European spring festivals. In Hindu tradition, mustard oil (a related oil) is used in religious ceremonies and wedding rituals.",
    },
    "Egg Yolk": {
        "fun_facts": "Egg yolks are nature's emulsifiers! They contain lecithin, which allows oil and water to mix - essential for making mayonnaise, hollandaise, and aioli. One yolk contains nearly all the vitamins and minerals in an egg. The color depends on the hen's diet - more carotene = more orange!",
        "cultural_significance": "Eggs symbolize new life and rebirth across cultures. The tradition of decorating eggs dates back thousands of years. In medieval Europe, egg yolks were mixed with pigments to create tempera paint for masterpiece paintings. They were also currency - rents were sometimes paid in eggs!",
        "ritual_uses": "Eggs are central to Easter celebrations, Passover seders, and Chinese Moon Festival. In some traditions, eggs are buried under foundations for good luck. Japanese sumo wrestlers drink raw eggs for strength.",
    },
}


def translate_ingredients():
    """Translate German ingredient names to English"""
    count = 0
    for german_name, english_name in ingredient_translations.items():
        try:
            german_ingredient = Ingredient.objects.get(name=german_name)

            # Check if English version already exists
            try:
                english_ingredient = Ingredient.objects.get(name=english_name)
                # English version exists, copy fun facts to it and delete German version
                if german_ingredient.fun_facts and not english_ingredient.fun_facts:
                    english_ingredient.fun_facts = german_ingredient.fun_facts
                if (
                    german_ingredient.cultural_significance
                    and not english_ingredient.cultural_significance
                ):
                    english_ingredient.cultural_significance = (
                        german_ingredient.cultural_significance
                    )
                if german_ingredient.ritual_uses and not english_ingredient.ritual_uses:
                    english_ingredient.ritual_uses = german_ingredient.ritual_uses
                english_ingredient.save()

                # Delete German version
                german_ingredient.delete()
                print(
                    f"[MERGED] {german_name} -> {english_name} (merged and deleted German version)"
                )
                count += 1

            except Ingredient.DoesNotExist:
                # English version doesn't exist, just rename
                german_ingredient.name = english_name
                german_ingredient.save()
                print(f"[TRANSLATED] {german_name} -> {english_name}")
                count += 1

        except Ingredient.DoesNotExist:
            print(f"[SKIP] Ingredient not found: {german_name}")

    return count


def translate_product_ingredients():
    """Translate German product ingredient names to English"""
    count = 0
    for german_name, english_name in product_ingredient_translations.items():
        product_ingredients = ProductIngredient.objects.filter(text=german_name)
        if product_ingredients.exists():
            for pi in product_ingredients:
                pi.text = english_name
                pi.save()
                print(
                    f'[TRANSLATED PI] {german_name} -> {english_name} (Product: {pi.product.name if pi.product else "None"})'
                )
                count += 1
        else:
            print(f"[SKIP] ProductIngredient not found: {german_name}")

    return count


def add_functional_ingredient_info():
    """Add educational information for functional ingredients"""
    count = 0
    created = 0

    for ingredient_name, info in functional_ingredients_info.items():
        # Try to get or create the ingredient
        ing, was_created = Ingredient.objects.get_or_create(
            name=ingredient_name, defaults={"category": "additive"}
        )

        # Add the educational info
        ing.fun_facts = info.get("fun_facts", "")
        ing.cultural_significance = info.get("cultural_significance", "")
        ing.ritual_uses = info.get("ritual_uses", "")

        # Add tags for functional ingredients
        if "tags" not in ing.__dict__ or not ing.tags:
            ing.tags = ["additive", "functional"]

        ing.save()

        if was_created:
            print(f"[CREATED] {ingredient_name}")
            created += 1
        else:
            print(f"[UPDATED] {ingredient_name}")
        count += 1

    return count, created


if __name__ == "__main__":
    print("=" * 60)
    print("TRANSLATING INGREDIENTS")
    print("=" * 60)

    translated = translate_ingredients()
    print(f"\nTranslated {translated} ingredient names")

    print("\n" + "=" * 60)
    print("TRANSLATING PRODUCT INGREDIENTS")
    print("=" * 60)

    pi_translated = translate_product_ingredients()
    print(f"\nTranslated {pi_translated} product ingredient names")

    print("\n" + "=" * 60)
    print("ADDING FUNCTIONAL INGREDIENT INFO")
    print("=" * 60)

    updated, created = add_functional_ingredient_info()
    print(
        f"\nUpdated {updated} functional ingredients ({created} created, {updated - created} updated)"
    )

    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
