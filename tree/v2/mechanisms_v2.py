"""The 99 mechanisms of mother tree v2 (level L2: the lever a plan pulls), hand-written.

Each entry: (id, family_id, name, intermediate variable the lever is meant to move, plan words
(a case-insensitive regex that marks the lever in a strategy's own wording), SDG targets whose
indicators move with the intermediate variable, asset classes the mechanism mobilises, pathways
carried (v1 L3 ids as integers)).

SDG targets are the outcome crosswalk; a mechanism's 5 P profile follows from them through
workflow/vocab/sdg_target_dimensions.json. Risk tags are not written here: build.py rolls them up
from the pathways' literature tags, so the mechanism x risk matrix stays traceable to a citation.
"""

M = []


def m(mid, fam, name, variable, words, sdg, assets, pathways):
    M.append((mid, fam, name, variable, words, sdg, assets, pathways))


# ---------------------------------------------------------------- FAM-01 Equal rights and inclusion (TSE)
m("MEC-01", "FAM-01", "Non-discrimination and equal access", "gaps in employment, pay and service access by group",
  r"discriminat|equal (opportunit|access|treatment|pay)|anti-?racis|affirmative action|disabilit|accessib|civil registr|birth registr|identity (card|document)|legal identity",
  ["10.2", "10.3", "16.9", "16.b", "8.5"], [], [1, 4, 6])
m("MEC-02", "FAM-01", "Gender equality and care work", "female labour-force participation and women's control of resources",
  r"gender|women|girls|female|childcare|child care|unpaid care|care (work|economy)|maternity|paternity",
  ["5.1", "5.4", "5.5", "5.c", "5.a"], ["AST-03"], [2, 5])
m("MEC-03", "FAM-01", "Representation of excluded groups", "share of excluded groups in decision-making bodies",
  r"representation|quota|reserved seat|indigenous|ethnic minorit|minority (right|participation)|voice of",
  ["5.5", "10.2", "16.7"], [], [3])
m("MEC-99", "FAM-01", "Decent work and protection of informal workers", "share of workers with contracts, labour rights and social insurance coverage",
  r"informal (worker|labour|employment|sector worker)|labour (right|standard|inspection)|decent work|collective bargaining|trade union|occupational (safety|health)|workplace safety|social (insurance|security) coverage for (informal|all) workers",
  ["8.8", "8.5", "10.4", "1.3"], [], [181, 182])

# ---------------------------------------------------------------- FAM-02 Safety from violence and exploitation (CAP)
m("MEC-04", "FAM-02", "Violence against women and children", "prevalence of intimate-partner violence, child labour and child marriage",
  r"domestic violence|gender-?based violence|violence against (women|children)|child (protection|labour|marriage|abuse)|early marriage|traffick|sexual (violence|abuse|harass)",
  ["5.2", "5.3", "8.7", "16.2"], [], [7, 8, 9, 10])
m("MEC-05", "FAM-02", "Crime prevention and policing", "crime and violence rates",
  r"\bcrime|policing|police|public (safety|security|order)|drug (traffick|control|enforcement)|organi[sz]ed crime|illicit",
  ["16.1", "16.4", "16.a"], [], [63, 64, 67])
m("MEC-06", "FAM-02", "Justice, rehabilitation and legal empowerment", "access to justice and recidivism",
  r"access to justice|legal aid|court|judicia|justice (system|sector|reform)|prison|correction|rehabilitat|recidiv|dispute resolution|paralegal",
  ["16.3", "16.6", "16.b"], ["AST-07"], [65, 66])

# ---------------------------------------------------------------- FAM-03 Social cohesion and peace (TSE)
m("MEC-07", "FAM-03", "Reducing group grievance and polarisation", "horizontal inequality between groups and affective polarisation",
  r"grievance|horizontal inequalit|polari[sz]|inter-?group|inter-?ethnic|sectarian|extremis|radicali[sz]",
  ["10.2", "16.1", "16.a"], [], [11, 12, 17, 259])  # 259 merged into 011
m("MEC-08", "FAM-03", "Shared identity and intergroup contact", "trust between groups and sense of shared national identity",
  r"national (identity|unity|harmony)|social (cohesion|harmony)|tolerance|multicultural|interfaith|unity in diversity|shared values",
  ["16.7", "10.2", "4.7"], ["AST-09"], [13, 14])
m("MEC-09", "FAM-03", "Reconciliation and peacebuilding", "trust in institutions and conflict recurrence",
  r"reconciliation|peace(building| process| agreement)|transitional justice|truth commission|ex-?combatant|disarm|demobili[sz]|reintegrat",
  ["16.1", "16.3", "16.a"], [], [15, 16])
m("MEC-10", "FAM-03", "Displacement, resettlement and refugee integration", "livelihood recovery of displaced people and host-community outcomes",
  r"displac|resettle|refugee|asylum|internally displaced|\bIDPs?\b|host communit|relocat",
  ["10.7", "1.5", "16.1"], [], [18, 20])

# ---------------------------------------------------------------- FAM-04 Human capital formation (CAP)
m("MEC-11", "FAM-04", "Early childhood development and nutrition", "stunting, early learning and school attendance",
  r"early childhood|pre-?school|kindergarten|nutrition|stunting|malnutrition|school (meal|feeding|health)|breastfeed|micronutrient",
  ["2.2", "4.2", "3.2"], ["AST-03"], [39, 54, 58, 42])
m("MEC-12", "FAM-04", "Access to and completion of schooling", "enrolment and completion rates",
  r"enrol|out-?of-?school|school (access|attendance|completion|dropout|infrastructure|building)|compulsory education|free education|classroom|scholarship|basic education|secondary education",
  ["4.1", "4.5", "4.a"], ["AST-03"], [36, 40])
m("MEC-13", "FAM-04", "Teaching and learning quality", "learning outcomes and teacher effectiveness",
  r"learning (outcome|quality|achievement)|teacher|curricul|pedagog|literacy|numeracy|education quality|quality of education|(learning|student|national) assessment|national examination",
  ["4.1", "4.6", "4.c"], ["AST-04"], [37, 38])
m("MEC-14", "FAM-04", "Skills for work", "share of the workforce with job-relevant and digital skills",
  r"vocational|TVET|technical education|apprentice|skills? (development|training|gap|mismatch)|reskill|upskill|lifelong learning|workforce (skill|development)|digital (skill|literacy)|competenc",
  ["4.3", "4.4", "8.6"], ["AST-03", "AST-04"], [32, 33, 34, 35, 31])
m("MEC-15", "FAM-04", "Higher education and research skills", "graduates and researchers per capita, university quality",
  r"universit|higher education|tertiary|postgraduate|doctoral|\bPhD|research (talent|skill|capacity)|academic",
  ["4.3", "4.b", "9.5"], ["AST-04", "AST-10"], [41])

