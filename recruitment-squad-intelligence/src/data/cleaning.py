"""
清洗与规范化。

针对旧项目的缺陷：
1. `skiprows` 心智错误        -> 已在 loaders 中修复
2. 赛季中转会导致球员重复      -> `aggregate_player_season()` 合并（旧项目未去重，52 行重复进入参考池）
3. 多位置信息被丢弃            -> `parse_positions()` 保留完整位置列表（旧项目只取首个字母，影响 118/143 人）
4. 低出场样本未过滤            -> `mark_low_sample()` 标记而非删除（旧项目文档声称过滤，代码未实现）
5. 合同 `-1` 被当成数值        -> 已在 loaders 中拆分为 is_loan
6. 位置分组逻辑重复 4 次        -> 此处唯一实现
"""
from __future__ import annotations

import pandas as pd

from config import config

# 参与数值聚合的计数型指标（standard 表中的真实规范化列名）
COUNT_METRICS: tuple[str, ...] = (
    "MP", "Starts", "Min", "90s",
    "Gls", "Ast", "G_plus_A", "G_minus_PK", "PK", "PKatt", "CrdY", "CrdR",
    "xG", "npxG", "xAG", "npxG_plus_xAG",
    "PrgC", "PrgP", "PrgR",
)

# 由本系统自行计算的 per-90 指标：分子（计数列） -> 输出列名。
# 不采用 FBref 自身的 "Per 90 Minutes" 分档列，原因：
#   1) 部分列是按分档（如 G+A 分档）计算的，列名被组名前缀污染；
#   2) 自算可保证"分子=合并后总计数、分母=合并后总 90s"，去重后口径一致。
PER90_DEFINITIONS: dict[str, str] = {
    "Gls": "Gls_per90",
    "Ast": "Ast_per90",
    "G_plus_A": "GA_per90",
    "xG": "xG_per90",
    "xAG": "xAG_per90",
    "npxG": "npxG_per90",
    "PrgC": "PrgC_per90",
    "PrgP": "PrgP_per90",
    "PrgR": "PrgR_per90",
}


class CleaningError(ValueError):
    """清洗阶段的校验失败。"""


def parse_positions(pos) -> tuple[str, list[str]]:
    """
    解析 FBref 的 pos 字段。

    FBref 的 pos 可能是多值字符串，如 'FW,MF'、'MF,DF'、'DF'。
    实测确认（见审计）：**逗号顺序本身表达主次**——
    `FW,MF` 与 `MF,FW` 在数据中是两种不同的取值，说明第一位是主要位置。
    因此本系统以 **FBref 列出的第一个位置** 作为该 stint 的主位置。

    旧项目的做法（if-elif 链按 GK->FW->MF->DF 顺序取首个命中）会：
      - 把 'MF,DF' 判为中场（应以后卫为主）
      - 把 'FW,MF' 判为前锋（偶然正确）
      - 丢弃第二位置的全部信息

    返回
    ----
    (primary_position_label, [位置代号按 FBref 顺序])
    """
    if pos is None or (isinstance(pos, float) and pd.isna(pos)):
        return "Unknown", []

    raw = str(pos).strip()
    if not raw or raw.lower() in ("nan", "none"):
        return "Unknown", []

    parts = [p.strip().upper() for p in raw.split(",") if p.strip()]
    valid: list[str] = []
    for p in parts:
        if p in config.POSITION_LABELS and p not in valid:
            valid.append(p)

    if not valid:
        return "Unknown", []

    return config.POSITION_LABELS[valid[0]], valid


