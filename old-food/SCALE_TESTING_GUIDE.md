# Scale Integration Testing Guide

**Status**: ✅ Ready to test
**Servers Running**:
- Backend: http://192.168.2.38:5025
- Expo Web: http://localhost:8081
- Expo Dev: Metro bundler active (811 modules compiled successfully)

---

## Test 1: Web Browser Testing

### Step 1: Open the App
1. Open your web browser
2. Navigate to: **http://localhost:8081**
3. The Food App should load

### Step 2: Navigate to Pancake Recipe
1. **Option A - Direct URL** (if Expo Router supports it):
   - Try: `http://localhost:8081/recipe/1125`

2. **Option B - Manual Navigation**:
   - Tap the **Recipes** tab at the bottom
   - Search for "Pancake" or "Fluffy Buttermilk"
   - Tap on **Recipe ID 1125** ("Fluffy Buttermilk Pancakes (Scale Demo)")

### Step 3: Test Scale Modal on Step 1 (Dry Ingredients)
The recipe should show **Step 1: Measure Dry Ingredients** with ingredient chips below the instruction text:

**Expected Ingredient Chips**:
- 250g flour
- 25g sugar
- 12g baking powder
- 3g baking soda
- 5g salt

**Test Actions**:
1. **Tap "250g flour" chip**
   - ScaleMeasureModal should open fullscreen
   - Header shows: "Measuring flour"
   - Target displays: "250g"
   - Live weight starts at: "0.0g"

2. **Watch Mock Scale Simulation**:
   - Weight should gradually increase: 0g → 50g → 100g → 150g → 200g → 245g → 250g
   - Progress bar fills from left to right (blue)
   - When weight reaches 248-252g (±2g tolerance):
     - Progress bar turns **green**
     - Status text: "Perfect! Weight stable ✓"
     - Screen pulses slightly (animation)
     - *Note: Web doesn't support haptic feedback, but mobile will*

3. **Tap "DONE" button**:
   - Modal closes
   - "250g flour" chip turns **green** with ✓ checkmark
   - Ingredient marked as measured

4. **Repeat for Other Ingredients**:
   - Tap "25g sugar" → Watch weight climb to 25g → Done
   - Tap "12g baking powder" → Watch weight climb to 12g → Done
   - Continue with baking soda and salt

### Step 4: Test Step 3 (Wet Ingredients)
Navigate to **Step 3: Measure Wet Ingredients**:

**Expected Ingredient Chips**:
- 360ml buttermilk (or 360g)
- 2 eggs (~100g)
- 50g melted butter
- 5ml vanilla extract

Repeat the same tapping/measuring process.

### Step 5: Test TARE Button
1. Open any ingredient chip
2. Wait for weight to increase to ~100g
3. Tap **"TARE" button**:
   - Weight should reset to 0.0g
   - Progress bar resets
   - You can now measure from zero again

### Step 6: Test Over-Target Warning
1. Open any ingredient (e.g., "25g sugar")
2. Wait for weight to exceed 27g (target + 2g)
3. **Expected Behavior**:
   - Progress bar turns **orange**
   - Status text: "Too much! Remove X.Xg"
   - This shows the overflow warning system works

---

## Test 2: Android Emulator Testing

### Prerequisites
- Android emulator running (Android Studio or Expo-compatible emulator)
- Expo Go app installed on emulator

### Step 1: Launch on Android
1. In your terminal where Expo is running, press **`a`**
   - This opens the app on Android emulator
   - OR scan the QR code with Expo Go app

2. Wait for app to build and install
   - First launch may take 1-2 minutes

### Step 2: Repeat Web Tests with Mobile Features
Follow the same test steps as web, but pay attention to **mobile-specific features**:

**Haptic Feedback** (not available in web):
- When weight reaches target → Device vibrates (success pattern)
- When over target → Device vibrates (warning pattern)
- When tapping TARE → Light vibration

**Performance**:
- Weight updates should be smooth (1.5s polling)
- Modal animations should be fluid
- No lag when tapping ingredient chips

