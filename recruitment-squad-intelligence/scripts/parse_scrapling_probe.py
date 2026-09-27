"""Offline DOM extraction and checks for the three known probe fixtures."""
import json
from pathlib import Path
from scrapling.parser import Selector

ROOT = Path('data/csl/scrapling_probe')
CASES = [('13522670-stats', '22/11/2025', {'Beijing Guoan', 'Meizhou Hakka'}, 6),
         ('13522595-stats', '15/08/2025', {'Shanghai Port', 'Henan FC'}, 5),
         ('13400350-categories', '22/02/2025', {'Yunnan Yukun', 'Beijing Guoan'}, 2)]


def parse(path):
    page = Selector(path.read_text(encoding='utf-8'))
    table = page.css('table')[0]
    headers = [str(c.get_all_text(separator=' ', strip=True)) for c in table.css('thead th')]
    result = []
    for row in table.css('tbody tr'):
        cells = row.css('td')
        values = [str(c.get_all_text(separator=' ', strip=True)) for c in cells]
        assert len(values) == len(headers)
        url = row.css('a[href*="/football/player/"]::attr(href)').get()
        result.append({'player_id': int(url.rstrip('/').split('/')[-1]),
                       'player_name': values[1], 'team': cells[0].css('img::attr(alt)').get(),
                       'rating': row.css('[role="meter"]::attr(aria-valuenow)').get(),
                       'stats_raw': dict(zip(headers[2:], values[2:]))})
    return result


def main():
    summary = []
    for label, date, teams, goals in CASES:
        folder = ROOT / label
        visible = (folder / 'visible_30.txt').read_text(encoding='utf-8')
        rows = parse(folder / 'player_stats.html')
        assert date in visible, (label, 'date mismatch')
        assert set(r['team'] for r in rows) == teams, (label, 'teams mismatch')
        assert len({r['player_id'] for r in rows}) == len(rows)
        assert sum(int(r['stats_raw']['Goals'] or 0) for r in rows) == goals
        # Goal sum is only a sample cross-check: blanks remain raw blanks, not imputed zeros.
        ratings = [r for r in rows if r['rating'] is not None]
        assert all(3 <= float(r['rating']) <= 10 for r in ratings)
        (folder / 'general_dom_parsed.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
        summary.append({'sample': label, 'date_verified': date, 'rows': len(rows),
                        'teams': sorted(teams), 'ratings_from_aria': len(ratings),
                        'visible_goal_sum': goals})
    (ROOT / 'validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
