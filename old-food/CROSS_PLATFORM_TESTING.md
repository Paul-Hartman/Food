# Cross-Platform Testing Matrix - Food App

**Goal**: Achieve complete feature parity between Web App and Mobile App

**Testing Dashboard**: http://localhost:5025/testing
**Web App**: http://localhost:5025/
**Mobile App**: Expo Go on Android emulator + iPhone

______________________________________________________________________

## Core Features Comparison

| Feature                       | Web Route               | Mobile Screen              | Status       |
| ----------------------------- | ----------------------- | -------------------------- | ------------ |
| **Recipe Browsing**           | `/` (index.html)        | RecipesScreen              | ⏳ Test Both |
| **Recipe Detail**             | `/recipe/<id>`          | EnhancedRecipeDetailScreen | ⏳ Test Both |
| **MealDB Recipe Detail**      | `/recipe_mealdb/<id>`   | EnhancedRecipeDetailScreen | ⏳ Test Both |
| **Shopping List**             | `/shopping`             | ShoppingScreen             | ⏳ Test Both |
| **Pantry**                    | `/pantry`               | PantryScreen               | ⏳ Test Both |
| **Pantry Product Detail**     | `/ingredient/<barcode>` | PantryProductDetailScreen  | ⏳ Test Both |
| **Nutrition Tracking**        | `/nutrition`            | NutritionScreen            | ⏳ Test Both |
| **Meal Planning**             | `/meal_plan`            | MealPlanScreen             | ⏳ Test Both |
| **Calendar (Month)**          | `/calendar_month`       | CalendarScreen             | ⏳ Test Both |
| **Calendar (Week)**           | `/calendar_week`        | CalendarScreen             | ⏳ Test Both |
| **Cooking Mode**              | `/cook`                 | CookingScreen              | ⏳ Test Both |
| **MealDB Cooking**            | `/cook_mealdb/<id>`     | CookingScreen              | ⏳ Test Both |
| **Bulk Review/Swipe**         | `/swipe`                | BulkReviewScreen           | ⏳ Test Both |
| **Recipe Collections/Decks**  | `/discover_deck`        | DecksScreen                | ⏳ Test Both |
| **Family Features**           | `/family`               | FamilyScreen               | ⏳ Test Both |
| **Game/Gamification**         | `/game_dashboard`       | GameScreen                 | ⏳ Test Both |
| **Alchemy (Recipe Creation)** | `/alchemy`              | AlchemyScreen              | ⏳ Test Both |
| **Meal Prep**                 | `/meal_prep`            | MealPrepScreen             | ⏳ Test Both |
| **Personal Dashboard**        | `/personal_dashboard`   | AnalyticsScreen?           | ⏳ Test Both |
| **Barcode Scanner**           | `/scanner`              | ProductSearchScreen        | ⏳ Test Both |

______________________________________________________________________

## Testing Workflow

### Phase 1: Baseline Testing (Today)

**Goal**: Identify what works and what's broken on each platform

