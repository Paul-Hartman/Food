# Cross-Platform Pretest Results
**Date**: 2025-12-23
**Tester**: Claude (Automated Pretest)
**Purpose**: Identify what works, what's missing, and feature parity gaps before manual testing

---

## Executive Summary

### Web App Status
- **8 routes working** (200 OK)
- **6 routes missing** (404)
- **Core features present**: Recipes, Shopping, Pantry, Nutrition, Scanner, Testing

### Mobile App Status
- **7 bottom tab screens** (always accessible)
- **10 stack screens** (accessible via navigation)
- **17 total screens** implemented
- **All screens present in codebase**, need testing for functionality

### Feature Parity Analysis
- ✅ **4 features** have parity: Recipes, Shopping, Pantry, Nutrition
- ⚠️ **6 web routes** missing (but templates exist in templates/)
- 🆕 **9 mobile-only screens** (advanced features)
- 📋 **Detailed testing required** for all features

---

## Web App Routes - Detailed Status

### ✅ Working Routes (200 OK)

| Route | Purpose | Mobile Equivalent | Notes |
|-------|---------|-------------------|-------|
| `/` | Recipe browsing | RecipesScreen | Home page |
| `/shopping` | Shopping list | ShoppingScreen | Core feature |
| `/pantry` | Pantry inventory | PantryScreen | Core feature |
| `/nutrition` | Nutrition tracking | ComprehensiveNutritionScreen | Core feature |
| `/scanner` | Barcode scanner | ProductSearchScreen | Product lookup |
| `/testing` | Testing dashboard | N/A (web-only) | QA tool |
| `/meal` | Meal view | MealPlanScreen? | Need testing |
| `/cook/meal` | Cooking mode | CookingScreen | Active cooking |

### ❌ Missing Routes (404 - Templates exist but no routes)

| Route Attempted | Expected Template | Mobile Equivalent | Action Needed |
|----------------|-------------------|-------------------|---------------|
| `/meal_plan` | `meal_plan.html` | MealPlanScreen | Add Flask route |
| `/calendar_month` | `calendar_month.html` | CalendarScreen | Add Flask route |
| `/calendar_week` | `calendar_week.html` | CalendarScreen | Add Flask route |
| `/cook` | `cook.html` | CookingScreen | Add Flask route |
| `/swipe` | `swipe.html` | BulkReviewScreen | Add Flask route |
| `/discover_deck` | `discover_deck.html` | DecksScreen | Add Flask route |

### 📋 Templates Without Routes (From templates/ directory)

These templates exist but have no Flask routes defined:
- `alchemy.html` → Mobile: AlchemyScreen
- `family.html` → Mobile: FamilyScreen
- `game_dashboard.html` → Mobile: GameScreen
- `meal_prep.html` → Mobile: MealPrepScreen
- `personal_dashboard.html` → Mobile: AnalyticsScreen
- `interested.html` → No mobile equivalent
- `tonights_menu.html` → No mobile equivalent
- `swipe_simple.html` → Mobile: BulkReviewScreen
- `cooking_deck.html` → No mobile equivalent
- `discover.html` → Mobile: DecksScreen (different?)

---

## Mobile App Screens - Detailed Status

### 📱 Bottom Tab Navigation (7 Tabs - Always Accessible)

| Tab | Screen | Icon | Web Equivalent | Status |
|-----|--------|------|----------------|--------|
| Recipes | RecipesScreen | 🍞 | `/` | ✅ Both exist |
| Plan | MealPlanScreen | 📅 | `/meal_plan` (404) | ⚠️ Web missing route |
| Shopping | ShoppingScreen | 🛒 | `/shopping` | ✅ Both exist + offline |
| Pantry | PantryScreen | 🏠 | `/pantry` | ✅ Both exist |
| Nutrition | ComprehensiveNutritionScreen | 📊 | `/nutrition` | ✅ Both exist |
| Calendar | CalendarScreen | 📅 | `/calendar_month` (404) | ⚠️ Web missing route |
| Collections | DecksScreen | 📚 | `/discover_deck` (404) | ⚠️ Web missing route |

### 🔗 Stack Screens (Accessed via Navigation)

