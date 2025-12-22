import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useFocusEffect } from '@react-navigation/native';
import { API_BASE_URL } from '../config';

export default function ScannerScreen({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(true);

  // Reset camera when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      // Screen is focused - activate camera and reset scan state
      setCameraActive(true);
      setScanned(false);
      setLoading(false);

      return () => {
        // Screen is unfocused - deactivate camera
        setCameraActive(false);
      };
    }, [])
  );

  if (!permission) {
    return <View style={styles.container}><ActivityIndicator size="large" color="#4CAF50" /></View>;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>Camera access is needed to scan barcodes</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const resetScanner = () => {
    setScanned(false);
    setLoading(false);
    // Force camera to restart by toggling it
    setCameraActive(false);
    setTimeout(() => setCameraActive(true), 100);
  };

  const handleBarCodeScanned = async ({ type, data }) => {
    if (scanned || loading) return;
    setScanned(true);
    setLoading(true);

    try {
      // Look up barcode in our API
      const response = await fetch(`${API_BASE_URL}/api/barcode/${data}`);
      const result = await response.json();

      setLoading(false);

      if (result.found && result.source === 'local') {
        // Product already in our database
        Alert.alert(
          'Product Found',
          `${result.product.name}${result.product.brand ? ` by ${result.product.brand}` : ''}`,
          [
            {
              text: 'Add to Inventory',
              onPress: () => navigation.navigate('AddProduct', {
                product: result.product,
                mode: 'add_inventory'
              }),
            },
            {
              text: 'View Details',
              onPress: () => navigation.navigate('ProductDetail', {
                productId: result.product.id
              }),
            },
            { text: 'Scan Another', onPress: resetScanner },
          ]
        );
      } else if (result.found && result.source === 'open_food_facts') {
        // Found in Open Food Facts
        Alert.alert(
          'Product Found',
          `${result.name}${result.brand ? ` by ${result.brand}` : ''}\n\nSave to your pantry?`,
          [
            {
              text: 'Save & Add',
              onPress: () => navigation.navigate('AddProduct', {
                product: result,
                mode: 'new_product'
              }),
            },
            { text: 'Scan Another', onPress: resetScanner },
          ]
        );
      } else {
        // Not found anywhere
        Alert.alert(
          'Product Not Found',
          `Barcode: ${data}\n\nWould you like to add this product manually?`,
          [
            {
              text: 'Add Manually',
              onPress: () => navigation.navigate('AddProduct', {
                barcode: data,
                mode: 'manual'
              }),
            },
            { text: 'Scan Another', onPress: resetScanner },
          ]
        );
      }
    } catch (error) {
      setLoading(false);
      Alert.alert('Error', `Failed to look up barcode: ${error.message}`, [
        { text: 'OK', onPress: resetScanner },
      ]);
    }
  };

  return (
    <View style={styles.container}>
      {cameraActive ? (
        <CameraView
          style={styles.camera}
          barcodeScannerSettings={{
            barcodeTypes: ['ean13', 'ean8', 'upc_a', 'upc_e', 'code128', 'code39', 'qr'],
          }}
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
        >
          <View style={styles.overlay}>
            <View style={styles.scanFrame}>
              <View style={[styles.corner, styles.topLeft]} />
              <View style={[styles.corner, styles.topRight]} />
              <View style={[styles.corner, styles.bottomLeft]} />
              <View style={[styles.corner, styles.bottomRight]} />
            </View>
            <Text style={styles.scanText}>
              {loading ? 'Looking up product...' : 'Point camera at barcode'}
            </Text>
          </View>
        </CameraView>
      ) : (
        <View style={styles.cameraPlaceholder}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Starting camera...</Text>
        </View>
      )}

      {scanned && !loading && (
        <TouchableOpacity
          style={styles.rescanButton}
          onPress={resetScanner}
        >
          <Text style={styles.buttonText}>Tap to Scan Again</Text>
        </TouchableOpacity>
      )}

      <TouchableOpacity
        style={styles.manualButton}
        onPress={() => navigation.navigate('AddProduct', { mode: 'manual' })}
      >
        <Text style={styles.manualButtonText}>+ Add Manually</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  permissionText: {
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 20,
    paddingHorizontal: 40,
  },
  camera: {
    flex: 1,
    width: '100%',
  },
  cameraPlaceholder: {
    flex: 1,
    width: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 16,
  },
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  scanFrame: {
    width: 280,
    height: 200,
    borderWidth: 0,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: '#4CAF50',
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
  },
  scanText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 20,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#4CAF50',
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  rescanButton: {
    position: 'absolute',
    bottom: 120,
    backgroundColor: '#4CAF50',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 8,
  },
  manualButton: {
    position: 'absolute',
    bottom: 60,
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 25,
    borderRadius: 8,
  },
  manualButtonText: {
    color: '#fff',
    fontSize: 16,
  },
});
