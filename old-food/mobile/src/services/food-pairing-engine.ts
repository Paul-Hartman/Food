/**
 * Food Pairing Recommendation Engine
 *
 * Analyzes products from OpenFoodFacts and suggests optimal pairings
 * based on nutrient synergies, complementary nutrition profiles,
 * and scientific evidence.
 */

import { OpenFoodFactsProduct } from './openfoodfacts';
import {
  NUTRIENT_SYNERGIES,
  NUTRIENT_ANTAGONISMS,
  NutrientSynergy,
  NutrientAntagonism,
} from './nutrient-synergies';

export interface ProductNutrientProfile {
  product: OpenFoodFactsProduct;
  nutrients: {
    // Macros
    hasProtein: boolean;
    hasCarbs: boolean;
    hasFat: boolean;
    hasFiber: boolean;

    // Key micronutrients detected
    hasIron: boolean;
    hasVitaminC: boolean;
    hasVitaminD: boolean;
    hasVitaminE: boolean;
    hasVitaminK: boolean;
    hasCalcium: boolean;
    hasMagnesium: boolean;
    hasZinc: boolean;
    hasPotassium: boolean;
    hasSelenium: boolean;

    // Special compounds (detected from categories/ingredients)
    hasCurcumin: boolean; // Turmeric
    hasPiperine: boolean; // Black pepper
    hasCarotenoids: boolean; // Vitamin A sources
    hasLycopene: boolean; // Tomatoes
    hasOmega3: boolean; // Fish, walnuts, flax
    hasAllicin: boolean; // Garlic
    hasCatechins: boolean; // Green tea
    hasQuercetin: boolean; // Onions, apples
    hasResveratrol: boolean; // Grapes, berries
    hasSulforaphane: boolean; // Broccoli, cruciferous
    hasAnthocyanins: boolean; // Berries

    // Food categories
    isGrain: boolean;
    isLegume: boolean;
    isDairy: boolean;
    isFruit: boolean;
    isVegetable: boolean;
    isNut: boolean;
    isSeed: boolean;
    isFish: boolean;
    isMeat: boolean;
  };
  rawValues: {
    iron: number;
    vitaminC: number;
    vitaminD: number;
    calcium: number;
    protein: number;
    fat: number;
  };
}

/**
 * Analyze a product and extract its nutrient profile
 */
