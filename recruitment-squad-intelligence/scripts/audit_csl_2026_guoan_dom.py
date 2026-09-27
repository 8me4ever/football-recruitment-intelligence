"""Audit Guoan's saved 2026 visible match tables and export player-match rows.

The browser DOM archive is the evidence. Scrapling Selector reparses each saved
HTML table; no network request is made by this script.
"""
from __future__ import annotations

import csv
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scrapling.parser import Selector

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/season_2026"
RAW = ROOT / "csl_2026_capture/browser_dom"
FIXTURES = DATA / "guoan_fixtures_observed_2026.csv"
AUDIT = DATA / "guoan_collection_audit.json"
EXPORT = DATA / "guoan_player_match_stats_2026.csv"
CATEGORIES = ("General", "Attacking", "Defending", "Passing", "Duels", "Goalkeeping")
OUTFIELD = CATEGORIES[:-1]
REQUIRED_HEADERS = {
    "General": "Minutes played",
    "Attacking": "Shots on target",
    "Defending": "Defensive actions",
    "Passing": "Key passes",
    "Duels": "Possession lost",
    "Goalkeeping": "Total saves",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def player_id(href: str) -> str:
    match = re.search(r"/(\d+)/?$", href or "")
    check(bool(match), f"missing player ID in {href!r}")
    return match.group(1)


def parse_table(record: dict, category: str, teams: set[str]) -> tuple[list[dict], dict]:
    tables = record.get("categories", {}).get(category)
    check(isinstance(tables, list) and len(tables) == 1, f"{category}: expected one table")
    table = tables[0]
    headers = table.get("headers", [])
    rows = table.get("rows", [])
    check(REQUIRED_HEADERS[category] in headers, f"{category}: wrong or missing header")
    html = table.get("html") or record.get("category_evidence", {}).get(category, {}).get("table_html")
    if isinstance(html, list):
        check(len(html) == 1, f"{category}: expected one saved HTML table")
        html = html[0]
    check(bool(rows) and bool(html), f"{category}: empty table")

    parsed = Selector(html)
    dom_rows = [row for row in parsed.css("tbody tr")
                if row.css('a[href*="/football/player/"]::attr(href)').get()]
    check(len(dom_rows) == len(rows), f"{category}: DOM/record row count differs")
    seen: set[str] = set()
    result = []
    rating_count = 0
    for index, (saved, dom) in enumerate(zip(rows, dom_rows)):
        href = dom.css('a[href*="/football/player/"]::attr(href)').get()
        cells = dom.css("td")
        team = cells[0].css("img::attr(alt)").get() if cells else None
        check(href == saved.get("player_href"), f"{category}: player link differs at row {index}")
        check(team == saved.get("team_name") and team in teams,
              f"{category}: team differs at row {index}")
        check(len(saved.get("cells", [])) == len(headers), f"{category}: cell/header mismatch")
        check(len(cells) == len(headers), f"{category}: HTML cell/header mismatch")
        pid = player_id(href)
        check(pid not in seen, f"{category}: duplicate player ID {pid}")
        seen.add(pid)
        rating_raw = dom.css('[role="meter"]::attr(aria-valuenow)').get()
        check(rating_raw is None or rating_raw == "-" or re.fullmatch(r"\d+(?:\.\d+)?", rating_raw),
              f"{category}: malformed rating at row {index}")
        rating = rating_raw if rating_raw not in (None, "-") else None
        if rating is not None:
            check(3 <= float(rating) <= 10, f"{category}: rating out of range")
            rating_count += 1
        saved_meters = [meter.get("value") for cell in saved["cells"]
                        for meter in cell.get("meters", []) if meter.get("value") is not None]
        check((rating_raw is None and not saved_meters) or rating_raw in saved_meters,
              f"{category}: rating differs at row {index}")
        values = {}
        for header, cell in zip(headers[2:], saved["cells"][2:]):
            if header:
                values[header] = rating if header == "Sofascore Rating" and rating is not None else cell.get("text", "")
        result.append({"player_id": pid, "player_name": saved.get("player_name"),
                       "team_name": team, "rating": rating, "values": values})
    check({row["team_name"] for row in result} == teams, f"{category}: two-team coverage failed")
    return result, {"rows": len(result), "ratings": rating_count}


def validate_record(record: dict, fixture: dict) -> tuple[list[dict], dict]:
    mid = fixture["match_id"]
    check(str(record.get("match_id")) == mid, "event ID differs")
    check(record.get("source_url") == fixture["source_url"], "event URL differs")
    check(record.get("match_date") == fixture["match_date"], "date differs")
    check(record.get("competition") == fixture["competition"], "competition differs")
    check(str(record.get("competition_id")) == fixture["competition_id"], "competition ID differs")
    check(str(record.get("season_id")) == fixture["competition_season_id"], "season ID differs")
    for field in ("home_team", "away_team", "home_goals", "away_goals"):
        check(str(record.get(field)) == fixture[field], f"{field} differs")
    teams = {fixture["home_team"], fixture["away_team"]}
    parsed = {}
    counts = {}
    for category in CATEGORIES:
        parsed[category], counts[category] = parse_table(record, category, teams)
    general_ids = [row["player_id"] for row in parsed["General"]]
    for category in OUTFIELD[1:]:
        check([row["player_id"] for row in parsed[category]] == general_ids,
              f"{category}: player ID order differs from General")
    check(set(row["player_id"] for row in parsed["Goalkeeping"]).issubset(general_ids),
          "Goalkeeping: player outside General roster")
    check(len(parsed["Goalkeeping"]) >= 2, "Goalkeeping: fewer than two rows")

    by_category = {category: {row["player_id"]: row for row in rows}
                   for category, rows in parsed.items()}
    output_rows = []
    for general in parsed["General"]:
        pid = general["player_id"]
        output = {"match_id": mid, "match_date": fixture["match_date"],
                  "competition": fixture["competition"],
                  "competition_id": fixture["competition_id"],
                  "competition_season_id": fixture["competition_season_id"],
                  "home_team": fixture["home_team"], "away_team": fixture["away_team"],
                  "home_goals": fixture["home_goals"], "away_goals": fixture["away_goals"],
                  "player_id": pid, "player_name": general["player_name"],
                  "team_name": general["team_name"],
                  "minutes_played": general["values"].get("Minutes played", ""),
                  "position": general["values"].get("Position", ""),
                  "sofascore_rating": general["rating"] or "",
                  "source_url": record["source_url"], "observed_at": record.get("observed_at", "")}
        for category in CATEGORIES:
            item = by_category[category].get(pid)
            output[f"{category.lower()}_json"] = json.dumps(item["values"] if item else {}, ensure_ascii=False)
        output_rows.append(output)
    return output_rows, {"match_id": mid, "category_counts": counts,
                         "general_player_rows": len(output_rows)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("in-app", "scrapling"), default="in-app",
                        help="Which browser DOM archive to validate")
    args = parser.parse_args()
    raw_dir = RAW if args.source == "in-app" else ROOT / "csl_2026_capture/scrapling_raw"
    audit_path = DATA / "guoan_in_app_collection_audit.json" if args.source == "in-app" else AUDIT
    export_path = DATA / "guoan_player_match_stats_2026_in_app.csv" if args.source == "in-app" else EXPORT
    with FIXTURES.open(encoding="utf-8-sig", newline="") as source:
        ledger = list(csv.DictReader(source))
    finished = {row["match_id"]: row for row in ledger if row["status"] == "finished"}
    archives: dict[str, list[Path]] = defaultdict(list)
    for path in raw_dir.glob("*.json"):
        archives[path.name.split("_")[0]].append(path)
    accepted = []
    exported = []
    rejected = []
    for mid, fixture in finished.items():
        candidates = []
        for path in archives.get(mid, []):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                rows, summary = validate_record(record, fixture)
                candidates.append((record.get("observed_at", ""), path, rows, summary))
            except Exception as exc:
                rejected.append({"match_id": mid, "file": str(path.relative_to(ROOT)),
                                 "reason": str(exc)})
        if candidates:
            _, path, rows, summary = sorted(candidates, key=lambda item: item[0])[-1]
            accepted.append({**summary, "file": str(path.relative_to(ROOT)),
                             "source": ("in-app browser visible DOM" if args.source == "in-app"
                                        else "Scrapling DynamicSession visible DOM") + "; Scrapling Selector offline validation"})
            for row in rows:
                row["raw_file"] = str(path.relative_to(ROOT))
            exported.extend(rows)

    fields = ["match_id", "match_date", "competition", "competition_id", "competition_season_id",
              "home_team", "away_team", "home_goals", "away_goals", "player_id", "player_name",
              "team_name", "minutes_played", "position", "sofascore_rating", "source_url",
              "observed_at", "raw_file", *(f"{category.lower()}_json" for category in CATEGORIES)]
    with export_path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(exported)
    report = {"audited_at": datetime.now(timezone.utc).isoformat(), "source": args.source,
              "fixture_snapshot": str(FIXTURES.relative_to(ROOT)),
              "finished_fixtures": len(finished), "accepted_matches": len(accepted),
              "accepted_csl_matches": sum(row["competition"] == "Chinese Super League"
                                          for mid, row in finished.items() if any(a["match_id"] == mid for a in accepted)),
              "accepted_afc_matches": sum(row["competition"].startswith("AFC Champions League")
                                          for mid, row in finished.items() if any(a["match_id"] == mid for a in accepted)),
              "missing_match_ids": sorted(set(finished) - {row["match_id"] for row in accepted}),
              "player_match_rows": len(exported), "accepted": accepted,
              "rejected_archive_versions": rejected,
              "scope_note": "Beijing Guoan fixture snapshot only; not the full 2026 CSL fixture universe",
              "method_note": ("Browser-visible HTML saved from the in-app browser" if args.source == "in-app"
                              else "Browser-visible HTML saved by Scrapling DynamicSession")
              + " and reparsed offline with Scrapling Selector"}
    audit_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("finished_fixtures", "accepted_matches",
                                                 "accepted_csl_matches", "accepted_afc_matches",
                                                 "missing_match_ids", "player_match_rows",
                                                 "rejected_archive_versions")}, ensure_ascii=False, indent=2))
    return 0 if not report["missing_match_ids"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
