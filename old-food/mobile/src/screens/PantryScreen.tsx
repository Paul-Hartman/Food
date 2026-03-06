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
  Image,
} from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { PantryItem } from '../types';
import { api } from '../services/api';
import BarcodeScanner from '../components/BarcodeScanner';
import HoverableCard from '../components/HoverableCard';
import type { NavigationProp } from '@react-navigation/native';
import type { RootStackParamList } from '../types';

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

// Helper function to get expiry status with color coding
const getExpiryStatus = (expiryDate: string | null) => {
  if (!expiryDate) return null;

  const now = new Date();
  const expiry = new Date(expiryDate);
  const days = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (days < 0) return { color: '#f44336', text: 'Expired', emoji: '⚠️' };
  if (days <= 3) return { color: '#ff5722', text: `${days}d`, emoji: '🔴' };
  if (days <= 7) return { color: '#ff9800', text: `${days}d`, emoji: '🟡' };
  return { color: '#4CAF50', text: `${days}d`, emoji: '🟢' };
};

export default function PantryScreen() {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();

  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [newItemName, setNewItemName] = useState('');
  const [newItemExpiry, setNewItemExpiry] = useState('');
  const [newItemPrice, setNewItemPrice] = useState('');
  const [totalValue, setTotalValue] = useState(0);

  // Scanner modal state
  const [scannerVisible, setScannerVisible] = useState(false);
  const [bulkMode, setBulkMode] = useState(false);

  // Edit modal state
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<PantryItem | null>(null);
  const [editQty, setEditQty] = useState('');
  const [editExpiry, setEditExpiry] = useState('');
  const [editPrice, setEditPrice] = useState('');

  // Daily-use state
  const [isDailyUse, setIsDailyUse] = useState(false);
  const [dailyUsageRate, setDailyUsageRate] = useState('');
  const [restockThreshold, setRestockThreshold] = useState('3');
  const [daysRemaining, setDaysRemaining] = useState<number | null>(null);

  useFocusEffect(
    useCallback(() => {
      loadPantry();
    }, [])
  );

  const loadPantry = async () => {
    try {
      setLoading(true);
      const [data, valueData] = await Promise.all([
        api.getPantry(),
        api.getPantryTotalValue(),
      ]);
      setPantryItems(data);
      setTotalValue(valueData.total);
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
      const priceValue = newItemPrice ? parseFloat(newItemPrice) : undefined;
      await api.addToPantry({
        name: newItemName.trim(),
        quantity: 1,
        unit: 'item',
        expires_at: newItemExpiry || undefined,
        price: priceValue,
      });
      setNewItemName('');
      setNewItemExpiry('');
      setNewItemPrice('');
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
    image_url?: string;
  }) => {
    try {
      console.log('📦 Receiving scanned item with image:', item.image_url);
      await api.addToPantry(item);
      loadPantry();
      // Removed popup - haptic feedback is enough
      console.log('✓ Added to pantry:', item.name);
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to add item to pantry');
    }
  };

  const handleBulkScanComplete = (scannedItemIds: number[]) => {
    // Navigate to bulk review screen
    navigation.navigate('BulkReview', {
      scannedItemIds,
      onComplete: () => {
        loadPantry(); // Refresh pantry after edits
      }
    });
  };

  const showEditModal = (item: PantryItem) => {
    setEditingItem(item);
    setEditQty(item.quantity.toString());
    setEditExpiry(item.expires_at || '');
    setEditPrice(item.price ? item.price.toString() : '');

    // Load daily-use settings
    setIsDailyUse(item.is_daily_use || false);
    setDailyUsageRate(item.daily_usage_rate?.toString() || '');
    setRestockThreshold(item.restock_threshold_days?.toString() || '3');

    // Calculate days remaining
    if (item.daily_usage_rate && item.daily_usage_rate > 0) {
      const days = item.quantity / item.daily_usage_rate;
      setDaysRemaining(days);
    } else {
      setDaysRemaining(null);
    }

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
      const priceValue = editPrice ? parseFloat(editPrice) : undefined;
      await api.updatePantryItem(
        editingItem.id,
        newQty,
        editExpiry || undefined,
        priceValue
      );

      // Update daily-use settings
      if (isDailyUse) {
        const usageRate = parseFloat(dailyUsageRate);
        const threshold = parseInt(restockThreshold);

        if (isNaN(usageRate) || usageRate <= 0) {
          Alert.alert('Error', 'Please enter a valid daily usage rate');
          return;
        }

        await api.toggleDailyUse(editingItem.id, {
          is_daily_use: true,
          daily_usage_rate: usageRate,
          restock_threshold_days: threshold,
        });
      } else if (editingItem.is_daily_use) {
        await api.toggleDailyUse(editingItem.id, { is_daily_use: false });
      }

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

      {/* Total Value Banner */}
      {totalValue > 0 && (
        <View style={styles.totalValueBanner}>
          <Text style={styles.totalValueText}>
            Total Pantry Value: €{totalValue.toFixed(2)}
          </Text>
        </View>
      )}

      {/* Add item form */}
      <View style={styles.addForm}>
        <View style={styles.addInputsContainer}>
          <TextInput
            style={styles.addInput}
            placeholder="Add item..."
            value={newItemName}
            onChangeText={setNewItemName}
            returnKeyType="done"
          />
          <View style={styles.addInputRow}>
            <TextInput
              style={[styles.addInputSmall, { flex: 1 }]}
              placeholder="Expiry (YYYY-MM-DD)"
              value={newItemExpiry}
              onChangeText={setNewItemExpiry}
              returnKeyType="done"
            />
            <TextInput
              style={[styles.addInputSmall, { width: 80 }]}
              placeholder="€0.00"
              value={newItemPrice}
              onChangeText={setNewItemPrice}
              keyboardType="decimal-pad"
              returnKeyType="done"
            />
          </View>
        </View>
        <View style={styles.scanContainer}>
          <View style={styles.scanModeToggle}>
            <TouchableOpacity
              style={[styles.modeButton, !bulkMode && styles.modeButtonActive]}
              onPress={() => setBulkMode(false)}
            >
              <Text style={[styles.modeButtonText, !bulkMode && styles.modeButtonTextActive]}>
                Single
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modeButton, bulkMode && styles.modeButtonActive]}
              onPress={() => setBulkMode(true)}
            >
              <Text style={[styles.modeButtonText, bulkMode && styles.modeButtonTextActive]}>
                Bulk
              </Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity style={styles.scanButton} onPress={() => setScannerVisible(true)}>
            <Text style={styles.scanButtonText}>📷 {bulkMode ? 'Bulk Scan' : ''}</Text>
          </TouchableOpacity>
        </View>
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
              <View style={styles.cardGrid}>
              {items.map((item) => {
                const expiryStatus = getExpiryStatus(item.expires_at);

                // Calculate depletion warning
                let depletionWarning = null;
                if (item.is_daily_use && item.daily_usage_rate && item.daily_usage_rate > 0) {
                  const daysLeft = item.quantity / item.daily_usage_rate;
                  if (daysLeft <= (item.restock_threshold_days || 3)) {
                    depletionWarning = {
                      color: daysLeft <= 1 ? '#f44336' : '#ff9800',
                      text: `${daysLeft.toFixed(1)}d`,
                    };
                  }
                }

                // Build badge text for card
                let badgeText = '';
                if (depletionWarning) {
                  badgeText = depletionWarning.text;
                } else if (expiryStatus) {
                  badgeText = expiryStatus.text;
                }

                // Build stats array
                const stats = [
                  { label: 'Qty', value: `${item.quantity}${item.unit || ''}` },
                ];
                if (item.price) {
                  stats.push({ label: 'Price', value: `€${item.price.toFixed(2)}` });
                }

                return (
                  <View key={item.id} style={styles.cardWrapper}>
                    <HoverableCard
                      title={item.name}
                      image={item.image_url || undefined}
                      badge={badgeText}
                      stats={stats}
                      onPress={() => navigation.navigate('PantryProductDetail', { productId: item.id })}
                    />
                    {/* Delete button overlay */}
                    <TouchableOpacity
                      style={styles.deleteButtonOverlay}
                      onPress={() => deleteItem(item)}
                    >
                      <Text style={styles.deleteButtonText}>×</Text>
                    </TouchableOpacity>
                  </View>
                );
              })}
              </View>
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
        bulkMode={bulkMode}
        onBulkScanComplete={handleBulkScanComplete}
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
            />
            <Text style={styles.inputLabel}>Expiry Date (Optional)</Text>
            <TextInput
              style={styles.input}
              value={editExpiry}
              onChangeText={setEditExpiry}
              placeholder="YYYY-MM-DD"
            />
            <Text style={styles.inputLabel}>Price (Optional)</Text>
            <TextInput
              style={styles.input}
              value={editPrice}
              onChangeText={setEditPrice}
              placeholder="€0.00"
              keyboardType="decimal-pad"
            />

            {/* Daily-Use Section */}
            <View style={styles.dailyUseSection}>
              <TouchableOpacity
                style={styles.checkboxRow}
                onPress={() => setIsDailyUse(!isDailyUse)}
              >
                <View style={[styles.checkbox, isDailyUse && styles.checkboxChecked]}>
                  {isDailyUse && <Text style={styles.checkmark}>✓</Text>}
                </View>
                <Text style={styles.checkboxLabel}>Track daily usage</Text>
              </TouchableOpacity>

              {isDailyUse && (
                <>
                  <Text style={styles.inputLabel}>Daily Usage Rate</Text>
                  <View style={styles.usageInputRow}>
                    <TextInput
                      style={[styles.input, { flex: 1 }]}
                      value={dailyUsageRate}
                      onChangeText={(text) => {
                        setDailyUsageRate(text);
                        const rate = parseFloat(text);
                        if (!isNaN(rate) && rate > 0) {
                          setDaysRemaining(parseFloat(editQty) / rate);
                        }
                      }}
                      placeholder="50"
                      keyboardType="decimal-pad"
                    />
                    <Text style={styles.unitText}>{editingItem?.unit || 'g'} per day</Text>
                  </View>

                  <Text style={styles.inputLabel}>Restock Alert (days before empty)</Text>
                  <TextInput
                    style={styles.input}
                    value={restockThreshold}
                    onChangeText={setRestockThreshold}
                    placeholder="3"
                    keyboardType="number-pad"
                  />

                  {daysRemaining !== null && (
                    <View style={styles.projectionBox}>
                      <Text style={styles.projectionLabel}>📊 Projection:</Text>
                      <Text style={styles.projectionText}>
                        {daysRemaining > 0
                          ? `Runs out in ${daysRemaining.toFixed(1)} days`
                          : 'Out of stock!'}
                      </Text>
                    </View>
                  )}
                </>
              )}
            </View>

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
  addInputsContainer: {
    flex: 1,
    gap: 8,
  },
  addInput: {
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  addInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  addInputSmall: {
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  totalValueBanner: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    marginHorizontal: 16,
    marginTop: 8,
    alignItems: 'center',
  },
  totalValueText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  scanContainer: {
    flexDirection: 'column',
    gap: 8,
  },
  scanModeToggle: {
    flexDirection: 'row',
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    padding: 2,
  },
  modeButton: {
    flex: 1,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  modeButtonActive: {
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  modeButtonText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  modeButtonTextActive: {
    color: '#4CAF50',
    fontWeight: '600',
  },
  scanButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
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
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardImage: {
    height: 120,
    backgroundColor: '#f0f0f0',
    position: 'relative',
  },
  productImage: {
    width: '100%',
    height: '100%',
  },
  placeholderImage: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  placeholderEmoji: {
    fontSize: 48,
  },
  cardContent: {
    padding: 12,
  },
  cardName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
  },
  cardDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  cardQuantity: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: '500',
  },
  cardPrice: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: '600',
  },
  cardBadges: {
    flexDirection: 'row',
    gap: 6,
    flexWrap: 'wrap',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  deleteButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  deleteButtonText: {
    fontSize: 20,
    color: '#f44336',
    fontWeight: 'bold',
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
  dailyUseSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#4CAF50',
    borderRadius: 4,
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#4CAF50',
  },
  checkmark: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#333',
  },
  usageInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  unitText: {
    fontSize: 14,
    color: '#666',
  },
  projectionBox: {
    backgroundColor: '#e3f2fd',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
  },
  projectionLabel: {
    fontSize: 12,
    color: '#1976d2',
    marginBottom: 4,
  },
  projectionText: {
    fontSize: 14,
    color: '#0d47a1',
    fontWeight: '600',
  },
  cardGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    justifyContent: 'space-between',
  },
  cardWrapper: {
    position: 'relative',
  },
  deleteButtonOverlay: {
    position: 'absolute',
    top: 8,
    left: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 3,
    zIndex: 100,
  },
});
