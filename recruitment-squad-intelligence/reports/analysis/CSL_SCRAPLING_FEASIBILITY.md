# Scrapling 获取 Sofascore 网页数据：实测报告

## 2026-09-27 全季重试更新（当前覆盖状态）

本报告下面的2025全季初次采集结论记录于2026-09-25，已被本次重试结果取代。此前失败的37场现已全部通过“赛季页 → 选择可见轮次 → 点击精确完赛赛事卡片 → 等待比赛标题和 `Player stats` 分类 → 抓取六分类 DOM”的链路采集并验收。2025当前覆盖为240/240，导出7,417条General球员比赛记录、452个球员ID；北京国安覆盖30/30。六类表格对每场均通过表头、球队和球员ID核验；五个非门将分类逐场球员集合一致，门将球员ID属于General集合。

可复现脚本为 `scripts/retry_csl_2025_failed_card_click.py`。成功重试原始记录为 `data/csl/season_2025/player_category_dom_retry.jsonl`，已合入规范档案并备份旧203场版本；新审计为 `reports/analysis/CSL_2025_COLLECTION_AUDIT.md` 与 `data/csl/season_2025/collection_audit.json`。该结果指逐场球员统计表覆盖完整，不代表包含所有未出场替补的完整阵容表，也不是比赛当时冻结的历史信息。

日期：2026-09-25。结论：**逐场网页提取技术路线已通过小样本验证，可进入全季采集器实施；尚未证明240场完整覆盖。** 用户已确认官方授权，本次遵循其指定的网页获取方式。

## 实际执行结果

独立 Python 3.12.14 环境安装 Scrapling 0.4.15、Playwright 1.63.0；调用 `DynamicFetcher.fetch`，使用系统 Chrome 153.0.8010.52、headless、1440×1000、en-GB、Asia/Shanghai。通过 page_action 点击页面控件，从渲染 DOM 提取数据，没有主动请求 API、捕获 XHR 数据或解析隐藏应用状态。

| 页面 | HTTP | 已取得内容 |
|---|---:|---|
| 2025-02-22 云南玉昆 0–2 北京国安，13400350 | 200 | General 31行；Attacking、Defending、Passing、Duels各31行；Goalkeeping 2行 |
| 2025-08-15 上海海港 4–1 河南，13522595 | 200 | General 32行 |
| 2025-11-22 北京国安 5–1 梅州客家，13522670 | 200 | General 32行 |
| 2025中超赛季，649 / 71364 | 200 | 2025、By round及Round 30赛程控件已渲染；本次未遍历全部30轮 |

三场共95条 player-match，均从本轮实际保存的 HTML 离线解析，不是此前12条选择性转录。核对日期、两队队名集合、场内球员ID唯一性、样本进球数合计通过；从评分元素 aria-valuenow 提取95个评分，均在页面定义的3–10范围。球队主客顺序、逐场出场名单完整性尚未由生产审计自动验证。普通射门/对抗等全字段语义尚未逐项人工核对，六分类已抓到不等于全部字段已经建模就绪。

配套离线命令 `scripts/parse_scrapling_probe.py` 已执行成功；现有10项 CSL 单元测试通过。这些旧测试并不证明本次浏览器采集器可处理所有页面或240场。

## 确认的操作路径

初始三个比赛页均没有 HTML table。点击 `get_by_role('tab', name='Player stats', exact=True)` 后出现球员表。该入口位于阵容区域，而非顶层 Statistics。六个分类的准确名称是 General、Attacking、Defending、Passing、Duels、Goalkeeping。

每类使用当前 `thead th` 建立列名映射，逐行读取 `tbody tr`/`td`。球员ID来自页面球员链接，球队来自首列 img.alt；不从链接中队名排列推断主客。评分由 CSS 显示，innerText 可能为空，应读取评分单元格的 `[role="meter"]` / `aria-valuenow`。离线 get_all_text 可读取普通单元格；本版本 `xpath('string(.)').get()` 的字符串结果出现序列化错误，已改用前者。

页面截图确认首轮整张球员表已出现，右侧部分列横向溢出；DOM仍包含这些列。人工复查评分/位置时需横向滚动或查看可访问性信息，不能只凭初始截图断言右侧字段缺失。

## 证据位置

`data/csl/scrapling_probe/`：

- `13522670/`：首次页面加载探针，无点击统计。
- `13522670-stats/`、`13522595-stats/`：General HTML、表头/行、截图和run.json。
- `13400350-categories/`：General及六分类HTML、categories.json、截图和run.json。
- `season-2025/`：赛季入口HTML、可见文本、可访问性快照和run.json。
- `validation.json`：三场离线核验摘要；各场 general_dom_parsed.json 含解析的球队、球员及评分。

早期 player_tables.json 仅存 innerText，部分评分为空；这属于第一版提取器局限。最终 general_dom_parsed.json 从同一HTML的aria属性恢复评分，保留早期文件作为证据，不应拿早期空值统计真实评分缺失。

`scripts/probe_sofascore_scrapling.py` 为可复现探针，默认30秒多时点观察并留证；不是完整批量爬虫。程序后续增加了六分类及meter属性采集，因此较早run.json没有categories，较早categories.json没有meters；原始HTML仍可离线复核。`captured_for_review` 表示抓取结束而非业务验收完成。

## 对旧报告的更正

1. API返回403不能推导网页不可采；本次四类目标页面实际HTTP200，无需API凭据即可完成本轮网页验证。
2. “海港—河南13522595缺少Statistics/统计覆盖”是此前页面尚未稳定时的过早判断，应撤回。本轮完整General取得32行。
3. 用户已确认授权，不再将“待取得许可/待接API”作为当前实施前置条件。

