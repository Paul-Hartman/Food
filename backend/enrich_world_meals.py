"""
Enrich food database with world meal patterns for 72+ cultures.
Links foods to meal types with culture context and creates ingredient categories.
"""

import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "food.db"


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:200]


# ============================================================================
# REGION FIXES for cultures currently marked "Other"
# ============================================================================
REGION_FIXES = {
    # Continents / meta-regions
    "Africa": "Sub-Saharan Africa",
    "Americas": "Americas",
    "Asia": "East Asia",
    "Europe": "Western Europe",
    "Central Asia": "Central Asia",
    "Central Europe": "Western Europe",
    "Eastern Europe": "Eastern Europe",
    "Latin America": "South America",
    "Near East": "Middle East",
    "North Africa": "North Africa",
    "North America": "North America",
    "Scandinavia": "Northern Europe",
    "South America": "South America",
    "Southeast Asia": "Southeast Asia",
    "Southern Europe": "Southern Europe",
    "Middle East": "Middle East",
    "Caribbean": "Caribbean",
    # Historical entities
    "Ancient Greece": "Southern Europe",
    "Ancient Rome": "Southern Europe",
    "Byzantine Empire": "Southern Europe",
    "Empire of Japan": "East Asia",
    "Goryeo": "East Asia",
    "Grand Duchy of Lithuania": "Eastern Europe",
    "Joseon": "East Asia",
    "Kievan Rus'": "Eastern Europe",
    "Kingdom of Hungary": "Eastern Europe",
    "Kingdom of the Netherlands": "Western Europe",
    "Korean Empire": "East Asia",
    "Mesoamerica": "Central America",
    "Mesopotamia": "Middle East",
    "Middle Eastern empires": "Middle East",
    "Ottoman Empire": "Middle East",
    "Persian Empire": "Middle East",
    "Polish People's Republic": "Eastern Europe",
    "Prussia": "Western Europe",
    "Qing dynasty": "East Asia",
    "Republic of China": "East Asia",
    "Roman Empire": "Southern Europe",
    "Russian Empire": "Eastern Europe",
    "Russian Soviet Federative Socialist Republic": "Eastern Europe",
    "Ryukyu Kingdom": "East Asia",
    "Soviet Union": "Eastern Europe",
    "Tokugawa shogunate": "East Asia",
    "al-Andalus": "Southern Europe",
    "ancient Near East": "Middle East",
    "Qajar Iran": "Middle East",
    "People's Republic of China": "East Asia",
    "Republic of Artsakh": "Middle East",
    "German Democratic Republic": "Western Europe",
    "Georgian Soviet Socialist Republic": "Eastern Europe",
    "British Hong Kong": "East Asia",
    "Czechoslovakia": "Eastern Europe",
    # Sub-national / regional
    "Acadia": "North America",
    "Andalusia": "Southern Europe",
    "Aosta Valley": "Western Europe",
    "Autonomous Republic of Crimea": "Eastern Europe",
    "Arabian Peninsula": "Middle East",
    "Arizona": "North America",
    "Balkans": "Eastern Europe",
    "Basque Country": "Southern Europe",
    "Bavaria": "Western Europe",
    "Bengal": "South Asia",
    "Berlin": "Western Europe",
    "Bhadrak": "South Asia",
    "Bohemia": "Eastern Europe",
    "Buenos Aires": "South America",
    "Chongqing": "East Asia",
    "Connecticut": "North America",
    "Corsica": "Western Europe",
    "County of Flanders": "Western Europe",
    "Crimea": "Eastern Europe",
    "England": "Western Europe",
    "Eryuan County": "East Asia",
    "Faroe Islands": "Northern Europe",
    "Gibraltar": "Southern Europe",
    "Haizhu District": "East Asia",
    "Hawaii": "Oceania",
    "Hesse": "Western Europe",
    "Hong Kong": "East Asia",
    "Indian subcontinent": "South Asia",
    "Java": "Southeast Asia",
    "Jieyang": "East Asia",
    "Kentucky": "North America",
    "Kinmen County": "East Asia",
    "Korea": "East Asia",
    "Kurdistan": "Middle East",
    "Kurdistan Province": "Middle East",
    "Labin": "Southern Europe",
    "Levant": "Middle East",
    "Long Island": "North America",
    "Los Angeles": "North America",
    "Louisiana": "North America",
    "Low Countries": "Western Europe",
    "Lower Austria": "Western Europe",
    "Madeira": "Western Europe",
    "Maghreb": "North Africa",
    "Mallorca": "Southern Europe",
    "Moldavia": "Eastern Europe",
    "Moravia": "Eastern Europe",
    "Naples": "Southern Europe",
    "New Caledonia": "Oceania",
    "New Orleans": "North America",
    "New York City": "North America",
    "Northern Ireland": "Western Europe",
    "Occitania": "Western Europe",
    "Ossetia": "Eastern Europe",
    "Piedmont": "Western Europe",
    "Provence": "Western Europe",
    "Quebec": "North America",
    "Scotland": "Western Europe",
    "Sicily": "Southern Europe",
    "Silesia": "Eastern Europe",
    "Styria": "Western Europe",
    "Taiwan Island": "East Asia",
    "Tasmania": "Oceania",
    "Tengchong City": "East Asia",
    "Texas": "North America",
    "Tibet Autonomous Region": "East Asia",
    "Valencian Community": "Southern Europe",
    "Victoria": "Oceania",
    "Vienna": "Western Europe",
    "Vojvodina": "Eastern Europe",
    "Wales": "Western Europe",
    "Wallonia": "Western Europe",
    "Xiamen": "East Asia",
    "Xinjiang": "East Asia",
    "Yunnan": "East Asia",
    # Nations
    "Angola": "Sub-Saharan Africa",
    "Antigua and Barbuda": "Caribbean",
    "Armenia": "Middle East",
    "Azerbaijan": "Central Asia",
    "Benin": "Sub-Saharan Africa",
    "Bohtan": "Middle East",
    "Botswana": "Sub-Saharan Africa",
    "Burkina Faso": "Sub-Saharan Africa",
    "Burundi": "Sub-Saharan Africa",
    "Cape Verde": "Sub-Saharan Africa",
    "Cayman Islands": "Caribbean",
    "Central African Republic": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa",
    "Democratic Republic of the Congo": "Sub-Saharan Africa",
    "Djibouti": "Sub-Saharan Africa",
    "Dominica": "Caribbean",
    "Equatorial Guinea": "Sub-Saharan Africa",
    "Eswatini": "Sub-Saharan Africa",
    "Georgia": "Middle East",
    "Guam": "Oceania",
    "Guinea": "Sub-Saharan Africa",
    "Guinea-Bissau": "Sub-Saharan Africa",
    "Ivory Coast": "Sub-Saharan Africa",
    "Lesotho": "Sub-Saharan Africa",
    "Liberia": "Sub-Saharan Africa",
    "Liechtenstein": "Western Europe",
    "Luxembourg": "Western Europe",
    "Madagascar": "Sub-Saharan Africa",
    "Malawi": "Sub-Saharan Africa",
    "Maldives": "South Asia",
    "Marshall Islands": "Oceania",
    "Mauritania": "Sub-Saharan Africa",
    "Mauritius": "Sub-Saharan Africa",
    "Monaco": "Western Europe",
    "Moldavia": "Eastern Europe",
    "Namibia": "Sub-Saharan Africa",
    "Nauru": "Oceania",
    "Niger": "Sub-Saharan Africa",
    "North Korea": "East Asia",
    "Northern Cyprus": "Middle East",
    "Ossetia": "Eastern Europe",
    "Palau": "Oceania",
    "Republic of the Congo": "Sub-Saharan Africa",
    "Rwanda": "Sub-Saharan Africa",
    "Saint Kitts and Nevis": "Caribbean",
    "Saint Lucia": "Caribbean",
    "Saint Vincent and the Grenadines": "Caribbean",
    "Seychelles": "Sub-Saharan Africa",
    "Sierra Leone": "Sub-Saharan Africa",
    "Somalia": "Sub-Saharan Africa",
    "South Sudan": "Sub-Saharan Africa",
    "Sudan": "North Africa",
    "Suriname": "South America",
    "Togo": "Sub-Saharan Africa",
    "United Arab Emirates": "Middle East",
    "Zambia": "Sub-Saharan Africa",
    "Zimbabwe": "Sub-Saharan Africa",
    "internationality": "Other",
}


# ============================================================================
# NEW CULTURES to create
# ============================================================================
NEW_CULTURES = [
    ("Catalan", "nation", "Southern Europe", "Spain"),
    ("Cajun/Creole", "nation", "North America", "United States"),
    ("Southern US", "nation", "North America", "United States"),
    ("Tex-Mex", "nation", "North America", "United States, Mexico"),
    ("Native American", "nation", "North America", "United States, Canada"),
    ("Polynesian", "nation", "Oceania", "Samoa, Tonga, Cook Islands, French Polynesia"),
]


# ============================================================================
# Culture adjective → DB culture name
# ============================================================================
CULTURE_DB_MAP = {
    # East Asia
    "Vietnamese": "Vietnam",
    "Filipino": "Philippines",
    "Malaysian": "Malaysia",
    "Burmese": "Myanmar",
    "Cambodian": "Cambodia",
    "Mongolian": "Mongolia",
    # South Asia
    "Pakistani": "Pakistan",
    "Sri Lankan": "Sri Lanka",
    "Bangladeshi": "Bangladesh",
    "Nepali": "Nepal",
    "Afghan": "Afghanistan",
    # Southeast Asia
    "Singaporean": "Singapore",
    "Laotian": "Laos",
    # Middle East
    "Lebanese": "Lebanon",
    "Iraqi": "Iraq",
    "Yemeni": "Yemen",
    "Egyptian": "Egypt",
    "Syrian": "Syria",
    "Emirati": "United Arab Emirates",
    "Israeli": "Israel",
    # Africa
    "Nigerian": "Nigeria",
    "Ghanaian": "Ghana",
    "Senegalese": "Senegal",
    "Kenyan": "Kenya",
    "Tanzanian": "Tanzania",
    "South African": "South Africa",
    "Congolese": "Democratic Republic of the Congo",
    "Somali": "Somalia",
    "Tunisian": "Tunisia",
    "Algerian": "Algeria",
    # Europe
    "German": "Germany",
    "British": "United Kingdom",
    "Greek": "Greece",
    "Polish": "Poland",
    "Hungarian": "Hungary",
    "Portuguese": "Portugal",
    "Dutch": "Netherlands",
    "Belgian": "Belgium",
    "Swiss": "Switzerland",
    "Austrian": "Austria",
    "Czech": "Czech Republic",
    "Romanian": "Romania",
    "Ukrainian": "Ukraine",
    "Georgian": "Georgia",
    "Armenian": "Armenia",
    "Basque": "Basque Country",
    "Catalan": "Catalan",
    "Sicilian": "Sicily",
    "Swedish": "Sweden",
    "Norwegian": "Norway",
    "Danish": "Denmark",
    "Finnish": "Finland",
    "Irish": "Ireland",
    "Scottish": "Scotland",
    # Americas
    "Peruvian": "Peru",
    "Argentine": "Argentina",
    "Colombian": "Colombia",
    "Cuban": "Cuba",
    "Jamaican": "Jamaica",
    "Puerto Rican": "Puerto Rico",
    "Haitian": "Haiti",
    "Trinidadian": "Trinidad and Tobago",
    "Cajun/Creole": "Cajun/Creole",
    "Southern US": "Southern US",
    "Tex-Mex": "Tex-Mex",
    "Hawaiian": "Hawaii",
    "Native American": "Native American",
    "Brazilian": "Brazil",
    # Oceania
    "Australian": "Australia",
    "Maori": "New Zealand",
    "Polynesian": "Polynesian",
    "Fijian": "Fiji",
}


