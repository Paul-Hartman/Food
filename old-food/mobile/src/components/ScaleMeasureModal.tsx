/**
 * ScaleMeasureModal - Recipe Ingredient Measuring Component
 *
 * Live weight display for precise ingredient measurement during cooking.
 * Integrates with BluetoothScaleService for real-time weight polling.
 *
 * Features:
 * - Large live weight display (updates every 1.5s)
 * - Progress bar showing % of target reached
 * - Visual/haptic feedback when target reached
 * - Tare button to zero scale
 * - Auto-deduct from pantry on confirm
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { scaleService } from '../services/BluetoothScaleService';
import type { ScaleReading } from '../services/BluetoothScaleService';

// ============================================================================
// Types
// ============================================================================

export interface IngredientToMeasure {
  name: string;              // "Flour"
  targetAmount: number;      // 250 (grams)
  unit: string;              // "g"
  inventoryId?: number;      // For pantry deduction
  productId?: number;        // For logging
}

interface Props {
  visible: boolean;
  ingredient: IngredientToMeasure | null;
  onClose: () => void;
  onComplete: (actualAmount: number) => void;
  containerTare?: number;    // Optional container tare weight
}

// ============================================================================
// Component
// ============================================================================

export default function ScaleMeasureModal({
  visible,
  ingredient,
  onClose,
  onComplete,
  containerTare = 0,
}: Props) {
  // State
  const [currentWeight, setCurrentWeight] = useState<number>(0);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isStable, setIsStable] = useState<boolean>(false);
  const [tareOffset, setTareOffset] = useState<number>(containerTare);
  const [errorMessage, setErrorMessage] = useState<string>('');

  // Animations
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  // Calculate net weight and progress
  const netWeight = Math.max(0, currentWeight - tareOffset);
  const targetWeight = ingredient?.targetAmount || 0;
  const progress = targetWeight > 0 ? (netWeight / targetWeight) * 100 : 0;
  const isTargetReached = Math.abs(netWeight - targetWeight) <= 2; // ±2g tolerance
  const isOverTarget = netWeight > targetWeight + 2;

  // ============================================================================
  // Effects
  // ============================================================================

  // Connect to scale when modal opens
  useEffect(() => {
    if (visible && ingredient) {
      connectToScale();
    } else {
      disconnectFromScale();
    }

    return () => {
      disconnectFromScale();
    };
  }, [visible, ingredient]);

  // Update progress animation
  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: Math.min(progress, 100),
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [progress]);

  // Pulse animation when target reached
  useEffect(() => {
    if (isTargetReached && !isOverTarget) {
      // Trigger haptic feedback
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      // Pulse animation
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.1, duration: 200, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
      ]).start();
    } else if (isOverTarget) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
  }, [isTargetReached, isOverTarget]);

  // ============================================================================
  // Scale Connection
  // ============================================================================

  const connectToScale = async () => {
    try {
      setIsConnecting(true);
      setErrorMessage('');

      // Request permissions
      const hasPermissions = await scaleService.requestPermissions();
      if (!hasPermissions) {
        setErrorMessage('Bluetooth permissions required');
        setIsConnecting(false);
        return;
      }

      // Connect to scale (mock or real)
      await scaleService.connect();

      // Start polling for weight updates
      scaleService.startPolling((reading: ScaleReading) => {
        setCurrentWeight(reading.weight);
        setIsStable(reading.isStable);
      });

      setIsConnected(true);
      setIsConnecting(false);
    } catch (error) {
      console.error('Scale connection error:', error);
      setErrorMessage('Failed to connect to scale');
      setIsConnecting(false);
    }
  };

  const disconnectFromScale = () => {
    scaleService.stopPolling();
    scaleService.disconnect();
    setIsConnected(false);
  };

  // ============================================================================
  // Actions
  // ============================================================================

  const handleTare = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setTareOffset(currentWeight);

    // Visual feedback
    Animated.sequence([
      Animated.timing(pulseAnim, { toValue: 0.9, duration: 100, useNativeDriver: true }),
      Animated.timing(pulseAnim, { toValue: 1, duration: 100, useNativeDriver: true }),
    ]).start();
  };

  const handleDone = () => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    onComplete(netWeight);
    onClose();
  };

  const handleCancel = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onClose();
  };

  // ============================================================================
  // Status Text
  // ============================================================================

  const getStatusText = (): string => {
    if (!isConnected) return 'Connecting...';
    if (isOverTarget) return `Too much! Remove ${(netWeight - targetWeight).toFixed(1)}g`;
    if (isTargetReached) return isStable ? 'Perfect! Weight stable ✓' : 'Perfect! Wait for stable...';
    if (netWeight === 0) return 'Place ingredient on scale';
    return `Keep adding... ${(targetWeight - netWeight).toFixed(1)}g to go`;
  };

  const getStatusColor = (): string => {
    if (!isConnected) return '#757575';
    if (isOverTarget) return '#FF5722';
    if (isTargetReached) return '#4CAF50';
    return '#2196F3';
  };

  // ============================================================================
  // Render
  // ============================================================================

  if (!ingredient) return null;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={false}
      onRequestClose={handleCancel}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleCancel} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Measuring {ingredient.name}</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Main Content */}
        <View style={styles.content}>
          {/* Target Display */}
          <View style={styles.targetSection}>
            <Text style={styles.targetLabel}>TARGET</Text>
            <Text style={styles.targetValue}>
              {targetWeight}{ingredient.unit}
            </Text>
          </View>

          {/* Live Weight Display */}
          <Animated.View style={[styles.weightCard, { transform: [{ scale: pulseAnim }] }]}>
            <View style={styles.weightContainer}>
              <Text style={styles.weightValue}>
                {netWeight.toFixed(1)}
              </Text>
              <Text style={styles.weightUnit}>g</Text>
            </View>

            {/* Scale Icon */}
            <Text style={styles.scaleIcon}>⚖️</Text>

            {/* Connection Status */}
            {isConnecting && (
              <Text style={styles.connectionStatus}>Connecting...</Text>
            )}
            {!isConnected && !isConnecting && errorMessage && (
              <Text style={styles.errorText}>{errorMessage}</Text>
            )}
          </Animated.View>

          {/* Progress Bar */}
          <View style={styles.progressSection}>
            <View style={styles.progressBarContainer}>
              <Animated.View
                style={[
                  styles.progressBarFill,
                  {
                    width: progressAnim.interpolate({
                      inputRange: [0, 100],
                      outputRange: ['0%', '100%'],
                    }),
                    backgroundColor: isOverTarget
                      ? '#FF5722'
                      : isTargetReached
                      ? '#4CAF50'
                      : '#2196F3',
                  },
                ]}
              />
            </View>
            <Text style={styles.progressText}>
              {progress.toFixed(1)}% {isTargetReached && '(±2g tolerance)'}
            </Text>
          </View>

          {/* Status Text */}
          <View style={[styles.statusSection, { backgroundColor: getStatusColor() + '20' }]}>
            <Text style={[styles.statusText, { color: getStatusColor() }]}>
              {getStatusText()}
            </Text>
            {isStable && isTargetReached && (
              <Text style={styles.stableIndicator}>🟢 Stable</Text>
            )}
          </View>

          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.button, styles.tareButton]}
              onPress={handleTare}
              disabled={!isConnected}
            >
              <Text style={styles.buttonText}>TARE</Text>
              <Text style={styles.buttonSubtext}>(Zero Scale)</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.button,
                styles.doneButton,
                (!isConnected || netWeight === 0) && styles.buttonDisabled,
              ]}
              onPress={handleDone}
              disabled={!isConnected || netWeight === 0}
            >
              <Text style={styles.buttonText}>DONE</Text>
              <Text style={styles.buttonSubtext}>
                {netWeight > 0 ? `Use ${netWeight.toFixed(1)}g` : 'Add ingredient'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Helper Text */}
          <Text style={styles.helperText}>
            💡 Tip: Use "Tare" to zero scale with container on it
          </Text>
        </View>
      </View>
    </Modal>
  );
}

