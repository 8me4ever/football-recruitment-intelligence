# 代码文件分级盘点报告（CODE_INVENTORY_RAW）

**审计对象**：`F:\Samuel\football recruitment\final project`
**审计范围**：该目录下全部 **54 个 `.py` 文件**（已排除 `venv/`、`.idea/`、`.claude/`、`__pycache__/`）
**审计方式**：纯静态只读 —— 只使用 read / grep / 只读 PowerShell（读取 CSV 前几行、venv 包探测、哈希比对）。**未修改任何原有文件，未写入任何脚本，未运行被审计脚本的业务逻辑**（仅用 `venv\Scripts\python.exe -c` 做了只读的数据结构与数学复算验证）。
**项目背景**：伯明翰大学 MSc 数据科学毕业论文 —— 基于相对百分位排名的多层次概率融合算法，用于预测国际米兰球员离队。
**报告日期**：基于目录 2025-08-31 23:19 的时间戳快照。

---

## 一、总体结论

1. **文件总数与构成**：目录树中共 54 个 `.py`。其中真正属于"论文交付物候选"的只有 **16 个**（1 个核心引擎 + 4 个 `_Final` 算法 + 4 个 `_Updated` 算法 + 4 个 `_Clean` 算法 + 2 个 `_Final` 实验框架 + 1 个可视化）。其余 38 个中，**11 个是必须退役的一次性/无关脚本**（`main.py`、`111.py`、`11111.py`、`222.py`、`444.py`、`555.py`、`tax.py`、`basic_test.py`、`test_chart_fix.py`、`test_multi_run_quick.py`、`test_fixed_framework.py`），**7 个是已被下一代取代的旧代实现**。

2. **代际主线已确认**（依据 mtime + 代码内容双重证据）：早期框架代（2025-08-08，`Weight_Optimization_Framework.py` 用贝叶斯/GA/网格/随机搜索）→ 中间 `_Clean` 代（2025-08-13）→ 后期 `_Updated` 代（2025-08-26 02:00–02:24）→ 最终 `_Final` 代（2025-08-26 12:24–14:00）。`_Updated` 与 `_Final` 在**同一天相隔 10 小时**，且 `_Updated` 是相对 `_Final` 的**功能回归**（见 §四）。

3. **⚠️ 最严重的方法论缺陷：合同到期这一核心特征在最终模型里完全未生效。** `data excel/2022-2023/Contract_2022_2023.csv`（25 行，列 `['Name','Contract_expires']`）**存在**，但全项目 **没有任何一行代码读取它**（grep 全部 `.py` 无命中）。所有 4 个 `_Final` 算法与核心引擎调用 `calculate_enhanced_percentile_scores(...)` 时**只传 3 个位置参数**（如 `GA_Weight_Optimization_Experiment_Final.py:122-123`），第 4 个形参 `contract_data` 恒为 `None` → `weight_optimization_core_updated.py:237` 恒赋 `scores['Contract_expires'] = 0.5` → `:320` 的 `contract_years = max(0,(1-0.5)*4) = 2.0` **对所有球员恒定**。论文中以"合同剩余年限"为核心卖点的特征贡献为零，而张量却为 `Contract_expires_weight` 分配了搜索维度。

4. **⚠️ 统计检验结果是用 `np.random.normal()` 伪造的，且已数值级复现。** `Statistical_Testing_Framework.py:72-105` 的 `create_sample_data_for_testing()` 用 `np.random.seed(42)` + `np.random.normal(0.928, 0.01, 10)` 造假，由 `:204-205` 在 `main()`（`:330-333`）无参调用时**无条件触发**。我用同一行代码复算出 `mean=0.9325 / t=110.429 / Cohen's d=34.921`，与磁盘上 `Statistical_Test_Results_20250826_182039.txt` 第 9-11 行**逐位相同**。真实产物 `Multi_Run_Experiment_Results_20250826_171631.json` 明确记录 `n_runs = 5`，伪造数据把样本量放大到 10 并完全虚构方差。同类问题还有 `Run_Statistical_Tests.py:24-45`（其 t≈137.547 与产物文件不符，说明它甚至不是产物来源）。

5. **核心引擎的 8 个"权重维度"是惰性维度（已实测验证）。** 实测 `load_position_specific_data()` 后逐项核对 `get_position_specific_metrics()`：Forward 的 `Att_Pen`/`TakeOn_Succ` 声明 `source='possession'`，但 Forward 数据集只有 `['goal','shooting']`；Midfielder 的 `Tkl`（`defensive`）与 `SCA`（`goal`）不存在于 `['passing','possession']`；Defender 的 `Def_3rd`（`possession`）不存在于 `['passing','defensive']`；Goalkeeper 的 `PK_Save`/`Cmp_40_plus` 在实际加载列中不存在（真实列为 `PKsv`/`PK_Save_pct`）。这些指标恒取 0.5 兜底值，对应权重**对目标函数零影响**，但仍占据搜索维度。

6. **`_Final` 四算法的 `get_bounds()` 与 `fitness_function()` 逐字相同**（已用文本比对确认 4 份 `get_bounds` 完全一致）。差异只在搜索策略与**适应度符号**：GA 返回 `-score`（`:68`，适配 `differential_evolution` 最小化），PSO/SA/RS 返回 `score`（`PSO:67`、`SA:68`、`RS:68`）。

7. **`Generalization_Testing_Framework.py` 整体是死代码。** 其 `__main__`（`:599-600`）只调用 `example_generalization_testing()`，而该函数体（`:590-597`）**只有 4 句 `print`，不构造任何优化器、不跑任何测试**。全仓库无任何地方实例化 `GeneralizationValidator`。它调用的 `optimizer.calculate_percentile_features`（`:445`）与 `optimizer.calculate_departure_probability`（`:447`）**并非"不存在的方法"**——它们真实存在于 `Weight_Optimization_Framework.py` 的 `PercentileWeightOptimizer`（`:115` / `:177`）。真正的问题是**版本错配**：最终流水线使用 `weight_optimization_core_updated.py`（它没有类，只有模块级函数 `calculate_enhanced_percentile_scores:196` / `calculate_departure_probability_with_weights:289`）。此外 `optimizer.best_weights` 在 `PercentileWeightOptimizer` 中**根本不存在**（只有 `optimization_history:65`），导致 `:339` 分支永久死掉、`:426` 恒走"权重上下界中点"兜底。

8. **缺失本地模块共 6 个，集中在旧代文件上，导致 5 个文件必然不可导入。** `Enhanced_Weight_Optimization_Experiment.py`、`PSO_Weight_Optimization_Experiment.py`、`SA_Weight_Optimization_Experiment.py`、`RS_Weight_Optimization_Experiment.py`、`Multi_Run_Experiment_Framework.py`、`GA_Weight_Optimization_Experiment.py` 全部不存在。引用方：`Multi_Algorithm_Comparison_Experiment.py`（`:65/68/71/74`，4 个缺失模块）、`PSO/SA/RS_Weight_Optimization_Experiment_Updated.py`（均从 `Enhanced_...` 导入，其中 `calculate_contract_risk_adjustment` **全项目仅定义于 `GA_..._Updated.py:284`**，属"模块不存在 + 符号不在核心"双重失效）、`test_fixed_framework.py`（`:29` 引 `Multi_Run_Experiment_Framework`、`:59` 引 `Enhanced_...`，且 `:32` 调用全项目不存在的 `convert_to_json_serializable`）。

9. **最终可运行链是唯一自洽的一条，且已产出真实产物。** `weight_optimization_core_updated.py` ← `{GA,PSO,SA,RS}_Weight_Optimization_Experiment_Final.py` ← `{Single_Run_Test_Framework_Final.py, Multi_Run_Experiment_Framework_Final.py}` ← `Run_Statistical_Tests.py` / `Statistical_Testing_Framework.py`。磁盘产物（`Multi_Run_Experiment_Results_20250826_171631.json`、`Optimal_Weights_20250826_185855.txt`、`Single_Run_ML_Metrics_20250826_134951.txt`）均出自这一代。**这一代全部 4 个算法与我验证过的核心引擎函数签名兼容，数据管线实测可通过**：25 个国米球员与 25 行标签**100% 精确匹配**（含 `Džeko`/`Çalhanoğlu`/`Škriniar` 等重音字符），`team=='Inter'` 实测命中 25 行，无静默丢样本。

