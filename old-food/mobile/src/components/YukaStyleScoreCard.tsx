import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { OpenFoodFactsProduct } from '../services/openfoodfacts';
import {
  calculateProductScore,
  getRatingEmoji,
  getRatingDescription,
} from '../services/yuka-style-scoring';

interface YukaStyleScoreCardProps {
  product: OpenFoodFactsProduct;
  compact?: boolean;
}

/**
 * Displays a Yuka-style simplified product score
 * - 0-100 score with color coding
 * - Traffic light colors (green/yellow/orange/red)
 * - Quick-glance health rating
 */
export default function YukaStyleScoreCard({ product, compact }: YukaStyleScoreCardProps) {
  const scoreData = calculateProductScore(product);

  if (compact) {
    return (
      <View style={styles.compactContainer}>
        <View style={[styles.compactScoreBadge, { backgroundColor: scoreData.color }]}>
          <Text style={styles.compactScoreText}>{scoreData.score}</Text>
        </View>
        <Text style={styles.compactRating}>
          {getRatingEmoji(scoreData.rating)} {scoreData.rating}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Score Circle (Yuka-style) */}
      <View style={styles.scoreSection}>
        <View style={[styles.scoreCircle, { borderColor: scoreData.color }]}>
          <Text style={[styles.scoreNumber, { color: scoreData.color }]}>
            {scoreData.score}
          </Text>
          <Text style={styles.scoreMax}>/100</Text>
        </View>

        <View style={styles.ratingInfo}>
          <Text style={styles.emoji}>{getRatingEmoji(scoreData.rating)}</Text>
          <Text style={[styles.ratingText, { color: scoreData.color }]}>
            {getRatingDescription(scoreData.rating)}
          </Text>
        </View>
      </View>

      {/* Score Breakdown */}
      <View style={styles.breakdown}>
        <Text style={styles.breakdownTitle}>Score Breakdown:</Text>

        <ScoreRow
          label="Nutri-Score"
          points={scoreData.details.nutriScore}
          maxPoints={30}
        />
        <ScoreRow
          label="Processing/Additives"
          points={scoreData.details.additives}
          maxPoints={15}
        />
        <ScoreRow
          label="Organic"
          points={scoreData.details.organic}
          maxPoints={5}
        />
      </View>

      {/* Warnings */}
      {scoreData.warnings.length > 0 && (
        <View style={styles.warningsSection}>
          <Text style={styles.warningsTitle}>⚠️ Concerns:</Text>
          {scoreData.warnings.map((warning, index) => (
            <Text key={index} style={styles.warningText}>
              • {warning}
            </Text>
          ))}
        </View>
      )}

      {/* Recommendations */}
      {scoreData.recommendations.length > 0 && (
        <View style={styles.recommendationsSection}>
          <Text style={styles.recommendationsTitle}>💡 Recommendations:</Text>
          {scoreData.recommendations.map((rec, index) => (
            <Text key={index} style={styles.recommendationText}>
              • {rec}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

interface ScoreRowProps {
  label: string;
  points: number;
  maxPoints: number;
}

function ScoreRow({ label, points, maxPoints }: ScoreRowProps) {
  const percentage = Math.abs(points / maxPoints) * 100;
  const isPositive = points >= 0;

  return (
    <View style={styles.scoreRow}>
      <Text style={styles.scoreLabel}>{label}</Text>
      <View style={styles.scoreBar}>
        <View
          style={[
            styles.scoreBarFill,
            {
              width: `${percentage}%`,
              backgroundColor: isPositive ? '#4CAF50' : '#F44336',
            },
          ]}
        />
      </View>
      <Text style={[styles.scorePoints, { color: isPositive ? '#4CAF50' : '#F44336' }]}>
        {points > 0 ? '+' : ''}{points}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  compactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  compactScoreBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  compactScoreText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
  },
  compactRating: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
    textTransform: 'capitalize',
  },
  scoreSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 20,
  },
  scoreCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 6,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
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
  ratingInfo: {
    flex: 1,
  },
  emoji: {
    fontSize: 32,
    marginBottom: 4,
  },
  ratingText: {
    fontSize: 18,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  breakdown: {
    marginBottom: 16,
  },
  breakdownTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 12,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  scoreLabel: {
    fontSize: 12,
    color: '#666',
    width: 120,
  },
  scoreBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  scoreBarFill: {
    height: '100%',
  },
  scorePoints: {
    fontSize: 12,
    fontWeight: '600',
    width: 30,
    textAlign: 'right',
  },
  warningsSection: {
    backgroundColor: '#FFF3CD',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
    marginBottom: 12,
  },
  warningsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#856404',
    marginBottom: 8,
  },
  warningText: {
    fontSize: 12,
    color: '#856404',
    marginBottom: 4,
    lineHeight: 18,
  },
  recommendationsSection: {
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  recommendationsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2E7D32',
    marginBottom: 8,
  },
  recommendationText: {
    fontSize: 12,
    color: '#2E7D32',
    marginBottom: 4,
    lineHeight: 18,
  },
});
