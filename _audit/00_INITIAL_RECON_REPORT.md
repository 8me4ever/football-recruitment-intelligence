# 初次报告 — 原 Inter Milan 项目定位与结构勘查

> 对应主提示词 §22 要求的初次报告。
> 审计对象：`F:\Samuel\football recruitment\final project`
> 审计方式：全量文件清单 + 代码逐行追踪 + 数据实测（在项目自带 venv 中复现）
> 原则：只读取与分析，**未修改任何原项目文件**。审计产生的脚本与报告一律写入独立目录 `_audit\`。

---

## 0. 结论速览

工作区内**只有一个**项目，即 `final project\`（无多版本并存、无重复副本）。它是一个英国伯明翰大学 MSc 数据科学毕业论文项目，作者 Ziming Chen，题目：

> *Multi-layer Probability Fusion Algorithm Based on Relative Percentile Ranking with Weight Optimization: Application to Football Transfer Prediction*
> （基于相对百分位排名的多层次概率融合算法及其在足球转会预测中的应用）

项目的**真实性质**与标题存在明显落差，必须在动手改造前说清楚：

| 维度 | 标题/文档的自我描述 | 代码实测结论 |
|---|---|---|
| 方法 | "多层次概率融合算法"、"算法创新" | 一条**线性加权评分 + 固定偏移**的确定性公式 |
| 学习方式 | "supervised learning"、"machine learning" | **没有监督学习**，是启发式评分；优化器只调权重 |
| 算法名称 | "Genetic Algorithm" | 实际调用 `scipy.optimize.differential_evolution`（差分进化） |
| 训练样本 | 未强调 | **25 名球员**，按位置拆成 4 个模型（3–11 个样本/模型） |
| 评估 | "comprehensive validation"、"statistical significance" | 训练集=测试集；显著性检验的数据是 `np.random.normal()` **伪造**的 |
| 核心公式 | — | `离队概率 = 基础风险 + (1 − 表现分) × 风险系数` |

**一句话**：这是一个用元启发式算法在一份 25 行标签上调权的**启发式评分器**，被论文叙述包装成了算法创新成果。

---

## 1. 项目根目录

```
F:\Samuel\football recruitment\final project\      ← 唯一项目根
```

- 所有 `.py`、数据、论文、图表都平铺在根目录下，**没有 src/ 分层、没有包结构、没有测试目录**。
- 作者机器上的原始路径为 `F:\Samuel\学习\final project`（代码中硬编码），当前工作区的目录名已改为 `football recruitment`，因此**部分脚本的硬编码路径已失效**。
- 自带虚拟环境 `venv\`（457.6 MB，17376 个文件），依赖完整：pandas 2.3.0 / numpy 2.3.1 / scipy 1.16.1 / scikit-learn 1.7.1 / matplotlib / seaborn。系统 Python 未装 sklearn，**必须用 venv 运行**。

## 2. 重要目录

| 目录 | 内容 | 备注 |
|---|---|---|
| `data excel\2022-2023\` | 8 个 FBref 统计 CSV + 标签 + 合同 | 唯一真正被使用的数据源 |
| `data excel\2023-2024\` | 同上，用于留出集验证 | 位置统计文件被误用（见 §9） |
| `data\` | 8 个 FBref **原始 HTML** 页面 | 含 2024-25 赛季页面，但无对应 CSV |
| `Inter_Forwards_Analysis_Fixed\` | 4 名前锋的雷达图 PNG + 摘要 | 展示物 |
| `Inter_Midfielders_Analysis\` | 7 名中场的雷达图 PNG + 摘要 | 展示物 |
| `Inter_Midfielders_Analysis(原）\` | 同一批中场的旧版图 | **重复版本**，已被新版取代 |
| `Inter_Defenders_Analysis\` | 11 名后卫的雷达图 PNG + 摘要 | 展示物 |
| `LaTeX_Dissertation\` | 论文 8 章 `.tex` + `main.tex` | 成果主文档 |
| `语音转写\` | 语音转写文本 | 过程材料，与代码无关 |
| `.idea\` / `.claude\` | IDE 与工具配置 | 无关 |

## 3. 主要数据集

**规模（实测，与论文声明不符）**

| 赛季 | 数据行 | 唯一球员 | 球队 | 论文声明 |
|---|---|---|---|---|
| 2022-2023 | 603 | **577** | 20 | "535 名" ❌ |
| 2023-2024 | 616 | **590** | 20 | "547 名" ❌ |

**统计类别**：standard / goal / shooting / passing / possession / defensive / goalkeeper（**7 类**，非提示词猜测的 6 类；门将单独成表）。

**数据源**：FBref.com（论文 `data_collection.tex` 明确说明）。文件是 FBref 网页导出的多级表头 CSV（row0=组名、row1=指标名、row2=字段名、row3 起为数据）。

**标签（关键）**

| 赛季 | 国米球员数 | 离队 | 留队 | 离队率 | "全预测留队"基线准确率 |
|---|---|---|---|---|---|
| 2022-2023 | 25 | 12 | 13 | 0.480 | 0.5200 |
| 2023-2024 | 27 | 7 | 20 | 0.259 | **0.7407** |

**其他数据问题（实测）**

- **重复球员**：两个赛季各有 52 行重复球员（如 Alessandro Zanoli、Antonín Barák）——因赛季中转会，同一球员以不同球队出现两次。**当前代码未去重**，这些球员会被计入百分位参考池两次。
- **极低出场样本未过滤**：2 个赛季分别有 75 / 88 名球员出场 <90 分钟（最少仅 5 分钟，如 Lucien Agoumé）。论文与连续性文档都声称按 `min_minutes = 90` 过滤，**代码中从未实现该过滤**，导致这些噪声样本参与百分位计算。
- **数据完整度**：论文称各类别完整度 96.8%–98.5% 并列出具体缺失条数。实测核心指标列**零缺失**（100%）。
- **合同数据存在但从未被使用**：`Contract_2022_2023.csv`（26 行）与 `Contract_2023_2024.csv`（28 行）真实存在，采用 `-1` 表示租借球员、`0` 表示合同到期。但最终脚本调用 `calculate_enhanced_percentile_scores()` 时**从未传入** `contract_data` 参数，导致合同项恒为默认值 0.5、合同年限恒为 2.0 年。**合同变量对结果没有任何影响。**

## 4. 可能的入口点

根目录 `main.py` 是 PyCharm 自动生成的 `print_hi` 模板，**不是入口**。真正的可执行入口是：

| 入口 | 作用 | 状态 |
|---|---|---|
| `2023_2024_Prediction.py` | 加载 PSO 权重 → 预测 2023-24 → 输出指标 | 可运行（但依赖硬编码路径 + 赛季错配） |
| `Multi_Run_Experiment_Framework_Final.py` | 4 算法 × N 轮主实验 | 可运行（约 40+ 分钟/算法） |
| `Single_Run_Test_Framework_Final.py` | 单轮对比实验 | 可运行 |
| `Run_Statistical_Tests.py` | "统计检验" | 可运行，但**数据是伪造的** |
| `Statistical_Testing_Framework.py` | 同上 | 可运行，同样伪造数据 |
| `GA/PSO/SA/RS_Weight_Optimization_Experiment_Final.py` | 单算法优化 | 可运行 |
| `Generalization_Testing_Framework.py` | 泛化测试 | **不可运行**（与真实引擎版本错配：调用第 1 代类式 API，且 `GeneralizationValidator` 零实例化，入口只调一个 4 行 print 的 stub） |
| `Multi_Algorithm_Comparison_Experiment.py` | 早期对比实验 | **不可运行**（导入 4 个不存在的模块） |

## 5. 可能的建模脚本

**真正的核心引擎**：

```
weight_optimization_core_updated.py   (373 行, 2025-08-26)  ← 最终版核心
  ├── load_experimental_data_enhanced()      读标签 + 联赛数据 + 位置数据
  ├── get_universal_metrics()                5 个通用指标: minutes/age/CrdY/CrdR/Contract_expires
  ├── get_position_specific_metrics()        每个位置 10 个专属指标
  ├── calculate_percentile_score()           百分位转换（唯一被复用的算法）
  ├── calculate_enhanced_percentile_scores() 把球员值映射到 0–1 百分位
  ├── calculate_base_risk_sigmoid()          【活的，但输入失效】合同输入恒为 0.5 → 年限恒为 2.0
  ├── calculate_departure_probability_with_weights()  ← 评分主公式
  └── evaluate_weights_enhanced()            ← 目标函数（在全样本上评估）

weight_optimization_core.py  (旧版, 2025-08-13)  ← 上一代，仍被 *_Clean.py 引用
```

**四个元启发式算法（最终版 `*_Final.py`）**

| 文件 | 实际算法 | 说明 |
|---|---|---|
| `GA_Weight_Optimization_Experiment_Final.py` | `scipy.optimize.differential_evolution` | **不是**经典遗传算法 |
| `PSO_Weight_Optimization_Experiment_Final.py` | 手写 PSO（30 粒子 × 50 代） | 标准 PSO |
| `SA_Weight_Optimization_Experiment_Final.py` | 手写模拟退火 | — |
| `RS_Weight_Optimization_Experiment_Final.py` | 带"smart"策略的随机搜索（1500 次） | 60% 纯随机 + 40% 局部扰动 |

**四个算法的搜索边界与目标函数完全相同**（重量级指标 0.08–0.15，普通指标 0.05–0.12，`alpha` 1–4，`tau` 0.3–0.7，`risk_multiplier` 0.3–0.7）。换言之，它们**不是四个模型，而是同一个模型的四种求参方法**。

**主评分公式**（`calculate_departure_probability_with_weights`）：

```
表现分 (performance_score) = Σ(指标百分位 × 权重) / Σ(权重)
基础风险 (base_risk)       = sigmoid(α × (0.6×合同分 + 0.4×年龄分) − τ)   ← 实际因合同分恒为0.5而退化为年龄函数
离队概率 = base_risk + (1 − 表现分) × risk_multiplier      , 截断到 [0.05, 0.95]
```

## 6. 实验与结果文件夹

本项目**没有独立的结果目录**，所有产物平铺在根目录：

| 类别 | 文件 |
|---|---|
| 权重报告 | `Optimal_Weights_20250813_003733.txt`、`..._20250814_022008.txt`、`..._20250818_185855.txt` |
| 指标报告 | `Single_Run_ML_Metrics_20250826_134951.txt`、`Multi_Run_Average_Metrics_20250826_171631.txt` |
| 结构化结果 | `Multi_Run_Experiment_Results_20250826_171631.json`（119 KB，含 4 算法 × 5 轮完整数据） |
| 统计检验 | `Statistical_Test_Results_20250826_182039.txt` 及 3 个 `..._20250831_*.txt` |
| 预测输出 | `Player_Departure_Predictions_2023_2024_*.txt`、`Inter_2023_2024_Predictions_*.json`、`Inter_2023_2024_Prediction_Report_*.txt` |
| 图 | 42 个 PNG（多算法对比图、指标柱状图、球员雷达图） |
| 演示 | `Demonstration Slide——Ziming Chen.pptx`、`requirement.jpg`、`1756678204016.png` |

## 7. 报告与文档

**论文**（`LaTeX_Dissertation\`）：`main.tex` + 7 章 + 附录，README 自述约 40,000 词，作者 Ziming Chen，导师 Todd，2024。

**根目录 Markdown（11 份）**：`Algorithm_Selection_Rationale.md`(22 KB)、`Algorithm_Modification_Documentation.md`(12 KB)、`Final_Algorithmic_Contribution_Summary.md`(14 KB)、`Weight_Optimization_Research_Results.md`(10 KB)、`PPT_Content_Document.md`(15 KB)、`Project_Continuity_Documentation.md`(12 KB) 及 4 份中文技术说明。

**中文文档已经比较直白**：`增强版权重优化算法解释文档.md`(5 KB) 和 `算法原理与权重计算效果说明文档.md`(8 KB) 揭示后期（2025-08-19）团队已意识到早期文档不诚实，开始如实描述"这是一个加权评分模型，不是机器学习"。这是重要的**诚实化拐点**，新系统应继承这一态度。

## 8. 重复版本与代际

**没有**"多个版本的整个项目"，但**同一模块存在 3–4 代并存**：

| 代际 | 时间 | 代表文件 | 特征 |
|---|---|---|---|
| 第 1 代 | 08-08 ~ 08-10 | `Weight_Optimization_Framework.py`、`Weight_Optimization_Experiment.py` | 贝叶斯优化 / GA / 网格搜索；指标名用英文长名（`goals_weight`） |
| 第 2 代 | 08-13 | `weight_optimization_core.py` + `GA/PSO/SA/RS_Clean.py` | 改为 FBref 原始列名（`Gls_weight`）；引入 `alpha`/`tau` |
| 第 3 代 | 08-26 02:xx | `weight_optimization_core_updated.py` + `*_Updated.py` | 加入合同 sigmoid 支持（但未接线）、详细日志 |
| 第 4 代 | 08-26 12:2x | `*_Final.py`（8–10 KB，最小） | 精简版，去掉日志与合同逻辑，**实际产出论文结果** |

**同一算法最多有 4 个版本**：`GA_Clean.py`、`GA_Weight_Optimization_Experiment_Updated.py`、`GA_Weight_Optimization_Experiment_Final.py`，另有 08-08 的第 1 代实现。

**重复但内容不同的"中场分析"目录**：`Inter_Midfielders_Analysis\` 与 `Inter_Midfielders_Analysis(原）\`（后者文件名为无变音符的旧拼写），属同一批图的新旧两版。

**22 个一次性/草稿脚本**：`111.py`、`222.py`、`444.py`、`555.py`、`tax.py`、`test.py`、`basic_test.py`、`test_*.py`（6 个）、`simple_*.py`（3 个）等，属开发过程残留。

## 9. 即时风险与歧义（按严重度排序）

| # | 风险 | 证据 | 影响 |
|---|---|---|---|
| **R1** | **论文统计显著性来自伪造数据** | `Run_Statistical_Tests.py:20-45` 用 `np.random.normal(0.928, 0.008, 10)` 生成"实验结果"；`Statistical_Testing_Framework.create_sample_data_for_testing()`（第 72-105 行）同样伪造。而 `results.tex:52` 却写成 "multi-run experimental data (5 independent runs per algorithm)" | 论文第 6 章核心结论（p<0.001、Cohen's d=34.92）**不成立**。这是最严重的问题，必须在新系统中彻底纠正 |
| **R2** | **训练集即测试集，指标虚高** | `evaluate_weights_enhanced()` 在全部 25 个样本上评估；优化器直接最大化该分数 | 样本内 96%，样本外仅 77.78%，净增益从 +44.0pp 掉到 +3.7pp |
| **R3** | **样本量极小且过度参数化** | 25 个标签按位置拆成 4 个模型（后卫 11 / 中场 7 / 前锋 4 / **门将 3**），每模型 16 个权重参数 | 门将模型 3 个样本全为"离队"，多数类基线 100%；模型可完全记忆 |
| **R4** | **赛事数据赛季错配** | `2023_2024_Prediction.py:171-172` 调用的 `load_position_specific_data()` 只读 `2022-2023` 路径 | 用 2023-24 预测时混入 2022-23 的对手数据。**我实测修正后样本外准确率 0.7778 → 0.8519** |
| **R5** | **合同变量完全失效** | `calculate_enhanced_percentile_scores(player, league, pos_ds)` 未传 `contract_data` → 合同百分位恒为 0.5 → `contract_years` 恒为 2.0（注：`calculate_base_risk_sigmoid()` 本身在第 324 行被正常调用，失效的是它的输入） | 论文大篇幅论述"合同 sigmoid"和"α、τ 参数"，实际对结果零影响 |
| **R6** | **关键验证代码不可运行** | `Generalization_Testing_Framework.py` 与真实引擎**版本错配**：`:445,447` 调用的是第 1 代 `Weight_Optimization_Framework.py:115/177` 的类式方法，而实际运行的第 4 代引擎是无类的函数式模块；且 `GeneralizationValidator` 全仓库零实例化、`__main__` 只调一个 4 行 print 的 stub。`Multi_Algorithm_Comparison_Experiment.py:65-74` 导入 **4 个**不存在模块 | 论文声称的"泛化能力测试"与"交叉验证稳定性"从未真正跑通 |
| **R7** | **论文数字与磁盘真实输出不符** | 论文 `results.tex` 与真实报告一致（77.78%），但早期报告 `Inter_2023_2024_Prediction_Report_20250826_172047.txt` 显示 accuracy=0.7407、precision=recall=F1=**0.0000**、所有球员 `position=Unknown`、概率恒为 0.5 | 同一目标在不同运行中获得截然不同结果，说明流程**不稳定、结果不可复现** |
| **R8** | **论文数据描述与磁盘数据不符** | 球员数（535/547 vs 577/590）、合同分布（10 离队/15 留队 vs 12/13）、位置分布（门将2/后卫11/中场8/前锋4 vs 门将3/后卫11/中场7/前锋4）、完整度（96.8–98.5% vs 100%）全部对不上 | 论文第 4 章数据章节不可信 |
| **R9** | **文档引用了不存在的文件** | `Project_Continuity_Documentation.md` 引用 `Algorithm_Innovation_Framework_Analysis.md`、`V1_Percentile_Based_Model_Technical_Documentation.md`、`Project_Repositioning_and_Algorithm_Innovation_Strategy.md`、`Inter_V1_*.json` —— 全部 `Test-Path = False` | 项目历史链条断裂 |
| **R10** | **硬编码绝对路径** | `2023_2024_Prediction.py:15` `sys.path.append(r"F:\Samuel\学习\final project")`；`:163` `os.chdir(...)` | 换机即失效；当前工作区路径已变 |
| **R11** | **无去重、无低样本过滤、无数据校验** | 52 行重复球员进入参考池；75–88 名 <90 分钟球员参与百分位；`load_experimental_data_enhanced()` 有 `except: return None,None,None` 静默吞异常 | 数据层不可信，且错误被静默掩盖 |
| **R12** | **`_Updated` 与 `_Final` 两套结果并存且互相矛盾** | `_Updated` 系列引入合同 sigmoid 与更多指标；`_Final` 系列移除之。论文使用的是 `_Final` | 无法确定哪个是"正式"版本；后续若继续开发会读错文件 |

---

## 10. 与主提示词"背景描述"的核对结果

| 提示词猜测 | 实测 | 判定 |
|---|---|---|
| Inter Milan 阵容分析 | 有，25/27 人标签 | ✅ 存在 |
| Serie A 2022–2023 数据 | 有 | ✅ 存在 |
| "约 500+ 名 Serie A 球员" | 603 行 / 577 名唯一球员 | ✅ 基本吻合 |
| 国米约 25 人 | 25 人（22-23）、27 人（23-24） | ✅ 吻合 |
| 位置分组建模（前/中/后） | 有，4 组（含门将） | ✅ 存在 |
| 门将建模"可能有限" | 有，但仅 3 个样本 | ✅ 存在且确实不可靠 |
| 按位置百分位排名 | 有，`stats.percentileofscore` | ✅ 存在 |
| performance score | 有（加权平均） | ✅ 存在 |
| departure probability | 有 | ✅ 存在 |
| base risk | 有，sigmoid 定义但实际退化为年龄函数 | ⚠️ 部分失效 |
| age | 有 | ✅ |
| contract length | 有数据，但**未被使用** | ❌ 形同虚设 |
| sigmoid 风险逻辑 | 有定义，实际输入缺一半 | ⚠️ 部分失效 |
| GA / PSO / SA / Random Search | 四者都有，但 GA 实为差分进化 | ⚠️ 名不符实 |
| 重复实验、多轮平均 | 有（N=5 轮，论文称 10 轮） | ⚠️ 存在但轮数陈述不一致 |
| JSON 实验结果 | 有 | ✅ |
| 统计检验 | 有代码，但数据伪造 | ❌ 不可信 |
| 模型对比可视化 | 有（42 张 PNG） | ✅ |
| SHAP 或特征重要性 | **完全没有**（无 shap 依赖、无相关代码） | ❌ 不存在 |
| 报告/论文材料 | 有，8 章 LaTeX | ✅ 存在 |
| notebook | **完全没有**（0 个 `.ipynb`） | ❌ 不存在 |
| Python 脚本 | 54 个 | ✅ |
| CSV / Excel 数据集 | 23 个 CSV，**0 个 Excel** | ⚠️ 无 Excel |
| 生成图 | 42 个 PNG | ✅ |
| 结果文件夹 | 无独立目录，全部平铺根目录 | ⚠️ 缺失 |
| 六类指标（standard/goal/shooting/passing/possession/defensive） | **7 类**，另有 goalkeeper | ⚠️ 多一类 |
| 前锋特征集（Goals/xG/SoT/…/Age） | 实测前锋用 Gls/Ast/xG/SoT/G_per_Sh/Sh_per90/SCA/GCA/Att_Pen/TakeOn_Succ | ⚠️ 大体吻合，细节不同 |

---

## 11. 下一步

初次勘查已完成，**未做任何修改**。接下来按主提示词继续产出：

- `EXISTING_PROJECT_AUDIT.md`（交付物 A）
- `OLD_TO_NEW_MAPPING.md`（交付物 B）
- `GAP_ANALYSIS.md`（交付物 C）
- `MIGRATION_PLAN.md`（交付物 D）
- 8 个必答问题的最终评估（§18）

> 所有新文档写入 `F:\Samuel\football recruitment\_audit\`，原项目文件保持只读不动。