10. **一处高风险学术诚信问题需立即隔离**：`test_basic_experiment.py:29-75` 在真实读完数据后，把实验结论**硬编码**（`accuracy` 0.720/0.879、`improvement` 0.159、`improvement_percentage` 22.1、`statistical_significance` `'p < 0.05'`、`effect_size` `"Large (Cohen's d = 1.24)"`），并在 `:79` 落盘为 `Weight_Optimization_Demo_Results_*.json`、`:87-100` 打印为 "EXPERIMENT SUMMARY"。同类还有 `test_chart_fix.py:11-19`、`test_multi_run_quick.py:16-40`、`def_possession.py:26-36`。

---

## 二、主表格（54 个 .py 全量）

> 「可运行」判定口径：**能跑** = import 全部可解析 + 数据文件存在 + 有入口或已被上游正确调用；**不可运行** = 有缺失 import 或缺少入口且无调用方；**需先改** = 可解析但被硬编码路径/数据或死入口阻断。
> 所有判定均以本报告 §三、§四 的行号证据为准。

### A. 核心引擎（2）

| 文件 | 角色 | 代际 | 可运行 | 重复对象 | 去留建议 |
|---|---|---|---|---|---|
| `weight_optimization_core_updated.py` | 核心引擎 | 最终（2025-08-26 12:28） | ✅ 能跑（无入口，纯函数库，被 `_Final` 正确调用） | 其前 7 个函数被 `GA_Weight_Optimization_Experiment_Updated.py:13-278` **逐字节复制** | **直接复用** —— 唯一被最终流水线依赖的引擎 |
| `weight_optimization_core.py` | 核心引擎（旧版） | 中期偏后（2025-08-13 19:02） | ⚠️ 结构性缺陷：`calculate_percentile_scores:262` 用 `position_datasets[source_dataset]` 而实际键是位置名 → 非 standard 指标全走 0.5 兜底 | 被 `_updated` 完全取代 | **仅作历史参考** —— 记录"扁平命名指标 → 通用+位置分层指标"的架构演进；不再复用 |

### B. 算法实现（12）

| 文件 | 角色 | 代际 | 可运行 | 重复对象 | 去留建议 |
|---|---|---|---|---|---|
| `GA_Weight_Optimization_Experiment_Final.py` | 算法实现（GA/最终） | 最终（08-26 12:24） | ✅ 能跑，有 `__main__:189` | 4 个 `_Final` 共享逐字相同的 `get_bounds:26-55`；fitness 体相同但 `:68` 返回 `-score` | **直接复用** |
| `PSO_Weight_Optimization_Experiment_Final.py` | 算法实现（PSO/最终） | 最终（08-26 12:25） | ✅ 能跑，有 `__main__` | 同上，`get_bounds:25-54`，`:67` 返回 `score` | **直接复用** |
| `SA_Weight_Optimization_Experiment_Final.py` | 算法实现（SA/最终） | 最终（08-26 12:25） | ✅ 能跑，有 `__main__` | 同上，`get_bounds:26-55`，`:68` 返回 `score` | **直接复用** |
| `RS_Weight_Optimization_Experiment_Final.py` | 算法实现（RS/最终） | 最终（08-26 12:25） | ✅ 能跑，有 `__main__:221` | 同上，`get_bounds:26-55`，`:68` 返回 `score` | **直接复用** |
| `GA_Weight_Optimization_Experiment_Updated.py` | 算法实现（GA/后期，单体版） | 后期（08-26 02:24） | ⚠️ 可导入但目标函数与 core 不一致 | **整份内核副本**：7 个函数与 `weight_optimization_core_updated.py` **逐字节相同**（实测 `load_experimental_data_enhanced`/`load_position_specific_data`/`get_universal_metrics`/`get_position_specific_metrics`/`calculate_percentile_score`/`calculate_enhanced_percentile_scores` 全部 identical） | **仅作历史参考** —— 它是"把 core 内联进来"的中间态；`:284` 的 `calculate_contract_risk_adjustment` 是全项目唯一实现，有一定史料价值 |
| `PSO_Weight_Optimization_Experiment_Updated.py` | 算法实现（PSO/后期） | 后期（08-26 02:08） | ❌ **不可运行**，`:12-16` 从缺失模块导入，导入即 `ModuleNotFoundError` | bounds/fitness/composite 公式与 GA `_Final` 逐字相同 | **建议退役**（或按 `_Final` 改写，见 §四） |
| `SA_Weight_Optimization_Experiment_Updated.py` | 算法实现（SA/后期） | 后期（08-26 02:07） | ❌ **不可运行**，`:13-17` 同上 | 同上；另有 `:169-182` 三个不可达冷却分支 | **建议退役** |
| `RS_Weight_Optimization_Experiment_Updated.py` | 算法实现（RS/后期） | 后期（08-26 02:06） | ❌ **不可运行**，`:12-16` 同上 | 同上；`:184-185` 纯随机分支不可达 | **建议退役** |
| `GA_Clean.py` | 算法实现（GA/中间） | 中间（08-13 18:24） | ⚠️ 可跑但语义错误：`:91-141` 把 `shots_on_target→'GA'`、`tackles→'CrdY'`、`clearances→'PK'`、GK `saves→'GA'`；`:185-260` 每次评估重读 CSV | bounds `:265-271`、`load_data:16-56`、`calculate_player_score:143-183`、`get_position_specific_metrics:91-141` 与 PSO/SA/RS_Clean **逐字节相同** | **仅作历史参考** |
| `PSO_Clean.py` | 算法实现（PSO/中间） | 中间（08-13 18:25） | ⚠️ 同上；`:184` 定义 `class PSO`，无随机种子 | 同上（4 份 Clean 共享 5 个核心函数） | **仅作历史参考** |
| `SA_Clean.py` | 算法实现（SA/中间） | 中间（08-13 18:26） | ⚠️ 同上；`class SimulatedAnnealing:184`；`:295` 接受准则为正号最大化 | 同上 | **仅作历史参考** |
| `RS_Clean.py` | 算法实现（RS/中间） | 中间（08-13 18:27） | ⚠️ 同上；`class RandomSearch:184` | 同上 | **仅作历史参考** |

### C. 实验框架（8）

| 文件 | 角色 | 代际 | 可运行 | 重复对象 | 去留建议 |
|---|---|---|---|---|---|
| `Multi_Run_Experiment_Framework_Final.py` | 实验框架（多次运行/最终） | 最终（08-26 14:00） | ⚠️ 能跑并已产出真实 JSON/TXT；但 `:329` 把嵌套 dict 传给 `create_charts_from_multi_run_data`，该函数 `:228` 调 `.iterrows()` → AttributeError 被 `:328-333` 吞掉，**多次运行图表从不生成** | 与 `_Updated` 版前 200 行同源 | **重构后复用** —— 主干可用，需修 `:329` 改为 `pd.DataFrame(self.generate_averaged_comparison_data())` 并统一列名大小写 |
| `Multi_Run_Experiment_Framework_Updated.py` | 实验框架（多次运行/后期） | 后期（08-26 02:18） | ❌ **不可运行**：`:13` 导入 PSO `_Updated`（该模块本身导入失败） | 与 `_Final` 同源；同样是 `:203` 的 dict→iterrows 缺陷 | **建议退役** |
| `Single_Run_Test_Framework_Final.py` | 实验框架（单次运行/最终） | 最终（08-26 13:20） | ✅ 能跑，已产 `Single_Run_ML_Metrics_20250826_134951.txt` | 与 `_Updated` 版同源 | **直接复用** |
| `Single_Run_Test_Framework_Updated.py` | 实验框架（单次运行/后期） | 后期（08-26 02:17） | ❌ **不可运行**：`:13` 同上；且 `:94-96` 结果文件只有 `pass` **从不落盘** | 与 `_Final` 同源；`:34-55` 大量局部变量算出后未使用 | **建议退役** |
| `Multi_Algorithm_Comparison_Experiment.py` | 实验框架（多算法对比/早期） | 早期（08-12 16:05） | ❌ **不可运行**：`:65/68/71/74` 导入 **4 个不存在的模块** | 其 `:104-107` 产出的大写列 DataFrame 才是 `create_charts_from_multi_run_data` 期望的输入 | **建议退役** |
| `Multi_Algorithm_Comparison_Clean.py` | 实验框架（多算法对比/中间） | 中间（08-13 18:27） | ✅ 能跑（4 个 `run_*_optimization()` 签名零参，调用点 `:36` 匹配） | 被 `Multi_Algorithm_Comparison_Experiment.py` 取代方向相反 | **仅作历史参考** |
| `Weight_Optimization_Experiment.py` | 实验框架（基线对比/早期） | 早期（08-08 14:10） | ✅ 能跑；`:176-177` 调 `PercentileWeightOptimizer` 的方法（存在于同代框架） | 被 `Multi_Algorithm_Comparison_Clean.py` 取代 | **仅作历史参考** |
| `Fixed_Weight_Optimization_Experiment.py` | 实验框架（逐位置优化/早期） | 早期（08-10 18:53） | ✅ 能跑；`:401-447` 贝叶斯（`skopt` 已装）、`:448-484` GA、`:485-521` 随机搜索、`:522-583` 均匀基线 | 与 `Weight_Optimization_Framework.py` 的 4 算法并列——**同一"四算法对比"任务在早期有两套独立实现** | **仅作历史参考** |

