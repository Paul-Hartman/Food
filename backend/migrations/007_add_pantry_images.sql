-- Migration 007: Add image_url to pantry table
-- Allows storing product images from Open Food Facts

ALTER TABLE pantry ADD COLUMN image_url TEXT;

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_pantry_image_url ON pantry(image_url);
