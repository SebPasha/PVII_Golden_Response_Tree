"""Mother tree v3: the reviewer's framework (29 October 2026) laid over tree v2's pathways.

Reads inputs/reviewer_framework.json (the reviewer's PVII_Mother_Tree.html parsed into an
outline: subpillar > group > family > mechanism) and ../v2/tree_v2.json, and writes
groups_v3.csv, families_v3.csv, pathways_v3.csv, sdg_crosswalk.csv, risk_matrix.csv and
tree_v3.json.

Three placement levels under the RHDR subpillars:
  group (L1, 33): the reviewer's groups, each citing a published framework
  family (L2, 60): the reviewer's families, the required mapping level, with plan words
  pathway (L3, 264): the reviewer's mechanisms = v2's 259 pathways (ids kept) plus 5 new ones

The reviewer's structure is taken whole for the governance subpillars (Future-Ready
Governance Index and WDR 2017). Elsewhere the amendments below apply; each is a decision
recorded in the comparison doc (Reviewer framework vs tree v2, 29 October 2026).

The deep check of 30 October 2026 (all 264 pathways read against their families; cues tested on
the Thai strategies) added the constants from MOVE_PATHWAY down: pathway moves, three unmerges,
revised text cues, seven citation swaps and the distinctions of the five new pathways.

Run: python3 build.py
"""
import collections
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(os.path.dirname(HERE), "v2", "tree_v2.json")
REVIEWER = os.path.join(HERE, "inputs", "reviewer_framework.json")

SUBPILLAR_CODE = {"Tackling Structural Exclusion": "TSE", "Enhancing Capabilities": "CAP",
                  "Future Generations": "FUT", "Export-led": "EXP", "Domestic Integration": "DOM",
                  "Growth through Inclusion": "GTI", "Anticipation and Strategic Foresight": "ANT",
                  "Adaptability and Course Correction": "ADA", "Agility and Delivery Capability": "AGI",
                  "Reform Leadership, Coalitions and Civic Engagement": "REF"}
GENERAL = {"General People": "H-SPE", "General Economy": "H-SEC", "General Governance": "H-SGO"}

# ---------------------------------------------------------------- amendments (the decisions)
# A family merged into a sibling: the thinnest People and Economy families (one or two pathways).
MERGE = {"Digital access and use": "Skills for work",
         "Public balance sheet": "Subsoil wealth and resource rents"}
# (Displaced and uprooted populations was merged into Exclusion from social and political spaces
#  at the first build; the deep check restored it: that family's definition says nothing about
#  displacement, and three pathways is no thinner than other families kept.)
RENAME = {"Subsoil wealth and resource rents": "Public wealth: resource rents and the balance sheet",
          "Lagging places and displaced workers": "Displaced workers and local adjustment",
          "Property rights and market rules": "Competition, contracts and state ownership",
          "Knowledge: schooling": "Knowledge: schooling and higher education"}
REDEFINE = {"Public wealth: resource rents and the balance sheet":
            "Exhaustible resource rents and the public balance sheet: whether rents are reinvested and whether debt and fiscal policy shift burdens onto future taxpayers.",
            "Displaced workers and local adjustment":
            "Concentrated shocks to local labour markets from trade and technology, and how displaced workers and places adjust.",
            "Skills for work":
            "Job-relevant skills formed after or alongside schooling, the signals that make them pay, and households' access to and use of digital connectivity.",
            "Competition, contracts and state ownership":
            "Competition, contract enforcement and state ownership rules that decide who captures returns, and the misallocation that follows when they favour some firms."}
# Examples for families the build created or emptied.
EXAMPLES = {"Lagging regions and place-based development":
            "Promote local and regional economic development · Reduce regional disparities · Promote rural development",
            "Displaced workers and local adjustment":
            "Support workers and places hit by trade and technology shocks · Retrain retrenched workers",
            "Land rights and land markets":
            "Secure land and property rights · Reform land administration · Implement agrarian reform"}
# Group definitions that the family moves left stale.
GROUP_REDEFINE = {"Decent standard of living":
                  "Income security, food security, personal safety, and first access to basic services and adequate housing.",
                  "Long and healthy life": "Health services and the prevention of disease and injury.",
                  "Linkages, clusters and cities": "Production linkages, clusters, urban systems and lagging regions."}
# A family moved to another group (and subpillar where the group sits elsewhere).
MOVE_FAMILY = {"Living environment and basic services": "Decent standard of living",
               "Property rights and market rules": "Market rules and property rights"}
# Groups added, with the subpillar they sit under and their basis.
NEW_GROUPS = {"Market rules and property rights": ("Growth through Inclusion",
              "Inclusive Growth Analytics (Ianchovichina and Lundstrom 2009); WDR 2017 on contracts and competition",
              "Security of property, contract enforcement, competition and state ownership rules that decide who captures returns.")}
# A family split: these pathways leave their family for a new family under the group named.
SPLIT = {"Lagging regions and place-based development": {
    "group": "Linkages, clusters and cities", "from": "Lagging places and displaced workers",
    "definition": "Persistent spatial gaps between regions, and the place-based policies that try to close them.",
    "pathways": ["Place-based policy and spatial equilibrium", "Geographic poverty traps"]},
    "Land rights and land markets": {
    "group": "Market rules and property rights", "from": "Property rights and market rules",
    "definition": "Security, documentation and transferability of rights to land, and its redistribution.",
    "pathways": ["Tenure security and investment", "Titling, collateral and labour supply",
                 "Land-market transaction costs and allocation", "Land redistribution and agrarian reform"]}}