### D. 评估与统计（5）

| 文件 | 角色 | 代际 | 可运行 | 重复对象 | 去留建议 |
|---|---|---|---|---|---|
| `Statistical_Testing_Framework.py` | 评估与统计 | 最新（08-31 23:19） | ⚠️ 能跑，但**默认路径走伪造数据**：`:72-105` `np.random.normal`；`:204-205` 在 `main():330-333` 无参时无条件触发 | `Run_Statistical_Tests.py:24-45` 是同一造假思路的另一份实现 | **重构后复用** —— `:28-69` 的真实 JSON 读取通路字段与 `Multi_Run_Experiment_Results_*.json` **完全匹配**，只需强制传入文件名并删除 `:72-105` |
| `Run_Statistical_Tests.py` | 评估与统计 | 后期（08-26 18:19） | ⚠️ 能跑，但**无任何文件 I/O，全部靠 print**；`:24-45` 伪造数据；`:182-186` 结论段是**硬编码断言** | 与 `Statistical_Testing_Framework.py` 重复 | **建议退役** —— 它既不能产出磁盘产物（实测其 t≈137.547 ≠ 产物中的 110.429），结论也不由计算得出 |
| `Statistical_Significance_Testing_Framework.py` | 评估与统计 | 早期（08-08 14:16） | ⚠️ 能跑但**完全没有真实数据通路**（无 `read_csv`/`json.load`）；`:527-533` 用 `np.random.seed(42)` + `np.random.choice` 造假 | 与 `Statistical_Testing_Framework.py` 部分功能重叠；**但 Bootstrap CI `:239-322` 与 McNemar `:324-406` 是它独有的** | **仅作历史参考** —— 两个特色检验未被新版继承；若论文需要，应移植而非退役 |
| `Generalization_Testing_Framework.py` | 评估与统计 | 早期（08-08 14:18） | ❌ **实质不可运行**：`__main__:599-600` 只调 `example_generalization_testing():590-597`，该函数体**只有 4 句 print**、不构造优化器；全仓库零实例化 `GeneralizationValidator` | 与 `PercentileWeightOptimizer` API 绑定 | **建议退役** —— 600 行泛化测试框架从未执行过；`best_weights:339/426` 属性不存在导致分支永久死掉 |
| `Enhanced_Evaluation_Metrics_Framework.py` | 评估与统计 | 早期（08-12 14:40） | ⚠️ 能跑，但**无任何调用方**（全项目零 import）；唯一驱动 `create_sample_evaluation:258` 喂的是 `np.random.beta:266` / `np.random.binomial:267` 合成数据 | 与 `Statistical_Testing_Framework.py` 的指标计算部分功能重叠 | **建议退役** —— 其"业务影响/财务影响"指标（`:43-76`、`:165-193`）的输入是 `:169-171` 硬编码假想金额（2500 万/200 万/15%），结论不可用；`calculate_probability_calibration_metrics:105` 的 Brier 分解思路可考虑移植 |

### E. 可视化（2）

| 文件 | 角色 | 代际 | 可运行 | 重复对象 | 去留建议 |
|---|---|---|---|---|---|
| `Algorithm_Comparison_Visualization.py` | 可视化 | 后期（08-15 00:04） | ✅ 能跑；被 `Single_Run_Test_Framework_Final.py:16` 正确使用（实测结构匹配） | 与 `Simple_Chart_Generator.py` **同一套图表的功能版 vs 类版** | **直接复用** |
| `Simple_Chart_Generator.py` | 可视化 | 后期（08-15 00:04） | ⚠️ 能跑但**无任何调用方**（全项目无 import）；`:191-192` 的 `__main__` 只有 `pass` | 与 `Algorithm_Comparison_Visualization.py` 重复（`create_main_metrics_chart:13` ↔ `create_main_metrics_comparison:22`、`create_all_charts:168` ↔ `:194`）；差异：本文件 `:4` 用 `matplotlib.use('Agg')` 且不调 `plt.show()`，更适合无头批量出图 | **重构后复用** —— 建议作为 `Agg` 后端出图入口，类版保留用于交互 |

### F. 预测应用（5）

| 文件 | 角色 | 代际 | 可运行 | 重复对象 | 去留建议 |
|---|---|---|---|---|---|
| `2023_2024_Prediction.py` | 预测应用 | 最新（08-31 23:11） | ❌ **需先改**：`:15` `sys.path.append(r"F:\Samuel\学习\final project")`、`:163` `os.chdir(r"F:\Samuel\学习\final project")` —— 旧机绝对路径；`:39` 用 `skiprows=2 + names` 导致多一行脏数据 | 与 `weight_optimization_core_updated.py:9-62` 的数据加载逻辑逐行重复 | **重构后复用** —— 是最新的预测入口，只需删两处绝对路径、修 `skiprows`、改为传入 `contract_data` |
| `Player_Departure_Predictor_2023_2024.py` | 预测应用 | 中间（08-13 00:53） | ✅ 能跑（自包含，无数据文件依赖）；但 `:368-670` 是 **21 名球员硬编码假数据**，`:285/686` 写死 `综合评分: 0.9275` | 与 `Working_Prediction_Demo_2023_2024.py` 权重字典**数值逐一相同** | **仅作历史参考** —— 归一化算法（`min(1.0, x/max)`）与核心的 `percentileofscore` 是两套算法，不能混用 |
| `Working_Prediction_Demo_2023_2024.py` | 预测应用 | 中间（08-13 00:49） | ✅ 能跑（`:398-415` 有 `__main__`，只依赖 `json`/`datetime`）；7 名球员假数据；`:326/383` 写死 `0.9275` | 与 `Player_Departure_Predictor_2023_2024.py` 重复 | **仅作历史参考** |
| `simple_prediction_test.py` | 一次性测试脚本 | 中间（08-13 00:46） | ✅ 能跑（`:91-92` 有 `__main__`）；单人 4 指标手算 | 是上两份的极小真子集 | **建议退役** —— 手工验算残留，`pandas`/`numpy` 均未使用 |
| `manual_integration.py` | 预测应用（数据导出） | 早期（08-03 02:01） | ❌ **不可运行**：`:19` `os.system("pip install openpyxl")`（导入即联网装包），且实测 venv 中 `openpyxl`/`xlsxwriter` **均未安装** → `:50` `pd.ExcelWriter(engine='openpyxl')` 必失败；**无函数、无 `__main__`、导入即执行副作用** | 与 `2023_2024_Prediction.py`/core 的数据准备层重复 | **建议退役** |

### G. 临时草稿与其余一次性脚本（21）

