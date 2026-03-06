import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ActivityIndicator,
  Alert,
  Dimensions,
} from 'react-native';
import { Camera, CameraView } from 'expo-camera';
import * as Haptics from 'expo-haptics';
import { lookupBarcode, extractPantryItem, OpenFoodFactsProduct } from '../services/openfoodfacts';

const { width } = Dimensions.get('window');
const SCAN_BOX_SIZE = width * 0.7;

interface BarcodeScannerProps {
  visible: boolean;
  onClose: () => void;
  onProductFound: (item: { name: string; category: string; quantity: number; unit: string }) => void;
}

export default function BarcodeScanner({ visible, onClose, onProductFound }: BarcodeScannerProps) {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [scannedBarcode, setScannedBarcode] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    // Prevent duplicate scans
    if (scannedBarcode === data || loading) {
      return;
    }

    setScannedBarcode(data);
    setLoading(true);

    // Haptic feedback
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    console.log('📱 Scanned:', data);

    try {
      // Look up product in OpenFoodFacts
      const product = await lookupBarcode(data);

      if (product) {
        // Success haptic
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

        // Extract pantry item data
        const item = extractPantryItem(product);

        // Show product info and confirm
        Alert.alert(
          'Product Found',
          `${product.product_name}\n${product.brands || ''}\n\nAdd to pantry?`,
          [
            {
              text: 'Cancel',
              style: 'cancel',
              onPress: () => {
                setScannedBarcode(null);
                setLoading(false);
              },
            },
            {
              text: 'Add',
              onPress: () => {
                onProductFound(item);
                onClose();
              },
            },
          ]
        );
      } else {
        // Error haptic
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

        Alert.alert(
          'Product Not Found',
          `Barcode ${data} was not found in the OpenFoodFacts database.\n\nYou can add it manually or try scanning again.`,
          [
            {
              text: 'Try Again',
              onPress: () => {
                setScannedBarcode(null);
                setLoading(false);
              },
            },
            { text: 'Close', onPress: onClose },
          ]
        );
      }
    } catch (error) {
      console.error('Barcode scan error:', error);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

      Alert.alert(
        'Scan Error',
        'Failed to look up product. Please try again.',
        [
          {
            text: 'Try Again',
            onPress: () => {
              setScannedBarcode(null);
              setLoading(false);
            },
          },
          { text: 'Close', onPress: onClose },
        ]
      );
    }
  };

  if (hasPermission === null) {
    return <View />;
  }

  if (hasPermission === false) {
    return (
      <Modal visible={visible} animationType="slide">
        <View style={styles.container}>
          <Text style={styles.errorText}>No access to camera</Text>
          <TouchableOpacity style={styles.button} onPress={onClose}>
            <Text style={styles.buttonText}>Close</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide">
      <View style={styles.container}>
        <CameraView
          style={StyleSheet.absoluteFillObject}
          onBarcodeScanned={loading ? undefined : handleBarCodeScanned}
          barcodeScannerSettings={{
            barcodeTypes: ['ean13', 'ean8', 'upc_a', 'upc_e', 'code128', 'code39'],
          }}
        />

        {/* Overlay */}
        <View style={styles.overlay}>
          {/* Top bar */}
          <View style={styles.topBar}>
            <Text style={styles.title}>Scan Barcode</Text>
            <TouchableOpacity onPress={onClose} disabled={loading}>
              <Text style={styles.closeButton}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Scan box */}
          <View style={styles.scanArea}>
            <View style={styles.scanBox}>
              {/* Corner markers */}
              <View style={[styles.corner, styles.cornerTopLeft]} />
              <View style={[styles.corner, styles.cornerTopRight]} />
              <View style={[styles.corner, styles.cornerBottomLeft]} />
              <View style={[styles.corner, styles.cornerBottomRight]} />

              {loading && (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size="large" color="#fff" />
                  <Text style={styles.loadingText}>Looking up product...</Text>
                </View>
              )}
            </View>

            <Text style={styles.instructions}>
              {loading ? 'Checking database...' : 'Align barcode within the frame'}
            </Text>
          </View>

          {/* Bottom info */}
          <View style={styles.bottomBar}>
            <Text style={styles.infoText}>
              Powered by OpenFoodFacts
            </Text>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  overlay: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 50,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
  },
  closeButton: {
    fontSize: 28,
    color: '#fff',
    fontWeight: '300',
  },
  scanArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanBox: {
    width: SCAN_BOX_SIZE,
    height: SCAN_BOX_SIZE * 0.6,
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  corner: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderColor: '#4CAF50',
    borderWidth: 3,
  },
  cornerTopLeft: {
    top: 0,
    left: 0,
    borderBottomWidth: 0,
    borderRightWidth: 0,
  },
  cornerTopRight: {
    top: 0,
    right: 0,
    borderBottomWidth: 0,
    borderLeftWidth: 0,
  },
  cornerBottomLeft: {
    bottom: 0,
    left: 0,
    borderTopWidth: 0,
    borderRightWidth: 0,
  },
  cornerBottomRight: {
    bottom: 0,
    right: 0,
    borderTopWidth: 0,
    borderLeftWidth: 0,
  },
  loadingContainer: {
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    marginTop: 12,
    fontSize: 14,
  },
  instructions: {
    color: '#fff',
    marginTop: 24,
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  bottomBar: {
    paddingBottom: 40,
    alignItems: 'center',
  },
  infoText: {
    color: '#aaa',
    fontSize: 12,
  },
  errorText: {
    fontSize: 18,
    color: '#fff',
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
