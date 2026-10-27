# UNGA lane

This folder holds a part of PV2 that is **not running** in this workflow yet. Every file is lifted unchanged, still imports PV2's `pv2` package, and does not run here as it stands.

| File | From PV2 |
|---|---|
| `prompts/8_unga_statement.txt` | The whole-speech read |
| `code/stages_unga.py`, `code/publish_unga.py`, `code/07_unga.py` | Stage 8, its publisher and its runbook script |

When this lane comes back, speeches go through step E with `doc_type` `unga`, and their period is the speech year. That gives a signal of how well each speech lines up with the plan in force. Prompt 8 is the reference for what that comparison asked. Each country config already lists its speeches under `parked.unga`.
