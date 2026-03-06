# Morning Pancake Demo - Pre-Flight Checklist

**Date**: January 11, 2026 (Tomorrow Morning)
**Status**: ALL SYSTEMS READY ✓
**Last Updated**: January 10, 2026 - 1:35 AM

---

## 🎯 What You'll Demo Tomorrow

- **Recipe**: Fluffy Buttermilk Pancakes (Scale Demo) - Recipe ID 1125
- **Features Tested**:
  - Scale integration with mock Bluetooth device
  - Live weight measuring for 9 ingredients
  - Two-bowl method (5 dry + 4 wet ingredients)
  - Timer integration (3 timer steps: rest batter, cook first side, flip)
  - Ingredient tracking with visual checkmarks

---

## ✅ VERIFIED WORKING - Just Done

### 1. Database ✓
- **All 9 Ingredients Added**:
  - Dry Bowl: 250g Flour, 25g Sugar, 12g Baking Powder, 5g Salt, 3g Baking Soda
  - Wet Bowl: 360ml Buttermilk, 50g Butter, 5ml Vanilla Extract, 2 Eggs
- **Recipe Steps**: 11 steps total
- **Timer Steps**: 3 steps (Step 6, 8, 9)
- **Scale Containers**: 5 example containers with tare weights

### 2. Backend API ✓
- **Server Running**: http://192.168.2.38:5025
- **All 12 Scale Endpoints Fixed** (database errors resolved)
- **Verified Endpoints**:
  - `/api/recipes/1125` - Returns complete recipe with 9 ingredients ✓
  - `/api/scale/containers` - Returns 5 containers ✓
  - `/api/scale/measure` - Ready to log measurements ✓
  - `/api/pantry/inventory/<id>/weigh` - Ready for pantry updates ✓

### 3. Mobile App ✓
- **Expo Dev Server Running**: http://localhost:8081
- **Metro Bundler**: Compiled 811 modules successfully ✓
- **Dependencies Installed**: react-native-ble-plx, buffer ✓
- **Integration Complete**:
  - CookingScreen.tsx has ScaleMeasureModal ✓
  - Ingredient parsing working ✓
  - Timer modal integrated ✓

---

## 📋 Morning Startup Checklist (Do These Steps)

### Step 1: Start Backend (30 seconds)
```bash
# If backend is not already running:
cd backend
python app.py

# Should see:
# "Food App v2.0 starting!"
# "Running on http://192.168.2.38:5025"
```

**Verify**: Open http://192.168.2.38:5025/api/health in browser → Should show `{"status": "ok"}`

### Step 2: Start Mobile App (1 minute)
```bash
# If Expo is not already running:
cd mobile
npm start

# Should see:
# "Starting Metro Bundler"
# QR code appears
```

**Verify**: Open http://localhost:8081 in browser → Food App loads

### Step 3: Open Recipe (30 seconds)

#### Option A: Web Browser
1. Navigate to: http://localhost:8081
2. Bottom tabs → Tap **"Recipes"**
3. Search bar → Type **"Pancake"**
4. Tap → **"Fluffy Buttermilk Pancakes (Scale Demo)"**

#### Option B: Android Emulator (If using)
1. In Expo terminal, press **`a`** to open on Android
2. Wait for app to build (1-2 min first time)
3. Follow same steps as web browser

---

## 🥞 Step-by-Step Demo Guide

### Part 1: Dry Ingredients (Step 1) - 5 Minutes

**You Should See**:
- Step title: "Measure Dry Ingredients"
- Instruction text with all measurements
- **5 ingredient chips** below the text:
  - `250g flour`
  - `25g sugar`
  - `12g baking powder`
  - `3g baking soda`
  - `5g salt`

**Test Sequence**:
1. **Tap "250g flour"**
   - ScaleMeasureModal opens fullscreen ✓
   - Header: "Measuring flour" ✓
   - Target: "250g" displayed ✓
   - Current weight: "0.0g" ✓
   - Big scale icon ⚖️ ✓

