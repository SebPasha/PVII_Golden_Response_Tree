#!/usr/bin/env bash
# Rebuild the migration of the earlier PV2 run onto mother tree v4, and its page.
#
#   ./run_migration.sh <PV2 data folder> <out folder>            # no model calls: uses the answers saved in run/
#   ./run_migration.sh <PV2 data folder> <out folder> --paid     # also re-runs the mapping and the instrument pass
#                                                                 # (gpt-5.4, keys in workflow/.env; about $95, see README)
#
# The page is written to <out folder>/page/index.html, with rows_*.js and detail/ beside it.
set -euo pipefail
cd "$(dirname "$0")"

DATA=${1:?give the PV2 data folder (the one holding union/ and llm/)}
OUT=${2:?give an out folder}
PAID=${3:-}

if [ "$PAID" = "--paid" ]; then
  echo "== 1. national plans, placed by the objective crosswalk (input for the mapping)"
  python3 reshape.py "$DATA" "$OUT"
  echo "== 2. sector plans, UNGA statements, budgets"
  python3 sources.py "$DATA" "$OUT"
  for s in "" sector unga budget; do
    dir="$OUT${s:+/$s}"; suffix="${s:+_$s}"
    echo "== 3. mapping (step M) for ${s:-national plans}: dry run, then the real run"
    batch=""; [ "$s" = budget ] && batch="--batch 50"   # budget lines are short: 50 a call
    python3 map_run.py "$dir" $batch --dry-run --max-cost 100
    python3 map_run.py "$dir" $batch --max-cost 100
    echo "== 4. instrument pass for ${s:-national plans}"
    python3 inst_run.py "$dir" --mapping "$dir/mapping.csv" --max-cost 30
    cp "$dir/mapping.csv" "run/mapping$suffix.csv"
    cp "$dir/mapping_run.json" "run/mapping_run$suffix.json"
    cp "$dir/instrument.csv" "run/instrument$suffix.csv"
  done
fi

echo "== 5. national plans, placed by the mapping"
python3 reshape.py "$DATA" "$OUT" --mapping=run/mapping.csv --instrument=run/instrument.csv
echo "== 6. the other sources, placed by the mapping"
python3 sources.py "$DATA" "$OUT" --mapping=run
echo "== 7. the page"
python3 viewer.py "$OUT" "$OUT/page/index.html"
echo "done: open $OUT/page/index.html (keep rows_*.js and detail/ beside it when you publish it)"
