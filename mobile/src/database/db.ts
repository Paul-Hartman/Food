import * as SQLite from 'expo-sqlite';

// Open database
const db = SQLite.openDatabaseSync('food_app.db');

/**
 * Initialize database tables for offline storage
 *
 * Strategy: Only cache what you need
 * - Shopping lists (use in store without WiFi)
 * - Pantry inventory (check at home)
 * - Favorited/saved recipes (cook offline)
 * - Meal plans (this week's meals)
 * - NOT all MealDB recipes (too large)
 */
export const initDatabase = async () => {
  try {
    // Shopping list - works 100% offline
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS shopping_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER,
        item TEXT NOT NULL,
        quantity TEXT,
        category TEXT,
        checked INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        synced INTEGER DEFAULT 0
      );

      CREATE INDEX IF NOT EXISTS idx_shopping_checked ON shopping_list(checked);
      CREATE INDEX IF NOT EXISTS idx_shopping_synced ON shopping_list(synced);
    `);

    // Pantry inventory - works 100% offline
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS pantry_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER,
        name TEXT NOT NULL,
        quantity TEXT,
        unit TEXT,
        location TEXT,
        expiration_date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        synced INTEGER DEFAULT 0
      );

      CREATE INDEX IF NOT EXISTS idx_pantry_location ON pantry_items(location);
      CREATE INDEX IF NOT EXISTS idx_pantry_expiration ON pantry_items(expiration_date);
      CREATE INDEX IF NOT EXISTS idx_pantry_synced ON pantry_items(synced);
    `);

    // Favorites - recipes user wants to cook
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mealdb_id TEXT,
        recipe_type TEXT,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(mealdb_id, recipe_type)
      );

      CREATE INDEX IF NOT EXISTS idx_favorites_type ON favorites(recipe_type);
    `);

    // Cached recipes - only favorites and recently viewed
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS cached_recipes (
        mealdb_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        area TEXT,
        instructions TEXT,
        thumbnail_url TEXT,
        ingredients TEXT,
        measures TEXT,
        source_url TEXT,
        youtube_url TEXT,
        tags TEXT,
        cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_accessed TEXT DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_cached_category ON cached_recipes(category);
      CREATE INDEX IF NOT EXISTS idx_cached_area ON cached_recipes(area);
      CREATE INDEX IF NOT EXISTS idx_cached_accessed ON cached_recipes(last_accessed);
    `);

    // Meal plan - this week's planned meals
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS meal_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER,
        date TEXT NOT NULL,
        meal_type TEXT,
        mealdb_id TEXT,
        recipe_type TEXT,
        recipe_name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        synced INTEGER DEFAULT 0
      );

      CREATE INDEX IF NOT EXISTS idx_meal_plan_date ON meal_plan(date);
      CREATE INDEX IF NOT EXISTS idx_meal_plan_synced ON meal_plan(synced);
    `);

    // Sync metadata - track last sync times
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS sync_metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
      );
    `);

    console.log('✅ Database initialized successfully');
  } catch (error) {
    console.error('❌ Database initialization failed:', error);
    throw error;
  }
};

/**
 * Get last sync time for a specific data type
 */
export const getLastSyncTime = async (key: string): Promise<number> => {
  try {
    const result = await db.getFirstAsync<{ value: string }>(
      'SELECT value FROM sync_metadata WHERE key = ?',
      [key]
    );
    return result ? parseInt(result.value) : 0;
  } catch {
    return 0;
  }
};

/**
 * Set last sync time for a specific data type
 */
export const setLastSyncTime = async (key: string, timestamp: number): Promise<void> => {
  await db.runAsync(
    `INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
     VALUES (?, ?, CURRENT_TIMESTAMP)`,
    [key, timestamp.toString()]
  );
};

/**
 * Clean up old cached recipes (not favorited, not accessed in 30 days)
 */
export const cleanupOldCache = async (daysOld: number = 30): Promise<number> => {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - daysOld);
  const cutoffDate = cutoff.toISOString();

  const result = await db.runAsync(
    `DELETE FROM cached_recipes
     WHERE last_accessed < ?
     AND mealdb_id NOT IN (SELECT mealdb_id FROM favorites WHERE mealdb_id IS NOT NULL)`,
    [cutoffDate]
  );

  console.log(`🧹 Cleaned up ${result.changes} old cached recipes`);
  return result.changes || 0;
};

export default db;