export function analyzeProductNutrients(
  product: OpenFoodFactsProduct
): ProductNutrientProfile {
  const n = product.nutriments || {};
  const categories = (product.categories || '').toLowerCase();
  const ingredients = (product.ingredients_text || '').toLowerCase();
  const tags = product.categories_tags?.join(' ').toLowerCase() || '';

  const nutrients = {
    // Macros
    hasProtein: (n.proteins_100g || 0) > 3,
    hasCarbs: (n.carbohydrates_100g || 0) > 5,
    hasFat: (n.fat_100g || 0) > 2,
    hasFiber: (n.fiber_100g || 0) > 2,

    // Micronutrients
    hasIron: (n.iron_100g || 0) > 0.5,
    hasVitaminC: (n['vitamin-c_100g'] || 0) > 5,
    hasVitaminD: (n['vitamin-d_100g'] || 0) > 0.1,
    hasVitaminE: (n['vitamin-e_100g'] || 0) > 0.5,
    hasVitaminK: false, // Not commonly in OpenFoodFacts data
    hasCalcium: (n.calcium_100g || 0) > 50,
    hasMagnesium: (n.magnesium_100g || 0) > 20,
    hasZinc: (n.zinc_100g || 0) > 0.5,
    hasPotassium: (n.potassium_100g || 0) > 100,
    hasSelenium: false, // Rarely in OFF data

    // Special compounds (keyword detection)
    hasCurcumin: ingredients.includes('turmeric') || ingredients.includes('curcumin'),
    hasPiperine:
      ingredients.includes('black pepper') ||
      ingredients.includes('pepper') ||
      ingredients.includes('piperine'),
    hasCarotenoids:
      tags.includes('carrot') ||
      tags.includes('sweet-potato') ||
      categories.includes('carrot') ||
      (n['vitamin-a_100g'] || 0) > 100,
    hasLycopene:
      tags.includes('tomato') ||
      categories.includes('tomato') ||
      ingredients.includes('tomato'),
    hasOmega3:
      tags.includes('fish') ||
      tags.includes('salmon') ||
      tags.includes('sardine') ||
      ingredients.includes('flax') ||
      ingredients.includes('walnut') ||
      ingredients.includes('chia'),
    hasAllicin: ingredients.includes('garlic') || ingredients.includes('allicin'),
    hasCatechins:
      ingredients.includes('green tea') ||
      ingredients.includes('tea extract') ||
      categories.includes('tea'),
    hasQuercetin:
      ingredients.includes('onion') ||
      ingredients.includes('apple') ||
      tags.includes('onion') ||
      tags.includes('apple'),
    hasResveratrol:
      ingredients.includes('grape') ||
      categories.includes('wine') ||
      tags.includes('berry'),
    hasSulforaphane:
      tags.includes('broccoli') ||
      tags.includes('brussels-sprouts') ||
      tags.includes('kale') ||
      tags.includes('cauliflower') ||
      categories.includes('cruciferous'),
    hasAnthocyanins:
      tags.includes('berry') ||
      tags.includes('blueberry') ||
      tags.includes('strawberry') ||
      categories.includes('berries'),

    // Categories
    isGrain:
      tags.includes('cereals') ||
      tags.includes('bread') ||
      tags.includes('pasta') ||
      tags.includes('rice'),
    isLegume:
      tags.includes('legume') ||
      tags.includes('bean') ||
      tags.includes('lentil') ||
      tags.includes('pea'),
    isDairy:
      tags.includes('dairies') || tags.includes('milk') || tags.includes('cheese'),
    isFruit: tags.includes('fruit'),
    isVegetable: tags.includes('vegetable'),
    isNut: tags.includes('nut') || tags.includes('almond') || tags.includes('walnut'),
    isSeed: tags.includes('seed'),
    isFish: tags.includes('fish') || tags.includes('seafood'),
    isMeat: tags.includes('meat') || tags.includes('poultry'),
  };

  return {
    product,
    nutrients,
    rawValues: {
      iron: n.iron_100g || 0,
      vitaminC: n['vitamin-c_100g'] || 0,
      vitaminD: n['vitamin-d_100g'] || 0,
      calcium: n.calcium_100g || 0,
      protein: n.proteins_100g || 0,
      fat: n.fat_100g || 0,
    },
  };
}

export interface PairingRecommendation {
  synergy: NutrientSynergy;
  relevance: 'high' | 'medium' | 'low';
  suggestedPairings: string[];
  explanation: string;
  scientificEvidence: string;
}

export interface PairingWarning {
  antagonism: NutrientAntagonism;
  severity: 'high' | 'medium' | 'low';
  avoidWith: string[];
  advice: string;
}

/**
 * Get pairing recommendations for a product
 */
