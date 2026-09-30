# C1 Guoan Decision Layer — 2026-09-27

**Snapshot cut-off:** 2026-09-27  
**Status:** C1 remains `IN PROGRESS` for matchday-squad and role evidence. The user supplied an authoritative 39-person formal roster on 2026-09-30 and directed that it be used without external cross-verification. Seven listed U20 nonparticipants are excluded from C2 discussion, leaving 32. Exact dates for three exits/reassignments remain unknown.

## What is now built

The builder at `scripts/build_guoan_c1_snapshot.py` combines the canonical 2026 Guoan player-match rows with public registration and official match-report evidence. A reconciliation against the full-season fixture ledger found that the older Guoan-specific ledger had omitted Round 1 event `15551889` (Wuhan Three Towns 0–2 Beijing Guoan, 2026-03-08), even though its saved DOM and canonical six-category data were present. The fixture was restored to the Guoan ledger, and its dedicated export/audit were rebuilt; the current Guoan capture audit is now 27/27 completed fixtures, 26 CSL + 1 AFC Elite, and 823 player-match rows across both teams. It generated:

- `data/csl/decision_snapshot_2026-09-27/public_source_register.csv`
- `data/csl/decision_snapshot_2026-09-27/squad_registration_evidence_2026.csv`
- `data/csl/decision_snapshot_2026-09-27/squad_membership_decision_snapshot_2026-09-27.csv`
- `data/csl/decision_snapshot_2026-09-27/c2_operational_cohort_2026-09-27.csv` — 39-person formal roster with a per-player flag for the 32-person C2 discussion scope.
- `data/csl/decision_snapshot_2026-09-27/user_authoritative_roster_2026-09-30.csv` — direct user authority for membership, U20 discussion exclusion, registration notes and current role notes.
- `data/csl/decision_snapshot_2026-09-27/user_provided_membership_reconciliation_2026-09-27.csv`
- `data/csl/decision_snapshot_2026-09-27/player_match_participation_2026_guoan.csv`
- `data/csl/decision_snapshot_2026-09-27/player_season_usage_2026_guoan.csv`
- `data/csl/decision_snapshot_2026-09-27/player_position_evidence_2026_guoan.csv`
- `data/csl/decision_snapshot_2026-09-27/official_starting_xi_audit_2026_guoan.csv`
- `data/csl/decision_snapshot_2026-09-27/secondary_starting_xi_audit_2026_guoan.csv`
- `data/csl/decision_snapshot_2026-09-27/transfermarkt_starting_xi_crosscheck_2026_guoan.csv`
- `data/csl/decision_snapshot_2026-09-27/c1_snapshot_build_summary.json`

The outputs are reproducible from `data/csl/season_2026/player_match_stats_2026.csv`; they preserve source links and distinguish registration, observed appearance, official start, broad observed position group, nominal position, and functional role.

## Evidence reconciliation

