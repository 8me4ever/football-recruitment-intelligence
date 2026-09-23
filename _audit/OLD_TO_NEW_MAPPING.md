# OLD_TO_NEW_MAPPING.md — 旧资产到新系统的映射

> **交付物 B**（对应主提示词 §17）
> 目标系统：**Recruitment & Squad Planning Intelligence System**（引援与阵容规划智能系统）
> 原则：不必要地重建可用代码（提示词 §13）；技术复杂度排在最后（§19）

---

## 0. 映射总览

旧项目 180 个文件中，真正进入新系统的**源码**只有 **6 个片段**，其余分四类处置：

```
旧项目（180 文件）
   │
   ├── 直接复用 ────────────  6 个代码片段 / 2 份数据资产      → src/
   ├── 重构后复用 ──────────  5 个概念 / 3 份数据             → src/（重写）
   ├── 仅历史参考 ──────────  论文、图表、旧文档              → archive/
   └── 退役 ───────────────  伪造评估、空壳框架、3 代重复代码  → archive/（标注作废）
```

**核心判断**：旧项目对**数据管道**和**百分位特征工程**的贡献是真实的；对**建模**和**评估**的贡献不可用。因此映射的重点是"把数据层和特征层捞出来，把建模层和评估层重做"。

---

## 1. 主映射表