# ---------------------------------------------------------------- FAM-05 Health and longevity (CAP)
m("MEC-16", "FAM-05", "Coverage and quality of health care", "service coverage, avoidable mortality and quality of care",
  r"health (service|care|facilit|system|centre|center|infrastructure)|hospital|primary (health )?care|universal health|maternal|newborn|child (health|mortality)|quality of care|clinic",
  ["3.1", "3.2", "3.8", "3.4"], [], [43, 44, 47])
m("MEC-17", "FAM-05", "Health workforce and medicines", "health workers per 10,000 and access to essential medicines",
  r"health (worker|workforce|personnel|professional)|doctor|nurse|midwi|medicine|pharmaceutical|drug (supply|access|quality)|vaccine (supply|production)|medical (supplies|equipment)",
  ["3.c", "3.b", "3.8"], ["AST-04"], [45, 46])
m("MEC-18", "FAM-05", "Infectious disease control and food safety", "incidence of infectious and foodborne disease",
  r"infectious|communicable disease|HIV|tuberculosis|malaria|immuni[sz]ation|vaccinat|epidemic control|food safety|food (hygiene|standard)|antimicrobial",
  ["3.3", "2.1", "3.d"], [], [49, 56])
m("MEC-98", "FAM-05", "Healthy behaviours, mental health and injury prevention", "burden of non-communicable disease, mental illness and injury",
  r"non-?communicable|NCD|tobacco|alcohol|obesity|physical activity|mental health|suicide|road (safety|accident|traffic)|injur|healthy (lifestyle|behaviour)|health promotion|substance|narcotic",
  ["3.4", "3.5", "3.6", "3.a"], [], [48, 50, 51, 52])
m("MEC-19", "FAM-05", "Financial protection and health insurance", "catastrophic health spending and insurance coverage",
  r"health insurance|health (financing|coverage scheme)|out-?of-?pocket|catastrophic (health )?(spending|expenditure)|social health",
  ["3.8", "1.3"], [], [26])

# ---------------------------------------------------------------- FAM-06 Income security and social protection (CAP)
m("MEC-20", "FAM-06", "Social assistance and cash transfers", "coverage of the poor by transfers and consumption stability",
  r"cash transfer|social (assistance|welfare|protection|safety net|registry)|safety net|(social|welfare|child|disability|unemployment|old-?age) benefit|allowance|grant to (poor|household)|targeting|poverty (reduction|alleviation) program",
  ["1.3", "1.2", "10.4"], [], [21, 27, 28, 30])
m("MEC-21", "FAM-06", "Social insurance and pensions", "pension coverage and old-age poverty",
  r"pension|social insurance|social security (fund|scheme|system)|retirement|old-?age (income|security|benefit)|contributory",
  ["1.3", "10.4", "8.5"], ["AST-08"], [25, 23])
m("MEC-22", "FAM-06", "Shock-responsive protection", "speed and reach of support after shocks",
  r"shock-?responsive|adaptive social protection|emergency (cash|assistance|transfer)|disaster (relief|assistance) to households|crop insurance|livestock insurance|index insurance",
  ["1.5", "1.3", "13.1"], [], [24, 22])
m("MEC-23", "FAM-06", "Graduation from poverty", "sustained income gains of poor households",
  r"graduation|asset transfer|productive inclusion|economic inclusion|livelihood (program|support|grant)|ultra-?poor|poor household.*(asset|livestock|enterprise)",
  ["1.1", "1.2", "1.4"], [], [29])
m("MEC-24", "FAM-06", "Household food security and food prices", "food access and food price volatility for net buyers",
  r"food (security|access|price|reserve|stock|subsid|bank)|staple|rice (price|stock|subsid)|price stabili[sz]|strategic grain",
  ["2.1", "2.c", "1.2"], [], [53, 55])

# ---------------------------------------------------------------- FAM-07 Basic services and living conditions (CAP)
m("MEC-25", "FAM-07", "Water and sanitation", "household access to safe water and sanitation",
  r"drinking water|water supply|safe water|piped water|sanitation|toilet|latrine|sewer|hygiene|open defecation",
  ["6.1", "6.2", "3.9"], [], [60])
m("MEC-26", "FAM-07", "Household energy access", "household electrification and clean cooking",
  r"electrif|electricity access|household (energy|electricity)|clean cooking|cookstove|LPG|off-?grid|rural electr|energy access",
  ["7.1", "3.9"], [], [59, 61])
m("MEC-27", "FAM-07", "Housing and settlements", "share of households in adequate housing",
  r"housing|slum|informal settlement|shelter|home ownership|rental|dwelling",
  ["11.1", "1.4"], [], [62])

# ---------------------------------------------------------------- FAM-08 Climate mitigation and energy transition (FUT)
m("MEC-28", "FAM-08", "Carbon pricing and climate regulation", "emissions covered by a price or a binding cap",
  r"carbon (tax|pric|market|credit|trading)|emission(s)? trading|cap-?and-?trade|net[- ]zero|NDC|nationally determined|climate (law|act|governance|target)|greenhouse gas (target|reduction|inventory)|(climate|emission|GHG|greenhouse) mitigation|mitigation of (emission|greenhouse|climate)",
  ["13.2", "12.c", "9.4"], ["AST-07"], [68])
m("MEC-29", "FAM-08", "Clean energy and technology deployment", "share of renewable and low-carbon energy in supply",
  r"renewable|solar|wind (power|energy|farm)|hydro(power)?|geothermal|biomass|bio-?energy|nuclear|hydrogen|clean energy|low-?carbon (energy|power|technolog)|energy transition|electric vehicle|\bEVs?\b",
  ["7.2", "7.a", "7.b", "13.2"], ["AST-01", "AST-10"], [69, 70])
m("MEC-30", "FAM-08", "Energy efficiency", "energy intensity of output",
  r"energy (efficien|saving|conservation|intensity)|efficient (appliance|building|lighting)|building (code|standard)|demand-?side management",
  ["7.3", "12.2", "9.4"], [], [71])
m("MEC-31", "FAM-08", "Low-carbon infrastructure and avoiding lock-in", "emissions embedded in long-lived capital",
  r"low-?(carbon|emission) (transport|infrastructure|city|development|economy)|coal (phase|plant)|fossil fuel subsid|stranded|green (building|transport|infrastructure)|modal shift|mass transit for emission",
  ["9.4", "11.2", "13.2"], ["AST-06"], [72])

# ---------------------------------------------------------------- FAM-09 Natural capital and ecosystems (FUT)
m("MEC-32", "FAM-09", "Conservation and protected areas", "protected area coverage and species status",
  r"protected area|national park|biodiversity|wildlife|endangered|species|conservation area|habitat|invasive|biosecurity|wetland|coral|mangrove",
  ["15.1", "15.5", "14.5", "15.8"], ["AST-01", "AST-09"], [75, 79])
