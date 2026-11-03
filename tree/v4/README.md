# Mother tree v4 (draft, 3 November 2026): levers in place of pathways

v3's bottom level was the literature's causal pathways, and plans do not speak that language: the Thai v3 run put 13% of strategies on a pathway. v4 keeps v3's groups and families and puts a lever under each family: what a government does that moves the family's purpose, in a plan's own grain. The pathways stay in the tree under the lever they belong to, as the evidence behind it, and as an optional depth.

Levels under the RHDR pillars and subpillars:

- `groups_v4.csv`: 33 groups (L1), unchanged from v3.
- `families_v4.csv`: 60 families (L2), unchanged from v3, with the ids of their levers.
- `levers_v4.csv`: 229 levers (L3), the placement level. Each carries its `joins_when` and `joins_not` tests (prose, judged by meaning), its pathways, the union of their text cues and risk tags, the Thai entry points of the bridge face, and the literature of its pathways in `evidence`. 198 levers rest on one pathway, 28 on two, 3 on three.
- `pathways_v4.csv`: 263 pathways (L4), v3's rows (266 less the 3 still merged into a sibling) with the `lever_id` they sit under. Columns as v3 plus the bridge face: lever, joins_when, joins_not.

Depth rule: every strategy that names an action is placed on a lever, judged by meaning with the lever's tests. A summary line with no action stays on its family. Where no lever of the family describes the action, the strategy stays on the family and `reason` says what lever is missing: a lever is not forced where none exists. A pathway is recorded only when the lever has one pathway or the strategy's wording names the channel; the text cues are an advisory flag, never a veto. A group alone is a weak placement and is counted.

`tree_v4.json` holds everything in one file; `meta.merged_pathways` lists the 3 merged pathways.

## How the levers were made

Each v3 pathway got a bridge face on 3 November (`../v3/bridge.py`): a lever phrase, a joins-when test, a joins-not test. v4 turns those into nodes. `LEVER_MERGES` in `build.py` lists the 31 places where several sibling pathways are one action for a government (for example contributory insurance, income replacement in shocks and unemployment insurance, which a plan writes as one social-insurance line); the lever then carries all its pathways and a joins-when test written for the merged lever. Everything else is one lever per pathway. Lever ids are LV-001 to LV-229 in family order; the short lever names are cut from the bridge phrase and are for the reviewers to rename.

## Intervention-level evidence on the levers (scan of 3 November 2026)

The pathways carry the mechanism literature (why a lever works). Each lever also carries one or two sources on the intervention itself: a systematic review or meta-analysis where one exists (3ie, Campbell, Cochrane, J-PAL, World Bank, IEG, OECD, ILO, IFPRI), otherwise a flagship evaluation or landmark empirical paper, with evidence from developing and middle-income countries preferred. Columns on `levers_v4.csv` and in `tree_v4.json`:

- `intervention_evidence`: "Author Year, Title, Outlet", one or two sources.
- `evidence_finding`: one sentence on what the evidence finds, with the main condition under which the lever works or fails.
- `evidence_strength`: strong (consistent evidence from reviews or several rigorous studies), mixed (effects depend on design or context), thin (few rigorous studies), none found.
- `evidence_verified`: yes when the source was confirmed online by title and author at the scan; `evidence_url` is where. A source that could not be confirmed is not kept: the lever reads "No suitable intervention-level source confirmed".

The scan was drafted and checked with web search by model workers and is a first pass for the economists' review, not a settled evidence base: findings are paraphrased from the sources, not quoted, and the strength rating is a judgement. Source: `inputs/lever_evidence.json`; the build reads it when present.

## Rebuild

```bash
cd tree/v4 && python3 build.py
```

Reads `../v3/tree_v3.json` (which carries the bridge face) and writes the four CSVs and the JSON. The build fails if a pathway is left without a lever or a lever without a family.

## Status

The workflow maps onto v4 by default (`workflow/prompts/M_map_v4.txt`; `workflow/pvii/tree.py` reads the lever level and the pathways as literature). Output rows carry `lever_id`, `lever`, `pathway_id` (optional), `reason` and `depth_basis`. Not done: the economists' network review of the levers and their tests; the Thai re-run on v4; objectives under the levers, which step M proposes.
