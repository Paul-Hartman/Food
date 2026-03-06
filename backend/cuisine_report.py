"""Generate a report of all world cuisines, food catalog counts, and recipe coverage."""
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "food.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Recipe counts by normalized cuisine
    c.execute(
        "SELECT LOWER(cuisine), COUNT(*) FROM recipes WHERE cuisine IS NOT NULL GROUP BY LOWER(cuisine)"
    )
    small_r = {r[0]: r[1] for r in c.fetchall()}
    c.execute(
        "SELECT LOWER(cuisine), COUNT(*) FROM recipes_large WHERE cuisine IS NOT NULL GROUP BY LOWER(cuisine)"
    )
    large_r = {r[0]: r[1] for r in c.fetchall()}

    # Normalize variations to canonical names
    normalize = {
        "chinese": "Chinese", "chinese cuisine": "Chinese", "people's republic of china": "Chinese",
        "china": "Chinese", "sichuan cuisine": "Chinese", "cantonese cuisine": "Chinese",
        "japanese": "Japanese", "japanese cuisine": "Japanese", "japan": "Japanese", "yoshoku": "Japanese",
        "korean": "Korean", "korean cuisine": "Korean", "korea": "Korean", "south korea": "Korean",
        "indian": "Indian", "indian cuisine": "Indian", "india": "Indian",
        "indian subcontinent": "Indian", "south asian cuisine": "Indian",
        "gujarati cuisine": "Indian", "bengali cuisine": "Indian",
        "italian": "Italian", "italian cuisine": "Italian", "italy": "Italian",
        "sicilian cuisine": "Italian", "neapolitan cuisine": "Italian",
        "french": "French", "french cuisine": "French", "france": "French",
        "cuisine nicoise": "French", "provencal cuisine": "French",
        "mexican": "Mexican", "mexican cuisine": "Mexican", "mexico": "Mexican",
        "spanish": "Spanish", "spanish cuisine": "Spanish", "spain": "Spanish",
        "galician cuisine": "Spanish", "basque cuisine": "Spanish", "catalan cuisine": "Spanish",
        "greek": "Greek", "greek cuisine": "Greek", "greece": "Greek",
        "turkish": "Turkish", "turkish cuisine": "Turkish", "turkey": "Turkish",
        "ottoman empire": "Turkish",
        "german": "German", "german cuisine": "German", "germany": "German",
        "bavarian cuisine": "German",
        "thai": "Thai", "thai cuisine": "Thai", "thailand": "Thai",
        "vietnamese": "Vietnamese", "vietnamese cuisine": "Vietnamese", "vietnam": "Vietnamese",
        "indonesian": "Indonesian", "indonesia": "Indonesian", "indonesian cuisine": "Indonesian",
        "acehnese cuisine": "Indonesian", "javanese cuisine": "Indonesian",
        "padang cuisine": "Indonesian",
        "british": "British", "united kingdom": "British", "england": "British",
        "scotland": "British", "welsh": "British",
        "american": "American", "united states": "American",
        "cuisine of the united states": "American",
        "southern us": "American (Southern)", "cajun/creole": "American (Cajun/Creole)",
        "cajun": "American (Cajun/Creole)", "tex-mex": "American (Tex-Mex)",
        "kentucky": "American (Southern)",
        "middle eastern": "Middle Eastern", "middle east": "Middle Eastern",
        "levantine cuisine": "Middle Eastern",
        "mediterranean": "Mediterranean",
        "russian": "Russian", "russian cuisine": "Russian", "russia": "Russian",
        "soviet cuisine": "Russian", "soviet union": "Russian",
        "scandinavian": "Scandinavian",
        "swedish": "Swedish", "swedish cuisine": "Swedish", "sweden": "Swedish",
        "norwegian": "Norwegian", "norwegian cuisine": "Norwegian", "norway": "Norwegian",
        "danish": "Danish", "danish cuisine": "Danish", "denmark": "Danish",
        "finnish": "Finnish", "finnish cuisine": "Finnish", "finland": "Finnish",
        "icelandic": "Icelandic", "iceland": "Icelandic",
        "african": "Pan-African", "african cuisine": "Pan-African",
        "caribbean": "Caribbean",
        "latin american": "Latin American",
        "polish": "Polish", "polish cuisine": "Polish", "poland": "Polish",
        "hungarian": "Hungarian", "hungarian cuisine": "Hungarian", "hungary": "Hungarian",
        "portuguese": "Portuguese", "portuguese cuisine": "Portuguese", "portugal": "Portuguese",
        "swiss": "Swiss", "swiss cuisine": "Swiss", "switzerland": "Swiss",
        "ukrainian": "Ukrainian", "ukrainian cuisine": "Ukrainian", "ukraine": "Ukrainian",
        "romanian": "Romanian", "romanian cuisine": "Romanian", "romania": "Romanian",
        "czech": "Czech", "czech cuisine": "Czech", "czech republic": "Czech",
        "georgian": "Georgian", "georgian cuisine": "Georgian", "georgia": "Georgian",
        "armenian": "Armenian", "armenian cuisine": "Armenian", "armenia": "Armenian",
        "azerbaijani": "Azerbaijani", "azerbaijani cuisine": "Azerbaijani", "azerbaijan": "Azerbaijani",
        "taiwanese": "Taiwanese", "taiwanese cuisine": "Taiwanese",
        "taiwan": "Taiwanese", "taiwan island": "Taiwanese",
        "philippine": "Filipino", "philippines": "Filipino",
        "malaysian": "Malaysian", "malaysia": "Malaysian",
        "singaporean": "Singaporean", "singapore": "Singaporean",
        "cambodian": "Cambodian", "cambodia": "Cambodian",
        "burmese": "Burmese", "myanmar": "Burmese",
        "laotian": "Laotian", "laos": "Laotian",
        "peruvian": "Peruvian", "peru": "Peruvian",
        "brazilian": "Brazilian", "brazil": "Brazilian",
        "argentine": "Argentine", "argentine cuisine": "Argentine", "argentina": "Argentine",
        "chilean": "Chilean", "chile": "Chilean",
        "colombian": "Colombian", "colombia": "Colombian",
        "venezuelan": "Venezuelan", "venezuela": "Venezuelan",
        "bolivian": "Bolivian", "bolivia": "Bolivian",
        "paraguayan": "Paraguayan", "paraguay": "Paraguayan",
        "uruguayan": "Uruguayan", "uruguay": "Uruguayan",
        "ecuadorian": "Ecuadorian", "ecuador": "Ecuadorian",
        "cuban": "Cuban", "cuba": "Cuban",
        "jamaican": "Jamaican", "jamaica": "Jamaican",
        "haitian": "Haitian", "haiti": "Haitian",
        "trinidadian": "Trinidadian", "trinidad and tobago": "Trinidadian",
        "puerto rican": "Puerto Rican", "puerto rico": "Puerto Rican",
        "nigerian": "Nigerian", "nigerian cuisine": "Nigerian", "nigeria": "Nigerian",
        "ghanaian": "Ghanaian", "ghana": "Ghanaian",
        "ethiopian": "Ethiopian", "ethiopia": "Ethiopian",
        "senegalese": "Senegalese", "senegal": "Senegalese",
        "south african": "South African", "south africa": "South African",
        "kenyan": "Kenyan", "kenya": "Kenyan",
        "ugandan": "Ugandan", "uganda": "Ugandan",
        "cameroonian": "Cameroonian", "cameroon": "Cameroonian",
        "moroccan": "Moroccan", "moroccan cuisine": "Moroccan", "morocco": "Moroccan",
        "tunisian": "Tunisian", "tunisia": "Tunisian",
        "algerian": "Algerian", "algerian cuisine": "Algerian", "algeria": "Algerian",
        "egyptian": "Egyptian", "egypt": "Egyptian",
        "libyan": "Libyan", "libya": "Libyan",
        "lebanese": "Lebanese", "lebanon": "Lebanese",
        "iranian": "Iranian", "iranian cuisine": "Iranian", "iran": "Iranian",
        "iraqi": "Iraqi", "iraq": "Iraqi",
        "syrian": "Syrian", "syria": "Syrian",
        "saudi": "Saudi Arabian", "saudi arabia": "Saudi Arabian",
        "yemeni": "Yemeni", "yemen": "Yemeni",
        "israeli": "Israeli", "israel": "Israeli",
        "palestinian": "Palestinian", "palestinian cuisine": "Palestinian", "palestine": "Palestinian",
        "jordanian": "Jordanian", "jordan": "Jordanian",
        "jewish": "Jewish", "jewish cuisine": "Jewish",
        "kurdish": "Kurdish", "kurdish cuisine": "Kurdish", "kurdistan": "Kurdish",
        "irish": "Irish", "ireland": "Irish",
        "austrian": "Austrian", "austrian cuisine": "Austrian", "austria": "Austrian",
        "belgian": "Belgian", "belgium": "Belgian", "cuisine of belgium": "Belgian",
        "dutch": "Dutch", "dutch cuisine": "Dutch", "netherlands": "Dutch",
        "luxembourgish": "Luxembourgish", "luxembourg": "Luxembourgish",
        "serbian": "Serbian", "serbia": "Serbian",
        "croatian": "Croatian", "croatia": "Croatian",
        "slovenian": "Slovenian", "slovenia": "Slovenian",
        "bosnian": "Bosnian", "bosnia and herzegovina": "Bosnian",
        "bulgarian": "Bulgarian", "bulgarian cuisine": "Bulgarian", "bulgaria": "Bulgarian",
        "albanian": "Albanian", "albanian cuisine": "Albanian", "albania": "Albanian",
        "estonian": "Estonian", "estonia": "Estonian",
        "latvian": "Latvian", "latvia": "Latvian",
        "lithuanian": "Lithuanian", "lithuanian cuisine": "Lithuanian", "lithuania": "Lithuanian",
        "belarusian": "Belarusian", "belarusian cuisine": "Belarusian", "belarus": "Belarusian",
        "moldovan": "Moldovan", "moldova": "Moldovan",
        "montenegrin": "Montenegrin", "montenegro": "Montenegrin",
        "kosovar": "Kosovar", "kosovo": "Kosovar",
        "north macedonian": "North Macedonian", "north macedonia": "North Macedonian",
        "slovak": "Slovak", "slovakia": "Slovak",
        "maltese": "Maltese", "malta": "Maltese",
        "cypriot": "Cypriot", "cyprus": "Cypriot",
        "mongolian": "Mongolian", "mongolia": "Mongolian",
        "kazakh": "Kazakh", "kazakh cuisine": "Kazakh", "kazakhstan": "Kazakh",
        "uzbek": "Uzbek", "uzbekistan": "Uzbek",
        "kyrgyz": "Kyrgyz", "kyrgyzstan": "Kyrgyz",
        "tajik": "Tajik", "tajikistan": "Tajik",
        "polynesian": "Polynesian",
        "australian": "Australian", "australia": "Australian",
        "new zealand": "New Zealand",
        "canadian": "Canadian", "canada": "Canadian",
        "central asian": "Central Asian", "central asia": "Central Asian",
        "eastern european": "Eastern European", "eastern europe": "Eastern European",
        "southeast asian": "Southeast Asian",
        "nepali": "Nepali", "nepal": "Nepali",
        "sri lankan": "Sri Lankan", "sri lanka": "Sri Lankan",
        "bangladeshi": "Bangladeshi", "bangladesh": "Bangladeshi",
        "pakistani": "Pakistani", "pakistan": "Pakistani",
        "afghan": "Afghan", "afghanistan": "Afghan",
        "bhutanese": "Bhutanese", "bhutan": "Bhutanese",
    }

    # Aggregate food counts
    c.execute(
        'SELECT tag_value, COUNT(DISTINCT food_id) FROM food_tags WHERE tag_category = "cuisine" GROUP BY tag_value'
    )
    raw = c.fetchall()

    consolidated = {}
    for tag_val, count in raw:
        key = normalize.get(tag_val.lower(), tag_val)
        consolidated[key] = consolidated.get(key, 0) + count

    # Map recipe counts dynamically for all cuisines
    # Build recipe_map by matching canonical cuisine names to lowercase keys in recipe tables
    recipe_map = {}

    # All canonical cuisine names used in the region_map below
    all_cuisines = set()
    _region_map = {
        "East Asia": ["Chinese", "Japanese", "Korean", "Taiwanese", "Mongolian"],
        "Southeast Asia": ["Indonesian", "Thai", "Vietnamese", "Filipino", "Malaysian",
                          "Singaporean", "Cambodian", "Burmese", "Laotian", "Southeast Asian"],
        "South Asia": ["Indian", "Pakistani", "Bangladeshi", "Sri Lankan", "Nepali",
                       "Afghan", "Bhutanese"],
        "Central Asia": ["Kazakh", "Uzbek", "Kyrgyz", "Tajik", "Central Asian"],
        "Middle East": ["Turkish", "Iranian", "Iraqi", "Syrian", "Lebanese", "Israeli",
                       "Palestinian", "Jordanian", "Saudi Arabian", "Yemeni", "Kurdish",
                       "Middle Eastern", "Jewish"],
        "North Africa": ["Moroccan", "Tunisian", "Algerian", "Egyptian", "Libyan"],
        "Sub-Saharan Africa": ["Nigerian", "Ghanaian", "Ethiopian", "Senegalese",
                               "South African", "Kenyan", "Ugandan", "Cameroonian", "Pan-African"],
        "Western Europe": ["French", "Italian", "Spanish", "Portuguese", "Belgian",
                          "Dutch", "Luxembourgish", "Swiss", "Austrian", "German",
                          "British", "Irish"],
        "Northern Europe": ["Scandinavian", "Swedish", "Norwegian", "Danish", "Finnish", "Icelandic"],
        "Eastern Europe": ["Russian", "Polish", "Ukrainian", "Czech", "Hungarian",
                          "Romanian", "Bulgarian", "Serbian", "Croatian", "Slovenian",
                          "Bosnian", "Albanian", "Estonian", "Latvian", "Lithuanian",
                          "Belarusian", "Moldovan", "Slovak", "Montenegrin", "Kosovar",
                          "North Macedonian", "Georgian", "Armenian", "Azerbaijani",
                          "Eastern European"],
        "Southern Europe": ["Greek", "Maltese", "Cypriot", "Mediterranean"],
        "North America": ["American", "American (Southern)", "American (Cajun/Creole)",
                         "American (Tex-Mex)", "Canadian"],
        "Central America & Caribbean": ["Cuban", "Jamaican", "Haitian", "Trinidadian",
                                        "Puerto Rican", "Caribbean"],
        "South America": ["Brazilian", "Argentine", "Peruvian", "Chilean", "Colombian",
                         "Venezuelan", "Bolivian", "Paraguayan", "Uruguayan", "Ecuadorian",
                         "Latin American"],
        "Oceania": ["Australian", "New Zealand", "Polynesian"],
    }
    for cuisines_list in _region_map.values():
        all_cuisines.update(cuisines_list)

    # Special mappings for cuisines whose lowercase name differs from recipe key
    special_keys = {
        "American (Cajun/Creole)": ["cajun", "american (cajun/creole)"],
        "American (Southern)": ["american (southern)", "southern us"],
        "American (Tex-Mex)": ["american (tex-mex)", "tex-mex"],
        "Pan-African": ["pan-african", "african"],
        "North Macedonian": ["north macedonian"],
    }

    for cuisine_name in all_cuisines:
        keys_to_check = special_keys.get(cuisine_name, [cuisine_name.lower()])
        total = 0
        for key in keys_to_check:
            total += large_r.get(key, 0) + small_r.get(key, 0)
        recipe_map[cuisine_name] = total

    # Region grouping
    region_map = {
        "East Asia": ["Chinese", "Japanese", "Korean", "Taiwanese", "Mongolian"],
        "Southeast Asia": ["Indonesian", "Thai", "Vietnamese", "Filipino", "Malaysian",
                          "Singaporean", "Cambodian", "Burmese", "Laotian", "Southeast Asian"],
        "South Asia": ["Indian", "Pakistani", "Bangladeshi", "Sri Lankan", "Nepali",
                       "Afghan", "Bhutanese"],
        "Central Asia": ["Kazakh", "Uzbek", "Kyrgyz", "Tajik", "Central Asian"],
        "Middle East": ["Turkish", "Iranian", "Iraqi", "Syrian", "Lebanese", "Israeli",
                       "Palestinian", "Jordanian", "Saudi Arabian", "Yemeni", "Kurdish",
                       "Middle Eastern", "Jewish"],
        "North Africa": ["Moroccan", "Tunisian", "Algerian", "Egyptian", "Libyan"],
        "Sub-Saharan Africa": ["Nigerian", "Ghanaian", "Ethiopian", "Senegalese",
                               "South African", "Kenyan", "Ugandan", "Cameroonian", "Pan-African"],
        "Western Europe": ["French", "Italian", "Spanish", "Portuguese", "Belgian",
                          "Dutch", "Luxembourgish", "Swiss", "Austrian", "German",
                          "British", "Irish"],
        "Northern Europe": ["Scandinavian", "Swedish", "Norwegian", "Danish", "Finnish", "Icelandic"],
        "Eastern Europe": ["Russian", "Polish", "Ukrainian", "Czech", "Hungarian",
                          "Romanian", "Bulgarian", "Serbian", "Croatian", "Slovenian",
                          "Bosnian", "Albanian", "Estonian", "Latvian", "Lithuanian",
                          "Belarusian", "Moldovan", "Slovak", "Montenegrin", "Kosovar",
                          "North Macedonian", "Georgian", "Armenian", "Azerbaijani",
                          "Eastern European"],
        "Southern Europe": ["Greek", "Maltese", "Cypriot", "Mediterranean"],
        "North America": ["American", "American (Southern)", "American (Cajun/Creole)",
                         "American (Tex-Mex)", "Canadian"],
        "Central America & Caribbean": ["Cuban", "Jamaican", "Haitian", "Trinidadian",
                                        "Puerto Rican", "Caribbean"],
        "South America": ["Brazilian", "Argentine", "Peruvian", "Chilean", "Colombian",
                         "Venezuelan", "Bolivian", "Paraguayan", "Uruguayan", "Ecuadorian",
                         "Latin American"],
        "Oceania": ["Australian", "New Zealand", "Polynesian"],
    }

    print("=" * 90)
    print("WORLD CUISINE REPORT: FOOD CATALOG vs RECIPE COVERAGE")
    print("=" * 90)

    total_recipes_needed = 0
    cuisines_covered = 0
    cuisines_needing = 0

    for region, cuisines in region_map.items():
        region_foods = 0
        region_recipes = 0
        region_items = []

        for cuisine in cuisines:
            foods = consolidated.get(cuisine, 0)
            if foods == 0:
                continue
            recipes = recipe_map.get(cuisine, 0)
            region_foods += foods
            region_recipes += recipes

            if recipes > 0:
                status = f"{recipes} recipes"
                cuisines_covered += 1
            else:
                status = "NEED RECIPES"
                cuisines_needing += 1
                total_recipes_needed += min(foods, 30)

            region_items.append((cuisine, foods, recipes, status))

        if not region_items:
            continue

        print(f"\n{'=' * 90}")
        print(f"  {region.upper():40s}  |  {region_foods} foods  |  {region_recipes} recipes")
        print(f"{'=' * 90}")
        print(f"  {'Cuisine':30s} | {'Foods':>7s} | {'Recipes':>8s} | Status")
        print(f"  {'-' * 80}")

        for cuisine, foods, recipes, status in sorted(region_items, key=lambda x: x[1], reverse=True):
            print(f"  {cuisine:30s} | {foods:7d} | {recipes:8d} | {status}")

    print(f"\n{'=' * 90}")
    print(f"SUMMARY")
    print(f"{'=' * 90}")
    print(f"  Cuisines with recipe coverage:  {cuisines_covered}")
    print(f"  Cuisines needing recipes:       {cuisines_needing}")
    print(f"  Estimated recipes to source:    ~{total_recipes_needed}")
    print(f"  Total foods in catalog:         {sum(consolidated.values())}")
    print(f"  Total recipes (small):          {sum(small_r.values())}")
    print(f"  Total recipes (large):          {sum(large_r.values())}")

    conn.close()


if __name__ == "__main__":
    main()
