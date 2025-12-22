# Comprehensive Nutrition Tracking System

## Overview

Your food app now has **complete micronutrient tracking** including all vitamins, minerals, and water intake.

## What's Tracked

### Macronutrients (7)
- Calories
- Protein
- Carbohydrates
- Total Fat
- Saturated Fat
- Fiber
- Sugar

### Hydration
- Water (ml)
  - Quick-add buttons: +250ml, +500ml, +1L

### Vitamins (13)

#### Fat-Soluble Vitamins
- **Vitamin A** (900 mcg RAE) - Vision, immune function, skin health
- **Vitamin D** (20 mcg) - Bone health, immune function
- **Vitamin E** (15 mg) - Antioxidant, cell protection
- **Vitamin K** (120 mcg) - Blood clotting, bone health

#### B Complex Vitamins
- **B1 Thiamin** (1.2 mg) - Energy metabolism, nerve function
- **B2 Riboflavin** (1.3 mg) - Energy production, cell growth
- **B3 Niacin** (16 mg) - Metabolism, DNA repair
- **B5 Pantothenic Acid** (5 mg) - Hormone production, energy
- **B6 Pyridoxine** (1.7 mg) - Brain development, immune function
- **B7 Biotin** (30 mcg) - Hair, skin, nail health
- **B9 Folate** (400 mcg) - DNA synthesis, red blood cells
- **B12 Cobalamin** (2.4 mcg) - Nerve function, red blood cells

#### Water-Soluble Vitamins
- **Vitamin C** (90 mg) - Immune function, collagen synthesis, antioxidant

### Minerals (14)

#### Major Minerals
- **Calcium** (1000 mg) - Bones, teeth, muscle function
- **Phosphorus** (700 mg) - Bones, energy production
- **Magnesium** (420 mg) - Muscle/nerve function, blood sugar
- **Sodium** (2300 mg) - Fluid balance, nerve signals
- **Potassium** (3400 mg) - Blood pressure, muscle function
- **Chloride** (2300 mg) - Fluid balance, digestion

#### Trace Minerals
- **Iron** (18 mg) - Oxygen transport, energy
- **Zinc** (11 mg) - Immune function, wound healing
- **Copper** (0.9 mg) - Iron absorption, connective tissue
- **Manganese** (2.3 mg) - Bone formation, metabolism
- **Selenium** (55 mcg) - Antioxidant, thyroid function
- **Iodine** (150 mcg) - Thyroid hormones
- **Chromium** (35 mcg) - Blood sugar regulation
- **Molybdenum** (45 mcg) - Enzyme function

### Other Nutrients (2)
- **Omega-3 Fatty Acids** (1.6 g) - Heart health, brain function
- **Cholesterol** (300 mg) - Cell membranes (limit intake)

## Features

### Visual Progress Bars
- Green = Adequate
- Orange = Low (< 50% for nutrients you need more of)
- Red = High (> 100% for nutrients to limit like sodium, cholesterol)

### Collapsible Sections
- **Macronutrients** - Expanded by default
- **Hydration** - Expanded by default
- **Vitamins** - Collapsed (tap to expand)
- **Minerals** - Collapsed (tap to expand)
- **Other Nutrients** - Collapsed (tap to expand)

### Smart Warnings
- **Low Warning**: Nutrients you're not getting enough of (vitamins, minerals, fiber, omega-3)
- **High Warning**: Nutrients to limit (saturated fat, sugar, sodium, cholesterol)

## API Endpoints

### Get Today's Nutrition
```
GET /api/nutrition/comprehensive/today
```

Returns:
```json
{
  "date": "2025-01-01",
  "goals": { ... all nutrient goals ... },
  "consumed": { ... all consumed nutrients ... }
}
```

### Log Water
```
POST /api/nutrition/comprehensive/log-water
Body: { "ml": 250 }
```

### Log Nutrients Manually
```
POST /api/nutrition/comprehensive/log-nutrients
Body: {
  "vitamin_c_mg": 90,
  "iron_mg": 8,
  ... any nutrients ...
}
```

### Get/Update Goals
```
GET /api/nutrition/comprehensive/goals
PUT /api/nutrition/comprehensive/goals
Body: { ... nutrient goals to update ... }
```

## Database Schema

### `nutrition_goals` Table
- All 42 nutrient goals with defaults based on FDA/NIH recommendations

### `nutrition_tracking` Table
- Daily tracking for all 42 nutrients
- One row per day
- Auto-created when you first interact with the nutrition screen

## Recipe Images

Recipe images use **emoji placeholders** based on cuisine/category:
- Mexican: 🌮
- Italian: 🍝
- Asian: 🥡
- American: 🍖
- Sides: 🥗
- Default: 🍽️

This provides a clean, consistent look without needing actual food photos.

## How to Use

1. **View Your Progress**: Open the Nutrition tab to see today's intake
2. **Log Water**: Tap quick-add buttons (+250ml, +500ml, +1L)
3. **Expand Sections**: Tap section headers to see vitamins/minerals
4. **Track Progress**: Green bars = good, Orange = low, Red = too high
5. **Set Custom Goals**: Tap "Edit Goals" (coming soon in UI)

## Goals Defaults (Adult, 2000 cal diet)

Based on FDA Daily Values and NIH recommendations:
- Calories: 2000
- Protein: 50g
- Carbs: 275g
- Fat: 78g
- Fiber: 28g
- Water: 2000ml (2L)
- All vitamins/minerals set to RDA/AI values

## Notes

- **Nutrient synergies**: Vitamin C enhances iron absorption, vitamin D needs magnesium, etc.
- **Water is crucial**: Most people are dehydrated - aim for 2-3L per day
- **B vitamins work together**: All 8 B vitamins support energy and metabolism
- **Electrolyte balance**: Sodium, potassium, chloride, magnesium work together
- **Fat-soluble vitamins**: Need dietary fat for absorption (A, D, E, K)

## Future Enhancements

- Meal logging integration (auto-calculate nutrients from recipes)
- Weekly trends and charts
- Nutrient synergy suggestions
- Supplement tracking
- Custom goals by age/gender/activity level
- Export to CSV
