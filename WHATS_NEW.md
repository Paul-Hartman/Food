# What's New - Receipt Scanning & Budget Tracking with AI Image Processing! 🎯

## 🚀 Latest Updates (November 2025)

### 1. AI-Powered Product Image Upload 📸

**Automatic background removal for product photos!**

- Upload product images with **automatic AI background removal**
- Professional-looking product photos from casual snapshots
- Smart image optimization (resize, compress, format conversion)
- Three powerful endpoints:
  - `/api/products/upload-image/` - Update existing product images
  - `/api/products/add-with-image/` - Create products with images
  - `/api/receipt-items/update-image/` - Add images to receipt items

**How it works:**

```bash
# Upload a photo and get a professional product image
curl -X POST http://localhost:8000/api/products/upload-image/ \
  -F "barcode=1234567890" \
  -F "image=@product_photo.jpg" \
  -F "remove_background=true"
```

**Features:**

- AI-powered background removal using rembg
- Automatic image optimization (max 800x800px)
- Transparent PNG output
- Works with any image format
- Optional background removal control

______________________________________________________________________

### 2. Complete Receipt Scanning & Budget Tracking System 🧾💰

**Track all your household spending with receipt scanning!**

**Receipt Management:**

- Upload receipt images with purchase details
- Store metadata: store name, date, total, tax, payment method
- Categorize receipts into expense categories
- Extract line items with prices and quantities
- Product matching for receipt items
- Receipt verification workflow

**11 Expense Categories with Budgets:**

- 🛒 Groceries & Food - $150/week
- 👕 Clothing & Accessories - $50/week
- 🧹 Cleaning Supplies - $20/week
- 💄 Personal Care & Cosmetics - $30/week
- ⚕️ Health & Medical - $25/week
- 🏠 Household Items - $40/week
- 🎬 Entertainment - $50/week
- 💻 Electronics - $25/week
- 🚗 Automotive - $50/week
- 🐾 Pet Supplies - $30/week
- 📦 Other - No budget

**Budget Tracking:**

- Automatic weekly spending calculation
- Budget vs. actual comparison
- Over-budget warnings with visual indicators
- Spending trends by category
- Receipt and item counts
- Historical tracking

**API Endpoints:**

- POST `/api/receipts/upload/` - Upload receipt with image
- POST `/api/receipts/add-items/` - Add line items to receipt
- GET `/api/receipts/` - Get receipts with filtering
- GET `/api/expense-categories/` - Get categories with budgets
- GET `/api/weekly-spending/` - Get weekly spending summary

**Example Workflow:**

1. Take photo of receipt
1. Upload with store name, date, and total
1. Categorize as "Groceries"
1. Add line items (or extract manually)
1. System auto-updates weekly spending
1. View budget status: $75 spent of $150 (50%)

______________________________________________________________________

### 3. Universal Household Inventory System 🏠

**Expanded from meal planning to complete household tracking!**

**Product Database:**

- Track ANY household item (food, cosmetics, tools, electronics, etc.)
- Multi-source barcode lookup:
  - Local cache (fastest)
  - Open Food Facts API (food items)
  - Open Beauty Facts API (cosmetics)
- Automatic product caching
- Missing barcode reporting

**Organization System:**

- 11 product categories with subcategories
- Hierarchical storage locations (room → furniture → shelf)
- 8 item purposes (daily, emergency, seasonal, etc.)
- Enhanced pantry with location and purpose tracking

**New Models:**

- `Product` - Universal product storage
- `ProductCategory` - Hierarchical categorization
- `StorageLocation` - Multi-level storage tracking
- `ItemPurpose` - Use-case tagging
- `MissingBarcodeReport` - Track unknown products
- `ExpenseCategory` - Budget categories
- `Receipt` - Receipt records with images
- `ReceiptItem` - Line items with prices
- `WeeklySpending` - Automatic budget tracking

______________________________________________________________________

## Previous Updates

# What's New - Automatic Data Population & Nutrition Tracking!

## 🎉 Major Updates

### 1. Automatic Initial Data Population ✨

You asked "why can't you just add all this stuff?" - **Done!**

Now you can populate everything with a single command:

```bash
python manage.py populate_initial_data
```

This automatically creates:

- **14 Measurement Units** (grams, cups, tablespoons, etc.)
- **10 Dietary Tags** (vegan, vegetarian, gluten-free, keto, etc.)
- **33 Common Ingredients** with full nutritional data
- **1 Sample Recipe** (Scrambled Eggs) to get you started

