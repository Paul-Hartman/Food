# Food App - Meal Planning & Nutrition Tracking

A complete meal planning system with Flask backend and React Native mobile app.

## Structure

```
Food/
├── backend/              # Flask API (port 5025)
│   ├── app.py            # Main server
│   ├── food.db           # SQLite database (37MB)
│   └── requirements.txt
├── mobile/               # React Native Expo app
│   ├── src/
│   │   ├── screens/      # MealPlanScreen, RecipesScreen, PantryScreen
│   │   ├── services/     # API client, OpenFoodFacts
│   │   └── components/   # Reusable UI components
│   ├── package.json
│   └── app.json
├── FEATURES.json         # Feature checklist (read by Mission Control)
└── README.md
```

## Quick Start

### Deploy to TestFlight (iPhone)

```bash
cd Food/mobile
npm run deploy
# Wait 30 min → Check email → Update in TestFlight
```

**📱 Current Version:** 1.0.1 on TestFlight

### Backend Server

```bash
cd Food/backend
python app.py
# Runs at http://localhost:5025
```

**Or double-click:** `backend/start_server.bat` (Windows)

### Development (Local Testing)

```bash
cd Food/mobile
npm install
npx expo start
# Scan QR with Expo Go app
```

## Access URLs

- **Flask Web App**: http://192.168.2.38:5025 (or http://localhost:5025)
- **Expo Web/Mobile**: http://localhost:8081
- **Mission Control**: http://localhost:5002/project/food-app
- **API Health**: http://localhost:5025/health

**Note:** Both apps show identical recipe detail pages. The Expo app embeds Flask pages via iframe for MealDB recipes to ensure feature parity.

## Features

### Recipe Management

- Browse and search recipes with images
- Step-by-step cooking instructions
- Nutritional information (calories, macros)
- Recipe cards with cooking mode

### Pantry Tracking

- Card-based UI for pantry items
- Location tracking (pantry/fridge/freezer)
- Expiration date warnings
- Quantity management

### Barcode Scanner (Mobile)

- Native camera barcode scanning
- Open Food Facts API integration
- Automatic product info lookup
- Nutri-Score ratings (A-E)

### Meal Planning

- Tinder-style swipe UI for meal selection
- Weekly meal calendar
- Shopping list generation (planned)

### MealDB Integration

- Access to 300+ recipes from TheMealDB
- Recipe cards with images, cuisine, and category
- Step-by-step cooking instructions
- Ingredient cards with nutritional tags
- Both Flask and Expo apps show the same content

## API Endpoints

### Recipes

- `GET /api/recipes` - List all recipes
- `GET /api/recipes/<id>` - Get recipe details
- `GET /api/recipes/<id>/image` - Get recipe image
- `POST /api/recipes` - Create recipe

### Pantry

- `GET /api/pantry` - List pantry items
- `POST /api/pantry` - Add item
- `PUT /api/pantry/<id>` - Update item
- `DELETE /api/pantry/<id>` - Remove item

### Products (Open Food Facts)

- `GET /api/products/barcode/<code>` - Lookup by barcode
- `GET /api/products/search?q=<query>` - Search products

### Meal Plan

- `GET /api/mealplan` - Get current meal plan
- `POST /api/mealplan` - Add meal to plan

### MealDB

- `GET /api/mealdb/batch-random` - Get random MealDB recipes
- `GET /api/mealdb/recipe/<id>` - Get MealDB recipe details
- `GET /api/mealdb/categories` - List all categories
- `GET /api/mealdb/search?q=<query>` - Search MealDB recipes

## Database Schema

Key tables in `food.db`:

- `recipes` - Recipe details, instructions, nutrition
- `pantry_items` - User's pantry inventory
- `meal_plans` - Scheduled meals
- `ingredients` - Ingredient master list

## Mobile App Screens

| Screen              | Description                |
| ------------------- | -------------------------- |
| RecipesScreen       | Browse/search recipes      |
| MealPlanScreen      | Tinder-style meal planning |
| PantryScreen        | View/manage pantry items   |
| ProductSearchScreen | Search Open Food Facts     |

## Technologies

### Backend

- Python 3.11+
- Flask
- SQLite
- Open Food Facts API

### Mobile

- React Native
- Expo
- expo-camera (barcode scanning)
- React Navigation

## Integration with Profile Service

The Food App can sync data to the unified Profile Service:

```typescript
import { ProfileClient } from '@lotus/api/profile-client';

const profile = new ProfileClient();

// Log a meal
await profile.logMeal({ recipeName: 'Pasta', calories: 500 });

// Add to pantry
await profile.addToPantry({ name: 'Eggs', quantity: 12 });
```

## Documentation

| Document | Description |
|----------|-------------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | TestFlight deployment guide |
| [AUTOMATION_PLAN.md](./AUTOMATION_PLAN.md) | Offline mode, auto-start, CI/CD |
| [OFFLINE_ARCHITECTURE.md](./OFFLINE_ARCHITECTURE.md) | SQLite offline-first design |
| [TESTFLIGHT_SETUP.md](./mobile/TESTFLIGHT_SETUP.md) | Apple Developer setup |

## Status

**Priority:** HIGH (Primary daily-use app)
**Latest Deploy:** Version 1.0.1 (2025-12-23)
**Deployment:** GitHub + TestFlight (90-day builds)

See `FEATURES.json` for detailed feature checklist.
