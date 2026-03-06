-- Pancake Recipe Optimized for Scale Measuring Demo
-- Two bowl method: Dry ingredients in one bowl, wet in another, then mix

-- Insert pancake recipe
INSERT INTO recipes (name, description, category, cuisine, prep_time_min, cook_time_min, servings, difficulty, image_url)
VALUES (
  'Fluffy Buttermilk Pancakes (Scale Demo)',
  'Classic fluffy pancakes using precise scale measurements. Two bowl method for best results.',
  'Breakfast',
  'American',
  10,
  15,
  8,  -- Makes 8 pancakes
  'Easy',
  'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400'
);

-- Get the recipe ID
-- We'll use recipe_id = (SELECT MAX(id) FROM recipes)

-- Insert recipe ingredients (for shopping list and nutrition)
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
SELECT
  (SELECT MAX(id) FROM recipes),
  id,
  qty,
  unit_name,
  note
FROM (
  -- Dry ingredients
  SELECT (SELECT id FROM ingredients WHERE name LIKE '%flour%' AND name LIKE '%all%purpose%' LIMIT 1) as id, 250 as qty, 'g' as unit_name, 'Dry bowl' as note
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%sugar%' AND name NOT LIKE '%brown%' LIMIT 1), 25, 'g', 'Dry bowl'
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%baking powder%' LIMIT 1), 12, 'g', 'Dry bowl'
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%baking soda%' LIMIT 1), 3, 'g', 'Dry bowl'
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%salt%' LIMIT 1), 5, 'g', 'Dry bowl'
  -- Wet ingredients
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%buttermilk%' LIMIT 1), 360, 'ml', 'Wet bowl'
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%egg%' AND name NOT LIKE '%powder%' LIMIT 1), 2, 'whole', 'Wet bowl (~100g)'
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%butter%' LIMIT 1), 50, 'g', 'Melted'
  UNION ALL SELECT (SELECT id FROM ingredients WHERE name LIKE '%vanilla extract%' LIMIT 1), 5, 'ml', 'Wet bowl'
) WHERE id IS NOT NULL;