def aggregate_player_season(
    df: pd.DataFrame,
    numeric_metrics: tuple[str, ...] = COUNT_METRICS,
) -> pd.DataFrame:
    """
    把一个赛季的球员行聚合到「唯一球员」。

    背景：球员在赛季中转会会出现两行（实测每赛季 52 行 / 26 人）。
    旧项目未去重，这些球员被计两次进入百分位参考池，扭曲分位数。

    聚合规则：
    - 计数型指标（进球、分钟、牌等）：求和（合并两段效力，语义正确）
    - `age`：取最大（赛季中过生日的情况，取较晚的年龄更贴近赛季末状态）
    - `team`：若跨队则记为 'MULTI:队A|队B'，否则为该队
    - `transferred_midseason`：是否出现多行
    - `positions_all`：合并两行的位置并集
    - `primary_position`：按优先级从并集中重新选取
    """
    if df.empty:
        raise CleaningError("输入为空")

    for c in ("player", "team", "pos"):
        if c not in df.columns:
            raise CleaningError(f"缺少必需列: {c}")

    work = df.copy()
    for c in numeric_metrics:
        if c in work.columns:
            work[c] = pd.to_numeric(work[c], errors="coerce")
    work["age"] = pd.to_numeric(work["age"], errors="coerce")

    if work["age"].isna().any():
        bad = work.loc[work["age"].isna(), "player"].unique().tolist()
        raise CleaningError(f"age 无法解析的球员: {bad}")

    agg_numeric = [c for c in numeric_metrics if c in work.columns]
    g = work.groupby("player", as_index=False).agg(
        {**{c: "sum" for c in agg_numeric}, "age": "max"}
    )
    g = g.rename(columns={"player": "player_name"})

    # 队伍
    def _team(series: pd.Series) -> str:
        vals = sorted({str(x) for x in series})
        return vals[0] if len(vals) == 1 else "MULTI:" + "|".join(vals)

    team_map = work.groupby("player")["team"].apply(_team)
    g["team"] = g["player_name"].map(team_map)

    # 国家（取首个非空）
    if "nation" in work.columns:
        nation_map = work.groupby("player")["nation"].first()
        g["nation"] = g["player_name"].map(nation_map)

    # 位置：合并所有 stint 的位置并集
    def _positions(series: pd.Series) -> list[str]:
        merged: list[str] = []
        for v in series:
            _, codes = parse_positions(v)
            for c in codes:
                if c not in merged:
                    merged.append(c)
        return merged

    pos_map = work.groupby("player")["pos"].apply(_positions)

    # 主位置：取**出场时间最多的那个 stint** 的主位置。
    # 理由：合并后的球员跨队效力，各 stint 位置可能不同（实测 6-9 人），
    # 用分钟数决定哪段是主要身份，比人为规定位置优先级更贴近事实。
    def _primary(name: str) -> str:
        g = work[work["player"] == name]
        if g.empty:
            return "Unknown"
        idx = g["Min"].idxmax()
        label, _ = parse_positions(g.loc[idx, "pos"])
        return label

    primary_map = {n: _primary(n) for n in pos_map.index}

    g["positions_all"] = g["player_name"].map(
        lambda n: ",".join(pos_map.get(n, []))
    )
    g["primary_position"] = g["player_name"].map(primary_map)
    g["n_positions"] = g["player_name"].map(lambda n: len(pos_map.get(n, [])))
    g["n_source_rows"] = g["player_name"].map(work.groupby("player").size())
    g["transferred_midseason"] = g["n_source_rows"] > 1

    # 未识别位置的球员单独标记，便于后续审查
    unknown = int((g["primary_position"] == "Unknown").sum())
    if unknown:
        names = g.loc[g["primary_position"] == "Unknown", "player_name"].tolist()
        raise CleaningError(f"有 {unknown} 名球员的位置无法解析: {names[:10]}")

    # 清理 positions_all 为空的异常（位置可解析却有 n_positions=0 不可能，双保险）
    if (g["n_positions"] < 1).any():
        raise CleaningError("存在 n_positions < 1 的球员，位置解析异常")

    return g


def mark_low_sample(df: pd.DataFrame, threshold: int | None = None) -> pd.DataFrame:
    """
    标记低样本球员（不删除）。

    旧项目文档与论文均声称按 min_minutes=90 过滤，但最终管线从未实现；
    实测有 75/88 行球员出场 <90 分钟（最少 5 分钟）。
    本系统：**标记而非删除**，让下游决定如何降级处理（删除会掩盖数据问题）。
    """
    thr = config.MIN_MINUTES_RELIABLE if threshold is None else threshold
    out = df.copy()
    out["is_low_sample"] = out["Min"] < thr
    return out


def mark_inter(df: pd.DataFrame) -> pd.DataFrame:
    """
    标记国际米兰球员。

    注意：不能用 `str.contains('Inter')` —— 那会误伤其他含该子串的队名，
    且跨队球员的 team 形如 'MULTI:A|B'，需要用分隔后的精确匹配。
    """
    target = config.INTER_TEAM_NAME.strip().lower()

    def _is_inter(team_val) -> bool:
        if team_val is None or (isinstance(team_val, float) and pd.isna(team_val)):
            return False
        s = str(team_val)
        if s.startswith("MULTI:"):
            parts = s[len("MULTI:"):].split("|")
        else:
            parts = [s]
        return any(p.strip().lower() == target for p in parts)

    out = df.copy()
    out["is_inter"] = out["team"].map(_is_inter).astype(bool)
    return out


