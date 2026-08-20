-- =====================================================================
-- RETAIL DATA PIPELINE SCHEMA & ANALYTICAL QUERIES
-- Target: PostgreSQL / SQLite / Databricks Delta Lake
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. BRONZE LAYER (Append-Only Raw File Ingestion Log)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bronze_orders_raw (
    raw_order_id     VARCHAR(64),
    raw_order_date   VARCHAR(64),
    raw_customer_id  VARCHAR(64),
    raw_product_id   VARCHAR(64),
    raw_quantity     VARCHAR(32),
    raw_unit_price   VARCHAR(32),
    raw_region       VARCHAR(64),
    extra_data       TEXT,
    source_file      VARCHAR(255) NOT NULL,
    ingested_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 2. SILVER LAYER: DIMENSIONS & CONFORMED FACT TABLES
-- ---------------------------------------------------------------------

-- Product Reference Dimension Table
CREATE TABLE IF NOT EXISTS silver_dim_products (
    product_id       VARCHAR(64) PRIMARY KEY,
    product_name     VARCHAR(255) NOT NULL,
    category         VARCHAR(128) NOT NULL,
    list_price       DECIMAL(10, 2) NOT NULL,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Conformed Orders Fact Table (CDC Merged & Deduplicated)
CREATE TABLE IF NOT EXISTS silver_fct_orders (
    order_id         VARCHAR(64) PRIMARY KEY,
    order_date       DATE NOT NULL,
    customer_id      VARCHAR(64), -- Nullable for guest checkouts
    product_id       VARCHAR(64) NOT NULL,
    category         VARCHAR(128) NOT NULL,
    quantity         INTEGER NOT NULL,
    unit_price       DECIMAL(10, 2) NOT NULL,
    line_amount      DECIMAL(12, 2) NOT NULL,
    region           VARCHAR(64) NOT NULL,
    is_return        BOOLEAN NOT NULL DEFAULT FALSE,
    source_file      VARCHAR(255) NOT NULL,
    ingested_at      TIMESTAMP NOT NULL,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_silver_orders_date_cat_reg 
ON silver_fct_orders (order_date, category, region);

-- ---------------------------------------------------------------------
-- 3. CDC MERGE / UPSERT SPECIFICATION (Delta Lake / PostgreSQL)
-- ---------------------------------------------------------------------
-- On Databricks / Delta Lake:
/*
MERGE INTO silver_fct_orders AS target
USING staged_batch AS source
ON target.order_id = source.order_id
WHEN MATCHED AND source.ingested_at >= target.ingested_at THEN
  UPDATE SET
    target.order_date   = source.order_date,
    target.customer_id  = source.customer_id,
    target.product_id   = source.product_id,
    target.category     = source.category,
    target.quantity     = source.quantity,
    target.unit_price   = source.unit_price,
    target.line_amount  = source.line_amount,
    target.region       = source.region,
    target.is_return    = source.is_return,
    target.source_file  = source.source_file,
    target.ingested_at  = source.ingested_at,
    target.updated_at   = CURRENT_TIMESTAMP
WHEN NOT MATCHED THEN
  INSERT (
    order_id, order_date, customer_id, product_id, category,
    quantity, unit_price, line_amount, region, is_return,
    source_file, ingested_at, updated_at
  ) VALUES (
    source.order_id, source.order_date, source.customer_id, source.product_id, source.category,
    source.quantity, source.unit_price, source.line_amount, source.region, source.is_return,
    source.source_file, source.ingested_at, CURRENT_TIMESTAMP
  );
*/

-- ---------------------------------------------------------------------
-- 4. GOLD LAYER: BUSINESS REPORTING AGGREGATION VIEW / MART
-- ---------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS gold_daily_sales_by_category_region AS
SELECT
    order_date,
    category,
    region,
    ROUND(SUM(line_amount), 2) AS net_revenue,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(quantity) AS net_units_sold,
    SUM(CASE WHEN quantity > 0 THEN quantity ELSE 0 END) AS gross_units_sold,
    CASE 
        WHEN COUNT(DISTINCT order_id) > 0 
        THEN ROUND(SUM(line_amount) / COUNT(DISTINCT order_id), 2)
        ELSE 0.00 
    END AS average_order_value
FROM silver_fct_orders
GROUP BY
    order_date,
    category,
    region
ORDER BY
    order_date ASC,
    category ASC,
    region ASC;
