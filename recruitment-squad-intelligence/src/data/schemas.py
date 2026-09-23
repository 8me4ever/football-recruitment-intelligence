"""
Schema 定义与校验。

针对旧项目的缺陷：
- 旧项目 `except Exception: return None, None, None` 静默吞掉一切错误；
- 无列数断言，`skiprows=2` 的心智错误长期存在而未被发现；
- 无范围检查，论文中声称的"Z-score/IQR 异常值检测"在代码里不存在。

本模块提供：列定义 + 显式断言 + 范围检查，全部失败都 **抛异常**（不静默）。
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# --------------------------------------------------------------------------------------
# FBref 表头结构
# --------------------------------------------------------------------------------------

# FBref 三层表头各层的起始列（前 4 列为标识列）
IDENTITY_COLUMNS: tuple[str, ...] = ("league", "season", "team", "player")

# row 1（指标名层）在前 8 列的内容：
#   [nan, nan, nan, nan, nation, pos, age, born]
# 注意：nation/pos/age/born 位于 row 1 的第 4..7 个位置，而标准表把它放在 row 0。
# 因此解析时必须用「row 0 与 row 1 取并集」的方式还原列名，不能只看一层。
ROW0_META_COLUMNS: tuple[str, ...] = ("nation", "pos", "age", "born")

# 标准统计表：row 0 前 8 列为 [nan]*4 + nation/pos/age/born；row 1 前 8 列为 [nan]*8。
# 其他统计表：row 0 与 row 1 都可能是 [nan]*4 + 各自内容。
# 标准统计表：与原始数据实际列名一致（规范化后）。
# 实测确认：数据里是 G_plus_A / G_minus_PK / npxG_plus_xAG，**没有** 单独的 'GA' 列。
STANDARD_COLUMNS: tuple[str, ...] = (
    "league", "season", "team", "player", "nation", "pos", "age", "born",
    "MP", "Starts", "Min", "90s",
    "Gls", "Ast", "G_plus_A", "G_minus_PK", "PK", "PKatt", "CrdY", "CrdR",
    "xG", "npxG", "xAG", "npxG_plus_xAG",
    "PrgC", "PrgP", "PrgR",
)

# 每个统计文件在 row 1 上的「指标名」列数（用于断言文件未被替换/截断）
# 这些数字来自对原始文件的实测，是防止静默错位的第一道防线。
EXPECTED_ROW1_METRICS: dict[str, int] = {
    "standard": 29,
    "goal": 16,
    "shooting": 17,
    "passing": 16,
    "possession": 22,
    "defensive": 12,
    "goalkeeper": 19,
    "goalkeeper_advance": 25,
}

# 每个赛季各统计文件的期望数据行数（来自实测；用于检测"读到冗余表头行"这类错误）
EXPECTED_DATA_ROWS: dict[str, dict[str, int]] = {
    "2022-2023": {
        "standard": 603, "goal": 603, "shooting": 603, "passing": 603,
        "possession": 603, "defensive": 603,
        "goalkeeper": 49, "goalkeeper_advance": 49,
    },
    "2023-2024": {
        "standard": 616, "goal": 616, "shooting": 616, "passing": 616,
        "possession": 616, "defensive": 616,
        "goalkeeper": 51, "goalkeeper_advance": 51,
    },
}


# --------------------------------------------------------------------------------------
# 成品表 schema
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnSpec:
    """一列的期望类型与取值范围（数值列）。"""

    dtype: str                      # "str" | "int" | "float" | "bool"
    min_value: float | None = None
    max_value: float | None = None
    allow_missing: bool = True


PLAYERS_SCHEMA: dict[str, ColumnSpec] = {
    "player_name": ColumnSpec("str", allow_missing=False),
    "season": ColumnSpec("str", allow_missing=False),
    "team": ColumnSpec("str", allow_missing=False),
    "nation": ColumnSpec("str"),
    "primary_position": ColumnSpec("str", allow_missing=False),
    "positions_all": ColumnSpec("str", allow_missing=False),
    "n_positions": ColumnSpec("int", min_value=1, max_value=4, allow_missing=False),
    "age": ColumnSpec("float", min_value=15, max_value=45, allow_missing=False),
    # ---- standard 表的计数型指标（赛季中转会时对多行求和）----
    "MP": ColumnSpec("float", min_value=0),
    "Starts": ColumnSpec("float", min_value=0),
    "Min": ColumnSpec("float", min_value=0),
    "90s": ColumnSpec("float", min_value=0),
    "Gls": ColumnSpec("float", min_value=0),
    "Ast": ColumnSpec("float", min_value=0),
    "G_plus_A": ColumnSpec("float", min_value=0),
    "G_minus_PK": ColumnSpec("float"),
    "PK": ColumnSpec("float", min_value=0),
    "PKatt": ColumnSpec("float", min_value=0),
    "CrdY": ColumnSpec("float", min_value=0),
    "CrdR": ColumnSpec("float", min_value=0),
    "xG": ColumnSpec("float", min_value=0),
    "npxG": ColumnSpec("float", min_value=0),
    "xAG": ColumnSpec("float", min_value=0),
    "npxG_plus_xAG": ColumnSpec("float", min_value=0),
    "PrgC": ColumnSpec("float", min_value=0),
    "PrgP": ColumnSpec("float", min_value=0),
    "PrgR": ColumnSpec("float", min_value=0),
    # ---- 派生 per-90（由本系统按总计数/总 90s 计算，不采用 FBref 的分档列）----
    "Gls_per90": ColumnSpec("float", min_value=0),
    "Ast_per90": ColumnSpec("float", min_value=0),
    "GA_per90": ColumnSpec("float", min_value=0),
    "xG_per90": ColumnSpec("float", min_value=0),
    "xAG_per90": ColumnSpec("float", min_value=0),
    "npxG_per90": ColumnSpec("float", min_value=0),
    "PrgC_per90": ColumnSpec("float", min_value=0),
    "PrgP_per90": ColumnSpec("float", min_value=0),
    "PrgR_per90": ColumnSpec("float", min_value=0),
    # ---- 派生标记 ----
    "is_low_sample": ColumnSpec("bool", allow_missing=False),
    "is_inter": ColumnSpec("bool", allow_missing=False),
    "n_source_rows": ColumnSpec("int", min_value=1, allow_missing=False),
    "transferred_midseason": ColumnSpec("bool", allow_missing=False),
    # ---- 合同（来自独立 CSV；联赛其他球员无合同数据，故允许缺失）----
    "contract_years_left": ColumnSpec("float", min_value=0, max_value=10),
    "is_loan": ColumnSpec("bool", allow_missing=False),
    "contract_raw": ColumnSpec("float"),
    "has_contract_info": ColumnSpec("bool", allow_missing=False),
    # ---- 标签（仅国米球员有；没有标签文件的赛季整列为 NaN）----
    "departed": ColumnSpec("int", min_value=0, max_value=1),
    "has_departure_label": ColumnSpec("bool", allow_missing=False),
}

# 候选池 = 球员表去掉标签列（候选池不依赖离队标签）
CANDIDATE_POOL_SCHEMA: dict[str, ColumnSpec] = {
    k: v for k, v in PLAYERS_SCHEMA.items() if k != "departed"
}

# 国米阵容表
INTER_SQUAD_SCHEMA: dict[str, ColumnSpec] = dict(PLAYERS_SCHEMA)

CONTRACTS_SCHEMA: dict[str, ColumnSpec] = {
    "player_name": ColumnSpec("str", allow_missing=False),
    "season": ColumnSpec("str", allow_missing=False),
    "contract_years_left": ColumnSpec("float", min_value=0, max_value=10),
    "is_loan": ColumnSpec("bool", allow_missing=False),
    "contract_raw": ColumnSpec("float", allow_missing=False),
}

LABELS_SCHEMA: dict[str, ColumnSpec] = {
    "player_name": ColumnSpec("str", allow_missing=False),
    "season": ColumnSpec("str", allow_missing=False),
    "departed": ColumnSpec("int", min_value=0, max_value=1, allow_missing=False),
}


class SchemaError(AssertionError):
    """schema 校验失败。"""


def check_columns(df: pd.DataFrame, expected: dict[str, ColumnSpec], table_name: str) -> None:
    """断言 DataFrame 恰好包含期望的列集合。"""
    got = set(df.columns)
    want = set(expected)
    missing = want - got
    extra = got - want
    if missing or extra:
        raise SchemaError(
            f"[{table_name}] 列集合不符。缺失={sorted(missing)}；多余={sorted(extra)}"
        )


def check_ranges(df: pd.DataFrame, expected: dict[str, ColumnSpec], table_name: str) -> None:
    """断言数值列落在允许范围内，且不可缺失的列确实无缺失。"""
    problems: list[str] = []
    for col, spec in expected.items():
        if col not in df.columns:
            continue
        s = df[col]

        if not spec.allow_missing:
            n_na = int(s.isna().sum())
            if n_na:
                problems.append(f"{col}: 有 {n_na} 个缺失值（不允许缺失）")

        if spec.dtype in ("int", "float") and spec.min_value is not None:
            bad = s.dropna() < spec.min_value
            if bad.any():
                problems.append(
                    f"{col}: {int(bad.sum())} 个值 < 下限 {spec.min_value}"
                    f"（最小={s.min()}）"
                )
        if spec.dtype in ("int", "float") and spec.max_value is not None:
            bad = s.dropna() > spec.max_value
            if bad.any():
                problems.append(
                    f"{col}: {int(bad.sum())} 个值 > 上限 {spec.max_value}"
                    f"（最大={s.max()}）"
                )

    if problems:
        raise SchemaError(f"[{table_name}] 范围校验失败:\n  - " + "\n  - ".join(problems))


def validate(df: pd.DataFrame, expected: dict[str, ColumnSpec], table_name: str) -> None:
    """列集合 + 取值范围的完整校验。"""
    check_columns(df, expected, table_name)
    check_ranges(df, expected, table_name)


__all__ = [
    "IDENTITY_COLUMNS", "ROW0_META_COLUMNS", "STANDARD_COLUMNS",
    "EXPECTED_ROW1_METRICS", "EXPECTED_DATA_ROWS",
    "ColumnSpec", "PLAYERS_SCHEMA", "CONTRACTS_SCHEMA", "LABELS_SCHEMA",
    "SchemaError", "check_columns", "check_ranges", "validate",
]
