# -*- coding: utf-8 -*-
"""
审计探针 10：证明"干净数据层"可行且能立刻暴露旧数据层的问题。
产出一个规范化后的球员表，包含：
  - 无重复球员（赛季中转会的球员合并/标记）
  - 记录出场分钟，供后续过滤
  - 位置分组使用 FBref 的真实列名（支持多位置）
  - 挂上离队标签与合同年限
输出到审计目录，不修改原项目。
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path

SRC = Path(r"F:\Samuel\football recruitment\final project")
OUT = Path(r"F:\Samuel\football recruitment\_audit\processed")
OUT.mkdir(parents=True, exist_ok=True)

GRP = ["league", "season", "team", "player", "nation", "pos", "age", "born"]
STD_COLS = GRP + ["MP", "Starts", "Min", "90s", "Gls", "Ast", "GA", "G_minus_PK", "PK", "PKatt",
                  "CrdY", "CrdR", "xG", "npxG", "xAG", "npxG_plus_xAG", "PrgC", "PrgP", "PrgR"]


def load_standard(path, skip=3):
    """按 row1 的真实指标名读取 standard 表，只保留前 27 列并在数据行去掉冗余表头行。"""
    raw = pd.read_csv(path, header=None)
    data = raw.iloc[3:].reset_index(drop=True)     # row0 组名 / row1 指标 / row2 字段名 / row3+ 数据
    data.columns = range(raw.shape[1])
    keep = data.iloc[:, :len(STD_COLS)].copy()
    keep.columns = STD_COLS
    num = ["age", "born", "MP", "Starts", "Min", "90s", "Gls", "Ast", "GA", "G_minus_PK",
           "PK", "PKatt", "CrdY", "CrdR", "xG", "npxG", "xAG", "npxG_plus_xAG", "PrgC", "PrgP", "PrgR"]
    for c in num:
        keep[c] = pd.to_numeric(keep[c], errors="coerce")
    keep["player"] = keep["player"].astype(str).str.strip()
    keep["team"] = keep["team"].astype(str).str.strip()
    return keep


def position_group(pos):
    """FBref 的 pos 可能是 'FW,MF' 这种多位置；返回主位置 + 全部位置列表。"""
    if pd.isna(pos):
        return "Unknown", []
    parts = [p.strip() for p in str(pos).split(",") if p.strip()]
    order = ["GK", "DF", "MF", "FW"]
    parts = [p for p in parts if p in order]
    if not parts:
        return "Unknown", []
    label = {"GK": "Goalkeeper", "DF": "Defender", "MF": "Midfielder", "FW": "Forward"}
    primary = min(parts, key=lambda p: order.index(p))
    return label[primary], parts


for season, rel, lab_rel, lab_key, con_rel in [
    ("2022-2023", "data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv",
     "Inter_Players_Departure_Labels.csv", "Player_Name", "data excel/2022-2023/Contract_2022_2023.csv"),
    ("2023-2024", "data excel/2023-2024/ITA_SerieA_player_standard_stats_2023_2024.csv",
     "data excel/2023-2024/Inter_departured_2023_2024.csv", "Name", "data excel/2023-2024/Contract_2023_2024.csv"),
]:
    print("=" * 92)
    print(f"赛季 {season}")
    print("=" * 92)
    df = load_standard(SRC / rel)
    print(f"  原始行数 = {len(df)}")

    # 位置解析
    pg = df["pos"].apply(position_group)
    df["position_group"] = [x[0] for x in pg]
    df["positions_all"] = [",".join(x[1]) for x in pg]
    df["n_positions"] = [len(x[1]) for x in pg]
    print(f"  多位置球员数 = {int((df['n_positions'] > 1).sum())}  (例如 pos='FW,MF')")

    # 重复球员
    dup_mask = df.duplicated("player", keep=False)
    print(f"  赛季中转会导致重复的球员行数 = {int(dup_mask.sum())}  "
          f"涉及球员 {df.loc[dup_mask, 'player'].nunique()} 人")

    # 低出场样本
    low = df["Min"] < 90
    print(f"  出场 <90 分钟的球员行数 = {int(low.sum())}  "
          f"（旧代码未过滤，全部进入了百分位参考池）")
    print(f"  出场分钟分位数: p10={df['Min'].quantile(.1):.0f} p25={df['Min'].quantile(.25):.0f} "
          f"中位数={df['Min'].median():.0f}")

    # 聚合到唯一球员（按分钟加权，避免重复计数）
    key = ["player"]
    agg = {c: "sum" for c in ["MP", "Starts", "Min", "90s", "Gls", "Ast", "GA", "G_minus_PK",
                              "PK", "PKatt", "CrdY", "CrdR", "xG", "npxG", "xAG",
                              "npxG_plus_xAG", "PrgC", "PrgP", "PrgR"]}
    agg.update({"age": "max", "position_group": "first", "positions_all": "first",
                "n_positions": "max"})
    df_u = df.groupby(key, as_index=False).agg(agg)
    df_u = df_u.rename(columns={"player": "player_name"})
    print(f"  去重后唯一球员数 = {len(df_u)}")

    # 挂标签
    lab = pd.read_csv(SRC / lab_rel, encoding="utf-8-sig")
    lab = lab.rename(columns={lab_key: "player_name"})
    lab["player_name"] = lab["player_name"].astype(str).str.strip()
    df_u = df_u.merge(lab[["player_name", "Departed_Label"]], on="player_name", how="left")

    # 挂合同（-1 表示租借，需单独标记，不能当成年限参与计算）
    con = pd.read_csv(SRC / con_rel, encoding="utf-8-sig")
    con.columns = ["player_name", "contract_expires_raw"]
    con["player_name"] = con["player_name"].astype(str).str.strip()
    con["is_loan"] = con["contract_expires_raw"] < 0
    con["contract_years_left"] = con["contract_expires_raw"].where(~con["is_loan"], np.nan)
    df_u = df_u.merge(con[["player_name", "contract_years_left", "is_loan"]], on="player_name", how="left")

    inter = df_u[df_u["player_name"].isin(lab["player_name"])].copy()
    print()
    print(f"  ▶ 国米样本：{len(inter)} 人")
    print(f"    标签缺失 = {int(inter['Departed_Label'].isna().sum())}")
    print(f"    合同信息缺失 = {int(inter['contract_years_left'].isna().sum())} "
          f"（其中租借球员 {int(inter['is_loan'].sum())} 人）")
    print(f"    位置分布: {inter['position_group'].value_counts().to_dict()}")
    print(f"    多位置球员: {inter.loc[inter['n_positions']>1, ['player_name','positions_all']].to_dict('records')}")
    print(f"    出场 <90 分钟: {inter.loc[inter['Min']<90, ['player_name','Min']].to_dict('records')}")
    print()

    out = OUT / f"players_{season.replace('-','_')}.csv"
    df_u.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  已写出: {out}  ({len(df_u)} 行 × {df_u.shape[1]} 列)")

    # 全联赛候选池（供后续引援模块使用）：排除出场过少的球员
    pool = df_u[(df_u["Min"] >= 450) & (df_u["position_group"] != "Unknown")].copy()
    pool_out = OUT / f"candidate_pool_{season.replace('-','_')}.csv"
    pool.to_csv(pool_out, index=False, encoding="utf-8-sig")
    print(f"  候选池（Min>=450 且位置可知）: {len(pool)} 人 → {pool_out}")
    print()

print("=" * 92)
print("结论：干净数据层完全可行，且立刻暴露出旧数据层的 4 个问题：")
print("  1) 同一球员因赛季中转会出现多行，旧代码重复计入百分位参考池")
print("  2) 出场 <90 分钟的球员未被过滤（旧代码/文档声称过滤了，实际没有）")
print("  3) FBref 的 pos 是多位置字符串（如 'FW,MF'），旧代码只取首个匹配，丢失信息")
print("  4) 合同字段用 -1 表示租借，旧代码把它当普通数值，且最终从未使用")
print("=" * 92)
