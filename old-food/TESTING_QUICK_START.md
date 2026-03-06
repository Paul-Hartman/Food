# Food App Testing - Quick Start Guide

## ✅ Server Status: RUNNING on http://localhost:5025

All key routes tested and responding with 200 OK.

---

## Priority Testing Order

Test these in order of importance for your crafting + flip-book goals:

### 1. CORE COOKING EXPERIENCE (Critical)
Start with these to test the flip-book interface:

- **Flip-Book Cooking**: http://localhost:5025/cook
  - Test 3D card stack, swipe navigation, timers

- **Cook Specific Recipe**: http://localhost:5025/cook/mealdb/52772
  - Test cooking interface with a real recipe (Teriyaki Chicken)

### 2. INGREDIENT TRANSFORMATION SYSTEM (Your Unique Feature)
This is your crafting system foundation:

- **Transformation Discovery**: http://localhost:5025/ingredient/transformations
  - Search for "milk" to see fermentation transformations
  - Check if chemistry explanations toggle
  - Test if instructions expand

- **Ingredient Detail**: http://localhost:5025/ingredient/milk
  - See what transformations are available

### 3. ALCHEMY / POTION BREWING (Gamified Crafting)
Your magical interface for ingredient mixing:

- **Alchemy Interface**: http://localhost:5025/alchemy
  - Test 5-slot cauldron
  - Try dragging ingredients
  - Test brewing methods
  - Check potion preview

### 4. RECIPE SWIPE DISCOVERY (Key UX)
Tinder-style recipe discovery:

- **General Swipe**: http://localhost:5025/swipe
  - Swipe left (discard), right (like), up (tonight's menu)

- **Breakfast Swipe**: http://localhost:5025/swipe/breakfast
  - Test meal-type filtering

- **Liked Recipes**: http://localhost:5025/interested
  - See recipes you've saved

- **Tonight's Menu**: http://localhost:5025/cooking-deck
  - Recipes you swiped up on

### 5. PANTRY & SHOPPING (Daily Use)
Essential for practical use:

- **Pantry**: http://localhost:5025/pantry
  - Add/edit items, check expiry dates

- **Shopping List**: http://localhost:5025/shopping
  - Organized by Aldi sections

- **Barcode Scanner**: http://localhost:5025/scanner
  - Test product lookup

### 6. OTHER FEATURES (Test if you use them)

- **Meal Planning**: http://localhost:5025/meal_plan
- **Nutrition Dashboard**: http://localhost:5025/nutrition
- **Personal Dashboard**: http://localhost:5025/me
- **Family/Game**: http://localhost:5025/family
- **Calendar**: http://localhost:5025/calendar/week
- **Testing Dashboard**: http://localhost:5025/testing

---

## Quick Test Commands (API)

Open these URLs in your browser or use curl:

```bash
# Health check
curl http://localhost:5025/health

# List all recipes
curl http://localhost:5025/api/recipes

# Pantry inventory
curl http://localhost:5025/api/pantry

# Shopping list
curl http://localhost:5025/api/shopping

# Alchemy ingredients
curl http://localhost:5025/api/alchemy/ingredients

# Transformations for ingredient ID 1
curl http://localhost:5025/api/ingredients/1/transformations
```

---

## Testing Workflow

1. **Open** `WEB_FEATURE_TESTING_CHECKLIST.md` in a text editor
2. **Visit** each URL in your browser
3. **Test** the functionality listed in the checklist
4. **Add feedback** in the `[FEEDBACK]` sections
5. **Rate** each feature: ✅ Works Great | ⚠️ Needs Work | ❌ Broken | ⏭️ Skipped

---

## What to Look For

### For Flip-Book Cooking:
- Do cards stack in 3D?
- Does swipe navigation work smoothly?
- Are animations at 60fps?
- Do timers work correctly?
- Can you see all ingredients?

### For Transformations:
- Does searching for "milk" show yogurt/kefir/cheese?
- Are chemistry explanations visible?
- Is equipment listed?
- Can you see difficulty levels?

### For Alchemy:
- Can you drag 5 ingredients into the cauldron?
- Does the potion preview show effects?
- Are brewing methods (ferment, brew, blend) available?
- Does the "Brew" button do something?

### For Swipe:
- Do recipe cards load with images?
- Does swiping feel responsive?
- Do liked recipes save to /interested?
- Does swipe-up add to /cooking-deck?

---

## Focus Areas Based on Your Goals

**For Ingredients + Methods + Tools Crafting:**
1. Test `/ingredient/transformations` thoroughly
2. Check if tools are mentioned in transformations
3. See if methods are listed (fermentation, baking, etc.)
4. Note what's missing for full crafting system

**For Deck-Based Flip-Book Cooking:**
1. Test `/cook` interface extensively
2. Check if 3D card stack works
3. Test swipe navigation
4. Note any mobile-specific issues (if testing on phone)

---

## Server Info

- **Port**: 5025
- **Running**: Yes (background process)
- **Log File**: `C:\Users\paulh\AppData\Local\Temp\claude\C--Users-paulh-Documents-Lotus-Eater-Machine-food\tasks\b75a0ef.output`

To stop the server later, just close the terminal or use Ctrl+C if running in foreground.

---

## Next Steps

1. Start testing with the **Core Cooking Experience**
2. Move to **Transformation System**
3. Test **Alchemy Interface**
4. Fill out the checklist as you go
5. When done, share the checklist with Claude
6. Claude will create a prioritized fix list

**Happy testing!** 🧪🍳
