"""Migration: Add daily-use tracking to pantry table."""

import os
import sqlite3


def migrate():
    db_path = os.path.join(os.path.dirname(__file__), "food.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Starting migration...")

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(pantry)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add new columns to pantry table
        if "is_daily_use" not in columns:
            print("Adding is_daily_use...")
            cursor.execute("ALTER TABLE pantry ADD COLUMN is_daily_use INTEGER DEFAULT 0")

        if "daily_usage_rate" not in columns:
            print("Adding daily_usage_rate...")
            cursor.execute("ALTER TABLE pantry ADD COLUMN daily_usage_rate REAL DEFAULT 0")

        if "restock_threshold_days" not in columns:
            print("Adding restock_threshold_days...")
            cursor.execute("ALTER TABLE pantry ADD COLUMN restock_threshold_days INTEGER DEFAULT 3")

        if "last_depletion_date" not in columns:
            print("Adding last_depletion_date...")
            cursor.execute("ALTER TABLE pantry ADD COLUMN last_depletion_date DATE")

        # Create history table
        print("Creating pantry_usage_history...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pantry_usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pantry_item_id INTEGER NOT NULL,
                quantity_change REAL NOT NULL,
                quantity_before REAL NOT NULL,
                quantity_after REAL NOT NULL,
                change_type TEXT NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pantry_item_id) REFERENCES pantry(id) ON DELETE CASCADE
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_usage_history_item_date
            ON pantry_usage_history(pantry_item_id, logged_at)
        """
        )

        # Update calendar_events
        cursor.execute("PRAGMA table_info(calendar_events)")
        cal_columns = [col[1] for col in cursor.fetchall()]

        if "pantry_item_id" not in cal_columns:
            print("Adding pantry_item_id to calendar_events...")
            cursor.execute("ALTER TABLE calendar_events ADD COLUMN pantry_item_id INTEGER")

        if "event_metadata" not in cal_columns:
            print("Adding event_metadata to calendar_events...")
            cursor.execute("ALTER TABLE calendar_events ADD COLUMN event_metadata TEXT")

        conn.commit()
        print("[OK] Migration completed successfully!")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
