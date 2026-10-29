# PV II golden response tree

This repo turns national development plans into a comparable map of how governments respond to risk.

It reads a country's national development plans and sector plans. From each one it pulls out:
- the **risks** the plan names, from a fixed list of eleven global risks (Climate Change, Pandemics, Technological Change and so on);
- the **strategies** the plan commits to, each read as objective × target group × instrument.

It then places every strategy on the **PV II mother tree**, a shared classification of policy mechanisms. That makes plans comparable across countries and across successive editions of the same plan.

The work is for UNDP's PV II project. This repo replaces the earlier PV2 prompt pipeline. It keeps PV2's data guards and drops its sprawl. Thailand was run end to end on 21 October 2026. China and India are configured but not yet run.

## Quick start

```bash
git clone https://github.com/SebPasha/PVII_Golden_Response_Tree.git
cd PVII_Golden_Response_Tree
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd workflow && python3 -m pytest -q      # 6 smoke tests, no keys or documents needed
```

To run a real plan you need Azure OpenAI and Document Intelligence keys in `workflow/.env`, and the source PDFs. [workflow/RUNBOOK.md](workflow/RUNBOOK.md) walks through it step by step, with the Thai costs. `workflow/run_thailand.sh` runs every Thai plan one at a time, with a dry run before each.

## Environment

**Python:** 3.9 or later. Sebastian's runs used Python 3.12 in a `.venv`. Every package is listed in `requirements.txt`: the `openai` client, the Azure Document Intelligence client, `pypdf`, `pymupdf`, `tiktoken` and `pytest`.

**Services:** PV II uses no Anthropic APIs. It calls two Azure services:

| Service | Used for | Variables in `workflow/.env` |
|---|---|---|
| Azure OpenAI, through the `openai` client | Every model call (steps C, E, F and M) | `OPENAI_BASE_URL`, `AZURE_API_KEY`, `OPENAI_MODEL` (small model, step E), `OPENAI_MODEL_ALL_AT_ONCE` (large model, C, F and M) |
| Azure AI Document Intelligence | Parsing each PDF once (the result is cached) | `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`, `AZURE_DOCUMENT_INTELLIGENCE_KEY` |

To set it up, copy `workflow/.env.example` to `workflow/.env` and fill it in. The example lists every variable the code reads; the optional ones can stay blank. `.env` is gitignored. Keys are shared privately, never through the repo. No keys are needed for the tests or for the tree.

## Repository layout

```
tree/              the mother tree (read-only to the workflow)
  v3/                the v3 release the workflow reads: tree_v3.json, crosswalks, the reviewer's framework
  v2/                the v2 release: tree_v2.json, crosswalks, the Thailand page
  v1/                the v1 release: tree_v1.json, the build scripts, the viewer, validation notes
  inputs/            the objective, target-group and instrument lists the tree is built from
workflow/          the live pipeline
  pvii/              the Python package (entry point: python3 -m pvii.run)
  prompts/           the prompts: C_context, C_context_reduce, E_extract, F_fold, M_map_v3 (M_map_v2, M_map for older trees)
  configs/           one JSON per country: its documents, types, periods and languages
  vocab/             closed lists: sectors, SDG goals, SDG target dimensions
  tests/             6 smoke tests with a fake model
  RUNBOOK.md         how to run a country
  run_thailand.sh    runs every Thai plan, one at a time
budget/            budget lane (prompts and code lifted from PV2, not running yet)
unga/              UNGA speeches lane (prompts and code lifted from PV2, not running yet)
data/              created by runs; gitignored (sources, parse cache, outputs)
```

