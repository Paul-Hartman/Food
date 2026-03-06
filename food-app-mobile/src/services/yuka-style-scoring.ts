/**
 * Yuka-Style Scoring System
 *
 * Implements a simplified 0-100 scoring algorithm similar to Yuka,
 * using OpenFoodFacts data we already have.
 *
 * Yuka's algorithm (approximated):
 * - Nutri-Score: 60% weight
 * - Additives: 30% weight
 * - Organic: 10% weight
 */

import { OpenFoodFactsProduct } from './openfoodfacts';

export interface ProductScore {
  score: number; // 0-100
  rating: 'excellent' | 'good' | 'poor' | 'bad';
  color: string; // Hex color for UI
  details: {
    nutriScore: number;
    additives: number;
    organic: number;
  };
  warnings: string[];
  recommendations: string[];
}

/**
 * Calculate a Yuka-style 0-100 score for a product
 */
export function calculateProductScore(product: OpenFoodFactsProduct): ProductScore {
  let score = 50; // Start at neutral
  const warnings: string[] = [];
  const recommendations: string[] = [];

  // 1. Nutri-Score contribution (60% weight = ±30 points)
  const nutriScorePoints: Record<string, number> = {
    a: 30, // Excellent
    b: 15, // Good
    c: 0, // Average
    d: -15, // Poor
    e: -30, // Bad
  };

  if (product.nutriscore_grade) {
    const nutriPoints = nutriScorePoints[product.nutriscore_grade.toLowerCase()] || 0;
    score += nutriPoints;

    if (nutriPoints < 0) {
      warnings.push(`Poor nutritional quality (Nutri-Score ${product.nutriscore_grade.toUpperCase()})`);
      recommendations.push('Look for alternatives with Nutri-Score A or B');
    }
  }

  // 2. NOVA processing level (30% weight = ±15 points)
  // Yuka uses additives; we use NOVA + ingredient analysis
  if (product.nova_group) {
    const novaPoints: Record<number, number> = {
      1: 15, // Unprocessed
      2: 5, // Minimally processed
      3: -5, // Processed
      4: -15, // Ultra-processed
    };
    const points = novaPoints[product.nova_group] || 0;
    score += points;

    if (product.nova_group === 4) {
      warnings.push('Ultra-processed food (NOVA Group 4)');
      recommendations.push('Choose whole, minimally processed foods when possible');
    }
  }

  // Additive detection (E-numbers)
  const additives = detectAdditives(product.ingredients_text || '');
  if (additives.length > 0) {
    score -= Math.min(additives.length * 2, 15); // Max -15 points
    warnings.push(`Contains ${additives.length} additive(s): ${additives.slice(0, 3).join(', ')}`);
  }

  // 3. Eco-Score contribution (10% weight = ±5 points)
  if (product.ecoscore_grade) {
    const ecoPoints: Record<string, number> = {
      a: 5,
      b: 2,
      c: 0,
      d: -2,
      e: -5,
    };
    score += ecoPoints[product.ecoscore_grade.toLowerCase()] || 0;
  }

  // Organic bonus
  const isOrganic =
    product.categories_tags?.some((tag) => tag.includes('organic')) ||
    product.ingredients_text?.toLowerCase().includes('organic') ||
    false;
  if (isOrganic) {
    score += 5;
    recommendations.push('✓ Organic product');
  }

  // Check for problematic ingredients
  const problematicIngredients = detectProblematicIngredients(product);
  if (problematicIngredients.length > 0) {
    score -= problematicIngredients.length * 3;
    warnings.push(...problematicIngredients);
  }

  // Clamp score to 0-100
  score = Math.max(0, Math.min(100, Math.round(score)));

  // Determine rating
  const rating = getRating(score);
  const color = getRatingColor(rating);

  return {
    score,
    rating,
    color,
    details: {
      nutriScore: nutriScorePoints[product.nutriscore_grade?.toLowerCase() || 'c'] || 0,
      additives: -Math.min(additives.length * 2, 15),
      organic: isOrganic ? 5 : 0,
    },
    warnings,
    recommendations,
  };
}

/**
 * Get rating category from score
 */
function getRating(score: number): 'excellent' | 'good' | 'poor' | 'bad' {
  if (score >= 75) return 'excellent';
  if (score >= 50) return 'good';
  if (score >= 25) return 'poor';
  return 'bad';
}

/**
 * Get color for rating (Yuka-style)
 */
export function getRatingColor(rating: string): string {
  const colors: Record<string, string> = {
    excellent: '#4CAF50', // Green
    good: '#8BC34A', // Light green
    poor: '#FF9800', // Orange
    bad: '#F44336', // Red
  };
  return colors[rating] || '#9E9E9E';
}