# ============================================================================
# DB culture name → cuisine tag values (for finding foods)
# ============================================================================
CULTURE_TO_CUISINE_TAGS = {
    "Vietnam": ["Vietnamese"],
    "Philippines": ["Filipino"],
    "Malaysia": ["Malaysian", "Malay"],
    "Myanmar": ["Burmese"],
    "Cambodia": ["Cambodian", "Khmer"],
    "Mongolia": ["Mongolian"],
    "Pakistan": ["Pakistani"],
    "Sri Lanka": ["Sri Lankan"],
    "Bangladesh": ["Bangladeshi", "Bengali"],
    "Nepal": ["Nepali", "Nepalese"],
    "Afghanistan": ["Afghan"],
    "Singapore": ["Singaporean", "Singapore"],
    "Laos": ["Laotian", "Lao"],
    "Lebanon": ["Lebanese"],
    "Iraq": ["Iraqi"],
    "Yemen": ["Yemeni"],
    "Egypt": ["Egyptian"],
    "Syria": ["Syrian"],
    "United Arab Emirates": ["Emirati"],
    "Israel": ["Israeli"],
    "Nigeria": ["Nigerian"],
    "Ghana": ["Ghanaian"],
    "Senegal": ["Senegalese"],
    "Kenya": ["Kenyan"],
    "Tanzania": ["Tanzanian"],
    "South Africa": ["South African"],
    "Democratic Republic of the Congo": ["Congolese"],
    "Somalia": ["Somali"],
    "Tunisia": ["Tunisian"],
    "Algeria": ["Algerian"],
    "Germany": ["German", "Germany"],
    "United Kingdom": ["British", "English", "United Kingdom"],
    "Greece": ["Greek", "Greece"],
    "Poland": ["Polish", "Poland"],
    "Hungary": ["Hungarian", "Hungary"],
    "Portugal": ["Portuguese", "Portugal"],
    "Netherlands": ["Dutch", "Netherlands"],
    "Belgium": ["Belgian", "Belgium"],
    "Switzerland": ["Swiss", "Switzerland"],
    "Austria": ["Austrian", "Austria"],
    "Czech Republic": ["Czech"],
    "Romania": ["Romanian", "Romania"],
    "Ukraine": ["Ukrainian", "Ukraine"],
    "Georgia": ["Georgian"],
    "Armenia": ["Armenian"],
    "Basque Country": ["Basque"],
    "Catalan": ["Catalan"],
    "Sicily": ["Sicilian", "Sicily"],
    "Sweden": ["Swedish", "Sweden"],
    "Norway": ["Norwegian", "Norway"],
    "Denmark": ["Danish", "Denmark"],
    "Finland": ["Finnish", "Finland"],
    "Ireland": ["Irish", "Ireland"],
    "Scotland": ["Scottish", "Scotland"],
    "Peru": ["Peruvian", "Peru"],
    "Argentina": ["Argentine", "Argentinian", "Argentina"],
    "Colombia": ["Colombian", "Colombia"],
    "Cuba": ["Cuban", "Cuba"],
    "Jamaica": ["Jamaican", "Jamaica"],
    "Puerto Rico": ["Puerto Rican"],
    "Haiti": ["Haitian", "Haiti"],
    "Trinidad and Tobago": ["Trinidadian", "Trinidad"],
    "Cajun/Creole": ["Cajun", "Creole"],
    "Southern US": ["Southern US", "Southern"],
    "Tex-Mex": ["Tex-Mex"],
    "Hawaii": ["Hawaiian", "Hawaii"],
    "Native American": ["Native American"],
    "Brazil": ["Brazilian", "Brazil"],
    "Australia": ["Australian", "Australia"],
    "New Zealand": ["New Zealand", "Kiwi"],
    "Polynesian": ["Polynesian"],
    "Fiji": ["Fijian", "Fiji"],
}


