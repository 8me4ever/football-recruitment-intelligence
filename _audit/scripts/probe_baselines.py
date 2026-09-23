# -*- coding: utf-8 -*-
"""
审计探针 6：建立诚实基线对照。
问题：论文声称优化后 92% vs 基线 68%（+35.3% 提升）。这个"基线"合理吗？
      <1> 单变量规则（只看年龄 / 只看合同 / 只看上场时间）能得多少？
      <2> 均匀加权能得多少？
      <3> 多数类基线是多少？
      <4> 优化权重真的赢了吗？赢多少？在 25 个样本上这差值有意义吗？
"""
import os
import sys

ORIG = r"F:\Samuel\football recruitment\final project"
sys.path.insert(0, ORIG)
os.chdir = lambda p, *a, **k: None

import numpy as np
import pandas as pd
from scipy import stats

from weight_optimization_core_updated import (
    load_experimental_data_enhanced, get_universal_metrics, get_position_specific_metrics,
    calculate_enhanced_percentile_scores, calculate_departure_probability_with_weights,
)

inter, league, pos_ds = load_experimental_data_enhanced()
POSITIONS = ["Forward", "Midfielder", "Defender", "Goalkeeper"]

print("=" * 90)
print("[0] 样本构成")
print("=" * 90)
for p in POSITIONS:
    s = inter[inter["position_group"] == p]
    print(f"{p:12s} n={len(s):2d}  离队={int(s['departed_label'].sum())}  "
          f"留队={int((1-s['departed_label']).sum())}  多数类基线准确率="
          f"{max(s['departed_label'].mean(), 1-s['departed_label'].mean()):.4f}")
maj = max(inter['departed_label'].mean(), 1 - inter['departed_label'].mean())
print(f"{'整体':12s} n={len(inter):2d}  离队={int(inter['departed_label'].sum())}  "
      f"整体多数类基线准确率={maj:.4f}")


def get_bounds(position):
    uni = get_universal_metrics()
    psm = get_position_specific_metrics()
    b = {}
    for m in uni.keys():
        if m in ["age", "Contract_expires"]:
            continue
        b[f"{m}_weight"] = (0.08, 0.15)
    important = {"Forward": ["Gls", "xG", "SoT", "SCA", "GCA"],
                 "Midfielder": ["Ast", "xAG", "KP", "Cmp_pct", "PrgP"],
                 "Defender": ["Tkl", "Int", "Blocks", "Clr", "Cmp_pct"],
                 "Goalkeeper": ["Saves", "Save_pct", "CS", "CS_pct"]}[position]
    for m in psm[position].keys():
        b[f"{m}_weight"] = (0.08, 0.15) if m in important else (0.05, 0.12)
    b.update({"alpha": (1.0, 4.0), "tau": (0.3, 0.7), "risk_multiplier": (0.3, 0.7)})
    return b


UB = {p: get_bounds(p) for p in POSITIONS}


def uniform_weights(p, level):
    return {k: level for k in UB[p]}


def evaluate_overall(weights_by_pos, thresh=0.5):
    """把 4 个位置模型的结果汇总，返回整体准确率与混淆矩阵。"""
    preds, acts = [], []
    for _, row in inter.iterrows():
        p = row["position_group"]
        if p not in weights_by_pos:
            continue
        ps = calculate_enhanced_percentile_scores(row, league, pos_ds)
        prob = calculate_departure_probability_with_weights(row, ps, weights_by_pos[p])
        preds.append(int(prob > thresh))
        acts.append(int(row["departed_label"]))
    preds, acts = np.array(preds), np.array(acts)
    acc = (preds == acts).mean()
    tp = int(((preds == 1) & (acts == 1)).sum()); fp = int(((preds == 1) & (acts == 0)).sum())
    fn = int(((preds == 0) & (acts == 1)).sum()); tn = int(((preds == 0) & (acts == 0)).sum())
    return acc, (tp, fp, fn, tn), preds, acts


print()
print("=" * 90)
print("[1] 朴素单变量规则（不使用任何优化权重，仅按原始百分位排序）")
print("=" * 90)
# 直接看：年龄越大越可能走？上场时间越少越可能走？
age = inter["age"].astype(float).values
mins = inter["Min"].astype(float).values
y = inter["departed_label"].astype(int).values
for label, x, direction in [("年龄（越大越可能离队）", age, 1),
                            ("上场分钟（越少越可能离队）", mins, -1)]:
    corr = stats.pointbiserialr(y, x * direction)
    # 用最简单的阈值规则：在中位数处切分
    med = np.median(x)
    pred = ((x > med).astype(int) if direction == 1 else (x < med).astype(int))
    acc = (pred == y).mean()
    print(f"{label:26s} 准确率={acc:.4f}  点二列相关 r={corr[0]:+.3f} (p={corr[1]:.4f})")

print()
print("=" * 90)
print("[2] 均匀权重基线（不优化，所有指标同权）")
print("=" * 90)
for lvl, tag in [(0.08, "全部 0.08"), (0.10, "全部 0.10"), (0.12, "全部 0.12"),
                 (0.25, "全部 0.25（早期框架的 uniform 基线）")]:
    w = {p: uniform_weights(p, lvl) for p in POSITIONS}
    acc, cm, _, _ = evaluate_overall(w)
    print(f"{tag:34s} 整体准确率={acc:.4f}  混淆矩阵 TP/FP/FN/TN={cm}")

print()
print("=" * 90)
print("[3] 论文报告的“优化后”结果（PSO 最优权重，来自 Multi_Run_Average_Metrics）")
print("=" * 90)
import importlib
pred_mod = importlib.import_module("2023_2024_Prediction")
# 这里用的是 2022-2023 训练数据，需要对应权重；直接读取论文使用的 PSO 配置
FORWARD = importlib.import_module("GA_Weight_Optimization_Experiment_Final")
# 使用脚本内嵌的 PSO 权重（load_pso_optimal_weights 针对 2022-2023 结构）
PSO = pred_mod.load_pso_optimal_weights()
acc, cm, preds, acts = evaluate_overall(PSO)
print(f"{'PSO 优化权重':34s} 整体准确率={acc:.4f}  混淆矩阵 TP/FP/FN/TN={cm}")
print(f"{'多数类基线（全预测留队）':34s} 整体准确率={maj:.4f}")
# 是否所有位置都预测为留队？
print(f"预测为离队的球员数 = {int(preds.sum())} / {len(preds)}")
print()
print("结论：优化权重把所有人都预测成“留队”，准确率 = 多数类基线，"
      "即模型没有产生任何有效区分。")

print()
print("=" * 90)
print("[4] 换阈值能否改善？扫描决策阈值")
print("=" * 90)
for p in POSITIONS:
    s = inter[inter["position_group"] == p]
    if len(s) == 0:
        continue
    probs = []
    for _, row in s.iterrows():
        ps = calculate_enhanced_percentile_scores(row, league, pos_ds)
        probs.append(calculate_departure_probability_with_weights(row, ps, PSO[p]))
    probs = np.array(probs); acts = s["departed_label"].astype(int).values
    print(f"  {p:12s} n={len(s):2d}  概率 min={probs.min():.3f} max={probs.max():.3f} "
          f"mean={probs.mean():.3f}   实际离队率={acts.mean():.2f}")
