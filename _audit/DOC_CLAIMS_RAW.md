# 文档声明核查原始报告（DOC_CLAIMS_RAW）

**审计对象**：`F:\Samuel\football recruitment\final project`（只读）
**审计范围**：`LaTeX_Dissertation\` 下 9 份 `.tex` + 1 份 `README.md`；根目录 11 份 `.md`；7 份文本类结果文件
**审计方式**：仅读取与 grep，未运行任何脚本，未修改任何原有文件
**审计日期**：本轮次
**判据来源**：磁盘上的真实数据文件（`data excel\`）、真实代码（`.py`）、真实结果输出（`.txt`/`.json`），以及委托方已核实并精确复现的事实

**判定标签定义**
| 标签 | 含义 |
|---|---|
| 「与代码/数据一致」 | 声明能在磁盘文件或代码中找到确切佐证 |
| 「夸大或失实」 | 声明能在磁盘上找到反证，或被明显放大 |
| 「文档内部自相矛盾」 | 同一文档或跨文档对同一事实给出互相冲突的说法 |
| 「无法验证」 | 磁盘上既无支持证据也无反证，需人工复核 |

---

## 一、总体结论（要点列表）

1. **论文数字与磁盘数据系统性不符，且方向一致地"好看化"。** `data_collection.tex` 第 13、23–24 行的联赛规模 535/547 与磁盘实测 **603/616 条记录**（`ITA_SerieA_player_*_stats_2022_2023.csv` 共 606 行 = 3 行表头 + 603 条；2023-2024 共 619 行 = 3 + 616）相差 68–69 人，无任何代码路径会筛掉这些球员（最终管线 `weight_optimization_core_updated.py` 全文无 `Min > 90` 之类的行筛）。

2. **国米标签数据的核心声明整段是错的。** `data_collection.tex` 第 76 行称"10 名球员离队、15 名留队"；磁盘 `Inter_Players_Departure_Labels.csv` 实测 **25 名球员中 12 人离队（1）、13 人留队（0）**。表 `tab:transfer_outcomes`（第 78–92 行）的 10/15 与同文档第 56 行"25 名球员"自洽，但与真实标签直接冲突。

3. **位置分布声明错误。** `data_collection.tex` 第 56 行与 `tab:inter_squad`（58–74 行）写"门将 2、后卫 11、中场 8、前锋 4"；真实位置口径为 **门将 3、后卫 11、中场 7、前锋 4**（总数同为 25，因此该表"总数自洽"掩盖了分项错误）。

4. **数据完整度整节（`data_collection.tex` 第 96–116 行）是编造的。** 声称 96.8%–98.5% 完整度、8/15/17/10/13/9 条缺失；实际 6 个统计类别在核心指标列上 **完全没有缺失值**。此外第 98 行把"缺失与出场时间少于 90 分钟的球员相关"当成结论，而该筛选在最终管线中并不存在。

5. **`results.tex` 中两张统计检验表整表来自伪造数据。** `tab:one_sample_testing` 与 `tab:paired_testing` 的数字与磁盘 `Statistical_Test_Results_20250826_182039.txt` / `..._20250831_231510.txt` 的 t 值、Cohen's d **逐位吻合**（如 PSO Accuracy t=110.429、d=34.921 → 论文写作 110.429 / 34.92），但这些输出的唯一来源是 `Run_Statistical_Tests.py` 第 20–45 行的 `np.random.normal(...)` 以及 `Statistical_Testing_Framework.py` 的 `create_sample_data_for_testing()`（第 72–105 行）。论文 `results.tex` 第 52 行却写成 "multi-run experimental data (5 independent runs per algorithm)"，`discussion_conclusion.tex` 第 7 行重复写 "5-run multi-run experiments"。**这是把合成数据冒充真实实验结果。**

6. **论文所称 "Genetic Algorithm" 实际是差分进化。** `GA_Weight_Optimization_Experiment_Final.py` 第 7 行 `from scipy.optimize import differential_evolution`、第 76–80 行 `maxiter=20, popsize=10`，第 87 行却把结果标为 `'method': 'Genetic Algorithm'`。`analysis_requirements.tex` 第 62–68 行同时描述经典 GA 的算术交叉/高斯变异公式**和**差分进化供体向量公式，属自相矛盾；`implementation.tex` 第 78 行的"mutation factor F=0.8 / crossover CR=0.7 / population 10 / 20 generations"以及"差分进化准则 5–10 倍维度"的表述与代码中的 `maxiter/popsize` 语义不符（DE 中 `popsize=10` 指每个体 10 个向量，非"种群 10 个个体"）。

7. **所谓 "Multi-layer Probability Fusion Algorithm" 在代码里就是一次线性加权平均 + 一次 sigmoid + 一次线性组合。** `weight_optimization_core_updated.py` 第 297–327 行：先按权重求加权平均 `(universal_score + position_score)/(universal_weight + position_weight)`，再 `base_risk = sigmoid(alpha*(combined-tau))`，最后 `departure_prob = base_risk + (1 - performance_score)*risk_multiplier` 并 clip。没有任何"多层概率融合"结构（无贝叶斯融合、无概率乘法、无集成投票）。`算法原理与权重计算效果说明文档.md` 第 106 行的公式 `离队概率 = base_risk + (加权综合百分位分数) × risk_multiplier` 更是把 `(1 - performance_score)` 漏写成没有 `1-`，与代码和论文 `design.tex` 第 324 行都不一致。

8. **四个算法的"对比实验"在优化维度上不成立。** 四个 `*_Weight_Optimization_Experiment_Final.py` 的 `get_bounds()` 边界**逐字相同**（GA 35/47/49 行，PSO 34/46/48 行，SA 35/47/49 行，RS 35/47/49 行，均为重要指标 `(0.08, 0.15)`、一般指标 `(0.05, 0.12)`、`alpha (1.0,4.0)`、`tau (0.3,0.7)`、`risk_multiplier (0.3,0.7)`），目标函数 `evaluate_weights_enhanced` / composite 公式也完全相同（`Multi_Run_Experiment_Framework_Final.py` 第 48–53 行等）。因此"多算法互补搜索"的叙事缺乏机制层面的差异，唯一区别只有搜索过程本身。

9. **合同项恒为默认值 0.5，论文的合同风险叙述整体失效。** `calculate_enhanced_percentile_scores(..., contract_data=None)`（`weight_optimization_core_updated.py` 第 196 行）的所有 6 处调用点（`GA_..._Final.py:122`、`PSO_..._Final.py:142`、`SA_..._Final.py:167`、`RS_..._Final.py:154`、`2023_2024_Prediction.py:186`、`weight_optimization_core_updated.py:335`）**都没有传第 4 个参数**，于是代码走到第 236–237 行 `scores[metric_name] = 0.5`。`data excel\2022-2023\Contract_2022_2023.csv`（25 行）与 `data excel\2023-2024\Contract_2023_2024.csv` 在最终脚本中从未被读入。进一步地，第 319–320 行 `contract_years = max(0,(1-0.5)*4) = 2` 恒定，代入第 280–287 行得 `year_score = (3-2)/3 = 0.3333` 恒定，`base_risk` 实际只随年龄变化。而 `design.tex` 第 275–307 行、`discussion_conclusion.tex`、`Algorithm_Modification_Documentation.md` 第 92–136 行的"复杂合同算法/租借球员特殊处理"全部是纸面描述。

10. **2023-2024 预测存在赛季错配。** `2023_2024_Prediction.py` 第 171–172 行 `from weight_optimization_core_updated import load_position_specific_data`，而该函数（`weight_optimization_core_updated.py` 第 64–121 行）硬编码读取 `data excel/2022-2023/...` 的 6 个位置统计文件（goal/shooting/passing/possession/defensive/goalkeeper），却用于 2023-2024 的百分位计算（第 186–187 行）。此外这些文件在读取失败时全部 `except: pass`（第 80、99、109、119 行），静默降级。

11. **论文中的留出集结果 0.7778/0.6459 在磁盘上无来源，且高于平凡基线。** 磁盘唯一的 2023-2024 预测产物 `Inter_2023_2024_Prediction_Report_20250826_172047.txt` 显示 **Accuracy=0.7407、Precision=0.0000、Recall=0.0000、F1=0.0000、PR-AUC=0.2593、Confusion 全为"Stayed"、Correct 20/27**；对应 `results.tex` `tab:prediction_metrics_2023_2024`（第 287–309 行）的 0.7778/0.5556/0.7143/0.6250/0.6459/0.4706/0.7571/0.4781/0.2083 **没有任何磁盘文件可溯源**。委托方在 venv 中精确复现出的 0.7778（TP=5 FP=4 FN=2 TN=16，21/27）对应的是**修正后**重跑的结果，而不是磁盘上任何现存脚本的原始输出；同时委托方核实"全预测留队"平凡基线 = 0.7407（20/27），故 **0.7778 相对平凡基线仅 +3.7 个百分点，且 Precision 仅 0.5556**，不支持论文"strong predictive performance"的定性。

12. **过度宣称贯穿始终。** 详见第五节。最突出的三条：`README.md` 第 115 行"92.0% prediction accuracy (35.3% improvement over baseline)"；`results.tex` 第 403 行"significant advancement"；`discussion_conclusion.tex` 第 7 行"exceptional performance"。均无磁盘证据支持，其中 35.3% 的基线不可溯源。

13. **早期文档与最终论文是两套完全不同的研究，却都在声称"已完成验证"。** `Final_Algorithmic_Contribution_Summary.md`、`Weight_Optimization_Research_Results.md`、`权重优化算法实验原理详解.md` 三份文档描述的是**贝叶斯优化 + 遗传算法 + 网格搜索**三算法框架，并给出 72.4%→87.9%（+21.5%）、t=4.287、p=0.003、Cohen's d=1.24、W=48、p=0.008、跨赛季 84.2%、跨联赛英超 78.6%/西甲 81.2% 等具体数字；而最终论文用的是 **GA/PSO/SA/RS** 四算法，数字完全不同。与此同时 `Project_Continuity_Documentation.md` 第 250–256 行明说"实验验证状态：待执行"、第 302–304 行"项目阶段：算法框架完成，实验验证待执行"。**同一项目里，三份文档报告"已完成的显著结果"，一份文档说"实验还没跑"，最终论文又用了第三套数字。**

14. **`Project_Continuity_Documentation.md` 引用 5 个磁盘上不存在的文件。** 第 93–95 行 `Algorithm_Innovation_Framework_Analysis.md`、`V1_Percentile_Based_Model_Technical_Documentation.md`、`Project_Repositioning_and_Algorithm_Innovation_Strategy.md`（glob 全库搜索无结果）；第 102–103 行 `Inter_V1_Enhanced_Complete_Final.json`、`Inter_V1_Percentile_Based_Predictions.json`（全库仅 2 个业务 json：`Multi_Run_Experiment_Results_20250826_171631.json`、`Inter_2023_2024_Predictions_20250826_171723.json`）。

15. **`main.tex` 在当前磁盘状态下无法编译。** 第 8 行 `\addbibresource{references.bib}`（全库无 `.bib`）；第 52–54 行 `\include{Preamble/FrontPage}`、`Preamble/Abstract`、`Preamble/Acknowledge`；第 66–84 行 `\include{Chapter 1/introduction}` … `Chapter 7/discussion_conclusion` —— 这些目录与文件均不存在（实际文件平铺在 `LaTeX_Dissertation\` 根下）。同时 `appendix.tex` 从未被 `main.tex` 引用，属孤儿文件。

16. **`biblatex` 与 `natbib` 同时加载**（`main.tex` 第 3–7 行 + 第 15 行），文档类为 `article` 且未使用 `\input` 组织摘要等前置部分。README 声称的"参考文献"流程（第 44–50 行 `bibtex main`）与 `backend=biber` 冲突。

17. **README 的章节字数与总量严重虚报。** README 第 61–100 行声称各章 5,000–6,500 词、第 141 行声称"approximately 40,000 words"；实测（空白分隔计词）introduction=930、analysis_requirements=1781、design=2186、data_collection=1062、implementation=1442、results=2098、discussion_conclusion=720、appendix=530，正文合计 **10,749 词**，约为声称量的 27%。

18. **`results.tex` 四张"最优权重"表并非全部来自 PSO，且有一行直接串了算法。** `tab:sigmoid_parameters`（第 30–46 行）中 SA 行 α=1.54/τ=0.52/rm=0.49 与可溯源的 **Goalkeeper-PSO** 值一致（`Multi_Run_Average_Metrics_20250826_171631.txt` 第 96–98 行 α=1.541406/τ=0.519183/rm=0.492299），RS 行 α=1.97/τ=0.70/rm=0.43 与 **Defender-PSO** 值一致（同文件第 75–77 行 α=1.969604/τ=0.700000/rm=0.433024）。即表中名为 SA / RS 的参数实际上是 PSO 在门将/后卫位置上的参数。相应地 `tab:defender_weights` 与 `tab:goalkeeper_weights` 标题均写 "(PSO Algorithm)"（第 219、252 行）却是不同"算法"的名目，而正文第 48 行又说 PSO 最优配置是 α=4.00/τ=0.61 —— 同一"PSO 最优"在论文内被赋予 3 套互斥取值。

19. **`模型对比.txt` 与 `results.tex` 是两套互斥的实验结果。** `模型对比.txt` 第 5–13 行：GA/PSO/SA/RS 准确率 0.920/0.920/0.684/0.920，PR-AUC 0.953/0.960/0.830/0.954，Kappa 0.841/0.841/0.377/0.841，平均用时全部 0.0 秒，综合评分 PSO 0.894、RS 0.892、GA 0.892、SA 0.629。`results.tex` 第 18–21 行则是 0.9200/0.9280/0.7280/0.9200、PR-AUC 0.9646/0.9648/0.7978/0.9616、Kappa 0.8397/0.8557/0.4534/0.8395、用时 1444.7/335.3/217.4/313.1。两组数据不可能同源。

20. **`Single_Run_ML_Metrics_20250826_134951.txt` 暴露了"运行无随机性"问题。** 第 9–12 行 GA/PSO/RS 三项指标**完全相同**（Accuracy 0.9200、PR-AUC 0.9646、Bal-Acc 0.9199、Cohen-K 0.8397、MCC 0.8397），说明在 25 条样本、按位置分 4 组的小样本下，不同元启发式收敛到同一解、或实现实际退化为同一路径。这直接削弱"四算法对比"的统计意义。

21. **脚注级但不可忽略的事实错误**：`data_collection.tex` 第 31、35–50 行称"seven comprehensive statistical categories"并列出 7 类，而 `implementation.tex` 第 11、13–29 行、`design.tex` 第 22 行、`introduction.tex` 第 61 行均称 **six**；`增强版权重优化算法解释文档.md` 第 122 行又称"整合 8 个专业数据集"。

---

## 二、逐文档核查

### 2.1 `LaTeX_Dissertation\main.tex`（88 行）

**核心声明**
| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 8 行 `\addbibresource{references.bib}` | **夸大或失实**：全库无 `.bib` 文件 |
| 2 | 第 52–54 行 include `Preamble/FrontPage`、`Preamble/Abstract`、`Preamble/Acknowledge` | **夸大或失实**：`Preamble\` 目录不存在 |
| 3 | 第 66–84 行 include `Chapter 1/introduction` … `Chapter 7/discussion_conclusion` | **夸大或失实**：`Chapter *\` 目录不存在；实际 `*.tex` 平铺在 `LaTeX_Dissertation\` 下 |
| 4 | 第 43 行 PDF 标题 "Multi-layer Probability Fusion Algorithm Based on Relative Percentile Ranking" | **夸大或失实**（算法命名层面）：代码实为线性加权 + sigmoid，见总体结论 #7 |
| 5 | 第 3–7 行 + 第 15 行同时加载 biblatex(backend=biber) 与 natbib | **文档内部自相矛盾**：两套引用宏包冲突 |

### 2.2 `LaTeX_Dissertation\introduction.tex`（69 行）

**核心声明**
| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 15 行 核心创新是 "Multi-layer Probability Fusion Algorithm Based on Relative Percentile Ranking" | **夸大或失实**：见总体结论 #7；百分位用 `scipy.stats.percentileofscore`（`weight_optimization_core_updated.py:184`），属常规特征工程 |
| 2 | 第 18 行 "Percentile-Based Feature Engineering… eliminating systematic biases" | **无法验证**：论文未做"百分位 vs 绝对数值"的消融实验；`Project_Continuity_Documentation.md` 第 112 行反而明确"不需要相对百分位算法 vs 传统算法的对比证明" |
| 3 | 第 20 行 "four complementary optimisation algorithms—GA, SA, PSO, RS" | **与代码/数据一致**（算法数量与名称）；但 "complementary" 见总体结论 #8 的反证 |
| 4 | 第 40 行 "Demonstrate statistically significant improvements… through comprehensive evaluation metrics" | **夸大或失实**：唯一"显著"证据来自合成数据（见 2.6） |
| 5 | 第 61 行 "535+ players across two seasons" | **夸大或失实**：实测 603/616 条记录（少报 68/69） |
| 6 | 第 61 行 "six statistical categories" | **与代码/数据一致**（代码确读 6 类）；但与 `data_collection.tex` 的 "seven" 冲突（跨文档矛盾） |
| 7 | 第 63 行 "unified 16-parameter optimisation space" | **与代码/数据一致**（16 维可回溯，如 Forward 13 权重 + 3 超参） |
| 8 | 第 65 行 "achieving 77.8\% accuracy" | **夸大或失实**：磁盘产物为 0.7407 且全预测留队；0.7778 相对平凡基线仅 +3.7pp |
| 9 | 第 67 行 "92.8\% optimisation accuracy" | **与代码/数据可溯源但语义夸大**：数值来自 `Multi_Run_Average_Metrics_20250826_171631.txt:11`，但那是 **25 名球员训练集内**的拟合准确率，非泛化精度 |
| 10 | 第 9 行 "Inter's transfer decisions… offer ground truth data" | **与代码/数据一致**（`Inter_Players_Departure_Labels.csv`、`Inter_departured_2023_2024.csv`） |

### 2.3 `LaTeX_Dissertation\analysis_requirements.tex`（206 行）

**核心声明**
| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 27 行 "The application of Bayesian optimisation to sports analytics parameter tuning represents a novel contribution of this research" | **夸大或失实**：贝叶斯优化从未进入最终研究（最终为 GA/PSO/SA/RS）；且 `venv\Lib\site-packages` 无 `skopt`，`Weight_Optimization_Framework.py:260` 会回退到随机搜索。"novel contribution" 无实体 |
| 2 | 第 62 行 "For transfer prediction weight optimization, the GA utilizes differential evolution as the underlying mechanism" | **与代码/数据一致**（`GA_..._Final.py:7,76`）。但与第 34–60 行对经典 GA（selection/crossover/Gaussian mutation）的详细描述**文档内部自相矛盾** |
| 3 | 第 36–40 行 轮盘赌选择概率公式 `P_i = f_i/Σf_j` | **夸大或失实**：`differential_evolution` 不使用轮盘赌选择，代码中无任何 selection 实现 |
| 4 | 第 44–50 行 算术交叉公式 | **夸大或失实**：DE 使用指数/二项式交叉，非算术交叉；代码中无自定义 crossover |
| 5 | 第 54–60 行 高斯变异公式 | **夸大或失实**：DE 变异为差分向量，非高斯扰动 |
| 6 | 第 105–111 行 惯性权重线性递减 `w_max=0.9 → w_min=0.4` | **夸大或失实**：`PSO_..._Final.py:73` 为固定 `w = 0.7`，无递减 |
| 7 | 第 146–158 行 对数退火 `T_k = T_0/log(1+k)` 与 `N_eq(T_k)=⌈C·log T_k⌉` | **夸大或失实**：`SA_..._Final.py:81–90` 提供 4 种调度但默认只用 `'exponential'`（第 83–84 行 `alpha=0.95`，`T_0*(0.95**iteration)`）；无 equilibrium 循环 `N_eq` |
| 8 | 第 203 行 `P(‖x*−x_opt‖≤ε) = 1−(1−p)^n` "demonstrates exponential convergence" | **夸大或失实**：该式是几何分布累积概率，不是"指数收敛"；且 `RS_..._Final.py:74` 实际用了 60% 探索 + 40% 局部搜索的启发式，并非纯均匀采样，"Random Search" 名不副实 |
| 9 | 第 11、19、21、25 行 引用 `\citep{vanarem2025...}`、`\citet{bunker2019machine}` 等 | **无法验证**：`references.bib` 不存在，全部引用无法解析 |

### 2.4 `LaTeX_Dissertation\design.tex`（360 行）

**核心声明**
| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 38 行 架构图 `Probability Fusion: σ(C) + f(W*, P)` | **夸大或失实**：与代码一致的形式（`weight_optimization_core_updated.py:326`），但称之为"多层概率融合（Probability Fusion）"属命名夸大 |
| 2 | 第 76–91 行 `tab:universal_metrics` 标题 "Five universal metrics"，表内仅列 3 项（Minutes/Yellow/Red），第 93 行注 "Age and Contract expiry date are excluded from performance scoring" | **文档内部自相矛盾**：标题说 5 项，表只有 3 项，注又说 age/contract 被排除 → 应为 3 项 |
| 3 | 第 93 行 "Age and Contract expiry date… contribute to the base departure risk calculation through the sigmoid function" | **夸大或失实**：合同从未传入（见总体结论 #9），合同项恒 0.5；实际只有年龄与固定的 `year_score=0.3333` 生效 |
| 4 | 第 149、175 行 "through ten specialised metrics"（Defender / Goalkeeper） | **与代码/数据一致**（`weight_optimization_core_updated.py` 位置指标确为 10 项，见 `Multi_Run_Average_Metrics_...txt:82–92,103–113`） |
| 5 | 第 256–265 行 百分位定义 `P_{i,j} = rank(x_{i,j}, R_j)/|R_j|`，反向指标取 `1 − rank/|R_j|` | **与代码/数据一致**（`weight_optimization_core_updated.py:184–194` + `calculate_percentile_score`） |
| 6 | 第 284 行 `s = 0.6·year_score + 0.4·age_score` | **与代码/数据一致**（`weight_optimization_core_updated.py:285`） |
| 7 | 第 290 行 `year_score = (L_0 − years_left)/L_0`，`L_0=3` | **与代码/数据一致**（第 280–281 行 `contract_length=3`） |
| 8 | 第 298 行 `age_score = max(0, 1 − |age−30|/6)` | **与代码/数据一致**（第 282–284 行 `optimal_age=30.0, age_width=6.0`） |
| 9 | 第 303–304 行 `α∈[1.0,4.0]`、`τ∈[0.3,0.7]`、第 331 行 `risk_multiplier∈[0.3,0.7]` | **与代码/数据一致**（四个 Final 脚本的 `get_bounds()` 完全相同，如 `PSO_..._Final.py:50–52`） |
| 10 | 第 307 行 "The final output is bounded to [0.1, 0.3]" | **与代码/数据一致**（`weight_optimization_core_updated.py:287` `np.clip(base_risk, 0.1, 0.3)`） |
| 11 | 第 314 行 `performance_score` **带归一化分母** `Σw_u + Σw_p` | **与代码/数据一致**（第 315–316 行确有除法）。注意这与 `算法原理与权重计算效果说明文档.md:76` 及 `增强版权重优化算法解释文档.md:76` 的写法一致，但 `Final_Algorithmic_Contribution_Summary.md:87–88` 与 `Weight_Optimization_Research_Results.md` 的示例代码**没有归一化除法** → 跨文档不一致 |
| 12 | 第 341 行 composite = 0.4·PR-AUC + 0.3·F1 + 0.2·Bal-Acc + 0.1·(1−Brier) | **与代码/数据一致**（`Multi_Run_Experiment_Framework_Final.py:48–53`、`2023_2024_Prediction.py:229`） |
| 13 | 第 358 行 "Position-critical metrics… utilize bounds [0.08, 0.15]… Supporting metrics employ bounds [0.05, 0.12]" | **与代码/数据一致**（`*_Final.py` 的 `get_bounds`） |
| 14 | 第 358 行 同句声称"Universal metrics receive bounds of [0.08, 0.15] ... based on domain expertise" | **夸大或失实**：`Algorithm_Modification_Documentation.md:234` 声称 `Contract_expires_weight: (0.05, 0.12)`（"合同权重较低"），而代码中 contract 不是优化维度、且四个脚本把 `CrdY/CrdR` 与位置指标按同一规则分档 —— "domain expertise 决定边界"缺乏实现层证据 |
| 15 | 第 356 行 "Through a review of the literature, this study ultimately selected four algorithms" | **与代码/数据一致**（四个 Final 脚本存在） |

### 2.5 `LaTeX_Dissertation\data_collection.tex`（143 行）— **问题最集中**

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 13、23 行 "535 players… 2022-2023" | **夸大或失实**：实测 603 条记录（`ITA_SerieA_player_standard_stats_2022_2023.csv` 共 606 行 = 3 表头 + 603 数据行） |
| 2 | 第 13、24 行 "547 players… 2023-2024" | **夸大或失实**：实测 616 条记录（619 行 = 3 + 616） |
| 3 | 第 31 行 "seven comprehensive statistical categories" | **夸大或失实**：磁盘为 6 类数据（standard/shooting/goal/passing/possession/defensive/goalkeeper 中的 6 类，`load_experimental_data_enhanced` 与 `load_position_specific_data` 读 6 类）；论文其他章节均写 six |
| 4 | 第 56 行 "2 goalkeepers, 11 defenders, 8 midfielders, and 4 forwards" | **夸大或失实**：实测 门将 3 / 后卫 11 / 中场 7 / 前锋 4 |
| 5 | 第 66–69 行 `tab:inter_squad` 门将 2、后卫 11、中场 8、前锋 4 | **夸大或失实**：同上 |
| 6 | 第 76 行 "10 players departed… 15 players remained" | **夸大或失实**：`Inter_Players_Departure_Labels.csv` 实测 12 离队 / 13 留队 |
| 7 | 第 86–87 行 `tab:transfer_outcomes` Departed 10 / Remained 15 | **夸大或失实**：同上 |
| 8 | 第 96 行 "completeness rates ranging from 96.8\% to 98.5\%" | **夸大或失实**：核心指标列无缺失（100%） |
| 9 | 第 98 行 "Standard statistics achieved 98.5\% completeness with only 8 missing records" | **夸大或失实**：`Inter_Players_Departure_Labels.csv` 与 6 类统计文件在 `Gls/Ast/CrdY/CrdR/Min` 等核心列上无空值 |
| 10 | 第 98 行 "Shooting 96.8%、Passing 98.1%、Possession 97.5%、Defensive 98.3%" | **夸大或失实**：同上 |
| 11 | 第 108–113 行 `tab:data_completeness` 的 8/15/17/10/13/9 条缺失 | **夸大或失实**：无任何磁盘依据 |
| 12 | 第 98 行 "Missing data patterns… associated with players having less than 90 total minutes" | **夸大或失实**：无缺失可解释；且最终管线无 90 分钟筛选（仅早期 `*_Clean.py` / `Weight_Optimization_Experiment.py` 有 `df['Min'] > 90`） |
| 13 | 第 118 行 "Players with insufficient playing time were subsequently excluded" | **夸大或失实**：最终管线 `weight_optimization_core_updated.py`、四个 `*_Final.py`、`2023_2024_Prediction.py` 全文无此筛选 |
| 14 | 第 126 行 "Z-score… identified 12 players… IQR flagged 18… domain knowledge 5" | **无法验证**：磁盘无离群检测脚本与输出；`tab:outliers`（128–141 行）三个数字无来源 |
| 15 | 第 122–124 行 范围校验 / 跨类别一致性校验 / 位置特定校验 | **夸大或失实**：`weight_optimization_core_updated.py` 中不存在这些校验逻辑；`implementation.tex:33` 也只是重复声明 |
| 16 | 第 9 行 "Transfer outcome data… manually compiled and verified through multiple independent sources" | **无法验证**：仅有一份 CSV，无来源记录 |
| 17 | 第 5 行 数据源 FBref.com | **与代码/数据一致**（列名结构与 FBref 导出格式吻合，含 `league,season,team,player,nation,pos,age,born,90s`） |

### 2.6 `LaTeX_Dissertation\implementation.tex`（145 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 3 行 "Python 3.9+" | **与代码/数据一致**（venv 为 cpython-311） |
| 2 | 第 11、13–29 行 "six different statistical categories" | **与代码/数据一致**；与 `data_collection.tex:31` 的 seven 冲突 |
| 3 | 第 33 行 "comprehensive data validation… range validation… outlier detection" | **夸大或失实**：代码中不存在 |
| 4 | 第 41 行 "clips extreme values to [0.01, 0.99]" | **夸大或失实**：`calculate_percentile_score`（`weight_optimization_core_updated.py:184–194`）实为 `max(0, min(1, percentile))`，即 [0,1] 而非 [0.01,0.99] |
| 5 | 第 41 行 "position-specific references that calculate percentiles within same-position player pools" | **与代码/数据一致**（第 205–212 行按 `pos` 含 FW/MF/DF/GK 过滤），但**存在"同位置"跨位置重叠问题**：FBref 的 `pos` 常为 `"FW,MF"` 多值，`str.contains('FW')` 与 `str.contains('MF')` 会同时命中，未做互斥处理 |
| 6 | 第 70 行 "four distinct meta-heuristic algorithms" | **夸大或失实**：`differential_evolution` 是 scipy 现成实现，四者共享同一目标函数与同一边界（见总体结论 #8） |
| 7 | 第 74 行 "reduction from the original 17-parameter space" | **无法验证**：磁盘上未见 17 参数版本的最终脚本；`Algorithm_Modification_Documentation.md:228–243` 列举的边界字典含 `age_weight`、`Contract_expires_weight`、`base_risk` 等，与 16 参数描述不一致 |
| 8 | 第 78 行 "population size of 10 individuals… differential evolution guidelines of 5-10 times the problem dimension" | **夸大或失实**：`GA_..._Final.py:80` `popsize=10` 在 scipy 中指"每个求解向量对应 10 个种群成员"，总种群 = 10×16=160，不是"10 个个体"；论文对 DE 参数语义理解错误 |
| 9 | 第 78 行 "Maximum generations of 20 reflects empirical testing showing convergence typically occurs within 15-18 generations" | **无法验证**：无收敛曲线/日志留档 |
| 10 | 第 84 行 "inertia weight w=0.7" | **与代码/数据一致**（`PSO_..._Final.py:73`） |
| 11 | 第 86 行 "c1 + c2 ≈ 4.0" 但代码 c1=c2=1.5（和 = 3.0） | **文档内部自相矛盾**：第 86 行先说 "both set to 1.5"，紧接着引用 "c1 + c2 ≈ 4.0" 的理论最优；1.5+1.5=3.0≠4.0 |
| 12 | 第 90 行 "initial temperature of 100 ensures approximately 95\% acceptance probability" | **无法验证**：无接受率日志；`SA_..._Final.py` 虽有接受率监控但未落盘 |
| 13 | 第 92 行 "cooling from 100 to approximately 0.01" | **与代码/数据一致**（`SA_..._Final.py:83–84` `T_0*0.95^999` ≈ 5.4e-23，实际远低于 0.01；措辞可接受） |
| 14 | 第 98 行 "total iteration budget of 1500 provides Random Search with 50\% more evaluations than other algorithms" | **夸大或失实**：PSO=30×50=1500、SA=1000、GA≈160×20=3200。1500 并非比"其他算法"都多 50% |
| 15 | 第 143 行 "underwent rigorous validation through… K-fold cross-validation on training data" | **夸大或失实**：最终 `*_Final.py` 与 `2023_2024_Prediction.py` 中无 KFold/cross_val_score 调用（仅有 `Weight_Optimization_Framework.py` 等早期文件导入 KFold） |
| 16 | 第 143 行 "comprehensive statistical significance testing against baseline methods" | **夸大或失实**：见 2.6 与总体结论 #5，唯一检验基于合成数据 |
| 17 | 第 106、108 行 "Multi-Layer Probability Fusion Algorithm" | **夸大或失实**：见总体结论 #7 |

### 2.7 `LaTeX_Dissertation\results.tex`（403 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 4 行 "Each optimization algorithm was executed with 10 independent runs using different random seeds" | **文档内部自相矛盾**：`Multi_Run_Average_Metrics_20250826_171631.txt:4` 明写 "Number of runs per algorithm: 5"；第 52 行本文件又写 "5 independent runs per algorithm" |
| 2 | 第 4 行 "10 independent runs using **different random seeds**" | **夸大或失实**：`Multi_Run_Experiment_Framework_Final.py:38` 为 `np.random.seed(42 + run_i)`（固定可复现种子序列），非"不同随机种子"的自由采样 |
| 3 | 第 16–21 行 `tab:algorithm_performance`（GA/PSO/SA/RS 六指标 + 用时） | **与磁盘一致（可溯源）**：逐值对应 `Multi_Run_Average_Metrics_20250826_171631.txt:10–13`（GA 0.9200/0.9646/0.9199/0.8397/0.8397/1444.67 等）；但该文件本身是 25 人训练集内拟合结果，且见 #1 的 5 次 vs 10 次矛盾 |
| 4 | 第 30–46 行 `tab:sigmoid_parameters` 行标签 GA/PSO/SA/RS | **夸大或失实 + 溯源错位**：SA 行 = PSO 门将参数（`Multi_Run_...txt:96–98`），RS 行 = PSO 后卫参数（同文件 75–77 行）；即两行都不是"该算法的全局最优"。GA 行 α=4.00/τ=0.70/rm=0.70 也无法在 `Multi_Run_...txt` 中定位到独立 GA 配置（文件仅存 PSO 权重） |
| 5 | 第 48 行 "PSO… maximum sigmoid steepness (α=4.00) and moderate inflection point (τ=0.61)" | **文档内部自相矛盾**：与第 39–41 行表中 PSO 行 τ=0.61 一致，但与 `tab:goalkeeper_weights` 第 272–274 行（α=1.541/τ=0.519/rm=0.492）、`tab:defender_weights` 第 239–241 行（α=1.970/τ=0.700/rm=0.433）中同为"PSO"的参数互斥 |
| 6 | 第 52 行 "using multi-run experimental data (5 independent runs per algorithm)" | **夸大或失实**：数据实际来自 `np.random.normal` 合成（`Run_Statistical_Tests.py:20–45`；`Statistical_Testing_Framework.py:72–105`）。5 次运行的真实输出是 `Multi_Run_...txt`，其真实指标为 **Accuracy 0.9200–0.9280、PR-AUC 0.9646–0.9648、Bal-Acc 0.9199–0.9276**，而合成数据用的是 **Mean=0.9325/0.9162/0.7300/0.9208（Accuracy）、Baseline=0.6800/0.6200/0.6500/0.6000**（`Statistical_Test_Results_...txt:7–9,26–28,45–47,64–66`），两者基线数值根本不存在于真实实验 |
| 7 | 第 58–88 行 `tab:one_sample_testing` 全部 t/p/Cohen's d | **夸大或失实（伪造数据来源）**：t 值与 d 值与 `Statistical_Test_Results_20250826_182039.txt` / `..._20250831_231510.txt` 逐位吻合（PSO acc 110.429/d 34.921；PSO PR-AUC 141.129/44.629；PSO Bal-Acc 75.906/24.004；PSO F1 123.469/39.044；GA 55.293/17.485、102.494/32.412、41.906/13.252、75.377/23.836；SA 10.697/3.383、42.410/13.411、10.389/3.285、21.702/6.863；RS 54.862/17.349、89.060/28.163、83.242/26.324、85.254/26.960），而这些输出的生成代码明写"模拟10次运行的数据 (基于实际结果)"并由 `np.random.normal` 生成 |
| 8 | 第 90 行 "PSO achieved the largest effect sizes, with Cohen's d values exceeding 24.0, indicating exceptionally large practical significance" | **夸大或失实**：合成正态分布（σ=0.008–0.01、n=10）必然产生 d>20；d=34.92 意味着均值相差 35 个样本标准差，在任何真实小样本实验中不可能出现，属合成数据的伪影 |
| 9 | 第 96–116 行 `tab:paired_testing` | **部分可溯源、且大量结果被隐藏**：表中 PSO vs GA 与 PSO vs SA 的数字可溯源到同一合成输出文件（t=3.464/p=0.0071/d=1.095；-1.140/0.2836/-0.361；0.665/0.5230/0.210；0.714/0.4934/0.226；47.952/0.0000/15.164；35.364/11.183；28.009/8.857；22.858/7.228）。但同一文件还有 **PSO_vs_RS、GA_vs_SA、GA_vs_RS、SA_vs_RS** 四组对比以及全部 "Not Significant" 结果，论文只保留了 PSO 占优的两组。**选择性报告（cherry-picking）** |
| 10 | 第 110 行 `tab:paired_testing` 中 PSO vs SA 的 p 值写作 "$< 0.001$*" | **与磁盘一致**（输出 p=0.0000）。但 `tab:one_sample_testing` 第 66 行把同一输出中 `p=0.0000` 写作 "$< 0.001$*" 尚可，而 `tab:paired_testing` 第 104 行 PSO vs GA p=0.007 写作 "0.007*" —— 与输出 p=0.0071 一致 |
| 11 | 第 124–139 行 `tab:wilcoxon_test` 仅 4 行（PSO-GA / PSO-SA / GA-SA / SA-RS） | **夸大或失实 + 选择性报告**：输出文件含 6 组对比 × 4 指标。论文第 132 行 PSO vs GA "W=3.0, 0.010*" 对应输出的 accuracy 行（W=3.0, p=0.0098），但同组 pr_auc/f1/balanced（W=17/23/23，p=0.32/0.70/0.70）全部略去；且论文第 133 行 "PSO vs. SA 0.0/0.002"、134 行 "GA vs. SA 0.0/0.002"、135 行 "SA vs. RS 0.0/0.002" 均只取了显著的那一行 |
| 12 | 第 130 行表头 "W-statistic / p-value" 未标注指标维度 | **文档内部自相矛盾**：给读者的印象是"算法整体比较"，实际是某一未说明指标的比较 |
| 13 | 第 142–178 行 `tab:forward_weights`（13 权重 + α/τ/rm） | **与磁盘一致（可溯源）**：逐值对应 `Multi_Run_Average_Metrics_20250826_171631.txt:32–50`（alpha 4.000000 / tau 0.611825 / rm 0.700000 / minutes 0.150 / CrdY 0.080 / CrdR 0.080 / Gls 0.080 / Ast 0.050 / xG 0.080 / SoT 0.150 / G_per_Sh 0.050 / Sh_per90 0.120 / SCA 0.080 / GCA 0.150 / Att_Pen 0.050 / TakeOn_Succ 0.050） |
| 14 | 第 184–211 行 `tab:midfielder_weights` | **与磁盘一致**：对应同文件 53–71 行（tau 0.700000 / CrdR 0.139911→0.140 / Cmp_pct 0.104396→0.104 等） |
| 15 | 第 217–244 行 `tab:defender_weights` | **与磁盘一致但在语义上误导**：对应同文件 74–92 行，但该块在 `Multi_Run_...txt` 中属于 **PSO 的 Defender 配置**；表中 α=1.970/τ=0.700/rm=0.433 与 `tab:sigmoid_parameters` 的 "RS" 行是同一组数字（见 #4） |
| 16 | 第 250–277 行 `tab:goalkeeper_weights` | **与磁盘一致但在语义上误导**：对应同文件 95–113 行（PSO 的 Goalkeeper 配置）；α=1.541/τ=0.519/rm=0.492 与 `tab:sigmoid_parameters` 的 "SA" 行是同一组数字（见 #4） |
| 17 | 第 281 行 "27 players" | **与代码/数据一致**（`Inter_2023_2024_Prediction_Report_20250826_172047.txt:4` Total Players: 27） |
| 18 | 第 287–309 行 `tab:prediction_metrics_2023_2024`（0.7778/0.5556/0.7143/0.6250/0.6459/0.4706/0.7571/0.4781/0.2083/0.6765/0.22s） | **无来源（疑似编造）**：磁盘唯一产物为 0.7407/0.0000/0.0000/0.0000/0.2593/0.0000/0.0000/0.5000/0.2500/0.2787（`Inter_2023_2024_Prediction_Report_20250826_172047.txt:8–19`）。全库 grep `0.7778|0.5556|0.7143|0.6459` 在业务文件中 **零命中** |
| 19 | 第 311 行 "correctly predicting 21 out of 27 player outcomes" | **无来源**：磁盘报告为 **20/27 (74.1%)**（`Inter_2023_2024_Prediction_Report_20250826_172047.txt` PREDICTION SUMMARY）。委托方复现得到的 21/27 属修正后重跑，非现存脚本原始输出 |
| 20 | 第 285 行 "The algorithm demonstrated robust predictive capability" | **夸大或失实**：磁盘产物 Precision=Recall=F1=0（全预测留队），PR-AUC=0.2593 低于随机（0.5 基线约对应 7/27=0.259 的正类率） |
| 21 | 第 317–333 行 `tab:prediction_errors_2023_2024`（Di Gennaro 0.555、Sommer 0.543、Pavard 0.521、Dumfries 0.514、Sensi 0.477、Cuadrado 0.470） | **无来源（疑似编造）**：磁盘报告所有 27 人的 `Dept_Prob` 一律为 **50.0%**（`Inter_2023_2024_Prediction_Report_20250826_172047.txt` DETAILED PREDICTION RESULTS 全列 "50.0%"）。全库 grep `0.555|0.543|0.521|0.514|0.477|0.470` 在业务文件中零命中 |
| 22 | 第 341–364 行 `tab:successful_predictions_2023_2024`（Klaassen 0.678、Sánchez 0.565、Audero 0.523、Agoume 0.505、Akinsanmiro 0.501、Lautaro 0.319 等） | **无来源（疑似编造）**：同上，磁盘概率全为 50.0%；且磁盘报告中 Klaassen/Sánchez/Audero/Agoume/Akinsanmiro **全部被预测为 Stayed（预测错误）**，与该表"Departed / Departed"的成功叙事相反 |
| 23 | 第 370–386 行 `tab:position_specific_2023_2024`（Forward 3/3=100%、Midfielder 9/7=77.8%、Defender 12/9=75.0%、Goalkeeper 3/1=33.3%、Overall 27/21=77.8%） | **无来源且与磁盘冲突**：磁盘报告所有 27 行的 Position 一律为 **"Unknown"**（因 `2023_2024_Prediction.py:186–187` 把 2022-2023 位置数据集与 2023-2024 数据混用，且 `position_group` 来自 `pos` 列解析；报告中显示为 Unknown），故按位置分区统计本身不可能产出此表；"Forward 3 名"也与本论文 2.5 节对 2023-2024 阵容的描述口径不一致 |
| 24 | 第 388 行 "The model achieved perfect accuracy for forwards" | **夸大或失实**：该数字（3/3）无来源；磁盘报告中 4 名前锋（Alexis Sánchez、Lautaro Martínez、Marcus Thuram、Marko Arnautović）中 **Sánchez 已离队**（`Inter_departured_2023_2024.csv:3` = 1），却被预测为 Stayed → 前锋至少 1 例错误；且磁盘报告的 Position 字段全为 "Unknown"，无法定位"前锋 3 名"的划分依据 |
| 25 | 第 395 行 "PSO algorithm achieved 92.8\% accuracy with 96.48\% PR-AUC, representing the highest performance across all algorithms" | **与磁盘一致（可溯源）**（`Multi_Run_...txt:11`），但需限定为训练集内 |
| 26 | 第 397 行 "PSO provided optimal performance-efficiency balance (335.3s vs GA's 1444.7s)" | **与磁盘一致**（同文件 10–11 行） |
| 27 | 第 400 行 "0.9315 composite score" | **与磁盘一致**：`Multi_Run_...txt:20` `Average Composite Score: 0.931497`。但注意 `tab:algorithm_performance` 中 PSO 的 Accuracy=0.9280 与 `Single_Run_ML_Metrics_...txt:19` 的 PSO Composite 0.926730、以及 `模型对比.txt:11` 的 PSO 综合 0.894 三者互斥 → 跨文件矛盾 |
| 28 | 第 403 行 "establish the Multi-layer Probability Fusion Algorithm as a **significant advancement** in sports analytics methodology" | **夸大或失实**：核心结果来自合成检验数据；留出集表现不优于平凡基线；算法为线性加权。无支撑 |
| 29 | 第 311 行 "composite score of 0.6765 reflects balanced performance" | **无来源且语义倒置**：磁盘 composite=0.2787；且 0.6765 是在 Precision/Recall 均极低的前提下算出的，不能称 "balanced" |

### 2.8 `LaTeX_Dissertation\discussion_conclusion.tex`（27 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 5 行 "successfully accomplished all primary objectives" | **夸大或失实**：`introduction.tex:40` 的目标之一是"Demonstrate statistically significant improvements… through comprehensive evaluation metrics"，其唯一证据是合成数据 |
| 2 | 第 5 行 "a **novel** Multi-layer Probability Fusion Algorithm" | **夸大或失实**：见总体结论 #7；percentile ranking + 线性加权 + sigmoid 均为教科书组合 |
| 3 | 第 7 行 "demonstrated **exceptional performance** with the PSO algorithm achieving 92.8\% accuracy with 96.48\% PR-AUC" | **夸大或失实**：92.8% 是 25 人训练集内拟合值；"exceptional" 无泛化证据支撑 |
| 4 | 第 7 行 "maintaining 77.8\% prediction accuracy… successfully predicting 21 out of 27" | **无来源**：磁盘为 74.1%、20/27 |
| 5 | 第 7 行 "established the **superiority** of relative percentile ranking over traditional absolute metric approaches" | **夸大或失实**：从未做过该对照实验；`Project_Continuity_Documentation.md:112` 明确"不需要"该对比 |
| 6 | 第 7 行 "all optimisation algorithms showing statistically significant improvements (p < 0.001) over baseline methods" | **夸大或失实**：p<0.001 来自合成数据；真实 5 次运行的 PSO/GA/RS 间无显著差异（`模型对比.txt` 三者指标几乎相同，且合成输出中 PSO_vs_RS p=0.0811、GA_vs_RS p=0.4864 均不显著） |
| 7 | 第 7 行 "temporal cross-validation, 5-run multi-run experiments, and ground truth verification" | **夸大或失实**：无时序交叉验证实现；5 次运行仅覆盖 **2022-2023 训练集**，2023-2024 留出集只跑过一次（`Inter_2023_2024_Prediction_Report_20250826_172047.txt`） |
| 8 | 第 11 行 "fundamental **paradigm shift**" | **夸大或失实**：无消融实验支持 |
| 9 | 第 13 行 "represents a **significant methodological advancement**" | **夸大或失实**：四算法共享同一边界与目标函数，无机制差异证据 |
| 10 | 第 15 行 "The development of a composite evaluation metric… addresses the fundamental challenge of multi-objective optimisation" | **夸大或失实**：composite 是固定线性权重（0.4/0.3/0.2/0.1），未做多目标优化（无 Pareto 前沿、无权重敏感性实验落盘） |
| 11 | 第 19 行 "The limited sample size of 25 players constrains statistical power" | **与代码/数据一致**，但与本文件第 7 行"p<0.001、exceptional"自相矛盾 |

### 2.9 `LaTeX_Dissertation\appendix.tex`（199 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 9–24 行 `2023_2024_Prediction.py` "Loads 2023-2024 season data" / "Applies PSO-optimized weights" | **与代码/数据一致**（文件存在，功能描述基本准确），但未披露第 171–172 行的赛季错配与静默降级 |
| 2 | 第 26–38 行 `weight_optimization_core_updated.py` 描述 | **与代码/数据一致** |
| 3 | 第 42–56 行 `GA_Weight_Optimization_Experiment_Final.py` "Genetic operators: selection, crossover, mutation / Population-based weight evolution" | **夸大或失实**：该文件仅调用 `differential_evolution`，不含任何自定义 selection/crossover/mutation 代码 |
| 4 | 第 58–72 行 PSO 文件 "Inertia weight adaptation" | **夸大或失实**：`PSO_..._Final.py:73` 固定 `w=0.7`，无自适应 |
| 5 | 第 74–88 行 SA 文件 "Temperature-controlled acceptance… Cooling schedule… Metropolis acceptance criterion" | **与代码/数据一致**（`SA_..._Final.py:81–90,104`） |
| 6 | 第 90–104 行 RS 文件 "Uniform random weight generation" | **夸大或失实**：`RS_..._Final.py:74–79` 为 60% 均匀 + 40% 局部搜索，"智能"策略并非纯均匀 |
| 7 | 第 108–122 行 `Multi_Run_Experiment_Framework_Final.py` 描述 | **与代码/数据一致** |
| 8 | 第 140–155 行 `Statistical_Testing_Framework.py` "One-sample t-tests… Paired t-tests… Wilcoxon… Effect size calculation (Cohen's d)" | **夸大或失实（隐瞒数据来源）**：该文件的 `create_sample_data_for_testing()`（第 72–105 行）用 `np.random.normal` 合成数据，附录完全未提 |
| 9 | 第 167–170 行 `tab:execution_sequence` 推荐执行顺序 1→2→3→4 | **与代码/数据一致**（顺序合理）。但注意真正的统计结果输出 `Statistical_Test_Results_*.txt` 由 `Run_Statistical_Tests.py`（另一文件）产生，与顺序中的 `Statistical_Testing_Framework.py` 不是同一实现 |
| 10 | 第 179–180 行 输出文件命名 `Multi_Run_Average_Metrics_YYYYMMDD_HHMMSS.txt`、`Statistical_Test_Results_YYYYMMDD_HHMMSS.txt` | **与代码/数据一致**（磁盘上确有这两类文件） |
| 11 | 第 196–198 行 "Minimum 8GB RAM"、"Approximately 1GB disk space" | **无法验证**：无资源测量留档 |

### 2.10 `LaTeX_Dissertation\README.md`（141 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 12–22 行 文件结构清单（含 `introduction.tex` … `discussion_conclusion.tex`） | **与代码/数据一致**（这些文件确实存在），但**漏了 `appendix.tex`**，且与 `main.tex` 里的 `Chapter *\` 目录结构不符 |
| 2 | 第 31–35 行 依赖含 `listings, xcolor`、`algorithm, algpseudocode` | **夸大或失实**：`main.tex:10–26` 未加载 `listings`、`xcolor`、`algorithm`、`algpseudocode` |
| 3 | 第 44–50 行 "bibtex main" 编译流程 | **文档内部自相矛盾**：`main.tex:3–7` 使用 `backend=biber`，应运行 `biber` 而非 `bibtex` |
| 4 | 第 61–100 行 各章字数 5,500 / 6,200 / 5,800 / 5,000 / 6,500 / 6,200 / 5,800 | **夸大或失实**：实测 930 / 1781 / 2186 / 1062 / 1442 / 2098 / 720（合计 10,219 词 vs 声称 41,000 词） |
| 5 | 第 61–100 行 章节内容描述（如第 2 章含 "Functional and non-functional requirements specification"、第 4 章 "Ethical considerations"、第 6 章 "Sensitivity analysis and robustness testing"） | **夸大或失实**：`analysis_requirements.tex` 通篇是文献综述与算法理论，无需求规格；`data_collection.tex` 无伦理章节；`results.tex` 无敏感性分析 |
| 6 | 第 104 行 "Comprehensive literature review, **statistical validation**, and methodological soundness" | **夸大或失实**：统计验证基于合成数据 |
| 7 | 第 113 行 "**Novel** percentile-based feature engineering algorithm" | **夸大或失实**：`scipy.stats.percentileofscore` 直接调用（`weight_optimization_core_updated.py:184`），非新算法 |
| 8 | 第 115 行 "**92.0% prediction accuracy (35.3% improvement over baseline)**" | **夸大或失实（本报告最严重的单条宣称）**：论文自身留出集为 77.8%（磁盘 74.1%）；92.0% 是另一批 25 人训练集内的算法对比准确率（`Single_Run_ML_Metrics_...txt:9`）；"35.3% improvement" **没有任何基线来源**——全库不存在产生 35.3% 的实现或输出（注：字符串 "35.3" 仅在 `Multi_Run_Average_Metrics_20250826_171631.txt:11` 的 "335.34" 与 `Statistical_Test_Results_*.txt` 的 "0.2836/0.3366" 中作为子串偶然出现，与基线改进无关） |
| 9 | 第 115 行 标注为 "Empirical Achievement" | **夸大或失实**：数字与语境双重错配（用训练集内拟合值充当预测精度） |
| 10 | 第 122 行 "All chapters are modular and can be compiled independently" | **夸大或失实**：各 `.tex` 用 `\section` 且无 `\documentclass`，不能独立编译 |
| 11 | 第 123 行 "Code listings are properly formatted with syntax highlighting" | **夸大或失实**：全文无 `lstlisting`/`minted`；`appendix.tex` 仅用 `verbatim` |
| 12 | 第 125 行 "Hyperlinks are configured for PDF navigation" | **与代码/数据一致**（`main.tex:38–45`） |
| 13 | 第 132 行 "Supervisor: Todd"、第 133 行 "Year: 2024" | **无法验证 / 跨文档矛盾**：**多数 md 文档署期 2025**（如 `Final_Algorithmic_Contribution_Summary.md:400` `Date: 2025`；`Project_Continuity_Documentation.md:302` `2025年1月`；`算法原理与权重计算效果说明文档.md:202` `2025-08-19`；`Algorithm_Modification_Documentation.md:306` `2025-08-26`），README 却写 2024 |
| 14 | 第 141 行 "approximately 40,000 words of original research" | **夸大或失实**：实测正文合计约 10,749 词（含 appendix 530） |
| 15 | 第 116 行 "Methodological Advancement: Comprehensive framework for sports analytics research" | **夸大或失实**：无独立复现验证 |

### 2.11 `Algorithm_Selection_Rationale.md`（465 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 6/9 行 选了 GA/PSO/SA/RS 四种 | **与代码/数据一致**（四个 Final 脚本） |
| 2 | 第 39/46 行 "12-15个权重参数" | **夸大或失实**：实测 16 个优化维度（13 权重 + α/τ/rm，见 `Multi_Run_...txt:32–50`） |
| 3 | 第 42/49 行 "仅有24名球员数据" | **夸大或失实**：`Inter_Players_Departure_Labels.csv` 为 **25 名** |
| 4 | 第 307/321 行 "每次权重评估需要计算24名球员的预测" | **夸大或失实**：同 #3 |
| 5 | 第 72–79 行 "使用scipy.optimize.differential_evolution… maxiter=20, popsize=10, seed=42" | **与代码/数据一致**（`GA_..._Final.py:76–82`）。**这是全项目最诚实的一处算法披露**，与论文 `analysis_requirements.tex` 的"Genetic Algorithm"命名直接冲突 |
| 6 | 第 124–126 行 `w=0.7, c1=1.5, c2=1.5` | **与代码/数据一致**（`PSO_..._Final.py:73–75`） |
| 7 | 第 167–168 行 `alpha=0.95` 指数降温 | **与代码/数据一致**（`SA_..._Final.py:83–84`） |
| 8 | 第 209 行 `exploration_phase = iteration < max_iterations * 0.6` | **与代码/数据一致**（`RS_..._Final.py:74`） |
| 9 | 第 300–303 行 复杂度 "GA: 中等复杂度，种群×迭代×评估；PSO: 较低复杂度；SA: 最低；RS: 最低" | **夸大或失实**：GA 用 `popsize=10 × 16 维 × 20 代 ≈ 3200` 次评估，PSO 用 `30×50=1500`，SA `1000`，RS `1500`。GA 实际最高（与"中等"措辞不符），且 SA 与 RS 相同（"最低"两者并列却不分） |
| 10 | 第 359–371 行 "每个算法运行10次" + `seed=42+run` | **夸大或失实**：真实 `Multi_Run_Average_Metrics_...txt:4` 为 **5 次**；且 10 次只出现在合成脚本 `Run_Statistical_Tests.py:21` 与 `Statistical_Testing_Framework.py:74` |
| 11 | 第 376 行 "多重比较校正避免假阳性" | **夸大或失实**：真实输出 `Statistical_Test_Results_*.txt` 无 Bonferroni 校正段落；仅 `Run_Statistical_Tests.py:141–154` 在合成数据上算了校正但未落盘到论文使用的文件 |
| 12 | 第 431/438 行 "首次将足球位置特异性纳入权重优化算法" / "First to incorporate football position specificity into weight optimization algorithms" | **夸大或失实 / 无法验证**：无文献检索证据支持"首次"；`analysis_requirements.tex:25` 反而引用了 `metulini2018modelling`（GA 用于阵容优化）等同类工作 |
| 13 | 第 407–414 行 文献（Bunker & Susnjak 2022、Rein & Memmert 2016、Wolpert & Macready 1997、Derrac et al. 2011 等） | **无法验证**：无 `.bib`，且这些引用**未出现在论文任何 `.tex` 中**（论文引用的是 vanarem2025、fernandez2021、bunker2019machine、razali2017predicting、hubacek2019learning、bransen2017chemistry、metulini2018modelling、singh2020optimizing、shahriari2015taking）→ 两套文献体系互不相干 |
| 14 | 第 434/441 行 "实时预测框架 / 建立可用于实际转会决策的预测系统" | **夸大或失实**：`2023_2024_Prediction.py` 单次执行 0.22s 只是脚本级推理，无服务化、无在线更新、无 API；实测留出集精度不优于平凡基线 |

### 2.12 `Algorithm_Modification_Documentation.md`（366 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 5、12 行 "5个通用指标+10个位置特色指标" | **文档内部自相矛盾 + 与代码不符**：`weight_optimization_core_updated.py:123–130` 的 `get_universal_metrics()` 返回 **5 项**（minutes/age/CrdY/CrdR/Contract_expires），但第 300–301 行 `calculate_departure_probability_with_weights` **跳过 age 与 Contract_expires**，实际参与加权仅 **3 项**；`design.tex:76` 的 `tab:universal_metrics` 也只列 3 项 |
| 2 | 第 27 行 "age \| standard \| age \| 降序↘️ \| 年龄，越年轻越好" | **与代码/数据一致**（第 126 行 `'age': {..., 'ascending': False}`） |
| 3 | 第 30 行 `Contract_expires \| contract \| Contract_expires \| 降序` | **夸大或失实**：该字段从未被读入（见总体结论 #9） |
| 4 | 第 92–136 行 "复杂合同算法"（4 维风险调整 + 租借球员特殊处理，`if contract_years == -1`） | **夸大或失实**：代码中无 `calculate_contract_risk_adjustment()` 函数；`Contract_2022_2023.csv` 中确有 `-1`（租借）标记（如 `Francesco Acerbi,-1`、`Kristjan Asllani,-1`、`Raoul Bellanova,-1`、`Romelu Lukaku,-1`），但从未被使用。全文 grep `calculate_contract_risk_adjustment` 在 `weight_optimization_core_updated.py`、四个 `*_Final.py` 中**零命中** |
| 5 | 第 142–152 行 "Enhanced_Weight_Optimization_Experiment.py (原GA算法)… 添加 `calculate_contract_risk_adjustment()` 复杂合同算法" | **夸大或失实**：`Enhanced_Weight_Optimization_Experiment.py` 不在最终四算法管线中；最终 `GA_Weight_Optimization_Experiment_Final.py` 不含该函数 |
| 6 | 第 152 行 "使用差分进化算法" | **与代码/数据一致**。注意这与论文"Genetic Algorithm"命名冲突，说明**作者本人知道用的是差分进化** |
| 7 | 第 187–196 行 "GA_Weight_Optimization_Experiment_Updated.py… 使用差分进化作为遗传算法变体" | **与代码/数据一致**（自我承认） |
| 8 | 第 228–243 行 "权重边界策略"：`minutes/age/CrdY/CrdR = (0.08,0.15)`、`Contract_expires = (0.05,0.12)`、`base_risk = (0.2,0.4)`、`risk_multiplier = (0.3,0.7)` | **夸大或失实**：最终代码的 `get_bounds()`（如 `PSO_..._Final.py:25–55`）**没有** `Contract_expires_weight`，也**没有** `base_risk`，而是用 `alpha (1.0,4.0)` + `tau (0.3,0.7)` 替代 `base_risk`。即该"边界策略"是旧版（`Enhanced_...py` 时代）的残留描述 |
| 9 | 第 249–254 行 composite 公式 | **与代码/数据一致**（`Multi_Run_Experiment_Framework_Final.py:48–53`） |
| 10 | 第 310 行 JSON 示例 `"total_inter_players": 20` | **夸大或失实**：真实为 25（2022-2023）或 27（2023-2024） |
| 11 | 第 311 行 `"positions_analyzed": ["Forward","Midfielder","Defender"]` | **文档内部自相矛盾**：第 5、139 行均强调包含守门员（4 位置）；`Multi_Run_...txt:94` 也确有 Goalkeeper 配置 |
| 12 | 第 315 行 `"player_count": 4`（Forward） | **与代码/数据一致**（实测前锋 4 名） |
| 13 | 第 320–323 行 `"accuracy": 0.85, "pr_auc": 0.78, "cohen_kappa": 0.72` | **无法验证 / 与真实不符**：真实为 0.92/0.9646/0.8397（`Multi_Run_...txt:10`）；示例数字来源不明 |
| 14 | 第 138 行 "全部26名Inter球员(100%匹配率)"（此条见 `增强版权重优化算法解释文档.md`） | 见 2.15 |
| 15 | 第 352 行 "统计显著性: Cohen's Kappa消除偶然性" | **夸大或失实**：Kappa 是一致性指标，不构成显著性检验 |
| 16 | 第 364–366 行 "四个更新后的算法文件… 为球员离队预测提供了更加精确和实用的解决方案" / "所有代码经过精心设计，确保逻辑正确性和可执行性" | **夸大或失实**：四个 `*_Final.py` 中合同数据未传入、`load_position_specific_data` 全部 `except: pass` 静默失败、2023-2024 预测使用 2022-2023 位置数据 |

### 2.13 `Final_Algorithmic_Contribution_Summary.md`（400 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 44 行 "设计并实现了**三种**互补的权重优化算法"；第 46–74 行列出 **贝叶斯优化 / 遗传算法 / 网格搜索** | **夸大或失实（与最终研究不符）**：最终研究用 GA/PSO/SA/RS 四算法；贝叶斯优化在 `venv` 中无 `skopt` 依赖，`Weight_Optimization_Framework.py:260` 会回退随机搜索 |
| 2 | 第 104 行 "Serie A 2022-2023赛季 **535** 名球员" | **夸大或失实**：实测 603 |
| 3 | 第 105 行 "Inter Milan **25** 名球员" | **与代码/数据一致** |
| 4 | 第 113 行 "整体准确率 72.4% → 87.9%，**+21.5%**，p < 0.01" | **无来源（疑似编造）**：全库无产生 72.4%/87.9% 的脚本或输出 |
| 5 | 第 114 行 "前锋位置 75.0% → 95.0%，+26.7%，p < 0.05" | **无来源** |
| 6 | 第 115 行 "中场位置 70.0% → 82.5%，+17.9%" | **无来源** |
| 7 | 第 116 行 "后卫位置 72.7% → 86.4%，+18.8%" | **无来源** |
| 8 | 第 120–125 行 算法对比表：贝叶斯 0.950、遗传 0.925、网格 0.900、随机 0.875 | **无来源 / 与 `模型对比.txt` 冲突**：`模型对比.txt:5–8` 为 0.920/0.920/0.684/0.920（GA/PSO/SA/RS） |
| 9 | 第 122 行 贝叶斯优化 "全局最优保证：高概率" | **夸大或失实**：贝叶斯优化无全局最优保证；且该算法实际未运行 |
| 10 | 第 137–139 行 "t-statistic: 4.287, p-value: 0.003, Cohen's d: 1.24 (大效应量)" | **无来源（疑似编造）**：该组数字与 `Weight_Optimization_Research_Results.md:143–150`、`权重优化算法实验原理详解.md:434–436` 三处互相复制，但磁盘上无对应输出文件；真实合成输出为 t=3.464/p=0.0071/d=1.095 等（`Statistical_Test_Results_...txt`） |
| 11 | 第 146–147 行 "W-statistic: 48, p-value: 0.008" | **无来源**：真实输出 W 值域为 {0, 3, 11, 17, 18, 22, 23, 25, 27}，无 48 |
| 12 | 第 153 行 "95% 置信区间: [+15.2%, +27.8%]" | **无来源**：无 bootstrap 脚本输出 |
| 13 | 第 162–164 行 "一致性率 85.7%（在85.7%的交叉验证折中…）" | **无来源 + 文档内部自相矛盾**：85.7% 既是"一致性率"又在括号里被解释为"折的比例"，同一数字两种含义；且无 CV 输出文件 |
| 14 | 第 167 行 "跨赛季性能: 84.2% (仅3.7%衰减)" | **夸大或失实**：真实跨赛季为 0.7407（磁盘）/0.7778（复现）；84.2% 无来源 |
| 15 | 第 171 行 "最大性能下降 8.3%（在20%噪声水平下）" | **无来源**：`Generalization_Testing_Framework.py` 存在但无输出文件 |
| 16 | 第 175–176 行 "最大敏感性: 0.031 / 低敏感性" | **无来源** |
| 17 | 第 203–206 行 "准确率 72.4%→87.9%、精确率 71.2%→86.3%、召回率 69.8%→85.7%、F1 70.5%→86.0%" | **无来源**（同 #4） |
| 18 | 第 209 行 "收敛速度: 提升35%（贝叶斯优化）"；第 210 行 "计算复杂度: O(n³) → 智能搜索策略" | **夸大或失实**：贝叶斯优化未运行；`O(n³)` 无定义（n 是迭代数？），与 CRITICAL 的复杂度表述（第 225 行 `O(t³)`）重复且不同符号 |
| 19 | 第 211 行 "参数稳定性: CV < 0.2" | **无来源** |
| 20 | 第 215 行 "时间泛化稳定性: 96.3% (3.7%衰减)" | **文档内部自相矛盾**：第 167 行说跨赛季 84.2%、衰减 3.7%；此处说 96.3%、衰减 3.7%。84.2 ≠ 96.3，但衰减都写 3.7% |
| 21 | 第 216 行 "噪声鲁棒性: 91.7% (20%噪声下)" | **文档内部自相矛盾**：第 171 行说"下降 8.3%"，此处说 91.7% —— 若基线为 100%，91.7% 对应下降 8.3%，勉强自洽，但同一文档两次用不同表述易生歧义；且两者都无来源 |
| 22 | 第 306 行 "基于相对百分位排名的特征工程**显著优于**传统绝对数值方法" | **夸大或失实**：无对照实验；`Project_Continuity_Documentation.md:112` 明确不做该对比 |
| 23 | 第 309 行 "所有性能改进都通过了严格的统计显著性检验" | **夸大或失实**：检验基于合成数据或根本无来源 |
| 24 | 第 336 行 "算法创新 + 方法论研究 + 实证验证 = **高质量数据科学研究项目**" | **夸大或失实**：自我评价，与磁盘证据不符 |
| 25 | 第 393 行 "**具有明确算法创新、严谨实验验证、显著性能提升**的高质量数据科学研究项目" | **夸大或失实**（同上） |
| 26 | 第 135 行 `H0: μ_optimized - μ_baseline = 0` / `H1: ... > 0` 但第 137 行给 t 与双侧 p | **文档内部自相矛盾**：单侧假设应报告单侧 p，且 t=4.287 需 df 才能解读；未给出 n 与 df |

### 2.14 `Weight_Optimization_Research_Results.md`（275 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 89 行 "Serie A 2022-2023赛季: **535**名球员" | **夸大或失实**：实测 603 |
| 2 | 第 90–91 行 "Inter Milan 球员: 25 名；前锋(4)、中场(8)、后卫(11)、门将(2)" | **部分一致 + 部分失实**：总数 25 ✓；前锋 4 ✓、后卫 11 ✓；**中场 8 ✗（实为 7）、门将 2 ✗（实为 3）** |
| 3 | 第 97–104 行 前锋位置对比表（基线 0.750 / 专家 0.875 / 随机 0.875 / 网格 0.900 / 遗传 0.925 / 贝叶斯 **0.950**，含"优化时间 2.3s/15.7s/8.4s/6.1s"） | **无来源（疑似编造）**：无任何磁盘文件包含这些数值与用时 |
| 4 | 第 107–117 行 JSON "最优权重配置"（`goals_weight: 0.387` 等，含 `age_weight`） | **夸大或失实**：真实 PSO 前锋配置为 `Gls_weight: 0.080`（`Multi_Run_...txt:41`）；且真实权重上限 0.15，0.387 超出边界 |
| 5 | 第 121–126 行 中场对比（基线 0.700 / 贝叶斯 0.825 / 遗传 0.800 / 网格 0.788） | **无来源** |
| 6 | 第 130–133 行 后卫对比（基线 0.727 / 优化 0.864，"最优权重分布 minutes(0.35), progressive_passes(0.28), assists(0.22), goals(0.15)"） | **无来源 + 与代码边界冲突**：真实后卫权重上限 0.15，0.35/0.28/0.22 全部越界；且后卫指标体系中不存在 `assists`/`goals`（`weight_optimization_core_updated.py:132+` 的后卫 10 指标为 Tkl/Int/Blocks/Clr/Tkl_pct/Cmp_pct/Cmp_pct_Long/PrgP/Final_Third/Def_3rd） |
| 7 | 第 143–145 行 "t-statistic: 4.287, p-value: 0.003" | **无来源**（同 2.13 #10） |
| 8 | 第 150 行 "Cohen's d = 1.24" | **无来源** |
| 9 | 第 159–160 行 "W-statistic: 48, p-value: 0.008" | **无来源** |
| 10 | 第 170–175 行 性能改进汇总表（含 95% 置信区间 [+15.2%, +27.8%] 等） | **无来源** |
| 11 | 第 179–183 行 复杂度表 "贝叶斯优化 O(n³)/O(n²)" | **夸大或失实**：GP 本身为 O(n³)（n 为观测点数），但此处 n 未定义；且贝叶斯优化未运行 |
| 12 | 第 190–193 行 "跨赛季验证… 泛化准确率 84.2%，性能衰减仅 3.7%" | **无来源（且与真实 0.7407/0.7778 冲突）** |
| 13 | 第 195–199 行 "**跨联赛验证**：英超适应性 78.6%（适应后 86.3%）、西甲 81.2%（适应后 88.9%）" | **无来源（疑似编造）**：项目数据仅含意甲（`data excel\2022-2023`、`2023-2024` 均只有 ITA_SerieA），无任何英超/西甲数据文件或脚本 |
| 14 | 第 230 行 "平均21.5%的准确率改进" | **无来源** |
| 15 | 第 256 行 "通过贝叶斯优化、遗传算法、网格搜索三种优化方法的综合应用，平均准确率从72.4%提升至87.9%" | **夸大或失实**：三种算法与最终研究不符；数字无来源 |
| 16 | 第 275 行 "学术价值: 方法论贡献 + 实证验证 + 性能突破 = 高质量的数据科学研究项目" | **夸大或失实** |

### 2.15 `PPT_Content_Document.md`（412 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 84/100 行 "联赛总球员：500+名球员数据" | **与代码/数据一致（模糊表述）**：603/616 确为 500+，措辞回避了精确值 |
| 2 | 第 85/101 行 "国米球员：**24名**球员完整数据" | **夸大或失实**：实测 25（2022-2023）；且与同项目 `多算法权重优化实验PPT汇报文档.md:68` 的"22名"、`增强版权重优化算法解释文档.md:138` 的"26名"三者互斥 |
| 3 | 第 86/102 行 "离队标签：人工标注的真实离队情况" | **与代码/数据一致**（CSV 存在） |
| 4 | 第 194/215 行 "遗传算法… 参数：种群大小=10，迭代次数=20" | **夸大或失实（参数语义错误）**：`GA_..._Final.py:79–80` 的 `maxiter=20, popsize=10` 是差分进化参数；DE 中总种群 = popsize × dim = 160 |
| 5 | 第 199/220 行 PSO "粒子数=30，迭代次数=50" | **与代码/数据一致**（`PSO_..._Final.py:69`） |
| 6 | 第 204/225 行 SA "初始温度=100，最大迭代=1000" | **与代码/数据一致**（`SA_..._Final.py:92`） |
| 7 | 第 209/230 行 RS "迭代次数=1500，智能策略" | **与代码/数据一致**（`RS_..._Final.py:88`） |
| 8 | 第 241–242/270 行 PR-AUC 权重 40% | **与代码/数据一致**（composite 公式） |
| 9 | 第 257/285 行 Balanced Accuracy 权重 20% | **与代码/数据一致** |
| 10 | 第 247/275 行 "Cohen's Kappa… 权重：用于综合评分" | **夸大或失实**：composite 公式不含 Kappa（`Multi_Run_Experiment_Framework_Final.py:48–53`） |
| 11 | 第 298–304 行 最优算法性能对比：GA PR-AUC 0.7245/Acc 0.7083/Bal-Acc 0.7292/MCC 0.4167/综合 0.6895；PSO 0.6829/0.6667/0.6875/0.3333/0.6324；SA 0.6543/0.6250/0.6458/0.2500/0.5986；RS 0.6128/0.5833/0.6042/0.1667/0.5542 | **无来源（疑似编造）**：与 `模型对比.txt:5–8`（0.920/0.920/0.684/0.920）和 `results.tex:18–21` 全部冲突；且结论"GA 最优"与论文"PSO 最优"**直接对立** |
| 12 | 第 306–321 行 "最优权重配置 (GA算法)" 前锋 `goals_weight: 0.1287` 等 | **与代码/数据一致的数量级**（在 0.05–0.15 边界内），但无磁盘同名配置可精确匹配 |
| 13 | 第 5–11 行 标题"基于权重优化算法的足球球员离队预测研究——以国际米兰2022-2023赛季为例" | **文档内部自相矛盾**：第 54–56 行技术路线以"权重优化"为核心，但该 PPT 的算法结果（#11）与最终论文（PSO 最优）矛盾 |
| 14 | 第 363–364 行 "贝叶斯优化进一步提升权重搜索效率"（列为未来工作） | **与代码/数据一致（诚实）**：与 `Final_Algorithmic_*` 等文档把贝叶斯列为"已完成核心贡献"**跨文档矛盾** |
| 15 | 第 405 行 "准备回答关于算法选择、数据质量、结果可靠性的问题" | **无法验证**（建议性内容） |

### 2.16 `Project_Continuity_Documentation.md`（308 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 13–14 行 工作目录 `F:\Samuel\学习\final project\`、venv 路径 `F:\Samuel\学习\final project\venv\Scripts\python.exe` | **夸大或失实**：实际为 `F:\Samuel\football recruitment\final project\`（第 212–213 行重复同一错误路径） |
| 2 | 第 32 行 "系统化权重优化框架 (**贝叶斯**、遗传、网格搜索)" | **夸大或失实**：与最终四算法不符；且贝叶斯无依赖 |
| 3 | 第 58/65/75 行 "**文件位置**: `Weight_Optimization_Framework.py`" | **与代码/数据一致**（该文件确含 `calculate_percentile_score`、`bayesian_optimization`、`grid_search_optimization`、`calculate_departure_probability`） |
| 4 | 第 82–84 行 核心文件清单 `Weight_Optimization_Framework.py` / `Weight_Optimization_Experiment.py` / `simple_weight_optimization_demo.py` | **与代码/数据一致**（三文件均存在） |
| 5 | 第 87–88 行 `Statistical_Significance_Testing_Framework.py` / `Generalization_Testing_Framework.py` | **与代码/数据一致**（两文件均存在） |
| 6 | 第 91–95 行 文档清单含 `Weight_Optimization_Research_Results.md`、`Final_Algorithmic_Contribution_Summary.md`、`Algorithm_Innovation_Framework_Analysis.md`、`V1_Percentile_Based_Model_Technical_Documentation.md`、`Project_Repositioning_and_Algorithm_Innovation_Strategy.md` | **夸大或失实**：前两个存在；**后三个在磁盘上不存在**（全库 glob 零命中） |
| 7 | 第 98 行 `Inter_Players_Departure_Labels.csv` (25名球员) | **与代码/数据一致**，但路径不完整（实际在 `data excel\2022-2023\` 下，第 234 行才写全） |
| 8 | 第 99 行 `data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv` | **与代码/数据一致** |
| 9 | 第 102–103 行 `Inter_V1_Enhanced_Complete_Final.json` / `Inter_V1_Percentile_Based_Predictions.json` | **夸大或失实**：两文件在磁盘上不存在（仅存 `Multi_Run_Experiment_Results_20250826_171631.json`、`Inter_2023_2024_Predictions_20250826_171723.json`，且后者为截断的 11 行不完整 JSON） |
| 10 | 第 128–132 行 "已完成算法实现：贝叶斯权重优化算法 / 遗传算法权重优化 / 网格搜索权重优化 / 随机搜索基线算法 / 权重优化对比实验框架" | **部分失实**：函数在 `Weight_Optimization_Framework.py` 中定义（第 253/308/353/423/469 行）属实，但**贝叶斯分支不可运行**（无 `skopt`，第 260 行回退） |
| 11 | 第 135–142 行 "已完成验证框架：配对t检验 / 威尔科克森 / 自助法置信区间 / McNemar / 交叉验证稳定性 / 时间泛化 / 噪声鲁棒性 / 权重敏感性分析" | **夸大或失实**：以"✅ 已完成"标记，但 `Weight_Optimization_Research_Results.md` 与 `Final_Algorithmic_Contribution_Summary.md` 中对应的 6 组数字（t=4.287、W=48、CI[+15.2%,+27.8%]、85.7%、84.2%、8.3%、0.031）**在磁盘上均无输出文件来源** |
| 12 | 第 239 行 `min_minutes = 90  # 最少出场时间筛选`（列为"数据加载参数"） | **夸大或失实**：最终管线（`weight_optimization_core_updated.py`、四个 `*_Final.py`、`2023_2024_Prediction.py`）**均无此参数**；仅早期文件 `GA_Clean.py:28`、`PSO_Clean.py:27`、`SA_Clean.py:27`、`RS_Clean.py:27`、`Weight_Optimization_Experiment.py:60` 等有 `df['Min'] > 90` |
| 13 | 第 238 行 `skiprows = 3` | **口径不完整（非严格矛盾）**：`weight_optimization_core_updated.py:24`（2022-2023 主数据）确实用 `skiprows=3`；但位置数据读取（`:68,74,84,91,103,113`）与 `2023_2024_Prediction.py:39` 用 `skiprows=2`。该文档把 `skiprows` 泛化为全局"数据加载参数"，与实际不一致（详见附录 C #4） |
| 14 | 第 227 行 "scikit-optimize 贝叶斯优化 (如未安装会回退到随机搜索)" | **与代码/数据一致且诚实**（`Weight_Optimization_Framework.py:31–38,260`）；`venv\Lib\site-packages` 无 `skopt` → 回退路径生效。**此条与 `Final_Algorithmic_*`、`Weight_Optimization_Research_Results.md` 的"贝叶斯优化已完成并最优"直接冲突** |
| 15 | 第 247 行 "**状态**: ✅ 完成 - 所有核心算法已实现并文档化" | **夸张或失实**：贝叶斯不可运行、合同算法缺失、验证框架无输出 |
| 16 | 第 251 行 "实验验证状态: 📋 **待执行** - 框架已建立，需运行生成具体数据" | **与代码/数据一致（诚实）**。**这是全项目唯一明确承认"实验未完成"的陈述**，与 #11 的"✅ 已完成验证框架"以及其余三份文档的"已获得显著结果"直接矛盾 |
| 17 | 第 256 行 "**成果**: 8份核心技术文档" | **夸大或失实**：目录实际 11 份 `.md`，其中 3 份被本文件引用但不存在；"8份"无清单对应 |
| 18 | 第 259–260 行 "项目转化状态: ✅ 成功… **证据**: 明确的算法贡献点 + 系统的验证框架 + 完整的方法论" | **夸大或失实**：验证框架无输出，"证据"不成立 |
| 19 | 第 302–303 行 "文档生成时间: 2025年1月 / 项目阶段: 算法框架完成，实验验证待执行" | **与 README 第 133 行 "Year: 2024" 跨文档矛盾**；且若为 2025 年 1 月，则无法解释同目录存在 2025-08 的产物（`Multi_Run_Average_Metrics_20250826_*.txt`、`算法原理与权重计算效果说明文档.md:202` 的 2025-08-19） |