| # | 旧组件 | 旧位置 | 新模块 | 动作 | 理由 |
|---|---|---|---|---|---|
| 1 | FBref 多级表头 CSV 解析 | `weight_optimization_core_updated.py:64-121` | `src/data/loaders.py` | **REFACTOR** | 解析逻辑正确且必需，但 `skiprows=2` 错（应 3），且异常被静默吞掉 |
| 2 | 位置分组 `get_position_group()` | 各文件内重复 4 次 | `src/data/schemas.py` | **REFACTOR** | 逻辑需保留，但必须改为处理多位置字符串（`'FW,MF'`），当前丢弃第二位置 |
| 3 | 百分位转换 `calculate_percentile_score()` | `weight_optimization_core_updated.py:184-194` | `src/features/percentiles.py` | **REFACTOR** | 思路正确必须保留；需补最小出场门槛、收缩估计、并列值处理 |
| 4 | 位置专属指标映射 `get_position_specific_metrics()` | `weight_optimization_core_updated.py:132-182` | `src/features/position_features.py` | **REFACTOR** | 映射表有参考价值；但要去掉 `CrdY/CrdR` 作为"表现"，并补入门将 adv 指标 |
| 5 | 联赛内按位置建参考池的逻辑 | `calculate_enhanced_percentile_scores():204-212` | `src/features/contextualisation.py` | **REFACTOR** | 逻辑可用；需先修去重与低样本过滤 |
| 6 | 通用指标（minutes/age/contract）的抽象 | `get_universal_metrics()` | `src/features/contextualisation.py` | **REPURPOSE** | "通用 vs 位置专属"的分层是好设计；但 `Contract_expires` 从未生效，需真正接线 |
| 7 | **国米阵容名单 + 离队标签** | `Inter_Players_Departure_Labels.csv`、`Inter_departured_2023_2024.csv` | `data/processed/squad_*.csv` | **REUSE（需重定义）** | 数据有效，可用于**回溯标定**；但"离队"定义需重新文档化并检查前视偏差 |
| 8 | **Serie A 候选球员池**（577/590 人） | `data excel/{season}/*.csv` | `data/processed/candidate_pool_*.csv` | **REUSE** | **这是旧项目最有价值的资产**。去重+过滤后每赛季约 430 人可用作引援搜索池 |
| 9 | 合同数据 | `Contract_2022_2023.csv`、`Contract_2023_2024.csv` | `data/processed/contracts_*.csv` | **REUSE** | 真实数据，且**新系统必须真正使用它**（旧系统从未使用） |
| 10 | 2024-25 赛季原始 HTML | `data/players_ITA-SerieA_2425_standard.html` | `data/raw/` → 解析入库 | **REPURPOSE** | 磁盘上已有但从未解析；可提供第三个赛季，用于真正的时间外验证 |
| 11 | 门将先进统计（PSxG/Sweeper） | `data excel/*/..._goalkeeper_advance_stats_*.csv` | `src/features/position_features.py` | **REPURPOSE** | 数据已存在但旧系统完全未用；是门将画像的关键素材 |
| 12 | 离队风险评分公式 | `calculate_departure_probability_with_weights():289-327` | `src/departure/model.py` | **REBUILD** | 方向对（表现+年龄+合同→风险），但① 输出未校准却称"概率"② 合同项失效③ 牌越多越"好"④ 参数来自伪造优化 |
| 13 | 基础风险 sigmoid | `calculate_base_risk_sigmoid():280-287` | `src/departure/model.py` | **REPURPOSE** | 形状可用；但 α/τ 数值必须重新标定并给出论证 |
| 14 | 权重优化的**框架思想** | `Multi_Run_Experiment_Framework_Final.py:30-105` | `src/evaluation/validation.py` | **REBUILD** | 多轮+聚合+JSON 记录的习惯值得保留；实现必须重做（当前无留出、轮次不独立） |
| 15 | 四个元启发式优化器 | `GA/PSO/SA/RS_*_Final.py` + `*_Clean.py` + `*_Updated.py`（12 个文件） | — | **ARCHIVE** | 全部退役。证据见下方 §2 |
| 16 | 复合评分函数 | `evaluate_weights_enhanced():353-358` | `src/evaluation/metrics.py` | **REBUILD** | 0.4/0.3/0.2/0.1 权重任意；且目标函数=评估指标构成循环论证 |
| 17 | 统计显著性检验 | `Run_Statistical_Tests.py`、`Statistical_Testing_Framework.py` | `src/evaluation/validation.py` | **REMOVE** | **数据伪造**。必须整体退役并在归档中标明 |
| 18 | 泛化/稳定性测试框架 | `Generalization_Testing_Framework.py` | `src/evaluation/validation.py` | **REMOVE** | 600 行空壳；核心方法不存在；"时间泛化"用随机抽样冒充 |
| 19 | 早期算法对比实验 | `Multi_Algorithm_Comparison_Experiment.py` | — | **REMOVE** | 导入 4 个不存在的模块，无法运行 |
| 20 | 可视化（算法对比图） | `Algorithm_Comparison_Visualization.py` | `src/visualization/recruitment.py` | **REPURPOSE** | 绘图代码可用；需去掉 "ML Metrics" 措辞 |
| 21 | 球员雷达图 | `Inter_*_Analysis/*.png`（23 张） | `src/visualization/player_profiles.py` | **REPURPOSE** | 生成脚本已丢失，但**图形格式可作为新版画像的设计参考** |
| 22 | 论文 LaTeX | `LaTeX_Dissertation/` | `archive/` | **ARCHIVE** | 第 4 章（数据）与第 6 章统计部分**不得再引用** |
| 23 | 11 份根目录技术文档 | `*.md` | `archive/` | **ARCHIVE** | 8/19 之后的中文文档（诚实化拐点后）仍有参考价值 |
| 24 | 22 个草稿脚本 | `111.py`、`tax.py`、`test_*.py` 等 | `archive/` | **REMOVE** | 开发残留 |
| 25 | `main.py` | 根目录 | — | **REMOVE** | PyCharm 模板 |
| 26 | `venv/`（457 MB） | 根目录 | — | **REMOVE** | 改为 `requirements.txt` 重建 |
| 27 | 展示用 PPT / 需求图 / 语音转写 | `*.pptx`、`requirement.jpg`、`语音转写/` | `archive/` | **ARCHIVE** | 过程材料 |
| 28 | `demand.txt`（**项目最初需求**） | 根目录 | `docs/` | **REPURPOSE** | ⭐ 见 §4 —— 它证明项目**最初方向就是"引援预测"** |

---

## 2. 争议资产的处置论证

### 2.1 四个元启发式优化器：为什么全部 ARCHIVE

提示词 §7 要求"不要因为算法技术复杂度就保留它"。逐项论证：

| 算法 | 表面价值 | 实测证据 | 判定 |
|---|---|---|---|
| **GA**（实为差分进化） | "进化计算避免局部最优" | ① 名实不符：`differential_evolution` 不是遗传算法；② `seed=42` 硬编码，5 轮结果 std=**0.0000**；③ 其最优解仅比"全部取上界"好 **0.0005** | **ARCHIVE** |
| **PSO** | "群体智能，性能最佳（论文主推）" | ① 效果好只是因为它搜索更彻底，**不是模型更好**；② 在 16 维、n≤11 的空间上，它与 RS 结果几乎一致 → 说明空间容易被搜索，问题不在优化器 | **ARCHIVE** |
| **SA** | "模拟退火" | 结果最差（0.728），耗时 217s，**且 0.728 落在各位置多数类基线区间内**，即接近无信息 | **ARCHIVE** |
| **RS** | "随机搜索基线" | 与 GA/PSO 齐平（0.92）→ **恰恰证明"优化"的边际价值接近零** | **ARCHIVE** |

