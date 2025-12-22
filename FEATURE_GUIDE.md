# Budget & Expiry Tracking Features - Testing Guide

## ✅ Servers Running

**Backend:** `http://localhost:5025` (Flask)
**Mobile:** Expo Dev Server (check terminal output)

______________________________________________________________________

## 📱 WHERE TO FIND THE FEATURES

### Location: **Pantry Screen** (🏠 Tab in Bottom Navigation)

The Pantry screen is in the **bottom tab bar**, 4th icon from the left (house emoji 🏠).

______________________________________________________________________

## 🎯 WHAT YOU'LL SEE

### 1. **Total Pantry Value Banner** (Top of Screen)

```
┌──────────────────────────────────────┐
│   Total Pantry Value: €6.49          │  ← GREEN BANNER
└──────────────────────────────────────┘
```

**Shows:** Sum of all pantry items that have prices
**Location:** Below the subtitle "Track what you have at home"
**Only appears when:** At least one item has a price

______________________________________________________________________

### 2. **Enhanced Add Item Form**

```
┌──────────────────────────────────────┐
│ Add item...                           │  ← Item name
├────────────────────────┬─────────────┤
│ Expiry (YYYY-MM-DD)    │ €0.00       │  ← Two new fields
└────────────────────────┴─────────────┘
[📷 Scanner] [Add Button]
```

**New Fields:**

- **Left input:** Expiry date (format: 2025-12-25)
- **Right input:** Price in euros (e.g., 3.99)
- Both fields are **OPTIONAL** - you can leave them blank

______________________________________________________________________

### 3. **Item Rows with Expiry & Price**

```
🥛 Milk           2 L    €3.99   [2d]    [×]
                              ↑      ↑
                           price   expiry badge
```

**Expiry Badges (color-coded):**

- 🟢 **Green badge** (e.g., "12d") = More than 7 days left
- 🟡 **Yellow badge** (e.g., "5d") = 3-7 days remaining
- 🔴 **Red badge** (e.g., "1d") = Less than 3 days or expired
- **"Expired"** in red = Item is past expiry date

**Price Display:**

- Shows as **€X.XX** in green text
- Only appears if item has a price
- Located between quantity and expiry badge

______________________________________________________________________

### 4. **Enhanced Edit Modal**

When you tap an item's quantity, you get a modal:

```
┌──────────────────────────┐
│ Edit Item                 │
│ Milk                      │
│                           │
│ Quantity: [2]             │  ← Existing
│                           │
│ Expiry Date (Optional):   │  ← NEW
│ [2025-12-20]              │
│                           │
│ Price (Optional):         │  ← NEW
│ [€3.99]                   │
│                           │
│      [Cancel] [Save]      │
└──────────────────────────┘
```

______________________________________________________________________

## 🧪 HOW TO TEST

### Test 1: View Existing Data (READY NOW)

The database already has 2 test items with prices and expiry dates:

1. Open the mobile app
1. Go to **Pantry tab** (🏠 icon)
1. You should see:
   - **Green banner** showing "Total Pantry Value: €6.49"
   - **Bread** item (expires tomorrow - RED badge "1d")
   - **Test Milk** item (expires Dec 20 - YELLOW badge "2d")
   - Both items showing prices (€2.50 and €3.99)

______________________________________________________________________

### Test 2: Add New Item with Expiry & Price

1. In the **Add item** form at top:

   - Type "Cheese" in the name field
   - Type "2025-12-30" in the expiry field
   - Type "7.99" in the price field
   - Tap **[Add]**

1. **Expected Result:**

   - Item appears in the list
   - Shows **€7.99** next to quantity
   - Shows **green badge** "12d" (12 days until expiry)
   - **Total Value banner** updates to **€14.48**

______________________________________________________________________

### Test 3: Add Item WITHOUT Expiry/Price (Optional Fields)

1. In the **Add item** form:

   - Type "Salt" in the name field
   - Leave expiry and price fields **EMPTY**
   - Tap **[Add]**

