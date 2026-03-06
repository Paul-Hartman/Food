/**
 * The Apothecary: An Encyclopedia of Food Ingredients
 *
 * Traditional herbalism meets modern nutrition science.
 * Every ingredient - from ancient herbs to modern synthetics -
 * explained with history, function, and wisdom.
 *
 * "In nature's pharmacy, every plant is a teacher."
 */

export type IngredientOrigin = 'plant' | 'animal' | 'mineral' | 'fungal' | 'bacterial' | 'synthetic';
export type MedicinalTradition = 'ayurveda' | 'tcm' | 'western' | 'native_american' | 'middle_eastern' | 'african' | 'modern';

export interface ApothecaryIngredient {
  // Identity
  name: string;
  commonNames: string[];
  scientificName?: string; // e.g., "Curcuma longa" for turmeric
  origin: IngredientOrigin;

  // Apothecary Classification
  category: string; // e.g., "Spice", "Herb", "Root", "Preservative"
  jarLabel: string; // What you'd see on an apothecary jar
  color?: string; // Visual appearance
  texture?: string; // Powder, crystal, oil, dried leaf, etc.

  // Historical Wisdom
  traditionalUses: Array<{
    tradition: MedicinalTradition;
    use: string;
    preparation: string; // How it was prepared (tea, poultice, tincture, etc.)
    historicalContext?: string;
  }>;

  // Modern Science
  activeCompounds: Array<{
    name: string;
    function: string;
    mechanism: string; // How it works in the body
    evidence: 'well-established' | 'emerging' | 'traditional' | 'theoretical';
  }>;

  // In the Body
  whatItDoes: string; // Plain English explanation
  bodyTargets: string[]; // Which organs/systems it affects
  absorptionNotes?: string; // How the body processes it

  // Food Applications
  usedIn: string[]; // What foods contain it
  purpose: string[]; // Why it's added (flavor, preservation, color, etc.)
  processNotes?: string; // How it's made or extracted

  // Synthetic vs Natural
  isSynthetic: boolean;
  syntheticEquivalent?: string; // If natural, what's the synthetic version?
  naturalEquivalent?: string; // If synthetic, what's the natural version?
  synthesisMethod?: string; // How synthetic version is made

  // Safety & Wisdom
  safeDosage?: string;
  warnings?: string[];
  interactions?: string[];
  pregnancyWarning?: string;

  // Apothecary Lore
  folklore?: string;
  quotes?: string[]; // Historical or traditional sayings
  curiosities?: string[]; // Interesting facts
}

/**
 * THE APOTHECARY COLLECTION
 * Organized like jars on shelves
 */
