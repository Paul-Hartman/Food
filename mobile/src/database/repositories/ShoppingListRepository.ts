import db from '../db';

export interface ShoppingListItem {
  id?: number;
  server_id?: number;
  item: string;
  quantity?: string;
  category?: string;
  checked: boolean;
  created_at?: string;
  updated_at?: string;
  synced: boolean;
}

export class ShoppingListRepository {
  /**
   * Get all shopping list items
   */
  static async getAll(): Promise<ShoppingListItem[]> {
    const result = await db.getAllAsync<any>(
      'SELECT * FROM shopping_list ORDER BY checked ASC, created_at DESC'
    );
    return result.map(row => this.rowToItem(row));
  }

  /**
   * Get un-synced items (for background sync)
   */
  static async getUnsynced(): Promise<ShoppingListItem[]> {
    const result = await db.getAllAsync<any>(
      'SELECT * FROM shopping_list WHERE synced = 0'
    );
    return result.map(row => this.rowToItem(row));
  }

  /**
   * Add new item to shopping list
   */
  static async add(item: Omit<ShoppingListItem, 'id'>): Promise<number> {
    const result = await db.runAsync(
      `INSERT INTO shopping_list
       (item, quantity, category, checked, server_id, synced, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
      [
        item.item,
        item.quantity || null,
        item.category || null,
        item.checked ? 1 : 0,
        item.server_id || null,
      ]
    );

    return result.lastInsertRowId;
  }

  /**
   * Update shopping list item
   */
  static async update(id: number, updates: Partial<ShoppingListItem>): Promise<void> {
    const setClauses: string[] = [];
    const values: any[] = [];

    if (updates.item !== undefined) {
      setClauses.push('item = ?');
      values.push(updates.item);
    }
    if (updates.quantity !== undefined) {
      setClauses.push('quantity = ?');
      values.push(updates.quantity);
    }
    if (updates.category !== undefined) {
      setClauses.push('category = ?');
      values.push(updates.category);
    }
    if (updates.checked !== undefined) {
      setClauses.push('checked = ?');
      values.push(updates.checked ? 1 : 0);
    }

    if (setClauses.length === 0) return;

    // Mark as unsynced when updated locally
    setClauses.push('synced = 0');
    setClauses.push('updated_at = CURRENT_TIMESTAMP');

    values.push(id);

    await db.runAsync(
      `UPDATE shopping_list SET ${setClauses.join(', ')} WHERE id = ?`,
      values
    );
  }

  /**
   * Toggle checked status
   */
  static async toggleChecked(id: number): Promise<void> {
    await db.runAsync(
      'UPDATE shopping_list SET checked = NOT checked, synced = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [id]
    );
  }

  /**
   * Delete item from shopping list
   */
  static async delete(id: number): Promise<void> {
    await db.runAsync('DELETE FROM shopping_list WHERE id = ?', [id]);
  }

  /**
   * Clear checked items
   */
  static async clearChecked(): Promise<number> {
    const result = await db.runAsync('DELETE FROM shopping_list WHERE checked = 1');
    return result.changes || 0;
  }

  /**
   * Clear all items
   */
  static async clearAll(): Promise<void> {
    await db.runAsync('DELETE FROM shopping_list');
  }

  /**
   * Sync from server - replace local data
   */
  static async syncFromServer(items: Array<{
    id: number;
    item: string;
    quantity?: string;
    category?: string;
    checked: boolean;
  }>): Promise<void> {
    await db.withTransactionAsync(async () => {
      // Clear existing
      await db.runAsync('DELETE FROM shopping_list');

      // Insert server items
      for (const item of items) {
        await db.runAsync(
          `INSERT INTO shopping_list
           (server_id, item, quantity, category, checked, synced, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
          [
            item.id,
            item.item,
            item.quantity || null,
            item.category || null,
            item.checked ? 1 : 0,
          ]
        );
      }
    });
  }

  /**
   * Mark item as synced
   */
  static async markAsSynced(id: number, serverId?: number): Promise<void> {
    if (serverId) {
      await db.runAsync(
        'UPDATE shopping_list SET synced = 1, server_id = ? WHERE id = ?',
        [serverId, id]
      );
    } else {
      await db.runAsync(
        'UPDATE shopping_list SET synced = 1 WHERE id = ?',
        [id]
      );
    }
  }

  /**
   * Convert database row to ShoppingListItem
   */
  private static rowToItem(row: any): ShoppingListItem {
    return {
      id: row.id,
      server_id: row.server_id,
      item: row.item,
      quantity: row.quantity,
      category: row.category,
      checked: row.checked === 1,
      created_at: row.created_at,
      updated_at: row.updated_at,
      synced: row.synced === 1,
    };
  }
}