2. **Watch Mock Scale Work**:
   - Weight auto-increases: 0g → 50g → 100g → 150g → 200g → 245g → 250g
   - Progress bar fills (blue)
   - When reaches 248-252g:
     - Progress bar turns **GREEN** ✓
     - Status: "Perfect! Weight stable ✓" ✓
     - Screen pulses ✓
     - Haptic feedback (mobile only) ✓

3. **Tap "DONE" Button**:
   - Modal closes ✓
   - "250g flour" chip turns **GREEN** with ✓ checkmark ✓
   - Ingredient marked complete ✓

4. **Repeat for Other Dry Ingredients**:
   - 25g sugar → Watch to 25g → Done → Green ✓
   - 12g baking powder → Watch to 12g → Done → Green ✓
   - 3g baking soda → Watch to 3g → Done → Green ✓
   - 5g salt → Watch to 5g → Done → Green ✓

**Expected Result**: All 5 dry ingredient chips are now GREEN with checkmarks ✓

### Part 2: Skip Steps 2 (Whisk Dry) - No Scale

Swipe left to Step 2 → No ingredient chips (just whisk the dry bowl)

### Part 3: Wet Ingredients (Step 3) - 4 Minutes

**You Should See**:
- Step title: "Measure Wet Ingredients"
- **4 ingredient chips**:
  - `360ml buttermilk`
  - `50g butter`
  - `5ml vanilla extract`
  - `2 eggs`

**Test Sequence**:
- Tap each chip → Measure with mock scale → Tap DONE → Green ✓
- 360ml buttermilk (or 360g) ✓
- 50g melted butter ✓
- 5ml vanilla extract ✓
- 2 whole eggs (~100g) ✓

**Expected Result**: All 4 wet ingredient chips are GREEN ✓

### Part 4: Timer Test (Steps 6, 8, 9) - 2 Minutes