**决定性论证**：如果三个完全不同的搜索策略（差分进化、PSO、带局部扰动的随机搜索）都能收敛到同一个分数（0.92），那么**提高搜索能力不会带来任何收益**。这说明瓶颈不在优化器，而在：
- 样本量（25）；
- 特征的信息量；
- 公式的形式。

**在新系统中的替代方案**：

```
旧：16 维权重 × 4 位置 × 4 算法 × 5 轮 无约束元启发式搜索
新：带 L2 正则的逻辑回归（跨位置共享参数，约 4–8 个自由参数）
    或：专家先验权重 + 敏感性分析报告
    → 目标：可解释、可复现、参数数 << 样本数
```

### 2.2 离队风险公式：为什么是 REBUILD 而不是 REFACTOR

表面看公式"表现好 → 不易离队"很合理。但有四个独立问题：

| 问题 | 严重性 | 说明 |
|---|---|---|
| ① 输出不是概率，却按概率使用 | 🔴 高 | 被 clip 到 [0.05, 0.95]，实测集中在 0.32–0.68；却用 Brier score 评估 |
| ② 合同项恒为常数 | 🔴 高 | 导致论文关于 α/τ 的整章论述无效 |
| ③ 黄牌/红牌被当作正向"表现" | 🟠 中 | 足球逻辑反向 |
| ④ 年龄 30 岁被设为风险峰值 | 🟠 中 | 实测年龄与离队 **r=−0.008, p=0.969**，即数据里年龄与离队无关 |

四个问题叠加 ⇒ **保留公式形状，但所有输入语义、参数、输出语义都必须重定义**。故为 REBUILD。

### 2.3 统计检验代码：为什么必须 REMOVE 而非"修正"

**修正方案不成立**，因为：
1. 这些脚本的**入口就是伪造数据**（`Run_Statistical_Tests.py` 的 `main()` 直接调用伪造函数）；
2. `Statistical_Testing_Framework.main()` → `run_comprehensive_statistical_tests()`，若无 JSON 文件则回退到 `create_sample_data_for_testing()`；
3. **结论被硬编码**（`Run_Statistical_Tests.py:183-186`），即使喂入真实数据也会打印同样的结论。

⇒ 保留会造成"看起来在做统计检验"的假象。必须整体退役，且**在归档中明确标注其结论作废**。

---

## 3. 数据资产映射（最有价值的部分）

### 3.1 从旧数据到新数据层

| 新系统需要的表 | 旧来源 | 加工动作 | 我已验证可行性 |
|---|---|---|---|
| `players`（球员赛季表） | `data excel/{season}/*_standard_*.csv` | 修 `skiprows=3`；按 `player` 去重（合并赛季中转会的两行）；解析多位置 | ✅ 577/590 人 |
| `player_metrics`（长表或宽表） | 同一赛季的 7 个统计 CSV | 按 `(player, season)` join；修正列对齐 | ✅ 101 个指标可用 |
| `contracts` | `Contract_{season}.csv` | 把 `-1` 标记为 `is_loan=True`，年限置空；其余转数值 | ✅ 每赛季 4 名租借 |
| `squad_inter` | 同上 + 球队字段 | 筛 `team == 'Inter'` | ✅ 25 / 27 人 |
| `departure_labels` | `Inter_Players_Departure_Labels.csv`、`Inter_departured_2023_2024.csv` | **重新文档化"离队"定义**；标注是否含租借；评估前视偏差 | ⚠️ 需人工重定义 |
| `candidate_pool` | 全联赛 players 表 | 去重、`Min >= 450`、位置可知 | ✅ 430 / 422 人 |
| `season_2024_25` | `data/players_ITA-SerieA_2425_standard.html` | 解析 HTML（尚未做） | ⏳ 待做 |

### 3.2 我实测的数据质量问题（新数据层必须处理）

