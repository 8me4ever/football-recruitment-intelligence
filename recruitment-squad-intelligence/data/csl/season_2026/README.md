# 2026 CSL and CSL-club AFC data

## Snapshot at 2026-09-27

The 2026 CSL season is still in progress. The rendered Sofascore round selector listed 30 rounds and 243 CSL event cards: **208 finished, 32 scheduled and 3 postponed**. The 2026/27 AFC Champions League Elite and AFC Champions League Two schedules listed **22 fixtures involving a 2026 CSL club**: 3 finished and 19 scheduled. CFA Cup fixtures and continental fixtures with no CSL 2026 club are outside scope.

All **211/211 finished in-scope fixtures** passed the independent offline table/identity audit, with **6,503 player-match rows and 474 unique player IDs**. The output preserves both teams per match and the six Sofascore player-stat categories. Competition/season IDs remain explicit; competition weights are not applied during collection. Future and postponed matches stay in the fixture ledger until completed.

The full repeatable chain, selector details, checks and commands are documented in [COLLECTION_RUNBOOK_2026.md](COLLECTION_RUNBOOK_2026.md). The authoritative project rules remain in [docs/正式项目章程.md](../../../docs/正式项目章程.md).

## Main outputs

- `csl_fixtures_2026.csv` — all rendered CSL round cards.
- `afc_fixtures_2026_27_in_scope.csv` — 26/27 AFC cards involving any CSL 2026 club.
- `fixtures_2026_in_scope.csv` — unified 265-event target manifest.
- `player_match_stats_2026.csv` — accepted player × match dataset.
- `collection_coverage_2026.csv` and `data_quality_report_2026.json` — per-match coverage and audit.
- `C1_DATA_QUALITY_REPORT_2026.md` — human-readable C1 coverage and limitations report.
- `evidence/round_cards/` and `evidence/afc_round_cards/` — raw card HTML and round captures.
- `../../../csl_2026_capture/scrapling_raw/` — content-addressed visible six-category tables for all 211 accepted completed events.

The Beijing Guoan fixture snapshot and the original in-app/independent-browser comparison remain available as separate evidence and are not the season-level denominator.

On 2026-09-27, comparison with the canonical full-season fixture ledger found that the earlier Guoan-specific ledger omitted the completed Round 1 event `15551889` (Wuhan Three Towns 0–2 Beijing Guoan, 2026-03-08). The event was already present in the season-level dataset and saved visible Scrapling DOM. It has been restored to `guoan_fixtures_observed_2026.csv`; the rebuilt Guoan Scrapling audit now covers **27/27 completed fixtures** (26 CSL and 1 AFC Elite) and 823 two-team player-match rows. The prior in-app browser audit remains a 26-match/791-row comparison and references its preserved input snapshot `guoan_in_app_fixture_snapshot_2026-09-27.csv`.
