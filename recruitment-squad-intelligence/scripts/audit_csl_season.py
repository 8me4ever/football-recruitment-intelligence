"""Audit authorized CSV imports for a complete CSL season; makes no network requests."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/season_2025"
MANIFEST = DATA / "match_manifest.csv"
PLAYER_STATS = DATA / "player_match_stats.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def audit(manifest: list[dict[str, str]], player_rows: list[dict[str, str]], expected_matches: int = 240) -> dict:
    issues: list[str] = []
    match_ids = [row.get("match_id", "").strip() for row in manifest]
    if any(not value for value in match_ids):
        issues.append("manifest contains a blank match_id")
    duplicates = sorted(key for key, count in Counter(match_ids).items() if key and count > 1)
    if duplicates:
        issues.append(f"duplicate manifest match_ids: {duplicates}")
    if len(manifest) != expected_matches:
        issues.append(f"manifest has {len(manifest)} matches; expected {expected_matches}")
    if any(not row.get(field, "").strip() for row in manifest for field in ("match_date", "home_team", "away_team", "status", "source", "source_url")):
        issues.append("manifest has missing required metadata")

    manifest_set = set(match_ids) - {""}
    row_keys = [(r.get("source", "").strip(), r.get("match_id", "").strip(), r.get("player_id", "").strip()) for r in player_rows]
    if any(not source or not match_id or not player_id for source, match_id, player_id in row_keys):
        issues.append("player stats contain blank source/match_id/player_id keys")
    dup_rows = sorted(key for key, count in Counter(row_keys).items() if all(key) and count > 1)
    if dup_rows:
        issues.append(f"duplicate source/match/player keys: {dup_rows[:10]}")
    orphan_rows = sorted({match_id for _, match_id, _ in row_keys if match_id and match_id not in manifest_set})
    if orphan_rows:
        issues.append(f"player rows refer to matches absent from manifest: {orphan_rows[:10]}")

    rows_by_match = Counter(match_id for _, match_id, _ in row_keys if match_id)
    missing_stats = sorted(match_id for match_id in manifest_set if rows_by_match[match_id] == 0)
    matches_with_rows = sum(1 for match_id in manifest_set if rows_by_match[match_id] > 0)
    return {
        "expected_matches": expected_matches,
        "manifest_matches": len(manifest),
        "unique_manifest_matches": len(manifest_set),
        "player_match_rows": len(player_rows),
        "matches_with_player_rows": matches_with_rows,
        "matches_without_player_rows": len(missing_stats),
        "expected_matches_without_player_rows": max(0, expected_matches - matches_with_rows),
        "complete": not issues and not missing_stats and len(manifest_set) == expected_matches,
        "issues": issues + ([f"no player rows for {len(missing_stats)} manifest matches"] if missing_stats else []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--player-stats", type=Path, default=PLAYER_STATS)
    parser.add_argument("--expected-matches", type=int, default=240)
    args = parser.parse_args()
    result = audit(read_csv(args.manifest), read_csv(args.player_stats), args.expected_matches)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
