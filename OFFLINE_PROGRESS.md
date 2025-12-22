# Offline Implementation Progress

## ✅ Completed (Phase 1 - Infrastructure)

### Database Layer
- ✅ **SQLite Schema** - Tables for shopping lists, pantry, favorites, cached recipes, meal plans
- ✅ **Database Init** - Auto-initialization on app startup with loading screen
- ✅ **Cache Management** - Auto-cleanup of old recipes (30+ days), favorites kept forever

### Repositories (Local Storage CRUD)
- ✅ **ShoppingListRepository** - Add, update, toggle, delete, sync tracking
- ✅ **PantryRepository** - Full CRUD with location/expiration tracking
- ✅ **RecipeRepository** - Favorites and cached recipe management

### Infrastructure
- ✅ **App.tsx** - Database initialization before app loads
- ✅ **useOnlineStatus** - Hook for connectivity detection (30s refresh)
- ✅ **API Health Check** - 2-second timeout with cached results

### Bug Fixes
- ✅ Fixed MealDB recipes showing "View recipe at..." instead of displaying recipe

---

## 🚧 In Progress (Phase 2 - Screen Updates)

### ShoppingScreen Update
**Status:** Ready to implement
**Changes needed:**
1. Use `ShoppingListRepository` instead of API calls
2. Load from local DB on mount (instant)
3. Sync with server in background when online
4. Show offline indicator when no connection
5. Save changes locally (immediate)
6. Queue changes for sync when back online

### PantryScreen Update
**Status:** Ready to implement
**Changes needed:**
1. Use `PantryRepository` instead of API calls
2. Load from local DB (instant)
3. Add/update/delete works offline
4. Show expiring items from local data
5. Sync in background when online

---

## 📋 Next Steps (Phase 3 - Polish)

### Sync Manager
**Purpose:** Background synchronization when online

```typescript
class SyncManager {
  // Upload pending changes to server
  async syncPendingChanges() {
    const unsyncedShopping = await ShoppingListRepository.getUnsynced();
    const unsyncedPantry = await PantryRepository.getUnsynced();

    for (const item of unsyncedShopping) {
      try {
        await api.updateShoppingItem(item);
        await ShoppingListRepository.markAsSynced(item.id);
      } catch {
        // Will retry on next sync
      }
    }
  }

  // Download latest from server
  async syncFromServer() {
    const shopping = await api.getShopping();
    await ShoppingListRepository.syncFromServer(shopping.items);

    const pantry = await api.getPantry();
    await PantryRepository.syncFromServer(pantry.items);
  }
}
```

### Connection Status UI
- Show "📡 Offline Mode" banner when no connection (only on screens that need internet)
- Show "☁️ Syncing..." when uploading changes
- Show "✅ Synced" confirmation

### Recipe Caching
- Auto-cache when user views recipe detail
- Auto-cache when user favorites recipe
- Show cached recipes in favorites (works offline)

---

## 📱 User Experience

### At Home with WiFi ✅
1. Open app → Shows latest data from server
2. Browse recipes → Fetches from MealDB API
3. Add to shopping list → Saves locally AND syncs to server
4. View pantry → Shows local data, syncs in background

### At Grocery Store (No WiFi) ✅
1. Open shopping list → **Loads instantly from local DB**
2. Check off items → **Saves locally** (syncs when home)
3. View pantry → **Works offline**
4. Try to browse recipes → Shows "Connect to WiFi to discover recipes"

### Cooking (No WiFi) ✅
1. View favorited recipe → **Cached, works offline**
2. Follow instructions → **All there**
3. Use timers → **100% local**

---

## 🔧 Implementation Plan

### Screen Updates (2-3 hours)

**ShoppingScreen.tsx:**
```typescript
import { ShoppingListRepository } from '../database/repositories/ShoppingListRepository';
import { useOnlineStatus } from '../hooks/useOnlineStatus';

const [items, setItems] = useState([]);
const { isOnline } = useOnlineStatus();

useEffect(() => {
  // Load from local DB (instant)
  loadLocalData();

  // Sync with server in background
  if (isOnline) {
    syncWithServer();
  }
}, [isOnline]);

const loadLocalData = async () => {
  const localItems = await ShoppingListRepository.getAll();
  setItems(localItems);
};

const toggleItem = async (id) => {
  // Update local DB immediately
  await ShoppingListRepository.toggleChecked(id);

  // Reload from DB
  await loadLocalData();

  // Sync to server in background (don't wait)
  if (isOnline) {
    syncToServer(id).catch(() => {
      // Failed to sync - will retry later
    });
  }
};
```

**PantryScreen.tsx:**
```typescript
// Same pattern as shopping screen
// Load local → Show immediately → Sync in background
```

### Sync Manager (30 mins)
- Create `src/services/SyncManager.ts`
- Run sync every 5 minutes when app is open and online
- Run sync on app open
- Run sync after user makes changes

### UI Polish (30 mins)
- Add connection status indicator
- Show sync status
- Handle offline gracefully

---

## 📊 Storage Estimates

| Data Type | Current Size | After Caching 50 Recipes |
|-----------|-------------|--------------------------|
| Shopping List | ~5 KB | ~5 KB |
| Pantry Items | ~20 KB | ~20 KB |
| Cached Recipes | 0 KB | ~2 MB |
| Favorites | ~1 KB | ~1 KB |
| **Total** | **~26 KB** | **~2 MB** |

**Much better than 100+ MB if we cached all MealDB recipes!**

---

## 🚀 Deployment

Once screens are updated:

```bash
cd mobile

# Update version
# Edit app.json: "version": "1.0.2"

# Build and deploy
npm run deploy

# Wait 30 min → Check email → Update in TestFlight
```

---

## ✅ What Works Now (Even Without Screen Updates)

- ✅ Database is initialized and ready
- ✅ Repositories work and can be tested
- ✅ Online/offline detection works
- ✅ Recipe detail displays correctly

## ⏳ What Needs Screen Updates

- Shopping list still uses API (needs to use repository)
- Pantry still uses API (needs to use repository)
- No sync manager yet (changes don't upload to server)
- No offline indicator UI

---

## 📝 Testing Plan

### Manual Testing
1. **With WiFi:**
   - Open app → Should load normally
   - Add to shopping list → Should save and sync
   - Check pantry → Should load from server

2. **Without WiFi (Airplane Mode):**
   - Open shopping list → Should load from local DB
   - Toggle items → Should save locally
   - Try to browse recipes → Should show "need internet" message

3. **Back Online:**
   - Changes should sync to server
   - New data should appear

### Edge Cases
- What if server is down?
- What if user makes changes on two devices?
- What if sync fails halfway?

---

## 🎯 Success Criteria

- [ ] Shopping list works 100% offline
- [ ] Pantry works 100% offline
- [ ] Favorited recipes work offline
- [ ] Browsing requires internet (expected)
- [ ] Changes sync when back online
- [ ] No data loss
- [ ] Fast performance (instant local load)
- [ ] Clear offline/online indicators

---

## Current Status

**Infrastructure:** ✅ DONE
**Screen Updates:** 🚧 IN PROGRESS
**Testing:** ⏳ PENDING
**Deployment:** ⏳ PENDING

Next immediate task: Update ShoppingScreen to use ShoppingListRepository
