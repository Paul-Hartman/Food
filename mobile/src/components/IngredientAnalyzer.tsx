import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { analyzeProductIngredients, type IngredientAnalysis } from '../services/apothecary-database';

interface IngredientAnalyzerProps {
  ingredientsList: string; // Comma-separated ingredient list from product
  onIngredientPress?: (ingredientName: string) => void;
}

/**
 * Ingredient Analyzer Component
 *
 * Breaks down a product's ingredients into:
 * - Natural vs Synthetic
 * - What each ingredient does
 * - Historical context
 * - Safety information
 *
 * "Understanding what you eat transforms fear into knowledge."
 */
export default function IngredientAnalyzer({
  ingredientsList,
  onIngredientPress,
}: IngredientAnalyzerProps) {
  if (!ingredientsList) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>No ingredients listed</Text>
      </View>
    );
  }

  const analysis = analyzeProductIngredients(ingredientsList);

  const naturalPercentage =
    analysis.totalIngredients > 0
      ? Math.round((analysis.natural / analysis.totalIngredients) * 100)
      : 0;

  const syntheticPercentage =
    analysis.totalIngredients > 0
      ? Math.round((analysis.synthetic / analysis.totalIngredients) * 100)
      : 0;

  return (
    <ScrollView style={styles.container}>
      {/* Summary Card */}
      <View style={styles.summary}>
        <Text style={styles.summaryTitle}>Ingredient Analysis</Text>

        <View style={styles.summaryStats}>
          <View style={styles.stat}>
            <Text style={styles.statNumber}>{analysis.totalIngredients}</Text>
            <Text style={styles.statLabel}>Total</Text>
          </View>

          <View style={styles.stat}>
            <Text style={[styles.statNumber, { color: '#4CAF50' }]}>{analysis.natural}</Text>
            <Text style={styles.statLabel}>Natural</Text>
          </View>

          <View style={styles.stat}>
            <Text style={[styles.statNumber, { color: '#FF9800' }]}>
              {analysis.synthetic}
            </Text>
            <Text style={styles.statLabel}>Synthetic</Text>
          </View>

          <View style={styles.stat}>
            <Text style={[styles.statNumber, { color: '#999' }]}>{analysis.unknown}</Text>
            <Text style={styles.statLabel}>Unknown</Text>
          </View>
        </View>

        {/* Visual Bar */}
        <View style={styles.visualBar}>
          {analysis.natural > 0 && (
            <View
              style={[
                styles.naturalBar,
                { width: `${naturalPercentage}%` },
              ]}
            />
          )}
          {analysis.synthetic > 0 && (
            <View
              style={[
                styles.syntheticBar,
                { width: `${syntheticPercentage}%` },
              ]}
            />
          )}
        </View>

        <View style={styles.legend}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: '#4CAF50' }]} />
            <Text style={styles.legendText}>Natural {naturalPercentage}%</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: '#FF9800' }]} />
            <Text style={styles.legendText}>Synthetic {syntheticPercentage}%</Text>
          </View>
        </View>
      </View>

      {/* Known Ingredients (from Apothecary) */}
      {analysis.knownIngredients.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            📖 Ingredients We Know About ({analysis.knownIngredients.length})
          </Text>
          <Text style={styles.sectionSubtitle}>
            Tap to learn more about each ingredient
          </Text>

          {analysis.knownIngredients.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={styles.ingredientCard}
              onPress={() => onIngredientPress?.(item.apothecaryData.name)}
            >
              <View style={styles.ingredientHeader}>
                <Text style={styles.ingredientName}>{item.name}</Text>
                <View
                  style={[
                    styles.originBadge,
                    {
                      backgroundColor: item.isSynthetic ? '#FF9800' : '#4CAF50',
                    },
                  ]}
                >
                  <Text style={styles.originBadgeText}>
                    {item.isSynthetic ? '⚗️ Synthetic' : '🌿 Natural'}
                  </Text>
                </View>
              </View>

              <Text style={styles.ingredientCategory}>{item.apothecaryData.category}</Text>

              <Text style={styles.ingredientDescription} numberOfLines={2}>
                {item.apothecaryData.whatItDoes}
              </Text>

              {/* Show first purpose */}
              {item.apothecaryData.purpose.length > 0 && (
                <Text style={styles.ingredientPurpose}>
                  Purpose: {item.apothecaryData.purpose[0]}
                </Text>
              )}

              <Text style={styles.tapToLearn}>Tap to learn more →</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Unknown Ingredients */}
      {analysis.unknownIngredients.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            ❓ Ingredients Not in Our Database ({analysis.unknownIngredients.length})
          </Text>
          <Text style={styles.sectionSubtitle}>
            These ingredients aren't in our apothecary yet. They may be common food items,
            specific brand ingredients, or very rare compounds.
          </Text>

          <View style={styles.unknownList}>
            {analysis.unknownIngredients.map((name, index) => (
              <View key={index} style={styles.unknownItem}>
                <Text style={styles.unknownName}>{name}</Text>
              </View>
            ))}
          </View>

          <View style={styles.infoBox}>
            <Text style={styles.infoText}>
              💡 Don't worry! Not being in our database doesn't mean an ingredient is bad.
              Many common foods (like "wheat flour" or "tomatoes") are safe but not in our
              herbal/chemical database yet.
            </Text>
          </View>
        </View>
      )}

      {/* Educational Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerTitle}>🧪 About Natural vs Synthetic</Text>
        <Text style={styles.footerText}>
          <Text style={styles.bold}>Natural</Text> ingredients come from plants, animals, or
          minerals with minimal processing.{'\n\n'}
          <Text style={styles.bold}>Synthetic</Text> ingredients are made in laboratories,
          often identical to natural versions but more pure and consistent.{'\n\n'}
          Neither is inherently "better" - both can be safe or harmful depending on the
          specific compound, dosage, and context. What matters is understanding what each
          ingredient does in your body.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF9E6',
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 14,
    padding: 40,
  },
  summary: {
    backgroundColor: '#8D6E63',
    padding: 20,
  },
  summaryTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFF',
    marginBottom: 16,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  stat: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFF',
  },
  statLabel: {
    fontSize: 12,
    color: '#BCAAA4',
    marginTop: 4,
  },
  visualBar: {
    flexDirection: 'row',
    height: 12,
    borderRadius: 6,
    overflow: 'hidden',
    backgroundColor: '#4E342E',
    marginBottom: 12,
  },
  naturalBar: {
    backgroundColor: '#4CAF50',
  },
  syntheticBar: {
    backgroundColor: '#FF9800',
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  legendText: {
    fontSize: 12,
    color: '#BCAAA4',
  },
  section: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#EFEBE9',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#3E2723',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#6D4C41',
    marginBottom: 16,
    lineHeight: 18,
  },
  ingredientCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#D4C5A9',
  },
  ingredientHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  ingredientName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#3E2723',
    flex: 1,
  },
  originBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  originBadgeText: {
    fontSize: 11,
    color: '#FFF',
    fontWeight: '600',
  },
  ingredientCategory: {
    fontSize: 13,
    color: '#8D6E63',
    marginBottom: 8,
  },
  ingredientDescription: {
    fontSize: 14,
    color: '#4E342E',
    lineHeight: 20,
    marginBottom: 8,
  },
  ingredientPurpose: {
    fontSize: 12,
    color: '#6D4C41',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  tapToLearn: {
    fontSize: 12,
    color: '#1976D2',
    fontWeight: '500',
  },
  unknownList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  unknownItem: {
    backgroundColor: '#FFF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D4C5A9',
  },
  unknownName: {
    fontSize: 13,
    color: '#6D4C41',
  },
  infoBox: {
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#2196F3',
  },
  infoText: {
    fontSize: 13,
    color: '#1565C0',
    lineHeight: 18,
  },
  footer: {
    backgroundColor: '#FFF8E1',
    padding: 16,
    margin: 16,
    borderRadius: 8,
  },
  footerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F57F17',
    marginBottom: 8,
  },
  footerText: {
    fontSize: 13,
    color: '#6D4C41',
    lineHeight: 20,
  },
  bold: {
    fontWeight: '600',
  },
});