| 问题 | 规模 | 处理方式 |
|---|---|---|
| 赛季中转会导致球员重复 | 每赛季 52 行 / 26 人 | 按 `player` 聚合（分钟、进球等求和；`age` 取最大） |
| 多位置球员 | 118 / 143 人 | 保留 `positions_all` 列表 + `primary_position`，供角色画像用 |
| 低出场样本 | 75 / 88 行（最少 5 分钟） | 参考池用 `Min >= 450`；球员画像显示时标注低样本警告 |
| 合同 `-1` 表示租借 | 每赛季 4 人 | 拆分为 `is_loan` 布尔 + `contract_years_left`（租借为 NaN） |
| `skiprows` 错位 | 全部加载点 | 统一为 3；加列数断言 |

---

## 4. ⭐ 重要发现：`demand.txt` 证明项目最初方向就是"引援"

`demand.txt`（2025-08-03）是项目的**原始需求清单**，内容与"离队预测"完全不同：

```
[ ] 数据收集：获取 Inter 2022-2023 赛季引援数据（球员信息、转会费、位置等）
[ ] 数据收集：获取 Inter 历史引援数据用于建模
[ ] 数据收集：获取 Inter 2023-2024 赛季实际引援数据用于验证
[ ] 模型开发：建立引援预测模型（位置需求、预算分配等）
[ ] 模型验证：使用 2023-2024 实际数据验证预测准确性
[ ] 探索性数据分析：分析 2022-2023 赛季引援特征和模式
[ ] 结果分析：对比预测与实际引援的差异和原因
```

**这意味着**：

1. 项目**原本就想做引援（recruitment）预测**，与本次任务的新方向**天然一致**；
2. 中途因为**拿不到转会费/薪资/预算数据**（这些确实不在 FBref 免费数据里），退化为"离队概率预测"——这是一个**因数据可得性而缩小的范围**；
3. 因此新系统**不是"推翻重来"，而是"回到原始意图 + 用正确的数据和方法重做"**。

**对迁移策略的影响**：新系统的定位叙事应当是——

> "旧项目因为缺少转会费与薪资数据，把问题缩小成了球员离队二分类。新系统用已有的 Serie A 全联赛表现数据，把问题**还原**为阵容风险识别与引援候选筛选——这是球队真实决策链中可控的那一半。"

同时必须诚实声明**新系统仍然没有**（提示词 Principle 5：不编造缺失数据）：

| 缺失数据 | 影响 |
|---|---|
| 转会费 / 估值 | **无法做预算约束与性价比分析** |
| 薪资 | **无法评估薪资结构风险** |
| 伤病历史 | 无法纳入可用性风险 |
| 经纪人信息 | 无法评估交易可行性 |
| 合同细节（解约金、选项） | 合同风险只能做粗粒度判断 |
| 联赛外球员数据 | 候选池**只有 Serie A**，无法跨国引援推荐 |

---

## 5. 新旧模块一一对照

按提示词 §11 的 12 个目标模块逐一映射。

| 目标模块 | 旧系统对应能力 | 旧文件 | 复用级别 | 动作 |
|---|---|---|---|---|
| **M1 Squad Data** | 部分：有 25/27 人名单 + 年龄 + 位置 + 分钟 | `load_experimental_data_enhanced()`、标签/合同 CSV | 🟡 数据可复用，代码需重写 | **REFACTOR** |
| **M2 Performance Engine** | **有**：按位置百分位 + 加权表现分 | `calculate_percentile_score()`、`calculate_enhanced_percentile_scores()`、`get_position_specific_metrics()` | 🟢 高 | **REFACTOR**（本模块是旧项目最大遗产） |
| **M3 Role Profiling** | ❌ **完全没有**。只有 4 个粗位置 | — | ⚫ 无 | **NEW** |
| **M4 Departure Risk** | 有，但性质是启发式评分而非校准概率 | `calculate_departure_probability_with_weights()` | 🟠 低（概念可留） | **REBUILD** |
| **M5 Squad Vulnerability** | ❌ 完全没有 | — | ⚫ 无 | **NEW** |
| **M6 Need Detection** | ❌ 完全没有 | — | ⚫ 无 | **NEW** |
| **M7 Candidate Universe** | **有**：Serie A 577/590 人，但未去重/未过滤 | `data excel/` | 🟢 高 | **REUSE + CLEAN** |
| **M8 Player Similarity** | ❌ 完全没有（无 cosine、无 KNN、无嵌入） | — | ⚫ 无 | **NEW** |
| **M9 Candidate Ranking** | 部分：有加权评分的骨架 | `calculate_departure_probability_with_weights()` | 🟠 低 | **NEW**（另起） |
| **M10 League Translation** | ❌ 完全没有，且**数据不支持**（只有 Serie A） | — | ⚫ 无 | **BLOCKED** |
| **M11 Development Potential** | ❌ 完全没有 | — | ⚫ 无 | **NEW（后置）** |
| **M12 Uncertainty** | ⚠️ 仅"缺失值回退 0.5"，无置信区间、无 bootstrap | `calculate_percentile_score()` 的 NaN 分支 | 🟠 低 | **NEW** |
| **M13 Reporting / Dashboard** | 部分：有 PNG 图表与雷达图，无交互界面 | `Algorithm_Comparison_Visualization.py`、`Inter_*_Analysis/*.png` | 🟡 中 | **REPURPOSE** |

