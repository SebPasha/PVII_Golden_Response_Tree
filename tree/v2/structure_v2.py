"""Mother tree v2, hand-written source: family (L1) -> mechanism (L2) -> pathway (L3).

The pathways are the 259 v1 mechanisms with their frozen ids (tree/v1/ids.json); their causal
input, transmission, outcome, evidence, risk tags and text cues are read from tree/v1/mechanisms.csv
by build.py and are not repeated here. Everything new in v2 is in this file:

- FAMILIES: 28 families, each with one primary RHDR subpillar and the clause of the amended RHDR
  definition it rests on, so a placement can be checked against the RHDR text.
- MECHANISMS: 99 mechanisms (levers in plan-chapter language), each with the intermediate variable
  it is meant to move, the plan words that mark it, its SDG targets, and the asset classes it
  mobilises. Risk tags roll up from the pathways in build.py.
- MERGES: the seven pathway merges agreed on 28 October 2026; a merged id is kept, flagged, and
  its strategies count on the surviving pathway.
- OLD_FAMILY_DEFAULT: the v2 family for a strategy that v1 held at a family (L2-xx) and nothing deeper.
- SUBPILLARS: the amended RHDR definitions, verbatim.
- TARGET_CLASSES and INSTRUMENT_CLASSES: the roll-ups used for comparison.
- ASSETS: the ten asset classes and the literature that makes each an asset.

Decisions applied (Sebastian, 28 October 2026, "go with recommended"): 28 families; Safety from
violence and exploitation under Enhancing Capabilities; worker formalisation split off to Tackling
Structural Exclusion (new mechanism MEC-99); food and nutrition split across families; water a
mechanism of Natural capital; debt under Intergenerational balance; tourism a mechanism of
Productive transformation; the value-chain rule (producer to GTI, chain to DOM, so pathway 057 moves
to Clusters, zones and local supply chains).
"""

PILLARS = [("PFA", "People-first Approach"), ("SMG", "Smarter Growth"), ("MCH", "Making Change Happen")]

# code, pillar, name, amended RHDR definition (verbatim from the framework amendments, October 2026)
SUBPILLARS = [
 ("TSE", "PFA", "Tackling Structural Exclusion",
  "Covers strategies that address the exclusion of specific groups, including women, youth, informal workers, persons with disabilities, and marginalized communities, as well as the structural barriers that limit their opportunities, such as discrimination, unequal access to services and resources, limited voice and participation, and lack of protection of rights and dignity. Formalisation of informal workers belongs here, including registration, labour contracts, labour rights, and social insurance or pension coverage."),
 ("CAP", "PFA", "Enhancing Capabilities",
  "Covers strategies that expand people's capabilities to lead healthy, productive, and resilient lives, including through education, skills, digital access, health, social protection, food security, livelihoods, and basic services. This category is intentionally broad enough to include areas that may otherwise fall under 'human security,' avoiding an artificial distinction between capability-building and protection from vulnerability."),
 ("FUT", "PFA", "Future Generations",
  "Covers whether today's strategies protect long-term well-being and avoid shifting risks or costs onto future generations, including through climate resilience, just transition, nature and biodiversity, sustainable resource use, intergenerational equity and responsible public finance."),
 ("EXP", "SMG", "Export-led",
  "Covers strategies that grow the economy through external markets, including export promotion and diversification, trade agreements and market access, foreign direct investment, international tourism, trade logistics, and the innovation and technology upgrading that make traded sectors competitive."),
 ("DOM", "SMG", "Domestic Integration",
  "Covers strategies that strengthen links within the domestic economy, including local value chains and value addition, agro-processing, industrial clusters, and connections between regions and between rural and urban markets."),
 ("GTI", "SMG", "Growth through Inclusion",
  "Covers strategies that create jobs and incomes for groups left out of growth, including women, youth, informal workers and rural households, through enterprise development, MSME support, productivity, finance and market access. Formalisation of informal businesses belongs here, including registration, licensing, and access to finance and markets."),
 ("ANT", "MCH", "Anticipation and Strategic Foresight",
  "Focuses on the ability of governments to identify and prepare for future risks, opportunities and disruptions, including through horizon scanning, scenario planning, early warning, contingency planning, risk-informed analysis, and future-oriented strategy."),
 ("ADA", "MCH", "Adaptability and Course Correction",
  "Refers to the capacity to adjust priorities, policies, plans, and investments in response to new evidence, changing conditions or shifting development needs. This includes institutional flexibility, learning by doing, revising strategies, and making timely course corrections."),
 ("AGI", "MCH", "Agility and Delivery Capability",
  "Captures the ability of institutions to act quickly and effectively, mobilize resources, coordinate across government, implement reforms and respond to shocks or emerging priorities without major disruption."),
 ("REF", "MCH", "Reform Leadership, Coalitions and Civic Engagement",
  "Covers strategies that build the political, institutional, and social support needed to advance reform, including political will, reform incentives, collaborative leadership, coalitions, public-private collaboration, civic participation, and co-creation."),
]

