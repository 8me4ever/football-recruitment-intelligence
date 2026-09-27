"""Open Beijing Guoan's Sofascore page in a persistent, visible F: browser profile."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/csl/season_2026'
EVIDENCE = DATA / 'evidence'
TEMP = DATA / 'runtime_temp'
PROFILE = DATA / 'browser_profile'
URL = 'https://www.sofascore.com/football/team/beijing-guoan/3376#id:3376,tab:matches'


def main():
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification-wait', type=int, default=180,
                        help='Maximum seconds to wait for a person to complete any visible verification')
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    PROFILE.mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = str(TEMP)
    os.environ['TMP'] = str(TEMP)
    tempfile.tempdir = str(TEMP)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    result = {'url': URL, 'observed_at': datetime.now(timezone.utc).isoformat()}

    def action(page):
        try:
            import sys
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
        page.wait_for_timeout(6000)
        initial_text = page.locator('body').inner_text()
        result['challenge_visible_initially'] = 'Verify you are human' in initial_text
        if result['challenge_visible_initially']:
            print('A verification page is visible. Complete it in the open Chrome window if prompted; waiting without automating it.', flush=True)
            deadline = time.monotonic() + args.verification_wait
            while time.monotonic() < deadline:
                page.wait_for_timeout(1000)
                if 'Verify you are human' not in page.locator('body').inner_text():
                    break
            result['challenge_cleared_by_user'] = 'Verify you are human' not in page.locator('body').inner_text()
        page.wait_for_timeout(2000)
        result['title'] = page.title()
        result['url_after_load'] = page.url
        result['body_text'] = page.locator('body').inner_text()[:20000]
        result['match_links'] = page.locator('a[href*="/football/match/"]').evaluate_all(
            "as=>as.map(a=>({href:a.href,text:a.innerText,html:a.outerHTML}))")
        result['screenshot'] = str(EVIDENCE / 'season_2026_probe.png')
        result['comboboxes'] = page.get_by_role('combobox').evaluate_all(
            "es=>es.map(e=>({text:e.innerText,label:e.getAttribute('aria-label'),html:e.outerHTML}))")
        result['buttons'] = page.get_by_role('button').evaluate_all(
            "es=>es.map(e=>({text:e.innerText,label:e.getAttribute('aria-label'),disabled:e.disabled,html:e.outerHTML.slice(0,600)}))")
        for index in range(page.get_by_role('combobox').count()):
            box = page.get_by_role('combobox').nth(index)
            try:
                box.click(timeout=2000)
                page.wait_for_timeout(300)
                result['filter_options'] = page.get_by_role('option').all_text_contents()
                result['filter_menu_snapshot'] = page.locator('body').aria_snapshot()[:12000]
                competition = page.get_by_role('option', name='Chinese Super League', exact=True)
                if competition.count():
                    competition.click(timeout=2000)
                    page.wait_for_timeout(3000)
                    result['selected_filter_body'] = page.locator('body').inner_text()[:10000]
                    result['selected_filter_links'] = page.locator('a[href*="/football/match/"]').evaluate_all(
                        "as=>as.map(a=>({href:a.href,text:a.innerText,html:a.outerHTML}))")
                else:
                    box.press('Escape')
                break
            except Exception as error:
                result['filter_error'] = str(error)[:1500]
                try:
                    page.keyboard.press('Escape')
                except Exception:
                    pass
        page.wait_for_timeout(500)
        page.screenshot(path=result['screenshot'], full_page=False)
        result['html'] = page.content()
        result['tabs'] = page.locator('[role="tab"], [role="link"]').evaluate_all(
            "es=>es.map(e=>({role:e.getAttribute('role'),text:e.innerText,href:e.getAttribute('href')}))")
        result['accessibility'] = page.locator('body').aria_snapshot()[:40000]

    with DynamicSession(real_chrome=True, headless=False, google_search=False, network_idle=False,
                        timeout=60000, retries=1, locale='en-GB', timezone_id='Asia/Shanghai',
                        disable_resources=False, user_data_dir=str(PROFILE),
                        additional_args={'viewport': {'width': 1440, 'height': 1000}}) as session:
        session.fetch(URL, page_action=action)

    html = result.pop('html', '')
    (EVIDENCE / 'season_2026_probe.html').write_text(html, encoding='utf-8')
    (EVIDENCE / 'season_2026_probe.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('accessibility', 'html')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
