import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import { API_BASE_URL } from '../config';

// Store brand colors
const STORE_COLORS = {
  aldi: {
    primary: '#00005f',
    secondary: '#f9dc00',
    text: '#ffffff',
    name: 'ALDI',
  },
  lidl: {
    primary: '#0050aa',
    secondary: '#fff000',
    text: '#ffffff',
    name: 'Lidl',
  },
  rewe: {
    primary: '#cc0000',
    secondary: '#ffffff',
    text: '#ffffff',
    name: 'REWE',
  },
  edeka: {
    primary: '#0050aa',
    secondary: '#ffcc00',
    text: '#ffffff',
    name: 'EDEKA',
  },
  default: {
    primary: '#4CAF50',
    secondary: '#ffffff',
    text: '#ffffff',
    name: '',
  },
};

const getStoreColors = (store) => {
  if (!store) return STORE_COLORS.default;
  return STORE_COLORS[store.toLowerCase()] || STORE_COLORS.default;
};

const getCategoryEmoji = (category, location) => {
  if (location === 'spice_rack') return '🌶️';
  const emojis = {
    dairy: '🥛',
    meat: '🥩',
    produce: '🥬',
    grain: '🌾',
    pantry: '🥫',
    beverage: '🧃',
    frozen: '🧊',
    bakery: '🍞',
    spice: '🌶️',
  };
  return emojis[category?.toLowerCase()] || '📦';
};