| 文件 | 角色 | 代际 | 可运行 | 重复对象 | 去留建议 |
|---|---|---|---|---|---|
| `main.py` | 临时草稿 | 最早（07-01） | ✅ 能跑（PyCharm 模板） | 无 | **建议退役** —— 与论文零关系 |
| `111.py` | 临时草稿 | 最早（07-07） | ✅ 能跑（pandas 排序去重练习） | 无 | **建议退役** |
| `222.py` | 临时草稿 | 最早（07-08） | ❌ 只建 DataFrame 无输出（半截） | 无 | **建议退役** |
| `444.py` | 临时草稿 | 最早（07-08） | ✅ 能跑，但 `month_diff('202001','202003')` 返回负数（语义可疑） | 无 | **建议退役** —— 疑似"合同月数"草稿但全项目无人引用 |
| `555.py` | 临时草稿 | 最早（07-13） | ✅ 能跑（字符串解析练习） | 无 | **建议退役** |
| `tax.py` | 临时草稿 | 最早（07-13） | ❌ 导入即阻塞于 `input()`（无 `__main__` 保护） | 无 | **建议退役** —— 别的课程作业 |
| `11111.py` | 临时草稿 | 最早（07-31） | ✅ 能跑（LeetCode 279 完全平方数） | 无 | **建议退役** |
| `def_possession.py` | 临时草稿（含伪造数据） | 早期（07-24） | ❌ **不可运行**：`:6` 硬编码 `F:/Samuel/学习/final project/...`；无 `__main__`，导入即 `plt.show()` 阻塞 | 无 | **建议退役** —— 且 `:26-36` 用 `np.random.normal` **伪造"每 90 分钟赢得球权"指标**并当真实数据绘图；`:23-24` 球队名单混入 22-23 赛季的 Spezia/Cremonese/Sampdoria 却配 23-24 数据 |
| `test.py` | 一次性测试脚本 | 后期（08-26 01:34） | ❌ 不可运行：`soccerdata`（实测**已装**）可导入，但 `:15` `out.to_excel(...)` 因 `openpyxl` 缺失必失败 | 无 | **仅作历史参考** —— 它是合同/身价数据的唯一获取尝试（对应 `data/` 下的 soccerdata HTML 缓存），解释了为何合同特征最终缺失 |
| `basic_test.py` | 一次性测试脚本 | 早期（08-08 14:14） | ✅ 能跑（环境冒烟，`:6` 读的 CSV 存在） | 无 | **建议退役** |
| `test_basic_experiment.py` | 一次性测试脚本（⚠️ 伪造结果） | 早期（08-10 18:40） | ✅ 能跑，但 `:29-75` **把实验结论全部硬编码**并 `:79` 落盘 JSON | 无 | **建议退役 + 隔离** —— 最高学术诚信风险，任何结果不得被引用 |
| `test_chart_fix.py` | 一次性测试脚本 | 早期（08-12 15:49） | ✅ 能跑但数据全硬编码（`:11-19`）；输出 `test_chart_fix.png` 不存在 | 绘图块与 `Multi_Algorithm_Comparison_Experiment.py:182-223` 同源 | **建议退役** |
| `test_multi_run_quick.py` | 一次性测试脚本 | 早期（08-12 16:06） | ✅ 能跑但 `:16-40` 全为 `np.random` 模拟 | 与 `Multi_Algorithm_Comparison_Experiment.py` 绘图块同源 | **建议退役** |
| `test_fixed_framework.py` | 一次性测试脚本 | 早期（08-12 23:24） | ❌ **必然全红**：`:28/58` 硬编码旧绝对路径；`:29`/`:59` 导入 2 个缺失模块；`:32` 调全项目不存在的 `convert_to_json_serializable` | 无 | **建议退役** —— 且 `:155-160` 的"所有修复验证通过"分支是**死代码** |
| `test_prediction_model.py` | 一次性测试脚本 | 中间（08-13 00:45） | ❌ **不可运行 + 有害**：`:11-12` 在**模块级**执行 `os.chdir('F:/Samuel/学习/final project')` 与 `sys.path.append(...)` → 导入即改全局工作目录 | 与 `test_prediction_directly.py` 的 `test_player` 字典**逐字相同** | **建议退役** |
| `test_prediction_directly.py` | 一次性测试脚本 | 中间（08-13 00:47） | ❌ 不可运行：`:13` `os.chdir('F:/Samuel/学习/final project')` | 与 `test_prediction_model.py` 重复 | **建议退役** |
| `test_weight_optimization.py` | 一次性测试脚本（有效） | 早期（08-08 14:11） | ✅ 能跑：`:14` 导入 `PercentileWeightOptimizer`（存在），`:91`/`:98` 调用的方法均存在（`:115`/`:423`） | `get_position_group:46-58` 与 core `:32-45`、`2023_2024_Prediction.py:42-55` **第三次逐字重复** | **重构后复用** —— 全项目**唯一真正调用早期框架的集成测试**，有保留价值 |
| `Weight_Optimization_Framework.py` | 实验框架（早期主框架） | 早期（08-08 14:08） | ✅ 能跑：`:253-306` 贝叶斯（`skopt` 实测已装）、`:308-352` GA、`:353-422` 网格搜索、`:423-468` 随机搜索 | 其 `calculate_percentile_features:115` / `calculate_departure_probability:177` 是全项目这两个方法名的**唯一真实定义** | **仅作历史参考** —— 但 §五 的"三代差异"必须引用它作为第一代基准；且它定义了论文最初声称的"四算法（贝叶斯/GA/网格/多目标）" |
| `simple_weight_experiment.py` | 一次性测试脚本 | 早期（08-10 18:38） | ✅ 能跑；`:65` 定义 `calculate_percentile_features`、`:96` 定义 `calculate_departure_probability`（与框架同名但为独立函数） | 与 `Weight_Optimization_Framework.py` 功能重叠 | **仅作历史参考** |
| `simple_weight_optimization_demo.py` | 临时草稿 | 早期（08-08 14:13） | ⚠️ 能跑但**无 `__main__` 且无调用方**，`:138` 的 `objective_function` 只在模块内被 `minimize` 使用；**:430 行文件在 `def objective_function` 后直接结束，无演示入口** | 与 `Weight_Optimization_Framework.py` 重叠 | **建议退役** |

---

## 三、缺失依赖与死代码清单

### 3.1 不存在的本地模块（6 个）

| 缺失模块 | 引用位置（文件:行） | 后果 |
|---|---|---|
| `Enhanced_Weight_Optimization_Experiment.py` | `PSO_Weight_Optimization_Experiment_Updated.py:12-16`；`SA_..._Updated.py:13-17`；`RS_..._Updated.py:12-16`；`Multi_Algorithm_Comparison_Experiment.py:65`；`test_fixed_framework.py:59` | 3 个算法文件 + 2 个框架文件不可导入 |
| `PSO_Weight_Optimization_Experiment.py` | `Multi_Algorithm_Comparison_Experiment.py:68` | 同上 |
| `SA_Weight_Optimization_Experiment.py` | `Multi_Algorithm_Comparison_Experiment.py:71` | 同上 |
| `RS_Weight_Optimization_Experiment.py` | `Multi_Algorithm_Comparison_Experiment.py:74` | 同上 |
| `Multi_Run_Experiment_Framework.py` | `test_fixed_framework.py:29` | 测试必失败 |
| `GA_Weight_Optimization_Experiment.py` | `Multi_Algorithm_Comparison_Experiment.py`（GA 分支经 `:65` 走 `Enhanced_...`） | 该代 GA 入口缺失 |

**旁证**：`PSO/SA/RS_..._Updated.py` 从缺失模块导入的 `calculate_contract_risk_adjustment`，全项目**唯一定义处是 `GA_Weight_Optimization_Experiment_Updated.py:284`**，且该符号**不在** `weight_optimization_core_updated.py` 的 9 个公共函数中 → 属"模块名不存在 + 符号位置错误"双重失效。正确写法在仓库里已存在：`PSO_..._Final.py:10-14` 从 `weight_optimization_core_updated` 导入 `evaluate_weights_enhanced` 并在 `:61` 真实调用。

### 3.2 不存在的函数/方法/属性

| 被引用名 | 引用位置 | 事实 |
|---|---|---|
| `convert_to_json_serializable` | `test_fixed_framework.py:32` | 全项目零定义。`Multi_Run_Experiment_Framework_Final.py` 的 7 个方法中无此名 |
| `run_enhanced_weight_optimization` | `test_fixed_framework.py:59`；`Multi_Algorithm_Comparison_Experiment.py:65` | 全项目零定义（所属模块本身也不存在） |
| `optimizer.best_weights` | `Generalization_Testing_Framework.py:339/343/426/427` | `PercentileWeightOptimizer` 只有 `optimization_history`（`Weight_Optimization_Framework.py:65`），**无 `best_weights` 属性** → `:339` 判定恒 False（`weight_sensitivity_analysis` 永返回 None）、`:426` 恒走"权重上下界中点"兜底 |
| `optimizer.calculate_percentile_features` / `optimizer.calculate_departure_probability` | `Generalization_Testing_Framework.py:445/447` | **这两个方法真实存在** —— 在 `Weight_Optimization_Framework.py:115/177`。**不能记为"调用了不存在的方法"**；真正的问题是版本错配：最终引擎 `weight_optimization_core_updated.py` 无类，只有 `calculate_enhanced_percentile_scores:196` / `calculate_departure_probability_with_weights:289` |
| 指标列 `PK_Save` / `Cmp_40_plus` | `weight_optimization_core_updated.py:177/180`（经 `load_position_specific_data:113` 加载的 GK 数据集） | 实测 GK 数据集列为 `[..., 'PKatt','PKA','PKsv','PKm','PK_Save_pct']`，**无 `PK_Save`/`Cmp_40_plus`** → 恒 0.5 兜底 |
| `meta_*` 系列 | 无 | 全项目未出现，无需处理 |

