import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  TextInput,
  Modal,
  Alert,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { PantryItem } from '../types';
import { api } from '../services/api';
import BarcodeScanner from '../components/BarcodeScanner';

const CATEGORY_EMOJIS: Record<string, string> = {
  protein: '🥩',
  vegetable: '🥬',
  fruit: '🍎',
  dairy: '🥛',
  grain: '🌾',
  pantry: '🥫',
  spice: '🌶️',
  bakery: '🍞',
  frozen: '❄️',
  other: '📦',
};

export default function PantryScreen() {
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [newItemName, setNewItemName] = useState('');

  // Scanner modal state
  const [scannerVisible, setScannerVisible] = useState(false);

  // Edit modal state
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<PantryItem | null>(null);
  const [editQty, setEditQty] = useState('');

  useFocusEffect(
    useCallback(() => {
      loadPantry();
    }, [])
  );

  const loadPantry = async () => {
    try {
      setLoading(true);
      const data = await api.getPantry();
      setPantryItems(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const addToPantry = async () => {
    if (!newItemName.trim()) {
      Alert.alert('Error', 'Please enter an item name');
      return;
    }

    try {
      await api.addToPantry({
        name: newItemName.trim(),
        quantity: 1,
        unit: 'item',
      });
      setNewItemName('');
      loadPantry();
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to add item');
    }
  };

  const handleProductScanned = async (item: {
    name: string;
    category: string;
    quantity: number;
    unit: string;
  }) => {
    try {
      await api.addToPantry(item);
      loadPantry();
      Alert.alert('Success', `${item.name} added to pantry`);
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to add item to pantry');
    }
  };

  const showEditModal = (item: PantryItem) => {
    setEditingItem(item);
    setEditQty(item.quantity.toString());
    setEditModalVisible(true);
  };

  const saveEdit = async () => {
    if (!editingItem) return;

    const newQty = parseFloat(editQty);
    if (isNaN(newQty) || newQty < 0) {
      Alert.alert('Error', 'Please enter a valid quantity');
      return;
    }

    try {
      await api.updatePantryItem(editingItem.id, newQty);
      setEditModalVisible(false);
      setEditingItem(null);
      loadPantry();
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to update item');
    }
  };

  const deleteItem = (item: PantryItem) => {
    Alert.alert('Remove Item', `Remove ${item.name} from pantry?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            await api.deletePantryItem(item.id);
            loadPantry();
          } catch (err) {
            console.error(err);
            Alert.alert('Error', 'Failed to delete item');
          }
        },
      },
    ]);
  };

  // Group items by category
  const groupedItems = pantryItems.reduce((acc, item) => {
    const category = item.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(item);
    return acc;
  }, {} as Record<string, PantryItem[]>);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Subtitle */}
      <Text style={styles.subtitle}>Track what you have at home</Text>

      {/* Add item form */}
      <View style={styles.addForm}>
        <TextInput
          style={styles.addInput}
          placeholder="Add item..."
          value={newItemName}
          onChangeText={setNewItemName}
          onSubmitEditing={addToPantry}
          returnKeyType="done"
        />
        <TouchableOpacity style={styles.scanButton} onPress={() => setScannerVisible(true)}>
          <Text style={styles.scanButtonText}>📷</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.addButton} onPress={addToPantry}>
          <Text style={styles.addButtonText}>Add</Text>
        </TouchableOpacity>
      </View>

      {pantryItems.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyEmoji}>🏠</Text>
          <Text style={styles.emptyText}>Your pantry is empty</Text>
          <Text style={styles.emptySubtext}>Add items above to track what you have at home</Text>
        </View>
      ) : (
        <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
          {Object.entries(groupedItems).map(([category, items]) => (
            <View key={category} style={styles.categorySection}>
              <Text style={styles.categoryTitle}>
                {CATEGORY_EMOJIS[category] || '📦'} {category}
              </Text>
              {items.map((item) => (
                <View key={item.id} style={styles.item}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <TouchableOpacity onPress={() => showEditModal(item)}>
                    <Text style={styles.itemAmount}>
                      {item.quantity} {item.unit || ''}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.deleteButton}
                    onPress={() => deleteItem(item)}
                  >
                    <Text style={styles.deleteButtonText}>×</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          ))}
          <View style={{ height: 40 }} />
        </ScrollView>
      )}

      {/* Barcode Scanner */}
      <BarcodeScanner
        visible={scannerVisible}
        onClose={() => setScannerVisible(false)}
        onProductFound={handleProductScanned}
      />

      {/* Edit Modal */}
      <Modal visible={editModalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Edit Item</Text>
            <Text style={styles.modalSubtitle}>{editingItem?.name}</Text>
            <Text style={styles.inputLabel}>Quantity</Text>
            <TextInput
              style={styles.input}
              value={editQty}
              onChangeText={setEditQty}
              keyboardType="numeric"
              autoFocus
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalButton}
                onPress={() => setEditModalVisible(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalPrimaryButton]}
                onPress={saveEdit}
              >
                <Text style={[styles.modalButtonText, styles.modalPrimaryButtonText]}>
                  Save
                </Text>
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
  addForm: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  addInput: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  scanButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanButtonText: {
    fontSize: 20,
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 20,
    borderRadius: 8,
    justifyContent: 'center',
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  list: {
    flex: 1,
    paddingHorizontal: 16,
  },
  categorySection: {
    marginBottom: 16,
  },
  categoryTitle: {
    fontSize: 14,
    color: '#666',
    textTransform: 'capitalize',
    marginBottom: 8,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 4,
  },
  itemName: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  itemAmount: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: '500',
    paddingHorizontal: 12,
  },
  deleteButton: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteButtonText: {
    fontSize: 24,
    color: '#999',
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
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
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
    width: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 20,
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
