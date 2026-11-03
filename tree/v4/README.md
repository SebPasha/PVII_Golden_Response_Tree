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

Second pass (3 November, later the same day): every source was read (abstract or full text) against its lever; the finding was rewritten from the text read, with `evidence_basis` saying what in the text supports it; `evidence_design` records the study design, `evidence_fit` how directly the source evaluates the lever's action (direct, partial, loose), `evidence_checked` how much was read. Sources that could not be read were dropped, and 48 were replaced with a better review or evaluation. Strength was re-graded on the sources read only, so one or two agreeing studies count as thin: 24 strong, 97 mixed, 106 thin, 2 none found (LV-096 long-term fiscal planning, LV-109 tourism market diversification). Entries the scan itself flags as weak for an economists' review, by fit or design: LV-005, 008, 016, 017, 021, 030, 041, 043, 047, 055, 058, 067, 080, 091, 095, 108, 113, 119, 123, 132, 137, 152, 153, 164, 171, 172, 173, 177, 183, 186, 190, 200, 209, 218, 219.

The scan was done by model workers with web search and page reads; it is a checked first pass for the economists' review, not a settled evidence base. Source: `inputs/lever_evidence.json`; the build reads it when present.

Framework anchoring (`inputs/framework_refs.json`, columns `framework_source`, `framework_where`, `framework_says`, `framework_refs`; read 3 November 2026 from the full texts of 19 documents): the framework document behind each group, read against each lever: what it says about the action, on which printed page, and the references it cites for it, checked against the document's own reference list (a reference the reader could not find there was left out). Documents by subpillar: TSE Inclusion Matters (2013); CAP Human Development Reports 1990 and 1994; FUT Changing Wealth of Nations 2021, IPCC AR6 WGII and WGIII (Summary for Policymakers and Technical Summary) and the ILO just-transition guidelines (2015); EXP the Growth Report (2008) and WDR 2020; DOM WDR 2009; GTI WDR 2008, Finance for All? (2008) and Inclusive Growth Analytics (2009); REF WDR 2017, WDR 2004, Fox 2015 and DLP 2018. Result: 189 of 229 levers anchored to a document, 151 of them discussed in it and 38 not (then `framework_says` says what the document leaves out); 241 references in all. The 40 governance levers (anticipation, adaptation, agility) carry "No framework document published yet": the Future-Ready Governance Index has no published document, it is in pilot. Not obtained: the Inclusive Wealth Report 2018 (download blocked), so the FUT levers lean on Changing Wealth of Nations and the IPCC summaries. Caveats to keep in view: the HDRs cite no sources in their text (each chapter has a bibliographic note), so CAP references are chapter sources matched by title, a judgement call rather than citations from the passage; the IPCC summaries have no reference list, so the 14 FUT references all come from Changing Wealth of Nations; the Fox 2015 text is the 2014 GPSA working-paper version, so its page numbers differ from the World Development version; and 33 "discussed" anchors are weak (TSE LV-005, 007, 013, 017, 019; CAP LV-022, 026, 040, 049, 050; FUT LV-064, 078, 079, 081, 082, 085, 094, 097; EXP LV-104, 111, 123; DOM LV-127, 131, 132, 133; GTI LV-141, 162, 164; REF LV-216, 220, 224, 227, 229), each saying in `framework_says` what the document leaves out. Reviewers may prefer to count those as not discussed.

Thesis literature (`inputs/thesis_refs.json`, columns `thesis_n`, `thesis_citations`, `thesis_refs`): papers from the economics literature library behind the thesis (207 catalogued, 160 held; firm dynamics, misallocation, entrepreneurship, mobility, microenterprise; identification tagged RCT, natural experiment, structural and so on) whose intervention or setting matches a lever, with the identification design and a one-line finding. The match found 24 levers with at least one paper (39 references: 26 RCT, 10 quasi-experimental, 3 structural); the library is about firms and workers, so most of the tree has no match, and that is expected. Loose fits kept and flagged: LV-011, LV-024, LV-041, LV-054, LV-164, LV-227. The file is written on the laptop and is being transferred; the build runs without it.

## Rebuild

```bash
cd tree/v4 && python3 build.py
```

Reads `../v3/tree_v3.json` (which carries the bridge face) and writes the four CSVs and the JSON. The build fails if a pathway is left without a lever or a lever without a family.

## Status

The workflow maps onto v4 by default (`workflow/prompts/M_map_v4.txt`; `workflow/pvii/tree.py` reads the lever level and the pathways as literature). Output rows carry `lever_id`, `lever`, `pathway_id` (optional), `reason` and `depth_basis`. Not done: the economists' network review of the levers and their tests; the Thai re-run on v4; objectives under the levers, which step M proposes.