1. **Expected Result:**

   - Item appears in the list normally
   - **No** price shown
   - **No** expiry badge shown
   - Total value banner stays the same (€14.48)

______________________________________________________________________

### Test 4: Edit Existing Item

1. Tap on the **quantity** of "Test Milk" (e.g., "2 L")

1. Edit modal opens with 3 fields:

   - **Quantity:** Change to 3
   - **Expiry Date:** Change to 2025-12-25
   - **Price:** Change to 4.50

1. Tap **[Save]**

1. **Expected Result:**

   - Quantity updates to 3 L
   - Expiry badge recalculates (now ~7 days = yellow)
   - Price updates to €4.50
   - **Total value** recalculates automatically

______________________________________________________________________

### Test 5: Expiry Badge Colors

Create items with different expiry dates to see all badge colors:

**Green badge (>7 days):**

- Add "Pasta" with expiry: 2026-01-01

**Yellow badge (3-7 days):**

- Add "Yogurt" with expiry: 2025-12-22

**Red badge (\<3 days):**

- Add "Lettuce" with expiry: 2025-12-19

**Expired (past date):**

- Add "Old Bread" with expiry: 2025-12-17

______________________________________________________________________

## 🔍 TROUBLESHOOTING

### "I don't see the Total Value banner"

- The banner only shows if **at least one item has a price**
- Try adding an item with a price (any number)
- Or edit an existing item and add a price

### "Expiry badges not showing"

- Badges only show for items **with** an `expires_at` date
- Items without expiry dates won't have badges (this is normal)

### "Can't add price or expiry"

- Make sure the mobile app reloaded after code changes
- Try force-closing the Expo app and reopening
- Check the backend is running on port 5025

### "Getting API errors"

- Backend URL in mobile app: Check `mobile/src/services/api.ts`
- Should point to your PC's IP or `localhost:5025`
- Try: `curl http://localhost:5025/api/pantry` to test backend

______________________________________________________________________

## 📂 FILES MODIFIED

### Backend (Flask)

- `backend/app.py`
  - Line 2837-2849: Modified GET /api/pantry (adds days_until_expiry)
  - Line 2888-2900: Modified POST /api/pantry/add (accepts price)
  - Line 2916-2937: Modified PUT /api/pantry/<id> (accepts price & expiry)
  - Line 2949-2965: NEW GET /api/pantry/total-value endpoint

### Mobile (React Native)

- `mobile/src/types/index.ts`

  - Line 93: Added `price: number | null` to PantryItem

- `mobile/src/services/api.ts`

  - Line 127: Added `price` param to addToPantry()
  - Lines 135-149: Updated updatePantryItem() for expiry & price
  - Lines 157-159: NEW getPantryTotalValue() method

- `mobile/src/screens/PantryScreen.tsx`

  - Lines 31-43: NEW getExpiryStatus() helper function
  - Lines 49-61: Added state for price, expiry, totalValue
  - Lines 72-77: Load total value on mount
  - Lines 92-102: Add item with price & expiry
  - Lines 200-227: Enhanced add form UI
  - Lines 249-276: Display expiry badges & prices
  - Lines 286-332: Enhanced edit modal with price & expiry
  - Lines 370-408: New styles (totalValueBanner, priceText, expiryBadge, etc.)

______________________________________________________________________

## 🎉 SUCCESS CRITERIA

You'll know it's working when you see:

- ✅ Green banner at top showing total pantry value
- ✅ Color-coded expiry badges on items
- ✅ Prices displayed next to quantities
- ✅ New input fields in add form (expiry & price)
- ✅ Edit modal has expiry & price fields
- ✅ All features are optional (items work without them)

______________________________________________________________________

## 🔗 Quick Links

**Test Backend API:**

```bash
# Get all pantry items (with prices & expiry)
curl http://localhost:5025/api/pantry | python -m json.tool

# Get total value
curl http://localhost:5025/api/pantry/total-value

# Add item with price & expiry
curl -X POST http://localhost:5025/api/pantry/add \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","quantity":1,"unit":"item","expires_at":"2025-12-25","price":5.99}'
```