export const APOTHECARY: ApothecaryIngredient[] = [
  // ═══════════════════════════════════════════════════════════
  // SHELF 1: GOLDEN SPICES (Anti-inflammatory & Antioxidant)
  // ═══════════════════════════════════════════════════════════

  {
    name: 'Turmeric',
    commonNames: ['Haldi', 'Indian Saffron', 'Golden Root'],
    scientificName: 'Curcuma longa',
    origin: 'plant',
    category: 'Spice (Rhizome)',
    jarLabel: 'Curcuma ⚱ Root of Gold',
    color: 'Bright golden yellow',
    texture: 'Fine powder or dried root',

    traditionalUses: [
      {
        tradition: 'ayurveda',
        use: 'Anti-inflammatory, wound healing, digestive aid',
        preparation: 'Golden milk (turmeric + milk + black pepper), paste for wounds',
        historicalContext:
          'Used in Ayurveda for 4,000+ years. Considered sacred, used in wedding ceremonies.',
      },
      {
        tradition: 'tcm',
        use: 'Moves blood, reduces pain, especially shoulder pain',
        preparation: 'Decoction (boiled tea)',
        historicalContext: 'Called "Jiang Huang" - used since Tang Dynasty (618 AD)',
      },
      {
        tradition: 'western',
        use: 'Modern research: arthritis, depression, cancer prevention',
        preparation: 'Supplements, curry powder',
        historicalContext: 'Western medicine adopted after 1970s research boom',
      },
    ],

    activeCompounds: [
      {
        name: 'Curcumin',
        function: 'Powerful anti-inflammatory and antioxidant',
        mechanism:
          'Inhibits NF-κB (inflammation pathway), scavenges free radicals, modulates enzymes',
        evidence: 'well-established',
      },
      {
        name: 'Turmerone',
        function: 'Neuroprotective, may enhance brain repair',
        mechanism: 'Increases neural stem cell growth',
        evidence: 'emerging',
      },
    ],

    whatItDoes:
      'Turmeric is like a fire extinguisher for inflammation in your body. It cools down swollen joints, protects your brain, and helps your liver detoxify. The golden color comes from curcumin, which fights free radicals that damage cells.',

    bodyTargets: [
      'Joints (anti-inflammatory)',
      'Brain (neuroprotective)',
      'Liver (detoxification)',
      'Digestive system (aids bile production)',
      'Cardiovascular system',
    ],

    absorptionNotes:
      'Poor bioavailability! Only 1% absorbed alone. Needs fat (lipophilic) and black pepper (piperine blocks breakdown) to absorb properly.',

    usedIn: ['Curry powder', 'Golden milk', 'Mustard (coloring)', 'Supplements'],
    purpose: ['Flavor (earthy, slightly bitter)', 'Color (golden yellow)', 'Preservation'],

    isSynthetic: false,
    syntheticEquivalent: 'Curcumin extract (99% pure) - not same as whole turmeric',

    safeDosage: '1-3g powder daily (1 teaspoon = ~3g)',
    warnings: [
      'High doses may upset stomach',
      'Blood thinner - avoid before surgery',
      'May interfere with chemotherapy',
    ],
    interactions: ['Blood thinners (warfarin)', 'Diabetes medications', 'Iron supplements'],

    folklore:
      'Hindu brides are rubbed with turmeric paste before weddings - it represents fertility, prosperity, and warding off evil spirits.',
    quotes: [
      '"Let food be thy medicine and turmeric be thy spice." - Modern adaptation',
      '"Haldi ki goli, doctor ki kya jaroorat?" (Turmeric pills, who needs a doctor?) - Indian saying',
    ],
    curiosities: [
      'Used as a natural dye for Buddhist monks\' robes',
      'Ancient Romans used it as a cheap saffron substitute',
      'Can stain your hands yellow for days!',
    ],
  },

  {
    name: 'Black Pepper',
    commonNames: ['Peppercorn', 'King of Spices'],
    scientificName: 'Piper nigrum',
    origin: 'plant',
    category: 'Spice (Fruit)',
    jarLabel: 'Piper Nigrum ⚫ Black Gold',
    color: 'Black/dark brown',
    texture: 'Small hard berries, ground to powder',

    traditionalUses: [
      {
        tradition: 'ayurveda',
        use: 'Digestive fire (Agni) enhancer, respiratory aid, circulation booster',
        preparation: 'Trikatu (three spices: black pepper, long pepper, ginger)',
        historicalContext: 'Called "Maricha" after the sun - warming and energizing',
      },
      {
        tradition: 'western',
        use: 'Most valuable spice in history - worth its weight in gold',
        preparation: 'Ground fresh for maximum piperine',
        historicalContext:
          'Drove spice trade, discovery of Americas. Literally used as currency in medieval Europe.',
      },
    ],

    activeCompounds: [
      {
        name: 'Piperine',
        function: 'Bioavailability enhancer, thermogenic',
        mechanism:
          'Inhibits liver enzymes (CYP3A4, glucuronidation), increases nutrient absorption',
        evidence: 'well-established',
      },
    ],

    whatItDoes:
      'Black pepper is the key that unlocks other nutrients. Piperine blocks the liver from breaking down compounds too quickly, allowing 20x more curcumin (from turmeric) to enter your bloodstream. It also speeds up metabolism and aids digestion.',

    bodyTargets: [
      'Liver (enzyme inhibition)',
      'Digestive system (stimulates enzymes)',
      'Circulatory system (increases blood flow)',
    ],

    absorptionNotes: 'Highly bioavailable. Piperine itself absorbs well.',

    usedIn: ['Nearly all savory foods', 'Supplements (as BioPerine®)', 'Traditional formulas'],
    purpose: ['Flavor (pungent, spicy)', 'Nutrient absorption', 'Preservation'],

    isSynthetic: false,
    syntheticEquivalent: 'Piperine extract (BioPerine® - 95% piperine)',

    safeDosage: '5-20mg piperine daily',
    warnings: ['May increase absorption of medications (ask doctor)'],
    interactions: [
      'Enhances absorption of many drugs and supplements',
      'Turmeric (synergistic)',
      'CoQ10, Beta-carotene',
    ],

    folklore:
      'In ancient Rome, Alaric the Goth demanded 3,000 pounds of pepper as ransom for sparing the city. Pepper was literally treasure.',
    quotes: [
      '"Pepper is small in quantity and great in virtue." - Pliny the Elder, 77 AD',
    ],
    curiosities: [
      'Black, white, and green peppercorns are same plant, different processing',
      'Medieval Europeans believed pepper could cure plague',
      'Sneeze reflex triggered by piperine irritating nose nerves',
    ],
  },

  {
    name: 'Ginger',
    commonNames: ['Adrak', 'Ginger Root'],
    scientificName: 'Zingiber officinale',
    origin: 'plant',
    category: 'Spice (Rhizome)',
    jarLabel: 'Zingiber ⚱ Warming Root',
    color: 'Pale yellow interior, brown skin',
    texture: 'Fibrous root, becomes powder',

    traditionalUses: [
      {
        tradition: 'ayurveda',
        use: 'Universal medicine - digestive, anti-nausea, anti-inflammatory',
        preparation: 'Fresh ginger tea, dried powder in formulas',
        historicalContext: 'Called "Vishwabhesaj" (universal medicine) in Sanskrit',
      },
      {
        tradition: 'tcm',
        use: 'Warms the middle burner, expels cold, stops vomiting',
        preparation: 'Decoction with dates',
        historicalContext: 'Mentioned in writings of Confucius (500 BC)',
      },
    ],

    activeCompounds: [
      {
        name: 'Gingerol',
        function: 'Anti-inflammatory, anti-nausea, antioxidant',
        mechanism: 'Inhibits COX-2 and 5-LOX (inflammation enzymes), affects serotonin receptors',
        evidence: 'well-established',
      },
      {
        name: 'Shogaol (from dried ginger)',
        function: 'More potent anti-inflammatory than gingerol',
        mechanism: 'Forms when ginger is dried/heated - stronger COX-2 inhibition',
        evidence: 'well-established',
      },
    ],

    whatItDoes:
      'Ginger is your stomach\'s best friend and inflammation\'s worst enemy. It stops nausea (even from chemotherapy), reduces muscle pain, and warms your body from the inside. The spicy bite you feel is gingerol working.',

    bodyTargets: [
      'Digestive system (anti-nausea)',
      'Muscles (reduces soreness)',
      'Joints (anti-inflammatory)',
      'Immune system (antimicrobial)',
    ],

    absorptionNotes: 'Well absorbed. Fresh vs dried ginger have different compound profiles.',

    usedIn: [
      'Ginger tea',
      'Curry',
      'Ginger ale',
      'Sushi (pickled ginger)',
      'Anti-nausea supplements',
    ],
    purpose: ['Flavor (spicy, warming)', 'Medicinal', 'Digestive aid'],

    isSynthetic: false,

    safeDosage: '1-4g daily',
    warnings: ['Blood thinner at high doses', 'May worsen acid reflux in some people'],
    interactions: ['Blood thinners', 'Diabetes medications'],

    folklore:
      'Ancient Greeks baked ginger into bread - origin of gingerbread. Believed to aid digestion after heavy meals.',
    curiosities: [
      'Ginger beer was originally medicinal tonic',
      'Sailors used ginger for seasickness since 400 BC',
      'Fresh ginger can be planted and grown in a pot',
    ],
  },

  // ═══════════════════════════════════════════════════════════
  // SHELF 2: VITAMINS (Essential Nutrients)
  // ═══════════════════════════════════════════════════════════

  {
    name: 'Ascorbic Acid (Vitamin C)',
    commonNames: ['Vitamin C', 'L-Ascorbate'],
    scientificName: 'L-Ascorbic acid',
    origin: 'plant',
    category: 'Vitamin (Water-soluble)',
    jarLabel: 'Acidum Ascorbicum ◇ Scurvy\'s Cure',
    color: 'White crystalline powder',
    texture: 'Fine crystals, highly water-soluble',

    traditionalUses: [
      {
        tradition: 'western',
        use: 'Prevents and cures scurvy',
        preparation: 'Citrus fruits, rose hips tea',
        historicalContext:
          'British sailors ate limes to prevent scurvy (1700s) - nicknamed "limeys"',
      },
    ],

    activeCompounds: [
      {
        name: 'Ascorbic Acid',
        function: 'Antioxidant, collagen synthesis, immune support',
        mechanism:
          'Electron donor (reduces free radicals), cofactor for collagen enzymes, enhances iron absorption',
        evidence: 'well-established',
      },
    ],

    whatItDoes:
      'Vitamin C is the builder and protector. It makes collagen (glue holding your body together), fights infections, and turns plant iron into a form your body can absorb. Without it, your gums bleed, wounds don\'t heal, and you develop scurvy.',

    bodyTargets: [
      'Skin (collagen production)',
      'Immune system (white blood cells)',
      'Blood vessels (strengthens walls)',
      'Bones and teeth',
      'Iron absorption (intestines)',
    ],

    absorptionNotes:
      'Water-soluble, not stored. Excess urinated out. Best absorbed in divided doses throughout day.',

    usedIn: [
      'Citrus fruits (natural)',
      'Supplements (synthetic)',
      'Fortified foods',
      'Preservatives (E300)',
    ],
    purpose: ['Antioxidant (preservative)', 'Fortification', 'Health supplement'],
    processNotes: 'Synthetic vitamin C made from glucose via fermentation (indistinguishable from natural)',

    isSynthetic: true,
    naturalEquivalent: 'Citrus fruits, rose hips, acerola cherry',
    synthesisMethod:
      'Reichstein process: Glucose → Sorbitol → Sorbose → Ascorbic acid (via fermentation)',

    safeDosage: 'RDA: 75-90mg. Therapeutic: 500-2000mg. Upper limit: 2000mg',
    warnings: [
      'High doses (>2g) may cause diarrhea',
      'Kidney stones in susceptible people',
      'False glucose readings (diabetics)',
    ],
    interactions: ['Iron (enhances absorption)', 'Aluminum (increases absorption - avoid)'],

    folklore:
      'James Lind discovered citrus cured scurvy in 1747 - first controlled clinical trial in history.',
    quotes: [
      '"Nature never deceives us; it is always we who deceive ourselves." - Rousseau (on natural vs synthetic)',
    ],
    curiosities: [
      'Humans, guinea pigs, and fruit bats can\'t make vitamin C - must eat it',
      'Most animals synthesize it in liver',
      'Synthetic and natural ascorbic acid are chemically identical',
    ],
  },

  // ═══════════════════════════════════════════════════════════
  // SHELF 3: PRESERVATIVES (Modern Apothecary)
  // ═══════════════════════════════════════════════════════════

  {
    name: 'Sodium Benzoate',
    commonNames: ['E211', 'Benzoate of Soda'],
    scientificName: 'C₇H₅NaO₂',
    origin: 'synthetic',
    category: 'Preservative',
    jarLabel: 'Natrii Benzoas ⚗ The Preserver',
    color: 'White powder',
    texture: 'Crystalline, water-soluble',

    traditionalUses: [
      {
        tradition: 'modern',
        use: 'Food preservation - prevents mold, yeast, bacteria',
        preparation: 'Dissolved in acidic foods/drinks',
        historicalContext: 'FDA approved 1908 - one of first chemical preservatives',
      },
    ],

    activeCompounds: [
      {
        name: 'Benzoic Acid (active form)',
        function: 'Antimicrobial',
        mechanism:
          'Disrupts pH gradient across microbial cell membranes, inhibits enzymes',
        evidence: 'well-established',
      },
    ],

    whatItDoes:
      'Sodium benzoate is a molecular guard that keeps your food from rotting. In acidic environments (like soda), it converts to benzoic acid and kills microbes by disrupting their cellular energy. Your body breaks it down quickly into harmless compounds.',

    bodyTargets: [
      'Liver (metabolism)',
      'Kidneys (excretion)',
      'Gut microbes (antimicrobial effect)',
    ],

    absorptionNotes:
      'Rapidly absorbed, metabolized in liver via glycine conjugation to hippuric acid, excreted in urine within hours.',

    usedIn: [
      'Soft drinks (especially acidic ones)',
      'Pickles',
      'Salad dressings',
      'Pharmaceuticals',
    ],
    purpose: ['Preservation (prevents spoilage)', 'Safety (prevents botulism in acidic foods)'],
    processNotes: 'Synthesized from benzoic acid + sodium hydroxide',

    isSynthetic: true,
    naturalEquivalent: 'Benzoic acid occurs naturally in cranberries, plums, cinnamon',
    synthesisMethod: 'Benzoic acid (from toluene oxidation) + NaOH → Sodium benzoate',

    safeDosage: 'ADI: 0-5 mg/kg body weight. Typical soda: 100-200mg per can',
    warnings: [
      'Reacts with vitamin C to form benzene (carcinogen) - modern formulations minimize this',
      'May trigger allergic reactions in sensitive individuals',
      'ADHD concerns in children (controversial, limited evidence)',
    ],
    interactions: ['Vitamin C (may form benzene in acidic drinks)'],

    folklore:
      'Named after gum benzoin resin (from Styrax trees), historically used as incense and medicine.',
    curiosities: [
      'Your body naturally produces benzoic acid from foods',
      'Used in fireworks as fuel',
      'Cranberries use benzoic acid to prevent rot naturally',
      'Debate: "Chemical preservative" sounds scary, but prevents food poisoning',
    ],
  },

  {
    name: 'Citric Acid',
    commonNames: ['E330', 'Sour Salt'],
    scientificName: 'C₆H₈O₇',
    origin: 'bacterial',
    category: 'Acid/Preservative',
    jarLabel: 'Acidum Citricum 🍋 Nature\'s Tang',
    color: 'White crystalline',
    texture: 'Granular or powder',

    traditionalUses: [
      {
        tradition: 'western',
        use: 'Natural from citrus, now mass-produced via fermentation',
        preparation: 'Extracted from lemon juice historically',
        historicalContext: 'First isolated from lemon juice in 1784 by Carl Wilhelm Scheele',
      },
    ],

    activeCompounds: [
      {
        name: 'Citric Acid',
        function: 'Chelator, acidulant, flavor enhancer, preservative',
        mechanism:
          'Binds metals (chelation), lowers pH (prevents bacterial growth), participates in Krebs cycle',
        evidence: 'well-established',
      },
    ],

    whatItDoes:
      'Citric acid is nature\'s multitool. It gives foods that tangy taste, prevents spoilage by making the environment too acidic for bacteria, and even powers your cells\' energy production (Krebs cycle). It also grabs onto metals, helping your body absorb minerals better.',

    bodyTargets: [
      'Cells (Krebs cycle - energy production)',
      'Kidneys (prevents kidney stones by chelating calcium)',
      'Blood (buffers pH)',
    ],

    absorptionNotes:
      'Readily absorbed, metabolized into CO₂ and water, or used in cellular respiration.',

    usedIn: [
      'Sodas',
      'Candy (sour flavor)',
      'Preserves',
      'Cleaning products',
      'Bath bombs (fizz)',
    ],
    purpose: [
      'Flavor (sour/tart)',
      'Preservation (acidic environment)',
      'Antioxidant (prevents browning)',
    ],
    processNotes:
      'Modern production: Aspergillus niger (black mold) ferments sugar into citric acid in huge tanks',

    isSynthetic: false,
    naturalEquivalent: 'Lemons (6% citric acid), limes, other citrus',
    synthesisMethod:
      'Industrial fermentation: Sugar + Aspergillus niger → Citric acid (99% of world supply)',

    safeDosage: 'No upper limit - GRAS (Generally Recognized As Safe)',
    warnings: [
      'Tooth enamel erosion at high concentrations',
      'Rare allergic reactions',
      'Mold sensitivity (produced by fungus)',
    ],

    folklore:
      'Before 1893, citric acid came from Italian lemons. WWI cut supply, forcing invention of fermentation method.',
    curiosities: [
      'Same molecule whether from lemon or factory tank',
      'Essential for every cell in your body (Krebs cycle)',
      'Used in photography development',
      'Makes bath bombs fizz when mixed with baking soda',
    ],
  },

  // ═══════════════════════════════════════════════════════════
  // SHELF 4: MYSTERIOUS INGREDIENTS (E-Numbers Explained)
  // ═══════════════════════════════════════════════════════════

  {
    name: 'Carrageenan',
    commonNames: ['E407', 'Irish Moss Extract'],
    scientificName: 'Polysaccharide from Chondrus crispus',
    origin: 'plant',
    category: 'Thickener/Stabilizer',
    jarLabel: 'Carrageenan 🌊 Sea Vegetable Gum',
    color: 'Off-white to tan',
    texture: 'Powder (becomes gel in water)',

    traditionalUses: [
      {
        tradition: 'western',
        use: 'Irish folk remedy for coughs and colds',
        preparation: 'Boiled seaweed milk pudding',
        historicalContext:
          'Used in Ireland since 400 AD. Named after Carragheen near Waterford, Ireland.',
      },
    ],

    activeCompounds: [
      {
        name: 'Lambda, Kappa, Iota Carrageenan',
        function: 'Gel formation, thickening, stabilization',
        mechanism:
          'Long polysaccharide chains form helical structures, trap water molecules',
        evidence: 'well-established',
      },
    ],

    whatItDoes:
      'Carrageenan is seaweed\'s gift to food texture. These long sugar chains grab water and create smooth, creamy textures in ice cream, almond milk, and yogurt. Your body can\'t digest it - it passes through unchanged.',

    bodyTargets: ['Digestive tract (passes through undigested)'],

    absorptionNotes:
      'Not absorbed. Passes through digestive system intact. Not a source of calories.',

    usedIn: ['Almond milk', 'Ice cream', 'Chocolate milk', 'Deli meats', 'Toothpaste'],
    purpose: ['Thickening', 'Stabilization (prevents separation)', 'Improves mouthfeel'],
    processNotes: 'Extracted from red seaweed with hot water, filtered, dried',

    isSynthetic: false,
    synthesisMethod: 'Natural extraction from Eucheuma and Gigartina seaweeds',

    safeDosage: 'No upper limit (GRAS), typical intake: 100-300mg daily',
    warnings: [
      'Degraded carrageenan (poligeenan) linked to inflammation in animal studies - not used in food',
      'Food-grade carrageenan considered safe by FDA',
      'Some people report digestive sensitivity',
    ],

    folklore:
      'Irish immigrants brought carrageenan pudding recipe to America. Used traditionally as cough suppressant.',
    curiosities: [
      'Different types (kappa, iota, lambda) have different gelling strengths',
      'Used in chocolate milk to keep cocoa suspended',
      'Vegan alternative to gelatin',
      'Debate: Natural seaweed vs "processed chemical" perception',
    ],
  },
];

