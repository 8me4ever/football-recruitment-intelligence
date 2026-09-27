# C2 年龄与位置证据预分析 — 2026-09-27

**状态：** C2 预Gate描述性分析，不构成正式引援位置结论。分析人口是用户提供的 39 人决策日一线队名单；比赛出场样本不决定谁属于这 39 人。

## 年龄结构

39 人均有公开出生日期资料。按 2026-09-27 的完整周岁计算，平均年龄 **26.3 岁**，中位数 **28 岁**，范围 **17–37 岁**。

| 年龄段 | 人数 | 有正分钟样本 | 无统计行 |
|---|---:|---:|---:|
| 21岁及以下 | 11 | 4 | 7 |
| 22–24岁 | 3 | 1 | 2 |
| 25–29岁 | 14 | 12 | 2 |
| 30岁及以上 | 11 | 11 | 0 |

这份名单同时包括年轻注册成员和已有比赛贡献的年长球员。年龄本身不能说明球员表现、可用性或替代风险；无统计行仍表示没有当前统计样本，不代表零表现或未入选。

按注册材料的宽泛名义位置组拆分如下。该分组不是战术位置。

| 注册名义位置组 | 人数 | ≤21岁 | 22–24岁 | 25–29岁 | ≥30岁 | 平均年龄 | 有正分钟样本 | 无统计行 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 门将 | 5 | 1 | 2 | 1 | 1 | 25.2 | 1 | 4 |
| 后卫 | 12 | 3 | 0 | 6 | 3 | 27.2 | 10 | 2 |
| 中场 | 16 | 6 | 1 | 4 | 5 | 25.2 | 11 | 5 |
| 前锋 | 6 | 1 | 0 | 3 | 2 | 28.3 | 6 | 0 |

出生日期核验覆盖为：38 人的二级球员资料已由另一公开来源交叉核对；卢彤鋆的生日来自中国足协公开注册材料，并由 Transfermarkt 球员资料复核。39 人均有至少两项可追溯的生日资料。新增交叉来源包括 Transfermarkt 国安一线队与U20名单，以及 FotMob、Tuttosport、Sina Sports 和 Goal 的球员资料页。年龄快照逐人保留了出生日期来源 ID、核对状态和名单位置出处。这些来源用于生日核对，不用于证明决策日阵容身份。

## 位置证据与实际角色

现有公开名单或球员简介中，24 人有边后卫、中后卫、后腰、中前卫、前腰、边锋或更具体的球员位置标签；14 人只有宽泛位置组标签；1 人没有找到独立球员简介位置标签。相应来源与原文位置标签保存在球员证据表中。

这些公开标签只是名单或球员简介中的位置资料，不能说明球员本赛季每场实际担任的角色。现有 406 条国安球员比赛行中，22 条有比赛级角色资料：2026-09-15 亚冠对浦项铁人一场记录了 4-4-2 阵型线路；2026-08-15 中超对天津津门虎一场依据中足联首发与北青体育报道，记录了该场报告的门将/后卫/中场/前锋组别。后者的公开第三方阵型页存在 4-4-2 与 4-2-3-1 分歧，因此 formation 留空，只采用媒体报道明确给出的宽泛首发位置组。其余 384 条比赛行仍没有比赛级角色证据。两场样本都不细分左右/中路，也不外推至其他比赛或赛季角色；尚不足以诊断具体战术位置深度。

本轮另审查了 2026-08-15 对天津津门虎的角色候选。Mackolik、MatchCountdown 和 Foot Mercato 的页面列出国安 4-4-2；WorldFootball.net 列出 4-2-3-1。中足联战报与北青体育报道可核对同一组首发，后者直接按门将、后卫、中场、前锋列出11名球员。角色表据此只记录宽泛比赛位置组，不选择其中任一阵型，也不从阵型推演球员角色。各来源及这一限制已登记在公开来源台账。

两处标签差异保留待核对：蒋子承在注册名义组为前锋，赛季球员表则标为中场；恩科洛洛在注册名义组为中场，公开球员表则标为边锋。这里并列记录来源，不用球员简介覆盖名单登记组，也不将任一标签推定为比赛实际角色。

## 下一步诊断边界

