"""Inspect the visible Sofascore 2026 CSL tournament schedule DOM."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/csl/season_2026/evidence"
TEMP = ROOT / "data/csl/season_2026/runtime_temp"
URL = "https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:90049,tab:matches"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(TEMP)
    report = {"requested_url": URL, "observed_at": datetime.now(timezone.utc).isoformat()}

    def inspect(page):
        page.wait_for_timeout(8000)
        report["final_url"] = page.url
        report["title"] = page.title()
        report["body_text"] = page.locator("body").inner_text()[:30000]
        report["comboboxes"] = page.locator('[role="combobox"]').evaluate_all(
            "es => es.map(e => ({text:e.innerText,aria:e.getAttribute('aria-label'),html:e.outerHTML}))")
        report["schedule_panel_links"] = page.locator('#tabpanel-list a[href*="/football/match/"]').evaluate_all(
            "as => as.map(a => ({href:a.href,text:a.innerText.trim().replace(/\\s+/g,' '),html:a.outerHTML}))")
        report["event_cards"] = page.locator('a[data-id][class*="event-hl-"]').evaluate_all(
            "as => as.map(a => ({id:a.dataset.id,href:a.href,text:a.innerText.trim().replace(/\\s+/g,' ')," 
            "teams:Array.from(a.querySelectorAll('img[alt]')).map(i=>i.alt)," 
            "titles:Array.from(a.querySelectorAll('[title]')).map(e=>e.getAttribute('title'))," 
            "scores:Array.from(a.querySelectorAll('.score')).map(e=>e.innerText.trim())}))")
        boxes = page.locator('[role="combobox"]')
        if boxes.count() >= 2:
            boxes.nth(1).click()
            page.wait_for_timeout(300)
            report["schedule_options"] = page.get_by_role("option").all_text_contents()
            report["open_menu_snapshot"] = page.locator("body").aria_snapshot()[-12000:]
            page.keyboard.press("Escape")
        report["match_links"] = page.locator('a[href*="/football/match/"]').evaluate_all(
            "as => as.map(a => ({href:a.href,text:a.innerText.trim().replace(/\\s+/g,' '),html:a.outerHTML}))")
        report["challenge_indicators"] = [term for term in (
            "verify you are human", "captcha", "robot or human", "checking your browser")
            if term.lower() in report["body_text"].lower()]
        report["aria_snapshot"] = page.locator("body").aria_snapshot()[:30000]
        (OUT / "schedule_probe.html").write_text(page.content(), encoding="utf-8")

    with DynamicSession(real_chrome=True, headless=False, google_search=False,
                        network_idle=False, timeout=60000, retries=1,
                        locale="en-GB", timezone_id="Asia/Shanghai",
                        disable_resources=False,
                        user_data_dir=str(ROOT / "data/csl/season_2026/browser_profile"),
                        additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
        response = session.fetch(URL, page_action=inspect)
        try:
            report["response_status"] = response.status
        except Exception as exc:
            report["response_status_error"] = f"{type(exc).__name__}: {exc}"
    (OUT / "schedule_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("final_url", "title", "comboboxes", "schedule_options",
                                             "event_cards", "challenge_indicators", "response_status")
                      if k in report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