# A pathway moved to another family (reviewer's family names, before RENAME). Each is a
# pathway whose own distinction names a sibling that sat elsewhere, or whose family definition
# did not cover it.
MOVE_PATHWAY = {
    "University skills and local innovation": "Knowledge: schooling",            # the family's definition says "school and university"
    "Rural non-farm diversification": "Lagging regions and place-based development",  # not a trade or technology shock
    "Misallocation across firms": "Property rights and market rules",            # size-dependent rules, not small-firm capability
    "Intergroup contact and prejudice reduction": "Social cohesion and trust",   # its distinction is "vs nation-building", which sits there
    "Capability traps and isomorphic mimicry": "Monitoring and corrective feedback",  # its distinction is "vs PDIA", which sits there
}
# v2 merges undone at the deep check: each merged pathway is a channel plans name on its own.
UNMERGE = {"L3-047": "maternal and newborn programmes are named on their own in every health plan",
           "L3-082": "cleaner production and sustainable consumption are a family example and a distinct technique channel",
           "L3-099": "the one pathway that names what the public balance sheet does to future generations"}
# Citations the deep check found to contradict or miss their pathway.
EVIDENCE = {
    "L3-089": "Emerick, de Janvry, Sadoulet and Dar 2016 (flood-tolerant rice); Burke and Emerick 2016 (adaptation offsets little of the damage in US agriculture)",
    "L3-061": "Pattanayak et al. 2019 (LPG and improved stoves in India); Hanna, Duflo and Greenstone 2016 (null effect of improved stoves without sustained use)",
    "L3-199": "Deaton 1999; Cavalcanti, Mohaddes and Raissi 2015",
    "L3-207": "Oppenheim et al. 2019; Heymann and Rodier 2004",
    "L3-198": "Calvo 1998; Obstfeld, Shambaugh and Taylor 2010",
    "L3-122": "Javorcik 2004; Alfaro-Urena, Manelici and Vasquez 2022",
    "L3-261": "Bahia et al. 2020 (mobile broadband and household welfare in Nigeria); Aker and Mbiti 2010",
}
# Distinctions for the pathways the reviewer added.
DISTINCTION = {
    "L3-260": "vs informality and formalisation costs (L3-180): the insurance and pension side, not the cost of being formal",
    "L3-261": "vs broadband and firm entry (L3-140): households, not firms; vs digital skill complementarity (L3-035): access, not skills",
    "L3-262": "vs adjustment to trade shocks (L3-183): decarbonisation, not imports",
    "L3-263": "vs statistical capacity (L3-210): sharing across agencies, not measurement; vs data protection (L3-221): use, not rights",
    "L3-264": "vs early-warning lead time (L3-206): the public's understanding and behaviour, not the forecast",
}
# Text cues revised at the deep check of 30 October 2026, keyed by pathway id. Each replaces a
# cue that matched the wrong words on the Thai strategies ("mental" matched "environmental",
# "mechani[sz]" matched "mechanism", "secur" every "security") or was blank. The two blank cues
# were L3-017 and L3-137. L3-212 gains the plan words of its family's own example.
CUES = {
 # --- governance
 "L3-017": r"affective polari|partisan (animosity|hostil|divide|polari)|political (division|divide|polari)|cross-?party|bipartisan|inter-?party dialogue",
 "L3-137": r"core-?periphery|backwash|spread effect|concentrat\w*.{0,40}(core|capital|metropol|primate|bangkok|dhaka|sao paulo)|polari[sz]ation of (growth|development)|balanced (regional|spatial) (growth|development)",
 "L3-021": r"unemployment (insurance|benefit)|social insurance|income support|consumption smooth|cash assistance",
 "L3-024": r"shock-?responsive|adaptive social protection|scal(e|ing)[- ]up.{0,40}(transfer|benefit|social protection|cash|assistance)|horizontal expansion|vertical expansion|trigger.{0,30}(payout|transfer|benefit|assistance)",
 "L3-027": r"targeting|social registry|unified registry|registr(y|ies) of (the )?(poor|beneficiar|household)|beneficiary (registry|database|list)|proxy means|\bdtks|\bnser|single registry",
 "L3-022": r"distress sale|coping|asset (loss|protect)|(withdraw|pull).{0,20}(children|child).{0,20}school|school withdrawal",
 "L3-043": r"universal health|\buhc|health coverage|service coverage|access to health|primary (health )?care|community health",
 "L3-046": r"medicine|pharmac|essential medicine|drug (supply|quality|price|procure|regulat|availab|access)|medical (supply|product)",
 "L3-050": r"tobacco|alcohol|smoking|drug (abuse|use|addict|control|demand|prevention|dependen)|narcotic|substance (abuse|use|misuse)|addict",
 "L3-052": r"mental (health|illness|disorder|well-?being|care)|psychosocial|suicide|depress|psychiatr",
 "L3-055": r"food price|price stabili.{0,30}(food|rice|grain|staple)|(food|rice|grain|staple).{0,30}affordab|affordab.{0,30}(food|rice|grain|staple)",
 "L3-056": r"food safety|traceab|hygien|contaminat|halal|food (quality|standard|control|inspection)",
 "L3-057": r"post-?harvest|(grain|food|crop|produce|cold) storage|storage (facilit|capacity|loss)|warehouse|cold chain|silo|food loss|food waste",
 "L3-063": r"\bpolic(e|ing)\b|patrol|law enforcement|crime (detect|prevent|control|rate)|criminal investigat|deterren",
 "L3-064": r"violence prevention|crime prevention|at-?risk youth|gang|community safety|violence interrupt|cognitive behaviou?ral",
 "L3-066": r"prison|correctional|rehabilitat.{0,20}(offender|prisoner|inmate)|(offender|prisoner|inmate).{0,20}(rehabilit|reintegrat)|recidiv|parole|probation|offender",
 "L3-059": r"electrif|electricity access|access to electricity|off-?grid|mini-?grid|solar home|(electricity|grid|household|power) connection",
 "L3-037": r"learning (outcome|quality|loss|poverty)|foundational|(?<!digital )(?<!financial )(?<!media )literacy|numeracy|curricul|(learning|student|national|classroom) assessment|examination|pedagog|reading",
 "L3-034": r"qualification|certif.{0,20}(skill|competenc|worker|occupation)|skills? (certif|recogni|standard|framework|council|intelligence|forecast|anticipat|passport)|recognition of prior|mismatch|employabilit|labou?r market information",
 "L3-069": r"clean (tech|energy (research|technolog|innovat))|low-carbon technolog|green technolog|climate technolog|(clean|green|climate|low-carbon|renewable).{0,30}(r ?& ?d|research and development|innovation)",
 "L3-071": r"energy[- ]efficien|efficiency standard|energy (label|standard|audit|saving|conservation|performance)|appliance|green building|building (energy|efficiency)|retrofit",
 "L3-086": r"risk map|hazard map|risk-informed|risk-sensitive|(hazard|flood|disaster)[- ]prone|flood ?plain|setback|exposure to (hazard|flood|climate|disaster)|relocat.{0,30}(flood|hazard|risk|disaster)|land use.{0,30}(risk|hazard|flood|disaster)",
 "L3-073": r"\bcommons\b|common[- ]pool|common property|community[- ](based|managed|led) (forest|fisher|natural resource|resource|conservation|management)|co-management|community forest|social forestry|customary (tenure|resource|management)",
 "L3-074": r"catch (limit|share|quota)|fishing (quota|licen|right|effort|capacity)|harvest (limit|right|control|quota)|total allowable|individual transferable|\biuu\b|illegal fishing|stock assessment|overfish|fishing ban|closed season",
 "L3-075": r"protected area|national park|(nature|forest|marine|wildlife|biosphere|game) reserve|sanctuar|world heritage site|\bmpa\b|conservation area|no-?take",
 "L3-076": r"payment for ecosystem|\bpes\b|\bredd|(conservation|alternative|forest|nature-?based) livelihood|livelihood.{0,40}(forest|conservation|protected|wildlife|mangrove)|ecotour|non-timber|benefit shar",
 "L3-078": r"(land|forest|mangrove|ecosystem|habitat|watershed|coastal|wetland|coral|peat|soil).{0,20}(restor|rehabilit)|restor.{0,30}(land|forest|mangrove|ecosystem|habitat|wetland|coral|peat|degraded)|reforest|afforest|tree planting|degraded land|desertif|land degradation|regenerat(ive|ion of)",
 "L3-085": r"environmental (awareness|education|campaign|literacy)|(public )?awareness.{0,40}(environment|energy|water|waste|climate|conservation)|behaviou?r change|green school|eco-?school|nudge|social norm",
 "L3-093": r"extractive (transparen|governance|revenue|industr)|\beiti\b|beneficial owner|(mining|mineral|petroleum|oil|gas).{0,20}(licen|concession|contract|revenue|transparen)|resource revenue|revenue (shar|disclos)|natural resource governance",
 "L3-095": r"debt (sustainab|ceiling|anchor|target|reduction)|primary (balance|surplus)|deficit (target|reduction)|fiscal consolidat",
 "L3-098": r"contingent liabilit|(government|sovereign|state|loan|credit) guarantee|fiscal risk|hidden debt|\bsoe (debt|liabilit)",
 "L3-103": r"older worker|retirement age|active ageing|silver (econom|industr|workforce)|senior employ|elderly employ|older persons.{0,30}(work|employ)",
 "L3-105": r"water (allocat|pric|tariff|right|market|use efficien|loss|charge|permit)|allocation of water|metering|non-revenue water|irrigation (fee|charge|service fee)",
 "L3-107": r"\bdams?\b|reservoir|water storage|rainwater harvest|inter-?basin|water transfer|retention (pond|basin)",
 "L3-110": r"economic complex|product complex|complex (product|export)|high[- ]value|high[- ]tech|sophisticat|new export product|non-traditional export|higher value|product space",
 "L3-114": r"(product|quality|export|international|technical) standard|standards and (conformity|certif|quality)|certif.{0,30}(export|product|quality|halal|organic|standard)|conformity|metrolog|accredit|quality infrastructure|\bsps\b|sanitary and phyto|technical barrier|\btbt\b",
 "L3-120": r"trade liberali|tariff (reduc|cut|liberal|rational)|import liberal|open(ing)? (the |of the )?economy|trade openness|unilateral liberal",
 "L3-122": r"spillover|supplier (development|link|upgrad)|local supplier|technology transfer from|joint venture|linkage.{0,40}(foreign|fdi|multinational|investor)|(foreign|fdi|multinational).{0,40}linkage",
 "L3-127": r"touris.{0,40}(recover|restart|reviv|reopen|resilien|diversif.{0,20}market|source market)|(recover|reviv|resilien).{0,40}touris",
 "L3-129": r"technology adopt|adoption of (new |modern |digital |advanced )?technolog|technology (diffus|upgrad|extension|uptake)|diffus.{0,20}technolog|industry 4\.0|digital transformation of (firms|business|msme|sme|enterprise)|automation of|modern technolog",
 "L3-134": r"space (programme|program|agency|industr|technolog|exploration)|satellite|aerospace|semiconductor|quantum|frontier tech|moonshot|mission-oriented|deep tech",
 "L3-146": r"(power|electricity|energy) generat|generation capacity|transmission (line|grid|network|system)|\bgrid\b|outage|blackout|load shedding|reliab(le|ility) (power|electricity|supply|energy)|power (plant|station|supply)|substation|capacity addition",
 "L3-147": r"non-revenue|(technical|distribution|system) loss|(electricity|power|water) theft|(revenue|bill) collection|financial viabil|cost recover|utilit(y|ies) (financ|restructur|reform)|arrears|tariff.{0,20}cost",
 "L3-148": r"(energy|fuel|electricity|power|water|lpg|diesel|petrol|gas|kerosene) (subsid|pric|tariff)|subsid.{0,40}(energy|fuel|electricity|power|water|lpg|diesel|petrol|gas)|tariff reform|price reform|subsidy reform|cross-?subsid",
 "L3-149": r"unbundl|wholesale (power|electricity|energy) market|independent power|\bipp\b|open access|third-party access|liberali[sz].{0,40}(power|electricity|energy|telecom|water|utilit)|privati[sz].{0,40}(utilit|power|electricity|energy|water)|(power|electricity|energy|telecom) (sector|market) (reform|competition|liberal)",
 "L3-151": r"linkage|value chain|supply chain|supplier|agro-?process|(processing|manufacturing) (industr|plant|facilit|hub|zone)|food processing|downstream|upstream",
 "L3-155": r"aggregat(ion|or)|market linkage|transaction cost|middlem|intermediar|collection (cent|point)|market access for (farmer|smallholder|producer)",
 "L3-156": r"cooperativ|co-op|producer (organi|group|association|compan)|farmer (organi|group|association|compan)|collective (marketing|action)",
 "L3-158": r"\bseeds?\b|fertili[sz]|(agricultural|farm) input|input (subsid|voucher|supply|access)|agrochemical|improved (seed|variet)",
 "L3-159": r"agricultur(al)? extension|extension (service|worker|agent|officer|system)|(farm|agricultural) advisory|advisory service|farmer field school|demonstration (plot|farm|site)|farmer training|training of farmers|smart farmer",
 "L3-161": r"agricultur(al)? research|(crop|livestock|rice|seed|aquaculture) research|research.{0,40}(agricultur|crop|livestock|rice|variet|seed)|variet|breeding|biotech|genetic|seed system",
 "L3-162": r"mechani[sz](e|ation|ed|ing)|tractor|machinery|(land|farm|plot) consolidat|land pooling|farm size|collective farm|large-?scale farm",
 "L3-163": r"\bpests?\b|(plant|animal|livestock|crop|aquatic|fish) (disease|health)|veterinar|animal (health|vaccin)|biosecur|locust|fall armyworm|quarantine|pest (control|management)",
 "L3-164": r"management (practice|training|skill|quality|capabilit|consult)|business (training|skill|development service|advis)|mentor|consultanc|entrepreneurship (education|training)|kaizen|\blean\b",
 "L3-165": r"(sme|msme|small (firm|business|enterprise)|enterprise|business|firm).{0,40}(credit|loan|financ)|(credit|loan|financ).{0,40}(sme|msme|small (firm|business|enterprise)|enterprise|business|firm)|matching grant|credit guarantee",
 "L3-168": r"business (registr|licen|permit|start-?up procedure)|company registr|(licen[cs]ing|permit) (procedure|process|reform|regime)|one[- ]stop|ease of doing|regulatory burden|red tape|simplif.{0,40}(procedure|licen|regist|permit|regulat)|doing business",
 "L3-169": r"competition (law|polic|authorit|commission|act)|\bcompetition\b|antitrust|anti-?competitive|cartel|monopol|consumer protect|unfair (trade|competition|practice)|level playing",
 "L3-173": r"microfinanc|microcredit|micro-?loan|micro-?insurance|(credit|loan|lending).{0,40}(poor|household|farmer|women|micro|low-income|informal)|(poor|household|farmer|women|micro|low-income).{0,40}(credit|loan|lending)|financial inclusion|credit access",
 "L3-174": r"savings (account|product|group|mobili|scheme|culture|rate|behaviou?r)|household saving|village savings|saving(s)? and (credit|loan)|promote saving|saving(s)? (habit|promotion)",
 "L3-178": r"labou?r (law|code|regulation|market flexib|market reform)|flexible (work|employment|labou?r)|dismissal|employment protection|severance|hiring and firing",
 "L3-181": r"(trade|labou?r) union|\bunions?\b|collective bargain|decent work|labou?r (right|standard)|worker.?s rights|freedom of association",
 "L3-182": r"occupational|workplace (safety|health|accident|injur)|labou?r inspect|work(-| )related (injur|accident|disease)|\bosh\b|safety at work|industrial accident",
 "L3-183": r"adjustment assistance|trade adjust|retrench|displaced worker|transition of workers|worker (transition|redeploy)|import competition|(plant|factory) closure|lay-?off",
 "L3-191": r"return(ing|ee)? migrant|returnee|return migration|reintegrat.{0,40}(migrant|returnee|worker)|returning (worker|national|citizen)",
 "L3-192": r"overseas (employment|worker|job)|labou?r (export|mobility agreement|migration)|bilateral labou?r|seasonal work|migrant worker|deployment of workers|workers? abroad|foreign employment",
 "L3-194": r"land (tenure|right|certificat|title|security)|tenure|customary (land|tenure)|secure (land|property) rights",
 "L3-195": r"land (registr|titl|record)|\btitl(e|ing)\b|cadast|property registr",
 "L3-196": r"land (rental|market|lease|bank|valuation|information|transaction|administration)|rental market|land use right transfer|cadast",
 "L3-197": r"land redistribut|agrarian reform|land reform|landless|land allocation|land to the tiller|tenancy reform|land ceiling",
 "L3-202": r"energy secur|security of supply|supply secur|self-?suffic|import dependen|diversif.{0,40}(suppl|source|import)|supply (disruption|chain resilien|chain risk)|import substitut|critical (input|supplies|material|mineral|good)",
 "L3-221": r"data protection|personal data|privacy|consent",
 "L3-223": r"digital platform|platform (econom|regulat|competition|market|worker)|online platform|big tech|digital (market|competition)|telecom (regulat|competition)|spectrum",
 "L3-231": r"intergovernmental (transfer|grant|fiscal)|fiscal transfer|revenue shar|equali[sz]ation|block grant|conditional grant|fiscal decentrali|own-source|local (revenue|tax|government financ)|transfer formula",
 "L3-232": r"tax (compliance|audit|administrat|enforc|evasion|collection|gap)|e-?invoic|third-?party (information|report|data)|withholding|electronic (fil|tax)|digiti[sz].{0,30}tax|risk-based audit|taxpayer (regist|identif)|tax base broaden",
 "L3-237": r"budget (reform|process|credib|execution|institution|classification|preparation|system|transparen)|programme budget|performance budget|\bmtef\b|medium-term (expenditure|budget|fiscal framework)|treasury single|\bifmis\b|cash management|public financial management|\bpfm\b|expenditure management",
 "L3-240": r"regulator(y|s)?\b.{0,30}(capacit|independen|agency|authorit|body|commission|reform|framework|quality)|independent regulator|regulatory impact|sector regulat|regulat.{0,30}(telecom|energy|electricity|water|financial|transport|health|food|drug|pharma)",
 "L3-241": r"inspect|environmental (enforc|compliance|permit|impact|monitor|audit)|\beia\b|pollution (control|permit|licen|monitor)|compliance monitor|emission (permit|monitor)|effluent|enforcement of (environmental|pollution)",
 "L3-243": r"continuity|remote (learning|deliver|work)|distance learning|business continuity|tele-?(medicine|health|consult|education)|online (learning|class)",
 "L3-245": r"reconstruct|post-?disaster|rebuild|build back|disaster recover|recovery.{0,40}(disaster|flood|cyclone|earthquake|typhoon)",
 "L3-249": r"civil society|\bcsos?\b|\bngos?\b|non-governmental|civic (organi|associat|space|engagement)|community[- ]based organi|volunteer",
 "L3-253": r"electoral competition|competitive election|political competition|electoral accountab|re-?election|free and fair",
 "L3-004": r"disab|accessib.{0,30}(disab|person|building|transport|service|design)|universal design|impair|assistive",
 "L3-006": r"birth registr|civil registr|legal identity|identity (card|document|system|management)|national id|digital id|\bid card|identification (document|system|number)|vital (registr|statistic)",
 "L3-011": r"horizontal inequal|group grievance|grievance|between groups|ethnic (inequal|tension|minorit|group)|minority (rights|group)|indigenous|marginali[sz]ed (group|communit)",
 "L3-013": r"interfaith|inter-?faith|social harmony|religious harmony|toleran|intercultural|inter-?religious|coexist|inter-?group|inter-?communal|inter-?ethnic",
 "L3-018": r"resettl|relocat|displac|land acquisition.{0,40}compensat|compensat.{0,40}(land|resettl|displac|affected (people|household|communit))|project-?affected",
 "L3-015": r"reconcil|transitional justice|truth (commission|telling|and reconcil)|reparation|memorial|amnesty",
 "L3-010": r"child (abuse|neglect|protection|maltreat)|abuse|orphan|alternative care|foster care|street children|maltreat|adverse childhood",
}
CUES["L3-212"] = r"big push|coordinat\w* (of )?investment|complementar|development plan|national plan|planning (system|process|framework|commission|agency)|five[- ]year plan"

