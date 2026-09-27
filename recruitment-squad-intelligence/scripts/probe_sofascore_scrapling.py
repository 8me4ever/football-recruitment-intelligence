"""Bounded webpage-only Scrapling probe; no API requests or response capture."""
import argparse
import json
import platform
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from scrapling.fetchers import DynamicFetcher


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='https://www.sofascore.com/football/match/meizhou-hakka-beijing-guoan/BrbsLdLb#id:13522670')
    parser.add_argument('--label', default='13522670')
    args = parser.parse_args()
    if not args.url.startswith('https://www.sofascore.com/football/') or '/api/' in args.url:
        parser.error('Only Sofascore football webpage URLs are supported')
    if not args.label.replace('-', '').replace('_', '').isalnum():
        parser.error('Unsafe label')
    out = Path('data/csl/scrapling_probe') / args.label
    out.mkdir(parents=True, exist_ok=True)
    report = {'url_requested': args.url, 'observed_at': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(), 'scrapling': version('scrapling'),
              'playwright': version('playwright'), 'snapshots': []}

    def action(page):
        report['browser_version'] = page.context.browser.version
        # Preserve timed snapshots to distinguish initial shell from hydration.
        for seconds in (5, 15, 30):
            page.wait_for_timeout((seconds - (report['snapshots'][-1]['seconds'] if report['snapshots'] else 0)) * 1000)
            body = page.locator('body').inner_text()
            (out / f'visible_{seconds}.txt').write_text(body, encoding='utf-8')
            report['snapshots'].append({'seconds': seconds, 'title': page.title(), 'url': page.url,
                                        'text_length': len(body), 'tables': page.locator('table').count()})
        (out / 'rendered.html').write_text(page.content(), encoding='utf-8')
        (out / 'accessibility.yaml').write_text(page.locator('body').aria_snapshot(), encoding='utf-8')
        page.screenshot(path=str(out / 'page.png'), full_page=True)
        tables = page.locator('table').evaluate_all('(tables) => tables.map(t => ({text:t.innerText, html:t.outerHTML}))')
        (out / 'tables.json').write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding='utf-8')
        stats = page.get_by_role('tab', name='Player stats', exact=True)
        if stats.count() == 1:
            stats.click()
            page.locator('table').first.wait_for(state='visible', timeout=30000)
            page.wait_for_timeout(2000)
            (out / 'player_stats.html').write_text(page.content(), encoding='utf-8')
            (out / 'player_stats.yaml').write_text(page.locator('body').aria_snapshot(), encoding='utf-8')
            rows = page.locator('table').evaluate_all('''tables => tables.map(t => ({
                headers: Array.from(t.querySelectorAll('thead th')).map(c=>c.innerText),
                rows: Array.from(t.querySelectorAll('tbody tr')).map(r=>({
                    cells:Array.from(r.querySelectorAll('td')).map(c=>c.innerText),
                    links:Array.from(r.querySelectorAll('a[href]')).map(a=>({text:a.innerText,href:a.getAttribute('href')}))
                }))}))''')
            (out / 'player_tables.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
            report['player_table_rows'] = [len(t['rows']) for t in rows]
            page.screenshot(path=str(out / 'player_stats.png'), full_page=True)
            categories = {}
            for category in ('General', 'Attacking', 'Defending', 'Passing', 'Duels', 'Goalkeeping'):
                tab = page.get_by_role('tab', name=category, exact=True)
                if tab.count() != 1:
                    categories[category] = {'status': 'tab_not_found'}
                    continue
                tab.click()
                page.wait_for_timeout(2000)
                data = page.locator('table').evaluate_all('''tables => tables.map(t => ({
                    headers: Array.from(t.querySelectorAll('thead th')).map(c=>c.innerText),
                    rows: Array.from(t.querySelectorAll('tbody tr')).map(r=>({
                        cells:Array.from(r.querySelectorAll('td')).map(c=>({text:c.innerText, text_content:c.textContent, meters:Array.from(c.querySelectorAll('[role="meter"]')).map(m=>({value:m.getAttribute('aria-valuenow'),min:m.getAttribute('aria-valuemin'),max:m.getAttribute('aria-valuemax')})), images:Array.from(c.querySelectorAll('img')).map(i=>({alt:i.alt,src:i.getAttribute('src')}))})),
                        links:Array.from(r.querySelectorAll('a[href]')).map(a=>({text:a.innerText,href:a.getAttribute('href')}))
                    }))}))''')
                categories[category] = {'status': 'captured', 'tables': data}
                (out / f'{category}.html').write_text(page.content(), encoding='utf-8')
            (out / 'categories.json').write_text(json.dumps(categories, ensure_ascii=False, indent=2), encoding='utf-8')
            report['categories'] = {k: [len(t['rows']) for t in v.get('tables', [])] for k,v in categories.items()}

    started = time.monotonic()
    try:
        response = DynamicFetcher.fetch(args.url, real_chrome=True, headless=True,
            google_search=False, network_idle=False, timeout=60000, retries=1,
            locale='en-GB', timezone_id='Asia/Shanghai', disable_resources=False,
            additional_args={'viewport': {'width': 1440, 'height': 1000}}, page_action=action)
        report['http_status'] = response.status
        report['outcome'] = 'captured_for_review'
    except Exception as exc:
        report['outcome'] = 'error'
        report['error'] = f'{type(exc).__name__}: {exc}'
    report['elapsed_seconds'] = round(time.monotonic() - started, 2)
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 1 if report['outcome'] == 'error' else 0


if __name__ == '__main__':
    raise SystemExit(main())