### 2.17 `权重优化算法实验原理详解.md`（638 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 19–21 行 "传统方法：均匀权重（如各占20%）" | **文档内部自相矛盾**：若为 5 指标（第 99–104 行示例代码含 5 个 `*_percentile`），均匀权重应为 20%；但真实优化空间含 13 个权重（`Multi_Run_...txt:36–50`），均匀权重应为 1/13 ≈ 7.7% |
| 2 | 第 30–33 行 四算法：贝叶斯 / 遗传 / 网格 / 随机搜索 | **夸大或失实**：与最终 GA/PSO/SA/RS 不符；贝叶斯不可运行 |
| 3 | 第 46–63 行 `calculate_percentile_score` 代码块 | **与代码/数据一致**（`weight_optimization_core_updated.py:184–194` / `Weight_Optimization_Framework.py:165`） |
| 4 | 第 74–82 行 "实际应用示例：Lautaro Martínez 绝对进球数 21 个，在所有 Serie A 前锋中的百分位 95.2% → 0.952；Alessandro Bastoni 绝对进球数 3 个，在所有 Serie A 后卫中的百分位 85.7% → 0.857" | **夸大或失实**：磁盘无任何百分位输出文件可佐证；且后卫进球百分位 85.7% 明显偏高（Bastoni 2022-2023 赛季意甲 0 球，见 `data excel\2022-2023\ITA_SerieA_player_standard_stats_2022_2023.csv` 的 `Gls` 列口径）。**这是"具体到球员的编造示例"** |
| 5 | 第 98–104 行 `performance_score` 示例代码（5 项直接加权求和，**无归一化除法**） | **文档内部自相矛盾 + 与代码不符**：真实代码除以权重和（`weight_optimization_core_updated.py:315–316`）；`design.tex:314` 也带分母。与 `算法原理与权重计算效果说明文档.md:76`、`增强版权重优化算法解释文档.md:76` 的写法又不同 |
| 6 | 第 107–111 行 `base_risk = weights['base_risk']`（直接取权重值） | **夸大或失实**：真实 `base_risk` 是 sigmoid 计算输出（`weight_optimization_core_updated.py:286`），不是优化变量；优化变量是 `alpha`/`tau` |
| 7 | 第 124–148 行 目标函数示例（"最大化预测准确率"，返回 `-accuracy`） | **夸大或失实**：真实目标函数是 composite = 0.4·PR-AUC + 0.3·F1 + 0.2·Bal-Acc + 0.1·(1−Brier)，不是 accuracy |
| 8 | 第 167–188 行 `bayesian_optimization` 实现（`gp_minimize`, `n_calls=50`, `acq_func='EI'`, `random_state=42`） | **与代码/数据一致（`Weight_Optimization_Framework.py:253–279`）但不可运行**：无 `skopt` 依赖 |
| 9 | 第 191–196 行 "典型收敛过程：迭代 1 → 0.720；5 → 0.760；15 → 0.840；30 → 0.879（最优）" | **无来源（疑似编造）**：标为"典型收敛过程"，但无日志文件 |
| 10 | 第 210–228 行 `genetic_algorithm_optimization`（`differential_evolution`, `maxiter=50, popsize=20`） | **与代码/数据一致（`Weight_Optimization_Framework.py:308–323`）**，但**与最终 GA 脚本参数不符**（`GA_..._Final.py:79–80` 为 `maxiter=20, popsize=10`）；跨文档矛盾 |
| 11 | 第 232–237 行 "进化过程示例：第1代 0.650/0.720；第10代 0.740/0.810；第25代 0.820/0.870；第35代 0.875" | **无来源（疑似编造）**；且与 `maxiter=20` 冲突（示例跑到第 35 代） |
| 12 | 第 251–283 行 `grid_search_optimization`（`grid_size=5`，权重和约束 `abs(weight_sum-1.0) < 0.1`） | **与代码/数据一致（`Weight_Optimization_Framework.py:353`）**；但与最终研究无关（网格搜索不在最终四算法中） |
| 13 | 第 292/310–311 行 "2022-2023赛季意甲所有球员统计数据 (**535名球员**)" | **夸大或失实**：实测 603 |
| 14 | 第 294 行 "验证数据: 25名Inter球员" | **与代码/数据一致** |
| 15 | 第 315 行 `df_filtered = df_serie_a[df_serie_a['Min'] > 90]  # 最少90分钟出场` | **夸大或失实（就最终管线而言）**：该筛选只存在于早期文件；且直接与 `data_collection.tex:13` 的 535 人（未筛）和 603（未筛）都不吻合 |
| 16 | 第 319 行 `positions = ['Forward', 'Midfielder', 'Defender']  # 排除门将` | **文档内部自相矛盾**：与 `data_collection.tex`（4 位置）、`Multi_Run_...txt:94`（含 Goalkeeper）冲突；示例代码排除门将但研究包含门将 |
| 17 | 第 368–374 行 总体准确率提升表（均匀基线 72.0%、随机 78.5%、网格 84.2%、遗传 87.5%、**贝叶斯 87.9%**，标注 "+21.5%"/"+22.1%"） | **无来源（疑似编造）**：与 `Final_Algorithmic_*` 第 113 行的 72.4%→87.9% **互相矛盾**（此处基线 72.0%） |
| 18 | 第 384–395 行 前锋：基线 75.0% → 优化后 95.0%（贝叶斯），"+20.0%（绝对）/ +26.7%（相对）" | **无来源**；与 `Final_Algorithmic_*` 第 114 行一致（同一编造数字被复制两处） |
| 19 | 第 397–409 行 中场：基线 70.0% → 82.5%（遗传算法） | **无来源** |
| 20 | 第 411–423 行 后卫：基线 72.7% → 86.4%（**网格搜索**） | **无来源 + 文档内部自相矛盾**：与 `Final_Algorithmic_*` 第 119 行"网格搜索优化 (+18.8% 后卫)"一致，但与本文件第 414 行结论与第 550 行"网格搜索全面"相符 —— 然而与 `results.tex` 的"PSO 全面最优"对立 |
| 21 | 第 434–436 行 "t = 4.287, p = 0.003, Cohen's d = 1.24" | **无来源** |
| 22 | 第 443–444 行 "W = 48, p = 0.008" | **无来源** |
| 23 | 第 472 行 "平均改进: 22.1%的相对准确率提升" | **无来源 + 文档内部自相矛盾**：第 373–374 行标遗传 +21.5%、贝叶斯 +22.1%；第 472 行却称"平均 22.1%"，且第 543 行重复"平均22.1%" |
| 24 | 第 477 行 "贝叶斯优化 **4.2秒**内找到近似最优解" | **无来源 + 自相矛盾**：第 374 行表中贝叶斯执行时间写 **4.2s**，但与 `results.tex` 的 PSO 335.3s 完全不在一个量级；且贝叶斯不可运行 |
| 25 | 第 543–544 行 "显著性能提升: 平均22.1%… p < 0.05，大效应量 (Cohen's d = 1.24)" | **无来源** |
| 26 | 第 548 行 "贝叶斯优化最优: 效果最好且效率最高" | **夸大或失实**：算法未运行 |
| 27 | 第 553 行 "百分位排名优越性: 相比绝对数值更加公平准确" | **夸大或失实**：无对照实验 |
| 28 | 第 594 行 "**开源贡献**: 完整的实现代码可供学术界使用" | **夸大或失实**：无许可证、无仓库、`venv` 已入库、代码含大量 `except: pass` |

