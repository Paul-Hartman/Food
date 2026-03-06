#!/usr/bin/env python3
"""
USDA FoodData Central API Importer

Fetches nutritional data from USDA FoodData Central and imports into food database.
Free API with 900,000+ foods and comprehensive nutritional profiles.

API Documentation: https://fdc.nal.usda.gov/api-guide.html

Requirements:
- Free API key from: https://fdc.nal.usda.gov/api-key-signup.html
- Set environment variable: USDA_API_KEY=your_key_here

Features:
- Search by ingredient name
- Fetch detailed nutritional profiles
- Automatic import to database
- Rate limiting (1000 requests/hour free tier)
- Caching to avoid redundant calls
- Support for multiple data types (Foundation, SR Legacy, Branded)

Author: Claude
Date: 2025-11-20
"""

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests


@dataclass
class USDAFood:
    """USDA food item"""

    fdc_id: str
    description: str
    data_type: str  # Foundation, SR Legacy, Survey (FNDDS), Branded
    publication_date: str
    nutrients: Dict[str, float]  # nutrient_name -> amount
    category: Optional[str] = None
    scientific_name: Optional[str] = None


class USDAAPIImporter:
    """
    Import nutritional data from USDA FoodData Central API.

    Free tier: 1000 requests/hour
    Paid tier: 3600 requests/hour ($0.00 per request)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        db_path: str = "food_ingredients.db",
        cache_path: str = "usda_cache.db",
    ):
        self.api_key = api_key or os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "USDA API key required. Get one at: "
                "https://fdc.nal.usda.gov/api-key-signup.html\n"
                "Set environment variable: USDA_API_KEY=your_key_here"
            )

        self.db_path = db_path
        self.cache_path = cache_path

        self.base_url = "https://api.nal.usda.gov/fdc/v1"

        # Rate limiting
        self.requests_per_hour = 1000  # Free tier
        self.request_interval = 3600.0 / self.requests_per_hour  # seconds
        self.last_request_time = 0.0

        # Initialize cache
        self._initialize_cache()

        # USDA nutrient ID to our database field mapping
        self.nutrient_mapping = self._initialize_nutrient_mapping()

    def _initialize_cache(self):
        """Create cache database to avoid redundant API calls"""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usda_cache (
                fdc_id TEXT PRIMARY KEY,
                description TEXT,
                data_type TEXT,
                response_json TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS search_cache (
                query TEXT PRIMARY KEY,
                results_json TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def _initialize_nutrient_mapping(self) -> Dict[int, str]:
        """
        Map USDA nutrient IDs to our database fields.

        USDA uses numeric IDs for nutrients. This maps to our field names.
        """
        return {
            # Energy
            1008: "calories_kcal",
            # Macronutrients
            1003: "protein_g",
            1004: "total_fat_g",
            1005: "carbohydrate_g",
            1079: "fiber_g",
            2000: "total_sugars_g",
            # Fats
            1258: "saturated_fat_g",
            1293: "monounsaturated_fat_g",
            1292: "polyunsaturated_fat_g",
            1257: "trans_fat_g",
            1253: "cholesterol_mg",
            # Vitamins
            1106: "vitamin_a_ug_rae",
            1162: "vitamin_c_mg",
            1114: "vitamin_d_ug",
            1109: "vitamin_e_mg",
            1185: "vitamin_k_ug",
            1165: "thiamin_mg",
            1166: "riboflavin_mg",
            1167: "niacin_mg",
            1170: "vitamin_b6_mg",
            1177: "folate_ug_dfe",
            1178: "vitamin_b12_ug",
            # Minerals
            1087: "calcium_mg",
            1089: "iron_mg",
            1090: "magnesium_mg",
            1091: "phosphorus_mg",
            1092: "potassium_mg",
            1093: "sodium_mg",
            1095: "zinc_mg",
            1098: "copper_mg",
            1101: "manganese_mg",
            1103: "selenium_ug",
            # Other
            1051: "water_g",
        }

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            sleep_time = self.request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _get_from_cache(self, fdc_id: str) -> Optional[Dict]:
        """Retrieve cached food data"""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()

        cursor.execute("SELECT response_json FROM usda_cache WHERE fdc_id = ?", (fdc_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def _save_to_cache(self, fdc_id: str, description: str, data_type: str, response: Dict):
        """Cache food data"""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO usda_cache (fdc_id, description, data_type, response_json)
            VALUES (?, ?, ?, ?)
            """,
            (fdc_id, description, data_type, json.dumps(response)),
        )

        conn.commit()
        conn.close()

    def search_foods(
        self, query: str, data_type: Optional[str] = None, page_size: int = 10
    ) -> List[Tuple[str, str, str]]:
        """
        Search for foods by name.

        Args:
            query: Search term (e.g., "apple", "chicken breast")
            data_type: Filter by type: "Foundation", "SR Legacy", "Branded", "Survey (FNDDS)"
            page_size: Number of results (max 200)

        Returns:
            List of (fdc_id, description, data_type)
        """
        # Check search cache first
        cache_key = f"{query}|{data_type}|{page_size}"
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute("SELECT results_json FROM search_cache WHERE query = ?", (cache_key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            print(f"[Cache hit] Search: {query}")
            return json.loads(row[0])

        # Make API request
        self._rate_limit()

        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": min(page_size, 200),
        }

        if data_type:
            params["dataType"] = data_type

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"[Error] Search failed: {e}")
            return []

        # Parse results
        results = []
        for food in data.get("foods", []):
            fdc_id = str(food.get("fdcId", ""))
            description = food.get("description", "")
            dtype = food.get("dataType", "")
            results.append((fdc_id, description, dtype))

        # Cache results
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO search_cache (query, results_json)
            VALUES (?, ?)
            """,
            (cache_key, json.dumps(results)),
        )
        conn.commit()
        conn.close()

        return results

    def get_food_details(self, fdc_id: str) -> Optional[USDAFood]:
        """
        Fetch detailed nutritional information for a food.

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            USDAFood object with complete nutritional profile
        """
        # Check cache first
        cached = self._get_from_cache(fdc_id)
        if cached:
            print(f"[Cache hit] FDC ID: {fdc_id}")
            return self._parse_food_response(cached)

        # Make API request
        self._rate_limit()

        url = f"{self.base_url}/food/{fdc_id}"
        params = {
            "api_key": self.api_key,
            "format": "full",  # Get all nutrients
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"[Error] Failed to fetch FDC ID {fdc_id}: {e}")
            return None

        # Cache response
        description = data.get("description", "")
        data_type = data.get("dataType", "")
        self._save_to_cache(fdc_id, description, data_type, data)

        return self._parse_food_response(data)

    def _parse_food_response(self, data: Dict) -> USDAFood:
        """Parse USDA API response into USDAFood object"""
        fdc_id = str(data.get("fdcId", ""))
        description = data.get("description", "")
        data_type = data.get("dataType", "")
        publication_date = data.get("publicationDate", "")

        # Extract category
        category = None
        if "foodCategory" in data and data["foodCategory"]:
            category = data["foodCategory"].get("description")

        # Extract scientific name (if available)
        scientific_name = data.get("scientificName")

        # Parse nutrients
        nutrients = {}
        for nutrient_data in data.get("foodNutrients", []):
            nutrient_id = nutrient_data.get("nutrient", {}).get("id")
            nutrient_name = nutrient_data.get("nutrient", {}).get("name", "")

            # Get amount (handle different data structures)
            amount = nutrient_data.get("amount")
            if amount is None:
                amount = nutrient_data.get("value")  # Alternative field name

            if nutrient_id and amount is not None:
                # Map to our field name
                field_name = self.nutrient_mapping.get(nutrient_id)
                if field_name:
                    nutrients[field_name] = float(amount)
                else:
                    # Store unmapped nutrients with their names
                    nutrients[nutrient_name] = float(amount)

        return USDAFood(
            fdc_id=fdc_id,
            description=description,
            data_type=data_type,
            publication_date=publication_date,
            nutrients=nutrients,
            category=category,
            scientific_name=scientific_name,
        )

    def import_to_database(
        self,
        usda_food: USDAFood,
        ingredient_name: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """
        Import USDA food into our food ingredients database.

        Args:
            usda_food: USDAFood object from API
            ingredient_name: Override ingredient name (default: use USDA description)
            category: Override category (default: use USDA category)

        Returns:
            ingredient_id in our database
        """
        from .food_ingredient_manager import FoodIngredientManager

        manager = FoodIngredientManager(self.db_path)

        # Prepare ingredient data
        name = ingredient_name or usda_food.description
        cat = category or usda_food.category or "unknown"

        # Add ingredient
        ingredient_id = manager.add_ingredient(
            name=name,
            category=cat,
            scientific_name=usda_food.scientific_name,
            usda_fdc_id=usda_food.fdc_id,
        )

        # Add nutritional profile
        manager.add_nutritional_profile(ingredient_id, usda_food.nutrients)

        print(f"[Imported] {name} (FDC ID: {usda_food.fdc_id})")

        return ingredient_id

    def batch_import(
        self, search_queries: List[str], max_per_query: int = 3, data_type: str = "Foundation"
    ) -> List[int]:
        """
        Batch import multiple ingredients.

        Args:
            search_queries: List of ingredient names to search
            max_per_query: Maximum results to import per query
            data_type: Prefer "Foundation" (cleanest) or "SR Legacy" (comprehensive)

        Returns:
            List of imported ingredient IDs
        """
        imported_ids = []

        for query in search_queries:
            print(f"\n[Searching] {query}...")

            # Search
            results = self.search_foods(query, data_type=data_type, page_size=max_per_query)

            if not results:
                print(f"  No results found for: {query}")
                continue

            # Import top results
            for i, (fdc_id, description, dtype) in enumerate(results[:max_per_query]):
                print(f"  [{i+1}/{len(results[:max_per_query])}] {description}")

                # Get details
                usda_food = self.get_food_details(fdc_id)

                if not usda_food:
                    continue

                # Import
                try:
                    ingredient_id = self.import_to_database(usda_food)
                    imported_ids.append(ingredient_id)
                except sqlite3.IntegrityError:
                    print(f"    [Skip] Already exists")

        return imported_ids

    def get_statistics(self) -> Dict:
        """Get cache statistics"""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM usda_cache")
        cached_foods = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM search_cache")
        cached_searches = cursor.fetchone()[0]

        conn.close()

        return {
            "cached_foods": cached_foods,
            "cached_searches": cached_searches,
            "requests_saved": cached_foods + cached_searches,
        }


# ============================================================================
# DEMONSTRATION / TEST CODE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("USDA API IMPORTER DEMONSTRATION")
    print("=" * 70)
    print()

    # Check for API key
    api_key = os.getenv("USDA_API_KEY")
    if not api_key:
        print("⚠️  USDA_API_KEY environment variable not set!")
        print()
        print("To use this importer:")
        print("1. Get free API key: https://fdc.nal.usda.gov/api-key-signup.html")
        print("2. Set environment variable:")
        print("   export USDA_API_KEY=your_key_here")
        print()
        print("For now, showing mock demonstration...")
        print("=" * 70)

        # Mock demonstration
        print()
        print("EXAMPLE: Searching for 'apple'")
        print("-" * 70)
        print("Results:")
        print("  1. Apple, raw, with skin (FDC ID: 171688)")
        print("     Type: SR Legacy")
        print("  2. Apple, raw, without skin (FDC ID: 171689)")
        print("     Type: SR Legacy")
        print("  3. Apple juice, canned or bottled (FDC ID: 171691)")
        print("     Type: SR Legacy")
        print()

        print("EXAMPLE: Nutritional profile for 'Apple, raw, with skin'")
        print("-" * 70)
        print("  Calories: 52 kcal")
        print("  Protein: 0.26 g")
        print("  Total fat: 0.17 g")
        print("  Carbohydrate: 13.81 g")
        print("  Fiber: 2.4 g")
        print("  Total sugars: 10.39 g")
        print("  Vitamin C: 4.6 mg")
        print("  Potassium: 107 mg")
        print("  Calcium: 6 mg")
        print()

        print("=" * 70)
        print("With a valid API key, this script will:")
        print("  1. Search USDA database (900,000+ foods)")
        print("  2. Fetch detailed nutritional profiles")
        print("  3. Import into food_ingredients.db")
        print("  4. Cache results to avoid redundant API calls")
        print("  5. Respect rate limits (1000 requests/hour free)")
        print("=" * 70)

        exit(0)

    # Real demonstration with API key
    try:
        importer = USDAAPIImporter()

        # Example 1: Search for an ingredient
        print("EXAMPLE 1: Searching for 'chicken breast'")
        print("-" * 70)
        results = importer.search_foods("chicken breast", data_type="Foundation", page_size=5)

        for i, (fdc_id, description, data_type) in enumerate(results, 1):
            print(f"{i}. {description}")
            print(f"   FDC ID: {fdc_id}, Type: {data_type}")
        print()

        # Example 2: Get detailed nutrition
        if results:
            fdc_id = results[0][0]
            print(f"EXAMPLE 2: Detailed nutrition for FDC ID {fdc_id}")
            print("-" * 70)

            food = importer.get_food_details(fdc_id)
            if food:
                print(f"Description: {food.description}")
                print(f"Data Type: {food.data_type}")
                print(f"Category: {food.category}")
                print()
                print("Nutrients (per 100g):")
                for nutrient, value in sorted(food.nutrients.items())[:15]:  # First 15
                    print(f"  {nutrient}: {value}")
                if len(food.nutrients) > 15:
                    print(f"  ... and {len(food.nutrients) - 15} more nutrients")
            print()

        # Example 3: Batch import
        print("EXAMPLE 3: Batch import basic ingredients")
        print("-" * 70)

        basic_ingredients = [
            "apple",
            "banana",
            "carrot",
            "tomato",
            "onion",
        ]

        print(f"Importing {len(basic_ingredients)} ingredients...")
        print("(This respects rate limits, may take a moment)")
        print()

        imported = importer.batch_import(
            basic_ingredients,
            max_per_query=1,  # Just one per ingredient for demo
            data_type="Foundation",
        )

        print()
        print(f"✓ Imported {len(imported)} ingredients successfully")
        print()

        # Example 4: Statistics
        print("EXAMPLE 4: Cache statistics")
        print("-" * 70)
        stats = importer.get_statistics()
        print(f"Cached foods: {stats['cached_foods']}")
        print(f"Cached searches: {stats['cached_searches']}")
        print(f"Total API requests saved: {stats['requests_saved']}")
        print()

        print("=" * 70)
        print("SUCCESS! USDA data successfully imported.")
        print("Data is now available in food_ingredients.db")
        print("=" * 70)

    except ValueError as e:
        print(f"[Error] {e}")
    except Exception as e:
        print(f"[Error] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
