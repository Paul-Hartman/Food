import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api } from '../services/api';

interface AlchemyIngredient {
  id: number;
  name: string;
  category: string;
  effects: string[];
}

interface PotionEffect {
  id: number;
  name: string;
  description: string;
  icon: string;
}

interface BrewingMethod {
  id: number;
  name: string;
  description: string;
  icon: string;
}

export default function AlchemyScreen() {
  const [ingredients, setIngredients] = useState<AlchemyIngredient[]>([]);
  const [effects, setEffects] = useState<PotionEffect[]>([]);
  const [methods, setMethods] = useState<BrewingMethod[]>([]);
  const [selectedIngredients, setSelectedIngredients] = useState<number[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<number | null>(null);
  const [preview, setPreview] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlchemyData();
  }, []);

  useEffect(() => {
    if (selectedIngredients.length > 0 && selectedMethod) {
      previewPotion();
    } else {
      setPreview(null);
    }
  }, [selectedIngredients, selectedMethod]);

  async function loadAlchemyData() {
    setLoading(true);
    try {
      const [ingredientsData, effectsData, methodsData] = await Promise.all([
        api.getAlchemyIngredients(),
        api.getAlchemyEffects(),
        api.getAlchemyIngredients(), // Methods endpoint needs to be added
      ]);

      setIngredients(ingredientsData.slice(0, 20)); // Limit for mobile
      setEffects(effectsData);
      // Mock methods for now
      setMethods([
        { id: 1, name: 'Blend', description: 'Quick mixing', icon: '🌪️' },
        { id: 2, name: 'Steep', description: 'Hot water infusion', icon: '☕' },
        { id: 3, name: 'Press', description: 'Cold press extraction', icon: '💧' },
      ]);
    } catch (error) {
      console.error('Failed to load alchemy data:', error);
      Alert.alert('Error', 'Failed to load alchemy data');
    } finally {
      setLoading(false);
    }
  }

  async function previewPotion() {
    if (selectedIngredients.length === 0 || !selectedMethod) return;

    try {
      const data = await api.previewPotion({
        ingredients: selectedIngredients,
        brewing_method: selectedMethod.toString(),
      });
      setPreview(data);
    } catch (error) {
      console.error('Failed to preview potion:', error);
    }
  }

  function toggleIngredient(ingredientId: number) {
    if (selectedIngredients.includes(ingredientId)) {
      setSelectedIngredients(selectedIngredients.filter(id => id !== ingredientId));
    } else if (selectedIngredients.length < 5) {
      setSelectedIngredients([...selectedIngredients, ingredientId]);
    } else {
      Alert.alert('Limit Reached', 'Maximum 5 ingredients per potion');
    }
  }

  async function brewPotion() {
    if (selectedIngredients.length === 0 || !selectedMethod) {
      Alert.alert('Incomplete', 'Select ingredients and brewing method');
      return;
    }

    try {
      await api.brewPotion({
        ingredients: selectedIngredients,
        brewing_method: selectedMethod,
      });
      Alert.alert('Success', 'Potion brewed successfully!');
      setSelectedIngredients([]);
      setSelectedMethod(null);
      setPreview(null);
    } catch (error) {
      console.error('Failed to brew potion:', error);
      Alert.alert('Error', 'Failed to brew potion');
    }
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading alchemy lab...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Selected Ingredients */}
        <View style={styles.cauldron}>
          <Text style={styles.cauldronTitle}>🧪 Brewing Cauldron</Text>
          <View style={styles.selectedGrid}>
            {[...Array(5)].map((_, idx) => {
              const ingredient = ingredients.find(
                ing => ing.id === selectedIngredients[idx]
              );
              return (
                <View key={idx} style={styles.slot}>
                  {ingredient ? (
                    <TouchableOpacity onPress={() => toggleIngredient(ingredient.id)}>
                      <Text style={styles.slotText}>{ingredient.name.slice(0, 3)}</Text>
                    </TouchableOpacity>
                  ) : (
                    <Text style={styles.slotEmpty}>+</Text>
                  )}
                </View>
              );
            })}
          </View>
        </View>

        {/* Brewing Methods */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Brewing Method</Text>
          <View style={styles.methodsGrid}>
            {methods.map(method => (
              <TouchableOpacity
                key={method.id}
                style={[
                  styles.methodCard,
                  selectedMethod === method.id && styles.methodCardSelected,
                ]}
                onPress={() => setSelectedMethod(method.id)}
              >
                <Text style={styles.methodIcon}>{method.icon}</Text>
                <Text style={styles.methodName}>{method.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Preview */}
        {preview && (
          <View style={styles.preview}>
            <Text style={styles.previewTitle}>✨ Potion Preview</Text>
            <Text style={styles.previewEffect}>{preview.effect || 'Energy Boost'}</Text>
            <Text style={styles.previewDescription}>
              {preview.description || 'Increases energy and focus'}
            </Text>
            <TouchableOpacity style={styles.brewBtn} onPress={brewPotion}>
              <Text style={styles.brewBtnText}>Brew Potion</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Available Ingredients */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ingredients</Text>
          {ingredients.map(ingredient => (
            <TouchableOpacity
              key={ingredient.id}
              style={[
                styles.ingredientCard,
                selectedIngredients.includes(ingredient.id) && styles.ingredientCardSelected,
              ]}
              onPress={() => toggleIngredient(ingredient.id)}
            >
              <View style={styles.ingredientInfo}>
                <Text style={styles.ingredientName}>{ingredient.name}</Text>
                <Text style={styles.ingredientCategory}>{ingredient.category}</Text>
              </View>
              {selectedIngredients.includes(ingredient.id) && (
                <Text style={styles.checkmark}>✓</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  cauldron: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  cauldronTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 16,
  },
  selectedGrid: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
  },
  slot: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  slotText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  slotEmpty: {
    color: 'rgba(255,255,255,0.3)',
    fontSize: 24,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  methodsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  methodCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e5e7eb',
  },
  methodCardSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  methodIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  methodName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  preview: {
    backgroundColor: '#fef3c7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#fcd34d',
  },
  previewTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#78350f',
    marginBottom: 8,
  },
  previewEffect: {
    fontSize: 18,
    fontWeight: '700',
    color: '#92400e',
    marginBottom: 4,
  },
  previewDescription: {
    fontSize: 14,
    color: '#92400e',
    marginBottom: 12,
  },
  brewBtn: {
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  brewBtnText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  ingredientCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: '#e5e7eb',
  },
  ingredientCardSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  ingredientInfo: {
    flex: 1,
  },
  ingredientName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 2,
  },
  ingredientCategory: {
    fontSize: 12,
    color: '#6b7280',
  },
  checkmark: {
    fontSize: 20,
    color: '#4CAF50',
    fontWeight: '700',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
});
