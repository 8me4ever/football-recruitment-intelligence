"""Collect 2026 Guoan Player stats through visible fixture cards with Scrapling.

This uses only rendered Sofascore webpages. It never calls a data API, consumes
XHR payloads, or reads hidden application state.
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

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data/csl/season_2026/guoan_fixtures_observed_2026.csv"
CAPTURE = ROOT / "csl_2026_capture"
RAW = CAPTURE / "scrapling_raw"
EVIDENCE = CAPTURE / "scrapling_batch"
TEMP = CAPTURE / "runtime_temp"
TEAM_URL = "https://www.sofascore.com/football/team/beijing-guoan/3376#tab:matches"
CATEGORIES = ("General", "Attacking", "Defending", "Passing", "Duels", "Goalkeeping")
HEADER_KEY = {"General": "Minutes played", "Attacking": "Shots on target",
              "Defending": "Defensive actions", "Passing": "Key passes",
              "Duels": "Possession lost", "Goalkeeping": "Total saves"}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def fixture_cards(page) -> list[dict]:
    return page.locator('#tabpanel-list a[href*="/football/match/"]').evaluate_all(
        """links => links.map(a => ({href:a.getAttribute('href'),
              text:a.innerText.trim().replace(/\\s+/g,' ')})).filter(x => x.text && x.text.includes('FT'))""")


def open_fixture(page, fixture: dict) -> dict:
    page.goto(TEAM_URL, wait_until="load", timeout=60000)
    page.locator('[data-testid="tab-results"]').wait_for(state="attached", timeout=30000)
    finished = page.get_by_role("tab", name="Finished", exact=True)
    if finished.get_attribute("aria-selected") != "true":
        finished.click()
    page.locator('#tabpanel-list a[href*="/football/match/"]').filter(has_text="FT").first.wait_for(
        state="attached", timeout=30000)
    mid = fixture["match_id"]
    for page_number in range(9):
        cards = fixture_cards(page)
        card = next((item for item in cards if item["href"].endswith("#id:" + mid)), None)
        if card:
            selector = f'#tabpanel-list a[href="{card["href"]}"]'
            link = page.locator(selector).filter(has_text="FT")
            if link.count() != 1:
                raise ValueError(f"{mid}: ambiguous finished fixture card ({link.count()})")
            link.click()
            page.wait_for_url(fixture["source_url"], timeout=30000)
            page.locator("main h1").filter(has_text=fixture["home_team"]).filter(
                has_text=fixture["away_team"]).wait_for(state="visible", timeout=30000)
            return {"card": card, "pages_back": page_number, "route": "finished_fixture_card"}
        previous = page.locator('#tabpanel-list button:has(svg path[d^="M6 11.99"])')
        if previous.count() != 1 or not previous.is_enabled():
            page.goto(fixture["source_url"], wait_until="domcontentloaded", timeout=60000)
            if page.url != fixture["source_url"]:
                raise ValueError(f"{mid}: direct fallback opened a different event URL: {page.url}")
            page.locator("main h1").filter(has_text=fixture["home_team"]).filter(
                has_text=fixture["away_team"]).wait_for(state="visible", timeout=30000)
            return {"card": None, "pages_back": page_number,
                    "route": "direct_fallback_after_missing_fixture_card"}
        before = cards[0]["href"] if cards else None
        previous.click()
        page.wait_for_function(
            """before => { const a=Array.from(document.querySelectorAll('#tabpanel-list a[href*="/football/match/"]'))
              .find(x=>x.innerText.includes('FT')); return a && a.getAttribute('href')!==before; }""",
            arg=before, timeout=15000)
    raise ValueError(f"{mid}: fixture outside observed pagination range")


def extract_table(page, category: str) -> dict:
    header = HEADER_KEY[category]
    page.wait_for_function(
        """header => Array.from(document.querySelectorAll('table')).some(t =>
          Array.from(t.querySelectorAll('thead th')).some(h=>h.innerText.trim()===header) &&
          t.querySelectorAll('tbody tr a[href*="/football/player/"]').length>0)""",
        arg=header, timeout=30000)
    tables = page.locator("table").evaluate_all(
        """tables => tables.map(t=>({headers:Array.from(t.querySelectorAll('thead th')).map(c=>c.innerText.trim()),
          html:t.outerHTML, rows:Array.from(t.querySelectorAll('tbody tr')).map(r=>{
            const cells=Array.from(r.querySelectorAll('td'));
            const a=r.querySelector('a[href*="/football/player/"]');
            return {player_href:a?.getAttribute('href')||null,player_name:a?.innerText.trim()||null,
              team_name:cells[0]?.querySelector('img[alt]')?.alt||null,
              cells:cells.map(c=>({text:c.innerText.trim(),meters:Array.from(c.querySelectorAll('[role="meter"]'))
                .map(m=>({min:m.getAttribute('aria-valuemin'),max:m.getAttribute('aria-valuemax'),
                  value:m.getAttribute('aria-valuenow')}))}))};
          }).filter(r=>r.player_href)})).filter(t=>t.rows.length)""")
    tables = [table for table in tables if header in table["headers"]]
    if len(tables) != 1:
        raise ValueError(f"{category}: expected one player table, got {len(tables)}")
    return tables[0]


def collect_match(page, fixture: dict) -> dict:
    route = open_fixture(page, fixture)
    main_text = page.locator("main").inner_text()
    expected_date = datetime.strptime(fixture["match_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
    required = (expected_date, fixture["competition"], "Finished", fixture["home_goals"] + " - " + fixture["away_goals"])
    if not all(part in main_text for part in required):
        raise ValueError(f"{fixture['match_id']}: date/competition/status/score identity mismatch")
    page.get_by_role("tab", name="Player stats", exact=True).click()
    categories = {}
    teams = {fixture["home_team"], fixture["away_team"]}
    for category in CATEGORIES:
        if category != "General":
            page.get_by_role("tab", name=category, exact=True).click()
        table = extract_table(page, category)
        if {row["team_name"] for row in table["rows"]} != teams:
            raise ValueError(f"{fixture['match_id']}: {category} team mismatch")
        ids = [re.search(r"/(\d+)$", row["player_href"]) for row in table["rows"]]
        if any(value is None for value in ids) or len({value.group(1) for value in ids}) != len(ids):
            raise ValueError(f"{fixture['match_id']}: {category} invalid player IDs")
        categories[category] = [table]
    general_ids = [row["player_href"] for row in categories["General"][0]["rows"]]
    for category in CATEGORIES[1:-1]:
        if [row["player_href"] for row in categories[category][0]["rows"]] != general_ids:
            raise ValueError(f"{fixture['match_id']}: {category} player order differs")
    if not set(row["player_href"] for row in categories["Goalkeeping"][0]["rows"]).issubset(general_ids):
        raise ValueError(f"{fixture['match_id']}: goalkeeper outside General roster")
    record = {"match_id": fixture["match_id"], "match_date": fixture["match_date"],
              "competition": fixture["competition"], "competition_id": int(fixture["competition_id"]),
              "season_id": int(fixture["competition_season_id"]),
              "home_team": fixture["home_team"], "away_team": fixture["away_team"],
              "home_goals": int(fixture["home_goals"]), "away_goals": int(fixture["away_goals"]),
              "source": "Scrapling DynamicSession rendered webpage DOM", "source_url": page.url,
              "observed_at": datetime.now(timezone.utc).isoformat(),
              "identity": {"heading": page.locator("main h1").first.inner_text(),
                           "visible_text": main_text[:700], **route},
              "categories": categories}
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    dest = RAW / f"{fixture['match_id']}_{hashlib.sha256(payload).hexdigest()[:12]}.json"
    save_json(dest, record)
    return {"match_id": fixture["match_id"], "status": "validated", "file": str(dest.relative_to(ROOT)),
            "row_counts": {key: len(value[0]["rows"]) for key, value in categories.items()}, **route}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-id", action="append", help="Collect only this fixture ID; repeatable")
    parser.add_argument("--limit", type=int, help="Maximum number of fixtures")
    parser.add_argument("--skip-existing", action="store_true", help="Resume by skipping complete Scrapling DOM archives")
    parser.add_argument("--headless", action="store_true", help="Use a hidden browser (headed is the verified default)")
    args = parser.parse_args()
    with LEDGER.open(encoding="utf-8-sig", newline="") as source:
        fixtures = [row for row in csv.DictReader(source) if row["status"] == "finished"]
    if args.match_id:
        requested = set(args.match_id)
        fixtures = [row for row in fixtures if row["match_id"] in requested]
        if {row["match_id"] for row in fixtures} != requested:
            parser.error("Unknown or unfinished match ID requested")
    if args.skip_existing:
        def already_collected(mid: str) -> bool:
            for path in RAW.glob(f"{mid}_*.json"):
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                    if str(record.get("match_id")) == mid and all(
                        record.get("categories", {}).get(category, [{}])[0].get("rows")
                        for category in CATEGORIES
                    ):
                        return True
                except (OSError, ValueError, KeyError, IndexError, TypeError):
                    continue
            return False
        fixtures = [row for row in fixtures if not already_collected(row["match_id"])]
    if args.limit is not None:
        fixtures = fixtures[:args.limit]
    if not fixtures:
        print(json.dumps({"validated": 0, "requested": 0, "message": "All requested finished fixtures already have a complete raw archive"}, ensure_ascii=False))
        return 0
    TEMP.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    started_at = datetime.now(timezone.utc)
    run_file = EVIDENCE / f"run_{started_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    run = {"started_at": started_at.isoformat(), "source": "Sofascore rendered webpages",
           "route": "Guoan team page > Finished card > Player stats > six categories",
           "python": platform.python_version(), "scrapling": version("scrapling"),
           "playwright": version("playwright"), "headed": not args.headless,
           "viewport": "1440x1000", "locale": "en-GB", "timezone": "Asia/Shanghai",
           "temp_dir": str(TEMP), "fixtures_requested": len(fixtures),
           "results": []}
    started = time.monotonic()

    def action(page):
        try:
            run["browser_version"] = page.context.browser.version
        except Exception:
            run["browser_version"] = "unavailable"
        for index, fixture in enumerate(fixtures):
            if index:
                page.wait_for_timeout(3000)
            try:
                result = collect_match(page, fixture)
            except Exception as exc:
                result = {"match_id": fixture["match_id"], "status": "failed",
                          "error": f"{type(exc).__name__}: {exc}", "last_url": page.url}
                folder = EVIDENCE / fixture["match_id"]
                folder.mkdir(parents=True, exist_ok=True)
                try:
                    (folder / "failure.txt").write_text(page.locator("body").inner_text()[:25000], encoding="utf-8")
                    (folder / "failure.html").write_text(page.content(), encoding="utf-8")
                except Exception:
                    pass
            run["results"].append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            save_json(EVIDENCE / "latest_run.json", run)
            save_json(run_file, run)

    try:
        with DynamicSession(real_chrome=True, headless=args.headless, google_search=False,
                            network_idle=False, timeout=60000, retries=1, locale="en-GB",
                            timezone_id="Asia/Shanghai", disable_resources=False,
                            additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
            response = session.fetch(TEAM_URL, page_action=action)
            try:
                run["initial_http_status"] = response.status
            except Exception as exc:
                run["initial_http_status_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        run["session_error"] = f"{type(exc).__name__}: {exc}"
    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["elapsed_seconds"] = round(time.monotonic() - started, 1)
    save_json(EVIDENCE / "latest_run.json", run)
    save_json(run_file, run)
    print(json.dumps({"validated": sum(item["status"] == "validated" for item in run["results"]),
                      "requested": len(fixtures), "session_error": run.get("session_error")}, ensure_ascii=False))
    return 0 if len(run["results"]) == len(fixtures) and all(item["status"] == "validated" for item in run["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
