-- Schema: food_app.db
-- Source: C:\Users\paulh\Documents\lotus eater 2.0\Food\backend\food_app.db
-- Dumped: 2026-03-06T19:55:26.388625

-- Row counts:
--   grocery_budget: 0
--   grocery_config: 4
--   grocery_coupons: 0
--   grocery_prices: 0
--   grocery_products: 0
--   grocery_receipt_items: 0
--   grocery_receipts: 0
--   grocery_seasonal_calendar: 0

-- TABLES

CREATE TABLE grocery_budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month DATE NOT NULL,
    planned_budget REAL NOT NULL,
    spent_aldi REAL DEFAULT 0,
    spent_lidl REAL DEFAULT 0,
    spent_rewe REAL DEFAULT 0,
    spent_other REAL DEFAULT 0,
    forecast_end_of_month REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(month)
);

CREATE TABLE grocery_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    encrypted INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE grocery_coupons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    coupon_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    discount_type TEXT,  -- 'percentage', 'fixed', 'bogo'
    discount_value REAL,
    min_purchase REAL,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE NOT NULL,
    activated INTEGER DEFAULT 0,
    activated_at TIMESTAMP,
    redeemed INTEGER DEFAULT 0,
    redeemed_at TIMESTAMP,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE grocery_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    store TEXT NOT NULL,
    price REAL NOT NULL,
    is_promotion INTEGER DEFAULT 0,
    promotion_description TEXT,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES grocery_products(id) ON DELETE CASCADE
);

CREATE TABLE grocery_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT,
    name TEXT NOT NULL,
    generic_ingredient_id INTEGER,
    store TEXT NOT NULL,  -- 'aldi_nord', 'aldi_sud', 'rewe', 'lidl', 'other'
    category TEXT,
    package_size REAL,
    package_unit TEXT,
    image_url TEXT,
    last_updated DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (generic_ingredient_id) REFERENCES ingredients(id),
    UNIQUE(barcode, store)
);

CREATE TABLE grocery_receipt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    product_id INTEGER,
    name_on_receipt TEXT NOT NULL,
    quantity REAL DEFAULT 1,
    unit_price REAL,
    total_price REAL NOT NULL,
    category_guess TEXT,
    FOREIGN KEY (receipt_id) REFERENCES grocery_receipts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES grocery_products(id) ON DELETE SET NULL
);

CREATE TABLE grocery_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    total_amount REAL NOT NULL,
    purchase_date DATE NOT NULL,
    receipt_number TEXT,
    payment_method TEXT,
    source TEXT NOT NULL,  -- 'lidl_plus_api', 'ocr_asprise', 'ocr_tesseract', 'manual'
    ocr_confidence REAL,
    raw_ocr_text TEXT,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE grocery_seasonal_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_category TEXT NOT NULL,
    month INTEGER NOT NULL CHECK(month >= 1 AND month <= 12),
    season_status TEXT,  -- 'peak', 'available', 'imported', 'unavailable'
    avg_price_multiplier REAL DEFAULT 1.0,
    recommendation TEXT,
    UNIQUE(product_category, month)
);

CREATE TABLE sqlite_sequence(name,seq);

-- INDEXS

CREATE INDEX idx_grocery_budget_month ON grocery_budget(month);

CREATE INDEX idx_grocery_coupons_activated ON grocery_coupons(activated);

CREATE INDEX idx_grocery_coupons_store ON grocery_coupons(store);

CREATE INDEX idx_grocery_coupons_valid ON grocery_coupons(valid_from, valid_to);

CREATE INDEX idx_grocery_prices_date ON grocery_prices(valid_from, valid_to);

CREATE INDEX idx_grocery_prices_product ON grocery_prices(product_id);

CREATE INDEX idx_grocery_prices_store ON grocery_prices(store);

CREATE INDEX idx_grocery_products_barcode ON grocery_products(barcode);

CREATE INDEX idx_grocery_products_ingredient ON grocery_products(generic_ingredient_id);

CREATE INDEX idx_grocery_products_store ON grocery_products(store);

CREATE INDEX idx_grocery_receipt_items_product ON grocery_receipt_items(product_id);

CREATE INDEX idx_grocery_receipt_items_receipt ON grocery_receipt_items(receipt_id);

CREATE INDEX idx_grocery_receipts_created ON grocery_receipts(created_at);

CREATE INDEX idx_grocery_receipts_date ON grocery_receipts(purchase_date);

CREATE INDEX idx_grocery_receipts_store ON grocery_receipts(store);

CREATE INDEX idx_grocery_seasonal_month ON grocery_seasonal_calendar(month);

CREATE INDEX idx_grocery_seasonal_status ON grocery_seasonal_calendar(season_status);

-- TRIGGERS

CREATE TRIGGER update_grocery_budget_timestamp
AFTER UPDATE ON grocery_budget
FOR EACH ROW
BEGIN
    UPDATE grocery_budget SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_grocery_config_timestamp
AFTER UPDATE ON grocery_config
FOR EACH ROW
BEGIN
    UPDATE grocery_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
