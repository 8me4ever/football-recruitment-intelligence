#!/usr/bin/env python3
"""Build a descriptive pre-Gate C2 group snapshot from the frozen C1/C2 ledgers."""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "csl" / "decision_snapshot_2026-09-27"
USAGE = SNAPSHOT / "c2_player_usage_baseline_2026_guoan.csv"
AGES = SNAPSHOT / "c2_age_structure_2026_guoan.csv"
AUTHORITATIVE = SNAPSHOT / "user_authoritative_roster_2026-09-30.csv"
OUTPUT = SNAPSHOT / "c2_lite_group_signals_2026_guoan.csv"
REPORT = ROOT / "reports" / "analysis" / "C2_LITE_2026-09-27.md"
GROUPS = [("Goalkeeper", "门将"), ("Defender", "后卫"),
          ("Midfielder", "中场"), ("Forward", "前锋")]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def number(row: dict[str, str], column: str) -> int:
    return int(row[column] or 0)


def main() -> None:
    usage = read_csv(USAGE)
    ages = read_csv(AGES)
    authoritative = read_csv(AUTHORITATIVE)
    listed_group_by_name = {row["player_name_zh"]: row["user_listed_group"] for row in authoritative}
    discussion_names = {row["player_name_zh"] for row in authoritative if row["c2_discussion_member"] == "true"}
    members = [row for row in usage if row["decision_date_first_team_member"] == "true" and row["player_name_zh"] in discussion_names]
    ages_by_key = {row["player_key"]: row for row in ages}
    if len(members) != 32 or len(ages_by_key) != 39:
        raise SystemExit("Expected 32 C2 discussion members within the 39-person formal roster")
    if not {row["player_key"] for row in members} <= set(ages_by_key):
        raise SystemExit("C2 discussion member missing from age cohort")
    cohort_ages = [int(ages_by_key[row["player_key"]]["age_years_on_decision_date"])
                   for row in members]
    positive_sample_count = sum(number(row, "all_competitions_positive_minute_matches") > 0
                                for row in members)

    output_rows = []
    for group, label in GROUPS:
        group_members = [row for row in members if listed_group_by_name[row["player_name_zh"]] == group]
        minutes = sorted((number(row, "all_competitions_displayed_minutes_sum")
                          for row in group_members), reverse=True)
        total = sum(minutes)
        top_two = sum(minutes[:2])
        output_rows.append({
            "decision_date": "2026-09-27",
            "analysis_status": "pre_gate_descriptive_only",
            "population_scope": "user_authoritative_c2_discussion_32",
            "user_listed_group": group,
            "position_group_zh": label,
            "current_members": len(group_members),
            "members_with_positive_minute_sample": sum(number(row, "all_competitions_positive_minute_matches") > 0 for row in group_members),
            "members_without_positive_minute_sample": sum(number(row, "all_competitions_positive_minute_matches") == 0 for row in group_members),
            "members_aged_21_or_under": sum(int(ages_by_key[row["player_key"]]["age_years_on_decision_date"]) <= 21 for row in group_members),
            "members_aged_30_or_over": sum(int(ages_by_key[row["player_key"]]["age_years_on_decision_date"]) >= 30 for row in group_members),
            "csl_displayed_minutes_current_members": sum(number(row, "csl_displayed_minutes_sum") for row in group_members),
            "acl_displayed_minutes_current_members": sum(number(row, "acl_displayed_minutes_sum") for row in group_members),
            "all_competitions_displayed_minutes_current_members": total,
            "top_two_current_members_displayed_minutes": top_two,
            "top_two_share_pct": round(top_two / total * 100, 1) if total else "",
        })

    if sum(row["current_members"] for row in output_rows) != 32:
        raise SystemExit("Nominal groups do not partition the 32-person discussion cohort")
    by_group = {row["user_listed_group"]: row for row in output_rows}
    columns = list(output_rows[0])
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output_rows)

    table = "\n".join(
        f"| {row['position_group_zh']} | {row['current_members']} | "
        f"{row['members_with_positive_minute_sample']} | {row['members_without_positive_minute_sample']} | "
        f"{row['members_aged_21_or_under']} | {row['members_aged_30_or_over']} | "
        f"{row['all_competitions_displayed_minutes_current_members']:,} | {row['top_two_share_pct']:.1f}% |"
        for row in output_rows
    )
    report = f"""# C2 简版阵容结构与使用信号 — 2026-09-27

**状态：预 Gate 描述性分析。** 决策日期冻结在 2026-09-27；用户直接指定的正式名单有 39 人，其中 7 名 U20 本赛季未出场球员按用户要求不计入讨论，本报告使用其余 32 人作讨论分母，以该日期范围内已采集的 27 场比赛为使用量样本。C1 仍为 `IN PROGRESS`，本报告不生成补强优先级或候选名单。

全队平均年龄 **{mean(cohort_ages):.1f} 岁**、中位数 **{median(cohort_ages):g} 岁**；{positive_sample_count} 人有正分钟样本，{len(members) - positive_sample_count} 人没有正分钟样本。

## 当前能回答什么

| 用户名单组别 | 讨论人数 | 有正分钟样本 | 无正分钟样本 | ≤21岁 | ≥30岁 | 讨论成员赛季分钟 | 前两人分钟占比 |
|---|---:|---:|---:|---:|---:|---:|---:|
{table}

年龄以决策日完整周岁计算。位置组采用用户这次正式名单的分组；比赛统计中的名义位置和逐场角色保持独立。分钟是 32 名讨论成员在已采集 2026 国安比赛中的实际显示分钟，包含中超和亚冠精英赛，不按赛事等级加权；外租、转出和下放者的历史贡献仍留在 45 人赛季使用量基线，7 名 U20 仍留在 39 人正式名册。前两人分钟占比 = 同一名单组内讨论成员分钟最高两人的分钟和 ÷ 该组讨论成员总分钟。它表示使用集中度，不表示球员质量、替补能力或战术角色。无正分钟样本只表示现有统计行没有正分钟，不能解释为未入选、不可用或零表现。

## 下一步需要查证的信号

1. **门将替代比赛证据：** {by_group['Goalkeeper']['current_members']} 名门将讨论成员中仅 {by_group['Goalkeeper']['members_with_positive_minute_sample']} 人有正分钟样本，该成员占门将组已观察分钟的 {by_group['Goalkeeper']['top_two_share_pct']:.1f}%。这使替代能力无法从现有比赛数据评估；需要比赛日名单、训练/伤病信息及其他比赛证据。
2. **前锋组使用集中度：** {by_group['Forward']['current_members']} 名前锋名单组讨论成员均有正分钟样本，但张玉宁与法比奥的分钟合计占该组 {by_group['Forward']['top_two_share_pct']:.1f}%。恩科洛洛的夏窗中超撤销报名与阿科洛的亚冠专属身份仍须在赛事可用性层分别处理；下一步应按实际功能角色和可替代性拆分。
3. **中场成员解释：** {by_group['Midfielder']['current_members']} 名中场名单组讨论成员中有 {by_group['Midfielder']['members_without_positive_minute_sample']} 人无正分钟样本、{by_group['Midfielder']['members_aged_30_or_over']} 人已满 30 岁。名单组内可能包含不同功能角色；应先建立比赛级角色和可用性证据，再判断是否存在特定功能缺口。

后卫组有 {by_group['Defender']['current_members']} 名讨论成员，其中 {by_group['Defender']['members_with_positive_minute_sample']} 人有正分钟样本。用户直接提供的实际使用备注指出：邓捷夫近期主要踢左边前卫、柏杨报名为中后卫而实际踢左边后卫；林良铭在正式名单列于前锋，但实际踢左边前卫。这些是用户报告的当前角色，不当作逐场已观察角色。吴少聪赛季报销且本赛季 0 出场；何宇鹏的赛季报销记载来自用户此前对账。

## 暂不能下的结论

- 现有 406 条球员比赛行只有 22 条有比赛级角色证据；注册名义位置、球员简介位置和实际比赛角色仍分层记录。无法据此给出边后卫、中后卫、后腰等精确功能角色的深度矩阵。
- 当前没有完成位置调整后的表现比较、2025→2026 趋势判断、主力缺席时的可信替代分析及完整比赛日名单。用户直接指定的阵容无需外部交叉验证；未提供的准确变动日期仍留空。简版信号不能升级为正式 recruitment need，C2 Gate 不申请通过。
- 资料截至冻结决策日；2026-09-27 之后的比赛如需使用，应建立新的数据版本，不回填本快照。

## 复现与来源

- 脚本：[`build_c2_lite.py`](../../scripts/build_c2_lite.py)。
- 机器可读汇总：[`c2_lite_group_signals_2026_guoan.csv`](../../data/csl/decision_snapshot_2026-09-27/c2_lite_group_signals_2026_guoan.csv)。
- 输入：[`user_authoritative_roster_2026-09-30.csv`](../../data/csl/decision_snapshot_2026-09-27/user_authoritative_roster_2026-09-30.csv)、[`c2_player_usage_baseline_2026_guoan.csv`](../../data/csl/decision_snapshot_2026-09-27/c2_player_usage_baseline_2026_guoan.csv)、[`c2_age_structure_2026_guoan.csv`](../../data/csl/decision_snapshot_2026-09-27/c2_age_structure_2026_guoan.csv)。来源层级及比赛证据见 [C1 决策数据层](C1_GUOAN_DECISION_LAYER_2026-09-27.md)、[C2 初始使用量基线](C2_INITIAL_USAGE_BASELINE_2026.md)及[年龄与角色证据](C2_AGE_AND_ROLE_EVIDENCE_2026-09-27.md)。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(f"Built {OUTPUT} and {REPORT}")


if __name__ == "__main__":
    main()
