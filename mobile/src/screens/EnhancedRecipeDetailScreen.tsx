import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Image,
  Dimensions,
  Platform,
} from 'react-native';
import { RouteProp, useRoute, useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList, RecipeDetail, CookingStep } from '../types';
import { api } from '../services/api';

const FLASK_BASE_URL = 'http://192.168.2.38:5025';

type RouteProps = RouteProp<RootStackParamList, 'RecipeDetail'>;

const SCREEN_WIDTH = Dimensions.get('window').width;

export default function EnhancedRecipeDetailScreen() {
  const route = useRoute<RouteProps>();
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const { recipeId, mealId } = route.params;

  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [steps, setSteps] = useState<CookingStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [targetServings, setTargetServings] = useState<number | null>(null);

  // Determine if this is a MealDB recipe
  const isMealDB = !!mealId;

  // Unit conversions to grams
  const unitToGrams: { [key: string]: number } = {
    'g': 1, 'gram': 1, 'grams': 1,
    'kg': 1000, 'kilogram': 1000,
    'ml': 1, 'milliliter': 1,
    'l': 1000, 'liter': 1000,
    'cup': 240, 'cups': 240,
    'tbsp': 15, 'tablespoon': 15,
    'tsp': 5, 'teaspoon': 5,
    'oz': 28, 'ounce': 28,
    'lb': 454, 'pound': 454,
    'pinch': 1, // 1 pinch = ~1 gram as user requested
    'dash': 0.5,
    'slice': 30, 'slices': 30,
    'clove': 3, 'cloves': 3,
    'piece': 100, 'pieces': 100,
  };

  // Scale ingredient quantity based on serving multiplier
  const scaleQuantity = (quantity: number | string, unit: string, multiplier: number): string => {
    // Parse quantity - handle both number and string inputs
    let numQuantity: number;
    if (typeof quantity === 'string') {
      // Handle fractions like "1/2", "1 1/2"
      if (quantity.includes('/')) {
        const parts = quantity.trim().split(' ');
        if (parts.length === 2) {
          // Mixed fraction like "1 1/2"
          const whole = parseFloat(parts[0]);
          const [num, denom] = parts[1].split('/').map(Number);
          numQuantity = whole + (num / denom);
        } else {
          // Simple fraction like "1/2"
          const [num, denom] = quantity.split('/').map(Number);
          numQuantity = num / denom;
        }
      } else {
        numQuantity = parseFloat(quantity) || 0;
      }
    } else {
      numQuantity = quantity || 0;
    }

    const scaled = numQuantity * multiplier;
    const unitLower = (unit || '').toLowerCase().trim();

    // For pinch/dash, show as whole pinches when scaled up
    if (unitLower === 'pinch' || unitLower === 'pinches') {
      const pinches = Math.max(1, Math.round(scaled));
      return `${pinches} ${pinches === 1 ? 'pinch' : 'pinches'}`;
    }
    if (unitLower === 'dash' || unitLower === 'dashes') {
      const dashes = Math.max(1, Math.round(scaled));
      return `${dashes} ${dashes === 1 ? 'dash' : 'dashes'}`;
    }

    // Format nicely - show fractions for small amounts
    if (scaled < 1 && scaled > 0) {
      // Common fractions
      if (Math.abs(scaled - 0.25) < 0.01) return `1/4 ${unit}`;
      if (Math.abs(scaled - 0.33) < 0.02) return `1/3 ${unit}`;
      if (Math.abs(scaled - 0.5) < 0.01) return `1/2 ${unit}`;
      if (Math.abs(scaled - 0.66) < 0.02) return `2/3 ${unit}`;
      if (Math.abs(scaled - 0.75) < 0.01) return `3/4 ${unit}`;
      return `${scaled.toFixed(1)} ${unit}`;
    }

    // Round to 1 decimal place if needed
    const formatted = scaled % 1 === 0 ? scaled.toString() : scaled.toFixed(1);
    return `${formatted} ${unit}`;
  };

  useEffect(() => {
    loadRecipeAndSteps();
  }, [recipeId, mealId]);

  const loadRecipeAndSteps = async () => {
    try {
      setLoading(true);
      setError(null);

      let recipeData: RecipeDetail;

      if (isMealDB && mealId) {
        // Load MealDB recipe - API returns same format as local recipes
        recipeData = await api.getMealDBRecipeAsLocal(mealId);
      } else {
        // Load local recipe
        recipeData = await api.getRecipeDetail(recipeId);
      }

      setRecipe(recipeData);
      setTargetServings(recipeData.recipe.servings); // Initialize with recipe's default servings
      navigation.setOptions({ title: recipeData.recipe.name });

      // Load cooking steps
      if (isMealDB && mealId) {
        // MealDB steps are already in recipeData
        setSteps(recipeData.steps || []);
      } else {
        const stepsData = await api.getRecipeSteps(recipeId);
        setSteps(stepsData.steps || []);
      }
    } catch (err) {
      setError('Failed to load recipe details.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // For MealDB recipes, show the Flask page directly via iframe
  if (isMealDB && mealId) {
    const flaskUrl = `${FLASK_BASE_URL}/recipe/mealdb/${mealId}`;

    // Use iframe to embed the Flask page
    return (
      <View style={{ flex: 1 }}>
        {Platform.OS === 'web' ? (
          // @ts-ignore - iframe is valid in web
          <iframe
            src={flaskUrl}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="Recipe"
          />
        ) : (
          // For mobile, show link to open in browser
          <View style={styles.centered}>
            <Text>View recipe at:</Text>
            <Text style={{ color: '#4CAF50' }}>{flaskUrl}</Text>
          </View>
        )}
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  if (error || !recipe) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorEmoji}>😢</Text>
        <Text style={styles.errorText}>{error || 'Recipe not found'}</Text>
      </View>
    );
  }

  const { recipe: r, ingredients, nutrition_per_serving } = recipe;
  const totalTime = r.prep_time_min + r.cook_time_min;
  const currentServings = targetServings || r.servings;
  const servingMultiplier = currentServings / r.servings;

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Recipe Image */}
        {r.image_url && (
          <View style={styles.heroImageContainer}>
            <Image
              source={{ uri: r.image_url }}
              style={styles.heroImage}
              resizeMode="contain"
            />
          </View>
        )}

        {/* Header Info */}
        <View style={styles.header}>
          <Text style={styles.description}>{r.description}</Text>

          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Text style={styles.metaIcon}>⏱️</Text>
              <Text style={styles.metaValue}>{totalTime}m</Text>
              <Text style={styles.metaLabel}>Time</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaIcon}>🍽️</Text>
              <View style={styles.servingAdjuster}>
                <TouchableOpacity
                  style={styles.servingButton}
                  onPress={() => setTargetServings(Math.max(1, currentServings - 1))}
                >
                  <Text style={styles.servingButtonText}>-</Text>
                </TouchableOpacity>
                <Text style={styles.metaValue}>{currentServings}</Text>
                <TouchableOpacity
                  style={styles.servingButton}
                  onPress={() => setTargetServings(currentServings + 1)}
                >
                  <Text style={styles.servingButtonText}>+</Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.metaLabel}>Servings</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaIcon}>📊</Text>
              <Text style={styles.metaValue}>{r.difficulty}</Text>
              <Text style={styles.metaLabel}>Difficulty</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaIcon}>🔥</Text>
              <Text style={styles.metaValue}>{Math.round(nutrition_per_serving?.calories || 0)}</Text>
              <Text style={styles.metaLabel}>Calories</Text>
            </View>
          </View>
        </View>

        {/* Nutrition Card */}
        {nutrition_per_serving && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📊 Nutrition per Serving</Text>
          <View style={styles.nutritionCard}>
            <View style={styles.nutritionRow}>
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionValue}>{Math.round(nutrition_per_serving.protein || 0)}g</Text>
                <Text style={styles.nutritionLabel}>Protein</Text>
              </View>
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionValue}>{Math.round(nutrition_per_serving.carbs || 0)}g</Text>
                <Text style={styles.nutritionLabel}>Carbs</Text>
              </View>
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionValue}>{Math.round(nutrition_per_serving.fat || 0)}g</Text>
                <Text style={styles.nutritionLabel}>Fat</Text>
              </View>
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionValue}>{Math.round(nutrition_per_serving.fiber || 0)}g</Text>
                <Text style={styles.nutritionLabel}>Fiber</Text>
              </View>
            </View>
          </View>
        </View>
        )}

        {/* Ingredients Deck */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>🛒 Ingredients ({ingredients.length})</Text>
            {servingMultiplier !== 1 && (
              <Text style={styles.scaledBadge}>
                {servingMultiplier > 1 ? '↑' : '↓'} {servingMultiplier.toFixed(1)}x
              </Text>
            )}
          </View>
          <View style={styles.ingredientsDeck}>
            {ingredients.map((ing, index) => (
              <View key={index} style={styles.ingredientCard}>
                <View style={styles.ingredientHeader}>
                  <Text style={styles.ingredientName}>{ing.name}</Text>
                  <Text style={styles.ingredientAmount}>
                    {scaleQuantity(ing.quantity, ing.unit, servingMultiplier)}
                  </Text>
                </View>
                {ing.notes && (
                  <Text style={styles.ingredientNotes}>{ing.notes}</Text>
                )}
                <Text style={styles.ingredientSection}>{ing.aldi_section}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Cooking Steps */}
        {steps.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>👨‍🍳 Cooking Steps ({steps.length})</Text>
            {steps.map((step, index) => (
              <View key={index} style={styles.stepCard}>
                <View style={styles.stepHeader}>
                  <View style={styles.stepNumber}>
                    <Text style={styles.stepNumberText}>{step.step_number}</Text>
                  </View>
                  <View style={styles.stepTitleContainer}>
                    <Text style={styles.stepTitle}>{step.title}</Text>
                    {step.duration_min && step.duration_min > 0 && (
                      <Text style={styles.stepDuration}>⏱️ {step.duration_min} min</Text>
                    )}
                  </View>
                </View>

                <Text style={styles.stepInstruction}>{step.instruction}</Text>

                {step.tips && (
                  <View style={styles.stepTip}>
                    <Text style={styles.stepTipIcon}>💡</Text>
                    <Text style={styles.stepTipText}>{step.tips}</Text>
                  </View>
                )}

                {(step.timer_needed === true || step.timer_needed === 1) && (
                  <View style={styles.timerBadge}>
                    <Text style={styles.timerBadgeText}>⏰ Timer Needed</Text>
                  </View>
                )}
              </View>
            ))}
          </View>
        )}

        <View style={{ height: 100 }} />
      </ScrollView>

      {/* Start Cooking Button */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={styles.startButton}
          onPress={() => navigation.navigate('Cooking', { recipeId })}
        >
          <Text style={styles.startButtonText}>Start Cooking 👨‍🍳</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorEmoji: {
    fontSize: 48,
    marginBottom: 12,
  },
  errorText: {
    fontSize: 16,
    color: '#666',
  },
  heroImageContainer: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH * 0.65,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  header: {
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  description: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
    lineHeight: 22,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  metaItem: {
    alignItems: 'center',
  },
  metaIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  metaValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
  },
  metaLabel: {
    fontSize: 11,
    color: '#666',
    marginTop: 2,
  },
  servingAdjuster: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  servingButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#4CAF50',
    justifyContent: 'center',
    alignItems: 'center',
  },
  servingButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  scaledBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    fontSize: 12,
    fontWeight: '600',
    color: '#1976D2',
    overflow: 'hidden',
  },
  section: {
    padding: 16,
    backgroundColor: '#fff',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
    marginBottom: 12,
  },
  nutritionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  nutritionRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  nutritionItem: {
    alignItems: 'center',
  },
  nutritionValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#4CAF50',
  },
  nutritionLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  ingredientsDeck: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  ingredientCard: {
    width: (SCREEN_WIDTH - 48) / 2,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  ingredientHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  ingredientName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  ingredientAmount: {
    fontSize: 12,
    fontWeight: '700',
    color: '#4CAF50',
  },
  ingredientNotes: {
    fontSize: 11,
    color: '#666',
    fontStyle: 'italic',
    marginBottom: 4,
  },
  ingredientSection: {
    fontSize: 10,
    color: '#999',
  },
  stepCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  stepHeader: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  stepNumber: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#4CAF50',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  stepTitleContainer: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  stepDuration: {
    fontSize: 12,
    color: '#666',
  },
  stepInstruction: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
    marginBottom: 8,
  },
  stepTip: {
    flexDirection: 'row',
    backgroundColor: '#FFF9E6',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#FFC107',
  },
  stepTipIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  stepTipText: {
    flex: 1,
    fontSize: 13,
    color: '#666',
    lineHeight: 18,
  },
  timerBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginTop: 8,
  },
  timerBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1976D2',
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  startButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  startButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
});