/**
 * Helper functions for the Apothecary
 */

export function searchApothecary(query: string): ApothecaryIngredient[] {
  const lowerQuery = query.toLowerCase();

  return APOTHECARY.filter(
    (ingredient) =>
      ingredient.name.toLowerCase().includes(lowerQuery) ||
      ingredient.commonNames.some((name) => name.toLowerCase().includes(lowerQuery)) ||
      ingredient.scientificName?.toLowerCase().includes(lowerQuery) ||
      ingredient.category.toLowerCase().includes(lowerQuery)
  );
}

export function getIngredientByName(name: string): ApothecaryIngredient | undefined {
  return APOTHECARY.find((i) => i.name.toLowerCase() === name.toLowerCase());
}

export function getIngredientsByOrigin(origin: IngredientOrigin): ApothecaryIngredient[] {
  return APOTHECARY.filter((i) => i.origin === origin);
}

export function getIngredientsByCategory(category: string): ApothecaryIngredient[] {
  return APOTHECARY.filter((i) => i.category.toLowerCase().includes(category.toLowerCase()));
}

/**
 * Analyze ingredients in a product for synthetic vs natural
 */
export interface IngredientAnalysis {
  totalIngredients: number;
  natural: number;
  synthetic: number;
  unknown: number;
  knownIngredients: Array<{
    name: string;
    apothecaryData: ApothecaryIngredient;
    isSynthetic: boolean;
  }>;
  unknownIngredients: string[];
}

export function analyzeProductIngredients(ingredientsList: string): IngredientAnalysis {
  // Parse ingredients
  const ingredients = ingredientsList
    .split(/[,;]/)
    .map((i) => i.trim())
    .filter((i) => i.length > 0);

  const known: IngredientAnalysis['knownIngredients'] = [];
  const unknown: string[] = [];

  for (const ingredientText of ingredients) {
    // Try to find in apothecary
    const match = searchApothecary(ingredientText)[0];

    if (match) {
      known.push({
        name: ingredientText,
        apothecaryData: match,
        isSynthetic: match.isSynthetic,
      });
    } else {
      unknown.push(ingredientText);
    }
  }

  return {
    totalIngredients: ingredients.length,
    natural: known.filter((k) => !k.isSynthetic).length,
    synthetic: known.filter((k) => k.isSynthetic).length,
    unknown: unknown.length,
    knownIngredients: known,
    unknownIngredients: unknown,
  };
}
