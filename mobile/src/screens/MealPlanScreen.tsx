import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
  PanResponder,
  Dimensions,
  Image,
  ScrollView,
} from 'react-native';
import { useNavigation, CommonActions } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList, MealPlan, SmartRecipe, TabParamList } from '../types';
import { api } from '../services/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SWIPE_THRESHOLD = 100;

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';
type PlanType = 'day' | 'week' | 'month';
type SwipeDirection = 'left' | 'right' | 'up';

const MEAL_TYPE_CONFIG = {
  breakfast: { emoji: '🌅', label: 'Breakfast' },
  lunch: { emoji: '☀️', label: 'Lunch' },
  dinner: { emoji: '🌙', label: 'Dinner' },
  snack: { emoji: '🍎', label: 'Snack' },
};

export default function MealPlanScreen() {
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();

  // Plan state
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [currentMealType, setCurrentMealType] = useState<MealType>('dinner');
  const [recipes, setRecipes] = useState<SmartRecipe[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [creatingPlan, setCreatingPlan] = useState(false);

  // Plan creation options
  const [planType, setPlanType] = useState<PlanType>('week');
  const [budget, setBudget] = useState<number | null>(null);

  // Swipe animation
  const position = useRef(new Animated.ValueXY()).current;
  const [showLabels, setShowLabels] = useState({ nope: 0, yum: 0, prep: 0 });

  useEffect(() => {
    checkExistingPlan();
  }, []);

  const checkExistingPlan = async () => {
    try {
      setLoading(true);
      const plans = await api.getMealPlans();

      // Find an active/incomplete plan
      const activePlan = plans.find((p: MealPlan) => {
        const totalNeeded = p.breakfasts_needed + p.lunches_needed + p.dinners_needed + p.snacks_needed;
        const totalSelected = p.breakfasts_selected + p.lunches_selected + p.dinners_selected + p.snacks_selected;
        return totalSelected < totalNeeded;
      });

      if (activePlan) {
        setPlan(activePlan);
        findNextMealType(activePlan);
        await loadRecipes(activePlan.id, currentMealType);
      }
    } catch (err) {
      console.error('Failed to load plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const findNextMealType = (p: MealPlan) => {
    const order: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack'];
    for (const type of order) {
      const needed = p[`${type}s_needed` as keyof MealPlan] as number;
      const selected = p[`${type}s_selected` as keyof MealPlan] as number;
      if (needed > 0 && selected < needed) {
        setCurrentMealType(type);
        return type;
      }
    }
    return 'dinner';
  };

  const createNewPlan = async () => {
    try {
      setCreatingPlan(true);
      const newPlan = await api.createMealPlan(planType, budget ?? undefined);
      setPlan(newPlan);
      await loadRecipes(newPlan.id, 'breakfast');
      setCurrentMealType('breakfast');
    } catch (err) {
      console.error('Failed to create plan:', err);
    } finally {
      setCreatingPlan(false);
    }
  };

  const loadRecipes = async (planId: number, mealType: MealType) => {
    try {
      // Use smart recipes endpoint for ingredient overlap
      const data = await api.getSmartRecipes(planId, mealType);
      setRecipes(data.recipes || data);
      setCurrentIndex(0);
    } catch (err) {
      console.error('Failed to load recipes:', err);
    }
  };

  const handleSwipe = async (direction: SwipeDirection) => {
    if (!plan || currentIndex >= recipes.length) return;

    const recipe = recipes[currentIndex];

    try {
      const result = await api.swipeRecipe(plan.id, {
        direction,
        recipe_id: recipe.id,
        recipe_title: recipe.name,
        meal_type: currentMealType,
        ingredients: recipe.ingredients || [],
      });

      // Update plan state
      if (result.progress) {
        const progress = result.progress;
        setPlan(prev => prev ? {
          ...prev,
          breakfasts_selected: parseInt(progress.breakfast.split('/')[0]),
          lunches_selected: parseInt(progress.lunch.split('/')[0]),
          dinners_selected: parseInt(progress.dinner.split('/')[0]),
          snacks_selected: parseInt(progress.snack?.split('/')[0] || '0'),
          total_estimated_cost: result.total_plan_cost || prev.total_estimated_cost,
        } : null);
      }

      // Check if this meal type is complete
      if (result.is_meal_type_complete) {
        // Move to next meal type
        const nextType = findNextMealType({
          ...plan,
          [`${currentMealType}s_selected`]: plan[`${currentMealType}s_selected` as keyof MealPlan] as number + 1,
        } as MealPlan);

        if (nextType !== currentMealType) {
          setCurrentMealType(nextType);
          await loadRecipes(plan.id, nextType);
          return;
        }
      }

      // Next card
      setCurrentIndex(prev => prev + 1);

      // Load more if needed
      if (currentIndex >= recipes.length - 3) {
        await loadRecipes(plan.id, currentMealType);
      }
    } catch (err) {
      console.error('Swipe failed:', err);
    }
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderMove: (_, gesture) => {
        position.setValue({ x: gesture.dx, y: gesture.dy });

        // Update label opacity
        setShowLabels({
          nope: Math.min(Math.max(-gesture.dx / SWIPE_THRESHOLD, 0), 1),
          yum: Math.min(Math.max(gesture.dx / SWIPE_THRESHOLD, 0), 1),
          prep: Math.min(Math.max(-gesture.dy / SWIPE_THRESHOLD, 0), 1),
        });
      },
      onPanResponderRelease: (_, gesture) => {
        if (gesture.dy < -SWIPE_THRESHOLD) {
          // Swipe up - meal prep
          Animated.spring(position, {
            toValue: { x: 0, y: -SCREEN_WIDTH * 1.5 },
            useNativeDriver: false,
          }).start(() => {
            handleSwipe('up');
            position.setValue({ x: 0, y: 0 });
            setShowLabels({ nope: 0, yum: 0, prep: 0 });
          });
        } else if (gesture.dx > SWIPE_THRESHOLD) {
          // Swipe right - add to plan
          Animated.spring(position, {
            toValue: { x: SCREEN_WIDTH * 1.5, y: 0 },
            useNativeDriver: false,
          }).start(() => {
            handleSwipe('right');
            position.setValue({ x: 0, y: 0 });
            setShowLabels({ nope: 0, yum: 0, prep: 0 });
          });
        } else if (gesture.dx < -SWIPE_THRESHOLD) {
          // Swipe left - skip
          Animated.spring(position, {
            toValue: { x: -SCREEN_WIDTH * 1.5, y: 0 },
            useNativeDriver: false,
          }).start(() => {
            handleSwipe('left');
            position.setValue({ x: 0, y: 0 });
            setShowLabels({ nope: 0, yum: 0, prep: 0 });
          });
        } else {
          // Snap back
          Animated.spring(position, {
            toValue: { x: 0, y: 0 },
            useNativeDriver: false,
          }).start();
          setShowLabels({ nope: 0, yum: 0, prep: 0 });
        }
      },
    })
  ).current;

  const getProgress = () => {
    if (!plan) return { total: 0, selected: 0, percent: 0 };
    const total = plan.breakfasts_needed + plan.lunches_needed + plan.dinners_needed + plan.snacks_needed;
    const selected = plan.breakfasts_selected + plan.lunches_selected + plan.dinners_selected + plan.snacks_selected;
    return { total, selected, percent: Math.round((selected / total) * 100) };
  };

  const isComplete = () => {
    const progress = getProgress();
    return progress.selected >= progress.total;
  };

  // Loading state
  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading meal plans...</Text>
      </View>
    );
  }

  // No plan - show creation UI
  if (!plan) {
    return (
      <View style={styles.container}>
        <View style={styles.createPlanCard}>
          <Text style={styles.createTitle}>Create Meal Plan</Text>
          <Text style={styles.createSubtitle}>Choose your planning period</Text>

          <View style={styles.planTypeButtons}>
            {(['day', 'week', 'month'] as PlanType[]).map((type) => (
              <TouchableOpacity
                key={type}
                style={[styles.planTypeBtn, planType === type && styles.planTypeBtnActive]}
                onPress={() => setPlanType(type)}
              >
                <Text style={[styles.planTypeBtnText, planType === type && styles.planTypeBtnTextActive]}>
                  {type === 'day' ? '1 Day' : type === 'week' ? '1 Week' : '1 Month'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={styles.createButton}
            onPress={createNewPlan}
            disabled={creatingPlan}
          >
            {creatingPlan ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.createButtonText}>Start Swiping</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Plan complete
  if (isComplete()) {
    return (
      <View style={styles.container}>
        <View style={styles.completeCard}>
          <Text style={styles.completeEmoji}>🎉</Text>
          <Text style={styles.completeTitle}>Meal Plan Complete!</Text>
          <Text style={styles.completeSubtitle}>
            {getProgress().selected} meals planned
          </Text>
          {plan.total_estimated_cost > 0 && (
            <Text style={styles.costText}>
              Est. Cost: €{plan.total_estimated_cost.toFixed(2)}
            </Text>
          )}
          <TouchableOpacity
            style={styles.shoppingButton}
            onPress={() => {
              // Navigate to Shopping tab
              navigation.dispatch(
                CommonActions.navigate({
                  name: 'Main',
                  params: {
                    screen: 'Shopping',
                  },
                })
              );
            }}
          >
            <Text style={styles.shoppingButtonText}>🛒 View Shopping List</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.newPlanButton}
            onPress={() => setPlan(null)}
          >
            <Text style={styles.newPlanButtonText}>Create New Plan</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const currentRecipe = recipes[currentIndex];
  const progress = getProgress();

  return (
    <View style={styles.container}>
      {/* Progress Header */}
      <View style={styles.header}>
        <View style={styles.mealTypeTabs}>
          {(['breakfast', 'lunch', 'dinner', 'snack'] as MealType[]).map((type) => {
            const needed = plan[`${type}s_needed` as keyof MealPlan] as number;
            const selected = plan[`${type}s_selected` as keyof MealPlan] as number;
            if (needed === 0) return null;

            const isActive = type === currentMealType;
            const isComplete = selected >= needed;

            return (
              <TouchableOpacity
                key={type}
                style={[
                  styles.mealTab,
                  isActive && styles.mealTabActive,
                  isComplete && styles.mealTabComplete,
                ]}
                onPress={() => {
                  setCurrentMealType(type);
                  loadRecipes(plan.id, type);
                }}
              >
                <Text style={[
                  styles.mealTabText,
                  isActive && styles.mealTabTextActive,
                  isComplete && styles.mealTabTextComplete,
                ]}>
                  {MEAL_TYPE_CONFIG[type].emoji} {selected}/{needed}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress.percent}%` }]} />
        </View>
        <View style={styles.progressRow}>
          <Text style={styles.progressText}>
            {progress.selected}/{progress.total} meals • {plan.plan_type}
          </Text>
          {plan.budget_total && plan.budget_total > 0 && (
            <View style={[
              styles.budgetBadge,
              plan.total_estimated_cost > (plan.budget_total * 0.9) && styles.budgetBadgeWarning,
              plan.total_estimated_cost > plan.budget_total && styles.budgetBadgeDanger,
            ]}>
              <Text style={[
                styles.budgetText,
                plan.total_estimated_cost > (plan.budget_total * 0.9) && styles.budgetTextWarning,
                plan.total_estimated_cost > plan.budget_total && styles.budgetTextDanger,
              ]}>
                €{plan.total_estimated_cost.toFixed(0)} / €{plan.budget_total.toFixed(0)}
              </Text>
            </View>
          )}
          {!plan.budget_total && plan.total_estimated_cost > 0 && (
            <Text style={styles.costBadge}>
              ~€{plan.total_estimated_cost.toFixed(0)}
            </Text>
          )}
        </View>
      </View>

      {/* Swipe Cards */}
      <View style={styles.cardContainer}>
        {currentRecipe ? (
          <>
            {/* Next card preview */}
            {recipes[currentIndex + 1] && (
              <View style={[styles.card, styles.cardNext]}>
                <Image
                  source={{ uri: recipes[currentIndex + 1].image_url || 'https://via.placeholder.com/300' }}
                  style={styles.cardImage}
                />
              </View>
            )}

            {/* Current card */}
            <Animated.View
              {...panResponder.panHandlers}
              style={[
                styles.card,
                {
                  transform: [
                    { translateX: position.x },
                    { translateY: position.y },
                    {
                      rotate: position.x.interpolate({
                        inputRange: [-SCREEN_WIDTH, 0, SCREEN_WIDTH],
                        outputRange: ['-15deg', '0deg', '15deg'],
                      }),
                    },
                  ],
                },
              ]}
            >
              {/* Swipe labels */}
              <View style={[styles.swipeLabel, styles.swipeLabelNope, { opacity: showLabels.nope }]}>
                <Text style={styles.swipeLabelText}>NOPE</Text>
              </View>
              <View style={[styles.swipeLabel, styles.swipeLabelYum, { opacity: showLabels.yum }]}>
                <Text style={styles.swipeLabelText}>YUM!</Text>
              </View>
              <View style={[styles.swipeLabel, styles.swipeLabelPrep, { opacity: showLabels.prep }]}>
                <Text style={styles.swipeLabelText}>PREP</Text>
              </View>

              <Image
                source={{ uri: currentRecipe.image_url || 'https://via.placeholder.com/300' }}
                style={styles.cardImage}
              />

              <View style={styles.cardContent}>
                {currentRecipe.overlap_score && currentRecipe.overlap_score > 0 && (
                  <View style={styles.overlapBadge}>
                    <Text style={styles.overlapBadgeText}>
                      ♻️ {currentRecipe.overlap_score} shared ingredients
                    </Text>
                  </View>
                )}

                <Text style={styles.cardTitle}>{currentRecipe.name}</Text>

                <View style={styles.cardMeta}>
                  <Text style={styles.cardMetaText}>
                    {currentRecipe.prep_time_min + currentRecipe.cook_time_min}min
                  </Text>
                  <Text style={styles.cardMetaText}>•</Text>
                  <Text style={styles.cardMetaText}>{currentRecipe.servings} servings</Text>
                </View>

                {currentRecipe.overlap_ingredients && currentRecipe.overlap_ingredients.length > 0 && (
                  <Text style={styles.overlapIngredients}>
                    Uses: {currentRecipe.overlap_ingredients.slice(0, 3).join(', ')}
                  </Text>
                )}
              </View>
            </Animated.View>
          </>
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>🍽️</Text>
            <Text style={styles.emptyText}>
              All {currentMealType}s selected!
            </Text>
          </View>
        )}
      </View>

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={[styles.actionBtn, styles.actionBtnNope]}
          onPress={() => {
            Animated.spring(position, {
              toValue: { x: -SCREEN_WIDTH * 1.5, y: 0 },
              useNativeDriver: false,
            }).start(() => {
              handleSwipe('left');
              position.setValue({ x: 0, y: 0 });
            });
          }}
        >
          <Text style={styles.actionBtnText}>✕</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionBtn, styles.actionBtnPrep]}
          onPress={() => {
            Animated.spring(position, {
              toValue: { x: 0, y: -SCREEN_WIDTH * 1.5 },
              useNativeDriver: false,
            }).start(() => {
              handleSwipe('up');
              position.setValue({ x: 0, y: 0 });
            });
          }}
        >
          <Text style={styles.actionBtnText}>🥗</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionBtn, styles.actionBtnYum]}
          onPress={() => {
            Animated.spring(position, {
              toValue: { x: SCREEN_WIDTH * 1.5, y: 0 },
              useNativeDriver: false,
            }).start(() => {
              handleSwipe('right');
              position.setValue({ x: 0, y: 0 });
            });
          }}
        >
          <Text style={styles.actionBtnText}>❤️</Text>
        </TouchableOpacity>
      </View>

      {/* Instructions */}
      <View style={styles.instructions}>
        <Text style={styles.instructionText}>
          ← Skip • ↑ Meal Prep • Add →
        </Text>
      </View>
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
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  // Create Plan UI
  createPlanCard: {
    margin: 20,
    padding: 24,
    backgroundColor: '#fff',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  createTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
  },
  createSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  planTypeButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 24,
  },
  planTypeBtn: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 24,
    backgroundColor: '#f5f5f5',
    borderWidth: 2,
    borderColor: '#e0e0e0',
  },
  planTypeBtnActive: {
    backgroundColor: '#E8F5E9',
    borderColor: '#4CAF50',
  },
  planTypeBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  planTypeBtnTextActive: {
    color: '#4CAF50',
  },
  createButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  createButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  // Header
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  mealTypeTabs: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 12,
  },
  mealTab: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  mealTabActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  mealTabComplete: {
    backgroundColor: '#E8F5E9',
    borderColor: '#4CAF50',
  },
  mealTabText: {
    fontSize: 12,
    color: '#666',
  },
  mealTabTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  mealTabTextComplete: {
    color: '#4CAF50',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
  },
  budgetBadge: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  budgetBadgeWarning: {
    backgroundColor: '#FFF8E1',
  },
  budgetBadgeDanger: {
    backgroundColor: '#FFEBEE',
  },
  budgetText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4CAF50',
  },
  budgetTextWarning: {
    color: '#F57C00',
  },
  budgetTextDanger: {
    color: '#E53935',
  },
  costBadge: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4CAF50',
  },
  // Cards
  cardContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  card: {
    position: 'absolute',
    width: SCREEN_WIDTH - 40,
    height: 420,
    backgroundColor: '#fff',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
    overflow: 'hidden',
  },
  cardNext: {
    transform: [{ scale: 0.95 }, { translateY: 10 }],
    zIndex: -1,
  },
  cardImage: {
    width: '100%',
    height: '55%',
    backgroundColor: '#f0f0f0',
  },
  cardContent: {
    padding: 16,
    flex: 1,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#333',
    marginBottom: 8,
  },
  cardMeta: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  cardMetaText: {
    fontSize: 14,
    color: '#666',
  },
  overlapBadge: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  overlapBadgeText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '600',
  },
  overlapIngredients: {
    fontSize: 13,
    color: '#4CAF50',
    marginTop: 4,
  },
  // Swipe Labels
  swipeLabel: {
    position: 'absolute',
    top: 40,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    zIndex: 10,
  },
  swipeLabelNope: {
    left: 20,
    backgroundColor: '#ff5252',
    transform: [{ rotate: '-15deg' }],
  },
  swipeLabelYum: {
    right: 20,
    backgroundColor: '#4CAF50',
    transform: [{ rotate: '15deg' }],
  },
  swipeLabelPrep: {
    left: '50%',
    marginLeft: -40,
    backgroundColor: '#2196F3',
  },
  swipeLabelText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  // Action Buttons
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 24,
    paddingVertical: 16,
  },
  actionBtn: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderWidth: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionBtnNope: {
    borderColor: '#ff5252',
  },
  actionBtnPrep: {
    borderColor: '#2196F3',
    width: 70,
    height: 70,
    borderRadius: 35,
  },
  actionBtnYum: {
    borderColor: '#4CAF50',
  },
  actionBtnText: {
    fontSize: 24,
  },
  instructions: {
    paddingBottom: 8,
    alignItems: 'center',
  },
  instructionText: {
    fontSize: 12,
    color: '#999',
  },
  // Empty/Complete states
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
  },
  completeCard: {
    margin: 20,
    padding: 32,
    backgroundColor: '#fff',
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  completeEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  completeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#333',
    marginBottom: 8,
  },
  completeSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  costText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#4CAF50',
    marginBottom: 24,
  },
  shoppingButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
    marginBottom: 12,
  },
  shoppingButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  newPlanButton: {
    paddingVertical: 12,
  },
  newPlanButtonText: {
    color: '#666',
    fontSize: 14,
  },
});
