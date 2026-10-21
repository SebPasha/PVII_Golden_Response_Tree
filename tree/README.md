# The mother tree

`v1/` is the mother tree v1 release (draft for sign-off, built 20 October 2026), moved here from PV2 `support/golden_tree/tree_v1/` unchanged. Its own [README](v1/README.md) and [HANDOVER](v1/HANDOVER.md) explain the six levels, the depth rule and the open items.

The workflow reads exactly three files and writes nothing here:

- `v1/tree_v1.json`: families, mechanisms (with their `text_cues`), objectives and holding branches
- `inputs/targets.csv`: the 197 target-group labels
- `inputs/instruments.csv`: the 19 instrument labels

Step M's proposals (`data/plans/<plan_id>/proposals.csv`) are the input to the tree's next release. They never change v1.

## Rebuild

```bash
cd tree/v1 && python3 build.py && python3 notes.py && python3 viewer.py
```

`build.py` now reads its inputs from `inputs/`: `objectives.csv`, `strategy_decomposition.csv`, and `union_strategies.csv`, which is a copy of PV2 `data/union/strategies.csv` as it stood when v1 was built. A rebuild from the moved files reproduces `tree_v1.json` exactly. This was checked on 21 October 2026.

`inputs/buckets.py` is the script that produced the objective, target and instrument label lists from the PV2 strategy names. It is kept for the record. It reads the `names/` working files in PV2 `support/golden_tree/`, which were not copied here.
