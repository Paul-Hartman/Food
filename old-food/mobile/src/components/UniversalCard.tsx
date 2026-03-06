import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';

const SCREEN_WIDTH = Dimensions.get('window').width;
const CARD_WIDTH = Math.min((SCREEN_WIDTH - 48) / 2, 180); // Max 180px width, 2 columns with padding
const CARD_HEIGHT = CARD_WIDTH * (86 / 59); // Yu-Gi-Oh aspect ratio

interface UniversalCardProps {
  title: string;
  image?: string;
  badge?: string;
  stats?: Array<{ label: string; value: string | number }>;
  onPress?: () => void;
}

export default function UniversalCard({
  title,
  image,
  badge,
  stats,
  onPress,
}: UniversalCardProps) {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.9}
    >
      <View style={styles.cardInner}>
        {/* Badge */}
        {badge && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{badge}</Text>
          </View>
        )}

        {/* Title */}
        <View style={styles.header}>
          <Text style={styles.title} numberOfLines={2}>
            {title}
          </Text>
        </View>

        {/* Image Container - Center 1/3 */}
        <View style={styles.imageContainer}>
          {image ? (
            <Image
              source={{ uri: image }}
              style={styles.image}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Text style={styles.placeholderText}>
                {title.split(' ').map(word => word[0]).filter((_, i) => i < 2).join('')}
              </Text>
            </View>
          )}
        </View>

        {/* Stats */}
        {stats && stats.length > 0 && (
          <View style={styles.stats}>
            {stats.map((stat, idx) => (
              <View key={idx} style={styles.stat}>
                <Text style={styles.statValue}>{stat.value}</Text>
                <Text style={styles.statLabel}>{stat.label}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    marginBottom: 12,
  },
  cardInner: {
    flex: 1,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#4CAF50',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    zIndex: 10,
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  header: {
    paddingHorizontal: 8,
    paddingTop: 8,
    paddingBottom: 4,
    alignItems: 'center',
  },
  title: {
    fontSize: 12,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    lineHeight: 16,
  },
  imageContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  placeholderText: {
    fontSize: 32,
    fontWeight: '700',
    color: 'rgba(76, 175, 80, 0.5)',
  },
  stats: {
    flexDirection: 'row',
    paddingHorizontal: 4,
    paddingVertical: 6,
    gap: 4,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 11,
    fontWeight: '700',
    color: '#4CAF50',
  },
  statLabel: {
    fontSize: 9,
    color: '#666',
    marginTop: 2,
  },
});
