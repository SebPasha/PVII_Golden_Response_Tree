# PV II golden tree workflow

This workflow reads national development plans and sectoral plans, pulls out the risks they name and the strategies they commit to, and places each strategy on the PV II mother tree. The unit of work is **one plan edition**. Each plan produces one set of tables. A country's tables are its plans stacked, and the global tables are the countries stacked.

This repo replaces the PV2 prompt pipeline. Where possible, code, prompts and tests are lifted from PV2. Lifted code says where it came from; the prompts carry no provenance, and the table below records it. The design is on the [Workflow Redesign page](https://claude.ai/artifact/68Td9yeaHGUY7ybStUVWhX).

## What is where

| Folder | What it holds | Status |
|---|---|---|
| `workflow/` | The live pipeline: the `pvii` package, its four prompts, one config per country, and the tests | **running** |
| `tree/` | The mother tree: the v1 release that the workflow reads, plus everything needed to rebuild it | built, read-only to the workflow |
| `parked/budget/` | Budget prompts 5, 5b, 5c, 6 and 6b and their code, lifted unchanged | **not running**; comes back on tree nodes |
| `parked/unga/` | UNGA prompt 8 and its code, lifted unchanged | **not running**; speeches will go through step E |

## The steps, per plan

| Step | Prompt | What it does | Output in `data/plans/<plan_id>/` |
|---|---|---|---|
| 0 Register | none | The config gives each document a type, period and language. `plan_id` = `<country>_<doc_type>_<start>-<end>` | (every row carries it) |
| C Context | `C_context.txt`, `C_context_reduce.txt` | Reads the whole plan once, in 90k-token parts, then merges them: period, the plan's own structure, headline targets, risk framing and vocabulary. **The file is never overwritten**, so edit it freely | `context.json`, `context.md` |
| E Extract | `E_extract.txt` | Runs once per paragraph, with the context attached. Pulls out risks the plan frames as risks, and strategies as objective × target group × instrument, plus target year and place. Applies the commitment test. Also reads PV2 prompt 4's strategy fields: RHDR category (rhdr_2026_10), SDG targets, sector, response orientation, stated urgency, implementation status, timeline, quantified target, monitoring and legal basis. Every quote is checked against its own paragraph, and a risk or a proactive or transformative score whose quote is not found there is dropped | `risks.csv`, `strategy_rows.csv`, `strategy_rows_dropped.csv` |
| F Fold | `F_fold.txt` | Merges repeat statements of one strategy **within this plan only**, and merges their fields the PV2 way (SDG targets unioned, highest urgency, strongest status and basis, most common category and sector) | (feeds M) |
| M Map | `M_map.txt` | Places each strategy on the mother tree as same, differs or new, under the tree's own depth rule. Normalises the target group and instrument to the tree's lists | `strategies.csv`, `proposals.csv` |
| Stack | none | Plans are stacked into the country, and countries into the global tables. `editions.csv` shows which tree nodes each plan carried, added or dropped from the previous edition | `data/country/<slug>/`, `data/global/` |

Each plan also gets `run.json` (counts, quote checks, prompt hashes, tree version, cost) and `cost_report.md`.

### Time

Every row carries `period_start` and `period_end` from its plan. A strategy's `target_year` is recorded only where the plan states one, and its `horizon` says whether that year falls in the plan period (`plan`) or after it (`long`). A strategy is never merged across editions. Continuity between plans is read from `editions.csv`, by tree node. When the budget lane returns, a fiscal year joins only to the plan in force that year.

## Run it

```bash
pip install -r requirements.txt
cp workflow/.env.example workflow/.env      # fill in; PV2's workflow/.env keys work as they are
cd workflow

python3 -m pvii.run --list thailand                          # every document, its plan_id, and whether it runs
python3 -m pvii.run --plan thailand_ndp_2023-2027 --dry-run  # price it, spend nothing
python3 -m pvii.run --plan thailand_ndp_2023-2027            # C, E, F, M, then stack
python3 -m pvii.run --country thailand --doc-types ndp,vision,sector
python3 -m pvii.run --global                                 # restack everything, no model calls
python3 -m pytest -q                                         # 6 smoke tests: no network, no documents
```

On Sebastian's Mac, set `PVII_SOURCES_ROOT=~/Developer/Environment_UNDP/PV2/data` and `PVII_PARSE_CACHE_FALLBACK=~/Developer/Environment_UNDP/PV2/data/cache`. The source library is then read in place, and no Document Intelligence parse that PV2 already paid for is bought again. PV2's folders are only read, never written.

Responses are cached by prompt. A re-run after a failure, or after you edit `context.json`, only pays for the calls whose prompt changed. Each run is capped by `--max-cost` (default $25).

## Lifted from PV2

| Here | From PV2 | Change |
|---|---|---|
| `pvii/llm.py` | `workflow/pv2/extract/llm.py` | Env names only |
| `pvii/parse.py` | `workflow/pv2/parse/parse.py` | Reads PV2's parse cache without writing to it |
| `pvii/config.py` | `workflow/pv2/extract/config.py` | Cut to the four steps |
| `pvii/quotes.py` | `validate/truth.py`, `validate/evidence.py` | Only the quote matcher |
| `prompts/C_*` | prompt 4a | One document, all of it, plus framing and vocabulary |
| `prompts/E_extract.txt` | prompts 1, 3 and 4 (rhdr_2026_10) | One pass; quotes stay in the source language; prompt 4's strategy fields read per paragraph |
| `pvii/vocab.py`, `vocab/` | `pv2/vocab.py`, `extract/schemas.py`, `calcs/panel.py`, `vocab/`, `frameworks/rhdr_2026_10/vocab.json` | The category framework, sector and SDG lookups, the clamps, and the risk pairing |
| `prompts/F_fold.txt` | prompt 4b | Within one plan only |
| `prompts/M_map.txt` | new | Uses the tree's depth rule from `tree/v1/README.md` |

PV2 code and tests not carried over: stages 1, 2, 3, 4, 4_adopt, 4_consolidate, 4r, 7 and 8; union, calcs, publish, dashboard, screen and the validators other than the quote check. They also include the size ratchet, the prompt-currency and pipeline-map gates, and the frozen-baseline test. These are listed on the [Workflow Redesign page](https://claude.ai/artifact/68Td9yeaHGUY7ybStUVWhX).
