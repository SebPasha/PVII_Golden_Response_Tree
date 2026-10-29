# Runbook: running the workflow for one country

This is how Thailand was run in October 2026. The same steps work for any country that has a config in `configs/`.

## 1. Set up (once)

```bash
cd PVII_Golden_Response_Tree
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp workflow/.env.example workflow/.env
```

In `workflow/.env`, fill in:
- the Azure OpenAI endpoint, key and the two model names (small for E, large for C, F and M);
- the Document Intelligence endpoint and key, used to parse PDFs.

`.env` is gitignored. Never commit it.

Then check that nothing is broken. The 6 tests make no model calls and need no documents:

```bash
cd workflow
python3 -m pytest -q
```

## 2. Put the source PDFs in place

The PDFs are not in the repo. Each country config gives every document's path as `data/sources/<country>/...`, and the workflow looks for it under `PVII_SOURCES_ROOT`. By default that is the repo root, so the PDFs go in `data/sources/` (gitignored).

```bash
python3 -m pvii.run --list thailand
```

This lists every document, its `plan_id`, the file it expects, and whether it can run. A document with no confirmed period shows why it can't run. For Thailand those are the 20-Year Digital Economy plan and the 2024 National Adaptation Plan.

If you have PV2's data folder, point `PVII_SOURCES_ROOT` at it and `PVII_PARSE_CACHE_FALLBACK` at its `cache/`. That reuses every PDF parse PV2 already paid for.

## 3. Price it, then run it

Always price a plan before running it. A dry run spends nothing. It overestimates, and real runs have cost about 40% of the dry-run figure.

```bash
python3 -m pvii.run --plan thailand_ndp_2023-2027 --dry-run
python3 -m pvii.run --plan thailand_ndp_2023-2027
```

Or run one plan at a time with `run_thailand.sh`, which dry-runs each plan before running it.

Each run is capped by `--max-cost`, which defaults to $25 (set `PVII_MAX_COST_USD` to change it). Responses are cached by prompt, so a re-run after a failure only pays for the calls that didn't finish. Editing a prompt means paying again for that step.

What Thailand cost on 21 October 2026, before the E prompt was shortened by about 30%:

| plan_id | Cost | Strategies |
|---|---|---|
| thailand_ndp_2023-2027 | $4.24 | 514 |
| thailand_ndp_2017-2021 | $6.91 | 1,173 |
| thailand_ndp_2012-2016 | $4.60 | 886 |
| thailand_vision_2018-2037 | $1.50 | 294 |
| digital government (sector) | $5.10 | 462 |
| health security (sector) | $7.63 | 1,081 |
| climate change master plan (sector) | $2.62 | 372 |
| public health (sector) | $3.25 | 256 |
| education (sector) | $5.92 | 572 |

## 4. What comes out

Each plan writes `data/plans/<plan_id>/`:

| File | Step | What it holds |
|---|---|---|
| `context.json`, `context.md` | C | Publication date, period, structure, headline targets, risk framing and vocabulary. Never overwritten; use `--force-context` to re-read it |
| `risks.csv` | E | Risks the plan frames as risks, each with its quote and quote check |
| `strategy_rows.csv` | E | Strategies kept by the commitment test, one row per paragraph mention |
| `strategy_rows_dropped.csv` | E | Completed and background statements, kept for review |
| `strategies.csv` | F, M | Strategies folded within the plan and placed on the mother tree (v3: `group_id`, `family_id`, `pathway_id`; `node_id` is the deepest). `subpillar` and `pillar_rhdr` are the RHDR category and pillar |
| `proposals.csv` | M | Strategies the tree doesn't fit yet, proposed for its next release |
| `run.json`, `cost_report.md` | | Counts, every guard that fired, errors and cost |

After each plan, the country's tables are restacked under `data/country/<country>/`. `python3 -m pvii.run --global` restacks every country into `data/global/` without any model calls.

## 5. Check a run

- In `run.json`, `errors` should be empty. Look at `extract.guards` to see how many risks were dropped for a quote not found, and how many scores were set back to BAU.
- Read the first 20 rows of `strategies.csv` against the PDF.
- Look at `relation` in `strategies.csv`: same, differs or new against the tree. A strategy marked `new` lands in `proposals.csv`.

## Adding a country

Copy `configs/thailand.json` and change the slug, country and document list. Each document needs a `doc_type` (ndp, vision or sector), a file, a language and a period. Budget books and UNGA speeches go under `parked`; they don't run yet (see `../budget/` and `../unga/`).
