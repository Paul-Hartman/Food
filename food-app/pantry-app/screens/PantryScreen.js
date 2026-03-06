import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  RefreshControl,
  Alert,
  Animated,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { API_BASE_URL } from '../config';

// Store brand colors
const STORE_COLORS = {
  aldi: {
    primary: '#00005f',
    secondary: '#f9dc00',
    accent: '#e30613',
    text: '#ffffff',
  },
  lidl: {
    primary: '#0050aa',
    secondary: '#fff000',
    accent: '#e30613',
    text: '#ffffff',
  },
  rewe: {
    primary: '#cc0000',
    secondary: '#ffffff',
    accent: '#333333',
    text: '#ffffff',
  },
  edeka: {
    primary: '#0050aa',
    secondary: '#ffcc00',
    accent: '#000000',
    text: '#ffffff',
  },
  default: {
    primary: '#4CAF50',
    secondary: '#ffffff',
    accent: '#333333',
    text: '#ffffff',
  },
};

const getStoreColors = (store) => {
  if (!store) return STORE_COLORS.default;
  return STORE_COLORS[store.toLowerCase()] || STORE_COLORS.default;
};

const getStoreDisplayName = (store) => {
  if (!store) return '';
  const names = {
    aldi: 'ALDI',
    lidl: 'Lidl',
    rewe: 'REWE',
    edeka: 'EDEKA',
  };
  return names[store.toLowerCase()] || store.toUpperCase();
};

