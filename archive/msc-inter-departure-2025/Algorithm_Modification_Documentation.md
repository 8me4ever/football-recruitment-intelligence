# 算法修改说明文档

## 项目概述

本文档详细说明了四个权重优化算法文件的修改情况，包括新的5个通用指标+10个位置特色指标系统的实现，以及复杂合同算法的集成。

---

## 修改目标

### 主要需求
1. **新指标体系**: 将原有指标系统替换为5个通用指标+10个位置特色指标
2. **复杂合同算法**: 集成考虑合同剩余时间、年龄、表现和位置的复杂离队概率计算
3. **算法逻辑保持**: 保持各算法核心优化逻辑不变
4. **代码可执行性**: 确保修改后的代码逻辑正确且可运行

---

## 新指标体系设计

### 5个通用指标
所有位置球员都使用这5个通用指标：

| 指标名称 | 数据来源 | 列名 | 排序方向 | 说明 |
|---------|---------|------|---------|------|
| minutes | standard | Min | 升序↗️ | 上场时间，越多越好 |
| age | standard | age | 降序↘️ | 年龄，越年轻越好 |
| CrdY | standard | CrdY | 降序↘️ | 黄牌数，越少越好 |
| CrdR | standard | CrdR | 降序↘️ | 红牌数，越少越好 |
| Contract_expires | contract | Contract_expires | 降序↘️ | 合同剩余时间，越短离队风险越高 |

### 10个位置特色指标

#### 前锋 (Forward) - 强调进攻和创造
| 指标名称 | 数据来源 | 列名 | 说明 |
|---------|---------|------|------|
| Gls | standard | Gls | 进球数 |
| Ast | standard | Ast | 助攻数 |
| xG | shooting | xG | 预期进球 |
| SoT | shooting | SoT | 射正次数 |
| G_per_Sh | shooting | G_per_Sh | 每次射门进球率 |
| Sh_per90 | shooting | Sh_per90 | 每90分钟射门次数 |
| SCA | goal | SCA | 射门创造行动 |
| GCA | goal | GCA | 进球创造行动 |
| Att_Pen | possession | Att_Pen | 禁区内触球 |
| TakeOn_Succ | possession | TakeOn_Succ | 成功过人 |

#### 中场 (Midfielder) - 强调传球和组织
| 指标名称 | 数据来源 | 列名 | 说明 |
|---------|---------|------|------|
| Ast | standard | Ast | 助攻数 |
| xAG | passing | xAG | 预期助攻 |
| KP | passing | KP | 关键传球 |
| Cmp_pct | passing | Cmp_pct | 传球成功率 |
| PrgP | passing | PrgP | 前进传球 |
| Touches | possession | Touches | 触球次数 |
| PrgC | possession | PrgC | 前进带球 |
| TakeOn_Succ | possession | TakeOn_Succ | 成功过人 |
| Tkl | defensive | Tkl | 抢断次数 |
| SCA | goal | SCA | 射门创造行动 |

#### 后卫 (Defender) - 强调防守和传球
| 指标名称 | 数据来源 | 列名 | 说明 |
|---------|---------|------|------|
| Tkl | defensive | Tkl | 抢断次数 |
| Int | defensive | Int | 拦截次数 |
| Blocks | defensive | Blocks | 封堵次数 |
| Clr | defensive | Clr | 解围次数 |
| Tkl_pct | defensive | Tkl_pct | 抢断成功率 |
| Cmp_pct | passing | Cmp_pct | 传球成功率 |
| Cmp_pct_Long | passing | Cmp_pct_Long | 长传成功率 |
| PrgP | passing | PrgP | 前进传球 |
| Final_Third | passing | Final_Third | 前场传球 |
| Def_3rd | possession | Def_3rd | 防区控球 |

#### 守门员 (Goalkeeper) - 强调扑救和表现
| 指标名称 | 数据来源 | 列名 | 说明 |
|---------|---------|------|------|
| Saves | goalkeeper | Saves | 扑救次数 |
| Save_pct | goalkeeper | Save_pct | 扑救成功率 |
| CS | goalkeeper | CS | 零封次数 |
| CS_pct | goalkeeper | CS_pct | 零封率 |
| GA90 | goalkeeper | GA90 | 每90分钟失球 |
| SoTA | goalkeeper | SoTA | 面临射门 |
| PK_Save | goalkeeper | PK_Save | 点球扑救 |
| PK_Save_pct | goalkeeper | PK_Save_pct | 点球扑救率 |
| W | goalkeeper | W | 胜场数 |
| Cmp_40_plus | goalkeeper | Cmp_40_plus | 40码以上传球成功 |

---

## 复杂合同算法设计