## 下一阶段的边界

尚待实现和验证：30轮赛程遍历、延期事件与补赛关联、10场跨场景试采、首发/替补名单提取、逐场出场集合核对、240场六分类覆盖率、稳健条件等待、重试/断点恢复及异常页处理。本次不会把3场成功外推成全季保证。

## 2026-09-25 初次批量采集结果（已由2026-09-27重试更新）

2026-09-25初次全季尝试的历史指标（已被本页开头的2026-09-27更新取代）：**203/240**场通过，6,290条General记录，国安26/30场。

当时37场失败的原因是35条旧比赛链接解析到另一赛事/日期，另2场过早检查时未见Player stats标签。2026-09-27已通过可见2025赛程按轮次点击精确赛事卡片重新采集这37场；“轮次控件不再渲染”和“覆盖只能达到203/240”均为旧会话观察，不是当前状态。

`player_match_stats.csv`现为203场已验证记录的宽表，六分类原始单元格分别放在JSON列；`player_category_dom.jsonl`保存按场分类的行、表头、球员ID、队名及评分DOM值。完整事件页、重定向身份失败现场保存在 `data/csl/season_2025/evidence/`。历史失败尝试日志有重复重试，需以machine-readable审计中缺失比赛集合和最终原因分类为准。

详细可复制执行提示词在 `docs/CSL_SOFASCORE_SCRAPLING_EXECUTION_PROMPT.md`，明确以上边界、已验证配置和选择器、字段字典、状态机、验收标准。建议先按它补齐生产采集器，再逐场扩展。

官方参考：[Scrapling项目](https://github.com/d4vinci/Scrapling)、[DynamicFetcher/page_action参数](https://scrapling.readthedocs.io/en/latest/fetching/dynamic.html)、[安装方式](https://scrapling.readthedocs.io/en/latest/#installation)。文档只说明能力，本报告的可行性结论来自实际目标网页测试。

## 2026-09-27：国安 2026 网页路径复测与批次

独立 Scrapling `DynamicSession` 在正常网页网络权限、系统 Chrome、headed、1440×1000、`en-GB`、`Asia/Shanghai` 配置下，已从国安球队页的 **Finished** 卡片进入 2026 比赛页。先前一次探针将目标赛事卡片和同 URL 的空链接都视为目标，报出“找到 2 个链接”；限定选择 `#tabpanel-list` 中含 `FT` 的赛事卡片后，海港—国安 `15552633` 正确载入。点击 `Player stats` 后六分类表都可读取，五类各 31 行、Goalkeeping 2 行。该场独立 Scrapling 与内置浏览器的球员 ID 和六分类原始值逐项一致。

按该路线完成国安当前快照 26 场完赛赛事（25 中超、1 亚冠精英联赛）的批次。3 月 14 日山东泰山—国安 `15551891` 未出现在独立会话的国安 Finished 分页尾部，使用已知比赛 URL 直达并严格验收赛事身份和六分类后接纳。`csl_2026_capture/scrapling_raw/` 保存每场六分类 HTML，`data/csl/season_2026/guoan_collection_audit.json` 报告 **26/26 场通过、791 条球员比赛记录**。用 Scrapling Selector 对已保存的 HTML 离线复解析，并与内置浏览器同范围导出逐字段比较，791 条记录没有差异。

**后续更正（2026-09-27）：** 与全赛季规范赛程及导出核对后，发现上述国安专属快照漏列第1轮武汉三镇 0–2 北京国安 `15551889`。该事件已在全赛季主数据和已保存 Scrapling DOM 中，缺口只存在于当时的国安专属 fixture ledger。补回赛程行并重跑 `audit_csl_2026_guoan_dom.py --source scrapling` 后，当前专属审计为 **27/27 场通过（26 场中超、1 场亚冠精英），823 条双方球员记录**。原内置浏览器对照仍是其自己的26场、791行历史快照，fixture 清单现归档到 `data/csl/season_2026/guoan_in_app_fixture_snapshot_2026-09-27.csv`；该对照没有被扩成第27场。

**当时的结论（已由下方 2026-09-27 更新取代）：** 该轮测试只针对北京国安当前可见快照；尚未覆盖其他中超球队。C0 按正式章程仍待当前正式流程的 2025 基准赛复现。最新完整范围与复跑命令见 `data/csl/season_2026/README.md`。

## 2026-09-27 更新：全中超与中超球队亚冠赛程批量采集

在上述 Guoan 单队验证之后，同日进一步验证并批量运行了全联赛路径：从 2026 中超竞赛页的可见赛季和轮次选择器枚举 30 轮，再点击有精确事件 ID 的可见比赛卡片进入详情；不以直达历史 slug 作为主路径。全范围赛程清单包含 243 场中超事件、22 场与 2026 中超球队相关的 2026/27 亚冠精英/亚冠二级赛事。211 场已完赛目标赛事（208 场中超、2 场亚冠精英、1 场亚冠二级）全部通过六分类 DOM 离线复验，导出 6,503 条球员比赛记录，缺漏为 0。32 场未赛中超、3 场延期中超和 19 场未赛亚冠仍留在赛程清单；它们不是当前完赛覆盖分母。完整方法、选择器、复跑命令和产物索引见 `data/csl/season_2026/COLLECTION_RUNBOOK_2026.md` 及 `data/csl/season_2026/data_quality_report_2026.json`。
