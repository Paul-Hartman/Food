import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Vibration,
  Dimensions,
  Animated,
  PanResponder,
  Modal,
  FlatList,
} from 'react-native';
import { API_BASE_URL } from '../config';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = SCREEN_WIDTH * 0.75;
const CARD_MARGIN = 10;
const SWIPE_THRESHOLD = 50;

// Color scheme for each dish
const DISH_COLORS = {
  steak: '#8B4513',
  brussels: '#228B22',
  potatoes: '#DAA520',
  prep: '#6B5B95',
};

// Recipe dishes with nutrition (per serving)
const RECIPE_DISHES = [
  {
    id: 'steak',
    name: 'Reverse Sear Ribeye',
    type: 'main',
    emoji: '🥩',
    color: '#8B4513',
    nutrition: { calories: 650, protein_g: 45, carbs_g: 0, fat_g: 52, fiber_g: 0 },
  },
  {
    id: 'brussels',
    name: 'Roasted Brussels Sprouts',
    type: 'side',
    emoji: '🥬',
    color: '#228B22',
    nutrition: { calories: 120, protein_g: 4, carbs_g: 14, fat_g: 7, fiber_g: 5 },
  },
  {
    id: 'potatoes',
    name: 'Crispy Roasted Potatoes',
    type: 'side',
    emoji: '🥔',
    color: '#DAA520',
    nutrition: { calories: 220, protein_g: 4, carbs_g: 40, fat_g: 6, fiber_g: 4 },
  },
];

// Build the complete step deck with ingredient requirements
const buildStepDeck = (meaterTimeRemaining) => {
  const steakOvenTime = meaterTimeRemaining || 35 * 60;

  // MISE EN PLACE - no timers for mechanical/prep tasks
  const miseEnPlace = [
    { id: 'prep-1', dish: 'prep', phase: 'prep', name: 'Preheat Oven', instruction: 'Set oven to 250°F (120°C) for reverse sear. We\'ll crank it up for sides later.', emoji: '🔥', duration: 0, ingredients: [] },
    {
      id: 'prep-2', dish: 'steak', phase: 'prep', name: 'Temper Steak',
      instruction: 'Take steak out of fridge. Season generously with salt & pepper. Let it come to room temp.',
      emoji: '🥩', duration: 0,
      ingredients: [
        { name: 'Ribeye Steak', amount_g: 450, amount_display: '1 lb (16 oz)', required: true },
        { name: 'Salt', amount_g: 5, amount_display: '1 tsp', required: true },
        { name: 'Black Pepper', amount_g: 2, amount_display: '1/2 tsp', required: true },
      ]
    },
    { id: 'prep-3', dish: 'steak', phase: 'prep', name: 'Insert MEATER', instruction: 'Insert probe into the thickest part. Set target to 115°F - it will rise to 125°F during the long rest.', emoji: '🌡️', duration: 0, meaterSetup: true, ingredients: [] },
    {
      id: 'prep-4', dish: 'potatoes', phase: 'prep', name: 'Cube Potatoes',
      instruction: 'Cut potatoes into 1-inch cubes. Keep sizes similar for even cooking.',
      emoji: '🥔', duration: 0,
      ingredients: [
        { name: 'Potatoes', amount_g: 680, amount_display: '1.5 lbs', required: true },
      ]
    },
    {
      id: 'prep-5', dish: 'potatoes', phase: 'prep', name: 'Start Water',
      instruction: 'Fill large pot with water, add salt generously. Put on high heat to boil.',
      emoji: '🥔', duration: 0,
      ingredients: [
        { name: 'Salt', amount_g: 15, amount_display: '1 tbsp', required: true },
      ]
    },
    {
      id: 'prep-6', dish: 'brussels', phase: 'prep', name: 'Prep Brussels',
      instruction: 'Trim stem ends and halve through the core. Toss with olive oil, salt, and pepper. Set aside.',
      emoji: '🥬', duration: 0,
      ingredients: [
        { name: 'Brussels Sprouts', amount_g: 450, amount_display: '1 lb', required: true },
        { name: 'Olive Oil', amount_g: 30, amount_display: '2 tbsp', required: true },
        { name: 'Salt', amount_g: 3, amount_display: '1/2 tsp', required: true },
        { name: 'Black Pepper', amount_g: 1, amount_display: '1/4 tsp', required: true },
      ]
    },
  ];

  // COOKING STEPS - Optimized flow: Steak low → Rest while sides roast high → Sear → Serve
  const allCookingSteps = [
    // Phase 1: Steak in low oven + parboil potatoes
    { id: 'steak-1', dish: 'steak', phase: 'cook', name: 'Steak in Oven', instruction: 'Place steak on wire rack over sheet pan. Bake at 250°F until MEATER shows 115°F internal.', emoji: '🥩', duration: steakOvenTime, meaterStep: true, sequence: 1, ingredients: [] },
    { id: 'potato-1', dish: 'potatoes', phase: 'cook', name: 'Boil Potatoes', instruction: 'While steak cooks: Add cubed potatoes to boiling water. Cook until fork-tender, about 12 min.', emoji: '🥔', duration: 12 * 60, sequence: 2, ingredients: [] },
    { id: 'potato-2', dish: 'potatoes', phase: 'cook', name: 'Rough Up Edges', instruction: 'Drain well. Return to pot and shake vigorously to rough up edges - this makes them crispy!', emoji: '🥔', duration: 0, sequence: 3, ingredients: [] },

    // Phase 2: Pull steak, crank oven, roast sides during rest
    { id: 'steak-2', dish: 'steak', phase: 'cook', name: 'Pull & Rest Steak', instruction: '🎯 Steak hit 115°F! Remove from oven, tent loosely with foil. It will rest while sides roast (~30 min is perfect).', emoji: '🥩', duration: 0, sequence: 4, ingredients: [] },
    { id: 'oven-1', dish: 'prep', phase: 'cook', name: 'Crank Oven to 425°F', instruction: 'Turn oven up to 425°F (220°C). Put a sheet pan inside to preheat for the potatoes.', emoji: '🔥', duration: 5 * 60, sequence: 5, ingredients: [] },
    {
      id: 'potato-3', dish: 'potatoes', phase: 'cook', name: 'Roast Potatoes',
      instruction: 'Toss potatoes with oil, salt, rosemary. Spread on HOT sheet pan. Roast 35 min, flip halfway.',
      emoji: '🥔', duration: 35 * 60, sequence: 6,
      ingredients: [
        { name: 'Olive Oil', amount_g: 30, amount_display: '2 tbsp', required: true },
        { name: 'Salt', amount_g: 3, amount_display: '1/2 tsp', required: true },
        { name: 'Rosemary', amount_g: 2, amount_display: '1 sprig', required: false },
      ]
    },
    { id: 'brussels-1', dish: 'brussels', phase: 'cook', name: 'Roast Brussels', instruction: 'Add brussels to oven (can share pan or use second). Cut-side down. Roast 25 min until caramelized.', emoji: '🥬', duration: 25 * 60, sequence: 7, ingredients: [] },

    // Phase 3: Sear steak when sides almost done
    {
      id: 'steak-3', dish: 'steak', phase: 'cook', name: 'Heat Cast Iron',
      instruction: '⏰ ~5 min before sides done: Heat cast iron on HIGH. Add avocado oil. Wait until smoking!',
      emoji: '🥩', duration: 3 * 60, sequence: 8,
      ingredients: [
        { name: 'Avocado Oil', amount_g: 15, amount_display: '1 tbsp', required: true },
      ]
    },
    { id: 'steak-4', dish: 'steak', phase: 'cook', name: 'Sear Side 1', instruction: 'Place rested steak in screaming hot pan. DO NOT MOVE IT. Hard sear for 60-90 seconds.', emoji: '🥩', duration: 90, sequence: 9, ingredients: [] },
    { id: 'steak-5', dish: 'steak', phase: 'cook', name: 'Sear Side 2', instruction: 'Flip once. Sear the other side 60-90 seconds. Still don\'t move it around.', emoji: '🥩', duration: 90, sequence: 10, ingredients: [] },
    {
      id: 'steak-6', dish: 'steak', phase: 'cook', name: 'Butter Baste',
      instruction: 'Add butter, crushed garlic, thyme. Tilt pan and spoon butter over steak for 30-60 seconds.',
      emoji: '🥩', duration: 60, sequence: 11,
      ingredients: [
        { name: 'Butter', amount_g: 30, amount_display: '2 tbsp', required: true },
        { name: 'Garlic', amount_g: 10, amount_display: '2 cloves', required: true },
        { name: 'Thyme', amount_g: 2, amount_display: '2 sprigs', required: false },
      ]
    },

    // Phase 4: Final rest & serve
    { id: 'steak-7', dish: 'steak', phase: 'cook', name: 'Quick Rest & Slice', instruction: 'Rest 2-3 min on cutting board while you plate sides. Slice against the grain. Serve immediately!', emoji: '🥩', duration: 3 * 60, sequence: 12, ingredients: [] },
  ];

  // Final deck: mise en place first, then cooking steps in logical order
  const deck = [...miseEnPlace, ...allCookingSteps];
  deck.forEach((s, i) => { s.deckIndex = i; });

  return deck;
};

