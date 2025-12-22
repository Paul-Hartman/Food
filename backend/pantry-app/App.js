import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { Text } from 'react-native';

// Screens
import PantryScreen from './screens/PantryScreen';
import SpiceRackScreen from './screens/SpiceRackScreen';
import ScannerScreen from './screens/ScannerScreen';
import AddProductScreen from './screens/AddProductScreen';
import ProductDetailScreen from './screens/ProductDetailScreen';
import ProductBrowserScreen from './screens/ProductBrowserScreen';
import KitchenToolsScreen from './screens/KitchenToolsScreen';
import CookingScreen from './screens/CookingScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Tab icon component
function TabIcon({ name, focused }) {
  const icons = {
    Pantry: '🥫',
    Cook: '🔥',
    Shop: '🛒',
    Kitchen: '🍳',
    Scan: '📷',
  };
  const size = focused ? 28 : 24;
  return (
    <Text style={{ fontSize: size }}>
      {icons[name] || '📦'}
    </Text>
  );
}

// Main tab navigator
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused }) => <TabIcon name={route.name} focused={focused} />,
        tabBarActiveTintColor: '#4CAF50',
        tabBarInactiveTintColor: 'gray',
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth: 1,
          borderTopColor: '#e0e0e0',
          paddingBottom: 5,
          paddingTop: 5,
          height: 60,
        },
        headerStyle: {
          backgroundColor: '#4CAF50',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen
        name="Pantry"
        component={PantryScreen}
        options={{ title: 'Pantry' }}
      />
      <Tab.Screen
        name="Cook"
        component={CookingScreen}
        options={{
          title: 'Cook Tonight',
          headerStyle: { backgroundColor: '#1a1a2e' },
        }}
      />
      <Tab.Screen
        name="Shop"
        component={ProductBrowserScreen}
        options={{ title: 'Products' }}
      />
      <Tab.Screen
        name="Kitchen"
        component={KitchenToolsScreen}
        options={{
          title: 'Kitchen Tools',
          headerStyle: { backgroundColor: '#607D8B' },
        }}
      />
      <Tab.Screen
        name="Scan"
        component={ScannerScreen}
        options={{ title: 'Scan Barcode' }}
      />
    </Tab.Navigator>
  );
}

// Root stack navigator
export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator>
        <Stack.Screen
          name="Main"
          component={MainTabs}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="AddProduct"
          component={AddProductScreen}
          options={{
            title: 'Add Product',
            headerStyle: { backgroundColor: '#4CAF50' },
            headerTintColor: '#fff',
          }}
        />
        <Stack.Screen
          name="ProductDetail"
          component={ProductDetailScreen}
          options={{
            title: 'Product Details',
            headerStyle: { backgroundColor: '#4CAF50' },
            headerTintColor: '#fff',
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
