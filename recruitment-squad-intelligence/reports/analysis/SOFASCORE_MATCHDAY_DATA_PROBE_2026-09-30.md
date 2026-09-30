# Sofascore 比赛日名单与换人数据试采集（2026-09-30）

## 已取得的页面证据

从此前由 Scrapling 浏览器采集并保存的[山东泰山对北京国安可见 DOM](../../csl_2026_capture/route-direct-15551891-0927/match_5.html)（2026-03-14，event `15551891`），用[提取脚本](../../scripts/extract_sofascore_matchday_dom.py)生成[结构化结果](../../csl_2026_capture/sofascore_visible_matchday_15551891.json)。两队各取得 11 名首发、12 名替补和 3 名上场替补；每人保留可见姓名、球衣号、球员页或头像中的 ID，首发另有阵型线路与线路内顺位。国安显示 4-4-2，替补上场为林良铭 71′ 换曹永竞、张稀哲 71′ 换塞尔吉尼奥、贾非凡 90′ 换王刚。页面阵型仅支持**名义首发阵型位置**，不等于整场实际站位；其“Players' average positions”是另一类空间统计，尚未提取坐标，也不能直接解释成逐分钟角色。

换人时间须保留来源原文：同一页面替补卡写贾非凡 `90'`，事件时间线写 `90' +6`。此处结果忠实记录替补卡的 `90'`，不得将它当作精确事件时间。后续若要计算上场分钟，必须另取时间线并处理补时、半场换人和未知时刻。

该赛事是**一场历史页面样本**，不代表 27 场比赛日名单已经覆盖。现有 C1 的 27/27 首发证据和球员比赛统计不等于 27/27 替补席或换人事件覆盖。球员未出现在统计表中，仍不能判定未报名或未进比赛日名单。

## 当日实时 Scrapling 复试

使用现有 `DynamicSession` 探针及可见 DOM 保存流程，分别试了直接比赛 URL、带 `tab:lineups` 的比赛 URL，以及从国安球队页进入。可核查的运行摘要：

| 路径 | 结果 |
|---|---|
| 3 月 14 日泰山–国安直达旧 ID `15551891` | 页面自动显示为另一场同队对赛 `15552563`，只见 H2H；身份不符，拒收。[运行记录](../../csl_2026_capture/lineup-probe-15551891-0930-net/run.json) |
| 9 月 15 日国安–浦项直达 ID `16863671` | 页面身份正确，5/15/30 秒快照都只有 H2H，没有阵容 DOM。[运行记录](../../csl_2026_capture/lineup-probe-pohang-0930/run.json) |
| 同场直达并加 `tab:lineups` | 30 秒内仍只有 H2H。[运行记录](../../csl_2026_capture/lineup-probe-pohang-tab-0930/run.json) |
| 从球队赛程页进入 | 当前球队页改为 `List`/`Calendar`/`Players`/`Details`，原 `Finished` 卡片入口不再存在；旧选择器失效。[运行记录](../../csl_2026_capture/lineup-probe-pohang-via-team-0930/run.json) |

此观察只说明**当前运行路径**未得到完整阵容，不证明 Sofascore 从未提供该信息。历史完整快照证明可见页面曾提供这些字段。探针没有请求 Sofascore 数据 API、检查 XHR 或读取隐藏应用状态；若遇人工验证页应停止该批次。Scrapling 的[官方动态页面文档](https://scrapling.readthedocs.io/en/latest/fetching/dynamic.html)支持在渲染页执行页面操作并等待可见选择器，因此后续应针对新的赛程 UI 重建点击路径，再以可见阵容为完成条件，而非固定等待秒数。

## 逐场补齐方案

1. **先定赛事账本。**沿用现有 27 个国安完赛 event ID、日期、主客队和赛事。每次先从当前可见赛程卡进入；用页面标题、日期、双方队名、阵型球衣资源中的 event ID 同时校验，不接受同队历史交锋跳转或错场页面。
2. **恢复可见网页采集。**适配当前 `List`/`Calendar` 页，只点击实际显示的对应已完赛卡片和 `Lineups` 标签；等待 22 张首发卡出现，保存 DOM、可见文本、时间戳、浏览器配置与截图。若需要人工交互或仅出现 H2H，就标记 `lineup_dom_unavailable` 并转下一来源；不循环刷新或猜测私有接口。
3. **分层抽取。**首发、替补及球员 ID 来自阵容卡；换人上/下与精确补时来自可见事件时间线；名义阵型槽位来自首发图；平均位置若需使用，应保存图面坐标与视口并单独建表。阵型槽位、平均空间位置、用户给出的当前实际位置备注分别存储。
4. **补缺来源。**优先向俱乐部索取已获授权数据的比赛名单/换人导出，或人工保存能显示阵容的页面；其次逐场采集足协/中超官方比赛报告，再用 Transfermarkt、WhoScored、FotMob 等可见比赛页补缺并保留来源等级。用户手动提供的正式名单直接作为权威名册输入，但赛季名单不自动转成某场比赛日名单。
5. **验收口径。**每场分别统计 `首发两队各 11`、`国安替补人数`、`替补上场事件`、`换下者匹配`、`分钟原文及补时`、`阵型/位置粒度`、`来源冲突`。缺失写 `unknown`，不填 0。只有 27 场比赛日名单与事件校验完成后，才把 C1 的该维度视为完整。

### 建议的最小数据表

| 表 | 关键字段 |
|---|---|
| `matchday_player` | event_id, team, player_id, source_name, shirt_number, starter/bench, formation, formation_line, slot_in_line, source_url, evidence_time |
| `substitution_event` | event_id, team, incoming_player_id, outgoing_player_id, minute_display, minute_base, stoppage_minute, source_surface, conflict_status |
| `position_evidence` | event_id, player_id, `nominal_formation_slot`/`average_position`/`observed_role`, value, confidence, source |

下一项最高优先级的外部输入是**俱乐部已授权数据的逐场名单和事件导出**，若可提供，就能绕开当前网页 UI 漂移；对授权范围和项目章程中的网页采集边界应先作明确记录。否则按上述可见页面路线逐场补齐，不能从现有球员统计表推断未使用替补。
