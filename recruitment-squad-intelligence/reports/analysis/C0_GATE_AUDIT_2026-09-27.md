# C0 Gate Audit — Source & Collection Feasibility

**Audit date:** 2026-09-27  
**Decision:** `PASSED`  
**Scope:** Sofascore rendered webpage collection for the 2025 CSL historical layer and 2026 CSL / in-scope AFC primary layer.

## Gate evidence

| Criterion | Result | Evidence |
|---|---|---|
| Known 2025 benchmark | Pass | Re-ran event `13400381` from the visible 2025 tournament round and exact finished fixture card. Six tables validated: General 27, Attacking 27, Defending 27, Passing 27, Duels 27, Goalkeeping 2. HTTP 200. |
| Known 2026 benchmark | Pass | Re-ran event `15552633` (Shanghai Port–Beijing Guoan, 2026-09-05) from the visible 2026 tournament round and exact card. Six tables validated: 31, 31, 31, 31, 31, and 2 rows. HTTP 200. |
| Match identity | Pass | Existing full-season offline audits check event ID, date, competition/season, teams, status and score. 2025: 240/240 accepted, 0 missing; 2026: 211/211 finished in-scope events accepted, 0 missing. |
| Six-category validation | Pass | 2025 coverage is 240/240 for each category. 2026 audit checks visible headers, source-table values, both teams, player-ID uniqueness and category-specific ID relationships for all 211 accepted matches. |
| State-based success checks | Pass | Collectors wait for visible round selectors, exact event URLs, match headings, category headers and player rows. `wait_for_timeout` is used only between requests for pacing, never as the success condition. |
| Explicit failure outcomes | Pass | Collectors now emit `identity_mismatch`, `player_stats_missing`, `category_missing`, `load_timeout`, `page_shell_only` or `parse_failure`; verification surfaces emit `manual_verification_required` and stop the run. The classifier has direct smoke coverage. |
| Resume / retry / audit | Pass | 2025 retry queue is the set difference between the manifest and validated original/retry archives. 2026 collectors support `--skip-existing`; offline audit scripts rebuild coverage and exports from saved raw records. |

## Reproduction environment

Both fresh benchmark runs used the same formal configuration:

- Python 3.12.14; Scrapling 0.4.15; Playwright 1.63.0; Chrome 153.0.8010.53.
- Headed Chrome; 1440×1000 viewport; `en-GB`; `Asia/Shanghai`.
- Dedicated browser profiles, temporary files and evidence under `data/csl/c0_gate/` (browser profiles and temporary files are local runtime state and are excluded from version control).
- Full run metadata: `data/csl/c0_gate/evidence/2025/latest_run.json` and `data/csl/c0_gate/evidence/2026/latest_run.json`.
- Captured benchmark DOM: matching `*_visible_dom.json` files in the same season directories.

Full-season baselines were separately audited from `data/csl/season_2025/collection_audit.json` and `data/csl/season_2026/data_quality_report_2026.json`. The benchmark replay harness is `scripts/replay_c0_benchmarks.py`; failure labels are implemented in `scripts/collection_failure.py`.

## Boundary carried into C1

The C0 collection path proves repeatable retrieval and validation of the six **player-stat tables**. Those tables represent players present in the statistical tables and do not establish a complete match squad, unused substitutes, player membership intervals, or starts by themselves. C1 must build and validate those dimensions separately; this limitation does not invalidate the C0 acquisition gate.
