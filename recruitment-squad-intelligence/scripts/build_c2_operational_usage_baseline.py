#!/usr/bin/env python3
"""Build a descriptive, pre-Gate C2 usage baseline for Guoan's 2026 cohort.

This report summarizes observed match-table participation and source-backed
starting XIs. It does not score performance, infer non-selection, or apply
competition weights to minutes or appearances.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "csl" / "decision_snapshot_2026-09-27"
COHORT = SNAPSHOT / "c2_operational_cohort_2026-09-27.csv"
ROSTER = SNAPSHOT / "squad_membership_decision_snapshot_2026-09-27.csv"
POSITIONS = SNAPSHOT / "player_position_evidence_2026_guoan.csv"
PARTICIPATION = SNAPSHOT / "player_match_participation_2026_guoan.csv"
PLAYER_OUTPUT = SNAPSHOT / "c2_player_usage_baseline_2026_guoan.csv"
POSITION_OUTPUT = SNAPSHOT / "c2_position_usage_baseline_2026_guoan.csv"
SUMMARY_OUTPUT = SNAPSHOT / "c2_usage_baseline_summary.json"
REPORT = ROOT / "reports" / "analysis" / "C2_INITIAL_USAGE_BASELINE_2026.md"
DECISION_DATE = "2026-09-27"
CSL = "Chinese Super League"
ACL = "AFC Champions League Elite"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def int_value(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    cohort = read_csv(COHORT)
    roster = read_csv(ROSTER)
    position_evidence = read_csv(POSITIONS)
    participation = read_csv(PARTICIPATION)
    if len(cohort) != 39:
        raise SystemExit(f"Expected a 39-player operational cohort, found {len(cohort)}")
    cohort_by_name = {row["player_name_zh"]: row for row in cohort}
    if len(cohort_by_name) != len(cohort):
        raise SystemExit("Duplicate player identity in the provisional C2 cohort")
    roster_by_name = {row["player_name_zh"]: row for row in roster}
    if len(roster_by_name) != len(roster) or len(roster) != 45:
        raise SystemExit(f"Expected 45 unique season-candidate identities, found {len(roster_by_name)}")
    position_by_name = {row["player_name_zh"]: row for row in position_evidence}
    if set(position_by_name) != set(roster_by_name):
        raise SystemExit("Position evidence does not cover the 45-candidate season universe")
    if any(row["analysis_status"] != "pre_gate_operational_snapshot" for row in cohort):
        raise SystemExit("Unexpected C2 cohort status; expected pre-gate operational snapshot")
    current_names = {name for name, row in roster_by_name.items() if row["decision_cohort_member"] == "true"}
    if current_names != set(cohort_by_name):
        raise SystemExit("The 39-player operational cohort does not match the membership snapshot's current-member flags")

    event_ids = {row["event_id"] for row in participation}
    if len(event_ids) != 27:
        raise SystemExit(f"Expected 27 Guoan completed fixtures, found {len(event_ids)}")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in participation:
        if row["player_name_zh"] in roster_by_name:
            grouped[row["player_name_zh"]].append(row)

    player_rows: list[dict] = []
    for name, member in sorted(roster_by_name.items()):
        rows = grouped.get(name, [])
        if not member["player_id"] and rows:
            raise SystemExit(f"Rows exist for {name}, but the roster has no mapped player ID")
        if len({r["event_id"] for r in rows}) != len(rows):
            raise SystemExit(f"Duplicate player-match row in participation ledger for {name}")
        csl_rows = [r for r in rows if r["competition"] == CSL]
        acl_rows = [r for r in rows if r["competition"] == ACL]
        other_rows = [r for r in rows if r["competition"] not in {CSL, ACL}]
        if other_rows:
            raise SystemExit(f"Unexpected Guoan competition in C2 participation rows for {name}")

        def positive(rows_for_competition: list[dict[str, str]]) -> list[dict[str, str]]:
            return [r for r in rows_for_competition if int_value(r.get("minutes_played_numeric", "")) > 0]

        csl_positive = positive(csl_rows)
        acl_positive = positive(acl_rows)
        total_positive = csl_positive + acl_positive
        unknown_started = sum(r.get("started", "") == "" for r in rows)
        if unknown_started:
            raise SystemExit(f"Unexpected unknown starting-XI status in Guoan observed rows for {name}: {unknown_started}")
        pos = position_by_name[name]
        nominal_position = pos["nominal_position"]
        observed_groups = [v for v in pos["observed_position_groups"].split(";") if v]
        if nominal_position:
            season_usage_position = nominal_position
            season_usage_position_basis = "registration_nominal_position"
        elif len(observed_groups) == 1:
            season_usage_position = {"G": "Goalkeeper", "D": "Defender", "M": "Midfielder", "F": "Forward"}.get(observed_groups[0], "Unknown")
            season_usage_position_basis = "observed_match_position_group_fallback" if season_usage_position != "Unknown" else "unknown"
        else:
            season_usage_position = "Unknown"
            season_usage_position_basis = "unknown"
        is_current_member = member["decision_cohort_member"] == "true"
        player_key = f"sofascore:{member['player_id']}" if member["player_id"] else f"roster_name_zh:{name}"
        player_rows.append({
            "decision_date": DECISION_DATE,
            "analysis_status": "pre_gate_operational_snapshot",
            "player_key": player_key,
            "player_id": member["player_id"],
            "player_name_zh": name,
            "decision_date_first_team_member": "true" if is_current_member else "false",
            "membership_status_as_of_decision_date": member["membership_status_as_of_decision_date"],
            "membership_status_source_tier": member["membership_status_source_tier"],
            "membership_status_source": member["membership_status_source"],
            "membership_status_note": member["membership_status_note"],
            "membership_transition_effective_date": member["membership_transition_effective_date"],
            "valid_from": member["valid_from"],
            "valid_to": member["valid_to"],
            "user_reported_status_detail": member["user_reported_status_detail"],
            "user_reported_registration_detail": member["user_reported_registration_detail"],
            "user_reported_availability_detail": member["user_reported_availability_detail"],
            "nominal_position": nominal_position,
            "observed_position_groups": pos["observed_position_groups"],
            "season_usage_position_group": season_usage_position,
            "season_usage_position_basis": season_usage_position_basis,
            "public_verification_status": "user_identified_public_roster_evidence; exact_item_reference_pending" if member["membership_status_confidence"] == "public_roster_evidence_user_reconciled" else "public_transition_or_roster_evidence_only",
            "csl_stats_table_rows": len(csl_rows),
            "csl_positive_minute_matches": len(csl_positive),
            "csl_displayed_minutes_sum": sum(int_value(r.get("minutes_played_numeric", "")) for r in csl_rows),
            "csl_source_supported_starts": sum(r["started"] == "true" for r in csl_rows),
            "acl_stats_table_rows": len(acl_rows),
            "acl_positive_minute_matches": len(acl_positive),
            "acl_displayed_minutes_sum": sum(int_value(r.get("minutes_played_numeric", "")) for r in acl_rows),
            "acl_source_supported_starts": sum(r["started"] == "true" for r in acl_rows),
            "all_competitions_stats_table_rows": len(rows),
            "all_competitions_positive_minute_matches": len(total_positive),
            "all_competitions_displayed_minutes_sum": sum(int_value(r.get("minutes_played_numeric", "")) for r in rows),
            "all_competitions_source_supported_starts": sum(r["started"] == "true" for r in rows),
            "match_rows_with_unknown_started_status": unknown_started,
            "stats_sample_status": "observed_current_season_sample" if rows else "no_current_season_appearance_sample",
            "latest_positive_minutes_match_date": max((r["match_date"] for r in total_positive), default=""),
            "interpretation": "Season usage is counted for all 45 candidates with Guoan identity evidence, including players outside the decision-date first-team cohort; no row is not evidence of non-selection or non-availability.",
        })

    position_rows: list[dict] = []
    for position in sorted({r["season_usage_position_group"] for r in player_rows}):
        rows = [r for r in player_rows if r["season_usage_position_group"] == position]
        current_rows = [r for r in rows if r["decision_date_first_team_member"] == "true"]
        noncurrent_rows = [r for r in rows if r["decision_date_first_team_member"] == "false"]
        position_rows.append({
            "decision_date": DECISION_DATE,
            "analysis_status": "pre_gate_operational_snapshot",
            "season_usage_position_group": position,
            "season_usage_position_group_basis": "registration_nominal_position_or_observed_position_fallback; see player-level basis",
            "decision_date_first_team_members": len(current_rows),
            "current_members_with_positive_minutes": sum(r["all_competitions_positive_minute_matches"] > 0 for r in current_rows),
            "current_members_without_stats_table_sample": sum(r["all_competitions_stats_table_rows"] == 0 for r in current_rows),
            "noncurrent_candidates": len(noncurrent_rows),
            "noncurrent_candidates_with_stats_table_sample": sum(r["all_competitions_stats_table_rows"] > 0 for r in noncurrent_rows),
            "noncurrent_candidates_without_stats_table_sample": sum(r["all_competitions_stats_table_rows"] == 0 for r in noncurrent_rows),
            "all_candidates_in_position_group": len(rows),
            "all_candidates_with_stats_table_sample": sum(r["all_competitions_stats_table_rows"] > 0 for r in rows),
            "csl_positive_minute_matches": sum(r["csl_positive_minute_matches"] for r in rows),
            "csl_displayed_minutes_sum": sum(r["csl_displayed_minutes_sum"] for r in rows),
            "csl_source_supported_starts": sum(r["csl_source_supported_starts"] for r in rows),
            "acl_positive_minute_matches": sum(r["acl_positive_minute_matches"] for r in rows),
            "acl_displayed_minutes_sum": sum(r["acl_displayed_minutes_sum"] for r in rows),
            "acl_source_supported_starts": sum(r["acl_source_supported_starts"] for r in rows),
            "all_competitions_displayed_minutes_sum": sum(r["all_competitions_displayed_minutes_sum"] for r in rows),
            "all_competitions_source_supported_starts": sum(r["all_competitions_source_supported_starts"] for r in rows),
        })

    current_rows = [r for r in player_rows if r["decision_date_first_team_member"] == "true"]
    noncurrent_rows = [r for r in player_rows if r["decision_date_first_team_member"] == "false"]
    if len(player_rows) != 45 or len(current_rows) != 39 or len(noncurrent_rows) != 6:
        raise SystemExit("C2 season/current squad reconciliation failed: expected 45 candidates, 39 current and 6 noncurrent")
    if sum(r["all_competitions_stats_table_rows"] for r in player_rows) != len(participation):
        raise SystemExit("The 45-candidate season contribution rows do not reconcile to the full Guoan participation ledger")
    if sum(r["all_competitions_stats_table_rows"] == 0 for r in player_rows) != 13:
        raise SystemExit("Expected 13 candidates without current-season player-stat rows")
    if sum(r["all_competitions_stats_table_rows"] for r in noncurrent_rows) != 7:
        raise SystemExit("Expected 7 season player-match rows from candidates outside the decision-date first-team cohort")
    if sum(r["all_competitions_displayed_minutes_sum"] for r in noncurrent_rows) != 368:
        raise SystemExit("Expected 368 displayed minutes from candidates outside the decision-date first-team cohort")
    if sum(r["all_competitions_source_supported_starts"] for r in noncurrent_rows) != 3:
        raise SystemExit("Expected 3 source-supported starts from candidates outside the decision-date first-team cohort")
    if sum(r["all_competitions_positive_minute_matches"] > 0 for r in current_rows) != 28:
        raise SystemExit("Expected 28 current first-team members with positive-minute evidence")
    if sum(r["all_competitions_positive_minute_matches"] > 0 for r in noncurrent_rows) != 4:
        raise SystemExit("Expected 4 noncurrent candidates with positive-minute evidence")
    zhang = next(r for r in player_rows if r["player_name_zh"] == "张健智")
    if zhang["csl_stats_table_rows"] != 3 or zhang["csl_displayed_minutes_sum"] != 270 or zhang["csl_source_supported_starts"] != 3:
        raise SystemExit("Zhang Jianzhi's three 2026 CSL starts / 270 minutes did not reconcile")
    if sum(r["csl_displayed_minutes_sum"] for r in position_rows) + sum(r["acl_displayed_minutes_sum"] for r in position_rows) != sum(r["all_competitions_displayed_minutes_sum"] for r in player_rows):
        raise SystemExit("Competition-split minutes do not reconcile to the all-competition total")
    if sum(r["all_competitions_source_supported_starts"] for r in player_rows) != 297:
        raise SystemExit("Expected the 27 source-backed Guoan starting XIs to reconcile to 297 season starts")

    write_csv(PLAYER_OUTPUT, player_rows, list(player_rows[0]))
    write_csv(POSITION_OUTPUT, position_rows, list(position_rows[0]))
    summary = {
        "decision_date": DECISION_DATE,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "pre_gate_operational_snapshot",
        "season_candidate_universe_size": len(player_rows),
        "season_candidate_universe_basis": "45 identities from dated Guoan registrations, reconciled with decision-date membership evidence",
        "decision_date_first_team_members": len(current_rows),
        "noncurrent_or_former_first_team_candidates": len(noncurrent_rows),
        "public_source_roster_gate": "user_supplied_public_evidence; exact_source_traceability_pending",
        "completed_guoan_fixtures": len(event_ids),
        "observed_player_stats_rows_all_candidates": sum(r["all_competitions_stats_table_rows"] for r in player_rows),
        "observed_player_stats_rows_current_squad": sum(r["all_competitions_stats_table_rows"] for r in current_rows),
        "current_squad_players_with_positive_minutes": sum(r["all_competitions_positive_minute_matches"] > 0 for r in current_rows),
        "current_squad_players_without_stats_table_sample": sum(r["all_competitions_stats_table_rows"] == 0 for r in current_rows),
        "all_season_candidates_with_stats_table_sample": sum(r["all_competitions_stats_table_rows"] > 0 for r in player_rows),
        "all_season_candidates_without_stats_table_sample": sum(r["all_competitions_stats_table_rows"] == 0 for r in player_rows),
        "noncurrent_candidates_with_positive_minutes": sum(r["all_competitions_positive_minute_matches"] > 0 for r in noncurrent_rows),
        "noncurrent_candidates_stats_table_rows": sum(r["all_competitions_stats_table_rows"] for r in noncurrent_rows),
        "noncurrent_candidates_displayed_minutes_sum": sum(r["all_competitions_displayed_minutes_sum"] for r in noncurrent_rows),
        "noncurrent_candidates_source_supported_starts": sum(r["all_competitions_source_supported_starts"] for r in noncurrent_rows),
        "zhang_jianzhi_csl_starts": zhang["csl_source_supported_starts"],
        "zhang_jianzhi_csl_displayed_minutes": zhang["csl_displayed_minutes_sum"],
        "source_supported_starts_total": sum(r["all_competitions_source_supported_starts"] for r in player_rows),
        "csl_positive_minute_matches_total": sum(r["csl_positive_minute_matches"] for r in player_rows),
        "acl_positive_minute_matches_total": sum(r["acl_positive_minute_matches"] for r in player_rows),
        "competition_weights_applied_to_usage": False,
        "position_summary": position_rows,
        "limitations": [
            "This is descriptive usage context, not a performance ranking or recruitment recommendation.",
            "Decision-date first-team status uses a 39-player cohort reconciled by the user from public roster/registration evidence. Exact item-level public references are not yet attached to every local reconciliation row; this is a traceability gap, not a basis for classifying the evidence as private.",
            "Season contribution totals include all 45 registration candidates and retain match rows for players no longer in the decision-date first team. This is distinct from the 39-player current-squad depth cohort.",
            "No player absent from the match-stat export is classified as not selected, unavailable, or not in the matchday squad.",
            "Displayed minutes and observed appearances remain actual counts; ACL weighting applies only to a later performance view, never to usage totals.",
            "Nominal positions are broad registration groups; role-level diagnosis requires separate match-role evidence and review.",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    position_markdown = "\n".join(
        f"| {r['season_usage_position_group']} | {r['decision_date_first_team_members']} | {r['current_members_with_positive_minutes']} | {r['current_members_without_stats_table_sample']} | {r['noncurrent_candidates']} | {r['noncurrent_candidates_with_stats_table_sample']} | {r['csl_displayed_minutes_sum']} | {r['acl_displayed_minutes_sum']} | {r['all_competitions_source_supported_starts']} |"
        for r in position_rows
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        """# C2 Initial Usage Baseline — Beijing Guoan, 2026-09-27

