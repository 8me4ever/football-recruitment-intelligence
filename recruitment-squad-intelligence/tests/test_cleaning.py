"""
回归测试：清洗层。

对应关系：
- test_aggregate_removes_duplicates   <- 旧项目未去重，52 行重复进入百分位参考池
- test_midseason_transfer_metrics     <- 合并时计数指标应求和（而非取其一）
- test_multiposition_parsed           <- 旧项目丢弃第二位置（影响 118/143 人）
- test_primary_position_uses_fbref_order <- 旧项目的位置优先级取法错误
- test_primary_position_uses_max_minutes <- 跨队球员按主要 stint 定位置
- test_low_sample_marked_not_dropped  <- 旧项目文档声称过滤、代码未实现；新系统标记不删除
- test_contract_attached              <- 旧项目合同数据从未接入
- test_candidate_pool_threshold       <- 旧项目的 90 分钟门槛过松
- test_inter_exact_match              <- 不得用子串匹配识别国米
"""
from __future__ import annotations

import pandas as pd
import pytest

from config import config
from data import cleaning, loaders


# --------------------------------------------------------------------------------------
# 位置解析
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pos,expected_primary,expected_all",
    [
        ("DF", "Defender", ["DF"]),
        ("MF,DF", "Midfielder", ["MF", "DF"]),
        ("DF,MF", "Defender", ["DF", "MF"]),
        ("FW,MF", "Forward", ["FW", "MF"]),
        ("MF,FW", "Midfielder", ["MF", "FW"]),
        ("GK", "Goalkeeper", ["GK"]),
    ],
)
def test_multiposition_parsed(pos, expected_primary, expected_all) -> None:
    """回归：多位置必须完整保留，且主位置取 FBref 列出的第一个。

    旧项目只取首个命中字母并丢弃其余位置。
    """
    primary, allp = cleaning.parse_positions(pos)
    assert primary == expected_primary
    assert allp == expected_all


def test_multiposition_order_matters() -> None:
    """回归：'FW,MF' 与 'MF,FW' 必须给出不同的主位置。

    实测这两个值在数据中同时存在（2022-23 分别有 41 与 40 行），
    说明逗号顺序确实表达主次，不能归一化掉。
    """
    assert cleaning.parse_positions("FW,MF")[0] == "Forward"
    assert cleaning.parse_positions("MF,FW")[0] == "Midfielder"


@pytest.mark.parametrize("bad", [None, float("nan"), "", "nan", "None", "XYZ"])
def test_position_unknown(bad) -> None:
    assert cleaning.parse_positions(bad) == ("Unknown", [])


def test_unknown_position_raises_in_aggregate() -> None:
    """位置无法解析时必须报错，不能静默归为 Unknown 混入分析。"""
    df = pd.DataFrame(
        {
            "player": ["X"],
            "team": ["A"],
            "pos": ["XYZ"],
            "age": [25],
            "Min": [900],
            "90s": [10.0],
        }
    )
    with pytest.raises(cleaning.CleaningError, match="位置无法解析"):
        cleaning.aggregate_player_season(df)


# --------------------------------------------------------------------------------------
# 去重与聚合
# --------------------------------------------------------------------------------------

def _mini_frame() -> pd.DataFrame:
    """构造一个与真实结构一致的迷你表：球员 P 有两段效力（赛季中转会）。

    必须包含 add_per90 所需的全部分子列，否则会因缺列而报错（这本身也是一种保护）。
    """
    rows = [
        # player, team, pos, age, Min, 90s, Gls, Ast, G_plus_A, xG, xAG, npxG, PrgC, PrgP, PrgR
        ("P", "A", "FW", 24, 900, 10.0, 5, 2, 7, 4.5, 2.0, 4.0, 30, 20, 40),
        ("P", "B", "FW,MF", 25, 600, 6.7, 3, 1, 4, 2.5, 1.0, 2.2, 18, 12, 25),
        ("Q", "A", "DF", 30, 2000, 22.2, 1, 0, 1, 0.8, 0.4, 0.8, 10, 90, 5),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "player", "team", "pos", "age", "Min", "90s",
            "Gls", "Ast", "G_plus_A", "xG", "xAG", "npxG", "PrgC", "PrgP", "PrgR",
        ],
    )


def test_aggregate_removes_duplicates() -> None:
    """回归：赛季中转会的球员必须合并为一行。"""
    out = cleaning.aggregate_player_season(_mini_frame())
    assert len(out) == 2, "应合并为 2 名唯一球员"
    assert not out["player_name"].duplicated().any()