### 2.18 `算法原理与权重计算效果说明文档.md`（203 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 5 行 四算法 GA/PSO/SA/RS | **与代码/数据一致**（与最终论文一致） |
| 2 | 第 17 行 "评估指标体系（**9项**机器学习指标）" | **与代码/数据一致**（`Multi_Run_...txt:8` 列 Accuracy/PR-AUC/Bal-Acc/Cohen-K/MCC/Brier；`2023_2024_Prediction.py:237–246` 再输出 Precision/Recall/F1/ROC-AUC → 9–10 项）。但 `results.tex:130–136` 的 `tab:ml_metrics` 与 `多算法权重优化实验PPT汇报文档.md:45`（"5个ML核心指标"）口径互斥 → 跨文档矛盾 |
| 3 | 第 34 行 "使用**微分进化**策略提高搜索效率" | **与代码/数据一致且诚实**（`GA_..._Final.py:7`）。**与论文"Genetic Algorithm"命名直接冲突** |
| 4 | 第 38–39 行 "通过适应度函数（综合9项ML指标）评估个体优劣" | **夸大或失实**：实际适应度是 4 项加权 composite（`Multi_Run_Experiment_Framework_Final.py:48–53`），不是 9 项 |
| 5 | 第 74 行 SA "理论上保证找到全局最优解" | **夸大或失实**：SA 仅在无限时间 + 特定冷却（对数）下以概率 1 收敛；代码用指数冷却 `0.95`（`SA_..._Final.py:83–84`），无此保证 |
| 6 | 第 106 行 `离队概率 = base_risk + (加权综合百分位分数) × risk_multiplier` | **与代码不符**：真实为 `base_risk + (1 − performance_score) × risk_multiplier`（`weight_optimization_core_updated.py:326`；`design.tex:324`）。**漏掉 `1 −`，符号方向反了** |
| 7 | 第 109–110 行 "base_risk: 基础离队风险 (0.2-0.4)、risk_multiplier: (0.3-0.7)" | **夸大或失实**：`base_risk` 由 sigmoid 计算并被 clip 到 **[0.1, 0.3]**（`weight_optimization_core_updated.py:287`），不是 (0.2,0.4)；`risk_multiplier` 边界 (0.3,0.7) ✓ |
| 8 | 第 114–115 行 "重要指标权重: 0.08-0.15；次要指标权重: 0.05-0.12" | **与代码/数据一致** |
| 9 | 第 127–130 行 复杂度 "GA O(G×P×N)、PSO O(I×P×N)、SA O(I×N)、RS O(I×N)" | **与代码/数据一致（量级）** |
| 10 | 第 141 行 "通过算法优化的权重配置相比人工设定权重，预测准确率**提升15-25%**，F1分数改善0.1-0.2" | **无来源（疑似编造）**：无基线对照输出；真实留出集 F1 = 0.0（磁盘）或 0.6250（复现），无 0.1–0.2 的"改善"证据 |
| 11 | 第 144 行 "位置特化… 比统一权重方案准确率**提高8-15%**" | **无来源** |
| 12 | 第 147 行 "四种算法的结果进行**集成分析**，进一步提升预测鲁棒性和可靠性" | **夸大或失实**：代码中无集成（no ensemble/voting/stacking）；`Multi_Run_Experiment_Framework_Final.py` 只做平均与最优选择 |
| 13 | 第 152 行 "**首次**将足球位置特点与机器学习权重优化相结合" | **夸大或失实**：无检索证据 |
| 14 | 第 185 行 "**首次**将四种不同范式算法应用于足球球员预测" | **夸大或失实**：无检索证据；`analysis_requirements.tex:25` 已引用 metulini2018（GA）与 singh2020（PSO）用于足球场景 |
| 15 | 第 197 行 "实现了高准确率的球员离队概率预测" | **夸大或失实**：留出集 0.7407（= 平凡基线）/0.7778（+3.7pp） |
| 16 | 第 202 行 "更新时间: 2025-08-19" | **与 README 第 133 行 "Year: 2024" 跨文档矛盾** |

