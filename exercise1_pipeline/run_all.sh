#!/usr/bin/env bash
# Synaptiq Exercise 1 — one-command live run.
# Requires only Python 3.10+ (stdlib: csv, sqlite3, datetime). No pip installs.
set -euo pipefail
cd "$(dirname "$0")"
echo "== tests =="
python3 test_pipeline.py
echo
echo "== pipeline (daily drops 2024-01-01 + 2024-01-02 -> gold daily sales table) =="
python3 pipeline.py
echo
echo "Done. Final table: output_table.csv / output_table.md"