**统计**：13 个目标模块中，**2 个高度可复用**（M2、M7）、**4 个低度可复用需重建**（M1/M4/M9/M12）、**1 个概念可借**（M13）、**5 个完全新建**（M3/M5/M6/M8/M11）、**1 个受数据限制阻塞**（M10）。

---

## 6. 技术栈映射

| 维度 | 旧系统 | 新系统建议 | 理由 |
|---|---|---|---|
| Python | 3.x（venv） | 3.11（沿用，venv 已验证可用） | 零迁移成本 |
| 数据处理 | pandas / numpy | 沿用 | 已足够 |
| 统计 | scipy.stats | 沿用 | `percentileofscore` 已用 |
| 机器学习 | scikit-learn（**仅用 metrics，未用模型**） | scikit-learn（**真正用模型**：LogisticRegression + 正则化） | 旧系统装了 sklearn 却只用指标函数 |
| 降维/嵌入 | ❌ 无 | scikit-learn 的 PCA（**先不引入 UMAP**） | 提示词 §16：不必要地引入新依赖 |
| 聚类 | ❌ 无 | scikit-learn 的 KMeans / GMM（**M5 阶段再评估**） | 同上 |
| 可解释性 | ❌ 无 SHAP | 优先用**系数 + 置换重要性**（不引入 shap） | 提示词 §19：先要可解释性，不要复杂度 |
| 可视化 | matplotlib / seaborn | 沿用 | — |
| 交互界面 | ❌ 无 | Streamlit（**M9 阶段再说**） | 提示词 §16：暂不建 dashboard |
| 配置 | ❌ 无 | `pyproject.toml` + `requirements.txt` | 必需 |
| 结果管理 | 根目录平铺 + 时间戳文件名 | `results/{stage}/{timestamp}/` | 必需 |
| 测试 | ❌ 无 | pytest，**优先覆盖本次发现的缺陷** | 必需 |

---

## 7. 映射后的处置统计

| 动作 | 文件/资产数 | 占比 |
|---|---|---|
| **REUSE**（几乎原样搬） | 2（候选池数据、合同数据） | ~1% |
| **REUSE + CLEAN**（数据清洗后搬） | 3（赛季数据、标签、2024-25 HTML） | ~2% |
| **REFACTOR**（搬+改） | 6（解析、位置分组、百分位、指标映射、参考池、可视化） | ~3% |
| **REPURPOSE**（概念借用，另写） | 5（通用/专属分层、sigmoid 形状、雷达图格式、实验记录习惯、门将 adv 指标） | ~3% |
| **REBUILD**（重写） | 3（离队风险模型、评估层、复合指标） | ~2% |
| **ARCHIVE**（归档保留） | 论文 10 个 tex + 11 份 md + 42 PNG + 结果文件 ≈ 110 | ~61% |
| **REMOVE**（退役） | 12 个算法文件 + 6 个评估/空壳 + 22 个草稿 + venv + main.py ≈ 42 | ~23% |

**关键结论**：**约 6% 的旧文件进入新系统，94% 归档或退役。** 这与提示词 §13 的"不要把旧项目当整个架构，只当一个子系统"完全一致——而且实际上，旧项目连"一个子系统"都不够格（它只有数据层和特征层可用），更适合的定位是：

> **旧项目 = 新系统的「数据层 + 特征层」原型 + 一份高价值的方法论反面教材。**

---

*交付物 B 完成。继续阅读 `GAP_ANALYSIS.md` 与 `MIGRATION_PLAN.md`。*