All the data you need to start using the app is now in your database!

______________________________________________________________________

### 2. Automatic Nutritional Calculation by Portion 🥗

You asked for nutritional information based on portion - **Done!**

**Features:**

- Automatically calculates nutrition for any recipe
- Shows **per serving** and **total recipe** values
- Tracks: Calories, Protein, Carbs, Fat
- Adjusts calculations for any number of servings
- Displayed in admin interface
- Works with all measurement units

**How it Works:**

1. **Ingredients have nutritional data per 100g**

   - All 33 common ingredients now include calories, protein, carbs, and fat
   - Example: Eggs have 155 kcal, 13g protein, 1.1g carbs, 11g fat per 100g

1. **Recipes calculate automatically**

   - Converts all ingredients to grams
   - Multiplies by nutritional values
   - Sums up for total recipe
   - Divides by servings

1. **Example: Scrambled Eggs (2 servings)**

   - **Per Serving:** 191 kcal, 13g protein, 1.1g carbs, 15g fat
   - **Total Recipe:** 382 kcal, 26g protein, 2.2g carbs, 30g fat

______________________________________________________________________

## 📊 New Features in Admin Interface

### Recipe List View

- Now shows **Calories/Serving** column
- Quick view of nutritional content

### Recipe Detail View

- New **"Nutritional Information"** section (collapsible)
- Beautiful formatted display with:
  - Per serving breakdown
  - Total recipe values
  - Professional styling

**Example Display:**

```
Nutritional Information

Per Serving (2 servings total):
Calories:     191 kcal
Protein:      13g
Carbs:        1.1g
Fat:          15g

Total Recipe:
Calories:     382 kcal
Protein:      26g
Carbs:        2.2g
Fat:          30g
```

______________________________________________________________________

## 🍳 What's Already in Your Database

After running `populate_initial_data`, you now have:

### Measurement Units (14)

- **Weight:** gram, kilogram, milligram, ounce, pound
- **Volume:** milliliter, liter, cup, tablespoon, teaspoon, fluid ounce
- **Other:** piece, pinch, to taste

### Dietary Tags (10)

🌱 Vegan | 🥬 Vegetarian | 🌾 Gluten-Free | 🥛 Dairy-Free
🥑 Keto | 🍖 Paleo | 🔻 Low-Carb | ☪️ Halal
✡️ Kosher | 🐟 Pescatarian

### Common Ingredients (33) - All with Nutritional Data!

**Proteins:**

- Eggs (155 kcal/100g)
- Chicken Breast (165 kcal/100g)
- Ground Beef (250 kcal/100g)
- Salmon (208 kcal/100g)
- Tofu (76 kcal/100g)

**Dairy:**

- Milk, Butter, Cheese, Greek Yogurt

**Grains:**

- White Rice, Pasta, Bread, Flour, Oats

**Vegetables:**

- Onion, Garlic, Tomato, Carrot, Potato, Broccoli, Spinach, Bell Pepper

**Fruits:**

- Apple, Banana, Lemon

**Oils & Seasonings:**

- Olive Oil, Vegetable Oil, Salt, Black Pepper, Paprika, Cumin

**Sweeteners:**

- Sugar, Honey

### Sample Recipe (1)

**Scrambled Eggs** - Vegetarian, Gluten-Free

- 4 eggs
- 10g butter
- Salt and pepper
- Prep: 2 min | Cook: 5 min | Servings: 2
- **191 calories per serving**

______________________________________________________________________

## 🚀 How to Use

### 1. Run the Server

```bash
cd "C:\Users\paulh\Documents\UoPprojects\JavaProjects\Lotus-Eater Machine\Food\untitled"
venv\Scripts\activate
python manage.py runserver
```

### 2. Access Admin

http://127.0.0.1:8000/admin/

- Username: `admin`
- Password: `admin123`

### 3. Explore the Data

- Click **Recipes** → See the Scrambled Eggs example
- Expand **"Nutritional Information"** to see calculated nutrition
- Click **Ingredients** → See all 33 ingredients with nutrition data
- Click **Dietary Tags** → See all available tags

### 4. Create Your Own Recipes

1. Go to **Recipes** → **Add Recipe**
1. Fill in name, description, instructions
1. Add ingredients (with quantities and units)
1. Save
1. **Nutrition is automatically calculated!**

