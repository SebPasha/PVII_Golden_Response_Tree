#!/usr/bin/env bash
# Runs every runnable Thai plan, one at a time: a dry run first, then the real run.
# Each run is capped at MAX_COST dollars (default 10). Usage, from workflow/:
#   ./run_thailand.sh            # all nine plans
#   ./run_thailand.sh 2023-2027  # only plans whose plan_id contains this text
set -euo pipefail
cd "$(dirname "$0")"
MAX_COST="${MAX_COST:-10}"
PLANS=(
  thailand_ndp_2023-2027
  thailand_ndp_2017-2021
  thailand_ndp_2012-2016
  thailand_vision_2018-2037
  thailand_sector_2023-2027_digital-government-development-plan
  thailand_sector_2023-2027_national-action-plan-for-health-security
  thailand_sector_2015-2050_climate-change-master-plan
  thailand_sector_2017-2036_national-strategic-plan-for-public-healt
  thailand_sector_2017-2036_national-education-plan
)
for plan in "${PLANS[@]}"; do
  [[ -n "${1:-}" && "$plan" != *"$1"* ]] && continue
  echo "=== $plan: dry run"
  python3 -m pvii.run --plan "$plan" --dry-run --max-cost "$MAX_COST"
  echo "=== $plan: run (cap \$$MAX_COST)"
  python3 -m pvii.run --plan "$plan" --max-cost "$MAX_COST"
done
python3 -m pvii.run --global
