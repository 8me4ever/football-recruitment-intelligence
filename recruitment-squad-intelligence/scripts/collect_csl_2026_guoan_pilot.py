"""Collect a validated 2026 Beijing Guoan fixture via rendered Sofascore webpage DOM."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'csl_2026_capture'
EVIDENCE = DATA / 'evidence'
RUNTIME_TEMP = DATA / 'runtime_temp'
PROFILE = ROOT / 'data/csl/season_2026/browser_profile'
CATEGORIES = ('General', 'Attacking', 'Defending', 'Passing', 'Duels', 'Goalkeeping')
FIXTURE = {
    'match_date': '2026-09-15',
    'home_team': 'Beijing Guoan',
    'away_team': 'Pohang Steelers',
    'home_goals': 3,
    'away_goals': 1,
    'competition': 'AFC Champions League Elite',
    'competition_id': 463,
    'competition_season_id': 99217,
    'round': 'East Region, Round 1',
    'source_url': 'https://www.sofascore.com/football/match/pohang-steelers-beijing-guoan/Brbsadd',
}


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def main():
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true', help='Run hidden; default opens a normal visible browser')
    args = parser.parse_args()
    RUNTIME_TEMP.mkdir(parents=True, exist_ok=True)
    PROFILE.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = str(RUNTIME_TEMP)
    os.environ['TMP'] = str(RUNTIME_TEMP)
    tempfile.tempdir = str(RUNTIME_TEMP)
    outcome = {'fixture': FIXTURE, 'observed_at': datetime.now(timezone.utc).isoformat(),
               'source': 'Sofascore rendered webpage DOM', 'parser_version': '2026-pilot-1'}

    def capture(page):
        page.wait_for_timeout(5000)
        body = page.locator('body').inner_text()
        outcome['debug_page'] = {'url': page.url, 'title': page.title(), 'body_text': body[:20000]}
        (EVIDENCE / 'guoan_pilot_prevalidation.html').write_text(page.content(), encoding='utf-8')
        (EVIDENCE / 'guoan_pilot_prevalidation.txt').write_text(body, encoding='utf-8')
        exp_date = datetime.strptime(FIXTURE['match_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        if exp_date not in body:
            raise ValueError(f'identity mismatch: page does not display {exp_date}')
        if FIXTURE['home_team'] not in body or FIXTURE['away_team'] not in body:
            raise ValueError('identity mismatch: expected teams not both present')
        if FIXTURE['competition'] not in body or 'Finished' not in body:
            raise ValueError('identity mismatch: competition or finished status missing')
        if f"{FIXTURE['home_goals']}  -  {FIXTURE['away_goals']}" not in body:
            raise ValueError('identity mismatch: score differs from schedule')
        stats = page.get_by_role('tab', name='Player stats', exact=True)
        if stats.count() != 1:
            raise RuntimeError(f'Player stats tab not found (tabs={page.get_by_role("tab").all_text_contents()})')
        stats.click()
        page.locator('table').first.wait_for(state='visible', timeout=30000)
        page.wait_for_function("() => Array.from(document.querySelectorAll('table')).some(t => t.querySelector('a[href*=\"/football/player/\"]'))", timeout=30000)
        categories = {}
        general_ids = set()
        for category in CATEGORIES:
            tab = page.get_by_role('tab', name=category, exact=True)
            if tab.count() != 1:
                categories[category] = {'status': 'category_tab_missing'}
                continue
            tab.click()
            page.wait_for_timeout(600)
            table_data = page.locator('table').evaluate_all('''tables => tables.map(t => ({
              headers:Array.from(t.querySelectorAll('thead th')).map(c=>c.innerText.trim()),
              rows:Array.from(t.querySelectorAll('tbody tr')).map(r=>{
                const cells=Array.from(r.querySelectorAll('td'));
                const player=r.querySelector('a[href*="/football/player/"]');
                const href=player?.getAttribute('href')||'';
                const id=href.match(/\\/(\\d+)$/)?.[1]||null;
                return {player_id:id,player_name:player?.innerText.trim()||null,player_href:href||null,
                  team_name:cells[0]?.querySelector('img[alt]')?.alt||null,
                  cells:cells.map(c=>({text:c.innerText.trim(),text_content:c.textContent.trim(),meters:Array.from(c.querySelectorAll('[role="meter"]')).map(m=>({value:m.getAttribute('aria-valuenow'),min:m.getAttribute('aria-valuemin'),max:m.getAttribute('aria-valuemax')}))}))};
              }).filter(r=>r.player_id)}
            )).filter(t=>t.rows.length>0)''')
            if len(table_data) != 1:
                categories[category] = {'status': 'table_ambiguous_or_missing', 'tables': table_data}
                continue
            rows = table_data[0]['rows']
            team_names = {r['team_name'] for r in rows if r['team_name']}
            if team_names != {FIXTURE['home_team'], FIXTURE['away_team']}:
                raise ValueError(f'{category} table team mismatch: {sorted(team_names)}')
            if category == 'General':
                general_ids = {r['player_id'] for r in rows}
                if len(rows) < 15 or len(general_ids) != len(rows):
                    raise ValueError(f'incomplete General roster: rows={len(rows)} unique={len(general_ids)}')
            categories[category] = {'status': 'validated', **table_data[0]}
        if not general_ids:
            raise ValueError('General player table failed validation')
        entry = {**FIXTURE, 'match_id': (page.url.split('#id:')[-1] if '#id:' in page.url else None),
                 'source_url': page.url, 'observed_at': datetime.now(timezone.utc).isoformat(),
                 'general_player_count': len(general_ids), 'general_player_ids': sorted(general_ids),
                 'categories': categories}
        entry['evidence_sha256'] = hashlib.sha256(json.dumps(categories, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        outcome.update({'status': 'validated', 'match': entry})
        raw = DATA / 'raw' / f"match_{entry['match_id'] or 'unresolved'}_Brbsadd.json"
        atomic_json(raw, entry)
        outcome['raw_record'] = str(raw)
        outcome['category_row_counts'] = {k: len(v.get('rows', [])) for k, v in categories.items()}
        (EVIDENCE / 'guoan_pilot_16863671_rendered.html').write_text(page.content(), encoding='utf-8')
        (EVIDENCE / 'guoan_pilot_16863671_accessibility.txt').write_text(page.locator('body').aria_snapshot(), encoding='utf-8')
        page.screenshot(path=str(EVIDENCE / 'guoan_pilot_16863671_player_stats.png'), full_page=True)

    started = time.monotonic()
    try:
        with DynamicSession(real_chrome=True, headless=args.headless, google_search=False, network_idle=False,
                            timeout=60000, retries=1, locale='en-GB', timezone_id='Asia/Shanghai',
                            disable_resources=False, user_data_dir=str(PROFILE),
                            additional_args={'viewport': {'width': 1440, 'height': 1000}}) as session:
            response = session.fetch(FIXTURE['source_url'], page_action=capture)
            outcome['http_status'] = response.status
    except Exception as exc:
        outcome.update({'status': 'failed', 'error': f'{type(exc).__name__}: {exc}'})
    outcome['elapsed_seconds'] = round(time.monotonic() - started, 2)
    atomic_json(EVIDENCE / 'guoan_pilot_run.json', outcome)
    print(json.dumps({k: v for k, v in outcome.items() if k != 'match'}, ensure_ascii=False, indent=2))
    return 0 if outcome.get('status') == 'validated' else 1


if __name__ == '__main__':
    raise SystemExit(main())
