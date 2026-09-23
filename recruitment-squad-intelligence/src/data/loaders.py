"""
FBref CSV 加载器。

针对旧项目的缺陷：
- 旧项目用 `skiprows=2`（应为 3），把 row 2 的表头行当作数据读入，
  引入 1 行"幽灵球员"并污染 age 列的类型；
- 旧项目无列数断言，任何列错位都不会被发现；
- 旧项目 `except Exception: return None, None, None` 静默吞掉所有加载错误；
- 旧项目在多个文件中重复实现位置分组与列名映射，且指标名与数据列名不一致
  （如代码用 'G_minus_PK' 而数据列实际是 'G-PK'）。

本模块的做法：
- 用 `header=None` 读入原始网格，显式按层解析；
- 用 `EXPECTED_ROW1_METRICS` 与 `EXPECTED_DATA_ROWS` 做断言，任何异常都抛出；
- 列名统一规范化（`G+A` -> `G_plus_A` 等），使代码与数据列名一致。
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import config
from data import schemas
from data.schemas import EXPECTED_DATA_ROWS, EXPECTED_ROW1_METRICS, IDENTITY_COLUMNS


class DataLoadError(RuntimeError):
    """数据加载或结构校验失败。"""


# FBref 原始指标名 -> 规范化名
COLUMN_NORMALIZATION: dict[str, str] = {
    "G+A": "G_plus_A",
    "G-PK": "G_minus_PK",
    "G+A-PK": "G_plus_A_minus_PK",
    "npxG+xAG": "npxG_plus_xAG",
    "xG+xAG": "xG_plus_xAG",
    "G-xG": "G_minus_xG",
    "np:G-xG": "np_G_minus_xG",
    "A-xAG": "A_minus_xAG",
    "SoT%": "SoT_pct",
    "Sh/90": "Sh_per90",
    "SoT/90": "SoT_per90",
    "G/Sh": "G_per_Sh",
    "G/SoT": "G_per_SoT",
    "npxG/Sh": "npxG_per_Sh",
    "Cmp%": "Cmp_pct",
    "Tkl%": "Tkl_pct",
    "Succ%": "Succ_pct",
    "Tkld%": "Tkld_pct",
    "1/3": "Final_Third",
    "Def 3rd": "Def_3rd",
    "Mid 3rd": "Mid_3rd",
    "Att 3rd": "Att_3rd",
    "Att Pen": "Att_Pen",
    "Def Pen": "Def_Pen",
    "Per 90 Minutes_Gls": "Gls_per90",
    "Per 90 Minutes_Ast": "Ast_per90",
    "Per 90 Minutes_G+A": "G_plus_A_per90",
    "Per 90 Minutes_G-PK": "G_minus_PK_per90",
    "Per 90 Minutes_xG": "xG_per90",
    "Per 90 Minutes_xAG": "xAG_per90",
    "Per 90 Minutes_npxG": "npxG_per90",
    "Per 90 Minutes_npxG+xAG": "npxG_plus_xAG_per90",
    "Challenges_Tkl": "Challenges_Tkl",
    "SCA Types_PassLive": "SCA_PassLive",
    "SCA Types_PassDead": "SCA_PassDead",
    "SCA Types_TO": "SCA_TO",
    "SCA Types_Sh": "SCA_Sh",
    "SCA Types_Fld": "SCA_Fld",
    "SCA Types_Def": "SCA_Def",
}


def normalize_column_name(name: str) -> str:
    """把 FBref 的原始指标名规范化为合法的 Python 标识符风格。"""
    if name in COLUMN_NORMALIZATION:
        return COLUMN_NORMALIZATION[name]
    # 通用规则：空格/斜杠/百分号 -> 下划线；去掉其他非标识符字符
    out = name.replace("%", "_pct").replace("/", "_per_").replace(" ", "_")
    out = re.sub(r"[^0-9A-Za-z_]", "_", out)
    out = re.sub(r"_+", "_", out).strip("_")
    return out or name


def _build_flat_columns(raw: pd.DataFrame) -> list[str]:
    """
    从 FBref 三层表头还原扁平的列名。

    row 0 = 指标组名（Playing Time / Performance / Expected / ...）
    row 1 = 指标名（MP / Starts / Min / Gls / ...）
    row 2 = 标识列名（league / season / team / player，仅前 4 列有值）

    规则（实测得出，非猜测）：
    - 前 4 列固定为 IDENTITY_COLUMNS；
    - 第 4..7 列（nation/pos/age/born）可能出现在 row 0 或 row 1，
      取"row 0 非空则用 row 0，否则用 row 1"；
    - 其余列优先取 row 1（更细的指标名），row 1 为空时回退 row 0；
    - 重复指标名（如 possession 里的三个 '1/3'）用组名做前缀消歧。
    """
    row0 = raw.iloc[0].tolist()
    row1 = raw.iloc[1].tolist()
    n_cols = raw.shape[1]

    cols: list[str] = []
    seen: dict[str, int] = {}

    for i in range(n_cols):
        if i < len(IDENTITY_COLUMNS):
            cols.append(IDENTITY_COLUMNS[i])
            continue

        g = "" if pd.isna(row0[i]) else str(row0[i]).strip()
        m = "" if pd.isna(row1[i]) else str(row1[i]).strip()

        if i < 8:
            name = g or m
        else:
            name = m or g

        if not name:
            name = f"col_{i}"

        if name in seen:
            seen[name] += 1
            prefixed = f"{g}_{name}" if g else f"{name}_{seen[name]}"
            while prefixed in seen:
                seen[name] += 1
                prefixed = f"{g}_{name}_{seen[name]}"
            seen[prefixed] = 0
            name = prefixed
        else:
            seen[name] = 0

        cols.append(name)

    # 统一规范化（保留标识列原样）
    return [
        c if c in IDENTITY_COLUMNS else normalize_column_name(c)
        for c in cols
    ]


def load_fbref_table(path: Path, category: str, season: str,
                     expect_rows: bool = True) -> pd.DataFrame:
    """
    加载单个 FBref 统计表，返回带规范化列名的数据 DataFrame（不含表头行）。

    Raises
    ------
    DataLoadError
        文件缺失、结构不符、或行数/指标数与预期不一致。
    """
    if not path.exists():
        raise DataLoadError(f"数据文件不存在: {path}")

    raw = pd.read_csv(path, header=None)

    if raw.shape[0] <= config.FBREF_HEADER_ROWS:
        raise DataLoadError(
            f"{path.name}: 行数 {raw.shape[0]} <= 表头行数 {config.FBREF_HEADER_ROWS}，文件可能损坏"
        )

    # 断言 row 2 确实是标识行（"三层表头"假设的关键验证点）
    row2 = raw.iloc[2].tolist()[:4]
    if [str(x).strip() for x in row2] != list(IDENTITY_COLUMNS):
        raise DataLoadError(
            f"{path.name}: 第 3 行不是标识行，实际前 4 列 = {row2}。"
            f"文件结构可能已变化（预期 {list(IDENTITY_COLUMNS)}）"
        )

    # 断言 row 1 的指标数量
    row1 = raw.iloc[1].tolist()
    n_metrics = sum(1 for i, v in enumerate(row1) if i >= 4 and not pd.isna(v))
    exp_metrics = EXPECTED_ROW1_METRICS.get(category)
    if exp_metrics is not None and n_metrics != exp_metrics:
        raise DataLoadError(
            f"{path.name}: row1 指标数 = {n_metrics}，预期 {exp_metrics}。文件可能被截断或替换"
        )

    cols = _build_flat_columns(raw)
    if len(set(cols)) != len(cols):
        dupes = sorted({c for c in cols if cols.count(c) > 1})
        raise DataLoadError(f"{path.name}: 规范化后仍有重复列名: {dupes}")

    data = raw.iloc[config.FBREF_HEADER_ROWS:].reset_index(drop=True).copy()
    data.columns = cols

    if expect_rows:
        exp_rows = EXPECTED_DATA_ROWS.get(season, {}).get(category)
        if exp_rows is not None and len(data) != exp_rows:
            raise DataLoadError(
                f"{path.name}: 数据行数 = {len(data)}，预期 {exp_rows}。"
                f"很可能是 skiprows 错误读入了表头行"
            )

    for c in IDENTITY_COLUMNS:
        if data[c].isna().any():
            n = int(data[c].isna().sum())
            raise DataLoadError(f"{path.name}: 标识列 '{c}' 有 {n} 个缺失值")

    data["player"] = data["player"].astype(str).str.strip()
    data["team"] = data["team"].astype(str).str.strip()
    data["pos"] = data["pos"].astype(str).str.strip()
    data["season"] = data["season"].astype(str).str.strip()

    return data


def load_all_stat_tables(season: str) -> dict[str, pd.DataFrame]:
    """加载某赛季全部 8 个统计表。返回 {category: DataFrame}。"""
    sf = config.season_files(season)
    return {
        cat: load_fbref_table(getattr(sf, cat), cat, season)
        for cat in config.STAT_CATEGORIES
    }


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """把指定列转为数值；不可转换的值变为 NaN。"""
    out = df.copy()
    for c in columns:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def load_contracts(season: str) -> pd.DataFrame:
    """
    加载合同表。

    关键：CSV 中 `-1` 表示**租借球员**，其"剩余年数"不可解释。
    旧项目把 `-1` 当成普通数值（且实际上从未使用该文件）。
    这里拆成 `is_loan` + `contract_years_left`（租借为 NaN）。
    """
    path = config.season_files(season).contract
    if not path.exists():
        raise DataLoadError(f"合同文件不存在: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")
    if df.shape[1] != 2:
        raise DataLoadError(f"{path.name}: 期望 2 列，实际 {df.shape[1]} 列: {list(df.columns)}")

    df.columns = ["player_name", "contract_raw"]
    df["player_name"] = df["player_name"].astype(str).str.strip()
    df["contract_raw"] = pd.to_numeric(df["contract_raw"], errors="coerce")

    if df["contract_raw"].isna().any():
        bad = df.loc[df["contract_raw"].isna(), "player_name"].tolist()
        raise DataLoadError(f"{path.name}: 合同值不可解析的球员: {bad}")

    df["is_loan"] = (df["contract_raw"] == config.CONTRACT_LOAN_SENTINEL)
    df["contract_years_left"] = df["contract_raw"].where(~df["is_loan"])
    df["season"] = season

    return df[["player_name", "season", "contract_years_left", "is_loan", "contract_raw"]]


def load_departure_labels(season: str) -> pd.DataFrame:
    """加载国米球员离队标签。"""
    sf = config.season_files(season)
    path = sf.labels
    if path is None or not path.exists():
        raise DataLoadError(f"标签文件不存在: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")
    if sf.label_key not in df.columns:
        raise DataLoadError(
            f"{path.name}: 未找到标签列 '{sf.label_key}'，实际列 = {list(df.columns)}"
        )
    if "Departed_Label" not in df.columns:
        raise DataLoadError(f"{path.name}: 未找到 'Departed_Label' 列")

    df = df.rename(columns={sf.label_key: "player_name", "Departed_Label": "departed"})
    df["player_name"] = df["player_name"].astype(str).str.strip()
    df["departed"] = pd.to_numeric(df["departed"], errors="coerce")

    if df["departed"].isna().any():
        raise DataLoadError(f"{path.name}: 标签列存在不可解析值")
    if not df["departed"].isin([0, 1]).all():
        raise DataLoadError(
            f"{path.name}: 标签取值超出 {{0,1}}，实际 = {sorted(df['departed'].unique())}"
        )

    df["departed"] = df["departed"].astype(int)
    df["season"] = season

    dup = df.loc[df["player_name"].duplicated(), "player_name"].tolist()
    if dup:
        raise DataLoadError(f"{path.name}: 球员名重复: {dup}")

    return df[["player_name", "season", "departed"]]


# --------------------------------------------------------------------------------------
# FBref 原始 HTML（用于补充没有 CSV 的赛季，例如 2024-2025）
# --------------------------------------------------------------------------------------

# 解析后的 HTML 球员表 -> 与 CSV 口径一致的列名
_HTML_RENAMES: dict[str, str] = {
    "Player": "player",
    "Pos": "pos",
    "Squad": "team",
    "Age": "age",
    "Born": "born",
}


def load_fbref_html_standard(season: str) -> pd.DataFrame:
    """
    从 FBref 的原始 HTML 中解析 **球员级 standard 统计表**。

    背景：2024-2025 赛季在归档中只有 HTML、没有加工好的 CSV。
    旧项目完全未使用这些 HTML。

    实现要点（实测得出）：
    - FBref 把部分 `<table>` 放在 HTML 注释里，`pd.read_html` 默认看不到，
      必须先剥离 `<!--` / `-->`，否则只会拿到 2 张球队级表；
    - HTML 表是两层列头，需拍平；
    - 该文件**只有 standard 一类**统计，不含 goal/shooting/passing/possession/
      defensive/goalkeeper —— 因此该赛季只能用于 standard 口径的分析，
      M2 的跨类别指标（SCA/GCA/Tkl/...）在该赛季不可用。这一点必须显式声明。
    """
    if season not in config.LEGACY_HTML_FILES:
        raise DataLoadError(f"没有 {season} 的 HTML 文件记录")

    path = config.LEGACY_HTML_DIR / config.LEGACY_HTML_FILES[season]
    if not path.exists():
        raise DataLoadError(f"HTML 文件不存在: {path}")

    from io import StringIO

    raw_html = path.read_text(encoding="utf-8", errors="replace")
    stripped = raw_html.replace("<!--", "").replace("-->", "")

    try:
        tables = pd.read_html(StringIO(stripped))
    except ValueError as e:
        raise DataLoadError(f"{path.name}: 未解析到任何表格 ({e})") from e

    # 选球员表：包含 'Player' 列的表
    candidates = []
    for t in tables:
        flat = ["_".join(str(x) for x in c) if isinstance(c, tuple) else str(c)
                for c in t.columns]
        if any("Player" in c for c in flat):
            candidates.append((t, flat))
    if not candidates:
        raise DataLoadError(f"{path.name}: 未找到球员级表格")

    table, flat_cols = max(candidates, key=lambda x: x[0].shape[0] * x[0].shape[1])
    df = table.copy()
    df.columns = flat_cols

    # 拍平两层列头：取 underscore 后的层级名，再走与 CSV 相同的规范化。
    # 例：'Playing Time_Min' -> 'Min'；'Performance_G+A' -> 'G_plus_A'
    new_cols: list[str] = []
    for c in flat_cols:
        if c.startswith("Unnamed"):
            # ('Unnamed: 0_level_0', 'Rk') -> 取后段
            new_cols.append(c.split("_")[-1] if "_" in c else c)
        elif "_" in c:
            new_cols.append(c.split("_", 1)[1])
        else:
            new_cols.append(c)
    df.columns = [normalize_column_name(c) for c in new_cols]

    # 规范化后可能产生重名（例如 'Per 90 Minutes_Gls' 与 'Performance_Gls'
    # 都拍平成 'Gls'）。HTML 的 per-90 分档列本系统不使用（自算），
    # 因此对重名列保留**第一次出现**的那一列即可。
    if df.columns.duplicated().any():
        dupes = sorted(set(df.columns[df.columns.duplicated()].tolist()))
        df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()

    # 去掉行内重复的表头行（read_html 有时把二级表头当数据）
    if "Player" in df.columns:
        df = df[df["Player"].astype(str).str.strip() != "Player"]

    if "Player" not in df.columns:
        raise DataLoadError(f"{path.name}: 球员表中缺少 'Player' 列，实际列 = {list(df.columns)}")

    df = df.rename(columns=_HTML_RENAMES)

    # 打上赛季标识
    season_tag = config.HTML_SEASON_TAGS[season]
    df["league"] = "ITA-Serie A"
    df["season"] = season_tag

    # 清理 Nation（HTML 里形如 'ie IRL'，取后一段的国家代码）
    if "Nation" in df.columns:
        df["nation"] = (
            df["Nation"].astype(str).str.split().str[-1].replace({"nan": pd.NA})
        )
    else:
        df["nation"] = pd.NA

    # 数值化
    numeric_cols = [
        "age", "MP", "Starts", "Min", "90s", "Gls", "Ast", "G_plus_A", "G_minus_PK",
        "PK", "PKatt", "CrdY", "CrdR", "xG", "npxG", "xAG", "npxG_plus_xAG",
        "PrgC", "PrgP", "PrgR",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    keep = [c for c in schemas.STANDARD_COLUMNS if c in df.columns]
    missing = [c for c in schemas.STANDARD_COLUMNS if c not in df.columns]
    if missing:
        raise DataLoadError(f"{path.name}: 球员表缺少必需列 {missing}")

    out = df[keep].copy()
    out["player"] = out["player"].astype(str).str.strip()
    out["team"] = out["team"].astype(str).str.strip()
    out["pos"] = out["pos"].astype(str).str.strip()
    out["season"] = out["season"].astype(str).str.strip()

    # 至少要有基本的时间数据
    if out["Min"].isna().all():
        raise DataLoadError(f"{path.name}: Min 列全为空，解析可能失败")

    return out


__all__ = [
    "DataLoadError", "COLUMN_NORMALIZATION", "normalize_column_name",
    "load_fbref_table", "load_all_stat_tables", "to_numeric",
    "load_contracts", "load_departure_labels", "load_fbref_html_standard",
    "_build_flat_columns",
]
