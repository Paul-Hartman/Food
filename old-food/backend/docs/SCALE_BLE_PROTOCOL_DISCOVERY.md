# Hoto QWCFC001 Scale - BLE Protocol Discovery Guide

## Overview

The Hoto QWCFC001 smart kitchen scale uses Xiaomi's proprietary Bluetooth Low Energy (BLE) protocol. To integrate it with the mobile app, we need to discover:

1. **GATT Service UUID** - The BLE service that provides weight data
2. **Characteristic UUID** - The characteristic that notifies weight changes
3. **Data Format** - How weight values are encoded in the BLE messages

**Current Status**: ⚠️ UUIDs and data format are UNKNOWN and need to be discovered.

---

## Known Information

From [Home Assistant BLE Monitor Issue #424](https://github.com/custom-components/ble_monitor/issues/424):

- **Device Model**: QWCFC001
- **Manufacturer**: Hoto (Xiaomi ecosystem)
- **Bluetooth**: BLE 4.0
- **Xiaomi Device ID**: 0x8011 (hex)
- **Xiaomi UUID**: 0x95fe
- **Connection Type**: ACTIVE (not passive advertising)
- **Range**: ~8 meters
- **Capacity**: 3kg (3000g)
- **Precision**: 0.1g

**Critical**: The scale does NOT broadcast weight via BLE advertisements. You MUST establish an active GATT connection to read weight data.

---

## Discovery Methods

### Method 1: Android BLE Sniffing (Recommended)

**Requirements**:
- Android phone with Developer Options
- Xiaomi Home app (Mi Home) installed
- Wireshark on PC
- USB cable for transferring log

**Steps**:

1. **Enable BLE snoop logging**:
   ```
   Settings → System → Developer Options
   → Enable Bluetooth HCI snoop log
   ```

2. **Connect scale to Mi Home app**:
   - Open Mi Home app
   - Pair/connect to Hoto scale
   - Place various weights on scale (100g, 250g, 500g, 1000g)
   - Observe weight changes in app

3. **Stop snoop logging and extract**:
   ```bash
   # Connect phone via USB
   adb pull /sdcard/Android/data/btsnoop_hci.log
   ```

4. **Analyze in Wireshark**:
   - Open `btsnoop_hci.log` in Wireshark
   - Filter: `bluetooth.addr == [SCALE_MAC_ADDRESS]`
   - Look for GATT Read/Write/Notify operations
   - Identify service and characteristic UUIDs
   - Examine data payloads for weight patterns

**What to look for**:
- Service UUID in GATT service discovery
- Characteristic UUID with "Notify" property enabled
- Data patterns correlating with known weights:
  ```
  100g → [0x00, 0x64] or [0x03, 0xE8] (hex for 100 or 1000 for 0.1g precision)
  500g → [0x01, 0xF4] or [0x13, 0x88]
  ```

---

### Method 2: nRF Connect App (Manual Exploration)

**Requirements**:
- Android/iOS phone
- nRF Connect app (free)

**Steps**:

1. **Install nRF Connect**:
   - [Android](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp)
   - [iOS](https://apps.apple.com/app/nrf-connect-for-mobile/id1054362403)

2. **Scan for scale**:
   - Open nRF Connect
   - Tap "Scan"
   - Look for device named "HOTO" or similar
   - Note MAC address

3. **Connect and explore**:
   - Tap "CONNECT"
   - Wait for service discovery
   - Expand each service
   - Look for characteristics with these properties:
     - **Read** - Can read current value
     - **Notify** - Sends updates automatically
     - **Write** - Can send commands (e.g., tare)

4. **Enable notifications**:
   - Find characteristics with **Notify** property
   - Tap notification icon (triple arrows)
   - Place weights on scale
   - Observe value changes

5. **Decode data**:
   - Screenshot hex values for each weight
   - Compare patterns:
     ```
     Empty:  0x00 0x00 0x00
     100g:   0x?? 0x?? 0x??
     500g:   0x?? 0x?? 0x??
     1000g:  0x?? 0x?? 0x??
     ```

---

### Method 3: Community Research

**Resources to check**:

1. **Home Assistant Forums**:
   - [BLE Monitor Component](https://github.com/custom-components/ble_monitor)
   - Search for "Hoto" or "QWCFC001"

2. **GitHub Issues**:
   - [Issue #424 - Hoto Scale Support](https://github.com/custom-components/ble_monitor/issues/424)
   - [ble2mqtt Issue #36](https://github.com/devbis/ble2mqtt/issues/36)

3. **OpenScale Project**:
   - [Reverse Engineering Guide](https://github.com/oliexdev/openScale/wiki/How-to-reverse-engineer-a-Bluetooth-4.x-scale)
   - Community database of scale protocols

4. **Reddit Communities**:
   - r/homeassistant
   - r/bluetooth
   - r/ReverseEngineering

**Ask for help with**:
- "Anyone reverse-engineered Hoto QWCFC001 scale BLE protocol?"
- Share any data you've captured

---

## Expected Data Format

### Common BLE Scale Data Formats

**Option A: uint16 Big-Endian (Most common)**
```
Bytes: [HIGH, LOW]
Example: 500g → [0x01, 0xF4]
Decoding: (0x01 << 8) | 0xF4 = 500
```

**Option B: uint16 Little-Endian**
```
Bytes: [LOW, HIGH]
Example: 500g → [0xF4, 0x01]
Decoding: (0x01 << 8) | 0xF4 = 500
```

**Option C: uint16 with 0.1g Precision**
```
Bytes: [HIGH, LOW] / 10
Example: 50.5g → [0x01, 0xF9] (0x01F9 = 505)
Decoding: ((0x01 << 8) | 0xF9) / 10 = 50.5g
```

**Option D: uint32 with Additional Flags**
```
Bytes: [FLAGS, RESERVED, WEIGHT_HIGH, WEIGHT_LOW]
Example: Stable 500g → [0x01, 0x00, 0x01, 0xF4]
Bit 0 of FLAGS: 1 = stable, 0 = changing
```

### Stability Flag

Many scales include a "stable" indicator:
- Bit in status byte (e.g., byte 0, bit 0)
- `0x01` = weight stable
- `0x00` = weight changing

---

## Integration Steps (After Discovery)

Once UUIDs and data format are known:

### 1. Update BluetoothScaleService.ts

```typescript
// Replace placeholder UUIDs
const WEIGHT_SERVICE_UUID = '[DISCOVERED_SERVICE_UUID]';
const WEIGHT_CHAR_UUID = '[DISCOVERED_CHARACTERISTIC_UUID]';

// Update data parser
private parseWeightData(base64Data: string): ScaleReading {
  const buffer = Buffer.from(base64Data, 'base64');

  // Example for uint16 big-endian, 0.1g precision
  const rawWeight = buffer.readUInt16BE(0);
  const weight = rawWeight / 10;

  // Example stability flag (byte 2, bit 0)
  const isStable = (buffer[2] & 0x01) === 0x01;

  return {
    weight,
    unit: 'g',
    timestamp: Date.now(),
    isStable,
  };
}
```

### 2. Test with Physical Scale

```typescript
// Change config from mock to bluetooth
scaleService.updateConfig({ type: 'bluetooth' });

// Connect and test
await scaleService.connect();
scaleService.startPolling((reading) => {
  console.log(`Weight: ${reading.weight}g (Stable: ${reading.isStable})`);
});
```

### 3. Validate Accuracy

- Test with known weights (calibration weights)
- Verify stability detection works
- Test edge cases (0g, max weight, negative drift)

---

## Troubleshooting

### Scale not found during scan
- Ensure scale is powered on (place item on it)
- Scale may auto-sleep - wake it up
- Check Bluetooth is enabled on phone
- Try resetting scale (remove batteries for 30s)

### Can't connect to scale
- Scale may only allow one connection at a time
- Disconnect from Mi Home app first
- Try forgetting/re-pairing in phone settings

### No weight notifications
- Wrong characteristic UUID
- Notifications not enabled (need to write 0x01 to descriptor)
- Scale requires authentication/pairing

### Data looks random/incorrect
- Wrong byte order (try little-endian vs big-endian)
- Wrong data type (uint16 vs uint32)
- Missing scaling factor (divide by 10 or 100)

---

## Fallback Options

If discovery fails after 2 days of effort:

### Option A: Use Mock Mode for MVP
- BluetoothScaleService already has full mock implementation
- Allows testing all features without physical scale
- Can revisit BLE integration later

### Option B: Use Different Scale
Consider scales with documented protocols:
- **Acaia Coffee Scales** - Well-documented BLE protocol
- **Xiaomi Mi Smart Scale 2** - Community reverse-engineered
- **Generic BLE scales** - Many use standard Weight Scale Service (0x181D)

### Option C: HTTP API Scale
If you can't get BLE working, consider:
- WiFi-enabled scale with HTTP API
- ESP32 + load cell + Home Assistant
- Simpler integration (no BLE complexity)

---

## Success Criteria

You've successfully discovered the protocol when:

- ✅ Can scan and find scale by name
- ✅ Can connect to scale via BLE
- ✅ Can receive weight notifications in real-time
- ✅ Weight values match physical measurements (±0.1g)
- ✅ Stability flag correctly detects weight changes
- ✅ Connection is stable for 5+ minutes
- ✅ Can reconnect after disconnection

---

## Next Steps

After discovering the protocol:

1. Update `BluetoothScaleService.ts` with real UUIDs and parser
2. Test with ScaleMeasureModal (recipe measuring)
3. Test with ScaleWeighModal (pantry tracking)
4. Document findings in this file
5. (Optional) Contribute to Home Assistant BLE Monitor project

---

## References

- [Home Assistant BLE Monitor - Hoto Scale Issue](https://github.com/custom-components/ble_monitor/issues/424)
- [OpenScale BLE Reverse Engineering Guide](https://github.com/oliexdev/openScale/wiki/How-to-reverse-engineer-a-Bluetooth-4.x-scale)
- [Xiaomi MiScale Reverse Engineering](https://github.com/oliexdev/openScale/blob/master/android_app/app/src/main/java/com/health/openscale/core/bluetooth/BluetoothMiScale.java)
- [BLE Specification - Weight Scale Service](https://www.bluetooth.com/specifications/specs/weight-scale-service-1-0/)
