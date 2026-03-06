import db from '../db';

export interface CachedRecipe {
  mealdb_id: string;
  name: string;
  category?: string;
  area?: string;
  instructions?: string;
  thumbnail_url?: string;
  ingredients?: string; // JSON string
  measures?: string; // JSON string
  source_url?: string;
  youtube_url?: string;
  tags?: string;
  cached_at?: string;
  last_accessed?: string;
}

export class RecipeRepository {
  /**
   * Get cached recipe by MealDB ID
   */
  static async get(mealdbId: string): Promise<CachedRecipe | null> {
    const result = await db.getFirstAsync<any>(
      'SELECT * FROM cached_recipes WHERE mealdb_id = ?',
      [mealdbId]
    );

    if (!result) return null;

    // Update last accessed time
    await db.runAsync(
      'UPDATE cached_recipes SET last_accessed = CURRENT_TIMESTAMP WHERE mealdb_id = ?',
      [mealdbId]
    );

    return this.rowToRecipe(result);
  }

  /**
   * Cache a recipe (stores compressed data)
   */
  static async cache(recipe: CachedRecipe): Promise<void> {
    await db.runAsync(
      `INSERT OR REPLACE INTO cached_recipes
       (mealdb_id, name, category, area, instructions, thumbnail_url, ingredients,
        measures, source_url, youtube_url, tags, cached_at, last_accessed)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
      [
        recipe.mealdb_id,
        recipe.name,
        recipe.category || null,
        recipe.area || null,
        recipe.instructions || null,
        recipe.thumbnail_url || null,
        recipe.ingredients || null,
        recipe.measures || null,
        recipe.source_url || null,
        recipe.youtube_url || null,
        recipe.tags || null,
      ]
    );
  }

  /**
   * Get all favorited recipes
   */
  static async getFavorites(): Promise<string[]> {
    const result = await db.getAllAsync<{ mealdb_id: string }>(
      'SELECT mealdb_id FROM favorites WHERE mealdb_id IS NOT NULL'
    );
    return result.map(r => r.mealdb_id);
  }

  /**
   * Add recipe to favorites
   */
  static async addFavorite(mealdbId: string, recipeType: string = 'mealdb'): Promise<void> {
    await db.runAsync(
      `INSERT OR IGNORE INTO favorites (mealdb_id, recipe_type, added_at)
       VALUES (?, ?, CURRENT_TIMESTAMP)`,
      [mealdbId, recipeType]
    );
  }

  /**
   * Remove recipe from favorites
   */
  static async removeFavorite(mealdbId: string): Promise<void> {
    await db.runAsync(
      'DELETE FROM favorites WHERE mealdb_id = ?',
      [mealdbId]
    );
  }

  /**
   * Check if recipe is favorited
   */
  static async isFavorite(mealdbId: string): Promise<boolean> {
    const result = await db.getFirstAsync<{ count: number }>(
      'SELECT COUNT(*) as count FROM favorites WHERE mealdb_id = ?',
      [mealdbId]
    );
    return (result?.count || 0) > 0;
  }

  /**
   * Get all cached recipes (for browsing offline favorites)
   */
  static async getAllCached(): Promise<CachedRecipe[]> {
    const result = await db.getAllAsync<any>(
      `SELECT cr.* FROM cached_recipes cr
       INNER JOIN favorites f ON cr.mealdb_id = f.mealdb_id
       ORDER BY f.added_at DESC`
    );
    return result.map(row => this.rowToRecipe(row));
  }

  /**
   * Delete cached recipe (if not favorited)
   */
  static async deleteCache(mealdbId: string): Promise<void> {
    const isFav = await this.isFavorite(mealdbId);
    if (!isFav) {
      await db.runAsync(
        'DELETE FROM cached_recipes WHERE mealdb_id = ?',
        [mealdbId]
      );
    }
  }

  /**
   * Get cache size estimate
   */
  static async getCacheSize(): Promise<number> {
    const result = await db.getFirstAsync<{ count: number }>(
      'SELECT COUNT(*) as count FROM cached_recipes'
    );
    return result?.count || 0;
  }

  /**
   * Convert database row to CachedRecipe
   */
  private static rowToRecipe(row: any): CachedRecipe {
    return {
      mealdb_id: row.mealdb_id,
      name: row.name,
      category: row.category,
      area: row.area,
      instructions: row.instructions,
      thumbnail_url: row.thumbnail_url,
      ingredients: row.ingredients,
      measures: row.measures,
      source_url: row.source_url,
      youtube_url: row.youtube_url,
      tags: row.tags,
      cached_at: row.cached_at,
      last_accessed: row.last_accessed,
    };
  }
}
