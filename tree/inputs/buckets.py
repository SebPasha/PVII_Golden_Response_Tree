"""Build the three golden-tree buckets from the strategy names on the dashboard.

    python3.12 buckets.py combine    # join the split chunks, drop duplicates, write unique phrases
    python3.12 buckets.py finalise   # apply the meaning merges and definitions, write the outputs

Source: data/union/strategies.csv, the list the dashboard reads (9,918 strategies, 45
countries). Each name was split by an agent into objective, target and instrument
(names/decomp_*.tsv). `combine` checks every strategy has a row and writes, per bucket, the
distinct phrases with their counts (names/unique_<bucket>.tsv), which the merge agents read.
They return names/map_<bucket>.tsv (phrase -> label, family); objectives went through two
passes, four sector blocks (map_objective_tier1.tsv) then one across blocks (map_objlabel.tsv),
which `finalise` composes into map_objective.tsv. The definition agents return
names/def_<bucket>.tsv (label -> definition). `finalise` joins it all into:

    objectives.csv, targets.csv, instruments.csv   id, family, label, definition, aliases, counts
    strategy_decomposition.csv                     one row per strategy, phrase and merged label
    golden_table.csv                               the observed objective x target x instrument
    golden_buckets.xlsx                            the same, one sheet each
"""
import csv
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
NAMES = HERE / "names"
BUCKETS = ["objective", "target", "instrument"]
PREFIX = {"objective": "O", "target": "T", "instrument": "I"}
NONE = {"", "not stated", "none", "n/a", "na", "nan"}


def read_tsv(path):
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE)


def clean(s):
    s = " ".join(str(s).split()).strip(" .;")
    return "" if s.lower() in NONE else s[:1].upper() + s[1:]


def combine():
    names = pd.read_csv(NAMES / "all_names.csv", dtype={"n": int})
    parts = sorted(NAMES.glob("decomp_*_p*.tsv"))
    d = pd.concat([read_tsv(p) for p in parts], ignore_index=True)
    d["n"] = pd.to_numeric(d["n"], errors="coerce")
    d = d.dropna(subset=["n"]).astype({"n": int}).drop_duplicates("n", keep="last")
    for b in BUCKETS:
        d[b] = d[b].map(clean)
    missing = sorted(set(names.n) - set(d.n))
    extra = sorted(set(d.n) - set(names.n))
    d = names.merge(d[["n", *BUCKETS]], on="n", how="left").fillna("")
    d.to_csv(NAMES / "decomposition_raw.csv", index=False)
    print(f"{len(parts)} part files, {len(names) - len(missing)} of {len(names)} strategies split;"
          f" missing {len(missing)}, stray {len(extra)}")
    if missing:
        print("missing n:", missing[:40], "..." if len(missing) > 40 else "")
    for b in BUCKETS:
        s = d[d[b] != ""]
        u = (s.groupby(s[b].str.lower())
              .agg(phrase=(b, "first"), n=("n", "size"), countries=("slug", "nunique"),
                   sector=("sector", lambda x: x.mode().iat[0] if len(x.mode()) else ""))
              .sort_values(["sector", "phrase"]))
        u[["phrase", "n", "countries", "sector"]].to_csv(NAMES / f"unique_{b}.tsv", sep="\t", index=False)
        print(f"{b}: {len(s)} filled, {d[b].eq('').sum()} blank, {len(u)} distinct after case-folding")
    return 1 if missing else 0


def compose_objectives():
    """Objectives were merged in two passes: four sector blocks, then across blocks."""
    tier1 = read_tsv(NAMES / "map_objective_tier1.tsv")
    cross = read_tsv(NAMES / "map_objlabel.tsv").set_index("block_label")
    lost = sorted(set(tier1["label"]) - set(cross.index))
    if lost:
        raise SystemExit(f"{len(lost)} block labels missing from map_objlabel.tsv, e.g. {lost[:5]}")
    tier1["family"] = tier1["label"].map(cross["family"])
    tier1["label"] = tier1["label"].map(cross["label"])
    tier1.to_csv(NAMES / "map_objective.tsv", sep="\t", index=False)