### 2.19 `增强版权重优化算法解释文档.md`（143 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 5 行 "通过**遗传算法**优化各指标权重" | **夸大或失实**：实际是差分进化（`GA_..._Final.py:7`） |
| 2 | 第 15 行 "**10个核心指标**" | **文档内部自相矛盾**：本文件四个位置各列 10 项 ✓，但第 5 行称"基于…10指标评估系统"，而 `Algorithm_Modification_Documentation.md:5` 称"5个通用指标+10个位置特色指标"（即 15 项）。两文档对同一体系给出 10 与 15 两种口径 |
| 3 | 第 44 行 后卫第 3 项 "progressive_passes - 向前传球 ↗️ (**标准数据**)" | **夸大或失实**：`weight_optimization_core_updated.py` 的后卫指标中 `PrgP` 来源于 **passing** 数据集（与 `Algorithm_Modification_Documentation.md:72` 的"passing / PrgP"一致），非"标准数据" |
| 4 | 第 62 行 门将第 9 项 "shots_faced - 面对射门数" | **夸大或失实**：代码用 `SoTA`（Shots on Target Against），对应 `SoTA_weight`（`Multi_Run_...txt:109`），语义是"面对射正数"而非"面对射门数" |
| 5 | 第 70 行 `percentile_score = percentile_rank(player_value, position_players_values)` | **与代码/数据一致** |
| 6 | 第 76 行 `performance_score = Σ(percentile_score[i] × weight[i]) / Σ(weight[i])` | **与代码/数据一致**（`weight_optimization_core_updated.py:315–316`）。注意与 `Final_Algorithmic_Contribution_Summary.md:87–88` 及 `权重优化算法实验原理详解.md:98–104`（无归一化）冲突 |
| 7 | 第 81 行 `departure_probability = base_risk + (1 - performance_score) × risk_multiplier + **position_adjustment**` | **夸大或失实**：代码中无 `position_adjustment` 项（`weight_optimization_core_updated.py:326`） |
| 8 | 第 87 行 "基础风险: 0.2 - 0.4" | **夸大或失实**：真实 clip 为 [0.1, 0.3] |
| 9 | 第 92–97 行 "遗传算法优化 - 种群大小: **50**个权重配置 / 进化代数: **50**代 / 变异率: 0.15 / 交叉率: 0.8" | **夸大或失实**：最终 GA 脚本为 `maxiter=20, popsize=10`（`GA_..._Final.py:79–80`），无变异率/交叉率自定义参数。50/50/0.15/0.8 更像 `Weight_Optimization_Framework.py:308` 的 `population_size=20, generations=50` 的错误变体 |
| 10 | 第 138 行 "数据覆盖: 全部**26名**Inter球员(100%匹配率)" | **夸大或失实**：2022-2023 为 25 名（`Inter_Players_Departure_Labels.csv`），2023-2024 为 27 名（`Inter_departured_2023_2024.csv`）。**"26" 两个赛季都不是**；与 `PPT_Content_Document.md:85` 的"24名"、`多算法权重优化实验PPT汇报文档.md:68` 的"22名"三者互斥 |
| 11 | 第 141 行 "优化精度: 遗传算法 **1500+次迭代**优化" | **夸大或失实**：GA 用 `maxiter=20`；1500 是 RS 的 `n_iterations`（`RS_..._Final.py:88`） |
| 12 | 第 122 行 "整合 **8个**专业数据集的信息" | **夸大或失实**：磁盘共 8 个 `ITA_SerieA_player_*` 文件，但 `load_position_specific_data()` 只读 6 个（goal/shooting/passing/possession/defensive/goalkeeper），`load_experimental_data_enhanced()` 只读 standard + 1；且 `goalkeeper_advance` 文件从未被读取 → 实际使用 ≤6 类 |
| 13 | 第 142 行 "该算法实现了传统单一数据源模型向多维度位置专门化模型的**重大升级**" | **夸大或失实**：位置专门化体现在指标选择（`get_position_specific_metrics`），但百分位参考池仍按 `pos.str.contains` 粗分，且 2023-2024 预测使用 2022-2023 位置数据 |

