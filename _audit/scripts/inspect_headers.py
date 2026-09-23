# -*- coding: utf-8 -*-
"""检查 FBref CSV 的表头层级结构（只读）。"""
import pandas as pd

BASE = r"F:\Samuel\football recruitment\final project"
FILES = [
    "data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv",
    "data excel/2022-2023/ITA_SerieA_player_goal_stats_2022_2023.csv",
    "data excel/2022-2023/ITA_SerieA_player_shooting_stats_2022_2023.csv",
    "data excel/2022-2023/ITA_SerieA_player_passing_stats_2022_2023.csv",
    "data excel/2022-2023/ITA_SerieA_player_possession_stats_2022_2023.csv",
    "data excel/2022-2023/ITA_SerieA_player_defensive_stats_2022_2023.csv",
    "data excel/2022-2023/ITA_SerieA_player_goalkeeper_stats_2022_2023.csv",
]
for f in FILES:
    p = f"{BASE}\\{f}"
    raw = pd.read_csv(p, header=None, nrows=4)
    print("=" * 90)
    print(f.split("/")[-1], " shape_full=", pd.read_csv(p, header=None).shape)
    for i in range(4):
        row = [str(x)[:11] for x in raw.iloc[i].tolist()]
        print(f"  row{i}: {row}")
