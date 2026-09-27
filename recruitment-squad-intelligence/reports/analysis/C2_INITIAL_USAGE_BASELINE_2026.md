# C2 Initial Usage Baseline — Beijing Guoan, 2026-09-27

**Status:** Preliminary, pre-Gate descriptive baseline. It separates the 39-person decision-date first-team cohort from the 45-person season contribution universe. The user supplied this cohort reconciliation as public roster/registration evidence; exact item-level citations are not yet attached to every player row, so the local evidence ledger still needs traceability completion before formal C1 sign-off.

## Scope

This first C2 artifact uses two compatible but distinct populations. The **39-person decision-date first-team cohort** is used for current squad depth. The **45-person season candidate universe** is used for 2026 season contribution, so appearances and minutes remain counted for players who left, went on loan, or moved to U20 during the season. The full Guoan match ledger covers 27 completed fixtures (26 CSL, 1 AFC Champions League Elite), with 406 player-match rows across both populations. Actual appearances, displayed minutes, and evidence-backed starts remain unweighted; ACL performance weighting is reserved for a separate later performance view.

The player-level result is `data/csl/decision_snapshot_2026-09-27/c2_player_usage_baseline_2026_guoan.csv`; it contains 45 rows and has an explicit decision-date membership flag. The position-level aggregation is `data/csl/decision_snapshot_2026-09-27/c2_position_usage_baseline_2026_guoan.csv`; the machine-readable summary is `data/csl/decision_snapshot_2026-09-27/c2_usage_baseline_summary.json`.

## Position-group usage

| Season usage group | Current first-team members | Current members with positive minutes | Current members with no stat row | Noncurrent candidates | Noncurrent candidates with a stat row | CSL displayed minutes, all candidates | ACL displayed minutes, all candidates | Source-supported starts, all candidates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Defender | 12 | 10 | 2 | 2 | 2 | 9282 | 382 | 108 |
| Forward | 6 | 6 | 0 | 0 | 0 | 5149 | 98 | 61 |
| Goalkeeper | 5 | 1 | 4 | 1 | 1 | 2340 | 90 | 27 |
| Midfielder | 16 | 11 | 5 | 1 | 1 | 8998 | 420 | 101 |
| Unknown | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |

Minutes are the sum of displayed actual minutes and are not a player quality score. Position labels use registration nominal groups where available, with observed match-position group as an explicitly marked fallback for former candidates. They are not tactical roles.

## Midseason exits remain part of season performance

Zhang Jianzhi is outside the 2026-09-27 first-team cohort because he was loaned out in the summer, but he started three CSL matches for Guoan before leaving. His season contribution remains **3 starts and 270 displayed minutes**, and is counted under the observed goalkeeper position group. Jiang Wenhao, Feng Boxuan, and Jiaao Wei also have Guoan match rows before their reported/public departures; their 2026 contributions remain in the 45-player season universe. Their current membership status is a separate field, so these players are not mistaken for current squad depth.

## Guardrails and next C2 work

- The decision-date cohort contains 39 players: 28 have positive-minute evidence and 11 have no player-stat row. The wider 45-candidate season universe has 32 with a stat sample and 13 without; four noncurrent candidates have positive-minute evidence, including Zhang Jianzhi. The two youth goalkeepers' no-appearance status is included in the user-supplied public roster evidence; other missing rows remain “no observed sample” only.
- All 27 Guoan fixtures have source-backed starting-XI evidence for observed player-stat rows. This does not establish complete benches or unused substitutes.
- No competition weight is applied to appearances, starts, or minutes. Keep CSL and ACL usage visible as separate columns.
- This baseline does not identify a recruitment need. The 39-player age structure and DOB cross-checks are documented in [C2_AGE_AND_ROLE_EVIDENCE_2026-09-27.md](C2_AGE_AND_ROLE_EVIDENCE_2026-09-27.md). Two fixtures now provide limited match-role evidence on 22 of 406 appearance rows: one 4-4-2 formation-line sample and one match-reported broad position-group sample whose exact formation remains disputed. The other 384 rows still need match-level role/deployment evidence before tactical-role depth can be compared. Public profile labels and G/D/M/F groups are not match roles. Any performance assessment must show CSL-only, ACL-weighted, and sensitivity views separately.
- All 39 current members and four exclusions are classified as user-supplied public roster/registration evidence, not non-public operational information. Add the exact public source references to the corresponding rows and resolve exact transition dates where needed for the formal C1 audit.
