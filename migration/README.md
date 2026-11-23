# Migration: the earlier PV2 run on mother tree v4

These scripts take the strategies of the earlier 45-country PV2 run and put them into the current
method: the current strategy format, one plan edition at a time, placed on mother tree v4 (198 levers).
They cover four sources: national plans, sector plans, UNGA general-debate statements and budget
programme lines. They also build the page that shows the result (mother tree by region, country
explorer, Audit tab).

## Run it

You need the earlier run's data folder (`PV2/data`, the folder holding `union/` and `llm/`; ask
Sebastian for a copy) and Python 3.9+ with `openpyxl` (`pip install -r ../requirements.txt`).

    cd migration
    ./run_migration.sh <PV2 data folder> <out folder>

This takes about two minutes and makes no model calls. It uses the mapping and instrument answers from the paid runs, which are saved in
`run/`. The page lands in `<out folder>/page/index.html`, with `rows_*.js` and `detail/` beside it;
keep those together when you publish it.

To redo the paid steps as well (gpt-5.4 through Azure, keys in `workflow/.env` as in the main README):

    ./run_migration.sh <PV2 data folder> <out folder> --paid

Each mapping run prices itself with a dry run first and stops at its `--max-cost`. Answers are
cached, so a run that stops can be started again and pays only for what is missing. The paid runs of
17 to 19 November 2026 cost about $93: national plans $17, sector plans $46.56, UNGA $2.63,
budgets $17.06, instrument pass $9.51.

## The steps

| Step | Script | Model calls | What it does |
|---|---|---|---|
| 1 | `reshape.py` | none | National plans and visions. The earlier run pooled every edition of a country's plan; this splits each strategy back by the documents its passages come from (`llm/<c>/<c>_strategy_rows.xlsx`), so a strategy found in three editions gives three rows. Periods come from `union/documents.csv`, with hand fixes in `PERIOD_FIX`. Objective, target and instrument come from `tree/inputs/strategy_decomposition.csv`. Without `--mapping` it places strategies by `objective_crosswalk.csv` (a fixed objective-label table). |
| 2 | `sources.py` | none | Sector plans (`llm/<c>/sector/<c>_sector_responses.xlsx`), UNGA statements (`llm/<c>/unga/<c>_unga_statements.xlsx`) and budget programme lines (`union/budget_rows.csv`), in the same columns, under `<out>/sector`, `unga` and `budget`. Budget overhead lines (administration, personnel) go to General Governance by rule. Sector periods have hand fixes in `PERIOD_FIX`. |
| 3 | `map_run.py` | gpt-5.4 | The workflow's step M (`workflow/prompts/M_map_v4.txt`) on every distinct strategy, 25 a call (budget 50): a lever, a family, a general branch, or unmapped with a reason. Writes `mapping.csv`. |
| 4 | `inst_run.py` | gpt-5.4 | Names the policy instrument (plain words, class Money/Authority/Information/Organisation, list entry where one fits) for strategies the mapping left without one. Writes `instrument.csv`. |
| 5 | `reshape.py --mapping= --instrument=`, `sources.py --mapping=run` | none | Steps 1 and 2 again, placed by the mapping instead of the crosswalk. |
| 6 | `viewer.py` | none | The page: `viewer_template.html` and `forest.js` (country plants) with the data. |

`reshape_common.py` holds what steps 1 and 2 share (regions, country names, the tree, the columns).

## Corrections

- `excluded_plans.json`: plan editions taken off the page (plan id → why), for example China 2030 (a
  World Bank report), a duplicate Tuvalu plan, Serbia's SDG report. They stay in the outputs but the
  page drops them and lists them on its Audit tab.
- `excluded_documents.json`: single source files taken out of the edition they were merged into
  (`reshape.py` skips their passages).
- `PERIOD_FIX` in `reshape.py` and `sources.py`: periods the document table lacks or gets wrong.

The document check of 23 November 2026 found these; the Audit tab shows every document by country,
source and year, and marks the periods that are guessed.

## What is in the folder

- `run/`: the mapping and instrument answers of the paid runs (`mapping*.csv`, `instrument*.csv`,
  run reports `mapping_run*.json`).
- `plans.csv`, `placement_summary.csv`: the national-plan outputs of the last build, for reference.
  `strategies.csv` (25 MB), `passages.csv` (43 MB), the other sources and the page are not kept in the
  repo; the script rebuilds them.