m("MEC-33", "FAM-09", "Sustainable use of forests, fisheries and land", "forest cover, fish stocks and soil condition",
  r"forest|deforest|reforest|afforest|logging|fish(ery|eries|ing) (management|quota|stock)|overfishing|sustainable (fish|forest|land|agricultur|use)|community forest|\bcatch (limit|share|quota)|land degradation|soil",
  ["15.2", "14.4", "15.3", "2.4"], ["AST-01"], [73, 74, 76, 77])
m("MEC-34", "FAM-09", "Restoration of degraded ecosystems", "area of degraded land and water restored",
  r"restor(e|ation|ing) (of )?(degraded|forest|mangrove|wetland|land|ecosystem|river|coral|habitat|watershed|soil|peat)|rehabilitat(e|ion of) (land|forest|ecosystem|mangrove|wetland|river)|degraded|reclamation|regreen|land neutrality",
  ["15.3", "15.1", "6.6", "14.2"], ["AST-01"], [78])
m("MEC-35", "FAM-09", "Water resources management", "water stress and reliability of supply",
  r"water (resource|management|allocation|security|scarcity|storage|basin|governance|pric|use efficien)|river basin|groundwater|aquifer|reservoir|\bdams?\b|irrigation water|transboundary|flood control reservoir|integrated water",
  ["6.4", "6.5", "6.6", "6.a"], ["AST-01"], [105, 106, 107, 108])

# ---------------------------------------------------------------- FAM-10 Pollution and a healthy environment (FUT)
m("MEC-36", "FAM-10", "Air, water and industrial pollution control", "pollutant concentrations and emissions per unit of output",
  r"pollut|emission standard|air quality|effluent|wastewater|discharge|industrial (waste|emission)|environmental (standard|compliance|impact assessment)|clean(er)? production|PM2|smog|haze",
  ["6.3", "11.6", "12.4", "9.4"], [], [80, 82])
m("MEC-37", "FAM-10", "Waste management and circular economy", "waste collected, treated and recovered",
  r"waste|recycl|circular|landfill|garbage|refuse|plastic|material recovery|composting|3R",
  ["12.5", "11.6", "12.4"], [], [83])
m("MEC-38", "FAM-10", "Protecting people from pollution exposure", "population exposed to unsafe air, water and toxins",
  r"exposure|toxic|\blead (poison|exposure|paint|contamin)|mercury|chemical (safety|management)|hazardous|asbestos|pesticide residue|environmental health|contaminat",
  ["3.9", "12.4", "6.3"], [], [81, 84])
m("MEC-39", "FAM-10", "Environmental behaviour and awareness", "environmentally relevant behaviour of households and firms",
  r"environmental (awareness|education|consciousness|behaviour|behavior)|public awareness|green (lifestyle|consumption)|sustainable consumption|eco-?label|(awareness|public|information) campaign",
  ["12.8", "4.7", "13.3"], [], [85])

# ---------------------------------------------------------------- FAM-11 Resilience to climate and disasters (FUT)
m("MEC-40", "FAM-11", "Risk-informed land use and settlement", "people and assets in hazard-prone locations",
  r"hazard (map|zon)|risk-?informed|flood ?plain|zoning|land-?use planning for risk|relocation from|risk assessment|vulnerab(le|ility) (area|map|assessment)|disaster risk reduction|DRR",
  ["11.b", "13.1", "1.5"], [], [86])
m("MEC-41", "FAM-11", "Resilient infrastructure and asset protection", "disruption losses when hazards strike",
  r"flood (protection|defence|defense|barrier|wall|control)|dyke|dike|embankment|sea ?wall|drainage|resilient infrastructure|climate-?proof|retrofit|hardened|coastal protection",
  ["9.1", "11.5", "13.1"], ["AST-06"], [87])
m("MEC-42", "FAM-11", "Nature-based protection", "ecosystem buffers in place against hazards",
  r"nature-?based|ecosystem-?based adaptation|mangrove (for|protect)|green infrastructure|natural (buffer|defence|defense)|watershed protection|sponge cit",
  ["13.1", "14.2", "15.1"], ["AST-01"], [88])
m("MEC-43", "FAM-11", "Climate-resilient livelihoods and adaptation", "losses avoided by adaptive practices and mobility",
  r"adaptation|climate-?resilien|climate-?smart|drought-?(tolerant|resistant)|resilient (agricultur|livelihood|communit)|climate (risk|change) (management|response)|\bheat ?(wave|stress|action)",
  ["13.1", "2.4", "1.5", "13.b"], [], [89, 90, 19])

# ---------------------------------------------------------------- FAM-12 Intergenerational balance (FUT)
m("MEC-44", "FAM-12", "Debt and fiscal sustainability", "public debt path and fiscal balance",
  r"public debt|debt (sustainab|management|ceiling|service)|fiscal (sustainab|rule|deficit|consolidation|discipline|framework|balance|space)|budget deficit|contingent liabilit|medium-?term fiscal",
  ["17.4", "17.1", "17.13"], ["AST-08"], [95, 96, 97, 98, 99])
m("MEC-45", "FAM-12", "Managing natural resource wealth", "resource rents saved or reinvested and revenue volatility",
  r"sovereign wealth|resource (revenue|rent|wealth|fund)|mining|mineral|oil and gas|petroleum|extractive|royalt|stabili[sz]ation fund|Dutch disease|hydrocarbon",
  ["12.2", "17.1", "8.4"], ["AST-01", "AST-08"], [91, 92, 93, 94])
m("MEC-46", "FAM-12", "Demographic change and ageing", "fertility, old-age dependency and lifecycle saving",
  r"\bageing\b|\baging\b|elderly|older (person|people|worker|adult)|senior citizen|fertility|birth rate|population (policy|ageing|aging|growth)|family planning|demographic|long-?term care|retirement age|dependency ratio",
  ["3.7", "1.3", "8.5", "5.4"], ["AST-03"], [100, 101, 102, 103, 104])

# ---------------------------------------------------------------- FAM-13 Productive transformation (EXP)
m("MEC-47", "FAM-13", "Industrial upgrading and diversification", "export complexity and productivity of traded sectors",
  r"diversif|upgrad|value[- ]added|high(er)?-?value|sophisticat|complex|new (industr|product)|export (basket|product|diversif)|productivity of (industr|manufactur)|move up the value chain|industrial (upgrading|transformation|restructur)",
  ["8.2", "9.2", "9.b", "17.11"], ["AST-05"], [109, 110, 111])
m("MEC-48", "FAM-13", "Industrial policy and priority sectors", "output and employment in targeted industries",
  r"priority (sector|industr)|target(ed)? (sector|industr)|strategic (sector|industr)|S-?curve|flagship industr|industrial (policy|development plan|strateg)|(national|industrial) champion|incentive(s)? for (industr|investment in)",
  ["9.2", "8.2", "9.3"], ["AST-05"], [112])
m("MEC-49", "FAM-13", "Modern services and the digital economy", "share of modern services and digital activity in output",
  r"digital (economy|platform|business|service industr|content)|service (sector|export|industr)|creative (econom|industr)|software|fintech|e-?commerce platform|data (centre|center) industry|outsourcing|financial (centre|center|hub)|modern services",
  ["8.2", "9.c", "8.3", "17.11"], ["AST-10"], [113])
