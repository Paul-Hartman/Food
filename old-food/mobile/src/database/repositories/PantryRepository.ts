import db from '../db';

export interface PantryItem {
  id?: number;
  server_id?: number;
  name: string;
  quantity?: string;
  unit?: string;
  location?: string;  // pantry/fridge/freezer
  expiration_date?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  synced: boolean;
}

export class PantryRepository {
  /**
   * Get all pantry items
   */
  static async getAll(): Promise<PantryItem[]> {
    const result = await db.getAllAsync<any>(
      `SELECT * FROM pantry_items
       ORDER BY location ASC, name ASC`
    );
    return result.map(row => this.rowToItem(row));
  }

  /**
   * Get items by location (pantry/fridge/freezer)
   */
  static async getByLocation(location: string): Promise<PantryItem[]> {
    const result = await db.getAllAsync<any>(
      'SELECT * FROM pantry_items WHERE location = ? ORDER BY name ASC',
      [location]
    );
    return result.map(row => this.rowToItem(row));
  }

  /**
   * Get items expiring soon (within N days)
   */
  static async getExpiringSoon(days: number = 7): Promise<PantryItem[]> {
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + days);
    const futureDateStr = futureDate.toISOString().split('T')[0]; // YYYY-MM-DD

    const result = await db.getAllAsync<any>(
      `SELECT * FROM pantry_items
       WHERE expiration_date IS NOT NULL
       AND expiration_date <= ?
       AND expiration_date >= DATE('now')
       ORDER BY expiration_date ASC`,
      [futureDateStr]
    );
    return result.map(row => this.rowToItem(row));
  }

  /**
   * Get un-synced items (for background sync)
   */
  static async getUnsynced(): Promise<PantryItem[]> {
    const result = await db.getAllAsync<any>(
      'SELECT * FROM pantry_items WHERE synced = 0'
    );
    return result.map(row => this.rowToItem(row));
  }

  /**
   * Add new item to pantry
   */
  static async add(item: Omit<PantryItem, 'id'>): Promise<number> {
    const result = await db.runAsync(
      `INSERT INTO pantry_items
       (name, quantity, unit, location, expiration_date, notes, server_id, synced, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
      [
        item.name,
        item.quantity || null,
        item.unit || null,
        item.location || null,
        item.expiration_date || null,
        item.notes || null,
        item.server_id || null,
      ]
    );

    return result.lastInsertRowId;
  }

  /**
   * Update pantry item
   */
  static async update(id: number, updates: Partial<PantryItem>): Promise<void> {
    const setClauses: string[] = [];
    const values: any[] = [];

    if (updates.name !== undefined) {
      setClauses.push('name = ?');
      values.push(updates.name);
    }
    if (updates.quantity !== undefined) {
      setClauses.push('quantity = ?');
      values.push(updates.quantity);
    }
    if (updates.unit !== undefined) {
      setClauses.push('unit = ?');
      values.push(updates.unit);
    }
    if (updates.location !== undefined) {
      setClauses.push('location = ?');
      values.push(updates.location);
    }
    if (updates.expiration_date !== undefined) {
      setClauses.push('expiration_date = ?');
      values.push(updates.expiration_date);
    }
    if (updates.notes !== undefined) {
      setClauses.push('notes = ?');
      values.push(updates.notes);
    }

    if (setClauses.length === 0) return;

    // Mark as unsynced when updated locally
    setClauses.push('synced = 0');
    setClauses.push('updated_at = CURRENT_TIMESTAMP');

    values.push(id);

    await db.runAsync(
      `UPDATE pantry_items SET ${setClauses.join(', ')} WHERE id = ?`,
      values
    );
  }

  /**
   * Delete item from pantry
   */
  static async delete(id: number): Promise<void> {
    await db.runAsync('DELETE FROM pantry_items WHERE id = ?', [id]);
  }

  /**
   * Clear all items
   */
  static async clearAll(): Promise<void> {
    await db.runAsync('DELETE FROM pantry_items');
  }

  /**
   * Sync from server - replace local data
   */
  static async syncFromServer(items: Array<{
    id: number;
    name: string;
    quantity?: string;
    unit?: string;
    location?: string;
    expiration_date?: string;
    notes?: string;
  }>): Promise<void> {
    await db.withTransactionAsync(async () => {
      // Clear existing
      await db.runAsync('DELETE FROM pantry_items');

      // Insert server items
      for (const item of items) {
        await db.runAsync(
          `INSERT INTO pantry_items
           (server_id, name, quantity, unit, location, expiration_date, notes, synced, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
          [
            item.id,
            item.name,
            item.quantity || null,
            item.unit || null,
            item.location || null,
            item.expiration_date || null,
            item.notes || null,
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
        'UPDATE pantry_items SET synced = 1, server_id = ? WHERE id = ?',
        [serverId, id]
      );
    } else {
      await db.runAsync(
        'UPDATE pantry_items SET synced = 1 WHERE id = ?',
        [id]
      );
    }
  }

  /**
   * Search pantry by name
   */
  static async search(query: string): Promise<PantryItem[]> {
    const result = await db.getAllAsync<any>(
      'SELECT * FROM pantry_items WHERE name LIKE ? ORDER BY name ASC',
      [`%${query}%`]
    );
    return result.map(row => this.rowToItem(row));
  }

  /**
   * Convert database row to PantryItem
   */
  private static rowToItem(row: any): PantryItem {
    return {
      id: row.id,
      server_id: row.server_id,
      name: row.name,
      quantity: row.quantity,
      unit: row.unit,
      location: row.location,
      expiration_date: row.expiration_date,
      notes: row.notes,
      created_at: row.created_at,
      updated_at: row.updated_at,
      synced: row.synced === 1,
    };
  }
}
