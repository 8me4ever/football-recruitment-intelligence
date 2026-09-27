"""Validate browser-observed CSL samples offline. No network requests.

Input is our documented transcription format, NOT a Sofascore API schema.
Blank cells remain null; displayed minutes are preserved without correction.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["team", "player_name", "goals", "assists", "tackles", "accurate_passes",
           "duels", "ground_duels", "aerial_duels", "minutes", "position", "rating"]


def count(value: str):
    if value == "":
        return None
    if not re.fullmatch(r"\d+", value):
        raise ValueError(f"Invalid count: {value!r}")
    return int(value)


def pair(value: str):
    """Parse total (successful); a lone number has unknown successes."""
    if value == "":
        return {"total": None, "successful": None}
    m = re.fullmatch(r"(\d+)(?: \((\d+)\))?", value)
    if not m:
        raise ValueError(f"Invalid pair: {value!r}")
    total = int(m[1])
    success = int(m[2]) if m[2] is not None else None
    if success is not None and success > total:
        raise ValueError("Successes exceed total")
    return {"total": total, "successful": success}


def passes(value: str):
    if value == "":
        return {"completed": None, "attempted": None, "displayed_pct": None}
    m = re.fullmatch(r"(\d+)/(\d+) \((\d+(?:\.\d+)?)%\)", value)
    if not m:
        raise ValueError(f"Invalid passing cell: {value!r}")
    completed, attempted, pct = int(m[1]), int(m[2]), float(m[3])
    if completed > attempted or not 0 <= pct <= 100:
        raise ValueError("Invalid passing totals/percentage")
    if attempted and abs(completed / attempted * 100 - pct) > 0.51:
        raise ValueError("Passing percentage inconsistent with displayed rounding")
    return {"completed": completed, "attempted": attempted, "displayed_pct": pct}


def normalize(payload: dict) -> list[dict]:
    if payload.get("schema_version") != 1 or payload.get("columns") != COLUMNS:
        raise ValueError("Unknown schema or column order")
    records, keys = [], set()
    for match in payload["matches"]:
        date.fromisoformat(match["match_date"])
        if f"#id:{match['match_id']}" != "#" + match["source_url"].split("#", 1)[-1]:
            raise ValueError("Match URL identity mismatch")
        for row in match["rows"]:
            if len(row["cells"]) != len(COLUMNS):
                raise ValueError("Column count mismatch")
            raw = dict(zip(COLUMNS, row["cells"]))
            if raw["team"] not in (match["home_team"], match["away_team"]):
                raise ValueError("Player team is not part of this match")
            key = (payload["source"], match["match_id"], row["player_id"])
            if key in keys:
                raise ValueError("Duplicate source/match/player")
            keys.add(key)
            minute = re.fullmatch(r"(\d+)'", raw["minutes"])
            if not minute:
                raise ValueError("Unknown minutes format")
            if raw["position"] not in {"G", "D", "M", "F"}:
                raise ValueError("Unknown coarse position")
            rating = float(raw["rating"]) if raw["rating"] else None
            if rating is not None and not 0 <= rating <= 10:
                raise ValueError("Rating out of range")
            records.append({
                "source": key[0], "match_id": key[1], "player_id": key[2],
                "match_date": match["match_date"], "source_url": match["source_url"],
                "observed_on": payload["observed_on"],
                "team": raw["team"], "player_name": raw["player_name"],
                "goals": count(raw["goals"]), "assists": count(raw["assists"]),
                "tackles": pair(raw["tackles"]), "passes": passes(raw["accurate_passes"]),
                **{field: pair(raw[field]) for field in ("duels", "ground_duels", "aerial_duels")},
                "minutes_provider": int(minute[1]), "minutes_convention": "unverified",
                "position_coarse": raw["position"], "rating_provider": rating,
                "empty_fields": [k for k, v in raw.items() if v == ""],
                "raw_cells": row["cells"],
            })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/csl/pilot/general_table_samples.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/csl/processed/pilot_normalized.json")
    args = parser.parse_args()
    records = normalize(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "matches": len({r['match_id'] for r in records}),
                      "rows_with_empty_fields": sum(bool(r['empty_fields']) for r in records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
