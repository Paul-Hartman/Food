import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  TextInput,
  RefreshControl,
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

export default function ProductBrowserScreen({ navigation }) {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStore, setSelectedStore] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pantry/products`);
      const data = await response.json();
      setProducts(data);
      setFilteredProducts(data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    let filtered = products;

    // Filter by store
    if (selectedStore) {
      filtered = filtered.filter(p => p.store?.toLowerCase() === selectedStore.toLowerCase());
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(p =>
        p.name?.toLowerCase().includes(query) ||
        p.brand?.toLowerCase().includes(query) ||
        p.category?.toLowerCase().includes(query)
      );
    }

    setFilteredProducts(filtered);
  }, [searchQuery, selectedStore, products]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchProducts();
    setRefreshing(false);
  }, []);

  const handleAddToInventory = async (product) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pantry/inventory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: product.id,
          location: product.storage_type || 'pantry',
          current_weight_g: product.package_weight_g,
        }),
      });

      if (response.ok) {
        Alert.alert(
          'Added!',
          `${product.name} added to your ${product.storage_type || 'pantry'}`,
          [
            { text: 'OK' },
            {
              text: 'Go to Pantry',
              onPress: () => navigation.navigate('Pantry'),
            },
          ]
        );
      } else {
        const error = await response.json();
        Alert.alert('Error', error.error || 'Failed to add product');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to add product to inventory');
    }
  };

  const renderStoreFilter = () => (
    <View style={styles.filterRow}>
      <TouchableOpacity
        style={[
          styles.filterChip,
          !selectedStore && styles.filterChipActive,
        ]}
        onPress={() => setSelectedStore(null)}
      >
        <Text style={[
          styles.filterChipText,
          !selectedStore && styles.filterChipTextActive,
        ]}>
          All
        </Text>
      </TouchableOpacity>
      {['aldi', 'lidl', 'rewe'].map((store) => {
        const colors = getStoreColors(store);
        const isActive = selectedStore === store;
        return (
          <TouchableOpacity
            key={store}
            style={[
              styles.filterChip,
              isActive && { backgroundColor: colors.primary },
            ]}
            onPress={() => setSelectedStore(isActive ? null : store)}
          >
            <Text style={[
              styles.filterChipText,
              isActive && { color: colors.text },
            ]}>
              {colors.name}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );

  const renderProduct = ({ item }) => {
    const storeColors = getStoreColors(item.store);
    const currency = item.currency === 'EUR' ? '€' : '$';

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => handleAddToInventory(item)}
        onLongPress={() => {
          // Show product details
          Alert.alert(
            item.name,
            `${item.brand || ''}\n` +
            `Store: ${storeColors.name || 'Unknown'}\n` +
            `Price: ${currency}${item.price?.toFixed(2) || 'N/A'}\n` +
            `Calories: ${item.calories || 0}/100g\n` +
            `Weight: ${item.package_weight_g || 'N/A'}${item.package_unit || 'g'}`,
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Add to Pantry', onPress: () => handleAddToInventory(item) },
            ]
          );
        }}
      >
        {/* Store badge */}
        {item.store && (
          <View style={[styles.storeBadge, { backgroundColor: storeColors.primary }]}>
            <Text style={[styles.storeBadgeText, { color: storeColors.text }]}>
              {storeColors.name}
            </Text>
          </View>
        )}

        {/* Product image/emoji */}
        <View style={[
          styles.cardImage,
          item.store && { borderTopColor: storeColors.primary, borderTopWidth: 3 }
        ]}>
          {item.image_url ? (
            <Image source={{ uri: item.image_url }} style={styles.image} />
          ) : (
            <Text style={styles.placeholderEmoji}>
              {getCategoryEmoji(item.category)}
            </Text>
          )}
        </View>

        <View style={styles.cardBody}>
          {/* Brand */}
          {item.brand && (
            <View style={styles.brandRow}>
              <View style={[styles.brandDot, { backgroundColor: storeColors.primary }]} />
              <Text style={styles.itemBrand} numberOfLines={1}>{item.brand}</Text>
            </View>
          )}

          {/* Name */}
          <Text style={styles.itemName} numberOfLines={2}>{item.name}</Text>

          {/* Category tag */}
          <View style={styles.categoryTag}>
            <Text style={styles.categoryText}>{item.category}</Text>
          </View>

          {/* Price and weight */}
          <View style={styles.cardFooter}>
            <Text style={styles.weightText}>
              {item.package_weight_g >= 1000
                ? `${(item.package_weight_g / 1000).toFixed(1)}kg`
                : `${item.package_weight_g}${item.package_unit || 'g'}`
              }
            </Text>
            {item.price && (
              <Text style={[styles.priceText, { color: storeColors.primary }]}>
                {currency}{item.price.toFixed(2)}
              </Text>
            )}
          </View>
        </View>

        {/* Add indicator */}
        <View style={[styles.addIndicator, { backgroundColor: storeColors.primary }]}>
          <Text style={styles.addIndicatorText}>+</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* Search bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search products..."
          placeholderTextColor="#999"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Store filters */}
      {renderStoreFilter()}

      {/* Results count */}
      <View style={styles.resultsHeader}>
        <Text style={styles.resultsCount}>
          {filteredProducts.length} products
        </Text>
        {selectedStore && (
          <TouchableOpacity onPress={() => setSelectedStore(null)}>
            <Text style={styles.clearFilter}>Clear filter</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Product grid */}
      <FlatList
        data={filteredProducts}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderProduct}
        numColumns={2}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyEmoji}>🛒</Text>
            <Text style={styles.emptyText}>No products found</Text>
            <Text style={styles.emptySubtext}>
              Try adjusting your search or filters
            </Text>
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
  searchContainer: {
    padding: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchInput: {
    backgroundColor: '#f0f0f0',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    color: '#333',
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#fff',
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#f0f0f0',
  },
  filterChipActive: {
    backgroundColor: '#4CAF50',
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
  },
  filterChipTextActive: {
    color: '#fff',
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  resultsCount: {
    fontSize: 13,
    color: '#666',
  },
  clearFilter: {
    fontSize: 13,
    color: '#4CAF50',
    fontWeight: '600',
  },
  list: {
    padding: 8,
    flexGrow: 1,
  },
  row: {
    justifyContent: 'space-between',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    width: '48%',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  storeBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    zIndex: 10,
  },
  storeBadgeText: {
    fontSize: 9,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  cardImage: {
    height: 90,
    backgroundColor: '#f8f8f8',
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  placeholderEmoji: {
    fontSize: 36,
  },
  cardBody: {
    padding: 10,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 2,
  },
  brandDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 5,
  },
  itemBrand: {
    fontSize: 10,
    color: '#888',
    fontWeight: '500',
    flex: 1,
  },
  itemName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
    lineHeight: 16,
  },
  categoryTag: {
    alignSelf: 'flex-start',
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginBottom: 6,
  },
  categoryText: {
    fontSize: 9,
    color: '#666',
    textTransform: 'capitalize',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  weightText: {
    fontSize: 10,
    color: '#999',
  },
  priceText: {
    fontSize: 13,
    fontWeight: '700',
  },
  addIndicator: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addIndicatorText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
    marginTop: -2,
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
    fontSize: 18,
    color: '#666',
    fontWeight: '600',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
});
