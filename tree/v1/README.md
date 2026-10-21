# Mother tree v1

The PV II strategy tree rebuilt on six levels, following the Golden Tree Layering Plan:

RHDR pillar → RHDR subpillar → mechanism family (L2) → mechanism (L3) → objective (L4) → strategy (L5: objective × target × instrument).

Three principles run through every file:

- **The literature decides which mechanisms exist.** Families and mechanisms are written from the literature review (lit_families.py, lit_mechanisms.py, notes/). They are not reverse-engineered from the objectives. 38 mechanisms the literature names hold no strategy; they stay in the tree as empty nodes.
- **The wording of each plan decides how precisely a commitment is classified.** An objective sits at a mechanism (L3) only when its whole wording names that channel and no sibling. Otherwise it sits on the family (L2), with the candidate mechanisms listed. A strategy under an L2 objective moves to L3 only when its own text names exactly one candidate (Rule 7: no invented specificity).
- **Reporting uses the deepest level the compared observations share.** The "Compare at" tab in mother_tree.html picks L3 or L2 per family for the countries selected, and shows each country's share classified finer.

Status: draft v1 for sign-off after the 21 October presentation. The plan's pilot gate (review notes checked by an economist who did not draft them) has not been run.

## Run

From this folder: `python3 build.py && python3 notes.py && python3 viewer.py`. The build reads ../objectives.csv, ../strategy_decomposition.csv and ../../../data/union/strategies.csv, and writes everything else here. It fails if any objective is unplaced, a node is unknown, a mechanism fails an admission test, or an L3 placement challenged by the sibling test is not adjudicated.

## Inputs written by hand

| File | What it is |
|---|---|
| lit_families.py | 13 subpillars (10 named, 3 Standard holding branches), 57 families with definition, core variables, inclusion and exclusion rules, literature, primary subpillar with reason, secondary subpillars with reasons, risks |
| lit_mechanisms.py | 259 mechanisms with causal input, transmission, outcome, conditions, distinction from siblings, evidence, risks and justification, and the text cues used for strategy-level deepening |
| placement.txt | Canonical node for each of the 456 source objectives, with notes where the plan's tables or adjudication decided |
| adjudicated_keep.json, ADJUDICATION.md | Second-coder and sibling-test decisions, as worked examples |

## Outputs

| File | What it is |
|---|---|
| families.csv, mechanisms.csv | L2 and L3 with every mandatory field, plus counts and classification suitability |
| objectives_v1.csv | 446 L4 objectives after the two meaningful merges: node, depth, depth reason, candidate mechanisms, basis, confidence, sibling check, merge history, source ids, sector tags |
| strategy_nodes.csv | Every strategy's node and level, how it got that depth, and the wording that justified it |
| causal_network.csv | Many-to-many causal links, kept apart from the classification and never summed |
| country_node_matrix.csv | Country × family counts at L2 and L3: the base for compare-at |
| admission_tests.csv | Five-question test and classification suitability for each mechanism |
| empty_nodes.csv | Mechanisms the literature names that no plan addresses |
| notes/ | The literature review, one note per risk |
| qa/ | The blind second-coder sample, its codes and the first-pass key |
| VALIDATION.md | Coverage both ways, depth shares, goal triage, Standard coverage, agreement |
| mother_tree.html | Viewer: tree with uneven depth, compare-at, mechanisms, objectives, validation |
| tree_v1.json | Everything above in one file |

## Decisions applied

- Standard People, Standard Economy and Standard Governance are holding branches with no literature levels. They are visible in the tree and dropped from reporting.
- Two literature levels.
- Goal-shaped objectives are triaged one by one. A strategy whose text names a channel is re-homed; the rest are held outside the tree.
- Two merges where nothing economic is lost: sector governance variants become "Strengthen sector governance and regulation", and digitisation variants become "Digitise public services". Original ids are kept.
- Option C placement: by convention, unless the plan's wording names the channel.
- Maintenance sits on the same node as expansion, flagged BAU.
- Where the plan's illustrative tables and an objective's definition disagree, the definition decides. Each case is noted in placement.txt and ADJUDICATION.md.

## Source verification (added 20 October, evening)

- **ids.json** freezes node ids, so review registers keep pointing at the same mechanism. New nodes get the next id; a removed node's id is retired.
- **verification/** holds the external reviewers' registers as received. The build reads the accepted condition decisions from it and marks those mechanisms source-verified. All others are "cited, not yet independently verified".
- **conditional_risk_links.csv** records reviewed risk links. A link accepted as conditional applies to a strategy only when the strategy's wording meets its scope (the trigger column). It never enters the mechanism × risk matrix. Rejected links are kept with the reason.
- **baseline_mechanisms.csv** lists mechanisms that carry no risk tag by design: valid development mechanisms not derived from any of the eleven risks.
- The admission test is reported as structural. It checks that each field is present, not that each paper supports the claim.
