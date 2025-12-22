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
import { ShoppingData, ShoppingItem, Recipe } from '../types';
import { api } from '../services/api';

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
  const [shoppingData, setShoppingData] = useState<ShoppingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selectedRecipes, setSelectedRecipes] = useState<Set<number>>(new Set());

  // Modals
  const [recipeModalVisible, setRecipeModalVisible] = useState(false);
  const [addItemModalVisible, setAddItemModalVisible] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQty, setNewItemQty] = useState('1');
  const [newItemUnit, setNewItemUnit] = useState('item');

  useFocusEffect(
    useCallback(() => {
      loadShopping();
    }, [])
  );

  const loadShopping = async () => {
    try {
      setLoading(true);
      const data = await api.getShopping();
      setShoppingData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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

  const toggleItem = async (itemId: number) => {
    try {
      await api.toggleShoppingItem(itemId);
      loadShopping();
    } catch (err) {
      console.error(err);
    }
  };

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
              await api.clearCheckedShopping();
              loadShopping();
            } catch (err) {
              console.error(err);
            }
          },
        },
      ]
    );
  };

  const showRecipeModal = () => {
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

    try {
      const result = await api.generateShopping(Array.from(selectedRecipes), false, true);
      Alert.alert('Success', `Added ${result.items_added} items to your shopping list!`);
      setRecipeModalVisible(false);
      loadShopping();
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to generate shopping list');
    }
  };

  const addManualItem = async () => {
    if (!newItemName.trim()) {
      Alert.alert('Error', 'Please enter an item name');
      return;
    }

    try {
      await api.addShoppingItem({
        name: newItemName.trim(),
        quantity: parseFloat(newItemQty) || 1,
        unit: newItemUnit || 'item',
      });
      setAddItemModalVisible(false);
      setNewItemName('');
      setNewItemQty('1');
      setNewItemUnit('item');
      loadShopping();
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

  const hasItems = shoppingData?.section_order && shoppingData.section_order.length > 0;

  return (
    <View style={styles.container}>
      {/* Subtitle */}
      <Text style={styles.subtitle}>Organized by Aldi sections</Text>

      {/* Action buttons */}
      <View style={styles.actionRow}>
        <TouchableOpacity style={styles.actionButton} onPress={showRecipeModal}>
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
          <TouchableOpacity style={styles.emptyButton} onPress={showRecipeModal}>
            <Text style={styles.emptyButtonText}>Add from Recipes</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
          {shoppingData!.section_order.map((section) => {
            const items = shoppingData!.sections[section];
            const uncheckedCount = items.filter((i) => !i.checked).length;

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
                {items.map((item) => (
                  <TouchableOpacity
                    key={item.id}
                    style={[styles.item, item.checked && styles.itemChecked]}
                    onPress={() => toggleItem(item.id)}
                  >
                    <View style={[styles.checkbox, item.checked && styles.checkboxChecked]}>
                      {item.checked && <Text style={styles.checkmark}>✓</Text>}
                    </View>
                    <Text style={[styles.itemName, item.checked && styles.itemNameChecked]}>
                      {item.name}
                    </Text>
                    <Text style={styles.itemAmount}>
                      {item.quantity} {item.unit}
                    </Text>
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
                placeholder="Unit"
                value={newItemUnit}
                onChangeText={setNewItemUnit}
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
  subtitle: {
    fontSize: 14,
    color: '#666',
    paddingHorizontal: 16,
    paddingTop: 8,
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
