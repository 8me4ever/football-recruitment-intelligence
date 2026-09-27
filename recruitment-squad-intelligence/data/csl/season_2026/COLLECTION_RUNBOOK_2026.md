# 2026 中超及中超球队亚冠网页采集链路

状态快照：2026-09-27。本文记录目前已完整跑通并通过离线审计的可复用采集路径。它覆盖截至该日期所有可见已完赛的 2026 中超比赛，以及 2026/27 亚冠精英联赛、亚冠二级联赛中至少一方属于 2026 中超球队的比赛。赛季仍在进行，未来/未完赛赛事只进入赛程台账，不会生成球员统计。

## 已验收结果

| 范围 | 已枚举赛程 | 已完赛并验收 | 球员比赛行 |
|---|---:|---:|---:|
| 2026 中超 | 243 | 208 | 包含在总计中 |
| 2026/27 亚冠精英 | 16 个中超球队相关赛事 | 2 | 包含在总计中 |
| 2026/27 亚冠二级 | 6 个中超球队相关赛事 | 1 | 包含在总计中 |
| **合计** | **265** | **211 / 211** | **6,503** |

此外，台账记录 32 场未开赛中超、3 场延期中超、19 场未开赛亚冠。足协杯排除。每场纳入比赛同时保留双方球员。六类数据为 General、Attacking、Defending、Passing、Duels、Goalkeeping。审计后有 474 个不同球员 ID；各赛事独立计数为中超 425、亚冠精英 64、亚冠二级 30，跨赛事可重复出现。

## 可复用的浏览器链路

全联赛路径以竞赛页为入口，不依赖单一球队赛程：

1. 在项目 Python 环境中用 Scrapling `DynamicSession` 启动 Chrome，有界面运行，桌面视口 1440×1000，语言 `en-GB`、时区 `Asia/Shanghai`。临时目录和独立浏览器配置目录位于 `data/csl/season_2026/`；它们是本机运行状态，不提交到版本控制。
2. 打开 [Sofascore 2026 中超赛程](https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:90049,tab:matches)，确认赛季下拉为 `2026`。通过可见的赛程轮次下拉框依次选择 Round 1–30。
3. 只读取当前渲染赛程中的比赛卡片 `a[data-id][class*="event-hl-"]`。卡片可见 ID 必须与链接 `#id:<event_id>` 一致；从卡片的可见文本和队徽 alt 文本记录日期、状态、主客队和比分。按状态把 FT 类赛事归为完赛，把 `Postponed` 留在延期台账，把无比分卡片留作 scheduled。改期补赛以其网页提供的新赛事 ID 单独保留。
4. 逐场从本轮可见卡片点击进入比赛页，避免直接粘贴历史 slug 时网站将页面解析到同一对阵的其他赛事。比赛详情页需同时核对事件 ID、日期、赛事名称、双方球队、完赛状态及比分；任何一项不一致都不接收。
5. 点击 `Player stats`，依次打开 General、Attacking、Defending、Passing、Duels、Goalkeeping。等待该分类专属表头和球员行出现后，保存可见表格 HTML、表头、单元格文本、球员链接/ID、队徽 alt 和评分 meter。
6. 验收每类球队集合必须恰好等于该场双方；球员 ID 不得缺失或重复；General、Attacking、Defending、Passing、Duels 的球员 ID 顺序逐行一致；Goalkeeping 球员必须是 General 名单子集。之后由 Scrapling Selector 离线重解析已存 HTML，并对身份及单元格数据再次校验。
7. 每场成功或失败后都写运行日志和原始证据，支持 `--skip-existing` 断点续跑。遇到人工验证页立即停下，由人工处理后再恢复；不绕过验证。

亚冠路径使用同一浏览器配置、卡片定位和六类表格验收，在各赛事 26/27 赛季页按可见比赛轮次读取赛程，然后仅保留至少一方与 2026 中超参赛球队名录精确匹配的比赛：[AFC Champions League Elite](https://www.sofascore.com/football/tournament/asia/afc-champions-league/463#id:99217,tab:matches)（赛季 ID `99217`）和 [AFC Champions League Two](https://www.sofascore.com/football/tournament/asia/afc-cup/668#tab:matches,id:97465)（赛季 ID `97465`）。比赛需保留亚冠比赛双方，不在采集层套用权重。

采集只对浏览器渲染后的公开页面 DOM 操作；脚本不请求数据 API、不读隐藏应用状态或 XHR 响应。所有原始页面证据、运行数据、临时目录和 Chrome profile 放在 F 盘项目目录。

## 重跑顺序

从项目根目录执行：

```powershell
& '.\.venv-scrapling\Scripts\python.exe' scripts/collect_csl_2026_schedule.py
& '.\.venv-scrapling\Scripts\python.exe' scripts/collect_afc_2026_schedule.py
& '.\.venv-scrapling\Scripts\python.exe' scripts/build_csl_2026_scope_manifest.py
& '.\.venv-scrapling\Scripts\python.exe' scripts/collect_csl_2026_all_scrapling.py --skip-existing
& '.\.venv-scrapling\Scripts\python.exe' scripts/collect_afc_2026_scrapling.py --skip-existing
& '.\.venv-scrapling\Scripts\python.exe' scripts/audit_csl_2026_all.py
```

## 产物索引

- `csl_fixtures_2026.csv`：30 轮中超赛事卡片清单。
- `afc_fixtures_2026_27_in_scope.csv`：两项亚冠赛事中至少有一方为 2026 中超球队的赛事清单。
- `fixtures_2026_in_scope.csv`：C1 统一范围清单，保留赛事、赛季、状态、轮次、事件 ID 和源链接。
- `evidence/round_cards/`、`evidence/afc_round_cards/`：逐轮原始赛事卡片 HTML 和 JSON 证据。
- `../..` 上层 `csl_2026_capture/scrapling_raw/`：211 场已完赛赛事的六类球员表原始归档。
- `player_match_stats_2026.csv`：全范围标准化球员×比赛导出，保留六类统计 JSON。
- `collection_coverage_2026.csv`、`data_quality_report_2026.json`：逐场覆盖和独立离线审计结果。
