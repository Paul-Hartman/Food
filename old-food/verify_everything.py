"""
Comprehensive verification script for Pancake Scale Demo
Tests all systems end-to-end before demo
"""

import requests
import json
import sqlite3
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
BACKEND_URL = "http://192.168.2.38:5025"
EXPO_URL = "http://localhost:8081"
DB_PATH = "backend/food.db"
RECIPE_ID = 1125

# Test results
tests_passed = 0
tests_failed = 0
warnings = []

def test(name, func):
    """Run a test and track results"""
    global tests_passed, tests_failed
    try:
        result = func()
        if result:
            print(f"[PASS] {name}")
            tests_passed += 1
            return True
        else:
            print(f"[FAIL] {name}")
            tests_failed += 1
            return False
    except Exception as e:
        print(f"[ERROR] {name}: {str(e)}")
        tests_failed += 1
        return False

print("="*60)
print("PANCAKE SCALE DEMO - COMPREHENSIVE VERIFICATION")
print("="*60)
print()

# =============================================================================
# 1. BACKEND TESTS
# =============================================================================
print("[1] BACKEND TESTS")
print("-"*60)

def test_backend_running():
    """Test backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        return response.status_code == 200 and response.json().get("status") == "healthy"
    except:
        return False

test("Backend server running", test_backend_running)

def test_recipe_api():
    """Test recipe API returns correct data"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/recipes/{RECIPE_ID}", timeout=5)
        data = response.json()
        return (
            data["recipe"]["id"] == RECIPE_ID and
            len(data["ingredients"]) == 9 and
            len(data["steps"]) == 11
        )
    except:
        return False

test("Recipe API returns 9 ingredients, 11 steps", test_recipe_api)

def test_scale_containers_api():
    """Test scale containers endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/scale/containers", timeout=5)
        containers = response.json()
        return len(containers) == 5
    except:
        return False

test("Scale containers API returns 5 containers", test_scale_containers_api)

# =============================================================================
# 2. DATABASE TESTS
# =============================================================================
print()
print("[2] DATABASE TESTS")
print("-"*60)

def test_database_exists():
    """Test database file exists"""
    return Path(DB_PATH).exists()

test("Database file exists", test_database_exists)

def test_recipe_ingredients():
    """Test recipe has all ingredients in DB"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = ?
        """, (RECIPE_ID,))
        count = cursor.fetchone()[0]
        conn.close()
        return count == 9
    except:
        return False

test("Recipe has 9 ingredients in database", test_recipe_ingredients)

def test_timer_steps():
    """Test recipe has timer flags on correct steps"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT step_number FROM cooking_steps
            WHERE recipe_id = ? AND timer_needed = 1
            ORDER BY step_number
        """, (RECIPE_ID,))
        steps = [row[0] for row in cursor.fetchall()]
        conn.close()
        return steps == [6, 8, 9]
    except:
        return False

test("Timer flags on steps 6, 8, 9", test_timer_steps)

def test_scale_tables():
    """Test scale tables exist and have data"""
    try:
        conn = sqlite3.connect(DB_PATH)

        # Check required scale tables exist (scale_containers and scale_measurements)
        required_tables = ['scale_containers', 'scale_measurements']
        for table in required_tables:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name = ?
            """, (table,))
            if not cursor.fetchone():
                conn.close()
                return False

        # Check container data
        cursor = conn.execute("SELECT COUNT(*) FROM scale_containers")
        container_count = cursor.fetchone()[0]

        conn.close()
        return container_count == 5
    except:
        return False

test("Scale tables exist with sample data", test_scale_tables)

# =============================================================================
# 3. INGREDIENT PARSING TESTS
# =============================================================================
print()
print("[3] INGREDIENT PARSING TESTS")
print("-"*60)

def test_step1_ingredients():
    """Test Step 1 has 5 parseable ingredients"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT instruction FROM cooking_steps
            WHERE recipe_id = ? AND step_number = 1
        """, (RECIPE_ID,))
        instruction = cursor.fetchone()[0]
        conn.close()

        # Count parseable ingredients (simple check)
        ingredients = ['250g', '25g', '12g', '3g', '5g']
        return all(ing in instruction for ing in ingredients)
    except:
        return False

test("Step 1 has 5 parseable ingredients", test_step1_ingredients)

