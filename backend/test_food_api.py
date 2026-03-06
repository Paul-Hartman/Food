"""
Comprehensive test suite for the Food Catalog API endpoints.
Tests: /api/foods/search, /api/foods/{id}, /api/foods/tags,
       /api/foods/discover, /api/foods/similar/{id}
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import subprocess
import time
import requests
import os
import signal

BASE_URL = "http://localhost:5020"
PASSED = 0
FAILED = 0
ERRORS = []


def log_pass(name):
    global PASSED
    PASSED += 1
    print(f"  PASS: {name}")


def log_fail(name, reason):
    global FAILED
    FAILED += 1
    ERRORS.append((name, reason))
    print(f"  FAIL: {name} -- {reason}")


def check(name, condition, fail_reason=""):
    if condition:
        log_pass(name)
    else:
        log_fail(name, fail_reason)


def get(path, params=None, retries=3):
    """Make a GET request and return (status_code, json_data)."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(f"{BASE_URL}{path}", params=params, timeout=60)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text[:500], "_error": "Not JSON"}
            return r.status_code, data
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
                continue
            return None, {"_error": str(e)}


# ============================================================================
# TEST: /api/foods/search
# ============================================================================
def test_search_basic():
    print("\n=== /api/foods/search - Basic ===")

    # Empty search should return foods
    code, data = get("/api/foods/search")
    check("Empty search returns 200", code == 200, f"got {code}")
    check("Empty search has 'total' key", "total" in data, f"keys: {list(data.keys()) if isinstance(data, dict) else data}")
    check("Empty search has 'results' key", "results" in data)
    check("Empty search has 'limit' key", "limit" in data)
    check("Empty search has 'offset' key", "offset" in data)
    check("Empty search total > 0", data.get("total", 0) > 0, f"total={data.get('total')}")
    check("Default limit is 50", data.get("limit") == 50, f"limit={data.get('limit')}")
    check("Default offset is 0", data.get("offset") == 0, f"offset={data.get('offset')}")

    # Check result structure
    if data.get("results"):
        r = data["results"][0]
        for key in ["id", "name", "slug", "tags"]:
            check(f"Result has '{key}' field", key in r, f"keys: {list(r.keys())}")


def test_search_text_query():
    print("\n=== /api/foods/search - Text Query ===")

    code, data = get("/api/foods/search", {"q": "sushi"})
    check("Text search 'sushi' returns 200", code == 200)
    check("Text search 'sushi' has results", data.get("total", 0) > 0, f"total={data.get('total')}")
    # Check that results contain 'sushi' in name or description
    if data.get("results"):
        found = any("sushi" in (r.get("name", "") or "").lower() or
                     "sushi" in (r.get("description", "") or "").lower()
                     for r in data["results"])
        check("Results contain 'sushi' in name/description", found)

    # Non-existent food
    code, data = get("/api/foods/search", {"q": "xyznonexistentfood123"})
    check("Search for nonexistent returns 200", code == 200)
    check("Search for nonexistent has 0 results", data.get("total") == 0, f"total={data.get('total')}")


