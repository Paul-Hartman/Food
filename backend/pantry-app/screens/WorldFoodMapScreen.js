import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { API_BASE_URL } from '../config';

const REGION_COLORS = {
  'East Asia': '#E53935',
  'South Asia': '#FF9800',
  'Southeast Asia': '#FF5722',
  'Middle East': '#8D6E63',
  'Sub-Saharan Africa': '#4CAF50',
  'North Africa': '#66BB6A',
  'Western Europe': '#1E88E5',
  'Eastern Europe': '#5C6BC0',
  'Northern Europe': '#42A5F5',
  'Southern Europe': '#29B6F6',
  'North America': '#AB47BC',
  'South America': '#7E57C2',
  'Central America': '#9C27B0',
  'Caribbean': '#CE93D8',
  'Oceania': '#00897B',
};

const MEAL_ICONS = {
  breakfast: '\u2600\uFE0F',
  lunch: '\uD83C\uDF1E',
  dinner: '\uD83C\uDF19',
  snack: '\uD83C\uDF7F',
};

const INGREDIENT_ICONS = {
  rice: '\uD83C\uDF5A',
  wheat_flour: '\uD83C\uDF5E',
  meat: '\uD83E\uDD69',
  fish_seafood: '\uD83D\uDC1F',
  dairy: '\uD83E\uDD5B',
  egg: '\uD83E\uDD5A',
  vegetables: '\uD83E\uDD66',
  legumes: '\uD83E\uDED8',
  coconut: '\uD83E\uDD65',
  spices: '\uD83C\uDF36\uFE0F',
  noodles_pasta: '\uD83C\uDF5C',
  fruit: '\uD83C\uDF4E',
  sugar_sweets: '\uD83C\uDF6C',
  other: '\uD83C\uDF7D\uFE0F',
};

