# Sofascore 网页采集执行提示词（Scrapling）

版本：2026-09-25。以下分隔线之后可整体复制给后续模型。配套报告：`reports/analysis/CSL_SCRAPLING_FEASIBILITY.md`。提示词区分已实测路径与尚待实现的批量工程步骤，不能把后者写成已完成。

**2026-09-27 更新：** 下文包含早期状态，旧的“203/240”和直接访问比赛链接的流程已过时。2025此前失败的37场已通过 `scripts/retry_csl_2025_failed_card_click.py` 从可见赛季轮次点击精确比赛卡片补齐；2025覆盖现为240/240，六分类审计无缺失。成功重试档案为 `data/csl/season_2025/player_category_dom_retry.jsonl`，规范化导出与审计已更新。该脚本自动跳过规范档案和重试档案中已有的通过比赛；再运行不会重访这240场。2026国安当前快照已校正至27场完赛赛事，全部中超与相关亚冠211场完赛范围见 `data/csl/season_2026/README.md` 与 `COLLECTION_RUNBOOK_2026.md`。项目范围与Gate以 `docs/正式项目章程.md` 为准。

---

你是此项目的数据采集工程师。请在工作区实际执行，持续推进至交付数据和审计报告，不能只给建议或生成空模板。

## 1. 任务、范围与已有授权

项目目录为仓库中的 `recruitment-squad-intelligence/`。目标是建立 2025 中国足球超级联赛逐场球员技术数据集，以北京国安为案例开展 Recruitment 分析。全联赛是候选比较样本，不能只采国安。

用户已明确说明所属职业俱乐部获得 Sofascore 官方的数据获取授权，并指定使用 Scrapling 从网页获取数据。按这一已有授权推进，不重新要求用户证明许可，不把 API 凭据作为前提。

只从浏览器渲染后的网页 DOM、可见表格和对应无障碍属性读取数据。允许浏览器正常运行网站脚本加载页面；这与采集器自行调用数据接口不同。采集程序不得主动请求 `/api/`，不得调用网站 API、捕获 XHR 响应作为数据源、读取页面应用状态或 `__NEXT_DATA__` 来代替网页统计表。队徽 img.src 中出现 `/api/` 只是已渲染元素属性，不要请求它来获取统计。无需下载队徽。

使用 Scrapling 的 `DynamicFetcher` 或 `DynamicSession` 驱动浏览器，再用 DOM 操作与 Scrapling Selector 解析。默认使用普通 DynamicFetcher；当前实测不需要更换代理、StealthyFetcher 或验证码处理。遇到技术阻塞如实记录，不无限重试。

本任务只做数据获取、标准化和质量检查。不要抢先构建球员排名、预测模型或补强结论。

## 2. 先阅读并核对进度

读取适用的 AGENTS.md（如存在），再读：

- `reports/analysis/CSL_SCRAPLING_FEASIBILITY.md`：最新实测结论。
- `reports/analysis/CSL_DATA_FEASIBILITY.md`：旧样本、字段语义及后续更正。
- `scripts/probe_sofascore_scrapling.py`、`scripts/parse_scrapling_probe.py`。
- `data/csl/scrapling_probe/validation.json` 和各场 `run.json`。
- `scripts/validate_csl_pilot.py`、`scripts/audit_csl_season.py`。
- `data/csl/season_2025/` 实际文件内容，而不只看文件是否存在。

历史采集快照（2026-09-25，已被2026-09-27的重试取代）：赛程清单240个唯一完赛ID，早期直达链接流程有37场未通过。重试批次已从可见赛程轮次点击精确赛事卡片并成功验证这37场；当前应以 `CSL_2025_COLLECTION_AUDIT.md` 和 `collection_audit.json` 的240/240结果为准。不要照搬后文早期 `collect_csl_season.py player-stats` 的直达链接命令来复采。

已通过比赛会按 `player_category_dom.jsonl` 中的 match_id 自动跳过。网页赛程卡片恢复且可进入旧比赛后，执行：

```powershell
.\.venv-scrapling\Scripts\python.exe scripts/collect_csl_season.py player-stats
.\.venv-scrapling\Scripts\python.exe scripts/export_csl_player_stats.py
.\.venv-scrapling\Scripts\python.exe scripts/create_csl_collection_audit.py
```

旧离线 pilot 的12行是选择性转录，不是12场，也不是完整逐场表。全季审计“每场有一行”的条件过弱，必须补充本提示词的完整性条件。

保护已有毕业设计、旧数据、用户未提交改动。原始新采集数据另存；不用旧的 Inter 离队预测标签套到 CSL 数据。

