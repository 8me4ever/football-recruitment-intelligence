# C1 Data Quality Report — 2026 Primary Dataset

**Observed through:** 2026-09-27  
**Dataset status:** in-season snapshot  
**Source:** Sofascore rendered webpages collected with Scrapling `DynamicSession`; six-category source tables were independently reparsed from saved HTML with Scrapling Selector.

## Coverage

| Competition scope | Enumerated fixtures | Finished targets | Accepted | Coverage |
|---|---:|---:|---:|---:|
| 2026 Chinese Super League | 243 | 208 | 208 | 100% |
| 2026/27 AFC Champions League Elite involving a 2026 CSL club | 16 | 2 | 2 | 100% |
| 2026/27 AFC Champions League Two involving a 2026 CSL club | 6 | 1 | 1 | 100% |
| **Total** | **265** | **211** | **211** | **100%** |

The 54 non-finished rows consist of 32 scheduled CSL fixtures, 3 postponed CSL fixtures, and 19 scheduled AFC fixtures. They remain in the manifest and are excluded from player-stat collection until completion. The 2026 season is not complete.

## Accepted data

- **6,503** player-match rows, at one row per player per match.
- **474** distinct player IDs across the combined dataset.
- Every accepted match contains both teams and all six categories: General, Attacking, Defending, Passing, Duels, and Goalkeeping.
- Competition names, competition IDs, competition season IDs, dates, round labels, event IDs and source URLs are retained separately. No competition weighting is applied in collection.
- **0** missing or rejected completed fixture IDs.

Unique player counts by competition are 425 in CSL, 64 in AFC Champions League Elite, and 30 in AFC Champions League Two; a player appearing in multiple competitions is counted in each relevant competition figure.

## Validation performed

For each accepted match the audit checks the fixture event ID and source URL, date, competition and season IDs, home/away teams, score, the six expected table headers, equality between saved row values and original table HTML, exact two-team coverage, nonempty unique player IDs, consistent player-ID order across the five outfield categories, and the goalkeeper subset relationship to General. The audit writes one coverage row per finished target fixture. A failed or missing table does not enter the canonical player-match CSV.

The entry path is a visible 2026 tournament page, visible round selector, exact match card click, match identity verification, then `Player stats` and the six category tabs. The collector uses rendered DOM only; it makes no direct data API requests and reads no hidden application state. If a verification page appears, the run stops for manual handling.

## Limitations and remaining C1 work

This is a complete snapshot of the **visible completed in-scope fixtures** at the observation time, not a final 2026 season dataset. Later league and continental fixtures must be appended with the same resumable collection and audit path. Player position and other source values retain Sofascore's displayed semantics; missingness distinctions and the minutes/appearance model still need a separate semantic review. The canonical player-match export does not replace the required player, club, lineup, or squad-membership/effective-date dimensions. The 2025 historical layer has since been completed at 240/240 matches; its updated audit is in `data/csl/season_2025/collection_audit.json`. Overall C1 remains `IN PROGRESS` pending its other dimensions and gate checks. C0 is `READY FOR GATE` after the 2025 and 2026 benchmark routes were re-run and validated.

## Artifacts

- Fixture universe: `fixtures_2026_in_scope.csv`
- CSL fixture ledger: `csl_fixtures_2026.csv`
- In-scope AFC ledger: `afc_fixtures_2026_27_in_scope.csv`
- Canonical export: `player_match_stats_2026.csv`
- Machine-readable audit: `data_quality_report_2026.json`
- Per-match audit table: `collection_coverage_2026.csv`
- Original six-category HTML records: `../../../csl_2026_capture/scrapling_raw/`
- Reusable method: `COLLECTION_RUNBOOK_2026.md`