- 年龄结构和出场样本已可按 39 人当前阵容阅读；45 人整季贡献口径仍留在原 C2 使用量基线。
- 在补强判断前，需要把名单位置、球员简介位置和比赛实际部署分开整理，并逐项保留证据。
- 实际角色需要有阵型、首发站位或出场描述等比赛级来源。未取得此类证据时继续标记未知。
- C1 仍处于 IN PROGRESS；本报告是预Gate分析，不能单独用于正式位置需求判断。

## 数据文件

- 球员级年龄与证据：[c2_age_structure_2026_guoan.csv](../../data/csl/decision_snapshot_2026-09-27/c2_age_structure_2026_guoan.csv)
- 出生日期与球员简介位置原始摘录：[player_public_profile_evidence_2026_guoan.csv](../../data/csl/decision_snapshot_2026-09-27/player_public_profile_evidence_2026_guoan.csv)
- 机器汇总：[c2_age_structure_summary_2026_guoan.json](../../data/csl/decision_snapshot_2026-09-27/c2_age_structure_summary_2026_guoan.json)
- 来源登记：[public_source_register.csv](../../data/csl/decision_snapshot_2026-09-27/public_source_register.csv)
- 单场比赛实际角色证据：[match_role_evidence_2026_guoan.csv](../../data/csl/decision_snapshot_2026-09-27/match_role_evidence_2026_guoan.csv)

## 来源

- [北京国安足球俱乐部2026赛季名单与球员资料（名单标注更新至2026-09-14）](https://zh.wikipedia.org/wiki/北京国安足球俱乐部2026赛季)
- [National Football Teams：Beijing Guoan 2026](https://www.national-football-teams.com/club/437/2026_2/Beijing_Guoan.html)
- [中国足协青少年运动员公开注册名单（卢彤鋆，2023）](https://imageoss.thecfa.cn/upload/file/20230628/1687936794968511.pdf)
- [Transfermarkt：北京国安2026一线队名单](https://www.transfermarkt.com/beijing-guoan/kader/verein/3176/saison_id/2025/plus/1)；[北京国安U20名单](https://www.transfermarkt.com/beijing-guoan-u20/kader/verein/93911/saison_id/2025/plus/1)
- [Transfermarkt：卢彤鋆球员资料](https://www.transfermarkt.co.uk/beijing-guoan/startseite/verein/3176/saison_id/2025)，用于复核中国足协登记生日。
- [FotMob：罗子祥](https://www.fotmob.com/players/2092752/zixiang-luo)、[Tuttosport：陈康悦](https://www.tuttosport.com/giocatore/calcio/kangyue-chen/673154)、[Sina Sports：刘俊泽](https://match.sports.sina.com.cn/football/player.php?dpc=1&id=9057656)、[Goal：夏晓雨](https://www.goal.com/en-sa/player/x-xia/sEnarSgXdEhTmhC89ehkj)
- [Starting11：国安对浦项的确认首发与4-4-2阵型](https://starting11.com/fixtures/beijing-guoan-vs-pohang-steelers)；[FotMob：同场首发与阵型交叉核对](https://www.fotmob.com/matches/beijing-guoan-vs-pohang-steelers/2ymampm)
- 2026-08-15 对天津津门虎：[中足联赛报](https://www.cfl-china.cn/zh/content/news/Lnuf.html) 与 [北青体育（新浪转载）](https://www.sina.cn/news/detail/5332249459557230.html) 支持首发身份及宽泛位置组；[Mackolik](https://www.mackolik.com/mac/tianjin-jinmen-vs-beijing-guoan/81po1759neralepgwtvnsles4)、[MatchCountdown](https://matchcountdown.com/en/football/football-169/tianjin-teda-vs-beijing-guoan-2026-08-15) 和 [Foot Mercato](https://www.footmercato.net/live/6633794515954937069-tianjin-teda-vs-beijing-guoan) 列 4-4-2，[WorldFootball.net](https://www.worldfootball.net/match-report/co1106/china-super-league/ma11909380/tianjin-jinmen-tiger_beijing-guoan/) 列 4-2-3-1。精确阵型未判定；角色数据只采用报道直接给出的宽泛位置组。
