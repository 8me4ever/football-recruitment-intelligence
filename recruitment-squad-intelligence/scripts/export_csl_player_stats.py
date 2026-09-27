"""Export saved category DOM records to a player-match wide CSV and coverage audit."""
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/csl/season_2025'
CATEGORIES = ('General', 'Attacking', 'Defending', 'Passing', 'Duels', 'Goalkeeping')


def category_map(category):
    rows = {}
    if category.get('status') != 'validated':
        return rows
    headers = category['headers']
    for row in category['rows']:
        values = row['cells']
        raw = {}
        for index, header in enumerate(headers):
            if index < 2:
                continue
            cell = values[index] if index < len(values) else {'text': ''}
            value = cell['text']
            meter = cell.get('meters') or []
            if header == 'Sofascore Rating' and meter:
                value = meter[0].get('value')
            raw[header] = value
        rows[row['player_id']] = {'name': row['player_name'], 'team': row['team_name'], 'stats': raw}
    return rows


def main():
    src = DATA / 'player_category_dom.jsonl'
    entries = [json.loads(line) for line in src.read_text(encoding='utf-8').splitlines() if line.strip()]
    wide, coverage = [], []
    schema = set()
    for entry in entries:
        maps = {name: category_map(entry['categories'].get(name, {})) for name in CATEGORIES}
        general = maps['General']
        ids = set(general)
        if not ids:
            continue
        coverage.append({'match_id': entry['match_id'], 'round': entry['round'],
            'general_rows': len(general), **{f'{c.lower()}_rows':len(maps[c]) for c in CATEGORIES},
            'all_categories_present':all(entry['categories'].get(c,{}).get('status')=='validated' for c in CATEGORIES),
            'players_missing_from_general':sorted(set().union(*(set(maps[c]) for c in CATEGORIES))-ids)})
        for player_id, base in general.items():
            row = {'source':entry['source'], 'competition_id':entry['competition_id'], 'season_id':entry['season_id'],
                'match_id':entry['match_id'], 'match_date':entry['match_date'], 'round':entry['round'],
                'home_team':entry['home_team'], 'away_team':entry['away_team'], 'home_goals':entry['home_goals'],
                'away_goals':entry['away_goals'], 'team_name':base['team'], 'player_id':player_id,
                'player_name':base['name'], 'source_url':entry['source_url'], 'observed_at':entry['observed_at'],
                'evidence_sha256':entry['evidence_sha256']}
            for cat in CATEGORIES:
                item = maps[cat].get(player_id)
                row[f'{cat.lower()}_stats_json'] = json.dumps(item['stats'],ensure_ascii=False,separators=(',',':')) if item else ''
                schema.add(f'{cat.lower()}_stats_json')
            wide.append(row)
    path = DATA / 'player_match_stats.csv'
    fields = ['source','competition_id','season_id','match_id','match_date','round','home_team','away_team','home_goals','away_goals','team_name','player_id','player_name','source_url','observed_at','evidence_sha256'] + sorted(schema)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(wide)
    audit={'generated_at':datetime.now(timezone.utc).isoformat(),'validated_match_records':len(entries),
        'player_match_rows':len(wide),'unique_players_in_sample':len({r['player_id'] for r in wide}),
        'categories':{c:sum(e['categories'].get(c,{}).get('status')=='validated' for e in entries) for c in CATEGORIES},
        'match_coverage':coverage,'all_category_match_records_complete':all(x['all_categories_present'] for x in coverage),
        'category_player_ids_missing_from_general':sum(bool(x['players_missing_from_general']) for x in coverage)}
    (DATA/'player_stats_coverage.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='match_coverage'},ensure_ascii=True,indent=2))


if __name__=='__main__': main()