# ============================================================================
# WORLD MEAL PATTERNS — 72 cultures × 4 meals
# Each: (meal_name, typical_time, description, typical_foods, social_context)
# Order: breakfast, lunch, dinner, snack
# ============================================================================
WORLD_MEAL_PATTERNS = [
    # === EAST ASIA ===
    ("Vietnamese", [
        ("phở sáng (breakfast)", "6-8 AM", "Pho or bánh mì from street vendors", "Pho, banh mi, xoi, banh cuon, ca phe sua da", "Street food dominates breakfast; ca phe sua da ritual"),
        ("bữa trưa (lunch)", "11:30-1 PM", "Rice-based meal with protein and vegetables", "Com tam, bun bo Hue, banh xeo, goi cuon, canh chua", "Street stalls or workplace cafeterias; broken rice popular"),
        ("bữa tối (dinner)", "6-8 PM", "Family dinner with shared dishes", "Hotpot, grilled meats, stir-fries, rice, canh", "Family gathers around shared dishes; communal style"),
        ("ăn vặt (snack)", "any time", "Street snacking culture", "Che, banh trang tron, sugarcane juice, tropical fruit", "Night market snack culture thrives; che dessert soup"),
    ]),
    ("Filipino", [
        ("almusal (breakfast)", "6-8 AM", "Heavy rice meal with silog combinations", "Sinangag, longganisa, tocino, tapa, pandesal, coffee", "Silog meals define Filipino breakfast tradition"),
        ("tanghalian (lunch)", "12-1 PM", "Rice with ulam (viand)", "Adobo, sinigang, kare-kare, rice, ensalada, pancit", "Rice is essential; ulam is the star of the plate"),
        ("hapunan (dinner)", "6-8 PM", "Family meal similar to lunch", "Lechon, tinola, paksiw, rice, vegetables, caldereta", "Family meal; mano po greeting before eating"),
        ("merienda (snack)", "3-5 PM", "Sweet or savory afternoon snacks", "Halo-halo, turon, puto, lumpia, bibingka, taho", "Spanish-influenced; two meriendas per day tradition"),
    ]),
    ("Malaysian", [
        ("sarapan (breakfast)", "7-9 AM", "Nasi lemak or roti canai with teh tarik", "Nasi lemak, roti canai, teh tarik, dim sum, kaya toast", "Mamak stalls serve multiethnic breakfast all hours"),
        ("makan tengahari (lunch)", "12-2 PM", "Rice with dishes from food court", "Nasi campur, laksa, char kway teow, satay, nasi goreng", "Food courts with Malay, Chinese, Indian options side by side"),
        ("makan malam (dinner)", "7-9 PM", "Family or hawker meal", "Rendang, nasi goreng, curry, roti, seafood, sup kambing", "Pasar malam (night market) culture; mamak supper runs late"),
        ("minum petang (tea)", "4-5 PM", "Tea and kuih snacks", "Teh tarik, kuih, curry puff, pisang goreng, apam balik", "British afternoon tea adapted with local kuih"),
    ]),
    ("Burmese", [
        ("mone hin ga (breakfast)", "6-8 AM", "Mohinga fish noodle soup", "Mohinga, ohn no khao swe, nan bya, samosa, strong tea", "Mohinga is unofficial national dish; tea shop culture"),
        ("ne le za (lunch)", "11:30-1 PM", "Rice with multiple curries", "Rice, htamin, curry, ngapi, salad, soup, hin", "Multiple small dishes shared family-style"),
        ("nya za (dinner)", "5-7 PM", "Similar to lunch but lighter", "Shan noodles, curry, salad, soup, rice, mohinga", "Earlier dinner than most Asian cultures"),
        ("lahpet thoke (snack)", "any time", "Tea leaf salad and snacks", "Lahpet thoke, fried beans, sesame, garlic, dried shrimp", "Tea leaf salad is quintessential social food"),
    ]),
    ("Cambodian", [
        ("bai pruk (breakfast)", "6-8 AM", "Rice porridge or noodle soup", "Bobor, kuy teav, num pang, bai sach chrouk, coffee", "Bai sach chrouk (pork rice) is beloved morning dish"),
        ("bai thngai trong (lunch)", "11:30-1 PM", "Rice with fish and curry", "Amok, samlor korko, stir-fries, rice, fish, prahok", "Fish is key protein; prahok paste defines the cuisine"),
        ("bai lngiet (dinner)", "6-8 PM", "Lighter family meal", "Soups, grilled fish, vegetables, rice, salad, samlor", "Family dinner; simpler than lunch"),
        ("nom (snack)", "any time", "Sweet coconut-based snacks", "Num krok, num banh chok, sticky rice, tropical fruits", "Sweet coconut snacks popular at markets"),
    ]),
    ("Mongolian", [
        ("öglöönii tsai (breakfast)", "7-9 AM", "Salty milk tea and dairy", "Suutei tsai, bootsog, aaruul, bread, butter, boortsog", "Salty milk tea starts every day in the ger"),
        ("ödriin khool (lunch)", "12-2 PM", "Meat-heavy steamed dumplings", "Buuz, khuushuur, tsuivan, bansh, guriltai shul", "Hearty portions; mutton is primary protein"),
        ("oroin khool (dinner)", "6-8 PM", "Meat and noodle soup", "Guriltai shul, khorkhog, bantan, bread, buuz", "Family meal in the ger; guests always fed first"),
        ("tsai (tea)", "all day", "Milk tea and dried curd", "Suutei tsai, airag, aaruul, bootsog, boortsog", "Hospitality ritual; refusing tea is considered rude"),
    ]),

    # === SOUTH ASIA ===
    ("Pakistani", [
        ("nashta (breakfast)", "7-9 AM", "Halwa puri or nihari with chai", "Halwa puri, paratha, omelette, chai, nihari, channay", "Chai is essential; nihari for Sunday breakfast tradition"),
        ("dopahar ka khana (lunch)", "1-3 PM", "Biryani or roti with curry", "Biryani, dal, sabzi, roti, raita, pickle, qorma", "Friday biryani tradition; lunch is substantial meal"),
        ("raat ka khana (dinner)", "8-10 PM", "Full family meal", "Karahi, seekh kebab, naan, rice, dal, salad, chapli kebab", "Late family dinner; meat-focused; naan from tandoor"),
        ("chai time (snack)", "4-6 PM", "Chai and fried snacks", "Chai, samosa, pakora, cake rusk, biscuits, jalebi", "Chai culture pervades all social interactions"),
    ]),
    ("Sri Lankan", [
        ("udē kǣma (breakfast)", "7-9 AM", "Hoppers or string hoppers with curry", "String hoppers, hoppers, kiribath, pol sambol, curry", "Kiribath (milk rice) for auspicious occasions"),
        ("dival kǣma (lunch)", "12:30-2 PM", "Rice and curry feast", "Rice, multiple curries, sambol, papadam, mallung, dhal", "Up to 8 curries on plate; banana leaf presentation"),
        ("rǣ kǣma (dinner)", "7-9 PM", "Lighter rice and curry or kottu", "Rice, curry, roti, kottu roti, soup, fish curry", "Kottu roti sound echoes through streets at night"),
        ("bē kǣma (tea)", "4 PM", "Ceylon tea and short eats", "Ceylon tea, patties, rolls, vadai, kavum, kokis", "British tea tradition merged with local short eats"),
    ]),
    ("Bangladeshi", [
        ("nashta (breakfast)", "7-9 AM", "Paratha or pitha with cha", "Paratha, dal puri, pitha, ruti, cha, bhaji, luchi", "Cha (tea) essential; pithas popular during winter"),
        ("dupur-er khabar (lunch)", "1-2 PM", "Rice with fish curry", "Rice, fish curry, dal, bhaji, vorta, shutki, begun bhaja", "Fish and rice define the cuisine; mustard oil key"),
        ("rater khabar (dinner)", "8-10 PM", "Similar to lunch", "Rice, meat curry, dal, salad, chutney, fish, shak", "Late dinner; slightly more meat than lunch"),
        ("bikaler nashta (snack)", "5-6 PM", "Cha and street food", "Cha, singara, puchka, jhalmuri, chotpoti, fuchka", "Street food snacking culture widespread"),
    ]),
    ("Nepali", [
        ("bihana ko khana (breakfast)", "7-9 AM", "Tea and light snack", "Sel roti, chiya, chiura, aloo tarkari, roti, tea", "Light breakfast before the main dal bhat"),
        ("khana (lunch)", "10 AM-12 PM", "Dal bhat tarkari", "Dal bhat, tarkari, achar, gundruk, saag, masu", "Dal bhat power 24 hour — the national motto"),
        ("beluka ko khana (dinner)", "7-8 PM", "Dal bhat again", "Dal bhat, tarkari, meat curry, achar, saag, papad", "Same structure as lunch; dal bhat eaten twice daily"),
        ("khaja (snack)", "3-5 PM", "Momos and chiya", "Momo, chiya, chatpate, sekuwa, samosa, sel roti", "Momo culture is huge; chiya pasal on every corner"),
    ]),
    ("Afghan", [
        ("nashta (breakfast)", "7-9 AM", "Naan bread and green tea", "Naan, green tea, cream, eggs, fruit, jam, honey", "Bread (naan) is sacred; never wasted or disrespected"),
        ("de chasht dodai (lunch)", "12-2 PM", "Kabuli pulao or kebab", "Kabuli pulao, mantu, ashak, kebab, salad, bolani", "Kabuli pulao is source of national pride"),
        ("de shaam dodai (dinner)", "7-9 PM", "Hearty shared meal", "Qorma, shorwa, naan, kebab, rice, sabzi, aush", "Communal floor dining; right hand only"),
        ("chai (snack)", "throughout", "Tea ceremony with dried fruits", "Chai sabz, chai siah, kulcha, dried fruits, nuts", "Tea ceremony defines Afghan hospitality"),
    ]),

    # === SOUTHEAST ASIA ===
    ("Singaporean", [
        ("zǎocān (breakfast)", "7-9 AM", "Kaya toast set or dim sum", "Kaya toast, soft-boiled eggs, kopi, roti prata, dim sum", "Kopitiam culture; multiethnic breakfast options"),
        ("wǔcān (lunch)", "12-2 PM", "Hawker center meal", "Chicken rice, laksa, char kway teow, nasi lemak, bee hoon", "Hawker centers are UNESCO heritage; cheap and excellent"),
        ("wǎncān (dinner)", "7-9 PM", "Hawker or restaurant", "Chili crab, satay, hokkien mee, bak kut teh, zi char", "Supper culture runs late into the night"),
        ("xiàwǔchá (tea)", "3-5 PM", "Kopi and kueh", "Kopi, teh, egg tart, pandan cake, kueh, ice kachang", "Afternoon break from British colonial influence"),
    ]),
    ("Laotian", [
        ("khao chao (breakfast)", "6-8 AM", "Sticky rice and laap", "Khao niaw, laap, khao piak sen, baguette, Lao coffee", "French-influenced coffee alongside sticky rice"),
        ("khao thiang (lunch)", "11:30-1 PM", "Sticky rice with som and laap", "Sticky rice, laap, som tam, ping kai, jeow, tam mak hoong", "Sticky rice rolled by hand from communal basket"),
        ("khao kham (dinner)", "6-8 PM", "Family dinner", "Sticky rice, or lam, laap, fish, vegetables, jeow", "Communal sharing; laap for celebrations"),
        ("khao lam (snack)", "any time", "Street food and baguettes", "Khao lam, khao poun, baguette sandwich, fruit, Beer Lao", "Beer Lao accompanies evening snacking"),
    ]),

    # === MIDDLE EAST ===
    ("Lebanese", [
        ("fṭūr (breakfast)", "7-9 AM", "Manakish and labneh spread", "Manakish, labneh, foul, hummus, falafel, Arabic coffee", "Fresh manakish from neighborhood bakeries"),
        ("ghadā (lunch)", "1-3 PM", "Full mezze and grilled meats", "Kibbeh, tabbouleh, fattoush, grilled meats, rice, hummus", "Biggest meal; elaborate mezze spread common"),
        ("ʿashā (dinner)", "8-10 PM", "Lighter mezze or shawarma", "Mezze spread, grilled halloumi, shawarma, manakish, bread", "Often lighter; late dinner is the norm"),
        ("qahwa (snack)", "throughout", "Arabic coffee and pastries", "Arabic coffee, baklava, maamoul, knafeh, dried fruits", "Coffee ritual is cornerstone of hospitality"),
    ]),
    ("Iraqi", [
        ("fuṭūr (breakfast)", "7-9 AM", "Bread with gaimer and date syrup", "Khubz, gaimer, eggs, date syrup, chai, foul, samoon", "Gaimer (clotted cream) with date syrup is uniquely Iraqi"),
        ("ghadā (lunch)", "1-3 PM", "Rice and stew or masgouf", "Quzi, dolma, biryani, kebab, masgouf, rice, tepsi baytinijan", "Dolma-making is communal family activity"),
        ("ʿashā (dinner)", "8-10 PM", "Kubba or lighter fare", "Kubba, soup, bread, salad, kebab, tashreeb", "Friday lunch is bigger; dinner lighter"),
        ("chai (snack)", "throughout", "Iraqi chai with kleicha", "Chai, kleicha, dates, baklava, samoon, halawat dihin", "Chai served in istikan glasses; always offered to guests"),
    ]),
    ("Yemeni", [
        ("fuṭūr (breakfast)", "6-8 AM", "Ful and flatbread with honey", "Ful medames, lahoh, fatoot, eggs, bint al-sahn, honey", "Bint al-sahn with honey is celebration food"),
        ("ghadā (lunch)", "12-2 PM", "Saltah or mandi", "Saltah, zurbiyan, fahsa, mandi, rice, schug, hulba", "Saltah is national dish; communal from one pot"),
        ("ʿashā (dinner)", "8-10 PM", "Lighter bread-based meal", "Lahoh, mufarrak, shakshouka, bread, broth, aseed", "Lighter than lunch; bread is central"),
        ("chai haleeb (snack)", "2-5 PM", "Sweet tea and pastries", "Chai haleeb, bint al-sahn, rawani, dates, basbousa", "Social bonding over afternoon spiced tea"),
    ]),
    ("Egyptian", [
        ("fiṭār (breakfast)", "7-9 AM", "Ful medames and tameya", "Ful medames, tameya, eggs, baladi bread, cheese, tea", "Ful cart on every corner; national breakfast"),
        ("ghadā (lunch)", "2-4 PM", "Koshary or molokhia", "Koshary, molokhia, mahshi, kebab, rice, fattoush, roz", "Koshary is Cairo street food king; carb-loaded"),
        ("ʿasha (dinner)", "9-11 PM", "Light meal or mezze", "Mezze, grilled meats, salad, bread, cheese, shakshuka", "Very late dinner; can be just bread and cheese"),
        ("shai (snack)", "throughout", "Sweet tea and pastries", "Shai, basbousa, konafa, feteer meshaltet, dates, qamar al-din", "Sweet tea culture; pastries ubiquitous"),
    ]),
    ("Syrian", [
        ("fuṭūr (breakfast)", "7-9 AM", "Fatteh and zeit o zaatar", "Fatteh, labne, zeit o zaatar, eggs, olives, bread, makdous", "Elaborate breakfast spreads on weekends"),
        ("ghadā (lunch)", "1-3 PM", "Kibbeh or stuffed vegetables", "Kibbeh, yalanji, mujadara, kebab, rice, tabbouleh, fattet", "Main meal; traditional home cooking from scratch"),
        ("ʿashā (dinner)", "8-10 PM", "Lighter fare or mezze", "Fattoush, hummus, manakish, grilled halloumi, bread, labneh", "Mezze-style dinners common; social occasion"),
        ("qahwa (snack)", "afternoon", "Arabic coffee and sweets", "Arabic coffee with cardamom, barazek, maamoul, ghraybeh", "Sweet pastries complement bitter coffee"),
    ]),
    ("Emirati", [
        ("fuṭūr (breakfast)", "7-9 AM", "Balaleet or chebab", "Balaleet, chebab, regag, beid w tomat, khameer, gahwa", "Traditional Emirati breakfast distinct from Levantine"),
        ("ghadā (lunch)", "1-3 PM", "Machboos or harees", "Machboos, harees, thareed, madrooba, salona, biryani", "Friday lunch is biggest family gathering of the week"),
        ("ʿashā (dinner)", "8-10 PM", "International or traditional", "Grilled meats, rice, fattoush, machboos, harees", "Global dining scene; traditional at home"),
        ("gahwa (snack)", "throughout", "Arabic coffee with dates", "Gahwa, dates, luqaimat, khanfaroosh, balaleet, chebab", "Gahwa with dates is non-negotiable hospitality"),
    ]),
    ("Israeli", [
        ("aruchat boker (breakfast)", "7-9 AM", "Israeli breakfast spread", "Shakshuka, salad, cheese, bread, eggs, hummus, labane", "Israeli breakfast is institution; salad at breakfast"),
        ("aruchat tsohoraim (lunch)", "12-2 PM", "Falafel or schnitzel", "Falafel, shawarma, schnitzel, hummus, sabich, pita, salad", "Fast-paced lunch; falafel stands everywhere"),
        ("aruchat erev (dinner)", "7-9 PM", "Home-cooked family meal", "Chicken schnitzel, couscous, rice, salad, jachnun, cholent", "Shabbat dinner is elaborate multi-course affair"),
        ("aruchat esser (snack)", "10 AM", "Mid-morning snack", "Bamba, bissli, fruit, cottage cheese, Turkish coffee", "Workplace snack culture; Bamba is iconic"),
    ]),

    # === AFRICA ===
    ("Nigerian", [
        ("oúnjẹ àárọ̀ (breakfast)", "7-9 AM", "Akara and pap", "Akara, pap, moi moi, bread, akamu, tea, agege bread", "Akara (bean cakes) freshly fried each morning"),
        ("oúnjẹ ọ̀sán (lunch)", "1-3 PM", "Jollof rice or swallow", "Jollof rice, pounded yam, egusi, efo riro, suya, amala", "Jollof rice debates with Ghana are passionate"),
        ("oúnjẹ alẹ́ (dinner)", "7-9 PM", "Swallow and soup", "Fufu, ogbono, pepper soup, eba, okra soup, goat meat", "Hearty swallow meals dominate dinner"),
        ("owó àdáná (snack)", "any time", "Street food", "Suya, puff puff, chin chin, plantain chips, zobo, boli", "Suya spice-grilled meat is late-night staple"),
    ]),
    ("Ghanaian", [
        ("anɔpa aduane (breakfast)", "6-8 AM", "Hausa koko and koose", "Hausa koko, koose, rice water, bread, tea, egg, waakye", "Hausa koko with koose is classic street breakfast"),
        ("awia aduane (lunch)", "12-2 PM", "Banku or jollof rice", "Banku, tilapia, jollof rice, fufu, light soup, groundnut soup", "Banku and grilled tilapia is iconic pairing"),
        ("anwummere aduane (dinner)", "7-9 PM", "Fufu and soup", "Fufu, palm nut soup, kenkey, waakye, kelewele, red red", "Family gathers for fufu pounding tradition"),
        ("nkwan (snack)", "any time", "Street food", "Kelewele, bofrot, roasted plantain, meat pie, Fan Ice", "Kelewele (spiced fried plantain) sold everywhere"),
    ]),
    ("Senegalese", [
        ("ndeki (breakfast)", "7-9 AM", "Baguette and café Touba", "Baguette, café Touba, lakh, accara, chocolate, bread", "French-influenced baguette with Touba coffee"),
        ("añ (lunch)", "1-3 PM", "Thieboudienne from one bowl", "Thieboudienne, yassa, mafe, ceebu jën, pastels, rice", "Thieboudienne is national dish; shared from one bowl"),
        ("reer (dinner)", "8-10 PM", "Lighter soup or couscous", "Soupe kandia, couscous, lakh, thiéré, mafe", "Lighter than lunch; can be millet-based"),
        ("goûter (snack)", "4-6 PM", "Attaya tea ceremony", "Attaya, fataya, pastels, fruits, dibi, bissap", "Attaya: three rounds with decreasing bitterness"),
    ]),
    ("Kenyan", [
        ("kiamsha kinywa (breakfast)", "7-9 AM", "Chai and mandazi", "Chai, mandazi, uji, bread, eggs, arrowroot, chapati", "Sweet milky chai with mandazi is quintessential"),
        ("chakula cha mchana (lunch)", "12-2 PM", "Ugali and sukuma wiki", "Ugali, sukuma wiki, nyama choma, rice, beans, githeri", "Ugali is staple starch; eaten with hands"),
        ("chakula cha jioni (dinner)", "7-9 PM", "Hearty family meal", "Nyama choma, ugali, mukimo, pilau, chapati, stew", "Nyama choma (grilled meat) for celebrations"),
        ("chai (snack)", "10 AM & 4 PM", "Kenyan chai masala", "Chai, mandazi, samosa, bhajia, mutura, mahamri", "British-influenced tea breaks; chai masala popular"),
    ]),
    ("Tanzanian", [
        ("chakula cha asubuhi (breakfast)", "7-9 AM", "Vitumbua or uji porridge", "Vitumbua, uji, chapati, mandazi, chai, kashata", "Coastal breakfasts differ from highland fare"),
        ("chakula cha mchana (lunch)", "12-2 PM", "Ugali or pilau", "Ugali, wali, maharage, nyama, mboga, pilau, ndizi", "Wali (rice) and maharage (beans) for everyday"),
        ("chakula cha jioni (dinner)", "7-9 PM", "Full family meal", "Ugali, ndizi nyama, mchicha, grilled fish, biryani", "Zanzibar influence on coast; biryani tradition"),
        ("vitafunio (snack)", "any time", "Street food innovation", "Mishkaki, chipsi mayai, zanzibar mix, kashata, vitumbua", "Chipsi mayai (chips omelette) is street invention"),
    ]),
    ("South African", [
        ("ontbyt (breakfast)", "7-9 AM", "Full English or pap", "Pap, boerewors, eggs, toast, rusks, rooibos, mieliepap", "English fry-up or pap with wors; rooibos tea"),
        ("middagete (lunch)", "12-2 PM", "Bunny chow or braai", "Bunny chow, vetkoek, bobotie, braai, chakalaka, gatsby", "Bunny chow (curry in bread) from Durban; gatsby in Cape Town"),
        ("aandete (dinner)", "6-8 PM", "Braai or potjiekos", "Braai, potjiekos, pap, boerewors, biltong, sosatie, bobotie", "Braai culture is social institution; every occasion"),
        ("biltong time (snack)", "any time", "Biltong and treats", "Biltong, droëwors, koeksisters, melktert, rusks", "Biltong is the national snack; always available"),
    ]),
    ("Congolese", [
        ("bilei ya ntongo (breakfast)", "7-9 AM", "Bread or chikwanga", "Baguette, chikwanga, tea, boiled eggs, beignets, coffee", "French influence; chikwanga (cassava bread) traditional"),
        ("bilei ya midi (lunch)", "12-2 PM", "Fufu and pondu", "Fufu, pondu, saka-saka, liboke, grilled fish, makemba", "Pondu (cassava leaves) is daily staple"),
        ("bilei ya butu (dinner)", "7-9 PM", "Moambe or lighter stew", "Fufu, moambe, fish stew, rice, plantain, ndakala", "Moambe (palm nut stew) is national dish"),
        ("bilei ya kati-kati (snack)", "any time", "Street food", "Beignets, grilled corn, mikate, brochettes, kwanga", "Brochettes (grilled meat) popular street food"),
    ]),
    ("Somali", [
        ("quraac (breakfast)", "6-8 AM", "Canjeero and suqaar", "Canjeero, laxoox, suqaar, liver, tea with milk, ful", "Canjeero (fermented flatbread) with spiced meat"),
        ("qado (lunch)", "12-2 PM", "Bariis or pasta", "Bariis iskukaris, baasto, suqaar, muufo, banana, hilib", "Italian-influenced pasta tradition; banana with meals"),
        ("casho (dinner)", "7-9 PM", "Meat stew or rice", "Hilib ari, suqaar, cambuulo, canjeero, rice, maraq", "Communal eating; meat is central to the meal"),
        ("shaah (snack)", "throughout", "Spiced Somali chai", "Shaah, xalwo, sambusa, bur, dates, halwa", "Tea heavily spiced with cardamom, cinnamon, clove"),
    ]),
    ("Tunisian", [
        ("fṭūr (breakfast)", "7-9 AM", "Bread with olive oil and harissa", "Bread, olive oil, harissa, eggs, tea, labna, ftir", "Simple breakfast; olive oil and harissa are king"),
        ("ghadā (lunch)", "12-2 PM", "Couscous or brik", "Couscous, lablabi, ojja, brik, mechouia, kafteji, tagine", "Friday couscous is sacred family tradition"),
        ("ʿashā (dinner)", "8-10 PM", "Lighter meal", "Brik, chorba, salad, shakshuka, bread, cheese, slata", "Can be just brik and salad on weeknights"),
        ("qahwa (snack)", "afternoon", "Mint tea and sweets", "Mint tea, Turkish coffee, bambalouni, makroudh, dates", "Café culture; mint tea ritual with pine nuts"),
    ]),
    ("Algerian", [
        ("fṭūr (breakfast)", "7-9 AM", "Bread and café au lait", "Kesra, msemen, café au lait, butter, jam, cheese, matlouh", "French-influenced coffee with traditional breads"),
        ("ghadā (lunch)", "12-2 PM", "Couscous or chorba", "Couscous, chorba frik, rechta, dolma, mehjouba, chakhchoukha", "Friday couscous tradition is paramount"),
        ("ʿashā (dinner)", "7-9 PM", "Lighter fare", "Bourek, chorba, merguez, salad, bread, lben, garantita", "Lighter dinner; lben (buttermilk) common"),
        ("goûter (snack)", "4 PM", "Mint tea and pastries", "Mint tea, makrout, baghrir, griwech, zlabia, qalb el louz", "Ramadan sweets tradition carries year-round"),
    ]),

    # === EUROPE ===
    ("German", [
        ("Frühstück (breakfast)", "7-9 AM", "Bread rolls with cold cuts and cheese", "Brötchen, Aufschnitt, cheese, Müsli, eggs, coffee, Quark", "Bakery visit for fresh Brötchen is morning ritual"),
        ("Mittagessen (lunch)", "12-2 PM", "Hot main meal", "Schnitzel, Kartoffeln, Bratwurst, Eintopf, Spätzle, sauerkraut", "Traditional hot meal; changing to lighter in cities"),
        ("Abendessen (dinner)", "6-8 PM", "Abendbrot — bread supper", "Brot, Aufschnitt, cheese, pickles, Kartoffelsalat, Brezeln", "Abendbrot: simple bread-and-cold-cuts supper tradition"),
        ("Kaffee und Kuchen (snack)", "3-4 PM", "Coffee and cake", "Kaffee, Kuchen, Strudel, Schwarzwälder Kirschtorte, Brezel", "Sunday Kaffee und Kuchen is institution"),
    ]),
    ("British", [
        ("breakfast (breakfast)", "7-9 AM", "Full English or toast", "Bacon, eggs, sausage, beans, toast, black pudding, tea", "Full English on weekends; toast and tea on weekdays"),
        ("lunch (lunch)", "12-2 PM", "Sandwich or Sunday roast", "Sandwich, ploughman's, fish and chips, pie, Sunday roast", "Sunday roast is family tradition; pub lunches"),
        ("dinner (dinner)", "6-8 PM", "Meat and two veg", "Bangers and mash, shepherd's pie, curry, chips, roast", "Curry is now national dish; Friday chip shop tradition"),
        ("afternoon tea (snack)", "3-5 PM", "Tea and scones", "Tea, scones, finger sandwiches, Victoria sponge, clotted cream", "Afternoon tea ritual; cream tea in Devon and Cornwall"),
    ]),
    ("Greek", [
        ("proïnó (breakfast)", "7-9 AM", "Light yogurt and coffee", "Greek yogurt, honey, bread, olive oil, koulouri, frappé", "Light breakfast; frappé coffee culture"),
        ("mesimeriané (lunch)", "1-3 PM", "Main meal followed by siesta", "Moussaka, souvlaki, horiatiki, spanakopita, dolmades, feta", "Biggest meal; followed by siesta tradition"),
        ("vrathino (dinner)", "9-11 PM", "Taverna meze and grilled fish", "Meze, grilled fish, lamb, salad, tzatziki, bread, souvlaki", "Very late dinner; taverna socializing for hours"),
        ("kafé (snack)", "throughout", "Greek coffee and pastries", "Greek coffee, frappé, loukoumades, baklava, koulouri", "Kafeneio culture; hours spent over one coffee"),
    ]),
    ("Polish", [
        ("śniadanie (breakfast)", "7-9 AM", "Bread with cold cuts", "Chleb, kiełbasa, cheese, eggs, tomato, cucumber, tea, twaróg", "Substantial sandwich-style breakfast"),
        ("obiad (lunch)", "1-3 PM", "Main meal with soup first", "Bigos, pierogi, żurek, schabowy, barszcz, kopytka, kotlet", "Obiad is the big meal; soup always comes first"),
        ("kolacja (dinner)", "6-8 PM", "Light bread supper", "Bread, cold cuts, sałatka, kanapki, tea, twaróg", "Light bread-based supper like German Abendbrot"),
        ("podwieczorek (snack)", "4-5 PM", "Tea and pastry", "Herbata, szarlotka, pączki, sernik, kremówka, makowiec", "Pączki on Fat Thursday is massive tradition"),
    ]),
    ("Hungarian", [
        ("reggeli (breakfast)", "7-9 AM", "Bread with spreads", "Kenyér, szalonna, kolbász, eggs, pogácsa, coffee, túró rudi", "Hearty bread-based breakfast"),
        ("ebéd (lunch)", "12-2 PM", "Gulyás or main dish", "Gulyás, pörkölt, töltött káposzta, lángos, lecsó, halászlé", "Three courses: soup, main, dessert tradition"),
        ("vacsora (dinner)", "7-9 PM", "Lighter cold meal", "Cold cuts, bread, túrós csusza, salads, soup, körözött", "Similar to kolacja; lighter than lunch"),
        ("uzsonna (snack)", "3-5 PM", "Street food and cake", "Kürtőskalács, rétes, pogácsa, lángos, coffee, túró rudi", "Kürtőskalács from street vendors; lángos at markets"),
    ]),
    ("Portuguese", [
        ("pequeno-almoço (breakfast)", "7-9 AM", "Pastel de nata and galão", "Pastel de nata, tosta mista, galão, pão com manteiga", "Pastelaria visit for pastéis and coffee is daily"),
        ("almoço (lunch)", "12:30-2:30 PM", "Bacalhau or grilled fish", "Bacalhau, arroz, caldo verde, francesinha, bitoque, sardinha", "Bacalhau: 365 recipes, one for each day of the year"),
        ("jantar (dinner)", "8-9:30 PM", "Lighter than lunch", "Grilled sardines, caldo verde, petiscos, sandes, arroz de marisco", "Petiscos (Portuguese tapas) culture growing"),
        ("lanche (snack)", "4-5 PM", "Pastry and espresso", "Bica, pastel de nata, bola de Berlim, croissant, café", "Pastelaria culture is daily ritual"),
    ]),
    ("Dutch", [
        ("ontbijt (breakfast)", "7-8 AM", "Bread with hagelslag", "Brood, hagelslag, kaas, roggebrood, boterham, coffee, ontbijtkoek", "Hagelslag (chocolate sprinkles) on bread is iconic"),
        ("lunch (lunch)", "12-1 PM", "Quick sandwich", "Broodje, kaas, kroket, uitsmijter, erwtensoep, tosti", "Lunch is quick sandwich; no hot meal tradition"),
        ("avondeten (dinner)", "6-7 PM", "AVG: potatoes, meat, veg", "Stamppot, bitterballen, hachee, rookworst, hutspot, boerenkool", "Dinner at 6 sharp; AVG tradition (aardappelen, vlees, groente)"),
        ("borrel (snack)", "5-7 PM", "Drinks and bites", "Bitterballen, kaasblokjes, haring, beer, jenever, frikandel", "Borrel culture: drinks with bite-sized snacks"),
    ]),
    ("Belgian", [
        ("petit-déjeuner (breakfast)", "7-9 AM", "Waffles and chocolate", "Wafels, bread, chocolate, confiture, coffee, cramique", "Waffle types vary by region (Liège vs Brussels)"),
        ("déjeuner (lunch)", "12-2 PM", "Moules-frites or stoofvlees", "Moules-frites, stoofvlees, vol-au-vent, croquettes, waterzooi", "Beer pairing with every meal is expected"),
        ("dîner (dinner)", "7-9 PM", "Hearty Belgian fare", "Carbonade flamande, witloof, stoemp, rabbit, frites, boulets", "Frites culture; frituur on every corner"),
        ("goûter (snack)", "4 PM", "Chocolate and beer", "Belgian chocolate, speculoos, gaufre, beer, pralines", "Chocolate craftsmanship; artisan praline shops"),
    ]),
    ("Swiss", [
        ("Zmorge (breakfast)", "7-8 AM", "Bircher muesli and zopf bread", "Bircher muesli, zopf, bread, butter, jam, cheese, coffee", "Bircher muesli invented here; zopf on Sundays"),
        ("Zmittag (lunch)", "12-1 PM", "Rösti or hot meal", "Rösti, raclette, zürigschnätzlets, cordon bleu, polenta, wurst", "Quick hot lunch; Rösti varies by region"),
        ("Znacht (dinner)", "6-8 PM", "Fondue or cold plate", "Fondue, raclette, Älplermagronen, cold cuts, bread, cheese", "Fondue and raclette are social winter rituals"),
        ("Zvieri (snack)", "4 PM", "Coffee and cake", "Kaffi, nusstorte, rüblitorte, leckerli, chocolate, gipfeli", "Regional cake specialties; Engadiner Nusstorte"),
    ]),
    ("Austrian", [
        ("Frühstück (breakfast)", "7-9 AM", "Semmel and Melange coffee", "Semmel, butter, jam, Müsli, eggs, Melange, Topfenstrudel", "Café culture; Melange is the go-to morning coffee"),
        ("Mittagessen (lunch)", "12-2 PM", "Wiener Schnitzel or Tafelspitz", "Wiener Schnitzel, Tafelspitz, Knödel, Gulasch, Erdäpfelsalat", "Beisl (pub) lunch culture; proper hot meal"),
        ("Abendessen (dinner)", "6-8 PM", "Jause — cold plate", "Brettljause, cold cuts, bread, cheese, pickles, Liptauer", "Jause is Austrian answer to Brotzeit"),
        ("Jause (snack)", "3-4 PM", "Kaffeehaus ritual", "Sachertorte, Apfelstrudel, Melange, Palatschinken, Kaiserschmarrn", "Kaffeehaus culture is UNESCO heritage"),
    ]),
    ("Czech", [
        ("snídaně (breakfast)", "7-9 AM", "Rolls with spreads", "Rohlík, chléb, butter, ham, cheese, coffee, tvaroh", "Rohlíky (rolls) fresh from bakery"),
        ("oběd (lunch)", "12-2 PM", "Svíčková or vepřo-knedlo-zelo", "Svíčková, vepřo knedlo zelo, guláš, smažený sýr, bramboráky", "Lunch is main meal; svíčková is national pride"),
        ("večeře (dinner)", "6-8 PM", "Light supper", "Chlebíčky, cold cuts, utopenci, soup, utopenec, obložené", "Open-face chlebíčky sandwich tradition"),
        ("svačina (snack)", "3-4 PM", "Beer and snacks", "Pivo, trdelník, koláče, klobása, utopenec, bramborák", "Beer culture; more beer per capita than anywhere"),
    ]),
    ("Romanian", [
        ("mic dejun (breakfast)", "7-9 AM", "Bread and cheese", "Pâine, brânză, ouă, kaizer, roșii, cafea, covrigi", "Simple continental breakfast"),
        ("prânz (lunch)", "12-2 PM", "Ciorbă and sarmale", "Ciorbă de burtă, sarmale, mici, mămăligă, tocană, mititei", "Ciorbă (sour soup) starts every proper lunch"),
        ("cină (dinner)", "7-9 PM", "Mici and lighter fare", "Mici, salad, zacuscă, bread, cheese, telemea, ciorbă", "Mici at grătar is beloved; zacuscă preserved tradition"),
        ("gustare (snack)", "any time", "Street pastries", "Covrigi, gogoși, papanași, plăcintă, cafea, kurtos", "Covrigi (pretzels) sold on street corners"),
    ]),
    ("Ukrainian", [
        ("snidanok (breakfast)", "7-9 AM", "Syrnyky or kasha", "Syrnyky, kasha, butter bread, eggs, tea, coffee, tvorog", "Syrnyky (cheese pancakes) beloved morning food"),
        ("obid (lunch)", "12-2 PM", "Borshch and varenyky", "Borshch, varenyky, holubtsi, pampushky, deruny, kotleta", "Borshch is cultural identity; UNESCO heritage"),
        ("vecheria (dinner)", "6-8 PM", "Lighter meal with salo", "Deruny, salo, bread, pickled vegetables, kompot, holodets", "Salo (cured pork fat) with garlic on black bread"),
        ("poldnyk (snack)", "4 PM", "Tea and pastries", "Chai, medovik, pyrizhky, syrnyky, kompot, pampushky", "Pyrizhky (stuffed pies) from babusya tradition"),
    ]),
    ("Georgian", [
        ("sauzme (breakfast)", "8-10 AM", "Khachapuri and eggs", "Khachapuri, eggs, cheese, bread, tkemali, tea, lobiani", "Khachapuri Adjaruli with runny egg is iconic"),
        ("sadili (lunch)", "1-3 PM", "Mini-supra feast", "Khinkali, lobio, badrijani, pkhali, mtsvadi, churchkhela", "Even lunch can become mini-supra with toasts"),
        ("vakhshami (dinner)", "7-10 PM", "Full supra feast", "Khinkali, mtsvadi, satsivi, lobiani, elarji, chacha, pkhali", "Supra: tamada leads toasts; hours-long celebration"),
        ("chai (snack)", "4-5 PM", "Tea and churchkhela", "Chai, churchkhela, pelamushi, gozinaki, tklapi", "Churchkhela (grape-nut candy) is ancient street food"),
    ]),
    ("Armenian", [
        ("nakhacharash (breakfast)", "7-9 AM", "Lavash and cheese with herbs", "Lavash, cheese, herbs, eggs, honey, jam, coffee, sujukh", "Fresh lavash from tonir oven; herb-filled wraps"),
        ("chash (lunch)", "1-3 PM", "Khorovats or tolma", "Khorovats, tolma, harissa, pilaf, lahmajoun, basturma", "Khorovats (BBQ) is celebratory; men typically grill"),
        ("entrik (dinner)", "7-9 PM", "Lighter fare with tan", "Soup, lavash, cheese, dolma, salad, tan, spas", "Lighter than lunch; tan (yogurt drink) common"),
        ("srcharan (snack)", "4 PM", "Coffee and gata", "Armenian coffee, gata, pakhlava, dried fruit, sujukh", "Gata pastry for celebrations; coffee fortune reading"),
    ]),
    ("Basque", [
        ("gosaria (breakfast)", "7-9 AM", "Quick pintxo and coffee", "Coffee, pintxo, tostada, yogurt, zumo de naranja", "Quick standing breakfast at the bar"),
        ("bazkaria (lunch)", "1-3 PM", "Full gastronomic meal", "Bacalao al pil-pil, marmitako, txuleta, kokotxas, pintxos", "Gastronomic society (txoko) culture; men cook"),
        ("afaria (dinner)", "9-10 PM", "Pintxos bar crawl", "Pintxos, cider, txakoli, gilda, croquetas, txistorra", "Poteo/txikiteo: bar-hopping for pintxos and txakoli"),
        ("hamaiketako (snack)", "11 AM", "Mid-morning bite", "Pintxo, bocadillo, cider, txistorra, tortilla", "Hamaiketako literally means elevenses"),
    ]),
    ("Catalan", [
        ("esmorzar (breakfast)", "7-9 AM", "Pa amb tomàquet and coffee", "Pa amb tomàquet, coffee, ensaïmada, croissant, suc", "Bread rubbed with tomato and olive oil is staple"),
        ("dinar (lunch)", "1:30-3:30 PM", "Fideuà or calçotada", "Calçots, fideuà, escudella, butifarra, pa amb tomàquet", "Calçotada is seasonal outdoor feast; fideuà at coast"),
        ("sopar (dinner)", "9-10:30 PM", "Lighter supper", "Croquetes, escalivada, esqueixada, crema catalana, trinxat", "Late dinner; crema catalana for dessert"),
        ("berenar (snack)", "5-6 PM", "Afternoon coca and coffee", "Coca, xuixo, café, horchata, ensaïmada, neules", "Coca (flatbread) comes sweet or savory"),
    ]),
    ("Sicilian", [
        ("colazione (breakfast)", "7-9 AM", "Granita con brioche", "Granita, brioche, espresso, arancina, cornetto", "Granita in brioche bun is iconic summer breakfast"),
        ("pranzo (lunch)", "1-3 PM", "Pasta and seafood", "Pasta alla Norma, arancini, caponata, pesce spada, sfincione", "Generous pasta portions; Sunday pranzo is marathon"),
        ("cena (dinner)", "8-10 PM", "Lighter seafood", "Grilled swordfish, pane cunzato, insalata, frutta di mare", "Street food cena from mobile vendors"),
        ("passeggiata (snack)", "6-8 PM", "Evening stroll treats", "Cannolo, gelato, iris, sfogliatella, granita, brioche", "Evening passeggiata with gelato or cannolo"),
    ]),
    ("Swedish", [
        ("frukost (breakfast)", "7-8 AM", "Smörgås and filmjölk", "Smörgås, knäckebröd, filmjölk, müsli, kaviar tube, coffee", "Filmjölk (soured milk) with cereal is daily"),
        ("lunch (lunch)", "11:30-1 PM", "Dagens lunch special", "Husmanskost, köttbullar, ärtsoppa, pytt i panna, smörgåsbord", "Thursday: ärtsoppa och pannkakor tradition"),
        ("middag (dinner)", "6-7 PM", "Husmanskost comfort food", "Köttbullar, Janssons frestelse, falukorv, potatis, sill", "Fredagsmys (Friday coziness): tacos now tradition"),
        ("fika (snack)", "10 AM & 3 PM", "Sacred coffee break", "Kaffe, kanelbulle, chokladboll, prinsesstårta, fikabröd", "Fika is sacred and non-negotiable at work"),
    ]),
    ("Norwegian", [
        ("frokost (breakfast)", "7-8 AM", "Open sandwiches with brunost", "Brødskiver, brunost, smoked salmon, eggs, kaviar, coffee", "Brunost (brown cheese) is uniquely Norwegian"),
        ("lunsj (lunch)", "11:30-1 PM", "Matpakke packed lunch", "Matpakke, smørbrød, fish cakes, rugbrød, leverpostei", "Everyone brings packed lunch from home"),
        ("middag (dinner)", "4-6 PM", "Early hot meal", "Fårikål, kjøttkaker, pinnekjøtt, lutefisk, potatoes, fish", "Early dinner by European standards; fårikål national dish"),
        ("kveldsmat (snack)", "8-9 PM", "Evening bread meal", "Open sandwiches, brunost, lefse, cold cuts, milk, kvikk lunsj", "Second bread meal; evening snack tradition"),
    ]),
    ("Danish", [
        ("morgenmad (breakfast)", "7-8 AM", "Rugbrød and yogurt", "Rugbrød, smør, ost, ymer, havregryn, wienerbrød, coffee", "Wienerbrød (Danish pastry) originated here"),
        ("frokost (lunch)", "12-1 PM", "Smørrebrød art form", "Smørrebrød, herring, leverpostej, rugbrød, snaps, frikadeller", "Smørrebrød is elevated to edible art form"),
        ("aftensmad (dinner)", "6-7 PM", "Hygge dinner", "Frikadeller, stegt flæsk, flæskesteg, rødkål, kartofler", "Hygge dining: candles, coziness, slow pace"),
        ("kaffe og kage (snack)", "3 PM", "Coffee and cake", "Kaffe, drømmekage, kanelsnurrer, romkugler, hindbærsnitter", "Cake for every occasion and visitor"),
    ]),
    ("Finnish", [
        ("aamupala (breakfast)", "7-8 AM", "Porridge and rye bread", "Puuro, ruisleipä, karjalanpiirakka, butter, coffee, piimä", "Karjalanpiirakka (Karelian pie) with egg butter"),
        ("lounas (lunch)", "11-1 PM", "Soup or casserole", "Hernekeitto, kalakukko, lihapullat, perunalaatikko, salaatti", "Thursday: hernekeitto (pea soup) + pannukakku"),
        ("päivällinen (dinner)", "5-7 PM", "Home-cooked meal", "Poronkäristys, lohikeitto, kalakukko, maksalaatikko, perunat", "Reindeer in Lapland; salmon everywhere; early dinner"),
        ("kahvitauko (snack)", "10 AM & 2 PM", "Coffee and pulla", "Kahvi, pulla, korvapuusti, mustikkapiirakka, laskiaispulla", "Most coffee per capita in the world; pulla essential"),
    ]),
    ("Irish", [
        ("bricfeasta (breakfast)", "7-9 AM", "Full Irish fry-up", "Bacon, eggs, sausages, black pudding, white pudding, soda bread, tea", "Full Irish rivals Full English; pudding varieties"),
        ("lón (lunch)", "12-2 PM", "Soup and soda bread", "Potato soup, soda bread, toastie, coddle, boxty, sandwich", "Hearty soups; pubs serve lunch"),
        ("dinnéar (dinner)", "6-8 PM", "Meat and potatoes", "Irish stew, colcannon, boxty, bacon and cabbage, shepherd's pie", "Potatoes in some form at every dinner"),
        ("tae (snack)", "4 PM", "Tea and barm brack", "Barry's or Lyons tea, scones, barm brack, brown bread, butter", "Ireland drinks most tea per capita after Turkey"),
    ]),
    ("Scottish", [
        ("bracaist (breakfast)", "7-9 AM", "Full Scottish fry-up", "Lorne sausage, haggis, tattie scone, black pudding, porridge", "Porridge purists: only water and salt"),
        ("lunch (lunch)", "12-2 PM", "Scotch pie or soup", "Scotch broth, cullen skink, Scotch pie, bridies, haggis", "Scotch pie from the chippy; cullen skink from Moray"),
        ("tea (dinner)", "5-7 PM", "Hearty supper", "Haggis neeps and tatties, stovies, cranachan, fish supper", "Fish supper (fish and chips) is Friday tradition"),
        ("elevenses (snack)", "11 AM", "Tea and shortbread", "Tea, shortbread, Dundee cake, tablet, fudge, empire biscuit", "Shortbread with tea; tablet is Scottish candy"),
    ]),

    # === AMERICAS ===
    ("Peruvian", [
        ("desayuno (breakfast)", "7-9 AM", "Pan con chicharrón or tamales", "Pan con chicharrón, tamales, empanadas, quinoa, emoliente", "Emoliente (herbal drink) from street vendors"),
        ("almuerzo (lunch)", "12:30-3 PM", "Menú ejecutivo set lunch", "Ceviche, lomo saltado, ají de gallina, arroz con pollo, papa", "Menú del día tradition; ceviche only at lunch time"),
        ("cena (dinner)", "7-9 PM", "Anticuchos and lighter fare", "Anticuchos, arroz chaufa, causa, papa rellena, caldo", "Anticuchos from street carts at night"),
        ("lonche (snack)", "5-6 PM", "Tea and picarones", "Emoliente, picarones, churros, pan, alfajores, chicha", "Picarones (sweet potato donuts) street tradition"),
    ]),
    ("Argentine", [
        ("desayuno (breakfast)", "7-9 AM", "Medialunas and café", "Medialunas, tostadas, dulce de leche, café con leche, mate", "Café culture; medialunas from panadería"),
        ("almuerzo (lunch)", "12:30-2:30 PM", "Milanesa or empanadas", "Milanesa, empanadas, asado, pasta, ensalada, provoleta", "Sunday asado replaces formal lunch"),
        ("cena (dinner)", "9-11 PM", "Asado or pasta", "Asado, pasta, pizza, milanesa, provoleta, choripán", "Extremely late dinner; 10 PM is normal start"),
        ("merienda (snack)", "5-6 PM", "Mate and facturas", "Mate, facturas, alfajores, dulce de leche, tortas fritas", "Mate sharing is sacred social ritual"),
    ]),
    ("Colombian", [
        ("desayuno (breakfast)", "6-8 AM", "Arepa and hot chocolate", "Arepa, huevos, calentado, changua, chocolate santafereño", "Changua (milk-egg soup) for Bogotanos"),
        ("almuerzo (lunch)", "12-2 PM", "Corrientazo set lunch", "Bandeja paisa, ajiaco, arroz con pollo, sancocho, jugo natural", "Corrientazo: set lunch; juice with everything"),
        ("comida (dinner)", "7-9 PM", "Lighter meal", "Empanadas, tamales, sopas, arepas, calentado, buñuelos", "Can be just hot chocolate with bread"),
        ("onces (snack)", "3-5 PM", "Coffee and pandebono", "Coffee, pandebono, buñuelos, almojábanas, empanadas", "Onces (like elevenses, but mid-afternoon)"),
    ]),
    ("Cuban", [
        ("desayuno (breakfast)", "7-9 AM", "Cuban coffee and tostada", "Cuban coffee, tostada, croqueta, tortilla, pan cubano", "Café cubano with sugar foam starts the day"),
        ("almuerzo (lunch)", "12-2 PM", "Rice and beans with meat", "Arroz con frijoles, ropa vieja, lechón, yuca, plátanos", "Congri or moros y cristianos at every meal"),
        ("comida (dinner)", "7-9 PM", "Pork-centered meal", "Lechón asado, congri, tostones, vaca frita, potaje, arroz", "Sunday lechón tradition; pork is king"),
        ("merienda (snack)", "4-5 PM", "Croqueta preparada", "Croqueta preparada, pastelitos, batido, guarapo, colada", "Ventanitas (coffee windows) for colada pickup"),
    ]),
    ("Jamaican", [
        ("breakfast (breakfast)", "7-9 AM", "Ackee and saltfish", "Ackee and saltfish, callaloo, bammy, fried dumpling, Blue Mountain coffee", "Ackee and saltfish is national dish"),
        ("lunch (lunch)", "12-2 PM", "Rice and peas with jerk", "Rice and peas, jerk chicken, curry goat, festival, coleslaw", "Jerk from roadside drum smokers"),
        ("dinner (dinner)", "6-8 PM", "Oxtail or curry", "Oxtail, curry chicken, rice, fried plantain, steamed fish", "Sunday dinner is elaborate family affair"),
        ("snack (snack)", "any time", "Patty and coco bread", "Patty, coco bread, roast corn, sugar cane juice, sorrel", "Jamaican patty in coco bread is iconic"),
    ]),
    ("Puerto Rican", [
        ("desayuno (breakfast)", "7-9 AM", "Mallorca and café", "Mallorca, quesito, huevos, café con leche, avena, tostada", "Panadería (bakery) breakfast tradition"),
        ("almuerzo (lunch)", "12-2 PM", "Comida criolla", "Arroz con habichuelas, pernil, mofongo, asopao, tostones", "Rice and beans foundation of every meal"),
        ("cena (dinner)", "6-8 PM", "Mofongo or churrasco", "Mofongo, churrasco, arroz con gandules, lechón, pasteles", "Lechón asado for holidays and celebrations"),
        ("merienda (snack)", "3-5 PM", "Frituras from kiosks", "Alcapurria, bacalaíto, piragua, limber, mallorca, sorullitos", "Chinchorreo: hopping from fry shack to fry shack"),
    ]),
    ("Haitian", [
        ("dejene (breakfast)", "7-9 AM", "Spaghetti or akasan", "Spaghetti, akasan, bread, peanut butter, coffee, banane peze", "Spaghetti for breakfast is uniquely Haitian"),
        ("manje midi (lunch)", "12-2 PM", "Diri ak pwa", "Diri ak pwa nwa, griot, pikliz, bannann peze, legim, poulet", "Diri kole ak pwa (rice stuck with beans) is soul food"),
        ("soupe (dinner)", "6-8 PM", "Soup or bouyon", "Bouyon, tchaka, soup joumou, legim, poisson gwo sel", "Soup joumou on Jan 1 celebrates independence"),
        ("goute (snack)", "any time", "Fritay street food", "Fritay, pate kode, marinad, akra, pen patat, banan peze", "Fritay vendors on every corner"),
    ]),
    ("Trinidadian", [
        ("breakfast (breakfast)", "6-8 AM", "Doubles from vendor", "Doubles, sada roti, choka, buljol, cocoa tea, bake", "Doubles vendor line before work is daily ritual"),
        ("lunch (lunch)", "12-2 PM", "Pelau or curry roti", "Pelau, curry chicken, roti, rice, callaloo, stew chicken", "Roti shops are institution; dhalpuri or buss up shut"),
        ("dinner (dinner)", "6-8 PM", "Home-cooked meal", "Stew, curry, dhal, provisions, bake and shark, callaloo", "Family dinner; provisions (ground food) included"),
        ("liming (snack)", "evening", "Liming food and drinks", "Bake and shark, corn soup, pholourie, doubles, rum punch", "Liming culture: gathering with food and drinks"),
    ]),
    ("Cajun/Creole", [
        ("breakfast (breakfast)", "7-9 AM", "Beignets and café au lait", "Beignets, café au lait, couche-couche, grillades and grits", "Beignets at Café du Monde is iconic tradition"),
        ("dinner (lunch)", "11:30-1:30 PM", "Gumbo or jambalaya", "Gumbo, jambalaya, étouffée, po-boy, red beans and rice", "Monday red beans and rice (wash day tradition)"),
        ("supper (dinner)", "6-8 PM", "Crawfish boil or court-bouillon", "Crawfish boil, court-bouillon, boudin, dirty rice, gumbo", "Crawfish boil is communal outdoor event"),
        ("lagniappe (snack)", "any time", "Boudin and pralines", "Boudin balls, pralines, snowball, beignets, café au lait", "Boudin from gas stations; pralines everywhere"),
    ]),
    ("Southern US", [
        ("breakfast (breakfast)", "7-9 AM", "Grits and biscuits", "Grits, biscuits and gravy, country ham, eggs, sweet tea", "Biscuits from scratch; buttermilk is key"),
        ("dinner (lunch)", "11:30-2 PM", "Meat and three sides", "BBQ, fried chicken, cornbread, collard greens, mac and cheese", "Meat-and-three: pick a protein and three sides"),
        ("supper (dinner)", "6-8 PM", "Comfort food", "Chicken fried steak, catfish, black-eyed peas, cornbread", "Sweet tea with every meal; front porch dining"),
        ("snack (snack)", "any time", "Porch food", "Pimento cheese, boiled peanuts, banana pudding, fried pies", "Front porch socializing with snacks"),
    ]),
    ("Tex-Mex", [
        ("desayuno (breakfast)", "7-9 AM", "Breakfast tacos", "Breakfast tacos, migas, huevos rancheros, chorizo, coffee", "Breakfast taco is religion in Texas"),
        ("almuerzo (lunch)", "11:30-2 PM", "Combo plate", "Enchiladas, tamales, chile con queso, fajitas, rice, beans", "Combo plate: enchiladas, rice, beans is standard"),
        ("cena (dinner)", "6-8 PM", "Fajitas or nachos", "Fajitas, nachos, chile con carne, puffy tacos, queso, brisket", "Queso (cheese dip) starts every meal"),
        ("snack (snack)", "any time", "Chips and queso", "Chips and salsa, elote, churros, raspas, margaritas", "Chips and salsa on every table automatically"),
    ]),
    ("Hawaiian", [
        ("breakfast (breakfast)", "7-9 AM", "Loco moco or spam musubi", "Loco moco, spam musubi, açaí bowl, malasadas, Kona coffee", "Spam musubi is quintessential Hawaiian breakfast"),
        ("lunch (lunch)", "11:30-1:30 PM", "Plate lunch", "Plate lunch, poke, laulau, kalbi, mac salad, two scoops rice", "Plate lunch: rice, mac salad, entrée"),
        ("dinner (dinner)", "6-8 PM", "Mixed plate or lūʻau", "Kalua pig, poi, lomi salmon, poke, haupia, lau lau", "Lūʻau feasts for celebrations; poi is staple"),
        ("snack (snack)", "any time", "Shave ice and musubi", "Shave ice, malasadas, musubi, manapua, li hing mui candy", "Shave ice with azuki beans and condensed milk"),
    ]),
    ("Native American", [
        ("morning meal (breakfast)", "dawn", "Seasonal breakfast", "Fry bread, blue corn mush, wild rice, berries, cedar tea", "Meals tied to seasonal availability and ceremony"),
        ("midday meal (lunch)", "12-2 PM", "Stew or three sisters", "Three sisters soup, bison stew, fry bread, wild rice, corn", "Three sisters (corn, beans, squash) foundation"),
        ("evening meal (dinner)", "sunset", "Community meal", "Venison, salmon, corn, beans, squash, wild greens, succotash", "Communal feasts tied to seasonal ceremonies"),
        ("trail food (snack)", "any time", "Portable provisions", "Pemmican, dried berries, nuts, parched corn, maple candy", "Pemmican: original energy food for travel"),
    ]),
    ("Brazilian", [
        ("café da manhã (breakfast)", "7-9 AM", "Pão de queijo and café", "Pão de queijo, café com leite, tapioca, frutas, bolo, cuscuz", "Pão de queijo (cheese bread) is daily staple"),
        ("almoço (lunch)", "12-2 PM", "PF (prato feito)", "Arroz, feijão, farofa, salad, meat, PF, feijoada, virado", "Arroz e feijão (rice and beans) at every lunch"),
        ("jantar (dinner)", "7-9 PM", "Churrasco or lighter fare", "Churrasco, pizza, sopa, pastel, açaí, moqueca, acarajé", "Weekend churrasco (rodízio) is social event"),
        ("lanche (snack)", "3-5 PM", "Padaria snack", "Coxinha, pastel, pão de queijo, suco, açaí, brigadeiro", "Padaria (bakery) culture; coxinha everywhere"),
    ]),

    # === OCEANIA ===
    ("Australian", [
        ("brekkie (breakfast)", "7-9 AM", "Smashed avo and flat white", "Smashed avocado toast, vegemite toast, flat white, bacon, eggs", "Café culture; flat white coffee is Australian icon"),
        ("lunch (lunch)", "12-2 PM", "Meat pie or sanga", "Meat pie, sausage roll, fish and chips, barramundi, sanga", "Meat pie at servo or bakery; sausage sizzle at Bunnings"),
        ("tea (dinner)", "6-8 PM", "BBQ or multicultural", "BBQ, lamb chops, seafood, parma, Thai, Vietnamese, Lebanese", "Backyard barbie culture; multiculti dining"),
        ("arvo snack (snack)", "3 PM", "Tim Tams and flat white", "Tim Tam, lamington, flat white, ANZAC biscuit, fairy bread", "Tim Tam Slam technique; ANZAC biscuits sacred"),
    ]),
    ("Maori", [
        ("parakuihi (breakfast)", "7-9 AM", "Rewena bread or fry-up", "Rewena bread, porridge, eggs, fry-up, flat white, marmite", "Rewena bread from potato bug starter"),
        ("tina (lunch)", "12-2 PM", "Pie or boil-up", "Meat pie, fish and chips, boil-up, whitebait fritters, kumara", "Boil-up: pork bones, watercress, pūhā, kumara"),
        ("hapa (dinner)", "6-8 PM", "Hāngi or roast lamb", "Hāngi, roast lamb, pavlova, green-lipped mussels, kumara", "Hāngi: earth oven cooking for gatherings; sacred"),
        ("kai (snack)", "any time", "Kiwi snacks", "Mince pie, Afghan biscuit, hokey pokey ice cream, pineapple lumps", "Hokey pokey ice cream is NZ icon"),
    ]),
    ("Polynesian", [
        ("breakfast (breakfast)", "7-9 AM", "Tropical staples", "Breadfruit, coconut, taro, banana, cocoa, palusami", "Breadfruit and coconut from backyard trees"),
        ("lunch (lunch)", "12-2 PM", "Umu or oka", "Oka, taro, palusami, lu, sapasui, chop suey, luau", "Umu (earth oven) for communal cooking"),
        ("dinner (dinner)", "6-8 PM", "Communal feast", "Whole roast pig, oka, taro, breadfruit, coconut cream, lu", "Food sharing is duty; communal eating style"),
        ("snack (snack)", "any time", "Tropical fruits and koko", "Coconut, breadfruit chips, poi, tropical fruits, koko Samoa", "Koko Samoa (cocoa) is ritual drink"),
    ]),
    ("Fijian", [
        ("breakfast (breakfast)", "7-9 AM", "Roti or cassava", "Roti, cassava, dhal, coconut milk tea, eggs, curry", "Indo-Fijian and indigenous fusion breakfast"),
        ("lunch (lunch)", "12-2 PM", "Kokoda or curry", "Kokoda, lovo, dhal, rourou, fish curry, cassava, rice", "Kokoda (raw fish in coconut) is national dish"),
        ("dinner (dinner)", "6-8 PM", "Lovo feast or family curry", "Lovo, curry, cassava, taro, fish, rourou, palusami", "Lovo (earth oven) for celebrations and gatherings"),
        ("snack (snack)", "any time", "Tropical snacks", "Coconut, cassava chips, Indian snacks, tropical fruits, kava", "Indo-Fijian and iTaukei snacks blend together"),
    ]),
]


