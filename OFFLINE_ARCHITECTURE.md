# Food App - Offline-First Architecture

## Core Principle

**The app works perfectly without any server. The server is just a bonus for syncing new recipes.**

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Mobile App (iPhone)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐          ┌──────────────┐                 │
│  │              │          │              │                 │
│  │  UI Layer    │◄────────►│  SQLite DB   │                 │
│  │              │          │  (Primary)   │                 │
│  └──────┬───────┘          └──────────────┘                 │
│         │                                                    │
│         │ Optional Sync                                      │
│         ▼                                                    │
│  ┌──────────────┐                                            │
│  │              │                                            │
│  │  Sync Layer  │◄────┐                                     │
│  │              │     │                                      │
│  └──────────────┘     │                                      │
│                       │                                      │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        │ Internet (Optional)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (PC)                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  - Fetches new recipes from MealDB API                       │
│  - Provides additional recipe search                         │
│  - Syncs user data across devices (future)                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## SQLite Database Schema

### Tables

#### `recipes`
```sql
CREATE TABLE recipes (
  id INTEGER PRIMARY KEY,
  mealdb_id TEXT UNIQUE,
  name TEXT NOT NULL,
  category TEXT,
  area TEXT,  -- Cuisine
  instructions TEXT,
  thumbnail_url TEXT,
  youtube_url TEXT,
  source_url TEXT,
  tags TEXT,  -- Comma-separated
  ingredients TEXT,  -- JSON array
  measures TEXT,  -- JSON array
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  synced_at TIMESTAMP  -- Last sync with server
);

CREATE INDEX idx_recipes_category ON recipes(category);
CREATE INDEX idx_recipes_area ON recipes(area);
CREATE INDEX idx_recipes_name ON recipes(name);
```

#### `user_recipes`
```sql
CREATE TABLE user_recipes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  ingredients TEXT,  -- JSON array
  instructions TEXT,
  prep_time INTEGER,
  cook_time INTEGER,
  servings INTEGER,
  image_path TEXT,  -- Local file path
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `shopping_list`
```sql
CREATE TABLE shopping_list (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item TEXT NOT NULL,
  quantity TEXT,
  category TEXT,
  checked BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shopping_checked ON shopping_list(checked);
```

#### `favorites`
```sql
CREATE TABLE favorites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id INTEGER,
  recipe_type TEXT,  -- 'mealdb' or 'user'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(recipe_id, recipe_type)
);
```

#### `cooking_timers`
```sql
CREATE TABLE cooking_timers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  duration INTEGER NOT NULL,  -- seconds
  started_at TIMESTAMP,
  completed BOOLEAN DEFAULT 0,
  recipe_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `sync_metadata`
```sql
CREATE TABLE sync_metadata (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracks last sync times
-- 'last_recipe_sync' -> timestamp
-- 'last_category_sync' -> timestamp
```

---

## Implementation Files

### 1. Database Layer

**File:** `mobile/src/database/db.ts`

```typescript
import * as SQLite from 'expo-sqlite';

const db = SQLite.openDatabaseSync('food_app.db');

export const initDatabase = async () => {
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS recipes (
      id INTEGER PRIMARY KEY,
      mealdb_id TEXT UNIQUE,
      name TEXT NOT NULL,
      category TEXT,
      area TEXT,
      instructions TEXT,
      thumbnail_url TEXT,
      ingredients TEXT,
      measures TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_recipes_category ON recipes(category);
    CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name);

    CREATE TABLE IF NOT EXISTS favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      recipe_id INTEGER,
      recipe_type TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(recipe_id, recipe_type)
    );

    CREATE TABLE IF NOT EXISTS shopping_list (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      item TEXT NOT NULL,
      quantity TEXT,
      category TEXT,
      checked BOOLEAN DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  `);
};

export default db;
```

### 2. Recipe Repository

**File:** `mobile/src/database/repositories/RecipeRepository.ts`

```typescript
import db from '../db';
import { Recipe } from '../../types';

export class RecipeRepository {
  static async getAll(): Promise<Recipe[]> {
    const result = await db.getAllAsync('SELECT * FROM recipes ORDER BY name');
    return result.map(row => this.rowToRecipe(row));
  }