export default function ProductDetailScreen({ route, navigation }) {
  const { inventory, productId } = route.params || {};
  const [item, setItem] = useState(inventory || null);
  const [currentWeight, setCurrentWeight] = useState(
    inventory?.current_weight_g?.toString() || ''
  );
  const [editing, setEditing] = useState(false);

  const storeColors = getStoreColors(item?.store);

  useEffect(() => {
    if (productId && !item) {
      fetchProduct();
    }
  }, [productId]);

  const fetchProduct = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pantry/inventory`);
      const data = await response.json();
      const found = data.find((i) => i.product_id === productId);
      if (found) {
        setItem(found);
        setCurrentWeight(found.current_weight_g?.toString() || '');
      }
    } catch (error) {
      console.error('Failed to fetch product:', error);
    }
  };

  const handleUpdateWeight = async () => {
    if (!item) return;

    try {
      await fetch(`${API_BASE_URL}/api/pantry/inventory/${item.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_weight_g: currentWeight ? parseFloat(currentWeight) : null,
        }),
      });
      setEditing(false);
      Alert.alert('Updated', 'Weight updated successfully');
      // Refresh item
      if (item.current_weight_g !== null) {
        setItem({
          ...item,
          current_weight_g: parseFloat(currentWeight),
          percent_remaining: item.package_weight_g
            ? (parseFloat(currentWeight) / item.package_weight_g) * 100
            : null,
        });
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to update weight');
    }
  };

  const handleMarkEmpty = async () => {
    Alert.alert(
      'Mark as Empty',
      'This will remove the item from your inventory. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await fetch(`${API_BASE_URL}/api/pantry/inventory/${item.id}`, {
                method: 'DELETE',
              });
              navigation.goBack();
            } catch (error) {
              Alert.alert('Error', 'Failed to remove item');
            }
          },
        },
      ]
    );
  };

  const getStockColor = (percent) => {
    if (percent === null || percent === undefined) return '#9e9e9e';
    if (percent <= 25) return '#f44336';
    if (percent <= 50) return '#ff9800';
    return '#4CAF50';
  };

  const formatWeight = (grams) => {
    if (!grams) return 'Not set';
    if (grams >= 1000) return `${(grams / 1000).toFixed(1)}kg`;
    return `${Math.round(grams)}g`;
  };

  if (!item) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  const stockPercent = item.percent_remaining;
  const currency = item.currency === 'EUR' ? '€' : '$';

  return (
    <ScrollView style={styles.container}>
      {/* Store branded header */}
      {item.store && (
        <View style={[styles.storeHeader, { backgroundColor: storeColors.primary }]}>
          <Text style={[styles.storeHeaderText, { color: storeColors.text }]}>
            {storeColors.name}
          </Text>
          {item.price_per_kg && (
            <Text style={[styles.pricePerKg, { color: storeColors.text }]}>
              {currency}{item.price_per_kg.toFixed(2)}/kg
            </Text>
          )}
        </View>
      )}

      {/* Product Image */}
      {item.image_url ? (
        <Image source={{ uri: item.image_url }} style={styles.productImage} />
      ) : (
        <View style={[
          styles.imagePlaceholder,
          item.store && { borderTopColor: storeColors.primary, borderTopWidth: 4 }
        ]}>
          <Text style={styles.placeholderEmoji}>
            {getCategoryEmoji(item.category, item.location)}
          </Text>
        </View>
      )}

      {/* Product Info */}
      <View style={styles.infoSection}>
        <View style={styles.nameRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.productName}>{item.name}</Text>
            {item.brand && (
              <View style={styles.brandRow}>
                {item.store && (
                  <View style={[styles.brandDot, { backgroundColor: storeColors.primary }]} />
                )}
                <Text style={[
                  styles.brandName,
                  item.store && { color: storeColors.primary }
                ]}>
                  {item.brand}
                </Text>
              </View>
            )}
          </View>
          {item.price && (
            <View style={[styles.priceBadge, { backgroundColor: storeColors.primary }]}>
              <Text style={[styles.priceText, { color: storeColors.text }]}>
                {currency}{item.price.toFixed(2)}
              </Text>
            </View>
          )}
        </View>

        {/* Category & Storage badges */}
        <View style={styles.badgeRow}>
          {item.category && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{item.category}</Text>
            </View>
          )}
          {item.subcategory && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{item.subcategory}</Text>
            </View>
          )}
          {item.storage_type && (
            <View style={[styles.badge, { backgroundColor: '#e3f2fd' }]}>
              <Text style={[styles.badgeText, { color: '#1976d2' }]}>{item.storage_type}</Text>
            </View>
          )}
        </View>

        {item.barcode && (
          <Text style={styles.barcode}>Barcode: {item.barcode}</Text>
        )}
      </View>

      {/* Stock Level Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Stock Level</Text>

        {stockPercent !== null && stockPercent !== undefined ? (
          <>
            <View style={styles.stockBarLarge}>
              <View
                style={[
                  styles.stockFill,
                  {
                    width: `${Math.min(100, Math.max(0, stockPercent))}%`,
                    backgroundColor: getStockColor(stockPercent),
                  },
                ]}
              />
            </View>
            <Text style={[styles.stockPercent, { color: getStockColor(stockPercent) }]}>
              {Math.round(stockPercent)}% remaining
            </Text>
          </>
        ) : (
          <Text style={styles.noData}>No weight tracking</Text>
        )}

        {/* Weight editor */}
        <View style={styles.weightRow}>
          <Text style={styles.weightLabel}>Current Weight:</Text>
          {editing ? (
            <View style={styles.editRow}>
              <TextInput
                style={styles.weightInput}
                value={currentWeight}
                onChangeText={setCurrentWeight}
                keyboardType="numeric"
                placeholder="grams"
              />
              <TouchableOpacity
                style={[styles.saveBtn, { backgroundColor: storeColors.primary }]}
                onPress={handleUpdateWeight}
              >
                <Text style={styles.saveBtnText}>Save</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity onPress={() => setEditing(true)}>
              <Text style={styles.weightValue}>
                {formatWeight(item.current_weight_g)}{' '}
                <Text style={[styles.editLink, { color: storeColors.primary }]}>Edit</Text>
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {item.package_weight_g && (
          <Text style={styles.packageWeight}>
            Package size: {formatWeight(item.package_weight_g)}
            {item.package_unit && ` (${item.package_unit})`}
          </Text>
        )}
      </View>

      {/* Nutrition Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Nutrition (per 100g)</Text>

        <View style={styles.nutritionGrid}>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionValue}>{item.calories || 0}</Text>
            <Text style={styles.nutritionLabel}>Calories</Text>
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionValue}>{item.protein || 0}g</Text>
            <Text style={styles.nutritionLabel}>Protein</Text>
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionValue}>{item.carbs || 0}g</Text>
            <Text style={styles.nutritionLabel}>Carbs</Text>
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionValue}>{item.fat || 0}g</Text>
            <Text style={styles.nutritionLabel}>Fat</Text>
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionValue}>{item.fiber || 0}g</Text>
            <Text style={styles.nutritionLabel}>Fiber</Text>
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionValue}>{item.sodium || 0}mg</Text>
            <Text style={styles.nutritionLabel}>Sodium</Text>
          </View>
          <View style={styles.nutritionItem}>
            <Text style={styles.nutritionValue}>{item.sugar || 0}g</Text>
            <Text style={styles.nutritionLabel}>Sugar</Text>
          </View>
          {item.saturated_fat > 0 && (
            <View style={styles.nutritionItem}>
              <Text style={styles.nutritionValue}>{item.saturated_fat}g</Text>
              <Text style={styles.nutritionLabel}>Sat. Fat</Text>
            </View>
          )}
        </View>
      </View>

      {/* Price & Details Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Details</Text>

        {item.store && (
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Store:</Text>
            <View style={[styles.storeTag, { backgroundColor: storeColors.primary }]}>
              <Text style={[styles.storeTagText, { color: storeColors.text }]}>
                {storeColors.name}
              </Text>
            </View>
          </View>
        )}

        {item.price && (
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Price:</Text>
            <Text style={[styles.detailValue, { color: storeColors.primary, fontWeight: '700' }]}>
              {currency}{item.price.toFixed(2)}
            </Text>
          </View>
        )}

        {item.price_per_kg && (
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Price/kg:</Text>
            <Text style={styles.detailValue}>{currency}{item.price_per_kg.toFixed(2)}</Text>
          </View>
        )}

        {item.expiry_date && (
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Expires:</Text>
            <Text style={styles.detailValue}>{item.expiry_date}</Text>
          </View>
        )}

        {item.purchase_date && (
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Purchased:</Text>
            <Text style={styles.detailValue}>{item.purchase_date}</Text>
          </View>
        )}

        {item.location && (
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Location:</Text>
            <Text style={styles.detailValue}>{item.location.replace('_', ' ')}</Text>
          </View>
        )}
      </View>

      {/* Quick Actions */}
      <View style={styles.actionsRow}>
        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: storeColors.primary }]}
          onPress={() => {
            const newWeight = Math.max(
              0,
              (parseFloat(currentWeight) || item.current_weight_g || 0) -
                (item.serving_size_g || 30)
            );
            setCurrentWeight(newWeight.toString());
            handleUpdateWeight();
          }}
        >
          <Text style={styles.actionButtonText}>Use Serving</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.emptyButton]}
          onPress={handleMarkEmpty}
        >
          <Text style={styles.actionButtonText}>Mark Empty</Text>
        </TouchableOpacity>
      </View>

      {/* Bottom padding */}
      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#666',
  },
  storeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  storeHeaderText: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
  },
  pricePerKg: {
    fontSize: 12,
    opacity: 0.9,
  },
  productImage: {
    width: '100%',
    height: 220,
    resizeMode: 'contain',
    backgroundColor: '#fff',
  },
  imagePlaceholder: {
    width: '100%',
    height: 180,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderEmoji: {
    fontSize: 80,
  },
  infoSection: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  productName: {
    fontSize: 22,
    fontWeight: '700',
    color: '#333',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  brandDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  brandName: {
    fontSize: 16,
    color: '#666',
  },
  priceBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    marginLeft: 12,
  },
  priceText: {
    fontSize: 18,
    fontWeight: '700',
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 12,
  },
  badge: {
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    fontSize: 12,
    color: '#666',
    textTransform: 'capitalize',
  },
  barcode: {
    fontSize: 12,
    color: '#999',
    marginTop: 12,
  },
  card: {
    backgroundColor: '#fff',
    margin: 12,
    marginBottom: 0,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginBottom: 12,
  },
  stockBarLarge: {
    height: 16,
    backgroundColor: '#e0e0e0',
    borderRadius: 8,
    overflow: 'hidden',
  },
  stockFill: {
    height: '100%',
    borderRadius: 8,
  },
  stockPercent: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 8,
  },
  noData: {
    color: '#999',
    textAlign: 'center',
  },
  weightRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  weightLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  weightValue: {
    fontSize: 14,
    color: '#333',
  },
  editLink: {
    fontWeight: '600',
  },
  editRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  weightInput: {
    backgroundColor: '#f5f5f5',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    fontSize: 14,
    width: 80,
    marginRight: 8,
  },
  saveBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  saveBtnText: {
    color: '#fff',
    fontWeight: '600',
  },
  packageWeight: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
  },
  nutritionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  nutritionItem: {
    width: '25%',
    alignItems: 'center',
    marginBottom: 12,
  },
  nutritionValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
  },
  nutritionLabel: {
    fontSize: 11,
    color: '#888',
    marginTop: 2,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    textTransform: 'capitalize',
  },
  storeTag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
  },
  storeTagText: {
    fontSize: 12,
    fontWeight: '600',
  },
  actionsRow: {
    flexDirection: 'row',
    padding: 12,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  emptyButton: {
    backgroundColor: '#f44336',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