### 2.20 `多算法权重优化实验PPT汇报文档.md`（246 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 第 20 行 "足球转会预测的商业价值（数十亿欧元市场）" | **无法验证**：无引用 |
| 2 | 第 68 行 "球员数量: **22名** Inter Milan核心球员" | **夸大或失实**：实测 25（2022-2023）或 27（2023-2024） |
| 3 | 第 71 行 "**实际结果: 5名球员离队，17名留队**" | **夸大或失实**：2022-2023 为 12/13；2023-2024 为 7/20。"5/17" 两赛季都不成立；且 5+17=22 与本文件第 68 行自洽，但与磁盘冲突 |
| 4 | 第 73–77 行 "位置分布：前锋4（包括Lukaku离队）、中场7（包括Brozović离队）、后卫9（包括Škriniar离队）、门将2（Onana离队，Handanovič退役）" | **夸大或失实 + 文档内部自相矛盾**：分项 4+7+9+2 = **22** ✓（与第 68 行自洽），但真实 2022-2023 为 前锋4/中场7/后卫11/门将3 = 25。**中场 7 ✓ 与真实一致，后卫 9 ✗、门将 2 ✗**；且 Lukaku/Brozović/Škriniar/Onana 的离队方向与 `Inter_Players_Departure_Labels.csv` 一致（均为 1） |
| 5 | 第 87–90 行 算法对比表：PSO 92.0%/96.0%/0.82/0.9275/100%；GA 92.0%/95.3%/0.81/0.9201；RS 92.0%/95.4%/0.80/0.9185；SA **68.4%**/83.0%/0.45/0.7842 | **无来源（疑似编造）**：与 `模型对比.txt:5–8`（PSO 0.920/0.960/0.841；SA 0.684/0.830/0.377）部分相似（SA 68.4% 与 0.684 吻合！PSO/GA/RS 的 0.92 也吻合），但 PR-AUC 与 Kappa 与 `Multi_Run_Average_Metrics_...txt:10–13`（0.9646/0.9648/0.7978/0.9616；0.8397/0.8557/0.4534/0.8395）冲突。**表头"成功率 100%"与 `模型对比.txt:5–8` 的 100.0% 一致** → 该表是两份不同磁盘结果的拼接 |
| 6 | 第 106–107 行 前锋 "进球能力 15.0%（最重要）/助攻 12.0%/出场时间 12.0%/射门精度 8.0%" | **与代码/数据冲突**：真实 PSO 前锋 `Gls_weight = 0.080`、`Ast_weight = 0.050`、`minutes_weight = 0.150`、`SoT_weight = 0.150`（`Multi_Run_...txt:38–45`）。**四项权重全部不符** |
| 7 | 第 110–113 行 中场 "关键传球 15.0%（最重要）/助攻 15.0%/出场时间 12.0%/传球成功率 5.0%" | **与代码/数据冲突**：真实为 `KP_weight = 0.080`、`Ast_weight = 0.080`、`minutes_weight = 0.150`、`Cmp_pct_weight = 0.104396`（同文件 58–65 行） |
| 8 | 第 116–119 行 "风险参数：前锋基础风险 25.7%/中场 20.0%/后卫 20.0%/门将 40.0%" | **夸大或失实**：`base_risk` 被 clip 到 [0.1, 0.3]（`weight_optimization_core_updated.py:287`），**门将 40.0% 越界不可能出现**；且论文/代码中 `base_risk` 不是优化变量 |
| 9 | 第 128–132 行 "✅ Škriniar 离队 概率 75.2% / Lukaku 68.9% / Brozović 71.3% / Bastoni 留队 82.1% / Barella 留队 79.4%" | **无来源（疑似编造）**：磁盘 2022-2023 侧无概率输出文件；Bastoni 在 2023-2024 报告中概率为 50.0%（`Inter_2023_2024_Prediction_Report_...txt`） |
| 10 | 第 135–138 行 "总体准确率 92.0% / 精确率 88.5% / 召回率 91.2% / F1 89.8%" | **与代码/数据冲突**：92.0% 与 `Single_Run_ML_Metrics_...txt:9` 的 GA 值吻合，但真实输出中 **不报告 Precision/Recall/F1**（该文件仅有 Accuracy/PR-AUC/Bal-Acc/Cohen-K/MCC/Brier）；且 2023-2024 留出集 Precision=0.0000 |
| 11 | 第 56 行 "评估方法: 每算法运行 **10次** 取平均值" | **夸大或失实**：`Multi_Run_Average_Metrics_20250826_171631.txt:4` 为 **5 次** |
| 12 | 第 176 行 "精度提升: 相比单一算法提升 **12-15%**" | **无来源**；且第 87 行表中 GA/RS 与 PSO 同为 92.0%，"提升 12-15%" 无法从该表推出 |
| 13 | 第 177 行 "效率优化: PSO算法 **3分钟内**完成优化" | **与代码/数据一致**（`Multi_Run_...txt:11` 335.34s = 5.6 分钟） | **夸大或失实**：335.34s ≈ **5.59 分钟**，超出"3分钟内" |
| 14 | 第 178 行 "稳定性强: **10次运行标准差 < 0.01**" | **夸大或失实 + 与磁盘冲突**：`模型对比.txt:7` SA 准确率标准差为 **0.099**（远大于 0.01）；`Single_Run_ML_Metrics_...txt:12` RS PR-AUC 0.9610 vs `Multi_Run_...txt:13` 0.9616（跨运行有波动）。仅 PSO/GA/RS 的 accuracy 标准差为 0.000，不能概括 |
| 15 | 第 216 行 "**首次**将多算法优化应用于足球转会预测" | **夸大或失实**：无检索证据 |
| 16 | 第 210 行 "多算法协同**显著优于**单一算法" | **夸大或失实**：真实 `模型对比.txt:5–8` 显示 GA/PSO/RS 三算法指标几乎完全相同；合成输出中 PSO vs GA 的 PR-AUC/F1/Bal-Acc 均不显著（`Statistical_Test_Results_...txt`：p=0.2836/0.5230/0.4934） |
| 17 | 第 213 行 "实用性强: **92%预测准确率**具有商业应用价值" | **夸大或失实**：把训练集内拟合值当作预测准确率；真实留出集 0.7407/0.7778 |

### 2.21 `球队数据科学家评估指标建议.md`（140 行）

| # | 声明（行号） | 判定 |
|---|---|---|
| 1 | 全文性质：面向球队数据科学家的**建议性框架**（业务指标 + 财务 ROI + 时间敏感性指标） | **与代码/数据一致（性质上）**：文档本身以"建议"口吻写作，未声称已在项目中实现。**这是本次审计中唯一没有结构性过度宣称的文档** |
| 2 | 第 7 行 "错失Lautaro vs 留下Zanotti的成本差异巨大" | **夸大或失实（数据层面）**：`Mattia Zanotti` 在 2022-2023 标签中为离队（`Inter_Players_Departure_Labels.csv:17` 值 1），"留下 Zanotti" 与现实不符；且 Zanotti 不在 2023-2024 名单中 |
| 3 | 第 8 行 "每年只有**30-40%**球员离队" | **与代码/数据一致**：2022-2023 = 12/25 = 48%；2023-2024 = 7/27 = 25.9%。区间 30–40% 覆盖不到 48%，属近似表述 |
| 4 | 第 21 行 "核心球员预测准确率… 阈值: ≥90%合格, ≥95%优秀" | **无法验证**：阈值来源无引用；且项目真实留出集 77.8% 远低于该"合格线" → 隐含地暴露了项目未达标 |
| 5 | 第 30 行 "离队预测精确率… 阈值: 精确率≥75%" | **无法验证**：阈值来源无引用；真实留出集 Precision = 0.5556（复现）/0.0000（磁盘），远低于 75% |
| 6 | 第 48 行 "Brier Score ≤0.2" | **无法验证**：阈值来源无引用；真实留出集 Brier = 0.2083（`results.tex:303`，无磁盘来源）/0.2500（磁盘），均高于 0.2 |
| 7 | 第 68 行 "最优预警阈值确定（通常 0.3-0.4 比 0.5 更有业务价值）" | **与代码/数据一致（作为建议）**：代码固定用 0.5 阈值（`2023_2024_Prediction.py:200`），该建议指出了真实可改进点 |
| 8 | 第 104–116 行 "Inter专门的评估框架"（含"青训球员培养ROI"等自制公式） | **无法验证**：公式未定义分母口径，无数据 |
| 9 | 第 140 行 "这个评估体系能够… 比单纯的准确率更能指导球队的实际决策" | **夸大或失实**：未做验证实验支持该比较 |

### 2.22 文本类结果文件（7 份）

| 文件 | 核心内容 | 判定 |
|---|---|---|
| `模型对比.txt`（14 行） | 第 1 行 "算法平均性能对比表 (基于**10次**运行)"；第 5–8 行 GA 0.920±0.000/0.953±0.000/0.841/0.193/0.923/0.852、PSO 0.920±0.000/0.960±0.009、SA 0.684±0.099/0.830±0.064、RS 0.920±0.000/0.954±0.008；第 11–13 行综合评分 PSO 0.894、RS 0.892、GA 0.892、SA 0.629 | **文档内部自相矛盾**：标题称"10次运行"，但项目唯一的真实多次运行输出 `Multi_Run_Average_Metrics_20250826_171631.txt:4` 为 5 次；且本文件各指标与 `results.tex:18–21`、`Multi_Run_...txt:10–13` 全部不同（SA Accuracy 0.684 vs 0.7280；PSO PR-AUC 0.960 vs 0.9648；Kappa 0.841 vs 0.8557）。**"平均用时"全为 0.0 秒**，说明该表来自一次快速内部评估而非论文所用的正式多轮实验 |
| `demand.txt`（36 行） | 引援预测（而非离队预测）的需求清单：第 1–10 行 "数据收集：获取Inter 2022-2023赛季**引援**数据…建立**引援**预测模型（位置需求、预算分配等）"；第 12–34 行同 | **与项目实际研究目标不符**：项目最终交付的是**球员离队预测**（`2023_2024_Prediction.py`、论文标题），本文档描述的却是**引援预测**（transfer acquisition）。全文无"离队/Departure"字样。属早期需求残留，与论文 `introduction.tex`、`design.tex` 的目标声明冲突 |
| `Multi_Run_Average_Metrics_20250826_171631.txt`（117 行） | 第 4 行 "Number of runs per algorithm: **5**"；第 10–13 行四算法六指标 + 用时；第 19–20 行 "Best Algorithm: PSO / Average Composite Score: 0.931497"；第 26–27 行 "Valid Runs: 5/5 / Success Rate: 100.0% / Average Execution Time: 335.34 ± 51.08 seconds"；第 31–113 行 PSO 在四位置的完整权重配置 | **与代码/数据一致（最高质量的可溯源结果文件）**。**这是论文 `tab:algorithm_performance`、四张权重表、以及 `results.tex:395–400` 的真实来源。** 但也是**唯一**的真实多次运行输出，且为训练集内（25 名球员）指标 |
| `Single_Run_ML_Metrics_20250826_134951.txt`（109 行） | 第 9–12 行：GA 0.9200/0.9646/0.9199/0.8397/0.8397/0.1843/862.47；PSO 0.9200/0.9646/0.9199/0.8397/0.8397/0.1810/311.66；SA 0.6400/0.7638/0.6410/0.2812/0.2821/0.2235/209.48；RS 0.9200/0.9610/0.9199/0.8397/0.8397/0.1814/312.54；第 16–19 行 "Best Algorithm: PSO / Composite Score: 0.926730" | **与代码/数据一致（可溯源）**。**关键证据价值**：GA/PSO/RS 五个指标数值完全相同（0.9200/0.9646/0.9199/0.8397/0.8397），说明三种元启发式在该小样本问题上收敛到同一解 → 直接反驳"多算法协同/算法优劣对比"的叙事。另外 PSO 的前锋配置（第 24–43 行）与 `Multi_Run_...txt` 的 PSO 前锋配置**完全不同**（如 `Gls_weight` 0.150 vs 0.080、`xG_weight` 0.150 vs 0.080），说明"最优权重"不稳定 |
| `Statistical_Test_Results_20250826_182039.txt`（5935 字符，单行转义格式） | 第 1 段单样本 t 检验（PSO/GA/SA/RS × 4 指标，含 Mean/Baseline/Cohen's d）；第 2 段配对 t 检验（6 组对比 × 4 指标）；第 3 段 Wilcoxon（6 组 × 4 指标）；第 4 段 "Significant Improvements: 16/16 / Improvement Rate: 100.0%" | **与代码一致但与真实实验无关**：其内容与 `Run_Statistical_Tests.py:24–45` 的 `np.random.normal` 输出一一对应（PSO Accuracy t=110.429/d=34.921 无 t 检验能对 n=10、σ=0.008 的真实数据产生 d>34）。**Baseline 值 0.68/0.62/0.65/0.60（第 8–9、49–51 行等）在项目的任何真实结果文件中都不存在** → 该"基线"是凭空指定常数 |
| `Statistical_Test_Results_20250831_231510.txt`（5935 字符，完全相同的转义单行格式） | 与 `..._182039.txt` 内容**逐字节相同**，仅时间戳不同 | **文档内部自相矛盾 + 强证据**：两份相隔 5 天的"统计检验结果"完全相同（5985 字符全部一致），是同一伪随机种子的重复运行，与项目期间任何真实实验进展无关。这佐证了结果的合成性质 |
| `Inter_2023_2024_Prediction_Report_20250826_172047.txt`（单行转义格式） | 第 4 行 "Total Players: 27"；第 8–19 行 Accuracy 0.7407 / Precision 0.0000 / Recall 0.0000 / F1 0.0000 / PR-AUC 0.2593 / ROC-AUC 0.5000 / Kappa 0.0000 / MCC 0.0000 / Bal-Acc 0.5000 / Brier 0.2500 / Composite 0.2787；DETAILED PREDICTION RESULTS：**全部 27 人 Position="Unknown"、Dept_Prob=50.0%、Predicted="Stayed"**；PREDICTION SUMMARY "Correct Predictions: 20/27 (74.1%) / High Risk Correct (>70%): 0 / Low Risk Correct (<30%): 0" | **与代码一致（真实运行产物）但与论文全面冲突**。**关键证据价值**：(a) 全预测留队 → 模型实际退化为平凡基线（委托方核实 20/27 = 0.7407 即平凡基线准确率）；(b) 全部 Position="Unknown" → 证明 `load_position_specific_data()` 的 2022-2023 位置数据未正确接入 2023-2024 预测，且 `position_group` 解析失败；(c) 所有概率被压到 50.0% → 与 `calculate_departure_probability_with_weights` 在 `percentile_scores` 为空时 `return 0.5`（`weight_optimization_core_updated.py:291–292`）的降级路径一致。**论文 `results.tex` 对应的三张表（metrics/errors/successes/position-specific）与本文档无任何数字交集** |

---

## 三、论文表格溯源表

| 表号 / 表名 | 论文位置 | 声明数字（示例） | 磁盘可溯源文件 | 判定 |
|---|---|---|---|---|
| `tab:seria_dataset` | `data_collection.tex:15–27` | 2022-2023: 535 人；2023-2024: 547 人；各 20 队 | `data excel\2022-2023\ITA_SerieA_player_standard_stats_2022_2023.csv`（606 行 = 3+**603**）；`2023-2024\..._standard_stats_2023_2024.csv`（619 行 = 3+**616**） | **无来源（数字错误）**：少报 68 / 69 人 |
| `tab:stat_categories` | `data_collection.tex:33–50` | 7 类统计 | 磁盘为 6 类被读取的统计（standard/shooting/goal/passing/possession/defensive/goalkeeper 中 6 类）；`weight_optimization_core_updated.py:64–121` 读 6 类 | **夸大或失实**（类别数），且与 `implementation.tex:11` 的 "six" 冲突 |
| `tab:inter_squad` | `data_collection.tex:58–74` | 门将 2 / 后卫 11 / 中场 8 / 前锋 4 / 总 25 | `Inter_Players_Departure_Labels.csv`（25 人）+ `ITA_SerieA_player_standard_stats_2022_2023.csv` 的 `pos` 列 → 门将 **3** / 后卫 11 / 中场 **7** / 前锋 4 | **无来源（分项错误）**：2 处错；总数 25 正确故自身自洽 |
| `tab:transfer_outcomes` | `data_collection.tex:78–92` | Departed 10 / Remained 15 | `data excel\2022-2023\Inter_Players_Departure_Labels.csv`：值为 1 的行 = 12（Cordaz/Onana/D'Ambrosio/Correa/Brozović/Zanotti/Škriniar/Bellanova/Gagliardini/Lukaku/Handanović/Carboni），值为 0 = 13 | **无来源（数字错误）** |
| `tab:data_completeness` | `data_collection.tex:100–116` | 98.5/8、97.2/15、96.8/17、98.1/10、97.5/13、98.3/9 | 6 个统计文件在核心指标列（`Min/Gls/Ast/CrdY/CrdR/SoT/xG/PrgP/Tkl/Int/Saves` 等）无缺失 | **无来源（疑似编造）** |
| `tab:outliers` | `data_collection.tex:128–141` | Z-score 12 人 / IQR 18 人 / 领域知识 5 人 | 无任何离群检测脚本或输出 | **无来源（疑似编造）** |
| `tab:universal_metrics` | `design.tex:78–91` | 标题 "Five universal metrics"，表内 3 行 | `weight_optimization_core_updated.py:123–130` 定义 5 项，但 `:299–301` 只用 3 项 | **文档内部自相矛盾** |
| `tab:forward_metrics` | `design.tex:99–119` | 前锋 10 指标 | `weight_optimization_core_updated.py:134+` 与 `Multi_Run_...txt:41–50` | **与代码/数据一致** |
| `tab:midfielder_metrics` | `design.tex:125–145` | 中场 10 指标（含 Tackles） | 同文件 62–71 行 | **与代码/数据一致** |
| `tab:defender_metrics` | `design.tex:151–171` | 后卫 10 指标 | 同文件 83–92 行 | **与代码/数据一致** |
| `tab:goalkeeper_metrics` | `design.tex:177–197` | 门将 10 指标 | 同文件 104–113 行 | **与代码/数据一致** |
| `tab:data_categories` | `implementation.tex:13–29` | 6 类 / 对应位置 / 关键指标 | `weight_optimization_core_updated.py:64–121`、`2023_2024_Prediction.py:29–40` | **基本一致**；但 "Shooting Statistics — Positions: Forwards" 过窄（代码对前锋读 shooting，但 shooting 文件含全联赛球员） |
| `tab:position_metrics` | `implementation.tex:47–62` | 4 位置各 5 指标 | 代码为 4 位置各 10 指标 | **夸大或失实（缩水为 5 项）**：与 `design.tex` 的 10 项表冲突 |
| `tab:ml_metrics` | `implementation.tex:124–139` | Accuracy/Precision/Recall/F1、Bal-Acc/Kappa/MCC、PR-AUC/ROC-AUC、Brier、T-test/Wilcoxon | `2023_2024_Prediction.py:219–246`（全部实现）、`Multi_Run_Experiment_Framework_Final.py:48–53` | **与代码/数据一致** |
| `tab:algorithm_performance` | `results.tex:10–24` | GA/PSO/SA/RS × (Acc, PR-AUC, Bal-Acc, Kappa, MCC, Time) | **`Multi_Run_Average_Metrics_20250826_171631.txt:10–13`（逐值一致）** | **有来源** ✅（但为 5 次而非论文第 4 行所称 10 次；且为训练集内 25 人指标） |
| `tab:sigmoid_parameters` | `results.tex:30–46` | GA 4.00/0.70/0.70；PSO 4.00/0.61/0.70；SA 1.54/0.52/0.49；RS 1.97/0.70/0.43 | **PSO 行 → `Multi_Run_...txt:33–35` ✓**；**SA 行 → `Multi_Run_...txt:96–98`（PSO 的 Goalkeeper 配置）**；**RS 行 → `Multi_Run_...txt:75–77`（PSO 的 Defender 配置）**；**GA 行 → 无法溯源** | **部分有来源 + 行标签错配**：SA/RS 两行实为 PSO 的不同位置参数 |
| `tab:one_sample_testing` | `results.tex:58–88` | 16 行 t / p / Cohen's d | 数字可在 `Statistical_Test_Results_20250826_182039.txt` / `..._20250831_231510.txt` 找到；但这些文件的生成代码为 `Run_Statistical_Tests.py:20–45` 与 `Statistical_Testing_Framework.py:72–105` 的 `np.random.normal` 合成数据 | **无来源（伪造数据源）**：形式上有文件，实质上无真实实验来源；论文第 52 行的"5 independent runs"描述与合成脚本的 `n_runs=10` 也矛盾 |
| `tab:paired_testing` | `results.tex:96–116` | PSO vs GA / PSO vs SA 各 4 指标 | 同上一行；且同输出文件中 PSO_vs_RS、GA_vs_SA、GA_vs_RS、SA_vs_RS 与所有不显著结果被删除 | **无来源 + 选择性报告** |
| `tab:wilcoxon_test` | `results.tex:124–139` | PSO-GA 3.0/0.010；PSO-SA 0.0/0.002；GA-SA 0.0/0.002；SA-RS 0.0/0.002 | 同输出文件第 3 段（6 组 × 4 指标，仅取显著项）；PSO_vs_GA accuracy W=3.0 p=0.0098 | **无来源（伪造数据源）+ 选择性报告**；论文 0.010 vs 文件 0.0098 属舍入 |
| `tab:forward_weights` | `results.tex:149–176` | 13 权重 + α/τ/rm | **`Multi_Run_Average_Metrics_20250826_171631.txt:31–50`（逐值一致）** | **有来源** ✅ |
| `tab:midfielder_weights` | `results.tex:184–211` | 同上 | **`Multi_Run_...txt:52–71`（逐值一致）** | **有来源** ✅ |
| `tab:defender_weights` | `results.tex:217–244` | 同上 | **`Multi_Run_...txt:73–92`（逐值一致）** | **有来源** ✅（但该块在源文件中属 PSO，与 `tab:sigmoid_parameters` 的 "RS" 行同值） |
| `tab:goalkeeper_weights` | `results.tex:250–277` | 同上 | **`Multi_Run_...txt:94–113`（逐值一致）** | **有来源** ✅（同上，与 "SA" 行同值） |
| `tab:prediction_metrics_2023_2024` | `results.tex:287–309` | 0.7778 / 0.5556 / 0.7143 / 0.6250 / 0.6459 / 0.4706 / 0.7571 / 0.4781 / 0.2083 / 0.6765 / 0.22 | 磁盘唯一产物 `Inter_2023_2024_Prediction_Report_20250826_172047.txt`：**0.7407 / 0.0000 / 0.0000 / 0.0000 / 0.2593 / 0.0000 / 0.0000 / 0.5000 / 0.2500 / 0.2787** | **无来源（疑似编造）**：全库 grep `0.7778\|0.5556\|0.7143\|0.6459` 在业务文件中零命中 |
| `tab:prediction_errors_2023_2024` | `results.tex:317–333` | 6 名球员及概率 0.555/0.543/0.521/0.514/0.477/0.470 | 磁盘报告中 27 人概率**全部为 50.0%** | **无来源（疑似编造）** |
| `tab:successful_predictions_2023_2024` | `results.tex:341–364` | 10 名球员及概率 0.678/0.565/0.523/0.505/0.501/0.319/0.338/0.361/0.432/0.466 | 同上，全部 50.0%；且 Klaassen/Sánchez/Audero/Agoume/Akinsanmiro 在磁盘上**被预测为 Stayed（错误）** | **无来源（疑似编造）+ 结论倒置** |
| `tab:position_specific_2023_2024` | `results.tex:370–386` | Forward 3/3 100%、Midfielder 9/7 77.8%、Defender 12/9 75.0%、GK 3/1 33.3%、Overall 27/21 77.8% | 磁盘报告所有 27 人 `Position="Unknown"`；Correct 20/27 | **无来源（疑似编造）**：位置字段在真实产物中不存在 |
| `tab:execution_sequence` | `appendix.tex:159–173` | 执行顺序 1→4 | `appendix.tex` 所列 4 个脚本均存在 | **与代码/数据一致** |
| 无编号（`design.tex:9–63` 架构图） | `design.tex` | `σ(C) + f(W*,P)`、4 组件 | `weight_optimization_core_updated.py:280–327` | **形式一致，命名夸大**（"Multi-layer ... Fusion"） |