## 3. 环境与重现实测

当前工作环境：Python 3.12.14，Scrapling 0.4.15，Playwright 1.63.0，系统 Chrome 153.0.8010.52。独立环境 `.venv-scrapling` 已建立；不要使用已失效的旧 venv，也不要盲目安装旧项目 requirements。

PowerShell 从仓库根目录运行：

```powershell
Set-Location 'recruitment-squad-intelligence'
.\.venv-scrapling\Scripts\python.exe -m pip show scrapling playwright
.\.venv-scrapling\Scripts\python.exe scripts/parse_scrapling_probe.py
```

新机器才重建环境（先核实 Python 实际路径）：

```powershell
python -m venv .venv-scrapling
.\.venv-scrapling\Scripts\python.exe -m pip install -r requirements-scrapling.txt
```

当前方案使用 `real_chrome=True`，系统已安装 Chrome，不需要为了复现另下浏览器。没有 Chrome 时，查阅对应版本官方安装文档，安装适用的浏览器并重新验证，不能声称已测试当前机器没有的配置。发生 WinError 10013、文件写入 WinError 5 或浏览器启动权限错误时，按运行环境要求请求该命令的执行权限；这是本地沙箱问题，不应记为 Sofascore 拒绝访问。

联网重现三场：

```powershell
.\.venv-scrapling\Scripts\python.exe scripts/probe_sofascore_scrapling.py --label rerun-final --url 'https://www.sofascore.com/football/match/meizhou-hakka-beijing-guoan/BrbsLdLb#id:13522670'
.\.venv-scrapling\Scripts\python.exe scripts/probe_sofascore_scrapling.py --label rerun-middle --url 'https://www.sofascore.com/football/match/shanghai-port-henan-fc-jiuzu-dukang/RTnsMFq#id:13522595'
.\.venv-scrapling\Scripts\python.exe scripts/probe_sofascore_scrapling.py --label rerun-first --url 'https://www.sofascore.com/football/match/yunnan-yukun-beijing-guoan/BrbsQZOd#id:13400350'
```

探针仅用于发现和留证：它用 5/15/30 秒快照及固定等待，不是完整生产采集器；`captured_for_review` 也不代表业务校验通过。不要直接把这个状态转成 completed。离线解析脚本的 CASES 是三个固定基准，只核验原标签目录；其他标签需显式传入新的清单或扩展参数，不能假称已自动验证新目录。

## 4. 已证实的比赛页路径与选择器

实测配置：

```python
from scrapling.fetchers import DynamicFetcher
response = DynamicFetcher.fetch(
    match_url,
    real_chrome=True, headless=True,
    google_search=False, network_idle=False,
    timeout=60000, retries=1,
    locale='en-GB', timezone_id='Asia/Shanghai',
    disable_resources=False,
    additional_args={'viewport': {'width': 1440, 'height': 1000}},
    page_action=extract_from_page,
)
```

`page_action` 接收 Playwright Page。桌面 1440×1000 布局下，页面右侧/阵容区域有 Player stats 标签。已实测：

```python
page.get_by_role('tab', name='Player stats', exact=True).click()
page.locator('table').first.wait_for(state='visible', timeout=30000)
page.get_by_role('tab', name='Passing', exact=True).click()
```

六分类准确英文名称：General、Attacking、Defending、Passing、Duels、Goalkeeping。逐一读取每类当前表头与行。General 为基础身份集合，Goalkeeping 通常仅门将；不能要求门将分类行数等于 General。

页面中的 Statistics 是比赛/球队统计入口，不要误当成逐场球员表入口。初始 table 数量为 0 是正常现象；不能直接判为缺失。旧报告关于海港—河南缺少统计的结论已撤回。

### 比赛身份必须在落盘前验证

从已验证赛程清单取得预期 ID、日期、主队、客队、轮次。页面完成加载后检查：

1. 当前 URL fragment 中事件 ID 与目标相符。
2. 比赛内容区显示预期日期、两队、赛事与轮次；同时核对比分和完赛状态。
3. 表格行中球队集合与这两队相符。
4. 内容在连续两次观察中稳定，且分类标签 `aria-selected=true`、表头符合所选分类。

URL 正确不能单独证明内容正确。同一对阵链接初次可能显示另一场更新比赛，然后才切换到历史 ID。页面标题通常不包含日期，也不能单独作为证据。2025 赛季实际补赛日期不一定与轮次日期一致。