### 3.3 硬编码旧机绝对路径（8 处 / 5 个文件）

| 文件:行 | 内容 |
|---|---|
| `2023_2024_Prediction.py:15` | `sys.path.append(r"F:\Samuel\学习\final project")` |
| `2023_2024_Prediction.py:163` | `os.chdir(r"F:\Samuel\学习\final project")` |
| `def_possession.py:6` | `pd.read_csv("F:/Samuel/学习/final project/data excel/2023-2024/ITA_SerieA_player_possession_stats_2023_2024.csv", header=1)` |
| `test_fixed_framework.py:28` | `sys.path.append('F:/Samuel/学习/final project')` |
| `test_fixed_framework.py:58` | `sys.path.append('F:/Samuel/学习/final project')` |
| `test_prediction_directly.py:13` | `os.chdir('F:/Samuel/学习/final project')` |
| `test_prediction_model.py:11` | `os.chdir('F:/Samuel/学习/final project')`（**模块级**，导入即生效） |
| `test_prediction_model.py:12` | `sys.path.append('F:/Samuel/学习/final project')`（**模块级**） |

当前真实路径是 `F:\Samuel\football recruitment\final project`，上述 8 处**全部失效**。

### 3.4 缺失或缺少 `if __name__ == "__main__"` 入口

**完全无入口且无调用方（导入即执行或纯定义）**：`111.py`、`222.py`、`444.py`、`555.py`、`tax.py`、`11111.py`、`basic_test.py`、`test.py`、`test_basic_experiment.py`、`test_chart_fix.py`、`manual_integration.py`、`def_possession.py`、`test_weight_optimization.py`、`simple_weight_optimization_demo.py`、`weight_optimization_core.py`、`weight_optimization_core_updated.py`。
> 说明：两个 core 文件作为纯函数库无入口是**正确的**；`test_weight_optimization.py` 无入口但作为被 import 的测试脚本尚可接受；其余 13 个属"缺入口"。

**有 `__main__` 但内容为空或仅打印**（形式上有、实质无入口）：`Algorithm_Comparison_Visualization.py:247-248`（`pass`）、`Simple_Chart_Generator.py:191-192`（`pass`）、`Generalization_Testing_Framework.py:599-600`（仅调 `example_generalization_testing()`，而后者 `:590-597` 只有 4 句 print）。

### 3.5 死代码（定义后从未被调用 / 从未被执行）

| 位置 | 死代码内容 |
|---|---|
| `Generalization_Testing_Framework.py` 全文件 | `class GeneralizationValidator`（`:34`）**全仓库零实例化**；实际可达路径只有 `__main__:599` → `example_generalization_testing():590-597`（4 句 print）→ 600 行框架（含 `cross_validation_stability_test:64`、`temporal_generalization_test:194`、`robustness_to_noise_test:252`、`weight_sensitivity_analysis:330`、`_evaluate_on_dataset:419`、`_evaluate_weights_on_fold:438`、`_analyze_weight_consistency:465`、`comprehensive_generalization_report:490`）**从未执行** |
| `Statistical_Significance_Testing_Framework.py` | 整类仅 `:31` 定义与 `:518` 的 example 内使用，无外部调用方；`bootstrap_confidence_interval:239-322`、`mcnemar_test:324-406` 只被 `comprehensive_statistical_report:408` 使用，而后者只被 `:518` 的 example 使用（目录中无 `Statistical_Significance_Report_*.json` → 从未跑通） |
| `Statistical_Testing_Framework.py` | `extract_performance_data:36-69` 仅可由 `load_multi_run_results:28` 到达，而 `load_multi_run_results` **全仓库零调用**（`main():330` 从不传文件名）→ 唯一真实的 JSON 读取通路是死代码，默认走 `:72-105` 伪造 |
| `Enhanced_Evaluation_Metrics_Framework.py` | 该模块**无任何外部 importers**，仅 `__main__:287-294` 调用 `create_sample_evaluation:258` |
| `Simple_Chart_Generator.py` | 4 个绘图函数 + `create_all_charts:168` **全项目零调用**；`__main__:191-192` 为 `pass` |
| `Single_Run_Test_Framework_Updated.py` | `:34-55` 的 `accuracy`/`pr_auc`/`f1_score_val`/`weights`/`predictions` 算出后从未使用；`:81-93` 的 `successful_algorithms`/`failed_algorithms` 只喂给 `pass`；**`:94-96` 结果文件名拼好后只有 `pass`，从不落盘**；`:101-102` 图表异常 `except: pass` |
| `Multi_Run_Experiment_Framework_Updated.py` | `:33-35` `valid_runs`；`:78-79` `if best_weights: pass`；`:132-136` 两个 `pass`；**`:200` `averaged_data` 算完即丢**（它才是本该传给绘图函数的对象）；`:201` 返回值丢弃；`:30` 形参 `alg_name` 未使用 |
| `Multi_Run_Experiment_Framework_Final.py` | 与上条同源：`:329` 把嵌套 dict 传给 `iterrows()`，异常被 `:328-333` 吞掉 → **多次运行图表从不生成**（属"沿用未修的既有 bug"）；`averaged_data` 同样被丢弃 |
| `Multi_Algorithm_Comparison_Experiment.py` | `:89-160` 的 `generate_comparison_report` 依赖 `:100` `result.get('overall_ml_metrics')`，但 4 个被导入模块均不存在 → `self.results` 全为 `None` → `:115-117` 提前返回，**整份对比报告逻辑不可达** |
| `test_fixed_framework.py` | `:148-162` 的 `test_comprehensive_improvements` 依赖前 3 个测试全通过，而前 3 个必然失败 → `:155-160` 的"✨所有修复验证通过"是死代码 |
| `Player_Departure_Predictor_2023_2024.py` / `Working_Prediction_Demo_2023_2024.py` | `:285/686` 与 `:326/383` 硬编码 `0.9275` 的"综合评分"从未由代码计算得出 |
| 4 个 `_Clean` 文件 | 均未使用 `json`、`datetime`、`roc_auc_score`；`precision`/`recall`/`cohen_kappa`/`mcc`/`accuracy` 算出后不进 composite（如 `GA_Clean.py:234-242`）；`metric_info['source']`（全部为 `'standard'`）从不被读取 |
| `_Updated` 系列 | `GA_..._Updated.py` 未使用 `numpy`(`:2`)、`json`(`:4`)；PSO/SA/RS `_Updated` 未使用 `pandas`；三者均**死导入** `calculate_contract_risk_adjustment`（`PSO:15`/`SA:16`/`RS:15`）；`SA_..._Updated.py:169-182` 三个冷却分支因 `:338` 固定 `'exponential'` 而不可达；`RS_..._Updated.py:184-185` 纯随机分支因 `:268` 固定 `'smart'` 而不可达 |
| `test.py` | 输出 `Inter_Contracts_from_soccerdata_SoFIFA.xlsx` 在目录中**不存在**（`openpyxl` 缺失） |
| `manual_integration.py` | 输出 `Inter_Players_Complete_Analysis.xlsx` 在目录中**不存在** |

### 3.6 引用了不存在的产物文件 / 从未跑通的路径

- `Generalization_Test_Report_*.json`（由 `Generalization_Testing_Framework.py:569` 指定）→ 目录中**不存在**。
- `Statistical_Significance_Report_*.json`（由 `Statistical_Significance_Testing_Framework.py:474` 指定）→ 目录中**不存在**。
- `{PSO,SA,RS}_Weight_Optimization_Results_*.json`（由 `_Updated.py:471/455/384` 指定）→ 目录中**不存在** → 这三个 `_Updated` 算法从未成功执行完。
- `Single_Run_Test_Results_*.json`（`Single_Run_Test_Framework_Updated.py:94`）→ 不存在（`:95-96` 只有 `pass`）。
- `test_chart_fix.png`、`test_improved_multi_run_chart.png`、`Inter_Players_Complete_Analysis.xlsx`、`Inter_Contracts_from_soccerdata_SoFIFA.xlsx` → 均不存在。