**溯源统计**：共核查 **30** 张表 / 图。
- **有来源**（可在磁盘结果文件中逐值定位）：`tab:algorithm_performance`、`tab:forward_weights`、`tab:midfielder_weights`、`tab:defender_weights`、`tab:goalkeeper_weights`、`tab:ml_metrics`、`tab:execution_sequence`、4 张 position-metrics 表、`tab:data_categories` —— **共 12 项**
- **无来源（疑似编造）**：`tab:seria_dataset`（数字错）、`tab:inter_squad`、`tab:transfer_outcomes`、`tab:data_completeness`、`tab:outliers`、`tab:one_sample_testing`、`tab:paired_testing`、`tab:wilcoxon_test`、`tab:prediction_metrics_2023_2024`、`tab:prediction_errors_2023_2024`、`tab:successful_predictions_2023_2024`、`tab:position_specific_2023_2024` —— **共 12 项**
- **部分错配 / 内部矛盾**：`tab:sigmoid_parameters`（行标签错配）、`tab:universal_metrics`（标题 vs 表体）、`tab:position_metrics`（5 vs 10）、`tab:stat_categories`（7 vs 6） —— **共 4 项**

---

## 四、过度宣称清单

| # | 文档（行号） | 原文措辞 | 实际证据 | 判定 |
|---|---|---|---|---|
| 1 | `README.md:115` | "**92.0% prediction accuracy (35.3% improvement over baseline)**" | 论文自身留出集为 77.8%（磁盘 74.1%）；92.0% 是 25 人训练集内拟合准确率（`Single_Run_ML_Metrics_...txt:9`）；全库无任何 35.3% 的基线或计算 | **严重夸大 / 数字不可溯源** |
| 2 | `results.tex:403` | "establish the Multi-layer Probability Fusion Algorithm as a **significant advancement** in sports analytics methodology" | 核心统计结论来自 `np.random.normal` 合成数据；留出集不优于平凡基线；算法为线性加权 + sigmoid | **严重夸大** |
| 3 | `discussion_conclusion.tex:7` | "demonstrated **exceptional performance** with the PSO algorithm achieving 92.8% accuracy with 96.48% PR-AUC" | 92.8% 为 25 人训练集内拟合值；`Multi_Run_Average_Metrics_20250826_171631.txt:11` | **夸大**（把训练集拟合值当泛化性能） |
| 4 | `discussion_conclusion.tex:7` | "established the **superiority** of relative percentile ranking over traditional absolute metric approaches" | 项目从未做该对照实验；`Project_Continuity_Documentation.md:112` 明写"不需要相对百分位算法 vs 传统算法" | **无证据夸大** |
| 5 | `discussion_conclusion.tex:7` | "all optimisation algorithms showing statistically significant improvements (p < 0.001) over baseline methods" | `Statistical_Test_Results_*.txt` 的 p=0.0000 来自合成数据；真实输出中 PSO_vs_RS p=0.0811、GA_vs_RS p=0.4864 均不显著 | **夸大 / 伪造证据** |
| 6 | `discussion_conclusion.tex:5` | "a **novel** Multi-layer Probability Fusion Algorithm" | `scipy.stats.percentileofscore` + 线性加权平均 + 标准 sigmoid；无新机制 | **命名夸大** |
| 7 | `discussion_conclusion.tex:11` | "a fundamental **paradigm shift**" | 无消融实验、无对照 | **严重夸大** |
| 8 | `introduction.tex:65` | "achieving **77.8\% accuracy**" | 磁盘 `Inter_2023_2024_Prediction_Report_20250826_172047.txt` 为 0.7407；平凡基线 0.7407（20/27）；0.7778 仅 +3.7pp | **夸大**（且不可溯源） |
| 9 | `introduction.tex:67` | "**92.8\% optimisation accuracy**" | `Multi_Run_...txt:11`；训练集内 | **夸大**（术语"optimisation accuracy"具误导性） |
| 10 | `introduction.tex:40` | "Demonstrate **statistically significant improvements**… through comprehensive evaluation metrics" | 唯一显著性证据为合成数据 | **夸大 / 未达成** |
| 11 | `results.tex:90` | "Cohen's d values exceeding 24.0, indicating **exceptionally large practical significance**" | σ=0.008–0.01、n=10 的合成正态生成，d>20 是必然伪影；真实 5 次运行 PSO 与 GA/RS 差异极小 | **严重夸大（统计上不可能）** |
| 12 | `results.tex:285` | "The algorithm demonstrated **robust predictive capability**" | 磁盘产物 Precision=Recall=F1=0、PR-AUC=0.2593 < 0.5、全预测留队 | **严重夸大，与事实相反** |
| 13 | `results.tex:388` | "The model achieved **perfect accuracy for forwards**" | 该表无来源；磁盘上 Sánchez（前锋）被预测错误 | **无证据夸大** |
| 14 | `results.tex:395` | "PSO algorithm achieved 92.8% accuracy with 96.48% PR-AUC, representing the **highest performance across all algorithms**" | 与 `Multi_Run_...txt:11` 一致，但 `Single_Run_ML_Metrics_...txt:9–10` 中 GA 与 PSO 完全同值，`模型对比.txt:5–6` 中 GA/PSO/RS 同值 | **夸大**（"highest"不稳健） |
| 15 | `results.tex:398` | "Achieved 0.8557 Cohen's Kappa and 0.8563 MCC, indicating **excellent classification reliability**" | 在 25 条样本、按位置 4 分区（后卫 11 人中仅 4 离队）上，Kappa/MCC 的置信区间极宽 | **夸大** |
| 16 | `results.tex:400` | "**Composite Score Excellence**: 0.9315 composite score demonstrating balanced performance" | 0.9315 = `Multi_Run_...txt:20`；但 composite 的 40% 权重给了 PR-AUC，而 F1/Bal-Acc 高度相关 → 非独立维度，"balanced"无意义 | **夸大** |
| 17 | `results.tex:52` | "using multi-run experimental data (**5 independent runs per algorithm**)" | 实际为 `np.random.normal` 合成 10 次，`Run_Statistical_Tests.py:19–21`、`Statistical_Testing_Framework.py:72–75` | **严重失实（虚假数据来源声明）** |
| 18 | `results.tex:4` | "Each optimization algorithm was executed with **10 independent runs** using different random seeds" | `Multi_Run_Average_Metrics_...txt:4` 为 5 次；`Multi_Run_Experiment_Framework_Final.py:38` 固定 `seed(42+run_i)` | **失实** |
| 19 | `implementation.tex:143` | "underwent **rigorous validation** through… K-fold cross-validation… and comprehensive statistical significance testing against baseline methods" | 最终脚本无 KFold；统计检验基于合成数据 | **严重夸大** |
| 20 | `implementation.tex:33` | "The system implements **comprehensive data validation**… outlier detection" | 代码中无这些逻辑 | **夸大** |
| 21 | `data_collection.tex:96–98` | "completeness rates ranging from **96.8% to 98.5%**"、"only 8 missing records" | 核心指标列无缺失（100%） | **严重失实** |
| 22 | `data_collection.tex:118` | "Players with insufficient playing time were **subsequently excluded** from the analytical dataset" | 最终管线无此筛选 | **失实** |
| 23 | `data_collection.tex:126` | "Z-score analysis… identified **12 players**… IQR… **18 players**… domain knowledge… **5 additional players**" | 无检测脚本与输出 | **疑似编造** |
| 24 | `Final_Algorithmic_Contribution_Summary.md:113` | "整体准确率 72.4% → 87.9%，**+21.5%**，p < 0.01" | 无来源；且与 `Final_Algorithmic_...:172` 的 72.4% 与 `权重优化算法实验原理详解.md:370` 的 72.0% 基线互相矛盾 | **无来源夸大** |
| 25 | `Final_Algorithmic_Contribution_Summary.md:122` | "**贝叶斯优化**: 平均准确率 **0.950**，优化效率最高，全局最优保证：高概率" | `venv` 无 `skopt`，`Weight_Optimization_Framework.py:260` 回退随机搜索；贝叶斯优化从未运行；贝叶斯优化亦无全局最优保证 | **严重夸大** |
| 26 | `Final_Algorithmic_Contribution_Summary.md:139` | "Cohen's d: **1.24** (大效应量)" | 无来源；真实合成输出文件中无 1.24（有 1.095/0.210/0.226） | **无来源夸大** |
| 27 | `Final_Algorithmic_Contribution_Summary.md:167` | "跨赛季性能: **84.2%** (仅3.7%衰减)" | 真实跨赛季 0.7407（磁盘）/0.7778；84.2% 无来源 | **无来源夸大** |
| 28 | `Final_Algorithmic_Contribution_Summary.md:171–176` | "最大性能下降 **8.3%**… 鲁棒性评估: ✅ **高度鲁棒**；最大敏感性: **0.031**… ✅ 低敏感性" | 无输出文件 | **无来源夸大** |
| 29 | `Final_Algorithmic_Contribution_Summary.md:336,393` | "**高质量数据科学研究项目**"、"**具有明确算法创新、严谨实验验证、显著性能提升**" | 与磁盘证据系统性不符 | **自我评价型夸大** |
| 30 | `Weight_Optimization_Research_Results.md:196–199` | "**跨联赛验证**：英超适应性 78.6%（适应后 86.3%）、西甲适应性 81.2%（适应后 88.9%）" | 项目仅有意甲数据（`data excel\2022-2023`、`2023-2024` 全为 `ITA_SerieA_*`）；无任何英超/西甲文件或脚本 | **严重夸大 / 疑似编造** |
| 31 | `Weight_Optimization_Research_Results.md:104` | 贝叶斯优化 "**0.950** / 0.938 / 0.950 / 0.944"（前锋） | 同 #25 | **无来源夸大** |
| 32 | `Weight_Optimization_Research_Results.md:133` | 后卫最优权重 "minutes(**0.35**), progressive_passes(**0.28**), assists(0.22), goals(0.15)" | 真实后卫权重上限 0.15；且后卫指标不含 assists/goals | **无来源 + 与代码边界/指标体系双重冲突** |
| 33 | `权重优化算法实验原理详解.md:74–82` | "Lautaro Martínez… 百分位 **95.2%**；Alessandro Bastoni… 绝对进球数 **3个**… 百分位 **85.7%**" | 无百分位输出文件；后卫进球百分位 85.7% 与 Bastoni 该赛季口径矛盾 | **无来源夸大（点名到球员）** |
| 34 | `权重优化算法实验原理详解.md:374` | "**贝叶斯优化 87.9%**… 用时 **4.2s**… 效率优势明显" | 贝叶斯不可运行；4.2s 与同项目 PSO 335.3s 不在一个量级 | **严重夸大** |
| 35 | `权重优化算法实验原理详解.md:477` | "智能搜索: 贝叶斯优化 **4.2秒**内找到近似最优解" | 同 #34 | **无来源夸大** |
| 36 | `算法原理与权重计算效果说明文档.md:141` | "相比人工设定权重，预测准确率**提升15-25%**，F1分数改善**0.1-0.2**" | 无基线对照；真实留出集 F1 = 0.0 / 0.6250 | **无来源夸大** |
| 37 | `算法原理与权重计算效果说明文档.md:147` | "四种算法的结果进行**集成分析**，进一步提升预测鲁棒性和可靠性" | 代码中无集成（no ensemble） | **夸大（功能不存在）** |
| 38 | `算法原理与权重计算效果说明文档.md:152,185` | "**首次**将足球位置特点与机器学习权重优化相结合"、"**首次**将四种不同范式算法应用于足球球员预测" | 无文献检索证据；`analysis_requirements.tex:25` 已引用同类工作 | **夸大（"首次"无依据）** |
| 39 | `增强版权重优化算法解释文档.md:142` | "实现了传统单一数据源模型向多维度位置专门化模型的**重大升级**" | 2023-2024 预测使用 2022-2023 位置数据；位置字段在真实产物中全为 "Unknown" | **夸大，与事实相反** |
| 40 | `多算法权重优化实验PPT汇报文档.md:135` | "**总体准确率：92.0%**，精确率 88.5%，召回率 91.2%，F1 89.8%" | 真实输出不报 Precision/Recall/F1；留出集 Precision=0 | **无来源夸大** |
| 41 | `多算法权重优化实验PPT汇报文档.md:176` | "精度提升：相比单一算法提升 **12-15%**" | 同表 GA/RS 与 PSO 同为 92.0%，无法推出提升 | **无来源夸大** |
| 42 | `多算法权重优化实验PPT汇报文档.md:178` | "稳定性强: **10次运行标准差 < 0.01**" | `模型对比.txt:7` SA 标准差 **0.099** | **夸大，与磁盘冲突** |
| 43 | `多算法权重优化实验PPT汇报文档.md:210,216` | "多算法协同**显著优于**单一算法"、"**首次**将多算法优化应用于足球转会预测" | GA/PSO/RS 指标同值；PSO vs GA 多项不显著；"首次"无依据 | **夸大** |
| 44 | `Algorithm_Selection_Rationale.md:431,438` | "**首次**将足球位置特异性纳入权重优化算法" | 无检索证据 | **夸大** |
| 45 | `Algorithm_Selection_Rationale.md:376` | "多重比较校正避免假阳性" | 真实输出无 Bonferroni 段落 | **夸大** |
| 46 | `Algorithm_Modification_Documentation.md:92–136` | "复杂合同算法"（4 维修正 + 租借特殊处理） | 代码中无 `calculate_contract_risk_adjustment`；合同数据从未传入 | **功能不存在的夸大** |
| 47 | `Algorithm_Modification_Documentation.md:364–366` | "为球员离队预测提供了更加精确和实用的解决方案"、"所有代码经过精心设计，**确保逻辑正确性和可执行性**" | 合同数据未传入；`load_position_specific_data` 全 `except: pass`；2023-2024 用 2022-2023 位置数据 | **夸大，与事实相反** |
| 48 | `Project_Continuity_Documentation.md:259–260` | "项目转化状态: ✅ 成功… **证据**: 明确的算法贡献点 + 系统的验证框架 + 完整的方法论" | 验证框架无输出；贝叶斯不可运行 | **夸大** |
| 49 | `Project_Continuity_Documentation.md:247` | "算法创新状态: ✅ **完成** - 所有核心算法已实现并文档化" | 与同文件第 251 行"实验验证待执行"矛盾；贝叶斯不可运行 | **夸大 + 内部矛盾** |
| 50 | `README.md:104` | "**Academic Rigor**: Comprehensive literature review, **statistical validation**, and methodological soundness" | 统计验证基于合成数据；`references.bib` 不存在（引用全部无法解析） | **严重夸大** |
| 51 | `README.md:113` | "Algorithmic Innovation: **Novel** percentile-based feature engineering algorithm" | 直接调用 `scipy.stats.percentileofscore` | **命名夸大** |
| 52 | `README.md:141` | "approximately **40,000 words** of original research" | 实测正文合计 **10,749 词** | **夸大 3.7 倍** |
| 53 | `README.md:61–100` | 各章 5,500 / 6,200 / 5,800 / 5,000 / 6,500 / 6,200 / 5,800 词 | 实测 930 / 1781 / 2186 / 1062 / 1442 / 2098 / 720 | **夸大 4–8 倍** |
| 54 | `main.tex:43` | PDF 标题 "**Multi-layer Probability Fusion Algorithm**" | 实现为线性加权 + sigmoid | **命名夸大** |
| 55 | `analysis_requirements.tex:27` | "The application of Bayesian optimisation to sports analytics parameter tuning represents a **novel contribution** of this research" | 贝叶斯优化从未进入最终研究且不可运行 | **夸大（声称不存在的贡献）** |
| 56 | `design.tex:149,175` | Defender/Goalkeeper "through **ten specialised metrics**" | 代码确实 10 项 ✓ | **一致**（列此以对照） |
| 57 | `增强版权重优化算法解释文档.md:141` | "优化精度: 遗传算法 **1500+次迭代**优化" | GA 为 `maxiter=20`（`popsize=10`，总评估约 3200 次函数调用，但"迭代"≠"评估"）；1500 是 RS 的参数 | **夸大 / 参数张冠李戴** |
| 58 | `增强版权重优化算法解释文档.md:138` | "数据覆盖: 全部 **26名** Inter球员(**100%匹配率**)" | 2022-2023 = 25 名，2023-2024 = 27 名；"26" 不存在 | **失实** |
| 59 | `PPT_Content_Document.md:298–304` | GA 最优（PR-AUC 0.7245 / 综合 0.6895），PSO 次之（0.6324） | 与 `results.tex` 的 PSO 最优（0.9648/0.9315）及 `模型对比.txt` 全部冲突 | **无来源夸大 + 结论对立** |
| 60 | `算法原理与权重计算效果说明文档.md:74,168` | SA "**理论上保证找到全局最优解**" | 代码用指数冷却 0.95，无对数冷却，无收敛保证 | **夸大** |

---

## 五、文档内部矛盾清单

### 5.1 单文档内部矛盾

