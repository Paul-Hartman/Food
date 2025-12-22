import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  TextInput,
  Alert,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useRoute, useNavigation, CompositeNavigationProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { api } from '../services/api';
import { PantryItem, RootStackParamList, TabParamList } from '../types';
import BulkScanFeedbackModal from '../components/BulkScanFeedbackModal';

type BulkReviewScreenNavigationProp = CompositeNavigationProp<
  StackNavigationProp<RootStackParamList, 'BulkReview'>,
  BottomTabNavigationProp<TabParamList>
>;

interface RouteParams {
  scannedItemIds: number[];
  onComplete?: () => void;
}

export default function BulkReviewScreen() {
  const route = useRoute();
  const navigation = useNavigation<BulkReviewScreenNavigationProp>();
  const { scannedItemIds, onComplete } = route.params as RouteParams;

  const [items, setItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editQty, setEditQty] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      setLoading(true);
      // Fetch full pantry, then filter to scanned items
      const allItems = await api.getPantry();
      const scannedItems = allItems.filter(item => scannedItemIds.includes(item.id));
      setItems(scannedItems);
    } catch (error) {
      console.error('Failed to load items:', error);
      Alert.alert('Error', 'Failed to load scanned items');
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId: number, newQty: number) => {
    try {
      await api.updatePantryItem(itemId, newQty);
      setItems(prev => prev.map(item =>
        item.id === itemId ? { ...item, quantity: newQty } : item
      ));
    } catch (error) {
      console.error('Update quantity error:', error);
      Alert.alert('Error', 'Failed to update quantity');
    }
  };

  const removeItem = async (itemId: number) => {
    Alert.alert(
      'Remove Item',
      'Delete this item from pantry?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deletePantryItem(itemId);
              setItems(prev => prev.filter(item => item.id !== itemId));
            } catch (error) {
              console.error('Remove item error:', error);
              Alert.alert('Error', 'Failed to remove item');
            }
          }
        }
      ]
    );
  };

  const findRecipes = () => {
    if (items.length === 0) {
      Alert.alert('No Items', 'Add some items first');
      return;
    }

    const ingredientNames = items.map(item => item.name);

    // Navigate to Recipes tab with ingredients
    navigation.navigate('Main', {
      screen: 'Recipes',
      params: { pantryIngredients: ingredientNames }
    });
  };

  const handleDone = () => {
    // Show feedback modal if bulk scan (5+ items)
    if (items.length >= 5) {
      setShowFeedback(true);
    } else {
      onComplete?.();
      navigation.goBack();
    }
  };

  const handleFeedbackClose = () => {
    setShowFeedback(false);
    onComplete?.();
    navigation.goBack();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading scanned items...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Review Scanned Items</Text>
        <Text style={styles.subtitle}>
          {items.length} item{items.length !== 1 ? 's' : ''} added to pantry
        </Text>
      </View>

      {/* Action buttons */}
      <View style={styles.actionBar}>
        <TouchableOpacity
          style={[styles.actionButton, styles.recipeButton]}
          onPress={findRecipes}
          disabled={items.length === 0}
        >
          <Text style={styles.actionButtonText}>🍳 What Can I Cook?</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.doneButton]}
          onPress={handleDone}
        >
          <Text style={styles.actionButtonText}>✓ Done</Text>
        </TouchableOpacity>
      </View>

      {/* Item list */}
      <FlatList
        data={items}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <View style={styles.itemCard}>
            <View style={styles.itemContent}>
              <Text style={styles.itemName}>{item.name}</Text>
              <Text style={styles.itemCategory}>{item.category}</Text>
            </View>

            {/* Inline quantity edit */}
            {editingItemId === item.id ? (
              <View style={styles.editContainer}>
                <TextInput
                  style={styles.qtyInput}
                  value={editQty}
                  onChangeText={setEditQty}
                  keyboardType="numeric"
                  autoFocus
                  onBlur={() => {
                    // Save on blur
                    const qty = parseFloat(editQty);
                    if (!isNaN(qty) && qty > 0) {
                      updateQuantity(item.id, qty);
                    }
                    setEditingItemId(null);
                  }}
                />
                <Text style={styles.unitText}>{item.unit}</Text>
                <TouchableOpacity
                  onPress={() => {
                    const qty = parseFloat(editQty);
                    if (!isNaN(qty) && qty > 0) {
                      updateQuantity(item.id, qty);
                      setEditingItemId(null);
                    } else {
                      Alert.alert('Invalid Quantity', 'Please enter a valid number');
                    }
                  }}
                  style={styles.saveButton}
                >
                  <Text style={styles.saveButtonText}>✓</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <TouchableOpacity
                onPress={() => {
                  setEditingItemId(item.id);
                  setEditQty(item.quantity.toString());
                }}
                style={styles.qtyButton}
              >
                <Text style={styles.itemQuantity}>
                  {item.quantity} {item.unit}
                </Text>
              </TouchableOpacity>
            )}

            {/* Remove button */}
            <TouchableOpacity
              onPress={() => removeItem(item.id)}
              style={styles.removeButton}
            >
              <Text style={styles.removeButtonText}>×</Text>
            </TouchableOpacity>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyEmoji}>📦</Text>
            <Text style={styles.emptyText}>No items to review</Text>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.backButtonText}>Go Back</Text>
            </TouchableOpacity>
          </View>
        }
      />

      {/* Feedback Modal */}
      <BulkScanFeedbackModal
        visible={showFeedback}
        onClose={handleFeedbackClose}
        itemCount={items.length}
        sessionId={new Date().toISOString()}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#fff',
    paddingVertical: 20,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  actionBar: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  recipeButton: {
    backgroundColor: '#4CAF50',
  },
  doneButton: {
    backgroundColor: '#2196F3',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
  },
  itemCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  itemContent: {
    flex: 1,
    marginRight: 12,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  itemCategory: {
    fontSize: 13,
    color: '#666',
    textTransform: 'capitalize',
  },
  editContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    paddingHorizontal: 8,
    gap: 4,
  },
  qtyInput: {
    width: 60,
    height: 36,
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  unitText: {
    fontSize: 14,
    color: '#666',
  },
  saveButton: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    borderRadius: 16,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  qtyButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  itemQuantity: {
    fontSize: 15,
    fontWeight: '600',
    color: '#4CAF50',
  },
  removeButton: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffebee',
    borderRadius: 16,
    marginLeft: 8,
  },
  removeButtonText: {
    fontSize: 24,
    color: '#f44336',
    fontWeight: '300',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    color: '#999',
    marginBottom: 24,
  },
  backButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
