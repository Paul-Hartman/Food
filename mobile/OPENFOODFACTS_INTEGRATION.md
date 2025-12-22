# OpenFoodFacts Integration Guide

## Overview

This food app now has comprehensive integration with [OpenFoodFacts](https://world.openfoodfacts.org/), the largest open database of food products in the world with over 2.5 million products.

## Features

### 1. **Barcode Scanner** 📷

Scan product barcodes to instantly add items to your pantry with full nutritional data.

**Location:** PantryScreen.tsx
- Tap the camera button next to the "Add" input
- Point your camera at any food barcode (UPC, EAN13, EAN8, etc.)
- Product info loads automatically from OpenFoodFacts
- Confirm to add to pantry

**Supported Barcode Types:**
- EAN-13 (most common worldwide)
- EAN-8
- UPC-A (US/Canada)
- UPC-E
- Code 128
- Code 39

### 2. **Comprehensive Nutrition Data** 📊

The integration provides:

#### Macronutrients (per 100g)
- Calories (kcal)
- Protein
- Carbohydrates (including sugars)
- Fat (including saturated fat)
- Fiber
- Salt/Sodium

#### Micronutrients (when available)
- Vitamins: A, C, D, E
- Minerals: Calcium, Iron, Potassium, Magnesium, Zinc

#### Quality Scores
- **Nutri-Score** (A-E): Overall nutritional quality
  - A (green) = Excellent
  - B (light green) = Good
  - C (yellow) = Average
  - D (orange) = Poor
  - E (red) = Very poor

- **NOVA Group** (1-4): Food processing level
  - 1 = Unprocessed or minimally processed
  - 2 = Processed culinary ingredients
  - 3 = Processed foods
  - 4 = Ultra-processed foods

- **Eco-Score** (A-E): Environmental impact rating

#### Additional Information
- Allergen warnings
- Full ingredients list
- Serving size information
- Product images

### 3. **Product Search** 🔍

Search the OpenFoodFacts database by product name, brand, or category.

**Component:** ProductSearchScreen.tsx
- Full-text search across 2.5M+ products
- Results filtered for quality (valid names, brands)
- View detailed nutrition facts for any product
- Tap any result to see comprehensive ProductNutritionCard

### 4. **Smart Category Detection** 🏷️

Products are automatically categorized based on OpenFoodFacts data:
- Protein (meat, poultry, fish, seafood)
- Dairy (milk, cheese, yogurt)
- Fruit (fruits, vegetables)
- Grain (bread, pasta, rice, cereals)
- Frozen
- Bakery
- Spice
- Other

## API Details

### Base URL
```
https://world.openfoodfacts.org/api/v2
```

### Endpoints Used

1. **Product Lookup**
   ```
   GET /product/{barcode}.json
   ```
   Returns full product data including nutrition, images, scores

2. **Product Search**
   ```
   GET /search?search_terms={query}&page={page}&page_size={size}
   ```
   Returns array of matching products

### Rate Limits
- None officially enforced
- Best practice: Use caching, avoid rapid-fire requests
- User-Agent header required: `FoodApp - React Native - Version 1.0`

## Components Reference

### Services

**`src/services/openfoodfacts.ts`**
```typescript
// Main functions
lookupBarcode(barcode: string): Promise<OpenFoodFactsProduct | null>
searchProducts(query: string, page?: number): Promise<OpenFoodFactsProduct[]>
extractPantryItem(product: OpenFoodFactsProduct): PantryItemData
formatNutritionData(product: OpenFoodFactsProduct): FormattedNutrition

// Helper functions
getNutriScoreDescription(grade?: string): string
getNovaDescription(group?: number): string
```

### UI Components

**`src/components/BarcodeScanner.tsx`**
- Full-screen camera scanner
- Real-time barcode detection
- Haptic feedback on scan success/failure
- Product confirmation dialog

**`src/components/ProductNutritionCard.tsx`**
- Comprehensive nutrition facts display
- Visual score badges (Nutri-Score, NOVA, Eco-Score)
- Color-coded quality indicators
- Allergen warnings
- Ingredients list

**`src/screens/ProductSearchScreen.tsx`**
- Search interface for OpenFoodFacts
- Product list with thumbnails
- Modal detail view

## Integration with Pantry System

When a product is scanned:

1. Barcode → OpenFoodFacts API lookup
2. Product data extracted:
   - Name from `product_name`
   - Brand from `brands`
   - Category inferred from `categories_tags`
   - Quantity parsed from `quantity` field
3. Item added to pantry via existing API
4. Nutrition data stored for tracking

## Data Quality

OpenFoodFacts is crowd-sourced, so quality varies:

✅ **High Quality**
- Major brands (Coca-Cola, Nestlé, Unilever, etc.)
- European products (especially France)
- Products with complete barcodes

⚠️ **Variable Quality**
- Small local brands
- New products
- Non-food items sometimes included

**Quality Filters Applied:**
- Products must have valid product name (>2 chars)
- Rejects products with "Unknown" in name
- Filters out incomplete entries

## Example Usage

### Basic Barcode Lookup
```typescript
import { lookupBarcode, formatNutritionData } from '../services/openfoodfacts';

const product = await lookupBarcode('3017620422003'); // Nutella
if (product) {
  const nutrition = formatNutritionData(product);
  console.log(nutrition.calories); // 539 kcal per 100g
  console.log(nutrition.nutriScore); // "D" (poor)
  console.log(nutrition.novaGroup); // 4 (ultra-processed)
}
```

### Product Search
```typescript
import { searchProducts } from '../services/openfoodfacts';

const results = await searchProducts('almond milk');
// Returns array of almond milk products with full nutrition data
```

### Add Scanned Product to Pantry
```typescript
import { lookupBarcode, extractPantryItem } from '../services/openfoodfacts';
import { api } from '../services/api';

const product = await lookupBarcode(barcode);
if (product) {
  const item = extractPantryItem(product);
  await api.addToPantry(item);
}
```

## Future Enhancements

Potential improvements:

1. **Offline Support**
   - Cache frequently scanned products
   - Download nutrition database subset

2. **Contribution Features**
   - Allow users to add missing products
   - Submit photos and nutrition facts
   - Report incorrect data

3. **Advanced Filtering**
   - Filter by Nutri-Score (only A/B products)
   - Filter by allergens
   - Filter by NOVA group (avoid ultra-processed)

4. **Recipe Integration**
   - Link scanned products to recipes
   - Auto-calculate recipe nutrition from ingredients

5. **Shopping List**
   - Scan products while shopping
   - Auto-check off items as scanned

## Resources

- **OpenFoodFacts Homepage**: https://world.openfoodfacts.org/
- **API Documentation**: https://openfoodfacts.github.io/api-documentation/
- **Product Browser**: https://world.openfoodfacts.org/products
- **Mobile Apps**: https://world.openfoodfacts.org/mobile-apps
- **Data Quality**: https://world.openfoodfacts.org/data-quality
- **GitHub**: https://github.com/openfoodfacts

## Comparison to Skincare App

This integration mirrors the pattern from `skincare-app/mobile/src/services/openbeautyfacts.ts`:

| Feature | Beauty Facts | Food Facts |
|---------|-------------|------------|
| Barcode lookup | ✅ | ✅ |
| Product search | ✅ | ✅ |
| Quality filtering | ✅ | ✅ |
| Multiple fallbacks | ✅ (UPC DB) | ❌ |
| Nutrition data | Limited | Comprehensive |
| Ingredient analysis | Fragrance detection | Allergen detection |
| Quality scores | None | Nutri/NOVA/Eco |

## License

OpenFoodFacts data is licensed under [ODbL](https://opendatacommons.org/licenses/odbl/1-0/) (Open Database License). You are free to:
- Share, create, and adapt
- Must attribute OpenFoodFacts
- Share-alike (any derivative databases must also be open)

## Support

For OpenFoodFacts API issues:
- Email: contact@openfoodfacts.org
- Slack: https://slack.openfoodfacts.org/

For app-specific issues:
- Check component documentation
- Review console logs for API errors
- Test with known barcodes (e.g., Coca-Cola: 5449000000996)
