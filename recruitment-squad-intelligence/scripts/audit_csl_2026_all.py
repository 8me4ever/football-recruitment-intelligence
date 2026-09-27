"""Offline identity/table audit and canonical export for all 2026 in-scope fixtures."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_csl_2026_guoan_dom import CATEGORIES, validate_record  # noqa: E402

DATA = ROOT / "data/csl/season_2026"
LEDGER = DATA / "fixtures_2026_in_scope.csv"
RAW = ROOT / "csl_2026_capture/scrapling_raw"
EXPORT = DATA / "player_match_stats_2026.csv"
AUDIT = DATA / "data_quality_report_2026.json"
COVERAGE = DATA / "collection_coverage_2026.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    fixtures = read_csv(LEDGER)
    finished = [row for row in fixtures if row["status"] == "finished"]
    archives: dict[str, list[Path]] = defaultdict(list)
    for path in RAW.glob("*.json"):
        archives[path.name.split("_")[0]].append(path)
    accepted: list[dict] = []
    rejected: list[dict] = []
    exports: list[dict] = []
    coverage_rows: list[dict] = []
    for fixture in finished:
        mid = fixture["match_id"]
        valid: list[tuple[str, Path, list[dict], dict]] = []
        for path in archives.get(mid, []):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                player_rows, summary = validate_record(record, fixture)
                valid.append((record.get("observed_at", ""), path, player_rows, summary))
            except Exception as exc:
                rejected.append({"match_id": mid, "file": str(path.relative_to(ROOT)),
                                 "reason": f"{type(exc).__name__}: {exc}"})
        if not valid:
            coverage_rows.append({"match_id": mid, "competition": fixture["competition"],
                                  "match_date": fixture["match_date"], "round": fixture.get("round", ""),
                                  "status": "missing_or_rejected", "general_rows": 0,
                                  "category_counts": "", "raw_file": ""})
            continue
        observed_at, path, player_rows, summary = sorted(valid, key=lambda item: item[0])[-1]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        accepted.append({"match_id": mid, "competition": fixture["competition"],
                         "match_date": fixture["match_date"], "round": fixture.get("round", ""),
                         "category_counts": summary["category_counts"],
                         "general_rows": summary["general_player_rows"],
                         "raw_file": str(path.relative_to(ROOT)), "sha256": digest,
                         "source": "Scrapling DynamicSession rendered webpage DOM; visible fixture-card entry",
                         "route": record.get("identity", {}).get("route",
                                      "Beijing Guoan Finished list > exact event-card click"
                                      if mid == "16863671" else "visible exact event-card click")})
        coverage_rows.append({"match_id": mid, "competition": fixture["competition"],
                              "match_date": fixture["match_date"], "round": fixture.get("round", ""),
                              "status": "accepted", "general_rows": summary["general_player_rows"],
                              "category_counts": json.dumps(summary["category_counts"], ensure_ascii=False),
                              "raw_file": str(path.relative_to(ROOT))})
        for row in player_rows:
            row["round"] = fixture.get("round", "")
            row["raw_file"] = str(path.relative_to(ROOT))
            row["evidence_sha256"] = digest
            exports.append(row)

    fields = ["match_id", "match_date", "round", "competition", "competition_id", "competition_season_id",
              "home_team", "away_team", "home_goals", "away_goals", "player_id", "player_name", "team_name",
              "minutes_played", "position", "sofascore_rating", "source_url", "observed_at", "raw_file",
              "evidence_sha256", *(f"{category.lower()}_json" for category in CATEGORIES)]
    with EXPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(exports)
    coverage_fields = ["match_id", "competition", "match_date", "round", "status", "general_rows",
                       "category_counts", "raw_file"]
    with COVERAGE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=coverage_fields)
        writer.writeheader()
        writer.writerows(coverage_rows)

    accepted_ids = {row["match_id"] for row in accepted}
    counts_by_comp = Counter(fixture["competition"] for fixture in finished)
    accepted_by_comp = Counter(row["competition"] for row in accepted)
    player_ids_by_comp: dict[str, set[str]] = defaultdict(set)
    for row in exports:
        player_ids_by_comp[row["competition"]].add(str(row["player_id"]))
    report = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "observed_on": datetime.now(timezone.utc).date().isoformat(),
              "scope": "2026 CSL plus observed AFC fixtures with a 2026 CSL club; CFA Cup excluded",
              "source": "Sofascore browser-rendered webpages via Scrapling DynamicSession; no API calls",
              "route": "visible competition/team fixture card > exact event ID click > identity validation > Player stats > six categories; season manifests are enumerated from visible tournament rounds",
              "fixture_ledger": str(LEDGER.relative_to(ROOT)), "target_finished_fixtures": len(finished),
              "accepted_fixtures": len(accepted), "missing_fixture_ids": sorted(set(x["match_id"] for x in finished)-accepted_ids),
              "coverage": round(len(accepted)/len(finished), 4) if finished else 0,
              "accepted_player_match_rows": len(exports),
              "unique_player_ids": len({str(row["player_id"]) for row in exports}),
              "fixtures_by_competition": dict(counts_by_comp),
              "accepted_by_competition": dict(accepted_by_comp),
              "unique_players_by_competition": {key: len(value) for key, value in player_ids_by_comp.items()},
              "scheduled_or_postponed_fixture_rows": sum(x["status"] != "finished" for x in fixtures),
              "category_validation": "Each accepted match passes visible header, DOM/table equality, two-team, unique player IDs, outfield roster/order and goalkeeper-subset checks for all six categories.",
              "accepted": accepted, "rejected_archives": rejected}
    AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("target_finished_fixtures", "accepted_fixtures", "coverage",
             "accepted_player_match_rows", "unique_player_ids", "fixtures_by_competition",
             "accepted_by_competition", "missing_fixture_ids")}, ensure_ascii=False, indent=2))
    return 0 if not report["missing_fixture_ids"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
