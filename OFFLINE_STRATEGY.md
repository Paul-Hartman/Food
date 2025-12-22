# Food App - Smart Offline Strategy

## Core Principle

**Only cache what you actually need. Browse recipes online, use your data offline.**

---

## What Works Offline vs Online

### ✅ Always Works Offline (Cached Locally)

| Feature | Why Offline |
|---------|-------------|
| **Shopping Lists** | Use in grocery store without WiFi |
| **Pantry Inventory** | Check what you have at home |
| **Saved/Favorited Recipes** | Recipes you actually want to cook |
| **Cooking Timers** | Obviously needs to work while cooking |
| **Your Custom Recipes** | Personal recipes you created |
| **Planned Meals** | This week's meal plan |

### 🌐 Requires Internet

| Feature | Why Online |
|---------|-----------|
| **Browse MealDB Recipes** | 10,000+ recipes = huge storage |
| **Recipe Search** | Real-time search of full database |
| **Random Recipes** | Fresh suggestions |
| **Recipe Discovery** | Browse new categories/cuisines |
| **Barcode Lookup** | OpenFoodFacts API |

### 🔄 Hybrid (Smart Caching)

| Feature | Behavior |
|---------|----------|
| **Recipe Detail** | Cache when you view/save it |
| **Shopping List Generation** | Generate offline from cached recipe |
| **Meal Planning** | Browse online, plan offline |

---

## SQLite Schema (Minimal)

### What to Store Locally

```sql
-- User's shopping list
CREATE TABLE shopping_list (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item TEXT NOT NULL,
  quantity TEXT,
  category TEXT,
  checked BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User's pantry inventory
CREATE TABLE pantry_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  quantity TEXT,
  unit TEXT,
  location TEXT,  -- pantry/fridge/freezer
  expiration_date TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User's favorites (only the IDs, fetch details online)
CREATE TABLE favorites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mealdb_id TEXT,
  recipe_type TEXT,  -- 'mealdb' or 'custom'
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cached recipe details (only for favorites/planned meals)
CREATE TABLE cached_recipes (
  mealdb_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT,
  area TEXT,
  instructions TEXT,
  thumbnail_url TEXT,
  ingredients TEXT,  -- JSON array
  measures TEXT,  -- JSON array
  cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User's meal plan for this week
CREATE TABLE meal_plan (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,  -- YYYY-MM-DD
  meal_type TEXT,  -- breakfast/lunch/dinner
  mealdb_id TEXT,
  recipe_type TEXT,  -- 'mealdb' or 'custom'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cooking timers (in-memory is fine, but persist for app restart)
CREATE TABLE timers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  duration INTEGER NOT NULL,  -- seconds
  started_at TIMESTAMP,
  paused_at TIMESTAMP,
  completed BOOLEAN DEFAULT 0
);

-- User's custom recipes
CREATE TABLE custom_recipes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  ingredients TEXT,  -- JSON
  instructions TEXT,
  prep_time INTEGER,
  cook_time INTEGER,
  servings INTEGER,
  image_path TEXT,  -- Local file
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Total Storage:** ~1-5 MB (not 100+ MB of unused recipes!)

---

## Smart Recipe Caching

### When to Cache a Recipe

```typescript
// Automatically cache when:
1. User favorites/saves it
2. User adds to meal plan
3. User views recipe detail (cache for 7 days)
4. User starts cooking it

// Auto-cleanup:
- Remove cached recipes after 30 days if not favorited
- Keep favorites forever
```

### Cache Lifecycle

```typescript
async function getRecipe(mealdbId: string): Promise<Recipe> {
  // 1. Check if cached locally
  const cached = await db.getCachedRecipe(mealdbId);

  if (cached) {
    // Update last_accessed for cache management
    await db.updateRecipeAccess(mealdbId);

    // If online, refresh in background (don't wait)
    if (await isOnline()) {
      refreshRecipeInBackground(mealdbId);
    }

    return cached;
  }

  // 2. Not cached - need internet
  if (!await isOnline()) {
    throw new Error('This recipe requires internet connection');
  }

  // 3. Fetch from server
  const recipe = await api.getRecipe(mealdbId);

  // 4. Cache it for next time
  await db.cacheRecipe(recipe);

  return recipe;
}
```

---

## User Experience Flows

### Scenario 1: At Home with WiFi

```
User opens app
  ↓
Shows shopping list (cached) ✅ Instant
  ↓
Browses recipes (MealDB API) 🌐 Online
  ↓
Favorites a recipe → Cached locally ✅
  ↓
Generates shopping list from recipe ✅ Now works offline
```

### Scenario 2: At Grocery Store (No WiFi)

```
User opens app (no internet)
  ↓
Shopping list loads instantly ✅ From cache
  ↓
Checks items off as shopping ✅ Saves to local DB
  ↓
Tries to browse new recipes ⚠️ "Connect to WiFi to browse recipes"
  ↓
Views favorited recipe ✅ Cached, works fine
```

### Scenario 3: Cooking in Kitchen (No WiFi)

```
User opens recipe they're cooking
  ↓
Recipe loads from cache ✅ Was cached when favorited
  ↓
Starts multiple timers ✅ All local
  ↓
Follows instructions ✅ All there
  ↓