def test_midseason_transfer_metrics() -> None:
    """合并规则：计数指标求和、age 取最大、team 标记 MULTI、位置取并集。"""
    out = cleaning.aggregate_player_season(_mini_frame())
    p = out[out["player_name"] == "P"].iloc[0]
    assert p["Min"] == 1500, "分钟应求和"
    assert p["Gls"] == 8, "进球应求和"
    assert p["Ast"] == 3
    assert p["age"] == 25, "age 应取较大值"
    assert p["n_source_rows"] == 2
    assert bool(p["transferred_midseason"]) is True
    assert p["team"].startswith("MULTI:")
    assert set(p["positions_all"].split(",")) == {"FW", "MF"}

    q = out[out["player_name"] == "Q"].iloc[0]
    assert bool(q["transferred_midseason"]) is False
    assert q["team"] == "A"


def test_primary_position_uses_max_minutes() -> None:
    """跨队球员的主位置由**出场更多的那个 stint** 决定。

    迷你表中 P 的第一段 900 分钟为 'FW'，第二段 600 分钟为 'FW,MF'，
    故主位置应为 Forward（两段一致）；另造一个冲突样例验证分钟优先。
    """
    df = pd.DataFrame(
        {
            "player": ["R", "R"],
            "team": ["A", "B"],
            "pos": ["MF", "DF"],
            "age": [27, 27],
            "Min": [1500, 100],  # 第一段出场远多 -> 主位置应为 Midfielder
            "90s": [16.7, 1.1],
        }
    )
    out = cleaning.aggregate_player_season(df)
    assert out.iloc[0]["primary_position"] == "Midfielder"
    assert set(out.iloc[0]["positions_all"].split(",")) == {"MF", "DF"}


def test_aggregate_rejects_missing_age() -> None:
    df = _mini_frame()
    df.loc[0, "age"] = None
    with pytest.raises(cleaning.CleaningError, match="age"):
        cleaning.aggregate_player_season(df)


# --------------------------------------------------------------------------------------
# per-90
# --------------------------------------------------------------------------------------

def test_per90_computed_from_totals() -> None:
    """per-90 必须用合并后的总计数/总 90s 计算。"""
    out = cleaning.add_per90(cleaning.aggregate_player_season(_mini_frame()))
    p = out[out["player_name"] == "P"].iloc[0]
    assert p["Gls_per90"] == pytest.approx(8 / 16.7)
    assert p["GA_per90"] == pytest.approx((8 + 3) / 16.7)


def test_per90_is_nan_not_zero_for_no_minutes() -> None:
    """回归：0 分钟出场时 per-90 必须是 NaN，而不是 0。

    填 0 会伪装成"表现差"，真相是"没有足够样本可评价"。
    """
    df = pd.DataFrame(
        {"player": ["Z"], "team": ["A"], "pos": ["DF"], "age": [22],
         "Min": [0], "90s": [0.0], "Gls": [0], "Ast": [0], "G_plus_A": [0],
         "xG": [0], "xAG": [0], "npxG": [0], "PrgC": [0], "PrgP": [0], "PrgR": [0]}
    )
    out = cleaning.add_per90(cleaning.aggregate_player_season(df))
    assert pd.isna(out.iloc[0]["Gls_per90"])


# --------------------------------------------------------------------------------------
# 低样本与候选池
# --------------------------------------------------------------------------------------

def test_low_sample_marked_not_dropped() -> None:
    """回归：低样本球员必须**保留**并标记，而不是被静默删除。"""
    df = pd.DataFrame({"Min": [10, 449, 450, 3000]})
    out = cleaning.mark_low_sample(df, threshold=450)
    assert len(out) == 4, "不得删除任何行"
    assert out["is_low_sample"].tolist() == [True, True, False, False]


def test_candidate_pool_threshold_is_450() -> None:
    """回归：候选池门槛为 450 分钟（旧项目用 90，过松）。"""
    assert config.MIN_MINUTES_CANDIDATE == 450
    df = pd.DataFrame(
        {
            "player_name": ["a", "b", "c"],
            "primary_position": ["Defender"] * 3,
            "Min": [89, 90, 450],
        }
    )
    pool = cleaning.build_candidate_pool(df)
    assert pool["player_name"].tolist() == ["c"]


# --------------------------------------------------------------------------------------
# 合同与国米识别
# --------------------------------------------------------------------------------------

