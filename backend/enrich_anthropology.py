"""
Enrich the food database with anthropological, historical, and scientific context.

Pulls from Wikipedia articles on:
- Food history by culture/region
- Culinary anthropology
- Historical trade routes and ingredient diffusion
- Traditional food science (fermentation, preservation, etc.)
- Meal patterns across cultures

Populates:
- cultures (descriptions, eras, wikipedia links)
- culture_eras (historical periods with food characteristics)
- culture_meal_patterns (how cultures eat throughout the day)
- food_tags (historical_period, trade_route, staple_food, cooking_science, social_class, etc.)
"""

import re
import sqlite3
import sys
import time
import urllib.parse

import requests

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "food.db"
WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "LotusEaterFoodApp/1.0 python-requests"}


def wiki_extract(title, chars=3000):
    """Get the full intro + first sections of a Wikipedia article."""
    try:
        resp = requests.get(WIKI_API, params={
            "action": "query", "format": "json",
            "prop": "extracts", "explaintext": True,
            "exsectionformat": "plain",
            "exchars": chars,
            "titles": title,
        }, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            return page.get("extract", "")
    except Exception as e:
        print(f"  Wiki error for {title}: {e}")
    return ""


def wiki_sections(title):
    """Get section titles from a Wikipedia article."""
    try:
        resp = requests.get(WIKI_API, params={
            "action": "parse", "format": "json",
            "page": title, "prop": "sections",
        }, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        sections = resp.json().get("parse", {}).get("sections", [])
        return [(s["index"], s["line"], int(s["level"])) for s in sections]
    except Exception:
        return []


def wiki_section_text(title, section_index, chars=4000):
    """Get text of a specific section."""
    try:
        resp = requests.get(WIKI_API, params={
            "action": "query", "format": "json",
            "prop": "extracts", "explaintext": True,
            "exsectionformat": "plain", "exchars": chars,
            "titles": title,
            "exintro": False,
        }, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            return page.get("extract", "")
    except Exception:
        return ""


# ============================================================================
# CULTURE DATA: Historical food civilizations with eras and context
# ============================================================================

CULTURE_DATA = [
    # (name, culture_type, region, subregion, modern_countries, era_start, era_end,
    #  is_living, wiki_article, description, eras[])
    # eras: (era_name, start, end, food_characteristics, trade_routes, social_notes)

    # EAST ASIA
    ("Chinese civilization", "civilization", "East Asia", "China",
     "China, Taiwan, Singapore", -5000, None, 1,
     "Chinese cuisine",
     "One of the world's oldest continuous food traditions. Regional diversity spans Cantonese dim sum, Sichuan mala spice, Shandong seafood, Hunan heat, and Jiangsu refinement. Philosophy of food as medicine (yao shi tong yuan) shapes cooking.",
     [
         ("Neolithic & Bronze Age", -5000, -1000, "Millet and rice cultivation, soybean domestication, early fermentation (jiu/rice wine), bronze cooking vessels, ancestor offering foods", "Yellow River corridor, Yangtze delta", "Oracle bone inscriptions mention feasts and food offerings"),
         ("Imperial Classical Period", -1000, 600, "Soy sauce and tofu development, chopstick adoption, wok emerges, tea cultivation begins, Silk Road spice imports (cumin, sesame, coriander)", "Silk Road (Chang'an to Rome), maritime Southeast Asia routes", "Confucian dining etiquette codified; food hierarchy reflects social rank"),
         ("Tang-Song Golden Age", 600, 1279, "Restaurant culture emerges in Kaifeng/Hangzhou, noodle and dumpling proliferation, sophisticated tea ceremony (Lu Yu's Cha Jing), sugar refining imported from India", "Maritime Silk Road, Grand Canal internal trade", "World's first restaurant culture; food poetry and gastronomy literature flourish"),
         ("Yuan-Ming-Qing Dynasties", 1279, 1912, "Chili pepper arrives from Americas (~1570s), Manchu-Han Imperial Feast codified, regional 'Eight Great Cuisines' crystallize, stir-frying perfected with thin-walled woks", "Silver trade with Spanish Americas, Portuguese Macau, Zheng He voyages", "Elaborate court cuisine vs. peasant preservation techniques (pickling, drying, salting)"),
         ("Modern & Contemporary", 1912, None, "Communist era collective dining, Cultural Revolution simplification, post-1978 renaissance, street food revival, fusion with Western techniques", "Global Chinese diaspora", "Rapid urbanization transforms eating habits; food safety concerns drive reform"),
     ]),

    ("Japanese civilization", "civilization", "East Asia", "Japan",
     "Japan", -300, None, 1,
     "Japanese cuisine",
     "Washoku (traditional Japanese cuisine) is UNESCO Intangible Cultural Heritage. Built on rice, seasonal ingredients (shun), and umami. Aesthetic presentation (moritsuke) is inseparable from cooking.",
     [
         ("Jomon & Yayoi Periods", -300, 710, "Rice paddy cultivation from Korea, fermented fish (narezushi - ancestor of sushi), miso origins from Chinese jiang, seaweed harvesting, dashi-like broths", "Korean Peninsula cultural exchange", "Hunter-gatherer Jomon diet transitions to agricultural Yayoi; pit cooking, stone boiling"),
         ("Nara-Heian Court Era", 710, 1185, "Buddhist vegetarian cuisine (shojin ryori), formal court dining (daibankyo), sake brewing refined, Chinese tea culture adopted, soy sauce (shoyu) development", "Tang Dynasty China diplomatic missions, Buddhist monastery exchange", "Aristocratic cuisine separates from common food; seasonal awareness formalized"),
         ("Kamakura-Edo Warrior Era", 1185, 1868, "Zen Buddhist influence on kaiseki, sushi evolution (hayazushi/nigiri), tempura from Portuguese missionaries (1543), sakoku isolation crystallizes unique cuisine, dashi+shoyu+mirin holy trinity established", "Nanban trade (Portugal, Holland), Nagasaki as sole port", "Samurai frugality vs. merchant-class food culture (Edo food stalls)"),
         ("Meiji-Modern Era", 1868, None, "Western foods adopted (curry rice, ramen, tonkatsu), yoshoku cuisine emerges, post-WWII American influence, sushi goes global 1970s+, ramen becomes art form", "Forced opening by Perry, global trade integration", "Rapid modernization; gyushoku school lunch program shapes national palate"),
     ]),

    ("Indian civilization", "civilization", "South Asia", "Indian subcontinent",
     "India, Pakistan, Bangladesh, Sri Lanka, Nepal", -3000, None, 1,
     "Indian cuisine",
     "Arguably the world's most spice-complex cuisine. Shaped by Ayurvedic medicine, Hindu vegetarianism, Muslim Mughlai cooking, and British colonial exchange. Every region is essentially a separate cuisine.",
     [
         ("Indus Valley & Vedic Period", -3000, -500, "Wheat, barley, rice cultivation, dairy centrality (ghee, yogurt), early spice trade (black pepper, turmeric, ginger), Vedic fire-cooking rituals, ghee as sacred substance", "Indus Valley maritime trade with Mesopotamia", "Vedic texts prescribe food rules; cow becomes sacred; vegetarianism emerges"),
         ("Buddhist-Maurya-Gupta Classical", -500, 600, "Ahimsa (non-violence) expands vegetarianism, sugar cane refining invented, elaborate monastery cooking, spice combinations formalized in Ayurvedic texts, pickles and chutneys develop", "Spice route to Rome, Buddhist missionary routes to China/SE Asia", "Ashoka's vegetarianism influences court; Arthashastra mentions food regulation"),
         ("Medieval-Mughal Period", 600, 1757, "Mughlai cuisine arrives (biryani, kebabs, naan, tandoor), Persian-Indian fusion (korma, pulao), Portuguese bring chili peppers (~1500) which transform Indian cooking permanently, Sikh langar communal kitchen established", "Arab spice traders, Portuguese Goa, Mughal court connections to Persia/Central Asia", "Hindu-Muslim culinary fusion creates India's most celebrated dishes; chili pepper revolution"),
         ("Colonial & Modern", 1757, None, "British introduce tea plantation culture, Anglo-Indian fusion (kedgeree, mulligatawny, curry powder), post-independence regional pride movements, global Indian restaurant culture", "British East India Company, global Indian diaspora", "Curry becomes global; regional cuisines gain recognition; street food culture thrives"),
     ]),

    ("Korean civilization", "civilization", "East Asia", "Korean Peninsula",
     "South Korea, North Korea", -700, None, 1,
     "Korean cuisine",
     "Built on fermentation (kimchi, doenjang, gochujang), banchan side dishes, and communal eating. Korean food science of fermentation is among the most sophisticated globally.",
     [
         ("Three Kingdoms & Goryeo", -700, 1392, "Kimchi origins (without chili), soybean fermentation (doenjang/ganjang), Buddhist temple cuisine during Goryeo, rice becomes staple, Korean tea ceremony develops", "Chinese cultural exchange, Buddhist routes", "Buddhist vegetarian period shapes temple cuisine traditions still practiced"),
         ("Joseon Dynasty", 1392, 1897, "Royal court cuisine (surasang) codified, chili pepper arrives from Japan (~1600) transforming kimchi permanently, elaborate banchan system, medicinal food philosophy (yak-sik-dong-won)", "Japan (chili pepper), China (Confucian food etiquette)", "Confucian hierarchy dictates who eats what; royal cuisine has 12 banchan minimum"),
         ("Modern Era", 1897, None, "Japanese colonial influence (ramyeon origins), Korean War survival foods, 1988 Olympics globalizes Korean food, K-food wave (hallyu), gochujang goes global", "Japanese occupation, American military influence, K-wave global reach", "Rapid industrialization transforms food; convenience culture vs. slow-food revival"),
     ]),

    # SOUTHEAST ASIA
    ("Indonesian civilization", "civilization", "Southeast Asia", "Maritime Southeast Asia",
     "Indonesia", -2000, None, 1,
     "Indonesian cuisine",
     "World's largest archipelago cuisine with 300+ ethnic groups. Built on rice, coconut, fermented shrimp paste (terasi), and the Spice Islands' native nutmeg, clove, and mace.",
     [
         ("Hindu-Buddhist Kingdoms", -2000, 1500, "Rice terracing (Bali), coconut milk cooking, spice cultivation (nutmeg, clove, pepper native to Maluku), Indian spice trade influence, temple food offerings", "Maritime Spice Route, Indian Ocean trade with India and China", "Hindu-Buddhist food rituals still visible in Balinese offerings; Srivijaya as trade hub"),
         ("Islamic & Colonial Period", 1500, 1945, "Islam transforms dietary laws (halal), Portuguese/Dutch/VOC spice trade, chili pepper arrives, Padang restaurant system (nasi padang), Indo-European fusion cuisine", "VOC (Dutch East India Company), Portuguese Malacca route", "Spice Islands as center of global trade; colonialism shapes plantation agriculture"),
         ("Modern Indonesia", 1945, None, "National cuisine concept emerges, street food (warung) culture, tempeh as global superfood, rendang voted world's best food (CNN 2017), sambal as national condiment", "Global Indonesian diaspora, tourism in Bali", "Unity in diversity (Bhinneka Tunggal Ika) applies to food; 5,000+ traditional recipes documented"),
     ]),

    ("Thai civilization", "civilization", "Southeast Asia", "Mainland Southeast Asia",
     "Thailand", -1000, None, 1,
     "Thai cuisine",
     "Balance of five flavors: sweet, sour, salty, bitter, spicy. Never colonized, Thai cuisine evolved through voluntary adoption of Chinese, Indian, and European elements.",
     [
         ("Sukhothai-Ayutthaya Kingdoms", -1000, 1767, "Rice cultivation central, fish sauce (nam pla) from ancient fermentation, Indian curry spice influence, Chinese wok/noodle adoption, chili from Portuguese (~1550s)", "Indian Ocean trade, Chinese merchant communities, Portuguese missionaries", "Royal court cuisine distinct from common food; Chinese immigrants bring stir-fry technique"),
         ("Rattanakosin-Modern", 1767, None, "Bangkok street food capital of world, royal Thai cuisine preserved, Tom Yum/Green Curry become global icons, night market culture, Thai-Chinese fusion mainstream", "Never colonized; selective adoption, global Thai restaurant expansion post-1970s", "Only SE Asian nation never colonized; food diplomacy (Global Thai program sends chefs worldwide)"),
     ]),

    # MIDDLE EAST
    ("Persian/Iranian civilization", "civilization", "Middle East", "Iran",
     "Iran, Afghanistan, Tajikistan", -3000, None, 1,
     "Iranian cuisine",
     "One of the world's great mother cuisines. Persian polo (rice dishes), stews (khoresh), and the sweet-sour flavor balance influenced cooking from India to Spain.",
     [
         ("Ancient Persia (Achaemenid-Sassanid)", -3000, 651, "Saffron cultivation, qanat irrigation enables agriculture, elaborate royal feasts (Persepolis reliefs), pomegranate/walnut/herb centrality, ice houses (yakhchal) for preservation", "Royal Road (Susa to Sardis), Silk Road intersection, maritime trade to India", "Zoroastrian food purity laws; Nowruz (New Year) feast traditions; world's first refrigeration"),
         ("Islamic Golden Age", 651, 1500, "Kitab al-Tabikh (cookbook tradition), sugar refining spreads to Europe, distillation knowledge, Persian cooking masters in Abbasid Baghdad, polo rice technique perfected", "Baghdad as food knowledge center, Moorish Spain transfers", "Arab-Persian fusion creates template for entire Middle Eastern cuisine; cookbooks emerge as genre"),
         ("Safavid-Modern Iran", 1500, None, "Tea replaces coffee as national drink, rice culture intensifies (Caspian region), khoresh stew tradition, Nowruz haft-sin table codified, post-revolution simplification then revival", "Safavid trade networks, modern Iranian diaspora", "Food tied deeply to poetry and hospitality (ta'arof); seasonal eating patterns from Zoroastrian calendar"),
     ]),

    ("Turkish/Ottoman civilization", "civilization", "Middle East", "Anatolia",
     "Turkey, Northern Cyprus", -2000, None, 1,
     "Turkish cuisine",
     "Crossroads cuisine merging Central Asian nomadic traditions with Byzantine Greek, Persian, and Arab cooking. Ottoman imperial kitchen was the world's most elaborate for centuries.",
     [
         ("Central Asian Turkic Origins", -2000, 1071, "Nomadic dairy culture (yogurt, kumiss, kurut), grilled meats (kebab), wheat flatbreads, horse-based pastoral economy, fermented mare's milk", "Central Asian steppe routes", "Yogurt word comes from Turkish yoğurt; nomadic preservation techniques"),
         ("Seljuk & Ottoman Empire", 1071, 1922, "Imperial Topkapi kitchen fed 10,000 daily, baklava perfected, coffee culture born (1555 Istanbul), meze tradition, börek from Central Asian antecedents, olive oil cuisine of Aegean adopted", "Ottoman trade routes spanning 3 continents, Spice Bazaar (Istanbul)", "Most elaborate court cuisine in world history; guild system regulates food trades; coffee houses as social institutions"),
         ("Modern Turkish Republic", 1922, None, "Regionalism preserved (SE kebabs, Black Sea anchovy, Aegean olive oil, Istanbul cosmopolitan), breakfast culture (kahvaltı), street food (simit, döner, lahmacun), Turkish tea replaces coffee as daily drink", "NATO integration, German-Turkish exchange (döner kebab Berlin story)", "Breakfast is sacred meal; regional pride intense; gastro-tourism rising"),
     ]),

    # AFRICA
    ("West African civilization", "civilization", "Sub-Saharan Africa", "West Africa",
     "Nigeria, Ghana, Senegal, Mali, Cameroon, Benin, Togo", -3000, None, 1,
     "West African cuisine",
     "Foundation of African-American, Caribbean, and Brazilian cooking. Built on starchy staples (yam, cassava, plantain), palm oil, fermented locust beans (dawadawa), and communal eating.",
     [
         ("Ancient & Pre-Colonial", -3000, 1400, "Yam domestication (Nigeria), African rice (Oryza glaberrima) cultivation, palm oil extraction, shea butter, fermented foods (dawadawa, ogiri), guinea fowl domestication", "Trans-Saharan gold-salt trade, Nile-Niger connection", "Yam festivals as cultural cornerstone; communal pot cooking; oral recipe tradition"),
         ("Columbian Exchange & Colonial", 1400, 1960, "Cassava/maize/chili pepper arrive from Americas and TRANSFORM West African cooking, cocoa cultivation begins, peanut (groundnut) becomes staple, European colonial plantation economy", "Atlantic slave trade, Columbian Exchange, colonial trading posts", "Enslaved Africans bring food knowledge to Americas (okra, black-eyed peas, rice cultivation, deep-frying)"),
         ("Post-Independence Modern", 1960, None, "Jollof rice becomes pan-West African icon (Nigeria vs. Ghana rivalry), street food culture (suya, kelewele, accara), palm wine, fufu/pounded yam traditions preserved, diaspora cuisine recognition", "West African diaspora, Nollywood food culture, global African restaurant movement", "Food as national identity; jollof wars between nations; growing global recognition"),
     ]),

    ("Ethiopian civilization", "civilization", "Sub-Saharan Africa", "East Africa",
     "Ethiopia, Eritrea", -3000, None, 1,
     "Ethiopian cuisine",
     "One of the world's most distinctive cuisines. Injera (teff flatbread) as edible plate, elaborate spice blends (berbere, mitmita), communal eating from shared plate, ancient coffee origin.",
     [
         ("Aksumite-Medieval Kingdoms", -3000, 1500, "Teff domestication (endemic grain), ensete (false banana) cultivation, coffee discovered in Kaffa region, honey wine (tej), animal husbandry (cattle, sheep)", "Red Sea trade with Rome/Arabia, incense route", "One of the world's oldest continuous civilizations; Orthodox Christian fasting creates extensive vegan cuisine"),
         ("Modern Ethiopia", 1500, None, "Berbere spice blend codified, injera culture spreads globally via diaspora, raw meat tradition (kitfo, gored gored), coffee ceremony (buna) as daily ritual, 200+ fasting days create world's richest vegan tradition", "Italian brief occupation introduces pasta, Ethiopian diaspora (esp. Washington DC)", "Orthodox fasting rules create most diverse vegan cuisine on earth; coffee ceremony is spiritual practice"),
     ]),

    # AMERICAS
    ("Mesoamerican civilization", "civilization", "North America", "Central America/Mexico",
     "Mexico, Guatemala, Belize, Honduras, El Salvador", -7000, None, 1,
     "Mexican cuisine",
     "UNESCO Intangible Cultural Heritage. The three sisters (maize, beans, squash) plus chili peppers form one of humanity's most nutritionally complete food systems. Nixtamalization is a food science breakthrough.",
     [
         ("Pre-Columbian (Olmec-Maya-Aztec)", -7000, 1521, "Maize domestication and nixtamalization (lime-treating corn unlocks niacin), chocolate (cacao) as sacred drink, chili pepper cultivation, tomato/avocado/vanilla/squash domestication, turkey domestication, amaranth as superfood", "Mesoamerican trade networks, cacao as currency", "Nixtamalization prevented pellagra - one of history's greatest food science discoveries; chocolate as ritual drink"),
         ("Colonial-Mestizo Fusion", 1521, 1821, "Spanish introduce wheat/cattle/pigs/cheese/sugar, mole sauces fuse Old and New World, convent cooking creates elaborate dishes, European-indigenous fusion births modern Mexican cuisine", "Manila galleon (Philippines-Mexico-Spain), transatlantic trade", "Convent nuns create complex moles; criolla cuisine emerges; chocolate conquers Europe"),
         ("Modern Mexico", 1821, None, "Street food culture (tacos, tamales, elotes), regional diversity celebrated (Oaxacan, Yucatecan, Norteño), taco stands as UNESCO consideration, mezcal renaissance, global Mexican food movement", "US-Mexico cultural exchange, global taqueria movement", "Street food is highest art form; regional identity fierce; corn as spiritual/cultural/nutritional foundation"),
     ]),

    ("Andean civilization", "civilization", "South America", "Andes",
     "Peru, Bolivia, Ecuador, Colombia", -5000, None, 1,
     "Peruvian cuisine",
     "Peru has been called the world's greatest food nation. Potato domestication (3,000+ varieties), quinoa, Incan freeze-drying (chuño), and modern ceviche-to-Nikkei fusion.",
     [
         ("Pre-Inca & Inca Empire", -5000, 1533, "Potato domestication (3,000+ native varieties), quinoa/kiwicha cultivation, freeze-drying (chuño) - first dehydrated food, guinea pig (cuy) domestication, chicha corn beer, coca leaf", "Inca road system (Qhapaq Ñan), vertical archipelago trading", "Inca freeze-drying invented millennia before modern technique; potato as foundation of Andean life"),
         ("Colonial & Nikkei/Chifa Fusion", 1533, None, "Spanish, African, Chinese (chifa), Japanese (Nikkei) layers of immigration create world's most fusion-rich cuisine, ceviche becomes national dish, pisco as spirit, Gastón Acurio's culinary revolution", "Spanish silver trade, Chinese/Japanese immigration waves, modern culinary tourism", "Lima now considered world gastronomy capital; Mistura food festival; chifa (Chinese-Peruvian) unique fusion"),
     ]),

    # EUROPE
    ("French civilization", "civilization", "Western Europe", "France",
     "France, Belgium (Wallonia), Switzerland (Romandy)", -500, None, 1,
     "French cuisine",
     "Systematized Western fine dining. Escoffier's brigade de cuisine, mother sauces, regional terroir. UNESCO Intangible Cultural Heritage. Both haute cuisine and peasant cooking are world-class.",
     [
         ("Medieval & Renaissance", -500, 1650, "Roman Gaul wine/cheese tradition, medieval spice excess (imported from East), guild system regulates trades (boulanger, charcutier), Taillevent's Le Viandier (1300s) - first French cookbook, Catherine de Medici Italian influence myth", "Champagne fairs connecting Mediterranean to Northern Europe, Crusade spice contact", "Feudal food hierarchy; monastic brewing and cheesemaking; medieval banquet spectacles"),
         ("Ancien Régime & Haute Cuisine", 1650, 1789, "La Varenne's Le Cuisinier François (1651) invents modern French cooking, roux/stock/reduction foundations, Versailles court dining, regional cheeses catalogued, champagne method invented", "French colonial spice access (Caribbean, Indian Ocean), Court of Versailles influence", "French cooking becomes Europe's prestige cuisine; sauce-based cooking replaces medieval spice masking"),
         ("Post-Revolution to Escoffier", 1789, 1970, "Restaurant invented (1765 Paris), Carême codifies haute cuisine, Escoffier's Le Guide Culinaire (1903) creates brigade system and mother sauces, Michelin Guide begins (1900), bistro culture", "Global French culinary dominance, colonial cuisine exchange (Indochina, North Africa)", "Revolution disperses royal chefs to public restaurants; Escoffier systematizes professional kitchen globally"),
         ("Nouvelle Cuisine to Modern", 1970, None, "Nouvelle cuisine lightens classical, regional revival (terroir movement), molecular gastronomy (Hervé This), natural wine movement, bistronomy democratization", "EU agricultural policy, global chef exchange, culinary school diplomacy", "From Bocuse to Ducasse to modern bistronomie; France remains global culinary reference point"),
     ]),

    ("Italian civilization", "civilization", "Western Europe", "Italy",
     "Italy, San Marino, Vatican City, parts of Switzerland", -800, None, 1,
     "Italian cuisine",
     "The world's most imitated cuisine. Built on regional specificity, seasonal ingredients, and the philosophy that great ingredients need minimal manipulation. Each of Italy's 20 regions is a separate culinary world.",
     [
         ("Roman Antiquity", -800, 476, "Garum (fermented fish sauce) as umami base, olive oil/wine/bread trinity, Apicius cookbook, banquet culture (convivium), grain imports from Egypt/North Africa, herb-forward cooking", "Mare Nostrum Mediterranean trade, Silk Road spice imports, Egyptian grain ships", "Roman food ranges from peasant puls (porridge) to Lucullus's legendary banquets; Apicius is first major Western cookbook"),
         ("Medieval-Renaissance", 476, 1600, "Pasta arrives (debate: Arab or Chinese origin), regional cheeses formalize (Parmigiano 1200s), Florentine Renaissance dining, Bartolomeo Scappi's Opera (1570) - most influential Italian cookbook", "Venetian spice trade, Genoese Mediterranean routes, Medici court", "Italian city-states develop fiercely distinct cuisines; pasta-making becomes art; tomato arrives from Americas but initially mistrusted"),
         ("Tomato Revolution & Unification", 1600, 1945, "Tomato finally adopted in Naples (~1700s) transforms Southern Italian cooking, pizza emerges, risotto formalized in North, espresso invented (1900s), regional cuisines crystallize along North-South divide", "Tomato from Americas via Spain, Italian diaspora to Americas brings recipes worldwide", "Tomato revolution creates modern Italian cuisine; diaspora creates Italian-American cooking; Pellegrino Artusi's La Scienza (1891) first unified Italian cookbook"),
         ("Postwar to Slow Food", 1945, None, "Slow Food movement founded (1986 Bra), DOC/DOP protection system, farm-to-table philosophy, regional pride movements, Italian cuisine becomes global default, Eataly as concept", "EU food regulation, Slow Food international movement, global Italian restaurant culture", "Slow Food fights against homogenization; terroir protection; every Italian region fiercely guards its food identity"),
     ]),

    # MEDITERRANEAN / LEVANT
    ("Levantine civilization", "civilization", "Middle East", "Levant",
     "Lebanon, Syria, Palestine, Jordan, Israel", -8000, None, 1,
     "Levantine cuisine",
     "The birthplace of agriculture. Wheat, lentils, chickpeas, olives, figs all domesticated here. Hummus, falafel, and tabbouleh are among the world's most ancient continuously-eaten foods.",
     [
         ("Neolithic Revolution", -8000, -3000, "First agriculture: wheat, barley, lentils, chickpeas domesticated in Fertile Crescent, olive and fig cultivation, bread-baking origins, beer invention, first animal husbandry (sheep, goats)", "Fertile Crescent as origin point radiating outward", "Literally where human food culture begins; transition from hunter-gatherer to farmer"),
         ("Ancient Near East to Roman", -3000, 636, "Phoenician olive oil trade, Biblical food laws (kashrut), Nabataean spice route, Roman bread and circus, wine culture, preservation techniques (olives, dates, dried legumes)", "Phoenician Mediterranean trade, Nabataean incense/spice route, Roman roads", "Food laws define religious identity; olive oil as currency; communal bread-breaking as social contract"),
         ("Islamic-Ottoman to Modern", 636, None, "Meze culture formalized, coffee from Yemen via Damascus, Arab sweets (baklava, knafeh), Ottoman multi-ethnic cuisine layers, modern hummus/falafel globalization, za'atar/sumac/pomegranate molasses as signature flavors", "Arab trade routes, Ottoman imperial kitchen influence, modern diaspora", "Contested cuisine politics (hummus wars); food as identity in conflict zones; extraordinary hospitality tradition"),
     ]),

    # ADDITIONAL MAJOR CUISINES
    ("Spanish civilization", "civilization", "Western Europe", "Iberian Peninsula",
     "Spain, Andorra", -1000, None, 1,
     "Spanish cuisine",
     "Tapas culture, jamón ibérico, olive oil, and the Columbian Exchange gateway. Spain was the bridge between Old and New World ingredients, introducing tomatoes, potatoes, and chocolate to Europe.",
     [
         ("Roman-Moorish Period", -1000, 1492, "Roman olive oil and wine, Moorish introduction of rice (paella origins), saffron, almonds, citrus, sugar cane, eggplant, sophisticated irrigation (acequia), Al-Andalus as Europe's food capital", "Mediterranean trade, Moorish North Africa connection, Al-Andalus silk/spice routes", "700 years of Moorish rule creates Spain's most distinctive flavors; convivencia multicultural dining"),
         ("Age of Discovery", 1492, 1800, "Columbian Exchange epicenter: Spain introduces tomato, potato, chocolate, corn, chili pepper, vanilla, turkey to Europe; colonial crops reshape global agriculture; chocolate houses in Madrid", "Americas-Spain-Philippines trade (Manila galleon), global colonial network", "Spain as gateway for New World ingredients that transform all of European and Asian cooking"),
         ("Modern Spain", 1800, None, "Regional cuisine pride (Basque, Catalan, Galician, Andalusian), tapas as social institution, Ferran Adrià and molecular gastronomy revolution (El Bulli), pintxos culture, cider houses, vermouth revival", "EU integration, culinary tourism (San Sebastián as food capital)", "Adrià invents molecular gastronomy; San Sebastián most Michelin stars per capita; tapas as democratic dining"),
     ]),

    ("Scandinavian civilization", "civilization", "Northern Europe", "Scandinavia",
     "Sweden, Norway, Denmark, Finland, Iceland", -2000, None, 1,
     "Scandinavian cuisine",
     "Preservation-driven cuisine: smoking, curing, pickling, fermenting, drying. New Nordic Cuisine movement (Noma) revolutionized global fine dining by proving foraging and terroir work in cold climates.",
     [
         ("Viking & Medieval", -2000, 1500, "Preservation necessity: smoking (laks), curing (gravlax), pickling (sill), fermenting (surströmming), drying (stockfish/klippfisk), dairy fermentation (skyr, filmjölk), rye bread, mead", "Viking trade routes (Scandinavia to Constantinople/Baghdad), Hanseatic League", "Preservation as survival; Viking trade brings Eastern spices; smörgåsbord (butter-goose table) tradition"),
         ("Modern to New Nordic", 1500, None, "Smörgåsbord formalized, Swedish meatballs, Danish smørrebrød, Finnish rye tradition, Icelandic fermented shark (hákarl), 2004 New Nordic Cuisine manifesto, Noma revolutionizes global fine dining, foraging renaissance", "Hanseatic trade, modern EU integration, Noma's global influence", "Noma (2010s world's best restaurant) proves cold-climate cuisine can lead innovation; foraging as philosophy"),
     ]),

    ("Russian civilization", "civilization", "Eastern Europe", "Russia",
     "Russia, Belarus, parts of Ukraine", -900, None, 1,
     "Russian cuisine",
     "Hearty cuisine shaped by long winters, vast geography, and Orthodox fasting tradition. Sour flavors (smetana, kvas, pickles), preserved foods, and the zakuski appetizer tradition.",
     [
         ("Kievan Rus to Tsarist", -900, 1917, "Rye bread centrality, kvas fermentation, Orthodox fasting creates elaborate fish/mushroom/vegetable cuisine, borscht origins, blini from pagan sun worship, pelmeni from Siberian/Central Asian influence, samovar tea culture from 1700s", "Volga trade route, Silk Road eastern terminus, Trans-Siberian contacts", "Orthodox fasting 200+ days/year creates huge vegetarian/vegan repertoire; peasant cooking is preservation-focused"),
         ("Soviet & Modern", 1917, None, "Standardized canteen (stolovaya) cuisine, Book of Tasty and Healthy Food (1939) as national cookbook, olivier salad, Soviet ice cream, post-Soviet restaurant renaissance, New Russian cuisine movement", "Soviet bloc food exchange, post-Soviet globalization", "Soviet standardization paradoxically preserved some traditions; modern chefs rediscovering pre-revolutionary recipes"),
     ]),

    ("Brazilian civilization", "civilization", "South America", "Brazil",
     "Brazil", -10000, None, 1,
     "Brazilian cuisine",
     "Triple fusion: indigenous Tupi, Portuguese colonial, and African (via slave trade). Feijoada, churrasco, açaí, and the world's most diverse street food scene.",
     [
         ("Indigenous & Colonial", -10000, 1822, "Tupi indigenous: manioc/cassava processing (removing cyanide), açaí, guaraná, hearts of palm, piranha; Portuguese bring sugar cane, cattle, wheat; African slaves bring okra, palm oil, dendê, black-eyed peas, cooking techniques", "Portuguese Atlantic trade, African slave trade, sugar economy", "African food knowledge (especially Bahian cuisine) is foundation of Brazilian cooking; moqueca, acarajé, vatapá all African-origin"),
         ("Modern Brazil", 1822, None, "Feijoada as national dish (slave food elevated), churrasco gaucho culture, São Paulo as food capital (Japanese-Brazilian sushi, Italian-Brazilian pizza), açaí goes global, cachaça and caipirinha", "Japanese immigration (1908+), Italian/German immigration, global açaí/churrasco export", "Most racially diverse cuisine on earth; street food from 50+ ethnic traditions"),
     ]),

    # NORTH AFRICA
    ("Moroccan civilization", "civilization", "North Africa", "Maghreb",
     "Morocco", -1000, None, 1,
     "Moroccan cuisine",
     "Berber, Arab, Andalusian, and French layers. Tagine slow-cooking, preserved lemons, ras el hanout spice blend, couscous tradition, and the world's most elaborate tea ceremony after Japan.",
     [
         ("Berber-Arab-Andalusian", -1000, 1912, "Indigenous Berber couscous and tagine technique, Arab spice trade influence, Andalusian refugees bring refined cooking (1492), preserved lemon technique, argan oil, mint tea ceremony, ras el hanout (30+ spice blend)", "Trans-Saharan trade, Andalusian exile, Arab spice routes", "Couscous is pre-Arab Berber invention; Andalusian refinement adds sweet-savory complexity; tea ceremony as hospitality ritual"),
         ("Modern Morocco", 1912, None, "French protectorate adds pastry tradition, street food (b'stilla, harira, msemen), UNESCO couscous recognition, tagine as global export, food tourism in Marrakech", "French colonial influence, modern tourism, diaspora in France/Belgium", "Couscous Friday is sacred; harira breaks Ramadan fast; food tied deeply to Islamic calendar"),
     ]),
]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:200]


def populate_cultures_and_eras(conn):
    """Insert rich culture data with historical eras."""
    print("\n=== Populating cultures with anthropological data ===")
    cursor = conn.cursor()
    cultures_added = 0
    eras_added = 0

    for data in CULTURE_DATA:
        (name, ctype, region, subregion, countries, era_start, era_end,
         is_living, wiki_article, description, eras) = data

        slug = slugify(name)

        # Check if culture exists (might exist as a bare nation entry)
        existing = cursor.execute("SELECT id FROM cultures WHERE name = ?", (name,)).fetchone()
        if existing:
            # Update with rich data
            cursor.execute("""
                UPDATE cultures SET
                    slug = COALESCE(slug, ?), culture_type = ?, region = ?, subregion = ?,
                    modern_countries = ?, era_start_year = ?, era_end_year = ?,
                    is_living_culture = ?, description = ?
                WHERE id = ?
            """, (slug, ctype, region, subregion, countries, era_start, era_end,
                  is_living, description, existing[0]))
            culture_id = existing[0]
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO cultures
                (name, slug, culture_type, region, subregion, modern_countries,
                 era_start_year, era_end_year, is_living_culture, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, slug, ctype, region, subregion, countries,
                  era_start, era_end, is_living, description))
            culture_id = cursor.lastrowid
            cultures_added += 1

        # Add eras
        for era_name, start, end, food_chars, trade, social in eras:
            cursor.execute("""
                INSERT OR IGNORE INTO culture_eras
                (culture_id, era_name, start_year, end_year,
                 food_characteristics, trade_routes, social_structure_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (culture_id, era_name, start, end, food_chars, trade, social))
            eras_added += 1

    conn.commit()
    print(f"  Cultures added/updated: {cultures_added}")
    print(f"  Historical eras added: {eras_added}")


def enrich_cultures_from_wikipedia(conn):
    """Pull Wikipedia food history articles for each culture."""
    print("\n=== Enriching cultures from Wikipedia food history articles ===")
    cursor = conn.cursor()

    # Wikipedia articles about food history by region/culture
    food_history_articles = [
        "History of food",
        "Columbian exchange",
        "Spice trade",
        "Silk Road cuisine",
        "History of agriculture",
        "Fermentation in food processing",
        "History of bread",
        "History of cheese",
        "History of chocolate",
        "History of coffee",
        "History of tea",
        "History of wine",
        "History of beer",
        "History of sugar",
        "History of sushi",
        "History of pasta",
        "Food preservation",
        "Ancient cuisine",
        "Medieval cuisine",
        "Aztec cuisine",
        "Ancient Egyptian cuisine",
        "Ancient Roman cuisine",
        "Ottoman cuisine",
        "Mughlai cuisine",
        "New Nordic Cuisine",
        "Nouvelle cuisine",
        "Molecular gastronomy",
        "Slow Food",
        "Food and Agriculture Organization",
        "Staple food",
    ]

    for article in food_history_articles:
        text = wiki_extract(article, chars=5000)
        if not text or len(text) < 100:
            continue

        # Extract key facts and tag foods mentioned
        _tag_foods_from_history_text(cursor, conn, article, text)
        print(f"  Processed: {article}")
        time.sleep(0.5)

    conn.commit()


def _tag_foods_from_history_text(cursor, conn, article_title, text):
    """Extract historical/scientific tags from a food history article."""
    text_lower = text.lower()

    # Historical period detection
    period_patterns = {
        "ancient": r"\b(ancient|antiquity|bronze age|iron age|neolithic|paleolithic|mesopotamia)\b",
        "medieval": r"\b(medieval|middle ages|feudal|dark ages|crusade)\b",
        "renaissance": r"\b(renaissance|early modern)\b",
        "colonial": r"\b(colonial|colonialism|plantation|east india company|voc)\b",
        "industrial": r"\b(industrial revolution|19th century|factory|canning|pasteurization)\b",
        "modern": r"\b(20th century|21st century|modern|contemporary|molecular gastronomy)\b",
    }

    # Trade route detection
    trade_patterns = {
        "Silk Road": r"\b(silk road|silk route)\b",
        "Spice Route": r"\b(spice (route|trade|island))\b",
        "Columbian Exchange": r"\b(columbian exchange|new world|old world)\b",
        "Trans-Saharan": r"\b(trans.?saharan|caravan|salt trade)\b",
        "Maritime Trade": r"\b(maritime trade|east india|voc|portuguese trade)\b",
        "Slave Trade": r"\b(slave trade|middle passage|plantation)\b",
    }

    # Scientific/technique detection
    science_patterns = {
        "fermentation": r"\b(ferment|lactic acid|yeast|culture|probiotic)\b",
        "preservation": r"\b(preserv|salt|cure|smoke|dry|pickle|can)\b",
        "nixtamalization": r"\b(nixtamal|lime.?treat|alkaline)\b",
        "maillard reaction": r"\b(maillard|browning|carameliz)\b",
        "distillation": r"\b(distill|spirit|alcohol)\b",
        "pasteurization": r"\b(pasteuriz|steriliz)\b",
        "freeze-drying": r"\b(freeze.?dr|lyophil|chuño)\b",
        "selective breeding": r"\b(selective breeding|domesticat|cultivar|hybrid)\b",
    }

    # Find foods in our database that are mentioned in this text
    # Get a batch of food names to check
    foods = cursor.execute(
        "SELECT id, name FROM foods WHERE LENGTH(name) > 3 ORDER BY LENGTH(name) DESC LIMIT 5000"
    ).fetchall()

    tagged = 0
    for food_id, food_name in foods:
        if len(food_name) < 4:
            continue
        # Simple substring match (case insensitive)
        name_pattern = re.escape(food_name.lower())
        if re.search(r"\b" + name_pattern + r"\b", text_lower):
            # Tag with historical context
            for period, pattern in period_patterns.items():
                if re.search(pattern, text_lower):
                    cursor.execute(
                        'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "historical_period", ?, 0.6, "wikipedia_history")',
                        (food_id, period)
                    )

            for route, pattern in trade_patterns.items():
                if re.search(pattern, text_lower):
                    cursor.execute(
                        'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "trade_route", ?, 0.6, "wikipedia_history")',
                        (food_id, route)
                    )

            for technique, pattern in science_patterns.items():
                if re.search(pattern, text_lower):
                    cursor.execute(
                        'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "cooking_science", ?, 0.5, "wikipedia_history")',
                        (food_id, technique)
                    )
            tagged += 1

    if tagged > 0:
        conn.commit()


def tag_columbian_exchange(conn):
    """Tag foods as Old World or New World origin based on known botanical history."""
    print("\n=== Tagging Columbian Exchange origins ===")
    cursor = conn.cursor()

    new_world = [
        "tomato", "potato", "corn", "maize", "chili", "pepper", "chocolate", "cacao",
        "vanilla", "avocado", "peanut", "cashew", "pineapple", "papaya", "guava",
        "squash", "pumpkin", "zucchini", "turkey", "tobacco", "rubber", "sunflower",
        "blueberry", "cranberry", "pecan", "sweet potato", "cassava", "manioc",
        "quinoa", "amaranth", "chia", "beans", "lima bean", "kidney bean",
        "cocoa", "allspice", "annatto", "acai", "mate", "guarana",
    ]

    old_world = [
        "wheat", "rice", "barley", "oat", "rye", "millet", "sorghum",
        "olive", "grape", "wine", "fig", "date", "pomegranate", "citrus",
        "lemon", "orange", "banana", "mango", "coconut", "sugar cane",
        "coffee", "tea", "ginger", "turmeric", "cinnamon", "clove",
        "nutmeg", "black pepper", "cardamom", "cumin", "coriander",
        "saffron", "garlic", "onion", "carrot", "cabbage", "lettuce",
        "apple", "pear", "peach", "apricot", "cherry", "plum",
        "cow", "beef", "pork", "pig", "chicken", "sheep", "lamb", "goat",
        "milk", "cheese", "yogurt", "butter", "cream",
        "soy", "soybean", "tofu", "sesame", "almond", "walnut", "pistachio",
    ]

    tagged = 0
    for ingredient in new_world:
        cursor.execute("""
            UPDATE food_tags SET tag_value = tag_value WHERE 1=0
        """)  # no-op for structure
        rows = cursor.execute(
            "SELECT id FROM foods WHERE LOWER(name) LIKE ?", (f"%{ingredient}%",)
        ).fetchall()
        for (fid,) in rows:
            cursor.execute(
                'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "origin_hemisphere", "New World (Americas)", 0.9, "botanical_history")',
                (fid,)
            )
            cursor.execute(
                'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "columbian_exchange", "post-1492 introduction to Old World", 0.8, "botanical_history")',
                (fid,)
            )
            tagged += 1

    for ingredient in old_world:
        rows = cursor.execute(
            "SELECT id FROM foods WHERE LOWER(name) LIKE ?", (f"%{ingredient}%",)
        ).fetchall()
        for (fid,) in rows:
            cursor.execute(
                'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "origin_hemisphere", "Old World (Afro-Eurasia)", 0.9, "botanical_history")',
                (fid,)
            )
            tagged += 1

    conn.commit()
    print(f"  Tagged {tagged} foods with Columbian Exchange / hemisphere data")


def tag_staple_foods(conn):
    """Tag global staple foods and their cultural significance."""
    print("\n=== Tagging staple foods and cultural significance ===")
    cursor = conn.cursor()

    staples = {
        "rice": ("grain", "Staple for 3.5 billion people. Domesticated ~9000 BCE in Yangtze River valley. Paddy cultivation enabled Asian civilizations."),
        "wheat": ("grain", "Foundation of Western civilization. Domesticated ~9500 BCE in Fertile Crescent. Bread as 'staff of life.'"),
        "corn": ("grain", "Sacred grain of Mesoamerica. Nixtamalization unlocks niacin. Three Sisters (corn/beans/squash) nutritionally complete."),
        "maize": ("grain", "Sacred grain of Mesoamerica. Nixtamalization unlocks niacin. Three Sisters (corn/beans/squash) nutritionally complete."),
        "potato": ("tuber", "Domesticated in Peru ~8000 BCE, 3000+ varieties. Prevented European famine after adoption. Irish Potato Famine (1845) shows danger of monoculture."),
        "cassava": ("tuber", "Feeds 800 million globally. Requires processing to remove cyanide. Foundation of West African, Brazilian, SE Asian cooking."),
        "soybean": ("legume", "East Asian 'meat of the field.' Tofu, soy sauce, miso, tempeh, natto - most versatile single ingredient on earth."),
        "olive": ("fruit/oil", "Sacred to Mediterranean civilizations for 6000+ years. Oil, table olives, and branch as symbol of peace."),
        "coconut": ("fruit/oil", "Tree of life in tropical cultures. Milk, oil, water, flesh, sugar, vinegar, toddy - nothing wasted."),
    }

    tagged = 0
    for staple, (category, significance) in staples.items():
        rows = cursor.execute(
            "SELECT id FROM foods WHERE LOWER(name) LIKE ?", (f"%{staple}%",)
        ).fetchall()
        for (fid,) in rows:
            cursor.execute(
                'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "staple_food", ?, 1.0, "anthropology")',
                (fid, category)
            )
            cursor.execute(
                'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "cultural_significance", ?, 0.9, "anthropology")',
                (fid, significance[:200])
            )
            tagged += 1

    conn.commit()
    print(f"  Tagged {tagged} foods with staple/significance data")


def tag_food_science(conn):
    """Tag foods with cooking science categories based on their descriptions."""
    print("\n=== Tagging food science categories ===")
    cursor = conn.cursor()

    science_tags = {
        "maillard_reaction": (r"\b(maillard|browning|sear|crust|toast|caramelize|golden brown)\b", "Maillard reaction (amino acid + sugar browning)"),
        "fermentation_lactic": (r"\b(lactic|lactobacillus|yogurt|kimchi|sauerkraut|pickl)\b", "Lactic acid fermentation"),
        "fermentation_alcoholic": (r"\b(yeast|alcohol|beer|wine|sake|mead|ferment.+grain)\b", "Alcoholic fermentation"),
        "fermentation_acetic": (r"\b(vinegar|acetic|mother|kombucha)\b", "Acetic acid fermentation"),
        "emulsification": (r"\b(emulsif|emulsion|mayonnaise|hollandaise|vinaigrette|lecithin)\b", "Emulsification"),
        "gelatinization": (r"\b(gelatin|collagen|bone broth|aspic|jelly|gel)\b", "Gelatin/collagen extraction"),
        "starch_gelatinization": (r"\b(starch|thicken|roux|slurry|cornstarch|arrowroot)\b", "Starch gelatinization"),
        "denaturation": (r"\b(denatur|ceviche|acid.+cook|lime.+juice.+cook|cure)\b", "Protein denaturation"),
        "osmosis": (r"\b(brine|salt.+draw|osmosis|dry.+rub|sugar.+cure)\b", "Osmotic preservation"),
        "smoke_preservation": (r"\b(smoke|smoking|smoked|wood.+fire|liquid smoke)\b", "Smoke preservation/flavoring"),
    }

    rows = cursor.execute(
        "SELECT id, name, description FROM foods WHERE description IS NOT NULL AND description != ''"
    ).fetchall()

    tagged = 0
    for fid, name, desc in rows:
        text = f"{name} {desc}".lower()
        for key, (pattern, label) in science_tags.items():
            if re.search(pattern, text, re.IGNORECASE):
                cursor.execute(
                    'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "cooking_science", ?, 0.7, "text_analysis")',
                    (fid, label)
                )
                tagged += 1

    conn.commit()
    print(f"  Tagged {tagged} food-science associations")


def tag_social_class(conn):
    """Tag foods with historical social class associations."""
    print("\n=== Tagging social class associations ===")
    cursor = conn.cursor()

    class_patterns = {
        "royal/aristocratic": r"\b(royal|imperial|court|king|queen|emperor|palace|aristocrat|noble|haute cuisine|fine dining|luxury)\b",
        "peasant/working class": r"\b(peasant|poor|working class|humble|simple|rustic|hearty|cheap|frugal|survival|poverty|ration)\b",
        "monastic/religious": r"\b(monast|monk|nun|temple|convent|abbey|church|mosque|synagogue|religious order|fasting|lenten)\b",
        "merchant/middle class": r"\b(merchant|trader|bourgeois|middle class|guild|market|bazaar|commercial)\b",
        "street/vendor": r"\b(street food|vendor|hawker|stall|cart|stand|roadside|night market)\b",
        "military/campaign": r"\b(military|army|navy|soldier|sailor|campaign|ration|field|trench|mess)\b",
    }

    rows = cursor.execute(
        "SELECT id, name, description FROM foods WHERE description IS NOT NULL AND LENGTH(description) > 50"
    ).fetchall()

    tagged = 0
    for fid, name, desc in rows:
        text = f"{name} {desc}".lower()
        for social_class, pattern in class_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                cursor.execute(
                    'INSERT OR IGNORE INTO food_tags (food_id, tag_category, tag_value, confidence, source) VALUES (?, "social_class", ?, 0.7, "text_analysis")',
                    (fid, social_class)
                )
                tagged += 1

    conn.commit()
    print(f"  Tagged {tagged} social class associations")


def cross_reference_everything(conn):
    """Link foods to cultures via tags, link eras to foods, create the full web."""
    print("\n=== Cross-referencing foods <-> cultures <-> eras ===")
    cursor = conn.cursor()

    # Link foods to enriched civilization cultures via cuisine tags
    enriched_cultures = cursor.execute(
        "SELECT id, name, modern_countries FROM cultures WHERE culture_type = 'civilization'"
    ).fetchall()

    linked = 0
    for cid, cname, countries in enriched_cultures:
        if not countries:
            continue
        for country in countries.split(","):
            country = country.strip()
            # Find foods tagged with this country as cuisine
            food_ids = cursor.execute(
                "SELECT DISTINCT food_id FROM food_tags WHERE tag_category = 'cuisine' AND tag_value LIKE ?",
                (f"%{country}%",)
            ).fetchall()
            for (fid,) in food_ids:
                cursor.execute(
                    "INSERT OR IGNORE INTO food_culture_origins (food_id, culture_id, origin_type) VALUES (?, ?, 'cultural')",
                    (fid, cid)
                )
                linked += 1

    conn.commit()
    print(f"  Linked {linked} foods to civilization-level cultures")


def print_final_stats(conn):
    """Print comprehensive stats."""
    cursor = conn.cursor()

    print("\n" + "=" * 70)
    print("ANTHROPOLOGICAL ENRICHMENT COMPLETE")
    print("=" * 70)

    cursor.execute("SELECT COUNT(*) FROM cultures WHERE description IS NOT NULL")
    print(f"Cultures with descriptions: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM culture_eras")
    print(f"Historical eras: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM food_tags")
    total = cursor.fetchone()[0]
    print(f"Total food tags: {total:,}")

    print("\n--- New anthropological tag categories ---")
    for cat in ["historical_period", "trade_route", "cooking_science",
                "origin_hemisphere", "columbian_exchange", "staple_food",
                "cultural_significance", "social_class"]:
        cursor.execute(
            "SELECT COUNT(*), COUNT(DISTINCT food_id) FROM food_tags WHERE tag_category = ?", (cat,)
        )
        tags, foods = cursor.fetchone()
        if tags > 0:
            cursor.execute(
                "SELECT tag_value, COUNT(*) FROM food_tags WHERE tag_category = ? GROUP BY tag_value ORDER BY COUNT(*) DESC LIMIT 5",
                (cat,)
            )
            top = ", ".join(f"{v}({c})" for v, c in cursor.fetchall())
            print(f"  {cat:25s}: {tags:6,} tags, {foods:5,} foods | top: {top}")

    print("\n--- Enriched civilizations ---")
    rows = cursor.execute("""
        SELECT c.name, c.region, COUNT(ce.id) as eras,
               (SELECT COUNT(*) FROM food_culture_origins WHERE culture_id = c.id) as foods
        FROM cultures c
        LEFT JOIN culture_eras ce ON ce.culture_id = c.id
        WHERE c.culture_type = 'civilization'
        GROUP BY c.id ORDER BY foods DESC
    """).fetchall()
    for name, region, eras, foods in rows:
        print(f"  {name:40s} | {region:20s} | {eras} eras | {foods:,} foods")

    print("=" * 70)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # Ensure culture_eras table has slug column issue handled
    try:
        conn.execute("SELECT slug FROM cultures LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE cultures ADD COLUMN slug TEXT")
        conn.commit()

    populate_cultures_and_eras(conn)
    tag_columbian_exchange(conn)
    tag_staple_foods(conn)
    tag_food_science(conn)
    tag_social_class(conn)
    enrich_cultures_from_wikipedia(conn)
    cross_reference_everything(conn)
    print_final_stats(conn)

    conn.close()


if __name__ == "__main__":
    main()
