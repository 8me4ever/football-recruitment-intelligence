"""Recover conservative substitution candidates from saved, truncated visible text.

These snippets were saved with the browser DOM capture, not by this script. A
two-player event without an icon is only a candidate, never a confirmed change.
"""

import argparse
import csv
import json
import re
from pathlib import Path


MINUTE = re.compile(r"^\d{1,3}'(?:\s*\+\d+)?$")
SCORE = re.compile(r"^\d+\s*-\s*\d+$")
EXCLUDED = {"Foul", "Argument", "Goal cancelled", "Professional handball",
            "Injury", "Additional time", "Penalty", "Yellow card", "Red card",
            "Second yellow card", "Own goal", "Goal", "Time wasting",
            "Leaving field", "Goalkeeper save", "Professional foul last man"}


def candidates(document, source):
    visible = document.get("identity", {}).get("visible_text", "")
    lines = [line.strip() for line in visible.splitlines() if line.strip()]
    first = next((i for i, line in enumerate(lines) if line.startswith("FT ")), None)
    if first is None:
        return []
    # The capture keeps only the first 600 characters; never accept the final
    # open event group, which may end in the middle of a player name.
    minute_positions = [i for i in range(first + 1, len(lines)) if MINUTE.fullmatch(lines[i])]
    timeline_end = next((i for i in range(first + 1, len(lines))
                         if lines[i] in ("Player of the match", "Who will win?", "On bench")), None)
    if timeline_end is not None:
        minute_positions = [i for i in minute_positions if i < timeline_end]
        minute_positions.append(timeline_end)
    rows = []
    for index, start in enumerate(minute_positions[:-1]):
        end = minute_positions[index + 1]
        block = lines[start + 1:end]
        block = [line for line in block
                 if not line.startswith(("Additional time", "HT "))]
        if len(block) == 3 and block[0] == "Substitution":
            kind, names = "labelled_substitution", block[1:]
        elif len(block) == 2:
            kind, names = "two_player_candidate", block
        else:
            continue
        if (any(SCORE.fullmatch(line) for line in block) or
                any(line in EXCLUDED for line in names) or
                any("(" in line or ")" in line for line in names)):
            continue
        if not all(re.search(r"[A-Za-zÀ-ž]", line) for line in names):
            continue
        rows.append({
            "event_id": document["match_id"],
            "match_date": document["match_date"],
            "home_team": document["home_team"],
            "away_team": document["away_team"],
            "minute_display": lines[start],
            "first_display_name": names[0],
            "second_display_name": names[1],
            "evidence_class": kind,
            "source_file": str(source),
            "capture_text_chars": len(visible),
            "timeline_end_visible": timeline_end is not None,
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path)
    parser.add_argument("--team", default="Beijing Guoan")
    args = parser.parse_args()
    files = sorted(args.input_dir.glob("*.json"))
    selected = {}
    for file in files:
        document = json.loads(file.read_text(encoding="utf-8"))
        if args.team not in (document.get("home_team"), document.get("away_team")):
            continue
        if not document.get("identity", {}).get("visible_text"):
            continue
        event_id = document["match_id"]
        current = selected.get(event_id)
        length = len(document["identity"]["visible_text"])
        if current is None or length > current[0]:
            selected[event_id] = (length, file, document)
    rows = []
    audit = []
    for _, file, document in selected.values():
        match_rows = candidates(document, file)
        rows.extend(match_rows)
        visible = document["identity"]["visible_text"]
        timeline_end_visible = any(marker in visible for marker in
                                   ("Player of the match", "Who will win?", "On bench"))
        audit.append({"event_id": document["match_id"],
                      "match_date": document["match_date"],
                      "candidate_rows": len(match_rows),
                      "timeline_end_visible": timeline_end_visible,
                      "capture_text_chars": len(visible),
                      "source_file": str(file)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["event_id", "match_date", "home_team", "away_team",
                  "minute_display", "first_display_name", "second_display_name",
                  "evidence_class", "source_file", "capture_text_chars",
                  "timeline_end_visible"]
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    if args.audit_output:
        args.audit_output.parent.mkdir(parents=True, exist_ok=True)
        with args.audit_output.open("w", encoding="utf-8", newline="") as stream:
            audit_writer = csv.DictWriter(stream, fieldnames=["event_id", "match_date",
                "candidate_rows", "timeline_end_visible", "capture_text_chars", "source_file"])
            audit_writer.writeheader()
            audit_writer.writerows(sorted(audit, key=lambda row: row["match_date"]))
    print(json.dumps({"input_files": len(files), "selected_matches": len(selected),
                      "candidate_rows": len(rows),
                      "matches_with_candidates": len({row["event_id"] for row in rows}),
                      "matches_with_timeline_end": sum(row["timeline_end_visible"] for row in audit),
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