# ============================================================================
# INGREDIENT CATEGORY KEYWORDS (checked in order — first match wins)
# ============================================================================
INGREDIENT_CATEGORY_ORDER = [
    ("rice", ["rice", "basmati", "jasmine rice", "glutinous"]),
    ("noodles_pasta", ["noodle", "pasta", "spaghetti", "macaroni", "vermicelli", "soba", "udon", "ramen", "mee", "mien"]),
    ("fish_seafood", ["fish", "shrimp", "prawn", "squid", "crab", "lobster", "clam", "mussel", "oyster", "anchovy", "tuna", "salmon", "sardine", "mackerel", "cod", "seafood", "octopus", "scallop", "eel"]),
    ("meat", ["beef", "pork", "chicken", "lamb", "mutton", "goat", "veal", "duck", "turkey", "sausage", "bacon", "ham", "meat", "venison", "rabbit", "bison"]),
    ("egg", ["egg"]),
    ("dairy", ["milk", "butter", "cheese", "cream", "yogurt", "yoghurt", "ghee", "curd", "whey", "paneer", "quark"]),
    ("coconut", ["coconut"]),
    ("sugar_sweets", ["sugar", "honey", "jaggery", "molasses", "syrup", "chocolate", "cacao", "cocoa", "palm sugar"]),
    ("wheat_flour", ["flour", "wheat", "bread", "dough", "pastry"]),
    ("legumes", ["bean", "lentil", "peanut", "chickpea", "soybean", "tofu", "dal", "mung", "tempeh"]),
    ("fruit", ["banana", "mango", "apple", "orange", "lemon", "lime", "pineapple", "papaya", "grape", "berry", "melon", "date", "fig", "tamarind", "plantain", "peach", "pear", "plum", "cherry", "jackfruit", "durian"]),
    ("spices", ["chili", "ginger", "turmeric", "cumin", "coriander", "cinnamon", "saffron", "cardamom", "clove", "nutmeg", "lemongrass", "cymbopogon", "vanilla", "anise", "fennel", "oregano", "basil", "thyme", "rosemary", "mint", "parsley", "cilantro", "dill", "salt", "pepper"]),
    ("vegetables", ["onion", "garlic", "tomato", "potato", "carrot", "cabbage", "spinach", "eggplant", "cucumber", "lettuce", "celery", "broccoli", "cauliflower", "zucchini", "pumpkin", "squash", "mushroom", "shallot", "leek", "radish", "turnip", "beet", "corn", "taro", "yam", "cassava", "sweet potato", "watercress", "bamboo"]),
]


