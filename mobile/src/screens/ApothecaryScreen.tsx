import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  StyleSheet,
  Modal,
  TouchableOpacity,
} from 'react-native';
import {
  APOTHECARY,
  searchApothecary,
  getIngredientsByOrigin,
  type ApothecaryIngredient,
  type IngredientOrigin,
} from '../services/apothecary-database';
import ApothecaryJar, { ApothecaryEntry } from '../components/ApothecaryJar';

/**
 * The Apothecary Screen
 *
 * Browse ingredients like wandering through an old apothecary shop.
 * Each jar tells a story - from ancient herbs to modern synthetics,
 * from traditional wisdom to cutting-edge science.
 *
 * "Every ingredient is a chapter in humanity's relationship with nature."
 */
export default function ApothecaryScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterOrigin, setFilterOrigin] = useState<IngredientOrigin | 'all'>('all');
  const [selectedIngredient, setSelectedIngredient] = useState<ApothecaryIngredient | null>(
    null
  );

  // Get filtered ingredients
  const getFilteredIngredients = () => {
    let ingredients = APOTHECARY;

    // Filter by origin
    if (filterOrigin !== 'all') {
      ingredients = getIngredientsByOrigin(filterOrigin);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      ingredients = searchApothecary(searchQuery);
    }

    return ingredients;
  };

  const filteredIngredients = getFilteredIngredients();

  // Count by origin
  const originCounts = APOTHECARY.reduce((acc, ing) => {
    acc[ing.origin] = (acc[ing.origin] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>🏺 The Apothecary</Text>
        <Text style={styles.subtitle}>
          A Cabinet of Curiosities & Knowledge
        </Text>
        <Text style={styles.count}>
          {filteredIngredients.length} of {APOTHECARY.length} ingredients
        </Text>
      </View>

      {/* Search Bar */}
      <View style={styles.searchBar}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search ingredients..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor="#999"
        />
      </View>

      {/* Origin Filters */}
      <View style={styles.filters}>
        <TouchableOpacity
          style={[styles.filterButton, filterOrigin === 'all' && styles.filterButtonActive]}
          onPress={() => setFilterOrigin('all')}
        >
          <Text style={[styles.filterText, filterOrigin === 'all' && styles.filterTextActive]}>
            All
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.filterButton, filterOrigin === 'plant' && styles.filterButtonActive]}
          onPress={() => setFilterOrigin('plant')}
        >
          <Text style={[styles.filterText, filterOrigin === 'plant' && styles.filterTextActive]}>
            🌿 Plant ({originCounts.plant || 0})
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.filterButton, filterOrigin === 'synthetic' && styles.filterButtonActive]}
          onPress={() => setFilterOrigin('synthetic')}
        >
          <Text style={[styles.filterText, filterOrigin === 'synthetic' && styles.filterTextActive]}>
            ⚗️ Synthetic ({originCounts.synthetic || 0})
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.filterButton, filterOrigin === 'fungal' && styles.filterButtonActive]}
          onPress={() => setFilterOrigin('fungal')}
        >
          <Text style={[styles.filterText, filterOrigin === 'fungal' && styles.filterTextActive]}>
            🍄 Fungal ({originCounts.fungal || 0})
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.filterButton, filterOrigin === 'bacterial' && styles.filterButtonActive]}
          onPress={() => setFilterOrigin('bacterial')}
        >
          <Text style={[styles.filterText, filterOrigin === 'bacterial' && styles.filterTextActive]}>
            🦠 Bacterial ({originCounts.bacterial || 0})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Ingredients List */}
      <FlatList
        data={filteredIngredients}
        renderItem={({ item }) => (
          <ApothecaryJar
            ingredient={item}
            compact
            onPress={() => setSelectedIngredient(item)}
          />
        )}
        keyExtractor={(item) => item.name}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No ingredients found</Text>
            <Text style={styles.emptySubtext}>
              Try a different search or filter
            </Text>
          </View>
        }
      />

      {/* Detail Modal */}
      <Modal
        visible={selectedIngredient !== null}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        {selectedIngredient && (
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <TouchableOpacity
                onPress={() => setSelectedIngredient(null)}
                style={styles.closeButton}
              >
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>
            </View>
            <ApothecaryEntry ingredient={selectedIngredient} />
          </View>
        )}
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFBF0',
  },
  header: {
    backgroundColor: '#8D6E63',
    padding: 20,
    paddingTop: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFF',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#FFECB3',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  count: {
    fontSize: 12,
    color: '#BCAAA4',
  },
  searchBar: {
    padding: 16,
  },
  searchInput: {
    backgroundColor: '#FFF',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#D4C5A9',
  },
  filters: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 8,
    flexWrap: 'wrap',
  },
  filterButton: {
    backgroundColor: '#FFF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#D4C5A9',
  },
  filterButtonActive: {
    backgroundColor: '#8D6E63',
    borderColor: '#8D6E63',
  },
  filterText: {
    fontSize: 12,
    color: '#6D4C41',
  },
  filterTextActive: {
    color: '#FFF',
  },
  list: {
    padding: 16,
  },
  empty: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#8D6E63',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#A1887F',
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    backgroundColor: '#8D6E63',
    padding: 16,
    alignItems: 'flex-end',
  },
  closeButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 28,
    color: '#FFF',
  },
});
