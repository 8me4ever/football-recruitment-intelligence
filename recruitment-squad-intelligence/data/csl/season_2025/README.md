# 2025 CSL season collection

Status: **complete match-stat coverage: 240/240 finished matches validated across all six player-stat categories**.

The target schedule contains 240 completed matches (16 clubs, double round robin). The manifest has 240 unique matches. Scrapling extracted and validated all six visible player-stat categories for all 240 events, producing 7,417 General-table player-match rows and 452 player IDs; Beijing Guoan coverage is 30/30. The 37 matches that failed the earlier direct-link collection were recovered by selecting the visible 2025 round and clicking the exact finished event card. The retry checks the event ID, card date and score, page title/team identity, and category team/player identities. It does not use a Sofascore data API.

The complete match-stat coverage does **not** establish complete squad/appearance coverage: the source Player stats tables do not enumerate every unused substitute, and the season-wide lineup/effective-membership model and missingness semantics still require separate work. The pages were collected retrospectively in 2026, not frozen as information available on each match date.

Key files:

- `match_manifest.csv` — 240-match schedule and source identifiers.
- `player_match_stats.csv` — one row per player listed in each validated General table; six category values are retained in JSON-valued columns.
- `player_category_dom.jsonl` — canonical per-match, six-category DOM-derived records.
- `player_category_dom_retry.jsonl` — separate archive of the 37 successful card-click retries.
- `player_category_dom.pre_card_retry.jsonl` — backup of the prior 203-match canonical archive.
- `collection_audit.json` and `player_stats_coverage.json` — machine-readable match/category audits.
- `collection_retry_checkpoint.json` — latest resumable retry-run checkpoint.
- `collection_retry_failures.jsonl` — failed pilot attempts; the first-match formatting/tab-wait errors were superseded by its later accepted capture.
- `evidence/retry_round_card/` — per-match failed-attempt evidence.

To retry any future missing fixture IDs without revisiting accepted matches, run `scripts/retry_csl_2025_failed_card_click.py`; it automatically queues only IDs absent from both the canonical and retry archives. The completed run can be reproduced with `.\.venv-scrapling\Scripts\python.exe scripts\retry_csl_2025_failed_card_click.py`.

See `reports/analysis/CSL_2025_COLLECTION_AUDIT.md` for current coverage and `reports/analysis/CSL_SCRAPLING_FEASIBILITY.md` for measured feasibility. The repeatable workflow is in `docs/CSL_SOFASCORE_SCRAPLING_EXECUTION_PROMPT.md`.