生产版本使用有界 DOM 条件等待，最多 60 秒；网站广告连接可能持续，不能依赖 networkidle。轮次/分类标签改变后，要等待对应内容更新，而不只等待按钮被选中。必要时记录旧表头签名与旧首行键，联合新分类独有列检查；切换到相同类别时不要要求内容必然改变。

## 5. DOM 提取规则（已发现的关键陷阱）

以目标表格为作用域：`thead th` 获取当前表头，`tbody tr` 获取行，逐行 `td` 获取单元格。先排除无关表格，不长期依赖全页面第一个 table。以 Player stats 对应 tabpanel + 表头签名定位；选择器匹配零个或多个目标时保存现场、停止该场标准化，不能随意取第一个。

- 球员：`a[href*="/football/player/"]` 的 href 最后一段为 player_id；保存显示姓名和链接。姓名会有转写差异，以 ID 关联。
- 球队：首列队徽的 `img.alt` 是全队名。首列 innerText 为空不代表没有球队。保留映射到赛程 team_id 的依据；不要从球员当前俱乐部回填历史归属。
- 评分：优先在评分单元格读取 `[role="meter"]` 的 `aria-valuenow`。CSS 动画评分的 innerText 可能为空。三场实测分别恢复 32、32、31 个评分。没有 meter 时，才检查经过验证的普通显示文本；均无值则 null。禁止把空评分填为 0。
- 普通数字：保存原始单元格文本，去除外围空白后解析；空白、0、缺列分开记录。
- 表头前两列实测 innerText 为 `""` 和 `"+"`，分别代表球队和球员，不应把它们当业务统计列。
- 不硬编码所有统计的列序；按表头名称映射。新增/缺失列写入 schema drift 报告。
- 不用应用状态、script JSON 或网络响应补齐表格空白。DOM 无障碍属性属于页面元素信息，可以读取。

离线使用 Scrapling Selector：

```python
from scrapling.parser import Selector
selector = Selector(html_text)
cells = selector.css('table tbody tr')[0].css('td')
raw_text = str(cells[2].get_all_text(separator=' ', strip=True))
```

在实测 0.4.15 中，`xpath('string(.)').get()` 出现字符串序列化异常；使用已经验证的 `get_all_text`，不要照搬这个失败写法。保存渲染 HTML、页面可见文本和可访问性快照便于离线修正。

## 6. 字段字典及缺失处理

首轮六分类已读到以下表头；其他比赛必须逐场检查，不能默认全赛季一致：

| 类别 | 页面统计列 |
|---|---|
| General | Goals; Assists; Tackles (won); Accurate passes; Duels (won); Ground duels (won); Aerial duels (won); Minutes played; Position; Sofascore Rating |
| Attacking | Shots on target; Shots off target; Shots blocked; Dribbles (successful); Notes; Position; Sofascore Rating |
| Defending | Defensive actions; Clearances; Blocked shots; Interceptions; Tackles (won); Dribbled past; Notes; Position; Sofascore Rating |
| Passing | Touches; Accurate passes; Key passes; Crosses (accurate); Long balls (accurate); Notes; Position; Sofascore Rating |
| Duels | Duels (won); Ground duels (won); Aerial duels (won); Possession lost; Fouls; Was fouled; Offsides; Position; Sofascore Rating |
| Goalkeeping | Total saves; Punches; High claims; Notes; Sofascore Rating |

解析示例：

- `29/32 (91%)` → completed=29、attempted=32、displayed_pct=91；比例允许显示舍入误差 0.51 个百分点。
- `7 (4)` 在 Duels (won) 中 → total=7、won=4；同理处理地面、空中、过人、传中、长传等成对字段，但以对应表头定义为准。
- Tackles (won) 只有一个数时不猜省略项含义；保留 raw，未明确的子字段为 null。
- `90'` → provider_minutes=90，同时保留 raw。不要截断成 90，也不要用换人时间重新计算替换它。
- `""` → null + missing_reason=`blank_cell`；页面明确 `0` 才是 0。字段不存在用 `column_absent`。
- 球员位置按场次保存。Notes 先原文保存；未证实其图标/提示语语义前不转成数字。
- 总射门只有当三个构成项都存在且语义确认时才派生，并记录 derived 标志；缺一项不把它补 0。
- xG、xA、逐次事件坐标、跑动距离、冲刺等不是本次六分类通用字段，不承诺全季可得；如后续另行探测，单独报覆盖率。

核心键为 `(source, season_id, match_id, player_id)`；分类原始行另加 category。跨分类按球员 ID 连接，不按排序位置连接。重复列应核对一致性，冲突保留双方原值并报错，不静默覆盖。

## 7. 建立全赛季赛程清单（批量遍历待实现与验收）

