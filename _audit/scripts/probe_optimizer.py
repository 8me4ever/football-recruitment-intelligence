# -*- coding: utf-8 -*-
"""
审计探针 5：检验权重优化是否真的在学习。
方法：在 Forward 位置上比较不同权重方案的目标函数值，并检查
      目标函数对单个权重的敏感度、以及最优解是否全部贴在边界上。
"""
import os
import sys

ORIG = r"F:\Samuel\football recruitment\final project"
sys.path.insert(0, ORIG)
os.chdir = lambda p, *a, **k: None

import numpy as np
import pandas as pd

from weight_optimization_core_updated import (
    load_experimental_data_enhanced, get_universal_metrics, get_position_specific_metrics,
    calculate_enhanced_percentile_scores, calculate_departure_probability_with_weights,
    evaluate_weights_enhanced,
)

inter, league, pos_ds = load_experimental_data_enhanced()
print("inter 样本:", None if inter is None else len(inter))
if inter is None:
    sys.exit("数据加载失败")

POS = "Forward"
sub = inter[inter["position_group"] == POS]
print(f"位置 {POS} 样本数 = {len(sub)}，其中离队 {int(sub['departed_label'].sum())} 人")
print()

# 构造与算法文件完全一致的边界
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

B = get_bounds(POS)
names = list(B.keys())
print(f"参数数量 = {len(names)}")
print()

def score(wd):
    s, m = evaluate_weights_enhanced(wd, inter, league, pos_ds, POS)
    return s, m

# 方案1：全部取下界
wd_lo = {k: v[0] for k, v in B.items()}
# 方案2：全部取上界
wd_hi = {k: v[1] for k, v in B.items()}
# 方案3：全部取中点
wd_mid = {k: (v[0] + v[1]) / 2 for k, v in B.items()}
# 方案4：随机 200 组，看分布
rng = np.random.default_rng(0)
rand_scores = []
for _ in range(200):
    wd = {k: rng.uniform(v[0], v[1]) for k, v in B.items()}
    rand_scores.append(score(wd)[0])

print("=" * 86)
print("[A] 目标函数在不同权重方案下的取值（越高越好）")
print("=" * 86)
for label, wd in [("全部取下界", wd_lo), ("全部取上界", wd_hi), ("全部取中点", wd_mid)]:
    s, m = score(wd)
    print(f"{label:14s} composite={s:.6f}  acc={m.get('accuracy')}  pr_auc={m.get('pr_auc')}  "
          f"f1={m.get('f1_score')}  bal_acc={m.get('balanced_accuracy')}  brier={m.get('brier_score')}")
rs = np.array(rand_scores)
print(f"{'随机200组':14s} mean={rs.mean():.6f}  std={rs.std():.6f}  min={rs.min():.6f}  max={rs.max():.6f}")
print()

print("=" * 86)
print(f"[B] 目标函数取值集合（随机采样 200 次）——若只有极少数不同取值，说明目标函数近乎常数")
print("=" * 86)
vals, counts = np.unique(np.round(rs, 6), return_counts=True)
print(f"不同取值个数 = {len(vals)}（共 200 次采样）")
for v, c in list(zip(vals, counts))[-10:]:
    print(f"   score={v:.6f}  出现 {c} 次")
print()

print("=" * 86)
print("[C] 用 scipy 差分进化做一次小预算优化（与 GA_Final 相同算法），看最优解位置")
print("=" * 86)
from scipy.optimize import differential_evolution

bounds = [B[k] for k in names]

def f(x):
    s, _ = score(dict(zip(names, x)))
    return -s

res = differential_evolution(func=f, bounds=bounds, maxiter=8, popsize=8, seed=42, disp=False,
                             tol=1e-8, polish=False)
print(f"最优目标值 = {-res.fun:.6f}   迭代次数 = {res.nfev}")
print()
print(f"{'参数':<26}{'最优值':>10}{'下界':>9}{'上界':>9}   位置")
at_bound = 0
for k, v in zip(names, res.x):
    lo, hi = B[k]
    span = hi - lo
    rel = (v - lo) / span
    tag = "贴下界" if rel <= 0.02 else ("贴上界" if rel >= 0.98 else "内部")
    if rel <= 0.02 or rel >= 0.98:
        at_bound += 1
    print(f"{k:<26}{v:>10.6f}{lo:>9.2f}{hi:>9.2f}   {tag} ({rel:.1%})")
print()
print(f"贴边界的参数数 = {at_bound}/{len(names)}")

# 用最优解与"全部取上界"比较
s_opt, _ = score(dict(zip(names, res.x)))
s_hi, _ = score(wd_hi)
print(f"\n最优解得分={s_opt:.6f}   全部取上界得分={s_hi:.6f}   差值={s_opt - s_hi:+.6f}")