### 3.7 实测环境依赖缺口

venv（Python 3.11.9）实测：`pandas` / `numpy` / `scipy` / `sklearn` / `matplotlib` / `seaborn` / `skopt` / **`soccerdata` ✅ 已安装**；**`openpyxl` ❌**、**`xlsxwriter` ❌**、`statsmodels` ❌。
→ 直接导致 `manual_integration.py:50` 与 `test.py:15` 的 xlsx 写出必然失败。

### 3.8 CSV 列映射与脏行（已实测复核，纠正一处流传的说法）

- **不存在 off-by-one 错位**。`ITA_SerieA_player_standard_stats_2022_2023.csv` 前 3 行均为 37 字段，核心模块传入的 `names` 也是 **37 个**（实测 `len(names)=37`）。实测 `pd.read_csv(skiprows=3, names=names)` 得到 `(603, 37)`，`team` 列正确解析出 `Atalanta/Bologna/.../Inter`，**`team=='Inter'` 命中 25 行**，`pos` 列正确为 `FW,MF`/`DF`/`GK` 等，`Min` 为 int 且 520 行 > 90。
- **但存在一条脏数据行**（真实且静默）：位置类 CSV（goal/shooting/passing/possession/defensive/goalkeeper）用 `skiprows=2 + names` 读取时，第 3 行 `league,season,team,player,...` 会作为**数据行**保留。实测 `pd.read_csv(goal_stats, skiprows=2, names=[...])` 得 `(604, 25)`，其中 `iloc[0]['team']=='team'`、`iloc[0]['player']=='player'`。不加 `names` 时得 `(603, 25)` 且首行即真实数据。该脏行被各处的 `pos.str.contains(..., na=False)` 过滤掉，故**静默无害但确为 bug**，影响 6 个位置数据集。
- `2023_2024_Prediction.py:39` 用 `skiprows=2 + names` 读 standard stats（同族文件正确应为 `skiprows=3`）→ 同样混入一条脏行，被 `:59` 的 `team == 'Inter'` 过滤掩盖。

### 3.9 文档声称 vs 代码实际（"有文档无代码"/"有代码无调用"）

| 文档声称 | 代码实际 |
|---|---|
| 算法包含"贝叶斯优化 / 遗传算法 / 网格搜索 / 多目标优化"（`Weight_Optimization_Framework.py:9-13` 自述） | 第一代框架 `:253/308/353/423` **确实实现了贝叶斯、GA（差分进化）、网格搜索、随机搜索**；但**"多目标优化"只在 `objective_function:240-241` 用 `0.7*accuracy + 0.3*f1` 加权和模拟，没有真正的 Pareto 多目标**。最终流水线**完全没有继承**这四个算法，只保留了 GA/PSO/SA/RS 四个元启发式 |
| 论文方法为"相对百分位排名的**多层次**概率融合" | 最终引擎只加载 `2022-2023` 赛季数据（`weight_optimization_core_updated.py:23/67/73/83/90/102/112`），**没有跨赛季/跨层级的融合结构**；`2023-2024` 数据仅被 `2023_2024_Prediction.py` 用于事后预测 |
| "合同剩余年限"为核心特征 | `Contract_2022_2023.csv` / `Contract_2023_2024.csv` **存在但全项目无任何代码读取**（§一.3） |
| 算法对比含 4 个元启发式 | `Multi_Algorithm_Comparison_Experiment.py` 对比的 4 个模块**全部不存在** → 该对比从未运行；真正跑通的是 `_Final` + `Multi_Run_Experiment_Framework_Final.py` |
| `Generalization_Testing_Framework.py` 提供泛化能力测试 | 600 行框架零实例化，`__main__` 只打印 4 行说明 |
| `Enhanced_Evaluation_Metrics_Framework.py` 提供增强评估指标 | 无任何调用方，唯一驱动喂的是 `np.random.beta`/`np.random.binomial` 合成数据（`:266-267`），财务数字（`:169-171` 的 2500 万/200 万/15%）为硬编码假想值 |
| `Statistical_Significance_Testing_Framework.py` 提供 Bootstrap CI / McNemar | 这两个检验**代码确实存在**（`:239-322` / `:324-406`），但**从未被真实数据驱动**（`:527-533` 用 `np.random` 造假），且无产物文件 |
| `test_basic_experiment.py` 声称"EXPERIMENT SUMMARY" | `:29-75` 全部硬编码 |

---

## 四、同一算法多版本差异（`_Clean` / `_Updated` / `_Final` 三代）

> 本节回答"逻辑到底变了什么"，而非"文件大小不同"。三代之间发生了**三次实质性重构**：数据源、搜索空间维度、概率模型。

### 4.0 三代总览

| 维度 | `_Clean`（2025-08-13） | `_Updated`（2025-08-26 02:xx） | `_Final`（2025-08-26 12:xx） |
|---|---|---|---|
| 数据加载 | 4 份各自复制 `load_data()`（`GA_Clean.py:16-56`） | GA 内联全部（`GA_..._Updated.py:13-278`）；PSO/SA/RS 从**不存在的** `Enhanced_...` 导入 | 统一 `from weight_optimization_core_updated import ...`（`GA_..._Final.py:11-15`） |
| 数据集 | **仅 standard 表**，`Min > 90` 过滤（`GA_Clean.py:28`） | standard + goal + shooting + passing + possession + defensive + goalkeeper | 同 `_Updated` |
| 指标来源 | `get_position_specific_metrics()` 里**所有指标 `source='standard'`**（`GA_Clean.py:94-139`） | 真正的多表来源（`source` ∈ standard/goal/shooting/passing/possession/defensive/goalkeeper/contract） | 同 `_Updated` |
| 搜索空间 | **42 维**（每位置 10 权重 + base_risk + risk_multiplier），`bounds` 循环拼接（`GA_Clean.py:265-271`） | **17 维**（5 通用 + 10 位置 + 2 风险） | **17 维**，但 `get_bounds` 明确排除 `age`/`Contract_expires`（`GA_..._Final.py:33`） |
| 概率模型 | `base_risk + (1-normalized_score)*risk_multiplier`（`GA_Clean.py:180`） | `base_risk + (1-performance_score)*risk_multiplier + contract_adjustment`（`GA_..._Updated.py:380`，乘性风险调整） | `base_risk_sigmoid(age, contract_years, alpha, tau) + (1-performance_score)*risk_multiplier`（core `:324-326`，sigmoid + alpha/tau） |
| 优化器 | GA 用 `differential_evolution`；PSO/SA/RS 自写类 | GA 用 `differential_evolution(maxiter=20, popsize=10, seed=42)` | 同 `_Updated`（GA），PSO 30×50、SA 1000 次、RS 1500 次 |
| 可否运行 | ✅ 能跑（自包含） | ❌ PSO/SA/RS 不可导入；仅 GA 可跑 | ✅ 全部能跑 |
| 落盘 | 各写自身 JSON | 仅 PSO/SA/RS 写 JSON（GA 不写） | 由上层框架统一写 |

### 4.1 `_Clean` → `_Updated`：数据源与搜索空间的双重重构

**(a) 指标→列名映射从"占位错配"改为"真实多表"** —— 这是最关键的一步。
`_Clean` 代把语义响亮但物理无意义的列硬映射到 standard 表，例如 `GA_Clean.py:124-127`（三个文件逐字相同）：

```python
124: 'tackles': {'source': 'standard', 'column': 'CrdY', ...}      # 抢断 := 黄牌数
125: 'interceptions': {'source': 'standard', 'column': 'PrgR', ...}  # 拦截 := 接球推进
126: 'blocks': {'source': 'standard', 'column': 'CrdR', ...}         # 封堵 := 红牌数
127: 'clearances': {'source': 'standard', 'column': 'PK', ...}       # 解围 := 点球数
```
以及 Goalkeeper（`GA_Clean.py:132-139`）：`'saves': {'column': 'GA'}`（扑救 := 失球数）、`'wins': {'column': 'MP'}`（胜场 := 出场数）、`'clean_sheets': {'column': 'PK'}`。
`_Updated`/`_Final` 改为真实来源，例如 core `:159-168`：`'Tkl': {'source': 'defensive', 'column': 'Tkl'}`、`'Clr': {'source': 'defensive', 'column': 'Clr'}`、`'Def_3rd': {'source': 'possession', 'column': 'Def_3rd'}`。
→ **同一份"算法对比"在 `_Clean` 代与 `_Final` 代测的根本不是同一组特征**，两代的指标表不可互相引用。