# Pathways the reviewer added. Fields the reviewer did not give (text cues, risks) are set here
# and marked as assigned at the v3 build, not source-verified.
NEW_PATHWAYS = {
    "Extension of contributory social insurance to informal workers": {
        "text_cues": r"informal (workers?|sector|economy|employ).{0,60}(insurance|pension|social (security|protection))|(insurance|pension|social (security|protection)).{0,60}informal",
        "risks": ["Demographic Shifts"]},
    "Household digital access and effective use": {
        "text_cues": r"digital (access|inclusion|literacy|divide|skills for (all|citizens))|internet access|affordable (internet|connectivity|devices|broadband)|households?.{0,40}(internet|broadband|connectivity)",
        "risks": ["Technological Change"]},
    "Local labour-market adjustment to decarbonisation": {
        "text_cues": r"just transition|coal (phase|transition|closure|mine|region)|fossil[- ]fuel (workers|communities|regions|dependent)|decarboni[sz]ation.{0,40}(workers|jobs|communities|regions)",
        "risks": ["Climate Change", "Resource and Energy Pressures"]},
    "Interoperability and data sharing across agencies": {
        "text_cues": r"data (sharing|exchange|interoperab)|interoperab|shared (data|registr|database)|data governance|open data|integrated (database|data platform|information system)",
        "risks": ["Technological Change"]},
    "Crisis and emergency risk communication": {
        "text_cues": r"risk communication|crisis communication|emergency communication|public (warning|alert)|communicat.{0,40}(crisis|emergenc|disaster|outbreak)",
        "risks": ["Pandemics", "Climate Change"]},
}
# SDG targets for families whose pathways came from no single v2 lever (the one-pathway
# governance families); every other family rolls its targets up from the v2 mechanisms.
FAMILY_SDG = {"Scenario and futures work": ["16.6"], "Development planning": ["17.14", "16.6"],
              "Statistics and data sharing": ["17.18", "17.19", "16.6"], "Policy experimentation": ["16.6"],
              "Participatory decision-making": ["16.7"], "Delegated management autonomy": ["16.6"],
              "Crisis and risk communication": ["16.6", "13.3", "3.d"]}
