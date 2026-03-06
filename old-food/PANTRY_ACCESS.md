# How to Access Pantry Screen (Budget & Expiry Features)

## 🔄 IMPORTANT: Clear Your Browser Cache First!

The web version is showing an **old cached version** with only 4 tabs. You need to **force refresh** to see all 7 tabs including Pantry.

### **Step 1: Force Refresh the Page**

Visit: `http://localhost:8081`

Then press:
- **Windows:** `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac:** `Cmd + Shift + R`

This will reload the app with the latest code.

---

## 📱 After Refresh, You'll See 7 Tabs:

Look at the **bottom navigation bar** - you should now see:

```
[🍞]  [📅]  [🛒]  [🏠]  [📊]  [📅]  [📚]
 ↓     ↓     ↓     ↓     ↓     ↓     ↓
Recipes Plan Shopping PANTRY Nutrition Calendar Collections
                      ↑
                  CLICK HERE!
```

---

## 🏠 Pantry Tab Features

### What You'll See:
```
┌──────────────────────────────────────────┐
│ Pantry                                    │
├──────────────────────────────────────────┤
│ Track what you have at home               │
│                                           │
│ ┌─────────────────────────────────────┐  │
│ │  Total Pantry Value: €6.49          │  │ ← GREEN BANNER
│ └─────────────────────────────────────┘  │
│                                           │
│ Add item form:                            │
│ [Item name...                    ]        │
│ [Expiry (YYYY-MM-DD)  ] [€0.00   ]        │ ← NEW INPUTS
│ [📷 Scanner] [Add]                        │
│                                           │
│ Your items:                               │
│ 🍞 bakery                                 │
│ Bread    1 loaf  €2.50  [1d]  [×]        │ ← Price & expiry badge
│                                           │
│ 🥛 dairy                                  │
│ Test Milk  2 L   €3.99  [2d]  [×]        │
└──────────────────────────────────────────┘
```

---

## 🎯 Quick Test:

1. **Force refresh** browser (Ctrl+Shift+R)
2. Count tabs at bottom - should be **7 tabs** now (not 4)
3. Click the **4th tab** (🏠 house icon)
4. You should see:
   - Green "Total Pantry Value" banner
   - 2 test items with prices and expiry badges
   - New input fields for expiry and price

---

## 🐛 Still Not Showing?

### Try This:
```bash
# Stop Expo
# Then restart with cache cleared:
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\mobile"
npx expo start --clear
```

Then in your browser:
1. Clear all cache and cookies for localhost
2. Hard refresh (Ctrl+Shift+R)
3. The 7 tabs should appear

---

## ✅ Current Tab List (After Refresh):

| Position | Icon | Name | What It Does |
|----------|------|------|--------------|
| 1 | 🍞 | Recipes | Browse recipes (has "Discover" sub-tab) |
| 2 | 📅 | Plan | Meal planning with swipe interface |
| 3 | 🛒 | Shopping | Shopping list |
| **4** | **🏠** | **Pantry** | **Budget & Expiry tracking** ← HERE! |
| 5 | 📊 | Nutrition | Nutrition tracking |
| 6 | 📅 | Calendar | Calendar view |
| 7 | 📚 | Collections | Recipe collections |

---

**If you still only see 4 tabs after force refresh, let me know and I'll check the code!**