m("MEC-50", "FAM-13", "Tourism", "tourism receipts, arrivals and local spillovers",
  r"touris|visitor|hospitality|destination|hotel|MICE|travel (industry|sector)|heritage site visit|wellness|cruise",
  ["8.9", "12.b", "14.7"], ["AST-09"], [125, 126, 127])

# ---------------------------------------------------------------- FAM-14 Integration into world markets (EXP)
m("MEC-51", "FAM-14", "Trade facilitation, logistics and standards", "trade costs, border times and standards compliance",
  r"trade facilitation|customs|single window|border (procedure|crossing|post)|logistic|freight|\bports?\b|shipping|cold chain|quality infrastructure|certification for export|SPS|standards? (complian|harmoni)|export procedure|\btransit\b",
  ["17.10", "9.1", "17.11", "8.a"], ["AST-02", "AST-06"], [114, 115, 116, 117])
m("MEC-52", "FAM-14", "Trade agreements and regional integration", "preferential market access and tariff levels",
  r"free trade agreement|FTA|trade agreement|regional (integration|economic community|cooperation)|ASEAN|RCEP|WTO|tariff|preferential|economic (partnership|diplomacy)|trade negotiation|market access abroad|bilateral",
  ["17.10", "17.12", "10.a", "17.11"], ["AST-02"], [118, 119, 120])
m("MEC-53", "FAM-14", "Foreign investment and global value chains", "FDI inflows and participation in global value chains",
  r"foreign (direct )?investment|FDI|inward investment|investment (promotion|climate|attraction|incentive|agency)|investor|global value chain|GVC|supply chain participation|multinational|joint venture",
  ["17.3", "17.5", "9.2", "10.b"], ["AST-05", "AST-02"], [121, 122, 123, 124])

# ---------------------------------------------------------------- FAM-15 Innovation and technology (EXP)
m("MEC-54", "FAM-15", "Research and development", "R&D spending and research output",
  r"research and development|R ?& ?D|R&D|basic research|science (and technology|park|fund)|research (fund|grant|institut|program|infrastructure)|laborator|innovation (fund|system|policy)|frontier|mission-?oriented",
  ["9.5", "9.b", "17.6"], ["AST-10", "AST-04"], [128, 133, 134])
m("MEC-55", "FAM-15", "Technology adoption and diffusion to firms", "share of firms using modern technology",
  r"technology (adoption|transfer|diffusion|upgrading|extension)|digital (transformation|adoption) of (firm|business|SME|industr)|industry 4\.0|automation|smart (factory|manufacturing|farm)|modernis(e|ation) of (production|equipment)|absorptive",
  ["9.5", "9.b", "8.2", "9.c"], ["AST-10"], [129, 130])
m("MEC-56", "FAM-15", "Knowledge transfer and intellectual property", "patents, licensing and university-industry links",
  r"intellectual property|patent|IP (right|protection|regime)|(technology|patent|IP) licens|commerciali[sz]|technology licensing|university-?industry|spin-?off|incubat|technology transfer office|knowledge transfer",
  ["9.5", "17.7", "9.b"], ["AST-10"], [131, 132])

# ---------------------------------------------------------------- FAM-16 Infrastructure networks (DOM)
m("MEC-57", "FAM-16", "Transport connectivity", "travel time and transport cost to markets",
  r"\broads?\b|highway|motorway|\brail(way)?s?\b|bridge|airport|aviation|transport (network|infrastructure|connectivity|corridor|system)|inland waterway|public transport|\bbus\b|\bmetro\b|connectivity between",
  ["9.1", "11.2", "9.a"], ["AST-06", "AST-02"], [135, 136, 137, 139])
m("MEC-58", "FAM-16", "Digital connectivity", "broadband coverage, use and price",
  r"broadband|internet|5G|4G|fibre|fiber|telecom|digital (infrastructure|connectivity|network|divide|access)|mobile (network|coverage)|spectrum|data centre|cloud infrastructure|e-?commerce (access|rural)",
  ["9.c", "17.8", "5.b"], ["AST-06", "AST-10"], [140, 141, 138])
m("MEC-59", "FAM-16", "Reliable and affordable utilities", "supply reliability, cost recovery and tariff structure",
  r"grid|transmission|power (supply|plant|generation|sector|shortage|outage|reliab)|electricity (supply|tariff|price|generation|market)|utility|utilities|energy (security|supply|infrastructure|market|pric|planning|regulator|storage|reserve)|tariff reform|energy subsid|fuel (price|subsid)|refiner|pipeline|LNG",
  ["7.1", "7.b", "9.1", "12.c"], ["AST-06", "AST-01"], [146, 147, 148, 149, 150])

# ---------------------------------------------------------------- FAM-17 Cities, regions and spatial development (DOM)
m("MEC-60", "FAM-17", "Urban productivity, planning and housing supply", "urban density, congestion and housing affordability",
  r"urban (plan|development|renewal|expansion|infrastructure|transport|mobility|management|governance|design)|\bcit(y|ies)\b|metropolitan|smart city|land-?use plan|master plan|zoning|congestion|housing (supply|market|polic)|real estate|town",
  ["11.3", "11.1", "11.2", "11.a"], ["AST-06"], [142, 143, 144, 145])
m("MEC-61", "FAM-17", "Clusters, zones and local supply chains", "domestic value added and linkages between firms",
  r"cluster|industrial (zone|estate|park|area)|special economic zone|SEZ|economic corridor|EEC|eastern economic|agro-?(industr|processing)|value chain|local content|linkage|supplier development|supply chain (within|domestic|local)|processing (industr|plant)|food (processing|loss|waste)|post-?harvest",
  ["9.2", "9.3", "8.2", "12.3", "2.3"], ["AST-05", "AST-01"], [151, 152, 153, 154, 57])
m("MEC-62", "FAM-17", "Lagging regions and place-based development", "income gap between leading and lagging regions",
  r"region(al)? (disparit|development|inequalit|gap|econom)|lagging|backward (area|region)|remote area|border (area|province)|rural (development|econom|area|non-?farm)|spatial|territorial|decentrali[sz]ed growth|secondary cit|provincial (development|econom)|special (region|area) development|disadvantaged area",
  ["10.1", "11.a", "1.4", "8.3"], ["AST-02"], [185, 186, 188])

# ---------------------------------------------------------------- FAM-18 Farmers and small enterprises (GTI)
m("MEC-63", "FAM-18", "Agricultural productivity and inputs", "yields and output per worker in farming, fishing and livestock",
  r"agricultur|farm|crop|yield|seed|fertili[sz]er|irrigat|livestock|dairy|poultry|aquaculture|fisher|harvest|extension service|agronom|mechani[sz]ation|pest|animal (health|disease)|veterinar|plantation|rubber|palm|sugar|rice (production|yield|farm)",
  ["2.3", "2.4", "2.a", "2.5"], ["AST-01", "AST-03"], [158, 159, 160, 161, 162, 163])