NEW_PATHWAY_NOTE = "assigned at the v3 build from the reviewer's note; not source-verified"


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def chain(text):
    """'Works when X · How A → B · Result C' -> conditions, causal_input, transmission, outcome."""
    out = {"conditions": "", "causal_input": "", "transmission": "", "outcome": ""}
    for part in (text or "").split(" · "):
        part = part.strip()
        if part.startswith("Works when "):
            out["conditions"] = part[len("Works when "):]
        elif part.startswith("How "):
            a, _, b = part[len("How "):].partition(" → ")
            out["causal_input"], out["transmission"] = a, b
        elif part.startswith("Result "):
            out["outcome"] = part[len("Result "):]
    return out


def read_reviewer():
    """The outline as groups and families, each family with its pathway names in order."""
    out = json.load(open(REVIEWER, encoding="utf-8"))
    groups, families, sub = [], [], None
    grp = fam = None
    for kind, n in out:
        if kind == "l1":
            sub = n["name"]
        elif kind == "g2":
            grp = {"group": n["name"], "subpillar": sub, "basis": n.get("basis", ""),
                   "definition": n.get("def", ""), "why": n.get("rule", "")}
            groups.append(grp)
        elif kind == "l2":
            fam = {"family": n["name"], "group": grp["group"], "definition": n.get("def", ""),
                   "examples": n.get("ex", ""), "pathways": []}
            families.append(fam)
        elif kind == "l3" and fam is not None:
            fam["pathways"].append({"name": n["name"], "chain": n.get("chain", ""), "cite": n.get("cite", "")})
    return groups, families


