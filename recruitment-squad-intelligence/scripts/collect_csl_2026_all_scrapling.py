"""Collect 2026 CSL player statistics via tournament cards and rendered match DOM.

The script follows Sofascore's visible tournament round selector, clicks the exact
fixture card, then reads the six visible Player stats categories. It does not call
data APIs or consume hidden application state. Browser profile, temp files, and
evidence remain on the F: drive.
"""
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
from collection_failure import classify_collection_failure

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/season_2026"
LEDGER = DATA / "fixtures_2026_in_scope.csv"
RAW = ROOT / "csl_2026_capture/scrapling_raw"
EVIDENCE = DATA / "evidence/all_league_collection"
TEMP = DATA / "runtime_temp"
TOURNAMENT_URL = "https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:90049,tab:matches"
CATEGORIES = ("General", "Attacking", "Defending", "Passing", "Duels", "Goalkeeping")
HEADER_KEY = {"General": "Minutes played", "Attacking": "Shots on target",
              "Defending": "Defensive actions", "Passing": "Key passes",
              "Duels": "Possession lost", "Goalkeeping": "Total saves"}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def challenge_text(page) -> bool:
    text = page.locator("body").inner_text().lower()
    return any(token in text for token in ("verify you are human", "captcha", "checking your browser"))


def ensure_schedule(page, round_no: str) -> None:
    season = page.get_by_role("combobox", name="Select season in unique tournament header", exact=True)
    try:
        if not page.url.startswith("https://www.sofascore.com/football/tournament/china/cfa-super-league/649"):
            page.go_back(wait_until="domcontentloaded", timeout=20000)
        season.wait_for(state="visible", timeout=12000)
        page.locator('a[data-id][class*="event-hl-"]').first.wait_for(state="attached", timeout=12000)
    except Exception:
        page.goto(TOURNAMENT_URL, wait_until="domcontentloaded", timeout=60000)
        season.wait_for(state="visible", timeout=30000)
        page.locator('a[data-id][class*="event-hl-"]').first.wait_for(state="attached", timeout=30000)
    if "2026" not in season.inner_text():
        raise ValueError(f"wrong tournament season: {season.inner_text()!r}")
    if challenge_text(page):
        raise RuntimeError("challenge_or_manual_verification_surface_detected")
    wanted = f"Round {int(round_no)}"
    round_box = page.get_by_role("combobox", name="Select item in event list", exact=True)
    if round_box.inner_text().strip() != wanted:
        before = page.locator('a[data-id][class*="event-hl-"]').evaluate_all(
            "as => as.map(a=>a.dataset.id).sort().join('|')")
        round_box.click()
        page.get_by_role("option", name=wanted, exact=True).click()
        page.wait_for_function("""arg => {
          const b=Array.from(document.querySelectorAll('[role="combobox"]')).find(e=>e.innerText.trim()===arg.round);
          const ids=Array.from(document.querySelectorAll('a[data-id][class*="event-hl-"]')).map(a=>a.dataset.id).sort().join('|');
          return Boolean(b && ids && ids!==arg.before);
        }""", arg={"round": wanted, "before": before}, timeout=20000)
    if round_box.inner_text().strip() != wanted:
        raise ValueError(f"wrong selected round: expected {wanted}, got {round_box.inner_text()!r}")


def open_csl_fixture(page, fixture: dict) -> dict:
    ensure_schedule(page, fixture["round"])
    card = page.locator(f'a[data-id="{fixture["match_id"]}"][class*="event-hl-"]')
    if card.count() != 1:
        raise ValueError(f"{fixture['match_id']}: expected one visible fixture card, got {card.count()}")
    card_text = card.inner_text().strip().replace("\n", " ")
    if "FT" not in card_text:
        raise ValueError(f"{fixture['match_id']}: ledger says finished but card does not show FT: {card_text}")
    card.click()
    page.wait_for_url(f"**#id:{fixture['match_id']}", timeout=30000)
    heading = page.locator("main h1").filter(has_text=fixture["home_team"]).filter(has_text=fixture["away_team"])
    heading.wait_for(state="visible", timeout=30000)
    return {"route": "CSL tournament round > exact visible finished card", "round": fixture["round"],
            "card_text": card_text}


def extract_table(page, category: str) -> dict:
    header = HEADER_KEY[category]
    try:
        page.wait_for_function("""header => Array.from(document.querySelectorAll('table')).some(t =>
          Array.from(t.querySelectorAll('thead th')).some(h=>h.innerText.trim()===header) &&
          t.querySelectorAll('tbody tr a[href*="/football/player/"]').length>0)""", arg=header, timeout=30000)
    except Exception as exc:
        raise RuntimeError(f"category_missing: {category} player table did not render") from exc
    tables = page.locator("table").evaluate_all("""tables => tables.map(t=>({
      headers:Array.from(t.querySelectorAll('thead th')).map(c=>c.innerText.trim()), html:t.outerHTML,
      rows:Array.from(t.querySelectorAll('tbody tr')).map(r=>{
        const cells=Array.from(r.querySelectorAll('td'));
        const a=r.querySelector('a[href*="/football/player/"]');
        return {player_href:a?.getAttribute('href')||null,player_name:a?.innerText.trim()||null,
          team_name:cells[0]?.querySelector('img[alt]')?.alt||null,
          cells:cells.map(c=>({text:c.innerText.trim(),meters:Array.from(c.querySelectorAll('[role="meter"]'))
            .map(m=>({min:m.getAttribute('aria-valuemin'),max:m.getAttribute('aria-valuemax'),value:m.getAttribute('aria-valuenow')}))}))};
      }).filter(r=>r.player_href)
    })).filter(t=>t.rows.length)""")
    tables = [table for table in tables if header in table["headers"]]
    if len(tables) != 1:
        raise ValueError(f"{category}: expected one player table, got {len(tables)}")
    return tables[0]