Checks off shopping list items ✅ Local DB
```

---

## UI/UX Changes

### Connection Status Indicator

```typescript
// Only show when it matters
const ConnectionBanner = ({ screen }: { screen: string }) => {
  const isOnline = useOnlineStatus();

  // Only show offline banner on screens that need internet
  const needsInternet = ['RecipeBrowse', 'RecipeSearch', 'Discover'].includes(screen);

  if (isOnline || !needsInternet) return null;

  return (
    <View style={styles.offlineBanner}>
      <Text>📡 Connect to WiFi to browse recipes</Text>
    </View>
  );
};
```

### Smart Feature Availability

```typescript
// Recipe Browse Screen
{!isOnline && (
  <EmptyState
    icon="📡"
    title="No Internet Connection"
    description="Connect to WiFi to browse thousands of recipes"
    action={{
      label: "View Saved Recipes",
      onPress: () => navigation.navigate('Favorites')
    }}
  />
)}

// Shopping List Screen
{/* Always works - no messaging needed */}

// Pantry Screen
{/* Always works - no messaging needed */}

// Recipe Detail Screen
{!recipe && !isOnline && (
  <EmptyState
    icon="📡"
    title="Recipe Not Cached"
    description="This recipe needs internet to load. Save recipes to view them offline."
  />
)}
```

### Pull-to-Refresh (Only When Online)

```typescript
const onRefresh = async () => {
  if (!await isOnline()) {
    // Don't show error - just silently skip
    return;
  }

  setRefreshing(true);
  await syncWithServer();
  setRefreshing(false);
};
```

---

## Sync Strategy

### What to Sync

```typescript
class SyncManager {
  async sync() {
    if (!await isOnline()) return;

    // Upload user changes
    await this.uploadPendingChanges();

    // Download updates for cached recipes
    await this.refreshCachedRecipes();

    // Cleanup old cache
    await this.cleanupCache();
  }

  private async uploadPendingChanges() {
    // Sync shopping list changes
    const pendingItems = await db.getPendingShoppingItems();
    for (const item of pendingItems) {
      await api.updateShoppingItem(item);
      await db.markAsSynced(item.id);
    }

    // Sync pantry changes
    const pendingPantry = await db.getPendingPantryItems();
    for (const item of pendingPantry) {
      await api.updatePantryItem(item);
      await db.markAsSynced(item.id);
    }
  }

  private async refreshCachedRecipes() {
    // Only refresh favorited recipes
    const favorites = await db.getFavorites();

    for (const favorite of favorites) {
      try {
        const updated = await api.getRecipe(favorite.mealdb_id);
        await db.updateCachedRecipe(updated);
      } catch {
        // Skip if recipe fails to update
      }
    }
  }

  private async cleanupCache() {
    // Remove recipes not accessed in 30 days (except favorites)
    await db.cleanupOldCache(30);
  }
}
```

### When to Sync

```typescript
// Background sync (don't block user)
useEffect(() => {
  const syncInterval = setInterval(async () => {
    if (await isOnline()) {
      await syncManager.sync();
    }
  }, 5 * 60 * 1000); // Every 5 minutes when online

  return () => clearInterval(syncInterval);
}, []);

// On app open
useEffect(() => {
  syncManager.sync(); // Don't await - happens in background
}, []);

// Manual sync (pull-to-refresh)
const onRefresh = async () => {
  await syncManager.sync();
};
```

---

## Implementation Priority

### Phase 1: Core Offline Features (Week 1)
- [ ] SQLite database setup
- [ ] Shopping list offline storage
- [ ] Pantry inventory offline storage
- [ ] Timers persistence
- [ ] Basic online/offline detection

### Phase 2: Smart Caching (Week 2)
- [ ] Favorite recipe caching
- [ ] Meal plan offline storage
- [ ] Recipe detail caching on view
- [ ] Cache cleanup system

### Phase 3: Seamless Sync (Week 3)
- [ ] Background sync manager
- [ ] Conflict resolution (local wins)
- [ ] Connection status UI
- [ ] Smart feature availability

### Phase 4: Polish (Week 4)
- [ ] Offline empty states
- [ ] Pull-to-refresh sync
- [ ] Cache size management
- [ ] Sync status indicators

---

## Storage Estimates

| Data Type | Typical Size | Max Expected |
|-----------|-------------|--------------|
| Shopping list | 1-5 KB | 50 KB |
| Pantry items | 5-20 KB | 200 KB |
| Cached recipes (20) | 100-500 KB | 2 MB |
| Custom recipes | 50-200 KB | 1 MB |
| Meal plans | 10-50 KB | 100 KB |
| Timers | 1-5 KB | 10 KB |
| **TOTAL** | **~200 KB - 1 MB** | **~5 MB** |

**vs 100+ MB** if we cached all MealDB recipes!

---

## Edge Cases

### User Saves 100+ Recipes

**Solution:** Warn at 50 cached recipes:
```typescript
if (cachedRecipeCount > 50) {
  showWarning(
    'Storage Notice',
    'You have 50+ saved recipes. Consider removing old ones to save space.'
  );
}
```

### Recipe Changed on Server

**Solution:** Background refresh when online
- Don't block user
- Update silently
- User always sees latest when online

### User Goes Offline Mid-Browse

**Solution:** Graceful degradation
```typescript
try {
  const recipe = await api.getRecipe(id);
} catch (error) {
  if (!isOnline()) {
    showMessage('This recipe needs internet. Save recipes to view offline.');
  } else {
    showMessage('Failed to load recipe. Please try again.');
  }
}
```

---

## Benefits

✅ **Small storage footprint** (MB not GB)
✅ **Fast performance** (only cache what you use)
✅ **Works offline where it matters** (shopping, cooking)
✅ **Always fresh recipes** (browse latest online)
✅ **Seamless experience** (smart online/offline transitions)
✅ **No user confusion** ("Why is this so slow?" / "Why so much storage?")

---

## Next Steps

1. Implement core offline storage (shopping list, pantry)
2. Add smart recipe caching on favorite/view
3. Build sync manager for background updates
4. Polish UI for online/offline states
