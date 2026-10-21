# Brief for one decomposition batch

You decompose one batch of PV II strategies into objective, target and instrument, and grow
the three bucket lists. Work from `PV2/support/golden_tree/` (absolute:
`/Users/sebastianpasha/Developer/Environment_UNDP/PV2/support/golden_tree/`). Use `python3.12`.

Write only these files: your batch CSV `by_country/<slug>__bNN.csv`, `objectives.csv`,
`targets.csv`, `instruments.csv`, and your section of `notes.md`. Touch nothing else. No git.

## Read first

1. `PROMPT_fill_buckets.md`: the method. Its rules bind you; this brief only adds mechanics.
2. The three lists as they stand. Earlier batches built them; reuse their entries.
3. `notes.md`: earlier batches' merge decisions and conventions. Follow them.
4. Your batch file `batches/<slug>__bNN.md`, in parts if it is long. Each strategy block gives
   its key, name, grouped members, sector, published and amended RHDR category, risks, and its
   numbered stage 3 rows (`[Ref] name: evidence ;; programmes ;; projects ;; details`).
5. For RHDR decisions: `../../workflow/frameworks/rhdr_2026_10/vocab.json`, key
   `hdi_framework` (definitions, `_from`, `rules`).

## The batch CSV

One row per decomposed strategy, or per split. Columns, in this order:

`strategy_key, slug, strategy, objective_id, objective, objective_quote, target_id, target,
target_quote, instrument_id, instrument, instrument_quote, split_n, not_strategy_reason,
rhdr_amended, flags`

- `objective`, `target`, `instrument` are the list entry's label, exactly as in the list.
- **Quotes.** Each `*_quote` is a phrase copied character for character from that strategy's own
  block: its name, a member name, or one of its stage 3 rows. Not from another strategy's block.
  Keep it short (2 to 12 words), and the phrase that carries the meaning. The checker rejects any
  quote not found in the block. The quote must name the thing itself: a target quote names the
  group, sector or place ("smallholder farmers", "local governments", "rural areas"), never an
  action phrase such as "support relevant agencies" or "eliminate problems". If no phrase in the
  block names the target, use the broadest one that does (often in the strategy name) and add
  `hard_case`.
- **Instrument.** Fill only when the text names the lever: a transfer, subsidy, tax measure,
  regulation or standard, a fund, a loan or guarantee, an insurance scheme, a named facility to be
  built, a service delivered directly, a register or information system, a trade agreement. Verbs
  such as strengthen, promote, develop, enhance, support, improve are not instruments, and nor are
  the response types (programme, policy, reform). If no lever is stated, leave `instrument_id`,
  `instrument` and `instrument_quote` all blank. Never infer one.
- **Splits.** Split only where the strategy's name, or its member names, join distinct objectives
  or distinct targets that would change a comparison. Never split off an objective that appears
  only in the stage 3 rows and not in the name or members; never split on sub-activities. At most 4 rows per strategy; if there are more, keep the 4 that carry
  most of its rows and add the flag `split_capped`. `split_n` is the number of rows the strategy
  has (1 when not split), the same on each of its rows.
- **Not a strategy.** A goal or vision, a quantified target, a single activity, or a risk mention:
  fill `not_strategy_reason` with `goal_or_vision`, `quantified_target`, `activity` or
  `risk_mention`, leave the decomposition columns blank, `split_n` 1. Use it sparingly: a
  grouped strategy with many concrete rows is a strategy.
- **rhdr_amended.** Copy the block's `rhdr_amended` when it is a category. When it reads
  `SPLIT:...`, decide from the strategy text using the amended definitions and `rules` (Joined-up
  Thinking goes to Adaptability and Course Correction only where a coordination mechanism is
  created or reformed; otherwise by what the work does. Fostering the Spirit of Change splits to
  Export-led for innovation and research, Standard People for culture), and add the flag
  `rhdr_split_decided`. The value must be one of the 13 amended categories.
- **flags**, separated by `;`: `rhdr_split_decided`, `split_capped`, `no_stage3_rows` (copy it
  when the block carries it), `hard_case` (you were unsure; explain it in notes.md).
- Write the CSV with Python's `csv` module (UTF-8, header row), never by hand.
- Every strategy key in your batch appears in your CSV. Count them before you finish.

## The lists

Columns: `objectives.csv`: objective_id, family, label, definition, rhdr_category, sector_core,
aliases, n_strategies, n_countries. `targets.csv` and `instruments.csv`: id, family, label,
definition, aliases, n_strategies, n_countries.

- Ids: `O0001`, `T0001`, `I0001`, next free number. Never renumber or delete an entry; to merge,
  write the merge in notes.md and keep using the survivor.
- Reuse an entry wherever the meaning is the same and add the new wording to `aliases`
  (separated by ` | `, no duplicates). Create an entry only for a genuinely new meaning: one that
  would change a comparison, a budget join, a coherence check or a risk analysis.
- Labels short, neutral, no country names. Objectives are verb-led outcomes with no target and no
  instrument in them. Definitions are one or two sentences saying what is in and what is out.
- `rhdr_category` on an objective is the amended category it most often carries; `sector_core`
  is one of: Economic / industrial / productivity; Trade / export; Employment / skills; Digital /
  tech / AI; Climate / green growth / energy; Social protection; Education; Health; or blank.
- Families. Use the existing ones; add one only when nothing fits, and say why in notes.md.
  Aim for tens of entries per family, not hundreds.
- Leave `n_strategies` and `n_countries` alone: `check.py` computes them.
- Edit the lists with Python (pandas or csv), reading the current file first.

## notes.md

Append one section, `## <slug> bNN`, with: new families and why; merges or near-duplicates you
saw; conventions you set that later batches should follow; and up to 5 hard cases (strategy_key,
what was hard, what you chose). Keep it short.

## Finish

Run `python3.12 check.py --batch <slug>__bNN` from this folder and fix every failure it reports.
Reply with: rows written, splits, not-strategy count, instrument share, new entries per list, and
the check result as printed.
