import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { OpenFoodFactsProduct } from '../services/openfoodfacts';
import { analyzeMealCombination } from '../services/food-pairing-engine';

interface MealSynergyAnalyzerProps {
  products: OpenFoodFactsProduct[];
}

/**
 * Analyzes a meal of multiple products for nutrient synergies and conflicts
 *
 * Example use case:
 * - User adds spinach, lentils, and orange to their meal plan
 * - This component detects:
 *   ✅ Iron (lentils/spinach) + Vitamin C (orange) = 3x better absorption
 *   ⚠️ Calcium (spinach) + Iron conflict if consuming with milk
 */
export default function MealSynergyAnalyzer({ products }: MealSynergyAnalyzerProps) {
  if (products.length < 2) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>Add 2+ items to analyze meal synergies</Text>
      </View>
    );
  }

  const analysis = analyzeMealCombination(products);

  const getScoreColor = (score: number): string => {
    if (score >= 75) return '#4CAF50';
    if (score >= 50) return '#8BC34A';
    if (score >= 25) return '#FF9800';
    return '#F44336';
  };

  return (
    <ScrollView style={styles.container}>
      {/* Overall Meal Score */}
      <View style={styles.scoreSection}>
        <Text style={styles.scoreLabel}>Meal Synergy Score</Text>
        <View style={[styles.scoreCircle, { borderColor: getScoreColor(analysis.overallScore) }]}>
          <Text style={[styles.scoreNumber, { color: getScoreColor(analysis.overallScore) }]}>
            {analysis.overallScore}
          </Text>
          <Text style={styles.scoreMax}>/100</Text>
        </View>
        {analysis.suggestions.map((suggestion, index) => (
          <Text key={index} style={styles.suggestion}>
            {suggestion}
          </Text>
        ))}
      </View>

      {/* Synergies Found */}
      {analysis.synergiesFound.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            ✨ Beneficial Combinations ({analysis.synergiesFound.length})
          </Text>
          {analysis.synergiesFound.map((item, index) => (
            <View key={index} style={styles.synergyCard}>
              <View style={styles.productPair}>
                <Text style={styles.productName}>{item.products[0]}</Text>
                <Text style={styles.plusIcon}>+</Text>
                <Text style={styles.productName}>{item.products[1]}</Text>
              </View>

              <View style={styles.benefitBadge}>
                <Text style={styles.benefitText}>{item.benefit}</Text>
              </View>

              <View style={styles.synergyDetails}>
                <Text style={styles.synergyLabel}>
                  {item.synergy.nutrient1} + {item.synergy.nutrient2}
                </Text>
                <Text style={styles.synergyEffect}>{item.synergy.effect}</Text>

                {item.synergy.timing && (
                  <Text style={styles.timingNote}>⏱️ {item.synergy.timing}</Text>
                )}
              </View>

              <Text style={styles.scientific}>
                📚 {item.synergy.scientificBasis}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Antagonisms Found */}
      {analysis.antagonismsFound.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            ⚠️ Nutrient Conflicts ({analysis.antagonismsFound.length})
          </Text>
          {analysis.antagonismsFound.map((item, index) => (
            <View key={index} style={styles.antagonismCard}>
              <View style={styles.productPair}>
                <Text style={styles.productName}>{item.products[0]}</Text>
                <Text style={styles.conflictIcon}>⚡</Text>
                <Text style={styles.productName}>{item.products[1]}</Text>
              </View>

              <View style={styles.concernBadge}>
                <Text style={styles.concernText}>{item.concern}</Text>
              </View>

              <View style={styles.antagonismDetails}>
                <Text style={styles.antagonismLabel}>
                  {item.antagonism.nutrient1} vs {item.antagonism.nutrient2}
                </Text>
                <Text style={styles.antagonismEffect}>{item.antagonism.effect}</Text>
              </View>

              <View style={styles.solutionBox}>
                <Text style={styles.solutionTitle}>💡 How to fix:</Text>
                <Text style={styles.solutionText}>
                  {item.antagonism.separationTime || 'Consider separating these foods'}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* No synergies or conflicts */}
      {analysis.synergiesFound.length === 0 && analysis.antagonismsFound.length === 0 && (
        <View style={styles.neutralSection}>
          <Text style={styles.neutralEmoji}>😐</Text>
          <Text style={styles.neutralTitle}>No Major Interactions</Text>
          <Text style={styles.neutralText}>
            These foods can be eaten together without significant nutrient synergies or conflicts.
          </Text>
        </View>
      )}

      {/* Educational Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerTitle}>💡 About Nutrient Synergies</Text>
        <Text style={styles.footerText}>
          Certain nutrients work better together! For example, vitamin C increases iron absorption
          by 3-4x, while black pepper boosts turmeric absorption by 2000%. Strategic food pairing
          maximizes nutrition from your meals.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 14,
    padding: 40,
  },
  scoreSection: {
    backgroundColor: '#fff',
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  scoreLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  scoreCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 6,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
    marginBottom: 12,
  },
  scoreNumber: {
    fontSize: 36,
    fontWeight: '700',
  },
  scoreMax: {
    fontSize: 14,
    color: '#999',
    marginTop: -4,
  },
  suggestion: {
    fontSize: 13,
    color: '#666',
    textAlign: 'center',
    marginTop: 4,
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 12,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  synergyCard: {
    backgroundColor: '#F1F8E9',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#8BC34A',
  },
  antagonismCard: {
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  productPair: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  productName: {
    fontSize: 13,
    color: '#333',
    fontWeight: '500',
    flex: 1,
  },
  plusIcon: {
    fontSize: 16,
    color: '#8BC34A',
    fontWeight: '600',
  },
  conflictIcon: {
    fontSize: 16,
    color: '#FF9800',
  },
  benefitBadge: {
    backgroundColor: '#C5E1A5',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  benefitText: {
    fontSize: 12,
    color: '#33691E',
    fontWeight: '600',
  },
  concernBadge: {
    backgroundColor: '#FFE0B2',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  concernText: {
    fontSize: 12,
    color: '#E65100',
    fontWeight: '600',
  },
  synergyDetails: {
    marginBottom: 8,
  },
  synergyLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#558B2F',
    marginBottom: 2,
  },
  synergyEffect: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  timingNote: {
    fontSize: 11,
    color: '#7CB342',
    fontStyle: 'italic',
  },
  scientific: {
    fontSize: 10,
    color: '#999',
    lineHeight: 14,
    marginTop: 4,
  },
  antagonismDetails: {
    marginBottom: 8,
  },
  antagonismLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#E65100',
    marginBottom: 2,
  },
  antagonismEffect: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  solutionBox: {
    backgroundColor: 'rgba(255, 152, 0, 0.1)',
    padding: 8,
    borderRadius: 6,
    marginTop: 4,
  },
  solutionTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#E65100',
    marginBottom: 4,
  },
  solutionText: {
    fontSize: 11,
    color: '#666',
    lineHeight: 16,
  },
  neutralSection: {
    backgroundColor: '#fff',
    padding: 40,
    alignItems: 'center',
  },
  neutralEmoji: {
    fontSize: 48,
    marginBottom: 12,
  },
  neutralTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  neutralText: {
    fontSize: 13,
    color: '#999',
    textAlign: 'center',
    lineHeight: 20,
  },
  footer: {
    backgroundColor: '#E3F2FD',
    padding: 16,
    marginTop: 12,
  },
  footerTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 8,
  },
  footerText: {
    fontSize: 12,
    color: '#1565C0',
    lineHeight: 18,
  },
});