**Status:** Preliminary, pre-Gate descriptive baseline. It separates the 39-person decision-date first-team cohort from the 45-person season contribution universe. The user supplied this cohort reconciliation as public roster/registration evidence; exact item-level citations are not yet attached to every player row, so the local evidence ledger still needs traceability completion before formal C1 sign-off.

## Scope

This first C2 artifact uses two compatible but distinct populations. The **39-person decision-date first-team cohort** is used for current squad depth. The **45-person season candidate universe** is used for 2026 season contribution, so appearances and minutes remain counted for players who left, went on loan, or moved to U20 during the season. The full Guoan match ledger covers 27 completed fixtures (26 CSL, 1 AFC Champions League Elite), with 406 player-match rows across both populations. Actual appearances, displayed minutes, and evidence-backed starts remain unweighted; ACL performance weighting is reserved for a separate later performance view.

The player-level result is `data/csl/decision_snapshot_2026-09-27/c2_player_usage_baseline_2026_guoan.csv`; it contains 45 rows and has an explicit decision-date membership flag. The position-level aggregation is `data/csl/decision_snapshot_2026-09-27/c2_position_usage_baseline_2026_guoan.csv`; the machine-readable summary is `data/csl/decision_snapshot_2026-09-27/c2_usage_baseline_summary.json`.