### Step 3: Test Offline Mode
1. In emulator, swipe down and **disable WiFi**
2. Retry measuring ingredients:
   - Scale should still work (mock mode doesn't need backend)
   - Measurements should save to local SQLite
   - Backend sync will happen when WiFi returns

---

## Expected Results Checklist

### Visual Elements
- [ ] Ingredient chips display parsed amounts from step text
- [ ] Unmeasured chips: White background, dark text
- [ ] Measured chips: Green background, white text, ✓ checkmark
- [ ] Modal opens with smooth slide animation
- [ ] Large weight display (80pt font, easy to read)
- [ ] Progress bar animates smoothly
- [ ] Green header bar with "Measuring [ingredient]" title

### Functional Elements
- [ ] Weight increases gradually (mock simulation)
- [ ] Progress bar fills proportionally to target
- [ ] Target reached detection (±2g tolerance)
- [ ] Pulse animation when target reached
- [ ] Haptic feedback on mobile (target + over-target + tare)
- [ ] TARE button zeros the scale
- [ ] DONE button marks ingredient complete
- [ ] ✕ button cancels and closes modal
- [ ] All 9 ingredients can be measured (5 dry + 4 wet)

### Data Persistence
- [ ] Measured ingredients stay checked after modal closes
- [ ] Unmeasured ingredients remain white/unmarked
- [ ] Can re-measure an ingredient by tapping it again

---

## Troubleshooting

### Modal Doesn't Open
**Problem**: Tapping ingredient chip does nothing

**Solutions**:
1. Check browser/metro console for errors:
   - Look for import errors related to ScaleMeasureModal
   - Look for "ingredient" undefined errors

2. Verify ingredient parsing worked:
   - Open browser DevTools → Console
   - Look for parsed ingredients in logs

3. Check CookingScreen.tsx:
   - Verify `ScaleMeasureModal` is imported
   - Verify `handleIngredientTap` function exists

### Weight Not Updating
**Problem**: Weight stays at 0.0g

**Solutions**:
1. Check mock scale is enabled:
   - BluetoothScaleService should auto-use mock mode
   - Look for console logs: "Mock scale enabled"

2. Check polling started:
   - Modal should call `scaleService.startPolling()` on open
   - Check for polling interval errors

3. Restart Expo dev server:
   ```bash
   # Press Ctrl+C in terminal
   npm start
   ```

### "Connecting..." Stuck
**Problem**: Modal shows "Connecting..." forever

**Solutions**:
1. Mock mode should connect instantly (no real Bluetooth)
2. Check console for permission errors
3. Verify `scaleService.connect()` completes successfully

### Ingredient Chips Not Showing
**Problem**: No chips appear below step instructions

**Solutions**:
1. Verify step has measurable ingredients:
   - Step 1 should show 5 chips (dry ingredients)
   - Step 3 should show 4 chips (wet ingredients)
   - Step 2, 4-11 may have fewer or no chips (not all steps have measurable ingredients)

2. Check `parseIngredients()` function:
   - Regex patterns should match "250g flour" style text
   - Check recipe step text format

### Backend Errors
**Problem**: Console shows API errors

**Solutions**:
1. Verify backend is running:
   ```bash
   curl http://192.168.2.38:5025/api/health
   # Should return: {"status": "ok"}
   ```

2. Check backend logs:
   - Read: `C:\Users\paulh\AppData\Local\Temp\claude\C--Users-paulh-Documents-Lotus-Eater-Machine-food\tasks\b8b081e.output`
   - Look for SQL errors or missing tables

3. Verify migration ran:
   ```bash
   cd backend
   sqlite3 food.db "SELECT COUNT(*) FROM scale_containers;"
   # Should return: 5
   ```

---

## What's Working vs. Not Yet Implemented

### ✅ Fully Working (Test These!)

**Core Features**:
- Ingredient parsing from recipe step text
- Ingredient chip UI (unmeasured/measured states)
- ScaleMeasureModal opens on tap
- Live weight display with mock simulation
- Progress bar with color states (blue/green/orange)
- Pulse animation on target reached
- TARE button functionality
- DONE button marks ingredient complete
- ✕ button cancels

**Mock Scale Simulation**:
- Gradual weight increase (realistic)
- Random drift (±0.5g for realism)
- Stabilization detection (weight stable for 2s)
- Battery simulation (always 85% in mock)

**Database**:
- 5 scale container examples in backend
- Scale tables created in mobile SQLite
- API endpoints ready (12 total)

### 🚧 Not Yet Implemented

**Pantry Integration**:
- Measured weight → pantry deduction
  - *Current*: Measurements are logged but pantry inventory not updated
  - *Future*: Wire up `onComplete()` → `API.weighPantryItem()`

**Real Bluetooth**:
- Physical Hoto scale connection
  - *Current*: Mock mode only
  - *Future*: Follow `backend/docs/SCALE_BLE_PROTOCOL_DISCOVERY.md` to discover UUIDs

**Container Selection**:
- Choose container with tare weight
  - *Current*: containerTare parameter exists but not exposed in UI
  - *Future*: Add dropdown to select container before measuring

**Additional Screens**:
- ScaleWeighModal (pantry weighing)
- InfusionTrackerScreen
- CoffeeBrewScreen
- Recipe experimentation mode

---

## Success Criteria

You've successfully tested the scale integration if:

- ✅ ScaleMeasureModal opens when tapping ingredient chips
- ✅ Live weight display updates automatically
- ✅ Progress bar shows % of target reached
- ✅ Visual feedback (green/orange) triggers correctly
- ✅ Haptic feedback works on mobile (not web)
- ✅ "DONE" button marks ingredient complete with ✓
- ✅ Can measure all 9 pancake ingredients (5 dry + 4 wet)
- ✅ Recipe steps show heat & flip instructions clearly
- ✅ No errors in browser/metro console

---

## Next Steps After Testing

### Immediate (If Tests Pass)
1. **Test on real device** (optional):
   - Build APK or use Expo Go on your phone
   - Test haptic feedback
   - Test Bluetooth permissions (even though mock for now)

2. **Make pancakes tomorrow morning**:
   - Follow the recipe with mock scale
   - Experience the two-bowl method
   - Verify heat and flip instructions are clear

### Future Enhancements
1. **Real BLE Integration** (1-2 days):
   - Follow protocol discovery guide
   - Update BluetoothScaleService with real UUIDs
   - Test with physical Hoto scale

2. **Pantry Integration** (0.5 day):
   - Wire up measured weight → inventory update
   - Add "⚖️ Weigh" button to pantry screen

3. **Additional Features**:
   - Coffee brewing mode
   - Infusion tracking
   - Recipe experimentation

---

## Quick Command Reference

**Check Backend Health**:
```bash
curl http://192.168.2.38:5025/api/health
```

**Check Scale Containers**:
```bash
curl http://192.168.2.38:5025/api/scale/containers
```

**Check Recipe 1125**:
```bash
curl http://192.168.2.38:5025/api/recipes/1125
```

**View Backend Logs**:
```bash
# Read the output file
type C:\Users\paulh\AppData\Local\Temp\claude\C--Users-paulh-Documents-Lotus-Eater-Machine-food\tasks\b8b081e.output
```

**View Metro Logs**:
```bash
# Read the output file
type C:\Users\paulh\AppData\Local\Temp\claude\C--Users-paulh-Documents-Lotus-Eater-Machine-food\tasks\bb60a9f.output
```

**Restart Expo**:
```bash
# Kill the Expo process (in task manager or Ctrl+C)
cd mobile
npm start
```

---

**Good luck testing! Make some delicious pancakes tomorrow! 🥞**

**Status**: Servers running, ready to test
**Web URL**: http://localhost:8081
**Backend URL**: http://192.168.2.38:5025
**Recipe ID**: 1125
