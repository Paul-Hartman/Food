import React, { useState, useEffect, useRef } from 'react';
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
import { ScannedItem } from '../types';
import { api } from '../services/api';
import ErrorReportButton from './ErrorReportButton';

const { width } = Dimensions.get('window');
const SCAN_BOX_SIZE = width * 0.7;
const DEBOUNCE_MS = 3000; // 3 seconds between scans

interface BarcodeScannerProps {
  visible: boolean;
  onClose: () => void;
  onProductFound: (item: { name: string; category: string; quantity: number; unit: string }) => void;

  // Bulk mode
  bulkMode?: boolean;
  onBulkScanComplete?: (scannedItemIds: number[]) => void;
}

export default function BarcodeScanner({
  visible,
  onClose,
  onProductFound,
  bulkMode = false,
  onBulkScanComplete
}: BarcodeScannerProps) {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [scannedBarcode, setScannedBarcode] = useState<string | null>(null);

  // Bulk mode state
  const [bulkScannedItems, setBulkScannedItems] = useState<ScannedItem[]>([]);
  const [lastScanTime, setLastScanTime] = useState(0);
  const [previewExpanded, setPreviewExpanded] = useState(true);
  const isScanningRef = useRef(false);
  const processedBarcodesRef = useRef<Map<string, number>>(new Map()); // barcode -> timestamp

  // Error reporting state
  const [showErrorButton, setShowErrorButton] = useState(false);
  const [lastError, setLastError] = useState<{
    type: string;
    message: string;
    barcode?: string;
  } | null>(null);

  useEffect(() => {
    (async () => {
      const { status} = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const scanInBulkMode = async (barcode: string) => {
    // Prevent duplicate scans
    if (isScanningRef.current) {
      console.log('⏱️ Already scanning, ignoring...');
      return;
    }

    isScanningRef.current = true;
    setLoading(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const product = await lookupBarcode(barcode);

      if (!product) {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        console.log('Product not found');
        setLoading(false);
        isScanningRef.current = false;
        return;
      }

      const item = extractPantryItem(product);

      // Check for duplicate: If barcode already scanned, increment quantity
      const existingIndex = bulkScannedItems.findIndex(i => i.barcode === barcode);

      if (existingIndex !== -1) {
        // UPDATE existing item's quantity
        const existingItem = bulkScannedItems[existingIndex];
        const newQty = existingItem.quantity + item.quantity;

        await api.updatePantryItem(existingItem.id, newQty);

        setBulkScannedItems(prev => prev.map((it, idx) =>
          idx === existingIndex
            ? { ...it, quantity: newQty, timestamp: Date.now() }
            : it
        ));

        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        console.log(`Updated ${item.name}: ${newQty}${item.unit}`);

      } else {
        // ADD new item to pantry immediately
        console.log('📦 Adding to pantry with image:', item.image_url);
        const response = await api.addToPantry({
          name: item.name,
          category: item.category,
          quantity: item.quantity,
          unit: item.unit,
          image_url: item.image_url,
        });

        const newItem: ScannedItem = {
          id: response.id,
          barcode,
          name: item.name,
          category: item.category,
          quantity: item.quantity,
          unit: item.unit,
          timestamp: Date.now(),
        };

        setBulkScannedItems(prev => [newItem, ...prev]); // Prepend

        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        console.log(`Added ${item.name}: ${item.quantity}${item.unit}`);
      }

    } catch (error) {
      console.error('Bulk scan error:', error);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

      // Show error report button
      setLastError({
        type: 'bulk_scan_error',
        message: error instanceof Error ? error.message : 'Unknown error during bulk scan',
        barcode,
      });
      setShowErrorButton(true);
    } finally {
      setLoading(false);
      isScanningRef.current = false;
    }
  };

  const handleDoneScanning = () => {
    if (bulkScannedItems.length === 0) return;

    const itemIds = bulkScannedItems.map(item => item.id);
    onBulkScanComplete?.(itemIds);

    // Reset state
    setBulkScannedItems([]);
    setLastScanTime(0);
    setPreviewExpanded(true);

    onClose();
  };

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    const now = Date.now();

    // NUCLEAR OPTION: ABSOLUTE SINGLE-SHOT LOCK
    // Check if this barcode was processed in the last 3 seconds
    const lastProcessed = processedBarcodesRef.current.get(data);
    if (lastProcessed && (now - lastProcessed) < DEBOUNCE_MS) {
      return; // HARD BLOCK - already processed
    }

    // Check if any scan is currently in progress
    if (isScanningRef.current) {
      return; // HARD BLOCK - scan in progress
    }

    // Mark barcode as processed IMMEDIATELY (before any async work)
    processedBarcodesRef.current.set(data, now);
    isScanningRef.current = true; // CRITICAL: Lock immediately

    // Clean up old barcode entries
    for (const [barcode, timestamp] of processedBarcodesRef.current.entries()) {
      if (now - timestamp > DEBOUNCE_MS) {
        processedBarcodesRef.current.delete(barcode);
      }
    }

    if (bulkMode) {
      setLastScanTime(now);
      await scanInBulkMode(data);
      return;
    }

    // Single mode: existing logic
    // Prevent duplicate scans
    if (scannedBarcode === data || loading) {
      isScanningRef.current = false; // Unlock before return
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
                isScanningRef.current = false;
              },
            },
            {
              text: 'Add',
              onPress: () => {
                onProductFound(item);
                isScanningRef.current = false;
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
                isScanningRef.current = false;
              },
            },
            {
              text: 'Close',
              onPress: () => {
                isScanningRef.current = false;
                onClose();
              }
            },
          ]
        );
      }
    } catch (error) {
      console.error('Barcode scan error:', error);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

      // Show error report button
      setLastError({
        type: 'scan_error',
        message: error instanceof Error ? error.message : 'Unknown error during scan',
        barcode: data,
      });
      setShowErrorButton(true);

      Alert.alert(
        'Scan Error',
        'Failed to look up product. Please try again.',
        [
          {
            text: 'Try Again',
            onPress: () => {
              setScannedBarcode(null);
              setLoading(false);
              isScanningRef.current = false;
            },
          },
          {
            text: 'Close',
            onPress: () => {
              isScanningRef.current = false;
              onClose();
            }
          },
        ]
      );
    } finally {
      // Always unlock when done
      isScanningRef.current = false;
    }
  };

  const renderPreviewDrawer = () => {
    const visibleItems = bulkScannedItems.slice(0, 3);

    return (
      <View style={styles.previewDrawer}>
        {/* Header with item count */}
        <TouchableOpacity
          onPress={() => setPreviewExpanded(!previewExpanded)}
          style={styles.previewHeader}
        >
          <Text style={styles.previewTitle}>
            ✅ {bulkScannedItems.length} item{bulkScannedItems.length !== 1 ? 's' : ''} added
          </Text>
          <Text style={styles.expandIcon}>{previewExpanded ? '▼' : '▲'}</Text>
        </TouchableOpacity>

        {/* Last 3 items (collapsible) */}
        {previewExpanded && (
          <View style={styles.previewList}>
            {visibleItems.map(item => (
              <View key={item.id} style={styles.previewItem}>
                <Text style={styles.previewName} numberOfLines={1}>
                  {item.name}
                </Text>
                <Text style={styles.previewQty}>
                  {item.quantity}{item.unit}
                </Text>
              </View>
            ))}
            {bulkScannedItems.length > 3 && (
              <Text style={styles.moreText}>+{bulkScannedItems.length - 3} more</Text>
            )}
          </View>
        )}

        {/* Done button */}
        <TouchableOpacity
          style={[styles.doneButton, bulkScannedItems.length === 0 && styles.doneButtonDisabled]}
          onPress={handleDoneScanning}
          disabled={bulkScannedItems.length === 0}
        >
          <Text style={styles.doneButtonText}>
            Done Scanning ({bulkScannedItems.length})
          </Text>
        </TouchableOpacity>
      </View>
    );
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
            <Text style={styles.title}>
              {bulkMode ? 'Bulk Scan Mode' : 'Scan Barcode'}
            </Text>
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
              {loading
                ? 'Checking database...'
                : bulkMode
                ? 'Scan items continuously. Tap Done when finished.'
                : 'Align barcode within the frame'}
            </Text>
          </View>

          {/* Preview drawer (bulk mode only) */}
          {bulkMode && renderPreviewDrawer()}

          {/* Bottom info (single mode only) */}
          {!bulkMode && (
            <View style={styles.bottomBar}>
              <Text style={styles.infoText}>
                Powered by OpenFoodFacts
              </Text>
            </View>
          )}
        </View>

        {/* Error Report Button */}
        <ErrorReportButton
          screen="BarcodeScanner"
          errorType={lastError?.type}
          errorMessage={lastError?.message}
          barcode={lastError?.barcode}
          context={{ bulkMode, itemsScanned: bulkScannedItems.length }}
          visible={showErrorButton}
          onDismiss={() => setShowErrorButton(false)}
        />
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
  previewDrawer: {
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 12,
    paddingBottom: 40,
    paddingHorizontal: 20,
  },
  previewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  previewTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  expandIcon: {
    color: '#fff',
    fontSize: 14,
  },
  previewList: {
    paddingTop: 12,
    paddingBottom: 12,
  },
  previewItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(76, 175, 80, 0.2)',
    borderRadius: 8,
    marginBottom: 8,
  },
  previewName: {
    color: '#fff',
    fontSize: 14,
    flex: 1,
    marginRight: 12,
  },
  previewQty: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: '600',
  },
  moreText: {
    color: '#aaa',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
  },
  doneButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
  },
  doneButtonDisabled: {
    backgroundColor: '#555',
    opacity: 0.5,
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
