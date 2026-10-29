# Mother tree v3 (draft, 29 October 2026)

The reviewer's framework laid over tree v2's pathways. Three placement levels under the RHDR pillars and subpillars:

- `groups_v3.csv`: 33 groups (L1), the reviewer's, each citing a published framework (Inclusion Matters, the HDI, inclusive wealth, the Growth Report, WDR 2009, WDR 2008, the Future-Ready Governance Index for the three PV3 subpillars, WDR 2017).
- `families_v3.csv`: 58 families (L2), the required mapping level. Each has the reviewer's definition and plan words rolled up from the v2 mechanisms whose pathways landed in it.
- `pathways_v3.csv`: 264 pathways (L3): v2's 259 with their ids kept (6 still merged into a sibling; L3-259 unmerged because the reviewer places it elsewhere) plus 5 the reviewer added (L3-260 to L3-264: social insurance for informal workers, household digital access, just transition, data sharing across agencies, crisis communication). The new ones carry text cues and risk tags assigned at this build, marked not source-verified.

Depth rule: every strategy is placed on a family. A pathway only when the strategy's wording names that causal channel and no sibling. A group alone is a weak placement and is counted in `run.json` as `group_only`. Standing functions of the state go to the subpillar's General branch (H-SPE, H-SEC, H-SGO); goals with no policy area to H-GOAL.

`tree_v3.json` holds everything in one file, plus `v2_mechanism_default` and `v2_family_default` (the v3 family or group each v2 node mostly maps to) for reading v2 outputs on v3.

## What was decided against the reviewer's draft

The governance subpillars are taken whole. Elsewhere, from the comparison doc of 29 October (Reviewer framework vs tree v2):

- Three thin families merged into a sibling: Digital access and use into Skills for work; Displaced and uprooted populations into Exclusion from social and political spaces; Public balance sheet with Subsoil wealth and resource rents (now Public wealth: resource rents and the balance sheet).
- Living environment and basic services sits under Decent standard of living, not Long and healthy life.
- Property rights and market rules get a group of their own under Growth through Inclusion (Market rules and property rights), not Domestic Integration.
- Lagging places and displaced workers is split: Lagging regions and place-based development under Domestic Integration (Linkages, clusters and cities); Displaced workers and local adjustment stays under Growth through Inclusion.

Every amendment is a constant at the top of `build.py`.

## Rebuild

```bash
cd tree/v3 && python3 build.py
```

Reads `inputs/reviewer_framework.json` (the reviewer's PVII_Mother_Tree.html of 27 October parsed into an outline; the comments document is beside it) and `../v2/tree_v2.json`. The build fails if a v2 pathway is left unplaced, a family has no plan words or SDG targets, or a plan-words pattern does not compile.

## Status

Structure, plan words and crosswalks built. The workflow maps onto v3 by default (`workflow/prompts/M_map_v3.txt`). Not done: objectives (L4) under the families, which step M proposes; a Thailand page on v3; re-running M for the Thai plans mapped on v1.
