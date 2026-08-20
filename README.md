# Synaptiq Technical Exercises — Igor Ganapolsky

Submission for the **Senior Forward Deployed Data & AI Engineer** process (August 2026).
Both optional exercises are included, each runnable live with one command.

## Exercise 1 — Daily Retail Data Pipeline (`exercise1_pipeline/`)

Medallion-style (bronze → silver → gold) daily pipeline over the provided order drops and
product reference file. Stock **Python 3.10+ only** (stdlib csv/sqlite3) — no installs.

```bash
cd exercise1_pipeline && ./run_all.sh   # runs 5 tests, then the pipeline, prints the final table
```

Design decisions, data-anomaly handling, and the Databricks/Delta production mapping
(Auto Loader, Delta upsert semantics, DLT expectations, Liquid Clustering) are in
`exercise1_pipeline/NOTES.md`. Final table: `output_table.csv` (per order_date × category ×
region: net revenue, order count, net units, AOV).

## Exercise 2 — Online Retail II EDA (`exercise2_eda/`)

A single notebook that reads as a short analytical presentation over the full
1,067,371-row public UCI **Online Retail II** dataset — executive summary, data grain,
quality audit, exploratory analysis, ranked findings with confidence, caveats, next steps,
and the GenAI-usage disclosure.

```bash
cd exercise2_eda && ./run_all.sh   # bootstraps venv, fetches data if absent, executes notebook, renders HTML
```

The repo ships `online_retail_II.parquet` so the notebook runs immediately; the script can
also rebuild it from the original UCI download. Pre-rendered `online_retail_ii_eda.html`
is included for reading without running anything.

## Proof of live execution (`proof/`)

`PROOF.md` plus full timestamped terminal transcripts of same-day end-to-end runs, with
SHA-256 checksums of every produced artifact and notes on the independent verification
pass (all output numbers recomputed by a second implementation).
