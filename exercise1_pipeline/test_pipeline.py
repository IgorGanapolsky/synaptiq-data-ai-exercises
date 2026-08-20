#!/usr/bin/env python3
"""
Unit and Integration Test Suite for Retail Data Pipeline
Verifies data quality cleaning, multi-date parsing, currency parsing,
CDC upserts, missing price catalog lookups, and aggregation contracts.
"""

import os
import unittest
import tempfile
import csv

from pipeline import RetailDataPipeline, DataCleaner


class TestDataCleaner(unittest.TestCase):

    def test_parse_currency(self):
        self.assertEqual(DataCleaner.parse_currency("$24.99"), 24.99)
        self.assertEqual(DataCleaner.parse_currency("$1,099.00"), 1099.00)
        self.assertEqual(DataCleaner.parse_currency("3.50"), 3.50)
        self.assertEqual(DataCleaner.parse_currency(""), None)
        self.assertEqual(DataCleaner.parse_currency(None), None)

    def test_parse_date(self):
        # ISO
        self.assertEqual(DataCleaner.parse_date("2024-01-01"), "2024-01-01")
        # US Format
        self.assertEqual(DataCleaner.parse_date("01/02/2024"), "2024-01-02")
        # Unix Epoch Timestamp (1704153600 = 2024-01-02 00:00:00 UTC)
        self.assertEqual(DataCleaner.parse_date("1704153600"), "2024-01-02")
        # Invalid
        self.assertIsNone(DataCleaner.parse_date("invalid_date"))

    def test_normalize_text(self):
        self.assertEqual(DataCleaner.normalize_text("west"), "West")
        self.assertEqual(DataCleaner.normalize_text("  electronics "), "Electronics")
        self.assertEqual(DataCleaner.normalize_text("", default="Unknown"), "Unknown")


class TestRetailPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = RetailDataPipeline(":memory:")
        self.test_dir = tempfile.mkdtemp()

        # Write sample products.csv
        self.products_file = os.path.join(self.test_dir, "products.csv")
        with open(self.products_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "product_name", "category", "list_price"])
            writer.writerow(["P001", "Wireless Mouse", "Electronics", "24.99"])
            writer.writerow(["P003", "Notebook", "stationery", "3.50"])
            writer.writerow(["P004", "Desk Lamp", "Home & Office", "29.99"])

        self.pipeline.load_products(self.products_file)

    def test_deduplication_and_cdc_upsert(self):
        # Day 1: Insert order O1003 with quantity 5
        day1_file = os.path.join(self.test_dir, "day1.csv")
        with open(day1_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "order_date", "customer_id", "product_id", "quantity", "unit_price", "region"])
            writer.writerow(["O1003", "2024-01-01", "C001", "P003", "5", "3.50", "North"])

        raw_c, ins_c, upd_c = self.pipeline.process_order_drop(day1_file)
        self.assertEqual(ins_c, 1)
        self.assertEqual(upd_c, 0)

        # Day 2: Replay O1003 with updated quantity 6 (CDC update)
        day2_file = os.path.join(self.test_dir, "day2.csv")
        with open(day2_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "order_date", "customer_id", "product_id", "quantity", "unit_price", "region"])
            writer.writerow(["O1003", "2024-01-01", "C001", "P003", "6", "3.50", "North"])

        raw_c2, ins_c2, upd_c2 = self.pipeline.process_order_drop(day2_file)
        self.assertEqual(ins_c2, 0)
        self.assertEqual(upd_c2, 1)

        # Verify Gold Mart reflects the updated quantity 6
        gold = self.pipeline.generate_gold_daily_sales_mart()
        self.assertEqual(len(gold), 1)
        self.assertEqual(gold[0]["order_count"], 1)
        self.assertEqual(gold[0]["net_units_sold"], 6)
        self.assertEqual(gold[0]["net_revenue"], 21.00)

    def test_missing_price_imputation_from_catalog(self):
        # Order with missing unit price
        day_file = os.path.join(self.test_dir, "missing_price.csv")
        with open(day_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "order_date", "customer_id", "product_id", "quantity", "unit_price", "region"])
            writer.writerow(["O2009", "2024-01-02", "C019", "P004", "2", "", "West"])

        raw_c, ins_c, upd_c = self.pipeline.process_order_drop(day_file)
        gold = self.pipeline.generate_gold_daily_sales_mart()
        self.assertEqual(len(gold), 1)
        # Should impute list_price 29.99 -> 2 * 29.99 = 59.98
        self.assertEqual(gold[0]["net_revenue"], 59.98)


if __name__ == "__main__":
    unittest.main()
