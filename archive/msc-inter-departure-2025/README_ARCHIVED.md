# README_ARCHIVED — 已归档的 MSc 项目（INTER_DEPARTURE_2025）

> **本目录是历史归档，不是新系统的组成部分。**
> 归档日期：本次审计会话
> 原始位置：`F:\Samuel\football recruitment\final project\`（原件为 `F:\Samuel\学习\final project\`）
> 归档方式：**移动，未删除任何文件**。完整性已校验（171 个文件，SHA256 清单见 `MANIFEST_SHA256.txt`）。

---

## 1. 这是什么

一个英国伯明翰大学（University of Birmingham）MSc 数据科学毕业论文项目：

> **标题**：Multi-layer Probability Fusion Algorithm Based on Relative Percentile Ranking with Weight Optimization: Application to Football Transfer Prediction
> **中文**：基于相对百分位排名的多层次概率融合算法及其在足球转会预测中的应用
> **作者**：Ziming Chen
> **导师**：Todd

项目试图预测国际米兰球员在赛季间"离队 / 留队"，技术路线是：

```
球员指标 → 按位置计算联赛内百分位 → 加权平均得"表现分"
        → 基础风险(年龄sigmoid) + (1 − 表现分) × 风险系数
        = 离队概率
```

其中权重由 4 种元启发式算法（GA/PSO/SA/RS）在标签上搜索得到。

---

## 2. ⚠️ 阅读本归档前必须知道的三件事

### 2.1 这个项目**不是机器学习**

代码中大量使用 "Machine Learning Metrics"、"supervised learning" 等措辞，但实际实现是：

- ❌ 无参数化模型、无损失函数、无梯度、无拟合过程；
- ✅ 实际是一个**确定性启发式评分器**，权重由**搜索**（而非学习）得到。

### 2.2 这个项目输出的**不是概率**

`departure_prob = base_risk + (1 − performance_score) × risk_multiplier`，随后被 `clip(0.05, 0.95)`。
输出从未经过概率校准（无 Platt / Isotonic），实测集中在 0.32–0.68 的窄带内。
**但它被当作 "departure probability" 使用，甚至用 Brier score 评估。**

### 2.3 论文的核心统计结论**不成立**

论文第 6 章的显著性检验（p<0.001、Cohen's d=34.92 等）所依据的"实验数据"是**程序生成的随机数**：

- `Statistical_Testing_Framework.py:72-105` 的 `create_sample_data_for_testing()` 使用 `np.random.normal(0.928, 0.01, 10)`；
- 该函数在 `main()` 无参调用时**无条件触发**（`:330-333`）；
- 复算可逐位复现磁盘上的 `Statistical_Test_Results_20250826_182039.txt`；
- 而论文 `results.tex:52` 却称这是 "multi-run experimental data (5 independent runs per algorithm)"。

此外，`Run_Statistical_Tests.py:183-186` 的结论是**硬编码**的——无论输入什么数据都打印同样的话。

---

## 3. 已作废的结论清单（**不得再引用**）

| 作废内容 | 位置 | 原因 |
|---|---|---|
| 所有统计显著性结论（p 值、Cohen's d、t 值、W 值） | `results.tex` 的 `tab:one_sample_testing`、`tab:paired_testing`、`tab:wilcoxon_test`；`Run_Statistical_Tests.py`；`Statistical_Testing_Framework.py`；`Statistical_Test_Results_*.txt` | 数据由 `np.random.normal()` 伪造；结论硬编码 |
| 论文第 4 章全部数据表（5 张） | `LaTeX_Dissertation\data_collection.tex` | 与磁盘数据全部不符（球员数 535/547 vs 实际 577/590；标签 10/15 vs 实际 12/13；位置分布；完整度 96.8–98.5% vs 实际 100%；异常值检测代码中不存在） |
| "泛化能力 / 交叉验证稳定性 / 时间泛化" 的一切结果 | `Generalization_Testing_Framework.py` | 600 行空壳：`GeneralizationValidator` 全仓库零实例化，`__main__` 只调一个 4 行 print 的 stub；"时间泛化测试"用 `np.random.choice` 从当前联赛随机抽 1/3 冒充"未来赛季数据" |
| "合同 sigmoid 参数优化"的整段论述 | `results.tex` 的 `tab:sigmoid_parameters` 及相关正文 | 合同数据从未传入计算函数 → 合同百分位恒为 0.5 → 合同年限恒为 2.0 常数 → 合同维度对结果**零影响** |
| 数据完整度 96.8%–98.5% 的声明 | `data_collection.tex:96-114` | 实测核心指标列**零缺失（100%）** |
| "40,000 词"的论文篇幅声明 | `LaTeX_Dissertation\README.md:141` | 实测 8 个 tex 空白分隔计词合计约 10,749 词 |
| "35.3% improvement over baseline" | `LaTeX_Dissertation\README.md:115` | 留出集实测 0.7778 vs 平凡基线 0.7407，净增益仅 +3.7 个百分点；样本内 +44.0pp 是训练集自评 |

---

## 4. 仍然真实、有价值的部分

### 4.1 数据资产（有价值，已在新系统中复用）

| 资产 | 说明 |
|---|---|
| `data excel\2022-2023\`、`data excel\2023-2024\` | FBref 导出的 Serie A 全联赛数据，各约 600 行 × 7 个统计类别，共 101 个去重指标 |
| `Contract_2022_2023.csv`、`Contract_2023_2024.csv` | 合同剩余年数（`-1` 表示租借）。**旧代码从未使用，新系统必须使用** |
| `Inter_Players_Departure_Labels.csv`、`Inter_departured_2023_2024.csv` | 国米阵容离队标签（25 / 27 人） |
| `data\players_ITA-SerieA_2425_standard.html` | **2024-25 赛季原始 HTML（2.0 MB）**，磁盘上已有但从未解析——可提供第三个赛季 |

### 4.2 技术资产

| 资产 | 文件 | 价值 |
|---|---|---|
| FBref 三层表头解析逻辑 | `weight_optimization_core_updated.py:64-121` | 解析映射关系已摸清（row0 组名 / row1 指标名 / row2 字段名 / row3+ 数据） |
| 百分位特征工程 | `calculate_percentile_score()` | 思路正确（同位置内相对排名） |
| 位置专属指标映射 | `get_position_specific_metrics()` | 每位置 10 个指标的选择有领域参考价值 |
| 球员雷达图 | `Inter_*_Analysis\*.png`（23 张） | 图形设计可作新版球员画像的参考 |
| 实验记录习惯 | `Multi_Run_Experiment_Framework_Final.py` | JSON 结构化输出 + 时间戳 + 多轮聚合 |

### 4.3 最有价值的资产：**它踩过的坑**

本归档建议保留以下"负面资产"，作为新系统的方法论教训与回归测试来源：

- `Run_Statistical_Tests.py` —— 伪造实验数据的活标本；
- `Generalization_Testing_Framework.py` —— 空壳框架的标本；
- `Inter_2023_2024_Prediction_Report_20250826_172047.txt` —— **常数预测器**那次运行（accuracy=0.7407、Precision=Recall=F1=0.0000、27 人全部 `Position="Unknown"`、概率恒为 50.0%）。它证明同一目标存在**两种截然不同的结果**，即流程不可复现。

---

## 5. 关键实测数字（供新系统做回归基线）

| 指标 | 值 | 说明 |
|---|---|---|
| 留出集准确率（2023-24，n=27） | **0.7778** | 我已按代码逻辑复现；混淆矩阵 TP=5 FP=4 FN=2 TN=16 |
| 留出集的平凡基线 | **0.7407** | 全预测"留队" |
| 留出集净增益 | **+3.7pp** | 统计上不显著（n=27 时 95% CI 约 ±0.16） |
| 样本内准确率（2022-23，n=25） | 0.9600（单配置）/ 0.9280（5 轮均值） | **训练集自评，非预测能力** |
| 训练样本量 | **25**（离队 12 / 留队 13） | 按位置拆分：后卫 11、中场 7、前锋 4、**门将 3** |
| 每个模型的可调参数 | **16** | 明显过参数化 |
| 修正赛季错配后的留出集准确率 | **0.8519**（FN=0） | 旧脚本 `2023_2024_Prediction.py:171` 误用 2022-23 的位置数据 |

---

## 6. 归档内容清单

```
archive/msc-inter-departure-2025/
├── README_ARCHIVED.md          ← 本文件
├── MANIFEST_SHA256.txt         ← 170 条 SHA256 校验和
├── *.py                54 个   ← 全部 Python 代码（3–4 代并存）
├── *.md                12 份   ← 技术文档
├── *.txt               19 个   ← 结果报告与草稿
├── *.png               42 张   ← 图表
├── *.json               2 个   ← 结构化结果
├── *.csv               23 个   ← 数据
├── *.tex                9 个   ← 论文（在 LaTeX_Dissertation/）
├── *.html               8 个   ← FBref 原始页面（在 data/）
├── data/                       ← FBref 原始 HTML
├── data excel/                 ← 加工后的 CSV（2 个赛季）
├── LaTeX_Dissertation/         ← 论文 8 章
├── Inter_Defenders_Analysis/           ← 12 张雷达图
├── Inter_Forwards_Analysis_Fixed/      ← 4 张雷达图
├── Inter_Midfielders_Analysis/         ← 7 张雷达图（新版）
├── Inter_Midfielders_Analysis(原）/    ← 7 张雷达图（旧版，重复）
├── 语音转写/                   ← 语音转写文本
├── Demonstration Slide——Ziming Chen.pptx
└── requirement.jpg
```

**未随归档迁移的内容**（仍在原 `final project\` 目录）：

| 项 | 原因 |
|---|---|
| `venv/`（457.6 MB，17376 文件） | 体积过大且可由 `requirements.txt` 重建。**新系统已从其中提取依赖清单** |
| `.idea/`（7 文件） | PyCharm 工程配置，无归档价值 |
| `.claude/settings.local.json` | 工具配置 |
| `claude-code`、`111.txt` | 空文件 |
| `__pycache__/*.pyc` | 可再生缓存 |

---

## 7. 相关审计文档

本次归档所依据的完整审计报告位于：

```
F:\Samuel\football recruitment\_audit\
├── EXISTING_PROJECT_AUDIT.md    ← 交付物 A：完整取证审计（含 39 项技术债清单）
├── OLD_TO_NEW_MAPPING.md        ← 交付物 B：新旧映射
├── GAP_ANALYSIS.md              ← 交付物 C：差距分析
├── MIGRATION_PLAN.md            ← 交付物 D：M0–M9 迁移路线图
├── FINAL_ASSESSMENT.md          ← §18 的 8 个必答问题
├── CODE_INVENTORY_RAW.md        ← 54 个 .py 逐文件分级
└── DOC_CLAIMS_RAW.md            ← 22 份文档逐条声明核查
```

---

*本归档为只读历史材料。新系统位于 `F:\Samuel\football recruitment\recruitment-squad-intelligence\`，不依赖本目录中的任何代码。*
