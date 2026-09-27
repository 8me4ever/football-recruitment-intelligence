"""Collect rendered 2026/27 AFC fixture cards involving 2026 CSL clubs."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/season_2026"
TEMP = DATA / "runtime_temp"
EVIDENCE = DATA / "evidence/afc_round_cards"
CLUBS_FILE = DATA / "csl_fixtures_2026.csv"
OUT = DATA / "afc_fixtures_2026_27_in_scope.csv"
TOURNAMENTS = (
    {"key": "elite", "name": "AFC Champions League Elite", "competition_id": "463",
     "season_id": "99217", "url": "https://www.sofascore.com/football/tournament/asia/afc-champions-league/463#id:99217,tab:matches"},
    {"key": "two", "name": "AFC Champions League Two", "competition_id": "668",
     "season_id": "97465", "url": "https://www.sofascore.com/football/tournament/asia/afc-cup/668#tab:matches,id:97465"},
)
FIELDS = ("observed_on", "season_year", "competition", "competition_id", "competition_season_id",
          "round", "match_date", "match_id", "status", "home_team", "away_team", "home_goals",
          "away_goals", "source_url", "source")


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    clubs: set[str] = set()
    with CLUBS_FILE.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            clubs.update((row["home_team"], row["away_team"]))
    TEMP.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    found: dict[str, dict[str, str]] = {}
    run = {"observed_at": datetime.now(timezone.utc).isoformat(), "club_filter": sorted(clubs),
           "tournaments": [], "failures": []}

    def collect_tournament(page, config: dict) -> None:
        season = page.get_by_role("combobox", name="Select season in unique tournament header", exact=True)
        round_box = page.get_by_role("combobox", name="Select item in event list", exact=True)
        season.wait_for(state="visible", timeout=30000)
        if season.inner_text().strip() != "26/27":
            raise RuntimeError(f"{config['key']}: wrong AFC season {season.inner_text()!r}")
        round_box.click()
        options = page.get_by_role("option").all_text_contents()
        page.keyboard.press("Escape")
        result = {"key": config["key"], "competition": config["name"], "season": season.inner_text(),
                  "options": options, "rounds": [], "target_fixture_ids": []}
        if not options or len(set(options)) != len(options):
            raise RuntimeError(f"{config['key']}: invalid/empty round options {options}")
        for label in options:
            previous_ids = page.locator('a[data-id][class*="event-hl-"]').evaluate_all(
                "as=>as.map(a=>a.dataset.id).sort().join('|')")
            if round_box.inner_text().strip() != label:
                round_box.click()
                page.get_by_role("option", name=label, exact=True).click()
                if label == "Preliminary":
                    page.wait_for_function("label=>Array.from(document.querySelectorAll('[role=combobox]')).some(x=>x.innerText.trim()===label)", arg=label, timeout=20000)
                    page.wait_for_timeout(1800)
                else:
                    page.wait_for_function("""arg=>{
                      const b=Array.from(document.querySelectorAll('[role="combobox"]')).find(x=>x.innerText.trim()===arg.label);
                      const cards=Array.from(document.querySelectorAll('a[data-id][class*="event-hl-"]'));
                      const ids=cards.map(a=>a.dataset.id).sort().join('|');
                      return Boolean(b && cards.length>=16 && ids!==arg.before);
                    }""", arg={"label": label, "before": previous_ids}, timeout=30000)
            if label != "Preliminary":
                page.wait_for_timeout(500)
            cards = page.locator('a[data-id][class*="event-hl-"]').evaluate_all("""as=>as.map(a=>{
              const text=a.innerText.trim().replace(/\\s+/g,' ');
              const rawDate=(text.match(/\\b\\d{2}\\/\\d{2}\\/\\d{2,4}\\b/)||[])[0]||'';
              const titles=Array.from(a.querySelectorAll('[title]')).map(e=>e.getAttribute('title')).filter(Boolean);
              const scoreTokens=Array.from(a.querySelectorAll('.score')).map(e=>e.innerText.trim()).filter(Boolean);
              return {match_id:a.dataset.id,href:a.href,text,team_alts:Array.from(a.querySelectorAll('img[alt]')).map(i=>i.alt).filter(Boolean),
                raw_date:rawDate,status:titles[0]||'',score_tokens:scoreTokens,
                numeric_scores:scoreTokens.filter(x=>/^\\d+$/.test(x)),html:a.outerHTML};
            })""")
            if label != "Preliminary" and len(cards) < 16:
                raise RuntimeError(f"{config['key']} {label}: expected 16 visible event cards, found {len(cards)}")
            in_scope = []
            for card in cards:
                teams = card["team_alts"][:2]
                if len(teams) != 2:
                    continue
                if not any(team in clubs for team in teams):
                    continue
                mid = str(card["match_id"])
                parsed = re.search(r"#id:(\d+)", card["href"])
                if not parsed or parsed.group(1) != mid:
                    raise RuntimeError(f"{config['key']} {label}: event URL/ID mismatch for {mid}")
                if not card["raw_date"]:
                    raise RuntimeError(f"{config['key']} {mid}: visible match date missing")
                match_date = datetime.strptime(card["raw_date"], "%d/%m/%y" if len(card["raw_date"].split("/")[-1]) == 2 else "%d/%m/%Y").date().isoformat()
                raw_status = (card["status"] or "").strip()
                if raw_status in ("", "-", "—"):
                    raw_status = "scheduled"
                goals = card["numeric_scores"][-2:] if raw_status.upper() in ("FT", "AET", "PEN", "PENS") else []
                fixture = {"observed_on": date.today().isoformat(), "season_year": "2026",
                    "competition": config["name"], "competition_id": config["competition_id"],
                    "competition_season_id": config["season_id"], "round": label,
                    "match_date": match_date, "match_id": mid,
                    "status": "finished" if raw_status.upper() in ("FT", "AET", "PEN", "PENS") else raw_status.lower(),
                    "home_team": teams[0], "away_team": teams[1],
                    "home_goals": goals[0] if len(goals)==2 else "", "away_goals": goals[1] if len(goals)==2 else "",
                    "source_url": card["href"], "source": "Sofascore rendered AFC tournament round card"}
                old = found.get(mid)
                if old and old != fixture:
                    raise RuntimeError(f"duplicate AFC event ID has conflicting fixture values: {mid}")
                found[mid] = fixture
                in_scope.append({**card, "fixture": fixture})
            evidence = {"tournament": config["name"], "round": label,
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                        "page_url": page.url, "visible_card_count": len(cards),
                        "all_cards": cards, "in_scope_cards": in_scope}
            atomic_json(EVIDENCE / f"{config['key']}_{re.sub('[^A-Za-z0-9]+','_',label)}.json", evidence)
            result["rounds"].append({"round": label, "visible_cards": len(cards), "in_scope_cards": len(in_scope)})
            result["target_fixture_ids"].extend(x["fixture"]["match_id"] for x in in_scope)
            run["current_tournament"] = config["key"]
            run["current_round"] = label
            atomic_json(EVIDENCE / "latest_afc_schedule_run.json", {**run, "tournaments": run["tournaments"] + [result]})
            print(json.dumps({"tournament": config["key"], "round": label,
                              "visible_cards": len(cards), "in_scope_cards": len(in_scope)}, ensure_ascii=False), flush=True)
        result["target_fixture_ids"] = sorted(set(result["target_fixture_ids"]))
        run["tournaments"].append(result)

    try:
        with DynamicSession(real_chrome=True, headless=False, google_search=False, network_idle=False,
                            timeout=60000, retries=1, locale="en-GB", timezone_id="Asia/Shanghai",
                            disable_resources=False, user_data_dir=str(DATA / "browser_profile_afc"),
                            additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
            for config in TOURNAMENTS:
                session.fetch(config["url"], page_action=lambda page, c=config: collect_tournament(page, c))
    except Exception as exc:
        run["failures"].append({"error": f"{type(exc).__name__}: {exc}",
                                "tournament": run.get("current_tournament"),
                                "round": run.get("current_round")})
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(found.values(), key=lambda x: (x["match_date"], x["competition"], x["round"], x["match_id"])))
    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["in_scope_fixture_count"] = len(found)
    run["in_scope_finished_count"] = sum(x["status"] == "finished" for x in found.values())
    run["in_scope_fixture_ids"] = sorted(found)
    atomic_json(EVIDENCE / "latest_afc_schedule_run.json", run)
    print(json.dumps({"in_scope_fixtures": len(found), "finished": run["in_scope_finished_count"],
                      "failures": run["failures"], "by_competition": {
                          config["name"]: sum(x["competition"] == config["name"] for x in found.values())
                          for config in TOURNAMENTS}}, ensure_ascii=False))
    return 1 if run["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