## Position-group usage

| Season usage group | Current first-team members | Current members with positive minutes | Current members with no stat row | Noncurrent candidates | Noncurrent candidates with a stat row | CSL displayed minutes, all candidates | ACL displayed minutes, all candidates | Source-supported starts, all candidates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
""" + position_markdown + """

Minutes are the sum of displayed actual minutes and are not a player quality score. Position labels use registration nominal groups where available, with observed match-position group as an explicitly marked fallback for former candidates. They are not tactical roles.

## Midseason exits remain part of season performance

Zhang Jianzhi is outside the 2026-09-27 first-team cohort because he was loaned out in the summer, but he started three CSL matches for Guoan before leaving. His season contribution remains **3 starts and 270 displayed minutes**, and is counted under the observed goalkeeper position group. Jiang Wenhao, Feng Boxuan, and Jiaao Wei also have Guoan match rows before their reported/public departures; their 2026 contributions remain in the 45-player season universe. Their current membership status is a separate field, so these players are not mistaken for current squad depth.

## Guardrails and next C2 work

- The decision-date cohort contains 39 players: 28 have positive-minute evidence and 11 have no player-stat row. The wider 45-candidate season universe has 32 with a stat sample and 13 without; four noncurrent candidates have positive-minute evidence, including Zhang Jianzhi. The two youth goalkeepers' no-appearance status is included in the user-supplied public roster evidence; other missing rows remain “no observed sample” only.
- All 27 Guoan fixtures have source-backed starting-XI evidence for observed player-stat rows. This does not establish complete benches or unused substitutes.
- No competition weight is applied to appearances, starts, or minutes. Keep CSL and ACL usage visible as separate columns.
- This baseline does not identify a recruitment need. Next, add public birth-date evidence and detailed role/deployment evidence, then compare depth, age profile, and usage by plausible role. Any performance assessment must show CSL-only, ACL-weighted, and sensitivity views separately.
- All 39 current members and four exclusions are classified as user-supplied public roster/registration evidence, not non-public operational information. Add the exact public source references to the corresponding rows and resolve exact transition dates where needed for the formal C1 audit.
""",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
