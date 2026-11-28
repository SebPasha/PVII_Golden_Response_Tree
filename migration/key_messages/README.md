# Key messages (bottom up)

Each country's key messages, one chain each: megatrend risks and opportunities, domestic pressures and
comparative advantages -> mechanism (lever on tree v4) -> objective (Growth, Wellbeing, Governance: the RHDR
pillars) -> instrument -> target group.

- `../key_messages.py` builds the chains of one plan from the page build (no model calls).
- `../k_run.py` (step K, gpt-5.4, one call a plan) writes the messages for every country's latest national plan,
  and compares two plans of one country (`--compare`).
- `runs/<country>/<plan_id>/`: plans run through the live workflow (C, E, F, M) for this work, for example
  Brazil's PPA 2020-2023 and 2024-2027, so the two governments' plans are read the same way.
- `out/`: step K's answers, one JSON per plan, `key_messages.json` with all of them, and `compare_*.json`.

Step C now also asks each document for its comparative advantages and the megatrends it sees as opportunities.
