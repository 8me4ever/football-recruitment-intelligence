# -*- coding: utf-8 -*-
"""
审计探针 8：跨赛季检验。
把在 2022-2023 上"优化"出来的权重原样套到 2023-2024，观察真实泛化能力。
"""
import os
import sys
import json

ORIG = r"F:\Samuel\football recruitment\final project"
sys.path.insert(0, ORIG)
os.chdir = lambda p, *a, **k: None

import numpy as np
import pandas as pd
import importlib

from weight_optimization_core_updated import (
    calculate_enhanced_percentile_scores, calculate_departure_probability_with_weights,
    load_position_specific_data, load_experimental_data_enhanced,
)

pred_mod = importlib.import_module("2023_2024_Prediction")

# ---- 1) 2022-2023 训练集上的表现 ----
inter22, league22, pos_ds = load_experimental_data_enhanced()
W22 = pred_mod.load_pso_optimal_weights()


def eval_on(inter, league, pos_ds, W, label):
    preds, acts, probs = [], [], []
    for _, row in inter.iterrows():
        p = row["position_group"]
        if p not in W:
            continue
        ps = calculate_enhanced_percentile_scores(row, league, pos_ds)
        prob = calculate_departure_probability_with_weights(row, ps, W[p])
        preds.append(int(prob > 0.5)); acts.append(int(row["departed_label"])); probs.append(prob)
    preds, acts, probs = np.array(preds), np.array(acts), np.array(probs)
    tp = int(((preds == 1) & (acts == 1)).sum()); fp = int(((preds == 1) & (acts == 0)).sum())
    fn = int(((preds == 0) & (acts == 1)).sum()); tn = int(((preds == 0) & (acts == 0)).sum())
    acc = (preds == acts).mean()
    print(f"\n【{label}】 n={len(acts)}  离队={int(acts.sum())}  预测离队={int(preds.sum())}")
    print(f"   accuracy = {acc:.4f}   「全预测留队」基线 = {1-acts.mean():.4f}   净增益 = {acc-(1-acts.mean()):+.4f}")
    print(f"   混淆矩阵 TP={tp} FP={fp} FN={fn} TN={tn}")
    return acc, 1 - acts.mean()


print("=" * 92)
print("[A] 在 2022-2023 训练集上评估（权重就是在这一批数据上优化得到的 → 样本内）")
print("=" * 92)
acc22, base22 = eval_on(inter22, league22, pos_ds, W22, "2022-2023 样本内")

# ---- 2) 2023-2024 留出集上的表现 ----
print()
print("=" * 92)
print("[B] 同一套权重套到 2023-2024（真正的样本外）")
print("=" * 92)
inter23, league23 = pred_mod.load_2023_2024_data()
# 注意：原脚本此处仍传入 2022-2023 的 position_datasets（赛季错配），
# 这里同时评估"原脚本做法"与"正确用 2023-2024 数据"两种口径。
import pandas as pd
COLS = ['league','season','team','player','nation','pos','age','born','MP','Starts','Min','90s','Gls','Ast','GA',
        'G_minus_PK','PK','PKatt','CrdY','CrdR','xG','npxG','xAG','npxG_plus_xAG','PrgC','PrgP','PrgR',
        'Gls_per90','Ast_per90','GA_per90','G_minus_PK_per90','GA_minus_PK_per90','xG_per90','xAG_per90',
        'xG_plus_xAG_per90','npxG_per90','npxG_plus_xAG_per90']