def test_step3_ingredients():
    """Test Step 3 has 4 parseable ingredients"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT instruction FROM cooking_steps
            WHERE recipe_id = ? AND step_number = 3
        """, (RECIPE_ID,))
        instruction = cursor.fetchone()[0]
        conn.close()

        # Check for all 4 ingredients with units
        ingredients = ['360ml', '2 whole', '50g', '5ml']
        return all(ing in instruction for ing in ingredients)
    except:
        return False

test("Step 3 has 4 parseable ingredients (including '2 whole eggs')", test_step3_ingredients)

# =============================================================================
# 4. EXPO/MOBILE TESTS
# =============================================================================
print()
print("[4] EXPO/MOBILE TESTS")
print("-"*60)

def test_expo_running():
    """Test Expo dev server is running"""
    try:
        response = requests.get(EXPO_URL, timeout=5)
        return response.status_code == 200 and "Food App" in response.text
    except:
        return False

test("Expo dev server running", test_expo_running)

def test_mobile_dependencies():
    """Test required dependencies are installed"""
    try:
        package_json = Path("mobile/package.json")
        if not package_json.exists():
            return False

        with open(package_json) as f:
            data = json.load(f)
            deps = data.get("dependencies", {})
            return "react-native-ble-plx" in deps and "buffer" in deps
    except:
        return False

test("Mobile dependencies (react-native-ble-plx, buffer) installed", test_mobile_dependencies)

# =============================================================================
# 5. FILE STRUCTURE TESTS
# =============================================================================
print()
print("[5] FILE STRUCTURE TESTS")
print("-"*60)

critical_files = [
    ("Backend app.py", "backend/app.py"),
    ("Mobile CookingScreen", "mobile/src/screens/CookingScreen.tsx"),
    ("ScaleMeasureModal", "mobile/src/components/ScaleMeasureModal.tsx"),
    ("BluetoothScaleService", "mobile/src/services/BluetoothScaleService.ts"),
    ("API service", "mobile/src/services/api.ts"),
]

for name, path in critical_files:
    test(f"{name} exists", lambda p=path: Path(p).exists())

# =============================================================================
# 6. API ENDPOINT TESTS
# =============================================================================
print()
print("[6] API ENDPOINT TESTS (Sample)")
print("-"*60)

scale_endpoints = [
    "/api/scale/containers",
    "/api/scale/measurements",
]

for endpoint in scale_endpoints:
    def test_endpoint(ep=endpoint):
        try:
            response = requests.get(f"{BACKEND_URL}{ep}", timeout=5)
            return response.status_code in [200, 201]
        except:
            return False

    test(f"GET {endpoint}", test_endpoint)

# =============================================================================
# 7. WARNINGS CHECK
# =============================================================================
print()
print("[7] WARNINGS")
print("-"*60)

# Check for common issues
def check_warnings():
    global warnings

    # Check if servers have been running long
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=2)
        # Backend is responsive
    except:
        warnings.append("Backend may need restart for fresh state")

    # Check mobile compilation
    try:
        response = requests.get(f"{EXPO_URL}", timeout=2)
        if "error" in response.text.lower():
            warnings.append("Expo may have compilation errors")
    except:
        warnings.append("Expo server not responding")

check_warnings()

if warnings:
    for warning in warnings:
        print(f"[WARN] {warning}")
else:
    print("[OK] No warnings")

# =============================================================================
# SUMMARY
# =============================================================================
print()
print("="*60)
print("VERIFICATION SUMMARY")
print("="*60)
print(f"Tests Passed:  {tests_passed}")
print(f"Tests Failed:  {tests_failed}")
print(f"Warnings:      {len(warnings)}")
print()

if tests_failed == 0:
    print("[SUCCESS] ALL SYSTEMS READY FOR DEMO!")
    print()
    print("Next steps:")
    print("  1. Open http://localhost:8081")
    print("  2. Navigate to Recipes -> Search 'Pancake'")
    print("  3. Open Recipe 1125")
    print("  4. Start measuring ingredients!")
    sys.exit(0)
else:
    print("[FAILURE] Some tests failed - check issues above")
    print()
    print("Recommended actions:")
    print("  - Restart backend: cd backend && python app.py")
    print("  - Restart Expo: cd mobile && npm start")
    print("  - Check TROUBLESHOOTING section in docs")
    sys.exit(1)
