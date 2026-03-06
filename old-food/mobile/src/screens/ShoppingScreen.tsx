import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { ShoppingData, Recipe } from '../types';
import { api } from '../services/api';
import { ShoppingListRepository, ShoppingListItem } from '../database/repositories/ShoppingListRepository';
import { useOnlineStatus } from '../hooks/useOnlineStatus';

const SECTION_EMOJIS: Record<string, string> = {
  Produce: '🥬',
  Bakery: '🍞',
  'Dairy & Eggs': '🥛',
  'Meat & Seafood': '🥩',
  Frozen: '❄️',
  Pantry: '🥫',
  'Snacks & Beverages': '🍺',
  Other: '📦',
};

export default function ShoppingScreen() {
  const [items, setItems] = useState<ShoppingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selectedRecipes, setSelectedRecipes] = useState<Set<number>>(new Set());

  // Modals
  const [recipeModalVisible, setRecipeModalVisible] = useState(false);
  const [addItemModalVisible, setAddItemModalVisible] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQty, setNewItemQty] = useState('1');
  const [newItemCategory, setNewItemCategory] = useState('Other');

  const { isOnline } = useOnlineStatus();

  useFocusEffect(
    useCallback(() => {
      loadLocal();

      // Sync with server in background
      if (isOnline) {
        syncWithServer();
      }
    }, [isOnline])
  );

  /**
   * Load from local database (instant)
   */
  const loadLocal = async () => {
    try {
      setLoading(true);
      const localItems = await ShoppingListRepository.getAll();
      setItems(localItems);
    } catch (err) {
      console.error('Failed to load shopping list from local DB:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sync with server (background, non-blocking)
   */
  const syncWithServer = async () => {
    if (!isOnline) return;

    try {
      setSyncing(true);

      // Download latest from server
      const serverData = await api.getShopping();

      // Convert server format to local format
      const serverItems: Array<{
        id: number;
        item: string;
        quantity?: string;
        category?: string;
        checked: boolean;
      }> = [];

      for (const section of serverData.section_order) {
        const sectionItems = serverData.sections[section];
        for (const item of sectionItems) {
          serverItems.push({
            id: item.id,
            item: item.name,
            quantity: `${item.quantity || ''} ${item.unit || ''}`.trim(),
            category: section,
            checked: item.checked,
          });
        }
      }

      // Sync to local database
      await ShoppingListRepository.syncFromServer(serverItems);

      // Reload UI from local DB
      await loadLocal();
    } catch (err) {
      console.error('Failed to sync with server:', err);
      // Don't show error - offline mode is graceful
    } finally {
      setSyncing(false);
    }
  };

  const loadRecipes = async () => {
    try {
      const data = await api.getRecipes();
      setRecipes(data);
    } catch (err) {
      console.error(err);
    }
  };

  /**
   * Toggle item (instant local update + background sync)
   */
  const toggleItem = async (itemId: number) => {
    try {
      // Update local DB immediately
      await ShoppingListRepository.toggleChecked(itemId);

      // Reload UI from local DB
      await loadLocal();

      // Sync to server in background (don't await)
      if (isOnline) {
        api.toggleShoppingItem(itemId).catch(() => {
          // Failed to sync - will retry on next sync
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  /**
   * Clear checked items
   */
  const clearChecked = async () => {
    Alert.alert(
      'Clear Checked Items',
      'Remove all checked items from the list?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              // Clear from local DB
              await ShoppingListRepository.clearChecked();

              // Reload UI
              await loadLocal();

              // Sync to server in background
              if (isOnline) {
                api.clearCheckedShopping().catch(() => {
                  // Failed to sync - will retry on next sync
                });
              }
            } catch (err) {
              console.error(err);
            }
          },
        },
      ]
    );
  };

  const showRecipeModal = () => {
    if (!isOnline) {
      Alert.alert(
        'Internet Required',
        'Connect to WiFi to browse recipes and generate shopping lists.'
      );
      return;
    }

    loadRecipes();
    setSelectedRecipes(new Set());
    setRecipeModalVisible(true);
  };

  const toggleRecipeSelect = (recipeId: number) => {
    setSelectedRecipes((prev) => {
      const next = new Set(prev);
      if (next.has(recipeId)) {
        next.delete(recipeId);
      } else {
        next.add(recipeId);
      }
      return next;
    });
  };

  const generateFromRecipes = async () => {
    if (selectedRecipes.size === 0) {
      Alert.alert('Select Recipes', 'Please select at least one recipe');
      return;
    }

    if (!isOnline) {
      Alert.alert('Internet Required', 'Connect to WiFi to generate shopping lists from recipes.');
      return;
    }

    try {
      const result = await api.generateShopping(Array.from(selectedRecipes), false, true);
      Alert.alert('Success', `Added ${result.items_added} items to your shopping list!`);
      setRecipeModalVisible(false);

      // Sync from server to get new items
      await syncWithServer();
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to generate shopping list');
    }
  };

  /**
   * Add manual item (instant local save + background sync)
   */
  const addManualItem = async () => {
    if (!newItemName.trim()) {
      Alert.alert('Error', 'Please enter an item name');
      return;
    }

    try {
      // Save to local DB immediately
      await ShoppingListRepository.add({
        item: newItemName.trim(),
        quantity: newItemQty || '1',
        category: newItemCategory,
        checked: false,
        synced: false,
      });

      // Clear form and close modal
      setAddItemModalVisible(false);
      setNewItemName('');
      setNewItemQty('1');
      setNewItemCategory('Other');

      // Reload UI from local DB
      await loadLocal();

      // Sync to server in background
      if (isOnline) {
        api.addShoppingItem({
          name: newItemName.trim(),
          quantity: parseFloat(newItemQty) || 1,
          unit: 'item',
        }).catch(() => {
          // Failed to sync - will retry on next sync
        });
      }
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to add item');
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  // Group items by category for display
  const groupedItems: Record<string, ShoppingListItem[]> = {};
  const sectionOrder: string[] = [];

  for (const item of items) {
    const category = item.category || 'Other';
    if (!groupedItems[category]) {
      groupedItems[category] = [];
      sectionOrder.push(category);
    }
    groupedItems[category].push(item);
  }

  const hasItems = items.length > 0;

  return (
    <View style={styles.container}>
      {/* Subtitle with sync status */}
      <View style={styles.subtitleRow}>
        <Text style={styles.subtitle}>
          {isOnline ? 'Organized by section' : '📱 Offline Mode'}
        </Text>
        {syncing && (
          <View style={styles.syncingBadge}>
            <ActivityIndicator size="small" color="#666" />
            <Text style={styles.syncingText}>Syncing...</Text>
          </View>
        )}
      </View>

      {/* Action buttons */}
      <View style={styles.actionRow}>
        <TouchableOpacity
          style={[styles.actionButton, !isOnline && styles.actionButtonDisabled]}
          onPress={showRecipeModal}
        >
          <Text style={styles.actionButtonText}>Add from Recipes</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.secondaryButton]}
          onPress={clearChecked}
        >
          <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>
            Clear Checked
          </Text>
        </TouchableOpacity>
      </View>

      {!hasItems ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyEmoji}>🛒</Text>
          <Text style={styles.emptyText}>Your shopping list is empty</Text>
          <TouchableOpacity
            style={[styles.emptyButton, !isOnline && styles.actionButtonDisabled]}
            onPress={showRecipeModal}
          >
            <Text style={styles.emptyButtonText}>Add from Recipes</Text>
          </TouchableOpacity>
          {!isOnline && (
            <Text style={styles.offlineHint}>Connect to WiFi to browse recipes</Text>
          )}
        </View>
      ) : (
        <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
          {sectionOrder.map((section) => {
            const sectionItems = groupedItems[section];
            const uncheckedCount = sectionItems.filter((i) => !i.checked).length;

            return (
              <View key={section} style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Text style={styles.sectionTitle}>
                    {SECTION_EMOJIS[section] || '📦'} {section}
                  </Text>
                  <View style={styles.countBadge}>
                    <Text style={styles.countText}>{uncheckedCount}</Text>
                  </View>
                </View>
                {sectionItems.map((item) => (
                  <TouchableOpacity
                    key={item.id}
                    style={[styles.item, item.checked && styles.itemChecked]}
                    onPress={() => toggleItem(item.id!)}
                  >
                    <View style={[styles.checkbox, item.checked && styles.checkboxChecked]}>
                      {item.checked && <Text style={styles.checkmark}>✓</Text>}
                    </View>
                    <Text style={[styles.itemName, item.checked && styles.itemNameChecked]}>
                      {item.item}
                    </Text>
                    {item.quantity && (
                      <Text style={styles.itemAmount}>{item.quantity}</Text>
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            );
          })}

          <TouchableOpacity
            style={styles.addManualButton}
            onPress={() => setAddItemModalVisible(true)}
          >
            <Text style={styles.addManualButtonText}>+ Add Item Manually</Text>
          </TouchableOpacity>

          <View style={{ height: 40 }} />
        </ScrollView>
      )}

      {/* Recipe Selection Modal */}
      <Modal visible={recipeModalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add from Recipes</Text>
            <ScrollView style={styles.recipeList}>
              {recipes.map((recipe) => (
                <TouchableOpacity
                  key={recipe.id}
                  style={[
                    styles.recipeItem,
                    selectedRecipes.has(recipe.id) && styles.recipeItemSelected,
                  ]}
                  onPress={() => toggleRecipeSelect(recipe.id)}
                >
                  <View
                    style={[
                      styles.checkbox,
                      selectedRecipes.has(recipe.id) && styles.checkboxChecked,
                    ]}
                  >
                    {selectedRecipes.has(recipe.id) && <Text style={styles.checkmark}>✓</Text>}
                  </View>
                  <View style={styles.recipeInfo}>
                    <Text style={styles.recipeName}>{recipe.name}</Text>
                    <Text style={styles.recipeMeta}>
                      {recipe.prep_time_min + recipe.cook_time_min} min | {recipe.servings}{' '}
                      servings
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalButton}
                onPress={() => setRecipeModalVisible(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalPrimaryButton]}
                onPress={generateFromRecipes}
              >
                <Text style={[styles.modalButtonText, styles.modalPrimaryButtonText]}>
                  Add to List
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Add Manual Item Modal */}
      <Modal visible={addItemModalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Item</Text>
            <TextInput
              style={styles.input}
              placeholder="Item name"
              value={newItemName}
              onChangeText={setNewItemName}
              autoFocus
            />
            <View style={styles.inputRow}>
              <TextInput
                style={[styles.input, styles.inputSmall]}
                placeholder="Qty"
                value={newItemQty}
                onChangeText={setNewItemQty}
                keyboardType="numeric"
              />
              <TextInput
                style={[styles.input, styles.inputFlex]}
                placeholder="Category"
                value={newItemCategory}
                onChangeText={setNewItemCategory}
              />
            </View>
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalButton}
                onPress={() => setAddItemModalVisible(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalPrimaryButton]}
                onPress={addManualItem}
              >
                <Text style={[styles.modalButtonText, styles.modalPrimaryButtonText]}>Add</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  subtitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  syncingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  syncingText: {
    fontSize: 12,
    color: '#666',
  },
  actionRow: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionButtonDisabled: {
    backgroundColor: '#ccc',
    opacity: 0.6,
  },
  secondaryButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  secondaryButtonText: {
    color: '#666',
  },
  list: {
    flex: 1,
    paddingHorizontal: 16,
  },
  section: {
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  countBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  countText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 4,
  },
  itemChecked: {
    backgroundColor: '#f5f5f5',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#4CAF50',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#4CAF50',
  },
  checkmark: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  itemName: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  itemNameChecked: {
    textDecorationLine: 'line-through',
    color: '#999',
  },
  itemAmount: {
    fontSize: 14,
    color: '#666',
  },
  addManualButton: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderStyle: 'dashed',
    marginTop: 8,
  },
  addManualButtonText: {
    color: '#666',
    fontSize: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginBottom: 20,
  },
  emptyButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  emptyButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  offlineHint: {
    marginTop: 12,
    fontSize: 14,
    color: '#999',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
  },
  recipeList: {
    maxHeight: 300,
  },
  recipeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  recipeItemSelected: {
    backgroundColor: '#e8f5e9',
  },
  recipeInfo: {
    flex: 1,
  },
  recipeName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  recipeMeta: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  inputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  inputSmall: {
    width: 80,
  },
  inputFlex: {
    flex: 1,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 16,
  },
  modalButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  modalPrimaryButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  modalButtonText: {
    fontSize: 16,
    color: '#666',
  },
  modalPrimaryButtonText: {
    color: '#fff',
  },
});
