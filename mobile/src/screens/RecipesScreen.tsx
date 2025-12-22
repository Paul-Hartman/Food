import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList, Recipe, MealDBRecipe, RecipeWithAvailability } from '../types';
import { api } from '../services/api';
import HoverableCard from '../components/HoverableCard';

type Source = 'local' | 'mealdb';
type Filter = 'all' | 'main' | 'side' | 'quick';

const SOURCE_TABS: { key: Source; label: string }[] = [
  { key: 'local', label: 'My Recipes' },
  { key: 'mealdb', label: 'Discover' },
];

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'main', label: 'Mains' },
  { key: 'side', label: 'Sides' },
  { key: 'quick', label: 'Quick (<30m)' },
];

export default function RecipesScreen() {
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const route = useRoute();

  const [source, setSource] = useState<Source>('mealdb');
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [mealDBRecipes, setMealDBRecipes] = useState<MealDBRecipe[]>([]);
  const [matchedRecipes, setMatchedRecipes] = useState<RecipeWithAvailability[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [mealDBCategory, setMealDBCategory] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [isIngredientSearch, setIsIngredientSearch] = useState(false);
  const [selectedForDeck, setSelectedForDeck] = useState<Set<number>>(new Set());

  useEffect(() => {
    // Check if pantryIngredients param exists
    const params = route.params as { pantryIngredients?: string[] } | undefined;

    if (params?.pantryIngredients && params.pantryIngredients.length > 0) {
      searchByIngredients(params.pantryIngredients);
    } else {
      loadRecipes();
      loadMealDBCategories();
    }
  }, [route.params]);

  useEffect(() => {
    if (source === 'mealdb') {
      loadMealDBRecipes();
    }
  }, [source, mealDBCategory]);

  const loadRecipes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRecipes();
      setRecipes(data);
    } catch (err) {
      setError('Failed to load recipes. Make sure Flask is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadMealDBCategories = async () => {
    try {
      const data = await api.getMealDBCategories();
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Failed to load MealDB categories:', err);
    }
  };

  const loadMealDBRecipes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getMealDBRecipes(mealDBCategory || undefined, 20);
      setMealDBRecipes(data.recipes || []);
    } catch (err) {
      setError('Failed to load recipes from MealDB.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const searchByIngredients = async (ingredients: string[]) => {
    try {
      setLoading(true);
      setError(null);
      setIsIngredientSearch(true);

      const results = await api.searchRecipesByIngredients(ingredients);

      // Sort by availability score (descending)
      const sorted = results.sort((a, b) =>
        (b.availabilityScore || 0) - (a.availabilityScore || 0)
      );

      setMatchedRecipes(sorted);

      console.log(`Found ${results.length} recipes matching ${ingredients.length} ingredients`);
    } catch (err) {
      setError('Failed to search recipes by ingredients');
      console.error('Recipe search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleRecipeSelection = (recipeId: number) => {
    setSelectedForDeck(prev => {
      const newSet = new Set(prev);
      if (newSet.has(recipeId)) {
        newSet.delete(recipeId);
      } else {
        newSet.add(recipeId);
      }
      return newSet;
    });
  };

  const addSelectedToDeck = async () => {
    try {
      const selectedRecipes = matchedRecipes.filter(r => selectedForDeck.has(r.id));

      if (selectedRecipes.length === 0) return;

      // Add each recipe to cooking deck with swipe up
      for (const recipe of selectedRecipes) {
        await api.swipeUp({
          recipe_id: recipe.id,
          recipe_source: 'local',
          name: recipe.name,
          image_url: recipe.image_url || undefined,
          meal_type: 'dinner',
          category: recipe.category,
          cuisine: recipe.cuisine,
        });
      }

      // Clear selection
      setSelectedForDeck(new Set());

      // Navigate to DecksScreen, Tonight tab
      navigation.navigate('Decks' as any, { screen: 'Tonight' });

      // Show success message
      console.log(`Added ${selectedRecipes.length} recipes to Tonight's deck`);
    } catch (err) {
      console.error('Failed to add recipes to deck:', err);
      setError('Failed to add recipes to cooking deck');
    }
  };

  const filteredRecipes = recipes.filter((recipe) => {
    if (filter === 'all') return true;
    if (filter === 'main') return recipe.category === 'main';
    if (filter === 'side') return recipe.category === 'side';
    if (filter === 'quick') return recipe.prep_time_min + recipe.cook_time_min <= 30;
    return true;
  });

  const renderRecipeCard = ({ item }: { item: Recipe }) => (
    <HoverableCard
      title={item.name}
      image={item.image_url || undefined}
      badge={item.category}
      stats={[
        { label: 'Time', value: `${item.prep_time_min + item.cook_time_min}m` },
        { label: 'Serves', value: item.servings },
      ]}
      onPress={() => navigation.navigate('RecipeDetail', { recipeId: item.id })}
    />
  );

  const renderMealDBCard = ({ item }: { item: MealDBRecipe }) => (
    <HoverableCard
      title={item.strMeal}
      image={item.strMealThumb}
      badge={item.strCategory}
      stats={[
        { label: 'Cuisine', value: item.strArea },
      ]}
      onPress={() => navigation.navigate('RecipeDetail', { recipeId: 0, mealId: item.idMeal })}
    />
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading recipes...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorEmoji}>😢</Text>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadRecipes}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header subtitle */}
      <Text style={styles.subtitle}>
        {isIngredientSearch ? '🍳 Recipes You Can Cook' : 'What are we cooking tonight?'}
      </Text>

      {/* Show clear button if ingredient search is active */}
      {isIngredientSearch && (
        <TouchableOpacity
          style={styles.clearSearchButton}
          onPress={() => {
            setIsIngredientSearch(false);
            setMatchedRecipes([]);
            loadRecipes();
            loadMealDBCategories();
          }}
        >
          <Text style={styles.clearSearchText}>✕ Clear Search</Text>
        </TouchableOpacity>
      )}

      {/* Source tabs (My Recipes / Discover) - hide when ingredient search is active */}
      {!isIngredientSearch && (
        <View style={styles.sourceTabs}>
          {SOURCE_TABS.map((tab) => (
            <TouchableOpacity
              key={tab.key}
              style={[styles.sourceTab, source === tab.key && styles.sourceTabActive]}
              onPress={() => setSource(tab.key)}
            >
              <Text
                style={[
                  styles.sourceTabText,
                  source === tab.key && styles.sourceTabTextActive,
                ]}
              >
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Matched recipes - Ingredient Search */}
      {isIngredientSearch && (
        matchedRecipes.length === 0 ? (
          <View style={styles.centered}>
            <Text style={styles.emptyEmoji}>🔍</Text>
            <Text style={styles.emptyText}>No recipes match your ingredients</Text>
          </View>
        ) : (
          <ScrollView
            contentContainerStyle={styles.gridContainer}
            showsVerticalScrollIndicator={false}
          >
            {matchedRecipes.map((item) => (
              <View key={item.id} style={styles.recipeCardWrapper}>
                <TouchableOpacity
                  onPress={() => toggleRecipeSelection(item.id)}
                  onLongPress={() => navigation.navigate('RecipeDetail', { recipeId: item.id })}
                  activeOpacity={0.7}
                >
                  <HoverableCard
                    title={item.name}
                    image={item.image_url || undefined}
                    stats={[
                      { label: 'Time', value: `${item.prep_time_min + item.cook_time_min}m` },
                      { label: 'Level', value: item.difficulty }
                    ]}
                    onPress={() => {}}
                  />
                  {/* Selection checkbox overlay */}
                  <View style={styles.checkboxOverlay}>
                    <View style={[
                      styles.checkbox,
                      selectedForDeck.has(item.id) && styles.checkboxSelected
                    ]}>
                      {selectedForDeck.has(item.id) && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </View>
                  </View>
                  {/* Availability score badge */}
                  <View style={styles.availabilityBadge}>
                    <Text style={styles.availabilityScore}>
                      {Math.round(item.availabilityScore * 100)}% match
                    </Text>
                  </View>
                  {/* Missing ingredients */}
                  {item.missingIngredients && item.missingIngredients.length > 0 && (
                    <View style={styles.missingContainer}>
                      <Text style={styles.missingLabel}>Missing:</Text>
                      <Text style={styles.missingText}>
                        {item.missingIngredients.slice(0, 3).join(', ')}
                        {item.missingIngredients.length > 3 ? '...' : ''}
                      </Text>
                    </View>
                  )}
                </TouchableOpacity>
              </View>
            ))}
          </ScrollView>
        )
      )}

      {/* Floating action button - Add to Tonight's Deck */}
      {isIngredientSearch && selectedForDeck.size > 0 && (
        <TouchableOpacity
          style={styles.floatingButton}
          onPress={addSelectedToDeck}
        >
          <Text style={styles.floatingButtonText}>
            Add {selectedForDeck.size} to Tonight's Deck
          </Text>
        </TouchableOpacity>
      )}

      {/* Filter chips for local recipes */}
      {!isIngredientSearch && source === 'local' && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterContainer}
          contentContainerStyle={styles.filterContent}
        >
          {FILTERS.map((f) => (
            <TouchableOpacity
              key={f.key}
              style={[styles.filterChip, filter === f.key && styles.filterChipActive]}
              onPress={() => setFilter(f.key)}
            >
              <Text
                style={[
                  styles.filterChipText,
                  filter === f.key && styles.filterChipTextActive,
                ]}
              >
                {f.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Category filter for MealDB recipes */}
      {!isIngredientSearch && source === 'mealdb' && categories.length > 0 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterContainer}
          contentContainerStyle={styles.filterContent}
        >
          <TouchableOpacity
            style={[styles.filterChip, mealDBCategory === '' && styles.filterChipActive]}
            onPress={() => setMealDBCategory('')}
          >
            <Text
              style={[
                styles.filterChipText,
                mealDBCategory === '' && styles.filterChipTextActive,
              ]}
            >
              All
            </Text>
          </TouchableOpacity>
          {categories.slice(0, 8).map((cat) => (
            <TouchableOpacity
              key={cat}
              style={[styles.filterChip, mealDBCategory === cat && styles.filterChipActive]}
              onPress={() => setMealDBCategory(cat)}
            >
              <Text
                style={[
                  styles.filterChipText,
                  mealDBCategory === cat && styles.filterChipTextActive,
                ]}
              >
                {cat}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Recipe grid - Local recipes */}
      {!isIngredientSearch && source === 'local' && (
        filteredRecipes.length === 0 ? (
          <View style={styles.centered}>
            <Text style={styles.emptyEmoji}>🍽️</Text>
            <Text style={styles.emptyText}>No recipes found</Text>
          </View>
        ) : (
          <ScrollView
            contentContainerStyle={styles.gridContainer}
            showsVerticalScrollIndicator={false}
          >
            {filteredRecipes.map((item) => (
              <View key={item.id}>{renderRecipeCard({ item })}</View>
            ))}
          </ScrollView>
        )
      )}

      {/* Recipe grid - MealDB recipes */}
      {!isIngredientSearch && source === 'mealdb' && (
        mealDBRecipes.length === 0 ? (
          <View style={styles.centered}>
            <Text style={styles.emptyEmoji}>🌍</Text>
            <Text style={styles.emptyText}>Discovering recipes...</Text>
          </View>
        ) : (
          <ScrollView
            contentContainerStyle={styles.gridContainer}
            showsVerticalScrollIndicator={false}
          >
            {mealDBRecipes.map((item) => (
              <View key={item.idMeal}>{renderMealDBCard({ item })}</View>
            ))}
          </ScrollView>
        )
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  sourceTabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  sourceTab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: '#e0e0e0',
  },
  sourceTabActive: {
    borderBottomColor: '#4CAF50',
  },
  sourceTabText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#888',
  },
  sourceTabTextActive: {
    color: '#4CAF50',
    fontWeight: '600',
  },
  filterContainer: {
    maxHeight: 50,
  },
  filterContent: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#fff',
    marginHorizontal: 4,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  filterChipActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  filterChipText: {
    fontSize: 14,
    color: '#666',
  },
  filterChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    padding: 16,
    paddingBottom: 32,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  errorEmoji: {
    fontSize: 48,
    marginBottom: 12,
  },
  errorText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#4CAF50',
    borderRadius: 8,
  },
  retryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
  },
  clearSearchButton: {
    backgroundColor: '#f5f5f5',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignSelf: 'center',
    marginBottom: 12,
  },
  clearSearchText: {
    color: '#666',
    fontSize: 14,
    fontWeight: '500',
  },
  availabilityBadge: {
    backgroundColor: '#4CAF50',
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginTop: -32,
    marginLeft: 12,
    marginBottom: 8,
  },
  availabilityScore: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  missingContainer: {
    paddingHorizontal: 12,
    marginBottom: 12,
  },
  missingLabel: {
    fontSize: 11,
    color: '#999',
    marginBottom: 2,
    fontWeight: '600',
  },
  missingText: {
    fontSize: 13,
    color: '#666',
  },
  recipeCardWrapper: {
    position: 'relative',
  },
  checkboxOverlay: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 10,
  },
  checkbox: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#fff',
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxSelected: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  checkmark: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  floatingButton: {
    position: 'absolute',
    bottom: 32,
    left: 16,
    right: 16,
    backgroundColor: '#4CAF50',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  floatingButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
  },
});