m("MEC-64", "FAM-18", "Market access for small producers", "share of output sold and prices received by small producers",
  r"market access for (farmer|producer|smallholder)|farmer (group|organi[sz]ation|cooperative|market)|cooperative|collective marketing|contract farming|producer (organi[sz]ation|price|group)|smallholder|community enterprise|OTOP|local product|farm-?gate|farmers'? market|middlemen",
  ["2.3", "2.c", "8.3", "9.3"], [], [155, 156, 157])
m("MEC-65", "FAM-18", "Firm capability and entrepreneurship", "productivity, survival and growth of small firms",
  r"\bM?SMEs?\b|small (and medium )?(business|enterprise|firm)|micro-?enterprise|entrepreneur|start-?up|business (development|incubat|advisory|support service|registration|formali[sz]ation)|management (training|practice|capability)|informal (business|enterprise|sector) formali[sz]|OTOP|community business|social enterprise",
  ["8.3", "9.3", "8.5"], ["AST-05"], [164, 166, 167])

# ---------------------------------------------------------------- FAM-19 Jobs and labour markets (GTI)
m("MEC-66", "FAM-19", "Job matching and active labour-market programmes", "unemployment duration and match quality",
  r"employment (service|promotion|creation|program|office|agency)|job (creation|placement|matching|centre|center|seeker|fair|search)|labour market information|public employment|unemploy|active labour|career (guidance|counsel)|work(force)? placement|internship|hiring incentive",
  ["8.5", "8.6", "8.b"], ["AST-03"], [176, 177])
m("MEC-67", "FAM-19", "Labour regulation and firm formalisation", "formal employment share and labour-cost structure",
  r"labour (law|code|regulation|market (regulation|reform|flexib)|cost)|employment protection|minimum wage|wage (floor|polic|setting)|severance|formal(i[sz]ation of (business|enterprise|firm|employment)|employment|sector)|hiring (rule|regulation)|labour (market )?institution",
  ["8.5", "8.3", "10.4"], [], [178, 179, 180])
m("MEC-68", "FAM-19", "Adjustment to trade and technology shocks", "re-employment of displaced workers and wage recovery",
  r"displaced worker|job loss|retrench|laid off|layoff|just transition|adjustment (assistance|program|support)|affected (worker|communit|industr)|transition (support|assistance) for workers|automation.*(worker|job)|redeploy|economic (restructuring|transition) (support|assistance)",
  ["8.5", "8.8", "10.1", "13.b"], [], [183, 184, 187])
m("MEC-69", "FAM-19", "Migration and remittances", "migrant earnings, remittances and skill flows",
  r"migrant|migration|remittance|diaspora|overseas (worker|employment|Thai|Filipino|citizen)|labour (export|mobility|migration)|brain (drain|gain)|return(ing)? migra|returnee|expatriate|foreign worker|work permit|guest worker",
  ["10.7", "10.c", "8.8", "17.3"], ["AST-04"], [189, 190, 191, 192, 193])

# ---------------------------------------------------------------- FAM-20 Markets, finance and property rights (GTI)
m("MEC-70", "FAM-20", "Competition, business regulation and contract enforcement", "entry costs, market concentration and contract enforcement times",
  r"competition (law|polic|commission|authorit)|anti-?trust|monopol|ease of doing business|doing business|business (environment|climate|regulat|licens|registration|law)|regulatory (reform|burden|simplif|guillotine|impact)|red tape|one-?stop|contract enforcement|commercial court|insolvency|bankruptcy|state-?owned enterprise reform|SOE reform|privati[sz]|corporate governance|consumer protection",
  ["8.3", "16.6", "9.3", "10.5"], ["AST-07"], [168, 169, 170, 171])
m("MEC-71", "FAM-20", "Access to finance", "credit to firms and households, savings and payment use",
  r"financ(e|ial) (access|inclusion|literacy|service|sector|deepening|market|institution|system)|\bcredit|\bloans?\b|microfinance|microcredit|guarantee|collateral|savings|banking|\bbanks?\b|capital market|stock (market|exchange)|bond market|venture capital|digital (payment|finance|banking)|mobile money|fintech|insurance (market|penetration)|leasing|factoring|credit bureau",
  ["8.10", "9.3", "8.3", "1.4"], ["AST-08"], [172, 173, 174, 175, 165])
m("MEC-72", "FAM-20", "Land and property rights", "tenure security and land-market functioning",
  r"land (right|titl|tenure|registr|administration|reform|redistribution|market|bank|allocation|use right|ownership|cadastr|dispute|governance|polic)|property right|cadastr|title deed|land (and|&) property|agrarian reform|communal land|customary (land|tenure)|land for (farmer|poor|landless)",
  ["1.4", "5.a", "2.3", "16.3"], ["AST-01", "AST-07"], [194, 195, 196, 197])

# ---------------------------------------------------------------- FAM-21 Foresight, data and early warning (ANT)
m("MEC-73", "FAM-21", "Early warning and surveillance", "warning lead time and outbreak detection speed",
  r"early warning|surveillance|monitoring (system|network) for (hazard|disease|disaster|weather|flood)|forecast|meteorolog|hydrolog|seismic|disease (surveillance|detection|intelligence)|one health|zoonotic|epidemic intelligence|alert system|siren",
  ["13.3", "3.d", "11.b", "13.1"], ["AST-10"], [206, 207, 208])
m("MEC-74", "FAM-21", "Statistics, evidence and planning", "statistical capacity and use of evidence in planning",
  r"statistic|census|data (system|collection|infrastructure|governance for planning|platform for planning)|national (planning|development planning)|planning (system|process|capacity|framework)|scenario|foresight|horizon scanning|strategic (plan|foresight)|evidence-?based|indicator (system|framework)|big data for (planning|polic)|SDG (mainstream|integration|localization)|M&E system for the plan",
  ["17.18", "17.19", "17.14", "16.6"], ["AST-07", "AST-10"], [210, 211, 212])
m("MEC-75", "FAM-21", "Pre-arranged risk finance", "disaster finance arranged before the event",
  r"disaster (risk )?financ|contingen(cy|t) (fund|financ|credit|budget)|catastrophe (bond|insurance|fund)|risk (pool|financ|transfer)|calamity fund|emergency (fund|reserve) (established|set up)|insurance for disaster|sovereign insurance",
  ["1.5", "11.5", "13.1", "17.3"], ["AST-08"], [209])

# ---------------------------------------------------------------- FAM-22 Economic resilience to external shocks (ANT)
m("MEC-76", "FAM-22", "Macro-financial buffers", "reserves, exchange-rate flexibility and banking soundness",
  r"macro-?economic (stabilit|management|polic|framework|resilience)|monetary polic|inflation (target|control)|exchange rate|foreign (exchange|reserve)|international reserve|balance of payment|current account|financial (stabilit|regulat|supervis|crisis|soundness)|banking (supervision|stabilit|regulation|resilien)|capital (flow|control|adequacy)|external (debt|shock|vulnerab)|macro-?prudential|central bank",
  ["17.13", "10.5", "8.1", "17.4"], ["AST-08", "AST-07"], [198, 199, 200, 201])
