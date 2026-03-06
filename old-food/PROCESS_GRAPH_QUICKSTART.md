# Process Graph Navigation - Quick Reference

## What Was Done (2025-12-24)

Created a **graph-based culinary knowledge system** where processes (fermentation, baking, simmering) link ALL related recipes and transformations.

### Key Changes
1. ✅ Added `process_id` to cooking steps table
2. ✅ Enhanced API to show process info in recipe steps
3. ✅ Enhanced process detail page to show ALL uses
4. ✅ Linked 11 cooking steps to processes
5. ✅ Fixed milk transformations data
6. ✅ Added clickable process cards in cooking UI

## Current System Capabilities

### Navigation Paths

**Path 1: Milk → Yogurt → Fermentation → All Fermented Foods**
```
/ingredient/transformations?id=29
→ Click "Lactic Acid Fermentation"
→ /process/detail?id=1
→ See: Yogurt, Kefir, Skyr, Kimchi, etc.
```

**Path 2: Cooking Garlic Bread → Learn About Baking → Other Baked Items**
```
/cook?id=14
→ Step 4: "Bake" shows process card
→ Click "Learn about this process"
→ /process/detail?id=2
→ See: Flour→Bread transformation + 7 recipes using baking
```

## How to Continue This Work

### To Add More Processes to Recipe Steps:

1. **Find steps that use a process:**
```sql
SELECT cs.id, r.name, cs.step_number, cs.title
FROM cooking_steps cs
JOIN recipes r ON cs.recipe_id = r.id
WHERE LOWER(cs.instruction) LIKE '%keyword%'
AND cs.process_id IS NULL;
```

2. **Link them to a process:**
```sql
UPDATE cooking_steps
SET process_id = <process_id>
WHERE id IN (<step_ids>);
```

**Common process keywords:**
- Process 2 (Baking/Maillard): `%bake%`, `%brown%`, `%sear%`, `%roast%`
- Process 5 (Starch Gelatinization): `%simmer%`, `%boil%`, `%reduce%`
- Process 1 (Fermentation): `%ferment%`, `%rise%`, `%proof%`

### To Add More Transformation Recipes:

```python
import sqlite3
import json

conn = sqlite3.connect('food.db')
cursor = conn.cursor()

cursor.execute('''
    INSERT INTO transformation_recipes
    (recipe_name, base_ingredient_id, output_preparation_id, process_id,
     yield_percent, instructions_json)
    VALUES (?, ?, ?, ?, ?, ?)
''', (
    'Recipe Name',
    <base_ingredient_id>,
    <output_preparation_id>,
    <process_id>,
    <yield_percent>,
    json.dumps({
        'steps': ['Step 1', 'Step 2'],
        'difficulty': 'Easy',
        'chemistry': 'Explanation...'
    })
))
conn.commit()
```

### To Test:

```bash
# Start Flask
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\backend"
python app.py

# Test API
curl http://localhost:5025/api/process/2
curl http://localhost:5025/api/recipes/14/steps

# Test UI
http://localhost:5025/process/detail?id=2
http://localhost:5025/cook?id=14
```

## Important Database IDs

### Processes:
- 1: Lactic Acid Fermentation
- 2: Bread Baking (Maillard + Gelatinization)
- 5: Starch Gelatinization (Congee)

### Ingredients:
- 29: Milk
- 45: Flour
- 34: White Rice

### Recipes:
- 14: Garlic Bread
- 6: Baked Chicken Thighs
- 2: Classic Beef Tacos

## Next Session Priorities

1. **Add Equipment Discovery** (instant pot presets)
2. **Mobile UI** for process graph navigation
3. **More Transformations**: cream→butter, eggs→custard, etc.
4. **Auto-link Recipe Steps** using keyword matching
5. **Fermentation Tracking** with pH/temp logging

## Documentation Location

Full details: `.claude/sessions/2025-12-24_process-graph-navigation.md`
