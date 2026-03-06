import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
  Modal,
  SafeAreaView,
  Animated,
  PanResponder,
} from 'react-native';
import { RouteProp, useRoute, useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import * as Haptics from 'expo-haptics';
import { RootStackParamList } from '../types';
import { api } from '../services/api';
import ScaleMeasureModal, { IngredientToMeasure } from '../components/ScaleMeasureModal';

type RouteProps = RouteProp<RootStackParamList, 'Cooking'>;

interface Step {
  step_number: number;
  title: string;
  instruction: string;
  duration_min: number | null;
  tips: string | null;
  timer_needed: boolean;
}

interface ParsedIngredient {
  name: string;
  amount: number;
  unit: string;
  originalText: string;
}

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SWIPE_THRESHOLD = 80;

export default function CookingScreen() {
  const route = useRoute<RouteProps>();
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const { recipeId } = route.params;

  const [recipeName, setRecipeName] = useState('');
  const [steps, setSteps] = useState<Step[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(true);

  // Timer state
  const [timerModalVisible, setTimerModalVisible] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Scale measuring state
  const [scaleMeasureVisible, setScaleMeasureVisible] = useState(false);
  const [selectedIngredient, setSelectedIngredient] = useState<IngredientToMeasure | null>(null);
  const [measuredIngredients, setMeasuredIngredients] = useState<Set<string>>(new Set());

  // Swipe animation
  const pan = useRef(new Animated.Value(0)).current;

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, gestureState) => {
        return Math.abs(gestureState.dx) > 10;
      },
      onPanResponderMove: (_, gestureState) => {
        pan.setValue(gestureState.dx);
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dx < -SWIPE_THRESHOLD && currentStep < steps.length - 1) {
          // Swipe left - next step
          Animated.spring(pan, {
            toValue: -SCREEN_WIDTH,
            useNativeDriver: true,
          }).start(() => {
            setCurrentStep((prev) => prev + 1);
            pan.setValue(0);
          });
        } else if (gestureState.dx > SWIPE_THRESHOLD && currentStep > 0) {
          // Swipe right - previous step
          Animated.spring(pan, {
            toValue: SCREEN_WIDTH,
            useNativeDriver: true,
          }).start(() => {
            setCurrentStep((prev) => prev - 1);
            pan.setValue(0);
          });
        } else {
          // Snap back
          Animated.spring(pan, {
            toValue: 0,
            useNativeDriver: true,
          }).start();
        }
      },
    })
  ).current;

  useEffect(() => {
    loadSteps();
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [recipeId]);

  const loadSteps = async () => {
    try {
      setLoading(true);
      const data = await api.getRecipeSteps(recipeId);
      setRecipeName(data.recipe_name);
      setSteps(data.steps);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      setCurrentStep((prev) => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      setCurrentStep((prev) => prev - 1);
    }
  };

  const showTimer = (minutes: number) => {
    setTimerSeconds(minutes * 60);
    setTimerModalVisible(true);
    setTimerRunning(false);
  };

  const startTimer = () => {
    if (timerRunning) {
      // Pause
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setTimerRunning(false);
    } else {
      // Start
      setTimerRunning(true);
      timerRef.current = setInterval(() => {
        setTimerSeconds((prev) => {
          if (prev <= 1) {
            if (timerRef.current) {
              clearInterval(timerRef.current);
            }
            setTimerRunning(false);
            // Vibration pattern when done
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    setTimerRunning(false);
    setTimerModalVisible(false);
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const finishCooking = async () => {
    try {
      await api.logMeal({
        recipe_id: recipeId,
        meal_type: 'dinner',
        servings_eaten: 1,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (err) {
      console.error(err);
    }
    navigation.goBack();
  };

  // Parse ingredients from step instruction
  const parseIngredients = (instruction: string): ParsedIngredient[] => {
    const ingredients: ParsedIngredient[] = [];

    // Regex to match patterns like "250g flour", "2 eggs", "5ml vanilla"
    // Updated to handle hyphens (all-purpose), parentheticals, and multi-word names
    const patterns = [
      /(\d+(?:\.\d+)?)\s*(g|ml|kg|l|tbsp|tsp|cup|piece|whole)\s+([a-zA-Z\s\-]+?)(?=\n|,|\(|~|$)/gi,
    ];

    patterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(instruction)) !== null) {
        const amount = parseFloat(match[1]);
        const unit = match[2].toLowerCase();
        let name = match[3].trim();

        // Add space between amount and name if missing (e.g., "2whole" -> "2 whole")
        const displayAmount = `${amount}${unit} ${name}`;

        // Clean up name (remove trailing words like "and", "or", "with")
        name = name.replace(/\s+(and|or|with|melted|chopped)$/i, '').trim();

        // Skip very short names or obvious non-ingredients
        if (name.length > 2 && !name.match(/^(or|and|the|of|a)$/i)) {
          ingredients.push({
            name,
            amount,
            unit,
            originalText: match[0],
          });
        }
      }
    });

    return ingredients;
  };

  const handleIngredientTap = (ingredient: ParsedIngredient) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    setSelectedIngredient({
      name: ingredient.name,
      targetAmount: ingredient.amount,
      unit: ingredient.unit,
    });
    setScaleMeasureVisible(true);
  };

  const handleMeasureComplete = (actualAmount: number) => {
    if (selectedIngredient) {
      const key = `${currentStep}-${selectedIngredient.name}`;
      setMeasuredIngredients(prev => new Set(prev).add(key));
      console.log(`✅ Measured ${actualAmount}${selectedIngredient.unit} of ${selectedIngredient.name}`);
    }
    setScaleMeasureVisible(false);
  };

  const isIngredientMeasured = (ingredient: ParsedIngredient): boolean => {
    const key = `${currentStep}-${ingredient.name}`;
    return measuredIngredients.has(key);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#4CAF50" />
        </View>
      </SafeAreaView>
    );
  }

  const progress = ((currentStep + 1) / steps.length) * 100;
  const step = steps[currentStep];
  const ingredients = step ? parseIngredients(step.instruction) : [];

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeButton}>
          <Text style={styles.closeText}>✕</Text>
        </TouchableOpacity>
        <Text style={styles.recipeName} numberOfLines={1}>
          {recipeName}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Progress bar */}
      <View style={styles.progressContainer}>
        <View style={[styles.progressFill, { width: `${progress}%` }]} />
      </View>

      {/* Card */}
      <Animated.View
        style={[styles.cardWrapper, { transform: [{ translateX: pan }] }]}
        {...panResponder.panHandlers}
      >
        <View style={styles.card}>
          <View style={styles.stepHeader}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>{currentStep + 1}</Text>
            </View>
            <Text style={styles.stepTitle}>{step.title}</Text>
          </View>

          <Text style={styles.instruction}>{step.instruction}</Text>

          {/* Ingredient Chips */}
          {ingredients.length > 0 && (
            <View style={styles.ingredientsContainer}>
              <Text style={styles.ingredientsLabel}>⚖️ Tap to measure:</Text>
              <View style={styles.ingredientChips}>
                {ingredients.map((ingredient, index) => {
                  const measured = isIngredientMeasured(ingredient);
                  return (
                    <TouchableOpacity
                      key={index}
                      style={[
                        styles.ingredientChip,
                        measured && styles.ingredientChipMeasured,
                      ]}
                      onPress={() => handleIngredientTap(ingredient)}
                    >
                      <Text style={[
                        styles.ingredientChipText,
                        measured && styles.ingredientChipTextMeasured,
                      ]}>
                        {measured && '✓ '}
                        {ingredient.amount}{ingredient.unit} {ingredient.name}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          )}

          {step.timer_needed && step.duration_min && (
            <TouchableOpacity
              style={styles.timerButton}
              onPress={() => showTimer(step.duration_min!)}
            >
              <Text style={styles.timerButtonText}>
                ⏱️ Set Timer: {step.duration_min} min
              </Text>
            </TouchableOpacity>
          )}

          {step.tips && (
            <View style={styles.tipBox}>
              <Text style={styles.tipText}>💡 {step.tips}</Text>
            </View>
          )}
        </View>
      </Animated.View>

      {/* Navigation */}
      <View style={styles.navContainer}>
        <TouchableOpacity
          style={[styles.navButton, currentStep === 0 && styles.navButtonDisabled]}
          onPress={prevStep}
          disabled={currentStep === 0}
        >
          <Text style={styles.navButtonText}>← Back</Text>
        </TouchableOpacity>

        <Text style={styles.stepCounter}>
          {currentStep + 1} / {steps.length}
        </Text>

        {currentStep === steps.length - 1 ? (
          <TouchableOpacity style={styles.doneButton} onPress={finishCooking}>
            <Text style={styles.doneButtonText}>Done! 🎉</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.navButton} onPress={nextStep}>
            <Text style={styles.navButtonText}>Next →</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Timer Modal */}
      <Modal visible={timerModalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Timer</Text>
            <Text style={styles.timerDisplay}>{formatTime(timerSeconds)}</Text>
            <View style={styles.timerControls}>
              <TouchableOpacity style={styles.timerControlButton} onPress={stopTimer}>
                <Text style={styles.timerControlText}>Stop</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.timerControlButton, styles.timerStartButton]}
                onPress={startTimer}
              >
                <Text style={[styles.timerControlText, styles.timerStartText]}>
                  {timerRunning ? 'Pause' : timerSeconds === 0 ? 'Done' : 'Start'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Scale Measure Modal */}
      <ScaleMeasureModal
        visible={scaleMeasureVisible}
        ingredient={selectedIngredient}
        onClose={() => setScaleMeasureVisible(false)}
        onComplete={handleMeasureComplete}
      />
    </SafeAreaView>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#4CAF50',
  },
  closeButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeText: {
    fontSize: 24,
    color: '#fff',
  },
  recipeName: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
  },
  progressContainer: {
    height: 4,
    backgroundColor: '#e0e0e0',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  cardWrapper: {
    flex: 1,
    padding: 16,
  },
  card: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  stepNumber: {
    width: 40,
    height: 40,
    borderRadius: 20,
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
  stepTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
  instruction: {
    fontSize: 18,
    lineHeight: 28,
    color: '#333',
    marginBottom: 20,
  },
  timerButton: {
    backgroundColor: '#e3f2fd',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 16,
  },
  timerButtonText: {
    fontSize: 16,
    color: '#1976d2',
    fontWeight: '500',
  },
  tipBox: {
    backgroundColor: '#fff8e1',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  tipText: {
    fontSize: 14,
    color: '#795548',
    lineHeight: 20,
  },
  navContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  navButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  navButtonDisabled: {
    opacity: 0.3,
  },
  navButtonText: {
    fontSize: 16,
    color: '#4CAF50',
    fontWeight: '500',
  },
  stepCounter: {
    fontSize: 16,
    color: '#666',
  },
  doneButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  doneButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
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
    padding: 32,
    alignItems: 'center',
    width: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
  },
  timerDisplay: {
    fontSize: 64,
    fontWeight: '300',
    fontVariant: ['tabular-nums'],
    marginBottom: 24,
  },
  timerControls: {
    flexDirection: 'row',
    gap: 16,
  },
  timerControlButton: {
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  timerStartButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  timerControlText: {
    fontSize: 16,
    color: '#666',
  },
  timerStartText: {
    color: '#fff',
  },
  ingredientsContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#E8F5E9',
    borderRadius: 8,
  },
  ingredientsLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2E7D32',
    marginBottom: 8,
  },
  ingredientChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  ingredientChip: {
    backgroundColor: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  ingredientChipMeasured: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  ingredientChipText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4CAF50',
  },
  ingredientChipTextMeasured: {
    color: '#fff',
  },
});