m("MEC-77", "FAM-22", "Supply-chain and economic security", "import concentration and critical-input stocks",
  r"supply chain (resilien|security|diversif|disruption|risk)|economic security|strategic (reserve|stock|stockpile|industr|autonomy|sector)|critical (input|mineral|infrastructure|supply|technolog)|import (dependen|substitut|diversif)|self-?sufficien|self-?relian|food (self|sovereignty)|energy independence|national security of supply|de-?risk|friend-?shoring|reshor",
  ["17.13", "12.2", "2.c", "9.1"], ["AST-05", "AST-01"], [202, 203, 204, 205])

# ---------------------------------------------------------------- FAM-23 Rule of law and checks on power (ADA)
m("MEC-78", "FAM-23", "Judicial independence and review", "independence and reach of judicial review",
  r"judicial (independence|review|reform)|independent judiciary|constitutional (court|review)|administrative court|rule of law|separation of powers|judiciary|supreme court|legal (certainty|system reform)",
  ["16.3", "16.6", "16.10"], ["AST-07"], [213])
m("MEC-79", "FAM-23", "Legislative oversight and audit", "detection of misconduct by audit and oversight bodies",
  r"audit|parliament(ary)? (oversight|scrutiny|committee)|legislat(ive|ure) (oversight|strengthen|capacity)|oversight (body|mechanism|institution)|anti-?corruption|corruption|integrity|ombudsman|inspector|accountab(le|ility) (institution|mechanism|body)|asset declaration|whistle-?blow|public (sector )?integrity",
  ["16.5", "16.6", "16.a"], ["AST-07"], [214, 215])
m("MEC-80", "FAM-23", "Guarding against erosion of accountability", "constraints on the executive over time",
  r"constitution(al)? (reform|amendment|order|guarantee)|democratic (institution|governance|consolidation|principle)|checks and balances|term limit|executive (power|accountability|overreach)|human rights (commission|protection|institution)|civil (libert|right)|fundamental (right|freedom)|security sector (reform|oversight|governance)|civilian (control|oversight)",
  ["16.6", "16.10", "16.3", "16.b"], ["AST-07"], [216])

# ---------------------------------------------------------------- FAM-24 Adaptive and learning government (ADA)
m("MEC-81", "FAM-24", "Monitoring, evaluation and course correction", "use of monitoring and evaluation to revise programmes",
  r"monitoring and evaluation|M&E|evaluat|performance (monitoring|management|measurement|indicator|review|based)|KPI|results-?based|review (mechanism|cycle|of the plan)|feedback|pilot|experiment|sandbox|test(ing)? (polic|approach)|iterative|adaptive (management|governance|polic)|lessons? learn|course correction|midterm review|learning (organisation|organization|government)",
  ["16.6", "17.14", "17.18"], ["AST-07"], [217, 218, 219])
m("MEC-82", "FAM-24", "Whole-of-government coordination", "coherence of policy across agencies and levels",
  r"coordinat(ion|e|ing) (mechanism|among|between|across|committee|body|platform|of (agenc|ministr|polic|sector))|whole-?of-?government|inter-?(ministerial|agency|sectoral|governmental)|cross-?(sectoral|agency|ministerial|cutting) (mechanism|coordination|committee|platform|integration)|integrated (planning|approach|polic|delivery)|policy coherence|joint (committee|working|mechanism)|national committee on|alignment (of|between|across) (polic|plan|agenc|ministr)|mainstream",
  ["17.14", "16.6", "16.7"], ["AST-07"], [220])
m("MEC-83", "FAM-24", "Keeping laws and regulation up to date", "fit between the rule book and technology and markets",
  r"data (protection|privacy|governance|law|sovereignty)|personal data|privacy|cyber|cybersecurity|digital (law|regulation|governance|right|identity law|platform regulation)|platform (regulation|accountabil)|AI (governance|ethic|regulation|law)|artificial intelligence (governance|ethic|regulation|law|polic|strateg)|algorithm|regulatory (update|modernis|sandbox|framework for (digital|new technolog|emerging))|legal (framework|reform) for (digital|technolog|data|AI)|law(s)? (revision|modernis|update|amendment)|outdated (law|regulation)|legislat(ive|ion) (reform|modernis|update|review)|regulatory quality|better regulation|modernise legislation",
  ["16.10", "9.c", "16.6", "17.6"], ["AST-10", "AST-07"], [221, 222, 223, 224])

# ---------------------------------------------------------------- FAM-25 State capability and service delivery (AGI)
m("MEC-84", "FAM-25", "Civil service and public management", "quality, motivation and management of public servants",
  r"civil servi|civil servant|public (servant|administration|sector (reform|management|capacity|personnel|workforce|efficiency)|management|service (reform|delivery|quality|standard)|official|personnel|employee|agency (reform|restructur|capacity))|bureaucra|government (official|personnel|agenc(y|ies) (capacity|reform|restructur)|efficiency|workforce|restructur|reform)|human resource (management|development) (in|of) (government|the public|the civil)|institutional (capacity|reform|strengthen|development)|administrative (reform|capacity|efficiency|procedure|burden)|merit|HRM|organi[sz]ational (reform|restructur|development) of (government|public)|implementation capacity|plan implementation",
  ["16.6", "16.7", "17.9"], ["AST-07"], [225, 226, 228])
m("MEC-85", "FAM-25", "Digital government", "share of public services delivered digitally and leakage",
  r"e-?government|digital government|government (digital|data|platform|service(s)? online|cloud|app|portal|website|system)|online (service|platform|portal|system|registration|application|payment)|digital (public )?service|digital (ID|identity|signature|document|wallet|platform for (government|public|citizen))|one-?stop (digital|online|service)|\be-?(service|office|payment|procurement|licens|tax|filing|health record|document|registration|voting|court|budget|signature|invoice|portal|ID|KYC)\b|GovTech|paperless|data (sharing|exchange|interoperab|link) (between|across|among) (agenc|government|ministr)|interoperab|back-?office system|information system for (public|government|agency|the ministry|health|education|land|tax|social)|register(s)? (digiti|moderni|link|integrat)|national (data|digital) (platform|infrastructure|portal|ID)|big data (platform|centre|center|for government)|automat(ed|ion of) (service|process|procedure|workflow)|digitali[sz](e|ation|ing) (of )?(public|government|administrative|service|process|procedure|record|document|work)|digital transformation (of|in) (government|public|the public|agenc|ministr|administration)|smart government",
  ["16.6", "9.c", "16.9", "17.8"], ["AST-10", "AST-07"], [227])