**Current Test Data in Database:**

- ID 1: Test Milk - €3.99 - Expires 2025-12-20
- ID 2: Bread - €2.50 - Expires 2025-12-19

Total: **€6.49**

______________________________________________________________________

______________________________________________________________________

## 📱 NEW: Product Detail Pages & Trait System

### Location: **Pantry Screen → Tap any product card**

**Added:** 2025-12-19

### What's New

**1. Card UI for Pantry Items**

- Products now display in a 2-column grid using HoverableCard components
- Each card shows product image, name, quantity, and price
- Delete button (×) appears in top-left corner of each card

**2. Product Detail Pages**

- Tap any pantry product card to view full details
- Shows large product image at top
- Product name with category badge
- Basic info: quantity, price, expiry date
- Nutritional information section (calories, protein, carbs, fat, fiber)
- **Product Traits section** with smart badges

**3. Trait System**
The system automatically detects and displays trait badges:

**Category Traits:**

- 🥛 Dairy - Milk, cheese, yogurt
- 🥩 Meat - Chicken, beef, pork
- 🥕 Vegetable - Carrots, lettuce, etc.
- 🍎 Fruit - Apples, bananas, etc.
- 🥤 Drink - Beverages
- 🧂 Condiment - Sauces, spices
- 🌾 Grain - Bread, pasta, rice
- 📦 Other - Everything else

**Auto-Detected Traits:**

- 📅 **Daily Use** - Appears if daily tracking is enabled
- ⏰ **Has Expiry Date** - Shows for items with expiration dates
- 💪 **High Protein** - Auto-appears if >10g protein per 100g
- 🌾 **High Fiber** - Auto-appears if >5g fiber per 100g

### How to Test

**Test 1: View Product Cards**

1. Go to Pantry screen (🏠 tab)
1. Products display in 2-column grid
1. Each shows image (if available), name, quantity, price

**Test 2: Navigate to Detail Page**

1. Tap any product card
1. See full product details screen with:
   - Large image at top
   - Category badge (e.g., "🥛 dairy")
   - Quantity, price, expiry info
   - Nutritional facts (per 100g)
   - Traits badges at bottom

**Test 3: Check Traits**

1. On detail page, scroll to "Product Traits" section
1. Should see category badge
1. If product has >10g protein, see "💪 High Protein"
1. If product has >5g fiber, see "🌾 High Fiber"

**Test 4: Scan Product with Image**

1. Tap camera button in Pantry
1. Scan a barcode (mayonnaise, milk, etc.)
1. Product adds with image from OpenFoodFacts database
1. Image displays on card in pantry grid
1. Tap card to see image on detail page

### Files Added/Modified

**New Files:**

- `mobile/src/screens/PantryProductDetailScreen.tsx` - Full product detail page
- `backend/migrations/007_add_pantry_images.sql` - Image URL column
- `backend/backfill_pantry_images.py` - Utility to backfill images

**Modified Files:**

- `mobile/src/types/index.ts` - Added PantryProductDetail route type
- `mobile/src/navigation/AppNavigator.tsx` - Added detail screen to navigation
- `mobile/src/screens/PantryScreen.tsx` - Changed to card grid, navigate to detail
- `mobile/src/services/api.ts` - Added getIngredientById() method
- `mobile/src/services/openfoodfacts.ts` - Extract image_url from products
- `backend/app.py` - Save image_url when adding pantry items

### Database Changes

```sql
-- Migration 007: Add image support
ALTER TABLE pantry ADD COLUMN image_url TEXT;
CREATE INDEX IF NOT EXISTS idx_pantry_image_url ON pantry(image_url);
```

### Known Issues

- Scanner may still fire multiple times per scan (investigating)
- Type error "expected boolean got string" reported but not reproduced
- Metro bundler dependency errors on emulator (works on physical device)

______________________________________________________________________

**Last Updated:** 2025-12-19 23:59
**Backend Port:** 5025
**Status:** ✅ Product details & traits implemented, awaiting testing confirmation