def finalise():
    compose_objectives()
    d = pd.read_csv(NAMES / "decomposition_raw.csv", dtype=str, keep_default_na=False)
    out = d[["strategy_key", "slug", "strategy", "sector"]].copy()
    lists = {}
    for b in BUCKETS:
        m = read_tsv(NAMES / f"map_{b}.tsv")
        m["key"] = m["phrase"].map(lambda s: clean(s).lower())
        m["label"] = m["label"].map(clean)
        m = m.drop_duplicates("key", keep="last").set_index("key")
        key = d[b].str.lower()
        unmapped = sorted(set(key[key != ""]) - set(m.index))
        if unmapped:
            print(f"{b}: {len(unmapped)} phrases not in map_{b}.tsv, e.g. {unmapped[:5]}")
        out[f"{b}_phrase"] = d[b]
        out[b] = key.map(m["label"]).fillna("")
        defs = read_tsv(NAMES / f"def_{b}.tsv").assign(label=lambda x: x["label"].map(clean))
        defs = defs.drop_duplicates("label").set_index("label")["definition"]
        used = out[out[b] != ""]
        fam = m.drop_duplicates("label").set_index("label")["family"]
        entries = (used.groupby(b)
                   .agg(n_strategies=("strategy_key", "size"), n_countries=("slug", "nunique"),
                        aliases=(f"{b}_phrase", lambda x: " | ".join(sorted(set(x), key=str.lower))))
                   .reset_index().rename(columns={b: "label"}))
        entries["family"] = entries["label"].map(fam).fillna("")
        entries["definition"] = entries["label"].map(defs).fillna("")
        entries = entries.sort_values(["family", "n_strategies"], ascending=[True, False])
        entries.insert(0, f"{b}_id", [f"{PREFIX[b]}{i:04d}" for i in range(1, len(entries) + 1)])
        lists[b] = entries[[f"{b}_id", "family", "label", "definition", "aliases",
                            "n_strategies", "n_countries"]]
        out[f"{b}_id"] = out[b].map(lists[b].set_index("label")[f"{b}_id"]).fillna("")
        no_def = (lists[b]["definition"] == "").sum()
        print(f"{b}: {len(lists[b])} entries in {lists[b]['family'].nunique()} families,"
              f" {no_def} without a definition")
        lists[b].to_csv(HERE / f"{b}s.csv", index=False)
    cols = ["strategy_key", "slug", "strategy", "sector"]
    for b in BUCKETS:
        cols += [f"{b}_id", b, f"{b}_phrase"]
    out = out[cols]
    out.to_csv(HERE / "strategy_decomposition.csv", index=False)
    g = (out.groupby(["objective_id", "objective", "target_id", "target", "instrument_id", "instrument"])
         .agg(n_strategies=("strategy_key", "size"), n_countries=("slug", "nunique"),
              example_strategies=("strategy", lambda x: " | ".join(x.head(3))))
         .reset_index().sort_values(["n_countries", "n_strategies"], ascending=False))
    g.to_csv(HERE / "golden_table.csv", index=False)
    with pd.ExcelWriter(HERE / "golden_buckets.xlsx") as x:
        for b in BUCKETS:
            lists[b].to_excel(x, sheet_name=f"{b.title()}s", index=False)
        g.to_excel(x, sheet_name="Golden table", index=False)
        out.to_excel(x, sheet_name="Strategies", index=False)
    share = (out["instrument_id"] != "").mean()
    print(f"{len(out)} strategies, {len(g)} golden-table rows, {share:.0%} with an instrument")


if __name__ == "__main__":
    sys.exit({"combine": combine, "finalise": finalise}[sys.argv[1]]())
