import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Image,
  Modal,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Vibration,
  Dimensions,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { API_BASE_URL } from '../config';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function AddProductScreen({ route, navigation }) {
  const { product, barcode, mode } = route.params || {};

  // Camera permissions
  const [permission, requestPermission] = useCameraPermissions();

  // Product info
  const [name, setName] = useState(product?.name || '');
  const [brand, setBrand] = useState(product?.brand || '');
  const [category, setCategory] = useState(product?.category || 'pantry');
  const [imageUrl, setImageUrl] = useState(product?.image_url || '');
  const [packageWeight, setPackageWeight] = useState(
    product?.package_weight_g?.toString() || ''
  );
  const [price, setPrice] = useState(product?.price?.toString() || '');

  // Nutrition per 100g
  const [calories, setCalories] = useState(product?.calories?.toString() || '0');
  const [protein, setProtein] = useState(product?.protein?.toString() || '0');
  const [carbs, setCarbs] = useState(product?.carbs?.toString() || '0');
  const [fat, setFat] = useState(product?.fat?.toString() || '0');
  const [fiber, setFiber] = useState(product?.fiber?.toString() || '0');
  const [sodium, setSodium] = useState(product?.sodium?.toString() || '0');
  const [sugar, setSugar] = useState(product?.sugar?.toString() || '0');

  // Inventory info
  const [location, setLocation] = useState('fridge');

  // UNIT TRACKING - Multiple units with different weight/expiry
  const [units, setUnits] = useState([
    { id: 1, currentWeight: '', expiryDate: '', isOpened: false }
  ]);
  const [nextUnitId, setNextUnitId] = useState(2);

  // Scanner state - can be 'expiry' or 'weight'
  const [showScanner, setShowScanner] = useState(false);
  const [scannerMode, setScannerMode] = useState('expiry'); // 'expiry' or 'weight'
  const [scanningUnitId, setScanningUnitId] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const cameraRef = useRef(null);

  // CONTINUOUS OCR STATE - Google Translate style
  const [detectedBoxes, setDetectedBoxes] = useState([]);
  const [detectedValue, setDetectedValue] = useState(null);
  const [rawOcrText, setRawOcrText] = useState('');
  const [scanConfidence, setScanConfidence] = useState(0);
  const scanIntervalRef = useRef(null);
  const successCountRef = useRef(0); // Count consecutive successful reads

  // Autocomplete
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);

  // Existing product ID (for adding units to existing product)
  const [existingProductId, setExistingProductId] = useState(product?.id || null);

  // Search for products as user types
  const handleNameChange = async (text) => {
    setName(text);
    if (text.length >= 2) {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/pantry/search?q=${encodeURIComponent(text)}`
        );
        const results = await response.json();
        setSearchResults(results);
        setShowResults(true);
      } catch (error) {
        console.error('Search error:', error);
      }
    } else {
      setShowResults(false);
    }
  };

  const handleSelectResult = (item) => {
    setName(item.name);
    setBrand(item.brand || '');
    setImageUrl(item.image_url || '');
    setPackageWeight(item.package_weight_g?.toString() || '');
    setExistingProductId(item.id);
    setShowResults(false);

    // If it's a local product, ask if they want to add more units
    if (item.id) {
      Alert.alert(
        'Product Found',
        `${item.name} is already in your database.\nAdd new unit(s) to your ${location}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Add Units',
            onPress: () => {
              // Stay on screen to configure units
            },
          },
        ]
      );
    }
  };

  // Add a new unit
  const addUnit = () => {
    setUnits([
      ...units,
      { id: nextUnitId, currentWeight: '', expiryDate: '', isOpened: false }
    ]);
    setNextUnitId(nextUnitId + 1);
  };

  // Remove a unit
  const removeUnit = (unitId) => {
    if (units.length > 1) {
      setUnits(units.filter(u => u.id !== unitId));
    }
  };

  // Update a unit's properties
  const updateUnit = (unitId, field, value) => {
    setUnits(units.map(u =>
      u.id === unitId ? { ...u, [field]: value } : u
    ));
  };

  // Open scanner modal for expiry date or weight
  const openScanner = (unitId, mode) => {
    if (!permission?.granted) {
      requestPermission();
      return;
    }
    setScanningUnitId(unitId);
    setScannerMode(mode);
    setDetectedBoxes([]);
    setDetectedValue(null);
    setRawOcrText('');
    setScanConfidence(0);
    successCountRef.current = 0;
    setShowScanner(true);
  };

  // Close scanner and cleanup
  const closeScanner = useCallback(() => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    setShowScanner(false);
    setDetectedBoxes([]);
    setDetectedValue(null);
    setRawOcrText('');
    setScanConfidence(0);
    successCountRef.current = 0;
    setIsScanning(false);
  }, []);

  // Continuous OCR scanning - captures frame every 800ms
  const performContinuousScan = useCallback(async () => {
    if (!cameraRef.current || isScanning) return;

    setIsScanning(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({
        base64: true,
        quality: 0.7, // Lower quality for faster processing
        skipProcessing: true,
      });

      const endpoint = scannerMode === 'weight'
        ? `${API_BASE_URL}/api/ocr/scale-weight`
        : `${API_BASE_URL}/api/ocr/expiry-date`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: photo.base64 }),
      });

      const result = await response.json();

      // Update detected boxes for visual feedback
      if (result.detected_boxes) {
        setDetectedBoxes(result.detected_boxes);
      }
      if (result.raw_text) {
        setRawOcrText(result.raw_text.slice(0, 100));
      }

      if (result.success) {
        // Found a valid result!
        if (scannerMode === 'weight') {
          setDetectedValue(`${result.weight_g}g`);
          setScanConfidence(80);
        } else {
          setDetectedValue(result.display_date);
          setScanConfidence(result.confidence === 'high' ? 95 : 70);
        }

        // Count consecutive successful reads (need 2-3 in a row to auto-confirm)
        successCountRef.current += 1;

        if (successCountRef.current >= 2) {
          // AUTO-CONFIRM: Same value detected multiple times
          Vibration.vibrate(100); // Haptic feedback

          if (scannerMode === 'weight') {
            updateUnit(scanningUnitId, 'currentWeight', result.weight_g.toString());
          } else {
            updateUnit(scanningUnitId, 'expiryDate', result.expiry_date);
          }

          // Close scanner with success message
          closeScanner();
          const msg = scannerMode === 'weight'
            ? `Weight: ${result.weight_g}g`
            : `Expiry: ${result.display_date}`;
          Alert.alert('Detected!', msg, [{ text: 'OK' }]);
        }
      } else {
        // Reset success counter if no valid result
        successCountRef.current = 0;
        setDetectedValue(null);
        setScanConfidence(0);
      }
    } catch (error) {
      console.error('Continuous OCR error:', error);
      successCountRef.current = 0;
    } finally {
      setIsScanning(false);
    }
  }, [scannerMode, scanningUnitId, isScanning, closeScanner, packageWeight]);

  // Start/stop continuous scanning when scanner modal opens/closes
  useEffect(() => {
    if (showScanner && permission?.granted) {
      // Start continuous scanning after a brief delay to let camera initialize
      const startDelay = setTimeout(() => {
        scanIntervalRef.current = setInterval(performContinuousScan, 1000);
      }, 500);

      return () => {
        clearTimeout(startDelay);
        if (scanIntervalRef.current) {
          clearInterval(scanIntervalRef.current);
          scanIntervalRef.current = null;
        }
      };
    }
  }, [showScanner, permission?.granted, performContinuousScan]);

  // Manual confirm button (if user wants to accept before auto-confirm)
  const manualConfirm = () => {
    if (detectedValue) {
      Vibration.vibrate(50);
      if (scannerMode === 'weight') {
        const weightMatch = detectedValue.match(/(\d+\.?\d*)/);
        if (weightMatch) {
          updateUnit(scanningUnitId, 'currentWeight', weightMatch[1]);
        }
      } else {
        // Parse the display date back to ISO
        const parts = detectedValue.split('.');
        if (parts.length === 3) {
          const isoDate = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
          updateUnit(scanningUnitId, 'expiryDate', isoDate);
        }
      }
      closeScanner();
    }
  };

  // Calculate fullness percentage from weight
  const getFullnessPercent = (weight) => {
    const currentW = parseFloat(weight) || 0;
    const pkgW = parseFloat(packageWeight) || 1000;
    return Math.min(100, Math.round((currentW / pkgW) * 100));
  };

  // Format date for display (German format)
  const formatDateDisplay = (dateStr) => {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      return `${parts[2]}.${parts[1]}.${parts[0]}`;
    }
    return dateStr;
  };

  // Parse German date input to ISO format
  const parseGermanDate = (input) => {
    // Try DD.MM.YYYY or DD.MM.YY
    const match = input.match(/^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$/);
    if (match) {
      let [, day, month, year] = match;
      if (year.length === 2) {
        year = '20' + year;
      }
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    return input; // Return as-is if not German format
  };

  const addToInventory = async (productId) => {
    try {
      // Add each unit separately
      const pkgWeight = parseFloat(packageWeight) || 1000;

      for (const unit of units) {
        // Use currentWeight if set, otherwise assume full package
        const currentWeight = unit.currentWeight
          ? parseFloat(unit.currentWeight)
          : pkgWeight;

        await fetch(`${API_BASE_URL}/api/pantry/inventory`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            product_id: productId,
            location: location,
            current_weight_g: currentWeight,
            expiry_date: unit.expiryDate || null,
            is_opened: unit.isOpened ? 1 : 0,
          }),
        });
      }

      Alert.alert(
        'Success',
        `Added ${units.length} unit${units.length > 1 ? 's' : ''} to inventory!`,
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to add item to inventory');
    }
  };

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a product name');
      return;
    }

    try {
      // If we have an existing product ID, just add units
      if (existingProductId) {
        await addToInventory(existingProductId);
        return;
      }

      // First create/update the product
      const productData = {
        barcode: barcode || product?.barcode || null,
        name: name.trim(),
        brand: brand.trim(),
        category: category,
        storage_type: location,
        image_url: imageUrl,
        calories: parseFloat(calories) || 0,
        protein: parseFloat(protein) || 0,
        carbs: parseFloat(carbs) || 0,
        fat: parseFloat(fat) || 0,
        fiber: parseFloat(fiber) || 0,
        sodium: parseFloat(sodium) || 0,
        sugar: parseFloat(sugar) || 0,
        package_weight_g: packageWeight ? parseFloat(packageWeight) : null,
        price: price ? parseFloat(price) : null,
        price_source: price ? 'manual' : null,
        data_source: product?.source || 'manual',
      };

      const productResponse = await fetch(`${API_BASE_URL}/api/pantry/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(productData),
      });

      const productResult = await productResponse.json();

      if (!productResponse.ok && productResult.product_id) {
        // Product exists, use existing ID
        await addToInventory(productResult.product_id);
      } else if (productResponse.ok) {
        // New product created, add to inventory
        await addToInventory(productResult.product_id);
      } else {
        Alert.alert('Error', productResult.error || 'Failed to save product');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save product');
    }
  };

  const LocationButton = ({ value, label, emoji }) => (
    <TouchableOpacity
      style={[
        styles.locationButton,
        location === value && styles.locationButtonActive,
      ]}
      onPress={() => setLocation(value)}
    >
      <Text style={styles.locationEmoji}>{emoji}</Text>
      <Text
        style={[
          styles.locationLabel,
          location === value && styles.locationLabelActive,
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );

  // Fullness slider component
  const FullnessSlider = ({ value, onChange }) => {
    const levels = [0, 25, 50, 75, 100];
    const emojis = ['🫙', '🫙', '🥛', '🥛', '🥛'];
    const fills = ['empty', 'quarter', 'half', 'three-quarter', 'full'];

    return (
      <View style={styles.fullnessContainer}>
        <View style={styles.fullnessBar}>
          {levels.map((level, index) => (
            <TouchableOpacity
              key={level}
              style={[
                styles.fullnessSegment,
                value >= level && styles.fullnessSegmentActive,
                index === 0 && styles.fullnessSegmentFirst,
                index === levels.length - 1 && styles.fullnessSegmentLast,
              ]}
              onPress={() => onChange(level)}
            />
          ))}
        </View>
        <Text style={styles.fullnessText}>{value}% full</Text>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView style={styles.scrollView} keyboardShouldPersistTaps="handled">
        {/* Product Image */}
        {imageUrl ? (
          <Image source={{ uri: imageUrl }} style={styles.productImage} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.imagePlaceholderEmoji}>📦</Text>
          </View>
        )}

        {/* Barcode */}
        {(barcode || product?.barcode) && (
          <Text style={styles.barcodeText}>
            Barcode: {barcode || product?.barcode}
          </Text>
        )}

        {/* Name with autocomplete */}
        <View style={styles.field}>
          <Text style={styles.label}>Product Name *</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={handleNameChange}
            placeholder="Enter product name"
          />
          {showResults && searchResults.length > 0 && (
            <View style={styles.autocompleteResults}>
              {searchResults.slice(0, 5).map((item, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.autocompleteItem}
                  onPress={() => handleSelectResult(item)}
                >
                  <Text style={styles.autocompleteText}>{item.name}</Text>
                  {item.brand && (
                    <Text style={styles.autocompleteBrand}>{item.brand}</Text>
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {/* Brand */}
        <View style={styles.field}>
          <Text style={styles.label}>Brand</Text>
          <TextInput
            style={styles.input}
            value={brand}
            onChangeText={setBrand}
            placeholder="Brand name"
          />
        </View>

        {/* Location selector */}
        <View style={styles.field}>
          <Text style={styles.label}>Storage Location</Text>
          <View style={styles.locationRow}>
            <LocationButton value="pantry" label="Pantry" emoji="🥫" />
            <LocationButton value="spice_rack" label="Spices" emoji="🌶️" />
            <LocationButton value="fridge" label="Fridge" emoji="🧊" />
            <LocationButton value="freezer" label="Freezer" emoji="❄️" />
          </View>
        </View>

        {/* Weight & Price row */}
        <View style={styles.row}>
          <View style={[styles.field, { flex: 1, marginRight: 8 }]}>
            <Text style={styles.label}>Package Size (g/ml)</Text>
            <TextInput
              style={styles.input}
              value={packageWeight}
              onChangeText={setPackageWeight}
              placeholder="e.g., 1000"
              keyboardType="numeric"
            />
          </View>
          <View style={[styles.field, { flex: 1, marginLeft: 8 }]}>
            <Text style={styles.label}>Price (€)</Text>
            <TextInput
              style={styles.input}
              value={price}
              onChangeText={setPrice}
              placeholder="e.g., 1.29"
              keyboardType="decimal-pad"
            />
          </View>
        </View>

        {/* UNITS SECTION */}
        <View style={styles.unitsSection}>
          <View style={styles.unitsSectionHeader}>
            <Text style={styles.sectionTitle}>Units ({units.length})</Text>
            <TouchableOpacity style={styles.addUnitButton} onPress={addUnit}>
              <Text style={styles.addUnitButtonText}>+ Add Unit</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.unitsHint}>
            Add multiple cartons/packages with different fill levels and expiry dates
          </Text>

          {units.map((unit, index) => (
            <View key={unit.id} style={styles.unitCard}>
              <View style={styles.unitHeader}>
                <Text style={styles.unitTitle}>Unit {index + 1}</Text>
                {units.length > 1 && (
                  <TouchableOpacity
                    style={styles.removeUnitButton}
                    onPress={() => removeUnit(unit.id)}
                  >
                    <Text style={styles.removeUnitButtonText}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>

              {/* Weight Input with Scale Scanner */}
              <View style={styles.unitField}>
                <Text style={styles.unitFieldLabel}>Current Weight (g)</Text>
                <View style={styles.weightRow}>
                  <TextInput
                    style={[styles.input, styles.weightInput]}
                    value={unit.currentWeight}
                    onChangeText={(text) => updateUnit(unit.id, 'currentWeight', text)}
                    placeholder={packageWeight ? `Full = ${packageWeight}g` : 'Enter weight'}
                    keyboardType="numeric"
                  />
                  <TouchableOpacity
                    style={styles.scanWeightButton}
                    onPress={() => openScanner(unit.id, 'weight')}
                  >
                    <Text style={styles.scanWeightButtonText}>⚖️ Scan Scale</Text>
                  </TouchableOpacity>
                </View>
                {/* Show fullness percentage if weight is entered and package weight is known */}
                {unit.currentWeight && packageWeight && (
                  <View style={styles.fullnessDisplay}>
                    <View style={styles.fullnessBarContainer}>
                      <View
                        style={[
                          styles.fullnessBarFill,
                          { width: `${Math.min(100, getFullnessPercent(unit.currentWeight))}%` }
                        ]}
                      />
                    </View>
                    <Text style={styles.fullnessPercentText}>
                      {getFullnessPercent(unit.currentWeight)}% full
                    </Text>
                  </View>
                )}
              </View>

              {/* Expiry Date with Scanner */}
              <View style={styles.unitField}>
                <Text style={styles.unitFieldLabel}>Expiry Date</Text>
                <View style={styles.expiryRow}>
                  <TextInput
                    style={[styles.input, styles.expiryInput]}
                    value={formatDateDisplay(unit.expiryDate)}
                    onChangeText={(text) => {
                      const isoDate = parseGermanDate(text);
                      updateUnit(unit.id, 'expiryDate', isoDate);
                    }}
                    placeholder="TT.MM.JJJJ"
                    keyboardType="numeric"
                  />
                  <TouchableOpacity
                    style={styles.scanExpiryButton}
                    onPress={() => openScanner(unit.id, 'expiry')}
                  >
                    <Text style={styles.scanExpiryButtonText}>📷 Scan</Text>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Is Opened Toggle */}
              <TouchableOpacity
                style={styles.openedToggle}
                onPress={() => updateUnit(unit.id, 'isOpened', !unit.isOpened)}
              >
                <View style={[styles.checkbox, unit.isOpened && styles.checkboxChecked]}>
                  {unit.isOpened && <Text style={styles.checkmark}>✓</Text>}
                </View>
                <Text style={styles.openedLabel}>Already opened</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* Nutrition section */}
        <Text style={styles.sectionTitle}>Nutrition (per 100g)</Text>

        <View style={styles.nutritionGrid}>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Calories</Text>
            <TextInput
              style={styles.nutritionInput}
              value={calories}
              onChangeText={setCalories}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Protein (g)</Text>
            <TextInput
              style={styles.nutritionInput}
              value={protein}
              onChangeText={setProtein}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Carbs (g)</Text>
            <TextInput
              style={styles.nutritionInput}
              value={carbs}
              onChangeText={setCarbs}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Fat (g)</Text>
            <TextInput
              style={styles.nutritionInput}
              value={fat}
              onChangeText={setFat}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Fiber (g)</Text>
            <TextInput
              style={styles.nutritionInput}
              value={fiber}
              onChangeText={setFiber}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Sodium (mg)</Text>
            <TextInput
              style={styles.nutritionInput}
              value={sodium}
              onChangeText={setSodium}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionLabel}>Sugar (g)</Text>
            <TextInput
              style={styles.nutritionInput}
              value={sugar}
              onChangeText={setSugar}
              keyboardType="numeric"
            />
          </View>
        </View>

        {/* Save button */}
        <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
          <Text style={styles.saveButtonText}>
            Save {units.length} Unit{units.length > 1 ? 's' : ''} to {location === 'spice_rack' ? 'Spice Rack' : location.charAt(0).toUpperCase() + location.slice(1)}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Continuous OCR Scanner Modal - Google Translate style */}
      <Modal
        visible={showScanner}
        animationType="slide"
        onRequestClose={closeScanner}
      >
        <View style={styles.scannerContainer}>
          <View style={styles.scannerHeader}>
            <TouchableOpacity onPress={closeScanner}>
              <Text style={styles.scannerCloseText}>✕ Close</Text>
            </TouchableOpacity>
            <Text style={styles.scannerTitle}>
              {scannerMode === 'weight' ? '⚖️ Scale Scanner' : '📅 Date Scanner'}
            </Text>
            <View style={{ width: 60 }} />
          </View>

          {permission?.granted ? (
            <View style={styles.cameraContainer}>
              {/* Camera - no children allowed */}
              <CameraView
                ref={cameraRef}
                style={styles.camera}
                facing="back"
              />

              {/* Overlay positioned absolutely on top of camera */}
              <View style={styles.scannerOverlay} pointerEvents="none">
                {/* Detected text boxes - highlight what OCR sees */}
                {detectedBoxes.map((box, idx) => (
                  <View
                    key={idx}
                    style={[
                      styles.detectedBox,
                      {
                        left: `${box.x_pct}%`,
                        top: `${box.y_pct}%`,
                        width: `${Math.max(box.w_pct, 5)}%`,
                        height: `${Math.max(box.h_pct, 3)}%`,
                      },
                      box.conf > 70 && styles.detectedBoxHighConf,
                    ]}
                  >
                    <View style={styles.detectedBoxLabel}>
                      <Text style={styles.detectedBoxText}>{box.text}</Text>
                    </View>
                  </View>
                ))}

                {/* Scanner guide frame */}
                <View style={[
                  styles.scannerFrame,
                  scannerMode === 'weight' && styles.scannerFrameWeight,
                  detectedValue && styles.scannerFrameSuccess,
                ]}>
                  {!detectedValue ? (
                    <Text style={styles.scannerHint}>
                      {scannerMode === 'weight'
                        ? 'Point at the scale display'
                        : 'Point at the expiry date\n(MHD / Haltbar bis)'}
                    </Text>
                  ) : (
                    <View style={styles.detectedValueContainer}>
                      <Text style={styles.detectedValueLabel}>DETECTED:</Text>
                      <Text style={styles.detectedValueText}>{detectedValue}</Text>
                      <Text style={styles.detectedConfidence}>
                        Confidence: {scanConfidence}%
                      </Text>
                    </View>
                  )}
                </View>
              </View>

              {/* Scanning indicator */}
              {isScanning && (
                <View style={styles.scanningIndicator}>
                  <ActivityIndicator color="#4CAF50" size="small" />
                  <Text style={styles.scanningText}>Scanning...</Text>
                </View>
              )}
            </View>
          ) : (
            <View style={styles.permissionContainer}>
              <Text style={styles.permissionText}>Camera permission needed</Text>
              <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
                <Text style={styles.permissionButtonText}>Grant Permission</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Bottom panel showing status and manual confirm option */}
          <View style={styles.scannerBottomPanel}>
            {detectedValue ? (
              <>
                <Text style={styles.bottomPanelText}>
                  Hold steady to auto-confirm or tap below
                </Text>
                <TouchableOpacity
                  style={styles.confirmButton}
                  onPress={manualConfirm}
                >
                  <Text style={styles.confirmButtonText}>
                    Use {detectedValue}
                  </Text>
                </TouchableOpacity>
              </>
            ) : (
              <>
                <Text style={styles.bottomPanelText}>
                  {scannerMode === 'weight'
                    ? 'Looking for numbers on scale display...'
                    : 'Looking for date format: DD.MM.YYYY or MM/YYYY'}
                </Text>
                {rawOcrText ? (
                  <Text style={styles.rawOcrPreview}>
                    Seeing: {rawOcrText.slice(0, 40)}...
                  </Text>
                ) : null}
              </>
            )}
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  productImage: {
    width: '100%',
    height: 200,
    resizeMode: 'contain',
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 16,
  },
  imagePlaceholder: {
    width: '100%',
    height: 150,
    backgroundColor: '#fff',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  imagePlaceholderEmoji: {
    fontSize: 60,
  },
  barcodeText: {
    textAlign: 'center',
    color: '#666',
    marginBottom: 16,
    fontSize: 12,
  },
  field: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  row: {
    flexDirection: 'row',
    marginBottom: 0,
  },
  locationRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  locationButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingVertical: 12,
    marginHorizontal: 4,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e0e0e0',
  },
  locationButtonActive: {
    borderColor: '#4CAF50',
    backgroundColor: '#e8f5e9',
  },
  locationEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  locationLabel: {
    fontSize: 11,
    color: '#666',
  },
  locationLabelActive: {
    color: '#4CAF50',
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginTop: 8,
    marginBottom: 12,
  },

  // Units Section
  unitsSection: {
    marginTop: 16,
    marginBottom: 16,
  },
  unitsSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  unitsHint: {
    fontSize: 12,
    color: '#888',
    marginBottom: 12,
  },
  addUnitButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  addUnitButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  unitCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  unitHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  unitTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
  },
  removeUnitButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#ffebee',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeUnitButtonText: {
    color: '#e53935',
    fontSize: 14,
    fontWeight: '600',
  },
  unitField: {
    marginBottom: 12,
  },
  unitFieldLabel: {
    fontSize: 13,
    color: '#666',
    marginBottom: 6,
  },

  // Fullness Slider
  fullnessContainer: {
    alignItems: 'center',
  },
  fullnessBar: {
    flexDirection: 'row',
    height: 36,
    borderRadius: 8,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  fullnessSegment: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRightWidth: 1,
    borderRightColor: '#e0e0e0',
  },
  fullnessSegmentFirst: {
    borderTopLeftRadius: 7,
    borderBottomLeftRadius: 7,
  },
  fullnessSegmentLast: {
    borderRightWidth: 0,
    borderTopRightRadius: 7,
    borderBottomRightRadius: 7,
  },
  fullnessSegmentActive: {
    backgroundColor: '#4CAF50',
  },
  fullnessText: {
    marginTop: 6,
    fontSize: 13,
    color: '#4CAF50',
    fontWeight: '600',
  },

  // Weight Row (with scale scanner)
  weightRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  weightInput: {
    flex: 1,
    marginRight: 8,
  },
  scanWeightButton: {
    backgroundColor: '#FF9800',
    paddingHorizontal: 12,
    paddingVertical: 12,
    borderRadius: 8,
  },
  scanWeightButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },

  // Fullness Display (calculated from weight)
  fullnessDisplay: {
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  fullnessBarContainer: {
    flex: 1,
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    marginRight: 10,
    overflow: 'hidden',
  },
  fullnessBarFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 4,
  },
  fullnessPercentText: {
    fontSize: 13,
    color: '#4CAF50',
    fontWeight: '600',
    width: 70,
    textAlign: 'right',
  },

  // Expiry Row
  expiryRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  expiryInput: {
    flex: 1,
    marginRight: 8,
  },
  scanExpiryButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 8,
  },
  scanExpiryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },

  // Opened Toggle
  openedToggle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#ccc',
    marginRight: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  checkmark: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },
  openedLabel: {
    fontSize: 14,
    color: '#555',
  },

  // Nutrition
  nutritionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -4,
  },
  nutritionItem: {
    width: '33.33%',
    paddingHorizontal: 4,
    marginBottom: 12,
  },
  nutritionLabel: {
    fontSize: 11,
    color: '#666',
    marginBottom: 4,
  },
  nutritionInput: {
    backgroundColor: '#fff',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 14,
    textAlign: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  autocompleteResults: {
    backgroundColor: '#fff',
    borderRadius: 8,
    marginTop: 4,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    maxHeight: 200,
  },
  autocompleteItem: {
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  autocompleteText: {
    fontSize: 14,
    color: '#333',
  },
  autocompleteBrand: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  saveButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 40,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },

  // Scanner Modal
  scannerContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  scannerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 50,
    backgroundColor: '#1a1a2e',
  },
  scannerCloseText: {
    color: '#fff',
    fontSize: 16,
  },
  scannerTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  camera: {
    flex: 1,
  },
  scannerOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scannerFrame: {
    width: 280,
    height: 150,
    borderWidth: 3,
    borderColor: '#4CAF50',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  scannerFrameWeight: {
    borderColor: '#FF9800',
    width: 220,
    height: 120,
  },
  scannerFrameSuccess: {
    borderColor: '#00E676',
    borderWidth: 4,
    backgroundColor: 'rgba(0,230,118,0.2)',
  },
  scannerHint: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
  },

  // Detected text boxes overlay (Google Translate style)
  detectedBox: {
    position: 'absolute',
    borderWidth: 2,
    borderColor: 'rgba(76, 175, 80, 0.7)',
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 4,
  },
  detectedBoxHighConf: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.4)',
  },
  detectedBoxLabel: {
    position: 'absolute',
    bottom: -18,
    left: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 2,
  },
  detectedBoxText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
  },

  // Detected value display
  detectedValueContainer: {
    alignItems: 'center',
    padding: 10,
  },
  detectedValueLabel: {
    color: '#00E676',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  detectedValueText: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '700',
  },
  detectedConfidence: {
    color: '#aaa',
    fontSize: 12,
    marginTop: 4,
  },

  // Scanning indicator
  scanningIndicator: {
    position: 'absolute',
    top: 20,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  scanningText: {
    color: '#4CAF50',
    fontSize: 12,
    marginLeft: 6,
  },

  // Bottom panel
  scannerBottomPanel: {
    backgroundColor: '#1a1a2e',
    padding: 20,
    alignItems: 'center',
    minHeight: 120,
  },
  bottomPanelText: {
    color: '#aaa',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
  },
  rawOcrPreview: {
    color: '#666',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    marginTop: 8,
  },
  confirmButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 30,
    paddingVertical: 14,
    borderRadius: 10,
    marginTop: 8,
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },

  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  permissionText: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 20,
    textAlign: 'center',
  },
  permissionButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
