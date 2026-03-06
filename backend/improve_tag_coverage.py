"""
improve_tag_coverage.py
-----------------------
Scans food names and descriptions to extract additional tags for under-tagged foods.
Uses regex patterns for cuisine, cooking_method, flavor_profile, dietary, course, and texture.
All new tags are inserted with source='text_enrichment' and INSERT OR IGNORE to avoid duplicates.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import sqlite3
import re
from collections import defaultdict

DB_PATH = "food.db"
SOURCE = "text_enrichment"
CONFIDENCE = 0.8  # slightly lower than manually curated tags


# ────────────────────────────────────────────────────────────
#  1.  CUISINE PATTERNS
# ────────────────────────────────────────────────────────────
# Maps regex pattern (applied to BOTH name and description, case-insensitive)
# to the normalised cuisine tag value.

CUISINE_PATTERNS = {
    # East Asia
    r"\b(chinese|china|cantonese|sichuan|szechuan|hunan|shandong|fujian|guangdong|shanghainese|beijing|peking|dim\s*sum|wonton|chow\s*mein|lo\s*mein|kung\s*pao|mapo)\b": "Chinese",
    r"\b(japanese|japan|sushi|sashimi|ramen|tempura|teriyaki|yakitori|udon|soba|miso|onigiri|bento|okonomiyaki|takoyaki|matcha|wasabi|izakaya|donburi|gyudon)\b": "Japanese",
    r"\b(korean|korea|kimchi|bibimbap|bulgogi|gochujang|tteok|japchae|samgyeopsal|galbi|jjigae|banchan)\b": "Korean",
    r"\b(taiwan(?:ese)?|bubble\s*tea|boba)\b": "Taiwanese",

    # Southeast Asia
    r"\b(thai(?:land)?|pad\s*thai|tom\s*yum|tom\s*kha|green\s*curry|massaman|som\s*tam|satay)\b": "Thai",
    r"\b(vietnam(?:ese)?|pho|banh\s*mi|bun\s*cha|spring\s*roll|vietnamese)\b": "Vietnamese",
    r"\b(indonesian?|nasi\s*goreng|rendang|satay|tempeh|sambal|gado.?gado|soto|bakso|nasi\s*padang|javanese|balinese|sundanese)\b": "Indonesian",
    r"\b(malay(?:sian)?|laksa|nasi\s*lemak|roti\s*canai|char\s*kway\s*teow)\b": "Malaysian",
    r"\b(filipino|filipin[oa]|philippine|adobo|sinigang|lumpia|lechon|kare.?kare|pancit)\b": "Filipino",
    r"\b(cambodian|khmer|amok)\b": "Cambodian",
    r"\b(burmese|myanmar|mohinga)\b": "Burmese",
    r"\b(singaporean|singapore)\b": "Singaporean",

    # South Asia
    r"\b(indian|india|tandoori|naan|biryani|masala|tikka|paneer|dal|dhal|samosa|chutney|korma|vindaloo|rogan\s*josh|rajasthani|gujarati|punjabi|goan|keralite|kerala|tamil|hyderabadi|mughlai|chettinad|awadhi)\b": "Indian",
    r"\b(bengali|bengal|bangladesh[i]?)\b": "Bengali",
    r"\b(sri\s*lank(?:an|a))\b": "Sri Lankan",
    r"\b(pakistan[i]?|nihari|haleem)\b": "Pakistani",
    r"\b(nepal(?:i|ese)?|momo|dal\s*bhat)\b": "Nepalese",

    # Middle East
    r"\b(middle\s*east(?:ern)?|lebanese|lebanon|hummus|falafel|tabbouleh|shawarma|kibbeh)\b": "Middle Eastern",
    r"\b(turkish|turkey|kebab|baklava|börek|pide|lahmacun|manti|doner)\b": "Turkish",
    r"\b(persian|iran(?:ian)?|tahdig|ghormeh|fesenjan|koobideh)\b": "Persian",
    r"\b(arab(?:ic|ian)?|saudi|emirati|uae)\b": "Arabian",
    r"\b(israeli|israel)\b": "Israeli",
    r"\b(palestinian|palestine)\b": "Palestinian",
    r"\b(syrian?|syria)\b": "Syrian",
    r"\b(iraqi?|iraq)\b": "Iraqi",

    # Europe
    r"\b(french|france|baguette|croissant|quiche|ratatouille|cassoulet|béchamel|béarnaise|provençal|bouillabaisse|crème|gratin|parisian|lyonnais[e]?|alsatian|breton|burgundy|normandy)\b": "French",
    r"\b(italian|italy|pasta|pizza|risotto|gnocchi|lasagna|pesto|tiramisu|gelato|bruschetta|prosciutto|ravioli|focaccia|polenta|milanese|neapolitan|sicilian|tuscan|roman|bolognese|carbonara|amatriciana)\b": "Italian",
    r"\b(spanish|spain|paella|tapas|gazpacho|chorizo|tortilla\s*española|jamón|andalusian|catalan|basque|galician)\b": "Spanish",
    r"\b(portuguese|portugal|bacalhau|pastel\s*de\s*nata|caldo\s*verde)\b": "Portuguese",
    r"\b(greek|greece|gyro|moussaka|souvlaki|tzatziki|spanakopita|dolma)\b": "Greek",
    r"\b(german|germany|bratwurst|pretzel|schnitzel|strudel|sauerkraut|bavarian|swabian)\b": "German",
    r"\b(british|england|english|scottish|scotland|welsh|wales|fish\s*and\s*chips|yorkshire|cornish|shepherd'?s?\s*pie)\b": "British",
    r"\b(irish|ireland|colcannon|boxty|coddle|soda\s*bread)\b": "Irish",
    r"\b(dutch|netherlands|holland|stroopwafel)\b": "Dutch",
    r"\b(belgian?|belgium|waffle)\b": "Belgian",
    r"\b(swiss|switzerland|fondue|raclette|rösti)\b": "Swiss",
    r"\b(austrian?|austria|wiener|sachertorte)\b": "Austrian",
    r"\b(polish|poland|pierogi|bigos|żurek)\b": "Polish",
    r"\b(hungarian?|hungary|goulash|paprikash)\b": "Hungarian",
    r"\b(czech|bohemian|svíčková)\b": "Czech",
    r"\b(romanian?|romania|sarmale|mici)\b": "Romanian",
    r"\b(russian?|russia|borscht|blini|pelmeni|stroganoff|piroshki)\b": "Russian",
    r"\b(ukrainian?|ukraine|varenyky|borscht)\b": "Ukrainian",
    r"\b(scandinavian|nordic|swedish|sweden|norwegian|norway|danish|denmark|finnish|finland|smörgåsbord|gravlax|lutefisk|smørrebrød)\b": "Scandinavian",

    # Americas
    r"\b(mexican|mexico|taco|burrito|enchilada|quesadilla|tamale|mole|guacamole|salsa|pozole|chilaquiles|tostada|oaxacan)\b": "Mexican",
    r"\b(peruvian|peru|ceviche|lomo\s*saltado|aji)\b": "Peruvian",
    r"\b(brazilian|brazil|feijoada|açaí|pão\s*de\s*queijo|churrasco)\b": "Brazilian",
    r"\b(argentin[ea]|argentina|empanada|asado|chimichurri)\b": "Argentinian",
    r"\b(colombian|colombia|arepa|bandeja\s*paisa)\b": "Colombian",
    r"\b(cuban|cuba|ropa\s*vieja|cubano)\b": "Cuban",
    r"\b(caribbean|jamaican|jamaica|jerk\s*chicken|jerk|trinidadian|barbadian|haitian|puerto\s*rican)\b": "Caribbean",
    r"\b(cajun|creole|louisiana|gumbo|jambalaya|crawfish|etouffee)\b": "Cajun/Creole",
    r"\b(southern\s*(?:us|american)|soul\s*food|fried\s*chicken|cornbread|grits|collard|biscuits\s*and\s*gravy)\b": "Southern US",
    r"\b(tex.?mex)\b": "Tex-Mex",
    r"\b(hawaiian|hawaii|poke|loco\s*moco|kalua|luau|polynesian)\b": "Hawaiian",
    r"\b(canadian|canada|poutine|nanaimo|tourtière)\b": "Canadian",

    # Africa
    r"\b(nigerian?|nigeria|jollof|egusi|suya|pounded\s*yam|fufu|amala)\b": "Nigerian",
    r"\b(ethiopian?|ethiopia|injera|doro\s*wat|kitfo)\b": "Ethiopian",
    r"\b(moroccan|morocco|tagine|couscous|harissa|pastilla)\b": "Moroccan",
    r"\b(egyptian|egypt|koshari|ful\s*medames)\b": "Egyptian",
    r"\b(south\s*african|south\s*africa|biltong|bobotie|braai|boerewors)\b": "South African",
    r"\b(ghanaian|ghana|kenkey|banku|waakye)\b": "Ghanaian",
    r"\b(kenyan|kenya|ugali|nyama\s*choma)\b": "Kenyan",
    r"\b(senegalese|senegal|thieboudienne)\b": "Senegalese",
    r"\b(tunisian|tunisia|brik|shakshuka)\b": "Tunisian",
    r"\b(west\s*african)\b": "West African",
    r"\b(east\s*african)\b": "East African",
    r"\b(north\s*african)\b": "North African",

    # Central / Other Asia
    r"\b(tibetan|tibet|tsampa|thukpa)\b": "Tibetan",
    r"\b(mongolian|mongolia)\b": "Mongolian",
    r"\b(afghan[i]?|afghanistan|mantu|kabuli)\b": "Afghan",
    r"\b(uzbek|uzbekistan|plov|samsa)\b": "Uzbek",
    r"\b(georgian|georgia|khachapuri|khinkali)\b": "Georgian",
    r"\b(armenian|armenia|lavash)\b": "Armenian",

    # Oceania
    r"\b(australian|australia|vegemite|lamington|pavlova|meat\s*pie)\b": "Australian",
    r"\b(new\s*zealand|kiwi|hangi)\b": "New Zealand",
}

# Compile cuisine patterns once
CUISINE_COMPILED = [(re.compile(pat, re.IGNORECASE), val) for pat, val in CUISINE_PATTERNS.items()]


# ────────────────────────────────────────────────────────────
#  2.  COOKING METHOD PATTERNS
# ────────────────────────────────────────────────────────────
COOKING_METHOD_MAP = {
    "baked":     [r"\bbak(?:ed|ing|e)\b"],
    "fried":     [r"\b(?:deep[- ]?)?fri(?:ed|es|y|ying)\b", r"\bpan[- ]?fri(?:ed|es)\b"],
    "deep-fried":[r"\bdeep[- ]?fri(?:ed|es|y)\b"],
    "stir-fried":[r"\bstir[- ]?fri(?:ed|es|y)\b", r"\bwok[- ]?fri(?:ed)\b"],
    "grilled":   [r"\bgrill(?:ed|ing|s)?\b", r"\bchar[- ]?grill(?:ed)?\b", r"\bbbq\b", r"\bbarbe[cq]u(?:ed|e)?\b"],
    "steamed":   [r"\bsteam(?:ed|ing|s)?\b"],
    "boiled":    [r"\bboil(?:ed|ing|s)?\b", r"\bsimmer(?:ed|ing)?\b"],
    "braised":   [r"\bbrais(?:ed|ing|e)\b"],
    "roasted":   [r"\broast(?:ed|ing|s)?\b", r"\bspit[- ]?roast(?:ed)?\b"],
    "smoked":    [r"\bsmok(?:ed|ing|e|y)\b", r"\bhot[- ]?smok(?:ed)\b", r"\bcold[- ]?smok(?:ed)\b"],
    "pickled":   [r"\bpickl(?:ed|ing|e)\b"],
    "fermented": [r"\bferment(?:ed|ing|ation)?\b", r"\bcult?ur(?:ed)\b"],
    "raw":       [r"\braw\b", r"\buncooked\b", r"\bcarpaccio\b", r"\btartare?\b", r"\bcrudo\b"],
    "dried":     [r"\bdri(?:ed|y|ying)\b", r"\bdehydrat(?:ed|ing)\b", r"\bsun[- ]?dried\b", r"\bair[- ]?dried\b"],
    "cured":     [r"\bcur(?:ed|ing|e)\b"],
    "stewed":    [r"\bstew(?:ed|ing|s)?\b"],
    "poached":   [r"\bpoach(?:ed|ing)\b"],
    "marinated": [r"\bmarinat(?:ed|ing|e)\b"],
    "sauteed":   [r"\bsaut[ée](?:ed|ing|é)?\b", r"\bsauteed\b"],
    "blanched":  [r"\bblanch(?:ed|ing)\b"],
    "toasted":   [r"\btoast(?:ed|ing)?\b"],
    "slow-cooked":[r"\bslow[- ]?cook(?:ed|ing)?\b", r"\bcrock[- ]?pot\b"],
    "pressure-cooked":[r"\bpressure[- ]?cook(?:ed|ing)?\b"],
}

# Compile
COOKING_COMPILED = {}
for method, patterns in COOKING_METHOD_MAP.items():
    COOKING_COMPILED[method] = [re.compile(p, re.IGNORECASE) for p in patterns]


# ────────────────────────────────────────────────────────────
#  3.  FLAVOR PROFILE PATTERNS
# ────────────────────────────────────────────────────────────
FLAVOR_MAP = {
    "sweet":    [r"\bsweet(?:ened|ness)?\b", r"\bsugary\b", r"\bhoney(?:ed)?\b", r"\bcaramel(?:ized)?\b", r"\bsyrup(?:y)?\b"],
    "sour":     [r"\bsour(?:ness)?\b", r"\btart(?:ness)?\b", r"\bacidic\b", r"\btangy\b", r"\bvinegar(?:y)?\b", r"\bcitrus(?:y)?\b"],
    "salty":    [r"\bsalty\b", r"\bbriny\b", r"\bsalted\b"],
    "bitter":   [r"\bbitter(?:ness|sweet)?\b"],
    "umami":    [r"\bumami\b", r"\bsavory\b", r"\bsavoury\b", r"\bmeaty\b", r"\bbrothy\b"],
    "spicy":    [r"\bspic(?:y|ed|iness)\b", r"\bhot\s+(?:pepper|chil[il]?[ie]?)\b", r"\bpungent\b", r"\bfiery\b", r"\bchili\b", r"\bchilli\b", r"\bcayenne\b", r"\bjalapeño\b", r"\bhabanero\b"],
    "savory":   [r"\bsavo(?:ry|ury)\b", r"\bherb(?:y|al|aceous)\b"],
    "rich":     [r"\brich(?:ness)?\b", r"\bindulgent\b", r"\bdecadent\b", r"\bluscious\b"],
    "mild":     [r"\bmild(?:ly)?\b", r"\bgentle\b", r"\bsubtle\b", r"\bdelicate\b"],
    "smoky":    [r"\bsmok(?:y|ey|iness)\b"],
    "tangy":    [r"\btangy\b", r"\bzesty\b", r"\bzing(?:y)?\b"],
    "nutty":    [r"\bnutty\b", r"\bnut[- ]?flavou?red\b"],
    "earthy":   [r"\bearthy\b", r"\bmushroomy\b"],
    "fruity":   [r"\bfruity\b"],
    "aromatic": [r"\baromatic\b", r"\bfragrant\b", r"\bperfumed\b"],
    "garlicky": [r"\bgarlick?y\b"],
    "buttery":  [r"\bbuttery\b"],
    "peppery":  [r"\bpepper(?:y|iness)\b"],
}

FLAVOR_COMPILED = {}
for flavor, patterns in FLAVOR_MAP.items():
    FLAVOR_COMPILED[flavor] = [re.compile(p, re.IGNORECASE) for p in patterns]


# ────────────────────────────────────────────────────────────
#  4.  DIETARY PATTERNS
# ────────────────────────────────────────────────────────────
DIETARY_MAP = {
    "vegetarian":  [r"\bvegetarian\b", r"\bmeatless\b", r"\bmeat[- ]?free\b"],
    "vegan":       [r"\bvegan\b", r"\bplant[- ]?based\b"],
    "gluten-free": [r"\bgluten[- ]?free\b", r"\bceliac\b", r"\bcoeliac\b"],
    "halal":       [r"\bhalal\b"],
    "kosher":      [r"\bkosher\b"],
    "dairy-free":  [r"\bdairy[- ]?free\b", r"\blactose[- ]?free\b", r"\bnon[- ]?dairy\b"],
    "nut-free":    [r"\bnut[- ]?free\b", r"\bpeanut[- ]?free\b"],
    "sugar-free":  [r"\bsugar[- ]?free\b", r"\bno[- ]?sugar\b"],
    "low-carb":    [r"\blow[- ]?carb\b", r"\bketo\b", r"\bketogenic\b"],
    "paleo":       [r"\bpaleo\b"],
    "organic":     [r"\borganic\b"],
    "whole grain": [r"\bwhole[- ]?grain\b", r"\bwhole[- ]?wheat\b"],
}

DIETARY_COMPILED = {}
for diet, patterns in DIETARY_MAP.items():
    DIETARY_COMPILED[diet] = [re.compile(p, re.IGNORECASE) for p in patterns]


# ────────────────────────────────────────────────────────────
#  5.  COURSE PATTERNS
# ────────────────────────────────────────────────────────────
COURSE_MAP = {
    "appetizer":   [r"\bappetiz(?:er|ing)\b", r"\bstarter\b", r"\bhors\s*d'?oeuvre\b", r"\bantipast[oi]\b", r"\bmeze\b", r"\btapas\b"],
    "main course": [r"\bmain\s*(?:course|dish|meal)\b", r"\bentr[ée]e\b"],
    "side dish":   [r"\bside\s*dish\b", r"\bside\s*order\b", r"\baccompaniment\b", r"\bgarnish\b"],
    "dessert":     [r"\bdessert\b", r"\bsweet\s*(?:course|dish|treat)\b", r"\bpastry\b", r"\bcake\b", r"\bpudding\b", r"\bpie\b", r"\btart\b", r"\bcookie\b", r"\bbiscuit\b", r"\bconfection(?:ery)?\b", r"\bice\s*cream\b", r"\bchocolate\b"],
    "snack":       [r"\bsnack\b", r"\bstreet\s*food\b", r"\bfinger\s*food\b", r"\bchips?\b"],
    "condiment":   [r"\bcondiment\b", r"\brelish\b", r"\bchutney\b", r"\bketchup\b", r"\bmustard\b"],
    "sauce":       [r"\bsauce\b", r"\bgravy\b", r"\bdressing\b", r"\bvinaigrette\b", r"\baioli\b", r"\bmayonnaise\b"],
    "beverage":    [r"\bbeverage\b", r"\bdrink\b", r"\bjuice\b", r"\btea\b", r"\bcoffee\b", r"\bsmoothie\b", r"\bcocktail\b", r"\blemonade\b", r"\bale\b", r"\bbeer\b", r"\bwine\b", r"\bspirits?\b", r"\bliqueur\b"],
    "soup":        [r"\bsoup\b", r"\bbroth\b", r"\bbisque\b", r"\bchowder\b", r"\bpottage\b", r"\bconsommé\b", r"\bstew\b"],
    "salad":       [r"\bsalad\b", r"\bslaw\b"],
    "bread":       [r"\bbread\b", r"\bflatbread\b", r"\bloaf\b", r"\broll[s]?\b", r"\bbaguette\b", r"\bciabatta\b", r"\bnaan\b", r"\bpita\b", r"\btortilla\b", r"\bchapati\b", r"\broti\b"],
    "sandwich":    [r"\bsandwich\b", r"\bwrap\b", r"\bburger\b", r"\bsub\b", r"\bpanini\b", r"\bhotdog\b", r"\bhot\s*dog\b"],
    "pasta":       [r"\bpasta\b", r"\bnoodle\b", r"\bspaghetti\b", r"\bpenne\b", r"\bfettuccin[ei]\b", r"\blinguine\b", r"\bmacaroni\b", r"\budon\b", r"\bramen\b", r"\bpho\b", r"\bvermicelli\b"],
    "rice dish":   [r"\brice\s*dish\b", r"\bbiryani\b", r"\brisotto\b", r"\bpilaf\b", r"\bfried\s*rice\b", r"\bnasi\b", r"\bpaella\b", r"\bplov\b", r"\bjollof\b"],
    "dumpling":    [r"\bdumpling\b", r"\bgyoza\b", r"\bpierogi\b", r"\bravioli\b", r"\bmanti\b", r"\bmomo\b", r"\bwonton\b", r"\bsamosa\b", r"\bempanada\b"],
    "curry":       [r"\bcurry\b", r"\bmasala\b", r"\bkorma\b", r"\bvindaloo\b"],
    "porridge":    [r"\bporridge\b", r"\bgruel\b", r"\bcongee\b", r"\boatmeal\b", r"\bgrits\b"],
    "pastry":      [r"\bpastry\b", r"\bcroissant\b", r"\bdanish\b", r"\béclair\b", r"\bpuff\b", r"\bstrudel\b", r"\bphyllo\b", r"\bfilo\b"],
    "breakfast":   [r"\bbreakfast\b", r"\bbrunch\b", r"\bmorning\s*meal\b", r"\bcereal\b", r"\bpancake\b", r"\bwaffle\b", r"\bomelet(?:te)?\b"],
    "preserve":    [r"\bjam\b", r"\bjelly\b", r"\bmarmalade\b", r"\bpreserve[sd]?\b", r"\bcompote\b", r"\bconfit\b"],
    "dip":         [r"\bdip\b", r"\bspread\b", r"\bpâté\b", r"\bpate\b", r"\bhummus\b", r"\bguacamole\b", r"\btzatziki\b", r"\bsalsa\b"],
}

COURSE_COMPILED = {}
for course, patterns in COURSE_MAP.items():
    COURSE_COMPILED[course] = [re.compile(p, re.IGNORECASE) for p in patterns]


# ────────────────────────────────────────────────────────────
#  6.  TEXTURE PATTERNS
# ────────────────────────────────────────────────────────────
TEXTURE_MAP = {
    "crispy":  [r"\bcrisp(?:y|ed|iness)?\b", r"\bcrunchy\b"],
    "creamy":  [r"\bcream(?:y|iness)?\b", r"\bvelvety\b", r"\bsilky\b"],
    "chewy":   [r"\bchew(?:y|iness)\b", r"\bchewy\b"],
    "crunchy": [r"\bcrunchy\b", r"\bcrisp(?:y)?\b"],
    "smooth":  [r"\bsmooth\b"],
    "flaky":   [r"\bflak(?:y|ey|iness)\b"],
    "tender":  [r"\btender(?:ness)?\b", r"\bsucculent\b"],
    "soft":    [r"\bsoft(?:ness)?\b", r"\bfluffy\b", r"\blight\b"],
    "thick":   [r"\bthick(?:ness|ened)?\b", r"\bhearty\b", r"\bdense\b"],
    "thin":    [r"\bthin(?:ly)?\b", r"\bpaper[- ]?thin\b", r"\bwafer[- ]?thin\b"],
    "moist":   [r"\bmoist(?:ness|ure)?\b"],
    "dry":     [r"\bdry\b", r"\bdried\b"],
    "sticky":  [r"\bsticky\b", r"\bglutin(?:ous)\b", r"\bgooey\b"],
    "crumbly": [r"\bcrumbl(?:y|e)\b", r"\bfriable\b"],
    "gelatinous":[r"\bgelatin(?:ous)?\b", r"\bjelly[- ]?like\b"],
    "elastic": [r"\belastic\b", r"\bspringy\b", r"\bbouncy\b"],
    "grainy":  [r"\bgrainy\b", r"\bgritty\b", r"\bcoarse\b"],
    "airy":    [r"\bairy\b", r"\blight\s+and\s+fluffy\b"],
    "layered": [r"\blayered\b", r"\blaminated\b"],
    "juicy":   [r"\bjuicy\b"],
}

TEXTURE_COMPILED = {}
for texture, patterns in TEXTURE_MAP.items():
    TEXTURE_COMPILED[texture] = [re.compile(p, re.IGNORECASE) for p in patterns]


# ────────────────────────────────────────────────────────────
#  ALSO: use existing boolean columns for dietary tags
# ────────────────────────────────────────────────────────────


def match_any(text, compiled_patterns):
    """Return True if any compiled pattern matches in text."""
    for pat in compiled_patterns:
        if pat.search(text):
            return True
    return False


def collect_before_stats(conn):
    """Gather tag coverage stats before enrichment."""
    c = conn.cursor()

    stats = {}

    # Total foods
    c.execute("SELECT COUNT(*) FROM foods")
    stats["total_foods"] = c.fetchone()[0]

    # Total tags
    c.execute("SELECT COUNT(*) FROM food_tags")
    stats["total_tags"] = c.fetchone()[0]

    # Foods by tag count buckets
    c.execute("""
        SELECT
            SUM(CASE WHEN cnt = 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN cnt BETWEEN 1 AND 2 THEN 1 ELSE 0 END),
            SUM(CASE WHEN cnt >= 3 THEN 1 ELSE 0 END)
        FROM (
            SELECT f.id, COALESCE(t.cnt, 0) as cnt
            FROM foods f
            LEFT JOIN (SELECT food_id, COUNT(*) as cnt FROM food_tags GROUP BY food_id) t
            ON f.id = t.food_id
        )
    """)
    row = c.fetchone()
    stats["zero_tags"] = row[0]
    stats["one_two_tags"] = row[1]
    stats["three_plus_tags"] = row[2]

    # Per-category counts
    categories = ["cuisine", "cooking_method", "flavor_profile", "dietary", "course", "texture"]
    stats["category_coverage"] = {}
    for cat in categories:
        c.execute("SELECT COUNT(DISTINCT food_id) FROM food_tags WHERE tag_category=?", (cat,))
        covered = c.fetchone()[0]
        stats["category_coverage"][cat] = covered

    return stats


def print_stats(stats, label):
    """Pretty-print tag stats."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Total foods:              {stats['total_foods']:>8,}")
    print(f"  Total tags:               {stats['total_tags']:>8,}")
    print(f"  Foods with 0 tags:        {stats['zero_tags']:>8,}")
    print(f"  Foods with 1-2 tags:      {stats['one_two_tags']:>8,}")
    print(f"  Foods with 3+ tags:       {stats['three_plus_tags']:>8,}")
    print(f"\n  Category coverage (foods with at least 1 tag):")
    for cat, count in stats["category_coverage"].items():
        pct = 100.0 * count / stats["total_foods"] if stats["total_foods"] else 0
        print(f"    {cat:<20s}  {count:>7,}  ({pct:5.1f}%)")
    print(f"{'='*60}\n")


