"""
回归测试：FBref 原始 HTML 解析（2024-2025 赛季）。

对应关系：
- test_html_requires_comment_stripping   <- FBref 把球员表放在 HTML 注释里，
                                             不剥离注释只能拿到 2 张球队表（旧项目未使用这些文件）
- test_html_standard_columns             <- 解析后的列名必须与 CSV 口径一致
- test_html_has_inter_squad              <- 能识别国米 2024-25 阵容
- test_html_missing_categories_documented <- 该赛季只有 standard 一类，
                                             必须在配置中显式声明缺失
"""
from __future__ import annotations

import pytest

from config import config
from data import loaders, schemas


def test_html_file_registered() -> None:
    assert "2024-2025" in config.LEGACY_HTML_FILES
    assert "2024-2025" in config.LEGACY_HTML_SEASONS_OR_SKIP()


def test_html_comment_stripping_is_required() -> None:
    """回归：FBref 把球员级表放在 HTML 注释内。

    不剥离 `<!--` 时 pd.read_html 只能看到 2 张球队级表（20 行）；
    剥离后才能看到第 3 张 634 行的球员表。这个坑必须被测试固化。
    """
    from io import StringIO

    import pandas as pd

    path = config.LEGACY_HTML_DIR / config.LEGACY_HTML_FILES["2024-2025"]
    raw = path.read_text(encoding="utf-8", errors="replace")

    as_is = pd.read_html(StringIO(raw))
    stripped = pd.read_html(StringIO(raw.replace("<!--", "").replace("-->", "")))
    assert len(stripped) > len(as_is), "剥离注释后应解析出更多表格"

    # 原始解析不出球员级表（行数 > 100）
    assert max(t.shape[0] for t in as_is) < 100, "未剥离注释时不应出现球员级大表"
    assert max(t.shape[0] for t in stripped) > 500, "剥离注释后应出现球员级大表"


def test_html_standard_columns() -> None:
    """解析后的列必须与 CSV 口径一致（含 born，且不含单独的 GA）。"""
    df = loaders.load_fbref_html_standard("2024-2025")
    for c in schemas.STANDARD_COLUMNS:
        assert c in df.columns, f"缺少列 {c}"
    assert "GA" not in df.columns, "数据中不存在单独的 GA 列（应为 G_plus_A）"
    assert df["Min"].notna().all()
    assert df["age"].between(15, 45).all()


def test_html_row_and_player_counts() -> None:
    df = loaders.load_fbref_html_standard("2024-2025")
    assert len(df) == 634, f"2024-25 应有 634 行，实际 {len(df)}"
    assert df["player"].nunique() == 599
    assert df["team"].nunique() == 20
    assert (df["season"] == "2425").all()


def test_html_has_inter_squad() -> None:
    df = loaders.load_fbref_html_standard("2024-2025")
    inter = df[df["team"] == config.INTER_TEAM_NAME]
    assert len(inter) == 26, f"2024-25 国米应有 26 行，实际 {len(inter)}"
    assert "Lautaro Martínez" in set(inter["player"])
    assert "Nicolò Barella" in set(inter["player"])


def test_html_only_standard_is_documented() -> None:
    """回归：该赛季只有 standard 一类，必须在配置里显式声明。

    否则下游会以为能拿到 SCA/GCA/Tkl 等指标，产生静默的缺失值。
    """
    assert "2024-2025" in config.STANDARD_ONLY_SEASONS
    assert "2024-2025" not in config.SEASONS, "不应把仅 standard 的赛季混入完整赛季列表"
    assert set(config.ALL_SEASONS) == set(config.SEASONS) | set(config.STANDARD_ONLY_SEASONS)


def test_html_season_has_no_labels_or_contracts() -> None:
    """回归：2024-25 在归档中没有标签与合同文件，必须被显式识别为缺失。"""
    assert not config.CONTRACT_FILES["2024-2025"].exists()
    sf = config.season_files("2024-2025") if "2024-2025" in config.SEASON_TAGS else None
    # SEASON_TAGS 只覆盖 CSV 赛季，故此处直接检查路径
    assert "2024-2025" not in config.SEASON_TAGS
    assert sf is None


def test_html_unknown_season_raises() -> None:
    with pytest.raises(loaders.DataLoadError):
        loaders.load_fbref_html_standard("2099-2100")
