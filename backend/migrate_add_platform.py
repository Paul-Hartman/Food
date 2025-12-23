"""
Add platform column to test_cases table
Run once to migrate existing test data
"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), "food.db")

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        # Check if platform column already exists
        cursor.execute("PRAGMA table_info(test_cases)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'platform' in columns:
            print("SUCCESS: Platform column already exists")
            return

        print("Adding platform column to test_cases...")

        # Add platform column with default 'both'
        cursor.execute("ALTER TABLE test_cases ADD COLUMN platform TEXT DEFAULT 'both'")

        # Update existing test cases based on category
        # Offline tests are mobile-only
        cursor.execute("UPDATE test_cases SET platform = 'mobile' WHERE category = 'offline'")

        conn.commit()
        print("SUCCESS: Added platform column")
        print("SUCCESS: Marked offline tests as mobile-only")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
