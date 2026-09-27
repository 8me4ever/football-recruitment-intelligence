"""Inspect rendered 2026/27 AFC tournament schedules and their visible controls."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/csl/season_2026/evidence/afc_probe"
TEMP = ROOT / "data/csl/season_2026/runtime_temp"
PAGES = {
    "elite": "https://www.sofascore.com/football/tournament/asia/afc-champions-league/463#id:99217,tab:matches",
    "two": "https://www.sofascore.com/football/tournament/asia/afc-cup/668#tab:matches",
}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    reports = []
    with DynamicSession(real_chrome=True, headless=False, google_search=False, network_idle=False,
                        timeout=60000, retries=1, locale="en-GB", timezone_id="Asia/Shanghai",
                        disable_resources=False, user_data_dir=str(ROOT / "data/csl/season_2026/browser_profile_afc"),
                        additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
        for name, url in PAGES.items():
            report = {"name": name, "requested_url": url, "observed_at": datetime.now(timezone.utc).isoformat()}
            def action(page):
                page.wait_for_timeout(7000)
                report["final_url"] = page.url
                report["title"] = page.title()
                report["body_text"] = page.locator("body").inner_text()[:25000]
                report["comboboxes"] = page.locator('[role="combobox"]').evaluate_all(
                    "es=>es.map(e=>({text:e.innerText,aria:e.getAttribute('aria-label')}))")
                report["event_cards"] = page.locator('a[data-id][class*="event-hl-"]').evaluate_all(
                    "as=>as.map(a=>({id:a.dataset.id,href:a.href,text:a.innerText.trim().replace(/\\s+/g,' '),teams:Array.from(a.querySelectorAll('img[alt]')).map(i=>i.alt)}))")
                report["all_data_cards"] = page.locator('a[data-id][href*="/football/match/"]').evaluate_all(
                    "as=>as.map(a=>({id:a.dataset.id,href:a.href,text:a.innerText.trim().replace(/\\s+/g,' '),className:a.className,teams:Array.from(a.querySelectorAll('img[alt]')).map(i=>i.alt)}))")
                report["team_links"] = page.locator('a[href*="/football/team/"]').evaluate_all(
                    "as=>as.map(a=>({href:a.href,text:a.innerText.trim()})).filter(a=>a.text)")
                report["challenge"] = any(x in report["body_text"].lower() for x in ("verify you are human", "captcha", "checking your browser"))
                boxes = page.locator('[role="combobox"]')
                if boxes.count() > 1:
                    for idx in range(boxes.count()):
                        try:
                            boxes.nth(idx).click()
                            page.wait_for_timeout(150)
                            options = page.get_by_role("option").all_text_contents()
                            if options:
                                report.setdefault("options", []).append({"control_index": idx, "options": options})
                            page.keyboard.press("Escape")
                        except Exception:
                            pass
                (OUT / f"{name}.html").write_text(page.content(), encoding="utf-8")
            response = session.fetch(url, page_action=action)
            try:
                report["response_status"] = response.status
            except Exception:
                pass
            reports.append(report)
            (OUT / f"{name}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({k: report.get(k) for k in ("name", "final_url", "title", "comboboxes", "options", "challenge", "event_cards", "all_data_cards", "response_status") if k in report}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