/**
 * Detect E-number additives in ingredients
 */
function detectAdditives(ingredientsText: string): string[] {
  if (!ingredientsText) return [];

  const eNumbers = ingredientsText.match(/E\d{3,4}/gi) || [];
  return [...new Set(eNumbers.map((e) => e.toUpperCase()))];
}

/**
 * Detect problematic ingredients
 */
function detectProblematicIngredients(product: OpenFoodFactsProduct): string[] {
  const warnings: string[] = [];
  const ingredients = (product.ingredients_text || '').toLowerCase();

  // High sugar content
  const sugars = product.nutriments?.sugars_100g || 0;
  if (sugars > 15) {
    warnings.push(`High sugar content: ${sugars.toFixed(1)}g per 100g`);
  }

  // High salt content
  const salt = product.nutriments?.salt_100g || 0;
  if (salt > 1.5) {
    warnings.push(`High salt content: ${salt.toFixed(1)}g per 100g`);
  }

  // Saturated fat
  const satFat = product.nutriments?.['saturated-fat_100g'] || 0;
  if (satFat > 10) {
    warnings.push(`High saturated fat: ${satFat.toFixed(1)}g per 100g`);
  }

  // Palm oil
  if (ingredients.includes('palm oil') || ingredients.includes('palmitate')) {
    warnings.push('Contains palm oil (environmental concern)');
  }

  // Artificial sweeteners
  const sweeteners = ['aspartame', 'sucralose', 'acesulfame', 'saccharin'];
  for (const sweetener of sweeteners) {
    if (ingredients.includes(sweetener)) {
      warnings.push(`Contains artificial sweetener: ${sweetener}`);
      break;
    }
  }

  return warnings;
}

/**
 * Find healthier alternatives to a product
 */
export interface AlternativeProduct {
  product: OpenFoodFactsProduct;
  score: ProductScore;
  improvement: number; // How much better the score is
}

/**
 * Get emoji for rating
 */
export function getRatingEmoji(rating: string): string {
  const emojis: Record<string, string> = {
    excellent: '🟢',
    good: '🟡',
    poor: '🟠',
    bad: '🔴',
  };
  return emojis[rating] || '⚪';
}

/**
 * Get human-readable description
 */
export function getRatingDescription(rating: string): string {
  const descriptions: Record<string, string> = {
    excellent: 'Excellent choice',
    good: 'Good product',
    poor: 'Mediocre quality',
    bad: 'Poor choice - consider alternatives',
  };
  return descriptions[rating] || 'Unknown';
}

/**
 * Check if product meets dietary preferences
 */
export interface DietaryPreference {
  vegan?: boolean;
  vegetarian?: boolean;
  glutenFree?: boolean;
  dairyFree?: boolean;
  organic?: boolean;
}

export function matchesDietaryPreferences(
  product: OpenFoodFactsProduct,
  preferences: DietaryPreference
): { matches: boolean; violations: string[] } {
  const violations: string[] = [];
  const tags = product.categories_tags || [];
  const ingredients = (product.ingredients_text || '').toLowerCase();

  if (preferences.vegan) {
    const hasAnimalProducts =
      tags.some((t) => t.includes('meat') || t.includes('dairy') || t.includes('egg')) ||
      ingredients.includes('milk') ||
      ingredients.includes('egg') ||
      ingredients.includes('honey');

    if (hasAnimalProducts) {
      violations.push('Not vegan (contains animal products)');
    }
  }

  if (preferences.vegetarian) {
    const hasMeat = tags.some((t) => t.includes('meat') || t.includes('fish'));
    if (hasMeat) {
      violations.push('Not vegetarian (contains meat/fish)');
    }
  }

  if (preferences.glutenFree) {
    const hasGluten =
      tags.some((t) => t.includes('wheat') || t.includes('barley')) ||
      ingredients.includes('wheat') ||
      ingredients.includes('gluten');

    if (hasGluten) {
      violations.push('Contains gluten');
    }
  }

  if (preferences.dairyFree) {
    const hasDairy =
      tags.some((t) => t.includes('dairy')) ||
      ingredients.includes('milk') ||
      ingredients.includes('lactose');

    if (hasDairy) {
      violations.push('Contains dairy');
    }
  }

  if (preferences.organic) {
    const isOrganic = tags.some((t) => t.includes('organic'));
    if (!isOrganic) {
      violations.push('Not certified organic');
    }
  }

  return {
    matches: violations.length === 0,
    violations,
  };
}