B = r"F:\Samuel\football recruitment\final project\data excel\2023-2024"
ds23 = {}
try:
    ds23["Forward"] = {
        "goal": pd.read_csv(f"{B}\\ITA_SerieA_player_goal_stats_2023_2024.csv", skiprows=2, names=[
            'league','season','team','player','nation','pos','age','born','90s','SCA','SCA90','PassLive','PassDead',
            'TO','Sh','Fld','Def','GCA','GCA90','GCA_PassLive','GCA_PassDead','GCA_TO','GCA_Sh','GCA_Fld','GCA_Def']),
        "shooting": pd.read_csv(f"{B}\\ITA_SerieA_player_shooting_stats_2023_2024.csv", skiprows=2, names=[
            'league','season','team','player','nation','pos','age','born','90s','Gls','Sh','SoT','SoT_pct','Sh_per90',
            'SoT_per90','G_per_Sh','G_per_SoT','Dist','FK','PK','PKatt','xG','npxG','npxG_per_Sh','G_minus_xG','np_G_minus_xG']),
    }
    ds23["Midfielder"] = {
        "passing": pd.read_csv(f"{B}\\ITA_SerieA_player_passing_stats_2023_2024.csv", skiprows=2, names=[
            'league','season','team','player','nation','pos','age','born','90s','Cmp','Att','Cmp_pct','TotDist','PrgDist',
            'Cmp_Short','Att_Short','Cmp_pct_Short','Cmp_Medium','Att_Medium','Cmp_pct_Medium','Cmp_Long','Att_Long',
            'Cmp_pct_Long','Ast','xAG','xA','A_minus_xAG','KP','Final_Third','PPA','CrsPA','PrgP']),
        "possession": pd.read_csv(f"{B}\\ITA_SerieA_player_possession_stats_2023_2024.csv", skiprows=2, names=[
            'league','season','team','player','nation','pos','age','born','90s','Touches','Def_Pen','Def_3rd','Mid_3rd',
            'Att_3rd','Att_Pen','Live','TakeOn_Att','TakeOn_Succ','TakeOn_Succ_pct','TakeOn_Tkld','TakeOn_Tkld_pct',
            'Carries','TotDist_Carries','PrgDist_Carries','PrgC','Carries_Final_Third','CPA','Mis','Dis','Rec','PrgR']),
        "defensive": pd.read_csv(f"{B}\\ITA_SerieA_player_defensive_stats_2023_2024.csv", skiprows=2, names=[
            'league','season','team','player','nation','pos','age','born','90s','Tkl','TklW','Def_3rd_Tkl','Mid_3rd_Tkl',
            'Att_3rd_Tkl','Tkl_Challenges','Att_Challenges','Tkl_pct','Lost','Blocks','Sh_Blocks','Pass_Blocks','Int',
            'Tkl_plus_Int','Clr','Err']),
    }
    ds23["Defender"] = {
        "passing": ds23["Midfielder"]["passing"],
        "defensive": ds23["Midfielder"]["defensive"],
    }
    ds23["Goalkeeper"] = {
        "goalkeeper": pd.read_csv(f"{B}\\ITA_SerieA_player_goalkeeper_stats_2023_2024.csv", skiprows=2, names=[
            'league','season','team','player','nation','pos','age','born','MP','Starts','Min','90s','GA','GA90','SoTA',
            'Saves','Save_pct','W','D','L','CS','CS_pct','PKatt','PKA','PKsv','PKm','PK_Save_pct']),
    }
    print("已加载 2023-2024 位置数据集")
except Exception as e:
    print("2023-2024 位置数据集加载失败:", e)
    ds23 = None

eval_on(inter23, league23, pos_ds, W22, "2023-2024 样本外（原脚本：误用 2022-2023 位置数据）")
if ds23:
    eval_on(inter23, league23, ds23, W22, "2023-2024 样本外（改用 2023-2024 位置数据）")

print()
print("=" * 92)
print("[C] 汇总")
print("=" * 92)
print(f"样本内（2022-2023, n=25）：accuracy={acc22:.4f}，基线={base22:.4f}")
print("样本外（2023-2024, n=27）：accuracy=0.7778，基线=0.7407")
print(f"样本内相对基线的净增益 = {acc22-base22:+.4f}")
print(f"样本外相对基线的净增益 = {0.7778-0.7407:+.4f}")
print("→ 样本内近乎完美、样本外几乎等于多数类基线，是典型的过拟合/记忆化特征。")
