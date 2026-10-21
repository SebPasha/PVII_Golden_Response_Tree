"""Write the literature review notes, one per risk, to notes/<risk>.md (the plan's proposed location, inside the tree folder).

Each note: the reference model and the levers it names (written), then the mechanisms this risk contributes to the pooled
tree, filed by subpillar and family, with live coverage from strategy_nodes.csv, the empty nodes, and the external-validity
checks the model implies.
"""
import csv, os, re, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lit_families import RISKS, SUB, SUBPILLARS

MODEL = {
"CC": ("Unbreakable (Hallegatte, Vogt-Schilb, Bangalore and Rozenberg 2017) separates asset losses from well-being losses: the poor lose a larger share of what they own and recover more slowly, so protecting assets, raising coping capacity and speeding recovery each cut losses by different routes. Mitigation is a global public-good problem (Nordhaus 2008), solved by prices, directed innovation and avoiding lock-in.",
       "Hazard exposure and vulnerability; coping capacity; speed of recovery; the carbon price and the direction of technical change; the lifetime of capital.",
       "A plan that adapts without addressing the coping capacity of the poor understates losses; a mitigation response with no price or innovation channel relies on luck."),
"PAN": ("Epidemic macroeconomics (Eichenbaum, Rebelo and Trabandt 2021) puts a trade-off between health and activity at the centre; surveillance, surge capacity and income protection are the levers that shift it, and private behaviour responds to risk before policy does (Goolsbee and Syverson 2021).",
        "Detection lead time; surge capacity; supply security for health goods; continuity of services; income protection during suppression.",
        "Preparedness without income protection makes suppression politically fragile; surge without surveillance arrives late."),
"BIO": ("Inclusive wealth (Dasgupta 2021) treats natural capital as an asset with a shadow price; open access drives it below its efficient level (Gordon 1954) unless rules, rights or incentives bind (Ostrom 1990; Costello, Gaines and Lynham 2008).",
        "Stock levels; property and harvest rules; habitat protection; payments that align local incentives.",
        "Protection without local incentives leaks; harvest growth without rights runs the stock down."),
"ENV": ("The environmental Kuznets curve (Grossman and Krueger 1995) and its critics (Stern 2004): pollution falls with income only where regulation binds and enforcement works; exposure harms health and human capital (Chay and Greenstone 2003; Ebenstein et al. 2017).",
        "Standards and prices; enforcement; composition and technique of production; waste flows; exposure of children.",
        "Standards without enforcement capacity do not bind; the review links this note to Regulatory enforcement capacity."),
"RES": ("Resource economics: rents should be reinvested to keep wealth from falling (Hartwick 1977); booms cause Dutch disease and rent-seeking (Corden and Neary 1982; Sachs and Warner 1995; Mehlum, Moene and Torvik 2006); energy and water security are diversification and allocation problems.",
        "Rent capture and reinvestment; supply reliability and pricing; storage and allocation of water; food system productivity.",
        "Extraction without a reinvestment rule shifts costs to future generations; subsidies without cost recovery hollow out utilities."),
"GLO": ("Five strands: comparative advantage and capability dynamics (Hausmann, Hwang and Rodrik 2007; Hidalgo and Hausmann 2009); value chains (Baldwin 2016; World Bank 2020); trade shocks and slow adjustment (Autor, Dorn and Hanson 2013; Dix-Carneiro and Kovak 2017); external finance and buffers (Calvo 1998; Rey 2015); geoeconomics (Farrell and Newman 2019; Baldwin and Freeman 2022; Juhasz, Lane and Rodrik 2023). Migration and remittances (Yang 2008; Docquier and Rapoport 2012) are the labour side.",
        "Export complexity; trade costs; market access; FDI linkages; buffers; supplier concentration; adjustment speed.",
        "Promoting exports without upgrading or trade-cost reduction is thin; opening without an adjustment family is incomplete."),
"TEC": ("Task-based automation (Acemoglu and Restrepo 2019) displaces labour from tasks and reinstates it in new ones; diffusion and absorptive capacity (Comin and Mestieri 2018; Cirera and Maloney 2017) decide whether frontier technology reaches firms; digital infrastructure is a public good whose returns depend on skills (Akerman, Gaarder and Mogstad 2015; Hjort and Poulsen 2019).",
        "Adoption lags; skills complementarity; connectivity; data and market rules; direction of AI.",
        "Connectivity without skills and adoption support leaves returns unrealised; adoption without adjustment support concentrates losses."),
"DEM": ("The demographic dividend: output per person equals output per worker times the support ratio (Bloom and Williamson 1998; Mason and Lee, NTA). The identity organises the note but is not a node. The mechanisms are fertility control, female and older-worker participation, human capital per child and lifecycle saving.",
        "Fertility; female and older participation; schooling per child; lifecycle saving; old-age income and care.",
        "Read against the country's dividend stage: a pre-dividend country without fertility and girls' schooling channels misses the first dividend; a post-dividend country without pensions and care misses the second."),
"DB": ("Autocratisation waves (Luhrmann and Lindberg 2019; V-Dem) run through executive aggrandisement: incremental capture of courts, legislatures, media and electoral bodies (Levitsky and Ziblatt 2018). Accountability works through judicial review, oversight, audits, information and electoral competition.",
        "Judicial independence; legislative oversight; audit; media independence; electoral integrity; civic space.",
        "Anti-corruption without independent courts and media is easily reversed."),
"POP": ("Economic insecurity and backlash (Guriev and Papaioannou 2022; Rodrik 2018): losers from trade and automation, places left behind (Rodriguez-Pose 2018), and falling trust in institutions (Algan et al. 2017) raise demand for populists.",
        "Regional equity; adjustment of displaced workers; cost-of-living protection; trust through service delivery; social dialogue.",
        "Populism is mostly addressed through other families; a plan with no regional-equity or adjustment channel leaves the demand side untouched."),
"POL": ("Polarisation measures (Esteban and Ray 1994) and horizontal inequality (Stewart 2008; Cederman, Weidmann and Gleditsch 2011) tie group inequality to conflict; affective polarisation (Iyengar et al. 2019) runs through identity and media; contact, recognition and reconciliation reverse it (Mousa 2020; Cilliers, Dube and Siddiqi 2016).",
        "Between-group inequality; contact across groups; shared identity; reconciliation; information environment.",
        "Cohesion programmes without addressing group inequality treat symptoms."),
}