1. **Open both platforms side-by-side**:

   - Desktop: Web app in browser (http://localhost:5025)
   - Emulator: Mobile app in Expo Go
   - iPhone: Mobile app in Expo Go (when ready)

1. **Test each feature on BOTH platforms**:

   - Navigate to feature on web
   - Navigate to same feature on mobile
   - Compare functionality
   - Document differences in testing dashboard

1. **Mark test results**:

   - **Pass** ✅: Works perfectly on BOTH platforms
   - **Fail** ❌: Broken on one or both platforms
   - **Needs Work** ⚠️: Works but different behavior between platforms
   - **Not Tested** ⏳: Haven't tested yet

### Phase 2: Feature Parity Analysis

**Goal**: Identify what features are missing on each platform

1. **Web-only features** (missing on mobile):

   - List them
   - Decide: Should mobile have it?
   - If yes, add to mobile backlog

1. **Mobile-only features** (missing on web):

   - List them
   - Decide: Should web have it?
   - If yes, add to web backlog

1. **Different implementations**:

   - List features that work differently
   - Decide: Which approach is better?
   - Standardize on the better approach

### Phase 3: Fix & Implement

**Goal**: Fix broken features and implement missing ones

1. **Fix broken features** (highest priority):

   - Start with features that are completely broken
   - Fix on both platforms
   - Re-test to confirm

1. **Implement missing features**:

   - Start with core features (shopping, pantry, recipes)
   - Add to platform that's missing it
   - Test on both platforms

1. **Standardize implementations**:

   - Align behavior between platforms
   - Ensure consistent UX
   - Test thoroughly

### Phase 4: Offline Support

**Goal**: Ensure mobile app works offline

1. **Test offline mode** (mobile only):

   - Shopping list ✅ (already implemented)
   - Pantry (needs implementation)
   - Favorites (needs implementation)
   - Cached recipes (needs implementation)

1. **Implement sync**:

   - Background sync when online
   - Conflict resolution
   - Sync status indicators

______________________________________________________________________

## Testing Checklist by Feature

### 1. Recipe Browsing

**Web App (`/`)**:

- [ ] Recipe grid loads
- [ ] Search filters recipes
- [ ] Category filters work
- [ ] Recipe cards clickable
- [ ] Images load
- [ ] MealDB integration works
- [ ] Empty state shows

**Mobile App (RecipesScreen)**:

- [ ] Recipe grid loads
- [ ] Search filters recipes
- [ ] Category filters work
- [ ] Recipe cards clickable
- [ ] Images load
- [ ] MealDB integration works
- [ ] Empty state shows

**Parity Issues**:

- [ ] Document any differences

______________________________________________________________________

### 2. Shopping List

**Web App (`/shopping`)**:

- [ ] Shopping list loads
- [ ] Add item manually
- [ ] Remove item
- [ ] Check off item
- [ ] Clear checked items
- [ ] Aldi section grouping
- [ ] Add from recipe
- [ ] Persistent after refresh

**Mobile App (ShoppingScreen)**:

- [ ] Shopping list loads
- [ ] Add item manually
- [ ] Remove item
- [ ] Check off item
- [ ] Clear checked items
- [ ] Aldi section grouping
- [ ] Add from recipe
- [ ] Persistent after refresh
- [ ] Works offline ✅
- [ ] Syncs when online ✅

**Parity Issues**:

- [ ] Mobile has offline support, web doesn't (expected)
- [ ] Document any other differences

______________________________________________________________________

### 3. Pantry

**Web App (`/pantry`)**:

- [ ] Pantry items load
- [ ] Search filters items
- [ ] Add item manually
- [ ] Update quantity
- [ ] Delete item
- [ ] Barcode scanner link
- [ ] Product detail page
- [ ] Expiring items shown

**Mobile App (PantryScreen)**:

- [ ] Pantry items load
- [ ] Search filters items
- [ ] Add item manually
- [ ] Update quantity
- [ ] Delete item
- [ ] Barcode scanner integration
- [ ] Product detail page
- [ ] Expiring items shown
- [ ] Works offline (needs testing)
- [ ] Syncs when online (needs testing)

**Parity Issues**:

- [ ] Document any differences

______________________________________________________________________

### 4. Nutrition Tracking

**Web App (`/nutrition`)**:

- [ ] Daily stats display
- [ ] Weekly chart shows
- [ ] Add manual entry
- [ ] Edit entry
- [ ] Goal tracking
- [ ] Chart interactions

**Mobile App (NutritionScreen)**:

- [ ] Daily stats display
- [ ] Weekly chart shows
- [ ] Add manual entry
- [ ] Edit entry
- [ ] Goal tracking
- [ ] Chart interactions

**Parity Issues**:

- [ ] Document any differences

______________________________________________________________________

### 5. Meal Planning

**Web App (`/meal_plan`)**:

- [ ] Weekly view loads
- [ ] Add meal to day
- [ ] Remove meal
- [ ] Navigate weeks
- [ ] Persistence

**Mobile App (MealPlanScreen)**:

- [ ] Weekly view loads
- [ ] Add meal to day
- [ ] Remove meal
- [ ] Swipe navigation
- [ ] Persistence

**Parity Issues**:

- [ ] Navigation might be different (swipe vs buttons)
- [ ] Document any differences

______________________________________________________________________

### 6. Calendar

**Web App (`/calendar_month` + `/calendar_week`)**:

- [ ] Month view loads
- [ ] Week view loads
- [ ] Planned meals show
- [ ] Navigate months
- [ ] Navigate weeks
- [ ] Tap date to add meal
- [ ] Today indicator

**Mobile App (CalendarScreen)**:

- [ ] Month view loads
- [ ] Week view (if exists)
- [ ] Planned meals show
- [ ] Navigate months
- [ ] Navigate weeks
- [ ] Tap date to add meal
- [ ] Today indicator

**Parity Issues**:

- [ ] Web has separate month/week pages, mobile might combine
- [ ] Document any differences

______________________________________________________________________

### 7. Cooking Mode

**Web App (`/cook` + `/cook_mealdb`)**:

- [ ] Recipe steps display
- [ ] Step navigation
- [ ] Timer functionality
- [ ] Multiple timers
- [ ] Screen stays awake
- [ ] Voice commands (if implemented)

**Mobile App (CookingScreen)**:

- [ ] Recipe steps display
- [ ] Step navigation
- [ ] Timer functionality
- [ ] Multiple timers
- [ ] Screen stays awake
- [ ] Voice commands (if implemented)

**Parity Issues**:

- [ ] Screen wake lock might work differently
- [ ] Document any differences

______________________________________________________________________

### 8. Recipe Detail

**Web App (`/recipe/<id>` + `/recipe_mealdb/<id>`)**:

- [ ] Recipe details load
- [ ] Ingredients list
- [ ] Cooking instructions
- [ ] Nutrition info
- [ ] Add to meal plan
- [ ] Add to shopping list
- [ ] Share recipe

**Mobile App (EnhancedRecipeDetailScreen)**:

- [ ] Recipe details load
- [ ] Ingredients list
- [ ] Cooking instructions
- [ ] Nutrition info
- [ ] Add to meal plan
- [ ] Add to shopping list
- [ ] Share recipe

**Parity Issues**:

- [ ] Document any differences

______________________________________________________________________

### 9. Bulk Review/Swipe

**Web App (`/swipe`)**:

- [ ] Recipe queue loads
- [ ] Swipe to approve
- [ ] Swipe to reject
- [ ] Undo last action
- [ ] Empty state

**Mobile App (BulkReviewScreen)**:

- [ ] Recipe queue loads
- [ ] Swipe to approve
- [ ] Swipe to reject
- [ ] Undo last action
- [ ] Empty state

**Parity Issues**:

- [ ] Swipe gestures might feel different
- [ ] Document any differences

______________________________________________________________________

### 10. Recipe Collections/Decks

**Web App (`/discover_deck` + `/cooking_deck`)**:

- [ ] Collections display
- [ ] Create new deck
- [ ] Add recipe to deck
- [ ] Remove from deck
- [ ] Deck thumbnails

**Mobile App (DecksScreen)**:

- [ ] Collections display
- [ ] Create new deck
- [ ] Add recipe to deck
- [ ] Remove from deck
- [ ] Deck thumbnails

**Parity Issues**:

- [ ] Document any differences

______________________________________________________________________

## Feature Parity Gaps (To Be Filled)

### Web-Only Features

- [ ] `/personal_dashboard` - Personal analytics dashboard
- [ ] `/tonights_menu` - Tonight's dinner suggestion
- [ ] `/interested` - Recipe interest tracking
- [ ] `/meal` - Single meal view
- [ ] `/discover` - Recipe discovery page

### Mobile-Only Features

- [ ] `ComprehensiveNutritionScreen` - Advanced nutrition analytics
- [ ] `JournalScreen` - Food journal/diary
- [ ] `ProductSearchScreen` - Advanced product search

### Features That Need Investigation

- [ ] Is ApothecaryScreen unique to mobile?
- [ ] Is AnalyticsScreen the mobile equivalent of personal_dashboard?
- [ ] Are there web equivalents of mobile-only screens?

______________________________________________________________________

## Testing Strategy

### Desktop Testing (Web App)

1. Open http://localhost:5025/testing in browser
1. Open http://localhost:5025/ in another tab
1. Test each feature from the list above
1. Mark results in testing dashboard
1. Add notes about issues

### Mobile Testing (Android Emulator)

1. Food app already open in Expo Go
1. Test each feature from the list above
1. Mark results in testing dashboard (use desktop browser)
1. Add notes about issues
1. Test offline mode for applicable features

### Mobile Testing (iPhone)

1. Connect to http://192.168.2.38:8081 in Expo Go
1. Repeat mobile tests
1. Compare to Android results
1. Note any iOS-specific issues

______________________________________________________________________

## Success Criteria

- [ ] All core features work on both platforms
- [ ] Offline mode works on mobile for key features
- [ ] No critical bugs on either platform
- [ ] Feature parity documented and justified
- [ ] User experience is consistent where appropriate
- [ ] Platform-specific features are intentional, not accidental

______________________________________________________________________

## Next Steps

1. **Start testing now**: Begin with Recipe Browsing (first feature)
1. **Use testing dashboard**: Mark each test as you go
1. **Document issues**: Add detailed notes for every problem
1. **Fix as you go**: Fix critical issues immediately
1. **Export failed tests**: Use markdown export for bug tracking
1. **Create GitHub issues**: For all bugs that need fixing

______________________________________________________________________

**Ready to start cross-platform testing!** 🚀

Let's go feature by feature, testing web and mobile side-by-side.
