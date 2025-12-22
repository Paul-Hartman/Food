import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import AppNavigator from './src/navigation/AppNavigator';
import { initDatabase } from './src/database/db';

export default function App() {
  const [isDbReady, setIsDbReady] = useState(false);

  useEffect(() => {
    const setupApp = async () => {
      try {
        // Initialize database for offline storage
        await initDatabase();
        setIsDbReady(true);
      } catch (error) {
        console.error('Failed to initialize database:', error);
        // Still show app even if DB init fails
        setIsDbReady(true);
      }
    };

    setupApp();
  }, []);

  if (!isDbReady) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#4CAF50' }}>
        <ActivityIndicator size="large" color="#fff" />
        <Text style={{ marginTop: 16, color: '#fff', fontSize: 16 }}>Preparing app...</Text>
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar style="light" />
      <AppNavigator />
    </GestureHandlerRootView>
  );
}