-- Insert cooking steps with scale-friendly instructions
INSERT INTO cooking_steps (recipe_id, step_number, title, instruction, duration_min, tips, timer_needed, step_type)
VALUES
  -- Step 1: Dry ingredients
  (
    (SELECT MAX(id) FROM recipes),
    1,
    'Measure Dry Ingredients',
    'In a large mixing bowl, use scale to measure:\n250g all-purpose flour\n25g sugar\n12g baking powder\n3g baking soda\n5g salt\n\nTip: Place bowl on scale, tare to zero, then add each ingredient one at a time. You can tare between ingredients or add them all together.',
    3,
    'Use the TARE button on your scale between each ingredient for accuracy, or weigh them together and subtract the bowl weight.',
    FALSE,
    'prep'
  ),

  -- Step 2: Whisk dry
  (
    (SELECT MAX(id) FROM recipes),
    2,
    'Whisk Dry Ingredients',
    'Whisk the dry ingredients together until evenly combined (about 30 seconds).',
    1,
    'This ensures even distribution of leavening agents for uniform fluffiness.',
    FALSE,
    'prep'
  ),

  -- Step 3: Wet ingredients
  (
    (SELECT MAX(id) FROM recipes),
    3,
    'Measure Wet Ingredients',
    'In a separate bowl (or large measuring cup), use scale to measure:\n360ml buttermilk (or 360g)\n2 eggs (~100g)\n50g melted butter\n5ml vanilla extract\n\nTip: For liquids, 1ml ≈ 1g for water-based ingredients.',
    3,
    'Melt butter in microwave (30 seconds) and let it cool slightly before adding to avoid cooking the eggs.',
    FALSE,
    'prep'
  ),

  -- Step 4: Whisk wet
  (
    (SELECT MAX(id) FROM recipes),
    4,
    'Whisk Wet Ingredients',
    'Whisk wet ingredients together until smooth and well combined.',
    1,
    'Make sure butter is incorporated evenly.',
    FALSE,
    'prep'
  ),

  -- Step 5: Combine
  (
    (SELECT MAX(id) FROM recipes),
    5,
    'Combine Wet and Dry',
    'Pour wet ingredients into dry ingredients. Gently fold together with a spatula until just combined.\n\nIMPORTANT: Do not overmix! Some lumps are OK. Overmixing makes tough pancakes.',
    2,
    'Stop mixing as soon as you don''t see dry flour anymore. The batter should be slightly lumpy.',
    FALSE,
    'prep'
  ),

  -- Step 6: Rest
  (
    (SELECT MAX(id) FROM recipes),
    6,
    'Rest Batter',
    'Let batter rest for 5 minutes. This allows the flour to hydrate and the leavening agents to activate.',
    5,
    'During this time, preheat your griddle or pan to medium heat (about 190°C/375°F).',
    TRUE,
    'cook'
  ),

  -- Step 7: Heat pan
  (
    (SELECT MAX(id) FROM recipes),
    7,
    'Preheat Griddle',
    'Heat a non-stick griddle or large pan over MEDIUM heat. Lightly grease with butter or oil.\n\nTest: Sprinkle a few drops of water - they should sizzle and evaporate in 2-3 seconds.',
    3,
    'Medium heat is key! Too hot = burnt outside, raw inside. Too cool = pale, dense pancakes.',
    FALSE,
    'cook'
  ),

  -- Step 8: Cook first side
  (
    (SELECT MAX(id) FROM recipes),
    8,
    'Cook First Side',
    'Pour 1/4 cup (60ml) batter onto griddle for each pancake. Cook until bubbles form on surface and edges look set (about 2-3 minutes).\n\nYou''ll know it''s ready to flip when:\n- Bubbles pop and don''t refill\n- Edges are matte (not shiny)\n- Bottom is golden brown',
    3,
    'Don''t flip too early! Wait for the bubbles. First pancake is often a test pancake - adjust heat if needed.',
    TRUE,
    'cook'
  ),

  -- Step 9: Flip and cook
  (
    (SELECT MAX(id) FROM recipes),
    9,
    'Flip and Finish',
    'Flip pancakes carefully. Cook second side until golden brown (about 1-2 minutes).\n\nSecond side cooks faster than first!',
    2,
    'Flip with confidence - a quick, decisive flip works best. Pancake should be puffy and spring back when touched.',
    TRUE,
    'cook'
  ),

  -- Step 10: Keep warm
  (
    (SELECT MAX(id) FROM recipes),
    10,
    'Keep Warm While Cooking Batches',
    'Transfer cooked pancakes to a plate in a 200°F (95°C) oven to keep warm while you cook the remaining batches.\n\nRepeat steps 8-9 with remaining batter.',
    10,
    'Re-grease griddle lightly between batches. Makes about 8 pancakes total.',
    FALSE,
    'cook'
  ),

  -- Step 11: Serve
  (
    (SELECT MAX(id) FROM recipes),
    11,
    'Serve Hot',
    'Serve immediately with butter and maple syrup, or your favorite toppings!\n\nSuggestions:\n- Classic: Butter + maple syrup\n- Fruit: Fresh berries + whipped cream\n- Decadent: Chocolate chips + nutella\n- Savory: Bacon + fried egg on top',
    1,
    'Pancakes are best fresh off the griddle. Stack them high!',
    FALSE,
    'serve'
  );

-- Verify the recipe was created
SELECT 'Recipe created with ID: ' || MAX(id) FROM recipes;
SELECT 'Number of steps: ' || COUNT(*) FROM cooking_steps WHERE recipe_id = (SELECT MAX(id) FROM recipes);
SELECT 'Number of ingredients: ' || COUNT(*) FROM recipe_ingredients WHERE recipe_id = (SELECT MAX(id) FROM recipes);
