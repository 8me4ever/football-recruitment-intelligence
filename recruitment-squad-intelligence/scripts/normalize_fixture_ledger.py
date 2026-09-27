"""Turn saved tournament-page event-card HTML into a reviewable fixture ledger."""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from scrapling.parser import Selector

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'data/csl/season_2025/evidence'
DATA = ROOT / 'data/csl/season_2025'
STATUSES = {'FT', 'AET', 'PEN', 'Postponed', 'Canceled', 'Cancelled', 'Abandoned', 'Awarded', 'After extra time', 'After penalties'}


def normalize():
    raw = json.loads((EVIDENCE / 'fixture_event_ledger.json').read_text(encoding='utf-8'))
    rows, issues = [], []
    for item in raw:
        p = Selector(item['card_html'])
        date_match = re.search(r'\b(\d{2}/\d{2}/\d{2})\b', item['card_text'])
        status_values = [str(n.get_all_text(separator=' ', strip=True)) for n in p.css('div[class*="min-w_lg"]')]
        status = next((x for x in status_values if x in STATUSES), '')
        scores = [x for x in status_values if x.isdigit()]
        teams = item.get('team_alts', [])
        home_goals = away_goals = ''
        if status in {'FT', 'AET', 'PEN'} and len(scores) >= 2:
            home_goals, away_goals = scores[-2:]
        if not date_match or len(teams) < 2 or not status:
            issues.append({'match_id': item['match_id'], 'date': bool(date_match), 'teams': teams, 'values': status_values})
        rows.append({'match_id': item['match_id'], 'match_date': datetime.strptime(date_match.group(1), '%d/%m/%y').date().isoformat() if date_match else '',
                     'round': item['selected_round'], 'home_team': teams[0] if teams else '', 'away_team': teams[1] if len(teams)>1 else '',
                     'home_goals': home_goals, 'away_goals': away_goals, 'status': status,
                     'source':'Sofascore webpage DOM', 'source_url':item['href'], 'observed_on':item['observed_at'],
                     'card_text':item['card_text'], 'score_nodes':json.dumps(status_values, ensure_ascii=False)})
    fields = list(rows[0]) if rows else []
    for name, subset in [('raw_event_ledger.csv', rows), ('match_manifest.csv', [r for r in rows if r['status'] in {'FT','AET','PEN'}])]:
        with (DATA / name).open('w', encoding='utf-8-sig', newline='') as f:
            w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(subset)
    summary = {'observed_at':datetime.now(timezone.utc).isoformat(), 'raw_events':len(rows),
               'finished':sum(r['status'] in {'FT','AET','PEN'} for r in rows), 'by_round':{},
               'status_counts':{}, 'parse_issues':issues}
    for r in rows:
        summary['by_round'][str(r['round'])]=summary['by_round'].get(str(r['round']),0)+1
        summary['status_counts'][r['status']]=summary['status_counts'].get(r['status'],0)+1
    (EVIDENCE/'fixture_parse_audit.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__=='__main__': normalize()