# Holding branches are unchanged from v1 (no literature levels, dropped from reporting).
HOLDING = [("H-SPE", "Standard People"), ("H-SEC", "Standard Economy"), ("H-SGO", "Standard Governance"),
           ("H-GOAL", "Goals held outside the tree")]

# id, subpillar, name, one-line meaning, anchor literature, RHDR clause the placement rests on
FAMILIES = [
 ("FAM-01", "TSE", "Equal rights and inclusion", "Removing the barriers that hold people back because of the group they belong to.",
  "World Bank 2013 Inclusion Matters; Becker 1957 and Phelps 1972 on discrimination; Stewart 2008 on horizontal inequalities; Duflo 2012 on women's empowerment",
  "exclusion of specific groups, including women, youth, informal workers, persons with disabilities, and marginalized communities ... discrimination, unequal access to services and resources, limited voice and participation, and lack of protection of rights and dignity"),
 ("FAM-02", "CAP", "Safety from violence and exploitation", "Keeping people safe from violence, abuse and crime at home, at work and in public.",
  "Becker 1968 on the economics of crime; World Bank WDR 2011 Conflict, Security and Development; Heckman and Cunha on early adversity; Abramsky et al. 2014 and Jewkes 2002 on violence against women",
  "intentionally broad enough to include areas that may otherwise fall under 'human security,' avoiding an artificial distinction between capability-building and protection from vulnerability"),
 ("FAM-03", "TSE", "Social cohesion and peace", "Trust between groups, a shared identity, and recovery from conflict and displacement.",
  "Stewart 2008; Esteban and Ray 2011 on polarisation and conflict; Allport 1954 and Paluck, Green and Green 2019 on contact; Collier and Hoeffler 2004; Cernea 1997 on displacement",
  "marginalized communities, as well as the structural barriers that limit their opportunities ... limited voice and participation"),
 ("FAM-04", "CAP", "Human capital formation", "The knowledge, skills and health people build from early childhood to working age.",
  "Becker 1964; Cunha and Heckman 2007 on lifecycle skill formation; Hanushek and Woessmann 2008; World Bank Human Capital Project 2018 and WDR 2018 Learning",
  "expand people's capabilities to lead healthy, productive, and resilient lives, including through education, skills, digital access"),
 ("FAM-05", "CAP", "Health and longevity", "Longer, healthier lives through care that reaches people and prevention that keeps them well.",
  "Grossman 1972 health capital; Jamison et al. 2013 Global Health 2035; Kruk et al. 2018 high-quality health systems; WHO universal health coverage framework (service coverage and financial protection)",
  "capabilities to lead healthy, productive, and resilient lives, including through ... health"),
 ("FAM-06", "CAP", "Income security and social protection", "A floor under household consumption through shocks and across the life cycle, and a way out of poverty.",
  "World Bank WDR 2014 Risk and Opportunity; Dercon 2002; Banerjee et al. 2015 on graduation; Bastagli et al. 2016 on cash transfers; Sen 1981 on entitlements",
  "social protection, food security, livelihoods ... protection from vulnerability"),
 ("FAM-07", "CAP", "Basic services and living conditions", "Safe water, sanitation, electricity, clean cooking and decent housing for every household.",
  "World Bank WDR 2004 Making Services Work for Poor People; Dinkelman 2011 on electrification; Duflo, Galiani and Mobarak 2012 on water and sanitation; Cattaneo et al. 2009 on housing",
  "basic services"),
 ("FAM-08", "FUT", "Climate mitigation and energy transition", "Cutting emissions through carbon pricing, clean energy, efficiency and avoiding lock-in.",
  "Stern 2007; Nordhaus 2019; Acemoglu, Aghion, Bursztyn and Hemous 2012; IPCC AR6 WGIII; Unruh 2000 on carbon lock-in",
  "avoid shifting risks or costs onto future generations, including through climate resilience, just transition"),
 ("FAM-09", "FUT", "Natural capital and ecosystems", "Keeping land, forests, oceans, freshwater and biodiversity productive for the future.",
  "Dasgupta Review 2021; Ostrom 1990; Hardin 1968; Costello, Gaines and Lynham 2008 on catch shares; Ferraro and Kiss 2002 on payments for conservation; Ostrom and Gardner 1993 on water commons",
  "nature and biodiversity, sustainable resource use"),
 ("FAM-10", "FUT", "Pollution and a healthy environment", "Clean air, water and soil, and waste that is collected and reused.",
  "Pigou 1920; Grossman and Krueger 1995; Greenstone and Hanna 2014; Currie et al. 2014 on pollution and human capital; Lancet Commission on Pollution and Health 2017",
  "protect long-term well-being and avoid shifting risks or costs onto future generations ... sustainable resource use"),
 ("FAM-11", "FUT", "Resilience to climate and disasters", "Fewer people, assets and livelihoods harmed when hazards strike.",
  "Hallegatte et al. 2017 Unbreakable; IPCC AR6 WGII; Sendai Framework 2015; Dell, Jones and Olken 2012; Black et al. 2011 on migration as adaptation",
  "climate resilience"),
 ("FAM-12", "FUT", "Intergenerational balance", "Not loading tomorrow's citizens with today's debts, depleted resource wealth or an unprepared age structure.",
  "Hartwick 1977 and Hamilton and Clemens 1999 on adjusted saving; Auerbach, Gokhale and Kotlikoff 1991 on generational accounting; Sachs and Warner 2001 on the resource curse; Lee and Mason 2006 on demographic dividends; Blanchard 2019 on debt",
  "intergenerational equity and responsible public finance"),
 ("FAM-13", "EXP", "Productive transformation", "Moving the economy into more productive, more sophisticated goods and services.",
  "Lewis 1954; Hidalgo and Hausmann 2009 on economic complexity; McMillan and Rodrik 2011; Rodrik 2016; Juhasz, Lane and Rodrik 2023 on the new industrial policy; Nayyar et al. 2021 on services",
  "export promotion and diversification ... international tourism ... the innovation and technology upgrading that make traded sectors competitive"),
 ("FAM-14", "EXP", "Integration into world markets", "Lower costs and better terms for trading, investing and joining value chains across borders.",
  "Melitz 2003; Anderson and van Wincoop 2004; Baier and Bergstrand 2007; Javorcik 2004; World Bank WDR 2020 on global value chains; Baldwin 2016",
  "trade agreements and market access, foreign direct investment ... trade logistics"),
 ("FAM-15", "EXP", "Innovation and technology", "Creating, adopting and spreading new technology across firms.",
  "Romer 1990; Aghion and Howitt 1992; Comin and Mestieri 2018 on diffusion; Cohen and Levinthal 1990 on absorptive capacity; Cirera and Maloney 2017 The Innovation Paradox; Mazzucato 2018 on missions",
  "the innovation and technology upgrading that make traded sectors competitive"),
 ("FAM-16", "DOM", "Infrastructure networks", "Transport, digital and energy networks that connect people, firms and markets, and work reliably.",
  "Aschauer 1989; Donaldson 2018 on railroads; Hjort and Poulsen 2019 on broadband; Allcott, Collard-Wexler and O'Connell 2016 on power shortages; Laffont and Tirole 1993 on regulation",
  "connections between regions and between rural and urban markets"),
 ("FAM-17", "DOM", "Cities, regions and spatial development", "Productive cities, clusters and connected regions, and lagging places catching up.",
  "Duranton and Puga 2004 and Glaeser and Gottlieb 2009 on agglomeration; Henderson 2010 on cities; Hirschman 1958 on linkages; Kline and Moretti 2014 on place-based policy; Jalan and Ravallion 2002 on geographic poverty traps",
  "local value chains and value addition, agro-processing, industrial clusters, and connections between regions"),
 ("FAM-18", "GTI", "Farmers and small enterprises", "Higher productivity and earnings for smallholders, informal businesses and small firms.",
  "Schultz 1964; Foster and Rosenzweig 1995 on learning; Barrett 2008 on smallholder market participation; Bloom et al. 2013 on management; Hsieh and Klenow 2009 on misallocation; de Mel, McKenzie and Woodruff 2008",
  "enterprise development, MSME support, productivity ... market access. Formalisation of informal businesses belongs here"),
 ("FAM-19", "GTI", "Jobs and labour markets", "More and better jobs, and people able to move to where the work is.",
  "Mortensen and Pissarides 1994; Card, Kluve and Weber 2018 on active labour-market programmes; La Porta and Shleifer 2014 on informality; Autor, Dorn and Hanson 2013; Acemoglu and Restrepo 2019; Clemens 2011 and Yang 2008 on migration and remittances",
  "create jobs and incomes for groups left out of growth, including women, youth, informal workers and rural households"),
 ("FAM-20", "GTI", "Markets, finance and property rights", "Rules and finance that let firms enter, compete, borrow, enforce contracts and own property securely.",
  "North 1990; Djankov et al. 2002 on entry regulation; Aghion et al. 2005 on competition; Levine 2005 on finance and growth; Karlan and Morduch 2010; Suri and Jack 2016 on mobile money; Besley 1995 and Field 2007 on property rights",
  "finance and market access ... registration, licensing, and access to finance and markets"),
 ("FAM-21", "ANT", "Foresight, data and early warning", "Seeing risks coming, with the data, plans and triggers ready before they hit.",
  "World Bank WDR 2014 (knowledge as the first pillar of risk management); Sendai Framework Priority 1; PARIS21 and Jerven 2013 on statistical capacity; Schoemaker 1995 on scenario planning; Clarke and Dercon 2016 Dull Disasters",
  "horizon scanning, scenario planning, early warning, contingency planning, risk-informed analysis, and future-oriented strategy"),
 ("FAM-22", "ANT", "Economic resilience to external shocks", "Buffers and diversification so global shocks do not become domestic crises.",
  "Obstfeld, Shambaugh and Taylor 2010 on reserves; Reinhart and Rogoff 2009; Kaminsky and Reinhart 1999; Baldwin and Freeman 2022 on supply-chain risk; Farrell and Newman 2019 on weaponised interdependence",
  "identify and prepare for future risks, opportunities and disruptions ... contingency planning"),
 ("FAM-23", "ADA", "Rule of law and checks on power", "Courts, legislatures and auditors that keep the executive within the law and catch abuse.",
  "North and Weingast 1989; World Bank WDR 2017 Governance and the Law (commitment); Acemoglu and Robinson 2012; Levitsky and Ziblatt 2018; Olken 2007 on audits",
  "institutional flexibility ... adjust priorities, policies, plans, and investments in response to new evidence (the institutions that make correction possible and binding)"),
 ("FAM-24", "ADA", "Adaptive and learning government", "Policies that are monitored, tested, corrected and kept up to date with technology.",
  "Andrews, Pritchett and Woolcock 2017 Building State Capability; Heilmann 2008 on experimentation; World Bank WDR 2017 (coordination); Tirole 2017 and Acemoglu 2021 on regulating digital markets and AI",
  "learning by doing, revising strategies, and making timely course corrections"),
 ("FAM-25", "AGI", "State capability and service delivery", "A civil service that can plan, implement, regulate and deliver, nationally and locally.",
  "Besley and Persson 2011 Pillars of Prosperity; Finan, Olken and Pande 2017 on the personnel economics of the state; Andrews, Pritchett and Woolcock 2017; Muralidharan, Niehaus and Sukhtankar 2016 on digital delivery; Bardhan and Mookherjee 2000 and Faguet 2004 on decentralisation",
  "act quickly and effectively ... coordinate across government, implement reforms"),
 ("FAM-26", "AGI", "Public finances", "Raising revenue fairly and spending it well.",
  "Besley and Persson 2011 on fiscal capacity; Kleven, Kreiner and Saez 2016 on third-party reporting; PEFA and Schick 1998 on budget institutions; IMF 2015 on public investment management; Bandiera, Prat and Valletti 2009 on procurement; Engel, Fischer and Galetovic 2014 on PPPs",
  "mobilize resources"),
 ("FAM-27", "AGI", "Emergency response and recovery", "Responding fast when a crisis hits and rebuilding better afterwards.",
  "Sendai Framework Priority 4; Hallegatte, Rentschler and Walsh 2018 Building Back Better; Clarke and Dercon 2016; WHO International Health Regulations core capacities; Kahn 2005",
  "respond to shocks or emerging priorities without major disruption"),
 ("FAM-28", "REF", "Voice, participation and accountability", "Citizens, media, business and workers able to take part, be informed and hold decision-makers to account, and the coalitions that carry reform.",
  "Hirschman 1970; Sen 1999; Bjorkman and Svensson 2009 and Olken 2007 on community monitoring; Mansuri and Rao 2013 Localizing Development; Besley and Burgess 2002 on media; Ferraz and Finan 2008; Khan 2010 on political settlements; World Bank WDR 2017 (cooperation)",
  "political will, reform incentives, collaborative leadership, coalitions, public-private collaboration, civic participation, and co-creation"),
]