入口：`https://www.sofascore.com/football/tournament/china/cfa-super-league/649#id:71364,tab:matches`。

competition_id=649，season_id=71364，Beijing Guoan team_id=3376。核对页面显示 2025，然后进入 Matches / By round。既往页面观察到的控件名称为 `Select season in unique tournament header`、`Select item in event list`。这部分历史控件观察并不等于本次 Scrapling 已完成 30 轮遍历；实现时先保存当前 DOM 验证角色和名称。

前一轮探针确实确认两个combobox名称、2025及Round 30，赛程遍历也已完成并经结构审计。本批再次检查时网页显示“No events”，By round轮次combobox消失，事件列表不再渲染。不可因此丢弃已保存的赛程卡片证据。重新尝试时记录当前页面DOM和日期；不可臆造比赛URL。

逐轮遍历 1–30：

1. 选择正确赛季和轮次。自定义 combobox 不能盲用 select_option；查看 DOM 决定用 option 点击或键盘。此前上下方向键加 Enter 能改变轮次，但必须核验实际内容。
2. 在赛事主内容列表中提取 href 含 `/football/match/` 的比赛链接，过滤页顶 Trending 和页尾推荐。
3. 获取可见日期、状态、队徽 alt 所示主客顺序、比分、href 和事件 ID。href slug 的队名顺序不等于主客顺序。
4. 比分可能存在动画/辅助重复文本，不能盲目取 innerText 最后两个数字。检查实际比分元素，核对匹配到的是两队比分。
5. 每轮保存渲染证据与原始行，并检查所选轮次和内容一致。出现空列表先检查水合/等待，不能直接判该轮无比赛。

保存两张表：完整 raw_event_ledger 和去除延期空壳后的 finished_match_manifest。预计目标是 16 队双循环、240 场完赛；原始事件条目可能多于 240。

此前页面观察到三组延期替换，必须在本次采集中重新确认并保存证据：

| 轮次/对阵 | 延期事件 ID | 补赛事件 ID |
|---|---:|---:|
| R26 山东—云南 | 13522641 | 14636006 |
| R24 梅州—青岛海牛 | 13522623 | 14468703 |
| R6 河南—上海海港 | 13763651 | 13885475 |

不要硬编码原始总数一定等于 243。将同轮、同主客队、状态及补赛页信息联合核验后建立 superseded_by 映射，保留延期原始条目，不删除证据。不能按相同两队名称直接去重，主客两回合不同。

清单验收：240 个唯一完赛 ID、16 队、每队 30 场且 15 主15客、每轮 8 场完赛、每个有序主客组合出现一次、国安 30 场。任何条件不符先查清，不裁剪或补造记录以凑数。

## 8. 先 10 场验收，再批量

生产采集器至少包含：`collect_fixture_manifest`、`collect_match_dom`、`parse_match_dom`、`validate_match`、`audit_season`。可用单一 CLI 的子命令实现，不强制文件名，但保证采集和离线解析分离。

选取赛季初中末、不同球队、至少一场补赛的 10 场。每场完成身份核验、General、其余五类、球队统计和阵容/换人核对；后两类页面采集在本次尚未实现，需要先验证 DOM。首发与未出场替补另存 lineup 表，不从 General 排序推断。

已验证三场参考：

| 比赛 ID | 日期 | 比分 | General 行数 |
|---|---|---|---:|
| 13400350 | 2025-02-22 云南—国安 | 0–2 | 31 |
| 13522595 | 2025-08-15 海港—河南 | 4–1 | 32 |
| 13522670 | 2025-11-22 国安—梅州 | 5–1 | 32 |

95 行是三场不同 player-match，不是95名不同球员。后续页面若更正数据，不强制改回本表；记录差异和新证据。

检查每类是否虚拟滚动/分页：滚动表格容器到末尾，合并新增 player_id，直至连续两次无新增且到达底部；观察分页或 Show more 是否属于目标表，不能误点评论的 Show more。31/32 行是样本观察值，不作为每场固定行数。

10 场通过后启动全季，默认单浏览器单并发，比赛之间间隔至少 3 秒。可使用持久 DynamicSession 减少启动开销，但先做两场对照确认无跨场旧 DOM。性能优化不能牺牲身份核验。

## 9. 断点续采、证据及错误分类

每次运行生成 run_id（UTC 时间戳），不得覆盖唯一旧证据。每场每分类保存渲染 HTML、表头、原始 cells、player/team 标识、页面 URL、观察时间、版本、选择器版本、SHA-256。截图在试采、异常及抽样复核时保存；不要全量截图造成不必要体积。