  static async getById(id: number): Promise<Recipe | null> {
    const result = await db.getFirstAsync(
      'SELECT * FROM recipes WHERE id = ?',
      [id]
    );
    return result ? this.rowToRecipe(result) : null;
  }

  static async search(query: string): Promise<Recipe[]> {
    const result = await db.getAllAsync(
      'SELECT * FROM recipes WHERE name LIKE ? OR category LIKE ?',
      [`%${query}%`, `%${query}%`]
    );
    return result.map(row => this.rowToRecipe(row));
  }

  static async upsert(recipe: Recipe): Promise<void> {
    const ingredients = JSON.stringify(recipe.ingredients);
    const measures = JSON.stringify(recipe.measures);

    await db.runAsync(
      `INSERT OR REPLACE INTO recipes
       (mealdb_id, name, category, area, instructions, thumbnail_url,
        ingredients, measures, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`,
      [
        recipe.mealdb_id,
        recipe.name,
        recipe.category,
        recipe.area,
        recipe.instructions,
        recipe.thumbnail_url,
        ingredients,
        measures,
      ]
    );
  }

  static async bulkUpsert(recipes: Recipe[]): Promise<void> {
    await db.withTransactionAsync(async () => {
      for (const recipe of recipes) {
        await this.upsert(recipe);
      }
    });
  }

  private static rowToRecipe(row: any): Recipe {
    return {
      ...row,
      ingredients: JSON.parse(row.ingredients || '[]'),
      measures: JSON.parse(row.measures || '[]'),
    };
  }
}
```

### 3. Sync Service

**File:** `mobile/src/services/SyncService.ts`

```typescript
import { RecipeRepository } from '../database/repositories/RecipeRepository';
import api from './api';

export class SyncService {
  private static isSyncing = false;

  static async syncRecipes(force = false): Promise<void> {
    if (this.isSyncing) return;

    try {
      this.isSyncing = true;

      // Get last sync time
      const lastSync = await this.getLastSyncTime('recipes');
      const hoursSinceSync = (Date.now() - lastSync) / (1000 * 60 * 60);

      // Only sync if > 24 hours or forced
      if (hoursSinceSync < 24 && !force) {
        console.log('Skipping sync - recent data');
        return;
      }

      // Try to fetch from server
      try {
        const recipes = await api.getRecipes();
        await RecipeRepository.bulkUpsert(recipes);
        await this.setLastSyncTime('recipes', Date.now());
        console.log(`✅ Synced ${recipes.length} recipes`);
      } catch (error) {
        console.log('⚠️ Server unavailable - using cached data');
      }
    } finally {
      this.isSyncing = false;
    }
  }

  private static async getLastSyncTime(key: string): Promise<number> {
    const result = await db.getFirstAsync(
      'SELECT value FROM sync_metadata WHERE key = ?',
      [key]
    );
    return result ? parseInt(result.value) : 0;
  }

  private static async setLastSyncTime(key: string, time: number): Promise<void> {
    await db.runAsync(
      'INSERT OR REPLACE INTO sync_metadata (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
      [key, time.toString()]
    );
  }
}
```

### 4. Updated API Service

**File:** `mobile/src/services/api.ts` (modified)

```typescript
import { RecipeRepository } from '../database/repositories/RecipeRepository';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://192.168.2.38:5025';

class API {
  private isServerAvailable = false;

