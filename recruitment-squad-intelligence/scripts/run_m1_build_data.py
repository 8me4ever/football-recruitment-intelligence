"""
M1 — 构建干净数据层。

输入：归档中的原始 FBref CSV（通过 config.LEGACY_RAW_DIR 定位，无硬编码路径）
输出：data/processed/ 下的成品表 + reports/analysis/ 下的数据质量报告

运行：
    python scripts/run_m1_build_data.py
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import config                    # noqa: E402
from data import cleaning, loaders, schemas  # noqa: E402


def hr(title: str = "", width: int = 92) -> None:
    if title:
        print(f"\n{title}")
        print("=" * width)
    else:
        print("-" * width)


def main() -> int:
    config.ensure_output_dirs()
    started = datetime.now(timezone.utc)
    print("=" * 92)
    print("M1 — 构建干净数据层")
    print("=" * 92)
    print(f"原始数据目录: {config.LEGACY_RAW_DIR}")
    print(f"输出目录    : {config.PROCESSED_DIR}")

    quality: dict = {
        "generated_at_utc": started.isoformat(),
        "raw_data_dir": str(config.LEGACY_RAW_DIR),
        "seasons": {},
        "known_data_gaps": [
            "无转会费 / 球员估值 —— 因此不做性价比与预算分析",
            "无薪资数据 —— 因此不做薪资结构分析",
            "无伤病历史 —— 因此不做可用性风险",
            "无位置坐标（x/y）数据 —— 角色刻画基于行为统计而非触球热区",
            "候选池仅限 Serie A —— 无法推荐其他联赛球员",
            "合同信息仅覆盖国米球员（每赛季约 25-27 人），联赛其他球员无合同数据",
        ],
    }

    tables: dict[str, pd.DataFrame] = {}

    for season in config.SEASONS:
        hr(f"赛季 {season}（完整 8 类统计，来自 CSV）")

        # ---------- 加载 ----------
        standard = loaders.load_fbref_table(
            config.season_files(season).standard, "standard", season
        )
        contracts = loaders.load_contracts(season)
        try:
            labels = loaders.load_departure_labels(season)
        except loaders.DataLoadError as e:
            print(f"  [警告] 标签加载失败，将继续但无标签: {e}")
            labels = None

        n_rows_raw = len(standard)
        n_players_raw = standard["player"].nunique()
        print(f"  原始: 行数={n_rows_raw}  唯一球员={n_players_raw}  球队={standard['team'].nunique()}")

        # ---------- 清洗 ----------
        players = cleaning.build_players_table(standard, contracts, labels, season)
        print(f"  清洗后: 唯一球员={len(players)}  "
              f"赛季中转会={int(players['transferred_midseason'].sum())} 人  "
              f"低样本(Min<{config.MIN_MINUTES_RELIABLE})={int(players['is_low_sample'].sum())} 人")
        print(f"  位置分布: {players['primary_position'].value_counts().to_dict()}")
        print(f"  多位置球员: {int((players['n_positions'] > 1).sum())} 人  "
              f"（旧项目丢弃了这一信息）")
        print(f"  合同信息覆盖: {int(players['has_contract_info'].sum())}/{len(players)}  "
              f"（租借 {int(players['is_loan'].sum())} 人）")

        # ---------- Schema 校验 ----------
        schemas.validate(players, schemas.PLAYERS_SCHEMA, f"players[{season}]")
        print("  [OK] players schema 校验通过")

        # ---------- 国米阵容 ----------
        inter = players[players["is_inter"]].copy()
        if labels is not None:
            n_labelled = int(inter["has_departure_label"].sum())
            if n_labelled != len(inter):
                raise AssertionError(
                    f"{season}: 国米球员 {len(inter)} 人，但仅 {n_labelled} 人有标签"
                )
            inter["departed"] = inter["departed"].astype(int)
            n_dep, n_stay = int(inter["departed"].sum()), int((1 - inter["departed"]).sum())
            print(f"  国米阵容: {len(inter)} 人（离队 {n_dep} / 留队 {n_stay}）")
            print(f"    按位置: {inter.groupby('primary_position')['departed'].agg(['count','sum']).to_dict('index')}")
        else:
            n_dep = n_stay = None

        # ---------- 候选池 ----------
        pool = cleaning.build_candidate_pool(players)
        print(f"  候选池 (Min>={config.MIN_MINUTES_CANDIDATE}): {len(pool)} 人")
        schemas.validate(pool, schemas.PLAYERS_SCHEMA, f"candidate_pool[{season}]")

        # ---------- 落盘 ----------
        tag = season.replace("-", "_")
        paths = {
            "players": config.PROCESSED_DIR / f"players_{tag}.csv",
            "inter_squad": config.PROCESSED_DIR / f"inter_squad_{tag}.csv",
            "candidate_pool": config.PROCESSED_DIR / f"candidate_pool_{tag}.csv",
            "contracts": config.PROCESSED_DIR / f"contracts_{tag}.csv",
        }
        players.to_csv(paths["players"], index=False, encoding="utf-8-sig")
        inter.to_csv(paths["inter_squad"], index=False, encoding="utf-8-sig")
        pool.to_csv(paths["candidate_pool"], index=False, encoding="utf-8-sig")
        contracts.to_csv(paths["contracts"], index=False, encoding="utf-8-sig")
        for name, p in paths.items():
            print(f"  已写出 {name}: {p.name} ({p.stat().st_size:,} bytes)")

        tables[season] = players
        quality["seasons"][season] = {
            "raw_rows": n_rows_raw,
            "raw_unique_players": n_players_raw,
            "raw_teams": int(standard["team"].nunique()),
            "players_after_cleaning": len(players),
            "midseason_transfers_merged": int(players["transferred_midseason"].sum()),
            "multi_position_players": int((players["n_positions"] > 1).sum()),
            "low_sample_players": int(players["is_low_sample"].sum()),
            "position_distribution": {
                k: int(v) for k, v in players["primary_position"].value_counts().items()
            },
            "contract_coverage": {
                "with_info": int(players["has_contract_info"].sum()),
                "total": len(players),
                "loans": int(players["is_loan"].sum()),
            },
            "inter_squad": {
                "n_players": len(inter),
                "departed": n_dep,
                "stayed": n_stay,
                "by_position": {
                    pos: {
                        "n": int(g.shape[0]),
                        "departed": int(g["departed"].sum()) if "departed" in g else None,
                    }
                    for pos, g in inter.groupby("primary_position")
                },
                "low_sample_players": inter.loc[
                    inter["is_low_sample"], ["player_name", "Min"]
                ].to_dict("records"),
            },
            "candidate_pool_size": len(pool),
        }

    # ---------------- 2024-2025：仅 standard 类，来自原始 HTML ----------------
    for season in config.STANDARD_ONLY_SEASONS:
        hr(f"赛季 {season}（仅 standard 类，来自原始 HTML）")
        try:
            standard = loaders.load_fbref_html_standard(season)
        except loaders.DataLoadError as e:
            print(f"  [跳过] HTML 解析失败: {e}")
            continue

        print(f"  解析: 行数={len(standard)}  唯一球员={standard['player'].nunique()}  "
              f"球队={standard['team'].nunique()}")

        # 该赛季没有合同文件：用一张空合同表（全部 has_contract_info=False）
        contracts = pd.DataFrame(
            columns=["player_name", "season", "contract_years_left", "is_loan", "contract_raw"]
        )
        # 该赛季没有离队标签文件（归档中不存在）
        labels = None

        players = cleaning.build_players_table(standard, contracts, labels, season)
        schemas.validate(players, schemas.PLAYERS_SCHEMA, f"players[{season}]")
        print(f"  清洗后: 唯一球员={len(players)}  "
              f"赛季中转会={int(players['transferred_midseason'].sum())} 人  "
              f"低样本={int(players['is_low_sample'].sum())} 人")
        print(f"  位置分布: {players['primary_position'].value_counts().to_dict()}")

        inter = players[players["is_inter"]].copy()
        print(f"  国米阵容: {len(inter)} 人（该赛季无离队标签，故仅用于画像）")

        pool = cleaning.build_candidate_pool(players)
        print(f"  候选池 (Min>={config.MIN_MINUTES_CANDIDATE}): {len(pool)} 人")

        tag = season.replace("-", "_")
        players.to_csv(config.PROCESSED_DIR / f"players_{tag}.csv", index=False, encoding="utf-8-sig")
        inter.to_csv(config.PROCESSED_DIR / f"inter_squad_{tag}.csv", index=False, encoding="utf-8-sig")
        pool.to_csv(config.PROCESSED_DIR / f"candidate_pool_{tag}.csv", index=False, encoding="utf-8-sig")
        print(f"  已写出 players/inter_squad/candidate_pool_{tag}.csv")

        tables[season] = players
        quality["seasons"][season] = {
            "source": "raw_html",
            "stat_categories_available": ["standard"],
            "stat_categories_missing": [
                c for c in config.STAT_CATEGORIES if c != "standard"
            ],
            "has_departure_labels": False,
            "has_contract_data": False,
            "raw_rows": len(standard),
            "raw_unique_players": int(standard["player"].nunique()),
            "raw_teams": int(standard["team"].nunique()),
            "players_after_cleaning": len(players),
            "midseason_transfers_merged": int(players["transferred_midseason"].sum()),
            "multi_position_players": int((players["n_positions"] > 1).sum()),
            "low_sample_players": int(players["is_low_sample"].sum()),
            "position_distribution": {
                k: int(v) for k, v in players["primary_position"].value_counts().items()
            },
            "inter_squad": {
                "n_players": len(inter),
                "departed": None,
                "stayed": None,
                "by_position": {
                    pos: {"n": int(g.shape[0]), "departed": None}
                    for pos, g in inter.groupby("primary_position")
                },
                "low_sample_players": inter.loc[
                    inter["is_low_sample"], ["player_name", "Min"]
                ].to_dict("records"),
            },
            "candidate_pool_size": len(pool),
        }

    # ---------------- 跨赛季汇总 ----------------
    hr("跨赛季汇总")
    # 2024-2025 没有合同与标签，因此 contract_years_left / contract_raw /
    # departed 在该赛季整列为空。pandas 对"整列为 NA 的 DataFrame 拼接"有
    # 一条 FutureWarning（关于 dtype 推断）。这里显式抑制并说明原因：
    # 空列是**真实的数据缺口**，已被 has_contract_info / has_departure_label
    # 显式标记，不存在静默错误。
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="The behavior of DataFrame concatenation with empty or all-NA entries",
            category=FutureWarning,
        )
        combined = pd.concat(tables.values(), ignore_index=True)
    combined_path = config.PROCESSED_DIR / "players_all_seasons.csv"
    combined.to_csv(combined_path, index=False, encoding="utf-8-sig")
    print(f"  合并表: {len(combined)} 行 -> {combined_path.name}")

    # 重复球员检查（跨赛季正常，同赛季内应唯一）
    for season, df in tables.items():
        d = df["player_name"].duplicated().sum()
        if d:
            raise AssertionError(f"{season}: 同赛季内仍有 {d} 个重复球员名")
    print("  [OK] 每个赛季内 player_name 唯一")

    quality["combined_rows"] = len(combined)
    quality["processed_files"] = sorted(
        p.name for p in config.PROCESSED_DIR.glob("*.csv")
    )

    # ---------------- 质量报告 ----------------
    hr("数据质量报告")
    report_path = config.ANALYSIS_DIR / "M1_data_quality_report.json"
    report_path.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  JSON 报告: {report_path}")

    md_lines = [
        "# M1 数据质量报告",
        "",
        f"生成时间（UTC）: {quality['generated_at_utc']}",
        f"原始数据目录: `{quality['raw_data_dir']}`",
        "",
        "## 各赛季概况",
        "",
        "| 赛季 | 原始行 | 唯一球员 | 清洗后 | 合并中场转会 | 多位置 | 低样本 | 候选池 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for season, q in quality["seasons"].items():
        md_lines.append(
            f"| {season} | {q['raw_rows']} | {q['raw_unique_players']} | "
            f"{q['players_after_cleaning']} | {q['midseason_transfers_merged']} | "
            f"{q['multi_position_players']} | {q['low_sample_players']} | "
            f"{q['candidate_pool_size']} |"
        )
    md_lines += ["", "## 国米阵容", ""]
    for season, q in quality["seasons"].items():
        s = q["inter_squad"]
        if s["departed"] is None:
            head = (f"### {season} —— {s['n_players']} 人"
                    f"（无离队标签：归档中没有该赛季的标签文件）")
        else:
            head = (f"### {season} —— {s['n_players']} 人"
                    f"（离队 {s['departed']} / 留队 {s['stayed']}）")
        md_lines += [head, "", "| 位置 | 人数 | 离队 |", "|---|---|---|"]
        for pos, d in s["by_position"].items():
            dep = "-" if d["departed"] is None else d["departed"]
            md_lines.append(f"| {pos} | {d['n']} | {dep} |")
        if s["low_sample_players"]:
            md_lines += ["", "低样本球员（出场不足门槛，下游需降级处理）:", ""]
            for r in s["low_sample_players"]:
                md_lines.append(f"- {r['player_name']}（{int(r['Min'])} 分钟）")
        md_lines.append("")
    md_lines += ["## 已知数据缺口（不可通过现有数据弥补）", ""]
    for g in quality["known_data_gaps"]:
        md_lines.append(f"- {g}")
    md_lines += ["", "## 处理方式说明", "",
                 f"- **表头解析**：FBref 三层表头，`skiprows={config.FBREF_HEADER_ROWS}`（旧项目用 2，会读入一行幽灵表头）",
                 "- **球员去重**：赛季中转会的球员按球员名聚合，计数指标求和、age 取最大、team 记为 `MULTI:队A|队B`",
                 "- **位置解析**：保留完整位置列表（`positions_all`）；主位置取 FBref 列出的第一个位置"
                 "（实测逗号顺序本身表达主次，`FW,MF` 与 `MF,FW` 是两个不同取值）；"
                 "跨队球员的主位置取**出场时间最多的那个 stint**",
                 f"- **低样本**：`Min < {config.MIN_MINUTES_RELIABLE}` 标记为 `is_low_sample`，**标记而不删除**",
                 f"- **候选池**：`Min >= {config.MIN_MINUTES_CANDIDATE}` 且位置可解析",
                 "- **合同**：`-1` 识别为租借（`is_loan=True`），其剩余年数置空；未匹配到合同的球员 `has_contract_info=False`",
                 "- **标签**：未匹配到标签的球员 `has_departure_label=False`；无标签文件的赛季整列为空",
                 "- **2024-2025**：来源是原始 HTML（FBref 把球员表放在 HTML 注释内，须先剥离 `<!--`/`-->`）。"
                 "该赛季**只有 standard 一类统计**，缺 goal/shooting/passing/possession/defensive/goalkeeper，"
                 "且**没有标签与合同文件**，故只能用于画像与候选池，不能用于离队风险建模",
                 ]
    md_path = config.ANALYSIS_DIR / "M1_data_quality_report.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"  Markdown 报告: {md_path}")

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    print(f"\n完成，用时 {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
