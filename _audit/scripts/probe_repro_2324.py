# -*- coding: utf-8 -*-
"""
审计探针 4：在 venv 中复现 2023-2024 预测流程，验证真实表现。
保护措施：把 os.chdir 重定向到审计目录，避免污染原项目。
"""
import os
import sys

ORIG = r"F:\Samuel\football recruitment\final project"
AUDIT_OUT = r"F:\Samuel\football recruitment\_audit\repro"
os.makedirs(AUDIT_OUT, exist_ok=True)

# 拦截 chdir：脚本里硬编码了作者机器的旧路径
os.chdir = lambda p, *a, **k: None
os.getcwd = lambda: ORIG

sys.path.insert(0, ORIG)
os.chdir(ORIG)  # 这一步是我们自己控制的
import builtins
_real_chdir = None
os.chdir = lambda p, *a, **k: None        # 之后所有 chdir 均无效

import pandas as pd
import numpy as np

import importlib
pred = importlib.import_module("2023_2024_Prediction")

print("=" * 88)
print("[A] 加载 2023-2024 数据（函数内部仍以当前工作目录相对路径读取）")
print("=" * 88)
inter, league = pred.load_2023_2024_data()
print("inter shape:", None if inter is None else inter.shape)
print("league shape:", None if league is None else league.shape)
if inter is not None:
    print("position_group 分布:", inter["position_group"].value_counts().to_dict())
    print("位置原始值样例:", inter["pos"].tolist()[:12])
    print("departed_label 分布:", inter["departed_label"].value_counts().to_dict())

print()
print("=" * 88)
print("[B] 手动复算离队概率（与脚本同逻辑），并对照“全预测留队”基线")
print("=" * 88)
from weight_optimization_core_updated import (
    calculate_enhanced_percentile_scores, calculate_departure_probability_with_weights,
)
try:
    from weight_optimization_core_updated import load_position_specific_data
    pos_ds = load_position_specific_data()
except Exception as e:
    pos_ds = {}
    print("position_datasets 加载失败:", e)
print("position_datasets 覆盖位置:", list(pos_ds.keys()))
for k, v in pos_ds.items():
    for src, df in v.items():
        season_vals = df["season"].unique() if "season" in df.columns else "?"
        print(f"   {k}/{src}: rows={len(df)} season={season_vals}")

W = pred.load_pso_optimal_weights()
rows = []
for _, player in inter.iterrows():
    position = player["position_group"]
    if position not in W:
        continue
    ps = calculate_enhanced_percentile_scores(player, league, pos_ds)
    p = calculate_departure_probability_with_weights(player, ps, W[position])
    rows.append({
        "player": player["player"], "position": position, "age": int(player["age"]),
        "Min": int(player["Min"]), "pos_raw": player["pos"],
        "prob": round(p, 4), "pred": int(p > 0.5), "actual": int(player["departed_label"]),
    })
res = pd.DataFrame(rows)
print()
print(res.to_string(index=False))
print()
print("样本数:", len(res))
print("真实离队数:", int(res["actual"].sum()))
print("预测离队数:", int(res["pred"].sum()))
print("准确率:", round((res["pred"] == res["actual"]).mean(), 4))
print("「全预测留队」基线准确率:", round(1 - res["actual"].mean(), 4))
print("概率范围:", res["prob"].min(), "~", res["prob"].max())
tp = int(((res["pred"] == 1) & (res["actual"] == 1)).sum())
fp = int(((res["pred"] == 1) & (res["actual"] == 0)).sum())
fn = int(((res["pred"] == 0) & (res["actual"] == 1)).sum())
tn = int(((res["pred"] == 0) & (res["actual"] == 0)).sum())
print(f"混淆矩阵: TP={tp} FP={fp} FN={fn} TN={tn}")
prec = tp / (tp + fp) if (tp + fp) else 0.0
rec = tp / (tp + fn) if (tp + fn) else 0.0
print(f"precision={prec:.4f} recall={rec:.4f} f1={(2*prec*rec/(prec+rec) if (prec+rec) else 0.0):.4f}")

# 位置取值是否被正确解析
print()
print("[C] 位置字段核对：2023-2024 原始 pos 是否被 get_position_group 正确识别")
print("   原始 pos 唯一值:", sorted(set(inter["pos"].astype(str))))
print("   映射结果:", inter.groupby("pos")["position_group"].first().to_dict())
