# Mother tree v2 (draft, 28 October 2026)

Three placement levels, literature-led and top-down, under the RHDR pillars and subpillars:

- `families_v2.csv`: 28 families (L1). Each carries the RHDR clause it answers, its literature and a one-line meaning.
- `mechanisms_v2.csv`: 99 mechanisms (L2). Each names the intermediate variable it moves, the plan words that signal it, its SDG targets and the asset classes it builds.
- `pathways_v2.csv`: the 259 v1 mechanisms, kept with their ids as the causal pathways (L3). Seven are merged into a sibling; the `merged_into` column says where.

Depth rule: family when a strategy only names the domain, mechanism when it names the lever, pathway when it names the causal channel and no sibling.

Crosswalks, all built from the three levels: `rhdr_clauses.csv`, `sdg_crosswalk.csv` (with the 5P dimension), `risk_matrix.csv` (rolled up from pathway tags, conditional links flagged), `asset_matrix.csv`, `target_classes.csv`, `instrument_classes.csv` (Hood: information, authority, money, organisation) and `old_family_default.csv` (v1 family to v2 family). `tree_v2.json` holds everything in one file.

## Rebuild

```bash
cd tree/v2
python3 build.py                      # structure_v2.py + mechanisms_v2.py + ../v1 -> CSVs and tree_v2.json
python3 thailand.py                   # data/plans/thailand_* and data/country/thailand -> thailand_v2.html
python3 test_bottomup.py <review.html> # bottom-up tree v48 leaf objectives read through v2 -> bottomup_test.json
```

`thailand.py` reads the workflow outputs under `data/`. Until those are at hand, `--from <mirror.json>` runs it on the Mirror Forests export instead, which has no SDG targets, urgency, status or quotes; the page says so on the Method tab. Mechanism placement in that mode is provisional, by plan words, and is replaced by the model's `node_id` once the workflow places strategies on v2.

`thailand_v2.html` is the page, drawn in the Mirror Forests style: the tree as a rice paddy (stalk per family, head branch per mechanism, grain per strategy, bright grain at a pathway), risk clouds with a storm test per mechanism, plan-to-plan growth, sector plans as optional coloured leaves, and views for the profile, strategies, risks, over time, sector plans, crosswalks, the bottom-up test and the method. It is a single file built from `page_template.html`.

## Status

Structure and crosswalks are complete and validated by `build.py`. Not done yet: adding strategies to the tree (step M proposals), the E framing field, and the workflow prompt that places on v2.
