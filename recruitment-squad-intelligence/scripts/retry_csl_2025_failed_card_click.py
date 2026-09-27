"""Retry previously failed 2025 CSL player tables through exact visible round cards.

This uses the rendered Sofascore schedule and match DOM only. It does not call
Sofascore data APIs or read hidden application state. Retry captures are kept
separate until their identity and six category tables have been validated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
import time
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from scrapling.fetchers import DynamicSession
from collection_failure import classify_collection_failure

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/season_2025"
EVIDENCE = DATA / "evidence/retry_round_card"
TEMP = DATA / "runtime_temp/retry_round_card"
PROFILE = DATA / "browser_profile_retry"
MANIFEST = DATA / "match_manifest.csv"
ORIGINAL = DATA / "player_category_dom.jsonl"
RETRY_RAW = DATA / "player_category_dom_retry.jsonl"
FAILURES = DATA / "collection_retry_failures.jsonl"
CHECKPOINT = DATA / "collection_retry_checkpoint.json"
TOURNAMENT_URL = "https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:71364,tab:matches"
CATEGORIES = ("General", "Attacking", "Defending", "Passing", "Duels", "Goalkeeping")
HEADER_KEY = {"General": "Minutes played", "Attacking": "Shots on target",
              "Defending": "Defensive actions", "Passing": "Key passes",
              "Duels": "Possession lost", "Goalkeeping": "Total saves"}


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def read_jsonl(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            out[str(entry["match_id"])] = entry
    return out


def write_jsonl(path: Path, records: dict[str, dict], manifest: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    ordered = sorted(records, key=lambda mid: (int(manifest[mid]["round"]), manifest[mid]["match_date"], int(mid)))
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for mid in ordered:
            f.write(json.dumps(records[mid], ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(path)


def challenge_text(page) -> bool:
    text = page.locator("body").inner_text().lower()
    return any(token in text for token in ("verify you are human", "captcha", "checking your browser"))


def ensure_schedule(page, round_no: str) -> str:
    if not page.url.startswith("https://www.sofascore.com/football/tournament/china/cfa-super-league/649"):
        try:
            page.go_back(wait_until="domcontentloaded", timeout=20000)
        except Exception:
            pass
    season = page.get_by_role("combobox", name="Select season in unique tournament header", exact=True)
    try:
        season.wait_for(state="visible", timeout=12000)
        page.locator('a[data-id][class*="event-hl-"]').first.wait_for(state="attached", timeout=12000)
    except Exception:
        page.goto(TOURNAMENT_URL, wait_until="domcontentloaded", timeout=60000)
        season.wait_for(state="visible", timeout=30000)
        page.locator('a[data-id][class*="event-hl-"]').first.wait_for(state="attached", timeout=30000)
    if "2025" not in season.inner_text():
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
          const b=Array.from(document.querySelectorAll('[role=combobox]')).find(e=>e.innerText.trim()===arg.round);
          const ids=Array.from(document.querySelectorAll('a[data-id][class*=\"event-hl-\"]')).map(a=>a.dataset.id).sort().join('|');
          return Boolean(b && ids && ids!==arg.before);
        }""", arg={"round": wanted, "before": before}, timeout=20000)
    if round_box.inner_text().strip() != wanted:
        raise ValueError(f"wrong selected round: expected {wanted}, got {round_box.inner_text()!r}")
    return round_box.inner_text().strip()


def open_fixture_card(page, fixture: dict) -> dict:
    round_name = ensure_schedule(page, fixture["round"])
    card = page.locator(f'a[data-id="{fixture["match_id"]}"][class*="event-hl-"]')
    if card.count() != 1:
        raise ValueError(f"{fixture['match_id']}: expected one visible event card in {round_name}, got {card.count()}")
    card_text = card.inner_text().strip().replace("\n", " ")
    if "FT" not in card_text:
        raise ValueError(f"{fixture['match_id']}: fixture is not visibly finished: {card_text}")
    expected_date = datetime.strptime(fixture["match_date"], "%Y-%m-%d").strftime("%d/%m/%y")
    if expected_date not in card_text:
        raise ValueError(f"{fixture['match_id']}: visible card date does not match {expected_date}: {card_text}")
    score_tokens = re.findall(r"\d+", card_text)
    expected_score = [str(fixture["home_goals"]), str(fixture["away_goals"])]
    if score_tokens[-2:] != expected_score:
        raise ValueError(f"{fixture['match_id']}: card score tokens {score_tokens[-2:]} != {expected_score}")
    card.click()
    page.wait_for_url(f"**#id:{fixture['match_id']}", timeout=30000)
    # Sofascore can update the URL before the event panel is hydrated. Waiting
    # for its visible player tab avoids reading the prior tournament DOM.
    page.get_by_role("tab", name="Player stats", exact=True).wait_for(state="visible", timeout=30000)
    title = page.title()
    if fixture["home_team"] not in title or fixture["away_team"] not in title:
        raise ValueError(f"{fixture['match_id']}: event title does not match both teams: {title!r}")
    return {"route": "2025 CSL tournament > selected round > exact visible finished card click",
            "selected_round": round_name, "card_text": card_text, "event_title": title}


