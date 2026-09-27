"""Re-run one known 2025 and one known 2026 fixture through the formal route."""
from __future__ import annotations

import csv
import json
import os
import platform
import sys
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from collect_csl_2026_all_scrapling import collect_match as collect_2026  # noqa: E402
from retry_csl_2025_failed_card_click import collect_match as collect_2025  # noqa: E402
from collection_failure import classify_collection_failure  # noqa: E402

OUT = ROOT / "data/csl/c0_gate/evidence"
TEMP = ROOT / "data/csl/c0_gate/runtime_temp"
PROFILE_2025 = ROOT / "data/csl/c0_gate/browser_profile_2025"
PROFILE_2026 = ROOT / "data/csl/c0_gate/browser_profile_2026"
BENCHMARKS = ((2025, "13400381"), (2026, "15552633"))


def read_fixture(path: Path, match_id: str) -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    matches = [row for row in rows if str(row["match_id"]) == match_id]
    if len(matches) != 1:
        raise ValueError(f"expected one fixture {match_id} in {path}, found {len(matches)}")
    return matches[0]


def run_one(season: int, match_id: str) -> dict:
    season_dir = ROOT / f"data/csl/season_{season}"
    manifest = season_dir / ("match_manifest.csv" if season == 2025 else "fixtures_2026_in_scope.csv")
    fixture = read_fixture(manifest, match_id)
    profile = PROFILE_2025 if season == 2025 else PROFILE_2026
    output = OUT / str(season)
    output.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    started = datetime.now(timezone.utc)
    run = {
        "started_at": started.isoformat(), "season": season, "benchmark_match_id": match_id,
        "source": "Sofascore rendered webpage DOM; no data API or hidden application state",
        "route": "visible competition > selected round > exact finished fixture card > Player stats > six categories",
        "python": platform.python_version(), "scrapling": version("scrapling"),
        "playwright": version("playwright"), "headed": True, "viewport": "1440x1000",
        "locale": "en-GB", "timezone": "Asia/Shanghai", "browser_profile": str(profile),
        "temp_dir": str(TEMP), "requested": 1, "results": [],
    }
    collector = collect_2025 if season == 2025 else collect_2026
    entry_url = (
        "https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:71364,tab:matches"
        if season == 2025 else
        "https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:90049,tab:matches"
    )

    def action(page) -> None:
        run["browser_version"] = getattr(page.context.browser, "version", "unavailable")
        try:
            collected = collector(page, fixture)
            if season == 2025:
                record = collected
            else:
                record_path = ROOT / collected["file"]
                record = json.loads(record_path.read_text(encoding="utf-8"))
            raw_path = output / f"{match_id}_visible_dom.json"
            raw_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            categories = record.get("categories", {})
            row_counts = {
                name: len(value["rows"] if isinstance(value, dict) else value[0]["rows"])
                for name, value in categories.items()
            }
            run["results"].append({"match_id": match_id, "status": "validated",
                                    "raw_evidence": str(raw_path.relative_to(ROOT)),
                                    "category_rows": row_counts})
        except Exception as exc:
            try:
                body = page.locator("body").inner_text()[:25000]
            except Exception:
                body = ""
            failure = classify_collection_failure(exc, body_text=body)
            failure_dir = output / f"failure_{match_id}"
            failure_dir.mkdir(parents=True, exist_ok=True)
            (failure_dir / "failure.txt").write_text(body, encoding="utf-8")
            try:
                (failure_dir / "failure.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
            run["results"].append({"match_id": match_id, "status": failure,
                                    "failure_class": failure,
                                    "error": f"{type(exc).__name__}: {exc}", "last_url": page.url})
            if failure == "manual_verification_required":
                run["halted"] = "manual verification required; no bypass attempted"

    session_error = None
    try:
        with DynamicSession(
            real_chrome=True, headless=False, google_search=False, network_idle=False,
            timeout=60000, retries=1, locale="en-GB", timezone_id="Asia/Shanghai",
            disable_resources=False, user_data_dir=str(profile),
            additional_args={"viewport": {"width": 1440, "height": 1000}},
        ) as session:
            response = session.fetch(entry_url, page_action=action)
            try:
                run["initial_http_status"] = response.status
            except Exception:
                pass
    except Exception as exc:
        session_error = f"{type(exc).__name__}: {exc}"
        run["session_error"] = session_error

    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["validated"] = sum(row["status"] == "validated" for row in run["results"])
    run["session_error"] = session_error
    run_path = output / "latest_run.json"
    run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(run, ensure_ascii=False), flush=True)
    return run


def main() -> int:
    runs = [run_one(season, match_id) for season, match_id in BENCHMARKS]
    return 0 if all(run.get("validated") == 1 for run in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
