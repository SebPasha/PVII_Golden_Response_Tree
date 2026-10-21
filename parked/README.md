# Parked lanes

These folders hold the parts of PV2 that are **not running** in this workflow. They are kept so that everything is in one place. Every file is lifted unchanged, still imports PV2's `pv2` package, and does not run here as it stands.

## budget/

| File | From PV2 |
|---|---|
| `prompts/5_budget_extraction.txt`, `5c_budget_transcript.txt`, `5b_programme_class.txt` | Budget lines, budget speeches, programme class |
| `prompts/6_mapping.txt`, `6b_programme_coverage.txt` | Programme-to-strategy mapping and its recall check |
| `code/stages_budget.py` | `run_stage5`, `5c`, `5b`, `6`, `6b` and their helpers, cut from `extract/stages.py` |
| `code/accept.py`, `code/scale.py` | The acceptance gate for a budget year, and scale words |

When this lane comes back, extraction (5, 5c, 5b) stays as it is. Mapping (6, 6b) will target mother-tree nodes from `workflow/` instead of PV2's strategy names. A fiscal year will join only to the plan whose period contains it. Each country config already lists its budget books under `parked.budget`.

## unga/

| File | From PV2 |
|---|---|
| `prompts/8_unga_statement.txt` | The whole-speech read |
| `code/stages_unga.py`, `code/publish_unga.py`, `code/07_unga.py` | Stage 8, its publisher and its runbook script |

When this lane comes back, speeches go through step E with `doc_type` `unga`, and their period is the speech year. That gives a signal of how well each speech lines up with the plan in force. Prompt 8 is the reference for what that comparison asked. Each country config already lists its speeches under `parked.unga`.