def extract_table(page, category: str) -> dict:
    header = HEADER_KEY[category]
    try:
        page.wait_for_function("""header => Array.from(document.querySelectorAll('table')).some(t =>
          Array.from(t.querySelectorAll('thead th')).some(h=>h.innerText.trim()===header) &&
          t.querySelectorAll('tbody tr a[href*=\"/football/player/\"]').length>0)""", arg=header, timeout=30000)
    except Exception as exc:
        raise RuntimeError(f"category_missing: {category} player table did not render") from exc
    tables = page.locator("table").evaluate_all("""tables => tables.map(t=>({
      headers:Array.from(t.querySelectorAll('thead th')).map(c=>c.innerText.trim()),
      rows:Array.from(t.querySelectorAll('tbody tr')).map(r=>{
        const cells=Array.from(r.querySelectorAll('td'));
        const a=r.querySelector('a[href*=\"/football/player/\"]');
        const href=a?.getAttribute('href')||'';
        const id=href.match(/\\/(\\d+)\\/?$/)?.[1]||null;
        return {player_id:id,player_name:a?.innerText.trim()||null,player_href:href||null,
          team_name:cells[0]?.querySelector('img[alt]')?.alt||null,
          cells:cells.map(c=>({text:c.innerText.trim(),meters:Array.from(c.querySelectorAll('[role=\"meter\"]'))
            .map(m=>({min:m.getAttribute('aria-valuemin'),max:m.getAttribute('aria-valuemax'),value:m.getAttribute('aria-valuenow')}))}))};
      }).filter(r=>r.player_id)
    })).filter(t=>t.rows.length)""")
    tables = [table for table in tables if header in table["headers"]]
    if len(tables) != 1:
        raise ValueError(f"{category}: expected one player table, got {len(tables)}")
    return tables[0]


