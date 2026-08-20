#!/usr/bin/env python3
"""
Production Retail Sales Data Pipeline (Medallion Architecture)
--------------------------------------------------------------
Ingests daily order drop files (CSV) and product catalog reference data (CSV/XLSX),
conforms and cleans the data (Silver layer with CDC upsert/dedup semantics), and produces
the daily sales reporting table (Gold layer) per business specifications.

Business Reporting Grain:
  Per Day (order_date), Per Product Category (category), Per Sales Region (region):
  - Net Revenue
  - Order Count (Distinct Orders)
  - Units Sold (Net Units)
  - Average Order Value (AOV = Net Revenue / Order Count)

Designed for daily scheduled execution with complete idempotency.
"""

from __future__ import annotations

import csv
import datetime
import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class CleanedOrder:
    order_id: str
    order_date: str          # Normalized ISO YYYY-MM-DD
    customer_id: Optional[str] # Nullable
    product_id: str
    quantity: int
    unit_price: float        # Normalized float
    region: str              # Normalized Title Case (East, West, North, South)
    ingested_at: str         # UTC timestamp of pipeline run
    source_file: str


@dataclass
class ProductReference:
    product_id: str
    product_name: str
    category: str            # Normalized Title Case
    list_price: float


class DataCleaner:
    """Handles raw data parsing, schema enforcement, and normalization."""

    @staticmethod
    def parse_currency(val: Any) -> Optional[float]:
        """Strips currency symbols ('$', ','), whitespace, and returns float."""
        if val is None:
            return None
        s = str(val).strip()
        if not s:
            return None
        # Remove '$' and ','
        s_clean = re.sub(r'[\$,]', '', s)
        try:
            return float(s_clean)
        except ValueError:
            return None

    @staticmethod
    def parse_date(val: Any) -> Optional[str]:
        """
        Normalizes varying date representations into ISO YYYY-MM-DD format:
        - ISO: '2024-01-01'
        - US: '01/01/2024', '01/02/2024'
        - Epoch Timestamp: '1704153600' (2024-01-02 00:00:00 UTC)
        """
        if val is None:
            return None
        s = str(val).strip()
        if not s:
            return None

        # Check if Unix Epoch timestamp (10-digit integer)
        if s.isdigit() and len(s) >= 10:
            try:
                ts = int(s)
                dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
                return dt.strftime('%Y-%m-%d')
            except (ValueError, OverflowError):
                pass

        # Try standard ISO YYYY-MM-DD
        try:
            dt = datetime.datetime.strptime(s, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

        # Try US format MM/DD/YYYY
        try:
            dt = datetime.datetime.strptime(s, '%m/%d/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

        return None

    @staticmethod
    def normalize_text(val: Any, default: str = "Unknown") -> str:
        """Trims whitespace and applies Title Case."""
        if val is None:
            return default
        s = str(val).strip()
        return s.title() if s else default


class RetailDataPipeline:
    """
    Modular ELT Pipeline orchestrator.
    Uses SQLite as the local relational execution engine (mimicking Databricks/Delta Lake tables).
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        """Initializes Bronze staging, Silver conformed, and Gold reporting schemas."""
        with self.conn:
            # Bronze: Raw append-only staging log
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS bronze_orders_raw (
                    raw_order_id TEXT,
                    raw_order_date TEXT,
                    raw_customer_id TEXT,
                    raw_product_id TEXT,
                    raw_quantity TEXT,
                    raw_unit_price TEXT,
                    raw_region TEXT,
                    extra_data TEXT,
                    source_file TEXT,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Silver Products: Reference lookup table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS silver_dim_products (
                    product_id TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    list_price REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Silver Orders: Cleaned, conformed, deduplicated table with primary key semantics
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS silver_fct_orders (
                    order_id TEXT PRIMARY KEY,
                    order_date DATE NOT NULL,
                    customer_id TEXT,
                    product_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    line_amount REAL NOT NULL,
                    region TEXT NOT NULL,
                    is_return BOOLEAN NOT NULL,
                    source_file TEXT NOT NULL,
                    ingested_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def load_products(self, products_csv_path: str) -> int:
        """Loads and normalizes product reference data into Silver dim table."""
        count = 0
        with open(products_csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            products = []
            for row in reader:
                pid = row.get("product_id", "").strip()
                pname = row.get("product_name", "").strip()
                category = DataCleaner.normalize_text(row.get("category", ""), default="Uncategorized")
                list_price = DataCleaner.parse_currency(row.get("list_price", 0.0)) or 0.0

                if pid:
                    products.append((pid, pname, category, list_price))
                    count += 1

            with self.conn:
                self.conn.executemany("""
                    INSERT INTO silver_dim_products (product_id, product_name, category, list_price, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(product_id) DO UPDATE SET
                        product_name = excluded.product_name,
                        category = excluded.category,
                        list_price = excluded.list_price,
                        updated_at = CURRENT_TIMESTAMP;
                """, products)
        return count

    def get_product_catalog(self) -> Dict[str, Tuple[str, float]]:
        """Returns in-memory map of product_id -> (category, list_price)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT product_id, category, list_price FROM silver_dim_products")
        return {row["product_id"]: (row["category"], row["list_price"]) for row in cursor.fetchall()}

    def process_order_drop(self, file_path: str) -> Tuple[int, int, int]:
        """
        Ingests a daily orders CSV drop into Bronze, cleanses, enriches,
        and merges (upserts) into Silver conformed table.

        Returns: (rows_raw, rows_inserted, rows_updated)
        """
        source_file = os.path.basename(file_path)
        ingested_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        product_catalog = self.get_product_catalog()

        raw_rows = []
        silver_records = []

        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return (0, 0, 0)

            for row in reader:
                if not row or not any(row):
                    continue

                # Handle potential extra columns (e.g. EXTRA_FLAG in day 1)
                order_id = row[0].strip() if len(row) > 0 else ""
                raw_date = row[1].strip() if len(row) > 1 else ""
                raw_cust = row[2].strip() if len(row) > 2 else ""
                raw_prod = row[3].strip() if len(row) > 3 else ""
                raw_qty  = row[4].strip() if len(row) > 4 else ""
                raw_price = row[5].strip() if len(row) > 5 else ""
                raw_region = row[6].strip() if len(row) > 6 else ""
                extra = "|".join(row[7:]) if len(row) > 7 else ""

                raw_rows.append((
                    order_id, raw_date, raw_cust, raw_prod, raw_qty,
                    raw_price, raw_region, extra, source_file
                ))

                # Normalization & Data Quality Cleaning
                norm_date = DataCleaner.parse_date(raw_date) or "1970-01-01"
                norm_cust = raw_cust if raw_cust else None
                norm_prod = raw_prod.strip() if raw_prod else "UNKNOWN_PRODUCT"
                
                # Quantity parsing
                try:
                    qty = int(raw_qty)
                except ValueError:
                    qty = 0

                # Unit Price with Catalog Fallback
                parsed_price = DataCleaner.parse_currency(raw_price)
                
                # Lookup category and catalog price
                if norm_prod in product_catalog:
                    cat, list_p = product_catalog[norm_prod]
                else:
                    cat, list_p = "Unknown", 0.0

                # If unit price missing from order record, impute using catalog list price
                effective_price = parsed_price if parsed_price is not None else list_p
                line_amount = round(qty * effective_price, 2)
                norm_region = DataCleaner.normalize_text(raw_region, default="Unknown")
                is_return = 1 if qty < 0 else 0

                silver_records.append((
                    order_id, norm_date, norm_cust, norm_prod, cat,
                    qty, effective_price, line_amount, norm_region,
                    is_return, source_file, ingested_at
                ))

        # 1. Append to Bronze
        with self.conn:
            self.conn.executemany("""
                INSERT INTO bronze_orders_raw (
                    raw_order_id, raw_order_date, raw_customer_id, raw_product_id,
                    raw_quantity, raw_unit_price, raw_region, extra_data, source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, raw_rows)

        # 2. Upsert (MERGE) into Silver
        # In SQL/Delta: MERGE INTO silver USING new_batch ON order_id
        # In SQLite: INSERT ... ON CONFLICT(order_id) DO UPDATE
        inserted = 0
        updated = 0

        with self.conn:
            for rec in silver_records:
                cur = self.conn.cursor()
                cur.execute("SELECT order_id FROM silver_fct_orders WHERE order_id = ?", (rec[0],))
                exists = cur.fetchone()

                self.conn.execute("""
                    INSERT INTO silver_fct_orders (
                        order_id, order_date, customer_id, product_id, category,
                        quantity, unit_price, line_amount, region, is_return,
                        source_file, ingested_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(order_id) DO UPDATE SET
                        order_date = excluded.order_date,
                        customer_id = excluded.customer_id,
                        product_id = excluded.product_id,
                        category = excluded.category,
                        quantity = excluded.quantity,
                        unit_price = excluded.unit_price,
                        line_amount = excluded.line_amount,
                        region = excluded.region,
                        is_return = excluded.is_return,
                        source_file = excluded.source_file,
                        ingested_at = excluded.ingested_at,
                        updated_at = CURRENT_TIMESTAMP;
                """, rec)

                if exists:
                    updated += 1
                else:
                    inserted += 1

        return (len(raw_rows), inserted, updated)

    def generate_gold_daily_sales_mart(self) -> List[Dict[str, Any]]:
        """
        Executes the business aggregation query:
        Per Day, Per Product Category, Per Region:
        - Net Revenue: SUM(line_amount)
        - Order Count: COUNT(DISTINCT order_id)
        - Units Sold: SUM(quantity) (Net units) and Gross Units
        - AOV: Net Revenue / Order Count
        """
        query = """
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
                    ELSE 0.0 
                END AS average_order_value
            FROM silver_fct_orders
            GROUP BY order_date, category, region
            ORDER BY order_date ASC, category ASC, region ASC;
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows


def run_pipeline(data_dir: str, output_csv_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Runs end-to-end ingestion and outputs report table."""
    pipeline = RetailDataPipeline()

    products_file = os.path.join(data_dir, "products.csv")
    if not os.path.exists(products_file):
        raise FileNotFoundError(f"products.csv not found at {products_file}")

    print(f"[*] Ingesting product catalog from {products_file}...")
    prod_count = pipeline.load_products(products_file)
    print(f"[✓] Loaded {prod_count} product reference records into Silver Dim.")

    order_files = sorted([
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.startswith("orders_") and f.endswith(".csv")
    ])

    for fpath in order_files:
        print(f"[*] Processing daily drop {os.path.basename(fpath)}...")
        raw_c, ins_c, upd_c = pipeline.process_order_drop(fpath)
        print(f"[✓] Processed {raw_c} raw rows -> {ins_c} new inserts, {upd_c} updates/replays.")

    print("\n[*] Generating Gold Daily Sales Reporting Mart...")
    gold_rows = pipeline.generate_gold_daily_sales_mart()

    if output_csv_path:
        with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
            if gold_rows:
                writer = csv.DictWriter(f, fieldnames=list(gold_rows[0].keys()))
                writer.writeheader()
                writer.writerows(gold_rows)
        print(f"[✓] Exported {len(gold_rows)} rows to {output_csv_path}")

    return gold_rows


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(base_dir, "output_table.csv")
    results = run_pipeline(base_dir, out_file)
    
    print("\n" + "="*85)
    print(f"{'Order Date':<12} | {'Category':<15} | {'Region':<8} | {'Net Revenue':<12} | {'Orders':<6} | {'Net Units':<10} | {'AOV':<10}")
    print("="*85)
    for r in results:
        print(f"{r['order_date']:<12} | {r['category']:<15} | {r['region']:<8} | ${r['net_revenue']:>10.2f} | {r['order_count']:>6} | {r['net_units_sold']:>10} | ${r['average_order_value']:>8.2f}")
    print("="*85)
