/**
 * Bluetooth Scale Service
 *
 * Handles connection and communication with Hoto QWCFC001 smart kitchen scale.
 *
 * Features:
 * - BLE device scanning and connection
 * - Real-time weight polling (1.5s interval)
 * - Auto-disconnect after idle period
 * - Mock mode for testing without physical scale
 * - Weight stabilization detection
 *
 * Usage:
 * ```typescript
 * import { scaleService } from '@/services/BluetoothScaleService';
 *
 * // Connect to scale
 * await scaleService.connect();
 *
 * // Start polling
 * scaleService.startPolling((reading) => {
 *   console.log(`Weight: ${reading.weight}g`);
 * });
 *
 * // Stop polling
 * scaleService.stopPolling();
 * scaleService.disconnect();
 * ```
 */

import { BleManager, Device, Characteristic } from 'react-native-ble-plx';
import { PermissionsAndroid, Platform } from 'react-native';
import { Buffer } from 'buffer';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface ScaleReading {
  weight: number;           // Weight in grams
  unit: string;             // Always 'g' for now
  timestamp: number;        // Unix timestamp (ms)
  isStable: boolean;        // Weight stabilized for 2+ seconds
  batteryPercent?: number;  // Battery level (if available)
}

export interface ScaleConfig {
  type: 'bluetooth' | 'mock' | 'homeassistant';
  deviceId?: string;        // Cached device UUID
  deviceName?: string;      // User-friendly name
  pollingInterval: number;  // Milliseconds between reads
  autoDisconnectTimeout: number;  // Idle timeout (ms)
  stabilityThreshold: number;     // Weight change threshold (g)
  stabilityDuration: number;      // Stable duration required (ms)
}

// ============================================================================
// Constants
// ============================================================================

// Hoto QWCFC001 Scale BLE identifiers
// TODO: These need to be discovered via reverse engineering
// See: backend/docs/SCALE_BLE_PROTOCOL_DISCOVERY.md
const SCALE_NAME_PREFIX = 'HOTO';  // Device name starts with this
const XIAOMI_UUID = '95fe';        // Xiaomi service UUID (partial)

// PLACEHOLDER UUIDs - TO BE DISCOVERED
const WEIGHT_SERVICE_UUID = '0000fff0-0000-1000-8000-00805f9b34fb';  // Placeholder
const WEIGHT_CHAR_UUID = '0000fff1-0000-1000-8000-00805f9b34fb';     // Placeholder

// Default configuration
const DEFAULT_CONFIG: ScaleConfig = {
  type: 'mock',  // Start with mock for testing
  pollingInterval: 1500,        // 1.5 seconds
  autoDisconnectTimeout: 30000, // 30 seconds
  stabilityThreshold: 0.1,      // 0.1g change
  stabilityDuration: 2000,      // 2 seconds stable
};

// ============================================================================
// Bluetooth Scale Service
// ============================================================================

class BluetoothScaleService {
  private config: ScaleConfig;
  private bleManager: BleManager | null = null;
  private connectedDevice: Device | null = null;
  private isConnected: boolean = false;
  private isScanning: boolean = false;

  // Polling state
  private pollingInterval: NodeJS.Timeout | null = null;
  private lastReading: ScaleReading | null = null;
  private onWeightUpdate: ((reading: ScaleReading) => void) | null = null;

  // Stabilization tracking
  private stabilityHistory: number[] = [];
  private stableStartTime: number | null = null;

  // Mock simulation state
  private mockWeight: number = 0;
  private mockTargetWeight: number = 0;
  private mockDriftRate: number = 0.5; // g/s drift

  constructor(config: Partial<ScaleConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };

