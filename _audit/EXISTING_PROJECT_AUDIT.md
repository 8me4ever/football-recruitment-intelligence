# EXISTING_PROJECT_AUDIT.md — 旧 Inter Milan 项目取证审计

> **交付物 A**（对应主提示词 §17）
> 审计对象：`F:\Samuel\football recruitment\final project`
> 审计日期：本次会话
> 审计方法：180 个文件全量清单 → 逐行追踪代码 → **在项目自带 venv 中实机复现** → 与论文逐表对照
> **未修改任何原项目文件**；所有审计产物写入 `_audit\`

---

## 1. Executive Summary（执行摘要）

### 1.1 这个项目实际上是什么

一个**英国伯明翰大学 MSc 数据科学毕业论文项目**（作者 Ziming Chen，导师 Todd），主题为足球转会（国际米兰球员离队）预测。

**代码层面它是什么**：一个**启发式加权评分器**。

```
球员指标 → 按位置计算联赛百分位 → 加权平均得"表现分"
        → 基础风险（年龄 sigmoid） + (1 − 表现分) × 风险系数
        = 离队概率
```

公式共 3 行，参数 16 个（每个位置）。**没有任何监督学习模型**（无逻辑回归、无树模型、无神经网络、无损失函数反传）。所谓"优化"仅仅是用元启发式算法在 **25 个标签**上搜索这 16 个权重的最佳取值。

**论文层面它声称是什么**：一个名为"Multi-layer Probability Fusion Algorithm"的"算法创新"，声称取得 92.8% 准确率、96.48% PR-AUC，对基线有"35.3% 提升"，并有多重统计显著性检验（p<0.001）支撑。

**两者之间的差距**构成本次审计的核心结论。

### 1.2 一句话定性

> **这是一个用 4 种元启发式算法在一份 25 行标签上做权重寻优的确定性评分器。它本身是合理的研究练习，但其论文核心统计结论建立在伪造数据和训练集自评之上，不能作为新系统的算法基石。**

### 1.3 最关键的 5 个事实

| # | 事实 | 证据 |
|---|---|---|
| 1 | **论文的统计显著性检验数据是程序伪造的** | `Run_Statistical_Tests.py:20-45` 用 `np.random.normal(0.928, 0.008, 10)` 造出"PSO 实验结果"；`Statistical_Testing_Framework.create_sample_data_for_testing()`（:72-105）同样伪造；而 `results.tex:52` 声称这是 "multi-run experimental data (5 independent runs per algorithm)" |
| 2 | **评估是训练集自评，样本内 96% / 样本外仅 77.78%** | `evaluate_weights_enhanced()` 在全样本上计算目标函数；我实测样本内净增益 +44.0pp，样本外净增益仅 **+3.7pp**（基线 0.7407） |
| 3 | **4 个"算法"共享同一目标函数与同一套边界**，GA 实为差分进化，且 GA/RS 的 5 次"独立运行"结果完全相同（std=0.0000） | `*_Final.py` 中 `get_bounds()` 与 `fitness_function()` 逐字符相同；`GA_..._Final.py:81` `seed=42` 硬编码 |
| 4 | **合同数据从未被使用**，论文大篇幅论述的"合同 sigmoid / α / τ"对结果零影响 | 所有最终脚本调用 `calculate_enhanced_percentile_scores(player, league, pos_ds)` 均未传 `contract_data`，导致合同的百分位输入恒为常数 0.5 |
| 5 | **存在一个可修复的真实缺陷：赛季错配**，修正后样本外 0.7778 → **0.8519** | `2023_2024_Prediction.py:171` 加载的是 2022-2023 的位置统计文件；我用正确赛季数据复测得到 0.8519（TP=7, FN=0） |

### 1.4 审计结论一句话

旧项目**不应被丢弃，也不应被当作架构基础**。它的价值在于：
- ✅ **数据管道思路**（FBref 多级表头解析、按位置百分位）可直接复用；
- ✅ **实验记录习惯**（JSON 结构化输出、时间戳、多轮运行）值得保留；
- ✅ **它踩过的坑是本项目最宝贵的资产**（样本量、自评、伪造、赛季错配）；
- ❌ 它的**建模方法、论文结论、评估框架**必须整体推倒重做。

---

## 2. Workspace Structure（工作区结构）

### 2.1 全景

```
F:\Samuel\football recruitment\
└── final project\                     ← 唯一项目根（无多版本项目副本）
    ├── *.py                    54 个  ← 全部平铺在根目录，无包结构
    ├── *.md                    12 份
    ├── *.txt                   19 个  ← 结果报告与草稿混杂
    ├── *.png                   42 张
    ├── *.json                   3 个
    ├── *.csv                   23 个
    ├── main.py                        ← PyCharm 模板，不是入口
    ├── venv\                          457.6 MB，依赖完整
    ├── data\                          8 个 FBref 原始 HTML（含 2024-25 赛季）
    ├── data excel\
    │   ├── 2022-2023\          10 个 CSV
    │   └── 2023-2024\          10 个 CSV
    ├── Inter_Defenders_Analysis\        12 张雷达图 + 摘要
    ├── Inter_Forwards_Analysis_Fixed\    4 张雷达图 + 摘要
    ├── Inter_Midfielders_Analysis\       7 张雷达图 + 摘要
    ├── Inter_Midfielders_Analysis(原）\   7 张（旧版，已被取代）
    ├── LaTeX_Dissertation\              论文 8 章
    ├── 语音转写\                         语音转写文本（与代码无关）
    ├── .idea\ .claude\                 IDE / 工具配置
    └── claude-code / 111.txt            空文件
```

### 2.2 结构性缺陷

| 问题 | 说明 |
|---|---|
| 无分层 | 54 个 `.py`、23 个 CSV、42 张图全部平铺在同一个目录，**没有 src/、没有 data/ 分层、没有 results/ 目录** |
| 无测试 | 0 个正式测试（`test_*.py` 全是开发期临时脚本） |
| 无配置 | 无 `requirements.txt`、无 `pyproject.toml`、无 `.env`；依赖只能从 `venv` 反推 |
| 无 notebook | **0 个 `.ipynb`**（提示词猜测有，实际没有） |
| 无 Excel | **0 个 Excel 文件**（提示词猜测有，实际没有） |
| 路径硬编码 | `2023_2024_Prediction.py:15,163` 硬编码 `F:\Samuel\学习\final project` |

---

## 3. Existing Data（现有数据）

### 3.1 数据源

**FBref.com**（`data_collection.tex:5` 明确说明）。`data\` 目录下的 HTML 是 FBref 网页原档，CSV 是从中导出的多级表头文件。

### 3.2 数据文件结构（关键，所有下游代码都依赖它）

FBref 导出的 CSV 是**三层表头**：

| 行号 | 内容 |
|---|---|
| row 0 | 指标**组名**（`Playing Time`、`Performance`、`Expected`…） |
| row 1 | **指标名**（`MP`、`Starts`、`Min`、`Gls`…） |
| row 2 | 字段名（`league`、`season`、`team`、`player`…，仅前 4 列有值） |
| row 3+ | 数据 |

**这是本项目最重要的技术前提**，也是旧代码 bug 的来源：核心引擎用 `skiprows=2` + 手工 `names=[...]`，**跳过了 2 行而不是 3 行**，于是 row2 被当成数据读入。

实测后果：

```
skiprows=2 → 604 行（含 1 行冗余表头，age 列因此变成 float）
skiprows=3 → 603 行（正确）
```

冗余行因 `player` 列值为 `"player"`、`age` 为 `NaN` 而侥幸未污染模型，但：
- `age` 列类型被污染为 float；
- 若 `dropna` 条件变化，冗余行会静默进入样本；
- `2023_2024_Prediction.py` 用的是 `skiprows=2`，与核心引擎的 `skiprows=2` 一致但都与正确值不符。

### 3.3 数据规模（实测 vs 论文声明）

| 赛季 | 数据行 | 唯一球员 | 球队 | 论文声明 | 判定 |
|---|---|---|---|---|---|
| 2022-2023 | 603 | **577** | 20 | 535 名 / 20 队 | ❌ 差 42 人 |
| 2023-2024 | 616 | **590** | 20 | 547 名 / 20 队 | ❌ 差 43 人 |

> 论文的 535/547 既不等于行数（603/616）也不等于唯一球员数（577/590），来源不明。

### 3.4 可用指标字典（实测，共 101 个去重指标）

| 类别 | 指标数 | 代表指标 |
|---|---|---|
| standard | 29 | MP, Starts, **Min**, 90s, Gls, Ast, G+A, PK, CrdY, CrdR, xG, npxG, xAG, npxG+xAG, PrgC, PrgP, PrgR + 10 个 per-90 派生 |
| goal | 16 | **SCA**, SCA90, PassLive, PassDead, TO, Sh, Fld, Def, **GCA**, GCA90 + 6 个 GCA 细分 |
| shooting | 17 | Gls, Sh, **SoT**, SoT%, Sh/90, SoT/90, G/Sh, G/SoT, Dist, FK, PK, PKatt, xG, npxG, npxG/Sh, G−xG, np:G−xG |
| passing | 16 | Cmp, Att, **Cmp%**, TotDist, **PrgDist**, Short/Medium/Long 三档 Cmp%, xA, A−xAG |
| possession | 22 | **Touches**, Def Pen, Def/Mid/Att 3rd, Att Pen, Live, Take-Ons(Att/Succ/Succ%/Tkld), **Carries**, **PrgC**, CPA, Mis, Dis, Rec, **PrgR** |
| defensive | 12 | **Tkl**, TklW, 三个区域 Tkl, Challenges(Tkl/Att/Tkl%/Lost), **Blocks**, Sh/Pass Blocks |
| goalkeeper | 19 | MP, Starts, Min, 90s, GA, **GA90**, SoTA, **Saves**, **Save%**, W, D, L, **CS**, **CS%**, PKatt, PKA, PKsv, PKm, PK Save% |
| **gk_adv**（先进门将） | 25 | GA, PKA, FK, CK, OG, **PSxG**, PSxG/SoT, PSxG+/−, /90, Launched(Cmp/Att/Cmp%), Passes(Att/Thr/Launch%/AvgLen), Goal Kicks, Crosses(Opp/Stp/Stp%), **Sweeper(#OPA, #OPA/90, AvgDist)** |

**重要**：`goalkeeper_advance` 类别包含 **PSxG（射门后预期进球）与 Sweeper（防守出击）**等高价值指标，**旧模型完全未使用**。新系统做门将画像时有充分素材。

### 3.5 标签与目标变量

| 赛季 | 国米球员 | 离队 | 留队 | 离队率 | "全预测留队"基线准确率 |
|---|---|---|---|---|---|
| 2022-2023 | 25 | 12 | 13 | 0.480 | **0.5200** |
| 2023-2024 | 27 | 7 | 20 | 0.259 | **0.7407** |

**"离队"的定义**：从两份 CSV 的文件名与内容看，2022-2023 是"离开 2022-23 赛季国米阵容"，2023-2024 是"离开 2023-24 赛季国米阵容"。**定义未在代码或数据中形式化文档化**，仅人工编制。这导致：
- 租借球员算不算离队？（`Alex Cordaz`、`Raoul Bellanova`、`Romelu Lukaku` 等标记为 1）
- 合同自然到期与转会未区分；
- **无法判断标签是否在预测时点可知**（潜在的前视偏差）。

### 3.6 合同数据（存在但失效）

| 文件 | 行数 | 编码方案 |
|---|---|---|
| `Contract_2022_2023.csv` | 26 | 剩余年数；**`-1` 表示租借球员**；`0` 表示合同到期 |
| `Contract_2023_2024.csv` | 28 | 同上 |

实测：每赛季有 **4 名租借球员**（`-1`），其合同年限不可直接使用。旧代码：
1. **从未把该文件传入**计算函数 → 合同项恒为 `percentile=0.5` → `contract_years = (1−0.5)×4 = 2.0` 常数；
2. 因此 `calculate_base_risk_sigmoid(age, 2.0, α, τ)` 中的 `years_left` 恒为 2.0，合同维度**完全失效**；
3. 但 `calculate_base_risk_sigmoid()` **本身是活的**——它在 `weight_optimization_core_updated.py:324` 被正常调用；失效的是喂给它的 `contract_years` 恒为常数（详见 §5.2 的审计更正）。

> **结论：论文第 5、6 章关于"合同 sigmoid 参数优化"（α=4.00、τ=0.61、risk_multiplier=0.70）的整段论述，描述的是对结果毫无影响的过程。**

### 3.7 数据质量问题（实测）

| # | 问题 | 规模 | 后果 |
|---|---|---|---|
| Q1 | **赛季中转会导致球员重复** | 每赛季 52 行、26 名球员 | 这些球员被**计两次**进入百分位参考池，扭曲该位置的分位数 |
| Q2 | **低出场样本未过滤** | 2022-23: 75 行；2023-24: 88 行（最少 5 分钟） | 论文与连续性文档都声称 `min_minutes = 90` 过滤，**代码中从未实现**。噪声样本参与百分位计算 |
| Q3 | **多位置球员信息丢失** | 2022-23: 118 人；2023-24: 143 人（如 `pos='FW,MF'`） | 旧代码只取首个匹配的位置字母，**丢弃第二位置**。这直接影响"位置分组建模"的分组正确性 |
| Q4 | **数据完整度声明不实** | 论文称 96.8%–98.5% 并列出具体缺失条数 | 实测核心指标列 **零缺失（100%）** |
| Q5 | **季节错配** | `2023_2024_Prediction.py:171` | 2023-24 预测时使用 2022-23 的位置统计数据 |
| Q6 | **静默吞异常** | `load_experimental_data_enhanced()` 末尾 `except Exception: return None, None, None` | 数据加载失败时无任何诊断信息，表现为"无结果" |
| Q7 | **无数据校验** | 全项目 0 个 schema 校验、0 个范围检查 | 论文声称的"Z-score/IQR 异常值检测（12/18 个）"在代码中不存在 |

### 3.8 赛季覆盖

| 赛季 | CSV | HTML | 状态 |
|---|---|---|---|
| 2022-2023 | ✅ 10 个 | ✅ | 训练用 |
| 2023-2024 | ✅ 10 个 | ✅ | 留出验证用 |
| **2024-2025** | ❌ **无** | ✅ `players_ITA-SerieA_2425_standard.html`（2.0 MB） | **原始 HTML 存在但从未解析** |

> **这是一条被浪费的资产**：2024-25 赛季的 standard 数据已经在磁盘上，只需解析即可获得第三个赛季（可用于真正的时间外验证，或作为"当前阵容"基准）。

---

## 4. Existing Pipeline（现有管道）

### 4.1 实际数据流（逐行追踪代码得出）

```
① weight_optimization_core_updated.load_experimental_data_enhanced()
   ├─ 读 Inter_Players_Departure_Labels.csv            → {球员名: 0/1}
   ├─ 读 data excel/2022-2023/..._standard_...csv       skiprows=2 (!) → 604 行
   ├─ 按 pos 列映射 position_group（取首个匹配字母）
   ├─ 筛 team == 'Inter'                                → 25 行
   ├─ 用球员名匹配标签（字符串精确匹配）                    → 全部 25 人匹配成功
   └─ 返回 (inter_data, df_league, position_datasets)
                    ↓
② load_position_specific_data()
   ├─ goal + shooting          → Forward
   ├─ passing + possession     → Midfielder
   ├─ passing + defensive      → Defender
   └─ goalkeeper                → Goalkeeper
   注意：passing 被 Midfielder 与 Defender 共享（同一 DataFrame 对象）
                    ↓
③ 对每个位置 p ∈ {Forward, Midfielder, Defender, Goalkeeper}：
   ├─ 优化器用元启发式算法搜索 16 维权重向量，目标 = evaluate_weights_enhanced()
   │   └─ 对 p 的 n 名球员（n = 4 / 7 / 11 / 3）：
   │       ├─ calculate_enhanced_percentile_scores()   → 每指标映射到联赛内百分位
   │       ├─ calculate_departure_probability_with_weights()
   │       │     表现分 = Σ(百分位 × 权重) / Σ(权重)
   │       │     基础风险 = sigmoid(...)  ← 合同项恒为常数 2.0，实际是年龄函数
   │       │     离队概率 = 基础风险 + (1 − 表现分) × risk_multiplier
   │       │     截断到 [0.05, 0.95]
   │       └─ 阈值 0.5 二分类 → 与 departed_label 比较
   │   └─ 复合分 = 0.4×PR-AUC + 0.3×F1 + 0.2×BalancedAcc + 0.1×(1−Brier)
                    ↓
④ Multi_Run_Experiment_Framework_Final.py
   ├─ 对 4 个算法各跑 N 轮（实际 N=5，论文声称 10）
   ├─ 每轮 np.random.seed(42 + run_i)
   ├─ 聚合平均 → Multi_Run_Experiment_Results_*.json
   └─ Algorithm_Comparison_Visualization → PNG
                    ↓
⑤ 2023_2024_Prediction.py
   ├─ 硬编码 PSO 权重（从 .txt 权重报告人工转录）
   ├─ 加载 2023-2024 standard 数据 + 2023-2024 标签
   ├─ 【BUG】load_position_specific_data() 读的是 2022-2023 文件
   └─ 输出 accuracy / precision / recall / PR-AUC
```

### 4.2 管道性质判定（回答 §6 的关键问题）

| 判定项 | 结论 | 依据 |
|---|---|---|
| 是否是**监督学习**？ | ❌ **不是** | 无参数化模型、无损失函数、无梯度、无拟合过程。权重是**搜索**出来的超参，不是**学习**出来的模型参数 |
| 是否是**启发式评分**？ | ✅ **是** | 核心是人工设计的线性加权公式 |
| 是否是**优化驱动的权重标定**？ | ✅ **是** | 元启发式算法在此扮演的角色是"在 25 个样本上标定评分权重" |
| 是否是**规则式概率构造**？ | ✅ **是** | 输出被截断在 [0.05, 0.95]，但从无概率校准（无 Platt/Isotonic），**不是校准概率** |
| 是否是**混合系统**？ | ⚠️ 部分 | "百分位特征工程（统计）+ 元启发式寻优（优化）+ 线性公式（启发式）"三段拼合；但**没有任何一段是机器学习** |

> **明确结论：把该系统称为 "machine learning" 是不准确的。** 代码内部（`Single_Run_ML_Metrics_*.txt`、`results.tex` 的 "Machine Learning Performance Metrics"）大量使用 ML 术语，但实际是**在统计指标上评估一个确定性评分器**。这一点在新系统中必须纠正措辞。

### 4.3 百分位特征工程（唯一真正可复用的算法）

```python
def calculate_percentile_score(value, reference_data, ascending=True):
    if pd.isna(value) or len(reference_data) == 0:
        return 0.5
    reference_data = reference_data.dropna()
    if ascending:
        percentile = stats.percentileofscore(reference_data, value, kind='rank') / 100
    else:
        percentile = 1 - (stats.percentileofscore(reference_data, value, kind='rank') / 100)
    return max(0, min(1, percentile))
```

**评价**：
- ✅ 思路正确：同位置内相对排名，避免"后卫 vs 前锋比进球"（符合提示词 Principle 8）
- ✅ 缺失值回退到 0.5（中性）是合理设计
- ⚠️ `kind='rank'` 对并列值处理较弱（大量并列 0 值指标会产生"伪高分"：一个 0 进球的后卫可能排在同一批 0 进球球员中位）
- ⚠️ **没有任何最小出场时间门槛**（论文暗示有，实际没有），低样本球员的百分位极不稳定
- ⚠️ 无**收缩估计**（empirical Bayes shrinkage）：n=5 分钟的球员与 n=3000 分钟的球员被同等对待

### 4.4 位置分组（存在真实缺陷）

```python
if 'GK' in pos_str:        return 'Goalkeeper'
elif 'FW' in pos_str:      return 'Forward'
elif 'MF' in pos_str:      return 'Midfielder'
elif 'DF' in pos_str:      return 'Defender'
```

**问题**：FBref 的 `pos` 是多位置字符串（`'FW,MF'`、`'MF,DF'`、`'DF,MF'`）。
- 实测 2022-23 有 118 名多位置球员，2023-24 有 143 名
- 该 if-elif 链按 GK→FW→MF→DF 顺序取**首个命中**，即 `'MF,DF'` 会被归为 Midfielder、`'FW,MF'` 归为 Forward
- 结果：国米样本中 `Valentin Carboni`（`MF,DF`）被归为中场、`Alexis Sánchez`（`FW,MF`）被归为前锋
- **这直接改变了 4 个位置模型的样本构成**，是一个静默的分组偏差

我实测两种口径的差异：

| 口径 | Defender | Midfielder | Forward | Goalkeeper |
|---|---|---|---|---|
| 旧代码（首个匹配） | 11 | 7 | 4 | 3 |
| 我实现的（按 GK<DF<MF<FW 优先级） | 12 | 6 | 4 | 3 |

---

## 5. Existing Models / Algorithms（现有模型与算法）

### 5.1 核心公式（唯一"模型"）

**文件**：`weight_optimization_core_updated.py:289-327`

```python
performance_score = (universal_score + position_score) / (universal_weight + position_weight)
contract_percentile = percentile_scores.get('Contract_expires', 0.5)   # ← 恒为 0.5
contract_years      = max(0, (1 - contract_percentile) * 4)            # ← 恒为 2.0
base_risk           = calculate_base_risk_sigmoid(age, contract_years, alpha, tau)
departure_prob      = base_risk + (1 - performance_score) * risk_multiplier
return max(0.05, min(0.95, departure_prob))
```

数学形式：

$$
P_{\text{depart}} = \mathrm{clip}\Big(\underbrace{\sigma\big(\alpha(0.6\, s_{\text{year}} + 0.4\, s_{\text{age}}) - \tau\big)}_{r_{\text{base}}} + (1 - \bar{p})\cdot m,\ 0.05,\ 0.95\Big)
$$

其中
- $\bar p = \dfrac{\sum_i w_i\, q_i}{\sum_i w_i}$，$q_i$ 为指标 $i$ 的**位置内百分位**，$w_i$ 为待优化权重；
- $s_{\text{year}} = \text{clip}\big((3 - y)/3, 0, 1\big)$，$y$ 为合同剩余年数 → **因 $y\equiv 2$，此项恒为 $1/3$**；
- $s_{\text{age}} = \text{clip}\big(1 - |\text{age} - 30|/6,\ 0, 1\big)$；
- $r_{\text{base}}$ 随后被 `np.clip(..., 0.1, 0.3)` 强制压缩到 **[0.1, 0.3]**。

**公式的方法论问题**（必须在审计中指出）：

| 问题 | 说明 |
|---|---|
| **不是校准概率** | 输出被 clip 到 [0.05, 0.95]，且构造方式使其**永远无法接近 0 或 1**。论文却以 "departure probability" 对待，并用 Brier score 评估——Brier 在未校准分数上无意义 |
| **"风险"与"表现"的耦合是任意的** | "表现好 → 不易离队"是一个**未经验证的假设**。实际上顶级球员更可能被豪门买走（如 Onana、Brozović、Škriniar 均为高水平球员且离队）|
| **基础风险被 clip 到 0.1–0.3** | 相当于人工压平了年龄信号；再叠加 `risk_multiplier ∈ [0.3, 0.7]`，输出范围被压缩到约 [0.1, 1.0)，实测输出集中在 **0.32–0.68** 的窄带内 |
| **年龄方向可疑** | `s_age` 在 age=30 处取最大值，即 30 岁被视为**最可能离队**。但 30 岁恰是当打之年；真正的高风险是 <22（潜力股被挖）与 >33（合同到期/退役）。实测年龄与离队的点二列相关 **r = −0.008, p = 0.969**，即**年龄在数据中与离队完全无关** |
| **黄牌/红牌被计入"表现分"** | `CrdY`、`CrdR` 出现在通用指标中且 `ascending=True`，即**牌越多→"表现越好"→越不易离队**。这在足球逻辑上是反向的 |

### 5.2 合同 sigmoid（函数是活的，但输入失效）

`weight_optimization_core_updated.py:280-287` 定义了 `calculate_base_risk_sigmoid()`，并在 **第 324 行被真实调用**：

```python
319:  contract_percentile = percentile_scores.get('Contract_expires', 0.5)
320:  contract_years = max(0, (1 - contract_percentile) * 4)
324:  base_risk = calculate_base_risk_sigmoid(age, contract_years, alpha, tau)
```

> **审计更正**：本报告初稿曾称该函数是"死代码、逻辑在别处重复实现"。经核实**不成立**——它是活的、被正常调用的。真正失效的是它的**输入**：由于 `contract_data` 从未被传入 `calculate_enhanced_percentile_scores()`，`percentile_scores['Contract_expires']` 恒为默认值 **0.5** → `contract_years` 恒为 **2.0** → `year_score = clip((3−2)/3, 0, 1) = 1/3` **对所有球员恒定**。

因此准确的表述是：**合同 sigmoid 函数本身工作正常，但它的合同输入是一个常数，导致合同维度在结果中零贡献。** 结论（合同对结果无影响）不变，但归因应指向"数据未接线"而非"函数未使用"。

### 5.3 四个优化算法（实质是同一模型的四种求参法）

| 文件 | 声称 | 实际实现 | 迭代预算 | 独立随机性 |
|---|---|---|---|---|
| `GA_Weight_Optimization_Experiment_Final.py` | Genetic Algorithm | `scipy.optimize.differential_evolution(maxiter=20, popsize=10, seed=42)` | ≈20×10×16 | ❌ **seed 硬编码 42**，5 轮结果完全相同 |
| `PSO_Weight_Optimization_Experiment_Final.py` | Particle Swarm | 手写 PSO：w=0.7, c1=c2=1.5, 30 粒子 × 50 代 | 1500 | ✅ 用 `np.random`，受外层 seed 控制 |
| `SA_Weight_Optimization_Experiment_Final.py` | Simulated Annealing | 手写 SA：T0=100, 指数退火 α=0.95, 1000 次迭代 | ~2000 | ✅ 用 `np.random` |
| `RS_Weight_Optimization_Experiment_Final.py` | Random Search | 60% 纯随机 + 40% 对当前最优加高斯噪声（"smart"策略），1500 次 | 1500 | ⚠️ 用 `np.random`，但结果 5 轮均为 0.92 |

**四者共享完全相同的东西**：

```python
# GA_Final.py:26-55 == PSO_Final.py:26-54 == SA_Final.py == RS_Final.py  （逐字符相同）
def get_bounds(self):
    ...
    bounds[f'{metric_name}_weight'] = (0.08, 0.15)   # "重要"指标
    bounds[f'{metric_name}_weight'] = (0.05, 0.12)   # 其他指标
    bounds.update({'alpha': (1.0, 4.0), 'tau': (0.3, 0.7), 'risk_multiplier': (0.3, 0.7)})

# 四者的 fitness_function 都调用同一个
evaluate_weights_enhanced(weights_dict, self.inter_data, self.league_data,
                          self.position_datasets, self.position)
```

**∴ "对比 4 种优化算法"实质是"对比 4 种搜索策略在同一个 16 维、目标函数完全相同的空间上的寻优能力"。这不是模型对比，是优化器对比。**

### 5.4 目标函数（复合分的构造）

`weight_optimization_core_updated.py:353-358`

```python
composite_score = (0.40 * pr_auc + 0.30 * f1
                 + 0.20 * balanced_accuracy + 0.10 * (1 - brier))
```

**问题**：
- 四个分量的**权重 0.4/0.3/0.2/0.1 是任意设定的**，没有论证，也没有敏感性分析（论文声称做了"权重敏感性分析"，但那是 `Generalization_Testing_Framework.py` 里一段**不可运行**的代码）；
- `pr_auc` 在 n=3、正例率 100%（Goalkeeper）时**恒为 1.0**，成为一个"免费满分"项；
- 该复合分是**在训练集上**计算的，优化器直接最大化它 → **目标函数即评估指标，构成循环论证**。

### 5.5 实测：优化器真的在学习吗？

我在 venv 中对 **Forward 位置（n=4）** 做了对照实验：

| 权重方案 | 复合分 | Accuracy | PR-AUC | F1 |
|---|---|---|---|---|
| 全部取下界（0.08/0.05） | 0.5085 | 0.50 | 0.8333 | 0.000 |
| 全部取中点 | 0.7605 | 0.75 | 0.8333 | 0.667 |
| **全部取上界（0.15/0.12）** | **0.8336** | **0.75** | **1.0000** | 0.667 |
| 随机采样 200 组 | 0.6801 ± 0.1214 | — | — | — |
| **差分进化寻优（1152 次评估）** | **0.8341** | — | — | — |

**关键观察**：
1. **"全部取上界"就能得到 PR-AUC = 1.0**（4 个样本的 PR-AUC 可以轻易饱和）；
2. 差分进化跑了 1152 次评估，最终得分 **0.834071**，仅比"全部取上界"的 **0.833568** 高 **0.0005**；
3. 最优解中有 4/16 个参数贴在边界上（`alpha`=3.96/上限4.0、`risk_multiplier`=0.697/上限0.7、`CrdY_weight`=0.0804/下限0.08、`G_per_Sh_weight`=0.0512/下限0.05）；
4. 最优解把 **`CrdY_weight` 压到下界**——这恰好说明优化器在此数据上"发现"黄牌不该加分，但它只是**拟合了 4 个样本的噪声**，没有统计意义。

> **结论：在 n=3~11 的样本上，16 维参数空间是完全过参数化的。优化器做的不是"学习规律"，而是"记忆答案"。**

### 5.6 多轮运行的独立性问题（实测 JSON）

我解析了 `Multi_Run_Experiment_Results_20250826_171631.json`（4 算法 × 5 轮）：

| 算法 | 5 轮 accuracy | 均值 | 标准差 | 论文表格值 |
|---|---|---|---|---|
| GA | `[0.92, 0.92, 0.92, 0.92, 0.92]` | 0.9200 | **0.0000** | 0.9200 ✓ |
| PSO | `[0.96, 0.92, 0.92, 0.92, 0.92]` | 0.9280 | 0.0160 | 0.9280 ✓ |
| SA | `[0.60, 0.76, 0.76, 0.76, 0.76]` | 0.7280 | 0.0640 | 0.7280 ✓ |
| RS | `[0.92, 0.92, 0.92, 0.92, 0.92]` | 0.9200 | 0.0000 | 0.9200 ✓ |

**发现**：
- ✅ 论文表格的均值**确实来自该 JSON**（数字可溯源，这一点是诚实的）；
- ❌ 但 **GA 与 RS 的 5 轮结果完全相同（std = 0.0000）** → 它们**不是 5 次独立实验**。GA 的 `seed=42` 写死在 `differential_evolution()` 调用里，`np.random.seed(42+run_i)` 对它无效；
- ❌ 论文 `results.tex:4` 写 "Each optimization algorithm was executed with **10 independent runs using different random seeds**"，而 `results.tex:52` 又写 "**5 independent runs** per algorithm"，**同一份论文内部矛盾**，且实际是 5 轮，其中 2 个算法根本不是独立运行。

### 5.7 优化算法的必要性评估

| 算法 | 判定 | 理由 |
|---|---|---|
| GA（差分进化） | **ARCHIVE / REMOVE** | 全局优化器用在 16 维小空间上属杀鸡用牛刀；其结果与"全部取上界"的差距（0.0005）远小于噪声。且名实不符（称 GA 实为 DE） |
| PSO | **REPURPOSE** | 思路可用，但应改为**在合理约束下做正则化拟合**（如带 L2 惩罚、logistic 回归），而非无约束搜索 |
| SA | **ARCHIVE** | 结果最差（0.728 ≈ 多数类基线 0.6364~1.0 区间内），且耗时 217s，**无任何证据表明它有助于足球决策** |
| RS | **ARCHIVE** | 表现与 GA/PSO 齐平，说明空间本身容易被搜索——这恰恰证明**问题不需要复杂算法**，优化器不是瓶颈 |

> 依据提示词 §7 与 §19（"Technical sophistication is deliberately last"）：**保留优化器不能因为其技术复杂度，只能因为它服务于足球决策问题。当前证据不支持保留任何一个。**

### 5.8 泄漏与过拟合风险清单

| 风险 | 存在？ | 说明 |
|---|---|---|
| 训练集=测试集 | ✅ **存在，严重** | `evaluate_weights_enhanced()` 在全部 25 个样本上评分，优化器直接最大化该分数 |
| 目标函数=评估指标 | ✅ **存在** | 复合分既是优化目标又作为报告指标 |
| 特征穿越（look-ahead） | ⚠️ 可能 | 标签定义不明确；若"离队"是在赛季结束后确定，而特征用整个赛季数据，则存在前视偏差 |
| 赛季间信息泄漏 | ⚠️ 可能 | 百分位参考池含 2023-24 赛季中从国米离开的球员 |
| 多重比较未校正 | ✅ **存在** | 每个位置独立优化 16 参数 × 4 位置 × 4 算法 × 5 轮 = 1280 次搜索，无任何选择性偏差讨论 |
| 超参搜索无嵌套CV | ✅ **存在** | 不存在嵌套交叉验证；超参在测试集上挑选 |
| 伪重复 | ✅ **存在** | 52 行赛季中转会球员重复进入参考池 |

---

## 6. Existing Evaluation（现有评估）

### 6.1 使用的指标

```python
accuracy, precision, recall, f1_score, average_precision_score (PR-AUC),
roc_auc_score, cohen_kappa_score, matthews_corrcoef,
balanced_accuracy_score, brier_score_loss
```

**指标选择本身是合理的**——类别不平衡下用 PR-AUC、MCC、Balanced Accuracy 比单看 accuracy 好。这一点值得肯定。

### 6.2 评估设计与真实表现

**（A）样本内评估（2022-2023，n=25）**

我实测（用 `2023_2024_Prediction.py` 内嵌的 PSO 权重）：

```
n=25  离队=12  预测离队=11
Accuracy = 0.9600   「全预测留队」基线 = 0.5200   净增益 = +0.4400
混淆矩阵 TP=11 FP=0 FN=1 TN=13
```

- 论文报告 0.9280（来自 5 轮均值），我复测单次配置得 **0.9600**（TP=11, FN=1）。差异说明**不同权重配置在此数据上有 0.92–0.96 的波动**——这个波动本身就表明结果不稳定。
- 净增益 +44.0pp 看起来很美，但这是**样本内**。

**（B）样本外评估（2023-2024，n=27）**

我在 venv 中**精确复现**了论文的留出集结果：

```
n=27  离队=7  预测离队=9
Accuracy = 0.7778   Precision = 0.5556   Recall = 0.7143   F1 = 0.6250   PR-AUC = 0.6459
混淆矩阵 TP=5 FP=4 FN=2 TN=16
「全预测留队」基线准确率 = 0.7407
净增益 = +0.0371  （3.7 个百分点）
```

> **论文 `results.tex` 表 tab:prediction_metrics_2023_2024 与 tab:prediction_errors_2023_2024 的数字，我在 venv 中按代码逻辑逐行复算后完全一致**（0.7778 / 0.5556 / 0.7143 / 0.6459，混淆矩阵 TP=5 FP=4 FN=2 TN=16，6 个错误案例逐条吻合）。
>
> ⚠️ **但必须精确说明证据链**：磁盘上**没有任何一个脚本产物直接记录了 0.7778**。全库检索 `0.7778 / 0.5556 / 0.7143 / 0.6459` 在 7 份业务结果文件中**零命中**；唯一存盘的留出集产物是 `Inter_2023_2024_Prediction_Report_20250826_172047.txt`，其值为 **0.7407** 且已退化为常数预测器。
>
> 因此准确表述是：**论文表格的数字与"代码逻辑的正确执行结果"一致（我已复现），但与"磁盘上存盘的任何一次运行"都不一致。** 这说明产生论文数字的那次运行**没有留下产物文件**（或产物被覆盖），即**该结果缺乏可追溯的原始输出**——这本身就是一个可复现性缺陷。

但审计必须指出：
- 净增益仅 **+3.7pp**，且 4 个"预测离队"的错误（FP）里有 2 个（`Raffaele Di Gennaro` 0.5553、`Yann Sommer` 0.5430）**仅比阈值 0.5 高 0.05**，属噪声级别；
- 5 个正确识别的离队（TP）中，`Ebenezer Akinsanmiro`（**15 分钟**出场，概率 0.5013）和 `Lucien Agoume`（**5 分钟**出场，概率 0.5046）**也是勉强越过阈值**。两人合计出场 20 分钟，被"预测"离队，属于低样本偶然命中；
- 在 n=27、7 个正例的情况下，单次准确率的 95% 置信区间约为 **±0.16**（Wilson 区间 [0.59, 0.90]）。**0.7778 与基线 0.7407 的差异在统计上完全不显著。**

**（C）一个可修复的真实缺陷：赛季错配**

我发现 `2023_2024_Prediction.py:171` 调用 `load_position_specific_data()` 时读的是 **2022-2023** 的位置统计文件。我把位置数据集改为正确的 2023-2024 后复测：

| 配置 | Accuracy | 混淆矩阵 | 相对基线净增益 |
|---|---|---|---|
| 原脚本（误用 2022-23 位置数据） | 0.7778 | TP=5 FP=4 FN=2 TN=16 | +0.0371 |
| **修正为 2023-24 位置数据** | **0.8519** | **TP=7 FP=4 FN=0 TN=16** | **+0.1111** |

> **修正一个真实 bug，样本外准确率从 77.78% 提升到 85.19%，召回率从 0.714 提升到 1.000（漏报归零）。** 这是一个具体、可验证、不涉及编造的改进点，建议纳入迁移计划的第一步。
>
> ⚠️ 但必须诚实标注：这是在单个赛季、单次配置上的结果，样本仍只有 27 人，**不能宣称"模型变强了"**，只能作为"缺陷修复后的初步证据"。

### 6.3 一个更严重的发现：同一目标，两次运行结果截然不同

磁盘上另有一份更早的报告 `Inter_2023_2024_Prediction_Report_20250826_172047.txt`：

```
Accuracy: 0.7407    Precision: 0.0000    Recall: 0.0000    F1: 0.0000
PR-AUC: 0.2593      ROC-AUC: 0.5000     Cohen's Kappa: 0.0000    MCC: 0.0000
Balanced Accuracy: 0.5000    Brier: 0.2500
所有球员 position = "Unknown"，departure_probability 恒为 50.0%
```

**解读**：该次运行中位置解析**完全失败**（全为 `Unknown`），所有球员被赋予默认概率 0.5，模型退化为常数预测器。其 0.7407 准确率**恰好等于"全预测留队"基线**，而 Precision/Recall/F1/MCC/Kappa **全为 0** 是常数预测器的典型特征。

> 同一目标（2023-24 预测）在同一天（17:17 与 17:20）产生了两份结论相反的报告。这说明流程**不稳定、不可复现、缺乏回归测试**。论文只采纳了对自己有利的那一份，且未在任何地方提及另一份。

### 6.4 统计检验的严重问题（本次审计最重大的发现）

`Run_Statistical_Tests.py:13-45`：

```python
# 基于Multi_Run_Average_Metrics的实际结果创建数据
# 模拟10次运行的数据 (基于实际结果)
np.random.seed(42)
n_runs = 10
pso_accuracy = np.random.normal(0.928, 0.008, n_runs)   # ← 伪造
ga_accuracy  = np.random.normal(0.920, 0.010, n_runs)   # ← 伪造
sa_accuracy  = np.random.normal(0.728, 0.015, n_runs)   # ← 伪造
...
```

`Statistical_Testing_Framework.create_sample_data_for_testing()`（第 72-105 行）同样伪造。

随后这些**正态分布随机数**被送进 `ttest_1samp`、`ttest_rel`、`wilcoxon`，产生论文表格中的：

| 论文表格 | 声称 | 实际来源 |
|---|---|---|
| tab:one_sample_testing | PSO Accuracy t=110.429, p<0.001, **Cohen's d=34.92** | `np.random.normal(0.928, 0.008, 10)` 生成的 10 个随机数 |
| tab:paired_testing | PSO vs GA Accuracy t=3.464, p=0.007 | 两组伪造随机数 |
| tab:wilcoxon_test | PSO vs SA W=0.0, p=0.002 | 同上 |

而 `results.tex:52` 却说：

> "Comprehensive statistical testing was conducted to validate the significance of improvements ... using **multi-run experimental data (5 independent runs per algorithm)**."

**多重问题叠加**：
1. **数据是伪造的**（`np.random.normal`），却未在论文中声明为"模拟"；
2. **轮数不一致**：伪造用 `n_runs = 10`，论文正文说 5 轮，`results.tex:4` 又说 10 轮；
3. **效应量荒谬**：Cohen's d = 34.92 意味着标准差只有均值的 1/35。任何审阅者都应立刻察觉这不可能——**这不是真实数据能产生的效应量**；
4. **结论是硬编码的**：`Run_Statistical_Tests.py:183-186` 直接写死
   ```
   print("1. PSO算法在所有指标上都显著优于基线 (p < 0.001)")
   print("2. PSO与GA算法性能相近，差异不显著")
   ```
   **无论输入的随机数是什么，这些结论都会原样打印。**

### 6.5 论文声称的验证手段 vs 实际

| 论文声称 | 代码位置 | 实际状态 |
|---|---|---|
| "temporal cross-validation" | `Generalization_Testing_Framework.temporal_generalization_test()` | ❌ 若未提供未来赛季数据，则**用 `np.random.choice` 从当前联赛数据中随机抽 1/3 冒充"未来赛季"**（第 204-208 行）。**这是伪造的跨时间验证** |
| "cross-validation stability testing" | `cross_validation_stability_test()` | ❌ 不可运行：`self.optimizer.__class__(train_fold, val_fold, self.optimizer.position_type)` 的签名与实际优化器不符；且用训练折的分数当验证分数（`optimized_score = optimization_result['best_score']`）→ **泄漏** |
| "noise robustness testing" | `robustness_to_noise_test()` | ❌ 依赖 `_evaluate_on_dataset()` → `_evaluate_weights_on_fold()` 调用 `optimizer.calculate_percentile_features()` / `optimizer.calculate_departure_probability()`。**这两个方法确实存在**，在 `Weight_Optimization_Framework.py:115` / `:177` 的 `PercentileWeightOptimizer` 类上——但 `Generalization_Testing_Framework` 被设计为接收 `_Final` 系列的优化器对象，而那些是**模块级函数 + 无类**的 `weight_optimization_core_updated.py`，**根本不具备这两个方法** → 版本错配（见下方 §6.5.1） |
| "weight sensitivity analysis" | `weight_sensitivity_analysis()` | ❌ 依赖 `self.optimizer.best_weights`，但 `_Final` 系列的优化器类没有该属性（权重在返回的 dict 里，不是实例属性） |
| "5-run multi-run experiments" | `Multi_Run_Experiment_Framework_Final.py` | ⚠️ 可运行，但 GA/RS 的"多轮"不独立（std=0.0000） |
| "ground truth verification" | 标签 CSV | ✅ 真实存在 |
| "multi-club validation" | — | ❌ 不存在 |
| 特征重要性 / SHAP | — | ❌ **完全不存在**（无 shap 依赖、无相关代码） |

> **`Generalization_Testing_Framework.py` 是一个 600 行的"空壳"**：它定义了完整的测试框架、评分等级（✅ HIGHLY STABLE 等）、甚至会自动生成 JSON 报告，**但核心评估方法依赖的两个优化器方法只存在于第 1 代的类式实现上，而项目实际使用的是模块级函数式的 `_Final` 引擎** → **该框架从未成功与真实引擎对接过**。

#### 6.5.1 一个必须澄清的细节：不是"调用了不存在的方法"，而是"版本错配"

审计过程中一个重要更正：`calculate_percentile_features()` 与 `calculate_departure_probability()` **并非不存在**。它们真实定义在：

```
Weight_Optimization_Framework.py:115   def calculate_percentile_features(self, player_data, league_data)
Weight_Optimization_Framework.py:177   def calculate_departure_probability(self, percentile_features, weights)
```

属于**第 1 代**的 `PercentileWeightOptimizer` 类（08-08）。

**真正的问题是架构代际断裂**：

| 代际 | 形态 | 调用方式 |
|---|---|---|
| 第 1 代（`Weight_Optimization_Framework.py`） | **类式**：`PercentileWeightOptimizer` 有 `calculate_percentile_features` / `calculate_departure_probability` / `best_weights` 等实例方法 | `optimizer.calculate_percentile_features(...)` |
| 第 4 代（`weight_optimization_core_updated.py` + `*_Final.py`） | **函数式**：模块级函数 `calculate_enhanced_percentile_scores()` / `calculate_departure_probability_with_weights()`，优化器类**只负责搜索**，不含评估方法 | `calculate_enhanced_percentile_scores(...)` |

`Generalization_Testing_Framework` 的 `_evaluate_weights_on_fold()`（第 445-448 行）写的是**第 1 代的调用方式**，但项目实际运行的是第 4 代引擎 → **接口不兼容**。

**更硬的缺陷（两个独立证据）**：

1. `class GeneralizationValidator` 在**全仓库零实例化**——没有任何文件 `import` 或 `new` 它；
2. 该文件的 `__main__`（第 599-600 行）只调用 `example_generalization_testing()`，而后者（第 590-597 行）**函数体只有 4 句 `print`**，不含任何测试逻辑。

⇒ **结论不变且更明确：整个泛化测试框架从未执行过。** 但准确表述应是"**版本错配 + 类从未被实例化 + 入口是空 stub**"，而非"方法不存在"。

### 6.6 论文表格溯源结论

| 表 | 内容 | 可否溯源 | 判定 |
|---|---|---|---|
| tab:algorithm_performance | 4 算法性能对比 | ✅ 可溯源至 `Multi_Run_Average_Metrics_20250826_171631.txt` | **真实** |
| tab:sigmoid_parameters | α/τ/risk_multiplier | ✅ 可溯源至同一文件 | **真实，但描述的过程（合同 sigmoid）无效** |
| tab:one_sample_testing | 单样本 t 检验 | ❌ **伪造数据** | **不成立** |
| tab:paired_testing | 配对 t 检验 | ❌ **伪造数据** | **不成立** |
| tab:wilcoxon_test | Wilcoxon 检验 | ❌ **伪造数据** | **不成立** |
| tab:forward/midfielder/defender/goalkeeper_weights | 各位置最优权重 | ✅ 可溯源 | **真实** |
| tab:prediction_metrics_2023_2024 | 留出集指标 | ✅ 我已在 venv 中精确复现 | **真实** |
| tab:prediction_errors_2023_2024 | 错误案例 | ✅ 我已在 venv 中精确复现 | **真实** |
| tab:successful_predictions_2023_2024 | 成功案例 | ✅ 可复现 | **真实** |
| tab:position_specific_2023_2024 | 分位置准确率 | ✅ 可复现（Forward 3/3、Midfielder 7/9、Defender 9/12、Goalkeeper 1/3） | **真实** |
| tab:seria_dataset / tab:inter_squad / tab:transfer_outcomes / tab:data_completeness / tab:outliers | 数据章节 5 张表 | ❌ 与磁盘数据全部不符 | **不实** |

**结论**：论文的**结果章节（第 6 章）中，实验性能表是真实的，统计显著性表是伪造的，数据章节（第 4 章）的表是不实的。**

### 6.7 论文内部矛盾汇总

| # | 矛盾 | 位置 |
|---|---|---|
| 1 | 运行轮数：10 轮 vs 5 轮 | `results.tex:4`（10 independent runs）vs `results.tex:52`（5 independent runs） |
| 2 | 数据规模：535/547 vs 实际 577/590 | `data_collection.tex:13,23-24` |
| 3 | 国米标签：10 离队/15 留队 vs 实际 12/13 | `data_collection.tex:76,86-87` |
| 4 | 位置分布：门将2/后卫11/中场8/前锋4 vs 实际 门将3/后卫11/中场7/前锋4（代码口径） | `data_collection.tex:56,66-69` |
| 5 | 数据完整度 96.8–98.5% vs 实际 100% | `data_collection.tex:96-114` |
| 6 | 导师质疑"这是算法创新还是简单应用？" vs 论文宣称"novel algorithm / significant advancement" | `Project_Continuity_Documentation.md:26` vs `results.tex:403` |
| 7 | 论文称 "Genetic Algorithm" vs 代码用差分进化 | `results.tex:8` vs `GA_..._Final.py:76` |
| 8 | README 称 "92.0% 预测准确率（35.3% improvement over baseline）" vs 留出集实际 77.78%、基线 74.07%（+3.7pp） | `LaTeX_Dissertation\README.md:115` |

---

## 7. Key Technical Debt（关键技术债）

按"对新系统的阻塞程度"排序。

### 🔴 P0 — 阻断级（不解决则新系统建立在不实基础上）

| # | 债 | 位置 | 偿还方式 |
|---|---|---|---|
| D1 | **伪造实验数据生成显著性结论** | `Run_Statistical_Tests.py:20-45`、`Statistical_Testing_Framework.py:72-105` | 立即弃用；新系统的所有统计结论必须来自真实运行产物；在文档中明确标注旧结论已作废 |
| D2 | **评估=训练集自评** | `weight_optimization_core_updated.py:329-373` | 重建评估层：训练/验证/时间外三分；超参搜索必须嵌套在训练折内 |
| D3 | **样本量 25 且过参数化（16 参数/位置）** | 全体 `*_Final.py` | 放弃"每位置独立模型"；改用**跨位置共享的少量参数**（正则化逻辑回归）或纯透明的启发式规则 |
| D4 | **目标函数=报告指标（循环论证）** | `evaluate_weights_enhanced()` | 分离：优化目标与最终评估指标必须不同，且评估只在留出集做 |
| D5 | **"离队概率"未校准** | `calculate_departure_probability_with_weights():327` | 要么做概率校准（Platt/Isotonic，需 ≥200 样本），要么**改名为"风险评分"并放弃概率语义** |

### 🟠 P1 — 严重（导致结果不可信或不稳定）

| # | 债 | 位置 |
|---|---|---|
| D6 | 赛季错配（2023-24 预测用 2022-23 位置数据） | `2023_2024_Prediction.py:171-172` |
| D7 | 合同数据从未传入 → 合同维度完全失效 | 所有 `calculate_enhanced_percentile_scores()` 调用点 |
| D8 | `Generalization_Testing_Framework.py` 与真实引擎**版本错配**（调用第 1 代类式 API）；"时间泛化"用随机抽样冒充；`GeneralizationValidator` 零实例化，入口是空 stub | 第 107-108、204-208、445-447、590-600 行 |
| D9 | `Multi_Algorithm_Comparison_Experiment.py` 导入 **4 个**不存在的模块（另 1 个缺失模块 `Multi_Run_Experiment_Framework` 见 `test_fixed_framework.py:29`） | 第 65-74 行 |
| D10 | `skiprows=2` 应为 `3`，引入 phantom 数据行 | `weight_optimization_core_updated.py:24`、`2023_2024_Prediction.py:39` |
| D11 | GA/RS 的"多轮实验"不独立（seed 硬编码） | `GA_..._Final.py:81` |
| D12 | 位置分组丢失多位置信息（118/143 名球员受影响） | `get_position_group()` 全部实现 |
| D13 | 52 行赛季中转会球员重复进入百分位池 | 无去重逻辑 |
| D14 | 低出场样本未过滤（75/88 行，最少 5 分钟） | 论文/文档声称有 `min_minutes=90`，代码无 |
| D15 | 同一目标两次运行结论相反（0.7778 vs 0.7407 且后者退化为常数预测器） | `Inter_2023_2024_Prediction_Report_*.txt` |

### 🟡 P2 — 中等（阻碍可维护性与复现性）

| # | 债 |
|---|---|
| D16 | 硬编码绝对路径 `F:\Samuel\学习\final project`（`2023_2024_Prediction.py:15,163`） |
| D17 | 无 `requirements.txt` / `pyproject.toml`，依赖只能从 venv 反推 |
| D18 | 54 个 `.py` 平铺根目录，同一算法 3–4 代并存（`_Clean`/`_Updated`/`_Final`） |
| D19 | 22 个草稿脚本（`111.py`、`tax.py`、`test_*.py` 等）混杂其中 |
| D20 | 全项目 `except Exception: pass` / `return None` 静默吞异常（核心引擎、所有实验框架） |
| D21 | 代码重复：`_Updated` 系列把核心引擎的 7 个函数**逐字节内联复制**，却修改了其中的概率模型，导致同名函数语义不同（见 D31） |
| D22 | `Project_Continuity_Documentation.md` 引用 5 个不存在的文件 |
| D23 | 无任何 schema 校验 / 数据范围检查 |
| D24 | 无回归测试；同一目标的两次运行结果不可复现 |
| D25 | 4 个算法文件 90% 代码重复（bounds、fitness、输出逻辑） |
| D26 | 权重从 `.txt` 报告手工转录回代码（`2023_2024_Prediction.py:83-157` 硬编码 64 个数值） |
| D27 | **8 个"惰性"权重维度**：指标声明了 `source`，但该位置的数据集里没有那张表/那一列 → 恒取 0.5 兜底，对应权重对目标函数零影响（Forward 的 `Att_Pen`/`TakeOn_Succ`；Midfielder 的 `Tkl`/`SCA`；Defender 的 `Def_3rd`；Goalkeeper 的 `PK_Save`/`Cmp_40_plus`；通用的 `Contract_expires`） |
| D28 | **`_Updated` 与 `_Final` 存在"同名同签名但语义不同"的函数**：`calculate_departure_probability_with_weights()` 在两代中实现不同 → GA（引用 `_Updated` 的副本）与 PSO/SA/RS 的分数**不可比**，却被同一外部框架汇总比较 |
| D29 | `_Updated` 是相对 `_Final` 的**回归**（mtime 早 10 小时、引用不存在的模块、内联副本），却仍在仓库中与 `_Final` 并存 |
| D30 | `Multi_Run_Experiment_Framework_Final.py:329` 把嵌套 dict 传给 `create_charts_from_multi_run_data()`，该函数调用 `.iterrows()` → AttributeError 被吞掉 → **多轮对比图从未生成** |
| D31 | venv 缺 `openpyxl`/`xlsxwriter`，`manual_integration.py:50`、`test.py:15` 的 xlsx 导出必然失败 |
| D32 | `test_prediction_model.py:11-12` 在**模块级**执行 `os.chdir`，导入即改工作目录 |

### 🟢 P3 — 轻微

| # | 债 |
|---|---|
| D33 | `main.py` 是 PyCharm 模板，误导入口 |
| D34 | 无 notebook、无 Excel、无独立结果目录 |
| D35 | 图表文件名带时间戳但无索引，难以对应实验 |
| D36 | 中文/英文文档混杂，术语不统一 |
| D37 | 4 个 `Statistical_Test_Results_*.txt` 中至少 2 份**逐字节相同**（仅时间戳不同），即相隔 5 天的"两次检验"是同一种子的重复运行 |
| D38 | `模型对比.txt` 给出**第三套互斥结果**（标题称"10 次运行"实际 5 次；SA=0.684 vs 论文 0.7280；平均用时全为 0.0 秒） |
| D39 | `PPT_Content_Document.md` 给出**与论文对立的最优算法**（GA 0.6895 > PSO 0.6324），而论文称 PSO 最优 |

---

## 8. Reusable Assets（可复用资产）

### 8.1 A 类 — 几乎可直接复用（High）

| 资产 | 文件 | 复用方式 | 需修补 |
|---|---|---|---|
| **FBref 多级表头解析逻辑** | `weight_optimization_core_updated.py:64-121` | 直接搬到 `src/data/loaders.py` | 修 `skiprows=3`；显式校验列数 |
| **百分位转换函数** | `calculate_percentile_score()` | 搬到 `src/features/percentiles.py` | 加最小出场门槛、加收缩估计、处理并列值 |
| **位置专属指标映射表** | `get_position_specific_metrics()` | 搬到 `src/features/position_features.py` | 去掉 `CrdY/CrdR` 作为"表现"；引入门将 adv 指标 |
| **联赛内按位置分组的参考池构造** | `calculate_enhanced_percentile_scores()` 中的 `position_filter` 逻辑 | 搬到 `src/features/contextualisation.py` | 先修位置分组与去重 |
| **实验记录习惯**（JSON + 时间戳 + 多轮聚合） | `Multi_Run_Experiment_Framework_Final.py:30-105` | 保留模式，重写实现 | 加真正的随机种子管理、加留出机制 |
| **可视化脚本** | `Algorithm_Comparison_Visualization.py` | 搬到 `src/visualization/` | 去掉"ML Metrics"措辞 |
| **指标选择清单**（PR-AUC/MCC/Balanced Acc/Brier） | `weight_optimization_core_updated.py:5-7` | 直接用作评估层指标集 | 加置信区间、加基线对照 |

### 8.2 B 类 — 重构后复用（Medium）

| 资产 | 说明 |
|---|---|
| **国米阵容名单 + 离队标签**（25+27 人） | 数据本身有效，但标签定义需重新文档化，且需评估前视偏差 |
| **Serie A 候选池**（去重后 577/590 人） | 数据有效，但需去重、过滤低样本、修位置分组后才可用于引援搜索 |
| **"离队风险"评分逻辑** | 概念方向正确（表现 + 年龄 + 合同 → 风险），但**必须重构为透明规则 + 明确不确定性**，不再伪装为概率 |
| **基础风险 sigmoid 思路** | sigmoid 形状合理，但需重新论证自变量与参数；当前 α/τ 取值来自伪造过程的"优化" |
| **加权评分框架** | 结构可留，但权重来源必须改为**专家先验**或**正则化拟合**，并给出敏感性分析 |

### 8.3 C 类 — 仅作历史参考（Low）

| 资产 | 处置 |
|---|---|
| 论文 8 章 LaTeX | 归档；**第 4 章与第 6 章统计部分不可再引用** |
| `results.tex` 中的统计显著性表 | 归档并标注"数据来源为模拟，结论不成立" |
| 42 张 PNG 图表 | 归档；其中球员雷达图（23 张）仍可作为新版画像的格式参考 |
| `Inter_Midfielders_Analysis(原）` | 重复的旧版，归档 |
| 11 份根目录 `.md` 技术文档 | 归档；**诚实化拐点之后的中文文档（8/19 之后）仍具参考价值** |
| `Demonstration Slide——Ziming Chen.pptx` | 归档 |
| `语音转写` | 与代码无关，归档 |

### 8.4 D 类 — 应退役（Retire）

| 资产 | 退役理由 |
|---|---|
| `Run_Statistical_Tests.py` | **伪造数据**，必须退役并留档说明 |
| `Statistical_Testing_Framework.create_sample_data_for_testing()` | 同上 |
| `Generalization_Testing_Framework.py` | 600 行空壳，核心方法不存在，且含伪造的"时间泛化" |
| `Multi_Algorithm_Comparison_Experiment.py` | 导入 4 个不存在的模块，无法运行 |
| `Weight_Optimization_Framework.py` + `Weight_Optimization_Experiment.py`（第 1 代） | 贝叶斯/网格搜索版本，已被 `_Final` 取代；且用英文长指标名，与数据不兼容 |
| `*_Clean.py`（4 个）与 `*_Updated.py`（4 个） | 中间代际，被 `_Final` 取代 |
| `simple_weight_optimization_demo.py`、`simple_weight_experiment.py`、`Fixed_Weight_Optimization_Experiment.py` | 早期探索，逻辑已并入 `_Final` |
| 22 个草稿脚本（`111.py`、`222.py`、`444.py`、`555.py`、`tax.py`、`test.py`、`test_*.py`、`basic_test.py`、`manual_integration.py`、`def_possession.py`、`Multi_Algorithm_Comparison_Clean.py`、`Simple_Chart_Generator.py`） | 开发残留 |
| `Enhanced_Evaluation_Metrics_Framework.py`、`Statistical_Significance_Testing_Framework.py` | 与 `Run_Statistical_Tests.py` 同源的伪造/空壳评估代码 |
| `Inter_Players_Departure_Labels.csv`（根目录副本） | 与 `data excel\2022-2023\` 下的同名文件重复 |
| `main.py`、`claude-code`、`111.txt`、`模型对比.txt` | 空文件或模板 |

---

## 9. Assets to Archive（应归档的资产）

**归档原则（遵循提示词 Principle 2：不删除旧项目文件）**：新建 `archive/` 目录，把旧项目**整体**移入，保留原始结构，另加一份 `archive/README_ARCHIVED.md` 说明：

```text
archive/
└── msc-inter-departure-2025/
    ├── README_ARCHIVED.md          ← 新写：说明这是什么、哪些结论已作废、为什么
    ├── AUDIT_FINDINGS.md           ← 指向本次审计的四份交付物
    ├── code/                       ← 原 54 个 .py
    ├── data/                       ← 原 data/ 与 data excel/
    ├── results/                    ← 原 .txt / .json / .png 结果
    ├── dissertation/               ← 原 LaTeX_Dissertation/
    ├── docs/                       ← 原 .md 文档
    └── venv/                       ← 建议不迁移（457 MB），改由 requirements.txt 重建
```

**必须随归档保留的"负面资产"**（它们是最有价值的部分）：

1. `Run_Statistical_Tests.py` 与 `Statistical_Testing_Framework.py` 的伪造代码 —— 作为**方法论教训**的活标本；
2. `Inter_2023_2024_Prediction_Report_20250826_172047.txt`（常数预测器那次运行）—— 作为**不可复现性**的证据；
3. `Generalization_Testing_Framework.py` —— 作为**空壳框架**的标本；
4. 本次审计发现的 15 项 P0/P1 缺陷清单 —— 作为新系统的**回归测试用例来源**。

**明确不建议迁移**：
- `venv/`（457.6 MB，17376 个文件）—— 用 `requirements.txt` 重建；
- `.idea/`、`.claude/`、`.ipynb_checkpoints`；
- `语音转写/`（与代码无关）。

---

## 10. 审计方法说明与可复现性

### 10.1 审计方式与交叉验证

本审计采用**双轨交叉验证**：主审计（我本人）逐行追踪代码并实机复现；另有两个独立子审计分别对**全部 54 个 `.py` 文件**与**全部 22 份文档**做穷尽盘点。两轨结论在**多数项上互相印证**，在 **4 个点上产生分歧**，我逐项实测后作出裁定（见 §10.3）。

### 10.2 审计脚本

本次审计的全部实测结论均可复现。审计脚本位于 `_audit\scripts\`：

| 脚本 | 验证内容 |
|---|---|
| `probe_data3.py` | 数据规模、完整度、标签平衡、位置样本量 |
| `probe_repro_2324.py` | 在 venv 中复现 2023-24 预测（0.7778，混淆矩阵 TP=5 FP=4 FN=2 TN=16） |
| `probe_optimizer.py` | 目标函数敏感性、"全部取上界"对照、差分进化最优解位置 |
| `probe_baselines.py` | 朴素单变量基线、均匀权重基线、多数类基线 |
| `probe_crossseason.py` | 样本内 vs 样本外对比、赛季错配修复效果（0.7778 → 0.8519） |
| `probe_json.py` | 多轮实验 JSON 自洽性、GA/RS 零方差问题 |
| `probe_metric_dict.py` | 101 个可用指标字典 |
| `inspect_headers.py` | FBref CSV 三层表头结构 |
| `build_clean_layer.py` | 干净数据层可行性验证（去重、过滤、候选池） |
| `probe_composite.py` | 核对论文 composite 分数的自洽性 |

### 10.3 审计过程中的自我修正记录（4 项）

为保证报告的可信度，如实记录我在审计中作出修正的 4 个判断。**4 项均为表述精度修正，无一改变总体结论。**

| # | 初稿表述 | 实测裁定 | 依据 |
|---|---|---|---|
| 1 | `Generalization_Testing_Framework.py` "调用了不存在的方法" | ❌ **表述错误 → 已修正**。`calculate_percentile_features()` / `calculate_departure_probability()` **真实存在**于 `Weight_Optimization_Framework.py:115/177`（第 1 代类式实现）。真正的问题是**版本错配**：项目实际运行的第 4 代引擎是无类的函数式模块。**更硬的证据**：`GeneralizationValidator` 全仓库零实例化，`__main__` 只调一个函数体仅 4 句 print 的 stub | 直接读取 `Weight_Optimization_Framework.py:108-147`；检索全仓库无实例化 |
| 2 | `calculate_base_risk_sigmoid()` 是"死代码，逻辑在别处重复实现" | ❌ **表述错误 → 已修正**。该函数在 `weight_optimization_core_updated.py:324` **被正常调用**。真正失效的是它的**输入**（合同百分位恒 0.5 → 年限恒 2.0）。结论（合同零贡献）不变，归因从"函数未用"改为"数据未接线" | 直接读取 `:319-327` 的调用点 |
| 3 | `Multi_Algorithm_Comparison_Experiment.py` 导入"5 个"不存在的模块 | ❌ **数字错误 → 已修正为 4 个**（`Enhanced_/PSO_/SA_/RS_Weight_Optimization_Experiment`）。第 5 个缺失模块 `Multi_Run_Experiment_Framework` 出现在 `test_fixed_framework.py:29` | `Test-Path` 逐一验证 6 个模块名 |
| 4 | 通用指标为"4 个" | ❌ **数字错误 → 已修正为 5 个**（含 `age`：minutes / age / CrdY / CrdR / Contract_expires） | 读取 `get_universal_metrics():123-130` |

### 10.4 经实测后**未采纳**的一项指控

子审计指出"论文 `results.tex:400` 的 composite=0.9315 与自身表格不自洽（代入应为 0.92774）"。我实测：按复合分公式代入**真实 JSON 的 5 轮均值**，PSO 得 **0.93049**；与论文的 0.9315 相差 **0.001**，属舍入/平均口径差异，**不构成实质矛盾**。

> **裁定：不采纳该指控。** 论文此处数字**基本可溯源**。（顺带确认：JSON 顶层 `global_best.score=0.9515` 是 PSO 单轮最佳，而 0.9305 是 5 轮均值，两者不冲突。）

### 10.5 原始项目的改动

**审计过程对原项目的改动：零。** 所有写操作均指向 `_audit\`。唯一的保护性措施是在探针脚本中把 `os.chdir` 重定向为空操作，以防 `2023_2024_Prediction.py` 内部硬编码的 `os.chdir(r"F:\Samuel\学习\final project")` 指向不存在的路径而报错。

---

*交付物 A 完成。继续阅读 `OLD_TO_NEW_MAPPING.md`、`GAP_ANALYSIS.md`、`MIGRATION_PLAN.md` 与 `FINAL_ASSESSMENT.md`。*
