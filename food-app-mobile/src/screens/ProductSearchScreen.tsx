import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Image,
  Modal,
} from 'react-native';
import {
  searchProducts,
  OpenFoodFactsProduct,
  formatNutritionData,
} from '../services/openfoodfacts';
import ProductNutritionCard from '../components/ProductNutritionCard';

export default function ProductSearchScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<OpenFoodFactsProduct[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<OpenFoodFactsProduct | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const products = await searchProducts(searchQuery);
      setResults(products);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderProduct = ({ item }: { item: OpenFoodFactsProduct }) => {
    const nutrition = formatNutritionData(item);

    return (
      <TouchableOpacity
        style={styles.productCard}
        onPress={() => setSelectedProduct(item)}
      >
        {item.image_small_url && (
          <Image
            source={{ uri: item.image_small_url }}
            style={styles.productImage}
            resizeMode="contain"
          />
        )}

        <View style={styles.productInfo}>
          <Text style={styles.productName} numberOfLines={2}>
            {item.product_name}
          </Text>
          {item.brands && (
            <Text style={styles.productBrand} numberOfLines={1}>
              {item.brands}
            </Text>
          )}
          {item.quantity && (
            <Text style={styles.productQuantity}>{item.quantity}</Text>
          )}

          <View style={styles.productScores}>
            {nutrition.nutriScore && (
              <View style={styles.scoreBadge}>
                <Text style={styles.scoreText}>
                  Nutri-Score: {nutrition.nutriScore.toUpperCase()}
                </Text>
              </View>
            )}
            {nutrition.novaGroup && (
              <View style={styles.scoreBadge}>
                <Text style={styles.scoreText}>NOVA: {nutrition.novaGroup}</Text>
              </View>
            )}
          </View>
        </View>

        <Text style={styles.arrow}>›</Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchBar}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search for food products..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
          autoCapitalize="none"
        />
        <TouchableOpacity
          style={styles.searchButton}
          onPress={handleSearch}
          disabled={loading}
        >
          <Text style={styles.searchButtonText}>
            {loading ? '...' : 'Search'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Results */}
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Searching OpenFoodFacts...</Text>
        </View>
      ) : results.length > 0 ? (
        <FlatList
          data={results}
          renderItem={renderProduct}
          keyExtractor={(item) => item.code}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      ) : searchQuery ? (
        <View style={styles.centered}>
          <Text style={styles.emptyText}>No products found</Text>
          <Text style={styles.emptySubtext}>Try a different search term</Text>
        </View>
      ) : (
        <View style={styles.centered}>
          <Text style={styles.emptyEmoji}>🔍</Text>
          <Text style={styles.emptyText}>Search for food products</Text>
          <Text style={styles.emptySubtext}>
            Search by name, brand, or product type
          </Text>
        </View>
      )}

      {/* Product Detail Modal */}
      <Modal
        visible={selectedProduct !== null}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Product Details</Text>
            <TouchableOpacity onPress={() => setSelectedProduct(null)}>
              <Text style={styles.closeButton}>✕</Text>
            </TouchableOpacity>
          </View>

          {selectedProduct && <ProductNutritionCard product={selectedProduct} />}
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
  searchBar: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    gap: 8,
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
  },
  searchButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    borderRadius: 8,
    justifyContent: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
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
  list: {
    padding: 16,
    gap: 12,
  },
  productCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  productImage: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginRight: 12,
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 4,
  },
  productBrand: {
    fontSize: 13,
    color: '#666',
    marginBottom: 2,
  },
  productQuantity: {
    fontSize: 12,
    color: '#999',
    marginBottom: 8,
  },
  productScores: {
    flexDirection: 'row',
    gap: 8,
  },
  scoreBadge: {
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  scoreText: {
    fontSize: 11,
    color: '#666',
    fontWeight: '500',
  },
  arrow: {
    fontSize: 24,
    color: '#ccc',
    marginLeft: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  closeButton: {
    fontSize: 28,
    color: '#666',
    fontWeight: '300',
  },
});
