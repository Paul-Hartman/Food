-- Fix cakes, pies, tarts: 10 servings
UPDATE recipes SET servings = 10
WHERE servings = 4 AND (
  name LIKE '%cake%' OR
  name LIKE '%pie%' OR
  name LIKE '%tart%' OR
  name LIKE '%crumble%' OR
  name LIKE '%cheesecake%'
);

-- Fix cookies, biscuits: 16 servings
UPDATE recipes SET servings = 16
WHERE servings = 4 AND (
  name LIKE '%cookie%' OR
  name LIKE '%biscuit%' OR
  name LIKE '%muffin%' OR
  name LIKE '%cupcake%' OR
  name LIKE '%brownie%'
);

-- Fix other desserts: 8 servings
UPDATE recipes SET servings = 8
WHERE servings = 4 AND category = 'Dessert';

-- Fix soups, stews: 6 servings
UPDATE recipes SET servings = 6
WHERE servings = 4 AND (
  name LIKE '%soup%' OR
  name LIKE '%stew%' OR
  name LIKE '%chili%' OR
  name LIKE '%casserole%' OR
  name LIKE '%curry%'
);

-- Fix pasta: 6 servings
UPDATE recipes SET servings = 6
WHERE servings = 4 AND (
  name LIKE '%pasta%' OR
  name LIKE '%spaghetti%' OR
  name LIKE '%lasagna%' OR
  name LIKE '%ravioli%' OR
  name LIKE '%penne%'
);
