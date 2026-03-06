# Food App Web Feature Testing Checklist

**Instructions**: Test each feature and add feedback in the `[FEEDBACK]` section. Rate: ✅ Works Great | ⚠️ Needs Work | ❌ Broken | ⏭️ Skipped

**Test Server**: http://localhost:5025 (✅ SERVER IS RUNNING)

**Progress**: [ ] Not Started | [ ] Testing In Progress | [ ] Complete

---

## 1. Core Cooking Experience

### 1.1 Homepage / Recipe Discovery
- **URL**: http://localhost:5025/
- **Test**:
  - [ ] Page loads without errors
  - [ ] Navigation menu works
  - [ ] Can access main features from homepage
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 1.2 Flip-Book Cooking Interface
- **URL**: http://localhost:5025/cook
- **Test**:
  - [ ] 3D card stack displays properly
  - [ ] Can swipe left/right to navigate steps
  - [ ] Step instructions are clear
  - [ ] Timer buttons appear on timed steps
  - [ ] Ingredient drop zones work
  - [ ] Card animations are smooth
  - [ ] Progress indicator shows current step
  - [ ] Tips/warnings display in yellow boxes
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 1.3 Cooking from MealDB Recipe
- **URL**: http://localhost:5025/cook/mealdb/52772 (example: Teriyaki Chicken)
- **Test**:
  - [ ] Recipe loads from MealDB API
  - [ ] Steps broken down properly
  - [ ] Images display
  - [ ] Can navigate through cooking steps
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 1.4 Multi-Timer System
- **URL**: While cooking (within /cook interface)
- **Test**:
  - [ ] Can start timer from a step
  - [ ] Timer counts down correctly
  - [ ] Can pause/resume timer
  - [ ] Multiple timers can run simultaneously
  - [ ] Timers persist if you navigate away
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 2. Recipe Swipe Discovery

