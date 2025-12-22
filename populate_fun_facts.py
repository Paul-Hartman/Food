"""
Script to populate fun facts and cultural information for common ingredients
"""

fun_facts_data = {
    "Salz": {
        "fun_facts": 'Salt was so valuable in ancient Rome that soldiers were paid partly in salt - this is where the word "salary" comes from! It was used as currency throughout history and has been essential for food preservation for thousands of years.',
        "cultural_significance": 'In many cultures, salt symbolizes purity, protection, and hospitality. Breaking bread and sharing salt is a sacred ritual in numerous traditions. Ancient trade routes called "salt roads" connected civilizations.',
        "ritual_uses": "Used in purification ceremonies, covenant rituals, and as an offering to gods across cultures. Japanese sumo wrestlers throw salt to purify the ring before matches.",
    },
    "Zucker": {
        "fun_facts": 'Sugar was once more valuable than gold! In medieval Europe, only the wealthy could afford it. The word "candy" comes from the Arabic "qandi" meaning crystallized sugar. Your brain uses about 120g of glucose per day - that\'s 420 calories just for thinking!',
        "cultural_significance": "Sugar revolutionized world trade and sadly drove the slave trade. Its journey from luxury spice to everyday staple transformed economies and cuisines worldwide. Indian culture has the oldest records of sugar production dating back 2,500 years.",
        "ritual_uses": "Offering sweets is part of Hindu puja ceremonies. In many cultures, sweet foods mark celebrations and transitions - birthdays, weddings, and festivals.",
    },
    "Milch": {
        "fun_facts": "Humans are the only species that drinks milk from other species! Milk was first domesticated around 10,000 years ago. A cow produces about 6-7 gallons of milk per day. Lactose tolerance evolved independently in different human populations.",
        "cultural_significance": 'The "land of milk and honey" symbolizes abundance in many religious texts. Milk has deep spiritual significance in Hinduism, with Krishna being a famous butter thief. Dairy farming shaped pastoral cultures across the world.',
        "ritual_uses": "Milk is poured as offerings in Hindu temples. Buddhist monks traditionally survived on milk and honey. In ancient Rome, milk was used in purification rituals.",
    },
    "Senf": {
        "fun_facts": 'Mustard is mentioned in ancient Sanskrit texts from 3000 BC! The Romans mixed mustard seeds with unfermented grape juice called "must" - hence "must-ard". Dijon, France produces 70% of the world\'s mustard. It was used medicinally before becoming a condiment!',
        "cultural_significance": "The mustard seed parable in Christianity symbolizes how small beginnings can lead to great things. In Indian culture, mustard seeds are used in tempering dishes and have Ayurvedic medicinal properties.",
        "ritual_uses": "Mustard seeds are used in Hindu wedding ceremonies and scattered to ward off evil spirits. They're believed to bring good fortune and protection.",
    },
    "Wasser": {
        "fun_facts": "Water is the only substance that exists naturally in all three states on Earth! Your body is about 60% water. Hot water freezes faster than cold water - the Mpemba effect! Water has memory-like properties that scientists are still studying.",
        "cultural_significance": "Every civilization developed around water sources. Sacred rivers like the Ganges, Nile, and Jordan hold deep spiritual meaning. Water is central to creation myths worldwide.",
        "ritual_uses": "Baptism, ritual bathing, holy water blessings, and ablutions before prayer are found across religions. Japanese misogi purification involves standing under waterfalls.",
    },
    "Sugar": {  # English version
        "fun_facts": 'Sugar was once more valuable than gold! In medieval Europe, only the wealthy could afford it. The word "candy" comes from the Arabic "qandi" meaning crystallized sugar. Your brain uses about 120g of glucose per day!',
        "cultural_significance": "Sugar revolutionized world trade and economies. Its journey from luxury spice to everyday staple transformed cuisines worldwide. Indian culture has the oldest records of sugar production dating back 2,500 years.",
        "ritual_uses": "Offering sweets is part of Hindu ceremonies. In many cultures, sweet foods mark celebrations - birthdays, weddings, and festivals symbolize sweetness in life.",
    },
    "Carbonated Water": {
        "fun_facts": 'Carbonated water was invented by Joseph Priestley in 1767 while experimenting with the "fixed air" hovering over beer vats! The bubbles are actually carbonic acid. Some people can taste carbonation even if all the bubbles are removed!',
        "cultural_significance": "Sparkling water became a luxury status symbol in the 19th century. European spa towns built their reputations on naturally carbonated mineral springs. It launched the global soft drink industry.",
    },
    "Colour": {
        "fun_facts": "Food coloring E150d (caramel color) is one of the most widely used food additives in the world! Natural food dyes have been used for thousands of years - ancient Egyptians used saffron and berries. Cochineal red comes from crushed beetles!",
        "cultural_significance": 'Color in food affects our perception of taste. Studies show people can\'t identify flavors correctly if the color is "wrong". Different cultures have different color preferences in food.',
    },
}

if __name__ == "__main__":
    import os
    import sys

    import django

    # Setup Django
    sys.path.append("C:\\Users\\paulh\\Documents\\Lotus-Eater Machine\\Food")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_planner.settings")
    django.setup()

    from recipes.models import Ingredient

    updated_count = 0
    created_count = 0

    for name, data in fun_facts_data.items():
        ing, created = Ingredient.objects.get_or_create(name=name, defaults={"category": "other"})

        if data.get("fun_facts"):
            ing.fun_facts = data["fun_facts"]
        if data.get("cultural_significance"):
            ing.cultural_significance = data["cultural_significance"]
        if data.get("ritual_uses"):
            ing.ritual_uses = data["ritual_uses"]

        ing.save()

        if created:
            created_count += 1
            print(f"[+] Created ingredient: {name}")
        else:
            updated_count += 1
            print(f"[*] Updated ingredient: {name}")

    print(f"\nDone! Created {created_count}, Updated {updated_count} ingredients with fun facts.")