______________________________________________________________________

## 🔬 Testing Nutrition Calculation

You can test nutrition calculation from the Django shell:

```bash
python manage.py shell
```

```python
from recipes.models import Recipe

# Get the scrambled eggs recipe
recipe = Recipe.objects.first()

# Get nutrition summary
print(recipe.get_nutrition_summary())

# Get nutrition for different servings
nutrition = recipe.calculate_nutrition(servings=4)
print(f"For 4 servings: {nutrition['calories']} cal/serving")

# Get default nutrition
nutrition = recipe.nutrition_per_serving
print(nutrition)
```

**Output:**

```
Per serving (2 servings):
Calories: 190.8 kcal
Protein: 13.0g
Carbs: 1.1g
Fat: 15.1g

Total recipe:
Calories: 381.7 kcal
Protein: 26.1g
Carbs: 2.2g
Fat: 30.1g
```

______________________________________________________________________

## 💡 How Nutrition Calculation Works

### Step 1: Ingredient Nutritional Data

Each ingredient has values **per 100g**:

```python
Ingredient: Eggs
-calories_per_100g: 155
-protein_per_100g: 13
-carbs_per_100g: 1.1
-fat_per_100g: 11
```

### Step 2: Recipe Ingredients with Quantities

```python
RecipeIngredient:
- 4 pieces eggs
- 10 grams butter
```

### Step 3: Automatic Conversion

- System converts quantities to grams
- For "pieces", uses standard weights (egg = ~50g)
- Multiplies by nutritional values per 100g

### Step 4: Calculation

```
4 eggs × 50g = 200g total
200g ÷ 100 × 155 kcal = 310 kcal from eggs

10g butter ÷ 100 × 717 kcal = 71.7 kcal from butter

Total = 381.7 kcal
Per serving (÷2) = 190.8 kcal
```

______________________________________________________________________

## 📝 Adding Custom Ingredients with Nutrition

When adding new ingredients, include nutritional data:

1. Go to **Ingredients** → **Add Ingredient**
1. Fill in basic info (name, category)
1. Scroll to **"Nutritional Information (Optional)"**
1. Add values per 100g:
   - Calories per 100g
   - Protein per 100g
   - Carbs per 100g
   - Fat per 100g
1. Save

**Where to find nutritional data:**

- USDA FoodData Central: https://fdc.nal.usda.gov/
- Nutritionix: https://www.nutritionix.com/
- MyFitnessPal: https://www.myfitnesspal.com/
- Package labels (convert to per 100g)

______________________________________________________________________

## 🎯 What This Enables

With automatic nutrition calculation, you can now:

✅ **Track your daily calorie intake**

- See exactly how many calories in each meal
- Plan meals to hit calorie targets

✅ **Monitor macronutrients**

- Track protein for muscle building
- Monitor carbs for keto/low-carb diets
- Track fat intake

✅ **Make informed choices**

- Compare recipes by nutritional content
- Choose healthier alternatives
- Balance your weekly meal plan

✅ **Scale recipes accurately**

- Calculate nutrition for any number of servings
- Adjust portions based on your needs

______________________________________________________________________

## 🔮 Future Enhancements (Coming Soon)

- **Micronutrients:** Vitamins and minerals tracking
- **Meal plan nutrition:** Weekly totals and daily averages
- **Nutrition goals:** Set and track targets
- **Charts and graphs:** Visual nutrition tracking
- **Export reports:** PDF nutrition summaries

______________________________________________________________________

## 📚 Command Reference

```bash
# Populate all initial data (run once)
python manage.py populate_initial_data

# Import REWE grocery data
python manage.py import_rewe_data --limit 100

# Start development server
python manage.py runserver

# Create database backup
python manage.py dumpdata > backup.json

# Access Django shell
python manage.py shell
```

______________________________________________________________________

## 🎉 Summary

**Before:** You had to manually create everything
**Now:** One command populates the entire database!

**Before:** No nutritional information
**Now:** Automatic calculation for every recipe!

**You asked, I delivered!** 🚀

The app is now ready to use with:

- 14 measurement units
- 10 dietary tags
- 33 common ingredients (with nutrition data)
- 1 sample recipe (with calculated nutrition)
- Full admin interface
- Automatic nutrition calculation

**Just run the server and start creating recipes!**

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/admin/

Happy cooking! 🍳
