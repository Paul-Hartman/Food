import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';

import { RootStackParamList, TabParamList } from '../types';

// Screens
import RecipesScreen from '../screens/RecipesScreen';
import MealPlanScreen from '../screens/MealPlanScreen';
import EnhancedRecipeDetailScreen from '../screens/EnhancedRecipeDetailScreen';
import CookingScreen from '../screens/CookingScreen';
import ShoppingScreen from '../screens/ShoppingScreen';
import PantryScreen from '../screens/PantryScreen';
import ComprehensiveNutritionScreen from '../screens/ComprehensiveNutritionScreen';
import CalendarScreen from '../screens/CalendarScreen';
import DecksScreen from '../screens/DecksScreen';
import FamilyScreen from '../screens/FamilyScreen';
import GameScreen from '../screens/GameScreen';
import AnalyticsScreen from '../screens/AnalyticsScreen';
import AlchemyScreen from '../screens/AlchemyScreen';
import JournalScreen from '../screens/JournalScreen';
import MealPrepScreen from '../screens/MealPrepScreen';
import BulkReviewScreen from '../screens/BulkReviewScreen';
import PantryProductDetailScreen from '../screens/PantryProductDetailScreen';

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

// Tab icons as emoji (simple for MVP)
const TabIcon = ({ emoji, focused }: { emoji: string; focused: boolean }) => (
  <Text style={{ fontSize: 24, opacity: focused ? 1 : 0.5 }}>{emoji}</Text>
);

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth: 1,
          borderTopColor: '#e0e0e0',
          paddingTop: 8,
          paddingBottom: 8,
          height: 85,
        },
        tabBarActiveTintColor: '#4CAF50',
        tabBarInactiveTintColor: '#757575',
        headerStyle: {
          backgroundColor: '#4CAF50',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: '600',
        },
      }}
    >
      <Tab.Screen
        name="Recipes"
        component={RecipesScreen}
        options={{
          title: 'Recipes',
          tabBarIcon: ({ focused }) => <TabIcon emoji="🍞" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="MealPlan"
        component={MealPlanScreen}
        options={{
          title: 'Plan',
          tabBarIcon: ({ focused }) => <TabIcon emoji="📅" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Shopping"
        component={ShoppingScreen}
        options={{
          title: 'Shopping',
          tabBarIcon: ({ focused }) => <TabIcon emoji="🛒" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Pantry"
        component={PantryScreen}
        options={{
          title: 'Pantry',
          tabBarIcon: ({ focused }) => <TabIcon emoji="🏠" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Nutrition"
        component={ComprehensiveNutritionScreen}
        options={{
          title: 'Nutrition',
          tabBarIcon: ({ focused }) => <TabIcon emoji="📊" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Calendar"
        component={CalendarScreen}
        options={{
          title: 'Calendar',
          tabBarIcon: ({ focused }) => <TabIcon emoji="📅" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Decks"
        component={DecksScreen}
        options={{
          title: 'Collections',
          tabBarIcon: ({ focused }) => <TabIcon emoji="📚" focused={focused} />,
        }}
      />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: '#4CAF50',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: '600',
          },
        }}
      >
        <Stack.Screen
          name="Main"
          component={TabNavigator}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="RecipeDetail"
          component={EnhancedRecipeDetailScreen}
          options={{ title: 'Recipe' }}
        />
        <Stack.Screen
          name="Cooking"
          component={CookingScreen}
          options={{
            title: 'Cooking',
            headerShown: false, // Full screen cooking mode
          }}
        />
        <Stack.Screen
          name="MealPrep"
          component={MealPrepScreen}
          options={{ title: 'Meal Prep' }}
        />
        <Stack.Screen
          name="Family"
          component={FamilyScreen}
          options={{ title: 'Family' }}
        />
        <Stack.Screen
          name="Game"
          component={GameScreen}
          options={{ title: 'Kitchen Quest' }}
        />
        <Stack.Screen
          name="Analytics"
          component={AnalyticsScreen}
          options={{ title: 'Analytics' }}
        />
        <Stack.Screen
          name="Alchemy"
          component={AlchemyScreen}
          options={{ title: 'Alchemy Lab' }}
        />
        <Stack.Screen
          name="Journal"
          component={JournalScreen}
          options={{ title: 'Journal' }}
        />
        <Stack.Screen
          name="BulkReview"
          component={BulkReviewScreen}
          options={{ title: 'Review Scanned Items' }}
        />
        <Stack.Screen
          name="PantryProductDetail"
          component={PantryProductDetailScreen}
          options={{ title: 'Product Details' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