**(b) 搜索空间从 42 维收缩到 17 维。**
`_Clean` 为 4 个位置 × (10 权重 + `base_risk` + `risk_multiplier`) = 42 个参数一次性全局优化（`GA_Clean.py:265-271`）。`_Final` 改为**按位置分别优化**（`GA_..._Final.py:106-116` 外层 for 位置、内层 1 次 `optimize()`），每个位置 5 通用 + 10 位置 + 2 风险 = **17 维**。代价是 `_Final` 的 `get_bounds:33` 显式 `continue` 掉 `age`/`Contract_expires`，把两个原本在 `_Clean` 中参与优化的量彻底移出搜索空间。

**(c) 概率模型：从常数基线改为 sigmoid 风险。**
- `_Clean`：`departure_probability = base_risk + (1 - normalized_score) * risk_multiplier`，`base_risk` 是**搜索变量**（`_Clean` bounds 中 `(0.2,0.4)`），并用 `max(0.0, min(1.0, ...))` 截断（`GA_Clean.py:180-181`）。
- `_Updated`（`GA_..._Updated.py:380`）：新增 `contract_adjustment` 项，由 `calculate_contract_risk_adjustment:284-341` 计算 —— 一个**乘性分段规则表**（`base_contract_risk` 按 `contract_years` 分档 `:293-300`，再乘 `performance_modifier` `:301-311`、`age_modifier` `:312-325`、`position_modifier` `:326-339`）。它保留 `base_risk` 作为**加性常数**（`:345`）。
- `_Final`（core `:324-326`）：删除 `contract_adjustment`，改用 `calculate_base_risk_sigmoid(age, contract_years, alpha, tau)`（core `:280-287`）—— `alpha` 与 `tau` 成为**新的搜索维度**（`_Final.py:51-52` 的 `(1.0,4.0)` / `(0.3,0.7)`），且 **`base_risk` 权重被完全忽略**（core `:289-327` 全文不读 `base_risk`），但 `_Final` 的 bounds **仍在生成 `base_risk` 维度**（`GA_..._Final.py:50-54`）→ 每个位置有 1 个**空转维度**。

**(d) 通用指标层的引入。**
`_Clean` 没有"通用指标"概念（`get_position_specific_metrics` 一个扁平 dict）。`_Updated`/`_Final` 拆成 `get_universal_metrics()`（core `:123-130`：minutes/age/CrdY/CrdR/Contract_expires）+ `get_position_specific_metrics()`（core `:132-182`），并在概率计算中**分块加权再合并**（core `:297-316` 先累加 `universal_score`/`universal_weight`，再累加 `position_score`/`position_weight`，最后 `(universal_score+position_score)/(universal_weight+position_weight)`）。这是论文"多层次概率融合"在代码中**唯一真实落地**的地方 —— 而 `_Clean` 代是单层扁平加权。

**(e) 反向证据：`_Updated` 是相对 `_Final` 的回归。**
虽同为 08-26，但时间戳显示 `_Updated`（02:06–02:24）**早于** `_Final`（12:24–12:28）约 10 小时，且 `_Updated` 引用的模块不存在、`_Final` 引用存在的模块。**且即便删掉时间戳，`_Final` 在结构上也更先进**：`GA_Weight_Optimization_Experiment_Updated.py:13-278` 把 core 的 7 个函数**逐字节内联**（实测 identical），这在工程上是"复制粘贴回退"，而 `_Final` 是"抽成公共模块"。因此 `_Updated` 是**过渡态**，不是"更早但更完整"的版本。

### 4.2 `_Updated` → `_Final`：三个实质变化

**(1) 概率模型从"加性合同调整"改为"sigmoid 基线 + alpha/tau"** —— 见 §4.1(c)。差异可直接对照：
- `_Updated`：`departure_prob = base_risk + (1 - performance_score) * risk_multiplier + contract_adjustment`（`GA_..._Updated.py:380`）
- `_Final`：`base_risk = calculate_base_risk_sigmoid(...)`；`departure_prob = base_risk + (1 - performance_score) * risk_multiplier`（core `:324-326`）
→ `_Updated` 中 `contract_adjustment` 可达 1.0（`:341` `return max(0.0, min(1.0, contract_risk))`），加上 `base_risk` 后极易撞上 `max(0.05, min(0.95, ...))`（`:381`）的**上界饱和**，所有高风险球员被压成同一概率 → 排序失去区分度。`_Final` 的 `calculate_base_risk_sigmoid` 用 `np.clip(base_risk, 0.1, 0.3)`（core `:287`）把基线压在窄区间，理论上排序更稳定。**这是两代最重要的单点差异。**

**(2) 空转维度的分布变了。**
- `_Updated` 的 `get_bounds`（`GA_..._Updated.py:398-420`）**不排除 age**，且 `_Updated` 版概率函数**只跳过 `Contract_expires`**（`:355-356`）→ `age_weight` 与 `base_risk` 在 `_Updated` 中**是有效维度**。
- `_Final` 的 `get_bounds:33` 排除 `age`/`Contract_expires`，而 core 的概率函数**既不读 `base_risk` 也不读 `age`**（core `:289-327`）→ `_Final` 每位置有 **1 个空转维度**（`base_risk`），`_Updated` 每位置有 **1 个空转维度**（`Contract_expires`）。
→ **两代的"17 维"含义不同、有效维度也不同**，不可直接比较"搜索空间大小"。

**(3) 内联副本 vs 单一真相源。**
`GA_..._Updated.py:13-278` 与 `weight_optimization_core_updated.py` 的前 7 个函数**逐字节相同**（`calculate_departure_probability_with_weights` 除外，见下）。这带来两个具体后果：
- `_Updated` 版的 `calculate_departure_probability_with_weights`（`:343-381`）与 core 版（`:289-327`）**已经不一致**：前者用 `base_risk` + 乘性 `contract_adjustment`，后者用 sigmoid + `alpha/tau`。**同名同签名的函数在两代里是不同算法** —— 这是最危险的坑：`GA_..._Updated.py` 的 `run_ga_weight_optimization()` 与 `GA_..._Final.py` 的 `run_ga_weight_optimization()` 会给出**不可比**的分数，而外部框架用同一套 `evaluate_weights_enhanced` 口径去汇总它们。
- `_Updated` 无条件跳过 `age`（`:355-356` 只 `if metric_name == 'Contract_expires'`），core 跳过 `age` 与 `Contract_expires`（core `:300`）→ **同一个 `age_weight` 在两代中的作用相反**。

### 4.3 四算法之间的重复（`_Final` 内部）

`GA/PSO/SA/RS_Weight_Optimization_Experiment_Final.py` 的 `get_bounds()` **四份逐字相同**（已用文本比对确认 4 份 `get_bounds` 完全一致：通用权重 `(0.08,0.15)`、`Contract_expires (0.05,0.12)`、重要指标列表 `['Gls','xG','SoT','SCA','GCA']` / `['Ast','xAG','KP','Cmp_pct','PrgP']` / `['Tkl','Int','Blocks','Clr','Cmp_pct']` / `['Saves','Save_pct','CS','CS_pct']`、`alpha (1.0,4.0)` / `tau (0.3,0.7)` / `risk_multiplier (0.3,0.7)`）。
`fitness_function()` **四份也相同**，唯一差异是返回符号：`GA:68` `return -score`（配合 `differential_evolution` 最小化），`PSO:67` / `SA:68` / `RS:68` `return score`（各自算法最大化）。
→ 建议把 `get_bounds` 与 fitness 提取到 `weight_optimization_core_updated.py`（例如 `get_weight_bounds(position, universal, position_metrics)` 与 `fitness(weights_array, ...)`），4 个文件只保留搜索循环。当前重复量约 4 × 30 行 = 120 行。

---

## 五、需要人工复核 / 我不确定的地方

1. **`Contract_expires` 的语义未经核对。** `Contract_2022_2023.csv` 的 `Contract_expires` 取值为 `0/1/4`（实测前 4 行：Bastoni=1、Cordaz=0、Onana=4、D'Ambrosio=0），`Contract_2023_2024.csv` 还出现 `-1`（Carlos Augusto）。这可能表示"剩余年限"，也可能是"合同到期年份末两位"。`GA_..._Updated.py:285` 的 `if contract_years == -1` 说明作者知道 `-1` 是特殊值，但**没有任何注释或文档说明编码约定**。若要在核心中接回合同特征，必须先确认编码。未核实。