### 算法逻辑

复杂合同算法考虑四个维度计算离队风险调整：

#### 1. 合同时长基础风险
```python
if contract_years <= 0.5:
    base_contract_risk = 0.6  # 合同即将到期，高风险
elif contract_years <= 1:
    base_contract_risk = 0.4  # 一年内到期，中等风险
elif contract_years <= 2:
    base_contract_risk = 0.2  # 两年内到期，低风险
else:
    base_contract_risk = 0.1  # 长期合同，很低风险
```

#### 2. 表现修正系数
- **高表现球员** (>80%): 合同短有续约机会，合同长仍有转会风险
- **中等表现球员** (60%-80%): 基础风险不变
- **低表现球员** (40%-60%): 增加30%离队风险
- **极低表现球员** (<40%): 增加60%离队风险

#### 3. 年龄修正系数
- **年轻球员** (<23岁): 高潜力者更可能留下，低表现者可能被卖掉
- **黄金年龄** (23-28岁): 转会价值最高，轻微增加离队风险
- **成熟球员** (28-32岁): 经验丰富，离队风险较低
- **老将** (>32岁): 高表现仍有价值，低表现离队风险高

#### 4. 位置特定修正
- **守门员**: 职业生涯更长，35岁以上风险增加
- **后卫**: 经验更重要，30岁以上高表现者风险降低
- **前锋/中场**: 标准修正

#### 5. 租借球员特殊处理
```python
if contract_years == -1:  # 租借球员
    if performance_score > 0.7 and age < 30:
        return 0.3  # 高表现年轻球员有机会获得永久合同
    elif performance_score > 0.6:
        return 0.5  # 中等表现有一定机会留下
    else:
        return 0.8  # 低表现租借球员离队风险很高
```

---

## 文件修改详情

### 1. Enhanced_Weight_Optimization_Experiment.py (原GA算法)

**核心修改**:
- ✅ 添加 `get_universal_metrics()` 函数
- ✅ 更新 `get_position_specific_metrics()` 为新的10指标结构
- ✅ 修改 `calculate_enhanced_percentile_scores()` 支持通用+位置指标
- ✅ 添加 `calculate_contract_risk_adjustment()` 复杂合同算法
- ✅ 更新 `calculate_departure_probability_with_weights()` 集成合同风险
- ✅ 修正位置专门数据集访问逻辑

**算法特点**: 使用差分进化算法，全局搜索能力强，适合复杂优化问题

### 2. RS_Weight_Optimization_Experiment_Updated.py (随机搜索)

**新建文件特点**:
- 🆕 完全基于新指标体系构建
- 🆕 集成复杂合同算法
- 🆕 智能随机搜索策略（探索+利用阶段）
- 🆕 多样性维护机制
- 🆕 实时进度显示

**算法优势**: 实现简单，对参数不敏感，适合作为基准算法

### 3. SA_Weight_Optimization_Experiment_Updated.py (模拟退火)

**新建文件特点**:
- 🆕 完全基于新指标体系构建
- 🆕 集成复杂合同算法
- 🆕 多种冷却策略（指数、线性、对数、自适应）
- 🆕 动态邻域生成
- 🆕 接受率监控

**算法优势**: 能够跳出局部最优，温度控制允许接受较差解，适合复杂搜索空间

### 4. PSO_Weight_Optimization_Experiment_Updated.py (粒子群优化)

**新建文件特点**:
- 🆕 完全基于新指标体系构建
- 🆕 集成复杂合同算法
- 🆕 自适应参数调整（惯性权重、学习因子）
- 🆕 群体多样性监控
- 🆕 多样性维护（粒子重启机制）

**算法优势**: 群体智能，平衡探索和利用，收敛速度较快

### 5. GA_Weight_Optimization_Experiment_Updated.py (遗传算法)

**新建文件特点**:
- 🆕 基于Enhanced版本的遗传算法专门实现
- 🆕 使用差分进化作为遗传算法变体
- 🆕 种群多样性跟踪
- 🆕 收敛速度分析
- 🆕 自适应变异和交叉策略

**算法优势**: 生物启发优化，全局搜索能力强，适合多模态优化问题

---

## 技术实现细节

### 数据加载架构
```python
# 位置专门数据集结构
position_datasets = {
    'Forward': {
        'goal': DataFrame,     # 进球创造数据
        'shooting': DataFrame  # 射门数据
    },
    'Midfielder': {
        'passing': DataFrame,     # 传球数据
        'possession': DataFrame   # 控球数据
    },
    'Defender': {
        'passing': DataFrame,    # 传球数据
        'defensive': DataFrame   # 防守数据
    },
    'Goalkeeper': {
        'goalkeeper': DataFrame,         # 基础守门员数据
        'goalkeeper_advance': DataFrame  # 高级守门员数据
    }
}
```