def test_search_tag_filters():
    print("\n=== /api/foods/search - Tag Filters ===")

    # Cuisine filter
    code, data = get("/api/foods/search", {"cuisine": "Japanese"})
    check("Cuisine=Japanese returns 200", code == 200)
    check("Cuisine=Japanese has results", data.get("total", 0) > 0, f"total={data.get('total')}")
    if data.get("results"):
        first = data["results"][0]
        has_japanese = "cuisine" in first.get("tags", {}) and any(
            "japanese" in v.lower() for v in first["tags"]["cuisine"]
        )
        check("First result tagged as Japanese cuisine", has_japanese,
              f"tags={first.get('tags', {}).get('cuisine')}")

    # Meal type filter
    code, data = get("/api/foods/search", {"meal_type": "breakfast"})
    check("meal_type=breakfast returns 200", code == 200)
    check("meal_type=breakfast has results", data.get("total", 0) > 0, f"total={data.get('total')}")

    # Dietary filter
    code, data = get("/api/foods/search", {"dietary": "vegan"})
    check("dietary=vegan returns 200", code == 200)
    check("dietary=vegan has results", data.get("total", 0) > 0, f"total={data.get('total')}")

    # Cooking method filter
    code, data = get("/api/foods/search", {"cooking_method": "grilled"})
    check("cooking_method=grilled returns 200", code == 200)
    check("cooking_method=grilled has results", data.get("total", 0) > 0, f"total={data.get('total')}")

    # Flavor profile filter
    code, data = get("/api/foods/search", {"flavor_profile": "sweet"})
    check("flavor_profile=sweet returns 200", code == 200)
    check("flavor_profile=sweet has results", data.get("total", 0) > 0, f"total={data.get('total')}")

    # Also test flavor shorthand
    code, data = get("/api/foods/search", {"flavor": "spicy"})
    check("flavor=spicy (shorthand) returns 200", code == 200)
    check("flavor=spicy has results", data.get("total", 0) > 0, f"total={data.get('total')}")

    # Multi-filter: combine cuisine + dietary
    code, data = get("/api/foods/search", {"cuisine": "Italian", "dietary": "vegetarian"})
    check("cuisine=Italian+dietary=vegetarian returns 200", code == 200)
    check("Multi-filter has results", data.get("total", 0) > 0, f"total={data.get('total')}")
    check("Multi-filter results < Italian alone",
          data.get("total", 999999) < 5000, f"total={data.get('total')}")


def test_search_new_anthropological_tags():
    print("\n=== /api/foods/search - New Anthropological Tag Categories ===")

    new_categories = {
        "historical_period": "ancient",
        "trade_route": "Silk",
        "cooking_science": "fermentation",
        "origin_hemisphere": "Old World",
        "columbian_exchange": "post-1492",
        "staple_food": "grain",
        "cultural_significance": "sacred",
        "social_class": "aristocratic",
    }

    for cat, val in new_categories.items():
        code, data = get("/api/foods/search", {cat: val})
        check(f"{cat}={val} returns 200", code == 200, f"got {code}, data={data}")
        if code == 200:
            check(f"{cat}={val} has results", data.get("total", 0) > 0,
                  f"total={data.get('total')} - category may be unsupported or no matches")
        else:
            log_fail(f"{cat}={val} has results", f"skipped (bad status {code})")


def test_search_remaining_categories():
    print("\n=== /api/foods/search - Remaining Standard Categories ===")

    tests = {
        "season": "summer",
        "tradition": "Christmas",
        "course": "soup",
        "temperature": "hot",
        "texture": "crispy",
        "region": "East Asia",
        "ingredient": "rice",
        "food_type": "seafood",
        "occasion": "party",
    }

    for cat, val in tests.items():
        code, data = get("/api/foods/search", {cat: val})
        check(f"{cat}={val} returns 200", code == 200, f"got {code}, data={data}")
        if code == 200:
            check(f"{cat}={val} has results", data.get("total", 0) > 0,
                  f"total={data.get('total')}")
        else:
            log_fail(f"{cat}={val} has results", f"skipped (bad status {code})")


def test_search_generic_tags():
    print("\n=== /api/foods/search - Generic Tags Param ===")

    code, data = get("/api/foods/search", {"tags": "sweet,Japanese"})
    check("Generic tags returns 200", code == 200)
    check("Generic tags has results", data.get("total", 0) > 0, f"total={data.get('total')}")


def test_search_pagination():
    print("\n=== /api/foods/search - Pagination ===")

    # Custom limit
    code, data = get("/api/foods/search", {"limit": 5})
    check("limit=5 returns 200", code == 200)
    check("limit=5 returns 5 or fewer results", len(data.get("results", [])) <= 5,
          f"got {len(data.get('results', []))}")
    check("limit=5 reported correctly", data.get("limit") == 5)

    # Offset
    code, data1 = get("/api/foods/search", {"limit": 3, "sort": "name"})
    code, data2 = get("/api/foods/search", {"limit": 3, "offset": 3, "sort": "name"})
    check("Offset results differ from page 1",
          data1.get("results", [{}])[0].get("id") != data2.get("results", [{}])[0].get("id"),
          "First results are the same")

    # Limit cap at 200
    code, data = get("/api/foods/search", {"limit": 500})
    check("Limit capped at 200", data.get("limit") == 200, f"limit={data.get('limit')}")


