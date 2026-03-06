import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  Alert,
} from 'react-native';
import { api } from '../services/api';
import { useNavigation, CompositeNavigationProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { RootStackParamList, TabParamList } from '../types';

type DecksScreenNavigationProp = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'Decks'>,
  StackNavigationProp<RootStackParamList>
>;

interface Deck {
  id: number;
  name: string;
  description: string;
  recipe_count: number;
  icon?: string;
  color?: string;
}

interface Recipe {
  id: number;
  name: string;
  image_url?: string;
  prep_time_min?: number;
  cook_time_min?: number;
  cuisine?: string;
  source?: string;
}

export default function DecksScreen() {
  const navigation = useNavigation<DecksScreenNavigationProp>();
  const [decks, setDecks] = useState<Deck[]>([]);
  const [interested, setInterested] = useState<Recipe[]>([]);
  const [cookingDeck, setCookingDeck] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'decks' | 'interested' | 'tonight'>('decks');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [decksData, interestedData, cookingDeckData] = await Promise.all([
        api.getDecks(),
        api.getInterested(),
        api.getCookingDeck(),
      ]);

      setDecks(decksData);
      setInterested(interestedData);
      setCookingDeck(cookingDeckData);
    } catch (error) {
      console.error('Failed to load decks:', error);
      Alert.alert('Error', 'Failed to load cooking decks');
    } finally {
      setLoading(false);
    }
  }

  async function removeFromInterested(id: number) {
    try {
      await api.removeFromInterested(id);
      loadData();
    } catch (error) {
      console.error('Failed to remove from interested:', error);
      Alert.alert('Error', 'Failed to remove recipe');
    }
  }

  async function generateShoppingList() {
    try {
      // Extract recipe IDs from cooking deck (only local recipes, not MealDB)
      const localRecipes = cookingDeck.filter(recipe => recipe.source !== 'mealdb');
      const recipeIds = localRecipes.map(recipe => recipe.id);

      if (recipeIds.length === 0) {
        Alert.alert(
          'No Local Recipes',
          'Your cooking deck only contains external recipes. Shopping list generation currently works with local recipes only.',
          [{ text: 'OK' }]
        );
        return;
      }

      // Generate shopping list with pantry subtraction
      const result = await api.generateShopping(recipeIds, false, true);

      // Navigate to Shopping tab
      navigation.navigate('Shopping' as any);

      // Show success alert
      Alert.alert(
        'Shopping List Generated',
        `Added ${result.items_added} items to your shopping list (after subtracting pantry ingredients).`,
        [{ text: 'View List', onPress: () => navigation.navigate('Shopping' as any) }]
      );
    } catch (error) {
      console.error('Failed to generate shopping list:', error);
      Alert.alert('Error', 'Failed to generate shopping list');
    }
  }

  function renderDeck(deck: Deck) {
    return (
      <TouchableOpacity
        key={deck.id}
        style={[styles.deckCard, { backgroundColor: deck.color || '#4CAF50' }]}
        onPress={() => navigation.navigate('DeckDetail', { deckId: deck.id })}
      >
        <Text style={styles.deckIcon}>{deck.icon || '📚'}</Text>
        <Text style={styles.deckName}>{deck.name}</Text>
        <Text style={styles.deckDescription}>{deck.description}</Text>
        <Text style={styles.deckCount}>{deck.recipe_count} recipes</Text>
      </TouchableOpacity>
    );
  }

  function renderRecipeCard(recipe: Recipe, showRemoveBtn: boolean = false) {
    const totalTime = (recipe.prep_time_min || 0) + (recipe.cook_time_min || 0);

    return (
      <TouchableOpacity
        key={recipe.id}
        style={styles.recipeCard}
        onPress={() =>
          navigation.navigate('RecipeDetail', { recipeId: recipe.id })
        }
      >
        {recipe.image_url && (
          <Image source={{ uri: recipe.image_url }} style={styles.recipeImage} />
        )}
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeName} numberOfLines={2}>
            {recipe.name}
          </Text>
          <Text style={styles.recipeMeta}>
            {totalTime > 0 ? `${totalTime} min` : ''}{' '}
            {recipe.cuisine ? `• ${recipe.cuisine}` : ''}
          </Text>
        </View>
        {showRemoveBtn && (
          <TouchableOpacity
            style={styles.removeBtn}
            onPress={() => removeFromInterested(recipe.id)}
          >
            <Text style={styles.removeBtnText}>✕</Text>
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'decks' && styles.tabActive]}
          onPress={() => setActiveTab('decks')}
        >
          <Text style={[styles.tabText, activeTab === 'decks' && styles.tabTextActive]}>
            📚 Collections
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'interested' && styles.tabActive]}
          onPress={() => setActiveTab('interested')}
        >
          <Text style={[styles.tabText, activeTab === 'interested' && styles.tabTextActive]}>
            ❤️ Saved ({interested.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'tonight' && styles.tabActive]}
          onPress={() => setActiveTab('tonight')}
        >
          <Text style={[styles.tabText, activeTab === 'tonight' && styles.tabTextActive]}>
            🍳 Tonight ({cookingDeck.length})
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {activeTab === 'decks' && (
          <>
            {decks.length > 0 ? (
              <View style={styles.decksGrid}>{decks.map(deck => renderDeck(deck))}</View>
            ) : (
              <Text style={styles.emptyText}>No recipe collections available</Text>
            )}
          </>
        )}

        {activeTab === 'interested' && (
          <>
            {interested.length > 0 ? (
              interested.map(recipe => renderRecipeCard(recipe, true))
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyIcon}>❤️</Text>
                <Text style={styles.emptyText}>No saved recipes yet</Text>
                <Text style={styles.emptySubtext}>
                  Heart recipes you like to save them here
                </Text>
              </View>
            )}
          </>
        )}

        {activeTab === 'tonight' && (
          <>
            {cookingDeck.length > 0 ? (
              <>
                <TouchableOpacity
                  style={styles.generateShoppingButton}
                  onPress={generateShoppingList}
                >
                  <Text style={styles.generateShoppingIcon}>🛒</Text>
                  <Text style={styles.generateShoppingText}>Generate Shopping List</Text>
                  <Text style={styles.generateShoppingSubtext}>
                    {cookingDeck.length} recipe{cookingDeck.length > 1 ? 's' : ''} • Subtracts pantry items
                  </Text>
                </TouchableOpacity>
                {cookingDeck.map(recipe => renderRecipeCard(recipe))}
              </>
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyIcon}>🍳</Text>
                <Text style={styles.emptyText}>Tonight's cooking queue is empty</Text>
                <Text style={styles.emptySubtext}>
                  Swipe up on recipes to add them to tonight's menu
                </Text>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#4CAF50',
  },
  tabText: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#4CAF50',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  decksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  deckCard: {
    width: '48%',
    padding: 16,
    borderRadius: 12,
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deckIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  deckName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 6,
  },
  deckDescription: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
    marginBottom: 8,
  },
  deckCount: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '600',
  },
  recipeCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    alignItems: 'center',
  },
  recipeImage: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginRight: 12,
  },
  recipeInfo: {
    flex: 1,
  },
  recipeName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  recipeMeta: {
    fontSize: 12,
    color: '#6b7280',
  },
  removeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#fee2e2',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  removeBtnText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 60,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  generateShoppingButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  generateShoppingIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  generateShoppingText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
  },
  generateShoppingSubtext: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.9)',
  },
});