// === OVERVIEW SCREEN ===
function MapOverview({ regions, onSelectCulture, onRefresh, refreshing }) {
  const regionEntries = Object.entries(regions).sort(
    (a, b) => b[1].cultures.length - a[1].cultures.length
  );

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <Text style={styles.title}>World Food Map</Text>
      <Text style={styles.subtitle}>
        {regionEntries.reduce((sum, [, r]) => sum + r.cultures.length, 0)} cultures across{' '}
        {regionEntries.length} regions
      </Text>

      {regionEntries.map(([regionName, regionData]) => (
        <View key={regionName} style={styles.regionSection}>
          <View style={[styles.regionHeader, { backgroundColor: REGION_COLORS[regionName] || '#607D8B' }]}>
            <Text style={styles.regionName}>{regionName}</Text>
            <Text style={styles.regionCount}>{regionData.cultures.length} cultures</Text>
          </View>
          <View style={styles.cultureGrid}>
            {regionData.cultures.map((culture) => (
              <TouchableOpacity
                key={culture.slug}
                style={styles.cultureCard}
                onPress={() => onSelectCulture(culture)}
              >
                <Text style={styles.cultureName} numberOfLines={1}>{culture.name}</Text>
                <Text style={styles.cultureStats}>
                  {culture.food_count} foods
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ))}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// === CULTURE DETAIL SCREEN ===
function CultureDetail({ culture, data, onSelectMeal, onBack }) {
  const mealOrder = ['breakfast', 'lunch', 'dinner', 'snack'];
  const meals = mealOrder.filter((m) => data.meal_patterns[m]);

  return (
    <ScrollView style={styles.container}>
      <TouchableOpacity style={styles.backButton} onPress={onBack}>
        <Text style={styles.backText}>{'\u2190'} Back to Map</Text>
      </TouchableOpacity>

      <Text style={styles.title}>{data.name}</Text>
      <Text style={styles.subtitle}>{data.region}</Text>

      {meals.map((mealKey) => {
        const meal = data.meal_patterns[mealKey];
        const foodCount = Object.values(meal.by_ingredient || {}).reduce(
          (sum, arr) => sum + arr.length, 0
        );

        return (
          <TouchableOpacity
            key={mealKey}
            style={styles.mealCard}
            onPress={() => onSelectMeal(mealKey)}
          >
            <View style={styles.mealHeader}>
              <Text style={styles.mealIcon}>{MEAL_ICONS[mealKey]}</Text>
              <View style={styles.mealInfo}>
                <Text style={styles.mealTitle}>{meal.local_name}</Text>
                <Text style={styles.mealTime}>{meal.typical_time}</Text>
              </View>
              <Text style={styles.mealFoodCount}>{foodCount}</Text>
            </View>
            <Text style={styles.mealDesc} numberOfLines={2}>{meal.description}</Text>
            <Text style={styles.mealFoods} numberOfLines={1}>{meal.typical_foods}</Text>
            {meal.social_context ? (
              <Text style={styles.mealContext} numberOfLines={2}>{meal.social_context}</Text>
            ) : null}

            {/* Ingredient chips */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.ingredientChips}>
              {Object.entries(meal.by_ingredient || {}).map(([cat, foods]) => (
                <View key={cat} style={styles.ingredientChip}>
                  <Text style={styles.chipText}>
                    {INGREDIENT_ICONS[cat] || '\uD83C\uDF7D\uFE0F'} {cat.replace('_', '/')} ({foods.length})
                  </Text>
                </View>
              ))}
            </ScrollView>
          </TouchableOpacity>
        );
      })}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// === MEAL DETAIL SCREEN ===
function MealDetail({ culture, mealType, data, onBack }) {
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const categories = Object.entries(data.by_ingredient || {}).sort(
    (a, b) => b[1].length - a[1].length
  );

  const filtered = selectedIngredient
    ? categories.filter(([cat]) => cat === selectedIngredient)
    : categories;

  return (
    <ScrollView style={styles.container}>
      <TouchableOpacity style={styles.backButton} onPress={onBack}>
        <Text style={styles.backText}>{'\u2190'} Back to {culture.name}</Text>
      </TouchableOpacity>

      <Text style={styles.title}>
        {MEAL_ICONS[mealType]} {mealType.charAt(0).toUpperCase() + mealType.slice(1)}
      </Text>
      <Text style={styles.subtitle}>{culture.name} — {data.total_foods} foods</Text>

      {data.pattern && (
        <View style={styles.patternBox}>
          <Text style={styles.patternName}>{data.pattern.meal_name}</Text>
          <Text style={styles.patternTime}>{data.pattern.typical_time}</Text>
          <Text style={styles.patternDesc}>{data.pattern.description}</Text>
          {data.pattern.social_context ? (
            <Text style={styles.patternContext}>{data.pattern.social_context}</Text>
          ) : null}
        </View>
      )}

      {/* Ingredient filter chips */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow}>
        <TouchableOpacity
          style={[styles.filterChip, !selectedIngredient && styles.filterChipActive]}
          onPress={() => setSelectedIngredient(null)}
        >
          <Text style={[styles.filterChipText, !selectedIngredient && styles.filterChipTextActive]}>
            All ({data.total_foods})
          </Text>
        </TouchableOpacity>
        {categories.map(([cat, foods]) => (
          <TouchableOpacity
            key={cat}
            style={[styles.filterChip, selectedIngredient === cat && styles.filterChipActive]}
            onPress={() => setSelectedIngredient(selectedIngredient === cat ? null : cat)}
          >
            <Text style={[styles.filterChipText, selectedIngredient === cat && styles.filterChipTextActive]}>
              {INGREDIENT_ICONS[cat] || '\uD83C\uDF7D\uFE0F'} {cat.replace('_', '/')} ({foods.length})
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Food grid by category */}
      {filtered.map(([cat, foods]) => (
        <View key={cat} style={styles.categorySection}>
          <Text style={styles.categoryTitle}>
            {INGREDIENT_ICONS[cat] || '\uD83C\uDF7D\uFE0F'} {cat.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
          </Text>
          <View style={styles.foodGrid}>
            {foods.map((food) => (
              <View key={food.id} style={styles.foodItem}>
                {food.image_url ? (
                  <Image source={{ uri: food.image_url }} style={styles.foodImage} />
                ) : (
                  <View style={[styles.foodImage, styles.foodImagePlaceholder]}>
                    <Text style={styles.placeholderText}>{food.name.charAt(0)}</Text>
                  </View>
                )}
                <Text style={styles.foodName} numberOfLines={2}>{food.name}</Text>
              </View>
            ))}
          </View>
        </View>
      ))}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// === MAIN SCREEN ===
export default function WorldFoodMapScreen({ navigation }) {
  const [view, setView] = useState('overview'); // overview | culture | meal
  const [regions, setRegions] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCulture, setSelectedCulture] = useState(null);
  const [cultureData, setCultureData] = useState(null);
  const [selectedMeal, setSelectedMeal] = useState(null);
  const [mealData, setMealData] = useState(null);

  const fetchOverview = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/food-map`);
      const data = await res.json();
      setRegions(data.regions || {});
    } catch (err) {
      console.error('Failed to load food map:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  const handleSelectCulture = async (culture) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/food-map/${culture.slug}`);
      const data = await res.json();
      setSelectedCulture(culture);
      setCultureData(data);
      setView('culture');
    } catch (err) {
      console.error('Failed to load culture:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMeal = async (mealType) => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/food-map/${selectedCulture.slug}/${mealType}`
      );
      const data = await res.json();
      setSelectedMeal(mealType);
      setMealData(data);
      setView('meal');
    } catch (err) {
      console.error('Failed to load meal:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && view === 'overview') {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading World Food Map...</Text>
      </View>
    );
  }

  if (view === 'meal' && mealData) {
    return (
      <MealDetail
        culture={selectedCulture}
        mealType={selectedMeal}
        data={mealData}
        onBack={() => setView('culture')}
      />
    );
  }

  if (view === 'culture' && cultureData) {
    return (
      <CultureDetail
        culture={selectedCulture}
        data={cultureData}
        onSelectMeal={handleSelectMeal}
        onBack={() => setView('overview')}
      />
    );
  }

  return (
    <MapOverview
      regions={regions}
      onSelectCulture={handleSelectCulture}
      onRefresh={() => {
        setRefreshing(true);
        fetchOverview();
      }}
      refreshing={refreshing}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a2e',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  subtitle: {
    fontSize: 14,
    color: '#888',
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  // Region
  regionSection: {
    marginHorizontal: 12,
    marginBottom: 16,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#fff',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  regionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  regionName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  regionCount: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.8)',
  },
  cultureGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
  },
  cultureCard: {
    width: '48%',
    margin: '1%',
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  cultureName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
  },
  cultureStats: {
    fontSize: 12,
    color: '#888',
    marginTop: 4,
  },
  // Back button
  backButton: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backText: {
    fontSize: 16,
    color: '#1E88E5',
    fontWeight: '600',
  },
  // Meal card
  mealCard: {
    marginHorizontal: 12,
    marginBottom: 12,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  mealHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  mealIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  mealInfo: {
    flex: 1,
  },
  mealTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  mealTime: {
    fontSize: 13,
    color: '#888',
  },
  mealFoodCount: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  mealDesc: {
    fontSize: 14,
    color: '#555',
    marginBottom: 4,
  },
  mealFoods: {
    fontSize: 13,
    color: '#888',
    fontStyle: 'italic',
    marginBottom: 4,
  },
  mealContext: {
    fontSize: 12,
    color: '#aaa',
    marginBottom: 8,
  },
  ingredientChips: {
    flexDirection: 'row',
    marginTop: 4,
  },
  ingredientChip: {
    backgroundColor: '#e8f5e9',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 6,
  },
  chipText: {
    fontSize: 12,
    color: '#2E7D32',
  },
  // Filters
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    marginBottom: 16,
  },
  filterChip: {
    backgroundColor: '#fff',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  filterChipActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  filterChipText: {
    fontSize: 13,
    color: '#555',
  },
  filterChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  // Pattern box
  patternBox: {
    marginHorizontal: 12,
    marginBottom: 16,
    backgroundColor: '#fff3e0',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  patternName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#E65100',
    marginBottom: 4,
  },
  patternTime: {
    fontSize: 14,
    color: '#F57C00',
    marginBottom: 8,
  },
  patternDesc: {
    fontSize: 14,
    color: '#555',
    marginBottom: 4,
  },
  patternContext: {
    fontSize: 13,
    color: '#888',
    fontStyle: 'italic',
  },
  // Category sections
  categorySection: {
    marginHorizontal: 12,
    marginBottom: 16,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  foodGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  foodItem: {
    width: '31%',
    margin: '1%',
    backgroundColor: '#fff',
    borderRadius: 8,
    overflow: 'hidden',
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  foodImage: {
    width: '100%',
    height: 80,
    backgroundColor: '#e0e0e0',
  },
  foodImagePlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 24,
    color: '#bbb',
    fontWeight: 'bold',
  },
  foodName: {
    fontSize: 12,
    color: '#333',
    padding: 6,
    textAlign: 'center',
  },
});
