# M1 数据质量报告

生成时间（UTC）: 2026-09-23T16:00:56.405640+00:00
原始数据目录: `F:\Samuel\football recruitment\archive\msc-inter-departure-2025\data excel`

## 各赛季概况

| 赛季 | 原始行 | 唯一球员 | 清洗后 | 合并中场转会 | 多位置 | 低样本 | 候选池 |
|---|---|---|---|---|---|---|---|
| 2022-2023 | 603 | 577 | 577 | 26 | 116 | 147 | 430 |
| 2023-2024 | 616 | 590 | 590 | 26 | 140 | 168 | 422 |
| 2024-2025 | 634 | 599 | 599 | 35 | 160 | 170 | 429 |

## 国米阵容

### 2022-2023 —— 25 人（离队 12 / 留队 13）

| 位置 | 人数 | 离队 |
|---|---|---|
| Defender | 11 | 4 |
| Forward | 4 | 2 |
| Goalkeeper | 3 | 3 |
| Midfielder | 7 | 3 |

低样本球员（出场不足门槛，下游需降级处理）:

- Alex Cordaz（26 分钟）
- Mattia Zanotti（27 分钟）
- Valentin Carboni（25 分钟）

### 2023-2024 —— 27 人（离队 7 / 留队 20）

| 位置 | 人数 | 离队 |
|---|---|---|
| Defender | 11 | 1 |
| Forward | 4 | 1 |
| Goalkeeper | 3 | 1 |
| Midfielder | 9 | 4 |

低样本球员（出场不足门槛，下游需降级处理）:

- Davy Klaassen（206 分钟）
- Ebenezer Akinsanmiro（15 分钟）
- Emil Audero（337 分钟）
- Juan Cuadrado（267 分钟）
- Lucien Agoume（5 分钟）
- Raffaele Di Gennaro（23 分钟）
- Stefano Sensi（46 分钟）
- Tajon Buchanan（161 分钟）

### 2024-2025 —— 26 人（无离队标签：归档中没有该赛季的标签文件）

| 位置 | 人数 | 离队 |
|---|---|---|
| Defender | 12 | - |
| Forward | 5 | - |
| Goalkeeper | 2 | - |
| Midfielder | 7 | - |

低样本球员（出场不足门槛，下游需降级处理）:

- Luka Topalović（11 分钟）
- Tajon Buchanan（95 分钟）

## 已知数据缺口（不可通过现有数据弥补）

- 无转会费 / 球员估值 —— 因此不做性价比与预算分析
- 无薪资数据 —— 因此不做薪资结构分析
- 无伤病历史 —— 因此不做可用性风险
- 无位置坐标（x/y）数据 —— 角色刻画基于行为统计而非触球热区
- 候选池仅限 Serie A —— 无法推荐其他联赛球员
- 合同信息仅覆盖国米球员（每赛季约 25-27 人），联赛其他球员无合同数据

## 处理方式说明

- **表头解析**：FBref 三层表头，`skiprows=3`（旧项目用 2，会读入一行幽灵表头）
- **球员去重**：赛季中转会的球员按球员名聚合，计数指标求和、age 取最大、team 记为 `MULTI:队A|队B`
- **位置解析**：保留完整位置列表（`positions_all`）；主位置取 FBref 列出的第一个位置（实测逗号顺序本身表达主次，`FW,MF` 与 `MF,FW` 是两个不同取值）；跨队球员的主位置取**出场时间最多的那个 stint**
- **低样本**：`Min < 450` 标记为 `is_low_sample`，**标记而不删除**
- **候选池**：`Min >= 450` 且位置可解析
- **合同**：`-1` 识别为租借（`is_loan=True`），其剩余年数置空；未匹配到合同的球员 `has_contract_info=False`
- **标签**：未匹配到标签的球员 `has_departure_label=False`；无标签文件的赛季整列为空
- **2024-2025**：来源是原始 HTML（FBref 把球员表放在 HTML 注释内，须先剥离 `<!--`/`-->`）。该赛季**只有 standard 一类统计**，缺 goal/shooting/passing/possession/defensive/goalkeeper，且**没有标签与合同文件**，故只能用于画像与候选池，不能用于离队风险建模