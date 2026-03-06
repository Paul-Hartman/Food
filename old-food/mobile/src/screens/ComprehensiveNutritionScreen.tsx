import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';

interface NutrientProgress {
  current: number;
  goal: number;
  unit: string;
  percentage: number;
}

interface ComprehensiveNutritionData {
  date: string;
  goals: Record<string, number>;
  consumed: Record<string, number>;
}

interface ProgressBarProps {
  nutrient: string;
  current: number;
  goal: number;
  unit: string;
  color: string;
  warn?: 'high' | 'low';
}

function ProgressBar({ nutrient, current, goal, unit, color, warn }: ProgressBarProps) {
  const percentage = Math.min((current / goal) * 100, 100);
  const isLow = warn === 'low' && percentage < 50;
  const isHigh = warn === 'high' && percentage > 100;

  return (
    <View style={styles.progressItem}>
      <View style={styles.progressHeader}>
        <Text style={styles.progressLabel}>{nutrient}</Text>
        <Text style={[styles.progressValues, isLow && styles.lowWarning, isHigh && styles.highWarning]}>
          {Math.round(current)}
          {unit} / {goal}
          {unit}
        </Text>
      </View>
      <View style={styles.progressBar}>
        <View
          style={[
            styles.progressFill,
            { width: `${percentage}%`, backgroundColor: isLow ? '#FF9800' : isHigh ? '#F44336' : color },
          ]}
        />
      </View>
    </View>
  );
}

