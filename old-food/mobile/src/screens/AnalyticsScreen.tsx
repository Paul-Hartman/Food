import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api } from '../services/api';

interface Analytics {
  nutrition_summary: {
    avg_calories: number;
    avg_protein: number;
    avg_carbs: number;
    avg_fat: number;
    days_tracked: number;
  };
  favorite_recipes: Array<{
    id: number;
    name: string;
    times_cooked: number;
    avg_rating: number;
  }>;
  cooking_frequency: {
    total_meals: number;
    this_week: number;
    this_month: number;
  };
  insights: string[];
}

export default function AnalyticsScreen() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  async function loadAnalytics() {
    setLoading(true);
    try {
      const data = await api.getPersonalAnalytics();
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      Alert.alert('Error', 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading analytics...</Text>
      </View>
    );
  }

  if (!analytics) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>No data available yet</Text>
        <Text style={styles.emptySubtext}>Cook and track meals to see your analytics</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      {/* Nutrition Summary */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📊 Nutrition Summary</Text>
        <Text style={styles.cardSubtitle}>Average per day ({analytics.nutrition_summary.days_tracked} days)</Text>

        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{Math.round(analytics.nutrition_summary.avg_calories)}</Text>
            <Text style={styles.statLabel}>Calories</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{Math.round(analytics.nutrition_summary.avg_protein)}g</Text>
            <Text style={styles.statLabel}>Protein</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{Math.round(analytics.nutrition_summary.avg_carbs)}g</Text>
            <Text style={styles.statLabel}>Carbs</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{Math.round(analytics.nutrition_summary.avg_fat)}g</Text>
            <Text style={styles.statLabel}>Fat</Text>
          </View>
        </View>
      </View>

      {/* Cooking Frequency */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>🍳 Cooking Activity</Text>
        <View style={styles.frequencyRow}>
          <View style={styles.frequencyItem}>
            <Text style={styles.frequencyValue}>{analytics.cooking_frequency.this_week}</Text>
            <Text style={styles.frequencyLabel}>This Week</Text>
          </View>
          <View style={styles.frequencyItem}>
            <Text style={styles.frequencyValue}>{analytics.cooking_frequency.this_month}</Text>
            <Text style={styles.frequencyLabel}>This Month</Text>
          </View>
          <View style={styles.frequencyItem}>
            <Text style={styles.frequencyValue}>{analytics.cooking_frequency.total_meals}</Text>
            <Text style={styles.frequencyLabel}>All Time</Text>
          </View>
        </View>
      </View>

      {/* Favorite Recipes */}
      {analytics.favorite_recipes.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>❤️ Top Recipes</Text>
          {analytics.favorite_recipes.map((recipe, idx) => (
            <View key={recipe.id} style={styles.recipeRow}>
              <Text style={styles.recipeRank}>#{idx + 1}</Text>
              <View style={styles.recipeInfo}>
                <Text style={styles.recipeName}>{recipe.name}</Text>
                <Text style={styles.recipeMeta}>
                  Cooked {recipe.times_cooked}x • {recipe.avg_rating.toFixed(1)} ⭐
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Insights */}
      {analytics.insights.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>💡 Insights</Text>
          {analytics.insights.map((insight, idx) => (
            <View key={idx} style={styles.insightRow}>
              <Text style={styles.insightIcon}>💡</Text>
              <Text style={styles.insightText}>{insight}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  scrollContent: {
    padding: 16,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#4CAF50',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  frequencyRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  frequencyItem: {
    alignItems: 'center',
  },
  frequencyValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#4CAF50',
    marginBottom: 4,
  },
  frequencyLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  recipeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  recipeRank: {
    fontSize: 18,
    fontWeight: '700',
    color: '#4CAF50',
    width: 40,
  },
  recipeInfo: {
    flex: 1,
  },
  recipeName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 2,
  },
  recipeMeta: {
    fontSize: 12,
    color: '#6b7280',
  },
  insightRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  insightIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
    marginTop: 60,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 8,
  },
});