| Folder | What it holds | Status |
|---|---|---|
| `workflow/` | The live pipeline: the `pvii` package, its prompts, one config per country, and the tests | **running** |
| `tree/` | The mother tree: v3 (read by the workflow), v2 and v1, each with everything needed to rebuild it. See [tree/README.md](tree/README.md) | built, read-only to the workflow |
| `budget/` | Budget prompts 5, 5b, 5c, 6 and 6b and their code, lifted unchanged. See [budget/README.md](budget/README.md) | **not running**; will map onto tree nodes |
| `unga/` | UNGA prompt 8 and its code, lifted unchanged. See [unga/README.md](unga/README.md) | **not running**; speeches will go through step E |

## Key ideas

- **One plan edition is the unit of work.** Each plan gets its own folder of tables, `data/plans/<plan_id>/`. A `plan_id` is `<country>_<doc_type>_<start>-<end>`, for example `thailand_ndp_2023-2027`. A sector plan adds a slug of its title. Countries are the plans stacked, and the global tables are the countries stacked.
- **Nothing is merged across plans.** A strategy carried from one plan to the next is a finding about time. It is read later by comparing plans on the tree (`editions.csv`), never by merging rows.
- **The mother tree** (v3, `tree/v3/`, the default; v2 and v1 kept): RHDR pillar → subpillar → group (L1) → family (L2, required) → pathway (L3), then objective (L4) and strategy (L5). v3 is the reviewer's framework of 27 October 2026 over v2's pathways. Set `PVII_TREE` to another release folder to map onto it. The 10 subpillars, plus 3 Standard holding branches, are the official **RHDR categories**. A strategy's category is the subpillar of the node it is placed on. Nothing guesses the category separately.
- **Quotes are checked.** Every risk, every related-risk link and every proactive or transformative score must carry a phrase that is found in the paragraph it came from. If none is found, the risk is dropped or the score falls back to BAU. Quotes stay in the plan's own language.
- **The commitment test.** A strategy is kept only when the plan commits to it or continues it. Completed results and background statements go to `strategy_rows_dropped.csv` for review.
- **Responses are cached by prompt.** A re-run after a failure only pays for the calls that didn't finish. Editing a prompt means paying again for that step.
- **Money is capped.** Every run takes `--max-cost`, and `--dry-run` prices a plan without spending anything.

## The steps, per plan

| Step | Prompt | What it does | Output in `data/plans/<plan_id>/` |
|---|---|---|---|
| 0 Register | none | The config gives each document a type, period and language. `plan_id` = `<country>_<doc_type>_<start>-<end>` | (every row carries it) |
| C Context | `C_context.txt`, `C_context_reduce.txt` | Reads the whole plan once, in 90k-token parts, then merges them: publication date, period, the plan's own structure, headline targets, risk framing and vocabulary. **The file is never overwritten**, so edit it freely | `context.json`, `context.md` |
| E Extract | `E_extract.txt` | Runs once per paragraph, with the context attached. Pulls out risks the plan frames as risks, and strategies as objective × target group × instrument, plus target year and place. Applies the commitment test. Also reads PV2 prompt 4's strategy fields: SDG targets, sector, response orientation, stated urgency, implementation status, timeline, quantified target, monitoring and legal basis. Every quote is checked against its own paragraph, and a risk or a proactive or transformative score whose quote is not found there is dropped | `risks.csv`, `strategy_rows.csv`, `strategy_rows_dropped.csv` |
| F Fold | `F_fold.txt` | Merges repeat statements of one strategy **within this plan only**, and merges their fields the PV2 way (SDG targets unioned, highest urgency, strongest status and basis, most common sector) | (feeds M) |
| M Map | `M_map_v3.txt` (`M_map_v2.txt`, `M_map.txt` for older releases) | Places each strategy on the mother tree (v3 by default: a family is required, a pathway when the wording names the channel, a group alone is counted; v1: same, differs or new against its objectives), under the tree's own depth rule. Normalises the target group and instrument to the tree's lists. The RHDR category and pillar are the tree's own (`subpillar`, `pillar_rhdr`): E does not guess them | `strategies.csv`, `proposals.csv` |
| Stack | none | Plans are stacked into the country, and countries into the global tables. `editions.csv` shows which tree nodes each plan carried, added or dropped from the previous edition | `data/country/<slug>/`, `data/global/` |

