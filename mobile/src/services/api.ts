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
  MealDBRecipe,
  MealDBRecipeDetail,
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
    price?: number;
    image_url?: string;
  }): Promise<{ success: boolean; id: number }> {
    return this.fetchJson('/api/pantry/add', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  async updatePantryItem(
    itemId: number,
    quantity: number,
    expiresAt?: string,
    price?: number
  ): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/pantry/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify({
        quantity,
        ...(expiresAt !== undefined && { expires_at: expiresAt || null }),
        ...(price !== undefined && { price: price || null }),
      }),
    });
  }

  async deletePantryItem(itemId: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/pantry/${itemId}`, {
      method: 'DELETE',
    });
  }

  async getPantryTotalValue(): Promise<{ total: number; items_with_price: number }> {
    return this.fetchJson('/api/pantry/total-value');
  }

  async toggleDailyUse(
    itemId: number,
    settings: {
      is_daily_use: boolean;
      daily_usage_rate?: number;
      restock_threshold_days?: number;
    }
  ): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/pantry/${itemId}/daily-use`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async getDailyUseItems(): Promise<
    Array<{
      id: number;
      name: string;
      quantity: number;
      unit: string;
      daily_usage_rate: number;
      days_remaining: number;
      projected_depletion_date: string;
      needs_restock: boolean;
    }>
  > {
    return this.fetchJson('/api/pantry/daily-use');
  }

  async getUsageHistory(
    itemId: number
  ): Promise<
    Array<{
      id: number;
      quantity_change: number;
      quantity_before: number;
      quantity_after: number;
      change_type: string;
      logged_at: string;
    }>
  > {
    return this.fetchJson(`/api/pantry/${itemId}/usage-history`);
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

  async getIngredientById(id: number): Promise<{ ingredients: any[] }> {
    return this.fetchJson(`/api/ingredients?id=${id}`);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; app: string }> {
    return this.fetchJson('/health');
  }

  // MealDB Recipes (external recipe database)
  async getMealDBRecipes(category?: string, limit = 20): Promise<{ recipes: MealDBRecipe[] }> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    params.append('limit', limit.toString());
    const query = params.toString() ? `?${params}` : '';
    // Flask returns array directly, wrap it
    const data = await this.fetchJson<any[]>(`/api/mealdb/batch-random${query}`);
    // Transform Flask format to MealDB format
    const recipes = data.map(item => ({
      idMeal: item.id,
      strMeal: item.name,
      strCategory: item.category,
      strArea: item.cuisine,
      strMealThumb: item.image_url,
      strTags: item.tags?.join(','),
    }));
    return { recipes };
  }

  async searchMealDBRecipes(query: string): Promise<{ meals: MealDBRecipe[] }> {
    return this.fetchJson(`/api/mealdb/search?q=${encodeURIComponent(query)}`);
  }

  async getMealDBRecipeDetail(mealId: string): Promise<MealDBRecipeDetail> {
    // Flask returns custom format, transform to MealDBRecipeDetail
    const data = await this.fetchJson<any>(`/api/mealdb/recipe/${mealId}`);
    return {
      idMeal: data.recipe.id,
      strMeal: data.recipe.name,
      strCategory: data.recipe.category,
      strArea: data.recipe.cuisine,
      strMealThumb: data.recipe.image_url,
      strTags: data.recipe.tags?.join(','),
      strInstructions: data.recipe.description,
      strYoutube: data.recipe.youtube_url || undefined,
      strSource: data.recipe.source_url || undefined,
      ingredients: data.ingredients.map((ing: any) => ({
        ingredient: ing.name,
        measure: ing.quantity,
      })),
    };
  }

  // Get MealDB recipe in the same format as local recipes (for EnhancedRecipeDetailScreen)
  async getMealDBRecipeAsLocal(mealId: string): Promise<RecipeDetail> {
    const data = await this.fetchJson<any>(`/api/mealdb/recipe/${mealId}`);

    // Transform MealDB ingredients to match RecipeIngredient format
    const ingredients = (data.ingredients || []).map((ing: any, idx: number) => ({
      id: idx,
      recipe_id: parseInt(mealId) || 0,
      ingredient_id: idx,
      quantity: parseFloat(ing.quantity) || 1,
      unit: ing.quantity?.replace(/[\d.]/g, '').trim() || 'piece',
      notes: null,
      name: ing.name,
      aldi_section: 'Other',
    }));

    // Transform steps to match CookingStep format
    const steps = (data.steps || []).map((step: any) => ({
      step_number: step.step_number,
      title: step.title || `Step ${step.step_number}`,
      instruction: step.instruction,
      duration_min: null,
      tips: null,
      timer_needed: step.timer_needed || false,
    }));

    return {
      recipe: {
        id: parseInt(data.recipe.id) || 0,
        name: data.recipe.name,
        description: data.recipe.description,
        category: data.recipe.category?.toLowerCase() === 'side' ? 'side' : 'main',
        cuisine: data.recipe.cuisine,
        prep_time_min: data.recipe.prep_time_min || 15,
        cook_time_min: data.recipe.cook_time_min || 30,
        servings: data.recipe.servings || 4,
        difficulty: 'medium',
        image_url: data.recipe.image_url,
      },
      ingredients,
      steps,
      nutrition_per_serving: data.nutrition_per_serving || {
        calories: 0,
        protein: 0,
        carbs: 0,
        fat: 0,
        fiber: 0,
      },
    };
  }

  async getMealDBCategories(): Promise<{ categories: string[] }> {
    // Flask returns array of category objects, extract just the names
    const data = await this.fetchJson<any[]>('/api/mealdb/categories');
    const categories = data.map(cat => cat.strCategory);
    return { categories };
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

  // Calendar & Scheduling
  async getCalendarWeek(startDate: string): Promise<any> {
    return this.fetchJson(`/api/calendar/week?date=${startDate}`);
  }

  async getCalendarMonth(year: number, month: number): Promise<any> {
    return this.fetchJson(`/api/calendar/month?year=${year}&month=${month}`);
  }

  async scheduleMeal(data: {
    recipe_id: number;
    recipe_source: string;
    recipe_name: string;
    meal_type: string;
    scheduled_date: string;
    chef_member_id?: number;
  }): Promise<{ success: boolean }> {
    return this.fetchJson('/api/meals/schedule', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async searchRecipes(query: string): Promise<any[]> {
    return this.fetchJson(`/api/recipes/search?q=${encodeURIComponent(query)}`);
  }

  async searchRecipesByIngredients(ingredients: string[]): Promise<Array<Recipe & {
    availabilityScore: number;
    matchedIngredients: string[];
    missingIngredients: string[];
  }>> {
    return this.fetchJson('/api/recipes/search-by-ingredients', {
      method: 'POST',
      body: JSON.stringify({ ingredients }),
    });
  }

  // Family Members
  async getFamilyMembers(): Promise<any[]> {
    return this.fetchJson('/api/family/members');
  }

  async addFamilyMember(data: {
    name: string;
    avatar_emoji?: string;
    color?: string;
    dietary_restrictions?: string[];
  }): Promise<{ success: boolean; id: number }> {
    return this.fetchJson('/api/family/members', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateFamilyMember(memberId: number, data: any): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/family/members/${memberId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteFamilyMember(memberId: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/family/members/${memberId}`, {
      method: 'DELETE',
    });
  }

  // Meal Prep
  async getMealPrepTasks(planId: number): Promise<any> {
    return this.fetchJson(`/api/meal-plans/${planId}/prep-tasks`);
  }

  async getMealPrepSchedule(planId: number): Promise<any> {
    return this.fetchJson(`/api/meal-plans/${planId}/prep-schedule`);
  }

  async completePrepTask(planId: number, taskId: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/meal-plans/${planId}/prep-tasks/complete`, {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId }),
    });
  }

  // Cooking Decks
  async getDecks(): Promise<any[]> {
    return this.fetchJson('/api/decks');
  }

  async getDeck(deckId: number): Promise<any> {
    return this.fetchJson(`/api/decks/${deckId}`);
  }

  async getDeckRecipes(deckId: number): Promise<any[]> {
    return this.fetchJson(`/api/decks/${deckId}/recipes`);
  }

  async getInterested(): Promise<any[]> {
    return this.fetchJson('/api/interested');
  }

  async addToInterested(recipeId: number, source: string = 'local'): Promise<{ success: boolean }> {
    return this.fetchJson('/api/interested', {
      method: 'POST',
      body: JSON.stringify({ recipe_id: recipeId, source }),
    });
  }

  async removeFromInterested(id: number): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/interested/${id}`, {
      method: 'DELETE',
    });
  }

  async getCookingDeck(): Promise<any[]> {
    return this.fetchJson('/api/cooking-deck');
  }

  async swipeUp(data: {
    recipe_id: number;
    recipe_source?: string;
    name?: string;
    image_url?: string;
    meal_type: string;
    category?: string;
    cuisine?: string;
    tags?: string;
  }): Promise<{ success: boolean; position: number }> {
    return this.fetchJson('/api/swipe/up', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Gamification
  async getGameDashboard(memberId: number): Promise<any> {
    return this.fetchJson(`/api/game/member/${memberId}/dashboard`);
  }

  async getMemberSkills(memberId: number): Promise<any> {
    return this.fetchJson(`/api/game/member/${memberId}/skills`);
  }

  async getMemberAchievements(memberId: number): Promise<any[]> {
    return this.fetchJson(`/api/game/member/${memberId}/achievements`);
  }

  async getMemberCollection(memberId: number): Promise<any> {
    return this.fetchJson(`/api/game/member/${memberId}/collection`);
  }

  async logCookedMeal(memberId: number, data: any): Promise<{ success: boolean }> {
    return this.fetchJson(`/api/game/member/${memberId}/cook`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Personal Analytics
  async getPersonalDashboard(): Promise<any> {
    return this.fetchJson('/api/personal/dashboard');
  }

  async getPersonalAnalytics(): Promise<any> {
    return this.fetchJson('/api/personal/analytics');
  }

  async getPersonalInsights(): Promise<any> {
    return this.fetchJson('/api/personal/insights');
  }

  // Alchemy
  async getAlchemyEffects(): Promise<any[]> {
    return this.fetchJson('/api/alchemy/effects');
  }

  async getAlchemyIngredients(): Promise<any[]> {
    return this.fetchJson('/api/alchemy/ingredients');
  }

  async getAlchemyRecipes(): Promise<any[]> {
    return this.fetchJson('/api/alchemy/recipes');
  }

  async previewPotion(data: {
    ingredients: number[];
    brewing_method: string;
  }): Promise<any> {
    return this.fetchJson('/api/alchemy/preview', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async brewPotion(data: any): Promise<{ success: boolean }> {
    return this.fetchJson('/api/alchemy/brew', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getBrewingJournal(): Promise<any[]> {
    return this.fetchJson('/api/alchemy/journal');
  }

  // Journal
  async getJournalToday(): Promise<any> {
    return this.fetchJson('/api/journal/today');
  }

  async getJournalByDate(date: string): Promise<any> {
    return this.fetchJson(`/api/journal/${date}`);
  }

  async createJournalEntry(data: {
    date: string;
    meal_type?: string;
    content: string;
    mood?: string;
  }): Promise<{ success: boolean }> {
    return this.fetchJson('/api/journal/entry', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Feedback & Bug Reporting
  async flagBug(data: {
    screen: string;
    description: string;
    severity?: string;
    timestamp?: string;
    errorType?: string;
    barcode?: string;
    context?: any;
    source?: string;
  }): Promise<{ success: boolean; message: string; bug_id: number }> {
    return this.fetchJson('/api/bugs/flag', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async submitFeedback(data: {
    sessionId?: string;
    satisfaction: number;
    whatWorkedWell: string;
    whatCouldImprove: string;
    bugDescription?: string;
    wouldRecommend: boolean;
    context?: any;
  }): Promise<{ success: boolean; message: string }> {
    return this.fetchJson('/api/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getFeedbackStats(): Promise<{
    totalResponses: number;
    avgSatisfaction: number;
    recommendYes: number;
    recommendNo: number;
    recentFeedback: any[];
  }> {
    return this.fetchJson('/api/feedback/stats');
  }
}

export const api = new ApiService();