// ============================================================================
// Styles
// ============================================================================

const { width, height } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 20,
    backgroundColor: '#4CAF50',
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    fontSize: 28,
    color: '#FFFFFF',
    fontWeight: '300',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'space-around',
  },
  targetSection: {
    alignItems: 'center',
    marginBottom: 20,
  },
  targetLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#757575',
    letterSpacing: 1,
  },
  targetValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#212121',
    marginTop: 4,
  },
  weightCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    minHeight: 250,
  },
  weightContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  weightValue: {
    fontSize: 80,
    fontWeight: '700',
    color: '#212121',
    fontVariant: ['tabular-nums'],
  },
  weightUnit: {
    fontSize: 32,
    fontWeight: '500',
    color: '#757575',
    marginLeft: 8,
  },
  scaleIcon: {
    fontSize: 48,
    marginTop: 20,
  },
  connectionStatus: {
    fontSize: 14,
    color: '#757575',
    marginTop: 10,
  },
  errorText: {
    fontSize: 14,
    color: '#F44336',
    marginTop: 10,
  },
  progressSection: {
    marginVertical: 30,
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#757575',
    textAlign: 'center',
    marginTop: 8,
  },
  statusSection: {
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
  },
  statusText: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  stableIndicator: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flex: 1,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tareButton: {
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#2196F3',
  },
  doneButton: {
    backgroundColor: '#4CAF50',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#212121',
  },
  buttonSubtext: {
    fontSize: 12,
    color: '#757575',
    marginTop: 4,
  },
  helperText: {
    fontSize: 12,
    color: '#757575',
    textAlign: 'center',
    marginTop: 20,
  },
});