### 权重优化边界
```python
# 权重边界策略
bounds = {
    # 通用指标权重
    'minutes_weight': (0.08, 0.15),
    'age_weight': (0.08, 0.15),
    'CrdY_weight': (0.08, 0.15),
    'CrdR_weight': (0.08, 0.15),
    'Contract_expires_weight': (0.05, 0.12),  # 合同权重较低
    
    # 位置特色指标权重（10个指标）
    # 重要指标: (0.08, 0.15)
    # 一般指标: (0.05, 0.12)
    
    # 风险参数
    'base_risk': (0.2, 0.4),
    'risk_multiplier': (0.3, 0.7)
}
```

### ML评估指标
所有算法使用统一的综合评分系统：
```python
composite_score = (
    0.40 * pr_auc +           # 40%: 不平衡数据排序能力
    0.30 * f1_score +         # 30%: 精确率召回率平衡
    0.20 * balanced_acc +     # 20%: 平衡分类能力
    0.10 * (1 - brier_score)  # 10%: 概率校准质量
)
```

---

## 使用说明

### 运行单个算法
```bash
# 随机搜索
python RS_Weight_Optimization_Experiment_Updated.py

# 模拟退火
python SA_Weight_Optimization_Experiment_Updated.py

# 粒子群优化
python PSO_Weight_Optimization_Experiment_Updated.py

# 遗传算法
python GA_Weight_Optimization_Experiment_Updated.py
```

### 导入使用
```python
# 导入特定算法函数
from RS_Weight_Optimization_Experiment_Updated import run_rs_weight_optimization
from SA_Weight_Optimization_Experiment_Updated import run_sa_weight_optimization
from PSO_Weight_Optimization_Experiment_Updated import run_pso_weight_optimization
from GA_Weight_Optimization_Experiment_Updated import run_ga_weight_optimization

# 运行算法
results_rs = run_rs_weight_optimization()
results_sa = run_sa_weight_optimization()
results_pso = run_pso_weight_optimization()
results_ga = run_ga_weight_optimization()
```

---

## 输出格式

### 控制台输出
每个算法都会输出以下信息：
1. **指标体系说明**: 5个通用指标 + 10个位置特色指标
2. **优化过程**: 实时进度和最佳适应度
3. **最终权重**: 每个位置的优化权重配置
4. **ML性能指标**: 基础指标 + 增强ML指标
5. **球员预测结果**: 每个球员的详细预测和实际结果对比

### JSON结果文件
```json
{
  "timestamp": "2025-08-26T...",
  "algorithm": "Algorithm Name",
  "metric_system": "5通用指标 + 10位置特色指标",
  "data_summary": {
    "total_inter_players": 20,
    "positions_analyzed": ["Forward", "Midfielder", "Defender"]
  },
  "positions": {
    "Forward": {
      "player_count": 4,
      "optimization_result": {...}
    }
  },
  "ml_metrics": {
    "accuracy": 0.85,
    "pr_auc": 0.78,
    "cohen_kappa": 0.72,
    ...
  },
  "predictions": [...],
  "optimized_weights": {...},
  "execution_time": 45.2
}
```

---

## 技术优势

### 1. 指标体系改进
- **通用性**: 5个通用指标确保所有球员可比较
- **专业性**: 10个位置特色指标体现位置专业要求
- **全面性**: 涵盖表现、年龄、纪律、合同等多维度

### 2. 合同算法创新
- **多维考量**: 合同时长、表现、年龄、位置四维分析
- **现实性**: 符合足球转会市场实际规律
- **灵活性**: 租借球员特殊处理逻辑

### 3. 算法鲁棒性
- **多样性维护**: 避免过早收敛
- **参数自适应**: 动态调整搜索策略
- **性能监控**: 实时跟踪优化进展

### 4. 评估体系完善
- **不平衡数据处理**: PR-AUC作为主要指标
- **统计显著性**: Cohen's Kappa消除偶然性
- **概率校准**: Brier Score评估概率质量

---

## 总结

本次修改成功实现了用户要求的两个核心目标：

1. ✅ **新指标体系**: 完整实现5个通用指标+10个位置特色指标系统
2. ✅ **复杂合同算法**: 集成考虑多维度因素的合同风险评估

四个更新后的算法文件保持了各自的核心优化逻辑，同时统一采用新的指标体系和合同算法，为球员离队预测提供了更加精确和实用的解决方案。

所有代码经过精心设计，确保逻辑正确性和可执行性，为后续的实验分析和模型部署奠定了坚实基础。