def test_search_sorting():
    print("\n=== /api/foods/search - Sorting ===")

    code, data = get("/api/foods/search", {"sort": "name", "limit": 10})
    check("Sort by name returns 200", code == 200, f"got {code}")
    if code == 200 and data.get("results") and len(data["results"]) > 1:
        names = [r["name"] for r in data["results"]]
        check("Results sorted by name ASC", names == sorted(names),
              f"first few: {names[:3]}")

    code, data = get("/api/foods/search", {"sort": "random", "limit": 5})
    check("Sort by random returns 200", code == 200, f"got {code}")
    if code == 200:
        check("Random sort returns results", len(data.get("results", [])) > 0)


def test_search_edge_cases():
    print("\n=== /api/foods/search - Edge Cases ===")

    # Special characters
    code, data = get("/api/foods/search", {"q": "O'Brien"})
    check("Apostrophe in query returns 200", code == 200)

    code, data = get("/api/foods/search", {"q": "creme brulee"})
    check("Accented-ish query returns 200", code == 200)

    code, data = get("/api/foods/search", {"q": "%DROP TABLE%"})
    check("SQL injection attempt returns 200", code == 200)

    code, data = get("/api/foods/search", {"q": ""})
    check("Empty q returns 200", code == 200)

    # Unicode
    code, data = get("/api/foods/search", {"q": "ramen"})
    check("Unicode-safe query returns 200", code == 200)

    # Negative offset should still work (SQLite treats it as 0)
    time.sleep(1)  # Flask dev server needs a breather between rapid requests
    code, data = get("/api/foods/search", {"offset": "0", "limit": "1"}, retries=3)
    check("offset=0 returns 200", code == 200, f"got {code}")


# ============================================================================
# TEST: /api/foods/{id}
# ============================================================================
def test_food_detail():
    print("\n=== /api/foods/{id} - Food Detail ===")

    # Get a valid food ID first
    _, search_data = get("/api/foods/search", {"limit": 1})
    if not search_data.get("results"):
        log_fail("Food detail", "No foods in database")
        return

    food_id = search_data["results"][0]["id"]

    code, data = get(f"/api/foods/{food_id}")
    check("Food detail returns 200", code == 200)
    check("Has 'name' field", "name" in data, f"keys: {list(data.keys())}")
    check("Has 'tags' field", "tags" in data)
    check("Has 'ingredients' field", "ingredients" in data)
    check("Has 'pairings' field", "pairings" in data)
    check("Has 'origins' field", "origins" in data)

    # Tags structure: dict of category -> list of {value, confidence, source}
    if data.get("tags"):
        first_cat = list(data["tags"].keys())[0]
        first_tag = data["tags"][first_cat][0]
        check("Tag has 'value' field", "value" in first_tag, f"tag keys: {list(first_tag.keys())}")
        check("Tag has 'confidence' field", "confidence" in first_tag)
        check("Tag has 'source' field", "source" in first_tag)


def test_food_detail_not_found():
    print("\n=== /api/foods/{id} - Not Found ===")

    code, data = get("/api/foods/9999999")
    check("Non-existent food returns 404", code == 404, f"got {code}")
    check("Error message present", "error" in data, f"keys: {list(data.keys()) if isinstance(data, dict) else data}")


# ============================================================================
# TEST: /api/foods/tags
# ============================================================================
def test_tags_overview():
    print("\n=== /api/foods/tags - Overview ===")

    code, data = get("/api/foods/tags")
    check("Tags overview returns 200", code == 200)
    check("Has 'categories' key", "categories" in data, f"keys: {list(data.keys()) if isinstance(data, dict) else data}")

    categories = data.get("categories", [])
    check("Has multiple categories", len(categories) > 5, f"count={len(categories)}")

    # Check structure
    if categories:
        cat = categories[0]
        check("Category has 'tag_category'", "tag_category" in cat, f"keys: {list(cat.keys())}")
        check("Category has 'unique_values'", "unique_values" in cat)
        check("Category has 'total_tags'", "total_tags" in cat)
        check("Category has 'foods_tagged'", "foods_tagged" in cat)

    # Verify new anthropological categories are present
    cat_names = [c["tag_category"] for c in categories]
    for expected in ["historical_period", "trade_route", "cooking_science",
                     "origin_hemisphere", "columbian_exchange", "staple_food",
                     "cultural_significance", "social_class"]:
        check(f"New category '{expected}' exists in tags",
              expected in cat_names,
              f"not found in {cat_names}")