const getCategoryEmoji = (category) => {
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

const getStockColor = (percent) => {
  if (percent === null || percent === undefined) return '#9e9e9e';
  if (percent <= 25) return '#f44336';
  if (percent <= 50) return '#ff9800';
  return '#4CAF50';
};

const formatWeight = (grams) => {
  if (!grams) return '';
  return grams >= 1000
    ? `${(grams / 1000).toFixed(1)}kg`
    : `${Math.round(grams)}g`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const parts = dateStr.split('-');
  if (parts.length === 3) {
    return `${parts[2]}.${parts[1]}.${parts[0]}`;
  }
  return dateStr;
};

// Product card with expandable units
const ProductCard = ({ product, navigation, onDeleteUnit, onRefresh }) => {
  const [expanded, setExpanded] = useState(false);
  const [animation] = useState(new Animated.Value(0));

  const toggleExpand = () => {
    const toValue = expanded ? 0 : 1;
    Animated.timing(animation, {
      toValue,
      duration: 200,
      useNativeDriver: false,
    }).start();
    setExpanded(!expanded);
  };

  const storeColors = getStoreColors(product.brand?.toLowerCase().includes('aldi') ? 'aldi' :
    product.brand?.toLowerCase().includes('lidl') ? 'lidl' :
    product.brand?.toLowerCase().includes('rewe') ? 'rewe' : null);

  // Calculate total fullness percentage across all units
  const totalPossible = product.package_weight_g * product.unit_count;
  const totalFullnessPercent = totalPossible > 0
    ? Math.round((product.total_weight_g / totalPossible) * 100)
    : 0;

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={toggleExpand}
      activeOpacity={0.8}
    >
      {/* Product Image */}
      <View style={styles.cardImage}>
        {product.image_url ? (
          <Image source={{ uri: product.image_url }} style={styles.image} />
        ) : (
          <Text style={styles.placeholderEmoji}>
            {getCategoryEmoji(product.category)}
          </Text>
        )}

        {/* Unit count badge */}
        <View style={styles.unitCountBadge}>
          <Text style={styles.unitCountText}>{product.unit_count}x</Text>
        </View>

        {/* Expiry warning */}
        {product.has_expired && (
          <View style={[styles.expiryBadge, styles.expiredBadge]}>
            <Text style={styles.expiryBadgeText}>EXPIRED</Text>
          </View>
        )}
        {!product.has_expired && product.expires_soon && (
          <View style={[styles.expiryBadge, styles.expiringSoonBadge]}>
            <Text style={styles.expiryBadgeText}>EXPIRING</Text>
          </View>
        )}
      </View>

      <View style={styles.cardBody}>
        {/* Brand */}
        {product.brand && (
          <Text style={styles.itemBrand} numberOfLines={1}>{product.brand}</Text>
        )}

        {/* Product name */}
        <Text style={styles.itemName} numberOfLines={2}>{product.product_name}</Text>

        {/* Total quantity display */}
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total:</Text>
          <Text style={styles.totalWeight}>{formatWeight(product.total_weight_g)}</Text>
        </View>

        {/* Aggregated fullness bar */}
        <View style={styles.stockContainer}>
          <View style={styles.stockBar}>
            <View
              style={[
                styles.stockFill,
                {
                  width: `${Math.min(100, totalFullnessPercent)}%`,
                  backgroundColor: getStockColor(totalFullnessPercent),
                },
              ]}
            />
          </View>
          <Text style={[styles.stockPercent, { color: getStockColor(totalFullnessPercent) }]}>
            {totalFullnessPercent}%
          </Text>
        </View>

        {/* Expand indicator */}
        <View style={styles.expandRow}>
          <Text style={styles.expandHint}>
            {expanded ? '▲ Hide units' : '▼ Show units'}
          </Text>
        </View>

        {/* Expanded unit cards */}
        {expanded && (
          <View style={styles.unitsContainer}>
            {product.units.map((unit, index) => (
              <View key={unit.unit_id} style={styles.unitCard}>
                <View style={styles.unitHeader}>
                  <Text style={styles.unitLabel}>Unit {index + 1}</Text>
                  {unit.is_opened ? (
                    <Text style={styles.openedBadge}>OPENED</Text>
                  ) : null}
                </View>

                {/* Unit fullness bar */}
                <View style={styles.unitFullnessRow}>
                  <View style={styles.unitStockBar}>
                    <View
                      style={[
                        styles.unitStockFill,
                        {
                          width: `${Math.min(100, unit.fullness_percent)}%`,
                          backgroundColor: getStockColor(unit.fullness_percent),
                        },
                      ]}
                    />
                  </View>
                  <Text style={[styles.unitPercent, { color: getStockColor(unit.fullness_percent) }]}>
                    {Math.round(unit.fullness_percent)}%
                  </Text>
                </View>

                {/* Unit info row */}
                <View style={styles.unitInfoRow}>
                  <Text style={styles.unitWeight}>{formatWeight(unit.current_weight_g)}</Text>
                  {unit.expiry_date && (
                    <View style={[
                      styles.unitExpiry,
                      unit.expiry_date < new Date().toISOString().split('T')[0]
                        ? styles.unitExpiryExpired
                        : null
                    ]}>
                      <Text style={styles.unitExpiryLabel}>Exp:</Text>
                      <Text style={styles.unitExpiryDate}>{formatDate(unit.expiry_date)}</Text>
                    </View>
                  )}
                </View>

                {/* Delete unit button */}
                <TouchableOpacity
                  style={styles.deleteUnitButton}
                  onPress={() => onDeleteUnit(unit.unit_id, product.product_name)}
                >
                  <Text style={styles.deleteUnitButtonText}>✕</Text>
                </TouchableOpacity>
              </View>
            ))}

            {/* Add another unit button */}
            <TouchableOpacity
              style={styles.addAnotherButton}
              onPress={() => navigation.navigate('AddProduct', {
                product: {
                  id: product.product_id,
                  name: product.product_name,
                  brand: product.brand,
                  image_url: product.image_url,
                  package_weight_g: product.package_weight_g,
                },
              })}
            >
              <Text style={styles.addAnotherButtonText}>+ Add Another Unit</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

export default function PantryScreen({ navigation }) {
  const [products, setProducts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState(null);
  const [viewMode, setViewMode] = useState('fridge'); // 'fridge', 'pantry', 'all'

  const fetchGroupedInventory = async () => {
    try {
      const url = viewMode === 'all'
        ? `${API_BASE_URL}/api/pantry/inventory/grouped`
        : `${API_BASE_URL}/api/pantry/inventory/grouped?location=${viewMode}`;
      const response = await fetch(url);
      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error('Failed to fetch grouped inventory:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pantry/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([fetchGroupedInventory(), fetchStats()]);
    setRefreshing(false);
  }, [viewMode]);

  useFocusEffect(
    useCallback(() => {
      fetchGroupedInventory();
      fetchStats();
    }, [viewMode])
  );

  const handleDeleteUnit = (unitId, productName) => {
    Alert.alert(
      'Remove Unit',
      `Remove this unit of ${productName}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await fetch(`${API_BASE_URL}/api/pantry/inventory/${unitId}`, {
                method: 'DELETE',
              });
              fetchGroupedInventory();
            } catch (error) {
              Alert.alert('Error', 'Failed to remove unit');
            }
          },
        },
      ]
    );
  };

  const renderProduct = ({ item }) => (
    <ProductCard
      product={item}
      navigation={navigation}
      onDeleteUnit={handleDeleteUnit}
      onRefresh={fetchGroupedInventory}
    />
  );

  // Calculate totals
  const totalUnits = products.reduce((sum, p) => sum + p.unit_count, 0);
  const expiredCount = products.filter(p => p.has_expired).length;
  const expiringSoonCount = products.filter(p => p.expires_soon && !p.has_expired).length;

  return (
    <View style={styles.container}>
      {/* Location tabs */}
      <View style={styles.tabRow}>
        <TouchableOpacity
          style={[styles.tab, viewMode === 'fridge' && styles.tabActive]}
          onPress={() => setViewMode('fridge')}
        >
          <Text style={[styles.tabText, viewMode === 'fridge' && styles.tabTextActive]}>
            🧊 Fridge
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, viewMode === 'pantry' && styles.tabActive]}
          onPress={() => setViewMode('pantry')}
        >
          <Text style={[styles.tabText, viewMode === 'pantry' && styles.tabTextActive]}>
            🥫 Pantry
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, viewMode === 'freezer' && styles.tabActive]}
          onPress={() => setViewMode('freezer')}
        >
          <Text style={[styles.tabText, viewMode === 'freezer' && styles.tabTextActive]}>
            ❄️ Freezer
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, viewMode === 'all' && styles.tabActive]}
          onPress={() => setViewMode('all')}
        >
          <Text style={[styles.tabText, viewMode === 'all' && styles.tabTextActive]}>
            All
          </Text>
        </TouchableOpacity>
      </View>

      {/* Stats header */}
      <View style={styles.statsRow}>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{products.length}</Text>
          <Text style={styles.statLabel}>Products</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{totalUnits}</Text>
          <Text style={styles.statLabel}>Units</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={[styles.statNumber, { color: '#f44336' }]}>
            {expiredCount}
          </Text>
          <Text style={styles.statLabel}>Expired</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={[styles.statNumber, { color: '#ff9800' }]}>
            {expiringSoonCount}
          </Text>
          <Text style={styles.statLabel}>Expiring</Text>
        </View>
      </View>

      {/* Inventory list */}
      <FlatList
        data={products}
        keyExtractor={(item) => item.product_id.toString()}
        renderItem={renderProduct}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyEmoji}>
              {viewMode === 'fridge' ? '🧊' : viewMode === 'freezer' ? '❄️' : '🥫'}
            </Text>
            <Text style={styles.emptyText}>
              No items in your {viewMode === 'all' ? 'inventory' : viewMode} yet
            </Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => navigation.navigate('Scan')}
            >
              <Text style={styles.addButtonText}>Scan to Add</Text>
            </TouchableOpacity>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  tabRow: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: '#4CAF50',
  },
  tabText: {
    fontSize: 13,
    color: '#888',
  },
  tabTextActive: {
    color: '#4CAF50',
    fontWeight: '600',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  statBox: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  statLabel: {
    fontSize: 11,
    color: '#666',
    marginTop: 2,
  },
  list: {
    padding: 12,
    flexGrow: 1,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  cardImage: {
    height: 120,
    backgroundColor: '#f8f8f8',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  placeholderEmoji: {
    fontSize: 50,
  },
  unitCountBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: '#4CAF50',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  unitCountText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: 'bold',
  },
  expiryBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  expiredBadge: {
    backgroundColor: '#f44336',
  },
  expiringSoonBadge: {
    backgroundColor: '#ff9800',
  },
  expiryBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  cardBody: {
    padding: 14,
  },
  itemBrand: {
    fontSize: 12,
    color: '#888',
    fontWeight: '500',
    marginBottom: 2,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    lineHeight: 20,
  },
  totalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  totalLabel: {
    fontSize: 13,
    color: '#666',
    marginRight: 6,
  },
  totalWeight: {
    fontSize: 15,
    fontWeight: '700',
    color: '#333',
  },
  stockContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  stockBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  stockFill: {
    height: '100%',
    borderRadius: 4,
  },
  stockPercent: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 8,
    minWidth: 32,
  },
  expandRow: {
    alignItems: 'center',
    paddingTop: 4,
  },
  expandHint: {
    fontSize: 12,
    color: '#888',
  },

  // Unit cards within expanded view
  unitsContainer: {
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingTop: 12,
  },
  unitCard: {
    backgroundColor: '#f8f8f8',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    position: 'relative',
  },
  unitHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  unitLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#555',
  },
  openedBadge: {
    fontSize: 10,
    color: '#ff9800',
    fontWeight: '600',
    backgroundColor: '#fff3e0',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  unitFullnessRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  unitStockBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#e0e0e0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  unitStockFill: {
    height: '100%',
    borderRadius: 3,
  },
  unitPercent: {
    fontSize: 11,
    fontWeight: '600',
    marginLeft: 6,
    minWidth: 28,
  },
  unitInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  unitWeight: {
    fontSize: 12,
    color: '#666',
  },
  unitExpiry: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  unitExpiryExpired: {
    backgroundColor: '#ffebee',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  unitExpiryLabel: {
    fontSize: 11,
    color: '#888',
    marginRight: 4,
  },
  unitExpiryDate: {
    fontSize: 11,
    color: '#555',
    fontWeight: '500',
  },
  deleteUnitButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#ffebee',
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteUnitButtonText: {
    color: '#e53935',
    fontSize: 12,
    fontWeight: '600',
  },
  addAnotherButton: {
    backgroundColor: '#e8f5e9',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4CAF50',
    borderStyle: 'dashed',
  },
  addAnotherButtonText: {
    color: '#4CAF50',
    fontSize: 13,
    fontWeight: '600',
  },

  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyEmoji: {
    fontSize: 60,
    marginBottom: 15,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 30,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
