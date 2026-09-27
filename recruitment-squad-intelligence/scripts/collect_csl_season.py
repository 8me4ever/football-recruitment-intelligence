"""Collect 2025 CSL fixtures and player statistics from rendered Sofascore pages only."""
from __future__ import annotations

import argparse
import hashlib
import csv
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from scrapling.fetchers import DynamicSession

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/csl/season_2025'
EVIDENCE = DATA / 'evidence'
RUNTIME_TEMP = DATA / 'runtime_temp'
BROWSER_PROFILE = DATA / 'browser_profile'
TOURNAMENT_URL = 'https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:71364,tab:matches'
CATEGORIES = ('General', 'Attacking', 'Defending', 'Passing', 'Duels', 'Goalkeeping')
MANIFEST_FIELDS = ('match_id', 'match_date', 'round', 'home_team', 'away_team', 'home_goals', 'away_goals',
                   'status', 'source', 'source_url', 'observed_on')


def configure_f_drive_runtime():
    """Keep Python temporary files and the persistent browser profile on F: drive."""
    RUNTIME_TEMP.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = str(RUNTIME_TEMP)
    os.environ['TMP'] = str(RUNTIME_TEMP)
    tempfile.tempdir = str(RUNTIME_TEMP)


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def probe_round_ui():
    """Inspect visible schedule UI and one round transition, without saving fixtures as complete."""
    report = {'observed_at': datetime.now(timezone.utc).isoformat(), 'rounds': []}

    def action(page):
        season = page.get_by_role('combobox', name='Select season in unique tournament header', exact=True)
        rounds = page.get_by_role('combobox', name='Select item in event list', exact=True)
        report['season_text'] = season.inner_text()
        report['round_before'] = rounds.inner_text()
        tabpanel = page.get_by_role('tabpanel').first
        report['sample_links_before'] = tabpanel.locator('a[href*="/football/match/"]').evaluate_all(
            'as => as.map(a => ({href:a.href,text:a.innerText,html:a.outerHTML}))')
        rounds.click()
        page.wait_for_timeout(300)
        report['menu_snapshot'] = page.locator('body').aria_snapshot()[:30000]
        report['menu_html'] = page.content()
        rounds.press('ArrowUp')
        rounds.press('Enter')
        page.wait_for_timeout(1200)
        report['round_after'] = rounds.inner_text()
        report['sample_links_after'] = tabpanel.locator('a[href*="/football/match/"]').evaluate_all(
            'as => as.map(a => ({href:a.href,text:a.innerText,html:a.outerHTML}))')

    with DynamicSession(real_chrome=True, headless=True, google_search=False, network_idle=False,
                        timeout=60000, retries=1, locale='en-GB', timezone_id='Asia/Shanghai',
                        disable_resources=False, user_data_dir=str(BROWSER_PROFILE),
                        additional_args={'viewport': {'width': 1440, 'height': 1000}}) as session:
        session.fetch(TOURNAMENT_URL, page_action=action)
    atomic_json(EVIDENCE / 'round_ui_probe.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'menu_html' and k != 'menu_snapshot'}, ensure_ascii=True, indent=2))


def collect_fixtures():
    """Walk all 30 round selectors in one browser session and save raw event-card DOM evidence."""
    ledger = {}
    diagnostics = []

    def action(page, expected_round):
        season = page.get_by_role('combobox', name='Select season in unique tournament header', exact=True)
        roundbox = page.get_by_role('combobox', name='Select item in event list', exact=True)
        if '2025' not in season.inner_text():
            raise RuntimeError(f'wrong season: {season.inner_text()}')
        tabpanel = page.get_by_role('tabpanel').first
        rows = tabpanel.locator('a[href*="/football/match/"]').evaluate_all('''as => as.map(a => ({
            href:a.href, text:a.innerText, html:a.outerHTML,
            teams:Array.from(a.querySelectorAll('img[alt]')).map(i=>i.alt)
        }))''')
        diagnostics.append({'round': expected_round, 'selected': roundbox.inner_text(), 'events': len(rows)})
        if f'Round {expected_round}' not in roundbox.inner_text():
            raise RuntimeError(f'round mismatch: wanted {expected_round}, got {roundbox.inner_text()}')
        for card in rows:
            match = re.search(r'#id:(\d+)', card['href'])
            if not match:
                continue
            mid = match.group(1)
            ledger[mid] = {'match_id': mid, 'href': card['href'], 'card_text': card['text'],
                           'team_alts': card['teams'], 'card_html': card['html'],
                           'selected_round': expected_round,
                           'observed_at': datetime.now(timezone.utc).isoformat()}

    def page_action(page):
        season = page.get_by_role('combobox', name='Select season in unique tournament header', exact=True)
        roundbox = page.get_by_role('combobox', name='Select item in event list', exact=True)
        if '2025' not in season.inner_text():
            raise RuntimeError(f'wrong season: {season.inner_text()}')
        # Start from the live last-round selection, then move one keyboard item per round.
        for expected_round in range(30, 0, -1):
            if expected_round != 30:
                previous_ids = tabpanel.locator('a[href*="/football/match/"]').evaluate_all(
                    "as => as.map(a => a.href).sort().join('|')")
                roundbox.click()
                roundbox.press('ArrowUp')
                roundbox.press('Enter')
                page.wait_for_function('''arg => {
                    const boxes = Array.from(document.querySelectorAll('[role="combobox"]'));
                    const panel = document.querySelector('[role="tabpanel"]');
                    if (!boxes.some(e => e.innerText.includes(`Round ${arg.round}`)) || !panel) return false;
                    const ids = Array.from(panel.querySelectorAll('a[href*="/football/match/"]'))
                      .map(a => a.href).sort().join('|');
                    return ids && ids !== arg.previous;
                }''', arg={'round': expected_round, 'previous': previous_ids}, timeout=15000)
                # Confirm the selected round and card signature remain stable briefly.
                page.wait_for_timeout(300)
            action(page, expected_round)
            if len(ledger) >= 1:
                atomic_json(EVIDENCE / 'fixture_event_ledger.json', list(ledger.values()))
                atomic_json(EVIDENCE / 'fixture_round_checkpoint.json',
                            {'last_round': expected_round, 'unique_events': len(ledger), 'rounds': diagnostics})

    with DynamicSession(real_chrome=True, headless=True, google_search=False, network_idle=False,
                        timeout=60000, retries=1, locale='en-GB', timezone_id='Asia/Shanghai',
                        disable_resources=False, user_data_dir=str(BROWSER_PROFILE),
                        additional_args={'viewport': {'width': 1440, 'height': 1000}}) as session:
        session.fetch(TOURNAMENT_URL, page_action=page_action)
    atomic_json(EVIDENCE / 'fixture_event_ledger.json', list(ledger.values()))
    atomic_json(EVIDENCE / 'fixture_round_checkpoint.json', {'last_round': 1, 'unique_events': len(ledger), 'rounds': diagnostics})
    print(json.dumps({'unique_events': len(ledger), 'rounds': diagnostics}, ensure_ascii=True, indent=2))


def repair_round(target_round: int):
    """Fetch one round missed or stale in an earlier pass; keep existing ledger rows."""
    path = EVIDENCE / 'fixture_event_ledger.json'
    ledger = {str(r['match_id']): r for r in json.loads(path.read_text(encoding='utf-8'))} if path.exists() else {}
    report = {}

    def page_action(page):
        box = page.get_by_role('combobox', name='Select item in event list', exact=True)
        panel = page.get_by_role('tabpanel').first
        for wanted in range(29, target_round - 1, -1):
            previous = panel.locator('a[href*="/football/match/"]').evaluate_all('as => as.map(a=>a.href).sort().join("|")')
            box.click()
            box.press('ArrowUp')
            box.press('Enter')
            page.wait_for_function('''arg => {
              const bs=Array.from(document.querySelectorAll('[role="combobox"]'));
              const p=document.querySelector('[role="tabpanel"]');
              if(!bs.some(b=>b.innerText.includes(`Round ${arg.round}`))||!p) return false;
              const ids=Array.from(p.querySelectorAll('a[href*="/football/match/"]')).map(a=>a.href).sort().join('|');
              return ids && ids!==arg.previous;
            }''', arg={'round': wanted, 'previous': previous}, timeout=12000)
        cards = panel.locator('a[href*="/football/match/"]').evaluate_all('''as => as.map(a=>({href:a.href,text:a.innerText,html:a.outerHTML,
            teams:Array.from(a.querySelectorAll('img[alt]')).map(i=>i.alt)}))''')
        report.update({'selected_round': box.inner_text(), 'events': len(cards)})
        for card in cards:
            match = re.search(r'#id:(\d+)', card['href'])
            if match:
                mid = match.group(1)
                ledger[mid] = {'match_id': mid, 'href': card['href'], 'card_text': card['text'],
                    'team_alts': card['teams'], 'card_html': card['html'], 'selected_round': target_round,
                    'observed_at': datetime.now(timezone.utc).isoformat()}

    with DynamicSession(real_chrome=True, headless=True, google_search=False, network_idle=False,
                        timeout=60000, retries=1, locale='en-GB', timezone_id='Asia/Shanghai',
                        disable_resources=False, user_data_dir=str(BROWSER_PROFILE),
                        additional_args={'viewport': {'width': 1440, 'height': 1000}}) as session:
        session.fetch(TOURNAMENT_URL, page_action=page_action)
    atomic_json(path, list(ledger.values()))
    report['unique_events'] = len(ledger)
    atomic_json(EVIDENCE / f'fixture_round_{target_round}_repair.json', report)
    print(json.dumps(report, ensure_ascii=True, indent=2))


def collect_player_stats(limit: int | None = None, include_ids: set[str] | None = None):
    """Collect visible Player stats DOM for finished fixtures with validated checkpoints."""
    manifest = list(csv.DictReader((DATA / 'match_manifest.csv').open(encoding='utf-8-sig')))
    raw_path = DATA / 'player_category_dom.jsonl'
    checkpoint_path = DATA / 'collection_checkpoint.json'
    failure_path = DATA / 'collection_failures.jsonl'
    existing = {}
    if raw_path.exists():
        for line in raw_path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                entry = json.loads(line)
                existing[entry['match_id']] = entry
    selected = [r for r in manifest if (include_ids is None or r['match_id'] in include_ids)
                and r['match_id'] not in existing]
    if limit:
        selected = selected[:limit]
    print(f'queue={len(selected)} existing_validated={len(existing)}', flush=True)
    totals = {'validated': len(existing), 'failed': 0}

    def collect_page(page, fixture):
        expected_id = str(fixture['match_id'])
        expected_date = datetime.strptime(fixture['match_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        # Historical slugs can briefly resolve to a different event. Wait for both the
        # requested fragment and date before touching the statistics panel.
        page.wait_for_function('''arg => {
          const expected=[arg.date, arg.date.replace(/^0/, '').replace('/0','/') , arg.shortDate];
          return document.body && location.hash.includes(`id:${arg.id}`) &&
            expected.some(d => document.body.innerText.includes(d));
        }''', arg={'id':expected_id,'date':expected_date,
                    'shortDate':datetime.strptime(fixture['match_date'],'%Y-%m-%d').strftime('%d/%m/%y')}, timeout=8000)
        page_url = page.url
        body = page.locator('body').inner_text()
        if expected_date not in body and datetime.strptime(fixture['match_date'],'%Y-%m-%d').strftime('%d/%m/%y') not in body:
            raise ValueError(f'identity_mismatch: expected date {expected_date}')
        stats_tab = page.get_by_role('tab', name='Player stats', exact=True)
        try:
            stats_tab.wait_for(state='visible', timeout=20000)
        except Exception as e:
            # Preserve rendered evidence when the hydrated player panel is absent.
            folder = EVIDENCE / f'match_{expected_id}'
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'failure.html').write_text(page.content(), encoding='utf-8')
            (folder / 'failure.txt').write_text(body, encoding='utf-8')
            try:
                page.screenshot(path=str(folder / 'failure.png'), full_page=False)
            except Exception:
                pass
            raise ValueError(f'player_stats_tab_missing: {e}') from e
        stats_tab.click()
        page.wait_for_function("() => Array.from(document.querySelectorAll('table')).some(t => t.querySelector('a[href*=\"/football/player/\"]'))", timeout=30000)
        categories = {}
        identities = set()
        for category in CATEGORIES:
            tab = page.get_by_role('tab', name=category, exact=True)
            if tab.count() != 1:
                categories[category] = {'status': 'category_missing', 'tables': []}
                continue
            tab.click()
            # A short DOM condition wait handles the table's client-side category switch.
            page.wait_for_timeout(350)
            data = page.locator('table').evaluate_all('''tables => tables.map(t => {
              const headers=Array.from(t.querySelectorAll('thead th')).map(c=>c.innerText.trim());
              const rows=Array.from(t.querySelectorAll('tbody tr')).map(r=>{
                const cells=Array.from(r.querySelectorAll('td'));
                const player=r.querySelector('a[href*="/football/player/"]');
                const href=player?.getAttribute('href')||'';
                const id=href.match(/\\/(\\d+)$/)?.[1]||null;
                return {player_id:id,player_name:player?.innerText.trim()||null,player_href:href||null,
                  team_name:cells[0]?.querySelector('img[alt]')?.alt||null,
                  cells:cells.map(c=>({text:c.innerText.trim(), meters:Array.from(c.querySelectorAll('[role="meter"]')).map(m=>({value:m.getAttribute('aria-valuenow'),min:m.getAttribute('aria-valuemin'),max:m.getAttribute('aria-valuemax')}))}))};
              }).filter(r=>r.player_id);
              return {headers,rows};
            }).filter(t=>t.rows.length>0)''')
            if len(data) != 1:
                categories[category] = {'status': 'table_ambiguous_or_missing', 'tables': data}
            else:
                rows = data[0]['rows']
                teamset = {r['team_name'] for r in rows}
                expected_teams = {fixture['home_team'], fixture['away_team']}
                if teamset != expected_teams:
                    raise ValueError(f'identity_mismatch: table teams={sorted(teamset)} expected={sorted(expected_teams)}')
                ids = [r['player_id'] for r in rows]
                if len(ids) != len(set(ids)):
                    raise ValueError(f'duplicate_player_id in {category}')
                if category == 'General':
                    identities = set(ids)
                    if len(rows) < 15:
                        raise ValueError('incomplete_roster: fewer than 15 General rows')
                categories[category] = {'status': 'validated', **data[0]}
        if not identities:
            raise ValueError('table_not_ready: no validated General rows')
        entry = {'source': 'Sofascore webpage DOM', 'competition_id': 649, 'season_id': 71364,
                 'match_id': expected_id, 'match_date': fixture['match_date'], 'round': int(fixture['round']),
                 'home_team': fixture['home_team'], 'away_team': fixture['away_team'],
                 'home_goals': fixture['home_goals'], 'away_goals': fixture['away_goals'], 'source_url': page_url,
                 'observed_at': datetime.now(timezone.utc).isoformat(), 'parser_version': '1.0',
                 'categories': categories, 'general_player_count': len(identities),
                 'general_player_ids': sorted(identities)}
        if categories['General']['status'] != 'validated':
            raise ValueError('table_not_ready: General table not validated')
        incomplete_categories = [c for c in CATEGORIES if categories.get(c, {}).get('status') != 'validated']
        if incomplete_categories:
            raise ValueError(f'category_missing: {incomplete_categories}')
        entry['evidence_sha256'] = hashlib.sha256(json.dumps(categories, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
        return entry

    with DynamicSession(real_chrome=True, headless=True, google_search=False, network_idle=False,
                        timeout=60000, retries=1, locale='en-GB', timezone_id='Asia/Shanghai',
                        disable_resources=False, user_data_dir=str(BROWSER_PROFILE),
                        additional_args={'viewport': {'width': 1440, 'height': 1000}}) as session:
        for index, fixture in enumerate(selected, 1):
            mid = fixture['match_id']
            result_box = {'entry': None, 'error': None}
            def action(page, f=fixture, box=result_box):
                try:
                    box['entry'] = collect_page(page, f)
                except Exception as e:
                    box['error'] = f'{type(e).__name__}: {e}'
                    folder = EVIDENCE / f'match_{f["match_id"]}'
                    folder.mkdir(parents=True, exist_ok=True)
                    try:
                        (folder / 'failure.html').write_text(page.content(), encoding='utf-8')
                        (folder / 'failure.txt').write_text(page.locator('body').inner_text(), encoding='utf-8')
                        page.screenshot(path=str(folder / 'failure.png'), full_page=False)
                    except Exception:
                        pass
            url = fixture['source_url']
            try:
                response = session.fetch(url, page_action=action)
                result_box['http_status'] = response.status
                if result_box['entry'] is None:
                    raise RuntimeError(f'http={response.status}: {result_box["error"] or "page_action_failed"}')
                existing[mid] = result_box['entry']
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = raw_path.with_suffix('.jsonl.tmp')
                with tmp.open('w', encoding='utf-8', newline='\n') as f:
                    for key in sorted(existing, key=lambda x: (int(next(r['round'] for r in manifest if r['match_id']==x)), int(x))):
                        f.write(json.dumps(existing[key], ensure_ascii=False, separators=(',', ':')) + '\n')
                tmp.replace(raw_path)
                totals['validated'] += 1
                atomic_json(checkpoint_path, {'updated_at': datetime.now(timezone.utc).isoformat(),
                    'validated_count': len(existing), 'last_match_id': mid, 'last_round': fixture['round']})
                print(f'[{index}/{len(selected)}] {mid} R{fixture["round"]} rows={len(existing[mid]["general_player_ids"])} validated', flush=True)
            except Exception as e:
                totals['failed'] += 1
                failure = {'match_id': mid, 'round': fixture['round'], 'source_url': url,
                           'error': str(e), 'observed_at': datetime.now(timezone.utc).isoformat()}
                failure_path.parent.mkdir(parents=True, exist_ok=True)
                with failure_path.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(failure, ensure_ascii=False) + '\n')
                print(f'[{index}/{len(selected)}] {mid} failed: {e}', flush=True)
            time.sleep(5)
    print(json.dumps(totals, ensure_ascii=True, indent=2))


def debug_event_route(match_id: str):
    """Test whether resetting the browser fragment restores a reused historical match."""
    manifest = {r['match_id']:r for r in csv.DictReader((DATA/'match_manifest.csv').open(encoding='utf-8-sig'))}
    fixture = manifest[match_id]
    report = {'match_id':match_id,'requested_url':fixture['source_url'],'snapshots':[]}
    def action(page):
        expected_date=datetime.strptime(fixture['match_date'],'%Y-%m-%d').strftime('%d/%m/%Y')
        page.wait_for_timeout(5000)
        report['snapshots'].append({'stage':'initial','url':page.url,'title':page.title(),
            'contains_expected_date':expected_date in page.locator('body').inner_text(),
            'body_excerpt':page.locator('body').inner_text()[:1000]})
        page.evaluate('(id) => { location.hash = `id:${id}`; }',match_id)
        page.wait_for_timeout(15000)
        report['snapshots'].append({'stage':'repeat_hash','url':page.url,'title':page.title(),
            'contains_expected_date':expected_date in page.locator('body').inner_text(),
            'body_excerpt':page.locator('body').inner_text()[:1000]})
        folder=EVIDENCE/f'match_{match_id}'
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'route_debug.html').write_text(page.content(),encoding='utf-8')
        (folder/'route_debug.txt').write_text(page.locator('body').inner_text(),encoding='utf-8')
    with DynamicSession(real_chrome=True,headless=True,google_search=False,network_idle=False,
        timeout=60000,retries=1,locale='en-GB',timezone_id='Asia/Shanghai',disable_resources=False,
        user_data_dir=str(BROWSER_PROFILE),
        additional_args={'viewport':{'width':1440,'height':1000}}) as session:
        session.fetch(fixture['source_url'],page_action=action)
    atomic_json(EVIDENCE/f'route_debug_{match_id}.json',report)
    print(json.dumps(report,ensure_ascii=True,indent=2))


def refresh_schedule_ui():
    report={}
    def action(page):
        season=page.get_by_role('combobox',name='Select season in unique tournament header',exact=True)
        season.wait_for(state='visible',timeout=30000)
        report['season_before']=season.inner_text()
        report['matches_text_count']=page.get_by_text('Matches',exact=True).count()
        report['matches_elements']=page.get_by_text('Matches',exact=True).evaluate_all('es=>es.map(e=>({tag:e.tagName,role:e.getAttribute("role"),html:e.outerHTML}))')
        report['links_before']=page.locator('a[href*="/football/match/"]').count()
        season.click()
        page.wait_for_timeout(300)
        report['options']=page.get_by_role('option').all_text_contents()
        page.get_by_role('option',name='2025',exact=True).click()
        page.wait_for_timeout(4000)
        report['season_after']=season.inner_text()
        report['round_control_count']=page.get_by_role('combobox',name='Select item in event list',exact=True).count()
        report['match_card_count']=page.locator('a[data-id]').count()
        report['body_excerpt']=page.locator('body').inner_text()[:1200]
        (EVIDENCE/'schedule_refresh.html').write_text(page.content(),encoding='utf-8')
    with DynamicSession(real_chrome=True,headless=True,google_search=False,network_idle=False,timeout=60000,retries=1,
        locale='en-GB',timezone_id='Asia/Shanghai',disable_resources=False,user_data_dir=str(BROWSER_PROFILE),
        additional_args={'viewport':{'width':1440,'height':1000}}) as session:
        session.fetch(TOURNAMENT_URL,page_action=action)
    atomic_json(EVIDENCE/'schedule_refresh.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='season_menu'},ensure_ascii=True,indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('probe-round-ui', 'fixtures', 'repair-round', 'player-stats', 'debug-route', 'refresh-schedule'))
    parser.add_argument('--round', type=int, default=2)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--match-ids', nargs='*', default=None)
    parser.add_argument('--match-id', default=None)
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    configure_f_drive_runtime()
    if args.command == 'probe-round-ui':
        probe_round_ui()
    elif args.command == 'fixtures':
        collect_fixtures()
    elif args.command == 'repair-round':
        if not 1 <= args.round <= 30:
            parser.error('--round must be between 1 and 30')
        repair_round(args.round)
    elif args.command == 'player-stats':
        collect_player_stats(limit=args.limit, include_ids=set(args.match_ids) if args.match_ids else None)
    elif args.command=='debug-route':
        if not args.match_id or args.match_id not in {r['match_id'] for r in csv.DictReader((DATA/'match_manifest.csv').open(encoding='utf-8-sig'))}:
            parser.error('--match-id must be present in the completed manifest')
        debug_event_route(args.match_id)
    else:
        refresh_schedule_ui()


if __name__ == '__main__':
    main()