    // Only initialize BLE manager if not in mock mode
    if (this.config.type === 'bluetooth') {
      this.bleManager = new BleManager();
    }
  }

  // ==========================================================================
  // Public API
  // ==========================================================================

  /**
   * Request Bluetooth permissions (Android 31+)
   */
  async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'android' && Platform.Version >= 31) {
      const granted = await PermissionsAndroid.requestMultiple([
        PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN,
        PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
      ]);

      const allGranted = Object.values(granted).every(
        status => status === PermissionsAndroid.RESULTS.GRANTED
      );

      if (!allGranted) {
        console.warn('⚠️  Not all Bluetooth permissions granted');
      }

      return allGranted;
    }

    return true; // iOS handled by Info.plist
  }

  /**
   * Scan for nearby scale devices
   * @param timeoutMs Scan timeout in milliseconds
   * @returns Found device or null
   */
  async scanForScale(timeoutMs: number = 10000): Promise<Device | null> {
    if (this.config.type === 'mock') {
      console.log('📱 Mock mode: Simulating scale discovery');
      return null; // Mock mode doesn't need real device
    }

    if (!this.bleManager) {
      throw new Error('BLE Manager not initialized');
    }

    console.log(`🔍 Scanning for ${SCALE_NAME_PREFIX} scale...`);
    this.isScanning = true;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.bleManager!.stopDeviceScan();
        this.isScanning = false;
        console.log('⏱️  Scan timeout - no scale found');
        resolve(null);
      }, timeoutMs);

      this.bleManager!.startDeviceScan(null, null, (error, device) => {
        if (error) {
          clearTimeout(timeout);
          this.bleManager!.stopDeviceScan();
          this.isScanning = false;
          console.error('❌ BLE scan error:', error);
          reject(error);
          return;
        }

        // Check if device name matches scale
        if (device && device.name?.includes(SCALE_NAME_PREFIX)) {
          clearTimeout(timeout);
          this.bleManager!.stopDeviceScan();
          this.isScanning = false;
          console.log(`✅ Found scale: ${device.name} (${device.id})`);
          resolve(device);
        }
      });
    });
  }

  /**
   * Connect to scale (BLE or mock)
   * @param device Optional device to connect to (auto-scans if not provided)
   */
  async connect(device?: Device): Promise<void> {
    if (this.config.type === 'mock') {
      return this.connectMock();
    } else if (this.config.type === 'bluetooth') {
      return this.connectBluetooth(device);
    } else {
      throw new Error(`Connection type ${this.config.type} not implemented`);
    }
  }

  /**
   * Disconnect from scale
   */
  async disconnect(): Promise<void> {
    this.stopPolling();

    if (this.connectedDevice) {
      await this.connectedDevice.cancelConnection();
      this.connectedDevice = null;
    }

    this.isConnected = false;
    console.log('🔌 Scale disconnected');
  }

  /**
   * Start polling for weight updates
   * @param callback Function called with each weight reading
   */
  startPolling(callback: (reading: ScaleReading) => void): void {
    if (this.pollingInterval) {
      console.warn('⚠️  Polling already started');
      return;
    }

    this.onWeightUpdate = callback;

    console.log(`▶️  Started polling (${this.config.pollingInterval}ms interval)`);

    this.pollingInterval = setInterval(async () => {
      try {
        const reading = await this.readWeight();

        // Track stabilization
        this.updateStabilization(reading.weight);
        reading.isStable = this.isWeightStable();

        this.lastReading = reading;

        if (this.onWeightUpdate) {
          this.onWeightUpdate(reading);
        }
      } catch (error) {
        console.error('❌ Polling error:', error);
      }
    }, this.config.pollingInterval);
  }

  /**
   * Stop polling for weight updates
   */
  stopPolling(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
      console.log('⏸️  Stopped polling');
    }
  }

  /**
   * Send tare command to scale (zero out)
   * Note: This may not be supported by Hoto scale
   */
  async tare(): Promise<void> {
    if (this.config.type === 'mock') {
      this.mockWeight = 0;
      console.log('⚖️  Mock scale tared (zeroed)');
      return;
    }

    // TODO: Implement tare command for BLE scale if supported
    console.warn('⚠️  Tare command not implemented for BLE scale');
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): {
    connected: boolean;
    type: string;
    deviceName?: string;
    lastReading?: ScaleReading;
  } {
    return {
      connected: this.isConnected,
      type: this.config.type,
      deviceName: this.config.deviceName || (this.connectedDevice?.name),
      lastReading: this.lastReading || undefined,
    };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<ScaleConfig>): void {
    this.config = { ...this.config, ...config };
  }

  // ==========================================================================
  // Private Methods - Bluetooth Connection
  // ==========================================================================

  private async connectBluetooth(device?: Device): Promise<void> {
    if (!this.bleManager) {
      throw new Error('BLE Manager not initialized');
    }

    // Scan for device if not provided
    if (!device) {
      const foundDevice = await this.scanForScale();
      if (!foundDevice) {
        throw new Error('Scale not found');
      }
      device = foundDevice;
    }

    console.log(`🔗 Connecting to ${device.name}...`);

    try {
      // Connect to device
      this.connectedDevice = await device.connect();
      await this.connectedDevice.discoverAllServicesAndCharacteristics();

      console.log('✅ Connected to scale');
      console.log('🔍 Discovering GATT services...');

      // List all services and characteristics for debugging
      const services = await this.connectedDevice.services();
      for (const service of services) {
        console.log(`  Service: ${service.uuid}`);
        const characteristics = await service.characteristics();
        for (const char of characteristics) {
          console.log(`    Characteristic: ${char.uuid} (${char.isNotifiable ? 'notifiable' : 'not notifiable'})`);
        }
      }

      // TODO: Subscribe to weight notifications
      // This requires knowing the correct service and characteristic UUIDs
      // await this.subscribeToWeightNotifications();

      this.isConnected = true;
      this.config.deviceId = device.id;
      this.config.deviceName = device.name || undefined;

    } catch (error) {
      console.error('❌ Connection failed:', error);
      this.connectedDevice = null;
      throw error;
    }
  }

  private async subscribeToWeightNotifications(): Promise<void> {
    if (!this.connectedDevice) {
      throw new Error('No device connected');
    }

    console.log('📡 Subscribing to weight notifications...');

    try {
      await this.connectedDevice.monitorCharacteristicForService(
        WEIGHT_SERVICE_UUID,
        WEIGHT_CHAR_UUID,
        (error, characteristic) => {
          if (error) {
            console.error('❌ Weight notification error:', error);
            return;
          }

          if (characteristic && characteristic.value) {
            const reading = this.parseWeightData(characteristic.value);

            if (this.onWeightUpdate) {
              this.onWeightUpdate(reading);
            }
          }
        }
      );

      console.log('✅ Subscribed to weight notifications');
    } catch (error) {
      console.error('❌ Failed to subscribe to notifications:', error);
      throw error;
    }
  }

  private parseWeightData(base64Data: string): ScaleReading {
    // Parse BLE notification data
    // TODO: Actual format needs to be discovered via reverse engineering
    // Likely format: uint16 big-endian, 0.1g precision

    const buffer = Buffer.from(base64Data, 'base64');

    // Placeholder parsing (NEEDS TO BE UPDATED)
    let weight = 0;
    let isStable = false;

    if (buffer.length >= 2) {
      // Assume uint16 big-endian, 0.1g precision
      weight = buffer.readUInt16BE(0) / 10;
    }

    if (buffer.length >= 3) {
      // Assume byte 2 has stability flag (bit 0)
      isStable = (buffer[2] & 0x01) === 0x01;
    }

    return {
      weight,
      unit: 'g',
      timestamp: Date.now(),
      isStable,
    };
  }

  // ==========================================================================
  // Private Methods - Mock Mode
  // ==========================================================================

  private async connectMock(): Promise<void> {
    console.log('🎭 Connecting to mock scale...');

    // Simulate connection delay
    await new Promise(resolve => setTimeout(resolve, 500));

    this.isConnected = true;
    this.mockWeight = 0;
    this.mockTargetWeight = 0;

    console.log('✅ Mock scale connected');
  }

  private async readWeight(): Promise<ScaleReading> {
    if (this.config.type === 'mock') {
      return this.readWeightMock();
    }

    // TODO: Implement BLE weight reading
    // For now, return last known weight
    return this.lastReading || {
      weight: 0,
      unit: 'g',
      timestamp: Date.now(),
      isStable: false,
    };
  }

  private readWeightMock(): ScaleReading {
    // Simulate realistic weight behavior with drift
    const drift = (Math.random() - 0.5) * this.mockDriftRate;
    this.mockWeight = Math.max(0, this.mockWeight + drift);

    // Occasionally simulate weight changes (adding/removing items)
    if (Math.random() < 0.02) { // 2% chance per poll
      this.mockTargetWeight = Math.random() * 1000; // Random target 0-1000g
    }

    // Gradually move toward target weight
    if (Math.abs(this.mockWeight - this.mockTargetWeight) > 1) {
      const direction = this.mockTargetWeight > this.mockWeight ? 1 : -1;
      this.mockWeight += direction * 5; // 5g/poll change rate
    }

    return {
      weight: parseFloat(this.mockWeight.toFixed(1)),
      unit: 'g',
      timestamp: Date.now(),
      isStable: Math.abs(this.mockWeight - this.mockTargetWeight) < 2,
    };
  }

  // ==========================================================================
  // Private Methods - Weight Stabilization
  // ==========================================================================

  private updateStabilization(weight: number): void {
    const now = Date.now();

    // Add to history (keep last 10 readings)
    this.stabilityHistory.push(weight);
    if (this.stabilityHistory.length > 10) {
      this.stabilityHistory.shift();
    }

    // Check if weight is stable
    if (this.stabilityHistory.length >= 3) {
      const recentWeights = this.stabilityHistory.slice(-3);
      const maxDiff = Math.max(...recentWeights) - Math.min(...recentWeights);

      if (maxDiff < this.config.stabilityThreshold) {
        // Weight is stable
        if (!this.stableStartTime) {
          this.stableStartTime = now;
        }
      } else {
        // Weight is changing
        this.stableStartTime = null;
      }
    }
  }

  private isWeightStable(): boolean {
    if (!this.stableStartTime) {
      return false;
    }

    const stableDuration = Date.now() - this.stableStartTime;
    return stableDuration >= this.config.stabilityDuration;
  }

  // ==========================================================================
  // Static Methods
  // ==========================================================================

  /**
   * Calculate net weight (gross - tare)
   */
  static calculateNetWeight(grossWeight: number, tareWeight: number): number {
    return Math.max(0, grossWeight - tareWeight);
  }
}

// ============================================================================
// Singleton Export
// ============================================================================

export const scaleService = new BluetoothScaleService({
  type: 'mock', // Start with mock mode for development
});

export default scaleService;
