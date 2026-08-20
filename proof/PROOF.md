# Live Execution Proof — Synaptiq Technical Exercises
**Candidate:** Igor Ganapolsky · **Captured:** Thu Aug 20, 2026 (EDT) · host: Darwin arm64

Both solutions were re-executed end-to-end from scratch on the day of submission. Full
terminal transcripts with SHA-256 checksums of every produced artifact are in this folder.

## Exercise 1 — Data Pipeline (`exercise1_run_transcript.txt`)
- `python3 test_pipeline.py` → **5/5 tests OK** (cleaning rules, upsert/dedup semantics).
- `python3 pipeline.py` → bronze → silver → gold run over both daily drops; **17-row**
  `output_table.csv` (per order_date × category × region: net revenue, orders, net units, AOV).
- Runs on stock Python 3 (stdlib only — csv, sqlite3, datetime). One command: `./run_all.sh`.
- Independent verification: every output row was recomputed from the raw CSVs by a second,
  separately-written implementation — all 17 rows reconcile, including last-write-wins on the
  corrected O1003, dedup of re-delivered O1002, epoch/US date normalization, catalog price
  imputation for truncated O2009, and returns carried as negative revenue (O2004).

## Exercise 2 — Online Retail II EDA (`exercise2_run_transcript.txt`)
- `jupyter nbconvert --to notebook --execute` → **6/6 code cells executed, 0 errors**;
  HTML render regenerated; checksums recorded for notebook, HTML, and all four figures.
- One command: `./run_all.sh` (bootstraps venv, fetches the public UCI dataset if absent,
  builds the parquet, executes the notebook, renders HTML).
- Independent verification: headline statistics recomputed from a separately downloaded copy
  of the UCI dataset — 1,067,371 rows; 22.77% missing Customer ID; 53,628 invoices;
  5,305 StockCodes; 5,942 identified buyers; 43 countries; £19.29M GMV — all match the report.