m("MEC-86", "FAM-25", "Decentralisation and local government", "capacity, resources and accountability of local governments",
  r"decentrali[sz]|devolution|local (government|authorit|administration|council|governance|fiscal|revenue|budget|capacity|tax|autonom|administrative organi[sz]ation)|sub-?national|municipal (government|council|administration|finance|capacity)|provincial (administration|government|council|budget|capacity)|district (administration|council|government|office)|tambon|village (fund|committee)|intergovernmental (transfer|fiscal)|fiscal (transfer|decentrali[sz]ation|federalism|equali[sz]ation)|grant(s)? to local|local (service|public service) delivery|area-?based (administration|development|governance)|regional (administration|office|governance|government)",
  ["16.6", "16.7", "11.3", "17.1"], ["AST-07"], [229, 230, 231])
m("MEC-87", "FAM-25", "Regulation and enforcement capacity", "capacity and independence of regulators and inspectorates",
  r"regulator(y)? (agenc|authorit|bod|capacit|institution|independence|enforcement|oversight|commission)|regulatory (and supervisory|enforcement|compliance|capacity)|inspection|inspectorate|enforcement (capacity|of (environmental|safety|standard|regulation|law))|complian(ce|t) (monitoring|enforcement|system|inspection)|licensing (authorit|bod|system|regime|enforcement)|safety (regulation|authorit|oversight|inspection|standard enforcement)|environmental (enforcement|inspection|compliance|regulator|governance)|nuclear (safety|regulat)|radiation|food (safety )?(regulator|inspection|control authority)|drug (regulator|regulation|authorit|control)|market (surveillance|supervision|oversight)|quality (control|assurance|inspection) (system|authorit|agency)|standards? (bod|agenc|authorit|enforcement|institution|regime)|sector regulat",
  ["16.6", "12.4", "9.4", "3.9"], ["AST-07"], [240, 241])

# ---------------------------------------------------------------- FAM-26 Public finances (AGI)
m("MEC-88", "FAM-26", "Tax revenue and administration", "tax revenue to GDP and compliance",
  r"\btax(es|ation|payer|pay|base|rate|polic|reform|revenue|administration|collection|compliance|system|exemption|incentive|holiday|evasion|avoidance|gap|authorit|code|law|audit|regime|structure|effort|measure|burden|relief|credit|deduction)|revenue (mobili[sz]|collection|administration|authorit|measure|polic|reform|enhancement|generation|base|source|performance|target|effort|agency|department)|domestic resource|fiscal (revenue|capacity|incentive)|customs (revenue|dut)|excise|\bVAT\b|value-?added tax|income tax|property tax|land tax|wealth tax|carbon tax|(customs|import|export|excise) dut(y|ies)|levy|levies|royalt|non-?tax revenue|fee(s)? (collection|reform|structure|revenue|for service)|user (charge|fee)|cost recovery|revenue sharing|fiscal (contract|bargain)|taxpayer (service|registration|compliance|education)|informal (sector|economy) tax|broaden(ing)? the (tax )?base",
  ["17.1", "10.4", "16.6", "17.13"], ["AST-07"], [232, 233, 234])
m("MEC-89", "FAM-26", "Budgeting, procurement and public investment", "budget credibility, procurement value and investment efficiency",
  r"budget(ing|ary)? (process|reform|execution|credibility|transparen|system|allocation|framework|discipline|performance|law|management|planning|monitoring|efficiency|institution|rule)|public (financial management|expenditure|spending|investment (management|efficiency|planning|appraisal|pipeline)|procurement|asset management|finance management)|PFM|PIM|procurement|expenditure (review|efficiency|management|control|prioriti|rationali|quality|tracking)|spending (efficiency|review|quality|prioriti|control)|medium-?term (expenditure|budget) framework|MTEF|performance-?based budget|program(me)? budget|results-?based budget|fiscal (transparen|reporting|accountab)|treasury|cash management|FMIS|IFMIS|IPSAS|aid (effectiveness|coordination|management)|development (finance|assistance|partner) (coordination|management|effectiveness|alignment|mobili[sz]ation)|donor (coordination|harmoni|alignment)|ODA|official development assistance|financing (the plan|of the plan|framework|gap)|project (appraisal|selection|prioriti|pipeline|preparation) (of|for) (public|infrastructure|capital)|capital (budget|expenditure|spending|investment program)|infrastructure (financ|fund|investment plan|pipeline)|public asset|state asset|value for money|absorption (capacity|rate)|execution rate|off-?budget|extra-?budgetary",
  ["16.6", "17.1", "9.1", "16.5"], ["AST-07"], [235, 236, 237, 239])
m("MEC-90", "FAM-26", "Public-private partnerships", "private finance mobilised and fiscal risk from PPPs",
  r"public-?private partnership|PPP|private (sector )?(participation|financ(e|ing)|investment) in (infrastructure|public|service|utilit|transport|energy|water|health|education|housing)|concession|build-?operate|BOT|availability payment|viability gap|blended financ|contracting out|private (provision|provider|operator|management) of (public|service|infrastructure|utilit|hospital|school|water|transport)|management contract|asset recycling|land value capture|toll",
  ["17.17", "9.1", "17.3", "17.5"], ["AST-08", "AST-06"], [238])

# ---------------------------------------------------------------- FAM-27 Emergency response and recovery (AGI)
m("MEC-91", "FAM-27", "Preparedness, surge capacity and stockpiles", "stocks, surge capacity and readiness before a shock",
  r"preparedness|emergency (plan|planning|operation|management|response (capacity|plan|system|team|readiness|framework|mechanism|coordination|protocol|training|drill|exercise|stockpile|supplies))|contingency plan|stockpile|strategic (stock|reserve) of (medic|vaccine|PPE|food|fuel|equipment)|surge (capacity|staff|bed)|disaster (management|preparedness|response (capacity|plan|system|team|readiness)|agency|law)|civil (defence|defense|protection)|rescue|fire (service|brigade|fighting)|ambulance|emergency medical|first responder|incident (command|management)|rapid response|readiness|drill|simulation exercise|evacuation (plan|route|centre|center|shelter)|business continuity|continuity of (government|operation)|pandemic (preparedness|plan|readiness)|International Health Regulations|IHR|health (security|emergency) (preparedness|capacit|plan|framework|system|law|governance|workforce|financing|operation)|laboratory (capacity|network|biosafety)|biosafety|public health emergency|health emergency",
  ["3.d", "11.5", "13.1", "1.5"], ["AST-07"], [242])
m("MEC-92", "FAM-27", "Emergency relief and service continuity", "speed of relief and services kept running in a shock",
  r"relief|humanitarian|emergency (assistance|aid|support|supplies|food|shelter|cash)|disaster (relief|assistance|victim|affected|compensation)|affected (people|household|population|communit|famil) (support|assistance|compensation)|victim(s)? (support|assistance|compensation)|evacuee|compensation (for|to) (disaster|flood|affected|victim|damage|loss)|service continuity|continuity of (education|learning|health|care|essential|service|public|school|treatment|supply)|school (closure|reopening)|lockdown|quarantine|isolation (facilit|centre|center|ward)|field hospital|temporary (hospital|shelter|housing|accommodation|school|clinic)|psychosocial|mental health (support|service) (for|after|during) (disaster|emergenc|crisis|pandemic|outbreak|flood)",
  ["1.5", "11.5", "2.1", "3.d"], ["AST-07"], [243, 244])
