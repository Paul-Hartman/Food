// API Service for Flask Backend
// Flask runs at http://192.168.2.38:5025

import {
  Recipe,
  RecipeDetail,
  ShoppingData,
  PantryItem,
  NutritionToday,
  NutritionGoals,
  MealPlan,
  SmartRecipe,
  SwipeData,
  SwipeResult,
} from '../types';

// Use your PC's local IP - accessible from web browser
const BASE_URL = 'http://192.168.2.38:5025';

class ApiService {
  private async fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  // Recipes
  async getRecipes(filter?: { category?: string; quick?: boolean }): Promise<Recipe[]> {
    const params = new URLSearchParams();
    if (filter?.category) params.append('category', filter.category);
    if (filter?.quick) params.append('quick', 'true');

    const query = params.toString() ? `?${params}` : '';
    return this.fetchJson<Recipe[]>(`/api/recipes${query}`);
  }

  async getRecipeDetail(recipeId: number): Promise<RecipeDetail> {
    return this.fetchJson<RecipeDetail>(`/api/recipes/${recipeId}`);
  }

  async getRecipeSteps(recipeId: number): Promise<{
    recipe_name: string;
    steps: Array<{
      step_number: number;
      title: string;
      instruction: string;
      duration_min: number | null;
      tips: string | null;
      timer_needed: boolean;
    }>;
    total_steps: number;
  }> {
    return this.fetchJson(`/api/recipes/${recipeId}/steps`);
  }

  // Shopping
  async getShopping(): Promise<ShoppingData> {
    return this.fetchJson<ShoppingData>('/api/shopping');
  }

  async generateShopping(recipeIds: number[], clearExisting = false, subtractPantry = true): Promise<{ success: boolean; items_added: number }> {
    return this.fetchJson('/api/shopping/generate', {
      method: 'POST',
      body: JSON.stringify({
        recipe_ids: recipeIds,
        clear_existing: clearExisting,
        subtract_pantry: subtractPantry,
      }),
    });
  }

  async toggleShoppingItem(itemId: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/shopping/item/${itemId}/check`, {
      method: 'POST',
    });
  }

  async deleteShoppingItem(itemId: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/shopping/item/${itemId}`, {
      method: 'DELETE',
    });
  }

  async clearCheckedShopping(): Promise<{ success: boolean }> {
    return this.fetchJson('/api/shopping/clear-checked', {
      method: 'POST',
    });
  }

  async addShoppingItem(item: {
    name: string;
    quantity?: number;
    unit?: string;
    category?: string;
    aldi_section?: string;
  }): Promise<{ success: boolean }> {
    return this.fetchJson('/api/shopping/add', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  // Pantry
  async getPantry(): Promise<PantryItem[]> {
    return this.fetchJson<PantryItem[]>('/api/pantry');
  }

  async addToPantry(item: {
    name: string;
    quantity?: number;
    unit?: string;
    category?: string;
    aldi_section?: string;
    expires_at?: string;
  }): Promise<{ success: boolean }> {
    return this.fetchJson('/api/pantry/add', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  async updatePantryItem(itemId: number, quantity: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/pantry/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity }),
    });
  }

  async deletePantryItem(itemId: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/pantry/${itemId}`, {
      method: 'DELETE',
    });
  }

  // Nutrition
  async getNutritionToday(): Promise<NutritionToday> {
    return this.fetchJson<NutritionToday>('/api/nutrition/today');
  }

  async logMeal(data: {
    recipe_id: number;
    meal_type?: string;
    servings_eaten?: number;
    notes?: string;
  }): Promise<{ success: boolean }> {
    return this.fetchJson('/api/nutrition/log', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getNutritionGoals(): Promise<NutritionGoals> {
    return this.fetchJson<NutritionGoals>('/api/nutrition/goals');
  }

  async updateNutritionGoals(goals: {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g?: number;
  }): Promise<{ success: boolean }> {
    return this.fetchJson('/api/nutrition/goals', {
      method: 'PUT',
      body: JSON.stringify(goals),
    });
  }

  // Ingredients (for autocomplete)
  async searchIngredients(search?: string): Promise<Array<{
    id: number;
    name: string;
    category: string;
    aldi_section: string;
    default_unit: string;
  }>> {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.fetchJson(`/api/ingredients${query}`);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; app: string }> {
    return this.fetchJson('/health');
  }

  // Meal Planning
  async getMealPlans(): Promise<MealPlan[]> {
    return this.fetchJson<MealPlan[]>('/api/meal-plans');
  }

  async createMealPlan(planType: 'day' | 'week' | 'month', budget?: number): Promise<MealPlan> {
    return this.fetchJson<MealPlan>('/api/meal-plans', {
      method: 'POST',
      body: JSON.stringify({
        plan_type: planType,
        budget: budget || null,
      }),
    });
  }

  async getMealPlan(planId: number): Promise<MealPlan> {
    return this.fetchJson<MealPlan>(`/api/meal-plans/${planId}`);
  }

  async deleteMealPlan(planId: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/meal-plans/${planId}`, {
      method: 'DELETE',
    });
  }

  async getSmartRecipes(planId: number, mealType: string): Promise<{ recipes: SmartRecipe[] }> {
    return this.fetchJson(`/api/meal-plans/${planId}/smart-recipes?meal_type=${mealType}`);
  }

  async swipeRecipe(planId: number, data: SwipeData): Promise<SwipeResult> {
    return this.fetchJson<SwipeResult>(`/api/meal-plans/${planId}/swipe`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getShoppingListFromPlan(planId: number): Promise<ShoppingData> {
    return this.fetchJson<ShoppingData>(`/api/meal-plans/${planId}/shopping-list`);
  }

  async generateShoppingFromPlan(planId: number): Promise<{ success: boolean; items_added: number }> {
    return this.fetchJson(`/api/meal-plans/${planId}/shopping-list/generate`, {
      method: 'POST',
    });
  }
}

export const api = new ApiService();
