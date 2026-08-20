#!/usr/bin/env bash
# Synaptiq Exercise 2 — one-command live run.
# Bootstraps a venv, fetches the public UCI dataset if absent, builds the parquet,
# then re-executes the notebook end-to-end and renders HTML.
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
./.venv/bin/pip install --quiet -r requirements.txt
if [ ! -f online_retail_II.parquet ]; then
  if [ ! -f online_retail_II.xlsx ]; then
    echo "Fetching Online Retail II from the UCI archive (~46 MB)..."
    curl -sL -o online_retail_ii_uci.zip 'https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip'
    unzip -o online_retail_ii_uci.zip
  fi
  echo "Building parquet from xlsx (one-time, a few minutes)..."
  ./.venv/bin/python - <<'PY'
import pandas as pd
sheets = pd.read_excel('online_retail_II.xlsx', sheet_name=None)
pd.concat(sheets.values(), ignore_index=True).to_parquet('online_retail_II.parquet')
print('parquet built')
PY
fi
echo "== executing notebook end-to-end =="
./.venv/bin/jupyter nbconvert --to notebook --execute --inplace online_retail_ii_eda.ipynb
./.venv/bin/jupyter nbconvert --to html online_retail_ii_eda.ipynb
echo "Done. Open online_retail_ii_eda.html (or the .ipynb) to review."