| Evidence set | Rows / people | What it supports | Limit |
|---|---:|---|---|
| Club-attributed 2026 CSL roster post, 2026-03-03 | 35 registrations | Opening domestic registration candidate set | The club-attributed source is an image-only mirror; exact names/numbers are transcribed from third-party reporting. It is not a decision-date roster. |
| Beijing Guoan verified CSL second-window roster post, 2026-07-23 | 35 registrations | Dated evidence of domestic CSL registration; includes the roster's broad position groups | The club post is image-only. Names, numbers, and groups come from a linked secondary transcription that could not be independently OCR-read from the image in this pass. It does not establish status on 2026-09-27. |
| Verified club AFC Elite roster post, 2026-09-13 | 35 registrations | Latest dated club registration evidence before the cut-off; broadcaster transcription supplies the broad position groups | Competition-specific list; does not establish a complete domestic first-team list or prove no changes through 2026-09-27. |
| Union of March, July, and September registration evidence | 45 unique candidates | Evidence universe to reconcile | Not asserted to be the complete squad on the decision date. |
| Later-list reconciliation | 31 in both July CSL and September AFC lists; 4 July CSL only; 4 September AFC only; 4 March-only; 2 additional publicly documented transitions | Makes competition-specific scope and list turnover visible without treating omission as departure | Dated registrations remain separate historical evidence; the user's direct authoritative roster defines decision-date membership. |
| User-designated authoritative roster, 2026-09-30 | 45 candidates: 39 formal first-team members and 6 outside; 32 in C2 discussion | Direct user authority for the frozen decision-date membership and discussion scope, without external cross-verification | Three exit/reassignment dates remain unspecified; listed position groups and current-role remarks are not match-by-match observations. |
| Registration-derived nominal position group | 39 of 45 candidates classified; 6 unknown | Broad goalkeeper/defender/midfielder/forward category from the July CSL or September AFC roster grouping | These are registration-list categories, not tactical roles. Four initial-list-only candidates and the two confirmed departures have no later roster position evidence. |
| Sofascore Guoan player-stat rows | 406 rows / 32 player IDs across 27/27 completed in-scope fixtures | Positive-minute appearance evidence and source-displayed match position group | A missing row does not prove non-selection; no unused-substitute inference. |
| Latest positive-minute match evidence | 32 of 45 candidates; latest observation 2026-09-15 | Dated evidence of a candidate's last observed on-field participation for Guoan; match ID, competition, and source URL are retained in the membership and usage outputs | It confirms participation only on that match date, not continued club membership on 2026-09-27. Thirteen candidates have no positive-minute sample in the in-scope 2026 rows. |
| Official CFL match reports | 13 of 27 completed in-scope Guoan fixtures | Complete starting XI for those 13 matches; all 13 XIs contain 11 unique players and resolve to player-stat rows | Official-source coverage remains partial; bench and unused-substitute status are not complete. |
| Secondary public match reports / lineup pages | 11 additional fixtures | Complete reported XI for each; all 11 XIs contain 11 unique players and resolve to player-stat rows | Tagged separately from official CFL evidence; the reports confirm only their named XIs and do not provide a complete season bench ledger. |
| Transfermarkt match sheets | 3 additional fixtures: `15551891`, `15552547`, `15552563` | Complete XI and formation are listed for each; all 33 names resolve to the corresponding Sofascore Guoan match-stat rows | The user reviewed and confirmed these lineups on 2026-09-27. Recorded as a distinct third-party database tier, never as official evidence. |
| Combined starting-XI evidence | 27 of 27 completed in-scope Guoan fixtures | `started` is now evidence-backed for observed player-stat rows in every completed in-scope fixture, with source tier and URL retained per row | Starting-XI coverage does not establish complete benches, unused substitutes, or non-selection. |

The user's authoritative roster places 39 players in the formal first team and six outside it. Zhang Jianzhi is loaned to Guangxi Hengchen; Lin Hanqi and Ma Mingyang moved to U20 during the summer window. The seven U20 nonparticipants still named in the formal 39 are Lu Tongyun, Luo Zixiang, Xia Xiaoyu, Zhang Haoran, Liu Junze, Chen Kangyue and Wang Size; the user excludes them from C2 discussion. Spajic was added in the summer window in place of Nkololo's CSL registration; Akolo and Dudziak are AFC-only. User current-role notes place Deng Jiefu and Lin Liangming mainly at left midfield and Bai Yang at left-back despite his centre-back registration. These notes remain separate from match-specific observed roles. The 39-person formal cohort has 28 members showing positive minutes and 11 with no positive-minute sample; across all 45 candidates, the season totals remain 32 with positive minutes and 13 without.

## Semantic rules applied

- A player row in the completed-match General table with positive displayed minutes is coded as `appeared_in_player_stats_table`.
- Latest appearance fields point to the most recent positive-minute row, not to a contract interval. The final observed date is 2026-09-15, twelve days before the frozen decision date; membership follows the user's authoritative roster.
- All 32 distinct Guoan provider player identities in the 2026 match-stat export resolve through the maintained name crosswalk. The 11 formal first-team members with blank `player_id` have no row in the in-scope 2026 Guoan player-match export; this is recorded as no observed sample, not a failed alias match and not proof that a player was omitted from a matchday squad.
- Official CFL match reports set `started=true` for the named XI, and `started=false` for other observed appearances in those same matches. Separately tagged secondary reports and the three user-reviewed Transfermarkt lineups do the same only for their own events. Every in-scope Guoan appearance row now has a source-backed `started` value.
- Transfermarkt's complete XIs for events `15551891`, `15552547`, and `15552563` were manually reviewed and confirmed by the user. All 33 names crosswalk to their corresponding Sofascore player-stat rows. A verified BRTV post, the verified CSL account's matchday lineup graphic, and Beijing Youth Daily's match report remain documented as additional corroborating context; the Transfermarkt records stay visibly tagged as third-party database evidence.
- Provider values `G`, `D`, `M`, and `F` are retained only as `observed_position_group`. `nominal_position` now records the broad position category printed by the July CSL or September AFC registration list for 39 candidates; each category points to a source ID in the public source register. Six candidates without a later position-group source remain unknown. Match-specific `observed_role` is populated for 22 rows across two fixtures: 11 formation-line roles from the 2026-09-15 ACL 4-4-2 lineup, and 11 broad match-reported position groups from the 2026-08-15 CSL lineup report. Public sources disagree on the latter match's exact formation, so that field remains blank and the roles use only the directly reported groups. The other 384 appearance rows stay unknown; no role is inferred from `G/D/M/F`.
- No row absent from a match-stat table is coded as `did_not_play`, `not_selected`, or `unused_substitute`.
- No competition weight is applied to minutes, appearances, or starts. Performance weighting belongs in the later analysis view after C1 passes.
- First-team membership, competition registration, U20 C2 discussion exclusion, availability and user-reported current roles are separate. The user's authoritative roster controls membership and discussion scope; external cross-verification is not required for those direct inputs.
- `valid_from` and `valid_to` remain blank where exact first-team transition dates were not provided or supported. A roster-registration date is not silently substituted for a membership interval boundary.

