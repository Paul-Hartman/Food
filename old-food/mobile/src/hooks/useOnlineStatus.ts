import { useState, useEffect } from 'react';
import { api } from '../services/api';

/**
 * Hook to detect online/offline status
 *
 * Checks server connectivity by pinging /api/health endpoint
 * Updates automatically every 30 seconds
 */
export const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [isChecking, setIsChecking] = useState<boolean>(true);

  const checkConnection = async () => {
    setIsChecking(true);
    try {
      const online = await api.checkServerHealth();
      setIsOnline(online);
    } catch {
      setIsOnline(false);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    // Initial check
    checkConnection();

    // Re-check every 30 seconds
    const interval = setInterval(checkConnection, 30000);

    return () => clearInterval(interval);
  }, []);

  return { isOnline, isChecking, refresh: checkConnection };
};