m("MEC-93", "FAM-27", "Recovery and reconstruction", "speed and quality of rebuilding after a shock",
  r"reconstruct|rebuild|build back better|recovery (plan|program|fund|framework|strateg|phase|package|financ|and reconstruction|and rehabilitation|from (the )?(disaster|flood|pandemic|crisis|covid|earthquake|storm|tsunami|outbreak|shock))|post-?(disaster|flood|crisis|pandemic|covid|earthquake|tsunami|outbreak|conflict) (recovery|reconstruction|rehabilitation|rebuilding|restoration|economic recovery|stimulus)|stimulus|economic (recovery|revival|revitali[sz]ation) (plan|program|programme|package|measure|fund|strateg)|resilient (recovery|reconstruction|rebuilding)|rehabilitat(e|ion of) (damaged|destroyed|affected|disaster|flood)|damage (assessment|and loss|and needs)|loss and damage|PDNA|post-?disaster needs|repair of (damaged|destroyed|affected|flood)|new normal|post-?covid|post-?pandemic",
  ["11.5", "9.1", "1.5", "11.b"], ["AST-06"], [245])

# ---------------------------------------------------------------- FAM-28 Voice, participation and accountability (REF)
m("MEC-94", "FAM-28", "Citizen participation and community-driven development", "citizen involvement in decisions and community monitoring",
  r"(citizen|public|communit|people|civic|local|popular|stakeholder|youth|women).{0,14}participat|participatory|community-?(driven|based|led) (development|planning|management|monitoring|initiative|project|program|programme|approach|organi[sz]ation|fund|forum)|citizen (engagement|participation|involvement|voice|feedback|consultation|forum|panel|assembly|budget|monitoring|oversight|report card|scorecard|charter|complaint|grievance)|public (participation|consultation|hearing|engagement|involvement|forum|dialogue|deliberation|feedback|complaint|grievance)|civic (engagement|participation|education|space|action|tech)|community (participation|engagement|involvement|voice|consultation|forum|assembly|council|committee|organi[sz]ation|empowerment|ownership|mobili[sz]ation|development plan|monitoring|oversight|scorecard|audit|self-?(governance|management|help|reliance))|village (meeting|assembly|council|committee|fund|plan|development plan)|grassroots|bottom-?up|co-?(creat|design|produc|manag)|empower(ment|ing)? (of )?(communit|citizen|people|local|village|grassroots|civil society|women|youth|poor|vulnerable|marginali[sz]ed|indigenous|ethnic|disab|elderly|farmer|fisher|worker|informal)|social (accountability|audit|contract|mobili[sz]ation|movement)|volunteer|NGO|civil society|CSO|community organi[sz]ation|CBO|people's organi[sz]ation|self-?help group|savings group|village (bank|savings|credit|revolving fund)|community (bank|fund|savings|revolving fund|forest|fisher|rights|tenure|consent|FPIC)|youth (participation|engagement|council|parliament|assembly|forum|network|leadership|empowerment)|women's (participation|group|organi[sz]ation|network|movement|leadership|empowerment|collective|self-?help)",
  ["16.7", "16.6", "11.3", "17.17"], ["AST-07"], [246, 247, 248, 249])
m("MEC-95", "FAM-28", "Transparency, media and information integrity", "access to information, media freedom and disinformation",
  r"transparen|open (data|government|budget|contracting)|freedom of information|right to information|access to (public )?information|information (disclosure|integrity|access|law|act|literacy)|disclos|media (freedom|independence|pluralism|literacy|sector|development|regulation|law|reform|professionalism|ethic|standard|council|ownership|industry)|press (freedom|law|council)|journalis|broadcast|public (service )?(broadcast|media)|disinformation|misinformation|fake news|fact-?check|propaganda|hate speech|whistle|beneficial owner|asset declaration|lobby|conflict of interest|citizen (monitoring|oversight|report card|scorecard)|public (monitoring|oversight|scrutiny|reporting|accountability)|accountab(le|ility) to (citizen|the public|people|parliament|voter)",
  ["16.10", "16.6", "16.5", "9.c"], ["AST-07", "AST-10"], [250, 251, 252])
m("MEC-96", "FAM-28", "Elections and political institutions", "electoral integrity, competition and party institutionalisation",
  r"elect(ion|oral)|vot(er|ing)|ballot|referendum|political (part|competition|pluralism|reform|institution|system|process|participation|representation|financ|fund|campaign|stability|settlement|transition|dialogue)|parliament(ary)? (reform|strengthen|capacity|development|modernis|democracy|system|procedure|committee|secretariat|research|outreach)|party (system|law|registration|financ|institutionali|development|reform|regulation|competition)|multi-?party|democra(cy|tic|tisation|tization)|good governance|constitution(al)? (drafting|making|reform|amendment|revision|review|convention|assembly|referendum|order|democracy|monarchy|principle|provision|framework|design)",
  ["16.7", "16.6", "5.5", "16.10"], ["AST-07"], [253, 254, 255])
m("MEC-97", "FAM-28", "Reform coalitions and social dialogue", "breadth of the coalition behind reform and institutional trust",
  r"coalition|social (dialogue|partner|pact|compact|contract|consensus|agreement|accord)|tripartite|collective bargaining|wage (bargaining|negotiation|council|board|committee)|employer(s'|s)? (organi[sz]ation|association|federation|confederation|council)|trade union|labour union|public-?private (dialogue|consultation|forum|council|committee|platform|collaboration|cooperation|coordination|engagement|working group|task force|network)|business (association|chamber|council|forum|roundtable|dialogue|consultation)|chamber of commerce|industry (association|federation|council|forum|dialogue|consultation)|stakeholder (dialogue|consultation|engagement|participation|forum|platform|council|committee|network|alliance|partnership|collaboration|buy-?in|ownership|consensus)|multi-?stakeholder|collaborat(e|ion|ive) (with|between|among|across|governance|leadership|platform|network|mechanism|framework)|consensus|buy-?in|ownership of (reform|the plan|development|polic|change)|political (will|commitment|support|ownership|leadership|consensus|coalition|settlement|pact|economy of reform|feasibility)|reform (coalition|champion|leader|leadership|momentum|window|agenda|sequencing|delivery unit)|change (management|leadership|agent|champion|coalition)|trust in (government|institution|the state|public institution)|institutional trust|public trust|confidence in (government|institution|the state|public|democracy)|legitimacy|populis|anti-?(establishment|elite|system|politic|government|institution)|disenchantment|disillusion|disaffection",
  ["16.7", "8.8", "17.17", "16.6"], ["AST-07"], [256, 257, 258])

MECHANISMS = M
