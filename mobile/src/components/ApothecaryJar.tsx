import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import type { ApothecaryIngredient } from '../services/apothecary-database';

interface ApothecaryJarProps {
  ingredient: ApothecaryIngredient;
  onPress?: () => void;
  compact?: boolean;
}

/**
 * Apothecary Jar Component
 * Displays an ingredient like an old apothecary jar label
 */
export default function ApothecaryJar({ ingredient, onPress, compact }: ApothecaryJarProps) {
  const getOriginIcon = (origin: string) => {
    const icons: Record<string, string> = {
      plant: '🌿',
      animal: '🦴',
      mineral: '⛰️',
      fungal: '🍄',
      bacterial: '🦠',
      synthetic: '⚗️',
    };
    return icons[origin] || '📦';
  };

  const getOriginColor = (origin: string) => {
    const colors: Record<string, string> = {
      plant: '#4CAF50',
      animal: '#FF5722',
      mineral: '#607D8B',
      fungal: '#9C27B0',
      bacterial: '#2196F3',
      synthetic: '#FF9800',
    };
    return colors[origin] || '#999';
  };

  if (compact) {
    return (
      <TouchableOpacity style={styles.compactJar} onPress={onPress}>
        <View style={[styles.compactOriginBadge, { backgroundColor: getOriginColor(ingredient.origin) }]}>
          <Text style={styles.compactOriginIcon}>{getOriginIcon(ingredient.origin)}</Text>
        </View>
        <View style={styles.compactContent}>
          <Text style={styles.compactName}>{ingredient.name}</Text>
          <Text style={styles.compactCategory}>{ingredient.category}</Text>
        </View>
        <Text style={styles.arrow}>›</Text>
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity style={styles.jar} onPress={onPress}>
      {/* Jar Label (Vintage Style) */}
      <View style={styles.jarLabel}>
        <Text style={styles.jarLabelText}>{ingredient.jarLabel}</Text>
      </View>

      {/* Origin Badge */}
      <View style={[styles.originBadge, { backgroundColor: getOriginColor(ingredient.origin) }]}>
        <Text style={styles.originIcon}>{getOriginIcon(ingredient.origin)}</Text>
        <Text style={styles.originText}>{ingredient.origin}</Text>
      </View>

      {/* Scientific Name */}
      {ingredient.scientificName && (
        <Text style={styles.scientificName}>{ingredient.scientificName}</Text>
      )}

      {/* Visual Description */}
      <View style={styles.appearance}>
        <Text style={styles.appearanceLabel}>Appearance:</Text>
        <Text style={styles.appearanceText}>
          {ingredient.color} {ingredient.texture && ` • ${ingredient.texture}`}
        </Text>
      </View>

      {/* What It Does (Teaser) */}
      <Text style={styles.teaser} numberOfLines={2}>
        {ingredient.whatItDoes}
      </Text>

      {/* Tradition Indicators */}
      {ingredient.traditionalUses.length > 0 && (
        <View style={styles.traditions}>
          {ingredient.traditionalUses.slice(0, 3).map((use, index) => (
            <View key={index} style={styles.traditionBadge}>
              <Text style={styles.traditionText}>
                {use.tradition === 'ayurveda' && '🕉️'}
                {use.tradition === 'tcm' && '☯️'}
                {use.tradition === 'western' && '⚕️'}
                {use.tradition === 'native_american' && '🪶'}
                {use.tradition === 'middle_eastern' && '🌙'}
                {use.tradition === 'african' && '🌍'}
                {use.tradition === 'modern' && '🔬'}
              </Text>
            </View>
          ))}
        </View>
      )}
    </TouchableOpacity>
  );
}

/**
 * Detailed Apothecary Entry (Full Screen View)
 */
interface ApothecaryEntryProps {
  ingredient: ApothecaryIngredient;
}

export function ApothecaryEntry({ ingredient }: ApothecaryEntryProps) {
  return (
    <ScrollView style={styles.entry}>
      {/* Header */}
      <View style={styles.entryHeader}>
        <Text style={styles.entryName}>{ingredient.name}</Text>
        <Text style={styles.entryJarLabel}>{ingredient.jarLabel}</Text>
        {ingredient.scientificName && (
          <Text style={styles.entryScientific}>{ingredient.scientificName}</Text>
        )}

        {/* Common Names */}
        {ingredient.commonNames.length > 0 && (
          <Text style={styles.commonNames}>
            Also known as: {ingredient.commonNames.join(', ')}
          </Text>
        )}
      </View>

      {/* What It Does (Main Description) */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📖 What It Does</Text>
        <Text style={styles.sectionText}>{ingredient.whatItDoes}</Text>
      </View>

      {/* Traditional Uses */}
      {ingredient.traditionalUses.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🏛️ Traditional Wisdom</Text>
          {ingredient.traditionalUses.map((use, index) => (
            <View key={index} style={styles.traditionCard}>
              <View style={styles.traditionHeader}>
                <Text style={styles.traditionName}>
                  {use.tradition === 'ayurveda' && '🕉️ Ayurveda'}
                  {use.tradition === 'tcm' && '☯️ Traditional Chinese Medicine'}
                  {use.tradition === 'western' && '⚕️ Western Herbalism'}
                  {use.tradition === 'native_american' && '🪶 Native American'}
                  {use.tradition === 'middle_eastern' && '🌙 Middle Eastern'}
                  {use.tradition === 'african' && '🌍 African Traditional'}
                  {use.tradition === 'modern' && '🔬 Modern Science'}
                </Text>
              </View>
              <Text style={styles.traditionUse}>{use.use}</Text>
              <Text style={styles.traditionPrep}>Preparation: {use.preparation}</Text>
              {use.historicalContext && (
                <Text style={styles.traditionHistory}>📜 {use.historicalContext}</Text>
              )}
            </View>
          ))}
        </View>
      )}

      {/* Active Compounds (The Science) */}
      {ingredient.activeCompounds.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔬 Active Compounds</Text>
          {ingredient.activeCompounds.map((compound, index) => (
            <View key={index} style={styles.compoundCard}>
              <Text style={styles.compoundName}>{compound.name}</Text>
              <Text style={styles.compoundFunction}>{compound.function}</Text>
              <Text style={styles.compoundMechanism}>
                ⚙️ Mechanism: {compound.mechanism}
              </Text>
              <View style={styles.evidenceBadge}>
                <Text style={styles.evidenceText}>
                  Evidence: {compound.evidence.replace(/_/g, ' ')}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Body Targets */}
      {ingredient.bodyTargets.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🎯 Where It Works</Text>
          <View style={styles.targetsList}>
            {ingredient.bodyTargets.map((target, index) => (
              <View key={index} style={styles.targetItem}>
                <Text style={styles.targetBullet}>•</Text>
                <Text style={styles.targetText}>{target}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Absorption Notes */}
      {ingredient.absorptionNotes && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>💊 How Your Body Processes It</Text>
          <Text style={styles.sectionText}>{ingredient.absorptionNotes}</Text>
        </View>
      )}

      {/* Food Applications */}
      {ingredient.usedIn.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🍽️ Found In</Text>
          <View style={styles.foodList}>
            {ingredient.usedIn.map((food, index) => (
              <View key={index} style={styles.foodTag}>
                <Text style={styles.foodText}>{food}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Synthetic vs Natural */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          {ingredient.isSynthetic ? '⚗️ Synthetic Compound' : '🌿 Natural Origin'}
        </Text>
        {ingredient.isSynthetic && ingredient.synthesisMethod && (
          <Text style={styles.sectionText}>
            How it's made: {ingredient.synthesisMethod}
          </Text>
        )}
        {ingredient.naturalEquivalent && (
          <Text style={styles.sectionText}>
            Natural equivalent: {ingredient.naturalEquivalent}
          </Text>
        )}
        {ingredient.syntheticEquivalent && (
          <Text style={styles.sectionText}>
            Synthetic equivalent: {ingredient.syntheticEquivalent}
          </Text>
        )}
        {ingredient.processNotes && (
          <Text style={styles.sectionText}>
            Processing: {ingredient.processNotes}
          </Text>
        )}
      </View>

      {/* Safety */}
      {(ingredient.safeDosage || ingredient.warnings || ingredient.interactions) && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚠️ Safety & Dosage</Text>
          {ingredient.safeDosage && (
            <Text style={styles.dosage}>Safe dosage: {ingredient.safeDosage}</Text>
          )}
          {ingredient.warnings && ingredient.warnings.length > 0 && (
            <View style={styles.warningBox}>
              <Text style={styles.warningTitle}>Warnings:</Text>
              {ingredient.warnings.map((warning, index) => (
                <Text key={index} style={styles.warningText}>
                  • {warning}
                </Text>
              ))}
            </View>
          )}
          {ingredient.interactions && ingredient.interactions.length > 0 && (
            <View style={styles.interactionBox}>
              <Text style={styles.interactionTitle}>Interactions:</Text>
              {ingredient.interactions.map((interaction, index) => (
                <Text key={index} style={styles.interactionText}>
                  • {interaction}
                </Text>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Folklore & Curiosities */}
      {(ingredient.folklore || ingredient.curiosities || ingredient.quotes) && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📚 Lore & Curiosities</Text>
          {ingredient.folklore && (
            <View style={styles.folkloreBox}>
              <Text style={styles.folkloreText}>{ingredient.folklore}</Text>
            </View>
          )}
          {ingredient.quotes && ingredient.quotes.map((quote, index) => (
            <Text key={index} style={styles.quote}>
              "{quote}"
            </Text>
          ))}
          {ingredient.curiosities && ingredient.curiosities.map((fact, index) => (
            <Text key={index} style={styles.curiosity}>
              💡 {fact}
            </Text>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  // Compact Jar
  compactJar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF9E6',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#D4C5A9',
  },
  compactOriginBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  compactOriginIcon: {
    fontSize: 20,
  },
  compactContent: {
    flex: 1,
  },
  compactName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3E2723',
  },
  compactCategory: {
    fontSize: 12,
    color: '#6D4C41',
  },
  arrow: {
    fontSize: 20,
    color: '#A1887F',
  },

  // Full Jar
  jar: {
    backgroundColor: '#FFF9E6',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#D4C5A9',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  jarLabel: {
    backgroundColor: '#8D6E63',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 4,
    marginBottom: 12,
  },
  jarLabelText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
    fontFamily: 'monospace',
  },
  originBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 8,
  },
  originIcon: {
    fontSize: 16,
    marginRight: 4,
  },
  originText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  scientificName: {
    fontSize: 12,
    fontStyle: 'italic',
    color: '#6D4C41',
    marginBottom: 8,
  },
  appearance: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  appearanceLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#5D4037',
  },
  appearanceText: {
    fontSize: 12,
    color: '#6D4C41',
    marginLeft: 4,
  },
  teaser: {
    fontSize: 13,
    color: '#4E342E',
    lineHeight: 18,
    marginBottom: 8,
  },
  traditions: {
    flexDirection: 'row',
    gap: 6,
  },
  traditionBadge: {
    backgroundColor: '#EFEBE9',
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  traditionText: {
    fontSize: 16,
  },

  // Entry View
  entry: {
    flex: 1,
    backgroundColor: '#FFF9E6',
  },
  entryHeader: {
    backgroundColor: '#8D6E63',
    padding: 20,
  },
  entryName: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFF',
    marginBottom: 4,
  },
  entryJarLabel: {
    fontSize: 14,
    color: '#FFECB3',
    marginBottom: 8,
    fontFamily: 'monospace',
  },
  entryScientific: {
    fontSize: 14,
    fontStyle: 'italic',
    color: '#D7CCC8',
  },
  commonNames: {
    fontSize: 12,
    color: '#BCAAA4',
    marginTop: 8,
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
    marginBottom: 12,
  },
  sectionText: {
    fontSize: 14,
    color: '#4E342E',
    lineHeight: 20,
  },
  traditionCard: {
    backgroundColor: '#EFEBE9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#8D6E63',
  },
  traditionHeader: {
    marginBottom: 8,
  },
  traditionName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#5D4037',
  },
  traditionUse: {
    fontSize: 13,
    color: '#4E342E',
    marginBottom: 6,
  },
  traditionPrep: {
    fontSize: 12,
    color: '#6D4C41',
    fontStyle: 'italic',
    marginBottom: 6,
  },
  traditionHistory: {
    fontSize: 11,
    color: '#8D6E63',
    lineHeight: 16,
  },
  compoundCard: {
    backgroundColor: '#F5F5F5',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  compoundName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 4,
  },
  compoundFunction: {
    fontSize: 14,
    color: '#333',
    marginBottom: 6,
  },
  compoundMechanism: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
    marginBottom: 6,
  },
  evidenceBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  evidenceText: {
    fontSize: 11,
    color: '#1565C0',
    textTransform: 'capitalize',
  },
  targetsList: {
    gap: 6,
  },
  targetItem: {
    flexDirection: 'row',
  },
  targetBullet: {
    fontSize: 14,
    color: '#8D6E63',
    marginRight: 8,
  },
  targetText: {
    flex: 1,
    fontSize: 14,
    color: '#4E342E',
  },
  foodList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  foodTag: {
    backgroundColor: '#FFECB3',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  foodText: {
    fontSize: 12,
    color: '#F57F17',
  },
  dosage: {
    fontSize: 14,
    color: '#2E7D32',
    marginBottom: 12,
  },
  warningBox: {
    backgroundColor: '#FFF3E0',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
    marginBottom: 12,
  },
  warningTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E65100',
    marginBottom: 6,
  },
  warningText: {
    fontSize: 13,
    color: '#BF360C',
    lineHeight: 18,
  },
  interactionBox: {
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  interactionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2E7D32',
    marginBottom: 6,
  },
  interactionText: {
    fontSize: 13,
    color: '#1B5E20',
    lineHeight: 18,
  },
  folkloreBox: {
    backgroundColor: '#FFF8E1',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  folkloreText: {
    fontSize: 14,
    color: '#F57F17',
    lineHeight: 20,
    fontStyle: 'italic',
  },
  quote: {
    fontSize: 13,
    color: '#6D4C41',
    fontStyle: 'italic',
    marginBottom: 8,
    paddingLeft: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#BCAAA4',
  },
  curiosity: {
    fontSize: 13,
    color: '#4E342E',
    marginBottom: 6,
    lineHeight: 18,
  },
});
