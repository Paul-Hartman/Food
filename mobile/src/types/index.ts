// Types for Food App
import { NavigatorScreenParams } from '@react-navigation/native';

export interface Recipe {
  id: number;
  name: string;
  description: string;
  category: 'main' | 'side';
  cuisine: string;
  prep_time_min: number;
  cook_time_min: number;
  servings: number;
  difficulty: 'easy' | 'medium' | 'hard';
  image_url: string | null;
}

export interface Ingredient {
  id: number;
  name: string;
  category: string;
  aldi_section: string;
  default_unit: string;
  calories_per_100g: number;
  protein_per_100g: number;
  carbs_per_100g: number;
  fat_per_100g: number;
  fiber_per_100g: number;
  grams_per_unit: number;
}

export interface RecipeIngredient {
  id: number;
  recipe_id: number;
  ingredient_id: number;
  quantity: number;
  unit: string;
  notes: string | null;
  name: string;
  aldi_section: string;
}

export interface CookingStep {
  id?: number;
  recipe_id?: number;
  step_number: number;
  title: string;
  instruction: string;
  duration_min: number | null;
  tips: string | null;
  timer_needed: boolean | number;
  step_type?: string;
  ingredients?: any[];
}

export interface RecipeDetail {
  recipe: Recipe;
  ingredients: RecipeIngredient[];
  steps: CookingStep[];
  nutrition_per_serving: Nutrition;
}

export interface Nutrition {
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber: number;
}

export interface ShoppingItem {
  id: number;
  ingredient_id: number;
  quantity: number;
  unit: string;
  checked: boolean;
  name: string;
  aldi_section: string;
  recipe_name: string | null;
}

export interface ShoppingData {
  sections: Record<string, ShoppingItem[]>;
  section_order: string[];
}

export interface PantryItem {
  id: number;
  ingredient_id: number;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  expires_at: string | null;
  price: number | null;
  image_url?: string | null;

  // Daily-use tracking
  is_daily_use?: boolean;
  daily_usage_rate?: number;
  restock_threshold_days?: number;
  last_depletion_date?: string;
}

export interface MealLogEntry {
  id: number;
  recipe_id: number;
  recipe_name: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  servings_eaten: number;
  nutrition: Nutrition;
  logged_at: string;
}

export interface NutritionGoals {
  id: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
}

export interface NutritionToday {
  date: string;
  totals: Nutrition;
  goals: NutritionGoals;
  meals: MealLogEntry[];
}

// Meal Planning types
export interface MealPlan {
  id: number;
  name: string;
  plan_type: 'day' | 'week' | 'month';
  start_date: string;
  end_date: string;
  budget_total: number | null;
  budget_remaining: number | null;
  total_estimated_cost: number;
  include_snacks: boolean;
  breakfasts_needed: number;
  lunches_needed: number;
  dinners_needed: number;
  snacks_needed: number;
  breakfasts_selected: number;
  lunches_selected: number;
  dinners_selected: number;
  snacks_selected: number;
  created_at?: string;
}

export interface MealPlanEntry {
  id: number;
  date: string;  // YYYY-MM-DD
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  recipe_id: number;
  recipe_name: string;
  recipe_image?: string;
  servings: number;
}

export interface SmartRecipe extends Recipe {
  overlap_score?: number;
  overlap_ingredients?: string[];
  ingredients?: string[];
}

export interface SwipeData {
  direction: 'left' | 'right' | 'up';
  recipe_id: number;
  recipe_title: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  ingredients?: string[];
}

export interface SwipeResult {
  success: boolean;
  action: string;
  meal_type?: string;
  progress?: {
    breakfast: string;
    lunch: string;
    dinner: string;
    snack?: string;
  };
  is_meal_type_complete?: boolean;
  total_plan_cost?: number;
}

export interface DayPlan {
  date: string;
  dayName: string;
  isToday: boolean;
  meals: {
    breakfast: MealPlanEntry[];
    lunch: MealPlanEntry[];
    dinner: MealPlanEntry[];
    snack: MealPlanEntry[];
  };
}

export interface WeekPlan {
  startDate: string;
  endDate: string;
  days: DayPlan[];
}

// MealDB types (external recipe database)
export interface MealDBRecipe {
  idMeal: string;
  strMeal: string;
  strCategory: string;
  strArea: string;
  strMealThumb: string;
  strTags?: string;
}

export interface MealDBRecipeDetail extends MealDBRecipe {
  strInstructions: string;
  strYoutube?: string;
  strSource?: string;
  ingredients: Array<{
    ingredient: string;
    measure: string;
  }>;
}

// Recipe with availability scoring (for bulk pantry matching)
export interface RecipeWithAvailability extends Recipe {
  availabilityScore: number;
  matchedIngredients: string[];
  missingIngredients: string[];
}

// Scanned item (bulk mode)
export interface ScannedItem {
  id: number;
  barcode: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  timestamp: number;
}

// Navigation types
export type TabParamList = {
  Recipes: { pantryIngredients?: string[] } | undefined;
  MealPlan: undefined;
  Shopping: undefined;
  Pantry: undefined;
  Nutrition: undefined;
  Calendar: undefined;
  Decks: undefined;
};

export type RootStackParamList = {
  Main: NavigatorScreenParams<TabParamList> | undefined;
  RecipeDetail: { recipeId: number; mealId?: string };
  Cooking: { recipeId: number };
  BulkReview: {
    scannedItemIds: number[];
    onComplete?: () => void;
  };
  DeckDetail: { deckId: number };
  PantryProductDetail: { productId: number };
  MealPrep: undefined;
  Family: undefined;
  Game: undefined;
  Analytics: undefined;
  Alchemy: undefined;
  Journal: undefined;
};