// Format time
const formatTime = (seconds) => {
  if (!seconds || seconds <= 0) return '';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins >= 60) {
    const hrs = Math.floor(mins / 60);
    const m = mins % 60;
    return `${hrs}h ${m}m`;
  }
  return secs > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${mins}m`;
};

// Swipeable Card Deck Component
const CardDeck = ({ cards, currentIndex, onIndexChange, meaterData, onStartTimer, activeTimers, onConnectMeater }) => {
  const position = useRef(new Animated.Value(currentIndex)).current;
  const currentIndexRef = useRef(currentIndex);

  // Keep ref in sync with prop
  useEffect(() => {
    currentIndexRef.current = currentIndex;
  }, [currentIndex]);

  // Animate to new index when currentIndex changes
  useEffect(() => {
    Animated.spring(position, {
      toValue: currentIndex,
      useNativeDriver: true,
      friction: 8,
      tension: 40,
    }).start();
  }, [currentIndex]);

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: (_, gesture) => Math.abs(gesture.dx) > 10,
      onPanResponderGrant: () => {
        position.setOffset(currentIndexRef.current);
        position.setValue(0);
      },
      onPanResponderMove: (_, gesture) => {
        // Convert drag pixels to card index offset
        const dragOffset = -gesture.dx / (CARD_WIDTH + CARD_MARGIN * 2);
        position.setValue(dragOffset);
      },
      onPanResponderRelease: (_, gesture) => {
        position.flattenOffset();

        const dragOffset = -gesture.dx / (CARD_WIDTH + CARD_MARGIN * 2);
        const velocity = -gesture.vx;

        let newIndex = currentIndexRef.current;

        // Determine if we should change cards based on drag distance or velocity
        if (dragOffset > 0.3 || velocity > 0.5) {
          // Swiped left - go to next
          newIndex = Math.min(currentIndexRef.current + 1, cards.length - 1);
        } else if (dragOffset < -0.3 || velocity < -0.5) {
          // Swiped right - go to previous
          newIndex = Math.max(currentIndexRef.current - 1, 0);
        }

        onIndexChange(newIndex);
      },
    })
  ).current;

  const renderCard = (card, index) => {
    // Only render cards within range
    if (index < currentIndex - 2 || index > currentIndex + 2) return null;

    const color = DISH_COLORS[card.dish] || DISH_COLORS.prep;
    const isPrep = card.phase === 'prep';
    const isMeaterStep = card.meaterStep;
    const hasTimer = card.duration > 0 && !isMeaterStep;
    const activeTimer = activeTimers?.find(t => t.name?.includes(card.name));

    // Animated transforms based on position
    const translateX = position.interpolate({
      inputRange: [index - 1, index, index + 1],
      outputRange: [CARD_WIDTH + CARD_MARGIN * 2, 0, -(CARD_WIDTH + CARD_MARGIN * 2)],
      extrapolate: 'clamp',
    });

    const scale = position.interpolate({
      inputRange: [index - 1, index, index + 1],
      outputRange: [0.85, 1, 0.85],
      extrapolate: 'clamp',
    });

    const opacity = position.interpolate({
      inputRange: [index - 1, index, index + 1],
      outputRange: [0.5, 1, 0.5],
      extrapolate: 'clamp',
    });

    const zIndex = index === currentIndex ? 10 : 5;

    return (
      <Animated.View
        key={card.id}
        {...panResponder.panHandlers}
        style={[
          styles.card,
          {
            transform: [{ translateX }, { scale }],
            opacity,
            zIndex,
            borderColor: color,
          },
        ]}
      >
        {/* Card Header */}
        <View style={[styles.cardHeader, { backgroundColor: color }]}>
          <Text style={styles.cardEmoji}>{card.emoji}</Text>
          <View style={styles.cardHeaderText}>
            <Text style={styles.cardPhase}>{isPrep ? 'MISE EN PLACE' : `STEP ${card.sequence}`}</Text>
            <Text style={styles.cardName}>{card.name}</Text>
          </View>
          {card.duration > 0 && (
            <View style={styles.cardDuration}>
              <Text style={styles.cardDurationText}>{formatTime(card.duration)}</Text>
            </View>
          )}
        </View>

        {/* Card Body */}
        <View style={styles.cardBody}>
          <Text style={styles.cardInstruction}>{card.instruction}</Text>

          {/* Meater Status for meater steps */}
          {isMeaterStep && meaterData?.connected && (
            <View style={styles.meaterInCard}>
              <Text style={styles.meaterInCardLabel}>MEATER</Text>
              <Text style={styles.meaterInCardTemp}>
                {meaterData.internal_temp_f ? `${Math.round(meaterData.internal_temp_f)}°F` : '--'}
                {' → '}
                {meaterData.target_temp_f ? `${Math.round(meaterData.target_temp_f)}°F` : '--'}
              </Text>
              {meaterData.time_remaining_seconds > 0 && (
                <Text style={styles.meaterInCardTime}>
                  {formatTime(meaterData.time_remaining_seconds)} remaining
                </Text>
              )}
            </View>
          )}

          {/* Active Timer Display */}
          {activeTimer && (
            <View style={styles.activeTimerInCard}>
              <Text style={styles.activeTimerLabel}>TIMER</Text>
              <Text style={styles.activeTimerTime}>
                {activeTimer.remaining > 0 ? formatTime(activeTimer.remaining) : 'DONE!'}
              </Text>
            </View>
          )}

          {/* Timer Button */}
          {hasTimer && !activeTimer && index === currentIndex && (
            <TouchableOpacity
              style={[styles.startTimerButton, { backgroundColor: color }]}
              onPress={() => onStartTimer(card)}
            >
              <Text style={styles.startTimerText}>Start {formatTime(card.duration)} Timer</Text>
            </TouchableOpacity>
          )}

          {/* Meater Badge */}
          {isMeaterStep && (
            <View style={styles.meaterBadge}>
              <Text style={styles.meaterBadgeText}>🌡️ MEATER Controlled</Text>
            </View>
          )}

          {/* Connect to MEATER button for setup step */}
          {card.meaterSetup && (
            <View style={styles.meaterSetupSection}>
              {meaterData?.connected ? (
                <View style={styles.meaterConnected}>
                  <Text style={styles.meaterConnectedText}>✓ MEATER Connected</Text>
                  {meaterData.internal_temp_f && (
                    <Text style={styles.meaterConnectedTemp}>
                      Current: {Math.round(meaterData.internal_temp_f)}°F
                    </Text>
                  )}
                </View>
              ) : (
                <TouchableOpacity
                  style={styles.connectMeaterButton}
                  onPress={() => {
                    onConnectMeater();
                    Alert.alert('Connecting...', 'Checking MEATER connection via Home Assistant');
                  }}
                >
                  <Text style={styles.connectMeaterText}>🌡️ Connect to MEATER</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>

        {/* Card Footer - Progress */}
        <View style={styles.cardFooter}>
          <Text style={styles.cardProgress}>{card.deckIndex + 1} / {cards.length}</Text>
          <View style={styles.progressDots}>
            {cards.slice(Math.max(0, currentIndex - 2), currentIndex + 3).map((_, i) => {
              const actualIndex = Math.max(0, currentIndex - 2) + i;
              return (
                <View
                  key={actualIndex}
                  style={[
                    styles.progressDot,
                    actualIndex === currentIndex && styles.progressDotActive,
                  ]}
                />
              );
            })}
          </View>
        </View>
      </Animated.View>
    );
  };

  return (
    <View style={styles.deckContainer}>
      {cards.map((card, index) => renderCard(card, index))}
    </View>
  );
};

// Meater Status Bar (compact)
const MeaterBar = ({ meaterData }) => {
  if (!meaterData) return null;

  const { connected, internal_temp_f, target_temp_f, time_remaining_seconds, cook_state_display } = meaterData;

  if (!connected) {
    return (
      <View style={styles.meaterBar}>
        <Text style={styles.meaterBarText}>🌡️ MEATER: Not connected</Text>
      </View>
    );
  }

  return (
    <View style={[styles.meaterBar, styles.meaterBarActive]}>
      <Text style={styles.meaterBarText}>
        🌡️ {internal_temp_f ? `${Math.round(internal_temp_f)}°F` : '--'}
        {' → '}
        {target_temp_f ? `${Math.round(target_temp_f)}°F` : '--'}
      </Text>
      {time_remaining_seconds > 0 && (
        <Text style={styles.meaterBarTime}>{formatTime(time_remaining_seconds)}</Text>
      )}
      {cook_state_display && (
        <Text style={styles.meaterBarState}>{cook_state_display}</Text>
      )}
    </View>
  );
};

// Active Timers Bar
const TimersBar = ({ timers, onStop }) => {
  if (!timers || timers.length === 0) return null;

  return (
    <ScrollView horizontal style={styles.timersBar} showsHorizontalScrollIndicator={false}>
      {timers.map(timer => (
        <View key={timer.id} style={[styles.timerPill, timer.remaining <= 0 && styles.timerPillDone]}>
          <Text style={styles.timerPillName} numberOfLines={1}>{timer.name}</Text>
          <Text style={styles.timerPillTime}>
            {timer.remaining > 0 ? formatTime(timer.remaining) : 'DONE'}
          </Text>
          <TouchableOpacity onPress={() => onStop(timer.id)} style={styles.timerPillClose}>
            <Text style={styles.timerPillCloseText}>✕</Text>
          </TouchableOpacity>
        </View>
      ))}
    </ScrollView>
  );
};

export default function CookingScreen() {
  const [timers, setTimers] = useState([]);
  const [meaterData, setMeaterData] = useState(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [pantryItems, setPantryItems] = useState([]);
  const [selectedIngredients, setSelectedIngredients] = useState([]);
  const [mealLogged, setMealLogged] = useState(false);
  const [ingredientModalVisible, setIngredientModalVisible] = useState(false);

  // New state for ingredient tracking and meal completion
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [usedIngredients, setUsedIngredients] = useState({}); // { stepId: [{ pantryItem, amount }] }
  const [showPantryTray, setShowPantryTray] = useState(false);
  const [nutritionProgress, setNutritionProgress] = useState(null);
  const [showMealComplete, setShowMealComplete] = useState(false);
  const [mealRating, setMealRating] = useState(0);
  const [mealNotes, setMealNotes] = useState('');
  const [mealChanges, setMealChanges] = useState('');
  const [fusionAnimating, setFusionAnimating] = useState(false);

  // Animation refs
  const fusionAnim = useRef(new Animated.Value(0)).current;
  const intervalRef = useRef(null);
  const meaterIntervalRef = useRef(null);

  // Build deck based on Meater time
  const deck = buildStepDeck(meaterData?.time_remaining_seconds);

  // Calculate total meal nutrition
  const totalMealNutrition = RECIPE_DISHES.reduce((acc, dish) => ({
    calories: acc.calories + dish.nutrition.calories,
    protein_g: acc.protein_g + dish.nutrition.protein_g,
    carbs_g: acc.carbs_g + dish.nutrition.carbs_g,
    fat_g: acc.fat_g + dish.nutrition.fat_g,
    fiber_g: acc.fiber_g + dish.nutrition.fiber_g,
  }), { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 });

  // Fetch pantry items to link to meal - prioritize today's items
  const fetchPantryItems = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pantry/inventory`);
      const data = await response.json();
      setPantryItems(data);

      // Auto-select items added today (for tonight's meal)
      const today = new Date().toISOString().split('T')[0];
      const todayItems = data.filter(item => {
        const itemDate = item.created_at ? item.created_at.split('T')[0] : null;
        return itemDate === today;
      });

      // If items were added today, auto-select them; otherwise select all
      if (todayItems.length > 0) {
        setSelectedIngredients(todayItems.map(item => item.id));
      } else if (data.length > 0) {
        // No items today - show all but don't auto-select
        setSelectedIngredients([]);
      }
    } catch (error) {
      console.error('Failed to fetch pantry:', error);
    }
  };

  // Fetch timers
  const fetchTimers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/timers`);
      const data = await response.json();
      setTimers(data.filter(t => t.status !== 'stopped'));

      data.forEach(timer => {
        if (timer.status === 'running' && timer.remaining <= 0) {
          Vibration.vibrate([500, 200, 500, 200, 500]);
        }
      });
    } catch (error) {
      console.error('Failed to fetch timers:', error);
    }
  };

  // Fetch Meater
  const fetchMeaterStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/meater/status`);
      const data = await response.json();
      setMeaterData(data);

      if (data.cook_state === 'ready_for_resting' || data.cook_state === 'finished') {
        Vibration.vibrate([1000, 500, 1000, 500, 1000]);
      }
    } catch (error) {
      console.error('Failed to fetch Meater status:', error);
    }
  };

  useEffect(() => {
    fetchTimers();
    fetchMeaterStatus();
    fetchPantryItems();
    fetchNutritionProgress();
    intervalRef.current = setInterval(fetchTimers, 1000);
    meaterIntervalRef.current = setInterval(fetchMeaterStatus, 3000);

    return () => {
      clearInterval(intervalRef.current);
      clearInterval(meaterIntervalRef.current);
    };
  }, []);

  // Fetch nutrition progress
  const fetchNutritionProgress = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/nutrition/today`);
      const data = await response.json();
      setNutritionProgress(data);
    } catch (error) {
      console.error('Failed to fetch nutrition:', error);
    }
  };

  // Mark a step as complete and optionally assign an ingredient
  const completeStep = (stepId, assignedIngredient = null) => {
    setCompletedSteps(prev => new Set([...prev, stepId]));

    if (assignedIngredient) {
      setUsedIngredients(prev => ({
        ...prev,
        [stepId]: [...(prev[stepId] || []), assignedIngredient]
      }));

      // Deduct from pantry
      if (assignedIngredient.inventory_id && assignedIngredient.amount_g) {
        fetch(`${API_BASE_URL}/api/pantry/inventory/${assignedIngredient.inventory_id}/deduct`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount_g: assignedIngredient.amount_g }),
        }).then(() => fetchPantryItems()); // Refresh pantry
      }
    }

    // Check if all steps are complete
    const allStepsComplete = deck.every(step =>
      completedSteps.has(step.id) || step.id === stepId
    );

    if (allStepsComplete && completedSteps.size === deck.length - 1) {
      triggerFusionAnimation();
    }
  };

  // Assign pantry item to current step
  const assignIngredientToStep = (pantryItem, stepIngredient) => {
    const currentStep = deck[currentCardIndex];
    completeStep(currentStep.id, {
      inventory_id: pantryItem.id,
      product_id: pantryItem.product_id,
      ingredient_name: pantryItem.product_name || pantryItem.name,
      amount_g: stepIngredient.amount_g,
      step_id: currentStep.id,
    });

    Alert.alert(
      'Ingredient Used!',
      `${stepIngredient.amount_display} of ${pantryItem.product_name || pantryItem.name} used.`,
      [{ text: 'OK' }]
    );
  };

  // Trigger fusion animation when recipe is complete
  const triggerFusionAnimation = () => {
    setFusionAnimating(true);
    Vibration.vibrate([200, 100, 200, 100, 500]);

    Animated.sequence([
      Animated.timing(fusionAnim, {
        toValue: 1,
        duration: 1500,
        useNativeDriver: true,
      }),
      Animated.delay(500),
    ]).start(() => {
      setShowMealComplete(true);
      setFusionAnimating(false);
    });
  };

  // Complete and save the meal
  const completeMeal = async () => {
    try {
      // Build dishes with ingredients
      const dishes = RECIPE_DISHES.map(dish => {
        const dishIngredients = Object.entries(usedIngredients)
          .filter(([stepId]) => {
            const step = deck.find(s => s.id === stepId);
            return step && step.dish === dish.id;
          })
          .flatMap(([stepId, ingredients]) => ingredients);

        return {
          dish_name: dish.name,
          dish_type: dish.type,
          recipe_id: dish.id,
          recipe_source: 'custom',
          ...dish.nutrition,
          ingredients: dishIngredients,
        };
      });

      const response = await fetch(`${API_BASE_URL}/api/meals/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meal_name: `${RECIPE_DISHES[0].name} with ${RECIPE_DISHES.slice(1).map(d => d.name).join(' & ')}`,
          meal_type: 'dinner',
          servings: 2,
          dishes,
          rating: mealRating,
          notes: mealNotes,
          changes_for_next_time: mealChanges,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        setMealLogged(true);
        fetchNutritionProgress(); // Refresh nutrition
        Alert.alert(
          'Meal Complete!',
          `Your meal has been logged.\n\nNutrition added:\n${result.nutrition_added.calories} cal\n${result.nutrition_added.protein_g}g protein`,
          [{ text: 'Great!' }]
        );
      }
    } catch (error) {
      console.error('Failed to complete meal:', error);
      Alert.alert('Error', 'Failed to save meal');
    }
  };

  // Toggle ingredient selection
  const toggleIngredient = (itemId) => {
    setSelectedIngredients(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  // Select/deselect all ingredients
  const toggleAllIngredients = () => {
    if (selectedIngredients.length === pantryItems.length) {
      setSelectedIngredients([]);
    } else {
      setSelectedIngredients(pantryItems.map(item => item.id));
    }
  };

  // Open ingredient selection modal before logging
  const openIngredientSelector = () => {
    if (pantryItems.length === 0) {
      Alert.alert(
        'No Ingredients',
        'Scan some ingredients into your pantry first before logging a meal.',
        [{ text: 'OK' }]
      );
      return;
    }
    setIngredientModalVisible(true);
  };

  // Log meal with selected ingredients
  const handleLogMeal = async () => {
    try {
      // Get all unique dishes from the deck
      const dishes = ['Reverse Sear Ribeye', 'Roasted Brussels Sprouts', 'Crispy Roasted Potatoes'];

      // Filter to only selected ingredients
      const selectedItems = pantryItems.filter(item => selectedIngredients.includes(item.id));

      if (selectedItems.length === 0) {
        Alert.alert(
          'No Ingredients Selected',
          'Please select at least one ingredient for this meal.',
          [{ text: 'OK' }]
        );
        return;
      }

      const mealIngredients = selectedItems.map(item => ({
        inventory_id: item.id,
        product_id: item.product_id,
        ingredient_name: item.product_name || item.name,
        amount_used_g: item.current_weight_g || null,
      }));

      const response = await fetch(`${API_BASE_URL}/api/meals/cooked`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meal_name: dishes.join(' + '),
          meal_type: 'dinner',
          servings: 2,
          recipe_source: 'custom',
          notes: 'Reverse sear steak with roasted sides',
          ingredients: mealIngredients,
        }),
      });

      if (response.ok) {
        setMealLogged(true);
        setIngredientModalVisible(false);
        Alert.alert(
          'Meal Logged!',
          `Tonight's dinner recorded:\n${dishes.join('\n')}\n\nWith ${mealIngredients.length} ingredients from your pantry.`,
          [{ text: 'Great!' }]
        );
      } else {
        Alert.alert('Error', 'Failed to log meal');
      }
    } catch (error) {
      console.error('Failed to log meal:', error);
      Alert.alert('Error', 'Failed to log meal');
    }
  };

  const handleStartTimer = async (card) => {
    try {
      const createResponse = await fetch(`${API_BASE_URL}/api/timers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${card.emoji} ${card.name}`,
          duration: card.duration,
        }),
      });
      const { id } = await createResponse.json();

      await fetch(`${API_BASE_URL}/api/timers/${id}/start`, { method: 'POST' });
      fetchTimers();
    } catch (error) {
      Alert.alert('Error', 'Failed to start timer');
    }
  };

  const handleStopTimer = async (timerId) => {
    try {
      await fetch(`${API_BASE_URL}/api/timers/${timerId}/stop`, { method: 'POST' });
      fetchTimers();
    } catch (error) {
      Alert.alert('Error', 'Failed to stop timer');
    }
  };

  const goToCard = (index) => {
    setCurrentCardIndex(Math.max(0, Math.min(index, deck.length - 1)));
  };

  // Get current step's ingredient requirements
  const currentStep = deck[currentCardIndex];
  const stepIngredients = currentStep?.ingredients || [];
  const hasIngredients = stepIngredients.length > 0;

  return (
    <View style={styles.container}>
      {/* Nutrition Progress Bar */}
      {nutritionProgress && (
        <View style={styles.nutritionBar}>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Cal</Text>
            <View style={styles.nutritionProgress}>
              <View style={[styles.nutritionFill, { width: `${Math.min(nutritionProgress.progress?.calories || 0, 100)}%` }]} />
            </View>
            <Text style={styles.nutritionValue}>{nutritionProgress.consumed?.calories || 0}</Text>
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>P</Text>
            <View style={styles.nutritionProgress}>
              <View style={[styles.nutritionFill, styles.proteinFill, { width: `${Math.min(nutritionProgress.progress?.protein_g || 0, 100)}%` }]} />
            </View>
            <Text style={styles.nutritionValue}>{Math.round(nutritionProgress.consumed?.protein_g || 0)}g</Text>
          </View>
        </View>
      )}

      {/* Meater Status Bar */}
      <MeaterBar meaterData={meaterData} />

      {/* Active Timers */}
      <TimersBar timers={timers} onStop={handleStopTimer} />

      {/* Ingredient Requirements for Current Step */}
      {hasIngredients && (
        <View style={styles.ingredientRequirements}>
          <Text style={styles.ingredientReqTitle}>Ingredients Needed:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {stepIngredients.map((ing, idx) => (
              <TouchableOpacity
                key={idx}
                style={[styles.ingredientReqChip, !ing.required && styles.ingredientOptional]}
                onPress={() => setShowPantryTray(true)}
              >
                <Text style={styles.ingredientReqText}>{ing.amount_display}</Text>
                <Text style={styles.ingredientReqName}>{ing.name}</Text>
                {!ing.required && <Text style={styles.ingredientOptionalLabel}>(opt)</Text>}
              </TouchableOpacity>
            ))}
          </ScrollView>
          <TouchableOpacity style={styles.usePantryButton} onPress={() => setShowPantryTray(!showPantryTray)}>
            <Text style={styles.usePantryText}>{showPantryTray ? '▼ Hide Pantry' : '▲ Use from Pantry'}</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Pantry Tray - Draggable ingredient cards */}
      {showPantryTray && (
        <View style={styles.pantryTray}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {pantryItems.map(item => (
              <TouchableOpacity
                key={item.id}
                style={styles.pantryCard}
                onPress={() => {
                  // Find matching ingredient requirement
                  const matchingIng = stepIngredients.find(ing =>
                    ing.name.toLowerCase().includes((item.product_name || item.name || '').toLowerCase().split(' ')[0]) ||
                    (item.product_name || item.name || '').toLowerCase().includes(ing.name.toLowerCase().split(' ')[0])
                  );
                  if (matchingIng) {
                    assignIngredientToStep(item, matchingIng);
                    setShowPantryTray(false);
                  } else {
                    Alert.alert(
                      'Use Ingredient?',
                      `Use ${item.product_name || item.name} for this step?`,
                      [
                        { text: 'Cancel', style: 'cancel' },
                        {
                          text: 'Use',
                          onPress: () => {
                            assignIngredientToStep(item, { amount_g: 50, amount_display: 'some' });
                            setShowPantryTray(false);
                          }
                        }
                      ]
                    );
                  }
                }}
              >
                <Text style={styles.pantryCardEmoji}>🥫</Text>
                <Text style={styles.pantryCardName} numberOfLines={2}>{item.product_name || item.name}</Text>
                {item.current_weight_g && (
                  <Text style={styles.pantryCardWeight}>{item.current_weight_g}g left</Text>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Card Deck */}
      <CardDeck
        cards={deck}
        currentIndex={currentCardIndex}
        onIndexChange={goToCard}
        meaterData={meaterData}
        onStartTimer={handleStartTimer}
        activeTimers={timers}
        onConnectMeater={fetchMeaterStatus}
        completedSteps={completedSteps}
        onCompleteStep={completeStep}
      />

      {/* Navigation Arrows */}
      <View style={styles.navArrows}>
        <TouchableOpacity
          style={[styles.navArrow, currentCardIndex === 0 && styles.navArrowDisabled]}
          onPress={() => goToCard(currentCardIndex - 1)}
          disabled={currentCardIndex === 0}
        >
          <Text style={styles.navArrowText}>‹</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.navArrow, currentCardIndex === deck.length - 1 && styles.navArrowDisabled]}
          onPress={() => goToCard(currentCardIndex + 1)}
          disabled={currentCardIndex === deck.length - 1}
        >
          <Text style={styles.navArrowText}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Quick Jump */}
      <View style={styles.quickJump}>
        <TouchableOpacity style={styles.quickJumpButton} onPress={() => goToCard(0)}>
          <Text style={styles.quickJumpText}>Prep</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickJumpButton} onPress={() => goToCard(6)}>
          <Text style={styles.quickJumpText}>Cook</Text>
        </TouchableOpacity>
        <View style={styles.quickJumpDivider} />
        <TouchableOpacity style={[styles.quickJumpButton, styles.quickJumpSteak]} onPress={() => {
          const idx = deck.findIndex(c => c.id === 'steak-1');
          if (idx >= 0) goToCard(idx);
        }}>
          <Text style={styles.quickJumpText}>🥩</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.quickJumpButton, styles.quickJumpPotato]} onPress={() => {
          const idx = deck.findIndex(c => c.id === 'potato-1');
          if (idx >= 0) goToCard(idx);
        }}>
          <Text style={styles.quickJumpText}>🥔</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.quickJumpButton, styles.quickJumpBrussels]} onPress={() => {
          const idx = deck.findIndex(c => c.id === 'brussels-1');
          if (idx >= 0) goToCard(idx);
        }}>
          <Text style={styles.quickJumpText}>🥬</Text>
        </TouchableOpacity>
        <View style={styles.quickJumpDivider} />
        <TouchableOpacity
          style={[styles.quickJumpButton, mealLogged ? styles.quickJumpLogged : styles.quickJumpLog]}
          onPress={openIngredientSelector}
          disabled={mealLogged}
        >
          <Text style={styles.quickJumpText}>{mealLogged ? '✓' : '📝'}</Text>
        </TouchableOpacity>
      </View>

      {/* Pantry Items Count */}
      {pantryItems.length > 0 && (
        <View style={styles.pantryIndicator}>
          <Text style={styles.pantryIndicatorText}>
            {selectedIngredients.length}/{pantryItems.length} ingredients selected for meal
          </Text>
        </View>
      )}

      {/* Ingredient Selection Modal */}
      <Modal
        visible={ingredientModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setIngredientModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Ingredients</Text>
              <TouchableOpacity onPress={() => setIngredientModalVisible(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.modalSubtitle}>
              Choose which pantry items were used in tonight's meal
            </Text>

            <TouchableOpacity style={styles.selectAllButton} onPress={toggleAllIngredients}>
              <Text style={styles.selectAllText}>
                {selectedIngredients.length === pantryItems.length ? 'Deselect All' : 'Select All'}
              </Text>
            </TouchableOpacity>

            <FlatList
              data={pantryItems}
              keyExtractor={(item) => item.id.toString()}
              style={styles.ingredientList}
              renderItem={({ item }) => {
                const isSelected = selectedIngredients.includes(item.id);
                const isToday = item.created_at && item.created_at.split('T')[0] === new Date().toISOString().split('T')[0];
                return (
                  <TouchableOpacity
                    style={[styles.ingredientItem, isSelected && styles.ingredientItemSelected]}
                    onPress={() => toggleIngredient(item.id)}
                  >
                    <View style={styles.ingredientCheckbox}>
                      <Text style={styles.ingredientCheckmark}>{isSelected ? '✓' : ''}</Text>
                    </View>
                    <View style={styles.ingredientInfo}>
                      <Text style={styles.ingredientName}>{item.product_name || item.name}</Text>
                      {item.brand && <Text style={styles.ingredientBrand}>{item.brand}</Text>}
                      {isToday && <Text style={styles.ingredientToday}>Added today</Text>}
                    </View>
                    {item.current_weight_g && (
                      <Text style={styles.ingredientWeight}>{item.current_weight_g}g</Text>
                    )}
                  </TouchableOpacity>
                );
              }}
            />

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={[styles.logMealButton, selectedIngredients.length === 0 && styles.logMealButtonDisabled]}
                onPress={handleLogMeal}
                disabled={selectedIngredients.length === 0}
              >
                <Text style={styles.logMealButtonText}>
                  Log Meal with {selectedIngredients.length} Ingredient{selectedIngredients.length !== 1 ? 's' : ''}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Fusion Animation Overlay */}
      {fusionAnimating && (
        <View style={styles.fusionOverlay}>
          <Animated.View style={[styles.fusionContainer, {
            transform: [{
              scale: fusionAnim.interpolate({
                inputRange: [0, 0.5, 1],
                outputRange: [1, 1.2, 0.8],
              })
            }],
            opacity: fusionAnim.interpolate({
              inputRange: [0, 0.8, 1],
              outputRange: [1, 1, 0],
            }),
          }]}>
            {RECIPE_DISHES.map((dish, idx) => (
              <Animated.View
                key={dish.id}
                style={[styles.fusionCard, {
                  backgroundColor: dish.color,
                  transform: [{
                    translateX: fusionAnim.interpolate({
                      inputRange: [0, 0.5, 1],
                      outputRange: [idx === 0 ? -80 : idx === 2 ? 80 : 0, 0, 0],
                    })
                  }, {
                    translateY: fusionAnim.interpolate({
                      inputRange: [0, 0.5, 1],
                      outputRange: [idx === 1 ? -50 : 50, 0, 0],
                    })
                  }, {
                    rotate: fusionAnim.interpolate({
                      inputRange: [0, 0.5, 1],
                      outputRange: [`${idx * 10 - 10}deg`, '0deg', '0deg'],
                    })
                  }],
                }]}
              >
                <Text style={styles.fusionEmoji}>{dish.emoji}</Text>
                <Text style={styles.fusionDishName}>{dish.name}</Text>
              </Animated.View>
            ))}
          </Animated.View>
          <Animated.Text style={[styles.fusionText, {
            opacity: fusionAnim.interpolate({
              inputRange: [0.3, 0.7],
              outputRange: [0, 1],
            })
          }]}>
            FUSING...
          </Animated.Text>
        </View>
      )}

      {/* Meal Complete Modal with Rating */}
      <Modal
        visible={showMealComplete}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowMealComplete(false)}
      >
        <View style={styles.modalOverlay}>
          <ScrollView style={styles.mealCompleteScroll}>
            <View style={styles.mealCompleteContent}>
              {/* Meal Card */}
              <View style={styles.mealCard}>
                <View style={styles.mealCardHeader}>
                  <View style={styles.mealCardEmojis}>
                    {RECIPE_DISHES.map(d => (
                      <Text key={d.id} style={styles.mealCardEmoji}>{d.emoji}</Text>
                    ))}
                  </View>
                  <Text style={styles.mealCardTitle}>Tonight's Dinner</Text>
                  <Text style={styles.mealCardSubtitle}>
                    {RECIPE_DISHES[0].name} with {RECIPE_DISHES.slice(1).map(d => d.name).join(' & ')}
                  </Text>
                </View>

                {/* Nutrition Summary */}
                <View style={styles.mealNutrition}>
                  <View style={styles.nutritionBox}>
                    <Text style={styles.nutritionBoxValue}>{totalMealNutrition.calories}</Text>
                    <Text style={styles.nutritionBoxLabel}>Calories</Text>
                  </View>
                  <View style={styles.nutritionBox}>
                    <Text style={styles.nutritionBoxValue}>{totalMealNutrition.protein_g}g</Text>
                    <Text style={styles.nutritionBoxLabel}>Protein</Text>
                  </View>
                  <View style={styles.nutritionBox}>
                    <Text style={styles.nutritionBoxValue}>{totalMealNutrition.carbs_g}g</Text>
                    <Text style={styles.nutritionBoxLabel}>Carbs</Text>
                  </View>
                  <View style={styles.nutritionBox}>
                    <Text style={styles.nutritionBoxValue}>{totalMealNutrition.fat_g}g</Text>
                    <Text style={styles.nutritionBoxLabel}>Fat</Text>
                  </View>
                </View>

                {/* Individual Dishes */}
                <View style={styles.dishBreakdown}>
                  {RECIPE_DISHES.map(dish => (
                    <View key={dish.id} style={[styles.dishRow, { borderLeftColor: dish.color }]}>
                      <Text style={styles.dishRowEmoji}>{dish.emoji}</Text>
                      <View style={styles.dishRowInfo}>
                        <Text style={styles.dishRowName}>{dish.name}</Text>
                        <Text style={styles.dishRowType}>{dish.type}</Text>
                      </View>
                      <Text style={styles.dishRowCal}>{dish.nutrition.calories} cal</Text>
                    </View>
                  ))}
                </View>
              </View>

              {/* Rating */}
              <View style={styles.ratingSection}>
                <Text style={styles.ratingSectionTitle}>How was it?</Text>
                <View style={styles.ratingStars}>
                  {[1, 2, 3, 4, 5].map(star => (
                    <TouchableOpacity key={star} onPress={() => setMealRating(star)}>
                      <Text style={[styles.ratingStar, mealRating >= star && styles.ratingStarActive]}>
                        ★
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Notes */}
              <View style={styles.notesSection}>
                <Text style={styles.notesSectionTitle}>Notes</Text>
                <TouchableOpacity
                  style={styles.notesInput}
                  onPress={() => {
                    Alert.prompt(
                      'Add Notes',
                      'How did it turn out?',
                      (text) => setMealNotes(text),
                      'plain-text',
                      mealNotes
                    );
                  }}
                >
                  <Text style={mealNotes ? styles.notesText : styles.notesPlaceholder}>
                    {mealNotes || 'Tap to add notes...'}
                  </Text>
                </TouchableOpacity>

                <Text style={styles.notesSectionTitle}>Changes for Next Time</Text>
                <TouchableOpacity
                  style={styles.notesInput}
                  onPress={() => {
                    Alert.prompt(
                      'Changes',
                      'What would you do differently?',
                      (text) => setMealChanges(text),
                      'plain-text',
                      mealChanges
                    );
                  }}
                >
                  <Text style={mealChanges ? styles.notesText : styles.notesPlaceholder}>
                    {mealChanges || 'Tap to add changes...'}
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Save Button */}
              <TouchableOpacity
                style={styles.saveMealButton}
                onPress={() => {
                  completeMeal();
                  setShowMealComplete(false);
                }}
              >
                <Text style={styles.saveMealButtonText}>Save Meal & Update Nutrition</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.skipButton}
                onPress={() => setShowMealComplete(false)}
              >
                <Text style={styles.skipButtonText}>Skip</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },

  // Meater Bar
  meaterBar: {
    backgroundColor: '#2d2d44',
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  meaterBarActive: {
    backgroundColor: '#3d2d2d',
    borderBottomWidth: 2,
    borderBottomColor: '#ff6b35',
  },
  meaterBarText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  meaterBarTime: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: '700',
  },
  meaterBarState: {
    color: '#ff6b35',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },

  // Timers Bar
  timersBar: {
    backgroundColor: '#252538',
    paddingVertical: 8,
    paddingHorizontal: 12,
    maxHeight: 60,
  },
  timerPill: {
    backgroundColor: '#3d3d54',
    borderRadius: 20,
    paddingVertical: 6,
    paddingHorizontal: 12,
    marginRight: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  timerPillDone: {
    backgroundColor: '#2d442d',
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  timerPillName: {
    color: '#fff',
    fontSize: 12,
    maxWidth: 80,
  },
  timerPillTime: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: '700',
  },
  timerPillClose: {
    padding: 2,
  },
  timerPillCloseText: {
    color: '#888',
    fontSize: 14,
  },

  // Card Deck
  deckContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    position: 'absolute',
    width: CARD_WIDTH,
    backgroundColor: '#2d2d44',
    borderRadius: 20,
    borderWidth: 3,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  cardEmoji: {
    fontSize: 40,
  },
  cardHeaderText: {
    flex: 1,
  },
  cardPhase: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
  },
  cardName: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
  },
  cardDuration: {
    backgroundColor: 'rgba(0,0,0,0.3)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  cardDurationText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },
  cardBody: {
    padding: 20,
    paddingTop: 0,
    minHeight: 200,
  },
  cardInstruction: {
    color: '#ddd',
    fontSize: 17,
    lineHeight: 26,
  },
  meaterInCard: {
    backgroundColor: '#3d2d2d',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ff6b35',
  },
  meaterInCardLabel: {
    color: '#ff6b35',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
  },
  meaterInCardTemp: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '700',
    marginTop: 4,
  },
  meaterInCardTime: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 4,
  },
  activeTimerInCard: {
    backgroundColor: '#2d3d2d',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  activeTimerLabel: {
    color: '#4CAF50',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
  },
  activeTimerTime: {
    color: '#fff',
    fontSize: 32,
    fontWeight: '700',
    marginTop: 4,
  },
  startTimerButton: {
    marginTop: 20,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  startTimerText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  meaterBadge: {
    marginTop: 16,
    alignItems: 'center',
  },
  meaterBadgeText: {
    color: '#ff6b35',
    fontSize: 14,
    fontWeight: '600',
  },
  meaterSetupSection: {
    marginTop: 20,
  },
  connectMeaterButton: {
    backgroundColor: '#ff6b35',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  connectMeaterText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  meaterConnected: {
    backgroundColor: '#2d442d',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  meaterConnectedText: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: '700',
  },
  meaterConnectedTemp: {
    color: '#fff',
    fontSize: 14,
    marginTop: 4,
  },
  cardFooter: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#3d3d54',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardProgress: {
    color: '#888',
    fontSize: 13,
  },
  progressDots: {
    flexDirection: 'row',
    gap: 6,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#3d3d54',
  },
  progressDotActive: {
    backgroundColor: '#fff',
    width: 20,
  },

  // Navigation Arrows
  navArrows: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  navArrow: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#3d3d54',
    justifyContent: 'center',
    alignItems: 'center',
  },
  navArrowDisabled: {
    opacity: 0.3,
  },
  navArrowText: {
    color: '#fff',
    fontSize: 32,
    fontWeight: '300',
    marginTop: -4,
  },

  // Quick Jump
  quickJump: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 12,
    paddingBottom: 24,
    gap: 8,
  },
  quickJumpButton: {
    backgroundColor: '#3d3d54',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
  },
  quickJumpText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  quickJumpDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#555',
    marginHorizontal: 8,
  },
  quickJumpSteak: {
    backgroundColor: DISH_COLORS.steak,
  },
  quickJumpPotato: {
    backgroundColor: DISH_COLORS.potatoes,
  },
  quickJumpBrussels: {
    backgroundColor: DISH_COLORS.brussels,
  },
  quickJumpLog: {
    backgroundColor: '#4CAF50',
  },
  quickJumpLogged: {
    backgroundColor: '#2d442d',
    borderWidth: 1,
    borderColor: '#4CAF50',
  },

  // Pantry Indicator
  pantryIndicator: {
    backgroundColor: '#252538',
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  pantryIndicatorText: {
    color: '#888',
    fontSize: 12,
  },

  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
    paddingBottom: 30,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#3d3d54',
  },
  modalTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  modalClose: {
    color: '#888',
    fontSize: 24,
    padding: 4,
  },
  modalSubtitle: {
    color: '#888',
    fontSize: 14,
    paddingHorizontal: 20,
    paddingTop: 12,
  },
  selectAllButton: {
    marginHorizontal: 20,
    marginVertical: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: '#3d3d54',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  selectAllText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  ingredientList: {
    maxHeight: 300,
  },
  ingredientItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2d2d44',
  },
  ingredientItemSelected: {
    backgroundColor: '#2d442d',
  },
  ingredientCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#4CAF50',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  ingredientCheckmark: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: '700',
  },
  ingredientInfo: {
    flex: 1,
  },
  ingredientName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  ingredientBrand: {
    color: '#888',
    fontSize: 13,
    marginTop: 2,
  },
  ingredientToday: {
    color: '#4CAF50',
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  ingredientWeight: {
    color: '#888',
    fontSize: 14,
    marginLeft: 12,
  },
  modalFooter: {
    paddingHorizontal: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#3d3d54',
  },
  logMealButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  logMealButtonDisabled: {
    backgroundColor: '#3d3d54',
    opacity: 0.6,
  },
  logMealButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },

  // Nutrition Progress Bar
  nutritionBar: {
    flexDirection: 'row',
    backgroundColor: '#252538',
    paddingVertical: 8,
    paddingHorizontal: 16,
    gap: 16,
  },
  nutritionItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  nutritionLabel: {
    color: '#888',
    fontSize: 11,
    fontWeight: '600',
    width: 20,
  },
  nutritionProgress: {
    flex: 1,
    height: 4,
    backgroundColor: '#3d3d54',
    borderRadius: 2,
    overflow: 'hidden',
  },
  nutritionFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 2,
  },
  proteinFill: {
    backgroundColor: '#2196F3',
  },
  nutritionValue: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
    minWidth: 35,
    textAlign: 'right',
  },

  // Ingredient Requirements
  ingredientRequirements: {
    backgroundColor: '#2d2d44',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  ingredientReqTitle: {
    color: '#888',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 6,
  },
  ingredientReqChip: {
    backgroundColor: '#3d3d54',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginRight: 8,
    alignItems: 'center',
  },
  ingredientOptional: {
    backgroundColor: '#2d2d2d',
    borderWidth: 1,
    borderColor: '#3d3d54',
    borderStyle: 'dashed',
  },
  ingredientReqText: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: '700',
  },
  ingredientReqName: {
    color: '#fff',
    fontSize: 11,
  },
  ingredientOptionalLabel: {
    color: '#666',
    fontSize: 9,
  },
  usePantryButton: {
    marginTop: 8,
    paddingVertical: 6,
    alignItems: 'center',
  },
  usePantryText: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: '600',
  },

  // Pantry Tray
  pantryTray: {
    backgroundColor: '#1a1a2e',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#4CAF50',
  },
  pantryCard: {
    backgroundColor: '#2d2d44',
    width: 80,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 12,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  pantryCardEmoji: {
    fontSize: 24,
  },
  pantryCardName: {
    color: '#fff',
    fontSize: 10,
    textAlign: 'center',
    marginTop: 4,
  },
  pantryCardWeight: {
    color: '#4CAF50',
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
  },

  // Fusion Animation
  fusionOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  fusionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fusionCard: {
    width: 100,
    height: 120,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: -15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 8,
    elevation: 8,
  },
  fusionEmoji: {
    fontSize: 36,
  },
  fusionDishName: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 4,
  },
  fusionText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: 4,
    marginTop: 40,
    textShadowColor: '#4CAF50',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10,
  },

  // Meal Complete Modal
  mealCompleteScroll: {
    flex: 1,
    paddingTop: 60,
  },
  mealCompleteContent: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 40,
    paddingTop: 20,
  },
  mealCard: {
    backgroundColor: '#2d2d44',
    marginHorizontal: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  mealCardHeader: {
    padding: 20,
    alignItems: 'center',
    backgroundColor: '#3d3d54',
  },
  mealCardEmojis: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  mealCardEmoji: {
    fontSize: 32,
    marginHorizontal: 4,
  },
  mealCardTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  mealCardSubtitle: {
    color: '#aaa',
    fontSize: 13,
    textAlign: 'center',
    marginTop: 4,
  },
  mealNutrition: {
    flexDirection: 'row',
    padding: 16,
    justifyContent: 'space-around',
    borderBottomWidth: 1,
    borderBottomColor: '#3d3d54',
  },
  nutritionBox: {
    alignItems: 'center',
  },
  nutritionBoxValue: {
    color: '#4CAF50',
    fontSize: 20,
    fontWeight: '700',
  },
  nutritionBoxLabel: {
    color: '#888',
    fontSize: 11,
    marginTop: 2,
  },
  dishBreakdown: {
    padding: 12,
  },
  dishRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingLeft: 12,
    borderLeftWidth: 3,
    marginBottom: 8,
    backgroundColor: '#252538',
    borderRadius: 8,
  },
  dishRowEmoji: {
    fontSize: 20,
    marginRight: 10,
  },
  dishRowInfo: {
    flex: 1,
  },
  dishRowName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  dishRowType: {
    color: '#888',
    fontSize: 11,
    textTransform: 'capitalize',
  },
  dishRowCal: {
    color: '#4CAF50',
    fontSize: 13,
    fontWeight: '600',
    marginRight: 12,
  },

  // Rating Section
  ratingSection: {
    alignItems: 'center',
    paddingVertical: 20,
    marginTop: 16,
  },
  ratingSectionTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  ratingStars: {
    flexDirection: 'row',
    gap: 8,
  },
  ratingStar: {
    fontSize: 36,
    color: '#3d3d54',
  },
  ratingStarActive: {
    color: '#FFD700',
  },

  // Notes Section
  notesSection: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  notesSectionTitle: {
    color: '#888',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    marginTop: 12,
  },
  notesInput: {
    backgroundColor: '#2d2d44',
    borderRadius: 12,
    padding: 14,
    minHeight: 60,
  },
  notesText: {
    color: '#fff',
    fontSize: 14,
  },
  notesPlaceholder: {
    color: '#666',
    fontSize: 14,
  },

  // Save/Skip Buttons
  saveMealButton: {
    backgroundColor: '#4CAF50',
    marginHorizontal: 16,
    marginTop: 20,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveMealButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  skipButton: {
    marginHorizontal: 16,
    marginTop: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  skipButtonText: {
    color: '#888',
    fontSize: 14,
  },
});