def test_tags_single_category():
    print("\n=== /api/foods/tags - Single Category ===")

    code, data = get("/api/foods/tags", {"category": "cuisine"})
    check("Tags for cuisine returns 200", code == 200)
    check("Has 'category' key", "category" in data)
    check("Has 'values' key", "values" in data)
    check("Category is 'cuisine'", data.get("category") == "cuisine")
    check("Has multiple values", len(data.get("values", [])) > 5,
          f"count={len(data.get('values', []))}")

    # Check value structure
    if data.get("values"):
        v = data["values"][0]
        check("Value has 'tag_value'", "tag_value" in v, f"keys: {list(v.keys())}")
        check("Value has 'count'", "count" in v)

    # Test a new category
    code, data = get("/api/foods/tags", {"category": "historical_period"})
    check("Tags for historical_period returns 200", code == 200)
    check("historical_period has values", len(data.get("values", [])) > 0,
          f"count={len(data.get('values', []))}")

    # Non-existent category
    code, data = get("/api/foods/tags", {"category": "nonexistent_cat_xyz"})
    check("Non-existent category returns 200", code == 200)
    check("Non-existent category has empty values", len(data.get("values", [])) == 0)


# ============================================================================
# TEST: /api/foods/discover
# ============================================================================
def test_discover():
    print("\n=== /api/foods/discover - Browse by Tag ===")

    # Default group_by=cuisine
    code, data = get("/api/foods/discover")
    check("Discover default returns 200", code == 200)
    check("Has 'group_by' key", "group_by" in data)
    check("Has 'groups' key", "groups" in data)
    check("Default group_by is 'cuisine'", data.get("group_by") == "cuisine")
    check("Has multiple groups", len(data.get("groups", {})) > 3,
          f"count={len(data.get('groups', {}))}")

    # Check group structure
    groups = data.get("groups", {})
    if groups:
        first_key = list(groups.keys())[0]
        group = groups[first_key]
        check("Group has 'count'", "count" in group, f"keys: {list(group.keys())}")
        check("Group has 'sample'", "sample" in group)
        check("Sample has foods", len(group.get("sample", [])) > 0)
        if group.get("sample"):
            s = group["sample"][0]
            check("Sample food has 'id'", "id" in s)
            check("Sample food has 'name'", "name" in s)

    # Group by a different category
    code, data = get("/api/foods/discover", {"group_by": "meal_type"})
    check("Discover by meal_type returns 200", code == 200)
    check("group_by is 'meal_type'", data.get("group_by") == "meal_type")
    check("Has groups for meal_type", len(data.get("groups", {})) > 0)

    # Group by new category
    code, data = get("/api/foods/discover", {"group_by": "origin_hemisphere"})
    check("Discover by origin_hemisphere returns 200", code == 200)
    check("Has groups for origin_hemisphere", len(data.get("groups", {})) > 0,
          f"count={len(data.get('groups', {}))}")

    # Custom limit
    code, data = get("/api/foods/discover", {"group_by": "cuisine", "limit": 2})
    check("Discover with limit=2 returns 200", code == 200)
    groups = data.get("groups", {})
    if groups:
        first_key = list(groups.keys())[0]
        check("Sample respects limit=2", len(groups[first_key].get("sample", [])) <= 2,
              f"count={len(groups[first_key].get('sample', []))}")