def main():
    fam = {r["family_id"]: r for r in csv.DictReader(open(os.path.join(HERE, "families.csv")))}
    mech = list(csv.DictReader(open(os.path.join(HERE, "mechanisms.csv"))))
    os.makedirs(os.path.join(HERE, "notes"), exist_ok=True)
    order = [l for _, _, l, _ in SUBPILLARS]
    index = ["# Literature review notes\n", "One note per risk. The review is organised by risk because that is how the models are written; "
             "its mechanisms are pooled into one list and filed by RHDR subpillar. A mechanism tagged to several risks is defined once.\n",
             "| Risk | Mechanisms | Families | Subpillars | Empty nodes |", "|---|---|---|---|---|"]
    for code, risk in RISKS.items():
        ms = [m for m in mech if risk in m["risks"].split(" | ")]
        model, levers, check = MODEL[code]
        L = [f"# {risk}: literature review note\n", "## Reference model\n", model + "\n",
             f"**Levers the model names.** {levers}\n", f"**External-validity check.** {check}\n",
             "## Mechanisms this risk contributes\n",
             f"{len(ms)} mechanisms in {len({m['family_id'] for m in ms})} families. Counts are strategies placed at the mechanism across the 45 plans.\n"]
        by = defaultdict(list)
        for m in ms:
            by[(m["subpillar"], m["family_id"])].append(m)
        for (sp, fid) in sorted(by, key=lambda k: (order.index(k[0]), k[1])):
            f = fam[fid]
            L.append(f"### {f['family']} ({sp})\n")
            L.append(f"{f['definition']} Primary subpillar: {f['primary_reason']}\n")
            L.append("| Mechanism | Input, transmission, outcome | Conditions | Evidence | Strategies | Countries |")
            L.append("|---|---|---|---|---|---|")
            for m in by[(sp, fid)]:
                L.append(f"| {m['mechanism_id']} {m['mechanism']} | {m['causal_input']} → {m['transmission']} → {m['outcome']} | {m['conditions']} | {m['evidence']} | {m['n_strategies']} | {m['n_countries']} |")
            L.append("")
        empty = [m for m in ms if m["n_strategies"] == "0"]
        L.append("## Empty nodes\n")
        L.append(("The literature names these channels; no plan in the set commits to them. The empty node is the finding.\n\n" +
                  "\n".join(f"- {m['mechanism']} ({m['family']})" for m in empty)) if empty else "None.")
        L.append("\n## Status\n\nDraft v1, written to the template the pilot will test. Needs review by an economist who did not draft it, then sign-off.\n")
        fn = re.sub(r"[^a-z]+", "_", risk.lower()).strip("_") + ".md"
        open(os.path.join(HERE, "notes", fn), "w").write("\n".join(L))
        index.append(f"| [{risk}]({fn}) | {len(ms)} | {len({m['family_id'] for m in ms})} | {len({m['subpillar'] for m in ms})} | {len(empty)} |")
    untagged = [m for m in mech if not m["risks"]]
    index.append(f"\n{len(untagged)} mechanisms carry no risk tag: they come from the core development literature needed for exhaustiveness "
                 "(for example contract enforcement, teacher incentives, budget institutions) and are listed in mechanisms.csv.\n")
    open(os.path.join(HERE, "notes", "README.md"), "w").write("\n".join(index))
    print("\n".join(index))

if __name__ == "__main__":
    main()
