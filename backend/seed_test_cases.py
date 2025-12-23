"""
Seed comprehensive test cases for Food mobile app
Run once after database migration

Usage:
    cd backend
    python seed_test_cases.py
"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), "food.db")

# Test cases organized by suite
# Format: (test_name, test_description, category)
TEST_CASES = {
    'RecipesScreen': [
        ('Recipe list loads', 'Verify recipe grid displays on launch', 'ui'),
        ('Search functionality', 'Search bar filters recipes correctly', 'ui'),
        ('Recipe images load', 'Recipe thumbnails display properly', 'ui'),
        ('Category filters work', 'Filter buttons show correct categories', 'ui'),
        ('Empty state shows', 'When no recipes, show empty state message', 'edge_case'),
        ('Recipe card navigation', 'Tapping recipe card opens detail page', 'ui'),
        ('MealDB integration', 'Recipes load from MealDB API', 'api'),
        ('Slow network handling', 'Show loading state during slow API calls', 'edge_case'),
    ],
    'MealPlanScreen': [
        ('Weekly view loads', 'Display current week meal plan', 'ui'),
        ('Add meal to day', 'Can add recipe to specific day', 'ui'),
        ('Remove meal works', 'Can remove planned meal', 'ui'),
        ('Navigation between weeks', 'Swipe left/right to change weeks', 'ui'),
        ('Persistence after restart', 'Meal plan persists after app close', 'offline'),
        ('Empty days show placeholder', 'Days without meals show "Add Meal" prompt', 'ui'),
    ],
    'ShoppingScreen': [
        ('Shopping list displays', 'All shopping items render correctly', 'ui'),
        ('Add item functionality', 'Can add new item to list', 'ui'),
        ('Remove item works', 'Can delete item from list', 'ui'),
        ('Check off items', 'Can mark items as purchased', 'ui'),
        ('Aldi section grouping', 'Items grouped by store section', 'ui'),
        ('Persistence', 'Shopping list persists offline', 'offline'),
        ('Add from recipe', 'Add recipe ingredients to shopping list', 'ui'),
    ],
    'PantryScreen': [
        ('Pantry items load', 'All pantry items display', 'ui'),
        ('Search pantry', 'Search bar filters pantry items', 'ui'),
        ('Add pantry item', 'Can add new item to pantry', 'ui'),
        ('Update quantity', 'Can adjust item quantity', 'ui'),
        ('Delete item', 'Can remove item from pantry', 'ui'),
        ('Barcode scanner integration', 'Scanner adds products to pantry', 'ui'),
        ('Product detail page', 'Tapping item opens detail view', 'ui'),
        ('Offline sync', 'Pantry changes sync when back online', 'offline'),
    ],
    'NutritionScreen': [
        ('Daily stats display', 'Show calories, protein, carbs, fat', 'ui'),
        ('Weekly chart shows', 'Display 7-day nutrition chart', 'ui'),
        ('Add manual entry', 'Can log meal manually', 'ui'),
        ('Edit nutrition entry', 'Can modify logged meal', 'ui'),
        ('Goal tracking', 'Show progress toward daily goals', 'ui'),
        ('Chart interactions', 'Can tap chart to see details', 'ui'),
    ],
    'CalendarScreen': [
        ('Month view loads', 'Display current month calendar', 'ui'),
        ('Planned meals show', 'Meals appear on correct dates', 'ui'),
        ('Navigate months', 'Can switch between months', 'ui'),
        ('Tap date to add meal', 'Opens meal selector', 'ui'),
        ('Today indicator', 'Current date highlighted', 'ui'),
    ],
    'CookingScreen': [
        ('Recipe steps display', 'All cooking steps render', 'ui'),
        ('Step navigation', 'Can advance through steps', 'ui'),
        ('Timer functionality', 'Timers start/stop correctly', 'ui'),
        ('Multiple timers', 'Can run multiple timers simultaneously', 'ui'),
        ('Screen stays awake', 'Screen doesn\'t sleep during cooking', 'ui'),
        ('Voice command support', 'Voice commands work (if implemented)', 'ui'),
    ],
    'EnhancedRecipeDetailScreen': [
        ('Recipe details load', 'Name, image, description display', 'ui'),
        ('Ingredients list', 'All ingredients shown with quantities', 'ui'),
        ('Cooking instructions', 'Step-by-step instructions display', 'ui'),
        ('Nutrition info', 'Calories and macros shown', 'ui'),
        ('Add to meal plan', 'Can add recipe to weekly plan', 'ui'),
        ('Add to shopping list', 'Can add ingredients to shopping', 'ui'),
        ('Share recipe', 'Share functionality works', 'ui'),
    ],
    'BulkReviewScreen': [
        ('Recipe queue loads', 'Pending recipes display', 'ui'),
        ('Swipe to approve', 'Swipe right approves recipe', 'ui'),
        ('Swipe to reject', 'Swipe left rejects recipe', 'ui'),
        ('Undo last action', 'Can undo approval/rejection', 'ui'),
        ('Empty state', 'Show message when queue empty', 'edge_case'),
    ],
    'DecksScreen': [
        ('Collections display', 'All recipe collections shown', 'ui'),
        ('Create new deck', 'Can create new collection', 'ui'),
        ('Add recipe to deck', 'Can add recipe to collection', 'ui'),
        ('Remove from deck', 'Can remove recipe from collection', 'ui'),
        ('Deck thumbnails', 'Collection covers display correctly', 'ui'),
    ],
    'PantryProductDetailScreen': [
        ('Product info loads', 'Name, brand, quantity shown', 'ui'),
        ('Nutrition facts', 'Detailed nutrition displayed', 'ui'),
        ('Edit product', 'Can update product details', 'ui'),
        ('Delete product', 'Can remove product', 'ui'),
        ('Barcode shown', 'Product barcode displayed if available', 'ui'),
    ],
    'OfflineFunctionality': [
        ('App launches offline', 'App opens without internet', 'offline'),
        ('Local data loads', 'Cached recipes/meals load offline', 'offline'),
        ('Queue API calls', 'Changes sync when back online', 'offline'),
        ('Offline indicator', 'Show "offline" status in UI', 'offline'),
        ('Network error handling', 'Graceful error messages for failed API calls', 'edge_case'),
    ],
    'APIIntegration': [
        ('MealDB search works', 'Recipe search returns results', 'api'),
        ('Flask API connection', 'App connects to backend', 'api'),
        ('API error handling', '500 errors show user-friendly message', 'edge_case'),
        ('Slow API timeout', 'Don\'t hang on slow API calls', 'edge_case'),
        ('API response validation', 'Handle malformed API responses', 'edge_case'),
    ],
    'EdgeCases': [
        ('Empty recipe name', 'Handle recipes with missing data', 'edge_case'),
        ('Very long recipe name', 'Truncate or wrap long names', 'edge_case'),
        ('Missing recipe image', 'Show placeholder for missing images', 'edge_case'),
        ('Zero quantity ingredient', 'Handle invalid ingredient amounts', 'edge_case'),
        ('Special characters', 'Handle emoji/unicode in recipe names', 'edge_case'),
        ('Large datasets', 'App performs well with 100+ recipes', 'edge_case'),
    ],
}


def seed_test_cases():
    """Insert all test cases into database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get suite IDs
    cursor.execute("SELECT id, suite_name FROM test_suites")
    suites = {row[1]: row[0] for row in cursor.fetchall()}

    if not suites:
        print("ERROR: No test suites found! Did the database migration run?")
        print("Restart the Flask app to run init_db() first.")
        return

    display_order = 0
    total_inserted = 0

    for suite_name, test_cases in TEST_CASES.items():
        suite_id = suites.get(suite_name)
        if not suite_id:
            print(f"Warning: Suite '{suite_name}' not found in database")
            continue

        print(f"\n{suite_name} ({len(test_cases)} tests):")

        for test_name, test_description, category in test_cases:
            display_order += 1
            try:
                cursor.execute("""
                    INSERT INTO test_cases (suite_id, test_name, test_description, category, display_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (suite_id, test_name, test_description, category, display_order))
                print(f"  + {test_name}")
                total_inserted += 1
            except sqlite3.IntegrityError:
                print(f"  - Skipped (exists): {test_name}")

    conn.commit()

    # Update test_builds total_tests count
    cursor.execute("SELECT COUNT(*) FROM test_cases")
    total_tests = cursor.fetchone()[0]

    cursor.execute("""
        UPDATE test_builds
        SET total_tests = ?, not_tested = ?
        WHERE version = '1.0.1'
    """, (total_tests, total_tests))

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"SUCCESS: Seeded {total_inserted} test cases!")
    print(f"SUCCESS: Updated build '1.0.1' with {total_tests} total tests")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Seeding test cases for Food mobile app...")
    print("="*60)
    seed_test_cases()
