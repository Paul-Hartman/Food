/**
 * Nutrient Synergies & Food Pairing Science
 *
 * Database of scientifically-proven food synergies where nutrients
 * enhance each other's absorption, effectiveness, or health benefits.
 *
 * Examples:
 * - Vitamin C + Iron (non-heme) → Better iron absorption
 * - Black Pepper (piperine) + Turmeric (curcumin) → 2000% better absorption
 * - Vitamin D + Calcium → Better calcium absorption
 * - Fat + Carotenoids (vitamin A) → Better absorption
 */

export interface NutrientSynergy {
  id: string;
  nutrient1: string;
  nutrient2: string;
  effect: string;
  magnitude: 'low' | 'moderate' | 'high' | 'very_high';
  magnitudePercent?: number; // e.g., 200 for 200% increase
  scientificBasis: string;
  foodExamples: {
    source1: string[];
    source2: string[];
    idealCombinations: string[];
  };
  timing?: string; // e.g., "consume together in same meal"
  warnings?: string[];
}

export const NUTRIENT_SYNERGIES: NutrientSynergy[] = [
  // ═══════════════════════════════════════════════════════════
  // CLASSIC SYNERGIES
  // ═══════════════════════════════════════════════════════════

  {
    id: 'turmeric-black-pepper',
    nutrient1: 'Curcumin (Turmeric)',
    nutrient2: 'Piperine (Black Pepper)',
    effect: 'Increases curcumin absorption by up to 2000%',
    magnitude: 'very_high',
    magnitudePercent: 2000,
    scientificBasis:
      'Piperine inhibits glucuronidation in the liver and intestine, dramatically increasing curcumin bioavailability',
    foodExamples: {
      source1: ['Turmeric powder', 'Curry', 'Golden milk'],
      source2: ['Black pepper', 'Peppercorns'],
      idealCombinations: [
        'Curry with black pepper',
        'Golden milk latte with pepper',
        'Turmeric rice with pepper',
      ],
    },
    timing: 'Consume together in the same meal',
  },

  {
    id: 'vitamin-c-iron',
    nutrient1: 'Vitamin C (Ascorbic Acid)',
    nutrient2: 'Iron (Non-Heme)',
    effect: 'Increases iron absorption by 3-4x',
    magnitude: 'very_high',
    magnitudePercent: 300,
    scientificBasis:
      'Vitamin C converts ferric iron (Fe3+) to ferrous iron (Fe2+), the more bioavailable form',
    foodExamples: {
      source1: ['Oranges', 'Strawberries', 'Bell peppers', 'Broccoli', 'Tomatoes'],
      source2: ['Spinach', 'Lentils', 'Beans', 'Fortified cereals', 'Tofu'],
      idealCombinations: [
        'Spinach salad with orange slices',
        'Lentil soup with tomatoes',
        'Bean burrito with salsa',
        'Tofu stir-fry with bell peppers',
      ],
    },
    timing: 'Consume vitamin C source within same meal as iron source',
    warnings: ['Does not apply to heme iron from meat, which is already well-absorbed'],
  },

  {
    id: 'vitamin-d-calcium',
    nutrient1: 'Vitamin D',
    nutrient2: 'Calcium',
    effect: 'Increases calcium absorption and bone deposition',
    magnitude: 'high',
    magnitudePercent: 50,
    scientificBasis:
      'Vitamin D increases intestinal calcium absorption and regulates calcium homeostasis',
    foodExamples: {
      source1: ['Salmon', 'Egg yolks', 'Fortified milk', 'Mushrooms (UV-exposed)'],
      source2: ['Dairy products', 'Kale', 'Sardines', 'Fortified plant milk'],
      idealCombinations: [
        'Salmon with kale',
        'Fortified milk',
        'Eggs with cheese',
        'Sardines on toast',
      ],
    },
    timing: 'Regular co-consumption; vitamin D is fat-soluble so stores in body',
  },

  {
    id: 'fat-carotenoids',
    nutrient1: 'Healthy Fats',
    nutrient2: 'Carotenoids (Vitamin A, Lycopene)',
    effect: 'Increases carotenoid absorption by up to 600%',
    magnitude: 'very_high',
    magnitudePercent: 600,
    scientificBasis:
      'Carotenoids are fat-soluble and require dietary fat for micelle formation and absorption',
    foodExamples: {
      source1: ['Olive oil', 'Avocado', 'Nuts', 'Seeds'],
      source2: ['Carrots', 'Tomatoes', 'Spinach', 'Sweet potatoes', 'Kale'],
      idealCombinations: [
        'Carrot salad with olive oil dressing',
        'Tomato sauce with olive oil',
        'Kale salad with avocado',
        'Sweet potato with butter',
      ],
    },
    timing: 'Add fat to the same meal as carotenoid sources',
  },

  // ═══════════════════════════════════════════════════════════
  // VITAMIN SYNERGIES
  // ═══════════════════════════════════════════════════════════

  {
    id: 'vitamin-e-vitamin-c',
    nutrient1: 'Vitamin E',
    nutrient2: 'Vitamin C',
    effect: 'Vitamin C regenerates oxidized vitamin E, extending its antioxidant activity',
    magnitude: 'high',
    scientificBasis:
      'Vitamin C reduces vitamin E radicals back to active vitamin E, creating synergistic antioxidant protection',
    foodExamples: {
      source1: ['Almonds', 'Sunflower seeds', 'Avocado', 'Spinach'],
      source2: ['Oranges', 'Strawberries', 'Bell peppers', 'Kiwi'],
      idealCombinations: [
        'Spinach salad with strawberries and almonds',
        'Avocado toast with tomatoes',
        'Trail mix with nuts and dried citrus',
      ],
    },
  },

  {
    id: 'vitamin-k-vitamin-d',
    nutrient1: 'Vitamin K2',
    nutrient2: 'Vitamin D3',
    effect: 'Work together for optimal bone and cardiovascular health',
    magnitude: 'high',
    scientificBasis:
      'Vitamin D increases calcium absorption; vitamin K2 directs calcium to bones (not arteries)',
    foodExamples: {
      source1: ['Natto', 'Hard cheeses', 'Egg yolks', 'Grass-fed butter'],
      source2: ['Fatty fish', 'Egg yolks', 'Fortified milk'],
      idealCombinations: [
        'Salmon with cheese',
        'Eggs with butter',
        'Fortified milk with cheese',
      ],
    },
    warnings: ['Important for preventing arterial calcification while building bone density'],
  },

  {
    id: 'b-vitamins-complex',
    nutrient1: 'B Vitamins (B1, B2, B3, B6, B9, B12)',
    nutrient2: 'B Vitamin Complex',
    effect: 'B vitamins work synergistically in energy metabolism',
    magnitude: 'moderate',
    scientificBasis:
      'B vitamins function as coenzymes in interconnected metabolic pathways (Krebs cycle, etc.)',
    foodExamples: {
      source1: ['Whole grains', 'Nutritional yeast', 'Eggs', 'Legumes'],
      source2: ['Meat', 'Fish', 'Dairy', 'Dark leafy greens'],
      idealCombinations: [
        'Whole grain bowl with beans and greens',
        'Eggs with whole wheat toast',
        'Salmon with brown rice',
      ],
    },
  },

  // ═══════════════════════════════════════════════════════════
  // MINERAL SYNERGIES
  // ═══════════════════════════════════════════════════════════

  {
    id: 'magnesium-calcium',
    nutrient1: 'Magnesium',
    nutrient2: 'Calcium',
    effect: 'Balanced ratio needed for muscle function and bone health',
    magnitude: 'high',
    scientificBasis:
      'Magnesium and calcium compete for absorption; ideal ratio is 1:2 (Mg:Ca)',
    foodExamples: {
      source1: ['Pumpkin seeds', 'Spinach', 'Dark chocolate', 'Almonds'],
      source2: ['Dairy', 'Kale', 'Sardines', 'Tofu'],
      idealCombinations: [
        'Greek yogurt with almonds',
        'Kale salad with pumpkin seeds',
        'Chocolate milk',
      ],
    },
    warnings: ['Too much calcium without magnesium can cause muscle cramps and calcification'],
  },

  {
    id: 'zinc-copper',
    nutrient1: 'Zinc',
    nutrient2: 'Copper',
    effect: 'Balance needed for immune function and metabolism',
    magnitude: 'moderate',
    scientificBasis:
      'Zinc and copper compete for absorption; excess of one can cause deficiency of the other',
    foodExamples: {
      source1: ['Oysters', 'Beef', 'Pumpkin seeds', 'Chickpeas'],
      source2: ['Liver', 'Cashews', 'Dark chocolate', 'Mushrooms'],
      idealCombinations: ['Mixed nuts', 'Beef stew with mushrooms', 'Trail mix with seeds'],
    },
    warnings: ['Maintain 10:1 zinc:copper ratio; high zinc supplements can deplete copper'],
  },

  {
    id: 'sodium-potassium',
    nutrient1: 'Sodium',
    nutrient2: 'Potassium',
    effect: 'Balance critical for blood pressure and cellular function',
    magnitude: 'high',
    scientificBasis:
      'Sodium-potassium pump maintains cellular electrical gradients; modern diets too high in sodium',
    foodExamples: {
      source1: ['Sea salt', 'Celery', 'Beets'],
      source2: ['Bananas', 'Sweet potatoes', 'Avocado', 'Spinach', 'White beans'],
      idealCombinations: [
        'Baked sweet potato with sea salt',
        'Avocado toast with pinch of salt',
        'Banana with almond butter',
      ],
    },
    warnings: ['Aim for higher potassium intake to balance sodium in modern diet'],
  },

  // ═══════════════════════════════════════════════════════════
  // PROTEIN & AMINO ACID SYNERGIES
  // ═══════════════════════════════════════════════════════════

  {
    id: 'complete-protein-combination',
    nutrient1: 'Grains (Lysine-deficient)',
    nutrient2: 'Legumes (Methionine-deficient)',
    effect: 'Creates complete protein with all essential amino acids',
    magnitude: 'high',
    scientificBasis:
      'Combining complementary proteins provides all 9 essential amino acids',
    foodExamples: {
      source1: ['Rice', 'Wheat', 'Corn', 'Oats'],
      source2: ['Beans', 'Lentils', 'Peas', 'Peanuts'],
      idealCombinations: [
        'Rice and beans',
        'Peanut butter sandwich',
        'Lentil soup with bread',
        'Hummus with pita',
      ],
    },
    timing: 'Does not need to be same meal (body pools amino acids over 24h)',
  },

  // ═══════════════════════════════════════════════════════════
  // ANTIOXIDANT SYNERGIES
  // ═══════════════════════════════════════════════════════════

  {
    id: 'quercetin-vitamin-c',
    nutrient1: 'Quercetin',
    nutrient2: 'Vitamin C',
    effect: 'Enhanced antioxidant and anti-inflammatory effects',
    magnitude: 'moderate',
    scientificBasis:
      'Quercetin and vitamin C work synergistically to reduce inflammation and oxidative stress',
    foodExamples: {
      source1: ['Onions', 'Apples', 'Green tea', 'Berries'],
      source2: ['Citrus', 'Bell peppers', 'Strawberries', 'Kiwi'],
      idealCombinations: [
        'Apple slices with orange juice',
        'Berry smoothie',
        'Salad with onions and peppers',
      ],
    },
  },

  {
    id: 'sulforaphane-selenium',
    nutrient1: 'Sulforaphane (Broccoli)',
    nutrient2: 'Selenium',
    effect: 'Enhanced cancer-protective effects',
    magnitude: 'high',
    scientificBasis:
      'Both activate NRF2 pathway for cellular detoxification; synergistic anticancer activity',
    foodExamples: {
      source1: ['Broccoli', 'Brussels sprouts', 'Kale', 'Cauliflower'],
      source2: ['Brazil nuts', 'Fish', 'Eggs', 'Mushrooms'],
      idealCombinations: [
        'Broccoli with hard-boiled egg',
        'Roasted Brussels sprouts with Brazil nuts',
        'Kale salad with salmon',
      ],
    },
    timing: 'Regular consumption of both for long-term benefits',
  },

  // ═══════════════════════════════════════════════════════════
  // POLYPHENOL SYNERGIES
  // ═══════════════════════════════════════════════════════════

  {
    id: 'green-tea-lemon',
    nutrient1: 'Catechins (Green Tea)',
    nutrient2: 'Vitamin C (Lemon)',
    effect: 'Vitamin C stabilizes tea catechins, increasing absorption by 5x',
    magnitude: 'very_high',
    magnitudePercent: 400,
    scientificBasis:
      'Ascorbic acid prevents catechin degradation in intestinal pH conditions',
    foodExamples: {
      source1: ['Green tea', 'Matcha'],
      source2: ['Lemon juice', 'Lime', 'Orange'],
      idealCombinations: ['Green tea with lemon', 'Matcha lemonade'],
    },
    timing: 'Add citrus to tea immediately before drinking',
  },

  {
    id: 'resveratrol-quercetin',
    nutrient1: 'Resveratrol',
    nutrient2: 'Quercetin',
    effect: 'Synergistic anti-aging and cardiovascular benefits',
    magnitude: 'moderate',
    scientificBasis:
      'Both activate SIRT1 and other longevity pathways; work better together',
    foodExamples: {
      source1: ['Red grapes', 'Red wine', 'Peanuts', 'Berries'],
      source2: ['Onions', 'Apples', 'Berries', 'Green tea'],
      idealCombinations: [
        'Mixed berry salad',
        'Red wine with onion-rich meal',
        'Apple slices with peanut butter',
      ],
    },
  },

  // ═══════════════════════════════════════════════════════════
  // SPECIAL COMBINATIONS
  // ═══════════════════════════════════════════════════════════

  {
    id: 'garlic-fish-oil',
    nutrient1: 'Allicin (Garlic)',
    nutrient2: 'Omega-3 (Fish Oil)',
    effect: 'Enhanced cardiovascular protection and cholesterol reduction',
    magnitude: 'high',
    scientificBasis:
      'Garlic + omega-3 synergistically reduce triglycerides and improve HDL/LDL ratio',
    foodExamples: {
      source1: ['Garlic', 'Onions', 'Shallots'],
      source2: ['Salmon', 'Sardines', 'Mackerel', 'Walnuts', 'Flaxseed'],
      idealCombinations: [
        'Garlic butter salmon',
        'Sardines with garlic toast',
        'Tuna salad with onions',
      ],
    },
  },

  {
    id: 'lycopene-fat-heat',
    nutrient1: 'Lycopene (Tomatoes)',
    nutrient2: 'Fat + Heat',
    effect: 'Cooking tomatoes with fat increases lycopene bioavailability by 3-4x',
    magnitude: 'very_high',
    magnitudePercent: 300,
    scientificBasis:
      'Heat breaks down cell walls releasing lycopene; fat aids absorption of this carotenoid',
    foodExamples: {
      source1: ['Tomatoes', 'Tomato sauce', 'Tomato paste'],
      source2: ['Olive oil', 'Avocado oil'],
      idealCombinations: [
        'Pasta with tomato sauce and olive oil',
        'Roasted tomatoes with olive oil',
        'Gazpacho with olive oil',
      ],
    },
    timing: 'Cook tomatoes with oil for best absorption',
  },

  {
    id: 'ginger-turmeric',
    nutrient1: 'Gingerol (Ginger)',
    nutrient2: 'Curcumin (Turmeric)',
    effect: 'Enhanced anti-inflammatory effects',
    magnitude: 'moderate',
    scientificBasis:
      'Both inhibit COX-2 and other inflammatory pathways; synergistic effect on inflammation',
    foodExamples: {
      source1: ['Fresh ginger', 'Ginger powder'],
      source2: ['Turmeric', 'Curry'],
      idealCombinations: [
        'Golden milk with ginger and turmeric',
        'Curry with ginger',
        'Ginger-turmeric tea',
      ],
    },
  },
];