def attach_contracts(players: pd.DataFrame, contracts: pd.DataFrame) -> pd.DataFrame:
    """
    把合同信息挂到球员表。

    旧项目**从未**把合同数据传入计算函数，导致合同百分位恒为 0.5、
    合同年限恒为 2.0 常数 —— 论文关于合同 sigmoid 的整章论述因此无效。
    """
    if "player_name" not in players.columns:
        raise CleaningError("players 缺少 player_name")
    if "player_name" not in contracts.columns:
        raise CleaningError("contracts 缺少 player_name")

    exp = {"player_name", "season", "contract_years_left", "is_loan", "contract_raw"}
    missing = exp - set(contracts.columns)
    if missing:
        raise CleaningError(f"contracts 缺少列: {sorted(missing)}")

    out = players.merge(
        contracts[["player_name", "contract_years_left", "is_loan", "contract_raw"]],
        on="player_name",
        how="left",
    )

    # 未匹配到合同的球员：is_loan 记为 False，年限留空。
    # 这是**已知的数据缺口**，用 has_contract_info 显式记录，而不是静默填 0。
    out["is_loan"] = out["is_loan"].where(out["is_loan"].notna(), False).astype("bool")
    out["has_contract_info"] = out["contract_raw"].notna()
    return out


def attach_labels(players: pd.DataFrame, labels: pd.DataFrame | None) -> pd.DataFrame:
    """
    把离队标签挂到球员表。

    - 有标签文件：匹配到的球员 `has_departure_label=True`；
    - 无标签文件（如仅有 HTML 的赛季）：`departed` 整列为 NaN、
      `has_departure_label` 全为 False。
    两种情况都保持**相同的列结构**，避免下游按赛季分支处理。
    """
    out = players.copy()
    if labels is None:
        # 可空整数类型：整列无标签时不产生全 NA 的 object 列，
        # 也避免 pandas concat 的 FutureWarning。
        out["departed"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
        out["has_departure_label"] = False
        return out

    if "departed" not in labels.columns:
        raise CleaningError("labels 缺少 departed 列")

    out = out.merge(labels[["player_name", "departed"]], on="player_name", how="left")
    out["has_departure_label"] = out["departed"].notna()
    out["departed"] = out["departed"].astype("Int64")
    return out


def add_per90(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算 per-90 指标。

    分母用合并后的总 90s（= 总分钟 / 90）。若 90s 为 0（极端低样本），
    分母置 NaN 使结果为 NaN，而**不是填 0** —— 0 会伪装成"表现差"，
    而真相是"没有足够样本可评价"。
    """
    out = df.copy()
    denom = pd.to_numeric(out["90s"], errors="coerce")
    safe = denom.where(denom > 0)

    for numerator, target in PER90_DEFINITIONS.items():
        if numerator not in out.columns:
            raise CleaningError(f"缺少 per-90 分子列: {numerator}")
        out[target] = pd.to_numeric(out[numerator], errors="coerce") / safe

    return out


def build_players_table(
    standard_df: pd.DataFrame,
    contracts: pd.DataFrame,
    labels: pd.DataFrame | None,
    season: str,
) -> pd.DataFrame:
    """构建某赛季的球员成品表。"""
    players = aggregate_player_season(standard_df)
    players = add_per90(players)
    players = mark_low_sample(players)
    players = mark_inter(players)
    players = attach_contracts(players, contracts)
    players = attach_labels(players, labels)
    players.insert(1, "season", season)
    return players


def build_candidate_pool(
    players: pd.DataFrame, min_minutes: int | None = None
) -> pd.DataFrame:
    """
    构建引援候选池。

    规则：
    - 出场分钟 >= min_minutes（默认 450，旧项目的 90 过松）
    - 位置可解析（构造阶段已断言）
    - **不排除国米球员**，但用 is_inter 标记，便于在引援搜索时区分
      "已在队内"与"市场可选"。
    """
    thr = config.MIN_MINUTES_CANDIDATE if min_minutes is None else min_minutes
    pool = players[players["Min"] >= thr].copy()
    pool = pool.sort_values(["primary_position", "Min"], ascending=[True, False])
    return pool.reset_index(drop=True)


__all__ = [
    "CleaningError", "COUNT_METRICS", "PER90_DEFINITIONS", "parse_positions",
    "aggregate_player_season", "add_per90", "mark_low_sample", "mark_inter",
    "attach_contracts", "attach_labels", "build_players_table", "build_candidate_pool",
]
