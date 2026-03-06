# Cooking App Enhancement Plan

## Current State
- Backend working (Flask, port 5025)
- Mobile app working (Expo)
- Barcode scanning
- Pantry management
- Recipe browsing
- Multi-timer support
- OpenFoodFacts integration

## Missing Features
- Weekly meal planning UI
- Shopping list generation from meal plan
- Aldi deals integration
- Batch cooking scheduler
- Pantry sync with meal plan
- Water tracking
- Fitness calorie import

---

## Phase 1: Meal Planning (Dec 17-22) - AM BLOCKS

### Tasks
- [x] Weekly meal planner UI (Tinder-style swipe)
- [x] Recipe → shopping list aggregation (existing Flask endpoint)
- [x] Shopping list grouped by store section (existing Flask endpoint)
- [ ] Test with real meal planning

### Files Created/Modified
- `food-app-mobile/src/screens/MealPlanScreen.tsx` - NEW: Tinder-style swipe interface
- `food-app-mobile/src/services/api.ts` - Added meal planning API functions
- `food-app-mobile/src/types/index.ts` - Added MealPlan, SmartRecipe, SwipeData types

### Technical Approach (UPDATED - Uses Existing Backend)
1. **Swipe Interface**: Tinder-style card swiping (LEFT=skip, RIGHT=add, UP=meal prep)
2. **Smart Recipes**: Backend prioritizes recipes with ingredient overlap
3. **Meal Types**: Progress tabs for breakfast/lunch/dinner/snack
4. **Budget Tracking**: Optional budget with cost estimates from store prices
5. **Shopping List**: Auto-generated from plan ingredients minus pantry

---

## Phase 2: Polish (Dec 23-31) - AM BLOCKS

- [ ] Aldi deals integration (scraper or manual)
- [ ] Batch cooking scheduler
- [ ] Pantry sync with meal plan
- [ ] Shopping list export (shareable link or text)
- [ ] Water tracking UI

---

## Phase 3: Fitness Integration (Jan 20-26)

- [ ] Import calorie needs from fitness app
- [ ] Macro tracking dashboard
- [ ] Recipe suggestions based on goals

---

## API Endpoints (Already Exist in Flask Backend!)

```
GET  /api/meal-plans                     - List all meal plans
POST /api/meal-plans                     - Create new plan (day/week/month)
GET  /api/meal-plans/<id>                - Get plan with items
DELETE /api/meal-plans/<id>              - Delete plan

POST /api/meal-plans/<id>/swipe          - Handle swipe (left/right/up)
GET  /api/meal-plans/<id>/smart-recipes  - Get overlap-optimized recipes
GET  /api/meal-plans/<id>/shopping-list  - Generate shopping list
GET  /api/meal-plans/<id>/prep-schedule  - Get meal prep schedule
GET  /api/meal-plans/<id>/prep-tasks     - Get aggregated prep tasks
```

---

## Daily Progress Log

| Date | What Done | Blockers | Tomorrow |
|------|-----------|----------|----------|
| Dec 17 | Created MealPlanScreen with Tinder-style swipe. Added API functions to api.ts. Updated types. Discovered existing Flask meal planning endpoints. | None | Test swipe flow with real data, add shopping list navigation |
| Dec 18 | | | |
| Dec 19 | | | |
| Dec 20 | | | |
| Dec 21 | | | |
| Dec 22 | | | |