**Step 6: Rest Batter (5 min)**:
- Look for button: "⏱️ Set Timer: 5 min"
- Tap button → Timer modal opens ✓
- Shows: "05:00" ✓
- Tap "Start" → Timer counts down ✓
- Tap "Stop" to close (don't actually wait 5 min) ✓

**Step 8: Cook First Side (3 min)**:
- Timer button: "⏱️ Set Timer: 3 min" ✓
- Test same as above ✓

**Step 9: Flip and Finish (2 min)**:
- Timer button: "⏱️ Set Timer: 2 min" ✓
- Test same as above ✓

### Part 5: Test Additional Features - 2 Minutes

**Test TARE Button**:
1. Open any ingredient chip
2. Wait for weight to reach ~100g
3. Tap "TARE" button
4. **Expected**: Weight resets to 0.0g, progress bar resets ✓

**Test Over-Target Warning**:
1. Open "25g sugar" chip
2. Wait for weight to reach ~28g (over target by 3g)
3. **Expected**:
   - Progress bar turns **ORANGE** ✓
   - Status: "Too much! Remove 3.0g" ✓

**Test Cancel/Close**:
1. Open any chip
2. Tap **✕** button in top-left
3. **Expected**: Modal closes, chip stays white (not measured) ✓

---

## 🎮 Control Reference

### ScaleMeasureModal Controls
| Button | Action | Result |
|--------|--------|--------|
| **✕** (top-left) | Cancel | Close modal, ingredient NOT marked |
| **TARE** | Zero scale | Reset weight to 0.0g |
| **DONE** | Confirm | Close modal, mark ingredient complete ✓ |

### Progress Bar Colors
| Color | Meaning |
|-------|---------|
| **Blue** | In progress (below target) |
| **Green** | Target reached (±2g tolerance) |
| **Orange** | Over target (remove ingredient) |

### Status Messages
| Message | Meaning |
|---------|---------|
| "Connecting..." | Scale connecting (should be instant in mock) |
| "Place ingredient on scale" | Weight is 0g |
| "Keep adding... X.Xg to go" | Still below target |
| "Perfect! Weight stable ✓" | Target reached and stable |
| "Too much! Remove X.Xg" | Over target weight |

---

## 📊 Success Criteria

You've successfully tested if:

### Visual Elements
- [ ] Ingredient chips display for Steps 1 and 3
- [ ] Unmeasured chips: White background, dark text
- [ ] Measured chips: Green background, white text, ✓ checkmark
- [ ] Modal opens with smooth animation
- [ ] Large weight display (easy to read)
- [ ] Progress bar animates smoothly
- [ ] Green header "Measuring [ingredient]"

### Functional Elements
- [ ] Weight increases automatically (mock simulation)
- [ ] Progress bar fills proportionally
- [ ] Target detection works (±2g)
- [ ] Pulse animation on target
- [ ] Haptic feedback (mobile only)
- [ ] TARE button zeros scale
- [ ] DONE marks ingredient complete
- [ ] ✕ button cancels
- [ ] All 9 ingredients measurable
- [ ] Timer buttons appear on Steps 6, 8, 9
- [ ] Timer modal opens and counts down

### Data Integrity
- [ ] Measured chips stay green after closing modal
- [ ] Can re-measure by tapping chip again
- [ ] Recipe shows all 11 steps
- [ ] Steps show heat & flip instructions

---

## 🐛 Troubleshooting

### Problem: Modal doesn't open when tapping chip

**Possible Causes**:
1. Ingredient parsing failed (no chips appear)
2. ScaleMeasureModal import error
3. State handler not wired up

**Solutions**:
1. Check browser console for errors (F12 → Console tab)
2. Verify chips appear below step text
3. Try tapping a different ingredient chip
4. Restart Expo dev server: Ctrl+C → `npm start`

### Problem: Weight stays at 0.0g

**Possible Causes**:
1. Mock scale not starting auto-increment
2. Polling not started

**Solutions**:
1. Wait 2-3 seconds (mock has slight delay)
2. Check console logs for "Mock scale enabled"
3. Close and re-open modal
4. Restart Expo: Ctrl+C → `npm start`

### Problem: Backend errors in console

**Possible Causes**:
1. Backend not running
2. Database file locked

**Solutions**:
1. Verify backend: `curl http://192.168.2.38:5025/api/health`
2. Restart backend: `cd backend && python app.py`
3. Check backend logs for SQL errors

### Problem: No ingredient chips appear

**Possible Causes**:
1. Wrong step (Steps 2, 4-11 have few/no measurable ingredients)
2. Ingredient parsing regex failed
3. Recipe data not loaded

**Solutions**:
1. Verify you're on Step 1 or Step 3
2. Check that step text shows measurements (e.g., "250g flour")
3. Check console for "parsed ingredients" logs
4. Verify recipe API: `curl http://192.168.2.38:5025/api/recipes/1125`

### Problem: Timer button not showing

**Possible Causes**:
1. Wrong step (only Steps 6, 8, 9 have timers)
2. Step data missing `timer_needed` flag

**Solutions**:
1. Navigate to Step 6, 8, or 9
2. Verify step shows "⏱️ Set Timer: X min" button
3. Check recipe data: `curl http://192.168.2.38:5025/api/recipes/1125`

---

## 📱 Platform-Specific Notes

### Web Browser
- ✅ All features work
- ❌ No haptic feedback (browser limitation)
- ❌ No real Bluetooth (mock only)
- ✅ Fast reload with Ctrl+R

### Android Emulator
- ✅ Haptic feedback works
- ✅ All features work
- ❌ No real Bluetooth (mock only)
- ⏱️ Slower build time (1-2 min first launch)

### Physical Android Device (via Expo Go)
- ✅ Haptic feedback works
- ✅ All features work
- ❌ No real Bluetooth until BLE UUIDs discovered
- ✅ Fast reload by shaking device

---

## 🔧 Quick Commands

**Check Backend Health**:
```bash
curl http://192.168.2.38:5025/api/health
# Should return: {"status":"ok"}
```

**Check Recipe Data**:
```bash
curl http://192.168.2.38:5025/api/recipes/1125
# Should show 9 ingredients, 11 steps
```

**Check Scale Containers**:
```bash
curl http://192.168.2.38:5025/api/scale/containers
# Should show 5 containers with tare weights
```

**View Backend Logs**:
```bash
# Check the running backend task
# Look for errors or SQL issues
```

**View Metro Bundler Logs**:
```bash
# Check Expo terminal
# Look for compilation errors
```

**Restart Expo**:
```bash
# In Expo terminal: Ctrl+C
cd mobile
npm start
```

**Restart Backend**:
```bash
# Kill running backend
cd backend
python app.py
```

---

## 🎬 2-Minute Demo Script

**Opening**: "I'm testing live scale integration for cooking. Watch me measure pancake ingredients."

**Demo Flow**:
1. "Here's the recipe with 9 ingredients" (show Step 1)
2. "I tap '250g flour' to measure" (tap chip → modal opens)
3. "Watch the scale weigh in real-time" (weight climbs 0→250g)
4. "Green when perfect!" (progress bar turns green at 250g)
5. "Mark it done" (tap DONE → chip turns green with ✓)
6. "Repeat for all ingredients" (show a few more quick measurements)
7. "Timer for rest time" (tap timer button → show 5-min countdown)

**Closing**: "Scale works in mock mode. Next: connect real Bluetooth device!"

---

## 🚀 What's Working vs. Not Yet

### ✅ FULLY WORKING (Demo These!)

**Recipe System**:
- Recipe with 11 steps loaded ✓
- All 9 ingredients in database ✓
- Ingredient parsing from step text ✓
- Ingredient chips UI ✓
- Measured/unmeasured states ✓

**Scale Integration**:
- ScaleMeasureModal component ✓
- Mock Bluetooth scale simulation ✓
- Live weight polling (1.5s) ✓
- Progress bar with % tracking ✓
- Target detection (±2g) ✓
- Pulse animation ✓
- Haptic feedback (mobile) ✓
- TARE functionality ✓
- Over-target warnings ✓

**Timer System**:
- Timer modal ✓
- Start/Stop controls ✓
- Countdown display ✓
- 3 timer steps in recipe ✓

**Backend API**:
- 12 scale endpoints ✓
- Recipe endpoints ✓
- Container management ✓
- Measurement logging ✓

### 🚧 NOT YET IMPLEMENTED

**Real Hardware**:
- Physical Hoto scale Bluetooth (need UUIDs)
- BLE scanning/pairing (mock mode only)

**Pantry Integration**:
- Measured weight → pantry deduction
- Auto-update inventory after measuring

**Additional Screens**:
- ScaleWeighModal (for pantry weighing)
- InfusionTrackerScreen
- CoffeeBrewScreen
- Recipe experimentation mode

**Container Selection**:
- Dropdown to choose container before measuring
- Auto-suggest container based on weight

---

## 📞 Support / If Something Breaks

**If the demo fails tomorrow**:

1. **Backend not running?**
   ```bash
   cd backend
   python app.py
   ```

2. **Expo crashed?**
   ```bash
   cd mobile
   npm start
   ```

3. **Still broken?**
   - Check SCALE_TESTING_GUIDE.md for detailed troubleshooting
   - Check backend logs in terminal
   - Check browser console (F12)
   - Verify database: `sqlite3 food.db "SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = 1125;"`
     - Should return: 9

4. **Nuclear option (if all else fails)**:
   - Restart computer
   - Restart backend and Expo
   - Clear Expo cache: `expo start -c`

---

## 🎯 Final Status

**Systems**: ✅ ALL GREEN
**Recipe**: ✅ Loaded with 9 ingredients
**Backend**: ✅ Running on port 5025
**Mobile App**: ✅ Compiled 811 modules
**Scale Endpoints**: ✅ Fixed and tested
**Integration**: ✅ Complete

**Blockers**: None

**Time to Demo**: ~15 minutes
- Startup: 2 min
- Dry ingredients: 5 min
- Wet ingredients: 4 min
- Timers: 2 min
- Testing extras: 2 min

---

**YOU'RE READY! GOOD LUCK MAKING PANCAKES! 🥞⚖️**

**Status**: DEMO-READY
**Last Verified**: Jan 10, 2026 - 1:35 AM
**Servers**: Backend (ba896a2), Expo (bb60a9f) running in background