## C1 blockers and next work

1. Keep the 39-person authoritative formal roster and 32-person C2 discussion scope distinct; do not pull the seven U20 nonparticipants into depth arguments.
2. Record exact first-team transition dates for Zhang Jianzhi's Guangxi Hengchen loan and the summer U20 reassignments of Lin Hanqi and Ma Mingyang if supplied later. Jiang Wenhao's Shaanxi Union loan joined date is recorded as 2026-07-03. `valid_from`/`valid_to` remain blank where the full intervals are not established.
3. Continue seeking official match reports for the 11 events currently supported only by secondary reports and, where available, official confirmation for the three user-reviewed Transfermarkt XIs. Keep all source tiers distinct.
4. Build the matchday squad/substitute ledger if a public source supports it; until then, keep unobserved player-match statuses unknown.
5. Validate the transcribed registration position groups against the underlying club images or official player profiles where accessible; keep the match-level provider group and functional deployment role in separate fields.

The user-designated roster is sufficient to continue C2 without further membership verification. C1 remains in progress for matchday and role evidence; C2 discussion uses 32 players, while the 39-person formal roster and 45-person season contribution universe remain available as separate populations.

## Source URLs recorded in the output

- [Club-attributed March first-team roster post](https://news.zhibo8.com/zuqiu/2026-03-03/69a69592d5bbcnative.htm) and [third-party transcription](https://www.ppsport.com/360news/news/2495413.html?plt=clt)
- [Verified Beijing Guoan July CSL second-window roster post](https://www.sina.cn/news/detail/5323868302478142.html) and [secondary transcription of names, numbers, and position groups](https://www.yndredu.com/news/zuqiu/186139.html)
- [Verified Beijing Guoan September AFC roster post](https://weibo.com/2/detail/5342666443459201) and [verified Migu Football transcription](https://www.sina.cn/news/detail/5342688482169115.html)
- [Sofascore Beijing Guoan team page](https://www.sofascore.com/football/team/beijing-guoan/3376) is the recorded rendered-stat source; event-specific links are retained per appearance row in the output ledger.
- [Official CFL 2026-09-05 Guoan–Port report](https://www.cfl-china.cn/zh/content/news/nDAQ.html)
- Transfermarkt 2026 Guoan lineup sources, user-reviewed and confirmed on 2026-09-27: [Shandong–Guoan, 14 March](https://www.transfermarkt.com/spielbericht/index/spielbericht/4826113), [Chongqing–Guoan, 30 May](https://www.transfermarkt.co.uk/spielbericht/index/spielbericht/4827804), and [Guoan–Shandong, 4 July](https://www.transfermarkt.com/spielbericht/index/spielbericht/4827828). They remain a separate third-party database evidence tier.
- Corroborating public sources located: [verified BRTV Football 100 lineup post for 14 March](https://www.sina.cn/news/detail/5276379853625238.html), [verified CSL account's 30 May starting-lineup graphic](https://www.sina.cn/news/detail/5304345402807057.html), and [Beijing Youth Daily's 4 July match report](https://app.bjtitle.com/8816/newshow.php?did=356416815496248&mood=&newsid=6762008&typeid=16&uid=0).
- Official CFL lineup reports for 13 matches and secondary public lineup sources for 11 additional matches are listed by event in `public_source_register.csv` and their separate audit CSVs.
- [Transfermarkt Jiang Wenhao profile](https://www.transfermarkt.com/wenhao-jiang/profil/spieler/839306) (search-index excerpt, joined date) and [Shaanxi Union announcement mirror](https://i.ifeng.com/c/8uSMhET63Rq) (loan announcement) support the 2026-07-03 transition date. Direct Transfermarkt page access triggered human verification on 2026-09-30; the profile field was not inspected in a live page view. See `public_transition_evidence_2026-09-30.csv`.
