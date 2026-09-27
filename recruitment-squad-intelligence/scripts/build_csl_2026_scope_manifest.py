"""Merge the full CSL fixture ledger with in-scope AFC fixtures already observed."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/season_2026"
CSL = DATA / "csl_fixtures_2026.csv"
AFC = DATA / "afc_fixtures_2026_27_in_scope.csv"
GUOAN = DATA / "guoan_fixtures_observed_2026.csv"
OUT = DATA / "fixtures_2026_in_scope.csv"
FIELDS = ("observed_on", "season_year", "round", "match_date", "competition", "competition_id",
          "competition_season_id", "match_id", "status", "home_team", "away_team", "home_goals",
          "away_goals", "source_url", "source")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    fixtures: dict[str, dict[str, str]] = {}
    for row in read_csv(CSL):
        fixture = {key: row.get(key, "") or "" for key in FIELDS}
        fixture["status"] = {"-": "scheduled", "—": "scheduled"}.get(fixture["status"], fixture["status"])
        fixtures[fixture["match_id"]] = fixture
    afc_rows = read_csv(AFC)
    for row in afc_rows:
        mid = row["match_id"]
        fixture = {key: row.get(key, "") or "" for key in FIELDS}
        existing = fixtures.get(mid)
        if existing and existing["source_url"] != fixture["source_url"]:
            raise ValueError(f"conflicting source URL for event {mid}")
        fixtures[mid] = fixture
    # Preserve any previously observed Guoan continental fixture absent from the current AFC round ledger.
    for row in read_csv(GUOAN):
        if row.get("competition") == "Chinese Super League" or row["match_id"] in fixtures:
            continue
        fixture = {key: "" for key in FIELDS}
        fixture.update({key: row.get(key, "") or "" for key in (
            "observed_on", "season_year", "match_date", "competition", "competition_id",
            "competition_season_id", "match_id", "status", "home_team", "away_team",
            "home_goals", "away_goals", "source_url")})
        fixture["source"] = "Sofascore rendered Beijing Guoan Finished fixture card"
        fixtures[fixture["match_id"]] = fixture
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(fixtures.values(), key=lambda x: (x["match_date"], x["competition"], x["match_id"])))
    finished = [x for x in fixtures.values() if x["status"] == "finished"]
    print(f"scope fixtures={len(fixtures)} finished={len(finished)} CSL={sum(x['competition']=='Chinese Super League' for x in finished)} AFC={sum(x['competition']!='Chinese Super League' for x in finished)} as_of={date.today().isoformat()}")


if __name__ == "__main__":
    main()
