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
  ikea: {
    primary: '#0058a3',
    secondary: '#ffda1a',
    text: '#ffffff',
    name: 'IKEA',
  },
  wmf: {
    primary: '#000000',
    secondary: '#ffffff',
    text: '#ffffff',
    name: 'WMF',
  },
  default: {
    primary: '#607D8B',
    secondary: '#ffffff',
    text: '#ffffff',
    name: '',
  },
};

const getStoreColors = (store) => {
  if (!store) return STORE_COLORS.default;
  return STORE_COLORS[store.toLowerCase()] || STORE_COLORS.default;
};

// Category icons
const getCategoryEmoji = (category) => {
  const emojis = {
    cookware: '🍳',
    cutlery: '🔪',
    utensils: '🥄',
    appliances: '🔌',
    bakeware: '🧁',
    storage: '📦',
  };
  return emojis[category?.toLowerCase()] || '🍴';
};

// Material icons
const getMaterialEmoji = (material) => {
  const emojis = {
    stainless_steel: '🪙',
    cast_iron: '⬛',
    non_stick: '✨',
    wood: '🪵',
    silicone: '🔵',
    glass: '🔮',
    ceramic: '🏺',
    plastic: '🧊',
    metal: '🔩',
  };
  return emojis[material?.toLowerCase()] || '';
};

// Categories for filter
const CATEGORIES = [
  { key: null, label: 'All', emoji: '🍴' },
  { key: 'cookware', label: 'Cookware', emoji: '🍳' },
  { key: 'cutlery', label: 'Knives', emoji: '🔪' },
  { key: 'utensils', label: 'Utensils', emoji: '🥄' },
  { key: 'appliances', label: 'Appliances', emoji: '🔌' },
  { key: 'bakeware', label: 'Bakeware', emoji: '🧁' },
  { key: 'storage', label: 'Storage', emoji: '📦' },
];