# Seven pathway merges (28 October 2026): merged id -> surviving id. The merged pathway keeps its id and
# citations in pathways_v2.csv, flagged merged_into; strategies on it count on the survivor.
MERGES = {47: 43, 82: 80, 139: 135, 99: 95, 31: 34, 187: 183, 259: 11}

# Ten asset classes: id, name, why it is an asset (literature)
ASSETS = [
 ("AST-01", "Natural resources and land", "Resource rents, if reinvested (Hartwick 1977; Sachs and Warner 2001; van der Ploeg 2011); natural capital as a productive stock (Dasgupta 2021)"),
 ("AST-02", "Location and market access", "Proximity to markets and corridors (Krugman 1991; Redding and Venables 2004)"),
 ("AST-03", "Demographic structure", "A young labour force as a first dividend, savings as a second (Bloom, Canning and Sevilla 2003; Lee and Mason 2006)"),
 ("AST-04", "Skills, human capital and diaspora", "Human capital as the engine of growth (Lucas 1988); diaspora networks in trade and investment (Kerr 2008)"),
 ("AST-05", "Productive capabilities and industrial base", "What a country already makes predicts what it can make next (Hidalgo and Hausmann 2009); the endowment structure sets the viable industries (Lin 2012)"),
 ("AST-06", "Infrastructure and connectivity", "Networks already built lower the cost of everything else (Donaldson 2018)"),
 ("AST-07", "Institutions and governance quality", "Institutions as the deep determinant (North 1990; Acemoglu, Johnson and Robinson 2001)"),
 ("AST-08", "Financial wealth and sovereign funds", "Converting exhaustible rents into permanent income (Hartwick 1977; the Norwegian fiscal rule)"),
 ("AST-09", "Culture, heritage and natural beauty", "Tourism as a services export with local spillovers (Faber and Gaubert 2019)"),
 ("AST-10", "Technology and digital capability", "Absorptive capacity decides who benefits from the frontier (Cohen and Levinthal 1990; Cirera and Maloney 2017)"),
]

