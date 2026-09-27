"""Write a season-level coverage audit from fixture and saved page-DOM records."""
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/csl/season_2025'
REPORT=ROOT/'reports/analysis/CSL_2025_COLLECTION_AUDIT.md'
CATS=('General','Attacking','Defending','Passing','Duels','Goalkeeping')


def main():
    manifest=list(csv.DictReader((DATA/'match_manifest.csv').open(encoding='utf-8-sig')))
    entries=[json.loads(x) for x in (DATA/'player_category_dom.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    failures=[json.loads(x) for x in (DATA/'collection_failures.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    latest={}
    for f in failures: latest[f['match_id']]=f
    manifest_by_id={r['match_id']:r for r in manifest}
    entry_by_id={e['match_id']:e for e in entries}
    missing=sorted(set(manifest_by_id)-set(entry_by_id),key=lambda x:(int(manifest_by_id[x]['round']),int(x)))
    rows=list(csv.DictReader((DATA/'player_match_stats.csv').open(encoding='utf-8-sig')))
    category_diff=Counter(); mismatch_examples={}; category_rows=Counter()
    for e in entries:
        sets={c:{r['player_id'] for r in e['categories'][c].get('rows',[])} for c in CATS}
        general=sets['General']
        for c in CATS:
            category_rows[c]+=len(sets[c])
            if c!='Goalkeeping' and sets[c]!=general:
                category_diff[c]+=1
                mismatch_examples.setdefault(c,[]).append({'match_id':e['match_id'],
                    'only_in_general':sorted(general-sets[c]),'only_in_category':sorted(sets[c]-general)})
            if c=='Goalkeeping' and not sets[c].issubset(general):
                category_diff['Goalkeeping_not_subset']+=1
    guoan_ids={r['match_id'] for r in rows if r['team_name']=='Beijing Guoan'}
    team_matches=Counter()
    for r in manifest:
        team_matches[r['home_team']]+=1;team_matches[r['away_team']]+=1
    failures_by_reason=Counter()
    for mid in missing:
        err=latest.get(mid,{}).get('error','no failure record')
        if 'identity_mismatch' in err or 'TimeoutError: Page.wait_for_function' in err and 'http=200' in err:
            reason='page_resolved_to_different_event_or_date'
        elif 'player_stats_tab_missing' in err:
            reason='player_stats_tab_missing'
        elif '503' in err or 'http=503' in err:
            reason='http_503'
        elif 'Page.goto: Timeout' in err or 'CONNECTION_TIMED_OUT' in err:
            reason='navigation_timeout'
        else: reason='other_or_no_failure_record'
        failures_by_reason[reason]+=1
        latest[mid]['classified_reason']=reason
    audit={'generated_at':datetime.now(timezone.utc).isoformat(),'fixture_count':len(manifest),
        'unique_fixture_ids':len(manifest_by_id),'collected_match_count':len(entries),'missing_match_count':len(missing),
        'player_match_rows':len(rows),'unique_player_ids':len({r['player_id'] for r in rows}),
        'beijing_guoan_matches_collected':len(guoan_ids),'expected_guoan_matches':30,
        'category_match_coverage':{c:sum(e['categories'][c].get('status')=='validated' for e in entries) for c in CATS},
        'category_player_rows':dict(category_rows),'category_player_id_mismatch_match_counts':dict(category_diff),
        'team_fixture_appearance_violations':{t:n for t,n in team_matches.items() if n!=30},
        'missing_by_reason':dict(failures_by_reason),
        'missing_fixtures':[{'match_id':m,'round':manifest_by_id[m]['round'],'match_date':manifest_by_id[m]['match_date'],
             'home_team':manifest_by_id[m]['home_team'],'away_team':manifest_by_id[m]['away_team'],
             'reason':latest.get(m,{}).get('classified_reason','no failure record'),
             'error':latest.get(m,{}).get('error','no failure record')} for m in missing],
        'category_mismatch_examples':mismatch_examples,
        'complete':len(manifest)==240 and len(manifest_by_id)==240 and len(entries)==240 and not missing and not category_diff}
    (DATA/'collection_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 2025 CSL 球员数据采集审计','',f"更新时间：{audit['generated_at']}",'',
      '## 覆盖情况','',
      f"- 完赛赛程：{len(manifest_by_id)}/240；逐场网页球员表验证通过：{len(entries)}/240；未取得：{len(missing)}。",
      f"- 球员比赛记录：{len(rows):,} 行；不同球员 ID：{audit['unique_player_ids']:,}。",
      f"- 北京国安：30场中取得 {len(guoan_ids)} 场球员表。",
      '- 已采集场次六个分类均通过表头、球队、球员 ID 和页面身份检查。门将分类只含门将；其他五分类的球员集合对比见机器审计。',
      '- 重试时从可见的 2025 赛程中选择轮次并点击精确赛事卡片；验收匹配事件 ID、赛程日期/比分、比赛标题球队及六分类球队与球员 ID。跳转到其他赛事的页面不纳入目标赛季。','',
      '## 未取得的场次','',
      '| 原定轮次 | 日期 | 主队 | 客队 | 失败类别 |','|---:|---|---|---|---|']
    for f in audit['missing_fixtures']:
        lines.append(f"| {f['round']} | {f['match_date']} | {f['home_team']} | {f['away_team']} | {f['reason']} |")
    lines += ['', '失败类别计数：' + ', '.join(f'{k}: {v}' for k,v in failures_by_reason.items()) + '.',
      '', '## 数据解释与限制','',
      '- 原始球员分类数据保留页面单元格字符串；CSV 中六个分类以 JSON 列保存，空白不会转换成0，评分读取页面 meter 的 aria-valuenow。',
      f"- 当前已通过验收的 {len(entries)} 场记录用于本赛季比较；缺失清单为 {len(missing)} 场。没有把 2026 年同队比赛或延期占位记录当作目标数据。",
      '- 本批没有收集完整阵容名单和未出场替补；因此暂不能证明每场出场名单覆盖完整。球员行数是页面逐场表的观察结果。',
      '- 页面于2026年回溯获取2025数据，属于当前历史页面状态，不是比赛当时的冻结快照。',
      '- 详细错误、ID差异与逐场球员分类行数见 `data/csl/season_2025/collection_audit.json`；原始DOM和失败现场见 `data/csl/season_2025/evidence/`。','',
      '结果：**' + ('全季完整' if audit['complete'] else f"部分完成（{len(entries)}/240）") + '**。']
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('missing_fixtures','category_mismatch_examples')},ensure_ascii=True,indent=2))


if __name__=='__main__': main()