export function getPairingRecommendations(
  product: OpenFoodFactsProduct
): {
  recommendations: PairingRecommendation[];
  warnings: PairingWarning[];
  quickTips: string[];
} {
  const profile = analyzeProductNutrients(product);
  const recommendations: PairingRecommendation[] = [];
  const warnings: PairingWarning[] = [];
  const quickTips: string[] = [];

  // Check for turmeric + black pepper synergy
  if (profile.nutrients.hasCurcumin && !profile.nutrients.hasPiperine) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'turmeric-black-pepper');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'high',
        suggestedPairings: ['Add a pinch of black pepper', 'Use in curry with black pepper'],
        explanation: 'Black pepper increases curcumin absorption by up to 2000%!',
        scientificEvidence: synergy.scientificBasis,
      });
      quickTips.push('🌶️ Add black pepper to boost turmeric absorption by 2000%');
    }
  }

  // Check for iron + vitamin C synergy
  if (profile.nutrients.hasIron && !profile.nutrients.hasVitaminC) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'vitamin-c-iron');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'high',
        suggestedPairings: [
          'Serve with citrus fruits',
          'Add bell peppers',
          'Include tomatoes',
          'Pair with strawberries',
        ],
        explanation: 'Vitamin C increases iron absorption by 3-4x',
        scientificEvidence: synergy.scientificBasis,
      });
      quickTips.push('🍊 Pair with vitamin C to absorb 3x more iron');
    }
  }

  // Check for carotenoids + fat synergy
  if (profile.nutrients.hasCarotenoids && profile.rawValues.fat < 3) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'fat-carotenoids');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'high',
        suggestedPairings: [
          'Drizzle with olive oil',
          'Add avocado',
          'Include nuts/seeds',
          'Use oil-based dressing',
        ],
        explanation: 'Fat increases vitamin A absorption by up to 600%',
        scientificEvidence: synergy.scientificBasis,
      });
      quickTips.push('🥑 Add healthy fat to absorb 6x more vitamin A');
    }
  }

  // Check for lycopene (tomato) + fat + heat
  if (profile.nutrients.hasLycopene) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'lycopene-fat-heat');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'high',
        suggestedPairings: [
          'Cook with olive oil',
          'Make tomato sauce',
          'Roast with oil',
          'Sauté in butter',
        ],
        explanation: 'Cooking tomatoes with fat increases lycopene by 3-4x',
        scientificEvidence: synergy.scientificBasis,
      });
      quickTips.push('🔥 Cook with oil to unlock 4x more lycopene');
    }
  }

  // Check for calcium + vitamin D synergy
  if (profile.nutrients.hasCalcium && !profile.nutrients.hasVitaminD) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'vitamin-d-calcium');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'high',
        suggestedPairings: [
          'Pair with fatty fish',
          'Add egg yolks',
          'Use fortified products',
          'Get sunlight exposure',
        ],
        explanation: 'Vitamin D boosts calcium absorption by 50%',
        scientificEvidence: synergy.scientificBasis,
      });
      quickTips.push('☀️ Need vitamin D to absorb this calcium');
    }
  }

  // Check for grain + legume complete protein
  if (profile.nutrients.isGrain && !profile.nutrients.isLegume) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'complete-protein-combination');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'medium',
        suggestedPairings: ['Add beans', 'Serve with lentils', 'Include chickpeas'],
        explanation: 'Combine with legumes for complete protein',
        scientificEvidence: synergy.scientificBasis,
      });
      quickTips.push('🫘 Combine with beans for complete protein');
    }
  }

  // Check for legume + grain complete protein
  if (profile.nutrients.isLegume && !profile.nutrients.isGrain) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'complete-protein-combination');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'medium',
        suggestedPairings: ['Serve with rice', 'Add bread', 'Include quinoa'],
        explanation: 'Combine with grains for complete protein',
        scientificEvidence: synergy.scientificBasis,
      });
    }
  }

  // Check for green tea (catechins)
  if (profile.nutrients.hasCatechins) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'green-tea-lemon');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'high',
        suggestedPairings: ['Add lemon juice', 'Squeeze lime', 'Include citrus'],
        explanation: 'Lemon increases green tea benefits by 5x',
        scientificEvidence: synergy.scientificBasis,
      });
      quickTips.push('🍋 Add lemon to boost tea antioxidants by 5x');
    }
  }

  // Check for omega-3 + garlic synergy
  if (profile.nutrients.hasOmega3 && !profile.nutrients.hasAllicin) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'garlic-fish-oil');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'medium',
        suggestedPairings: ['Cook with garlic', 'Add garlic seasoning'],
        explanation: 'Garlic enhances omega-3 cardiovascular benefits',
        scientificEvidence: synergy.scientificBasis,
      });
    }
  }

  // Check for cruciferous + selenium
  if (profile.nutrients.hasSulforaphane) {
    const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'sulforaphane-selenium');
    if (synergy) {
      recommendations.push({
        synergy,
        relevance: 'medium',
        suggestedPairings: [
          'Top with Brazil nuts',
          'Serve with fish',
          'Add hard-boiled eggs',
        ],
        explanation: 'Selenium + broccoli = enhanced cancer protection',
        scientificEvidence: synergy.scientificBasis,
      });
    }
  }

  // WARNINGS - Check for antagonisms

  // Calcium + iron antagonism
  if (profile.nutrients.hasCalcium && profile.nutrients.hasIron) {
    const antagonism = NUTRIENT_ANTAGONISMS.find((a) => a.id === 'calcium-iron-inhibition');
    if (antagonism) {
      warnings.push({
        antagonism,
        severity: 'high',
        avoidWith: ['Iron supplements', 'Iron-fortified foods'],
        advice:
          'If relying on this for iron, avoid consuming with high-calcium foods in the same meal',
      });
      quickTips.push('⚠️ Calcium may reduce iron absorption - space meals apart');
    }
  }

  // High calcium + oxalates (spinach)
  if (
    profile.nutrients.hasCalcium &&
    (profile.product.categories_tags || []).some((t) => t.includes('spinach'))
  ) {
    const antagonism = NUTRIENT_ANTAGONISMS.find((a) => a.id === 'oxalates-calcium');
    if (antagonism) {
      warnings.push({
        antagonism,
        severity: 'medium',
        avoidWith: ['Raw spinach with dairy'],
        advice: 'Cooking spinach reduces oxalates and improves calcium availability',
      });
    }
  }

  return { recommendations, warnings, quickTips };
}