Each plan also gets `run.json` (counts, quote checks, prompt hashes, tree version, cost) and `cost_report.md`.

### Time

Every row carries `period_start` and `period_end` from its plan. A strategy's `target_year` is recorded only where the plan states one, and its `horizon` says whether that year falls in the plan period (`plan`) or after it (`long`). A strategy is never merged across editions. Continuity between plans is read from `editions.csv`, by tree node. When the budget lane returns, a fiscal year joins only to the plan in force that year.

## What is not in this repo

- **Source PDFs, parse cache and run outputs.** All of these live under `data/`, which is gitignored. The Thai outputs from October 2026 exist only on Sebastian's machine. Ask for them rather than re-running, which costs about $30 to $45 for the nine Thai plans.
- **API keys.** They go in `workflow/.env`, which is gitignored. `workflow/.env.example` lists every variable.
- **The Mirror Forests page.** This is the visual that draws each country's tree. Its builder still lives in the older PV2 repo (Environment_UNDP) and reads this repo's `data/plans/`.

## Working on it

- Keep it basic. There are 6 smoke tests and no CI. Extend an existing test rather than adding new files.
- Keep the data guards: the commitment test, the quote checks, "no quote, no risk", and the closed lists. They are what makes the output trustworthy.
- `tree/v1` is a signed-off release. The workflow only reads it. Step M's `proposals.csv` files feed the next release.
- Never commit `.env` or `data/`.

## Known open issues (October 2026)

- The Thai outputs on disk predate the 22 October prompt changes, and they still carry the old category columns. They will match the code again after a re-run.
- Proactive and transformative scores look generous, at 49% on the 13th Plan. The quote check proves the phrase exists, not that it names a change.
- Recall is unchecked. Adding the classification fields cut kept rows from 749 to 562 on the 13th Plan.
- A sector strategy that repeats a national one is counted in both.
- Fold compares rows only within shards of up to 60, so some duplicates survive.
- The dry run overestimates cost. Real runs have cost about 40% of the estimate.
- Two Thai documents can't run until their periods are confirmed: the 20-Year Digital Economy plan and the 2024 National Adaptation Plan.

## Lifted from PV2

| Here | From PV2 | Change |
|---|---|---|
| `pvii/llm.py` | `workflow/pv2/extract/llm.py` | Env names only |
| `pvii/parse.py` | `workflow/pv2/parse/parse.py` | Reads PV2's parse cache without writing to it |
| `pvii/config.py` | `workflow/pv2/extract/config.py` | Cut to the four steps |
| `pvii/quotes.py` | `validate/truth.py`, `validate/evidence.py` | Only the quote matcher |
| `prompts/C_*` | prompt 4a | One document, all of it, plus framing and vocabulary |
| `prompts/E_extract.txt` | prompts 1, 3 and 4 | One pass; quotes stay in the source language; prompt 4's strategy fields read per paragraph |
| `pvii/vocab.py`, `vocab/` | `pv2/vocab.py`, `extract/schemas.py`, `calcs/panel.py`, `vocab/` | Sector and SDG lookups, the clamps, and the risk pairing |
| `prompts/F_fold.txt` | prompt 4b | Within one plan only |
| `prompts/M_map.txt` | new | Uses the tree's depth rule from `tree/v1/README.md` |

PV2 code and tests not carried over: stages 1, 2, 3, 4, 4_adopt, 4_consolidate, 4r, 7 and 8; union, calcs, publish, dashboard, screen and the validators other than the quote check. They also include the size ratchet, the prompt-currency and pipeline-map gates, and the frozen-baseline test. These are listed on the [Workflow Redesign page](https://claude.ai/artifact/68Td9yeaHGUY7ybStUVWhX).
