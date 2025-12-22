/**
 * Open Food Facts API Service
 *
 * Provides barcode lookup and search for food products
 * API: https://world.openfoodfacts.org/data
 *
 * Features:
 * - Comprehensive nutrition data (macros, vitamins, minerals)
 * - Nutri-Score, NOVA group, Eco-Score
 * - Allergen information
 * - Ingredients list
 * - Product images
 */

export interface OpenFoodFactsProduct {
  code: string;
  product_name: string;
  brands?: string;
  quantity?: string;
  categories?: string;
  categories_tags?: string[];
  image_url?: string;
  image_small_url?: string;
  image_front_url?: string;
  image_front_small_url?: string;
  image_nutrition_url?: string;

  // Nutrition data per 100g
  nutriments?: {
    // Energy
    'energy-kcal_100g'?: number;
    'energy-kj_100g'?: number;

    // Macronutrients
    proteins_100g?: number;
    carbohydrates_100g?: number;
    fat_100g?: number;
    fiber_100g?: number;
    sugars_100g?: number;
    'saturated-fat_100g'?: number;
    salt_100g?: number;
    sodium_100g?: number;

    // Vitamins (when available)
    'vitamin-a_100g'?: number;
    'vitamin-c_100g'?: number;
    'vitamin-d_100g'?: number;
    'vitamin-e_100g'?: number;

    // Minerals (when available)
    calcium_100g?: number;
    iron_100g?: number;
    potassium_100g?: number;
    magnesium_100g?: number;
    zinc_100g?: number;
  };

  // Nutrition grades
  nutriscore_grade?: string; // a, b, c, d, e
  nutriscore_score?: number;

  // Processing level (NOVA groups 1-4)
  nova_group?: number;

  // Environmental impact
  ecoscore_grade?: string; // a, b, c, d, e
  ecoscore_score?: number;

  // Allergens
  allergens?: string;
  allergens_tags?: string[];

  // Ingredients
  ingredients_text?: string;
  ingredients_tags?: string[];

  // Serving size
  serving_size?: string;
  serving_quantity?: number;
}

export interface OpenFoodFactsResponse {
  status: number;
  status_verbose?: string;
  product?: OpenFoodFactsProduct;
}

export interface OpenFoodFactsSearchResponse {
  count: number;
  page: number;
  page_count: number;
  page_size: number;
  products: OpenFoodFactsProduct[];
}

const BASE_URL = 'https://world.openfoodfacts.org/api/v2';

/**
 * Look up a product by barcode in Open Food Facts database
 */
export async function lookupBarcode(barcode: string): Promise<OpenFoodFactsProduct | null> {
  try {
    console.log('🔍 Looking up barcode:', barcode);

    const response = await fetch(`${BASE_URL}/product/${barcode}.json`, {
      headers: {
        'User-Agent': 'FoodApp - React Native - Version 1.0',
      },
    });

    if (!response.ok) {
      console.log('❌ API returned error:', response.status);
      return null;
    }

    const data: OpenFoodFactsResponse = await response.json();

    if (data.status === 1 && data.product) {
      console.log('✓ Found product:', data.product.product_name);
      console.log('  Nutri-Score:', data.product.nutriscore_grade || 'N/A');
      console.log('  NOVA:', data.product.nova_group || 'N/A');
      return data.product;
    }

    console.log('✗ Product not found in database');
    return null;
  } catch (error) {
    console.error('OpenFoodFacts lookup error:', error);
    return null;
  }
}

/**
 * Search products by name or brand
 * Uses the v2 search API for better results
 */
export async function searchProducts(
  query: string,
  page: number = 1,
  pageSize: number = 20
): Promise<OpenFoodFactsProduct[]> {
  try {
    console.log('🔍 Searching:', query);

    const response = await fetch(
      `${BASE_URL}/search?search_terms=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}&json=true`,
      {
        headers: {
          'User-Agent': 'FoodApp - React Native - Version 1.0',
        },
      }
    );

    if (!response.ok) {
      return [];
    }

    const data: OpenFoodFactsSearchResponse = await response.json();
    const products = data.products || [];

    // Filter out products with missing essential data
    const qualityProducts = products.filter((product) => {
      const name = (product.product_name || '').trim();
      const brand = (product.brands || '').trim();

      // Must have name
      if (!name || name.length < 2) {
        return false;
      }

      // Reject if "Unknown" in name
      if (name.toLowerCase().includes('unknown')) {
        return false;
      }

      return true;
    });

    console.log(`📊 Found: ${products.length} → ${qualityProducts.length} quality products`);
    return qualityProducts;
  } catch (error) {
    console.error('OpenFoodFacts search error:', error);
    return [];
  }
}

/**
 * Extract pantry item data from OpenFoodFacts product
 */
