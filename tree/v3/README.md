# Mother tree v3 (draft, 29 October 2026; deep check of the pathways 30 October)

The reviewer's framework laid over tree v2's pathways. Three placement levels under the RHDR pillars and subpillars:

- `groups_v3.csv`: 33 groups (L1), the reviewer's, each citing a published framework (Inclusion Matters, the HDI, inclusive wealth, the Growth Report, WDR 2009, WDR 2008, the Future-Ready Governance Index for the three PV3 subpillars, WDR 2017).
- `families_v3.csv`: 60 families (L2), the required mapping level. Each has the reviewer's definition and plan words rolled up from the v2 mechanisms whose pathways landed in it.
- `pathways_v3.csv`: 264 pathways (L3): v2's 259 with their ids kept (3 still merged into a sibling: L3-031, L3-139, L3-187, each lending its cues to the sibling; L3-259, L3-047, L3-082 and L3-099 unmerged, the reason in `distinction`) plus 5 the reviewer added (L3-260 to L3-264: social insurance for informal workers, household digital access, just transition, data sharing across agencies, crisis communication). The new ones carry text cues and risk tags assigned at this build, marked not source-verified. The `revised` column says what the deep check of 30 October changed on a row: cues, evidence, moved, unmerged.

Depth rule: every strategy is placed on a family. A pathway only when the strategy's wording names that causal channel and no sibling. A group alone is a weak placement and is counted in `run.json` as `group_only`. Standing functions of the state go to the subpillar's General branch (H-SPE, H-SEC, H-SGO); goals with no policy area to H-GOAL.

`tree_v3.json` holds everything in one file, plus `v2_mechanism_default` and `v2_family_default` (the v3 family or group each v2 node mostly maps to) for reading v2 outputs on v3.

## What was decided against the reviewer's draft

The governance subpillars are taken whole. Elsewhere, from the comparison doc of 29 October (Reviewer framework vs tree v2):

- Three thin families merged into a sibling: Digital access and use into Skills for work; Displaced and uprooted populations into Exclusion from social and political spaces; Public balance sheet with Subsoil wealth and resource rents (now Public wealth: resource rents and the balance sheet).
- Living environment and basic services sits under Decent standard of living, not Long and healthy life.
- Property rights and market rules get a group of their own under Growth through Inclusion (Market rules and property rights), not Domestic Integration.
- Lagging places and displaced workers is split: Lagging regions and place-based development under Domestic Integration (Linkages, clusters and cities); Displaced workers and local adjustment stays under Growth through Inclusion.

## The deep check of 30 October 2026

All 264 pathways were read against their family and group definitions, and every text cue was run against the 562 strategies of Thailand's 13th Plan. What changed, each a constant in `build.py`:

- Displaced and uprooted populations is a family again (F-05): its three pathways were sitting in a family whose definition says nothing about displacement.
- Property rights and market rules is split: Competition, contracts and state ownership (F-37) and Land rights and land markets (F-38), two different purposes under one group.
- Five pathways moved to the family their own distinction names or whose definition covers them: university skills to Knowledge (F-11), rural non-farm diversification to Lagging regions (F-29), misallocation across firms to Competition (F-37), intergroup contact to Social cohesion (F-60), capability traps next to problem-driven iteration (F-44).
- Three v2 merges undone (L3-047 maternal and newborn, L3-082 cleaner production, L3-099 intergenerational fiscal burden); the three that remain lend their cues to the sibling, so their wording still reaches a pathway.
- 90 text cues rewritten and the two blank ones filled. The old cues matched fragments: "mental" matched "environmental", "mechani[sz]" matched "mechanism", "secur" every "security", "competit" (electoral) "competitiveness". On the Thai strategies the number of pathways firing on more than 3% of strategies fell from 30 to 9, and the mean number of pathways whose cue a strategy hits from 3.0 to 1.4.
- Seven citations swapped where the cited paper contradicted or missed the pathway (L3-061, L3-089, L3-122, L3-198, L3-199, L3-207, L3-261). The other 257 remain cited but not independently verified.
- Three stale definitions fixed (Decent standard of living, Long and healthy life, Linkages, clusters and cities) and examples added for the families the build had left without any.
- In the workflow, the cue gate now reads the strategy's own words only; it used to include the model's `depth_words`, so the model could pass any cue with its own wording.

Still open, for a decision: ten near-duplicate pairs that wording alone may not separate (for example credit for small firms L3-165 and credit for small borrowers L3-173; density L3-142 and agglomeration L3-152); whether migration as adaptation (L3-019) belongs with displaced populations or with climate risk; the "no sibling" half of the depth rule, which the code does not test; and the risk tags, which still come from the v1 review notes.

Every amendment is a constant at the top of `build.py`.

## Rebuild

```bash
cd tree/v3 && python3 build.py
```

Reads `inputs/reviewer_framework.json` (the reviewer's PVII_Mother_Tree.html of 27 October parsed into an outline; the comments document is beside it) and `../v2/tree_v2.json`. The build fails if a v2 pathway is left unplaced, a family has no plan words or SDG targets, or a plan-words pattern does not compile.

## Status

Structure, plan words and crosswalks built. The workflow maps onto v3 by default (`workflow/prompts/M_map_v3.txt`). Not done: objectives (L4) under the families, which step M proposes; a Thailand page on v3; re-running M for the Thai plans mapped on v1; an independent check of the 257 citations.