export default function KitchenToolsScreen({ navigation }) {
  const [tools, setTools] = useState([]);
  const [filteredTools, setFilteredTools] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedStore, setSelectedStore] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchTools = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/kitchen/tools`);
      const data = await response.json();
      setTools(data);
      setFilteredTools(data);
    } catch (error) {
      console.error('Failed to fetch tools:', error);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  useEffect(() => {
    let filtered = tools;

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(t => t.category === selectedCategory);
    }

    // Filter by store
    if (selectedStore) {
      filtered = filtered.filter(t => t.store?.toLowerCase() === selectedStore.toLowerCase());
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(t =>
        t.name?.toLowerCase().includes(query) ||
        t.brand?.toLowerCase().includes(query) ||
        t.material?.toLowerCase().includes(query) ||
        t.subcategory?.toLowerCase().includes(query)
      );
    }

    setFilteredTools(filtered);
  }, [searchQuery, selectedCategory, selectedStore, tools]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchTools();
    setRefreshing(false);
  }, []);

  const handleAddToInventory = async (tool) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/kitchen/inventory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_id: tool.id,
          location: 'kitchen',
        }),
      });

      if (response.ok) {
        Alert.alert(
          'Added!',
          `${tool.name} added to your kitchen`,
          [{ text: 'OK' }]
        );
      } else {
        const error = await response.json();
        Alert.alert('Error', error.error || 'Failed to add tool');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to add tool to inventory');
    }
  };

  const renderCategoryFilter = () => (
    <View style={styles.categoryRow}>
      {CATEGORIES.map((cat) => {
        const isActive = selectedCategory === cat.key;
        return (
          <TouchableOpacity
            key={cat.key || 'all'}
            style={[
              styles.categoryChip,
              isActive && styles.categoryChipActive,
            ]}
            onPress={() => setSelectedCategory(isActive ? null : cat.key)}
          >
            <Text style={styles.categoryEmoji}>{cat.emoji}</Text>
            <Text style={[
              styles.categoryText,
              isActive && styles.categoryTextActive,
            ]}>
              {cat.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );

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
          All Stores
        </Text>
      </TouchableOpacity>
      {['aldi', 'lidl', 'rewe', 'ikea'].map((store) => {
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

  const renderTool = ({ item }) => {
    const storeColors = getStoreColors(item.store);
    const currency = item.currency === 'EUR' ? '€' : '$';

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => handleAddToInventory(item)}
        onLongPress={() => {
          Alert.alert(
            item.name,
            `${item.brand || ''}\n` +
            `Store: ${storeColors.name || 'Unknown'}\n` +
            `Category: ${item.category}\n` +
            `Material: ${item.material || 'N/A'}\n` +
            `Size: ${item.size || 'N/A'}\n` +
            `Price: ${currency}${item.price?.toFixed(2) || 'N/A'}\n` +
            `Dishwasher Safe: ${item.dishwasher_safe ? 'Yes' : 'No'}\n` +
            `Oven Safe: ${item.oven_safe ? 'Yes' : (item.max_temp_c ? `Up to ${item.max_temp_c}°C` : 'No')}`,
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Add to Kitchen', onPress: () => handleAddToInventory(item) },
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

        {/* Tool image/emoji */}
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

          {/* Tags row */}
          <View style={styles.tagsRow}>
            {/* Material tag */}
            {item.material && (
              <View style={styles.tag}>
                <Text style={styles.tagText}>
                  {getMaterialEmoji(item.material)} {item.material.replace('_', ' ')}
                </Text>
              </View>
            )}
          </View>

          {/* Features icons */}
          <View style={styles.featuresRow}>
            {item.dishwasher_safe ? (
              <Text style={styles.featureIcon} title="Dishwasher safe">🧼</Text>
            ) : null}
            {item.oven_safe ? (
              <Text style={styles.featureIcon} title="Oven safe">🔥</Text>
            ) : null}
            {item.size && (
              <Text style={styles.sizeText}>{item.size}</Text>
            )}
          </View>

          {/* Price */}
          <View style={styles.cardFooter}>
            <Text style={styles.categoryLabel}>{item.subcategory || item.category}</Text>
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
          placeholder="Search tools..."
          placeholderTextColor="#999"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Category filters (horizontal scroll) */}
      {renderCategoryFilter()}

      {/* Store filters */}
      {renderStoreFilter()}

      {/* Results count */}
      <View style={styles.resultsHeader}>
        <Text style={styles.resultsCount}>
          {filteredTools.length} tools
        </Text>
        {(selectedCategory || selectedStore) && (
          <TouchableOpacity onPress={() => {
            setSelectedCategory(null);
            setSelectedStore(null);
          }}>
            <Text style={styles.clearFilter}>Clear filters</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Tools grid */}
      <FlatList
        data={filteredTools}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderTool}
        numColumns={2}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyEmoji}>🍴</Text>
            <Text style={styles.emptyText}>No tools found</Text>
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
  categoryRow: {
    flexDirection: 'row',
    paddingHorizontal: 8,
    paddingVertical: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    flexWrap: 'wrap',
    gap: 6,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#f0f0f0',
    gap: 4,
  },
  categoryChipActive: {
    backgroundColor: '#607D8B',
  },
  categoryEmoji: {
    fontSize: 14,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#666',
  },
  categoryTextActive: {
    color: '#fff',
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#fff',
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 14,
    backgroundColor: '#f0f0f0',
  },
  filterChipActive: {
    backgroundColor: '#607D8B',
  },
  filterChipText: {
    fontSize: 12,
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
    color: '#607D8B',
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
    backgroundColor: '#f8f9fa',
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
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginBottom: 4,
  },
  tag: {
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  tagText: {
    fontSize: 9,
    color: '#666',
    textTransform: 'capitalize',
  },
  featuresRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  featureIcon: {
    fontSize: 12,
  },
  sizeText: {
    fontSize: 10,
    color: '#888',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  categoryLabel: {
    fontSize: 9,
    color: '#999',
    textTransform: 'capitalize',
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