// ═══════════════════════════════════════════════════════════
// ANTAGONISTIC INTERACTIONS (What NOT to combine)
// ═══════════════════════════════════════════════════════════

export interface NutrientAntagonism {
  id: string;
  nutrient1: string;
  nutrient2: string;
  effect: string;
  magnitude: 'low' | 'moderate' | 'high';
  scientificBasis: string;
  avoidCombining: string[];
  separationTime?: string;
}

export const NUTRIENT_ANTAGONISMS: NutrientAntagonism[] = [
  {
    id: 'calcium-iron-inhibition',
    nutrient1: 'Calcium',
    nutrient2: 'Iron (Non-Heme)',
    effect: 'Calcium reduces iron absorption by up to 50%',
    magnitude: 'high',
    scientificBasis:
      'Calcium and iron compete for the same absorption pathway (DMT1 transporter)',
    avoidCombining: [
      'Milk with iron-fortified cereal',
      'Cheese with spinach (if relying on spinach for iron)',
      'Calcium supplement with iron supplement',
    ],
    separationTime: 'Separate calcium and iron sources by 2+ hours',
  },

  {
    id: 'phytates-minerals',
    nutrient1: 'Phytates (Grains, Legumes)',
    nutrient2: 'Iron, Zinc, Calcium',
    effect: 'Phytates bind minerals, reducing absorption by 50-80%',
    magnitude: 'high',
    scientificBasis:
      'Phytic acid chelates minerals, forming insoluble complexes that cannot be absorbed',
    avoidCombining: [
      'Unsoaked beans with zinc-dependent meals',
      'Raw oats with iron supplements',
    ],
    separationTime:
      'Soak, sprout, or ferment grains/legumes to reduce phytates; or separate by 3+ hours',
  },

  {
    id: 'tannins-iron',
    nutrient1: 'Tannins (Tea, Coffee)',
    nutrient2: 'Iron (Non-Heme)',
    effect: 'Tea/coffee can reduce iron absorption by 60-90%',
    magnitude: 'high',
    scientificBasis: 'Tannins bind iron, forming insoluble complexes',
    avoidCombining: [
      'Coffee with breakfast cereal',
      'Tea with vegetarian meal',
      'Coffee with iron supplement',
    ],
    separationTime: 'Wait 1+ hour after iron-rich meal before drinking tea/coffee',
  },

  {
    id: 'oxalates-calcium',
    nutrient1: 'Oxalates (Spinach, Rhubarb)',
    nutrient2: 'Calcium',
    effect: 'Oxalates bind calcium, reducing absorption',
    magnitude: 'moderate',
    scientificBasis: 'Oxalic acid forms calcium oxalate, which is not bioavailable',
    avoidCombining: [
      'Spinach smoothie with milk (if relying on milk for calcium)',
      'Rhubarb with yogurt',
    ],
    separationTime: 'Cook oxalate-rich vegetables to reduce oxalate content',
  },

  {
    id: 'alcohol-b-vitamins',
    nutrient1: 'Alcohol',
    nutrient2: 'B Vitamins (B1, B9, B12)',
    effect: 'Alcohol depletes B vitamins and impairs absorption',
    magnitude: 'high',
    scientificBasis:
      'Alcohol damages intestinal lining, increases excretion, and impairs B vitamin metabolism',
    avoidCombining: ['Heavy drinking with B vitamin-dependent processes'],
    separationTime: 'Limit alcohol consumption; supplement B vitamins if drinking regularly',
  },

  {
    id: 'high-fiber-medications',
    nutrient1: 'High Fiber',
    nutrient2: 'Medications/Supplements',
    effect: 'Fiber can reduce medication absorption',
    magnitude: 'moderate',
    scientificBasis: 'Fiber binds to some drugs, reducing bioavailability',
    avoidCombining: ['Fiber supplements with medications', 'Psyllium with thyroid medication'],
    separationTime: 'Take medications 1-2 hours before or 4 hours after fiber supplements',
  },
];

