# 北京国安 2026 人名册跨站核对（2026-09-30）

## 范围与结果

以 2026-09-27 冻结的 45 人整季贡献候选宇宙为逐行主键；其中 39 人属于决策日一线队分析队列，6 人不属于。对照结果见[逐人姓名交叉表](../data/csl/decision_snapshot_2026-09-27/roster_name_crosswalk_2026-09-30.csv)，可由 `scripts/build_roster_name_crosswalk_2026.py` 从现有决策名册与人工核读的站点名单重建。

| 来源 | 本表能与 45 人对应的姓名 | 核读方式与范围 |
|---|---:|---|
| [Transfermarkt 2026 详细名单](https://www.transfermarkt.com/beijing-guoan/kader/verein/3176/saison_id/2025/plus/1) | 36 | 搜索索引中的赛季名单；索引约 3 个月前抓取。网页直接访问触发人机验证。另将[刘邵子洋球员页](https://www.transfermarkt.com/shaoziyang-liu/profil/spieler/966946)的可检索档案计入，因此该站共 37 人。 |
| [Sofascore 国安球队页](https://www.sofascore.com/football/team/beijing-guoan/3376) | 41 | 2026-09-30 浏览器可见页面的“Current Beijing Guoan players”文字名单；该页共列 45 个英文姓名串。 |
| [WhoScored 国安 2026 赛季队页](https://www.whoscored.com/teams/2540/show/china-beijing-guoan) | 30 | 2026-09-30 浏览器可见“Beijing Guoan Squad”表格及球员资料链接；表格按本赛季赛事统计列人。 |

三站合并后，45 名既有候选每人至少有一条跨站姓名对应。表中列明各站原文写法、来源页、可见的 WhoScored 个人资料链接、已有官方/认证账号注册材料的来源 ID 与链接，以及决策队列标记。由于国安中英文姓名常有姓/名顺序差异，交叉表保留各站原文，例如“程熙/Cheng Xi/Xi Cheng”和“阿不都海米提/Abdugheni Abduhamit/Abduhamit Abdugheni”。这些对应以现有中文注册名册为基准，供后续逐人复核，不把纯字符串相似视为独立身份凭证。

## 不一致与证据边界

- Sofascore 没有列出本项目中的冯博轩、张健智、江文豪、魏家傲；这四人分别出现在 Transfermarkt 赛季索引或 WhoScored 赛季统计名单中。缺席 Sofascore 当前页不证明某个历史时点未效力国安。
- Sofascore 另列 `Wang Zihao`、第二个写法为 `Yu Wang` 的姓名串、`Shanghan Li`、`Arturo Cheng`；现有 45 人名册无法安全地逐一对应。详见[未匹配姓名表](../data/csl/decision_snapshot_2026-09-27/roster_unmatched_provider_names_2026-09-30.csv)。其中 `Wang Yu` 已与王禹对应，另一个 `Yu Wang` 暂不合并。
- Sofascore 当前页仍列有此前用户对账为 U20 的林涵祺、马名扬；Transfermarkt 旧索引及 WhoScored 赛季名单也含已离队/外租者。WhoScored 页明确说明表中阴影球员可能已租借或出售。因此三个站点的“列名”都只作姓名/赛季关联证据，不用来推断 2026-09-27 的效力状态。
- 日期 `2026-09-30` 是本次读取日期，不是名单各条目生效日期。Transfermarkt 搜索索引的抓取日期与读取日期还应分开理解。WhoScored 和 Sofascore 属可变页面；原 39 人决策队列未据此重算。
- 3 月、7 月中超和 9 月亚冠官方/已认证账号注册公告仍是既有注册证据。它们表明特定日期/赛事的报名情况，但单份报名图或第三方名单均不能自动给出完整效力区间。本次完成的是**45 人姓名对应**；43 条用户公开证据对账所需的逐项原始链接/归档引用和若干准确变动日期仍待补齐，C1 状态保持 `IN PROGRESS`。
