# Quick Start Guide - Meal Planner App

## Get Started in 5 Minutes

### Step 1: Start the Server

```bash
cd "C:\Users\paulh\Documents\UoPprojects\JavaProjects\Lotus-Eater Machine\Food\untitled"
venv\Scripts\activate
python manage.py runserver
```

The server will start at: http://127.0.0.1:8000/

### Step 2: Access Admin Panel

Visit: http://127.0.0.1:8000/admin/

Login credentials:

- **Username**: admin
- **Password**: admin123

### Step 3: Add Initial Data

To make the app functional, you need to add some basic data. Here's the recommended order:

#### 1. Measurement Units (Required)

Go to: Admin → Measurement Units → Add

**Essential units to add:**

| Name       | Abbreviation | Unit Type | Conversion to Base |
| ---------- | ------------ | --------- | ------------------ |
| gram       | g            | weight    | 1                  |
| kilogram   | kg           | weight    | 1000               |
| ounce      | oz           | weight    | 28.3495            |
| pound      | lb           | weight    | 453.592            |
| milliliter | ml           | volume    | 1                  |
| liter      | L            | volume    | 1000               |
| cup        | cup          | volume    | 236.588            |
| tablespoon | tbsp         | volume    | 14.787             |
| teaspoon   | tsp          | volume    | 4.929              |
| piece      | pc           | count     | - (leave blank)    |

#### 2. Dietary Tags (Optional but Recommended)

Go to: Admin → Dietary Tags → Add

Add these common tags:

- **vegan** (icon: 🌱)
- **vegetarian** (icon: 🥬)
- **gluten-free** (icon: 🌾❌)
- **dairy-free** (icon: 🥛❌)
- **keto** (icon: 🥑)
- **paleo** (icon: 🍖)
- **low-carb** (icon: 🔻)

#### 3. Common Ingredients

Go to: Admin → Ingredients → Add

Start with staples:

**Grains:**

- Flour (category: grain)
- Rice (category: grain)
- Pasta (category: grain)

**Proteins:**

- Chicken breast (category: protein)
- Eggs (category: protein, allergens: ["eggs"])
- Ground beef (category: protein)

**Dairy:**

- Milk (category: dairy, allergens: ["dairy"])
- Butter (category: dairy, allergens: ["dairy"])
- Cheese (category: dairy, allergens: ["dairy"])

**Vegetables:**

- Onion (category: vegetable)
- Garlic (category: vegetable)
- Tomato (category: vegetable)
- Carrot (category: vegetable)

**Seasonings:**

- Salt (category: spice)
- Black pepper (category: spice)
- Olive oil (category: oil)

#### 4. Create Your First Recipe

Go to: Admin → Recipes → Add

**Example: Simple Scrambled Eggs**

- Name: Scrambled Eggs
- Description: Quick and easy scrambled eggs
- Instructions:
  ```
  1. Crack eggs into a bowl and whisk
  2. Heat butter in pan over medium heat
  3. Pour eggs and stir gently until cooked
  4. Season with salt and pepper
  ```
- Prep time: 2 minutes
- Cook time: 5 minutes
- Servings: 2
- Difficulty: Easy
- Cuisine: American

**After saving, add ingredients:**
Click "Add another Recipe ingredient" inline:

- Ingredient: Eggs, Quantity: 4, Unit: piece
- Ingredient: Butter, Quantity: 10, Unit: gram
- Ingredient: Salt, Quantity: 1, Unit: gram
- Ingredient: Black pepper, Quantity: 0.5, Unit: gram

______________________________________________________________________

## Alternative: Use Django Shell to Bulk Create

For faster setup, you can use the Django shell:

```bash
python manage.py shell
```

Then paste this code:

