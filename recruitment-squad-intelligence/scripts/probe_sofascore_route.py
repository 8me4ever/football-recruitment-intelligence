"""Compare rendered webpage navigation routes without API calls."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from datetime import datetime, timezone
from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]

def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label', required=True)
    p.add_argument('--url', required=True)
    p.add_argument('--via-team', action='store_true')
    p.add_argument('--headed', action='store_true')
    p.add_argument('--width', type=int, default=1440)
    a = p.parse_args()
    if not a.label.replace('-', '').replace('_', '').isalnum():
        p.error('Invalid label')
    if not a.url.startswith('https://www.sofascore.com/football/match/') or '#id:' not in a.url:
        p.error('Expected a Sofascore match webpage URL with event ID')
    out = ROOT / 'csl_2026_capture' / a.label
    out.mkdir(parents=True, exist_ok=True)
    temp = ROOT / 'csl_2026_capture/runtime_temp'
    temp.mkdir(exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = tempfile.tempdir = str(temp)
    report = {'requested_url': a.url, 'observed_at': datetime.now(timezone.utc).isoformat(),
              'width': a.width, 'headed': a.headed, 'via_team': a.via_team, 'stages': [], 'status': 'pending'}

    def snapshot(page, name):
        body = page.locator('body').inner_text()
        (out / f'{name}.txt').write_text(body, encoding='utf-8')
        (out / f'{name}.html').write_text(page.content(), encoding='utf-8')
        (out / f'{name}.yaml').write_text(page.locator('body').aria_snapshot(), encoding='utf-8')
        stage = {'name': name, 'url': page.url, 'title': page.title(), 'text_length': len(body),
                 'tabs': page.get_by_role('tab').all_text_contents(),
                 'tables': page.locator('table').count()}
        report['stages'].append(stage)
        print(json.dumps(stage, ensure_ascii=False), flush=True)

    def capture(page):
        try:
            if a.via_team:
                page.wait_for_timeout(8000)
                snapshot(page, 'team')
                finished = page.get_by_role('tab', name='Finished', exact=True)
                if finished.count() == 1:
                    finished.click()
                    page.wait_for_timeout(3000)
                    snapshot(page, 'finished')
                href = a.url.removeprefix('https://www.sofascore.com')
                link = page.locator('a[href]').filter(has_text='')
                links = page.locator('a[href]').evaluate_all('(aa)=>aa.map(a=>({href:a.getAttribute("href"),text:a.innerText}))')
                report['team_match_links'] = [x for x in links if '/football/match/' in x['href']]
                target = page.locator(f'#tabpanel-list a[href="{href}"]').filter(has_text='FT')
                if target.count() != 1:
                    raise ValueError(f'Expected unique rendered fixture link, got {target.count()}')
                target.click()
            for seconds, delay in [(5, 5), (15, 10), (30, 15)]:
                page.wait_for_timeout(delay * 1000)
                snapshot(page, f'match_{seconds}')
            report['status'] = 'observed'
            page.screenshot(path=str(out / 'page.png'), full_page=False)
        except Exception as e:
            report.update(status='failed', error=f'{type(e).__name__}: {e}')
            snapshot(page, 'failure')

    try:
        with DynamicSession(real_chrome=True, headless=not a.headed, google_search=False,
                            network_idle=False, timeout=60000, retries=1, locale='en-GB',
                            timezone_id='Asia/Shanghai', disable_resources=False,
                            additional_args={'viewport': {'width': a.width, 'height': 1000}}) as session:
            url = 'https://www.sofascore.com/football/team/beijing-guoan/3376#tab:matches' if a.via_team else a.url
            response = session.fetch(url, page_action=capture)
            report['http_status'] = response.status
    except Exception as e:
        report.update(status='failed', error=f'{type(e).__name__}: {e}')
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(out / 'run.json')}), flush=True)
    return 0 if report['status'] == 'observed' else 1

if __name__ == '__main__':
    raise SystemExit(main())