def test_contract_attached_and_missing_flagged() -> None:
    """回归：合同必须真正挂上，且未匹配者用 has_contract_info 显式标记。"""
    players = pd.DataFrame(
        {
            "player_name": ["p1", "p2"],
            "Min": [1000, 1000],
        }
    )
    contracts = pd.DataFrame(
        {
            "player_name": ["p1"],
            "season": ["2022-2023"],
            "contract_years_left": [3.0],
            "is_loan": [False],
            "contract_raw": [3],
        }
    )
    out = cleaning.attach_contracts(players, contracts)
    r1 = out[out["player_name"] == "p1"].iloc[0]
    r2 = out[out["player_name"] == "p2"].iloc[0]
    assert r1["contract_years_left"] == 3.0
    assert bool(r1["has_contract_info"]) is True
    assert pd.isna(r2["contract_years_left"])
    assert bool(r2["has_contract_info"]) is False
    assert bool(r2["is_loan"]) is False, "未匹配者不应被误判为租借"


def test_contract_requires_columns() -> None:
    with pytest.raises(cleaning.CleaningError, match="contracts 缺少列"):
        cleaning.attach_contracts(
            pd.DataFrame({"player_name": ["p"]}),
            pd.DataFrame({"player_name": ["p"]}),
        )


@pytest.mark.parametrize(
    "team,expected",
    [
        ("Inter", True),
        ("Inter", True),
        ("MULTI:Inter|Juventus", True),
        ("Internazionale", False),   # 不是 FBref 的写法
        ("Inter Milan", False),      # 不是 FBref 的写法
        ("Inter Turku", False),      # 子串匹配会误伤
        ("Juventus", False),
        (None, False),
    ],
)
def test_inter_exact_match(team, expected) -> None:
    """回归：识别国米必须用精确匹配，不能用 str.contains('Inter')。

    子串匹配会把 'Inter Turku'、'Internazionale' 等误判为国米。
    """
    out = cleaning.mark_inter(pd.DataFrame({"team": [team]}))
    assert bool(out.iloc[0]["is_inter"]) is expected


# --------------------------------------------------------------------------------------
# 端到端（真实数据）
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("season", config.SEASONS)
def test_end_to_end_players_table(season: str) -> None:
    """端到端：真实数据能构建出通过 schema 校验的球员表。"""
    from data import schemas

    std = loaders.load_fbref_table(
        config.season_files(season).standard, "standard", season
    )
    con = loaders.load_contracts(season)
    lab = loaders.load_departure_labels(season)
    players = cleaning.build_players_table(std, con, lab, season)

    schemas.validate(players, schemas.PLAYERS_SCHEMA, f"players[{season}]")
    assert not players["player_name"].duplicated().any()

    expected_n = {"2022-2023": 577, "2023-2024": 590}[season]
    assert len(players) == expected_n

    inter = players[players["is_inter"]]
    assert len(inter) == {"2022-2023": 25, "2023-2024": 27}[season]
    assert inter["departed"].notna().all(), "国米球员必须都有标签"


@pytest.mark.parametrize(
    "season,n_departed,n_stayed",
    [("2022-2023", 12, 13), ("2023-2024", 7, 20)],
)
def test_label_distribution_is_known(season, n_departed, n_stayed) -> None:
    """回归：标签分布必须与审计记录一致（这是 A 类回归基线）。"""
    lab = loaders.load_departure_labels(season)
    assert int(lab["departed"].sum()) == n_departed
    assert int((1 - lab["departed"]).sum()) == n_stayed


def test_inter_position_distribution_2022_2023() -> None:
    """国米 2022-23 的位置分布（审计记录值）。

    注意 Valentin Carboni 的 pos 是 'MF,DF'：主位置为 Midfielder。
    旧项目因 if-elif 顺序把它归为 Midfielder —— 结果偶然一致，
    但推导路径不同（旧项目丢弃了 'DF' 这一第二位置）。
    """
    std = loaders.load_fbref_table(
        config.season_files("2022-2023").standard, "standard", "2022-2023"
    )
    con = loaders.load_contracts("2022-2023")
    lab = loaders.load_departure_labels("2022-2023")
    players = cleaning.build_players_table(std, con, lab, "2022-2023")
    inter = players[players["is_inter"]]
    dist = inter["primary_position"].value_counts().to_dict()
    assert dist == {
        "Defender": 11, "Midfielder": 7, "Forward": 4, "Goalkeeper": 3
    }
