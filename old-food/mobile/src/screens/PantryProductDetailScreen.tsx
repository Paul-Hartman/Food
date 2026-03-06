import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Image,
  Dimensions,
  Alert,
} from 'react-native';
import { RouteProp, useRoute, useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList, PantryItem, Ingredient } from '../types';
import { api } from '../services/api';

type RouteProps = RouteProp<RootStackParamList, 'PantryProductDetail'>;

const SCREEN_WIDTH = Dimensions.get('window').width;

// Category emoji mapping
const CATEGORY_EMOJIS: Record<string, string> = {
  dairy: '🥛',
  meat: '🥩',
  vegetable: '🥕',
  fruit: '🍎',
  grain: '🌾',
  condiment: '🧂',
  drink: '🥤',
  snack: '🍪',
  frozen: '🧊',
  canned: '🥫',
  bakery: '🥖',
  spice: '🌶️',
  sauce: '🥫',
  oil: '🫒',
  other: '📦',
};

export default function PantryProductDetailScreen() {
  const route = useRoute<RouteProps>();
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const { productId } = route.params;

  const [product, setProduct] = useState<PantryItem | null>(null);
  const [ingredient, setIngredient] = useState<Ingredient | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProduct();
  }, [productId]);

  const loadProduct = async () => {
    try {
      setLoading(true);

      // Load pantry item
      const pantryItems = await api.getPantry();
      const item = pantryItems.find(p => p.id === productId);

      if (!item) {
        Alert.alert('Error', 'Product not found');
        navigation.goBack();
        return;
      }

      setProduct(item);

      // Load ingredient details for nutritional info
      const ingredientResponse = await api.getIngredientById(item.ingredient_id);
      if (ingredientResponse.ingredients.length > 0) {
        setIngredient(ingredientResponse.ingredients[0]);
      }
    } catch (error) {
      console.error('Failed to load product:', error);
      Alert.alert('Error', 'Failed to load product details');
    } finally {
      setLoading(false);
    }
  };

  const getExpiryStatus = (expiresAt: string | null) => {
    if (!expiresAt) return null;

    const expiry = new Date(expiresAt);
    const now = new Date();
    const daysUntil = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (daysUntil < 0) {
      return { color: '#f44336', text: 'Expired', emoji: '⚠️' };
    } else if (daysUntil === 0) {
      return { color: '#f44336', text: 'Expires today', emoji: '⚠️' };
    } else if (daysUntil <= 3) {
      return { color: '#ff9800', text: `${daysUntil}d left`, emoji: '⏰' };
    } else if (daysUntil <= 7) {
      return { color: '#ffc107', text: `${daysUntil}d left`, emoji: '📅' };
    } else {
      return { color: '#4CAF50', text: `${daysUntil}d left`, emoji: '✓' };
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  if (!product) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Product not found</Text>
      </View>
    );
  }

  const expiryStatus = getExpiryStatus(product.expires_at);
  const categoryEmoji = CATEGORY_EMOJIS[product.category] || CATEGORY_EMOJIS.other;

  return (
    <ScrollView style={styles.container}>
      {/* Product Image */}
      {product.image_url && (
        <Image
          source={{ uri: product.image_url }}
          style={styles.image}
          resizeMode="contain"
        />
      )}

      {/* Product Name */}
      <View style={styles.header}>
        <Text style={styles.productName}>{product.name}</Text>

        {/* Category Badge */}
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryEmoji}>{categoryEmoji}</Text>
          <Text style={styles.categoryText}>{product.category}</Text>
        </View>
      </View>

      {/* Basic Info Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Product Information</Text>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Quantity:</Text>
          <Text style={styles.infoValue}>
            {product.quantity} {product.unit || 'items'}
          </Text>
        </View>

        {product.price && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Price:</Text>
            <Text style={styles.infoValue}>€{product.price.toFixed(2)}</Text>
          </View>
        )}

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Expiry Date:</Text>
          <Text style={[styles.infoValue, expiryStatus && { color: expiryStatus.color }]}>
            {expiryStatus ? `${expiryStatus.emoji} ${expiryStatus.text}` : 'Not set'}
          </Text>
        </View>

        {product.expires_at && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}></Text>
            <Text style={styles.infoSubtext}>{formatDate(product.expires_at)}</Text>
          </View>
        )}
      </View>

      {/* Daily Use Tracking Section */}
      {product.is_daily_use && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📊 Daily Use Tracking</Text>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Daily Usage Rate:</Text>
            <Text style={styles.infoValue}>
              {product.daily_usage_rate} {product.unit || 'g'}/day
            </Text>
          </View>

          {product.daily_usage_rate && product.daily_usage_rate > 0 && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Days Remaining:</Text>
              <Text style={styles.infoValue}>
                {(product.quantity / product.daily_usage_rate).toFixed(1)} days
              </Text>
            </View>
          )}

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Restock Alert:</Text>
            <Text style={styles.infoValue}>
              {product.restock_threshold_days || 3} days before empty
            </Text>
          </View>

          {product.last_depletion_date && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Last Depleted:</Text>
              <Text style={styles.infoValue}>{formatDate(product.last_depletion_date)}</Text>
            </View>
          )}
        </View>
      )}

      {/* Nutritional Information Section */}
      {ingredient && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🥗 Nutritional Information (per 100g)</Text>

          <View style={styles.nutritionGrid}>
            <View style={styles.nutritionItem}>
              <Text style={styles.nutritionLabel}>Calories</Text>
              <Text style={styles.nutritionValue}>{ingredient.calories_per_100g}</Text>
            </View>
            <View style={styles.nutritionItem}>
              <Text style={styles.nutritionLabel}>Protein</Text>
              <Text style={styles.nutritionValue}>{ingredient.protein_per_100g}g</Text>
            </View>
            <View style={styles.nutritionItem}>
              <Text style={styles.nutritionLabel}>Carbs</Text>
              <Text style={styles.nutritionValue}>{ingredient.carbs_per_100g}g</Text>
            </View>
            <View style={styles.nutritionItem}>
              <Text style={styles.nutritionLabel}>Fat</Text>
              <Text style={styles.nutritionValue}>{ingredient.fat_per_100g}g</Text>
            </View>
            <View style={styles.nutritionItem}>
              <Text style={styles.nutritionLabel}>Fiber</Text>
              <Text style={styles.nutritionValue}>{ingredient.fiber_per_100g}g</Text>
            </View>
          </View>

          {ingredient.aldi_section && (
            <View style={[styles.infoRow, { marginTop: 16 }]}>
              <Text style={styles.infoLabel}>Aldi Section:</Text>
              <Text style={styles.infoValue}>{ingredient.aldi_section}</Text>
            </View>
          )}
        </View>
      )}

      {/* Category Traits Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🏷️ Product Traits</Text>

        <View style={styles.traitsContainer}>
          <View style={styles.traitBadge}>
            <Text style={styles.traitEmoji}>{categoryEmoji}</Text>
            <Text style={styles.traitText}>{product.category}</Text>
          </View>

          {product.is_daily_use && (
            <View style={styles.traitBadge}>
              <Text style={styles.traitEmoji}>📅</Text>
              <Text style={styles.traitText}>Daily Use</Text>
            </View>
          )}

          {expiryStatus && product.expires_at && (
            <View style={[styles.traitBadge, { backgroundColor: '#fff3cd' }]}>
              <Text style={styles.traitEmoji}>⏰</Text>
              <Text style={styles.traitText}>Has Expiry Date</Text>
            </View>
          )}

          {ingredient?.protein_per_100g && ingredient.protein_per_100g > 10 && (
            <View style={styles.traitBadge}>
              <Text style={styles.traitEmoji}>💪</Text>
              <Text style={styles.traitText}>High Protein</Text>
            </View>
          )}

          {ingredient?.fiber_per_100g && ingredient.fiber_per_100g > 5 && (
            <View style={styles.traitBadge}>
              <Text style={styles.traitEmoji}>🌾</Text>
              <Text style={styles.traitText}>High Fiber</Text>
            </View>
          )}
        </View>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
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
  errorText: {
    fontSize: 16,
    color: '#666',
  },
  image: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH * 0.6,
    backgroundColor: '#fff',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  productName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  categoryEmoji: {
    fontSize: 18,
    marginRight: 8,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#555',
    textTransform: 'capitalize',
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 12,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    textAlign: 'right',
  },
  infoSubtext: {
    fontSize: 12,
    color: '#999',
    flex: 1,
    textAlign: 'right',
  },
  nutritionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  nutritionItem: {
    flex: 1,
    minWidth: '30%',
    backgroundColor: '#f9f9f9',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  nutritionLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  nutritionValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  traitsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  traitBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
  },
  traitEmoji: {
    fontSize: 14,
    marginRight: 6,
  },
  traitText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1976d2',
  },
});