| Screen | Trigger | Web Equivalent | Status |
|--------|---------|----------------|--------|
| EnhancedRecipeDetailScreen | Tap recipe | `/recipe/<id>` | ✅ Both exist |
| CookingScreen | Start cooking | `/cook` (404) | ⚠️ Web missing route |
| MealPrepScreen | Navigate from plan | `/meal_prep.html` exists | ⚠️ Web missing route |
| FamilyScreen | Navigate | `/family.html` exists | ⚠️ Web missing route |
| GameScreen | Navigate | `/game_dashboard.html` exists | ⚠️ Web missing route |
| AnalyticsScreen | Navigate | `/personal_dashboard.html` exists | ⚠️ Web missing route |
| AlchemyScreen | Navigate | `/alchemy.html` exists | ⚠️ Web missing route |
| JournalScreen | Navigate | N/A | 🆕 Mobile-only |
| BulkReviewScreen | Navigate | `/swipe` (404) | ⚠️ Web missing route |
| PantryProductDetailScreen | Tap product | `/ingredient/<name>` | ✅ Both exist |

### 🆕 Mobile-Only Screens (No Web Equivalent)

These screens exist in mobile but have no web counterpart:
1. **JournalScreen** - Food diary/journal (mobile-only feature)
2. **ApothecaryScreen** - Not in navigation (unused?)
3. **ProductSearchScreen** - Advanced product search (web has `/scanner`)
4. **ComprehensiveNutritionScreen** - Advanced nutrition (web has simpler `/nutrition`)

---

## Feature Parity Gaps

### High Priority (Core Features Missing Web Routes)

These features have templates but no Flask routes:

1. **Meal Planning** (`/meal_plan`)
   - Template: `meal_plan.html` ✅
   - Mobile: MealPlanScreen ✅
   - Web route: ❌ Missing
   - **Action**: Add `@app.route('/meal_plan')` to Flask app

2. **Calendar** (`/calendar_month`, `/calendar_week`)
   - Templates: `calendar_month.html`, `calendar_week.html` ✅
   - Mobile: CalendarScreen ✅
   - Web routes: ❌ Missing
   - **Action**: Add routes to Flask app

3. **Cooking Mode** (`/cook`)
   - Template: `cook.html` ✅
   - Mobile: CookingScreen ✅
   - Web route: ❌ Missing (but `/cook/meal` works)
   - **Action**: Add route to Flask app

4. **Recipe Swipe/Review** (`/swipe`)
   - Templates: `swipe.html`, `swipe_simple.html` ✅
   - Mobile: BulkReviewScreen ✅
   - Web route: ❌ Missing
   - **Action**: Add route to Flask app

5. **Recipe Collections** (`/discover_deck`)
   - Templates: `discover_deck.html`, `cooking_deck.html` ✅
   - Mobile: DecksScreen ✅
   - Web route: ❌ Missing
   - **Action**: Add route to Flask app

### Medium Priority (Advanced Features)

6. **Meal Prep** (`/meal_prep`)
   - Template: `meal_prep.html` ✅
   - Mobile: MealPrepScreen ✅
   - Web route: ❌ Missing

7. **Family Features** (`/family`)
   - Template: `family.html` ✅
   - Mobile: FamilyScreen ✅
   - Web route: ❌ Missing

8. **Gamification** (`/game_dashboard`)
   - Template: `game_dashboard.html` ✅
   - Mobile: GameScreen ✅
   - Web route: ❌ Missing

9. **Recipe Creation** (`/alchemy`)
   - Template: `alchemy.html` ✅
   - Mobile: AlchemyScreen ✅
   - Web route: ❌ Missing

10. **Analytics Dashboard** (`/personal_dashboard`)
    - Template: `personal_dashboard.html` ✅
    - Mobile: AnalyticsScreen ✅
    - Web route: ❌ Missing

### Web-Only Features (No Mobile)

- `/testing` - Testing dashboard (QA tool, intentionally web-only)
- `/interested` - Recipe interest tracking
- `/tonights_menu` - Tonight's dinner suggestion
- `/discover` - Discovery page (different from DecksScreen?)

---

## Testing Priority Matrix

### Phase 1: Core Features (Must Work on Both Platforms) ⏰ 30 mins

Test these first - they're critical and have both web + mobile:

