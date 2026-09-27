"""Compare the independently scraped Guoan rows with the in-app DOM archive."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data/csl/season_2026"
IN_APP = ROOT / "guoan_player_match_stats_2026_in_app.csv"
SCRAPLING = ROOT / "guoan_player_match_stats_2026.csv"
CATEGORIES = ("general", "attacking", "defending", "passing", "duels", "goalkeeping")
FIELDS = ("match_date", "competition", "home_team", "away_team", "home_goals", "away_goals",
          "player_name", "team_name", "minutes_played", "position", "sofascore_rating")


def load(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    keys = [(row["match_id"], row["player_id"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError(f"Duplicate match/player keys in {path}")
    return dict(zip(keys, rows))


def main():
    a, b = load(IN_APP), load(SCRAPLING)
    only_a, only_b = set(a) - set(b), set(b) - set(a)
    differences = []
    counts = Counter()
    for key in sorted(set(a) & set(b)):
        for field in FIELDS:
            if a[key][field] != b[key][field]:
                differences.append({"key": key, "field": field,
                                    "in_app": a[key][field], "scrapling": b[key][field]})
                counts[field] += 1
        for category in CATEGORIES:
            field = category + "_json"
            if json.loads(a[key][field]) != json.loads(b[key][field]):
                differences.append({"key": key, "field": field})
                counts[field] += 1
    result = {"in_app_rows": len(a), "scrapling_rows": len(b),
              "in_app_only": len(only_a), "scrapling_only": len(only_b),
              "difference_counts": counts, "first_differences": differences[:10]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not only_a and not only_b and not differences else 1


if __name__ == "__main__":
    raise SystemExit(main())