def categorize_ingredient(name):
    name_lower = name.lower()
    for category, keywords in INGREDIENT_CATEGORY_ORDER:
        for kw in keywords:
            if kw in name_lower:
                return category
    return "other"


# ============================================================================
# STEP 1a+1b: Fix slugs and regions
# ============================================================================
def fix_slugs_and_regions(conn):
    print("\n=== Step 1a: Backfilling slugs for all cultures ===")
    cursor = conn.cursor()

    # Backfill slugs
    rows = cursor.execute(
        "SELECT id, name FROM cultures WHERE slug IS NULL OR slug = ''"
    ).fetchall()
    slug_count = 0
    for row in rows:
        cid, name = row["id"], row["name"]
        slug = slugify(name)
        # Handle duplicates by appending id
        existing = cursor.execute("SELECT id FROM cultures WHERE slug = ? AND id != ?", (slug, cid)).fetchone()
        if existing:
            slug = f"{slug}-{cid}"
        cursor.execute("UPDATE cultures SET slug = ? WHERE id = ?", (slug, cid))
        slug_count += 1
    conn.commit()
    print(f"  Backfilled {slug_count} slugs")

    print("\n=== Step 1b: Fixing regions for 'Other' cultures ===")
    fixed = 0
    for name, region in REGION_FIXES.items():
        cursor.execute(
            "UPDATE cultures SET region = ? WHERE name = ? AND region = 'Other'",
            (region, name),
        )
        fixed += cursor.rowcount
    conn.commit()
    print(f"  Fixed {fixed} culture regions")