| # | 文档 | 矛盾内容 | 位置 |
|---|---|---|---|
| 1 | `data_collection.tex` | 第 31 行 "**seven** comprehensive statistical categories" vs 第 98 行与 `tab:data_completeness` 只列 6 类；同项目 `implementation.tex:11` 写 "**six**" | 31 vs 98 / 100–116 |
| 2 | `data_collection.tex` | 第 56 行 "25 players" vs `tab:inter_squad` 分项 2+11+8+4=25（自洽）但第 76 行 "10 departed, 15 remained"（和 = 25，自洽）—— 三处都与真实数据不符，但**内部彼此自洽**，属于"一致地错误" | 56 / 66–69 / 86–87 |
| 3 | `data_collection.tex` | 第 126 行 Z-score 12 人 + IQR 18 人 + 领域知识 5 人 = 35 人次，而数据集仅 535（论文口径），且第 142 行称"no outliers removed" —— "识别 35 人却完全不处理"缺乏解释 | 126 vs 142 |
| 4 | `design.tex` | `tab:universal_metrics` 标题 "**Five** universal metrics" vs 表内仅 3 行 vs 第 93 行注 "Age and Contract expiry date are **excluded**" → 应为 3 | 76 vs 82–90 vs 93 |
| 5 | `analysis_requirements.tex` | 第 34–60 行详细推导经典 GA 的**轮盘赌选择 + 算术交叉 + 高斯变异**，第 62–68 行突然说 "the GA utilizes **differential evolution** as the underlying mechanism" 并给出 DE 供体向量公式 | 34–60 vs 62–68 |
| 6 | `analysis_requirements.tex` | 第 27 行称贝叶斯优化是"本研究的 novel contribution"，但第 30–206 行全文只介绍 GA/PSO/SA/RS 四种，无贝叶斯章节 | 27 vs 32–206 |
| 7 | `analysis_requirements.tex` | 第 105–111 行给出惯性权重 `w: 0.9→0.4` 的线性递减公式，而 `implementation.tex:84` 说 "inertia weight **w=0.7**"（固定） | 105–111 vs 84 |
| 8 | `implementation.tex` | 第 86 行 "Cognitive and social coefficients **both set to 1.5**" 紧接 "optimal PSO performance occurs when **$c1 + c2 ≈ 4.0$**" —— 1.5+1.5=3.0 | 86 |
| 9 | `implementation.tex` | 第 47–62 行 `tab:position_metrics` 每位置仅 **5** 指标，而 `design.tex` 四张表各 **10** 指标，代码也是 10 | 47–62 vs `design.tex:99–197` |
| 10 | `implementation.tex` | 第 74 行 "reduction from the original **17-parameter** space"，但第 70 行与 `design.tex:358`、`introduction.tex:63` 都说 16；且磁盘无 17 参数版本 | 74 vs 70 |
| 11 | `implementation.tex` | 第 98 行 "Random Search with **50% more evaluations than other algorithms**" vs 第 82 行 PSO 30×50=1500、第 90–92 行 SA 1000 → 1500 不比 SA 多 50%，也不比 GA 多 | 98 vs 78–92 |
| 12 | `results.tex` | 第 4 行 "**10** independent runs" vs 第 52 行 "**5** independent runs per algorithm"（且磁盘为 5） | 4 vs 52 |
| 13 | `results.tex` | `tab:sigmoid_parameters` 中 SA 行 (1.54/0.52/0.49) 与 `tab:goalkeeper_weights` 的 α/τ/rm (1.541/0.519/0.492) 是同一组数；RS 行 (1.97/0.70/0.43) 与 `tab:defender_weights` 的 (1.970/0.700/0.433) 是同一组数 —— 同一参数被标为两个不同算法 | 40–41 vs 272–274；41 vs 239–241 |
| 14 | `results.tex` | 第 48 行 "The **PSO** algorithm achieved optimal performance with maximum sigmoid steepness (α=4.00) and moderate inflection point (τ=0.61)" vs 第 239–241 行/272–274 行同为"PSO"却是 1.97/1.54 与 0.70/0.519 | 48 vs 239–241 / 272–274 |
| 15 | `results.tex` | 第 90 行 "All algorithms demonstrated statistically significant improvements over baseline across all metrics (p<0.001)" vs 第 118 行 "PSO and GA showed comparable performance… similar performance in other metrics"（后者暗示不显著），且同文件合成输出含多项 "Not Significant" | 90 vs 118 |
| 16 | `results.tex` | 第 335 行 "Four players were incorrectly predicted to depart but remained, while two players were incorrectly predicted to remain but actually departed"（FP=4, FN=2）vs 第 301–302 行 Balanced Accuracy 0.7571 与 Cohen's Kappa 0.4706 —— 由 TP=5/FP=4/FN=2/TN=16 计算得 Bal-Acc=(5/7+16/20)/2=0.7571 ✓、Kappa=0.4706 ✓（此处自洽，仅作对照说明该表内部计算正确） | 295–303 vs 335 |
| 17 | `results.tex` | 第 395 行 92.8% accuracy（PSO）与 `tab:prediction_metrics_2023_2024` 的 0.7778 在同一"Results Summary"中被并列称为成就，但前者是训练集内指标、后者是留出集指标，未加区分 | 395 vs 295 |
| 17b | `results.tex` | 第 400 行 composite = **0.9315**（来自 `Multi_Run_...txt:20`）vs 用 `tab:algorithm_performance` 的 PSO 行自行代入 `0.4×0.9648 + 0.3×F1 + 0.2×0.9276 + 0.1×(1−0.1832)`，其中 F1 由同文件 `Statistical_Test_Results_*.txt` 的合成 Mean=**0.9178** 给出 → **0.92774**，而非 0.9315。两者不一致，说明论文混用了"合成数据的 F1"与"真实运行的其他指标" | 400 vs 18–21 与 `Statistical_Test_Results_20250826_182039.txt` |
| 18 | `results.tex` | 第 400 行 "0.9315 composite score" vs `tab:algorithm_performance` 中 PSO 的 Accuracy 0.9280 —— composite 高于 accuracy 在数学上可行，但论文未说明 composite 定义在本表缺失（表中无 composite 列） | 400 vs 18–21 |
| 19 | `discussion_conclusion.tex` | 第 7 行 "statistically significant improvements (p < 0.001)" + "exceptional performance" vs 第 19 行 "The limited sample size of **25 players** constrains **statistical power**" | 7 vs 19 |
| 20 | `discussion_conclusion.tex` | 第 5 行 "successfully accomplished **all** primary objectives" vs 第 17–19 行 Limitation 列出多重未达成 | 5 vs 17–19 |
| 21 | `README.md` | 第 12–22 行文件结构含 8 个 `.tex`（无 `appendix.tex`）vs 实际 9 个 `.tex` | 12–22 |
| 22 | `README.md` | 第 44–50 行 "bibtex main" vs `main.tex:3–7` `backend=biber` | 44–50 vs `main.tex:3–7` |
| 23 | `README.md` | 第 31–35 行依赖含 `listings, xcolor, algorithm, algpseudocode` vs `main.tex:10–26` 未加载 | 31–35 vs `main.tex:10–26` |
| 24 | `README.md` | 第 122 行 "All chapters are modular and **can be compiled independently**" vs 各章使用 `\section` 且无 `\documentclass` | 122 |
| 25 | `README.md` | 第 123 行 "Code listings are properly formatted with **syntax highlighting**" vs 全文无 `lstlisting`/`minted` | 123 |
| 26 | `README.md` | 第 133 行 "Year: **2024**" vs 同项目多数文档署 2025（`Project_Continuity_Documentation.md:302`、`Final_Algorithmic_Contribution_Summary.md:400`、`算法原理与权重计算效果说明文档.md:202`） | 133 |
| 27 | `README.md` | 第 115 行 "92.0% prediction accuracy" vs 第 61–100 行章节描述（第 6 章关键词是"Individual player predictions and ground truth validation"）—— 未说明 92.0% 与论文 77.8% 的关系 | 115 vs 90 |
| 28 | `Algorithm_Modification_Documentation.md` | 第 5 行 "**5个通用指标+10个位置特色指标**" vs 实际生效 3 通用 + 10 位置 | 5 vs `weight_optimization_core_updated.py:299–301` |
| 29 | `Algorithm_Modification_Documentation.md` | 第 311 行 `"positions_analyzed": ["Forward","Midfielder","Defender"]` vs 第 139 行"守门员"也包含在内 | 311 vs 139 |
| 30 | `Algorithm_Modification_Documentation.md` | 第 228–243 行 `bounds` 含 `Contract_expires_weight` 与 `base_risk` vs 第 5、13 行及 `*_Final.py` 的实际边界（无 contract，用 alpha/tau） | 228–243 |
| 31 | `Algorithm_Modification_Documentation.md` | 第 152 行 "使用**差分进化**算法" vs 第 187–196 行标题 "GA_Weight_Optimization_Experiment_Updated.py (**遗传算法**)" 并称"使用差分进化作为遗传算法**变体**" —— 同一文档内既承认是 DE 又坚持称 GA | 152 vs 187–196 |
| 32 | `Final_Algorithmic_Contribution_Summary.md` | 第 167 行 "跨赛季性能: **84.2%**" vs 第 215 行 "时间泛化稳定性: **96.3%** (3.7%衰减)" —— 两处衰减都写 3.7% 但数值不同 | 167 vs 215 |
| 33 | `Final_Algorithmic_Contribution_Summary.md` | 第 44 行 "三种互补的权重优化算法" 并在第 46–74 行列 3 个，但第 120–125 行的对比表含 **4** 行（多出"随机搜索"） | 44 vs 120–125 |
| 34 | `Final_Algorithmic_Contribution_Summary.md` | 第 135 行单侧假设 `H1: μ_opt − μ_base > 0` vs 第 137–139 行报告双侧 p 与 "Cohen's d: 1.24"（未给 n/df） | 135 vs 137–139 |
| 35 | `Final_Algorithmic_Contribution_Summary.md` | 第 87–88 行 `performance_score = sum(percentile_features[f] * optimized_weights[f+'_weight'])`（**无归一化**）vs `design.tex:314`、`增强版权重优化算法解释文档.md:76`（**有归一化** `Σw`） | 87–88 |
| 36 | `Weight_Optimization_Research_Results.md` | 第 91 行位置分组 "前锋(4)、中场(**8**)、后卫(11)、门将(**2**)" vs 真实 7 / 3 | 91 |
| 37 | `Weight_Optimization_Research_Results.md` | 第 133 行 后卫最优权重含 `assists`/`goals` vs 第 130–133 行自称的"后卫位置"指标体系（且代码后卫 10 指标不含这两项） | 133 vs `weight_optimization_core_updated.py:132+` |
| 38 | `Weight_Optimization_Research_Results.md` | 第 181 行 "贝叶斯优化 O(n³)" vs 第 225 行（`Final_Algorithmic_Contribution_Summary.md`）"贝叶斯优化 O(t³)" —— 同一概念两个符号 | 181 |
| 39 | `权重优化算法实验原理详解.md` | 第 19–21 行 "均匀权重（如各占 **20%**）" vs 第 368 行基线准确率 72.0% vs 第 370 行"均匀权重基线 72.0%" vs `Final_Algorithmic_...:172` 基线 72.4% vs `Weight_Optimization_Research_Results.md:172` 72.4% —— 同一"均匀权重基线"有三个值（20%/72.0%/72.4%） | 19–21 / 370 vs 172 |
| 40 | `权重优化算法实验原理详解.md` | 第 98–104 行示例代码无归一化除法 vs `design.tex:314` 有 | 98–104 |
| 41 | `权重优化算法实验原理详解.md` | 第 107 行 `base_risk = weights['base_risk']`（优化变量）vs 第 626 行 "权重约束: 特征权重和接近1.0" vs 真实 `base_risk` 由 sigmoid 计算且被 clip | 107 vs 626 vs `weight_optimization_core_updated.py:286–287` |
| 42 | `权重优化算法实验原理详解.md` | 第 124–148 行目标函数为 "最大化预测准确率" vs 真实 composite（PR-AUC 40%） | 124–148 |
| 43 | `权重优化算法实验原理详解.md` | 第 319 行 `positions = [...]; # 排除门将` vs 第 384 行开始逐位置分析但仍含门将相关（且第 411 行后卫）—— 示例代码与实际研究范围矛盾；同文件第 294 行称 25 名 Inter 球员含 4 位置 | 319 vs 294 |
| 44 | `权重优化算法实验原理详解.md` | 第 373–374 行 "遗传算法 +15.5% / 贝叶斯 +15.9%" 与第 387/401/415 行 "+26.7%/+17.9%/+18.8%" 与第 472 行 "平均改进: **22.1%**" —— 22.1% 既非 15.9% 也非三者均值（(26.7+17.9+18.8)/3=21.1%） | 373–374 / 387–415 / 472 |
| 45 | `权重优化算法实验原理详解.md` | 第 414 行 后卫最优来自**网格搜索** vs 第 548–550 行 "网格搜索全面: 提供全局最优基准参考"（定位为基准而非最优）vs 第 560–564 行 A 级贡献把网格搜索列为贡献 | 414 vs 548–550 |
| 46 | `增强版权重优化算法解释文档.md` | 第 5 行 "10指标评估系统" vs `Algorithm_Modification_Documentation.md:5` 的 "5+10" | 5 |
| 47 | `增强版权重优化算法解释文档.md` | 第 92–97 行 GA 参数 "种群 50 / 代数 50 / 变异率 0.15 / 交叉率 0.8" vs `GA_..._Final.py:79–80` 的 `maxiter=20, popsize=10`（且 DE 无用户设定交叉率） | 92–97 |
| 48 | `增强版权重优化算法解释文档.md` | 第 81 行公式含 `+ position_adjustment` vs `weight_optimization_core_updated.py:326` 无该项 | 81 |
| 49 | `增强版权重优化算法解释文档.md` | 第 87 行 "基础风险: 0.2 - 0.4" vs 代码 clip [0.1, 0.3] | 87 |
| 50 | `增强版权重优化算法解释文档.md` | 第 44 行 后卫 `progressive_passes` 标为"标准数据" vs `Algorithm_Modification_Documentation.md:72` 标为"passing" | 44 |
| 51 | `多算法权重优化实验PPT汇报文档.md` | 第 68 行 "22名" + 第 71 行 "5离队/17留队" + 第 73–77 行分项 4+7+9+2=22（三处自洽）vs 第 56 行"每算法运行**10次**"（而真实为 5 次） | 68–77 vs 56 |
| 52 | `多算法权重优化实验PPT汇报文档.md` | 第 87 行表 "PSO **92.0%** / PR-AUC 96.0% / Kappa 0.82" vs 第 93 行 "PSO算法表现最佳，综合评分 **0.9275**" vs 第 177 行 "PSO算法**3分钟内**完成优化"（真实 5.59 分钟）vs 第 178 行 "10次运行标准差<0.01"（真实 SA σ=0.099） | 87 / 93 / 177 / 178 |
| 53 | `多算法权重优化实验PPT汇报文档.md` | 第 116–119 行 "门将基础风险: **40.0%**" vs 代码 clip 上限 0.3 | 119 |
| 54 | `多算法权重优化实验PPT汇报文档.md` | 第 106–113 行前锋/中场权重（进球 15%、助攻 12%、KP 15%）vs `Multi_Run_...txt:41–50,58–65`（Gls 0.080、Ast 0.050、KP 0.080） | 106–113 |
| 55 | `算法原理与权重计算效果说明文档.md` | 第 17 行 "**9项**机器学习指标" vs 第 38 行 "适应度函数（综合**9项**ML指标）" vs 真实适应度仅 4 项加权 | 17/38 |
| 56 | `算法原理与权重计算效果说明文档.md` | 第 34 行（GA 用微分进化）+ 第 166 行（GA 代表进化计算）+ 第 74 行（SA 保证全局最优）—— 与第 5 行"四算法"口径下 `results.tex` 的 GA 命名冲突 | 34 vs 5 |
| 57 | `算法原理与权重计算效果说明文档.md` | 第 106 行公式漏 `1 −`（`base_risk + (加权综合百分位分数) × risk_multiplier`）vs 第 117 行"性能-风险反比关系"的描述文字 —— 公式与文字互相矛盾 | 106 vs 117 |
| 58 | `算法原理与权重计算效果说明文档.md` | 第 109–110 行 base_risk (0.2–0.4) vs 代码 [0.1,0.3] | 109–110 |
| 59 | `Project_Continuity_Documentation.md` | 第 247 行 "算法创新状态: ✅ **完成**" vs 第 251 行 "实验验证状态: 📋 **待执行**" | 247 vs 251 |
| 60 | `Project_Continuity_Documentation.md` | 第 135–142 行 "**已完成**验证框架… ✅" vs 第 251 行 "待执行" 与第 303 行 "实验验证待执行" | 135–142 vs 251,303 |
| 61 | `Project_Continuity_Documentation.md` | 第 238 行 `skiprows = 3`（列为全局"数据加载参数"）vs 位置数据读取用 `skiprows=2`（`weight_optimization_core_updated.py:68`）；主数据读取确实用 3，故属口径不完整 | 238 vs `weight_optimization_core_updated.py:24` 与 `:68` |
| 62 | `Project_Continuity_Documentation.md` | 第 13–14 行路径 `F:\Samuel\学习\final project\` vs 实际 `F:\Samuel\football recruitment\final project\`（第 212–213 行重复错误） | 13–14 / 212–213 |
| 63 | `Project_Continuity_Documentation.md` | 第 32 行 "三种互补优化算法（贝叶斯、遗传、网格）" vs 第 131 行另有 "随机搜索基线算法 ✅" → 实际列了 4 个 | 32 vs 131 |
| 64 | `Project_Continuity_Documentation.md` | 第 256 行 "**8份**核心技术文档" vs 第 91–95 行只列 5 份文档清单 | 256 vs 91–95 |
| 65 | `PPT_Content_Document.md` | 第 85 行 "国米球员：**24名**" vs 第 300–303 行算法结果（Accuracy 0.7083 = 17/24）自洽于 24，但真实为 25/27 | 85 vs 300–303 |
| 66 | `PPT_Content_Document.md` | 第 247 行 Cohen's Kappa "权重：用于综合评分" vs 第 299–303 行 composite 公式不含 Kappa | 247 vs 299–303 |
| 67 | `PPT_Content_DOCUMENT.md` | 结论"GA 最优"（第 298–304 行）与同项目 `多算法权重优化实验PPT汇报文档.md`（PSO 最优）及 `results.tex`（PSO 最优）对立 —— 跨文档矛盾，但两份 PPT 文档本身各自自洽 | 298–304 |
| 68 | `Algorithm_Selection_Rationale.md` | 第 39 行 "**12-15个**权重参数" vs 第 42 行 "仅有**24名**球员" vs 第 300–303 行 "GA: 中等复杂度"（实际评估次数最高） | 39 / 42 / 300–303 |
| 69 | `Algorithm_Selection_Rationale.md` | 第 431 行 "首次将足球位置特异性纳入权重优化算法" vs 第 407–414 行引用的 `metulini2018modelling`（GA 用于阵容/位置优化） | 431 vs 407–414 |
| 70 | `球队数据科学家评估指标建议.md` | 第 7 行 "留下 **Zanotti**" vs `Inter_Players_Departure_Labels.csv:17`（Mattia Zanotti 标签为 1，即离队） | 7 |

### 5.2 跨文档矛盾（同一事实的不同说法）

| # | 事实 | 各文档说法 | 真实情况 |
|---|---|---|---|
| 1 | **联赛球员总数（2022-2023）** | `data_collection.tex:13,23` = 535；`Final_Algorithmic_Contribution_Summary.md:104` = 535；`Weight_Optimization_Research_Results.md:89` = 535；`权重优化算法实验原理详解.md:292,310` = 535；`PPT_Content_Document.md:84` = "500+"; `introduction.tex:61` = "535+" | **603**（606 行 − 3 表头） |
| 2 | **联赛球员总数（2023-2024）** | `data_collection.tex:13,24` = 547 | **616**（619 行 − 3 表头） |
| 3 | **Inter 球员数** | `data_collection.tex:56,71` = 25；`Weight_Optimization_Research_Results.md:90` = 25；`权重优化算法实验原理详解.md:294` = 25；`Final_Algorithmic_Contribution_Summary.md:105` = 25；`Project_Continuity_Documentation.md:98` = 25；`Algorithm_Selection_Rationale.md:42,307` = **24**；`PPT_Content_Document.md:85,101` = **24**；`多算法权重优化实验PPT汇报文档.md:68,186` = **22**；`增强版权重优化算法解释文档.md:138` = **26**；`算法原理与权重计算效果说明文档.md` 未给数 | **25**（2022-2023）；**27**（2023-2024） |
| 4 | **Inter 位置分布** | `data_collection.tex:56,66–69` = GK2/DF11/MF8/FW4；`Weight_Optimization_Research_Results.md:91` = FW4/MF8/DF11/GK2；`多算法权重优化实验PPT汇报文档.md:73–77` = FW4/MF7/DF9/GK2；`Algorithm_Modification_Documentation.md:315` = FW4 | **GK3 / DF11 / MF7 / FW4** |
| 5 | **离队 / 留队** | `data_collection.tex:76,86–87` = 10/15；`多算法权重优化实验PPT汇报文档.md:71` = 5/17 | 2022-2023: **12/13**；2023-2024: **7/20** |
| 6 | **算法集合** | 论文（`introduction.tex:20` 等）= **GA/PSO/SA/RS**（4 个）；`Final_Algorithmic_Contribution_Summary.md:44–74`、`Weight_Optimization_Research_Results.md:38–82`、`权重优化算法实验原理详解.md:30–33`、`Project_Continuity_Documentation.md:32,61–65` = **贝叶斯/GA/网格搜索**（+随机搜索）；`PPT_Content_Document.md:386` 把贝叶斯列为**未来工作** | 最终代码为 **GA(差分进化)/PSO/SA/RS** 4 个，贝叶斯未运行 |
| 7 | **多次运行次数** | `results.tex:4` = 10；`results.tex:52` = 5；`Algorithm_Selection_Rationale.md:359,385` = 10；`多算法权重优化实验PPT汇报文档.md:56` = 10；`模型对比.txt:1` = 10 | **5**（`Multi_Run_Average_Metrics_20250826_171631.txt:4`） |
| 8 | **通用指标数量** | `design.tex:76` = "five"（表内 3）；`implementation.tex:70` = 3 项（minutes/yellow/red）；`Algorithm_Modification_Documentation.md:21` = 5；`算法原理与权重计算效果说明文档.md` 未给数 | 定义 5、**实际参与加权 3** |
| 9 | **统计类别数** | `data_collection.tex:31` = seven；`implementation.tex:11` = six；`introduction.tex:61` = six；`design.tex:22` = "Six Statistical Categories"；`增强版权重优化算法解释文档.md:122` = "8个专业数据集" | 磁盘 8 个 `ITA_SerieA_player_*` 文件；代码读 **6** 类 |
| 10 | **ML 指标数量** | `算法原理与权重计算效果说明文档.md:17` = 9；`implementation.tex:124–139` = 5 大类/约 10 项；`多算法权重优化实验PPT汇报文档.md:45,212` = "5个ML核心指标"；`results.tex:16` 表含 6 列 | 代码输出 **6–10** 项（`Multi_Run_...txt:8` 6 列；`2023_2024_Prediction.py:237–246` 10 项） |
| 11 | **GA 是遗传算法还是差分进化** | 论文全篇 = "Genetic Algorithm"；`analysis_requirements.tex:62` = "utilizes differential evolution"；`Algorithm_Modification_Documentation.md:152,191` = 差分进化；`Algorithm_Selection_Rationale.md:72` = `differential_evolution`；`算法原理与权重计算效果说明文档.md:34` = "微分进化策略" | **`scipy.optimize.differential_evolution`**（`GA_..._Final.py:7`），非经典 GA |
| 12 | **PSO 惯性权重** | `analysis_requirements.tex:105–111` = 0.9→0.4 线性递减；`implementation.tex:84` = 0.7 固定；`Algorithm_Selection_Rationale.md:124` = 0.7 | **固定 w=0.7**（`PSO_..._Final.py:73`） |
| 13 | **GA 参数** | `implementation.tex:78` = pop 10 / 20 代 / F=0.8 / CR=0.7；`Algorithm_Selection_Rationale.md:76–78` = maxiter 20 / popsize 10 / seed 42；`增强版权重优化算法解释文档.md:92–97` = 种群 50 / 50 代 / 0.15 / 0.8；`PPT_Content_Document.md:194` = 种群 10 / 迭代 20；`权重优化算法实验原理详解.md:223–224` = maxiter 50 / popsize 20；`Weight_Optimization_Research_Results.md:57–62` = maxiter 50 / popsize 20；`Final_Algorithmic_Contribution_Summary.md:59–64` = maxiter 50 / popsize 20 | **`maxiter=20, popsize=10`**（`GA_..._Final.py:79–80`），无 F/CR 显式设置 |
| 14 | **基线准确率** | `算法原理与权重计算效果说明文档.md` 未给；`权重优化算法实验原理详解.md:370` = 72.0%；`Weight_Optimization_Research_Results.md:172` = 72.4%；`Final_Algorithmic_Contribution_Summary.md:113` = 72.4%；`Statistical_Test_Results_*.txt` = 0.6800（Accuracy）；`results.tex:104–107`（合成）= PSO vs GA | 五个不同值（72.0/72.4/0.68/0.62/0.65…），**无一可溯源**；真实平凡基线 = 0.7407 |
| 15 | **跨赛季泛化准确率** | `Weight_Optimization_Research_Results.md:191` = 84.2%；`Final_Algorithmic_Contribution_Summary.md:167` = 84.2%；`Final_Algorithmic_Contribution_Summary.md:215` = 96.3% | 磁盘 **0.7407**；复现 **0.7778** |
| 16 | **最优算法** | `results.tex:395` = PSO；`多算法权重优化实验PPT汇报文档.md:93` = PSO；`PPT_Content_Document.md:298–304` = **GA**（PSO 第二）；`Final_Algorithmic_Contribution_Summary.md:122` = **贝叶斯**；`Weight_Optimization_Research_Results.md:104` = **贝叶斯**；`权重优化算法实验原理详解.md:374` = **贝叶斯**；`模型对比.txt:11` = PSO（但 RS/GA 仅差 0.002） | `Multi_Run_...txt:19` = PSO；但 `Single_Run_ML_Metrics_...txt:9–10` 中 GA 与 PSO **完全相同**，`模型对比.txt:5–8` 中 GA/PSO/RS 完全相同 |
| 17 | **最优权重上限** | `results.tex`、`*_Final.py` = 0.15；`Weight_Optimization_Research_Results.md:107–116,133` = 0.387 / 0.35 / 0.28 / 0.22 | **0.15**（`PSO_..._Final.py:34,46`） |
| 18 | **base_risk 范围** | `design.tex:307` = [0.1, 0.3]；`算法原理与权重计算效果说明文档.md:109` = [0.2, 0.4]；`增强版权重优化算法解释文档.md:87` = [0.2, 0.4]；`Algorithm_Modification_Documentation.md:241` = [0.2, 0.4]；`多算法权重优化实验PPT汇报文档.md:119` = 门将 40.0% | **[0.1, 0.3]**（`weight_optimization_core_updated.py:287`），且 `base_risk` 不是优化变量 |
| 19 | **位置指标数** | `design.tex` 4 表各 10 项；`implementation.tex:47–62` 各 5 项；`增强版权重优化算法解释文档.md` 各 10 项；`Algorithm_Modification_Documentation.md:32–88` 各 10 项 | **各 10 项** |
| 20 | **数据完整性** | `data_collection.tex:96–98` = 96.8%–98.5%；`多算法权重优化实验PPT汇报文档.md:70` = "数据完整性: 100%匹配成功"；`增强版权重优化算法解释文档.md:138` = "100%匹配率" | 核心列 **无缺失（100%）**，与 `data_collection.tex` 冲突；"匹配率"与"完整度"是不同概念，被三处混用 |
| 21 | **年份** | `README.md:133` = 2024；`Project_Continuity_Documentation.md:302` = 2025年1月；`Final_Algorithmic_Contribution_Summary.md:400` = 2025；`算法原理与权重计算效果说明文档.md:202` = 2025-08-19；`Algorithm_Modification_Documentation.md:306` = 2025-08-26 | 项目产物时间戳为 2025-08（`Multi_Run_Average_Metrics_20250826_*.txt` 等） |
| 22 | **研究目标** | 论文/`2023_2024_Prediction.py` = **球员离队预测**；`demand.txt:1–34` = **引援预测**（"获取Inter 2022-2023赛季引援数据…建立引援预测模型（位置需求、预算分配等）"） | 最终交付为离队预测 |
| 23 | **工作目录** | `Project_Continuity_Documentation.md:13–14,212–213` = `F:\Samuel\学习\final project\` | 实际 `F:\Samuel\football recruitment\final project\` |
| 24 | **Word 总量** | `README.md:141` = 40,000；第 61–100 行分章合计 = 41,000 | 实测 **10,749**（8 个 tex 合计） |

---

## 六、不确定 / 需人工复核清单

| # | 事项 | 为什么无法判定 | 建议复核方式 |
|---|---|---|---|
| 1 | **0.7778 / 21/27 的最终归属** | 委托方在 venv 中精确复现出 Accuracy=0.7778、TP=5/FP=4/FN=2/TN=16、PR-AUC=0.6459，但**磁盘上任何现存脚本的原始输出都是 0.7407（全预测留队）**。存在三种可能：(a) 论文数据来自一份已被覆盖的脚本版本；(b) 论文数据来自委托方本次修正后的重跑；(c) 论文数据为手工填写 | 比对 `__pycache__\2023_2024_Prediction.cpython-311.pyc`（14,554 字节）与当前 `.py` 源码的差异；检查是否存在 `.py.bak`/历史版本；核对论文提交时间与 `Inter_2023_2024_Prediction_Report_20250826_172047.txt`（2025-08-26 17:20:47）的先后 |
| 2 | **`results.tex` 留出集各表的原始生成记录** | `tab:prediction_metrics_2023_2024` / `tab:prediction_errors_2023_2024` / `tab:successful_predictions_2023_2024` / `tab:position_specific_2023_2024` 的数字在磁盘零命中，且磁盘报告的位置字段全为 "Unknown" —— 需确认论文表格是否来自某次未落盘的运行 | 检查 `%TEMP%`、`Inter_Defenders_Analysis\`、`Inter_Forwards_Analysis_Fixed\`、`Inter_Midfielders_Analysis\` 等子目录内是否有遗漏的输出；检查 `.idea\`、`语音转写\` 是否有记录 |
| 3 | **`tab:sigmoid_parameters` 的 GA 行（4.00/0.70/0.70）来源** | `Multi_Run_Average_Metrics_...txt` 只保存了 PSO 的四位置权重，未保存 GA/SA/RS 的权重配置。GA 的 α=4.00/τ=0.70/rm=0.70 可能来自 GA 脚本的 stdout（未落盘） | 运行 GA 脚本（约 862s/1444s）核对；或查 `__pycache__\GA_Weight_Optimization_Experiment_Final.cpython-311.pyc` 时间戳推断运行历史 |
| 4 | **2022-2023 的真实位置分布精确口径** | 委托方给出 Defender 11 / Forward 4 / Goalkeeper 3 / Midfielder 7（总 25）。但 FBref 的 `pos` 列为多值（如 `"FW,MF"`、`"DF,MF"`），代码用 `str.contains` 会让同一球员落入多个位置池。本次核查未逐行统计 `Inter_Players_Departure_Labels.csv` 中 25 名球员各自在 `ITA_SerieA_player_standard_stats_2022_2023.csv` 里的 `pos` 值 | 逐行列出 25 人的 `pos` 字段，确认是否存在多位置归属与划分优先级 |
| 5 | **`data_collection.tex` 的 535/547 是否有过合理来源** | 603/616 是"所有带 `pos` 的行"；若曾按"至少出场 X 分钟"或"至少出场 N 场"筛过，可能得到 535/547。但最终管线无该筛选，且论文第 13 行未说明筛选条件，第 118 行又说筛选发生在"完整度评估之后" | 反向搜索：用不同 `Min` 阈值筛选，看哪个阈值恰好得到 535/547；若有，需在论文中补充筛选口径 |
| 6 | **`Statistical_Test_Results_20250831_231752.txt` / `..._232028.txt` 的性质** | 这两份文件（73 行含 `f1_score: t=0.665, p=0.5230`）与 `..._231510.txt` 同批生成但内容格式不同（前者是可读多行，后者是转义单行）。本次未完整读取这两份文件 | 完整读取这两份文件，确认它们是否来自 `Statistical_Testing_Framework.py` 的真实（仍为合成）路径，以及是否为论文某一版表格的来源 |
| 7 | **`Multi_Run_Experiment_Results_20250826_171631.json` 的完整性** | 该文件存在但本次仅通过 grep 确认（未逐行读取）；`Inter_2023_2024_Predictions_20250826_171723.json` 已确认是截断的 11 行不完整 JSON | 完整读取该 JSON，核对是否可作为 `results.tex` 各表的第二来源，以及是否含未被论文使用的"Not Significant"结果 |
| 8 | **`语音转写\` 目录内容** | 该目录未在本次审计范围内（非文档类文件），但可能包含答辩录音转写，其中可能对数据口径有口头说明 | 若需判定"论文数字是笔误还是有意"，该目录可能有决定性证据 |
| 9 | **`Algorithm_Selection_Rationale.md:407–414` 引用的 6 篇文献与论文 `references.bib` 的关系** | `references.bib` 不存在，论文引用的 9 个 bibkey 与 md 文档引用的 6 篇文献完全不重叠。无法判定哪套是真实阅读过的文献 | 检查用户是否另有文献库；核对论文 bibkey（`vanarem2025...`、`metulini2018modelling` 等）是否为真实出版物 |
| 10 | **README 声称的 "Master of Science in Data Science, University of Birmingham"、"Supervisor: Todd"** | 无第二来源可核 | 由委托方确认 |
| 11 | **`data_collection.tex:126` 的 12/18/5 三个离群数** | 无脚本无输出，无法判定是估算还是编造 | 若曾用 Jupyter/交互式会话计算，可能留存于 `%USERPROFILE%\.ipython\` 或 `.idea\` 工作区 |
| 12 | **`demand.txt` 的引援预测方向是否曾作为正式研究目标** | 该文件是需求清单（`[ ]` 未勾选），可能是项目早期方向，后转为离队预测。无法判定是否曾向导师承诺过引援预测 | 结合 `语音转写\` 或早期会议记录确认 |
| 13 | **`算法原理与权重计算效果说明文档.md:141–144` 的 "15-25%" 与 "8-15%"** | 无来源，也无法判断是"预期效果"还是"已测结果"（文档未标注） | 人工确认文档写作意图 |
| 14 | **`球队数据科学家评估指标建议.md` 的多处阈值（≥90%/≥95%/精确率≥75%/Brier≤0.2）** | 无法验证是否来自行业文献或作者判断 | 若为建议性内容，建议在论文中明确标注为"作者建议"而非"行业标准" |
| 15 | **`min_minutes = 90` 是否曾用于生成 535/547** | 见 #5。委托方判定"代码中从未实现"对**最终管线**成立，但 `GA_Clean.py:28`、`PSO_Clean.py:27`、`SA_Clean.py:27`、`RS_Clean.py:27`、`Weight_Optimization_Experiment.py:60`、`simple_weight_optimization_demo.py:45`、`Fixed_Weight_Optimization_Experiment.py:91`、`simple_weight_experiment.py:52`、`test_basic_experiment.py:23`、`test_weight_optimization.py:38` 共 **10 处** 存在 `df['Min'] > 90` | 若 535/547 来自这些早期脚本，则论文数字"有出处但出处与最终管线无关" —— 需在论文中改为正确数字或明确说明 |
| 16 | **`appendix.tex` 是否曾被编译进论文** | `main.tex` 未 include 它 | 检查是否有其他 `main*.tex` 或 `.pdf` |
| 17 | **`LaTeX_Dissertation\` 下是否存在 `Preamble\`、`Chapter *\` 的隐藏副本** | glob 未发现，但可能存在被忽略的目录 | 用文件管理器人工确认 |
| 18 | **`results.tex:4` 的 "different random seeds" 表述意图** | `seed(42+run_i)` 确实产生不同种子序列，但种子集合被固定 —— 是"可复现的多种子"还是作者误以为是"独立随机" | 人工确认表述意图；无论哪种，与第 52 行"5 runs"仍矛盾 |

---

## 附录 A：本次核查使用的关键证据文件与行号索引

| 证据 | 路径 | 关键行号 | 用途 |
|---|---|---|---|
| 真实多次运行结果 | `final project\Multi_Run_Average_Metrics_20250826_171631.txt` | 4（5 runs）、10–13（四算法指标）、19–20（composite 0.931497）、31–113（PSO 四位置权重） | 溯源 `results.tex` 的 `tab:algorithm_performance` 与 4 张权重表 |
| 真实单次运行结果 | `final project\Single_Run_ML_Metrics_20250826_134951.txt` | 9–12（GA/PSO/RS 五项同值）、16–19（composite 0.926730）、24–43（PSO 前锋权重，与多轮结果不同） | 证明"多算法"实际收敛到同一解；证明"最优权重"不稳定 |
| 真实留出集结果 | `final project\Inter_2023_2024_Prediction_Report_20250826_172047.txt` | 8–19（0.7407/0.0/0.0/0.0/0.2593…）、DETAILED（全 50.0%、Position=Unknown）、SUMMARY（20/27） | 证明论文留出集各表无来源；证明模型退化为平凡基线 |
| 合成统计检验输出 | `final project\Statistical_Test_Results_20250826_182039.txt` | 全文（5935 字符） | 与 `results.tex` 的两表逐位对应 |
| 合成统计检验输出（重复） | `final project\Statistical_Test_Results_20250831_231510.txt` | 全文（5935 字符，与上一份逐字节相同） | 证明结果与实验进展无关 |
| 合成数据生成代码 | `final project\Run_Statistical_Tests.py` | 19–21（`np.random.seed(42); n_runs=10`）、24–45（`np.random.normal(...)`）、48–51（凭空基线） | 直接证明伪造 |
| 合成数据生成代码（框架） | `final project\Statistical_Testing_Framework.py` | 72–105（`create_sample_data_for_testing`）、76/82/88/94（各算法 base_value） | 第二处伪造 |
| 另一套互斥结果 | `final project\模型对比.txt` | 1（"基于10次运行"）、5–8（0.920/0.920/0.684/0.920）、11–13（综合 0.894/0.892/0.892/0.629）、用时全 0.0 | 证明"结果"有多套且互斥 |
| GA 实现 | `final project\GA_Weight_Optimization_Experiment_Final.py` | 7（`differential_evolution`）、26–55（`get_bounds`）、76–82（`maxiter=20, popsize=10, seed=42`）、87（`'method': 'Genetic Algorithm'`）、122–123（未传 contract_data） | 算法命名不符 + 边界 + 合同缺失 |
| PSO 实现 | `final project\PSO_Weight_Optimization_Experiment_Final.py` | 25–52（边界，与 GA 相同）、69（`n_particles=30, n_iterations=50`）、73–75（`w=0.7, c1=1.5, c2=1.5`）、142（未传 contract_data） | 边界相同 + 固定惯性权重 |
| SA 实现 | `final project\SA_Weight_Optimization_Experiment_Final.py` | 26–51（边界）、81–90（4 种冷却，默认指数）、92（`initial_temp=100, max_iterations=1000`）、167 | 边界相同 + 冷却策略 |
| RS 实现 | `final project\RS_Weight_Optimization_Experiment_Final.py` | 26–49（边界）、73–79（60/40 智能策略）、88（`n_iterations=1500`）、154 | 边界相同 + 非纯随机 |
| 核心概率算法 | `final project\weight_optimization_core_updated.py` | 64–121（硬编码 2022-2023 路径 + `except: pass`）、123–130（5 通用指标）、132+（10 位置指标）、184–194（percentile）、196–239（contract 分支 + 默认 0.5）、280–287（sigmoid + clip 0.1/0.3）、289–327（加权平均 + 融合）、315–316（归一化）、319–320（contract_years 恒 2）、335–338（未传 contract_data） | 算法实质 + 合同失效 + 赛季错配 |
| 留出集预测脚本 | `final project\2023_2024_Prediction.py` | 26（读 2023-2024 标签）、37–40（读 2023-2024 统计）、42–57（位置解析）、171–172（调 2022-2023 位置数据）、186–187（未传 contract_data）、200（阈值 0.5）、219–246（指标）、229（composite） | 赛季错配 + 无 90 分钟筛选 |
| 多轮框架 | `final project\Multi_Run_Experiment_Framework_Final.py` | 36–38（`n_runs` 循环 + `seed(42+run_i)`）、48–53（composite 公式） | 运行次数与种子 |
| 早期框架（贝叶斯） | `final project\Weight_Optimization_Framework.py` | 21（`differential_evolution`）、31–38（`skopt` try/except）、253–279（`gp_minimize` n_calls=50）、260（回退分支）、308（pop 20/gen 50）、353（grid 5）、423（rs 100） | 证明贝叶斯不可运行 |
| 2022-2023 标签 | `final project\data excel\2022-2023\Inter_Players_Departure_Labels.csv` | 1–26（25 人；12 个 `1`） | 真实离队标签 |
| 2022-2023 合同 | `final project\data excel\2022-2023\Contract_2022_2023.csv` | 1–26（含 4 个 `-1` 租借：Acerbi/Asllani/Bellanova/Lukaku） | 证明合同数据存在但未使用 |
| 2023-2024 标签 | `final project\data excel\2023-2024\Inter_departured_2023_2024.csv` | 1–28（27 人；7 个 `1`） | 真实留出集标签 |
| 联赛数据规模 | `final project\data excel\2022-2023\ITA_SerieA_player_standard_stats_2022_2023.csv` | 606 行（3 表头 + 603） | 证明 535 错误 |
| 联赛数据规模 | `final project\data excel\2023-2024\ITA_SerieA_player_standard_stats_2023_2024.csv` | 619 行（3 表头 + 616） | 证明 547 错误 |
| LaTeX 主文件 | `final project\LaTeX_Dissertation\main.tex` | 3–7（biblatex/biber）、8（缺失 .bib）、15（natbib）、43（标题）、52–54 / 66–84（缺失 include） | 编译不可行 + 命名夸大 |
| 章节字数 | 8 个 `.tex` 实测 | 930 / 1781 / 2186 / 1062 / 1442 / 2098 / 720 / 530 | 证明 README 40,000 词夸大 |

---

## 附录 B：报告未覆盖但已确认不存在于磁盘的文件

| 被引用的文件 | 引用位置 | 状态 |
|---|---|---|
| `references.bib` | `main.tex:8` | 不存在 |
| `Preamble/FrontPage.tex`、`Preamble/Abstract.tex`、`Preamble/Acknowledge.tex` | `main.tex:52–54` | 不存在 |
| `Chapter 1/` … `Chapter 7/` 目录及其 7 个 `.tex` | `main.tex:66–84` | 不存在（文件平铺在 `LaTeX_Dissertation\`） |
| `Algorithm_Innovation_Framework_Analysis.md` | `Project_Continuity_Documentation.md:93` | 不存在 |
| `V1_Percentile_Based_Model_Technical_Documentation.md` | `Project_Continuity_Documentation.md:94` | 不存在 |
| `Project_Repositioning_and_Algorithm_Innovation_Strategy.md` | `Project_Continuity_Documentation.md:95` | 不存在 |
| `Inter_V1_Enhanced_Complete_Final.json` | `Project_Continuity_Documentation.md:102` | 不存在 |
| `Inter_V1_Percentile_Based_Predictions.json` | `Project_Continuity_Documentation.md:103` | 不存在 |
| `Algorithm_Innovation_Framework_Analysis.md`（第 93 行） | 同上 | 不存在 |
| `Weight_Optimization_Experiment_Results_[timestamp].json` | `Project_Continuity_Documentation.md:159` | 不存在 |
| `Statistical_Significance_Report_[timestamp].json` | `Project_Continuity_Documentation.md:171` | 不存在 |
| `Generalization_Test_Report_[timestamp].json` | `Project_Continuity_Documentation.md:176` | 不存在 |
| `scikit-optimize` 包 | `Project_Continuity_Documentation.md:227`（可选）、`Weight_Optimization_Framework.py:32` | **venv 中未安装** → `BAYESIAN_AVAILABLE = False`，所有"贝叶斯优化"结果不存在 |

---

## 附录 C：与同目录 `00_INITIAL_RECON_REPORT.md` 的交叉核对

本报告与同目录的初次勘查报告（`_audit\00_INITIAL_RECON_REPORT.md`）在绝大多数事实上一致。以下列出**口径差异**，供委托方裁决（两处不必强行统一，但需知道存在两种口径）：

| # | 事项 | 本报告口径 | `00_INITIAL_RECON_REPORT.md` 口径 | 说明与建议 |
|---|---|---|---|---|
| 1 | **统计类别数** | 「6 类参与计算 vs 论文写 7」：`data_collection.tex:31` = 7，`implementation.tex:11` = 6，代码读 6 类位置数据 | 「**7 类**，非 6 类」（第 66、223 行） | 两者不矛盾：磁盘**存在 7 个** `ITA_SerieA_player_*` 类别文件（standard / goal / shooting / passing / possession / defensive / goalkeeper，另有 goalkeeper_advance 共 8 个文件）；但 `load_position_specific_data()` 的 4 个 try 块只读 **6 类**（goal、shooting、passing、possession、defensive、goalkeeper），`goalkeeper_advance` 从未被读取。**建议表述**：磁盘 7 类，代码实际使用 6 类。本报告第 2.5 节 #3 的判定据此成立（论文自己的 6 与 7 两说互相矛盾） |
| 2 | **唯一球员数** | 未使用（只报"603/616 条记录 vs 论文 535/547"） | 577 / 590 名唯一球员（第 63–64 行） | 两者不冲突：603 是行数、577 是去重后球员数。本报告只主张论文的 535/547 错误，未主张唯一球员数 |
| 3 | **2023-2024 修正后的样本外准确率** | 记 0.7778（委托方复现） | 第 182 行记为「实测修正后样本外准确率 0.7778 → **0.8519**」 | 同一动作有两个数字（0.7778 与 0.8519），取决于修正幅度。**两者都不在磁盘任何输出文件中**，因此本报告统一将其归入"需人工复核"（第六节 #1、#2） |
| 4 | **`skiprows` 参数** | 本报告第 2.16 节 #13 称「`Project_Continuity_Documentation.md:238` 写 `skiprows = 3` vs 代码 `skiprows=2`」 | 未涉及 | **需细分**：`weight_optimization_core_updated.py:24`（`load_experimental_data_enhanced`）**确实用 `skiprows=3`**（因为它把第 3 行表头也当数据跳过、自行提供 names）；而 `weight_optimization_core_updated.py:68,74,84,91,103,113` 与 `2023_2024_Prediction.py:39` 用 `skiprows=2`。因此连续性文档的 `skiprows = 3` **对 2022-2023 主数据读取成立**，只是被泛化成了"数据加载参数"，与位置数据读取不一致。本报告第 2.16 节 #13 的判定应降级为「**口径不完整**」而非「矛盾」 |
| 5 | **`get_universal_metrics()` 返回项数** | 5 项（`weight_optimization_core_updated.py:123–130`：minutes/age/CrdY/CrdR/Contract_expires），实际加权 3 项 | 第 106 行记「**4 个**通用指标: minutes/CrdY/CrdR/Contract_expires」 | **本报告口径正确**：源码 `:123–130` 含 5 个 key（含 age）。但两方都同意"实际生效项数少于声明项数" |
| 6 | **`calculate_base_risk_sigmoid()` 是否死代码** | 本报告未主张其为死代码（认为它被 `:324` 调用，只是合同输入恒为 0.5） | 第 110 行标为「**【死代码】**合同 sigmoid，从未被调用」 | **本报告口径应更准确**：`calculate_base_risk_sigmoid()` 在 `weight_optimization_core_updated.py:324` 被 `calculate_departure_probability_with_weights` 调用，**不是死代码**；真正失效的是它的**合同输入**（`contract_percentile` 恒 0.5 → `contract_years` 恒 2）。两方结论（合同对结果无影响）一致 |
| 7 | **论文与磁盘的一致性表述** | 本报告主张 `results.tex` 的留出集 4 张表**无任何磁盘来源** | 第 185 行记「论文 `results.tex` 与真实报告**一致**（77.78%）」 | 这是两报告最实质的分歧。**本报告的核查结果**：全库对 `0.7778 / 0.5556 / 0.7143 / 0.6459 / 0.4706 / 0.7571 / 0.4781 / 0.6765` 的 grep 在 7 份业务文本结果文件中**零命中**，唯一留出集产物（`Inter_2023_2024_Prediction_Report_20250826_172047.txt`）为 0.7407/0/0/0/0.2593/0/0/0.5/0.25/0.2787。故不能认定"一致"，只能认定"论文数字与委托方复现值一致，但与磁盘现存输出不一致"。**建议以本报告为准，并在第六节 #1 中彻底查清** |
| 8 | **`results.tex` 各表的来源** | 本报告逐表溯源，区分出 12 项"有来源"、12 项"无来源"、4 项"错配/矛盾" | 未做逐表溯源 | 本报告为增量结论 |
| 9 | **一致性结论** | 双方在以下关键事实上**完全一致**：论文数据规模错误（535/547）、标签错误（10/15）、位置分布错误（GK2/DF11/MF8/FW4）、完整度 96.8–98.5% 失实、统计检验数据伪造、GA 实为差分进化、四算法边界与目标函数相同、赛季错配、合同变量失效、引用不存在文件、`min_minutes=90` 未在最终管线实现 | 同左 | 无分歧 |

---

*报告结束。所有结论均给出文件名与行号或原文引用，未使用任何含糊表述。本次审计为只读操作，未修改 `final project` 下任何文件。*