# Hood 1983: the four resources of government. instrument_id (tree/inputs/instruments.csv) -> class
INSTRUMENT_CLASSES = {
 "I0001": "Money", "I0002": "Money", "I0003": "Money", "I0004": "Money", "I0005": "Organisation", "I0006": "Money",
 "I0007": "Information", "I0008": "Information", "I0009": "Organisation", "I0010": "Authority", "I0011": "Authority",
 "I0012": "Money", "I0013": "Money", "I0014": "Authority", "I0015": "Money", "I0016": "Authority", "I0017": "Authority",
 "I0018": "Money", "I0019": "Money",
}
INSTRUMENT_CLASS_NOTE = {
 "Information": "nodality: information systems, registers, data and advice",
 "Authority": "laws, regulation, standards, taxes and agreements that bind",
 "Money": "treasure: transfers, subsidies, loans, guarantees, funds and tax incentives",
 "Organisation": "the state's own hands: facilities, networks and partnerships that build or run things",
}

# Ten target-group classes. target_id (tree/inputs/targets.csv) -> class. Sector targets are the sector's
# producers and workers, so they fall to Firms and MSMEs unless the sector is a public service.
TARGET_CLASSES = {
 "Households and the poor": ["T0020", "T0021", "T0022", "T0023", "T0024", "T0026", "T0027", "T0028", "T0030", "T0031", "T0032", "T0033", "T0035", "T0037", "T0039", "T0040", "T0041", "T0042", "T0043", "T0025"],
 "Women and girls": ["T0070", "T0083", "T0092", "T0100", "T0103", "T0041", "T0017", "T0195"],
 "Children and youth": ["T0019", "T0029", "T0036", "T0038", "T0073", "T0074", "T0091", "T0093", "T0098", "T0101", "T0102"],
 "Older people": ["T0077", "T0196"],
 "Workers and informal workers": ["T0174", "T0175", "T0176", "T0177", "T0178", "T0180", "T0181", "T0182", "T0185", "T0186", "T0187", "T0188", "T0189", "T0190", "T0191", "T0192", "T0193", "T0194", "T0197", "T0005", "T0168"],
 "Farmers and fishers": ["T0173", "T0179", "T0183", "T0184", "T0125", "T0131", "T0135", "T0140", "T0152", "T0164", "T0162", "T0068", "T0171", "T0095", "T0094"],
 "Firms and MSMEs": ["T0006", "T0007", "T0008", "T0009", "T0010", "T0011", "T0012", "T0013", "T0014", "T0015", "T0016", "T0018", "T0126", "T0127", "T0129", "T0130", "T0132", "T0133", "T0136", "T0137", "T0139", "T0141", "T0142", "T0143", "T0144", "T0145", "T0146", "T0147", "T0148", "T0149", "T0150", "T0151", "T0153", "T0154", "T0155", "T0156", "T0157", "T0158", "T0159", "T0160", "T0163", "T0165", "T0167", "T0169", "T0170", "T0172", "T0138"],
 "Regions and places": ["T0044", "T0045", "T0046", "T0047", "T0048", "T0049", "T0050", "T0051", "T0052", "T0053", "T0054", "T0055", "T0056", "T0057", "T0058", "T0059", "T0060", "T0061", "T0062", "T0063", "T0064", "T0065", "T0066", "T0067", "T0071", "T0082"],
 "Public institutions": ["T0105", "T0106", "T0107", "T0108", "T0109", "T0110", "T0111", "T0112", "T0113", "T0114", "T0115", "T0116", "T0117", "T0118", "T0119", "T0120", "T0121", "T0122", "T0123", "T0124", "T0128", "T0134", "T0166", "T0001", "T0002", "T0003", "T0004"],
 "Excluded and affected groups": ["T0099", "T0072", "T0075", "T0076", "T0078", "T0079", "T0080", "T0081", "T0084", "T0086", "T0087", "T0088", "T0089", "T0090", "T0096", "T0097", "T0085"],
 "Whole population and future generations": ["T0069", "T0034", "T0104", "T0161"],
}

