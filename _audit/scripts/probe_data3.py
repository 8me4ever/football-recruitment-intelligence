# -*- coding: utf-8 -*-
"""审计探针 3：核对数据完整度与论文声明（row1 为指标名层）。只读。"""
import pandas as pd
from collections import Counter

BASE = r"F:\Samuel\football recruitment\final project"

# (类别, 路径, 指标名 -> 在 row1 中的列位置)
SPECS = [
    ("standard",   "data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv",
     {10: "Min", 12: "Gls", 13: "Ast", 20: "xG"}),
    ("goal",       "data excel/2022-2023/ITA_SerieA_player_goal_stats_2022_2023.csv",
     {9: "SCA", 10: "SCA90", 17: "GCA", 18: "GCA90"}),
    ("shooting",   "data excel/2022-2023/ITA_SerieA_player_shooting_stats_2022_2023.csv",
     {9: "Gls", 10: "Sh", 11: "SoT", 21: "xG"}),
    ("passing",    "data excel/2022-2023/ITA_SerieA_player_passing_stats_2022_2023.csv",
     {12: "TotDist", 13: "PrgDist", 23: "Ast", 27: "KP", 31: "PrgP"}),
    ("possession", "data excel/2022-2023/ITA_SerieA_player_possession_stats_2022_2023.csv",
     {9: "Touches", 21: "Carries", 24: "PrgC"}),
    ("defensive",  "data excel/2022-2023/ITA_SerieA_player_defensive_stats_2022_2023.csv",
     {9: "Tkl", 10: "TklW", 18: "Blocks", 21: "Int", 23: "Clr"}),
]
CLAIM = {"standard": "98.5% / 缺失8", "goal": "97.2% / 缺失15", "shooting": "96.8% / 缺失17",
         "passing": "98.1% / 缺失10", "possession": "97.5% / 缺失13", "defensive": "98.3% / 缺失9"}

print("=" * 88)
print("[1] 各统计类别真实完整度（2022-2023，整表口径：数据行 × 全部指标列）")
print("=" * 88)
print(f"{'category':12s}{'data_rows':>10s}{'missing':>9s}{'total':>8s}{'completeness':>14s}   论文声明")
for name, f, cols in SPECS:
    raw = pd.read_csv(f"{BASE}\\{f}", header=None)
    data = raw.iloc[3:].reset_index(drop=True)      # row0=组名 row1=指标 row2=字段名 row3+=数据
    miss = tot = 0
    for idx in cols:
        col = pd.to_numeric(data[idx], errors="coerce")
        miss += int(col.isna().sum())
        tot += len(col)
    print(f"{name:12s}{len(data):10d}{miss:9d}{tot:8d}{100*(1-miss/tot):13.2f}%   {CLAIM.get(name,'-')}")

print()
print("=" * 88)
print("[2] 真实球员数 / 球队数 vs 论文声明")
print("=" * 88)
for season, path in [("2022-2023", "data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv"),
                     ("2023-2024", "data excel/2023-2024/ITA_SerieA_player_standard_stats_2023_2024.csv")]:
    raw = pd.read_csv(f"{BASE}\\{path}", header=None)
    data = raw.iloc[3:].reset_index(drop=True)
    print(f"{season}: 数据行={len(data)}  唯一球员={data[3].nunique()}  球队={data[2].nunique()}")
print("论文声明: 2022-2023 = 535 名 / 20 队 ; 2023-2024 = 547 名 / 20 队")

print()
print("=" * 88)
print("[3] 标签类别平衡与「平凡基线」")
print("=" * 88)
for season, f in [("2022-2023", "Inter_Players_Departure_Labels.csv"),
                  ("2023-2024", "data excel/2023-2024/Inter_departured_2023_2024.csv")]:
    rows = pd.read_csv(f"{BASE}\\{f}", encoding="utf-8-sig").to_dict("records")
    lab = [int(r["Departed_Label"]) for r in rows]
    c = Counter(lab)
    print(f"{season}: n={len(lab):2d}  离队={c[1]:2d}  留队={c[0]:2d}  离队率={c[1]/len(lab):.3f}   "
          f"「全预测留队」基线准确率={max(c.values())/len(lab):.4f}")

print()
print("=" * 88)
print("[4] 各位置训练样本量（2022-2023，代码等价口径）+ 位置内多数类基线")
print("=" * 88)
COLS = ['league','season','team','player','nation','pos','age','born','MP','Starts','Min','90s','Gls','Ast','GA',
        'G_minus_PK','PK','PKatt','CrdY','CrdR','xG','npxG','xAG','npxG_plus_xAG','PrgC','PrgP','PrgR',
        'Gls_per90','Ast_per90','GA_per90','G_minus_PK_per90','GA_minus_PK_per90','xG_per90','xAG_per90',
        'xG_plus_xAG_per90','npxG_per90','npxG_plus_xAG_per90']
lab = pd.read_csv(f"{BASE}\\Inter_Players_Departure_Labels.csv", encoding="utf-8-sig")
lm = dict(zip(lab["Player_Name"].astype(str).str.strip(), lab["Departed_Label"]))
d = pd.read_csv(f"{BASE}\\data excel/2022-2023\\ITA_SerieA_player_standard_stats_2022_2023.csv",
                skiprows=2, names=COLS)
d = d[d["team"] == "Inter"].copy()
d["label"] = d["player"].map(lm)
d = d.dropna(subset=["label"])


def pg(p):
    if pd.isna(p):
        return "Unknown"
    p = str(p)
    for k, v in [("GK", "Goalkeeper"), ("FW", "Forward"), ("MF", "Midfielder"), ("DF", "Defender")]:
        if k in p:
            return v
    return "Unknown"


d["pg"] = d["pos"].apply(pg)
for pos, row in d.groupby("pg")["label"].agg(["count", "sum"]).iterrows():
    n, dep = int(row["count"]), int(row["sum"])
    print(f"{pos:12s} n={n:2d}  离队={dep}  位置内多数类基线准确率={max(dep, n-dep)/n:.4f}")
print(f"全样本 n={len(d)}，总离队={int(d['label'].sum())}，全样本多数类基线准确率={1-d['label'].mean():.4f}")

print()
print("=" * 88)
print("[5] 论文 2023-2024 留出集结果 vs 磁盘真实运行输出")
print("=" * 88)
print("论文 results.tex:  Accuracy=0.7778  Precision=0.5556  Recall=0.7143  PR-AUC=0.6459  21/27 正确")
print("真实报告 172047:  Accuracy=0.7407  Precision=0.0000  Recall=0.0000  PR-AUC=0.2593  20/27 正确")
print("真实报告中 position 全部为 'Unknown'，所有球员 departure_probability 恒为 0.5（默认值）")
