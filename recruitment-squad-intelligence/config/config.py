"""
全局配置：路径与参数。

设计原则（针对旧项目的缺陷）：
- **禁止硬编码绝对路径**：项目根由本文件位置推导；原始数据位置由 config/local.yaml 或环境变量提供，
  若不存在则回退到同工作区内的归档目录。
- **禁止散落的魔法数字**：所有阈值集中于此。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------------------
# 路径
# --------------------------------------------------------------------------------------

# config/config.py -> 项目根
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw" / "serie_a"
INTERIM_DIR: Path = DATA_DIR / "interim"
PROCESSED_DIR: Path = DATA_DIR / "processed"
EXTERNAL_DIR: Path = DATA_DIR / "external"

REPORTS_DIR: Path = PROJECT_ROOT / "reports"
FIGURES_DIR: Path = REPORTS_DIR / "figures"
ANALYSIS_DIR: Path = REPORTS_DIR / "analysis"

# 同工作区内的其他位置
WORKSPACE_ROOT: Path = PROJECT_ROOT.parent
ARCHIVE_ROOT: Path = WORKSPACE_ROOT / "archive" / "msc-inter-departure-2025"

# 旧项目归档是原始 FBref CSV 的权威来源。
# 可用环境变量覆盖，避免任何硬编码假设。
_env_raw = os.environ.get("RSI_RAW_DATA_DIR")
if _env_raw:
    LEGACY_RAW_DIR: Path = Path(_env_raw)
elif (ARCHIVE_ROOT / "data excel").is_dir():
    LEGACY_RAW_DIR = ARCHIVE_ROOT / "data excel"
elif (WORKSPACE_ROOT / "final project" / "data excel").is_dir():
    LEGACY_RAW_DIR = WORKSPACE_ROOT / "final project" / "data excel"
else:  # pragma: no cover - 仅在环境异常时触发
    LEGACY_RAW_DIR = RAW_DIR


# --------------------------------------------------------------------------------------
# 数据参数
# --------------------------------------------------------------------------------------

# FBref 导出的 CSV 是三层表头：
#   row 0 -> 指标组名（Playing Time / Performance / ...）
#   row 1 -> 指标名（MP / Starts / Min / Gls / ...）
#   row 2 -> 字段名（league / season / team / player / ...）
#   row 3+ -> 数据
# 旧项目用 skiprows=2，把 row 2 当成数据读入（引入 1 行冗余表头）。
FBREF_HEADER_ROWS: int = 3

# 候选池的最小出场时间门槛（分钟）。
# 旧项目在文档中声称有 min_minutes=90，但最终管线从未实现；且 90 分钟过松。
# 450 分钟 ≈ 5 场完整比赛，是"统计量可信"的经验下限。
MIN_MINUTES_CANDIDATE: int = 450

# 低样本标记门槛：低于此值仍保留在表中，但标记 is_low_sample=True，
# 下游画像必须降级展示或拒绝输出高置信结论。
MIN_MINUTES_RELIABLE: int = 450

# 合同：CSV 中的 -1 表示租借球员，其"剩余年数"不可解释。
CONTRACT_LOAN_SENTINEL: int = -1

# 拥有**全部 8 类统计**（可做完整画像）的赛季，来自加工好的 CSV
SEASONS: tuple[str, ...] = ("2022-2023", "2023-2024")

# 仅有 **standard 一类**统计的赛季，来源是原始 HTML。
# 这些赛季可用于 standard 口径的分析（出场、进球、xG、推进等），
# 但**不可用** SCA/GCA/Tkl/Int/Clr/Saves 等跨类别指标 —— 下游必须显式处理这一点。
STANDARD_ONLY_SEASONS: tuple[str, ...] = ("2024-2025",)

ALL_SEASONS: tuple[str, ...] = SEASONS + STANDARD_ONLY_SEASONS

# 位置分组：FBref 的 pos 可能是多值（如 "FW,MF"、"MF,DF"）。
# 实测确认：**逗号顺序本身表达主次**（`FW,MF` 与 `MF,FW` 是两个不同取值），
# 因此主位置取 FBref 列出的第一个位置，而不是人为规定位置优先级。
POSITION_LABELS: dict[str, str] = {
    "GK": "Goalkeeper",
    "DF": "Defender",
    "MF": "Midfielder",
    "FW": "Forward",
}

# 统计类别 -> 文件名模板。键为内部类别名。
STAT_CATEGORIES: dict[str, str] = {
    "standard": "ITA_SerieA_player_standard_stats_{season_tag}.csv",
    "goal": "ITA_SerieA_player_goal_stats_{season_tag}.csv",
    "shooting": "ITA_SerieA_player_shooting_stats_{season_tag}.csv",
    "passing": "ITA_SerieA_player_passing_stats_{season_tag}.csv",
    "possession": "ITA_SerieA_player_possession_stats_{season_tag}.csv",
    "defensive": "ITA_SerieA_player_defensive_stats_{season_tag}.csv",
    "goalkeeper": "ITA_SerieA_player_goalkeeper_stats_{season_tag}.csv",
    "goalkeeper_advance": "ITA_SerieA_player_goalkeeper_advance_stats_{season_tag}.csv",
}

# 赛季 -> FBref 的 season tag（文件名中用）
SEASON_TAGS: dict[str, str] = {
    "2022-2023": "2022_2023",
    "2023-2024": "2023_2024",
}


@dataclass(frozen=True)
class SeasonFiles:
    """一个赛季涉及的全部源文件路径。"""

    season: str
    stats_dir: Path
    standard: Path
    goal: Path
    shooting: Path
    passing: Path
    possession: Path
    defensive: Path
    goalkeeper: Path
    goalkeeper_advance: Path
    contract: Path
    labels: Path | None
    label_key: str


INTER_SQUAD_LABELS: dict[str, tuple[Path, str]] = {
    # 旧项目里标签文件有两处，以 data excel 下的为准（根目录那份是副本）
    "2022-2023": (LEGACY_RAW_DIR / "2022-2023" / "Inter_Players_Departure_Labels.csv", "Player_Name"),
    "2023-2024": (LEGACY_RAW_DIR / "2023-2024" / "Inter_departured_2023_2024.csv", "Name"),
}

CONTRACT_FILES: dict[str, Path] = {
    "2022-2023": LEGACY_RAW_DIR / "2022-2023" / "Contract_2022_2023.csv",
    "2023-2024": LEGACY_RAW_DIR / "2023-2024" / "Contract_2023_2024.csv",
}

# 目标俱乐部在 FBref 数据中的球队名（精确匹配，不做子串匹配）
INTER_TEAM_NAME: str = "Inter"

# 归档中保留的 FBref 原始 HTML 页面（注意文件名含空格："ITA-Serie A"）。
# 2024-2025 只有 HTML、没有对应的加工 CSV，需由 loader 解析。
LEGACY_HTML_DIR: Path = ARCHIVE_ROOT / "data"
LEGACY_HTML_FILES: dict[str, str] = {
    "2022-2023": "players_ITA-Serie A_2223_standard.html",
    "2023-2024": "players_ITA-Serie A_2324_standard.html",
    "2024-2025": "players_ITA-Serie A_2425_standard.html",
}

# HTML 中的 season tag（FBref 的 2425 形式）
HTML_SEASON_TAGS: dict[str, str] = {
    "2022-2023": "2223",
    "2023-2024": "2324",
    "2024-2025": "2425",
}

# 2024-2025 的标签与合同：归档中**没有**对应文件。
# 因此该赛季只能用于画像与候选池，不能用于离队风险建模。
INTER_SQUAD_LABELS["2024-2025"] = (
    LEGACY_RAW_DIR / "2024-2025" / "Inter_departured_2024_2025.csv",
    "Name",
)
CONTRACT_FILES["2024-2025"] = LEGACY_RAW_DIR / "2024-2025" / "Contract_2024_2025.csv"


def season_files(season: str) -> SeasonFiles:
    """返回某赛季的全部源文件路径，并断言必需文件存在。"""
    if season not in SEASON_TAGS:
        raise KeyError(f"未知赛季: {season}")
    tag = SEASON_TAGS[season]
    d = LEGACY_RAW_DIR / season
    stats_dir = d

    def p(cat: str) -> Path:
        return stats_dir / STAT_CATEGORIES[cat].format(season_tag=tag)

    lab_path, lab_key = INTER_SQUAD_LABELS[season]
    return SeasonFiles(
        season=season,
        stats_dir=stats_dir,
        standard=p("standard"),
        goal=p("goal"),
        shooting=p("shooting"),
        passing=p("passing"),
        possession=p("possession"),
        defensive=p("defensive"),
        goalkeeper=p("goalkeeper"),
        goalkeeper_advance=p("goalkeeper_advance"),
        contract=CONTRACT_FILES[season],
        labels=lab_path,
        label_key=lab_key,
    )


def ensure_output_dirs() -> None:
    for d in (RAW_DIR, INTERIM_DIR, PROCESSED_DIR, EXTERNAL_DIR, FIGURES_DIR, ANALYSIS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def LEGACY_HTML_SEASONS_OR_SKIP() -> tuple[str, ...]:
    """实际存在于磁盘上的 HTML 赛季（用于在测试/脚本中跳过缺失文件）。"""
    return tuple(
        s for s, f in LEGACY_HTML_FILES.items() if (LEGACY_HTML_DIR / f).exists()
    )


__all__ = [
    "PROJECT_ROOT", "DATA_DIR", "RAW_DIR", "INTERIM_DIR", "PROCESSED_DIR", "EXTERNAL_DIR",
    "REPORTS_DIR", "FIGURES_DIR", "ANALYSIS_DIR", "WORKSPACE_ROOT", "ARCHIVE_ROOT",
    "LEGACY_RAW_DIR", "FBREF_HEADER_ROWS", "MIN_MINUTES_CANDIDATE", "MIN_MINUTES_RELIABLE",
    "CONTRACT_LOAN_SENTINEL", "SEASONS", "STANDARD_ONLY_SEASONS", "ALL_SEASONS",
    "POSITION_LABELS",
    "STAT_CATEGORIES", "SEASON_TAGS", "SeasonFiles", "season_files", "ensure_output_dirs",
    "INTER_TEAM_NAME", "LEGACY_HTML_DIR", "LEGACY_HTML_FILES", "HTML_SEASON_TAGS",
    "LEGACY_HTML_SEASONS_OR_SKIP",
]