2. **`2023_2024_Prediction.py:84-157` 的硬编码 PSO 权重无法溯源。** 这批 `alpha`/`tau`/`*_weight` 数值我在 `Optimal_Weights_20250813_003733.txt`、`Optimal_Weights_20250814_022008.txt`、`Optimal_Weights_20250818_185855.txt` 中未逐一比对确认。建议人工比对 `2023_2024_Prediction.py:84-157` 与 `Optimal_Weights_*.txt` 的具体数值。未核实。

3. **`Statistical_Testing_Framework.py` 的 4 个产物文件是否全部为伪造。** 我已确认 `Statistical_Test_Results_20250826_182039.txt` 的前 9-11 行与 `create_sample_data_for_testing()` 复算结果**逐位相同**。但 `20250831_231510/231752/232028` 三个文件我只通过子代理的二手结论得知结构相似，**未亲自逐行比对**。建议人工 diff 这 4 个文件。

4. **`_Updated` 与 `_Final` 的真实先后关系。** 我依据的是文件系统 mtime（`_Updated` 02:06–02:24 早于 `_Final` 12:24–12:28）与"引用的模块是否存在"。但 mtime 可能被复制/解压操作改写。**若这些文件是从某处整体拷贝而来，mtime 会失真**。可交叉验证的证据是：`Algorithm_Modification_Documentation.md`（2025-08-26 02:14）与 `_Updated` 同批，可能记录了改动意图 —— 我**未阅读这些 .md 文档**（任务范围限定 .py）。建议人工阅读 `Algorithm_Modification_Documentation.md`、`Project_Continuity_Documentation.md` 以确认代际叙述。

5. **`weight_optimization_core.py`（旧版）是否曾被最终流水线使用。** 该文件的结构性缺陷（`:262` `position_datasets[source_dataset]` 而实际键为位置名）意味着它的非 standard 指标全部走 0.5 兜底。但它在 2025-08-13 19:02 被修改，比 `_Clean` 代（18:24–18:27）晚 35 分钟，说明它在 `_Clean` 代之后仍被主动维护过。**它到底服务于哪条链路我未追溯清楚**（没有任何现存文件 import 它）。建议人工 grep 确认它是否只是被手工运行过一次。

6. **`test.py` 与合同数据的因果关系未证实。** 我推断 `test.py`（用 soccerdata 抓 SoFIFA 导出合同/身价）是为了获得合同数据，但 `data/` 下的 soccerdata 缓存只有 `players_*_standard.html` / `teams_*_stats.html` / `leagues.html`，**没有 SoFIFA 相关缓存**。所以 `test.py` 可能从未成功运行过，`Contract_2022_2023.csv` 的来源是别的途径（手工整理？）。未证实。

7. **`_Final` 的 GA 适应度符号是否存在隐患。** `GA_..._Final.py:68` 返回 `-score`，而 `:66-67` 的 `if score > (self.best_result or -1)` 用的是**未取负**的 `score`。逻辑上一致（`best_result` 存原始分），但我未验证 `differential_evolution` 在高维（17 维）低样本（25 球员）下的收敛行为，也未实测 `polish=True` 默认值带来的额外 L-BFGS-B 阶段是否会使返回的 `result.x` 越出 bounds。未运行验证。

8. **样本量问题。** 实测 `team=='Inter'` 在 2022-2023 standard stats 中为 **25 行**，位置分布为 Defender 15 / Midfielder 6 / Forward 4 / Goalkeeper 3（按精确 `pos` 字符串），标签为 **13 离队 / 12 留队**。`GA_..._Final.py:107-109` 对每个位置单独优化，意味着 **Goalkeeper 只用 3 个样本优化 17 个参数**。这是否构成过拟合、论文是否有说明，我**无法从代码判断**（需看论文正文）。`evaluate_weights_enhanced`（core `:344`）在 `predictions` 为空时返回 `0.0`，`len(set(actuals)) > 1` 失败时用 `composite_score = accuracy`（core `:360`）—— 3 个样本下极易触发退化分支。建议人工评估这是否是算法对比结果（GA/PSO/RS 均 0.9200，SA 0.6400）的真实来源。

9. **`Multi_Run_Experiment_Framework_Final.py` 是否真的产出了 `Multi_Run_Experiment_Results_20250826_171631.json`。** 时间戳吻合（框架 mtime 14:00，产物 17:16），且产物 JSON 含 `n_runs`/`global_best`/`results`/`best_weights_per_algorithm`（与 `:175-176` 写出结构一致）。但**如果图表生成在 `:328-333` 抛异常，是否会中断整个 `run_experiment`** 我不确定 —— 该异常被 try/except 包裹，理论上不影响 JSON 落盘。未运行验证。

---

## 附录：54 个文件按去留建议汇总

| 建议 | 数量 | 文件 |
|---|---|---|
| **直接复用** | 9 | `weight_optimization_core_updated.py`；`GA_Weight_Optimization_Experiment_Final.py`、`PSO_Weight_Optimization_Experiment_Final.py`、`SA_Weight_Optimization_Experiment_Final.py`、`RS_Weight_Optimization_Experiment_Final.py`；`Single_Run_Test_Framework_Final.py`、`Multi_Run_Experiment_Framework_Final.py`；`Algorithm_Comparison_Visualization.py`；`Simple_Chart_Generator.py` |
| **重构后复用** | 4 | `Statistical_Testing_Framework.py`（删 `:72-105` 伪造路径，强制传真实 JSON）、`2023_2024_Prediction.py`（删两处旧机绝对路径 + 修 `skiprows`）、`test_weight_optimization.py`（升级为正式集成测试）、`Multi_Run_Experiment_Framework_Final.py` 的绘图接入（属上文直接复用的同一文件，单独列为一项待办而非独立文件） |
| **仅作历史参考** | 13 | `weight_optimization_core.py`、`GA_Weight_Optimization_Experiment_Updated.py`、`GA_Clean.py`、`PSO_Clean.py`、`SA_Clean.py`、`RS_Clean.py`、`Multi_Algorithm_Comparison_Clean.py`、`Weight_Optimization_Framework.py`、`Weight_Optimization_Experiment.py`、`Fixed_Weight_Optimization_Experiment.py`、`Statistical_Significance_Testing_Framework.py`、`Player_Departure_Predictor_2023_2024.py`、`Working_Prediction_Demo_2023_2024.py` |
| **仅作历史参考（次要）** | 2 | `simple_weight_experiment.py`、`test.py` |
| **建议退役** | 28 | `PSO_Weight_Optimization_Experiment_Updated.py`、`SA_Weight_Optimization_Experiment_Updated.py`、`RS_Weight_Optimization_Experiment_Updated.py`、`Single_Run_Test_Framework_Updated.py`、`Multi_Run_Experiment_Framework_Updated.py`、`Multi_Algorithm_Comparison_Experiment.py`、`Run_Statistical_Tests.py`、`Generalization_Testing_Framework.py`、`Enhanced_Evaluation_Metrics_Framework.py`、`manual_integration.py`、`simple_prediction_test.py`、`simple_weight_optimization_demo.py`、`main.py`、`111.py`、`11111.py`、`222.py`、`444.py`、`555.py`、`tax.py`、`basic_test.py`、`def_possession.py`、`test_chart_fix.py`、`test_multi_run_quick.py`、`test_fixed_framework.py`、`test_prediction_model.py`、`test_prediction_directly.py`、`test_basic_experiment.py`（**另需隔离**） |

**合计校验**（三分类互斥且完整）：
- 直接/重构后复用 = **12**：核心引擎 1 + `_Final` 算法 4 + `_Final` 框架 2 + 可视化 2 + 统计框架 1 + 预测应用 1 + 集成测试 1 = 12
- 仅作历史参考 = **15**
- 建议退役 = **27**（含 `test_basic_experiment.py`，需额外隔离）
- 合计 **12 + 15 + 27 = 54** ✅ 与目录实测 54 个 `.py` 一致

**主表格行数校验**：A 2 + B 12 + C 8 + D 5 + E 2 + F 5 + G 20 = **54** ✅ 与目录实测逐名比对，无遗漏、无重复。

> 注：`test_basic_experiment.py`、`def_possession.py`、`test_chart_fix.py`、`test_multi_run_quick.py` 四个文件除退役外，还应**明确标注其输出不可作为实验证据**（§一.10、§三.9）。
