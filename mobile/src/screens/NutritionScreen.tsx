import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { NutritionToday, Recipe } from '../types';
import { api } from '../services/api';

const MEAL_EMOJIS: Record<string, string> = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
  snack: '🍿',
};

interface ProgressBarProps {
  current: number;
  goal: number;
  color: string;
  label: string;
  unit?: string;
}

function ProgressBar({ current, goal, color, label, unit = '' }: ProgressBarProps) {
  const percentage = Math.min((current / goal) * 100, 100);

  return (
    <View style={styles.progressItem}>
      <View style={styles.progressHeader}>
        <Text style={styles.progressLabel}>{label}</Text>
        <Text style={styles.progressValues}>
          {Math.round(current)}
          {unit} / {goal}
          {unit}
        </Text>
      </View>
      <View style={styles.progressBar}>
        <View
          style={[styles.progressFill, { width: `${percentage}%`, backgroundColor: color }]}
        />
      </View>
    </View>
  );
}

export default function NutritionScreen() {
  const [nutritionData, setNutritionData] = useState<NutritionToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [recipes, setRecipes] = useState<Recipe[]>([]);

  // Goals modal state
  const [goalsModalVisible, setGoalsModalVisible] = useState(false);
  const [goalCalories, setGoalCalories] = useState('');
  const [goalProtein, setGoalProtein] = useState('');
  const [goalCarbs, setGoalCarbs] = useState('');
  const [goalFat, setGoalFat] = useState('');

  // Log meal modal state
  const [logModalVisible, setLogModalVisible] = useState(false);
  const [selectedRecipeId, setSelectedRecipeId] = useState<number | null>(null);
  const [mealType, setMealType] = useState('dinner');
  const [servingsEaten, setServingsEaten] = useState('1');

  useFocusEffect(
    useCallback(() => {
      loadNutrition();
    }, [])
  );

  const loadNutrition = async () => {
    try {
      setLoading(true);
      const data = await api.getNutritionToday();
      setNutritionData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRecipes = async () => {
    try {
      const data = await api.getRecipes();
      setRecipes(data);
    } catch (err) {
      console.error(err);
    }
  };

  const showGoalsModal = () => {
    if (nutritionData) {
      setGoalCalories(nutritionData.goals.calories.toString());
      setGoalProtein(nutritionData.goals.protein_g.toString());
      setGoalCarbs(nutritionData.goals.carbs_g.toString());
      setGoalFat(nutritionData.goals.fat_g.toString());
    }
    setGoalsModalVisible(true);
  };

  const saveGoals = async () => {
    try {
      await api.updateNutritionGoals({
        calories: parseInt(goalCalories) || 2000,
        protein_g: parseFloat(goalProtein) || 50,
        carbs_g: parseFloat(goalCarbs) || 250,
        fat_g: parseFloat(goalFat) || 65,
      });
      setGoalsModalVisible(false);
      loadNutrition();
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to save goals');
    }
  };

  const showLogModal = () => {
    loadRecipes();
    setSelectedRecipeId(null);
    setMealType('dinner');
    setServingsEaten('1');
    setLogModalVisible(true);
  };

  const logMeal = async () => {
    if (!selectedRecipeId) {
      Alert.alert('Error', 'Please select a recipe');
      return;
    }

    try {
      await api.logMeal({
        recipe_id: selectedRecipeId,
        meal_type: mealType,
        servings_eaten: parseFloat(servingsEaten) || 1,
      });
      setLogModalVisible(false);
      loadNutrition();
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to log meal');
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  if (!nutritionData) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Failed to load nutrition data</Text>
      </View>
    );
  }

  const { totals, goals, meals, date } = nutritionData;

  return (
    <View style={styles.container}>
      {/* Subtitle with date */}
      <Text style={styles.subtitle}>{formatDate(date)}</Text>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Daily Progress */}
        <View style={styles.summaryCard}>
          <Text style={styles.sectionTitle}>Daily Progress</Text>
          <ProgressBar
            current={totals.calories}
            goal={goals.calories}
            color="#FF9800"
            label="Calories"
          />
          <ProgressBar
            current={totals.protein}
            goal={goals.protein_g}
            color="#4CAF50"
            label="Protein"
            unit="g"
          />
          <ProgressBar
            current={totals.carbs}
            goal={goals.carbs_g}
            color="#2196F3"
            label="Carbs"
            unit="g"
          />
          <ProgressBar
            current={totals.fat}
            goal={goals.fat_g}
            color="#9C27B0"
            label="Fat"
            unit="g"
          />
        </View>

        {/* Meal Log */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🍽️ Today's Meals</Text>
          {meals.length === 0 ? (
            <View style={styles.emptyMeals}>
              <Text style={styles.emptyText}>No meals logged yet today</Text>
              <TouchableOpacity style={styles.logButton} onPress={showLogModal}>
                <Text style={styles.logButtonText}>Log a Meal</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              {meals.map((meal) => (
                <View key={meal.id} style={styles.mealItem}>
                  <Text style={styles.mealEmoji}>{MEAL_EMOJIS[meal.meal_type] || '🍽️'}</Text>
                  <View style={styles.mealInfo}>
                    <Text style={styles.mealName}>{meal.recipe_name}</Text>
                    <Text style={styles.mealMeta}>
                      {meal.meal_type} - {meal.servings_eaten} serving(s)
                    </Text>
                  </View>
                  <Text style={styles.mealCalories}>
                    {Math.round(meal.nutrition.calories)} cal
                  </Text>
                </View>
              ))}
              <TouchableOpacity
                style={[styles.logButton, styles.logButtonOutline]}
                onPress={showLogModal}
              >
                <Text style={[styles.logButtonText, styles.logButtonTextOutline]}>
                  + Log Another Meal
                </Text>
              </TouchableOpacity>
            </>
          )}
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickAction} onPress={showLogModal}>
            <Text style={styles.quickActionIcon}>🥬</Text>
            <Text style={styles.quickActionText}>Log a Meal</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickAction} onPress={showGoalsModal}>
            <Text style={styles.quickActionIcon}>🎯</Text>
            <Text style={styles.quickActionText}>Edit Goals</Text>
          </TouchableOpacity>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* Edit Goals Modal */}
      <Modal visible={goalsModalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Daily Goals</Text>
            <Text style={styles.inputLabel}>Calories</Text>
            <TextInput
              style={styles.input}
              value={goalCalories}
              onChangeText={setGoalCalories}
              keyboardType="numeric"
            />
            <Text style={styles.inputLabel}>Protein (g)</Text>
            <TextInput
              style={styles.input}
              value={goalProtein}
              onChangeText={setGoalProtein}
              keyboardType="numeric"
            />
            <Text style={styles.inputLabel}>Carbs (g)</Text>
            <TextInput
              style={styles.input}
              value={goalCarbs}
              onChangeText={setGoalCarbs}
              keyboardType="numeric"
            />
            <Text style={styles.inputLabel}>Fat (g)</Text>
            <TextInput
              style={styles.input}
              value={goalFat}
              onChangeText={setGoalFat}
              keyboardType="numeric"
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalButton}
                onPress={() => setGoalsModalVisible(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalPrimaryButton]}
                onPress={saveGoals}
              >
                <Text style={[styles.modalButtonText, styles.modalPrimaryButtonText]}>
                  Save
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Log Meal Modal */}
      <Modal visible={logModalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Log Meal</Text>

            <Text style={styles.inputLabel}>Recipe</Text>
            <ScrollView style={styles.recipeSelect}>
              {recipes.map((recipe) => (
                <TouchableOpacity
                  key={recipe.id}
                  style={[
                    styles.recipeOption,
                    selectedRecipeId === recipe.id && styles.recipeOptionSelected,
                  ]}
                  onPress={() => setSelectedRecipeId(recipe.id)}
                >
                  <Text style={styles.recipeOptionText}>{recipe.name}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <Text style={styles.inputLabel}>Meal Type</Text>
            <View style={styles.mealTypeRow}>
              {['breakfast', 'lunch', 'dinner', 'snack'].map((type) => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.mealTypeButton,
                    mealType === type && styles.mealTypeButtonActive,
                  ]}
                  onPress={() => setMealType(type)}
                >
                  <Text
                    style={[
                      styles.mealTypeText,
                      mealType === type && styles.mealTypeTextActive,
                    ]}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.inputLabel}>Servings Eaten</Text>
            <TextInput
              style={styles.input}
              value={servingsEaten}
              onChangeText={setServingsEaten}
              keyboardType="numeric"
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalButton}
                onPress={() => setLogModalVisible(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalPrimaryButton]}
                onPress={logMeal}
              >
                <Text style={[styles.modalButtonText, styles.modalPrimaryButtonText]}>
                  Log Meal
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  errorText: {
    fontSize: 16,
    color: '#666',
  },
  summaryCard: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  progressItem: {
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  progressLabel: {
    fontSize: 14,
    color: '#666',
  },
  progressValues: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  emptyMeals: {
    backgroundColor: '#fff',
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
  },
  logButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  logButtonOutline: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    marginTop: 12,
    alignItems: 'center',
  },
  logButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  logButtonTextOutline: {
    color: '#666',
  },
  mealItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  mealEmoji: {
    fontSize: 24,
    marginRight: 12,
  },
  mealInfo: {
    flex: 1,
  },
  mealName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  mealMeta: {
    fontSize: 14,
    color: '#666',
    textTransform: 'capitalize',
  },
  mealCalories: {
    fontSize: 16,
    fontWeight: '500',
    color: '#FF9800',
  },
  quickActions: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
  },
  quickAction: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  quickActionIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  quickActionText: {
    fontSize: 14,
    color: '#666',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    marginTop: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  recipeSelect: {
    maxHeight: 150,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
  },
  recipeOption: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  recipeOptionSelected: {
    backgroundColor: '#e8f5e9',
  },
  recipeOptionText: {
    fontSize: 16,
    color: '#333',
  },
  mealTypeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  mealTypeButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  mealTypeButtonActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  mealTypeText: {
    fontSize: 14,
    color: '#666',
  },
  mealTypeTextActive: {
    color: '#fff',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 20,
  },
  modalButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  modalPrimaryButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  modalButtonText: {
    fontSize: 16,
    color: '#666',
  },
  modalPrimaryButtonText: {
    color: '#fff',
  },
});
