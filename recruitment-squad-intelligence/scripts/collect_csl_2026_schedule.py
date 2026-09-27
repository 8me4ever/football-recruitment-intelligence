"""Collect the visible 2026 CSL tournament-round fixture cards with Scrapling."""
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
EVIDENCE = DATA / "evidence/round_cards"
TEMP = DATA / "runtime_temp"
URL = "https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:90049,tab:matches"
OUT = DATA / "csl_fixtures_2026.csv"
FIELDS = ("observed_on", "season_year", "round", "match_date", "competition", "competition_id",
          "competition_season_id", "match_id", "status", "home_team", "away_team", "home_goals",
          "away_goals", "source_url", "source")


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def save_manifest(rows: dict[str, dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows.values(), key=lambda x: (x["match_date"], x["round"], x["match_id"])))
    tmp.replace(OUT)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    TEMP.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    run = {"requested_url": URL, "observed_at": datetime.now(timezone.utc).isoformat(),
           "rounds_requested": 30, "rounds": [], "failures": []}
    rows: dict[str, dict] = {}

    def collect_rounds(page) -> None:
        season = page.get_by_role("combobox", name="Select season in unique tournament header", exact=True)
        round_box = page.get_by_role("combobox", name="Select item in event list", exact=True)
        season.wait_for(state="visible", timeout=30000)
        if "2026" not in season.inner_text():
            raise RuntimeError(f"wrong selected season: {season.inner_text()!r}")
        for round_no in range(1, 31):
            wanted = f"Round {round_no}"
            current = round_box.inner_text().strip()
            before_ids = page.locator('a[data-id][class*="event-hl-"]').evaluate_all(
                "as => as.map(a => a.dataset.id).sort().join('|')")
            if current != wanted:
                round_box.click()
                page.get_by_role("option", name=wanted, exact=True).click()
                page.wait_for_function("""arg => {
                  const b=Array.from(document.querySelectorAll('[role="combobox"]'))
                    .find(e=>e.innerText.trim()===arg.round);
                  const ids=Array.from(document.querySelectorAll('a[data-id][class*="event-hl-"]'))
                    .map(a=>a.dataset.id).sort().join('|');
                  return Boolean(b && ids && ids!==arg.before);
                }""", arg={"round": wanted, "before": before_ids}, timeout=20000)
            page.wait_for_timeout(250)
            selected = round_box.inner_text().strip()
            if selected != wanted:
                raise RuntimeError(f"selector mismatch: expected {wanted}, found {selected!r}")
            body = page.locator("body").inner_text()
            if any(x in body.lower() for x in ("verify you are human", "captcha", "checking your browser")):
                raise RuntimeError("challenge_or_manual_verification_surface_detected")
            cards = page.locator('a[data-id][class*="event-hl-"]').evaluate_all("""as => as.map(a => {
              const text=a.innerText.trim().replace(/\\s+/g,' ');
              const rawDate=(text.match(/\\b\\d{2}\\/\\d{2}\\/\\d{2,4}\\b/)||[])[0]||'';
              const titles=Array.from(a.querySelectorAll('[title]')).map(e=>e.getAttribute('title')).filter(Boolean);
              const scores=Array.from(a.querySelectorAll('.score')).map(e=>e.innerText.trim()).filter(Boolean);
              const nums=scores.filter(x=>/^\\d+$/.test(x));
              return {match_id:a.dataset.id,href:a.href,text,team_alts:Array.from(a.querySelectorAll('img[alt]')).map(i=>i.alt).filter(Boolean),
                raw_date:rawDate,status:titles[0]||'',score_tokens:scores,numeric_scores:nums,html:a.outerHTML};
            })""")
            if not cards:
                raise RuntimeError(f"no visible event cards in {wanted}")
            round_path = EVIDENCE / f"round_{round_no:02d}.json"
            parsed_cards = []
            for card in cards:
                mid = str(card["match_id"])
                url_match = re.search(r"#id:(\d+)", card["href"])
                if not url_match or url_match.group(1) != mid:
                    raise RuntimeError(f"event ID / URL mismatch in {wanted}: {mid}, {card['href']}")
                teams = card["team_alts"][:2]
                if len(teams) != 2 or teams[0] == teams[1]:
                    raise RuntimeError(f"expected two team crests for {mid}: {teams}")
                if not card["raw_date"]:
                    raise RuntimeError(f"missing visible date on card {mid}: {card['text']}")
                match_date = datetime.strptime(card["raw_date"], "%d/%m/%y" if len(card["raw_date"].split("/")[-1]) == 2 else "%d/%m/%Y").date().isoformat()
                status = (card["status"] or "").strip()
                if status in ("", "-", "—"):
                    status = "scheduled"
                goals = card["numeric_scores"][-2:] if status.upper() in ("FT", "AET", "PEN", "PENS") else []
                fixture = {"observed_on": date.today().isoformat(), "season_year": "2026",
                    "round": str(round_no), "match_date": match_date, "competition": "Chinese Super League",
                    "competition_id": "649", "competition_season_id": "90049", "match_id": mid,
                    "status": "finished" if status.upper() in ("FT", "AET", "PEN", "PENS") else status.lower(),
                    "home_team": teams[0], "away_team": teams[1], "home_goals": goals[0] if len(goals)==2 else "",
                    "away_goals": goals[1] if len(goals)==2 else "", "source_url": card["href"],
                    "source": "Sofascore rendered tournament round card"}
                if mid in rows and (rows[mid]["home_team"], rows[mid]["away_team"], rows[mid]["match_date"]) != (teams[0], teams[1], match_date):
                    raise RuntimeError(f"conflicting duplicate fixture ID {mid}")
                rows[mid] = fixture
                parsed_cards.append({**card, "fixture": fixture})
            atomic_json(round_path, {"round": round_no, "selected_round": selected,
                       "observed_at": datetime.now(timezone.utc).isoformat(), "cards": parsed_cards,
                       "page_url": page.url})
            save_manifest(rows)
            round_summary = {"round": round_no, "cards": len(cards), "unique_fixtures": len(rows),
                             "finished": sum(x["status"] == "finished" for x in rows.values())}
            run["rounds"].append(round_summary)
            run["last_round"] = round_no
            run["unique_fixtures"] = len(rows)
            atomic_json(EVIDENCE / "latest_schedule_run.json", run)
            print(json.dumps(round_summary, ensure_ascii=False), flush=True)

    def action(page) -> None:
        try:
            collect_rounds(page)
        except Exception as exc:
            run["failures"].append({"round": run.get("last_round", 0) + 1,
                                    "error": f"{type(exc).__name__}: {exc}"})
            atomic_json(EVIDENCE / "latest_schedule_run.json", run)
            print(json.dumps(run["failures"][-1], ensure_ascii=False), flush=True)
            raise

    try:
        with DynamicSession(real_chrome=True, headless=False, google_search=False, network_idle=False,
                            timeout=60000, retries=1, locale="en-GB", timezone_id="Asia/Shanghai",
                            disable_resources=False,
                            user_data_dir=str(DATA / "browser_profile"),
                            additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
            response = session.fetch(URL, page_action=action)
            try:
                run["response_status"] = response.status
            except Exception:
                pass
    except Exception as exc:
        run["failures"].append({"round": run.get("last_round", 0) + 1,
                                "error": f"{type(exc).__name__}: {exc}"})
    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["unique_fixtures"] = len(rows)
    run["finished_fixtures"] = sum(x["status"] == "finished" for x in rows.values())
    atomic_json(EVIDENCE / "latest_schedule_run.json", run)
    print(json.dumps({"unique_fixtures": len(rows), "finished_fixtures": run["finished_fixtures"],
                      "rounds_collected": len(run["rounds"]), "failures": run["failures"]}, ensure_ascii=False))
    return 1 if run["failures"] or len(run["rounds"]) != 30 else 0


if __name__ == "__main__":
    raise SystemExit(main())