def collect_match(page, fixture: dict) -> dict:
    route = open_csl_fixture(page, fixture)
    main_text = page.locator("main").inner_text()
    expected_date = datetime.strptime(fixture["match_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
    expected_score = f"{fixture['home_goals']} - {fixture['away_goals']}"
    required = (expected_date, fixture["competition"], "Finished", expected_score)
    if not all(part in main_text for part in required):
        raise ValueError(f"{fixture['match_id']}: match page date/competition/status/score mismatch")
    page.get_by_role("tab", name="Player stats", exact=True).wait_for(state="visible", timeout=20000)
    page.get_by_role("tab", name="Player stats", exact=True).click()
    categories = {}
    teams = {fixture["home_team"], fixture["away_team"]}
    for category in CATEGORIES:
        if category != "General":
            page.get_by_role("tab", name=category, exact=True).click()
        table = extract_table(page, category)
        if {row["team_name"] for row in table["rows"]} != teams:
            raise ValueError(f"{fixture['match_id']}: {category} table team names mismatch")
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
              "source": "Scrapling DynamicSession rendered webpage DOM; exact visible schedule-card click",
              "source_url": page.url, "observed_at": datetime.now(timezone.utc).isoformat(),
              "identity": {"heading": page.locator("main h1").first.inner_text(),
                           "visible_text": main_text[:900], **route}, "categories": categories}
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:12]
    dest = RAW / f"{fixture['match_id']}_{digest}.json"
    save_json(dest, record)
    return {"match_id": fixture["match_id"], "status": "validated", "file": str(dest.relative_to(ROOT)),
            "row_counts": {key: len(value[0]["rows"]) for key, value in categories.items()}, **route}


def read_fixtures() -> list[dict]:
    with LEDGER.open(encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.DictReader(f) if row["status"] == "finished"]


def has_complete_archive(match_id: str) -> bool:
    for path in RAW.glob(f"{match_id}_*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if str(record.get("match_id")) == match_id and all(
                record.get("categories", {}).get(category, [{}])[0].get("rows") for category in CATEGORIES
            ):
                return True
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            continue
    return False


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-id", action="append", help="Collect only this exact fixture ID")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    fixtures = read_fixtures()
    if args.match_id:
        wanted = set(args.match_id)
        fixtures = [x for x in fixtures if x["match_id"] in wanted]
        if {x["match_id"] for x in fixtures} != wanted:
            parser.error("unknown, out-of-scope, or unfinished match ID requested")
    if args.skip_existing:
        fixtures = [x for x in fixtures if not has_complete_archive(x["match_id"])]
    if args.limit is not None:
        fixtures = fixtures[:args.limit]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    started = datetime.now(timezone.utc)
    run = {"started_at": started.isoformat(), "source": "Sofascore rendered webpages",
           "route": "CSL tournament > season > round > exact fixture card > Player stats > six categories",
           "python": platform.python_version(), "scrapling": version("scrapling"),
           "playwright": version("playwright"), "headed": not args.headless,
           "viewport": "1440x1000", "locale": "en-GB", "timezone": "Asia/Shanghai",
           "temp_dir": str(TEMP), "fixtures_requested": len(fixtures), "results": [], "failures": []}
    print(f"queue={len(fixtures)}", flush=True)

    def action(page) -> None:
        run["browser_version"] = getattr(page.context.browser, "version", "unavailable")
        for idx, fixture in enumerate(fixtures):
            if idx:
                page.wait_for_timeout(1500)
            try:
                result = collect_match(page, fixture)
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                result = {"match_id": fixture["match_id"],
                          "status": classify_collection_failure(exc),
                          "failure_class": classify_collection_failure(exc), "error": message,
                          "last_url": page.url}
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
            save_json(EVIDENCE / f"run_{started.strftime('%Y%m%dT%H%M%SZ')}.json", run)
            if result["status"] == "manual_verification_required":
                run["halted"] = "challenge_surface_for_manual_handling"
                break

    session_error = None
    try:
        with DynamicSession(real_chrome=True, headless=args.headless, google_search=False,
                            network_idle=False, timeout=60000, retries=1, locale="en-GB",
                            timezone_id="Asia/Shanghai", disable_resources=False,
                            user_data_dir=str(DATA / "browser_profile"),
                            additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
            response = session.fetch(TOURNAMENT_URL, page_action=action)
            try:
                run["initial_http_status"] = response.status
            except Exception:
                pass
    except Exception as exc:
        session_error = f"{type(exc).__name__}: {exc}"
        run["session_error"] = session_error
    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["validated"] = sum(x["status"] == "validated" for x in run["results"])
    run["completed_or_failed"] = len(run["results"])
    save_json(EVIDENCE / "latest_run.json", run)
    print(json.dumps({"validated": run["validated"], "requested": len(fixtures),
                      "failures": len(run["failures"]), "halted": run.get("halted"),
                      "session_error": session_error}, ensure_ascii=False))
    return 0 if run["validated"] == len(fixtures) and not run["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
