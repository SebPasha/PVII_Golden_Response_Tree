# PV II golden strategy tree: project handover

Context for new threads in this project. Current to 21 October 2026.

## What this is

PV II (Project Vision II, UNDP RBAP) maps national budget programmes to national development plan strategies across 45 countries. The golden strategy tree, now called the **mother tree**, is the central reference structure: every strategy in every plan gets one canonical place in it, so countries can be compared and budgets joined at whatever level they report.

## The tree: six levels

RHDR pillar → RHDR subpillar → mechanism family (L2) → mechanism (L3) → objective (L4) → strategy (L5: objective × target × instrument).

- **L0–L1** come from the amended RHDR framework (rhdr_2026_10). It has 3 pillars and 10 named subpillars, plus 3 Standard holding branches (Standard People, Standard Economy, Standard Governance). The Standard branches have no literature levels; they are visible in the tree and dropped from reporting.
- **L2–L3** come from the literature review. The review is organised by the 11 PV II risks, but risks are tags, not levels. L2 groups explanations; L3 is a causal relationship (input → transmission → outcome, with conditions). Both are named as noun phrases.
- **L4–L5** come from the plans: objectives (verb-led), plus target and instrument where the plan states them.

## Governing principles (agreed 20 October)

- The literature determines which mechanisms exist.
- The evidence in plans determines how precisely a commitment can be classified. An objective sits at L3 only when its whole wording names that channel and no sibling; otherwise it sits at L2, with candidate mechanisms listed. No invented specificity.
- Reporting uses the deepest level the compared observations share, without erasing the finer information.

Further rules:
- One canonical home per objective.
- One primary RHDR subpillar per mechanism, with a reason, plus justified secondaries.
- The classification tree and the causal network are kept separate.
- Consolidate only where nothing economic is lost.
- Empty nodes stay; they are the gap analysis.
- No numeric gates on node counts.
- Pilot before scaling.
- Goal-shaped objectives are triaged one by one.
- Maintenance sits on the same node as expansion, flagged BAU.

## Where the work lives

`PV2/support/golden_tree/tree_v1/` on Sebastian's machine (Environment_UNDP). Run `python3 build.py && python3 notes.py && python3 viewer.py` to rebuild from `data/union/strategies.csv` and the golden-tree bucket files.

| File | What it is |
|---|---|
| mother_tree.html | The viewer (see below) |
| lit_families.py, lit_mechanisms.py | The literature layer, written by hand |
| placement.txt | Canonical node for each of the 456 source objectives |
| families.csv, mechanisms.csv, objectives_v1.csv, strategy_nodes.csv | Outputs with every mandatory field |
| causal_network.csv | Many-to-many causal links, never summed |
| notes/ | Literature review notes, one per risk |
| ADJUDICATION.md, qa/ | Second-coder and sibling-test decisions |
| verification/, conditional_risk_links.csv, baseline_mechanisms.csv | External source verification and risk-link decisions |
| ids.json | Frozen node ids, so review registers stay valid |
| VALIDATION.md | Coverage, depth, triage and agreement figures |

Related artifacts:
- Golden Tree Layering Plan doc: https://claude.ai/code/artifact/e726e177-20b7-46b9-8739-17e77eecf5e5. It includes a "What the v1 build found" section.
- Workflow redesign page: https://claude.ai/artifact/68Td9yeaHGUY7ybStUVWhX

Earlier outputs:
- An 11-slide deck in My Source Files
- Posters: Plate I The Golden Tree, Plate II Mirror Trees
- The bucket-filling prompt and the first golden_tree.html viewer, in support/golden_tree/

## v1 numbers (draft for sign-off)

| Measure | v1 |
|---|---|
| Mechanism families (L2) | 57 |
| Mechanisms (L3) | 259, of which 38 are empty |
| Objectives after two merges | 446 (from 456) |
| Objectives at L3 / L2 | 42% / 50%; 25 Standard, 10 goals held |
| Strategies at L3 / L2 | 53% / 41%; 4% Standard, 2% goals held |
| Strategies deepened by their own wording | 1,277 |
| Goal strategies re-homed | 50 of 208 |
| Blind second coder, 10% sample | same family 87%, same node 76% |
| Agreement with the earlier RHDR coding | 39% (diagnostic, not a target) |

Lesson from the second coder: the first pass over-reached to L3. Depth is now set by the whole commitment, a sibling test runs on every L3 placement, and the build fails if a challenged placement is not adjudicated.

## Source verification (external reviewer, 20 October)

The reviewer's verdict: the tree is structurally mature, but the scientific evidence is unevenly documented. Citations present ≠ claims verified. The admission test is now reported as structural only.

Applied so far:
- Two conditions verified and narrowed: L3-062 housing and health; L3-084 toxic exposure, now lead-specific.
- The mis-cited Velders et al. 2007 removed.
- Fourteen proposed risk links reviewed: 3 rejected and 11 kept as conditional. Conditional links apply to a strategy only when its wording meets the stated scope, and never enter the mechanism × risk matrix.
- Fourteen mechanisms marked as baseline: no risk tag, by design.

Evidence status: 2 mechanisms source-verified; 257 cited, not yet verified. 231 risk tags are not yet source-verified.

## Viewer (mother_tree.html)

- **Tree:** pan-and-zoom canvas. Columns are sized to their widest labels; L3 links are solid and L2 placements dashed gold. Column headers move with the view; clicking a node opens it and brings the branch into view. Filters by country and risk, plus search.
- **Strategy table:** opens large from any node. Click an objective to open it directly; families, mechanisms and subpillars have an "Open table" button. Columns: country, plan period, strategy, objective, placed at (L3 or L2), how it got there, BAU, target × instrument. It sorts on any column and downloads as CSV.
- **Other tabs:** Compare at (deepest common level per family, for the countries selected), Mechanisms, Objectives, Validation.

## Open items

1. **Plan period column is empty.** The union strategy table has no year. A source is needed: a plan-period file in PV2, or the budget year. The viewer reads an optional `plan_periods.csv` (country, plan, start_year, end_year).
2. **From the reviewer's queue:** audit the 259 mechanisms for causal distinctness, especially where a node may be an input, instrument or sector rather than a channel. Examples:
   - Health: workforce, medicines and provider quality may be inputs to one effective-coverage mechanism.
   - Education: access, teacher effort and learning quality play different roles in a production function.
   - Governance: consider the World Bank's 2017 framework of commitment, coordination and cooperation.

   The 160-flag review queue and the Scientific Validation Report are needed for this; Sebastian has them from the reviewer chat.
3. Investigate the 61% disagreement with the earlier RHDR coding, using the official subpillar definitions and plan quotations.
4. Source-verify the 231 existing risk tags.
5. **Pilot gate:** review notes checked by an economist who did not draft them, then sign-off by Sebastian. Open question: whether the regional economist network reviews the pooled list.
6. Move the tree into the pipeline: notes to pv2/tree/notes/, then L5 mapping and budget joins.

## Working preferences

- Brief, direct working documents.
- The PV II data and workflow folders are not edited by hand; outputs go to support/golden_tree/.
- Sebastian signs off after presenting and gathering feedback.