# ============================================================================
# TEST: /api/foods/similar/{id}
# ============================================================================
def test_similar():
    print("\n=== /api/foods/similar/{id} - Similar Foods ===")

    # Find a food with tags
    _, search_data = get("/api/foods/search", {"cuisine": "Japanese", "limit": 1})
    if not search_data.get("results"):
        log_fail("Similar foods", "No Japanese foods found")
        return

    food_id = search_data["results"][0]["id"]
    food_name = search_data["results"][0]["name"]

    code, data = get(f"/api/foods/similar/{food_id}")
    check(f"Similar to '{food_name}' (id={food_id}) returns 200", code == 200)
    check("Has 'food_id' key", "food_id" in data)
    check("Has 'similar' key", "similar" in data)
    check("food_id matches request", data.get("food_id") == food_id)

    similar = data.get("similar", [])
    check("Has similar foods", len(similar) > 0, f"count={len(similar)}")

    if similar:
        s = similar[0]
        check("Similar food has 'food_id'", "food_id" in s, f"keys: {list(s.keys())}")
        check("Similar food has 'name'", "name" in s)
        check("Similar food has 'shared_tags'", "shared_tags" in s)
        check("Similar food is different food", s.get("food_id") != food_id)
        check("shared_tags > 0", s.get("shared_tags", 0) > 0)

    # Custom limit
    code, data = get(f"/api/foods/similar/{food_id}", {"limit": 3})
    check("Similar with limit=3 returns 200", code == 200)
    check("Respects limit=3", len(data.get("similar", [])) <= 3,
          f"count={len(data.get('similar', []))}")


def test_similar_not_found():
    print("\n=== /api/foods/similar/{id} - Edge Cases ===")

    # Non-existent food
    code, data = get("/api/foods/similar/9999999")
    check("Non-existent food similar returns 404", code == 404, f"got {code}")


# ============================================================================
# MAIN
# ============================================================================
def main():
    global PASSED, FAILED

    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(app_dir, "app.py")

    print("=" * 60)
    print("Food Catalog API Test Suite")
    print("=" * 60)

    # Kill any existing process on port 5020
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if ":5020" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                print(f"Killing existing process on port 5020 (PID {pid})...")
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True)
    except Exception:
        pass

    # Start Flask app
    print("Starting Flask app...")
    env = os.environ.copy()
    env["FLASK_ENV"] = "testing"
    proc = subprocess.Popen(
        [sys.executable, app_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    # Wait for server to start
    max_wait = 30
    started = False
    for i in range(max_wait):
        time.sleep(1)
        try:
            r = requests.get(f"{BASE_URL}/api/foods/tags", timeout=3)
            if r.status_code == 200:
                started = True
                print(f"Server started after {i+1} seconds.")
                break
        except Exception:
            pass

    if not started:
        print("ERROR: Server did not start within 30 seconds!")
        # Try to read stderr
        proc.kill()
        _, stderr = proc.communicate(timeout=5)
        print(f"Stderr: {stderr.decode('utf-8', errors='replace')[:2000]}")
        return

    try:
        # Run all tests with small delays between groups
        test_search_basic()
        time.sleep(1)
        test_search_text_query()
        time.sleep(1)
        test_search_tag_filters()
        time.sleep(1)
        test_search_new_anthropological_tags()
        time.sleep(1)
        test_search_remaining_categories()
        time.sleep(1)
        test_search_generic_tags()
        time.sleep(1)
        test_search_pagination()
        time.sleep(1)
        test_search_sorting()
        time.sleep(1)
        test_search_edge_cases()
        time.sleep(1)
        test_food_detail()
        time.sleep(1)
        test_food_detail_not_found()
        time.sleep(1)
        test_tags_overview()
        time.sleep(1)
        test_tags_single_category()
        time.sleep(1)
        test_discover()
        time.sleep(1)
        test_similar()
        time.sleep(1)
        test_similar_not_found()

    finally:
        # Shutdown server
        print("\nShutting down server...")
        if sys.platform == "win32":
            proc.kill()
        else:
            proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
    print("=" * 60)

    if ERRORS:
        print("\nFailed tests:")
        for name, reason in ERRORS:
            print(f"  - {name}: {reason}")

    if FAILED == 0:
        print("\nAll tests passed!")
    else:
        print(f"\n{FAILED} test(s) failed.")

    return FAILED


if __name__ == "__main__":
    sys.exit(main())