1. ✅ **Recipe Browsing**
   - Web: `/`
   - Mobile: RecipesScreen (🍞 tab)
   - Tests: Grid loads, search works, MealDB integration, detail pages

2. ✅ **Shopping List**
   - Web: `/shopping`
   - Mobile: ShoppingScreen (🛒 tab) + offline mode
   - Tests: Add/remove items, check off, Aldi sections, offline sync

3. ✅ **Pantry Management**
   - Web: `/pantry`
   - Mobile: PantryScreen (🏠 tab)
   - Tests: Add/edit/delete, search, expiring items, barcode scanner

4. ✅ **Nutrition Tracking**
   - Web: `/nutrition`
   - Mobile: ComprehensiveNutritionScreen (📊 tab)
   - Tests: Charts, manual entry, goals, analytics

### Phase 2: Add Missing Web Routes ⏰ 1 hour

Fix these by adding Flask routes (templates already exist):

5. ⚠️ **Meal Planning** - Add `/meal_plan` route
6. ⚠️ **Calendar Views** - Add `/calendar_month` and `/calendar_week` routes
7. ⚠️ **Cooking Mode** - Add `/cook` route
8. ⚠️ **Recipe Swipe** - Add `/swipe` route
9. ⚠️ **Collections** - Add `/discover_deck` route

### Phase 3: Advanced Features ⏰ 1-2 hours

Test these once core features are solid:

10. ⚠️ **Meal Prep** - Add route + test
11. ⚠️ **Family** - Add route + test
12. ⚠️ **Gamification** - Add route + test
13. ⚠️ **Alchemy** - Add route + test
14. ⚠️ **Analytics** - Add route + test

### Phase 4: Platform-Specific Features ⏰ 30 mins

Accept that some features are platform-specific:

15. 🌐 **Testing Dashboard** - Web-only (intentional)
16. 📱 **Journal** - Mobile-only (intentional)
17. 📱 **ApothecaryScreen** - Mobile (not in nav, might be unused?)

---

## Quick Wins - Add Missing Routes

Here are the Flask routes that need to be added to `backend/app.py`:

```python
@app.route('/meal_plan')
def meal_plan():
    return render_template('meal_plan.html')

@app.route('/calendar_month')
def calendar_month():
    return render_template('calendar_month.html')

@app.route('/calendar_week')
def calendar_week():
    return render_template('calendar_week.html')

@app.route('/cook')
def cook():
    return render_template('cook.html')

@app.route('/swipe')
def swipe():
    return render_template('swipe.html')

@app.route('/discover_deck')
def discover_deck():
    return render_template('discover_deck.html')

@app.route('/meal_prep')
def meal_prep():
    return render_template('meal_prep.html')

@app.route('/family')
def family():
    return render_template('family.html')

@app.route('/game_dashboard')
def game_dashboard():
    return render_template('game_dashboard.html')

@app.route('/alchemy')
def alchemy():
    return render_template('alchemy.html')

@app.route('/personal_dashboard')
def personal_dashboard():
    return render_template('personal_dashboard.html')
```

**Estimated time to add**: 5 minutes
**Impact**: Unlocks 11 features for cross-platform testing

---

## Recommended Testing Flow

1. **Add missing routes** (5 mins) ← Do this FIRST
2. **Test core features** (30 mins) - Recipes, Shopping, Pantry, Nutrition
3. **Test newly accessible features** (1 hour) - Meal plan, Calendar, Cooking, etc.
4. **Document issues** in testing dashboard as you find them
5. **Fix critical bugs** immediately
6. **Create GitHub issues** for non-critical items

---

## Success Metrics

After adding routes and testing:
- [ ] All 19 Flask routes return 200 OK
- [ ] All 7 mobile bottom tabs work
- [ ] All 10 mobile stack screens accessible
- [ ] Feature parity documented in testing dashboard
- [ ] Critical bugs identified and prioritized
- [ ] Offline mode working for Shopping (✅ already done)

---

## Next Steps

1. ✅ Add missing Flask routes (Quick win!)
2. ⏳ Test each feature systematically
3. ⏳ Mark results in testing dashboard
4. ⏳ Fix broken features
5. ⏳ Implement missing features
6. ⏳ Achieve feature parity

**Ready to start!** Begin by adding those missing routes, then systematic testing.
