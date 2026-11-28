# Migration: the earlier PV2 run on mother tree v4

These scripts take the strategies of the earlier 45-country PV2 run and put them into the current
method: the current strategy format, one plan edition at a time, placed on mother tree v4 (198 levers).
They cover four sources: national plans, sector plans, UNGA general-debate statements and budget
programme lines. They also build the page that shows the result (mother tree by region, country
explorer, Audit tab).

## Run it

The earlier run's data is in `pv2_data/` (59 MB: `union/` strategies, documents and budget rows, and
the per-country `llm/` workbooks the scripts read; a copy of the matching parts of `PV2/data`). You need
Python 3.9+ and `pip install -r ../requirements.txt`.

    cd migration
    ./run_migration.sh

This takes about two minutes and makes no model calls. It uses the mapping and instrument answers from the paid runs, which are saved in
`run/`. The page lands in `../data/migration_out/page/index.html`, with `rows_*.js` and `detail/` beside it;
keep those together when you publish it.

To redo the paid steps as well (gpt-5.4 through Azure, keys in `workflow/.env` as in the main README):

    ./run_migration.sh pv2_data ../data/migration_out --paid

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
| 5b | `budget_links.py` | none | Ties a national or sector plan response to a budget line only on a clear match: same country and lever, fiscal year inside the plan period, and a shared two-word phrase ("green building", "water supply"). Writes `budget_links.csv`; the lever panel shows the ties when budgets and plans are switched on. |
| 6 | `viewer.py` | none | The page: `viewer_template.html` and `forest.js` (country plants) with the data. |

`reshape_common.py` holds what steps 1 and 2 share (regions, country names, the tree, the columns). `country_groups.json` holds each country's World Bank income group (FY27) and UNDP human development value (2025 report) for the page's filters; add a line there for a new country.

## Add a country run through the current workflow

The live workflow (`../workflow/`, steps C, E, F and M on tree v4) runs one plan edition at a time.
To put a country it has run on this page:

1. Set the country up as in [workflow/RUNBOOK.md](../workflow/RUNBOOK.md): a config in
   `workflow/configs/<country>.json` listing its documents, the PDFs under `data/sources/<country>/`, and
   the Azure keys in `workflow/.env` (shared privately, never committed).
2. Run each plan, dry run first:

       cd workflow
       python3 -m pvii.run --list <country>
       python3 -m pvii.run --plan <plan_id> --dry-run
       python3 -m pvii.run --plan <plan_id>

3. Copy each plan's `strategies.csv` and `strategy_rows.csv` from `data/plans/<plan_id>/` to
   `migration/added/<country>/<plan_id>/`. For a country not among the 45, add
   `migration/added/<country>/region.txt` with one of the page's regions (for example `Pacific`).
4. `cd migration && ./run_migration.sh`. The page now shows the country. A plan with the same plan_id as
   one from the earlier run replaces it; the earlier run's other editions stay (run
   `python3 add_country.py <out> added/<country> --replace` by hand to show only the new run). Sector
   plans go in with the sector plans. A strategy on a lever the tree has since dropped goes to its family,
   and the reason column says so.
5. Commit `migration/added/<country>/` on a branch and open a pull request, then publish the page (below).

## Corrections

- `excluded_plans.json`: plan editions taken off the page (plan id → why), for example China 2030 (a
  World Bank report), a duplicate Tuvalu plan, Serbia's SDG report. They stay in the outputs but the
  page drops them and lists them on its Audit tab.
- `excluded_documents.json`: single source files taken out of the edition they were merged into
  (`reshape.py` skips their passages).
- `PERIOD_FIX` in `reshape.py` and `sources.py`: periods the document table lacks or gets wrong.

The document check of 23 November 2026 found these; the Audit tab shows every document by country,
source and year, and marks the periods that are guessed.

## Publishing the page

The shared copy is GitHub Pages: the `gh-pages` branch of this repo serves
https://sebpasha.github.io/PVII_Golden_Response_Tree/ (note: anyone with the link can open it). To update it, copy
`index.html`, `rows_*.js` and `detail/` from `../data/migration_out/page/` onto that branch, remove any
`detail/*.js` the new build no longer writes, and push.

## What is in the folder

- `pv2_data/`: the earlier run's data the scripts read (see above).
- `added/`: countries run through the current workflow, one folder of plan outputs each (step above).
- `run/`: the mapping and instrument answers of the paid runs (`mapping*.csv`, `instrument*.csv`,
  run reports `mapping_run*.json`).
- `plans.csv`, `placement_summary.csv`: the national-plan outputs of the last build, for reference.
  `strategies.csv` (25 MB), `passages.csv` (43 MB), the other sources and the page are not kept in the
  repo; the script rebuilds them.