/**
 * Analyze multiple products in a meal for synergies
 */
export interface MealAnalysis {
  synergiesFound: Array<{
    synergy: NutrientSynergy;
    products: [string, string];
    benefit: string;
  }>;
  antagonismsFound: Array<{
    antagonism: NutrientAntagonism;
    products: [string, string];
    concern: string;
  }>;
  missingPairings: PairingRecommendation[];
  overallScore: number; // 0-100
  suggestions: string[];
}

export function analyzeMealCombination(products: OpenFoodFactsProduct[]): MealAnalysis {
  const profiles = products.map(analyzeProductNutrients);
  const synergiesFound: MealAnalysis['synergiesFound'] = [];
  const antagonismsFound: MealAnalysis['antagonismsFound'] = [];
  const missingPairings: PairingRecommendation[] = [];
  const suggestions: string[] = [];

  // Check all product pairs for synergies
  for (let i = 0; i < profiles.length; i++) {
    for (let j = i + 1; j < profiles.length; j++) {
      const p1 = profiles[i];
      const p2 = profiles[j];

      // Turmeric + black pepper
      if (
        (p1.nutrients.hasCurcumin && p2.nutrients.hasPiperine) ||
        (p2.nutrients.hasCurcumin && p1.nutrients.hasPiperine)
      ) {
        const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'turmeric-black-pepper')!;
        synergiesFound.push({
          synergy,
          products: [p1.product.product_name, p2.product.product_name],
          benefit: '2000% better curcumin absorption',
        });
      }

      // Iron + vitamin C
      if (
        (p1.nutrients.hasIron && p2.nutrients.hasVitaminC) ||
        (p2.nutrients.hasIron && p1.nutrients.hasVitaminC)
      ) {
        const synergy = NUTRIENT_SYNERGIES.find((s) => s.id === 'vitamin-c-iron')!;
        synergiesFound.push({
          synergy,
          products: [p1.product.product_name, p2.product.product_name],
          benefit: '3-4x better iron absorption',
        });
      }

      // Grain + legume
      if (
        (p1.nutrients.isGrain && p2.nutrients.isLegume) ||
        (p2.nutrients.isGrain && p1.nutrients.isLegume)
      ) {
        const synergy = NUTRIENT_SYNERGIES.find(
          (s) => s.id === 'complete-protein-combination'
        )!;
        synergiesFound.push({
          synergy,
          products: [p1.product.product_name, p2.product.product_name],
          benefit: 'Complete protein with all essential amino acids',
        });
      }

      // Calcium + iron antagonism
      if (
        (p1.nutrients.hasCalcium && p2.nutrients.hasIron) ||
        (p2.nutrients.hasCalcium && p1.nutrients.hasIron)
      ) {
        const antagonism = NUTRIENT_ANTAGONISMS.find(
          (a) => a.id === 'calcium-iron-inhibition'
        )!;
        antagonismsFound.push({
          antagonism,
          products: [p1.product.product_name, p2.product.product_name],
          concern: 'Calcium may reduce iron absorption by 50%',
        });
      }
    }
  }

  // Calculate overall score
  let score = 50; // Start neutral
  score += synergiesFound.length * 10; // +10 per synergy
  score -= antagonismsFound.length * 15; // -15 per antagonism
  score = Math.max(0, Math.min(100, score));

  // Generate suggestions
  if (synergiesFound.length > 0) {
    suggestions.push(`✅ Great! ${synergiesFound.length} beneficial pairing(s) detected`);
  }
  if (antagonismsFound.length > 0) {
    suggestions.push(`⚠️ ${antagonismsFound.length} nutrient conflict(s) to address`);
  }

  return {
    synergiesFound,
    antagonismsFound,
    missingPairings,
    overallScore: score,
    suggestions,
  };
}