export function extractPantryItem(product: OpenFoodFactsProduct): {
  name: string;
  category: string;
  quantity: number;
  unit: string;
  image_url?: string;
} {
  // Parse quantity from product data
  let quantity = 1;
  let unit = 'item';

  if (product.quantity) {
    // Try to parse quantity like "500g", "1L", "6 x 330ml"
    const match = product.quantity.match(/(\d+(?:\.\d+)?)\s*(g|kg|ml|l|oz|lb)?/i);
    if (match) {
      quantity = parseFloat(match[1]);
      unit = match[2]?.toLowerCase() || 'item';
    }
  }

  // Determine category from product categories
  const category = inferCategory(product);
  const name = product.product_name || product.brands || 'Unknown Product';

  // Get the best available image (prefer small for mobile)
  const image_url = product.image_small_url || product.image_front_small_url || product.image_url || product.image_front_url;

  return { name, category, quantity, unit, image_url };
}

/**
 * Infer product category from Open Food Facts data
 */
function inferCategory(product: OpenFoodFactsProduct): string {
  const categories = (product.categories || '').toLowerCase();
  const name = (product.product_name || '').toLowerCase();
  const combined = `${categories} ${name}`;

  // Check category tags first (more reliable)
  if (product.categories_tags) {
    const tags = product.categories_tags.join(' ').toLowerCase();

    if (tags.includes('meat') || tags.includes('poultry') || tags.includes('fish') || tags.includes('seafood')) {
      return 'protein';
    }
    if (tags.includes('dairies') || tags.includes('milk') || tags.includes('cheese') || tags.includes('yogurt')) {
      return 'dairy';
    }
    if (tags.includes('vegetables') || tags.includes('fruits')) {
      return 'fruit';
    }
    if (tags.includes('cereals') || tags.includes('bread') || tags.includes('pasta')) {
      return 'grain';
    }
    if (tags.includes('beverages') || tags.includes('drinks')) {
      return 'other';
    }
    if (tags.includes('snacks') || tags.includes('sweet-snacks') || tags.includes('salty-snacks')) {
      return 'other';
    }
    if (tags.includes('frozen-foods')) {
      return 'frozen';
    }
  }

  // Fallback to text matching
  if (combined.includes('meat') || combined.includes('poultry') || combined.includes('fish') || combined.includes('chicken') || combined.includes('beef') || combined.includes('pork')) {
    return 'protein';
  }
  if (combined.includes('dairy') || combined.includes('milk') || combined.includes('cheese') || combined.includes('yogurt')) {
    return 'dairy';
  }
  if (combined.includes('vegetable') || combined.includes('fruit')) {
    return 'fruit';
  }
  if (combined.includes('grain') || combined.includes('bread') || combined.includes('pasta') || combined.includes('rice')) {
    return 'grain';
  }
  if (combined.includes('spice') || combined.includes('seasoning')) {
    return 'spice';
  }
  if (combined.includes('frozen')) {
    return 'frozen';
  }
  if (combined.includes('bakery') || combined.includes('baked')) {
    return 'bakery';
  }

  return 'other';
}

/**
 * Get a human-readable nutrition score description
 */
export function getNutriScoreDescription(grade?: string): string {
  if (!grade) return 'Not rated';

  const descriptions: Record<string, string> = {
    a: 'Excellent nutritional quality',
    b: 'Good nutritional quality',
    c: 'Average nutritional quality',
    d: 'Poor nutritional quality',
    e: 'Very poor nutritional quality',
  };

  return descriptions[grade.toLowerCase()] || 'Not rated';
}

/**
 * Get NOVA group description (food processing level)
 */
export function getNovaDescription(group?: number): string {
  if (!group) return 'Unknown';

  const descriptions: Record<number, string> = {
    1: 'Unprocessed or minimally processed',
    2: 'Processed culinary ingredients',
    3: 'Processed foods',
    4: 'Ultra-processed foods',
  };

  return descriptions[group] || 'Unknown';
}

/**
 * Format nutrition data for display
 */
export function formatNutritionData(product: OpenFoodFactsProduct) {
  const n = product.nutriments || {};

  return {
    // Core macros (per 100g)
    calories: n['energy-kcal_100g'] || 0,
    protein: n.proteins_100g || 0,
    carbs: n.carbohydrates_100g || 0,
    fat: n.fat_100g || 0,
    fiber: n.fiber_100g || 0,
    sugars: n.sugars_100g || 0,
    saturatedFat: n['saturated-fat_100g'] || 0,
    salt: n.salt_100g || 0,
    sodium: n.sodium_100g || 0,

    // Vitamins (when available)
    vitaminA: n['vitamin-a_100g'],
    vitaminC: n['vitamin-c_100g'],
    vitaminD: n['vitamin-d_100g'],
    vitaminE: n['vitamin-e_100g'],

    // Minerals (when available)
    calcium: n.calcium_100g,
    iron: n.iron_100g,
    potassium: n.potassium_100g,
    magnesium: n.magnesium_100g,
    zinc: n.zinc_100g,

    // Scores
    nutriScore: product.nutriscore_grade?.toUpperCase(),
    nutriScoreDesc: getNutriScoreDescription(product.nutriscore_grade),
    novaGroup: product.nova_group,
    novaDesc: getNovaDescription(product.nova_group),
    ecoScore: product.ecoscore_grade?.toUpperCase(),

    // Allergens
    allergens: product.allergens_tags || [],

    // Serving info
    servingSize: product.serving_size,
  };
}
