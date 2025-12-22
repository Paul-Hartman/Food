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
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { API_BASE_URL } from '../config';

// Store brand colors (same as PantryScreen)
const STORE_COLORS = {
  aldi: {
    primary: '#00005f',
    secondary: '#f9dc00',
    text: '#ffffff',
  },
  lidl: {
    primary: '#0050aa',
    secondary: '#fff000',
    text: '#ffffff',
  },
  rewe: {
    primary: '#cc0000',
    secondary: '#ffffff',
    text: '#ffffff',
  },
  edeka: {
    primary: '#0050aa',
    secondary: '#ffcc00',
    text: '#ffffff',
  },
  default: {
    primary: '#ff7043',
    secondary: '#ffffff',
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

export default function SpiceRackScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchInventory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pantry/inventory?location=spice_rack`);
      const data = await response.json();
      setItems(data);
    } catch (error) {
      console.error('Failed to fetch spices:', error);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchInventory();
    setRefreshing(false);
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchInventory();
    }, [])
  );

  const handleDeleteItem = (item) => {
    Alert.alert(
      'Remove Spice',
      `Remove ${item.name} from spice rack?`,
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
              fetchInventory();
            } catch (error) {
              Alert.alert('Error', 'Failed to remove spice');
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

  const renderItem = ({ item }) => {
    const storeColors = getStoreColors(item.store);
    const storeName = getStoreDisplayName(item.store);

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('ProductDetail', { inventory: item })}
        onLongPress={() => handleDeleteItem(item)}
      >
        {/* Store indicator - small dot in corner for spices */}
        {item.store && (
          <View style={[styles.storeIndicator, { backgroundColor: storeColors.primary }]} />
        )}

        <View style={[
          styles.cardImage,
          item.store && { borderTopColor: storeColors.primary, borderTopWidth: 2 }
        ]}>
          {item.image_url ? (
            <Image source={{ uri: item.image_url }} style={styles.image} />
          ) : (
            <Text style={styles.placeholderEmoji}>🌶️</Text>
          )}
        </View>

        <View style={styles.cardBody}>
          <Text style={styles.itemName} numberOfLines={2}>{item.name}</Text>

          {/* Brand with store color */}
          {item.brand && (
            <Text style={[
              styles.itemBrand,
              item.store && { color: storeColors.primary }
            ]} numberOfLines={1}>
              {item.brand}
            </Text>
          )}

          {/* Weight indicator - smaller for spices */}
          <View style={styles.stockContainer}>
            {item.percent_remaining !== null && item.percent_remaining !== undefined ? (
              <View style={styles.stockBar}>
                <View
                  style={[
                    styles.stockFill,
                    {
                      width: `${Math.min(100, Math.max(0, item.percent_remaining))}%`,
                      backgroundColor: getStockColor(item.percent_remaining),
                    },
                  ]}
                />
              </View>
            ) : null}
          </View>

          <View style={styles.cardFooter}>
            {item.current_weight_g ? (
              <Text style={styles.weightText}>
                {Math.round(item.current_weight_g)}g
              </Text>
            ) : null}
            {item.price && (
              <Text style={[
                styles.priceText,
                item.store && { color: storeColors.primary }
              ]}>
                {item.currency === 'EUR' ? '€' : '$'}{item.price.toFixed(2)}
              </Text>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        numColumns={3}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyEmoji}>🌶️</Text>
            <Text style={styles.emptyText}>No spices in your rack yet</Text>
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
  list: {
    padding: 8,
    flexGrow: 1,
  },
  row: {
    justifyContent: 'flex-start',
    gap: 8,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 10,
    width: '31%',
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
    overflow: 'hidden',
  },
  storeIndicator: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 8,
    height: 8,
    borderRadius: 4,
    zIndex: 10,
  },
  cardImage: {
    height: 70,
    backgroundColor: '#fff5f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  placeholderEmoji: {
    fontSize: 30,
  },
  cardBody: {
    padding: 8,
  },
  itemName: {
    fontSize: 11,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
    lineHeight: 14,
  },
  itemBrand: {
    fontSize: 9,
    color: '#888',
    marginBottom: 4,
  },
  stockContainer: {
    marginVertical: 3,
  },
  stockBar: {
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  stockFill: {
    height: '100%',
    borderRadius: 2,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 2,
  },
  weightText: {
    fontSize: 9,
    color: '#888',
  },
  priceText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#ff7043',
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
    backgroundColor: '#ff7043',
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
