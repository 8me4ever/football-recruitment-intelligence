# -*- coding: utf-8 -*-
"""审计探针 9：建立可用指标字典（各统计类别的真实列名），供新系统设计参考。"""
import pandas as pd
import json
import re
from pathlib import Path

BASE = Path(r"F:\Samuel\football recruitment\final project")

FILES = {
    "standard":   "data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv",
    "goal":       "data excel/2022-2023/ITA_SerieA_player_goal_stats_2022_2023.csv",
    "shooting":   "data excel/2022-2023/ITA_SerieA_player_shooting_stats_2022_2023.csv",
    "passing":    "data excel/2022-2023/ITA_SerieA_player_passing_stats_2022_2023.csv",
    "possession": "data excel/2022-2023/ITA_SerieA_player_possession_stats_2022_2023.csv",
    "defensive":  "data excel/2022-2023/ITA_SerieA_player_defensive_stats_2022_2023.csv",
    "goalkeeper": "data excel/2022-2023/ITA_SerieA_player_goalkeeper_stats_2022_2023.csv",
    "gk_adv":     "data excel/2022-2023/ITA_SerieA_player_goalkeeper_advance_stats_2022_2023.csv",
}

out = {}
print("=" * 92)
print("各统计类别可用指标（row0 组名 + row1 指标名）")
print("=" * 92)
for name, rel in FILES.items():
    p = BASE / rel
    raw = pd.read_csv(p, header=None)
    grp = raw.iloc[0].tolist()
    met = raw.iloc[1].tolist()
    n_cols = raw.shape[1]
    n_data = raw.shape[0] - 3
    metrics = []
    for i in range(4, n_cols):
        g = "" if pd.isna(grp[i]) else str(grp[i]).strip()
        m = "" if pd.isna(met[i]) else str(met[i]).strip()
        if m:
            metrics.append((g, m))
    out[name] = {"rows": n_data, "columns": n_cols, "metrics": metrics}
    print(f"\n### {name}  (数据行={n_data}, 列数={n_cols}, 指标数={len(metrics)})")
    by_grp = {}
    for g, m in metrics:
        by_grp.setdefault(g or "(无组名)", []).append(m)
    for g, ms in by_grp.items():
        print(f"   [{g}] {', '.join(ms)}")

# 与代码实际使用的指标做对照
print()
print("=" * 92)
print("代码实际选用的指标 vs 数据中可用指标（覆盖度）")
print("=" * 92)
USED = {
    "universal": ["Min", "CrdY", "CrdR", "Contract_expires"],
    "Forward": ["Gls", "Ast", "xG", "SoT", "G/Sh", "Sh/90", "SCA", "GCA", "Att Pen", "Succ"],
    "Midfielder": ["Ast", "xAG", "KP", "Cmp%", "PrgP", "Touches", "PrgC", "Succ", "Tkl", "SCA"],
    "Defender": ["Tkl", "Int", "Blocks", "Clr", "Tkl%", "Cmp%", "Cmp%", "PrgP", "1/3", "Def 3rd"],
    "Goalkeeper": ["Saves", "Save%", "CS", "CS%", "GA90", "SoTA", "PKsv", "Save%", "W", "(40+)"],
}
allm = {m for v in out.values() for _, m in v["metrics"]}
for pos, ms in USED.items():
    found = [m for m in ms if m in allm]
    missing = [m for m in ms if m not in allm]
    print(f"{pos:12s} 代码用了 {len(ms)} 个；数据中匹配到 {len(found)} 个", 
          f"；未直接匹配: {missing}" if missing else "")

print()
print("=" * 92)
print("每个位置的可用指标池大小（可选做角色画像的候选特征量）")
print("=" * 92)
total = sum(len(v["metrics"]) for v in out.values())
print("全部统计类别指标总数 =", total)
print("去重后指标名总数 =", len(allm))

# 检查 2024-25 是否有 CSV
print()
print("=" * 92)
print("赛季覆盖情况")
print("=" * 92)
for p in sorted((BASE / "data").glob("*.html")):
    print(f"   HTML: {p.name}  ({p.stat().st_size/1024:.0f} KB)")
for d in sorted((BASE / "data excel").iterdir()):
    if d.is_dir():
        csvs = list(d.glob("*.csv"))
        print(f"   CSV 目录 {d.name}: {len(csvs)} 个文件")
