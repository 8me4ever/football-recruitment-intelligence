#!/usr/bin/env python3
"""Build an auditable Guoan C1 decision-date evidence layer from local match data.

The script intentionally distinguishes historic competition registrations,
decision-date membership, Sofascore stat-table appearances, and source-tiered starts.
It does not infer unused substitutes or tactical roles from missing stat rows.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATS = ROOT / "data" / "csl" / "season_2026" / "player_match_stats_2026.csv"
FIXTURES = ROOT / "data" / "csl" / "season_2026" / "fixtures_2026_in_scope.csv"
OUTPUT = ROOT / "data" / "csl" / "decision_snapshot_2026-09-27"
USER_ROSTER_RECONCILIATION = OUTPUT / "user_provided_membership_reconciliation_2026-09-27.csv"
PUBLIC_TRANSITION_EVIDENCE = OUTPUT / "public_transition_evidence_2026-09-30.csv"
DECISION_DATE = "2026-09-27"

DOMESTIC_URL = "https://news.zhibo8.com/zuqiu/2026-03-03/69a69592d5bbcnative.htm"
DOMESTIC_TRANSCRIPTION_URL = "https://www.ppsport.com/360news/news/2495413.html?plt=clt"
CSL_SECOND_WINDOW_URL = "https://www.sina.cn/news/detail/5323868302478142.html"
CSL_SECOND_WINDOW_TRANSCRIPTION_URL = "https://www.yndredu.com/news/zuqiu/186139.html"
AFC_URL = "https://weibo.com/2/detail/5342666443459201"
AFC_TRANSCRIPTION_URL = "https://www.sina.cn/news/detail/5342688482169115.html"
FENG_TRANSFER_URL = "https://i.ifeng.com/c/8uSnK13MrxB"
WEI_LOAN_URL = "https://k.sina.com.cn/article_7879923918_1d5ae18ce02001ethw.html?from=sports&subch=osport"

# March 3 CSL registration transcription of the club's image announcement.
DOMESTIC_ROSTER = [
    (2, "吴少聪"), (3, "何宇鹏"), (4, "李磊"), (5, "拉莫斯"), (6, "池忠国"),
    (7, "塞尔吉尼奥"), (8, "孔特"), (9, "张玉宁"), (10, "张稀哲"), (11, "林良铭"),
    (14, "卢彤鋆"), (16, "冯博轩"), (17, "杨立瑜"), (18, "王禹"), (20, "恩科洛洛"),
    (21, "茹子楠"), (22, "韩佳奇"), (23, "达万"), (24, "阿不都海米提"), (26, "柏杨"),
    (27, "王刚"), (29, "法比奥"), (30, "范双杰"), (32, "王思泽"), (33, "努尔艾力·阿巴斯"),
    (34, "侯森"), (35, "江文豪"), (36, "贾非凡"), (37, "曹永竞"), (38, "魏家傲"),
    (39, "张健智"), (41, "程熙"), (42, "林涵祺"), (45, "马名扬"), (47, "邓捷夫"),
]

# July 23 CSL second-window registration. The club's verified post is image-only;
# the position-group transcription is kept linked to the primary post and
# identified as secondary-source transcription evidence (the image itself was
# not independently readable in the current browser retrieval).
CSL_SECOND_WINDOW_ROSTER = [
    (22, "韩佳奇", "Goalkeeper"), (31, "刘邵子洋", "Goalkeeper"),
    (33, "努尔艾力·阿巴斯", "Goalkeeper"), (34, "侯森", "Goalkeeper"),
    (2, "吴少聪", "Defender"), (3, "何宇鹏", "Defender"), (4, "李磊", "Defender"),
    (5, "拉莫斯", "Defender"), (21, "茹子楠", "Defender"), (24, "阿不都海米提", "Defender"),
    (25, "斯帕伊奇", "Defender"), (26, "柏杨", "Defender"), (27, "王刚", "Defender"),
    (30, "范双杰", "Defender"), (47, "邓捷夫", "Defender"), (55, "罗子祥", "Defender"),
    (6, "池忠国", "Midfielder"), (7, "塞尔吉尼奥", "Midfielder"), (8, "孔特", "Midfielder"),
    (10, "张稀哲", "Midfielder"), (18, "王禹", "Midfielder"), (23, "达万", "Midfielder"),
    (32, "王思泽", "Midfielder"), (36, "贾非凡", "Midfielder"), (37, "曹永竞", "Midfielder"),
    (41, "程熙", "Midfielder"), (43, "夏晓雨", "Midfielder"), (50, "张昊冉", "Midfielder"),
    (57, "刘俊泽", "Midfielder"), (59, "陈康悦", "Midfielder"),
    (9, "张玉宁", "Forward"), (11, "林良铭", "Forward"), (17, "杨立瑜", "Forward"),
    (29, "法比奥", "Forward"), (58, "蒋子承", "Forward"),
]

# September 13 AFC registration, transcribed from the club's verified post.
AFC_ROSTER = [
    (4, "李磊"), (5, "拉莫斯"), (6, "池忠国"), (7, "塞尔吉尼奥"), (8, "孔特"),
    (9, "张玉宁"), (10, "张稀哲"), (11, "林良铭"), (14, "卢彤鋆"), (17, "杨立瑜"),
    (18, "王禹"), (20, "恩科洛洛"), (21, "茹子楠"), (22, "韩佳奇"), (23, "达万"),
    (24, "阿不都海米提"), (25, "斯帕伊奇"), (26, "柏杨"), (27, "王刚"), (28, "杜齐亚克"),
    (29, "法比奥"), (30, "范双杰"), (31, "刘邵子洋"), (32, "王思泽"), (34, "侯森"),
    (37, "曹永竞"), (41, "程熙"), (43, "夏晓雨"), (47, "邓捷夫"), (50, "张昊冉"),
    (55, "罗子祥"), (57, "刘俊泽"), (58, "蒋子承"), (59, "陈康悦"), (77, "阿科洛"),
]
AFC_POSITION_BY_NAME = {
    **{name: "Goalkeeper" for name in ["侯森", "韩佳奇", "卢彤鋆", "刘邵子洋"]},
    **{name: "Defender" for name in ["李磊", "拉莫斯", "茹子楠", "阿不都海米提", "斯帕伊奇", "柏杨", "王刚", "范双杰", "邓捷夫", "罗子祥"]},
    **{name: "Midfielder" for name in ["池忠国", "塞尔吉尼奥", "孔特", "张稀哲", "王禹", "恩科洛洛", "达万", "杜齐亚克", "王思泽", "曹永竞", "程熙", "夏晓雨", "张昊冉", "刘俊泽", "陈康悦"]},
    **{name: "Forward" for name in ["张玉宁", "林良铭", "杨立瑜", "法比奥", "蒋子承", "阿科洛"]},
}

# Map the provider's English transliterations to the Chinese identity used by
# the two registration sources. Values not in this map remain provider labels.
SOFASCORE_TO_ZH = {
    "Abdugheni Abduhamit": "阿不都海米提", "Aboubacar Konte": "孔特",
    "Béni Nkololo": "恩科洛洛", "Chadrac Akolo": "阿科洛", "Cheng Xi": "程熙",
    "Chi Zhongguo": "池忠国", "Dawhan": "达万", "Deng Jiefu": "邓捷夫",
    "Fabio Abreu": "法比奥", "Feifan Jia": "贾非凡", "Feng Boxuan": "冯博轩",
    "Gang Wang": "王刚", "Guilherme Ramos": "拉莫斯", "Hou Sen": "侯森",
    "Jeremy Dudziak": "杜齐亚克", "Jiaao Wei": "魏家傲", "Jiang Wenhao": "江文豪",
    "Li Lei": "李磊", "Lin Liangming": "林良铭", "Sai Erjini'ao": "塞尔吉尼奥",
    "Shuangjie Fan": "范双杰", "Tze-Nam Yue": "茹子楠", "Uroš Spajić": "斯帕伊奇",
    "Wang Yu": "王禹", "Yang Bai": "柏杨", "Yang Liyu": "杨立瑜",
    "Yongjing Cao": "曹永竞", "Yupeng He": "何宇鹏", "Zhang Jianzhi": "张健智",
    "Zhang Xizhe": "张稀哲", "Zhang Yuning": "张玉宁", "Zicheng Jiang": "蒋子承",
}

# Full official starting XIs as printed in CFL match reports. These retain the
# highest source tier; secondary and user-reviewed database lineups are distinct.
OFFICIAL_STARTERS = {
    "15551889": ("https://www.cfl-china.cn/zh/content/news/mBiB.html", [
        "拉莫斯", "塞尔吉尼奥", "孔特", "张玉宁", "林良铭", "恩科洛洛", "阿不都海米提", "王刚", "法比奥", "侯森", "邓捷夫"]),
    "15552489": ("https://www.cfl-china.cn/zh/content/news/bSDa.html", [
        "塞尔吉尼奥", "孔特", "张稀哲", "林良铭", "恩科洛洛", "阿不都海米提", "柏杨", "王刚", "法比奥", "侯森", "邓捷夫"]),
    "15552493": ("https://www.cfl-china.cn/zh/content/news/uVVu.html", [
        "李磊", "拉莫斯", "塞尔吉尼奥", "孔特", "张玉宁", "林良铭", "恩科洛洛", "达万", "柏杨", "王刚", "侯森"]),
    "15552498": ("https://www.cfl-china.cn/zh/content/news/GbVM.html", [
        "拉莫斯", "塞尔吉尼奥", "孔特", "张玉宁", "张稀哲", "林良铭", "达万", "柏杨", "王刚", "侯森", "曹永竞"]),
    "15552507": ("https://www.cfl-china.cn/zh/content/news/ePaU.html", [
        "李磊", "拉莫斯", "塞尔吉尼奥", "孔特", "张玉宁", "林良铭", "达万", "柏杨", "王刚", "侯森", "曹永竞"]),
    "15552546": ("https://www.cfl-china.cn/zh/content/news/CLkv.html", [
        "拉莫斯", "塞尔吉尼奥", "孔特", "张玉宁", "张稀哲", "茹子楠", "达万", "柏杨", "王刚", "法比奥", "侯森"]),
    "15552576": ("https://www.cfl-china.cn/zh/content/news/mcHi.html", [
        "何宇鹏", "拉莫斯", "塞尔吉尼奥", "孔特", "张玉宁", "林良铭", "恩科洛洛", "达万", "柏杨", "法比奥", "侯森"]),
    "15552587": ("https://www.cfl-china.cn/zh/content/news/GAYO.html", [
        "拉莫斯", "孔特", "张玉宁", "杨立瑜", "茹子楠", "达万", "斯帕伊奇", "柏杨", "法比奥", "侯森", "邓捷夫"]),
    "15552596": ("https://www.cfl-china.cn/zh/content/news/HjEz.html", [
        "拉莫斯", "孔特", "张玉宁", "杨立瑜", "茹子楠", "达万", "斯帕伊奇", "柏杨", "法比奥", "侯森", "曹永竞"]),
    "15552613": ("https://www.cfl-china.cn/zh/content/news/Lnuf.html", [
        "塞尔吉尼奥", "孔特", "张玉宁", "茹子楠", "达万", "阿不都海米提", "柏杨", "王刚", "法比奥", "侯森", "邓捷夫"]),
    "15552619": ("https://www.cfl-china.cn/zh/content/news/iZbR.html", [
        "拉莫斯", "塞尔吉尼奥", "张玉宁", "达万", "阿不都海米提", "柏杨", "王刚", "法比奥", "侯森", "曹永竞", "邓捷夫"]),
    "15552624": ("https://www.cfl-china.cn/zh/content/news/DqGe.html", [
        "拉莫斯", "塞尔吉尼奥", "张玉宁", "杨立瑜", "茹子楠", "达万", "柏杨", "王刚", "法比奥", "侯森", "曹永竞"]),
    "15552633": ("https://www.cfl-china.cn/zh/content/news/nDAQ.html", [
        "拉莫斯", "塞尔吉尼奥", "张玉宁", "张稀哲", "杨立瑜", "王禹", "茹子楠", "柏杨", "王刚", "侯森", "曹永竞"]),
}

# Complete XIs reported by reputable public media or match-lineup pages where
# a CFL match report was not located. These are kept in a separate evidence
# tier and never counted as official CFL reports. Each full XI is checked
# against the Guoan match-stat identities before it can set started status.
SECONDARY_STARTERS = {
    "15551900": ("https://finance.sina.com.cn/jjxw/2026-03-21/doc-inhruetq2920218.shtml", "Beijing Youth Daily syndicated report", [
        "张健智", "贾非凡", "阿不都海米提", "拉莫斯", "邓捷夫", "恩科洛洛", "张稀哲", "孔特", "林良铭", "法比奥", "张玉宁"]),
    "15552476": ("https://m2.zhibo8.com/news/web/zuqiu/2026-04-04/69d0948caa95cnative.htm", "Zhibo8 matchday lineup report", [
        "张健智", "拉莫斯", "阿不都海米提", "邓捷夫", "孔特", "张稀哲", "恩科洛洛", "贾非凡", "张玉宁", "林良铭", "法比奥"]),
    "15552529": ("https://sports.sina.cn/2026-05-02/detail-inhwppvx5370696.d.html", "Sina Sports match report", [
        "侯森", "拉莫斯", "阿不都海米提", "柏杨", "王刚", "塞尔吉尼奥", "孔特", "张稀哲", "达万", "曹永竞", "张玉宁"]),
    "15552536": ("https://www.fczhibo.net/live/zhongchao/511567.html", "Fengchi Live match lineup page", [
        "侯森", "茹子楠", "王刚", "拉莫斯", "柏杨", "达万", "孔特", "塞尔吉尼奥", "张稀哲", "曹永竞", "张玉宁"]),
    "15549838": ("https://news.zhibo8.com/zuqiu/2026-05-15/6a06c7b57051anative.htm", "Zhibo8 matchday lineup report", [
        "侯森", "拉莫斯", "茹子楠", "柏杨", "王刚", "塞尔吉尼奥", "孔特", "张稀哲", "张玉宁", "林良铭", "法比奥"]),
    "15549843": ("https://www.ppsports.com/article/news/2538609.html", "PP Sports match report", [
        "侯森", "李磊", "拉莫斯", "茹子楠", "柏杨", "王刚", "塞尔吉尼奥", "孔特", "张稀哲", "达万", "法比奥"]),
    "15549855": ("https://news.zhibo8.com/zuqiu/2026-05-23/6a1154355dcd0native.htm", "Zhibo8 matchday lineup report", [
        "侯森", "拉莫斯", "茹子楠", "柏杨", "王刚", "塞尔吉尼奥", "孔特", "张稀哲", "达万", "张玉宁", "法比奥"]),
    "15552561": ("https://www.ppsports.com/article/news/2564119.html", "PP Sports match report", [
        "侯森", "拉莫斯", "茹子楠", "柏杨", "王刚", "孔特", "张稀哲", "达万", "张玉宁", "林良铭", "法比奥"]),
    "15552600": ("https://i.ifeng.com/c/8vOsEt0rsRr", "Dongqiudi user report mirrored by Phoenix", [
        "侯森", "柏杨", "拉莫斯", "阿不都海米提", "茹子楠", "邓捷夫", "孔特", "达万", "曹永竞", "张玉宁", "法比奥"]),
    "16851672": ("https://app.bjtitle.com/8816/newshow.php?did=867950049830928&mood=&newsid=6773523&typeid=16&uid=0", "Beijing Youth Daily matchday report", [
        "侯森", "柏杨", "阿不都海米提", "拉莫斯", "茹子楠", "曹永竞", "达万", "塞尔吉尼奥", "杨立瑜", "张玉宁", "法比奥"]),
    "16863671": ("https://www.ppsport.com/article/news/2616403.html", "PP Sports official-lineup report", [
        "侯森", "拉莫斯", "茹子楠", "王刚", "邓捷夫", "塞尔吉尼奥", "张稀哲", "达万", "杜齐亚克", "恩科洛洛", "阿科洛"]),
}

# Transfermarkt publishes complete match-sheet XIs for the three fixtures that
# lacked a full XI in earlier snapshots. The user reviewed and confirmed these
# lineups on 2026-09-27; retain them as a distinct non-official evidence tier.
TRANSFERMARKT_STARTERS = {
    "15551891": ("https://www.transfermarkt.com/spielbericht/index/spielbericht/4826113", [
        "张健智", "拉莫斯", "邓捷夫", "阿不都海米提", "王刚", "孔特", "塞尔吉尼奥", "曹永竞", "恩科洛洛", "张玉宁", "法比奥"]),
    "15552547": ("https://www.transfermarkt.co.uk/spielbericht/index/spielbericht/4827804", [
        "侯森", "拉莫斯", "柏杨", "茹子楠", "王刚", "达万", "孔特", "张稀哲", "塞尔吉尼奥", "张玉宁", "法比奥"]),
    "15552563": ("https://www.transfermarkt.com/spielbericht/index/spielbericht/4827828", [
        "侯森", "拉莫斯", "柏杨", "何宇鹏", "达万", "孔特", "塞尔吉尼奥", "林良铭", "恩科洛洛", "张玉宁", "法比奥"]),
}

# Match-specific role units and published position groups. These do not assert
# exact left/right/central positions or a season-long player role; unresolved
# formations remain blank rather than being inferred from competing pages.
MATCH_ROLE_EVIDENCE = {
    "16863671": {
        "formation": "4-4-2",
        "role_granularity": "formation_line_only",
        "limitations": "Match-specific formation line only; exact left/right/central position is unresolved; do not generalize to other fixtures or season-long role.",
        "source_ids": "starting11_guoan_pohang_2026-09-15;fotmob_guoan_pohang_2026-09-15;sofascore_lineup_snapshot_16863671",
        "roles": {
            "侯森": "goalkeeper",
            "茹子楠": "defensive_line_member",
            "王刚": "defensive_line_member",
            "拉莫斯": "defensive_line_member",
            "邓捷夫": "defensive_line_member",
            "杜齐亚克": "midfield_line_member",
            "达万": "midfield_line_member",
            "塞尔吉尼奥": "midfield_line_member",
            "张稀哲": "midfield_line_member",
            "恩科洛洛": "forward_line_member",
            "阿科洛": "forward_line_member",
        },
    },
    "15552613": {
        "formation": "",
        "role_granularity": "match_reported_position_group",
        "limitations": "Match report's broad starting-XI position groups only; the exact formation is disputed across public sources; exact left/right/central positions and season-long role are unresolved.",
        "source_ids": "cfl_official_starting_xi_15552613;beijing_youth_daily_tianjin_guoan_2026-08-15",
        "roles": {
            "侯森": "goalkeeper",
            "茹子楠": "defensive_line_member",
            "王刚": "defensive_line_member",
            "阿不都海米提": "defensive_line_member",
            "柏杨": "defensive_line_member",
            "塞尔吉尼奥": "midfield_line_member",
            "孔特": "midfield_line_member",
            "达万": "midfield_line_member",
            "邓捷夫": "midfield_line_member",
            "张玉宁": "forward_line_member",
            "法比奥": "forward_line_member",
        },
    }
}

SOURCE_ROWS = [
    {"source_id": "guoan_csl_roster_2026-03-03", "source_type": "club_announcement_image_mirror", "published_at": "2026-03-03", "url": DOMESTIC_URL, "transcription_url": DOMESTIC_TRANSCRIPTION_URL, "evidence_note": "Page credits Beijing Guoan FC and carries the first-team roster title/date; roster is image-only. Names/numbers transcribed by Dongqiudi/PPSports and require official-image review for exact character verification."},
    {"source_id": "guoan_csl_roster_second_window_2026-07-23", "source_type": "verified_club_social_post_image_mirror", "published_at": "2026-07-23", "url": CSL_SECOND_WINDOW_URL, "transcription_url": CSL_SECOND_WINDOW_TRANSCRIPTION_URL, "evidence_note": "Sina mirror identifies the publisher as Beijing Guoan FC's verified account and shows its 2026 CSL second-window registration image. Names, shirt numbers, and roster position groups are transcribed from a secondary report; the image itself was not independently readable during this pass. This is registration evidence for 2026-07-23, not proof of exact 2026-09-27 membership."},
    {"source_id": "guoan_acl_roster_2026-09-13", "source_type": "verified_club_social_post_image", "published_at": "2026-09-13", "url": AFC_URL, "transcription_url": AFC_TRANSCRIPTION_URL, "evidence_note": "Verified Beijing Guoan FC post announces the 2026/27 AFC Elite registration. A verified Migu Football post transcribes the names and position groups; this is competition-specific registration, not a complete domestic first-team roster."},
    {"source_id": "guoan_acl_roster_transcription_2026-09-13", "source_type": "verified_broadcaster_account_transcription", "published_at": "2026-09-13", "url": AFC_TRANSCRIPTION_URL, "transcription_url": AFC_URL, "evidence_note": "Verified Migu Football account publishes the full AFC Elite squad grouped by nominal position and links the announcement to the club's roster post; retained as transcription/cross-check, not as the club's own source."},
    {"source_id": "feng_boxuan_transfer_2026-07-03", "source_type": "new_club_official_announcement_mirror", "published_at": "2026-07-03", "url": FENG_TRANSFER_URL, "transcription_url": "", "evidence_note": "Dalian Yingbo official announcement states Feng Boxuan joined after agreement with Beijing Guoan and the player."},
    {"source_id": "wei_jiaao_loan_2026-07-03", "source_type": "club_announcement_mirror", "published_at": "2026-07-03", "url": WEI_LOAN_URL, "transcription_url": "", "evidence_note": "Reports Beijing Guoan's announcement that Jiaao Wei and Ma Longjian joined Beijing Institute of Technology on loan through 2026-12-31."},
    {"source_id": "transfermarkt_jiang_wenhao_profile_index_2026-09-30", "source_type": "third_party_player_profile_search_index_excerpt", "published_at": "", "url": "https://www.transfermarkt.com/wenhao-jiang/profil/spieler/839306", "transcription_url": "", "evidence_note": "Search-index excerpt of Transfermarkt player profile lists Shaanxi Union joined date 2026-07-03 and loan parent Beijing Guoan. Direct page access triggered human verification on 2026-09-30; indexed fields are not a live page inspection."},
    {"source_id": "shaanxi_union_jiang_wenhao_loan_announcement_mirror_2026-07-03", "source_type": "new_club_announcement_mirror", "published_at": "2026-07-03", "url": "https://i.ifeng.com/c/8uSMhET63Rq", "transcription_url": "", "evidence_note": "Phoenix mirror reports Shaanxi Union's 2026-07-03 announcement of Jiang Wenhao's loan from Beijing Guoan. It corroborates the move and announcement date, while Transfermarkt supplies the joined date."},
    {"source_id": "transfermarkt_fan_shuangjie_profile_index_2026-09-30", "source_type": "third_party_player_profile_search_index_excerpt", "published_at": "", "url": "https://www.transfermarkt.com/shuangjie-fan/profil/spieler/1130473", "transcription_url": "", "evidence_note": "Search-index excerpt lists Fan Shuangjie's main profile position as Centre-Back and other positions as Defensive Midfield and Right-Back. Profile labels only; direct page access triggered human verification."},
    {"source_id": "transfermarkt_jia_feifan_profile_index_2026-09-30", "source_type": "third_party_player_profile_search_index_excerpt", "published_at": "", "url": "https://www.transfermarkt.com/feifan-jia/profil/spieler/824089", "transcription_url": "", "evidence_note": "Search-index excerpt lists Jia Feifan's main profile position as Central Midfield and other positions as Defensive Midfield and Attacking Midfield. Profile labels only; direct page access triggered human verification."},
    {"source_id": "sofascore_visible_match_stats", "source_type": "rendered_player_stats_tables", "published_at": "", "url": "https://www.sofascore.com/football/team/beijing-guoan/3376", "transcription_url": "", "evidence_note": "Local 2026 player-match export; a player row with positive minutes is treated as observed match participation. Row absence does not prove non-selection."},
]
for event_id, (url, _) in OFFICIAL_STARTERS.items():
    SOURCE_ROWS.append({"source_id": f"cfl_official_starting_xi_{event_id}", "source_type": "official_competition_match_report", "published_at": "", "url": url, "transcription_url": "", "evidence_note": f"Official CFL match report prints a complete Guoan starting XI for event {event_id}."})
for event_id, (url, source_type, _) in SECONDARY_STARTERS.items():
    SOURCE_ROWS.append({"source_id": f"secondary_starting_xi_{event_id}", "source_type": source_type, "published_at": "", "url": url, "transcription_url": "", "evidence_note": f"Public secondary source prints a complete Guoan starting XI for event {event_id}; source tier remains distinct from official CFL match reports."})
for event_id, (url, _) in TRANSFERMARKT_STARTERS.items():
    SOURCE_ROWS.append({"source_id": f"transfermarkt_starting_xi_user_reviewed_{event_id}", "source_type": "third_party_database_lineup_user_reviewed", "published_at": "", "url": url, "transcription_url": "", "evidence_note": f"Transfermarkt match sheet lists a complete Guoan starting XI for event {event_id}; user manually reviewed and confirmed the data on 2026-09-27. Used as source-tiered third-party evidence, never labelled official."})
SOURCE_ROWS.extend([
    {"source_id": "wikipedia_guoan_2026_squad_profile_2026-09-14", "source_type": "secondary_compiled_squad_profile", "published_at": "2026-09-14", "url": "https://zh.wikipedia.org/wiki/北京国安足球俱乐部2026赛季", "transcription_url": "", "evidence_note": "2026 season article first-team roster table is marked updated 2026-09-14 and lists player birth dates and position labels. Used for profile evidence only, not to establish decision-date squad membership."},
    {"source_id": "national_football_teams_guoan_2026_roster_profiles", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://www.national-football-teams.com/club/437/2026_2/Beijing_Guoan.html", "transcription_url": "", "evidence_note": "2026 Beijing Guoan page lists dates of birth and detailed position labels for 18 players cross-checked here. Secondary profile database; it does not define the project squad cohort."},
    {"source_id": "cfa_youth_athlete_registration_lu_tongyun_2023", "source_type": "official_cfa_youth_athlete_registration_list", "published_at": "2023-06-28", "url": "https://imageoss.thecfa.cn/upload/file/20230628/1687936794968511.pdf", "transcription_url": "", "evidence_note": "Chinese Football Association public youth-athlete register row 45 lists Lu Tongjun with date of birth 2008-03-30; the identifier is partially redacted."},
    {"source_id": "brtv_verified_lineup_post_15551891", "source_type": "verified_broadcaster_social_post_mirror", "published_at": "2026-03-14", "url": "https://www.sina.cn/news/detail/5276379853625238.html", "transcription_url": "", "evidence_note": "Verified BRTV Football 100 post states the match starting lineups and explicitly confirms Zhang Jianzhi started instead of Hou Sen; image's full XI was not transcribed in the text extraction."},
    {"source_id": "csl_verified_lineup_post_15552547", "source_type": "verified_league_social_post_mirror", "published_at": "2026-05-30", "url": "https://www.sina.cn/news/detail/5304345402807057.html", "transcription_url": "", "evidence_note": "Verified Chinese Super League account published the Round 15 starting-lineup graphic for Chongqing Tonglianglong v Beijing Guoan; the image's full XI was not transcribed in the text extraction."},
    {"source_id": "beijing_youth_daily_match_report_15552563", "source_type": "established_newspaper_match_report", "published_at": "2026-07-04", "url": "https://app.bjtitle.com/8816/newshow.php?did=356416815496248&mood=&newsid=6762008&typeid=16&uid=0", "transcription_url": "", "evidence_note": "Beijing Youth Daily's match report independently describes multiple Guoan starters and substitution events, but does not print the complete XI in searchable text."},
    {"source_id": "transfermarkt_guoan_2026_squad", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://www.transfermarkt.com/beijing-guoan/kader/verein/3176/saison_id/2025/plus/1", "transcription_url": "", "evidence_note": "Transfermarkt 2026 detailed squad lists dates of birth for 14 current-profile rows. The new Size Wang Defensive Midfield and Tongyun Lu Goalkeeper labels were retrieved from a search-index excerpt on 2026-09-30; direct page access triggered human verification. Used only for profile attributes, not decision-date membership or match role."},
    {"source_id": "transfermarkt_guoan_u20_squad", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://www.transfermarkt.com/beijing-guoan-u20/kader/verein/93911/saison_id/2025/plus/1", "transcription_url": "", "evidence_note": "Transfermarkt Beijing Guoan U20 detailed squad page independently lists dates of birth for Zicheng Jiang and Haoran Zhang. Used only as a DOB cross-check, not to establish decision-date cohort membership or match role."},
    {"source_id": "transfermarkt_tongyun_lu_profile", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://www.transfermarkt.co.uk/beijing-guoan/startseite/verein/3176/saison_id/2025", "transcription_url": "", "evidence_note": "Transfermarkt Beijing Guoan club profile lists Tongyun Lu date of birth as 2008-03-30. Used to independently cross-check the CFA youth-athlete registration entry; not to establish decision-date cohort membership or match role."},
    {"source_id": "fotmob_luo_zixiang_player_profile", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://www.fotmob.com/players/2092752/zixiang-luo", "transcription_url": "", "evidence_note": "FotMob player profile lists Luo Zixiang date of birth as 2007-12-16. Used only as an independent DOB cross-check, not to establish decision-date cohort membership or match role."},
    {"source_id": "tuttosport_chen_kangyue_profile", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://www.tuttosport.com/giocatore/calcio/kangyue-chen/673154", "transcription_url": "", "evidence_note": "Tuttosport player profile lists Chen Kangyue date of birth as 2008-05-26. Used only as an independent DOB cross-check, not to establish decision-date cohort membership or match role."},
    {"source_id": "sina_liu_junze_player_profile", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://match.sports.sina.com.cn/football/player.php?dpc=1&id=9057656", "transcription_url": "", "evidence_note": "Sina Sports player profile lists Liu Junze date of birth as 2008-04-17. Used only as an independent DOB cross-check, not to establish decision-date cohort membership or match role."},
    {"source_id": "goal_xiaoyu_xia_player_profile", "source_type": "secondary_player_profile_database", "published_at": "", "url": "https://www.goal.com/en-sa/player/x-xia/sEnarSgXdEhTmhC89ehkj", "transcription_url": "", "evidence_note": "Goal.com player profile lists Xiaoyu Xia date of birth as 2007-09-26. Used only as an independent DOB cross-check, not to establish decision-date cohort membership or match role."},
    {"source_id": "starting11_guoan_pohang_2026-09-15", "source_type": "third_party_confirmed_lineup_formation", "published_at": "2026-09-15", "url": "https://starting11.com/fixtures/beijing-guoan-vs-pohang-steelers", "transcription_url": "", "evidence_note": "Starting11 lists the confirmed Beijing Guoan XI in a 4-4-2 with players grouped by formation line for the 2026-09-15 match. Used for match-specific line-unit labels only; no exact left/right/central positions or other matches are inferred."},
    {"source_id": "fotmob_guoan_pohang_2026-09-15", "source_type": "secondary_match_lineup_formation", "published_at": "2026-09-15", "url": "https://www.fotmob.com/matches/beijing-guoan-vs-pohang-steelers/2ymampm", "transcription_url": "", "evidence_note": "FotMob independently lists the confirmed Beijing Guoan XI and 4-4-2 formation for 2026-09-15, cross-checking the formation-line order. Used only for match-specific formation-line roles."},
    {"source_id": "sofascore_lineup_snapshot_16863671", "source_type": "rendered_lineup_snapshot", "published_at": "", "url": "https://www.sofascore.com/football/match/pohang-steelers-beijing-guoan/Brbsadd#id:16863671,tab:lineups", "transcription_url": "", "evidence_note": "Local rendered-lineup snapshot records both formations and starting players by shirt number for event 16863671. Player IDs are unresolved in that raw snapshot; the external Starting11 and FotMob lineups provide the name crosswalk and independently confirm the 4-4-2."},
    {"source_id": "mackolik_guoan_tianjin_2026-08-15", "source_type": "third_party_match_lineup_candidate", "published_at": "2026-08-15", "url": "https://www.mackolik.com/mac/tianjin-jinmen-vs-beijing-guoan/81po1759neralepgwtvnsles4", "transcription_url": "", "evidence_note": "Mackolik lists the 2026-08-15 Guoan starting XI and a 4-4-2 formation. Candidate formation evidence only; another public database lists 4-2-3-1, so this source is not used to assign position groups."},
    {"source_id": "matchcountdown_guoan_tianjin_2026-08-15", "source_type": "third_party_match_lineup_candidate", "published_at": "2026-08-15", "url": "https://matchcountdown.com/en/football/football-169/tianjin-teda-vs-beijing-guoan-2026-08-15", "transcription_url": "", "evidence_note": "MatchCountdown lists the 2026-08-15 Guoan starting XI and a 4-4-2 formation. Candidate formation evidence only; another public database lists 4-2-3-1, so this source is not used to assign position groups."},
    {"source_id": "footmercato_guoan_tianjin_2026-08-15", "source_type": "third_party_match_lineup_candidate", "published_at": "2026-08-15", "url": "https://www.footmercato.net/live/6633794515954937069-tianjin-teda-vs-beijing-guoan", "transcription_url": "", "evidence_note": "Foot Mercato lists the 2026-08-15 Guoan starting XI and a 4-4-2 formation. Candidate formation evidence only; another public database lists 4-2-3-1, so this source is not used to assign position groups."},
    {"source_id": "worldfootball_guoan_tianjin_2026-08-15", "source_type": "third_party_match_lineup_conflict", "published_at": "2026-08-15", "url": "https://www.worldfootball.net/match-report/co1106/china-super-league/ma11909380/tianjin-jinmen-tiger_beijing-guoan/", "transcription_url": "", "evidence_note": "WorldFootball.net lists Beijing Guoan in a 4-2-3-1 for the 2026-08-15 fixture. It conflicts with three other checked public match pages that list 4-4-2; exact formation remains unresolved and no formation-derived roles are assigned."},
    {"source_id": "beijing_youth_daily_tianjin_guoan_2026-08-15", "source_type": "established_newspaper_match_report_mirror", "published_at": "2026-08-15", "url": "https://www.sina.cn/news/detail/5332249459557230.html", "transcription_url": "", "evidence_note": "Beijing Youth Daily Sports report, reposted by Sina, lists Guoan's confirmed XI under goalkeeper/defender/midfielder/forward groups. Used only for these broad match-specific position groups; it does not settle the exact formation."},
])


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def minutes_value(raw: str) -> int | None:
    if not raw:
        return None
    text = raw.strip().replace("′", "'").replace("’", "'").replace("'", "")
    if "+" in text:
        parts = text.split("+", 1)
        if all(p.isdigit() for p in parts):
            return int(parts[0]) + int(parts[1])
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def main() -> None:
    if not STATS.exists():
        raise SystemExit(f"Missing input: {STATS}")
    stats = read_csv(STATS)
    fixtures = read_csv(FIXTURES)
    if not USER_ROSTER_RECONCILIATION.exists():
        raise SystemExit(f"Missing user-provided roster reconciliation: {USER_ROSTER_RECONCILIATION}")
    user_roster_rows = read_csv(USER_ROSTER_RECONCILIATION)
    user_roster_by_name = {r["player_name_zh"]: r for r in user_roster_rows}
    if len(user_roster_by_name) != len(user_roster_rows):
        raise SystemExit("Duplicate player identity in user-provided roster reconciliation")
    transition_rows = read_csv(PUBLIC_TRANSITION_EVIDENCE)
    public_transition_by_name = {r["player_name_zh"]: r for r in transition_rows}
    if len(public_transition_by_name) != len(transition_rows):
        raise SystemExit("Duplicate player identity in public transition evidence")
    registered_source_ids = {r["source_id"] for r in SOURCE_ROWS}
    for transition in transition_rows:
        if transition["player_name_zh"] not in user_roster_by_name:
            raise SystemExit(f"Transition player missing from reconciliation: {transition['player_name_zh']}")
        datetime.strptime(transition["transition_effective_date"], "%Y-%m-%d")
        source_ids = transition["source_ids"].split(";")
        if not source_ids or any(source_id not in registered_source_ids for source_id in source_ids):
            raise SystemExit(f"Unregistered transition source: {transition['player_name_zh']}")
    expected_finished_guoan = {
        r["match_id"] for r in fixtures
        if r.get("status") == "finished"
        and (r.get("home_team") == "Beijing Guoan" or r.get("away_team") == "Beijing Guoan")
    }
    guoan = [r for r in stats if r.get("team_name") == "Beijing Guoan"]
    if not guoan:
        raise SystemExit("No Beijing Guoan rows found in the 2026 player-match dataset")
    observed_guoan_events = {r["match_id"] for r in guoan}
    if observed_guoan_events != expected_finished_guoan:
        raise SystemExit(
            "Guoan player-stat events do not match the canonical finished-fixture set; "
            f"missing={sorted(expected_finished_guoan - observed_guoan_events)}, "
            f"extra={sorted(observed_guoan_events - expected_finished_guoan)}"
        )
    if len({(r["match_id"], r["player_id"]) for r in guoan}) != len(guoan):
        raise SystemExit("Duplicate Guoan player-match rows in the canonical 2026 export")

    registrations: list[dict] = []
    for shirt, name in DOMESTIC_ROSTER:
        registrations.append({"player_name_zh": name, "shirt_number": shirt, "registration_scope": "CSL 2026", "source_id": "guoan_csl_roster_2026-03-03", "registered_on": "2026-03-03", "nominal_position": "", "nominal_position_source": ""})
    for shirt, name, position in CSL_SECOND_WINDOW_ROSTER:
        registrations.append({"player_name_zh": name, "shirt_number": shirt, "registration_scope": "CSL 2026 second-window", "source_id": "guoan_csl_roster_second_window_2026-07-23", "registered_on": "2026-07-23", "nominal_position": position, "nominal_position_source": "guoan_csl_roster_second_window_2026-07-23"})
    for shirt, name in AFC_ROSTER:
        if name not in AFC_POSITION_BY_NAME:
            raise SystemExit(f"Missing AFC roster position group for {name}")
        registrations.append({"player_name_zh": name, "shirt_number": shirt, "registration_scope": "AFC Champions League Elite 2026/27", "source_id": "guoan_acl_roster_2026-09-13", "registered_on": "2026-09-13", "nominal_position": AFC_POSITION_BY_NAME[name], "nominal_position_source": "guoan_acl_roster_transcription_2026-09-13"})

    # Source-level registration evidence is kept as separate rows.
    reg_by_name: dict[str, list[dict]] = defaultdict(list)
    for r in registrations:
        reg_by_name[r["player_name_zh"]].append(r)
    expected_user_reconciled = set(reg_by_name) - {"冯博轩", "魏家傲"}
    if set(user_roster_by_name) != expected_user_reconciled:
        raise SystemExit(
            "User-supplied public-evidence reconciliation does not cover exactly the candidates without the two separately linked public transitions; "
            f"missing={sorted(expected_user_reconciled - set(user_roster_by_name))}, "
            f"extra={sorted(set(user_roster_by_name) - expected_user_reconciled)}"
        )

    player_by_id: dict[str, dict] = {}
    player_ids_by_name: dict[str, set[str]] = defaultdict(set)
    appearances_by_player: dict[str, list[dict]] = defaultdict(list)
    participation_rows: list[dict] = []
    role_evidence_rows: list[dict] = []
    stats_name_to_zh = {k.casefold(): v for k, v in SOFASCORE_TO_ZH.items()}
    unmapped_provider_names = sorted({r["player_name"] for r in guoan if not stats_name_to_zh.get(r["player_name"].casefold())})
    if unmapped_provider_names:
        raise SystemExit(f"Unmapped Guoan provider identities: {unmapped_provider_names}")
    for r in guoan:
        pid = r["player_id"]
        provider_name = r["player_name"]
        zh = stats_name_to_zh.get(provider_name.casefold(), "")
        player_by_id[pid] = {"player_id": pid, "player_name_provider": provider_name, "player_name_zh": zh}
        if zh:
            player_ids_by_name[zh].add(pid)
        appearances_by_player[pid].append(r)
        raw_minutes = r.get("minutes_played", "")
        parsed_minutes = minutes_value(raw_minutes)
        event_id = r["match_id"]
        lineup = OFFICIAL_STARTERS.get(event_id)
        source_tier = "official_cfl_match_report" if lineup else ""
        if not lineup and event_id in SECONDARY_STARTERS:
            secondary_url, secondary_type, secondary_starters = SECONDARY_STARTERS[event_id]
            lineup = (secondary_url, secondary_starters)
            source_tier = f"secondary_public_report:{secondary_type}"
        if not lineup and event_id in TRANSFERMARKT_STARTERS:
            transfermarkt_url, transfermarkt_starters = TRANSFERMARKT_STARTERS[event_id]
            lineup = (transfermarkt_url, transfermarkt_starters)
            source_tier = "third_party_database_lineup_user_reviewed:Transfermarkt"
        started = ""
        started_source = ""
        if lineup:
            source_url, starters = lineup
            if len(starters) != 11 or len(set(starters)) != 11:
                raise SystemExit(f"Invalid source XI for {event_id}: expected 11 unique names")
            if not zh:
                # Keep provider player identities in the row; the source XI
                # crosswalk must resolve before setting a start status.
                started = ""
            else:
                if zh in starters:
                    started = "true"
                else:
                    started = "false"
                started_source = source_url
        started_source_tier = source_tier
        role_evidence = MATCH_ROLE_EVIDENCE.get(event_id, {})
        observed_role = role_evidence.get("roles", {}).get(zh, "")
        if observed_role:
            if started != "true":
                raise SystemExit(f"Role evidence assigned to non-starter in event {event_id}: {zh}")
            role_evidence_rows.append({
                "event_id": event_id, "match_date": r["match_date"], "competition": r["competition"],
                "player_id": pid, "player_name_provider": provider_name, "player_name_zh": zh,
                "formation": role_evidence["formation"], "observed_role": observed_role,
                "role_granularity": role_evidence["role_granularity"],
                "role_evidence_source_ids": role_evidence["source_ids"],
                "limitations": role_evidence["limitations"],
            })
        participation_rows.append({
            "event_id": event_id, "match_date": r["match_date"], "competition": r["competition"],
            "player_id": pid, "player_name_provider": provider_name, "player_name_zh": zh,
            "team_id_or_name": "Beijing Guoan", "participation_status": "appeared_in_player_stats_table",
            "minutes_played_raw": raw_minutes, "minutes_played_numeric": parsed_minutes if parsed_minutes is not None else "",
            "started": started, "started_source": started_source, "started_source_tier": started_source_tier,
            "observed_position_group": r.get("position", ""), "observed_role": observed_role,
            "participation_source": "sofascore_rendered_player_stats", "evidence_timestamp": r.get("observed_at", ""),
            "source_url": r.get("source_url", ""),
        })

    # Check all manually transcribed official starters resolve to the match table.
    for event_id, (url, starters) in OFFICIAL_STARTERS.items():
        event_rows = [r for r in guoan if r["match_id"] == event_id]
        observed_zh = {stats_name_to_zh.get(r["player_name"].casefold(), "") for r in event_rows}
        missing = sorted(set(starters) - observed_zh)
        if missing:
            raise SystemExit(f"Official XI crosswalk failed for event {event_id} ({url}); not in Sofascore rows: {missing}")
    for event_id, (url, source_type, starters) in SECONDARY_STARTERS.items():
        if len(starters) != 11 or len(set(starters)) != 11:
            raise SystemExit(f"Invalid secondary XI for {event_id} ({source_type}): expected 11 unique names")
        event_rows = [r for r in guoan if r["match_id"] == event_id]
        observed_zh = {stats_name_to_zh.get(r["player_name"].casefold(), "") for r in event_rows}
        missing = sorted(set(starters) - observed_zh)
        if missing:
            raise SystemExit(f"Secondary XI crosswalk failed for event {event_id} ({url}); not in Sofascore rows: {missing}")
    for event_id, (url, starters) in TRANSFERMARKT_STARTERS.items():
        if len(starters) != 11 or len(set(starters)) != 11:
            raise SystemExit(f"Invalid Transfermarkt XI for {event_id}: expected 11 unique names")
        event_rows = [r for r in guoan if r["match_id"] == event_id]
        observed_zh = {stats_name_to_zh.get(r["player_name"].casefold(), "") for r in event_rows}
        missing = sorted(set(starters) - observed_zh)
        if missing:
            raise SystemExit(f"Transfermarkt XI crosscheck failed for event {event_id} ({url}); not in Sofascore rows: {missing}")

    names = sorted(reg_by_name)
    roster_rows = []
    usage_rows = []
    position_rows = []
    roles_by_name: dict[str, list[dict]] = defaultdict(list)
    for role_row in role_evidence_rows:
        roles_by_name[role_row["player_name_zh"]].append(role_row)
    for name in names:
        evidence = reg_by_name[name]
        ids = sorted(player_ids_by_name.get(name, set()))
        if len(ids) > 1:
            raise SystemExit(f"Ambiguous identity mapping for {name}: {ids}")
        pid = ids[0] if ids else ""
        scopes = sorted({e["registration_scope"] for e in evidence})
        user_entry = user_roster_by_name.get(name)
        if name == "冯博轩":
            decision_status = "confirmed_transferred_out_2026-07-03"
            status_note = "Dalian Yingbo official announcement confirms permanent joining; not an active Guoan first-team member at decision date."
            membership_confidence = "public_confirmed_transition"
            decision_cohort_member = "false"
            status_source_tier = "public_announcement"
            status_source = "feng_boxuan_transfer_2026-07-03"
            transition_date = "2026-07-03"
            user_detail = {"status": "", "registration": "", "availability": "", "appearance": ""}
        elif name == "魏家傲":
            decision_status = "confirmed_loaned_out_2026-07-03"
            status_note = "Club announcement reports loan to Beijing Institute of Technology through 2026-12-31; exclude from active Guoan first-team snapshot while loan is active."
            membership_confidence = "public_confirmed_transition"
            decision_cohort_member = "false"
            status_source_tier = "public_announcement"
            status_source = "wei_jiaao_loan_2026-07-03"
            transition_date = "2026-07-03"
            user_detail = {"status": "", "registration": "", "availability": "", "appearance": ""}
        elif user_entry:
            is_member = user_entry["reported_first_team_status"] == "active_first_team"
            decision_status = (
                "public_roster_evidence_reconciled_first_team_member_as_of_2026-09-27"
                if is_member else "public_roster_evidence_reconciled_not_in_first_team_as_of_2026-09-27"
            )
            status_note = "User-supplied reconciliation of public roster/registration evidence: " + user_entry["reported_status_detail"]
            membership_confidence = "public_roster_evidence_user_reconciled"
            decision_cohort_member = "true" if is_member else "false"
            status_source_tier = "user_supplied_public_roster_evidence"
            status_source = "user_supplied_public_roster_reconciliation_2026-09-27"
            transition_date = user_entry.get("transition_effective_date", "")
            user_detail = {
                "status": user_entry.get("reported_status_detail", ""),
                "registration": user_entry.get("reported_registration_detail", ""),
                "availability": user_entry.get("reported_availability_detail", ""),
                "appearance": user_entry.get("reported_appearance_detail", ""),
            }
            public_transition = public_transition_by_name.get(name)
            if public_transition:
                if is_member:
                    raise SystemExit(f"Public exit conflicts with active-first-team reconciliation: {name}")
                transition_date = public_transition["transition_effective_date"]
                status_source = public_transition["source_ids"] + ";user_supplied_public_roster_reconciliation_2026-09-27"
                status_source_tier = "public_announcement_and_third_party_profile_index"
                status_note += " Public transition evidence: " + public_transition["evidence_note"]
        elif "CSL 2026 second-window" in scopes and "AFC Champions League Elite 2026/27" in scopes:
            decision_status = "registered_in_CSL_second_window_and_AFC_squad; exact_2026-09-27_membership_pending"
            status_note = "Listed in the 2026-07-23 CSL second-window roster and the 2026-09-13 AFC roster; no complete official roster exactly dated 2026-09-27 located."
            membership_confidence = "pending_public_verification"
            decision_cohort_member = "unknown"
            status_source_tier = "dated_public_registration_only"
            status_source = ";".join(sorted({e["source_id"] for e in evidence}))
            transition_date = ""
            user_detail = {"status": "", "registration": "", "availability": "", "appearance": ""}
        elif "AFC Champions League Elite 2026/27" in scopes:
            decision_status = "registered_in_AFC_squad_as_of_2026-09-13; CSL_second_window_registration_not_evidenced; exact_cutoff_membership_pending"
            status_note = "Listed in the 2026-09-13 AFC-specific roster. Absence from the complete 2026-07-23 CSL roster means CSL registration is not evidenced; it does not establish departure from the club."
            membership_confidence = "pending_public_verification"
            decision_cohort_member = "unknown"
            status_source_tier = "dated_public_registration_only"
            status_source = ";".join(sorted({e["source_id"] for e in evidence}))
            transition_date = ""
            user_detail = {"status": "", "registration": "", "availability": "", "appearance": ""}
        elif "CSL 2026 second-window" in scopes:
            decision_status = "registered_in_CSL_second_window_as_of_2026-07-23; exact_2026-09-27_membership_pending"
            status_note = "Listed in the 2026-07-23 CSL second-window roster. Absence from a competition-specific AFC squad does not establish club departure; exact cut-off membership remains unverified."
            membership_confidence = "pending_public_verification"
            decision_cohort_member = "unknown"
            status_source_tier = "dated_public_registration_only"
            status_source = ";".join(sorted({e["source_id"] for e in evidence}))
            transition_date = ""
            user_detail = {"status": "", "registration": "", "availability": "", "appearance": ""}
        else:
            decision_status = "initial_CSL_roster_only; omitted_from_2026-07-23_CSL_and_2026-09-13_AFC_rosters; exact_cutoff_status_pending"
            status_note = "Present in the 2026-03-03 initial CSL roster but absent from the later complete CSL second-window and AFC lists; omission does not prove release or non-membership."
            membership_confidence = "pending_public_verification"
            decision_cohort_member = "unknown"
            status_source_tier = "dated_public_registration_only"
            status_source = ";".join(sorted({e["source_id"] for e in evidence}))
            transition_date = ""
            user_detail = {"status": "", "registration": "", "availability": "", "appearance": ""}
        rows = appearances_by_player.get(pid, []) if pid else []
        positive_minute_rows = [
            r for r in rows
            if (minutes_value(r.get("minutes_played", "")) or 0) > 0
        ]
        latest_positive_appearance = max(
            positive_minute_rows,
            key=lambda r: (r.get("match_date", ""), r.get("match_id", "")),
            default=None,
        )
        roster_rows.append({
            "player_id": pid, "player_name_zh": name, "player_name_provider": player_by_id.get(pid, {}).get("player_name_provider", ""),
            "team_id": "Beijing Guoan", "membership_scope": "first_team_squad",
            "decision_cohort_member": decision_cohort_member,
            "shirt_numbers_by_source": ";".join(f"{e['registration_scope']}:{e['shirt_number']}" for e in evidence),
            "registration_scopes": ";".join(scopes), "registration_evidence_count": len(evidence),
            "membership_status_as_of_decision_date": decision_status, "membership_status_confidence": membership_confidence,
            "membership_status_note": status_note,
            "membership_status_source_tier": status_source_tier, "membership_status_source": status_source,
            "user_reported_status_detail": user_detail["status"],
            "user_reported_registration_detail": user_detail["registration"],
            "user_reported_availability_detail": user_detail["availability"],
            "user_reported_appearance_detail": user_detail["appearance"],
            "membership_transition_effective_date": transition_date,
            "valid_from": "", "valid_to": "",
            "latest_positive_minutes_match_date": latest_positive_appearance.get("match_date", "") if latest_positive_appearance else "",
            "latest_positive_minutes_event_id": latest_positive_appearance.get("match_id", "") if latest_positive_appearance else "",
            "latest_positive_minutes_competition": latest_positive_appearance.get("competition", "") if latest_positive_appearance else "",
            "latest_positive_minutes_source_url": latest_positive_appearance.get("source_url", "") if latest_positive_appearance else "",
            "decision_date": DECISION_DATE,
        })

        raw_positions = sorted({r.get("position", "") for r in rows if r.get("position")})
        minutes_values = [minutes_value(r.get("minutes_played", "")) for r in rows]
        valid_minutes = [v for v in minutes_values if v is not None]
        competitions = sorted({r.get("competition", "") for r in rows})
        player_participation = [r for r in participation_rows if pid and r["player_id"] == pid]
        start_confirmed = [r for r in player_participation if r["started"] == "true"]
        start_known = [r for r in player_participation if r["started"] in {"true", "false"}]
        start_unknown = [r for r in player_participation if r["started"] == ""]
        usage_rows.append({
            "player_id": pid, "player_name_zh": name, "player_name_provider": player_by_id.get(pid, {}).get("player_name_provider", ""),
            "registration_scopes": ";".join(scopes), "season_stats_appearances": len(rows) if pid else 0,
            "season_minutes_sum_from_displayed_minutes": sum(valid_minutes) if valid_minutes else (0 if pid else ""),
            "source_supported_starts_count_partial": len(start_confirmed),
            "appearance_rows_with_source_supported_start_status": len(start_known),
            "appearance_rows_with_start_status_unknown": len(start_unknown),
            "minutes_parseable_row_count": len(valid_minutes), "competitions_observed": ";".join(competitions),
            "latest_positive_minutes_match_date": latest_positive_appearance.get("match_date", "") if latest_positive_appearance else "",
            "latest_positive_minutes_event_id": latest_positive_appearance.get("match_id", "") if latest_positive_appearance else "",
            "latest_positive_minutes_competition": latest_positive_appearance.get("competition", "") if latest_positive_appearance else "",
            "latest_positive_minutes_source_url": latest_positive_appearance.get("source_url", "") if latest_positive_appearance else "",
            "observed_position_groups": ";".join(raw_positions),
            "appearance_sample_status": "observed_current_season_sample" if rows else "no_current_season_appearance_sample",
            "interpretation": "Stat-table row is appearance evidence; no row means no observed in-scope player-stat sample, not zero performance, non-availability, or proof of non-selection.",
            "membership_status_as_of_decision_date": next(x["membership_status_as_of_decision_date"] for x in roster_rows if x["player_name_zh"] == name),
        })
        position_evidence = [e for e in evidence if e.get("nominal_position")]
        if position_evidence:
            latest_position_date = max(e["registered_on"] for e in position_evidence)
            latest_position_evidence = [e for e in position_evidence if e["registered_on"] == latest_position_date]
            latest_positions = sorted({e["nominal_position"] for e in latest_position_evidence})
            all_positions = sorted({e["nominal_position"] for e in position_evidence})
            if len(latest_positions) == 1:
                nominal_position = latest_positions[0]
                nominal_position_source = ";".join(sorted({e["nominal_position_source"] for e in latest_position_evidence}))
                if len(all_positions) == 1:
                    nominal_position_status = "consistent_registration_position_group"
                elif len(all_positions) > 1:
                    nominal_position_status = "latest_roster_position_group_selected_prior_source_disagreement_retained"
                else:
                    nominal_position_status = "latest_roster_position_group"
            else:
                nominal_position = ""
                nominal_position_source = ";".join(sorted({e["nominal_position_source"] for e in latest_position_evidence}))
                nominal_position_status = "conflicting_latest_registration_position_groups_requires_review"
        else:
            nominal_position = ""
            nominal_position_source = ""
            nominal_position_status = "unknown_no_position_group_in_available_registration_sources"
        player_role_rows = roles_by_name.get(name, [])
        role_fixture_count = len({row["event_id"] for row in player_role_rows})
        role_status = (
            "match_specific_role_evidence_multiple_fixtures" if role_fixture_count > 1
            else "match_specific_role_evidence_one_fixture" if role_fixture_count == 1
            else "unknown_no_role_inferred_from_broad_G_D_M_F_group"
        )
        position_rows.append({
            "player_id": pid, "player_name_zh": name,
            "nominal_position": nominal_position, "nominal_position_source": nominal_position_source, "nominal_position_status": nominal_position_status,
            "observed_position_groups": ";".join(raw_positions), "observed_position_source": "Sofascore player-match General table Position field" if raw_positions else "",
            "observed_role": ";".join(sorted({row["observed_role"] for row in player_role_rows})),
            "observed_role_status": role_status,
        })

    cohort_counts = defaultdict(int)
    for row in roster_rows:
        cohort_counts[(row["membership_status_confidence"], row["decision_cohort_member"])] += 1
    if cohort_counts[("public_roster_evidence_user_reconciled", "true")] != 39:
        raise SystemExit("Expected 39 first-team members reconciled from user-supplied public roster evidence, got " + str(cohort_counts[("public_roster_evidence_user_reconciled", "true")]))
    if cohort_counts[("public_roster_evidence_user_reconciled", "false")] != 4:
        raise SystemExit("Expected 4 non-first-team candidates reconciled from user-supplied public roster evidence, got " + str(cohort_counts[("public_roster_evidence_user_reconciled", "false")]))
    if cohort_counts[("public_confirmed_transition", "false")] != 2:
        raise SystemExit("Expected 2 publicly documented transitions, got " + str(cohort_counts[("public_confirmed_transition", "false")]))
    if any(row["decision_cohort_member"] == "unknown" for row in roster_rows):
        raise SystemExit("Cannot construct operational C2 cohort while any candidate membership remains unknown")

    position_by_name = {row["player_name_zh"]: row for row in position_rows}
    usage_by_name = {row["player_name_zh"]: row for row in usage_rows}
    c2_cohort_rows = []
    for member in roster_rows:
        if member["decision_cohort_member"] != "true":
            continue
        pos = position_by_name[member["player_name_zh"]]
        use = usage_by_name[member["player_name_zh"]]
        c2_cohort_rows.append({
            "decision_date": DECISION_DATE,
            "analysis_status": "pre_gate_operational_snapshot",
            "player_key": f"sofascore:{member['player_id']}" if member["player_id"] else f"roster_name_zh:{member['player_name_zh']}",
            "player_id": member["player_id"],
            "player_identity_resolution_status": "matched_to_sofascore_player_id" if member["player_id"] else "no_current_season_stats_row_or_provider_id",
            "player_name_zh": member["player_name_zh"],
            "player_name_provider": member["player_name_provider"],
            "team_id": member["team_id"],
            "membership_scope": member["membership_scope"],
            "membership_status_source_tier": member["membership_status_source_tier"],
            "membership_status_source": member["membership_status_source"],
            "public_verification_status": "user_identified_public_roster_evidence; exact_item_reference_pending",
            "registration_scopes": member["registration_scopes"],
            "user_reported_registration_detail": member["user_reported_registration_detail"],
            "user_reported_availability_detail": member["user_reported_availability_detail"],
            "user_reported_appearance_detail": member["user_reported_appearance_detail"],
            "nominal_position": pos["nominal_position"],
            "nominal_position_source": pos["nominal_position_source"],
            "observed_position_groups": use["observed_position_groups"],
            "season_stats_appearances": use["season_stats_appearances"],
            "stats_sample_status": use["appearance_sample_status"],
            "season_minutes_sum_from_displayed_minutes": use["season_minutes_sum_from_displayed_minutes"],
            "source_supported_starts_count_partial": use["source_supported_starts_count_partial"],
            "competitions_observed": use["competitions_observed"],
            "latest_positive_minutes_match_date": member["latest_positive_minutes_match_date"],
            "latest_positive_minutes_event_id": member["latest_positive_minutes_event_id"],
            "source_limitations": "Membership follows public roster/registration evidence supplied by the user; exact item-level source references are not yet attached in this workspace, and exact membership interval dates remain unrecorded where unknown.",
        })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "public_source_register.csv", SOURCE_ROWS, ["source_id", "source_type", "published_at", "url", "transcription_url", "evidence_note"])
    write_csv(OUTPUT / "squad_registration_evidence_2026.csv", registrations, ["player_name_zh", "shirt_number", "registration_scope", "source_id", "registered_on", "nominal_position", "nominal_position_source"])
    write_csv(OUTPUT / "squad_membership_decision_snapshot_2026-09-27.csv", roster_rows, ["player_id", "player_name_zh", "player_name_provider", "team_id", "membership_scope", "decision_cohort_member", "shirt_numbers_by_source", "registration_scopes", "registration_evidence_count", "membership_status_as_of_decision_date", "membership_status_confidence", "membership_status_note", "membership_status_source_tier", "membership_status_source", "user_reported_status_detail", "user_reported_registration_detail", "user_reported_availability_detail", "user_reported_appearance_detail", "membership_transition_effective_date", "valid_from", "valid_to", "latest_positive_minutes_match_date", "latest_positive_minutes_event_id", "latest_positive_minutes_competition", "latest_positive_minutes_source_url", "decision_date"])
    write_csv(OUTPUT / "c2_operational_cohort_2026-09-27.csv", c2_cohort_rows, ["decision_date", "analysis_status", "player_key", "player_id", "player_identity_resolution_status", "player_name_zh", "player_name_provider", "team_id", "membership_scope", "membership_status_source_tier", "membership_status_source", "public_verification_status", "registration_scopes", "user_reported_registration_detail", "user_reported_availability_detail", "user_reported_appearance_detail", "nominal_position", "nominal_position_source", "observed_position_groups", "season_stats_appearances", "stats_sample_status", "season_minutes_sum_from_displayed_minutes", "source_supported_starts_count_partial", "competitions_observed", "latest_positive_minutes_match_date", "latest_positive_minutes_event_id", "source_limitations"])
    write_csv(OUTPUT / "player_match_participation_2026_guoan.csv", participation_rows, ["event_id", "match_date", "competition", "player_id", "player_name_provider", "player_name_zh", "team_id_or_name", "participation_status", "minutes_played_raw", "minutes_played_numeric", "started", "started_source", "started_source_tier", "observed_position_group", "observed_role", "participation_source", "evidence_timestamp", "source_url"])
    write_csv(OUTPUT / "match_role_evidence_2026_guoan.csv", role_evidence_rows, ["event_id", "match_date", "competition", "player_id", "player_name_provider", "player_name_zh", "formation", "observed_role", "role_granularity", "role_evidence_source_ids", "limitations"])
    write_csv(OUTPUT / "player_season_usage_2026_guoan.csv", usage_rows, ["player_id", "player_name_zh", "player_name_provider", "registration_scopes", "season_stats_appearances", "season_minutes_sum_from_displayed_minutes", "source_supported_starts_count_partial", "appearance_rows_with_source_supported_start_status", "appearance_rows_with_start_status_unknown", "minutes_parseable_row_count", "competitions_observed", "latest_positive_minutes_match_date", "latest_positive_minutes_event_id", "latest_positive_minutes_competition", "latest_positive_minutes_source_url", "observed_position_groups", "appearance_sample_status", "interpretation", "membership_status_as_of_decision_date"])
    write_csv(OUTPUT / "player_position_evidence_2026_guoan.csv", position_rows, ["player_id", "player_name_zh", "nominal_position", "nominal_position_source", "nominal_position_status", "observed_position_groups", "observed_position_source", "observed_role", "observed_role_status"])

    lineup_audit = []
    for event_id, (url, starters) in OFFICIAL_STARTERS.items():
        event_rows = [r for r in participation_rows if r["event_id"] == event_id]
        confirmed = [r for r in event_rows if r["started"] == "true"]
        lineup_audit.append({"event_id": event_id, "official_report_url": url, "official_xi_count": len(starters), "xi_names_resolved_to_stats_rows": len(confirmed), "nonstarter_appearances_classified": sum(r["started"] == "false" for r in event_rows), "status": "pass" if len(confirmed) == 11 else "fail"})
    write_csv(OUTPUT / "official_starting_xi_audit_2026_guoan.csv", lineup_audit, ["event_id", "official_report_url", "official_xi_count", "xi_names_resolved_to_stats_rows", "nonstarter_appearances_classified", "status"])

    secondary_lineup_audit = []
    for event_id, (url, source_type, starters) in SECONDARY_STARTERS.items():
        event_rows = [r for r in participation_rows if r["event_id"] == event_id]
        confirmed = [r for r in event_rows if r["started"] == "true"]
        secondary_lineup_audit.append({"event_id": event_id, "secondary_source_type": source_type, "secondary_source_url": url, "xi_count": len(starters), "xi_names_resolved_to_stats_rows": len(confirmed), "nonstarter_appearances_classified": sum(r["started"] == "false" for r in event_rows), "status": "pass" if len(confirmed) == 11 else "fail"})
    write_csv(OUTPUT / "secondary_starting_xi_audit_2026_guoan.csv", secondary_lineup_audit, ["event_id", "secondary_source_type", "secondary_source_url", "xi_count", "xi_names_resolved_to_stats_rows", "nonstarter_appearances_classified", "status"])

    transfermarkt_lineup_audit = []
    for event_id, (url, starters) in TRANSFERMARKT_STARTERS.items():
        event_rows = [r for r in guoan if r["match_id"] == event_id]
        observed_zh = {stats_name_to_zh.get(r["player_name"].casefold(), "") for r in event_rows}
        resolved = sorted(set(starters) & observed_zh)
        transfermarkt_lineup_audit.append({
            "event_id": event_id, "transfermarkt_source_url": url,
            "transfermarkt_xi_names": ";".join(starters),
            "xi_count": len(starters), "xi_names_resolved_to_stats_rows": len(resolved),
            "missing_xi_names": ";".join(sorted(set(starters) - observed_zh)),
            "user_review_status": "confirmed_correct_by_user_2026-09-27",
            "nonstarter_appearances_classified": sum(r["started"] == "false" for r in participation_rows if r["event_id"] == event_id),
            "started_status_decision": "apply_user_reviewed_transfermarkt_xi_with_third_party_tier",
            "status": "pass_crosswalk_and_user_review" if len(resolved) == 11 else "fail",
        })
    write_csv(OUTPUT / "transfermarkt_starting_xi_crosscheck_2026_guoan.csv", transfermarkt_lineup_audit, ["event_id", "transfermarkt_source_url", "transfermarkt_xi_names", "xi_count", "xi_names_resolved_to_stats_rows", "missing_xi_names", "user_review_status", "nonstarter_appearances_classified", "started_status_decision", "status"])

    counts = defaultdict(int)
    for r in roster_rows:
        counts[r["membership_status_confidence"]] += 1
    summary = {
        "decision_date": DECISION_DATE,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "registration_evidence_rows": len(registrations),
        "unique_registration_candidates": len(roster_rows),
        "csl_2026_registered_candidates": len(DOMESTIC_ROSTER),
        "csl_2026_second_window_registered_candidates": len(CSL_SECOND_WINDOW_ROSTER),
        "acl_2026_27_registered_candidates": len(AFC_ROSTER),
        "nominal_position_groups_from_later_registration_sources": sum(bool(r["nominal_position"]) for r in position_rows),
        "nominal_position_unknown_candidates": sum(not bool(r["nominal_position"]) for r in position_rows),
        "candidates_with_observed_positive_minutes": sum(bool(r["latest_positive_minutes_match_date"]) for r in roster_rows),
        "latest_positive_minutes_observation_date": max((r["latest_positive_minutes_match_date"] for r in roster_rows if r["latest_positive_minutes_match_date"]), default=""),
        "candidates_without_observed_positive_minutes": sum(not bool(r["latest_positive_minutes_match_date"]) for r in roster_rows),
        "unique_guoan_stats_players_2026": len(appearances_by_player),
        "player_match_participation_rows": len(participation_rows),
        "completed_guoan_in_scope_fixtures": len(expected_finished_guoan),
        "guoan_player_stats_fixture_coverage": f"{len(observed_guoan_events)}/{len(expected_finished_guoan)}",
        "official_match_reports_with_starting_xi": len(OFFICIAL_STARTERS),
        "official_starting_xi_audit_passed": sum(x["status"] == "pass" for x in lineup_audit),
        "secondary_public_reports_with_starting_xi": len(SECONDARY_STARTERS),
        "secondary_starting_xi_audit_passed": sum(x["status"] == "pass" for x in secondary_lineup_audit),
        "fixtures_with_starting_xi_evidence_total": len(set(OFFICIAL_STARTERS) | set(SECONDARY_STARTERS) | set(TRANSFERMARKT_STARTERS)),
        "transfermarkt_xi_crosschecks_found": len(TRANSFERMARKT_STARTERS),
        "transfermarkt_xi_crosschecks_resolved_to_player_stats_rows": sum(x["status"] == "pass_crosswalk_and_user_review" for x in transfermarkt_lineup_audit),
        "transfermarkt_xi_user_reviewed": sum(x["user_review_status"] == "confirmed_correct_by_user_2026-09-27" for x in transfermarkt_lineup_audit),
        "fixtures_with_starting_xi_evidence_in_decision_layer": len(set(OFFICIAL_STARTERS) | set(SECONDARY_STARTERS) | set(TRANSFERMARKT_STARTERS)),
        "decision_date_publicly_confirmed_transitions": sum(x["membership_status_confidence"] == "public_confirmed_transition" for x in roster_rows),
        "decision_date_first_team_members_reconciled_from_user_supplied_public_evidence": sum(x["decision_cohort_member"] == "true" and x["membership_status_confidence"] == "public_roster_evidence_user_reconciled" for x in roster_rows),
        "decision_date_candidates_reconciled_out_of_first_team_from_user_supplied_public_evidence": sum(x["decision_cohort_member"] == "false" and x["membership_status_confidence"] == "public_roster_evidence_user_reconciled" for x in roster_rows),
        "user_reconciled_exits_with_publicly_sourced_transition_date": len(public_transition_by_name),
        "decision_date_membership_pending_public_verification": sum(x["membership_status_confidence"] == "pending_public_verification" for x in roster_rows),
        "provisional_c2_operational_cohort_rows": len(c2_cohort_rows),
        "provisional_c2_nominal_position_unknown": sum(not bool(row["nominal_position"]) for row in c2_cohort_rows),
        "provisional_c2_public_source_traceability_limitation": "The user states the 39-person cohort and four exclusions were reconciled from public roster/registration evidence. Exact item-level public source references are not yet attached to every reconciliation row in this workspace.",
        "active_first_team_members_with_positive_minutes": sum(x["decision_cohort_member"] == "true" and bool(x["latest_positive_minutes_match_date"]) for x in roster_rows),
        "active_first_team_members_without_positive_minutes": sum(x["decision_cohort_member"] == "true" and not bool(x["latest_positive_minutes_match_date"]) for x in roster_rows),
        "limitations": [
            "The registration union is a 45-person evidence candidate universe. The 2026-09-27 cohort has 39 first-team members and 4 exclusions reconciled from public roster/registration evidence supplied by the user; two further exits are supported by linked public announcements. User-supplied public evidence is not classified as non-public operational information.",
            "The July 23 CSL registration is a verified club image post whose names and broad position groups are transcribed by a secondary report; the evidence ledger preserves both links and the source tier.",
            "The September AFC roster is competition-specific. Neither its inclusions nor omissions alone prove domestic registration or club departure.",
            "The exact 2026-09-27 cohort is reconciled from public roster/registration evidence supplied by the user. Exact public source links or artifact references are not yet attached to each of the 43 status rows in the local ledger; this is a traceability gap, not evidence that the information is private or non-public.",
            "Jiang Wenhao's loan joined date is recorded from an indexed Transfermarkt profile and corroborated by the receiving club announcement mirror. The other three user-reported loans/U20 reassignments lack exact transition dates; valid_from/valid_to intervals remain blank rather than inferred from registration or announcement dates.",
            "Competition registration is recorded separately from first-team membership and player availability. Injury, CSL/AFC scope, and no-appearance notes are retained as details transcribed from public materials by the user; exact source links should be associated with the relevant row when available.",
            "A positive-minute match row documents participation for Guoan on that match date only; the latest such date does not by itself prove continued club membership on 2026-09-27.",
            "Official CFL starting XIs, public secondary reports, and user-reviewed Transfermarkt lineups remain distinctly source-tiered; no third-party source is labelled official.",
            "Transfermarkt XIs for events 15551891, 15552547, and 15552563 were manually reviewed and confirmed by the user on 2026-09-27; all 33 names resolve to Sofascore participant rows and source-backed started status is now included for those events.",
            "Nominal position is the broad goalkeeper/defender/midfielder/forward category transcribed from later registration sources. Sofascore G/D/M/F remains separate as an observed match-table group; neither is converted to a functional role.",
            "No absent-player match status is inferred from a missing Sofascore statistics row.",
        ],
    }
    (OUTPUT / "c1_snapshot_build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