def main():
    v2 = json.load(open(V2, encoding="utf-8"))
    v2_paths = {norm(p["pathway"]): p for p in v2["pathways"]}
    v2_mechs = {m["mechanism_id"]: m for m in v2["mechanisms"]}
    sub_by_name = {s["name"]: s for s in v2["subpillars"]}
    pillar_name = {p["code"]: p["name"] for p in v2["pillars"]}
    groups_in, families_in = read_reviewer()
    groups_in = [g for g in groups_in if g["subpillar"] not in GENERAL]      # General branches are holding nodes

    # ---- amendments on the reviewer's structure
    for name, (sub, basis, definition) in NEW_GROUPS.items():
        groups_in.append({"group": name, "subpillar": sub, "basis": basis, "definition": definition, "why": ""})
    fam_by_name = {f["family"]: f for f in families_in}
    for new, spec in SPLIT.items():
        src = fam_by_name[spec["from"]]
        moved = [p for p in src["pathways"] if p["name"] in spec["pathways"]]
        src["pathways"] = [p for p in src["pathways"] if p["name"] not in spec["pathways"]]
        families_in.append({"family": new, "group": spec["group"], "definition": spec["definition"],
                            "examples": "", "pathways": moved})
        fam_by_name[new] = families_in[-1]
    for src, dst in MERGE.items():
        fam_by_name[dst]["pathways"] += fam_by_name[src]["pathways"]
        families_in.remove(fam_by_name[src])
    for name, dst in MOVE_PATHWAY.items():
        src = next(f for f in families_in if any(p["name"] == name for p in f["pathways"]))
        moved = next(p for p in src["pathways"] if p["name"] == name)
        src["pathways"].remove(moved)
        fam_by_name[dst]["pathways"].append(moved)
    for f in families_in:
        if f["family"] in EXAMPLES:
            f["examples"] = EXAMPLES[f["family"]]
        if f["family"] in MOVE_FAMILY:
            f["group"] = MOVE_FAMILY[f["family"]]
        if f["family"] in RENAME:
            f["family"] = RENAME[f["family"]]
        if f["family"] in REDEFINE:
            f["definition"] = REDEFINE[f["family"]]
    used = {f["group"] for f in families_in}
    groups_in = [g for g in groups_in if g["group"] in used]
    for g in groups_in:
        if g["group"] in GROUP_REDEFINE:
            g["definition"] = GROUP_REDEFINE[g["group"]]

    # ---- ids: groups in subpillar order, families in group order, pathways keep v2 ids
    sub_order = list(SUBPILLAR_CODE)
    groups_in.sort(key=lambda g: sub_order.index(g["subpillar"]))
    groups = {}
    for i, g in enumerate(groups_in, 1):
        code = SUBPILLAR_CODE[g["subpillar"]]
        gid = "G-%02d" % i
        groups[gid] = {"group_id": gid, "group": g["group"], "level": "L1",
                       "pillar": pillar_name[sub_by_name[g["subpillar"]]["pillar"]],
                       "pillar_code": sub_by_name[g["subpillar"]]["pillar"], "subpillar": g["subpillar"],
                       "subpillar_code": code, "basis": g["basis"], "definition": g["definition"],
                       "family_ids": [], "sdg_targets": [], "risks": [], "assets": [], "n_families": 0, "n_pathways": 0}
    gid_of = {g["group"]: gid for gid, g in groups.items()}
    families_in.sort(key=lambda f: list(groups).index(gid_of[f["group"]]))
    families, pathways = {}, {}
    next_new = 260
    for i, f in enumerate(families_in, 1):
        fid = "F-%02d" % i
        g = groups[gid_of[f["group"]]]
        fam = {"family_id": fid, "family": f["family"], "level": "L2", "group_id": g["group_id"],
               "group": g["group"], "pillar": g["pillar"], "subpillar": g["subpillar"],
               "subpillar_code": g["subpillar_code"], "definition": f["definition"],
               "examples": f["examples"].replace("Examples from plans ", ""), "plan_words": "",
               "pathway_ids": [], "v2_mechanisms": [], "sdg_targets": [], "assets": [], "risks": [],
               "conditional_risks": [], "n_pathways": 0}
        families[fid] = fam
        g["family_ids"].append(fid)
        for p in f["pathways"]:
            old = v2_paths.get(norm(p["name"]))
            if old:
                row = dict(old)
                row.update(family_id=fid, family=fam["family"], group_id=g["group_id"], group=g["group"],
                           subpillar=g["subpillar"], pillar=g["pillar"],
                           v2_mechanism_id=old["mechanism_id"], v2_mechanism=old["mechanism"],
                           v2_family_id=old["family_id"], v2_family=old["family"],
                           subpillar_changed=("from %s" % old["subpillar"]) if old["subpillar"] != g["subpillar"] else "")
                for k in ("mechanism_id", "mechanism"):
                    row.pop(k, None)
            else:
                spec = NEW_PATHWAYS[p["name"]]
                pid = "L3-%03d" % next_new
                next_new += 1
                row = dict(pathway_id=pid, pathway=p["name"], level="L3", family_id=fid, family=fam["family"],
                           group_id=g["group_id"], group=g["group"], subpillar=g["subpillar"], pillar=g["pillar"],
                           old_family_id="", old_family="", old_subpillar="", subpillar_changed="", merged_into="",
                           **chain(p["chain"]), distinction="", evidence=p["cite"],
                           risks=list(spec["risks"]), risk_justification=NEW_PATHWAY_NOTE, conditional_risks=[],
                           baseline="", evidence_status="cited by the reviewer, not yet independently verified",
                           risk_status=NEW_PATHWAY_NOTE, text_cues=spec["text_cues"],
                           v2_mechanism_id="", v2_mechanism="", v2_family_id="", v2_family="", added_in="v3")
            pathways[row["pathway_id"]] = row
            fam["pathway_ids"].append(row["pathway_id"])

    # ---- deep-check overrides on the rows
    for pid, row in pathways.items():
        row["revised"] = []
        if pid in CUES:
            row["text_cues"], _ = CUES[pid], row["revised"].append("cues")
        if pid in EVIDENCE:
            row["evidence"], _ = EVIDENCE[pid], row["revised"].append("evidence")
        if pid in DISTINCTION:
            row["distinction"] = DISTINCTION[pid]
        if pid in UNMERGE and row.get("merged_into"):
            row["distinction"] = ("unmerged in v3: %s. " % UNMERGE[pid] + (row.get("distinction") or "")).strip()
            row["merged_into"] = ""
            row["revised"].append("unmerged")
        row["distinction"] = (row.get("distinction") or "").replace("(F37)", "(L3-097)")
    for name, dst in MOVE_PATHWAY.items():
        row = next(r for r in pathways.values() if r["pathway"] == name)
        row["revised"].append("moved")
    # a pathway still merged into a sibling lends the sibling its cues, so its wording keeps a way in
    for row in pathways.values():
        dst = row.get("merged_into")
        if dst and row.get("text_cues"):
            tgt = pathways[dst]
            tgt["text_cues"] = "|".join(c for c in [tgt.get("text_cues", ""), row["text_cues"]] if c)
            tgt["revised"].append("cues of %s" % row["pathway_id"])
    for row in pathways.values():
        re.compile(row["text_cues"], re.I)
        row["revised"] = "; ".join(row["revised"])

    # ---- plan words, SDG targets and assets: from the v2 mechanisms whose pathways landed here
    for fam in families.values():
        own = [pathways[p] for p in fam["pathway_ids"]]
        share = collections.Counter(p["v2_mechanism_id"] for p in own if p.get("v2_mechanism_id"))
        words, sdg, assets = [], [], []
        for mid, n in share.most_common():
            m = v2_mechs[mid]
            total = len([p for p in m["pathway_ids"] if not v2_paths_by_id(v2)[p].get("merged_into")]) or len(m["pathway_ids"])
            if n * 2 >= total:                      # most of this lever's channels are here
                words.append(m["plan_words"])
                fam["v2_mechanisms"].append(mid)
                sdg += [t for t in m["sdg_targets"] if t not in sdg]
                assets += [a for a in m["assets"] if a not in assets]
        for p in own:                               # channels whose lever sits elsewhere, or new ones
            if p.get("v2_mechanism_id") not in fam["v2_mechanisms"] and p.get("text_cues"):
                words.append(p["text_cues"])
        fam["plan_words"] = "|".join(w for w in words if w)
        re.compile(fam["plan_words"], re.I)
        fam["sdg_targets"] = sdg or list(FAMILY_SDG.get(fam["family"], []))
        fam["assets"] = assets
        risks = collections.OrderedDict()
        for p in own:
            if p.get("merged_into"):
                continue
            for r in p.get("risks") or []:
                risks.setdefault(r, []).append(p["pathway_id"])
            for c in p.get("conditional_risks") or []:
                fam["conditional_risks"].append(dict(c, pathway_id=p["pathway_id"]) if isinstance(c, dict) else {"pathway_id": p["pathway_id"], "risk": c})
        fam["risks"] = list(risks)
        fam["risk_sources"] = {r: ps for r, ps in risks.items()}
        fam["n_pathways"] = len([p for p in own if not p.get("merged_into")])
    for g in groups.values():
        for fid in g["family_ids"]:
            f = families[fid]
            g["sdg_targets"] += [t for t in f["sdg_targets"] if t not in g["sdg_targets"]]
            g["risks"] += [r for r in f["risks"] if r not in g["risks"]]
            g["assets"] += [a for a in f["assets"] if a not in g["assets"]]
            g["n_pathways"] += f["n_pathways"]
        g["n_families"] = len(g["family_ids"])

    # ---- checks
    missing = [p["pathway"] for p in v2["pathways"] if p["pathway_id"] not in pathways]
    assert not missing, "v2 pathways not placed: %s" % missing
    assert len(pathways) == 264, len(pathways)
    assert all(f["plan_words"] for f in families.values()), [f["family"] for f in families.values() if not f["plan_words"]]
    assert all(f["sdg_targets"] for f in families.values()), [f["family"] for f in families.values() if not f["sdg_targets"]]
    # v2 merged seven pathways into siblings. Where the reviewer places the two under different
    # families they are distinct channels after all, so the merge is undone and said so.
    unmerged = []
    for p in pathways.values():
        dst = p.get("merged_into")
        if dst and pathways[dst]["family_id"] != p["family_id"]:
            p["merged_into"] = ""
            p["distinction"] = ("unmerged in v3: v2 merged it into %s, which the reviewer places under %s. "
                                % (dst, pathways[dst]["family"]) + (p.get("distinction") or "")).strip()
            unmerged.append(p["pathway_id"])
    merges = {p["pathway_id"]: p["merged_into"] for p in pathways.values() if p.get("merged_into")}

    for fam in families.values():
        fam["n_pathways"] = len([p for p in fam["pathway_ids"] if not pathways[p].get("merged_into")])
    for g in groups.values():
        g["n_pathways"] = sum(families[f]["n_pathways"] for f in g["family_ids"])

    # ---- defaults from v2 for re-mapping: v2 mechanism -> v3 family that holds most of its pathways
    mech_default = {}
    for mid, m in v2_mechs.items():
        c = collections.Counter(pathways[p]["family_id"] for p in m["pathway_ids"] if p in pathways)
        mech_default[mid] = c.most_common(1)[0][0] if c else ""
    fam_default = {}
    for f in v2["families"]:
        c = collections.Counter(families[mech_default[m]]["group_id"] for m in f["mechanism_ids"] if mech_default.get(m))
        fam_default[f["family_id"]] = c.most_common(1)[0][0] if c else ""

    # ---- write
    def write_csv(path, rows, columns):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()})
    write_csv(os.path.join(HERE, "groups_v3.csv"), groups.values(),
              ["group_id", "group", "level", "pillar", "subpillar", "subpillar_code", "basis", "definition",
               "n_families", "n_pathways", "family_ids", "sdg_targets", "risks", "assets"])
    write_csv(os.path.join(HERE, "families_v3.csv"), families.values(),
              ["family_id", "family", "level", "group_id", "group", "pillar", "subpillar", "subpillar_code", "definition",
               "examples", "plan_words", "n_pathways", "pathway_ids", "v2_mechanisms", "sdg_targets", "risks", "assets"])
    write_csv(os.path.join(HERE, "pathways_v3.csv"), pathways.values(),
              ["pathway_id", "pathway", "level", "family_id", "family", "group_id", "group", "subpillar", "pillar",
               "v2_mechanism_id", "v2_mechanism", "v2_family_id", "v2_family", "subpillar_changed", "merged_into",
               "causal_input", "transmission", "outcome", "conditions", "distinction", "evidence", "risks",
               "conditional_risks", "evidence_status", "risk_status", "text_cues", "added_in", "revised"])
    sdg_rows = [{"family_id": f["family_id"], "family": f["family"], "group": f["group"], "subpillar": f["subpillar"],
                 "sdg_target": t, "sdg_dimension": v2["sdg_dim"].get(t, "")}
                for f in families.values() for t in f["sdg_targets"]]
    write_csv(os.path.join(HERE, "sdg_crosswalk.csv"), sdg_rows,
              ["family_id", "family", "group", "subpillar", "sdg_target", "sdg_dimension"])
    risk_rows = [{"family_id": f["family_id"], "family": f["family"], "group": f["group"], "subpillar": f["subpillar"],
                  "risk": r, "pathways": ps, "conditional": any(c.get("risk") == r for c in f["conditional_risks"])}
                 for f in families.values() for r, ps in f["risk_sources"].items()]
    write_csv(os.path.join(HERE, "risk_matrix.csv"), risk_rows,
              ["family_id", "family", "group", "subpillar", "risk", "pathways", "conditional"])
    tree = {"meta": {"version": "v3", "built": "2026-10-29",
                     "levels": ["pillar", "subpillar", "L1 group", "L2 family", "L3 pathway", "L4 objective", "L5 strategy"],
                     "required_level": "L2",
                     "depth_rule": "Every strategy is placed on a family (L2), the required level; a group alone is not a placement. "
                                   "A pathway (L3) only when the strategy's wording names that causal channel (text_cues) and no sibling. "
                                   "A standing function of the state with no family goes to the subpillar's General branch.",
                     "source": "The reviewer's framework of 27 October 2026 (inputs/reviewer_framework.json) over tree v2's pathways; "
                               "amendments in build.py", "merges": merges},
            "pillars": v2["pillars"], "subpillars": v2["subpillars"],
            "holding": [{"id": "H-SPE", "name": "General People"}, {"id": "H-SEC", "name": "General Economy"},
                        {"id": "H-SGO", "name": "General Governance"}, {"id": "H-GOAL", "name": "Goals held outside the tree"}],
            "groups": list(groups.values()), "families": list(families.values()), "pathways": list(pathways.values()),
            "assets": v2["assets"], "risks": v2["risks"], "sdg_goals": v2["sdg_goals"], "sdg_dim": v2["sdg_dim"],
            "target_classes": v2["target_classes"], "instrument_classes": v2["instrument_classes"],
            "v2_mechanism_default": mech_default, "v2_family_default": fam_default}
    with open(os.path.join(HERE, "tree_v3.json"), "w", encoding="utf-8") as fh:
        json.dump(tree, fh, ensure_ascii=False, indent=1)
    by_sub = collections.Counter(g["subpillar_code"] for g in groups.values())
    print("v3: %d groups, %d families, %d pathways (%d merged, %d unmerged from v2, %d new); groups per subpillar %s" % (
        len(groups), len(families), len(pathways), len(merges), len(unmerged) + len(UNMERGE), 264 - 259, dict(by_sub)))
    thin = [(f["family"], f["n_pathways"]) for f in families.values() if f["n_pathways"] <= 1]
    print("one-pathway families:", thin)


_BY_ID = {}


def v2_paths_by_id(v2):
    if not _BY_ID:
        _BY_ID.update({p["pathway_id"]: p for p in v2["pathways"]})
    return _BY_ID


if __name__ == "__main__":
    main()