# strategies v1 held at a family (no mechanism named): the v2 family they fall to by default.
OLD_FAMILY_DEFAULT = {
 "L2-01": "FAM-01", "L2-02": "FAM-02", "L2-03": "FAM-03", "L2-04": "FAM-03",
 "L2-05": "FAM-06", "L2-06": "FAM-06", "L2-07": "FAM-04", "L2-08": "FAM-04", "L2-09": "FAM-05", "L2-10": "FAM-05",
 "L2-11": "FAM-06",  # split: nutrition -> FAM-04, food safety -> FAM-05, food loss -> FAM-17; default household food security
 "L2-12": "FAM-07", "L2-13": "FAM-02",
 "L2-14": "FAM-08", "L2-15": "FAM-09", "L2-16": "FAM-10", "L2-17": "FAM-11", "L2-18": "FAM-12", "L2-19": "FAM-12", "L2-20": "FAM-12", "L2-21": "FAM-09",
 "L2-22": "FAM-13", "L2-23": "FAM-14", "L2-24": "FAM-14", "L2-25": "FAM-14", "L2-26": "FAM-13", "L2-27": "FAM-15",
 "L2-28": "FAM-16", "L2-29": "FAM-17", "L2-30": "FAM-16", "L2-31": "FAM-17",
 "L2-32": "FAM-18", "L2-33": "FAM-18", "L2-34": "FAM-18", "L2-35": "FAM-20", "L2-36": "FAM-20", "L2-37": "FAM-19",
 "L2-38": "FAM-19",  # split: lagging places -> FAM-17
 "L2-39": "FAM-19", "L2-40": "FAM-20",
 "L2-41": "FAM-22", "L2-42": "FAM-22", "L2-43": "FAM-21", "L2-44": "FAM-21",
 "L2-45": "FAM-23", "L2-46": "FAM-24", "L2-47": "FAM-24",
 "L2-48": "FAM-25", "L2-49": "FAM-25", "L2-50": "FAM-26", "L2-51": "FAM-26", "L2-52": "FAM-25", "L2-53": "FAM-27",
 "L2-54": "FAM-28", "L2-55": "FAM-28", "L2-56": "FAM-28", "L2-57": "FAM-28",
}

from mechanisms_v2 import MECHANISMS  # noqa: E402  (same folder; kept in its own file for length)
