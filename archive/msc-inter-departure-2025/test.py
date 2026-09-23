import soccerdata as sd
import pandas as pd

sofifa = sd.SoFIFA()           # 不要传 seasons
players = sofifa.read_player_data()

# 按俱乐部过滤（可能是 'Inter' 或 'Internazionale'，先 print(players.columns) + 查看唯一值）
mask = players['club_name'].str.contains(r'\bInter\b', case=False, na=False)
inter = players[mask].copy()

cols = [c for c in inter.columns if any(k in c.lower() for k in [
    "short_name","long_name","club","contract","loan","value","wage","age","position"
])]
out = inter[cols].sort_values(by=cols[0])
out.to_excel("Inter_Contracts_from_soccerdata_SoFIFA.xlsx", index=False)
print("Saved: Inter_Contracts_from_soccerdata_SoFIFA.xlsx")