```python
from recipes.models import MeasurementUnit, DietaryTag, Ingredient

# Create measurement units
units_data = [
    {
        "name": "gram",
        "abbreviation": "g",
        "unit_type": "weight",
        "conversion_to_base": 1,
    },
    {
        "name": "kilogram",
        "abbreviation": "kg",
        "unit_type": "weight",
        "conversion_to_base": 1000,
    },
    {
        "name": "cup",
        "abbreviation": "cup",
        "unit_type": "volume",
        "conversion_to_base": 236.588,
    },
    {
        "name": "tablespoon",
        "abbreviation": "tbsp",
        "unit_type": "volume",
        "conversion_to_base": 14.787,
    },
    {
        "name": "teaspoon",
        "abbreviation": "tsp",
        "unit_type": "volume",
        "conversion_to_base": 4.929,
    },
    {"name": "piece", "abbreviation": "pc", "unit_type": "count"},
]

for unit_data in units_data:
    MeasurementUnit.objects.get_or_create(**unit_data)

print("✓ Measurement units created!")

# Create dietary tags
tags_data = [
    {"name": "vegan", "icon": "🌱"},
    {"name": "vegetarian", "icon": "🥬"},
    {"name": "gluten-free", "icon": "🌾❌"},
    {"name": "dairy-free", "icon": "🥛❌"},
    {"name": "keto", "icon": "🥑"},
]

for tag_data in tags_data:
    DietaryTag.objects.get_or_create(**tag_data)

print("✓ Dietary tags created!")

# Create common ingredients
ingredients_data = [
    {"name": "Eggs", "category": "protein", "allergens": ["eggs"]},
    {"name": "Butter", "category": "dairy", "allergens": ["dairy"]},
    {"name": "Salt", "category": "spice"},
    {"name": "Black Pepper", "category": "spice"},
    {"name": "Olive Oil", "category": "oil"},
    {"name": "Onion", "category": "vegetable"},
    {"name": "Garlic", "category": "vegetable"},
    {"name": "Tomato", "category": "vegetable"},
]

for ing_data in ingredients_data:
    Ingredient.objects.get_or_create(defaults=ing_data, name=ing_data["name"])

print("✓ Common ingredients created!")
print("\nAll done! You can now start using the app.")
```

______________________________________________________________________

## Test the Features

### 1. Create Your User Profile

1. In admin, go to "User Profiles" → Add
1. Select your user (admin)
1. Set:
   - Country: DE (Germany)
   - City: Berlin
   - Postal Code: 10243 (Friedrichshain)
   - Preferred measurement system: Metric (grams)
   - Cooking skill level: Choose yours
1. Add any dietary restrictions

### 2. Create a Meal Plan

1. Go to "Meal Plans" → Add
1. Set week starting date (e.g., next Monday)
1. Save
1. Add meals inline:
   - Date: Choose a day
   - Meal type: Dinner
   - Recipe: Select your recipe
   - Servings: 2
1. Save

### 3. Generate a Grocery List

1. Go to "Grocery Lists" → Add
1. Select user and meal plan
1. Save
1. In Django shell:
   ```python
   from recipes.models import GroceryList

   gl = GroceryList.objects.last()
   gl.generate_from_meal_plan(gl.meal_plan)
   ```
1. Refresh the grocery list in admin - items are now populated!

### 4. Track Your Pantry

1. Go to "User Pantries" → Add
1. Add ingredients you have:
   - User: admin
   - Ingredient: Eggs
   - Quantity: 12
   - Unit: piece
   - Location: fridge

### 5. Mark a Meal as Cooked

1. Go to your Meal Plan Recipe
1. Check the "cooked" checkbox
1. Save
1. Check your pantry - ingredients are automatically deducted!

______________________________________________________________________

## Useful Management Commands

### Import REWE Data (when available)

```bash
python manage.py import_rewe_data --limit 100
```

### Create Sample Data

```bash
python manage.py shell < scripts/create_sample_data.py
```

### Check Database

```bash
python manage.py dbshell
```

### Make Migrations (after model changes)

```bash
python manage.py makemigrations
python manage.py migrate
```

______________________________________________________________________

## Troubleshooting

### Server won't start

- Make sure virtual environment is activated: `venv\Scripts\activate`
- Check if another server is running on port 8000

### Can't log into admin

- Username: `admin`
- Password: `admin123`
- If forgotten, create new superuser: `python manage.py createsuperuser`

### Database errors

- Delete `db.sqlite3` and run `python manage.py migrate` again
- This will reset all data (use for development only)

### REWE import fails

- Data source may not have current date available
- This is normal for development/testing
- The feature will work when production data is available

______________________________________________________________________

## Next Steps

Once you have basic data:

1. **Build the frontend** - Create templates and views
1. **Add more recipes** - Import from TheMealDB
1. **Test meal planning** - Create a full week plan
1. **Test grocery lists** - Verify pantry deduction works
1. **Add Aldi products** - Manually enter weekly deals

______________________________________________________________________

**Happy Cooking! 🍳**

For questions or issues, check the full documentation in `README.md` and `PROGRESS.md`.
