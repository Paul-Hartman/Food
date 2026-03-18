# Food — STATUS

> Last updated: 2026-03-17
> Entity cards: `domain-food-app`, `plan-integration-report-foodfood-app`, `plan-food-app-backend-planning`
> Category: Wellness (data-only)

## Purpose
Recipe database and meal planning system with Flask backend and mobile app scaffold. Contains an 80MB recipe database and food planning tools.

## Current State
| Metric | Value |
|--------|-------|
| Status | DORMANT |
| Maturity | 30% |
| Tests | None |
| Last commit | 2026-03-06 |
| VPS service | No |

## Tech Stack
| Component | Technology | Port | Entry Point |
|-----------|-----------|------|-------------|
| Backend | Python/Flask | unknown | `backend/` |
| Mobile | React Native | — | `food-app-mobile/` |
| Web | JavaScript | — | `food-app/` |

## Databases
| Name | Path | Size | Tables | Notes |
|------|------|------|--------|-------|
| food.db | backend/food.db | 80 MB | — | Main recipe database |
| food_app.db | backend/food_app.db | 143 KB | — | App state |
| food_backup | backend/food_backup_demo_ready_*.db | 38 MB | — | Demo-ready backup |
| kitchen_planning.db | backend/kitchen_planning.db | 0 bytes | — | Empty |
| food.db | food-app/food.db | 38 MB | — | Duplicate of backend |
| food_app.db | food-app/food_app.db | 0 bytes | — | Empty |

## Entity Cards Owned
- `domain-food-app` (discovered)
- `plan-integration-report-foodfood-app` (active)
- `plan-food-app-backend-planning` (idea)

## Future Ideas
- [ ] `idea-recipe-ai` — AI-powered recipe suggestions
- [ ] `idea-meal-prep-mode` — Batch meal preparation planner
- [ ] `idea-nutrition-goals` — Nutritional goal tracking
- [ ] `idea-grocery-delivery` — Grocery delivery integration
- [ ] `idea-social-recipes` — Social recipe sharing
- [ ] `idea-restaurant-integration` — Restaurant menu integration
- [ ] `idea-companion-planting` — Kitchen herb/garden companion planting

## Integration Points
| Connected To | Direction | Mechanism | Notes |
|-------------|-----------|-----------|-------|
| LifeBalance | → | Shared food.db | Calorie/nutrition tracking |
| Wellness | → | Planned | Nutrition as wellness metric |

## Reorganization Notes
### Could absorb from elsewhere:
- `body/food/` mirror directory has identical databases

### Content that better fits elsewhere:
- Could be a sub-domain of Wellness or LifeBalance

### Duplicate data/logic to deduplicate:
- `backend/food.db` and `food-app/food.db` are near-identical (80MB vs 38MB)
- `body/food/` is exact mirror of this folder

## Completed Work
- Backend with recipe database (80MB of recipes)
- Mobile app scaffold
- Demo-ready backup created

## Known Issues
- Multiple copies of food.db across folders
- kitchen_planning.db is empty
- No tests

## Next Steps
- [ ] Decide canonical home: standalone or merge into Wellness
- [ ] Deduplicate food.db copies
- [ ] Add tests for backend
