import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Animated,
  PanResponder,
} from 'react-native';

const SCREEN_WIDTH = Dimensions.get('window').width;
const CARD_WIDTH = Math.min((SCREEN_WIDTH - 48) / 2, 180);
const CARD_HEIGHT = CARD_WIDTH * (86 / 59);

interface AnimatedCardProps {
  title: string;
  image?: string;
  badge?: string;
  stats?: Array<{ label: string; value: string | number }>;
  onPress?: () => void;
}

export default function AnimatedCard({
  title,
  image,
  badge,
  stats,
  onPress,
}: AnimatedCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Animated values for 3D transforms
  const rotateX = useRef(new Animated.Value(0)).current;
  const rotateY = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(1)).current;
  const elevation = useRef(new Animated.Value(3)).current;

  // Pan responder for tracking touch movement
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,

      onPanResponderGrant: () => {
        setIsHovered(true);
        Animated.parallel([
          Animated.spring(scale, {
            toValue: 1.05,
            useNativeDriver: true,
            friction: 8,
          }),
          Animated.spring(elevation, {
            toValue: 10,
            useNativeDriver: false,
          }),
        ]).start();
      },

      onPanResponderMove: (evt, gestureState) => {
        // Calculate rotation based on touch position
        const { moveX, moveY } = gestureState;
        const cardCenterX = CARD_WIDTH / 2;
        const cardCenterY = CARD_HEIGHT / 2;

        // Convert to relative position
        const relX = (moveX - cardCenterX) / cardCenterX;
        const relY = (moveY - cardCenterY) / cardCenterY;

        // Apply subtle 3D rotation
        Animated.parallel([
          Animated.spring(rotateY, {
            toValue: relX * 15, // Max 15 degrees
            useNativeDriver: true,
            friction: 8,
          }),
          Animated.spring(rotateX, {
            toValue: -relY * 15, // Inverted for natural tilt
            useNativeDriver: true,
            friction: 8,
          }),
        ]).start();
      },

      onPanResponderRelease: () => {
        setIsHovered(false);

        // Reset to default state
        Animated.parallel([
          Animated.spring(rotateX, {
            toValue: 0,
            useNativeDriver: true,
            friction: 8,
          }),
          Animated.spring(rotateY, {
            toValue: 0,
            useNativeDriver: true,
            friction: 8,
          }),
          Animated.spring(scale, {
            toValue: 1,
            useNativeDriver: true,
            friction: 8,
          }),
          Animated.spring(elevation, {
            toValue: 3,
            useNativeDriver: false,
          }),
        ]).start();

        // Trigger onPress after animation
        if (onPress) {
          setTimeout(onPress, 100);
        }
      },
    })
  ).current;

  const animatedStyle = {
    transform: [
      { perspective: 1000 },
      { rotateX: rotateX.interpolate({
        inputRange: [-15, 15],
        outputRange: ['-15deg', '15deg'],
      })},
      { rotateY: rotateY.interpolate({
        inputRange: [-15, 15],
        outputRange: ['-15deg', '15deg'],
      })},
      { scale },
    ],
  };

  return (
    <Animated.View
      style={[
        styles.card,
        animatedStyle,
        {
          shadowOpacity: isHovered ? 0.3 : 0.15,
          shadowRadius: isHovered ? 12 : 8,
        },
      ]}
      {...panResponder.panHandlers}
    >
      <View style={styles.cardInner}>
        {/* Glare effect */}
        {isHovered && <View style={styles.glare} />}

        {/* Glow effect */}
        {isHovered && <View style={styles.glow} />}

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

        {/* Image Container */}
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

        {/* Hover overlay */}
        {isHovered && (
          <View style={styles.hoverOverlay}>
            <Text style={styles.hoverText}>Tap to view</Text>
          </View>
        )}
      </View>
    </Animated.View>
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
  glare: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    zIndex: 100,
    pointerEvents: 'none',
  },
  glow: {
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    borderRadius: 14,
    backgroundColor: 'rgba(76, 175, 80, 0.4)',
    zIndex: -1,
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
    textTransform: 'capitalize',
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
  hoverOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(76, 175, 80, 0.9)',
    padding: 8,
    alignItems: 'center',
  },
  hoverText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
});
