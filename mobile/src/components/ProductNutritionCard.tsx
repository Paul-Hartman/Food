import React, { useState } from 'react';
import { View, Text, StyleSheet, Image, ScrollView, TouchableOpacity } from 'react-native';
import { OpenFoodFactsProduct, formatNutritionData } from '../services/openfoodfacts';
import { getPairingRecommendations } from '../services/food-pairing-engine';

interface ProductNutritionCardProps {
  product: OpenFoodFactsProduct;
}

export default function ProductNutritionCard({ product }: ProductNutritionCardProps) {
  const nutrition = formatNutritionData(product);
  const pairings = getPairingRecommendations(product);
  const [showSynergies, setShowSynergies] = useState(true);

  const getNutriScoreColor = (grade?: string) => {
    if (!grade) return '#999';
    const colors: Record<string, string> = {
      a: '#008000',
      b: '#85BB2F',
      c: '#FFBB00',
      d: '#FF8C00',
      e: '#FF0000',
    };
    return colors[grade.toLowerCase()] || '#999';
  };

  const getNovaColor = (group?: number) => {
    if (!group) return '#999';
    const colors: Record<number, string> = {
      1: '#008000',
      2: '#85BB2F',
      3: '#FF8C00',
      4: '#FF0000',
    };
    return colors[group] || '#999';
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Product Header */}
      <View style={styles.header}>
        {product.image_front_small_url && (
          <Image
            source={{ uri: product.image_front_small_url }}
            style={styles.productImage}
            resizeMode="contain"
          />
        )}
        <View style={styles.headerText}>
          <Text style={styles.productName}>{product.product_name}</Text>
          {product.brands && <Text style={styles.brand}>{product.brands}</Text>}
          {product.quantity && <Text style={styles.quantity}>{product.quantity}</Text>}
        </View>
      </View>

      {/* Quick Tips (if any) */}
      {pairings.quickTips.length > 0 && (
        <View style={styles.quickTipsSection}>
          {pairings.quickTips.slice(0, 2).map((tip, index) => (
            <View key={index} style={styles.quickTip}>
              <Text style={styles.quickTipText}>{tip}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Nutrition Scores */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Nutrition Quality</Text>

        <View style={styles.scoresRow}>
          {/* Nutri-Score */}
          {nutrition.nutriScore && (
            <View style={styles.scoreCard}>
              <Text style={styles.scoreLabel}>Nutri-Score</Text>
              <View
                style={[
                  styles.scoreBadge,
                  { backgroundColor: getNutriScoreColor(nutrition.nutriScore) },
                ]}
              >
                <Text style={styles.scoreBadgeText}>{nutrition.nutriScore}</Text>
              </View>
              <Text style={styles.scoreDescription}>{nutrition.nutriScoreDesc}</Text>
            </View>
          )}

          {/* NOVA Group */}
          {nutrition.novaGroup && (
            <View style={styles.scoreCard}>
              <Text style={styles.scoreLabel}>NOVA Group</Text>
              <View
                style={[
                  styles.scoreBadge,
                  { backgroundColor: getNovaColor(nutrition.novaGroup) },
                ]}
              >
                <Text style={styles.scoreBadgeText}>{nutrition.novaGroup}</Text>
              </View>
              <Text style={styles.scoreDescription} numberOfLines={2}>
                {nutrition.novaDesc}
              </Text>
            </View>
          )}

          {/* Eco-Score */}
          {nutrition.ecoScore && (
            <View style={styles.scoreCard}>
              <Text style={styles.scoreLabel}>Eco-Score</Text>
              <View
                style={[
                  styles.scoreBadge,
                  { backgroundColor: getNutriScoreColor(nutrition.ecoScore) },
                ]}
              >
                <Text style={styles.scoreBadgeText}>{nutrition.ecoScore}</Text>
              </View>
              <Text style={styles.scoreDescription}>Environmental impact</Text>
            </View>
          )}
        </View>

        {/* Score Explanations */}
        <View style={styles.scoreExplanations}>
          {nutrition.novaGroup && (
            <Text style={styles.explanationText}>
              💡 NOVA {nutrition.novaGroup}: {nutrition.novaDesc}
            </Text>
          )}
          {nutrition.ecoScore && (
            <Text style={styles.explanationText}>
              🌍 Eco-Score {nutrition.ecoScore.toUpperCase()}: Environmental impact rating
            </Text>
          )}
        </View>
      </View>

      {/* Macronutrients */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Nutrition Facts (per 100g)</Text>

        <View style={styles.nutritionTable}>
          <NutritionRow label="Calories" value={nutrition.calories} unit="kcal" highlight />
          <NutritionRow label="Protein" value={nutrition.protein} unit="g" />
          <NutritionRow label="Carbohydrates" value={nutrition.carbs} unit="g" />
          <NutritionRow label="  - Sugars" value={nutrition.sugars} unit="g" indent />
          <NutritionRow label="Fat" value={nutrition.fat} unit="g" />
          <NutritionRow label="  - Saturated" value={nutrition.saturatedFat} unit="g" indent />
          <NutritionRow label="Fiber" value={nutrition.fiber} unit="g" />
          <NutritionRow label="Salt" value={nutrition.salt} unit="g" />
        </View>
      </View>

      {/* Vitamins & Minerals (if available) */}
      {(nutrition.vitaminA ||
        nutrition.vitaminC ||
        nutrition.vitaminD ||
        nutrition.calcium ||
        nutrition.iron) && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Vitamins & Minerals</Text>
          <View style={styles.nutritionTable}>
            {nutrition.vitaminA && (
              <NutritionRow label="Vitamin A" value={nutrition.vitaminA} unit="µg" />
            )}
            {nutrition.vitaminC && (
              <NutritionRow label="Vitamin C" value={nutrition.vitaminC} unit="mg" />
            )}
            {nutrition.vitaminD && (
              <NutritionRow label="Vitamin D" value={nutrition.vitaminD} unit="µg" />
            )}
            {nutrition.calcium && (
              <NutritionRow label="Calcium" value={nutrition.calcium} unit="mg" />
            )}
            {nutrition.iron && <NutritionRow label="Iron" value={nutrition.iron} unit="mg" />}
            {nutrition.potassium && (
              <NutritionRow label="Potassium" value={nutrition.potassium} unit="mg" />
            )}
            {nutrition.magnesium && (
              <NutritionRow label="Magnesium" value={nutrition.magnesium} unit="mg" />
            )}
            {nutrition.zinc && <NutritionRow label="Zinc" value={nutrition.zinc} unit="mg" />}
          </View>
        </View>
      )}

      {/* Food Pairing Synergies */}
      {pairings.recommendations.length > 0 && (
        <View style={styles.section}>
          <TouchableOpacity
            onPress={() => setShowSynergies(!showSynergies)}
            style={styles.sectionHeader}
          >
            <Text style={styles.sectionTitle}>
              ✨ Boost Absorption ({pairings.recommendations.length})
            </Text>
            <Text style={styles.toggleIcon}>{showSynergies ? '▼' : '▶'}</Text>
          </TouchableOpacity>

          {showSynergies && (
            <View>
              {pairings.recommendations.slice(0, 3).map((rec, index) => (
                <View key={index} style={styles.synergyCard}>
                  <Text style={styles.synergyTitle}>
                    {rec.synergy.nutrient1} + {rec.synergy.nutrient2}
                  </Text>
                  <Text style={styles.synergyEffect}>
                    {rec.synergy.magnitudePercent
                      ? `↑ ${rec.synergy.magnitudePercent}% boost`
                      : rec.synergy.effect}
                  </Text>
                  <Text style={styles.synergyExplanation}>{rec.explanation}</Text>
                  <View style={styles.synergyPairings}>
                    <Text style={styles.pairingsLabel}>Pair with:</Text>
                    {rec.suggestedPairings.slice(0, 2).map((pairing, i) => (
                      <Text key={i} style={styles.pairingItem}>
                        • {pairing}
                      </Text>
                    ))}
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Pairing Warnings */}
      {pairings.warnings.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚠️ Nutrient Interactions</Text>
          {pairings.warnings.map((warning, index) => (
            <View key={index} style={styles.warningCard}>
              <Text style={styles.warningTitle}>
                {warning.antagonism.nutrient1} ⚡ {warning.antagonism.nutrient2}
              </Text>
              <Text style={styles.warningText}>{warning.advice}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Allergens */}
      {nutrition.allergens.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚠️ Allergens</Text>
          <View style={styles.allergensList}>
            {nutrition.allergens.map((allergen, index) => (
              <View key={index} style={styles.allergenBadge}>
                <Text style={styles.allergenText}>
                  {allergen.replace('en:', '').replace(/-/g, ' ')}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Ingredients */}
      {product.ingredients_text && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ingredients</Text>
          <Text style={styles.ingredientsText}>{product.ingredients_text}</Text>
        </View>
      )}

      {/* Data Source */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Data from OpenFoodFacts • Product code: {product.code}
        </Text>
      </View>
    </ScrollView>
  );
}

interface NutritionRowProps {
  label: string;
  value: number | undefined;
  unit: string;
  highlight?: boolean;
  indent?: boolean;
}

function NutritionRow({ label, value, unit, highlight, indent }: NutritionRowProps) {
  if (value === undefined || value === 0) return null;

  return (
    <View style={[styles.nutritionRow, highlight && styles.nutritionRowHighlight]}>
      <Text style={[styles.nutritionLabel, indent && styles.indented]}>{label}</Text>
      <Text style={styles.nutritionValue}>
        {value.toFixed(1)} {unit}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  productImage: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginRight: 12,
  },
  headerText: {
    flex: 1,
    justifyContent: 'center',
  },
  productName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  brand: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2,
  },
  quantity: {
    fontSize: 12,
    color: '#999',
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
  scoresRow: {
    flexDirection: 'row',
    gap: 12,
  },
  scoreCard: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
    padding: 12,
    borderRadius: 8,
  },
  scoreLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
    textAlign: 'center',
  },
  scoreBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  scoreBadgeText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
    textTransform: 'uppercase',
  },
  scoreDescription: {
    fontSize: 10,
    color: '#999',
    textAlign: 'center',
  },
  nutritionTable: {
    gap: 4,
  },
  nutritionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  nutritionRowHighlight: {
    backgroundColor: '#f9f9f9',
    paddingHorizontal: 8,
    borderRadius: 4,
  },
  nutritionLabel: {
    fontSize: 14,
    color: '#333',
  },
  indented: {
    marginLeft: 16,
    color: '#666',
  },
  nutritionValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#4CAF50',
  },
  allergensList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  allergenBadge: {
    backgroundColor: '#FFF3CD',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#FFD700',
  },
  allergenText: {
    fontSize: 12,
    color: '#856404',
    textTransform: 'capitalize',
  },
  ingredientsText: {
    fontSize: 13,
    color: '#666',
    lineHeight: 20,
  },
  footer: {
    padding: 16,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 11,
    color: '#999',
    textAlign: 'center',
  },
  quickTipsSection: {
    padding: 12,
    backgroundColor: '#E3F2FD',
    gap: 8,
  },
  quickTip: {
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#2196F3',
  },
  quickTipText: {
    fontSize: 13,
    color: '#1976D2',
    fontWeight: '500',
  },
  scoreExplanations: {
    marginTop: 12,
    gap: 6,
  },
  explanationText: {
    fontSize: 11,
    color: '#666',
    lineHeight: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  toggleIcon: {
    fontSize: 12,
    color: '#999',
  },
  synergyCard: {
    backgroundColor: '#F1F8E9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#8BC34A',
  },
  synergyTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#558B2F',
    marginBottom: 4,
  },
  synergyEffect: {
    fontSize: 12,
    color: '#7CB342',
    fontWeight: '500',
    marginBottom: 6,
  },
  synergyExplanation: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
    lineHeight: 16,
  },
  synergyPairings: {
    marginTop: 4,
  },
  pairingsLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#558B2F',
    marginBottom: 4,
  },
  pairingItem: {
    fontSize: 11,
    color: '#666',
    marginLeft: 8,
  },
  warningCard: {
    backgroundColor: '#FFF3E0',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  warningTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#E65100',
    marginBottom: 4,
  },
  warningText: {
    fontSize: 11,
    color: '#BF360C',
    lineHeight: 16,
  },
});