def enrich_tags(conn):
    """Main enrichment logic. Returns count of new tags inserted."""
    c = conn.cursor()

    # Load all foods with their name and description
    c.execute("SELECT id, name, description, is_vegetarian, is_vegan, is_gluten_free FROM foods")
    foods = c.fetchall()

    new_tags = []  # list of (food_id, tag_category, tag_value)

    for food_id, name, description, is_veg, is_vegan_flag, is_gf in foods:
        text = (name or "") + " " + (description or "")
        text_lower = text  # patterns are case-insensitive anyway

        # ── Cuisine ──
        for compiled_pat, cuisine_val in CUISINE_COMPILED:
            if compiled_pat.search(text_lower):
                new_tags.append((food_id, "cuisine", cuisine_val))

        # ── Cooking method ──
        for method, patterns in COOKING_COMPILED.items():
            if match_any(text_lower, patterns):
                new_tags.append((food_id, "cooking_method", method))

        # ── Flavor profile ──
        for flavor, patterns in FLAVOR_COMPILED.items():
            if match_any(text_lower, patterns):
                new_tags.append((food_id, "flavor_profile", flavor))

        # ── Dietary ──
        for diet, patterns in DIETARY_COMPILED.items():
            if match_any(text_lower, patterns):
                new_tags.append((food_id, "dietary", diet))

        # Also use the boolean columns from the foods table
        if is_veg:
            new_tags.append((food_id, "dietary", "vegetarian"))
        if is_vegan_flag:
            new_tags.append((food_id, "dietary", "vegan"))
        if is_gf:
            new_tags.append((food_id, "dietary", "gluten-free"))

        # ── Course ──
        for course, patterns in COURSE_COMPILED.items():
            if match_any(text_lower, patterns):
                new_tags.append((food_id, "course", course))

        # ── Texture ──
        for texture, patterns in TEXTURE_COMPILED.items():
            if match_any(text_lower, patterns):
                new_tags.append((food_id, "texture", texture))

    # Batch insert with INSERT OR IGNORE
    print(f"  Prepared {len(new_tags):,} candidate tag insertions.")

    inserted = 0
    batch_size = 500
    max_retries = 10
    for i in range(0, len(new_tags), batch_size):
        batch = new_tags[i:i+batch_size]
        for attempt in range(max_retries):
            try:
                c.executemany(
                    """INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source)
                       VALUES (?, ?, ?, ?, ?)""",
                    [(fid, cat, val, CONFIDENCE, SOURCE) for fid, cat, val in batch]
                )
                inserted += c.rowcount
                conn.commit()
                break
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    import time
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        if (i // batch_size) % 20 == 0:
            print(f"    ... processed {i + len(batch):,} / {len(new_tags):,}")

    print(f"  Actually inserted (new, non-duplicate): {inserted:,} tags.")
    return inserted


def cuisines_with_fewest_foods(conn, limit=20):
    """Show cuisines with the fewest linked foods."""
    c = conn.cursor()
    c.execute("""
        SELECT tag_value, COUNT(DISTINCT food_id) as cnt
        FROM food_tags WHERE tag_category='cuisine'
        GROUP BY tag_value ORDER BY cnt ASC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    print(f"\n  Cuisines with fewest foods (bottom {limit}):")
    for val, cnt in rows:
        print(f"    {val:<35s}  {cnt:>5}")


def lowest_coverage_categories(conn):
    """Show which tag categories have the lowest coverage."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM foods")
    total = c.fetchone()[0]
    c.execute("""
        SELECT tag_category, COUNT(DISTINCT food_id) as covered
        FROM food_tags GROUP BY tag_category ORDER BY covered ASC
    """)
    rows = c.fetchall()
    print(f"\n  Tag categories by coverage (ascending):")
    for cat, covered in rows:
        pct = 100.0 * covered / total if total else 0
        print(f"    {cat:<25s}  {covered:>7,} / {total:>7,}  ({pct:5.1f}%)")


def main():
    import shutil
    import os

    # Work on a copy to avoid lock conflicts with running servers
    work_db = DB_PATH + ".enrichment_work"
    if os.path.exists(work_db):
        os.remove(work_db)

    # Use sqlite3 backup API to get a clean copy (handles WAL properly)
    src_conn = sqlite3.connect(DB_PATH, timeout=60)
    src_conn.execute("PRAGMA busy_timeout=60000")
    dst_conn = sqlite3.connect(work_db)
    src_conn.backup(dst_conn)
    src_conn.close()
    dst_conn.close()

    conn = sqlite3.connect(work_db, timeout=30)
    conn.execute("PRAGMA journal_mode=DELETE")

    print("=" * 60)
    print("  TAG COVERAGE IMPROVEMENT SCRIPT")
    print("=" * 60)

    # ── BEFORE stats ──
    before = collect_before_stats(conn)
    print_stats(before, "BEFORE ENRICHMENT")

    cuisines_with_fewest_foods(conn)
    lowest_coverage_categories(conn)

    # ── Run enrichment ──
    print("\n>>> Running text-based tag enrichment...")
    new_count = enrich_tags(conn)

    # ── AFTER stats ──
    after = collect_before_stats(conn)
    print_stats(after, "AFTER ENRICHMENT")

    # ── Delta report ──
    print("=" * 60)
    print("  IMPROVEMENT SUMMARY")
    print("=" * 60)
    print(f"  New tags added:           {after['total_tags'] - before['total_tags']:>8,}")
    print(f"  Foods with 0 tags:        {before['zero_tags']:>8,}  ->  {after['zero_tags']:>8,}  (delta: {after['zero_tags'] - before['zero_tags']:+,})")
    print(f"  Foods with 1-2 tags:      {before['one_two_tags']:>8,}  ->  {after['one_two_tags']:>8,}  (delta: {after['one_two_tags'] - before['one_two_tags']:+,})")
    print(f"  Foods with 3+ tags:       {before['three_plus_tags']:>8,}  ->  {after['three_plus_tags']:>8,}  (delta: {after['three_plus_tags'] - before['three_plus_tags']:+,})")
    print(f"\n  Per-category improvement (foods covered):")
    for cat in before["category_coverage"]:
        b = before["category_coverage"][cat]
        a = after["category_coverage"][cat]
        delta = a - b
        print(f"    {cat:<20s}  {b:>7,}  ->  {a:>7,}  (+{delta:,})")

    cuisines_with_fewest_foods(conn, 15)
    lowest_coverage_categories(conn)

    conn.close()

    # Copy enriched DB back over the original
    print("\n>>> Copying enriched database back to original...")
    backup_path = DB_PATH + ".backup_before_enrichment"
    try:
        # Backup original first
        if not os.path.exists(backup_path):
            shutil.copy2(DB_PATH, backup_path)
            print(f"  Backup saved to {backup_path}")

        # Use SQLite backup API to write back (avoids lock issues with WAL)
        src = sqlite3.connect(work_db)
        dst = sqlite3.connect(DB_PATH, timeout=120)
        dst.execute("PRAGMA busy_timeout=120000")
        src.backup(dst)
        src.close()
        dst.close()
        print("  Successfully wrote enriched data back to food.db")
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            print(f"  WARNING: Could not write back to {DB_PATH} (locked by another process).")
            print(f"  The enriched database is available at: {work_db}")
            print(f"  To apply manually: copy {work_db} over {DB_PATH} when the server is stopped.")
        else:
            raise
    finally:
        # Clean up work file if copy succeeded
        if os.path.exists(work_db):
            try:
                os.remove(work_db)
            except Exception:
                pass

    print("\nDone.")


if __name__ == "__main__":
    main()