// ═══════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════

/**
 * Find synergies for a given nutrient
 */
export function findSynergiesForNutrient(nutrientName: string): NutrientSynergy[] {
  const lowerName = nutrientName.toLowerCase();
  return NUTRIENT_SYNERGIES.filter(
    (s) =>
      s.nutrient1.toLowerCase().includes(lowerName) ||
      s.nutrient2.toLowerCase().includes(lowerName)
  );
}

/**
 * Find antagonisms for a given nutrient
 */
export function findAntagonismsForNutrient(nutrientName: string): NutrientAntagonism[] {
  const lowerName = nutrientName.toLowerCase();
  return NUTRIENT_ANTAGONISMS.filter(
    (a) =>
      a.nutrient1.toLowerCase().includes(lowerName) ||
      a.nutrient2.toLowerCase().includes(lowerName)
  );
}

/**
 * Get ideal meal pairings for a product based on its nutrients
 */
export interface MealPairing {
  synergy: NutrientSynergy;
  confidence: 'low' | 'medium' | 'high';
  explanation: string;
}

/**
 * Check if two products have beneficial synergies
 */
export function checkProductSynergy(
  product1Nutrients: string[],
  product2Nutrients: string[]
): { synergies: NutrientSynergy[]; antagonisms: NutrientAntagonism[] } {
  const synergies: NutrientSynergy[] = [];
  const antagonisms: NutrientAntagonism[] = [];

  // Check for synergies
  for (const nutrient1 of product1Nutrients) {
    for (const nutrient2 of product2Nutrients) {
      const foundSynergies = NUTRIENT_SYNERGIES.filter(
        (s) =>
          (s.nutrient1.toLowerCase().includes(nutrient1.toLowerCase()) &&
            s.nutrient2.toLowerCase().includes(nutrient2.toLowerCase())) ||
          (s.nutrient1.toLowerCase().includes(nutrient2.toLowerCase()) &&
            s.nutrient2.toLowerCase().includes(nutrient1.toLowerCase()))
      );
      synergies.push(...foundSynergies);
    }
  }

  // Check for antagonisms
  for (const nutrient1 of product1Nutrients) {
    for (const nutrient2 of product2Nutrients) {
      const foundAntagonisms = NUTRIENT_ANTAGONISMS.filter(
        (a) =>
          (a.nutrient1.toLowerCase().includes(nutrient1.toLowerCase()) &&
            a.nutrient2.toLowerCase().includes(nutrient2.toLowerCase())) ||
          (a.nutrient1.toLowerCase().includes(nutrient2.toLowerCase()) &&
            a.nutrient2.toLowerCase().includes(nutrient1.toLowerCase()))
      );
      antagonisms.push(...foundAntagonisms);
    }
  }

  return { synergies, antagonisms };
}
