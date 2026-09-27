"""Collect 26/27 AFC player stats only for matches involving a 2026 CSL club."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from scrapling.fetchers import DynamicSession
from collect_csl_2026_all_scrapling import CATEGORIES, HEADER_KEY, extract_table, save_json
from collection_failure import classify_collection_failure

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/season_2026"
LEDGER = DATA / "afc_fixtures_2026_27_in_scope.csv"
RAW = ROOT / "csl_2026_capture/scrapling_raw"
EVIDENCE = DATA / "evidence/afc_collection"
TEMP = DATA / "runtime_temp"
PAGES = {
    "AFC Champions League Elite": "https://www.sofascore.com/football/tournament/asia/afc-champions-league/463#id:99217,tab:matches",
    "AFC Champions League Two": "https://www.sofascore.com/football/tournament/asia/afc-cup/668#tab:matches,id:97465",
}


def has_archive(match_id: str) -> bool:
    for path in RAW.glob(f"{match_id}_*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if str(record.get("match_id")) == match_id and all(
                record.get("categories", {}).get(cat, [{}])[0].get("rows") for cat in CATEGORIES
            ):
                return True
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            pass
    return False


def tournament_url(competition: str) -> str:
    if competition not in PAGES:
        raise ValueError(f"unsupported AFC competition {competition!r}")
    return PAGES[competition]


def open_fixture(page, fixture: dict) -> dict:
    url = tournament_url(fixture["competition"])
    tournament_base = url.split("#")[0]
    if not page.url.startswith(tournament_base):
        try:
            page.go_back(wait_until="domcontentloaded", timeout=20000)
        except Exception:
            pass
    if not page.url.startswith(tournament_base):
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    season = page.get_by_role("combobox", name="Select season in unique tournament header", exact=True)
    season.wait_for(state="visible", timeout=30000)
    page.locator('a[data-id][class*="event-hl-"]').first.wait_for(state="attached", timeout=30000)
    if season.inner_text().strip() != "26/27":
        raise ValueError(f"wrong AFC season {season.inner_text()!r}")
    wanted_round = fixture["round"]
    round_box = page.get_by_role("combobox", name="Select item in event list", exact=True)
    if round_box.inner_text().strip() != wanted_round:
        before = page.locator('a[data-id][class*="event-hl-"]').evaluate_all(
            "as=>as.map(a=>a.dataset.id).sort().join('|')")
        round_box.click()
        page.get_by_role("option", name=wanted_round, exact=True).click()
        page.wait_for_function("""arg=>{
          const b=Array.from(document.querySelectorAll('[role="combobox"]')).find(x=>x.innerText.trim()===arg.round);
          const cards=Array.from(document.querySelectorAll('a[data-id][class*="event-hl-"]'));
          const ids=cards.map(a=>a.dataset.id).sort().join('|');
          return Boolean(b && cards.length>=16 && ids!==arg.before);
        }""", arg={"round": wanted_round, "before": before}, timeout=30000)
    if round_box.inner_text().strip() != wanted_round:
        raise ValueError(f"wrong selected AFC matchday {round_box.inner_text()!r}")
    card = page.locator(f'a[data-id="{fixture["match_id"]}"][class*="event-hl-"]')
    if card.count() != 1:
        raise ValueError(f"{fixture['match_id']}: exact AFC round card missing or ambiguous ({card.count()})")
    card_text = card.inner_text().strip().replace("\n", " ")
    if "FT" not in card_text:
        raise ValueError(f"{fixture['match_id']}: expected FT card, got {card_text!r}")
    card.click()
    page.wait_for_url(f"**#id:{fixture['match_id']}", timeout=30000)
    page.locator("main h1").filter(has_text=fixture["home_team"]).filter(has_text=fixture["away_team"]).wait_for(
        state="visible", timeout=30000)
    return {"route": "AFC tournament > visible matchday > exact fixture card", "round": wanted_round,
            "card_text": card_text}


def collect_match(page, fixture: dict) -> dict:
    route = open_fixture(page, fixture)
    main_text = page.locator("main").inner_text()
    expected_date = datetime.strptime(fixture["match_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
    score = f"{fixture['home_goals']} - {fixture['away_goals']}"
    if not all(value in main_text for value in (expected_date, fixture["competition"], "Finished", score)):
        raise ValueError(f"{fixture['match_id']}: AFC match page identity/date/status/score mismatch")
    page.get_by_role("tab", name="Player stats", exact=True).wait_for(state="visible", timeout=20000)
    page.get_by_role("tab", name="Player stats", exact=True).click()
    categories = {}
    teams = {fixture["home_team"], fixture["away_team"]}
    for category in CATEGORIES:
        if category != "General":
            page.get_by_role("tab", name=category, exact=True).click()
        table = extract_table(page, category)
        if {row["team_name"] for row in table["rows"]} != teams:
            raise ValueError(f"{fixture['match_id']}: {category} team names mismatch")
        ids = [re.search(r"/(\d+)/?$", row["player_href"] or "") for row in table["rows"]]
        if any(item is None for item in ids) or len({item.group(1) for item in ids if item}) != len(ids):
            raise ValueError(f"{fixture['match_id']}: {category} player IDs missing or duplicated")
        categories[category] = [table]
    general_ids = [row["player_href"] for row in categories["General"][0]["rows"]]
    for category in CATEGORIES[1:-1]:
        if [row["player_href"] for row in categories[category][0]["rows"]] != general_ids:
            raise ValueError(f"{fixture['match_id']}: {category} roster/order differs from General")
    if not set(row["player_href"] for row in categories["Goalkeeping"][0]["rows"]).issubset(general_ids):
        raise ValueError(f"{fixture['match_id']}: Goalkeeping player outside General roster")
    record = {"match_id": fixture["match_id"], "match_date": fixture["match_date"],
              "competition": fixture["competition"], "competition_id": int(fixture["competition_id"]),
              "season_id": int(fixture["competition_season_id"]), "home_team": fixture["home_team"],
              "away_team": fixture["away_team"], "home_goals": int(fixture["home_goals"]),
              "away_goals": int(fixture["away_goals"]),
              "source": "Scrapling DynamicSession rendered AFC webpage DOM; exact match-card click",
              "source_url": page.url, "observed_at": datetime.now(timezone.utc).isoformat(),
              "identity": {"heading": page.locator("main h1").first.inner_text(),
                           "visible_text": main_text[:900], **route}, "categories": categories}
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    path = RAW / f"{fixture['match_id']}_{hashlib.sha256(payload).hexdigest()[:12]}.json"
    save_json(path, record)
    return {"match_id": fixture["match_id"], "status": "validated", "file": str(path.relative_to(ROOT)),
            "row_counts": {key: len(value[0]["rows"]) for key, value in categories.items()}, **route}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-id", action="append")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    with LEDGER.open(encoding="utf-8-sig", newline="") as f:
        fixtures = [row for row in csv.DictReader(f) if row["status"] == "finished"]
    if args.match_id:
        wanted = set(args.match_id)
        fixtures = [row for row in fixtures if row["match_id"] in wanted]
        if {row["match_id"] for row in fixtures} != wanted:
            parser.error("unknown, out-of-scope, or unfinished AFC fixture ID")
    if args.skip_existing:
        fixtures = [row for row in fixtures if not has_archive(row["match_id"])]
    if args.limit is not None:
        fixtures = fixtures[:args.limit]
    if not fixtures:
        print(json.dumps({"queue": 0, "message": "All requested AFC fixtures already have raw archives"}, ensure_ascii=False))
        return 0
    RAW.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    start = datetime.now(timezone.utc)
    run = {"started_at": start.isoformat(), "fixtures_requested": len(fixtures),
           "source": "Sofascore rendered webpages", "route": "AFC season/matchday > exact fixture card > Player stats > six categories",
           "python": platform.python_version(), "scrapling": version("scrapling"), "playwright": version("playwright"),
           "headed": not args.headless, "viewport": "1440x1000", "temp_dir": str(TEMP), "results": [], "failures": []}
    print(f"queue={len(fixtures)}", flush=True)

    def action(page):
        for index, fixture in enumerate(fixtures):
            if index:
                page.wait_for_timeout(1500)
            try:
                result = collect_match(page, fixture)
            except Exception as exc:
                result = {"match_id": fixture["match_id"],
                          "status": classify_collection_failure(exc),
                          "failure_class": classify_collection_failure(exc),
                          "error": f"{type(exc).__name__}: {exc}", "last_url": page.url}
                folder = EVIDENCE / fixture["match_id"]
                folder.mkdir(parents=True, exist_ok=True)
                try:
                    body = page.locator("body").inner_text()[:25000]
                    (folder / "failure.txt").write_text(body, encoding="utf-8")
                    (folder / "failure.html").write_text(page.content(), encoding="utf-8")
                    result["status"] = classify_collection_failure(exc, body_text=body)
                    result["failure_class"] = result["status"]
                except Exception:
                    pass
                run["failures"].append(result)
            run["results"].append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            save_json(EVIDENCE / "latest_run.json", run)
            if result["status"] == "manual_verification_required":
                run["halted"] = "manual_verification_required"
                break

    session_error = None
    try:
        first_url = tournament_url(fixtures[0]["competition"])
        with DynamicSession(real_chrome=True, headless=args.headless, google_search=False,
                            network_idle=False, timeout=60000, retries=1, locale="en-GB",
                            timezone_id="Asia/Shanghai", disable_resources=False,
                            user_data_dir=str(DATA / "browser_profile_afc"),
                            additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
            session.fetch(first_url, page_action=action)
    except Exception as exc:
        session_error = f"{type(exc).__name__}: {exc}"
        run["session_error"] = session_error
    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["validated"] = sum(row["status"] == "validated" for row in run["results"])
    save_json(EVIDENCE / "latest_run.json", run)
    print(json.dumps({"validated": run["validated"], "requested": len(fixtures),
                      "failures": len(run["failures"]), "session_error": session_error}, ensure_ascii=False))
    return 0 if run["validated"] == len(fixtures) and not run["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