# ============================================================================
# STEP 1c: Create missing cultures
# ============================================================================
def create_missing_cultures(conn):
    print("\n=== Step 1c: Creating missing cultures ===")
    cursor = conn.cursor()
    created = 0
    for name, culture_type, region, countries in NEW_CULTURES:
        slug = slugify(name)
        cursor.execute(
            """INSERT OR IGNORE INTO cultures (name, slug, culture_type, region, modern_countries, is_living_culture)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (name, slug, culture_type, region, countries),
        )
        if cursor.rowcount:
            created += 1
            print(f"  Created: {name} ({region})")
    conn.commit()
    print(f"  Created {created} new cultures")


# ============================================================================
# STEP 2: Insert meal patterns
# ============================================================================
def populate_meal_patterns(conn):
    print("\n=== Step 2: Populating meal patterns for 72 cultures ===")
    cursor = conn.cursor()

    # Ensure table exists with the actual schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS culture_meal_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            culture_id INTEGER REFERENCES cultures(id),
            meal_name TEXT NOT NULL,
            typical_time TEXT,
            description TEXT,
            typical_foods TEXT,
            social_context TEXT,
            UNIQUE(culture_id, meal_name)
        )
    """)

    # Build culture name → id mapping
    culture_ids = {}
    for row in cursor.execute("SELECT id, name FROM cultures").fetchall():
        culture_ids[row["name"]] = row["id"]

    patterns_added = 0
    cultures_done = 0

    for adj_name, meals in WORLD_MEAL_PATTERNS:
        db_name = CULTURE_DB_MAP.get(adj_name)
        if not db_name:
            print(f"  WARNING: No DB mapping for '{adj_name}'")
            continue
        culture_id = culture_ids.get(db_name)
        if not culture_id:
            print(f"  WARNING: Culture '{db_name}' not found in DB")
            continue

        for meal_name, typical_time, description, typical_foods, social_context in meals:
            cursor.execute(
                """INSERT OR IGNORE INTO culture_meal_patterns
                   (culture_id, meal_name, typical_time, description, typical_foods, social_context)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (culture_id, meal_name, typical_time, description, typical_foods, social_context),
            )
            patterns_added += cursor.rowcount
        cultures_done += 1

    conn.commit()
    print(f"  Added {patterns_added} meal patterns across {cultures_done} cultures")


# ============================================================================
# STEP 3: Link foods to meal types with culture context
# ============================================================================
def link_foods_to_meal_types(conn):
    print("\n=== Step 3: Linking foods to meal types with culture context ===")
    cursor = conn.cursor()

    # Meal type IDs: index 0=breakfast(1), 1=lunch(2), 2=dinner(3), 3=snack(4)
    MEAL_TYPE_IDS = [1, 2, 3, 4]

    # Map from tag values to meal_type_id
    TAG_TO_MEAL_ID = {
        "breakfast": 1, "brunch": 1,
        "lunch": 2,
        "dinner": 3,
        "snack": 4, "street food": 4, "appetizer": 4,
    }

    # Build culture name → id mapping
    culture_ids = {}
    for row in cursor.execute("SELECT id, name FROM cultures").fetchall():
        culture_ids[row["name"]] = row["id"]

    # Preload food meal_type tags
    food_meal_tags = {}
    for row in cursor.execute("SELECT food_id, tag_value FROM food_tags WHERE tag_category = 'meal_type'").fetchall():
        food_meal_tags.setdefault(row["food_id"], set()).add(row["tag_value"].lower())

    # Preload food names for pattern matching
    food_names = {}
    for row in cursor.execute("SELECT id, name FROM foods").fetchall():
        food_names[row["id"]] = row["name"].lower()

    total_linked = 0

    for adj_name, meals in WORLD_MEAL_PATTERNS:
        db_name = CULTURE_DB_MAP.get(adj_name)
        if not db_name:
            continue
        culture_id = culture_ids.get(db_name)
        if not culture_id:
            continue

        # Collect food IDs for this culture
        food_ids = set()

        # From food_culture_origins
        for row in cursor.execute(
            "SELECT food_id FROM food_culture_origins WHERE culture_id = ?", (culture_id,)
        ).fetchall():
            food_ids.add(row["food_id"])

        # From cuisine tags
        for tag in CULTURE_TO_CUISINE_TAGS.get(db_name, []):
            for row in cursor.execute(
                "SELECT food_id FROM food_tags WHERE tag_category = 'cuisine' AND tag_value = ?",
                (tag,),
            ).fetchall():
                food_ids.add(row["food_id"])

        if not food_ids:
            continue

        # Build typical_foods lists per meal index for pattern matching
        typical_by_idx = {}
        for idx, (meal_name, time, desc, foods_text, context) in enumerate(meals):
            typical_by_idx[idx] = [f.strip().lower() for f in foods_text.split(",")]

        inserts = []
        for food_id in food_ids:
            assigned_meal_ids = set()

            # From existing meal_type tags
            for tag in food_meal_tags.get(food_id, []):
                mid = TAG_TO_MEAL_ID.get(tag)
                if mid:
                    assigned_meal_ids.add(mid)

            # Pattern match against typical_foods if no tags found
            if not assigned_meal_ids:
                fname = food_names.get(food_id, "")
                for idx, food_list in typical_by_idx.items():
                    for typical_food in food_list:
                        typical_food = typical_food.strip()
                        if len(typical_food) > 2 and (typical_food in fname or fname in typical_food):
                            assigned_meal_ids.add(MEAL_TYPE_IDS[idx])
                            break

            # Default: lunch and dinner
            if not assigned_meal_ids:
                assigned_meal_ids = {2, 3}

            for mid in assigned_meal_ids:
                inserts.append((food_id, mid, culture_id))

        if inserts:
            cursor.executemany(
                "INSERT OR IGNORE INTO food_meal_types (food_id, meal_type_id, culture_id) VALUES (?, ?, ?)",
                inserts,
            )
            total_linked += len(inserts)
            print(f"  {adj_name}: {len(food_ids)} foods, {len(inserts)} meal links")

    conn.commit()
    print(f"  Total: {total_linked} culture-specific meal links created")


# ============================================================================
# STEP 4: Create ingredient_categories table
# ============================================================================
def create_ingredient_categories(conn):
    print("\n=== Step 4: Creating ingredient categories ===")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredient_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Gather all unique ingredient names
    ingredients = set()
    for row in cursor.execute("SELECT DISTINCT ingredient_name FROM food_ingredients_wiki").fetchall():
        ingredients.add(row["ingredient_name"])
    for row in cursor.execute(
        "SELECT DISTINCT tag_value FROM food_tags WHERE tag_category = 'ingredient'"
    ).fetchall():
        ingredients.add(row["tag_value"])

    categorized = 0
    category_counts = {}
    for ingredient in ingredients:
        cat = categorize_ingredient(ingredient)
        cursor.execute(
            "INSERT OR IGNORE INTO ingredient_categories (ingredient_name, category) VALUES (?, ?)",
            (ingredient, cat),
        )
        if cursor.rowcount:
            categorized += 1
            category_counts[cat] = category_counts.get(cat, 0) + 1

    conn.commit()
    print(f"  Categorized {categorized} ingredients:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}")


# ============================================================================
# STEP 5: Create indexes
# ============================================================================
def create_indexes(conn):
    print("\n=== Step 5: Creating indexes ===")
    cursor = conn.cursor()
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_fmt_culture ON food_meal_types(culture_id)",
        "CREATE INDEX IF NOT EXISTS idx_fmt_meal_culture ON food_meal_types(meal_type_id, culture_id)",
        "CREATE INDEX IF NOT EXISTS idx_ic_ingredient ON ingredient_categories(ingredient_name)",
        "CREATE INDEX IF NOT EXISTS idx_fco_culture ON food_culture_origins(culture_id)",
        "CREATE INDEX IF NOT EXISTS idx_ft_cuisine ON food_tags(tag_category, tag_value) WHERE tag_category = 'cuisine'",
    ]
    for idx_sql in indexes:
        cursor.execute(idx_sql)
        print(f"  {idx_sql.split('idx_')[1].split(' ')[0]}")
    conn.commit()


# ============================================================================
# STEP 6: Report stats
# ============================================================================
def report_stats(conn):
    cursor = conn.cursor()
    print("\n" + "=" * 70)
    print("WORLD MEAL ENRICHMENT COMPLETE")
    print("=" * 70)

    stats = [
        ("Cultures with slugs", "SELECT COUNT(*) FROM cultures WHERE slug IS NOT NULL AND slug != ''"),
        ("Cultures with proper regions", "SELECT COUNT(*) FROM cultures WHERE region != 'Other'"),
        ("Meal patterns total", "SELECT COUNT(*) FROM culture_meal_patterns"),
        ("Cultures with meal patterns", "SELECT COUNT(DISTINCT culture_id) FROM culture_meal_patterns"),
        ("Food-meal-type links (with culture)", "SELECT COUNT(*) FROM food_meal_types WHERE culture_id IS NOT NULL"),
        ("Distinct cultures in food_meal_types", "SELECT COUNT(DISTINCT culture_id) FROM food_meal_types WHERE culture_id IS NOT NULL"),
        ("Ingredient categories", "SELECT COUNT(*) FROM ingredient_categories"),
    ]

    for label, sql in stats:
        val = cursor.execute(sql).fetchone()[0]
        print(f"  {label}: {val:,}")

    # Region breakdown
    print("\n  Meal patterns by region:")
    rows = cursor.execute("""
        SELECT c.region, COUNT(DISTINCT c.id) as cultures, COUNT(cmp.id) as patterns
        FROM cultures c
        JOIN culture_meal_patterns cmp ON cmp.culture_id = c.id
        GROUP BY c.region
        ORDER BY patterns DESC
    """).fetchall()
    for row in rows:
        print(f"    {row['region'] or 'Unknown':25s}: {row['cultures']:3d} cultures, {row['patterns']:3d} patterns")


# ============================================================================
# MAIN
# ============================================================================
def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        fix_slugs_and_regions(conn)
        create_missing_cultures(conn)
        populate_meal_patterns(conn)
        link_foods_to_meal_types(conn)
        create_ingredient_categories(conn)
        create_indexes(conn)
        report_stats(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
