# Yuka App Analysis & Comparison

## TL;DR: We're Already Using the Same Data Source ✅

**Yuka does NOT have a public API.** They use a proprietary database that was originally built from OpenFoodFacts data. We're already using OpenFoodFacts directly, which gives us access to the same underlying product information that Yuka uses, plus it's open and free.

## What is Yuka?

[Yuka](https://yuka.io/) is a popular mobile app (10M+ downloads) that:
- Scans food and cosmetic product barcodes
- Rates products with a simple color-coded score (green/yellow/red)
- Provides health impact analysis
- Suggests healthier alternatives

## Yuka's Data Source History

### 2017-2018: Built on OpenFoodFacts
- Yuka initially relied entirely on [OpenFoodFacts](https://world.openfoodfacts.org/) for product data
- This is the same open database we're using in our food app
- Many popular apps (Foodvisor, El Coco, etc.) launched using OpenFoodFacts data

### 2018-Present: Proprietary Database
- In January 2018, Yuka [created their own database](https://help.yuka.io/l/en/article/5a4z64amnk-how-was-the-database-created)
- Implemented proprietary verification and monitoring systems
- Database is NOT publicly available
- NO public API for developers

### Current Relationship
- Yuka still contributes data back to OpenFoodFacts
- OpenFoodFacts tracks products tagged as ["App-yuka" data source](https://world.openfoodfacts.org/data-source/app-yuka)
- Two-way data flow between the platforms

## API Availability

### ❌ Yuka API: Does NOT Exist
- No public developer API
- No documented endpoints
- Proprietary database access only for Yuka app
- Several developers have tried to reverse-engineer it, but officially unsupported

### ✅ OpenFoodFacts API: Fully Open
- Public REST API with full documentation
- 2.5M+ products worldwide
- Free and unrestricted access
- Active developer community
- We're already using this! ✅

## What Makes Yuka Different?

Since we already use the same underlying data (OpenFoodFacts), here's what Yuka adds:

### 1. **Proprietary Scoring Algorithm**
Yuka's 0-100 score is calculated from:
- Nutri-Score (60% weight)
- Additives analysis (30% weight)
- Organic certification (10% weight)

**Our equivalent:**
- We already have Nutri-Score from OpenFoodFacts
- We can implement our own additive analysis
- Organic status available in OpenFoodFacts categories

### 2. **Simplified UI/UX**
- Single color-coded score (green/orange/red)
- Very consumer-friendly
- Minimal information overload

**Our approach:**
- More comprehensive nutrition facts display
- Educational (shows WHY something is rated a certain way)
- Power-user focused

### 3. **Alternative Product Recommendations**
- Suggests healthier alternatives when you scan unhealthy items
- Based on their scoring algorithm

**Potential feature for us:**
- We could implement this using OpenFoodFacts search + Nutri-Score filtering
- Find similar products with better scores

### 4. **Cosmetics Analysis** (Yuka also scans beauty products)
- Uses INCI database for cosmetic ingredients
- Endocrine disruptor detection
- Allergen warnings

**We already have this!** ✅
- Our skincare app uses OpenBeautyFacts
- Same concept, different database
- Already detecting allergens and fragrances

## Comparison Table

| Feature | Yuka | Our Food App | Our Skincare App |
|---------|------|--------------|------------------|
| **Data Source** | Proprietary (originally OFF) | OpenFoodFacts | OpenBeautyFacts |
| **Public API** | ❌ No | ✅ Yes (OFF) | ✅ Yes (OBF) |
| **Product Count** | ~3M | 2.5M+ (growing) | 900K+ |
| **Nutri-Score** | ✅ Yes | ✅ Yes | N/A |
| **NOVA Group** | ❌ No | ✅ Yes | N/A |
| **Eco-Score** | ❌ No | ✅ Yes | N/A |
| **Full Nutrition** | Limited | ✅ Comprehensive | N/A |
| **Vitamins/Minerals** | ❌ No | ✅ Yes (when available) | N/A |
| **Additives Analysis** | ✅ Yes (proprietary) | ⚠️ Could add | N/A |
| **Ingredient Analysis** | Limited | ✅ Full list | ✅ Yes |
| **Allergen Detection** | ✅ Yes | ✅ Yes | N/A |
| **Alternative Suggestions** | ✅ Yes | ⚠️ Could add | ⚠️ Could add |
| **Barcode Scanner** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Product Search** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Cost** | Free (with ads/premium) | Free | Free |
| **Data Access** | Closed | Open | Open |

## Should We Integrate Yuka?

### ❌ Cannot Integrate - No API Available

**Reasons:**
1. Yuka does not provide a public API
2. Their database is proprietary and not accessible
3. Using OpenFoodFacts directly gives us the same base data
4. We have MORE data features than Yuka (NOVA, Eco-Score, comprehensive nutrition)

### ✅ What We Can Do Instead

1. **Implement Yuka-like Features**
   - Add simplified scoring (0-100 scale)
   - Color-coded ratings (green/yellow/red)
   - "Find a better product" suggestions
   - Additive analysis (flag E-numbers)

2. **Enhance Our Existing Integration**
   - Better UI for quick glances (like Yuka's simplicity)
   - Alternative product recommendations
   - Personalized filtering (vegan, gluten-free, etc.)
   - Shopping list smart suggestions

3. **Leverage OpenFoodFacts Features Yuka Doesn't Have**
   - NOVA processing levels (ultra-processed detection)
   - Eco-Score environmental impact
   - Complete vitamin/mineral data
   - More detailed ingredient breakdowns

## Feature Ideas Inspired by Yuka

### For Food App:

```typescript
// 1. Yuka-style simplified score (0-100)
function calculateYukaStyleScore(product: OpenFoodFactsProduct): number {
  let score = 50; // Start at neutral

  // Nutri-Score contribution (60% weight)
  const nutriScoreValues = { a: 30, b: 15, c: 0, d: -15, e: -30 };
  score += nutriScoreValues[product.nutriscore_grade] || 0;

  // NOVA contribution (30% weight)
  const novaValues = { 1: 15, 2: 5, 3: -5, 4: -15 };
  score += novaValues[product.nova_group] || 0;

  // Eco-Score contribution (10% weight)
  const ecoValues = { a: 5, b: 2, c: 0, d: -2, e: -5 };
  score += ecoValues[product.ecoscore_grade] || 0;

  return Math.max(0, Math.min(100, score));
}

// 2. Find healthier alternatives
async function findHealthierAlternatives(
  product: OpenFoodFactsProduct
): Promise<OpenFoodFactsProduct[]> {
  const category = product.categories?.split(',')[0];
  const results = await searchProducts(category);

  // Filter for better Nutri-Score
  return results.filter(alt => {
    const grades = ['a', 'b', 'c', 'd', 'e'];
    return grades.indexOf(alt.nutriscore_grade) <
           grades.indexOf(product.nutriscore_grade);
  });
}

// 3. Additive detector
function detectAdditives(ingredients: string): string[] {
  const eNumbers = ingredients.match(/E\d{3,4}/gi) || [];
  return [...new Set(eNumbers.map(e => e.toUpperCase()))];
}
```

### For Skincare App:

Similar enhancements already possible with OpenBeautyFacts data.

## Conclusion

**We're already in the best position:**

✅ **Our Advantages:**
- Using the open, unrestricted OpenFoodFacts/OpenBeautyFacts APIs
- More comprehensive nutrition data than Yuka shows
- Additional metrics (NOVA, Eco-Score) Yuka doesn't display
- Full control over features and presentation
- No API restrictions or rate limits
- Free and open forever

❌ **Why NOT Yuka:**
- No public API available
- Proprietary database we can't access
- Less comprehensive data presentation
- Would need to reverse-engineer (against TOS)

**Recommendation:**
Instead of trying to integrate Yuka (impossible), we should **implement Yuka-inspired UX improvements** using our existing OpenFoodFacts data:

1. Simplified scoring display
2. Color-coded health ratings
3. "Find better" product suggestions
4. One-tap decision making

This gives users the simplicity of Yuka with the depth of OpenFoodFacts.

## Sources

- [How was Yuka's database created?](https://help.yuka.io/l/en/article/5a4z64amnk-how-was-the-database-created)
- [OpenFoodFacts data source tracking for Yuka](https://world.openfoodfacts.org/data-source/app-yuka)
- [SaaSHub comparison: OpenFoodFacts vs Yuka](https://www.saashub.com/compare-open-food-facts-vs-yuka)
- [Apps built on OpenFoodFacts](https://tms-outsource.com/blog/posts/apps-like-yuka/)