  async checkServerHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/health`, {
        timeout: 2000,
      });
      this.isServerAvailable = response.ok;
      return this.isServerAvailable;
    } catch {
      this.isServerAvailable = false;
      return false;
    }
  }

  async getRecipes(): Promise<Recipe[]> {
    // Always try local first
    const localRecipes = await RecipeRepository.getAll();

    // Try to sync from server in background
    if (await this.checkServerHealth()) {
      try {
        const response = await fetch(`${API_URL}/api/recipes`);
        const serverRecipes = await response.json();

        // Update local cache
        await RecipeRepository.bulkUpsert(serverRecipes);

        return serverRecipes;
      } catch (error) {
        console.log('Server fetch failed, using cache');
      }
    }

    return localRecipes;
  }

  async getRecipeById(id: number): Promise<Recipe | null> {
    // Check local first
    let recipe = await RecipeRepository.getById(id);

    // If not found and server available, try fetching
    if (!recipe && await this.checkServerHealth()) {
      try {
        const response = await fetch(`${API_URL}/api/mealdb/recipe/${id}`);
        recipe = await response.json();

        if (recipe) {
          await RecipeRepository.upsert(recipe);
        }
      } catch {
        // Ignore server errors
      }
    }

    return recipe;
  }

  getServerStatus(): boolean {
    return this.isServerAvailable;
  }
}

export default new API();
```

---

## App Initialization Flow

### 1. First Launch (Fresh Install)

```typescript
// In App.tsx
useEffect(() => {
  const initApp = async () => {
    // 1. Initialize database
    await initDatabase();

    // 2. Seed with default recipes (embedded JSON)
    const seedRecipes = require('./assets/seed_recipes.json');
    await RecipeRepository.bulkUpsert(seedRecipes);

    // 3. Try to sync from server (background)
    SyncService.syncRecipes(true).catch(() => {
      // Ignore errors - we have seed data
    });

    setIsReady(true);
  };

  initApp();
}, []);
```

### 2. Subsequent Launches

```typescript
useEffect(() => {
  const initApp = async () => {
    // 1. Load from local DB (instant)
    const recipes = await RecipeRepository.getAll();
    setRecipes(recipes);

    // 2. Background sync (non-blocking)
    SyncService.syncRecipes().catch(() => {
      // App works fine without server
    });
  };

  initApp();
}, []);
```

---

## Seed Data Strategy

### Create Seed File

**File:** `mobile/assets/seed_recipes.json`

Contains ~100 popular recipes embedded in the app for first-time users.

**Generate seed data:**
```bash
# Run once on PC with internet
cd backend
python scripts/generate_seed_data.py
# Creates mobile/assets/seed_recipes.json
```

**Script:** `backend/scripts/generate_seed_data.py`
```python
import json
import requests

# Fetch 100 popular recipes from MealDB
categories = ['Beef', 'Chicken', 'Dessert', 'Pasta', 'Seafood', 'Vegetarian']
seed_recipes = []

for category in categories:
    response = requests.get(f'https://www.themealdb.com/api/json/v1/1/filter.php?c={category}')
    meals = response.json()['meals'][:15]  # 15 per category

    for meal in meals:
        # Fetch full recipe details
        detail = requests.get(f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal["idMeal"]}')
        seed_recipes.append(detail.json()['meals'][0])

with open('../mobile/assets/seed_recipes.json', 'w') as f:
    json.dump(seed_recipes, f, indent=2)

print(f'✅ Generated seed data with {len(seed_recipes)} recipes')
```

---

## User Experience

### Offline Mode Indicator

```typescript
// components/StatusBar.tsx
export const ConnectionStatus = () => {
  const [status, setStatus] = useState<'online' | 'offline'>('offline');

  useEffect(() => {
    const checkConnection = async () => {
      const isOnline = await api.checkServerHealth();
      setStatus(isOnline ? 'online' : 'offline');
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  if (status === 'offline') {
    return (
      <View style={styles.offlineBanner}>
        <Text style={styles.offlineText}>📱 Offline Mode</Text>
      </View>
    );
  }

  return null;
};
```

### Pull-to-Refresh

```typescript
// screens/RecipesScreen.tsx
const [refreshing, setRefreshing] = useState(false);

const onRefresh = async () => {
  setRefreshing(true);
  await SyncService.syncRecipes(true);
  const updated = await RecipeRepository.getAll();
  setRecipes(updated);
  setRefreshing(false);
};

return (
  <FlatList
    data={recipes}
    renderItem={renderRecipe}
    refreshControl={
      <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
    }
  />
);
```

---

## Benefits

✅ **App works 100% offline**
✅ **Instant loading** (no network delays)
✅ **Works on airplane, subway, anywhere**
✅ **Server is optional enhancement**
✅ **Reduced data usage**
✅ **Better battery life** (fewer network requests)
✅ **User owns their data** (on device)

---

## Next Steps

1. Implement SQLite schema
2. Create repositories
3. Migrate API calls to local-first
4. Generate seed data
5. Add sync service
6. Test offline functionality
