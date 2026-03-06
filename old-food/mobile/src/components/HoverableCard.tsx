import React, { useState, useRef, useEffect } from 'react';
import { View, Text, Image, Pressable, StyleSheet, Dimensions, Platform } from 'react-native';

const SCREEN_WIDTH = Dimensions.get('window').width;
const CARD_WIDTH = Math.min((SCREEN_WIDTH - 48) / 2, 180);
const CARD_HEIGHT = CARD_WIDTH * (86 / 59);

interface HoverableCardProps {
  title: string;
  image?: string;
  badge?: string;
  stats?: Array<{ label: string; value: string | number }>;
  onPress?: () => void;
}

export default function HoverableCard({
  title,
  image,
  badge,
  stats,
  onPress,
}: HoverableCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [transform, setTransform] = useState('');
  const [glarePosition, setGlarePosition] = useState({ x: 50, y: 50 });
  const cardRef = useRef<any>(null);
  const innerRef = useRef<any>(null);
  const isWeb = Platform.OS === 'web';

  // Simple card for mobile - no fancy transforms
  if (!isWeb) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          mobileStyles.card,
          pressed && { opacity: 0.8, transform: [{ scale: 0.98 }] }
        ]}
      >
        {badge && (
          <View style={mobileStyles.badge}>
            <Text style={mobileStyles.badgeText}>{badge}</Text>
          </View>
        )}
        <View style={mobileStyles.header}>
          <Text style={mobileStyles.title} numberOfLines={2}>{title}</Text>
        </View>
        <View style={mobileStyles.imageContainer}>
          {image ? (
            <Image source={{ uri: image }} style={mobileStyles.image} resizeMode="cover" />
          ) : (
            <View style={mobileStyles.imagePlaceholder}>
              <Text style={mobileStyles.placeholderText}>
                {title.split(' ').map(word => word[0]).filter((_, i) => i < 2).join('')}
              </Text>
            </View>
          )}
        </View>
        {stats && stats.length > 0 && (
          <View style={mobileStyles.stats}>
            {stats.map((stat, idx) => (
              <View key={idx} style={mobileStyles.stat}>
                <Text style={mobileStyles.statValue}>{stat.value}</Text>
                <Text style={mobileStyles.statLabel}>{stat.label}</Text>
              </View>
            ))}
          </View>
        )}
      </Pressable>
    );
  }

  useEffect(() => {
    if (!isWeb || !cardRef.current) return;

    const card = cardRef.current;
    const inner = innerRef.current;

    const handleMouseMove = (e: MouseEvent) => {
      if (!isHovered) return;

      const rect = card.getBoundingClientRect();
      const cardWidth = rect.width;
      const cardHeight = rect.height;

      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const centerX = cardWidth / 2;
      const centerY = cardHeight / 2;

      // Calculate rotation (intensity = 15)
      const rotateX = ((mouseY - centerY) / centerY) * -15;
      const rotateY = ((mouseX - centerX) / centerX) * 15;

      // Apply transform
      const transformString = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(20px) scale3d(1.02, 1.02, 1.02)`;

      if (inner) {
        inner.style.transform = transformString;
      }

      // Update glare position
      const glareX = (mouseX / cardWidth) * 100;
      const glareY = (mouseY / cardHeight) * 100;
      setGlarePosition({ x: glareX, y: glareY });
    };

    const handleMouseLeave = () => {
      if (inner) {
        inner.style.transform = 'none';
      }
      setIsHovered(false);
    };

    card.addEventListener('mousemove', handleMouseMove);
    card.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      card.removeEventListener('mousemove', handleMouseMove);
      card.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [isWeb, isHovered]);

  const handlePress = () => {
    console.log('[HoverableCard] CLICK - navigating to:', title);
    // Reset hover state and call onPress
    setIsHovered(false);
    if (onPress) {
      onPress();
    }
  };

  return (
    <Pressable
      ref={cardRef}
      onPress={handlePress}
      onHoverIn={isWeb ? () => setIsHovered(true) : undefined}
      onHoverOut={isWeb ? () => setIsHovered(false) : undefined}
      style={[styles.card, isHovered && styles.cardHovered]}
    >
      <View ref={innerRef} pointerEvents="box-none" style={[styles.cardInner, isHovered && styles.cardInnerHovered]}>
        {/* Multiple thickness layers for 3D effect - pointerEvents none */}
        <View pointerEvents="none" style={[styles.cardSide1, isHovered && styles.cardSideHovered]} />
        <View pointerEvents="none" style={[styles.cardSide2, isHovered && styles.cardSideHovered]} />
        <View pointerEvents="none" style={[styles.cardSide3, isHovered && styles.cardSideHovered]} />

        {/* Card Front - box-none lets clicks through */}
        <View pointerEvents="box-none" style={styles.cardFront}>
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

          {/* Image Container - pointerEvents box-none to let clicks through */}
          <View style={[styles.imageContainer, { pointerEvents: 'box-none' }]}>
            {image ? (
              <Image
                source={{ uri: image }}
                style={[styles.image, isHovered && styles.imageHovered, { pointerEvents: 'none' }]}
                resizeMode="cover"
              />
            ) : (
              <View style={styles.imagePlaceholder}>
                <Text style={styles.placeholderText}>
                  {title.split(' ').map(word => word[0]).filter((_, i) => i < 2).join('')}
                </Text>
              </View>
            )}

            {/* Glare effect on hover - follows mouse */}
            {isHovered && isWeb && (
              <View
                pointerEvents="none"
                style={[
                  styles.glare,
                  {
                    // @ts-ignore
                    backgroundImage: `radial-gradient(circle at ${glarePosition.x}% ${glarePosition.y}%, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.1) 20%, transparent 50%)`,
                  },
                ]}
              />
            )}

            {/* Glow effect */}
            <View pointerEvents="none" style={[styles.glow, isHovered && styles.glowActive]} />
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

          {/* Hover overlay - pointerEvents none so clicks pass through */}
          {isHovered && (
            <View pointerEvents="none" style={styles.hoverOverlay}>
              <View pointerEvents="none" style={styles.overlayContent}>
                <Text style={styles.overlayText}>Tap to view</Text>
                <Text style={styles.overlayArrow}>→</Text>
              </View>
            </View>
          )}
        </View>
      </View>
    </Pressable>
  );
}

// Web-only CSS properties used for hover effects (cursor, transition, transform, etc.)
// These are passed through to web but ignored on native
const styles = StyleSheet.create<any>({
  card: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    marginBottom: 12,
    cursor: Platform.OS === 'web' ? 'pointer' : undefined,
    transition: Platform.OS === 'web' ? 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)' : undefined,
  },
  cardHovered: {
    transform: Platform.OS === 'web' ? 'translateY(-8px)' : undefined,
  },
  cardInner: {
    position: 'relative',
    width: '100%',
    height: '100%',
    borderRadius: 12,
    backgroundColor: '#fff',
    overflow: 'visible',
    transformStyle: Platform.OS === 'web' ? 'preserve-3d' : undefined,
    transition: Platform.OS === 'web' ? 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)' : undefined,
  },
  cardInnerHovered: {
    shadowColor: '#4CAF50',
    shadowOffset: { width: 0, height: 30 },
    shadowOpacity: 0.3,
    shadowRadius: 40,
    elevation: 15,
  },
  // Card side layers for 3D thickness
  cardSide1: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    borderRadius: 12,
    backgroundColor: 'rgba(76, 175, 80, 0.95)',
    borderWidth: 1,
    borderColor: 'rgba(76, 175, 80, 0.9)',
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'translateZ(-2px)' : undefined,
    pointerEvents: 'none',
  },
  cardSide2: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    borderRadius: 12,
    backgroundColor: 'rgba(76, 175, 80, 0.9)',
    borderWidth: 1,
    borderColor: 'rgba(76, 175, 80, 0.8)',
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'translateZ(-4px)' : undefined,
    pointerEvents: 'none',
  },
  cardSide3: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    borderRadius: 12,
    backgroundColor: 'rgba(76, 175, 80, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(76, 175, 80, 0.7)',
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'translateZ(-6px)' : undefined,
    pointerEvents: 'none',
  },
  cardSideHovered: {
    borderColor: '#4CAF50',
  },
  cardFront: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: 12,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    overflow: 'hidden',
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 5,
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'translateZ(50px)' : undefined,
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
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'translateZ(30px)' : undefined,
  },
  title: {
    fontSize: 12,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    lineHeight: 16,
  },
  imageContainer: {
    position: 'relative',
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'translateZ(20px)' : undefined,
  },
  image: {
    width: '100%',
    height: '100%',
    // @ts-ignore
    transition: Platform.OS === 'web' ? 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)' : undefined,
  },
  imageHovered: {
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'scale(1.1)' : [{ scale: 1.1 }],
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
  glare: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    // @ts-ignore
    backgroundImage: Platform.OS === 'web'
      ? 'radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.3) 0%, transparent 50%)'
      : undefined,
    opacity: 1,
    // @ts-ignore
    mixBlendMode: Platform.OS === 'web' ? 'overlay' : undefined,
    pointerEvents: 'none',
    zIndex: 5,
  },
  glow: {
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    borderRadius: 20,
    opacity: 0,
    zIndex: -1,
    // @ts-ignore
    backgroundImage: Platform.OS === 'web'
      ? 'linear-gradient(135deg, #4CAF50, #66BB6A)'
      : undefined,
    // @ts-ignore
    filter: Platform.OS === 'web' ? 'blur(20px)' : undefined,
    transition: Platform.OS === 'web' ? 'opacity 0.3s ease' : undefined,
  },
  glowActive: {
    opacity: 0.6,
  },
  stats: {
    flexDirection: 'row',
    paddingHorizontal: 4,
    paddingVertical: 6,
    gap: 4,
    // @ts-ignore
    transform: Platform.OS === 'web' ? 'translateZ(30px)' : undefined,
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
    // @ts-ignore
    backgroundImage: Platform.OS === 'web'
      ? 'linear-gradient(to top, rgba(76, 175, 80, 0.9) 0%, rgba(102, 187, 106, 0.9) 100%)'
      : undefined,
    backgroundColor: Platform.OS !== 'web' ? 'rgba(76, 175, 80, 0.9)' : undefined,
    padding: 12,
    zIndex: 20,
    pointerEvents: 'none', // CRITICAL: Allow clicks to pass through to Pressable
  },
  overlayContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  overlayText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  overlayArrow: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    // @ts-ignore
    transition: Platform.OS === 'web' ? 'transform 0.3s ease' : undefined,
  },
});

// Mobile-specific styles (cleaner, no web transforms)
const mobileStyles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    marginBottom: 12,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
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
    backgroundColor: '#f0f0f0',
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
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
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