export default function ComprehensiveNutritionScreen() {
  const [data, setData] = useState<ComprehensiveNutritionData | null>(null);
  const [loading, setLoading] = useState(true);

  // Collapsible sections
  const [macrosExpanded, setMacrosExpanded] = useState(true);
  const [waterExpanded, setWaterExpanded] = useState(true);
  const [vitaminsExpanded, setVitaminsExpanded] = useState(false);
  const [mineralsExpanded, setMineralsExpanded] = useState(false);
  const [otherExpanded, setOtherExpanded] = useState(false);

  useFocusEffect(
    useCallback(() => {
      loadNutrition();
    }, [])
  );

  const loadNutrition = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://192.168.2.38:5025/api/nutrition/comprehensive/today');
      const json = await response.json();
      setData(json);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const logWater = async (ml: number) => {
    try {
      await fetch('http://192.168.2.38:5025/api/nutrition/comprehensive/log-water', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ml }),
      });
      loadNutrition();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  if (!data) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Failed to load nutrition data</Text>
      </View>
    );
  }

  const { goals, consumed } = data;

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Macronutrients */}
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => setMacrosExpanded(!macrosExpanded)}
        >
          <Text style={styles.sectionTitle}>
            {macrosExpanded ? '▼' : '▶'} Macronutrients
          </Text>
        </TouchableOpacity>
        {macrosExpanded && (
          <View style={styles.sectionContent}>
            <ProgressBar
              nutrient="Calories"
              current={consumed.calories || 0}
              goal={goals.calories || 2000}
              unit=""
              color="#FF9800"
            />
            <ProgressBar
              nutrient="Protein"
              current={consumed.protein_g || 0}
              goal={goals.protein_g || 50}
              unit="g"
              color="#4CAF50"
            />
            <ProgressBar
              nutrient="Carbohydrates"
              current={consumed.carbs_g || 0}
              goal={goals.carbs_g || 275}
              unit="g"
              color="#2196F3"
            />
            <ProgressBar
              nutrient="Total Fat"
              current={consumed.fat_g || 0}
              goal={goals.fat_g || 78}
              unit="g"
              color="#9C27B0"
            />
            <ProgressBar
              nutrient="Saturated Fat"
              current={consumed.saturated_fat_g || 0}
              goal={goals.saturated_fat_g || 20}
              unit="g"
              color="#E91E63"
              warn="high"
            />
            <ProgressBar
              nutrient="Fiber"
              current={consumed.fiber_g || 0}
              goal={goals.fiber_g || 28}
              unit="g"
              color="#8BC34A"
              warn="low"
            />
            <ProgressBar
              nutrient="Sugar"
              current={consumed.sugar_g || 0}
              goal={goals.sugar_g || 50}
              unit="g"
              color="#FF5722"
              warn="high"
            />
          </View>
        )}

        {/* Water */}
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => setWaterExpanded(!waterExpanded)}
        >
          <Text style={styles.sectionTitle}>{waterExpanded ? '▼' : '▶'} Hydration 💧</Text>
        </TouchableOpacity>
        {waterExpanded && (
          <View style={styles.sectionContent}>
            <ProgressBar
              nutrient="Water"
              current={consumed.water_ml || 0}
              goal={goals.water_ml || 2000}
              unit="ml"
              color="#03A9F4"
              warn="low"
            />
            <View style={styles.waterButtons}>
              <TouchableOpacity style={styles.waterButton} onPress={() => logWater(250)}>
                <Text style={styles.waterButtonText}>+250ml</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.waterButton} onPress={() => logWater(500)}>
                <Text style={styles.waterButtonText}>+500ml</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.waterButton} onPress={() => logWater(1000)}>
                <Text style={styles.waterButtonText}>+1L</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Vitamins */}
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => setVitaminsExpanded(!vitaminsExpanded)}
        >
          <Text style={styles.sectionTitle}>{vitaminsExpanded ? '▼' : '▶'} Vitamins (13)</Text>
        </TouchableOpacity>
        {vitaminsExpanded && (
          <View style={styles.sectionContent}>
            <Text style={styles.subsectionTitle}>Fat-Soluble Vitamins</Text>
            <ProgressBar
              nutrient="Vitamin A"
              current={consumed.vitamin_a_mcg || 0}
              goal={goals.vitamin_a_mcg || 900}
              unit="mcg"
              color="#FF9800"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin D"
              current={consumed.vitamin_d_mcg || 0}
              goal={goals.vitamin_d_mcg || 20}
              unit="mcg"
              color="#FFC107"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin E"
              current={consumed.vitamin_e_mg || 0}
              goal={goals.vitamin_e_mg || 15}
              unit="mg"
              color="#4CAF50"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin K"
              current={consumed.vitamin_k_mcg || 0}
              goal={goals.vitamin_k_mcg || 120}
              unit="mcg"
              color="#8BC34A"
              warn="low"
            />

            <Text style={[styles.subsectionTitle, { marginTop: 16 }]}>B Complex Vitamins</Text>
            <ProgressBar
              nutrient="Vitamin B1 (Thiamin)"
              current={consumed.vitamin_b1_mg || 0}
              goal={goals.vitamin_b1_mg || 1.2}
              unit="mg"
              color="#9C27B0"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin B2 (Riboflavin)"
              current={consumed.vitamin_b2_mg || 0}
              goal={goals.vitamin_b2_mg || 1.3}
              unit="mg"
              color="#673AB7"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin B3 (Niacin)"
              current={consumed.vitamin_b3_mg || 0}
              goal={goals.vitamin_b3_mg || 16}
              unit="mg"
              color="#3F51B5"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin B5 (Pantothenic Acid)"
              current={consumed.vitamin_b5_mg || 0}
              goal={goals.vitamin_b5_mg || 5}
              unit="mg"
              color="#2196F3"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin B6 (Pyridoxine)"
              current={consumed.vitamin_b6_mg || 0}
              goal={goals.vitamin_b6_mg || 1.7}
              unit="mg"
              color="#03A9F4"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin B7 (Biotin)"
              current={consumed.vitamin_b7_mcg || 0}
              goal={goals.vitamin_b7_mcg || 30}
              unit="mcg"
              color="#00BCD4"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin B9 (Folate)"
              current={consumed.vitamin_b9_mcg || 0}
              goal={goals.vitamin_b9_mcg || 400}
              unit="mcg"
              color="#009688"
              warn="low"
            />
            <ProgressBar
              nutrient="Vitamin B12 (Cobalamin)"
              current={consumed.vitamin_b12_mcg || 0}
              goal={goals.vitamin_b12_mcg || 2.4}
              unit="mcg"
              color="#4CAF50"
              warn="low"
            />

            <Text style={[styles.subsectionTitle, { marginTop: 16 }]}>Water-Soluble Vitamins</Text>
            <ProgressBar
              nutrient="Vitamin C (Ascorbic Acid)"
              current={consumed.vitamin_c_mg || 0}
              goal={goals.vitamin_c_mg || 90}
              unit="mg"
              color="#FF9800"
              warn="low"
            />
          </View>
        )}

        {/* Minerals */}
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => setMineralsExpanded(!mineralsExpanded)}
        >
          <Text style={styles.sectionTitle}>{mineralsExpanded ? '▼' : '▶'} Minerals (14)</Text>
        </TouchableOpacity>
        {mineralsExpanded && (
          <View style={styles.sectionContent}>
            <Text style={styles.subsectionTitle}>Major Minerals</Text>
            <ProgressBar
              nutrient="Calcium"
              current={consumed.calcium_mg || 0}
              goal={goals.calcium_mg || 1000}
              unit="mg"
              color="#00BCD4"
              warn="low"
            />
            <ProgressBar
              nutrient="Phosphorus"
              current={consumed.phosphorus_mg || 0}
              goal={goals.phosphorus_mg || 700}
              unit="mg"
              color="#9C27B0"
              warn="low"
            />
            <ProgressBar
              nutrient="Magnesium"
              current={consumed.magnesium_mg || 0}
              goal={goals.magnesium_mg || 420}
              unit="mg"
              color="#4CAF50"
              warn="low"
            />
            <ProgressBar
              nutrient="Sodium"
              current={consumed.sodium_mg || 0}
              goal={goals.sodium_mg || 2300}
              unit="mg"
              color="#FF5722"
              warn="high"
            />
            <ProgressBar
              nutrient="Potassium"
              current={consumed.potassium_mg || 0}
              goal={goals.potassium_mg || 3400}
              unit="mg"
              color="#FF9800"
              warn="low"
            />
            <ProgressBar
              nutrient="Chloride"
              current={consumed.chloride_mg || 0}
              goal={goals.chloride_mg || 2300}
              unit="mg"
              color="#607D8B"
            />

            <Text style={[styles.subsectionTitle, { marginTop: 16 }]}>Trace Minerals</Text>
            <ProgressBar
              nutrient="Iron"
              current={consumed.iron_mg || 0}
              goal={goals.iron_mg || 18}
              unit="mg"
              color="#795548"
              warn="low"
            />
            <ProgressBar
              nutrient="Zinc"
              current={consumed.zinc_mg || 0}
              goal={goals.zinc_mg || 11}
              unit="mg"
              color="#9E9E9E"
              warn="low"
            />
            <ProgressBar
              nutrient="Copper"
              current={consumed.copper_mg || 0}
              goal={goals.copper_mg || 0.9}
              unit="mg"
              color="#FF9800"
              warn="low"
            />
            <ProgressBar
              nutrient="Manganese"
              current={consumed.manganese_mg || 0}
              goal={goals.manganese_mg || 2.3}
              unit="mg"
              color="#8D6E63"
              warn="low"
            />
            <ProgressBar
              nutrient="Selenium"
              current={consumed.selenium_mcg || 0}
              goal={goals.selenium_mcg || 55}
              unit="mcg"
              color="#607D8B"
              warn="low"
            />
            <ProgressBar
              nutrient="Iodine"
              current={consumed.iodine_mcg || 0}
              goal={goals.iodine_mcg || 150}
              unit="mcg"
              color="#9C27B0"
              warn="low"
            />
            <ProgressBar
              nutrient="Chromium"
              current={consumed.chromium_mcg || 0}
              goal={goals.chromium_mcg || 35}
              unit="mcg"
              color="#78909C"
              warn="low"
            />
            <ProgressBar
              nutrient="Molybdenum"
              current={consumed.molybdenum_mcg || 0}
              goal={goals.molybdenum_mcg || 45}
              unit="mcg"
              color="#455A64"
              warn="low"
            />
          </View>
        )}

        {/* Other Nutrients */}
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => setOtherExpanded(!otherExpanded)}
        >
          <Text style={styles.sectionTitle}>{otherExpanded ? '▼' : '▶'} Other Nutrients</Text>
        </TouchableOpacity>
        {otherExpanded && (
          <View style={styles.sectionContent}>
            <ProgressBar
              nutrient="Omega-3 Fatty Acids"
              current={consumed.omega3_g || 0}
              goal={goals.omega3_g || 1.6}
              unit="g"
              color="#03A9F4"
              warn="low"
            />
            <ProgressBar
              nutrient="Cholesterol"
              current={consumed.cholesterol_mg || 0}
              goal={goals.cholesterol_mg || 300}
              unit="mg"
              color="#F44336"
              warn="high"
            />
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
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
  errorText: {
    fontSize: 16,
    color: '#666',
  },
  sectionHeader: {
    backgroundColor: '#fff',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  sectionContent: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 1,
  },
  subsectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 12,
    textTransform: 'uppercase',
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
  lowWarning: {
    color: '#FF9800',
  },
  highWarning: {
    color: '#F44336',
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
  waterButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  waterButton: {
    flex: 1,
    backgroundColor: '#03A9F4',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  waterButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
});