### 2.1 Tinder-Style Recipe Swipe
- **URL**: http://localhost:5025/swipe
- **Test**:
  - [ ] Recipe cards display with images
  - [ ] Can swipe left (discard) and right (like)
  - [ ] Can swipe up (add to tonight's menu)
  - [ ] New recipes load after swipe
  - [ ] Card animations smooth
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 2.2 Meal Type Specific Swipe
- **URL**: http://localhost:5025/swipe/breakfast (try: breakfast, lunch, dinner, snack)
- **Test**:
  - [ ] Shows recipes filtered by meal type
  - [ ] Can switch between meal types
  - [ ] Swipe actions work
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 2.3 Interested Recipes (Liked List)
- **URL**: http://localhost:5025/interested
- **Test**:
  - [ ] Shows all recipes you've swiped right on
  - [ ] Can remove recipes from list
  - [ ] Can click to view recipe detail
  - [ ] Can add to cooking deck
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 2.4 Tonight's Menu / Cooking Deck
- **URL**: http://localhost:5025/cooking-deck
- **Test**:
  - [ ] Shows recipes added via swipe-up
  - [ ] Organized by meal type
  - [ ] Can mark recipes as completed
  - [ ] Can remove recipes from deck
  - [ ] 3D card hover effects work
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 3. Ingredient Transformation System

### 3.1 Ingredient Transformations Discovery
- **URL**: http://localhost:5025/ingredient/transformations
- **Test**:
  - [ ] Can search for an ingredient (try "milk")
  - [ ] Transformation cards show input → output
  - [ ] Process type displayed (fermentation, baking, etc.)
  - [ ] Equipment requirements listed
  - [ ] Difficulty level shown
  - [ ] Chemistry explanations toggle works
  - [ ] Instructions accordion expands
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 3.2 Process Detail View
- **URL**: http://localhost:5025/process/detail (click from transformation card)
- **Test**:
  - [ ] Process name and description clear
  - [ ] Chemistry tab shows scientific explanation
  - [ ] Temperature and pH ranges displayed
  - [ ] Equipment capabilities listed
  - [ ] Step-by-step instructions detailed
  - [ ] Yield and quality metrics shown
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 3.3 Ingredient Detail Page
- **URL**: http://localhost:5025/ingredient/milk (try any ingredient)
- **Test**:
  - [ ] Ingredient info displays
  - [ ] Nutrition data shown
  - [ ] Related recipes listed
  - [ ] Transformations available
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 4. Alchemy / Potion Brewing

### 4.1 Alchemy Interface
- **URL**: http://localhost:5025/alchemy
- **Test**:
  - [ ] 5-slot cauldron displays
  - [ ] Can drag/select ingredients into slots
  - [ ] Ingredient categories work (Herbs, Spices, etc.)
  - [ ] Brewing method selector (ferment, brew, blend)
  - [ ] Potion preview shows before brewing
  - [ ] Effect visualization (energy, health, focus)
  - [ ] "Brew Potion" button works
  - [ ] Ingredient cards show images
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 5. Pantry Management

### 5.1 Pantry Inventory
- **URL**: http://localhost:5025/pantry
- **Test**:
  - [ ] Pantry items display in list/grid
  - [ ] Can add new items
  - [ ] Can update quantities
  - [ ] Can set expiry dates
  - [ ] Can organize by location (fridge, freezer, cupboard)
  - [ ] Low stock warnings appear
  - [ ] Expired items highlighted
  - [ ] Search/filter works
  - [ ] Can delete items
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 5.2 Barcode Scanner
- **URL**: http://localhost:5025/scanner
- **Test**:
  - [ ] Scanner interface loads
  - [ ] Can enter barcode manually
  - [ ] Barcode lookup returns product info
  - [ ] Nutrition data auto-populated
  - [ ] Can add scanned item to pantry
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 6. Shopping List

### 6.1 Shopping List Management
- **URL**: http://localhost:5025/shopping
- **Test**:
  - [ ] Shopping list items display
  - [ ] Organized by Aldi sections
  - [ ] Can add items manually
  - [ ] Can check off items
  - [ ] Can edit quantities
  - [ ] Can delete items
  - [ ] Can clear checked items
  - [ ] Can generate from recipes
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 7. Meal Planning

### 7.1 Weekly Meal Planner
- **URL**: http://localhost:5025/meal_plan
- **Test**:
  - [ ] Weekly view displays
  - [ ] Can add recipes to specific days
  - [ ] Can assign to breakfast/lunch/dinner
  - [ ] Can drag recipes between days
  - [ ] Can remove recipes
  - [ ] Can generate shopping list from plan
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 7.2 Meal Planning with Swipe
- **URL**: http://localhost:5025/plan (if meal plan exists)
- **Test**:
  - [ ] Can create meal plan
  - [ ] Swipe interface for adding recipes
  - [ ] Can see prep schedule
  - [ ] Shopping list generation works
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 8. Calendar & Scheduling

### 8.1 Calendar Week View
- **URL**: http://localhost:5025/calendar/week
- **Test**:
  - [ ] Week calendar displays
  - [ ] Meals scheduled on calendar
  - [ ] Family events show (if family feature used)
  - [ ] Can add events
  - [ ] Can navigate weeks
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 8.2 Calendar Month View
- **URL**: http://localhost:5025/calendar/month
- **Test**:
  - [ ] Month calendar displays
  - [ ] Events and meals shown on days
  - [ ] Can click days to see details
  - [ ] Can navigate months
  - [ ] Busy days highlighted
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 9. Family / Multi-User Features

### 9.1 Family Dashboard
- **URL**: http://localhost:5025/family
- **Test**:
  - [ ] Can add family members
  - [ ] Member profiles display
  - [ ] Can set dietary restrictions per member
  - [ ] Can assign cooking tasks
  - [ ] Family schedule integration
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 9.2 Game Dashboard
- **URL**: http://localhost:5025/game
- **Test**:
  - [ ] Gamification elements display
  - [ ] Family member cards/avatars
  - [ ] Can view leaderboard
  - [ ] Skills/achievements visible
  - [ ] Can navigate to member-specific views
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 9.3 Member-Specific Game View
- **URL**: http://localhost:5025/game/member/1 (replace 1 with member ID)
- **Test**:
  - [ ] Member dashboard loads
  - [ ] Needs displayed (hunger, health, energy)
  - [ ] Skills shown with progress
  - [ ] Achievements listed
  - [ ] Recipe collection visible
  - [ ] Can cook meals as member
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 10. Nutrition Tracking

### 10.1 Nutrition Dashboard
- **URL**: http://localhost:5025/nutrition
- **Test**:
  - [ ] Daily nutrition summary displays
  - [ ] Calories, protein, carbs, fat shown
  - [ ] Micronutrients tracked
  - [ ] Daily goals/targets displayed
  - [ ] Progress bars work
  - [ ] Can log consumed meals
  - [ ] Historical data view available
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 11. Personal Dashboard

### 11.1 Personal Analytics Dashboard
- **URL**: http://localhost:5025/me
- **Test**:
  - [ ] Personal stats display
  - [ ] Nutrition insights shown
  - [ ] Favorite recipes listed
  - [ ] Cooking history visible
  - [ ] Smart suggestions provided
  - [ ] Can set targets/goals
  - [ ] Can rate meals
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 12. Testing Dashboard

### 12.1 Testing & QA Dashboard
- **URL**: http://localhost:5025/testing
- **Test**:
  - [ ] Dashboard loads
  - [ ] Build versions listed
  - [ ] Test results displayed
  - [ ] Can view test details
  - [ ] Can export results
  - [ ] Can create GitHub issues from tests
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 13. Recipe Detail Pages

### 13.1 Local Recipe Detail
- **URL**: Click any recipe from swipe/interested (or use /recipe/1)
- **Test**:
  - [ ] Recipe name and image display
  - [ ] Description readable
  - [ ] Ingredients list with quantities
  - [ ] Cooking steps numbered
  - [ ] Prep/cook time shown
  - [ ] Servings displayed
  - [ ] Difficulty level
  - [ ] Nutrition info
  - [ ] Can add to favorites
  - [ ] Can add to meal plan
  - [ ] Can start cooking
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 13.2 MealDB Recipe Detail
- **URL**: http://localhost:5025/recipe/mealdb/52772 (Teriyaki Chicken)
- **Test**:
  - [ ] Recipe loads from MealDB
  - [ ] All fields populate correctly
  - [ ] Video embeds if available
  - [ ] Can start cooking
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 14. API Testing (Developer)

### 14.1 Key API Endpoints
Test these with curl/Postman or browser:

- **GET** http://localhost:5025/api/recipes
  - [ ] Returns JSON recipe list
  - [ ] Includes pagination
  - [ ] Filters work (if parameters added)

- **GET** http://localhost:5025/api/pantry
  - [ ] Returns pantry inventory
  - [ ] Shows quantities and expiry

- **GET** http://localhost:5025/api/shopping
  - [ ] Returns shopping list
  - [ ] Organized by Aldi sections

- **GET** http://localhost:5025/api/nutrition/today
  - [ ] Returns today's nutrition data
  - [ ] Shows calories, macros, micros

- **GET** http://localhost:5025/api/alchemy/ingredients
  - [ ] Returns alchemy ingredients
  - [ ] Includes effects data

- **GET** http://localhost:5025/api/ingredients/1/transformations
  - [ ] Returns transformations for ingredient
  - [ ] Includes process details

- **GET** http://localhost:5025/health
  - [ ] Returns 200 OK
  - [ ] Confirms app is running

**[API FEEDBACK]**: ⏭️
```

```

---

## 15. Performance & UX

### 15.1 Load Times
- **Test**:
  - [ ] Homepage loads in <2 seconds
  - [ ] Recipe pages load quickly
  - [ ] Images optimized
  - [ ] Swipe transitions smooth (60fps)
  - [ ] No lag when filtering/searching
- **[FEEDBACK]**: ⏭️
  ```

  ```

### 15.2 Visual Design
- **Test**:
  - [ ] Color scheme consistent
  - [ ] Fonts readable
  - [ ] Spacing/padding comfortable
  - [ ] Buttons clearly clickable
  - [ ] Icons intuitive
  - [ ] Mobile-responsive (test in mobile view)
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 16. Error Handling

### 16.1 Edge Cases
- **Test**:
  - [ ] Visit /recipe/99999 (non-existent recipe) - graceful error?
  - [ ] Search with no results - helpful message?
  - [ ] Add invalid barcode - error handling?
  - [ ] Try to cook with missing ingredients - warning?
  - [ ] 404 page exists and is helpful
- **[FEEDBACK]**: ⏭️
  ```

  ```

---

## 17. Features Found But Not Tested

These routes exist but need exploration:

- `/meal` - Meal view (purpose unknown)
- `/cook/meal` - Cook from meal (different from /cook?)
- `/meal_prep` - Meal prep interface
- `/discover` - Alternative discovery interface?
- `/discover_deck` - Deck-based discovery
- `/schedule` - Scheduling interface
- `/game/skills/<member_id>` - Skills detail
- `/game/achievements` - Achievements list
- `/game/collection/<member_id>` - Recipe collection

**[NOTES]**: ⏭️
```
What are these pages for?
```

---

## SUMMARY

**Total Features Tested**: ____ / 50+

**Priority Fixes Needed**:
1.
2.
3.

**Nice-to-Have Improvements**:
1.
2.
3.

**Features That Work Great**:
1.
2.
3.

**Features That Are Broken**:
1.
2.
3.

**Overall Impression**:
```
[Your thoughts here]
```

**Highest Priority to Fix**:
```
[What absolutely must be fixed first?]
```

---

## Next Steps

1. **Save this file** with your feedback
2. **Share it with Claude** when done
3. **I'll create a prioritized fix list** based on your ratings
4. **We'll tackle the highest-impact issues first**

**Testing Tips**:
- Start with Core Cooking Experience (most important)
- Test Alchemy and Transformations (your unique features)
- Try the Swipe interface (key UX differentiator)
- Leave the Family/Game features for later if not using them
- Focus on what matters most to your daily use