写入临时文件后原子替换，校验通过才更新 checkpoint。中断后重启应跳过证据齐全且校验通过的场次；failed/partial 单独重试。逐场状态至少包括 pending、in_progress、partial、validated、failed；分类也有独立状态。记录 error_type、attempts、last_attempt、evidence_path。

错误分类：navigation_timeout、identity_mismatch、challenge_or_access_denied、player_stats_tab_missing、category_missing、table_not_ready、schema_drift、parse_error、incomplete_roster、network_error。标签缺失先核验比赛身份、展开阵容区并重载一次；仍缺失保存证据。403/429 或访问验证页面不得写成成功的空表。

普通瞬时失败最多重试 2 次，退避例如 10 秒、30 秒；如果响应有 Retry-After 则尊重它。连续 3 场同类失败暂停批量并诊断；禁止无限刷新，也不因此删除已成功数据。长任务保持简短进度更新，不要每场向用户请求许可。

## 10. 完整性标准，不能只数比赛

分开报告赛程覆盖、逐场出场球员覆盖、分类覆盖、字段非空率。240 场都有1行远远不够。

- 每场与阵容、换人事件核对：两队首发及实际替补出场球员应被 General 覆盖；未出场替补单列。红牌或伤退不导致删行。
- 列出每场每队球员行数、各分类行数、与预期出场集合的差集。
- 正常外场分类与 General 的 ID 集合不符时调查；门将分类单独核对门将出场集合，包括替补门将。
- 球员 ID 唯一，外键引用存在，所属队符合该场；没有 orphan rows。
- 成功次数不超过总次数，传球百分比舍入合理；统计非负；评分按页面 meter 范围检查。
- 球员进球和比分可交叉核对，但乌龙球、赛后判罚等需解释，不能为了相等修改原值。样本脚本仅对三场固定基准检查，不是通用进球审计规则。
- 分钟和位置异常记录，不擅自矫正。不要强制两队分钟和等于990。
- null 与真实0分别统计，按球队/轮次/分类报告缺失集中性。
- 至少抽查10场，与保存网页/截图逐项对比；优先复查异常、补赛、门将、红牌和替补记录。
- 只在240场都完成所要求分类、出场集合核对及质量验收后标记本阶段 complete。若部分网页确实缺字段，交付现有数据和明确缺口，不伪装完整。

## 11. 交付与测试

建议输出：

- `data/csl/season_2025/raw_event_ledger.csv`、`match_manifest.csv`。
- `data/csl/season_2025/player_match_stats.csv`（标准化宽表）和原始分类 JSONL。
- `data/csl/season_2025/lineups.csv`、`checkpoint.json`、`failures.csv`。
- `reports/analysis/CSL_2025_COLLECTION_AUDIT.md` 及机器可读 JSON。
- 可运行的采集/解析脚本、锁定依赖、重跑与断点续采命令。

字段至少包含 source、competition_id、season_id、match_id、match_date、round、team_id（有可靠映射时）、team_name、player_id、player_name、position、provider_minutes、starter（有阵容证据时）、六类已覆盖统计、observed_at、raw_evidence_path、parser_version。现有模板列不够可以扩充，不能因模板没有列而丢掉关键传球、地面对抗等已采字段。

运行有意义的离线回归：空白与0、评分 aria、队徽 alt、列序改变、分类错页、主客误判、延期事件映射、重复 ID、失败重跑幂等、半写入恢复。使用真实已保存 HTML，避免为了测试反复访问网站。旧 pilot 测试继续运行，新增批量检查需确实验证出场完整性。

最终报告明确：实际完成了多少场/240、多少 player-match、国安多少场/30、哪些分类完整、哪些字段缺失、哪些失败可重试；列出未完成事项和原因。采集日期晚于赛季时说明这是回溯获取的数据，不能当作当时可知快照。提供真实文件链接，不把空目录、模板、请求成功日志当作数据交付。

执行顺序：读取进度 → 环境核验 → 复现样本/离线检查 → 建立并验收赛程 → 10场试采 → 补充完整性审计 → 全季采集 → 失败补采 → 最终审计。已有证据仍有效时不重复劳动，但未经验证的步骤必须实际运行。

---

参考： [Scrapling 仓库](https://github.com/d4vinci/Scrapling)、[动态页面文档](https://scrapling.readthedocs.io/en/latest/fetching/dynamic.html)、[安装说明](https://scrapling.readthedocs.io/en/latest/#installation)。在线文档可能领先于安装版本，运行时以锁定版本签名及实测为准。