def collect_match(page, fixture: dict) -> dict:
    route = open_fixture_card(page, fixture)
    stats_tab = page.get_by_role("tab", name="Player stats", exact=True)
    stats_tab.wait_for(state="visible", timeout=20000)
    stats_tab.click()
    page.get_by_role("tab", name="General", exact=True).wait_for(state="visible", timeout=20000)
    categories = {}
    identities = set()
    expected_teams = {fixture["home_team"], fixture["away_team"]}
    for category in CATEGORIES:
        tab = page.get_by_role("tab", name=category, exact=True)
        if tab.count() != 1:
            raise ValueError(f"{fixture['match_id']}: {category} tab missing")
        if category != "General":
            tab.click()
        table = extract_table(page, category)
        rows = table["rows"]
        teamset = {row["team_name"] for row in rows}
        if teamset != expected_teams:
            raise ValueError(f"{fixture['match_id']}: {category} table teams {sorted(teamset)} != {sorted(expected_teams)}")
        ids = [row["player_id"] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{fixture['match_id']}: duplicated player ID in {category}")
        if category == "General":
            identities = set(ids)
            if len(rows) < 15:
                raise ValueError(f"{fixture['match_id']}: General table has only {len(rows)} rows")
        categories[category] = {"status": "validated", **table}
    if not identities:
        raise ValueError(f"{fixture['match_id']}: no validated General roster")
    for category in CATEGORIES[1:-1]:
        category_ids = {r["player_id"] for r in categories[category]["rows"]}
        if category_ids != identities:
            raise ValueError(f"{fixture['match_id']}: {category} player set differs from General")
    if not {r["player_id"] for r in categories["Goalkeeping"]["rows"]}.issubset(identities):
        raise ValueError(f"{fixture['match_id']}: Goalkeeping table contains player outside General")
    entry = {"source": "Sofascore webpage DOM", "competition_id": 649, "season_id": 71364,
             "match_id": str(fixture["match_id"]), "match_date": fixture["match_date"],
             "round": int(fixture["round"]), "home_team": fixture["home_team"],
             "away_team": fixture["away_team"], "home_goals": fixture["home_goals"],
             "away_goals": fixture["away_goals"], "source_url": page.url,
             "observed_at": datetime.now(timezone.utc).isoformat(), "parser_version": "2.0-card-click",
             "route": route, "categories": categories, "general_player_count": len(identities),
             "general_player_ids": sorted(identities)}
    entry["evidence_sha256"] = hashlib.sha256(
        json.dumps(categories, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--match-id", action="append")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    PROFILE.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        fixtures = list(csv.DictReader(f))
    manifest = {str(row["match_id"]): row for row in fixtures}
    originals = read_jsonl(ORIGINAL)
    captured = read_jsonl(RETRY_RAW)
    targets = sorted(set(manifest) - set(originals) - set(captured),
                     key=lambda mid: (int(manifest[mid]["round"]), manifest[mid]["match_date"], int(mid)))
    if args.match_id:
        requested = set(args.match_id)
        unknown = requested - set(manifest)
        already_collected = requested & set(originals)
        if unknown or already_collected:
            parser.error(f"IDs unknown or already in original validated data: {sorted(unknown | already_collected)}")
        targets = [mid for mid in targets if mid in requested]
        missing_targets = requested - set(targets) - set(captured)
        if missing_targets:
            parser.error(f"IDs are already in retry captures or otherwise not retryable: {sorted(missing_targets)}")
    if args.limit is not None:
        targets = targets[:args.limit]
    if not targets:
        print("queue=0; every manifest match is already present in the canonical or retry archive", flush=True)
        return 0
    run = {"started_at": datetime.now(timezone.utc).isoformat(), "season": 2025,
           "route": "visible tournament > round selector > exact finished fixture card > Player stats > six categories",
           "viewport": "1440x1000", "timezone": "Asia/Shanghai", "locale": "en-GB",
           "headed": not args.headless, "requested": len(targets), "results": [],
           "python": platform.python_version(), "scrapling": version("scrapling"),
           "playwright": version("playwright"), "browser_profile": str(PROFILE),
           "temp_dir": str(TEMP), "failure_statuses": ["identity_mismatch", "player_stats_missing",
           "category_missing", "load_timeout", "page_shell_only", "parse_failure",
           "manual_verification_required"]}
    print(f"queue={len(targets)} previously_validated={len(originals)} retry_validated={len(captured)}", flush=True)
    challenged = False

    def action(page) -> None:
        nonlocal challenged
        run["browser_version"] = getattr(page.context.browser, "version", "unavailable")
        for index, mid in enumerate(targets, 1):
            fixture = manifest[mid]
            result = {"match_id": mid, "round": fixture["round"]}
            try:
                if index > 1:
                    page.wait_for_timeout(1200)
                entry = collect_match(page, fixture)
                captured[mid] = entry
                write_jsonl(RETRY_RAW, captured, manifest)
                result.update({"status": "validated", "general_rows": entry["general_player_count"],
                               "category_rows": {c: len(entry["categories"][c]["rows"]) for c in CATEGORIES},
                               "route": entry["route"]})
            except Exception as exc:
                result.update({"status": classify_collection_failure(exc),
                               "failure_class": classify_collection_failure(exc),
                               "error": f"{type(exc).__name__}: {exc}", "last_url": page.url})
                folder = EVIDENCE / f"match_{mid}"
                folder.mkdir(parents=True, exist_ok=True)
                try:
                    body = page.locator("body").inner_text()
                    (folder / "failure.txt").write_text(body, encoding="utf-8")
                    (folder / "failure.html").write_text(page.content(), encoding="utf-8")
                    page.screenshot(path=str(folder / "failure.png"), full_page=False)
                    result["status"] = classify_collection_failure(exc, body_text=body)
                    result["failure_class"] = result["status"]
                except Exception:
                    pass
                with FAILURES.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({**result, "observed_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False) + "\n")
            run["results"].append(result)
            run["validated"] = sum(r["status"] == "validated" for r in run["results"])
            run["completed"] = len(run["results"])
            save_json(CHECKPOINT, run)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if result["status"] == "manual_verification_required":
                challenged = True
            if challenged:
                run["halted"] = "challenge_surface_for_manual_handling"
                break

    with DynamicSession(real_chrome=True, headless=args.headless, google_search=False,
                        network_idle=False, timeout=60000, retries=1, locale="en-GB",
                        timezone_id="Asia/Shanghai", disable_resources=False,
                        user_data_dir=str(PROFILE),
                        additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
        session.fetch(TOURNAMENT_URL, page_action=action)
    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["validated"] = sum(r["status"] == "validated" for r in run["results"])
    save_json(CHECKPOINT, run)
    print(json.dumps({"requested": len(targets), "validated_this_run": run["validated"],
                      "retry_validated_total": len(captured), "remaining": len(targets) - run["validated"],
                      "halted": run.get("halted")}, ensure_ascii=False))
    return 0 if run["validated"] == len(targets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
