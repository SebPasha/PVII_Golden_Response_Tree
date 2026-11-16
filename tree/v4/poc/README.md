# Proof of concept: the earlier multi-country strategies on tree v4

The 9,918 strategies of the earlier 45-country run, reshaped into the current strategy format and
placed on mother tree v4 (198 levers). No model calls.

    python3 reshape.py <earlier run's data folder> <out folder>   # strategies.csv, plans.csv, placement_summary.csv
    python3 viewer.py <out folder> <out.html>                      # mother tree by region + country explorer

- **Plan editions.** The earlier run pooled every edition of a country's plan. `reshape.py` splits each
  strategy back by the documents its passages come from: 110 plan editions, 14,213 strategy-by-plan rows.
  Periods come from the earlier run's document table; the fixes and the periods that had to be inferred
  are listed in `PERIOD_FIX` and flagged in `plans.csv` (`period_source`).
- **Objective, target, instrument.** From `tree/inputs/strategy_decomposition.csv` (read from strategy
  names only, so the instrument is stated for about a fifth).
- **Placement.** `objective_crosswalk.csv` maps each of the 456 objective labels to a lever, a live
  family, or a general branch (General Economy, General People, General Governance). It is a fixed
  table, not the mapping prompt: every strategy with the same objective label lands on the same node.
  58% reach a lever, 32% a live family, 10% a general branch; 152 of 198 levers are used.
- **Dropped parts.** The 31 levers dropped as unbacked, and the 5 families left without a lever, are
  drawn in grey and take no strategies: `reshape.py` stops if the crosswalk points at one.

`plans.csv` and `placement_summary.csv` here are the outputs of the last build; `strategies.csv` (25 MB)
and the page are kept out of the repo.
