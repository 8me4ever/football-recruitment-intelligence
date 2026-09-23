"""
回归测试：数据加载层。

每一项测试都对应审计中发现的**一个具体缺陷**，目的是让旧缺陷无法再次出现。

对应关系：
- test_no_phantom_header_row      <- 旧项目 skiprows=2 读入一行幽灵表头
- test_expected_row_counts        <- 无行数断言，错位长期未被发现
- test_identity_columns_not_null  <- 无校验
- test_column_normalization       <- 代码列名与数据列名不一致（'G_minus_PK' vs 'G-PK'）
- test_loader_raises_not_silent   <- 旧项目 `except: return None,None,None` 静默吞异常
- test_row2_is_identity_row       <- 三层表头假设被显式验证
"""
from __future__ import annotations

import pandas as pd
import pytest

from config import config
from data import loaders, schemas


@pytest.mark.parametrize("season", config.SEASONS)
@pytest.mark.parametrize("category", sorted(config.STAT_CATEGORIES))
def test_expected_row_counts(season: str, category: str) -> None:
    """回归：每个统计表的数据行数必须与实测预期一致。

    旧项目用 skiprows=2 会多读一行，行数变成 604（预期 603）而不自知。
    """
    path = getattr(config.season_files(season), category)
    df = loaders.load_fbref_table(path, category, season)
    expected = schemas.EXPECTED_DATA_ROWS[season][category]
    assert len(df) == expected, (
        f"{season}/{category}: 行数 {len(df)} != 预期 {expected}"
    )


@pytest.mark.parametrize("season", config.SEASONS)
def test_no_phantom_header_row(season: str) -> None:
    """回归：数据中不得出现值为 'player' 的幽灵行。

    这是旧项目 skiprows 心智错误的直接症状。
    """
    std = loaders.load_fbref_table(
        config.season_files(season).standard, "standard", season
    )
    assert not (std["player"] == "player").any(), "读到了表头幽灵行"
    assert not (std["league"] == "league").any(), "读到了表头幽灵行"
    for c in ("league", "season", "team", "player"):
        assert std[c].notna().all(), f"标识列 {c} 存在缺失"


@pytest.mark.parametrize("season", config.SEASONS)
def test_age_is_numeric(season: str) -> None:
    """回归：age 必须是数值型且无缺失。

    旧项目因多读一行表头，age 列被污染为 object/float 混合。
    """
    std = loaders.load_fbref_table(
        config.season_files(season).standard, "standard", season
    )
    age = pd.to_numeric(std["age"], errors="coerce")
    assert age.notna().all(), "age 存在无法解析的值"
    assert age.between(15, 45).all(), "age 落在不合理区间"


@pytest.mark.parametrize("season", config.SEASONS)
def test_column_normalization(season: str) -> None:
    """回归：列名必须已规范化，不得残留 'G+A' / 'G-PK' / 'npxG+xAG' 等原始名。"""
    std = loaders.load_fbref_table(
        config.season_files(season).standard, "standard", season
    )
    for bad in ("G+A", "G-PK", "npxG+xAG", "Per 90 Minutes_Gls", "Cmp%"):
        assert bad not in std.columns, f"列名未规范化: {bad}"
    for good in ("G_plus_A", "G_minus_PK", "npxG_plus_xAG"):
        assert good in std.columns, f"缺少规范化列: {good}"


@pytest.mark.parametrize("season", config.SEASONS)
def test_identity_columns(season: str) -> None:
    """标识列必须存在且球队数为 20。"""
    std = loaders.load_fbref_table(
        config.season_files(season).standard, "standard", season
    )
    assert list(std.columns[:4]) == list(schemas.IDENTITY_COLUMNS)
    assert std["team"].nunique() == 20, "Serie A 应有 20 支球队"


def test_loader_raises_not_silent(tmp_path) -> None:
    """回归：加载失败必须抛异常，绝不静默返回 None。

    旧项目 `except Exception: return None, None, None` 使所有加载错误
    都表现为"无结果"，掩盖了数据问题。
    """
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(loaders.DataLoadError):
        loaders.load_fbref_table(missing, "standard", "2022-2023")


def test_loader_rejects_bad_structure(tmp_path) -> None:
    """回归：结构不符必须抛异常（旧项目无任何结构断言）。"""
    bad = tmp_path / "bad.csv"
    # 只有 2 行，不足以构成三层表头 + 数据
    bad.write_text("a,b,c,d\n1,2,3,4\n", encoding="utf-8")
    with pytest.raises(loaders.DataLoadError):
        loaders.load_fbref_table(bad, "standard", "2022-2023")


def test_row2_is_identity_row() -> None:
    """显式验证三层表头假设：第 3 行（index 2）是标识行。"""
    path = config.season_files("2022-2023").standard
    raw = pd.read_csv(path, header=None)
    assert [str(x).strip() for x in raw.iloc[2].tolist()[:4]] == list(
        schemas.IDENTITY_COLUMNS
    )
    assert config.FBREF_HEADER_ROWS == 3


@pytest.mark.parametrize("season", config.SEASONS)
def test_contract_loan_sentinel(season: str) -> None:
    """回归：合同 CSV 中的 -1 必须被识别为租借，而不是当成负的年限。

    旧项目把 -1 当普通数值（且实际从未使用该文件）。
    """
    con = loaders.load_contracts(season)
    assert con["is_loan"].sum() == 4, f"{season} 应有 4 名租借球员"
    loans = con[con["is_loan"]]
    assert loans["contract_years_left"].isna().all(), "租借球员的年限应为空"
    assert not con.loc[~con["is_loan"], "contract_years_left"].isna().any()
    assert (con.loc[~con["is_loan"], "contract_years_left"] >= 0).all()


@pytest.mark.parametrize("season", config.SEASONS)
def test_labels_binary_and_unique(season: str) -> None:
    """标签必须是 {0,1} 且球员名唯一。"""
    lab = loaders.load_departure_labels(season)
    assert set(lab["departed"].unique()) <= {0, 1}
    assert not lab["player_name"].duplicated().any()


def test_missing_contract_file_raises(tmp_path, monkeypatch) -> None:
    """合同文件缺失时应抛异常，而不是静默跳过。"""
    monkeypatch.setitem(config.CONTRACT_FILES, "2022-2023", tmp_path / "nope.csv")
    with pytest.raises(loaders.DataLoadError):
        loaders.load_contracts("2022-2023")
