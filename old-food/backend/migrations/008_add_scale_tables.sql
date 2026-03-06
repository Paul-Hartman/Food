-- Migration: Add Scale Integration Tables
-- Created: 2026-01-10
-- Description: Adds tables for smart kitchen scale integration (containers, measurements, infusion tracking, brew logs)

-- Scale containers - tare weights for reusable containers
CREATE TABLE IF NOT EXISTS scale_containers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  tare_weight_g REAL NOT NULL,
  color_hex TEXT,
  icon_emoji TEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scale_containers_name ON scale_containers(name);

-- Scale measurements - historical log of all weight readings
CREATE TABLE IF NOT EXISTS scale_measurements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER,
  pantry_inventory_id INTEGER,
  gross_weight_g REAL NOT NULL,
  tare_weight_g REAL DEFAULT 0,
  net_weight_g REAL NOT NULL,
  container_id INTEGER,
  measurement_type TEXT,  -- "recipe_ingredient", "add_to_pantry", "manual"
  recipe_id INTEGER,
  notes TEXT,
  measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (product_id) REFERENCES pantry_products(id),
  FOREIGN KEY (pantry_inventory_id) REFERENCES pantry_inventory(id),
  FOREIGN KEY (container_id) REFERENCES scale_containers(id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

CREATE INDEX IF NOT EXISTS idx_scale_measurements_product ON scale_measurements(product_id);
CREATE INDEX IF NOT EXISTS idx_scale_measurements_measured_at ON scale_measurements(measured_at);
CREATE INDEX IF NOT EXISTS idx_scale_measurements_type ON scale_measurements(measurement_type);

-- Infusion tracking - track weight changes over time (limoncello, vanilla extract, etc.)
CREATE TABLE IF NOT EXISTS infusion_tracking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT,  -- "alcohol", "oil", "coffee", "tea"
  start_date DATE NOT NULL,
  target_duration_days INTEGER,
  initial_weight_g REAL NOT NULL,
  current_weight_g REAL,
  reminder_interval_days INTEGER DEFAULT 3,
  next_reminder_date DATE,
  status TEXT DEFAULT 'active',  -- "active", "completed", "discarded"
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_infusion_status ON infusion_tracking(status);
CREATE INDEX IF NOT EXISTS idx_infusion_next_reminder ON infusion_tracking(next_reminder_date);

-- Infusion check-ins - weight measurements over time
CREATE TABLE IF NOT EXISTS infusion_check_ins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  infusion_id INTEGER NOT NULL,
  day_number INTEGER NOT NULL,
  weight_g REAL NOT NULL,
  temperature_c REAL,
  notes TEXT,
  logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (infusion_id) REFERENCES infusion_tracking(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_infusion_check_ins_infusion ON infusion_check_ins(infusion_id);
CREATE INDEX IF NOT EXISTS idx_infusion_check_ins_day ON infusion_check_ins(day_number);

-- Brew logs - coffee brewing sessions
CREATE TABLE IF NOT EXISTS brew_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brew_method TEXT NOT NULL,  -- "pour_over", "french_press", "espresso", "aeropress"
  coffee_weight_g REAL NOT NULL,
  water_weight_g REAL NOT NULL,
  ratio REAL,  -- e.g., 16.0 for 1:16 ratio
  grind_size TEXT,
  brew_time_seconds INTEGER,
  water_temp_c REAL,
  rating INTEGER,  -- 1-5 stars
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_brew_logs_method ON brew_logs(brew_method);
CREATE INDEX IF NOT EXISTS idx_brew_logs_rating ON brew_logs(rating);
CREATE INDEX IF NOT EXISTS idx_brew_logs_created_at ON brew_logs(created_at);

-- Add scale tracking flag to pantry_inventory
-- This allows tracking which items were measured vs manually entered
ALTER TABLE pantry_inventory ADD COLUMN measured_by_scale INTEGER DEFAULT 0;

-- Example data: Common container types
INSERT INTO scale_containers (name, tare_weight_g, color_hex, icon_emoji, notes) VALUES
  ('Small Mason Jar', 250, '#4CAF50', '🫙', 'Standard 500ml mason jar'),
  ('Large Mason Jar', 350, '#4CAF50', '🫙', 'Standard 1L mason jar'),
  ('Glass Mixing Bowl', 450, '#2196F3', '🥣', 'Pyrex mixing bowl'),
  ('Plastic Container', 120, '#FF9800', '📦', 'Standard Tupperware'),
  ('Measuring Cup', 180, '#9C27B0', '🥤', 'Glass measuring cup');
