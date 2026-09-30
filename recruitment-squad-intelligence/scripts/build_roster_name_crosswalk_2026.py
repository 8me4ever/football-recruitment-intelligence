"""Build a source-labelled name crosswalk for the frozen 2026-09-27 Guoan cohort.

The three provider lists below are transcriptions of public, mutable pages
retrieved on 2026-09-30. Presence is identity evidence, not cut-off membership.
"""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/csl/decision_snapshot_2026-09-27"
MEMBERSHIP = DATA / "squad_membership_decision_snapshot_2026-09-27.csv"
REGISTRATION = DATA / "squad_registration_evidence_2026.csv"
SOURCES = DATA / "public_source_register.csv"
OUT = DATA / "roster_name_crosswalk_2026-09-30.csv"
UNMATCHED = DATA / "roster_unmatched_provider_names_2026-09-30.csv"

TM_URL = "https://www.transfermarkt.com/beijing-guoan/kader/verein/3176/saison_id/2025/plus/1"
SOFA_URL = "https://www.sofascore.com/football/team/beijing-guoan/3376"
WHO_URL = "https://www.whoscored.com/teams/2540/show/china-beijing-guoan"

# Chinese name | Transfermarkt | Sofascore | WhoScored | WhoScored player ID
NAMES = """何宇鹏|Yupeng He|Yupeng He|He Yupeng|372652
侯森|Sen Hou|Hou Sen|Hou Sen|62293
冯博轩|Boxuan Feng||Feng Boxuan|341643
刘俊泽||Junze Liu||
刘邵子洋|Shaoziyang Liu|Shaoziyang Liu||
努尔艾力·阿巴斯|Nureli Abbas|Nureli Abbas||
卢彤鋆|Tongyun Lu|Tongyun Lu||
吴少聪|Shaocong Wu|Wu Shaocong||
塞尔吉尼奥|Serginho|Sai Erjini'ao|Sai Erjini'ao|149142
夏晓雨||Xiaoyu Xia||
孔特|Boubacar Konté|Aboubacar Konte|Boubacar Konté|377475
张健智|Jianzhi Zhang||Zhang Jianzhi|402857
张昊冉||Haoran Zhang||
张玉宁|Yuning Zhang|Zhang Yuning|Zhang Yuning|303136
张稀哲|Xizhe Zhang|Zhang Xizhe|Zhang Xizhe|279458
恩科洛洛|Béni Nkololo|Béni Nkololo|Béni Nkololo|315270
拉莫斯|Gui Ramos|Guilherme Ramos|Guilherme Ramos|422719
斯帕伊奇|Uros Spajic|Uroš Spajić|Uros Spajic|127920
曹永竞|Yongjing Cao|Yongjing Cao|Cao Yongjing|353924
李磊|Lei Li|Li Lei|Li Lei|72519
杜齐亚克||Jeremy Dudziak||
杨立瑜|Liyu Yang|Yang Liyu|Yang Liyu|334453
林涵祺|Hanqi Lin|Lin Hanqi||
林良铭|Liangming Lin|Lin Liangming|Lin Liangming|396726
柏杨|Yang Bai|Yang Bai|Yang Bai|414131
江文豪|Wenhao Jiang||Wenhao Jiang|413833
池忠国|Zhongguo Chi|Chi Zhongguo|Chi Zhongguo|271454
法比奥|Fabio Abreu|Fabio Abreu|Fábio Abreu|142269
王刚|Gang Wang|Gang Wang|Wang Gang|353926
王思泽|Size Wang|Wang Size||
王禹|Yu Wang|Wang Yu|Yu Wang|419656
程熙|Xi Cheng|Cheng Xi|Xi Cheng|612253
罗子祥||Zixiang Luo||
范双杰|Shuangjie Fan|Shuangjie Fan|Shuangjie Fan|539618
茹子楠|Tze-Nam Yue|Tze-Nam Yue|Tze-Nam Yue|391485
蒋子承||Zicheng Jiang|Zicheng Jiang|639738
贾非凡|Feifan Jia|Feifan Jia|Feifan Jia|426554
达万|Dawhan|Dawhan|Dawhan|363306
邓捷夫|Jiefu Deng|Deng Jiefu|Jiefu Deng|611623
阿不都海米提|Abduhamit Abdugheni|Abdugheni Abduhamit|Abduhamit Abdugheni|354046
阿科洛||Chadrac Akolo||
陈康悦||Kangyue Chen||
韩佳奇|Jiaqi Han|Han Jiaqi||
马名扬|Mingyang Ma|Ma Mingyang||
魏家傲|Jia'ao Wei||Jiaao Wei|568217"""

WHO_SLUGS = {
    "塞尔吉尼奥": "sai-erjini-39-ao",
    "孔特": "boubacar-kont%C3%A9",
    "恩科洛洛": "b%C3%A9ni-nkololo",
    "法比奥": "f%C3%A1bio-abreu",
}

TM_PROFILE_URLS = {
    "刘邵子洋": "https://www.transfermarkt.com/shaoziyang-liu/profil/spieler/966946",
}

UNMATCHED_SOFA = [
    ("Wang Zihao", "No reliable match in the 45-person decision candidate universe"),
    ("Yu Wang", "Sofascore also lists Wang Yu; do not merge this second string with 王禹 without a player ID"),
    ("Shanghan Li", "No reliable match in the 45-person decision candidate universe"),
    ("Arturo Cheng", "No reliable match in the 45-person decision candidate universe"),
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    membership = read_csv(MEMBERSHIP)
    registrations = read_csv(REGISTRATION)
    source_urls = {r["source_id"]: r["url"] for r in read_csv(SOURCES)}
    registration_sources = {}
    for registration in registrations:
        registration_sources.setdefault(registration["player_name_zh"], set()).add(registration["source_id"])
    by_name = {r["player_name_zh"]: r for r in membership}
    entries = [line.split("|") for line in NAMES.splitlines()]
    names = [entry[0] for entry in entries]
    if len(names) != len(set(names)) or set(names) != set(by_name):
        raise SystemExit("Crosswalk and frozen candidate universe do not match")

    rows = []
    for name, tm, sofa, who, who_id in entries:
        cohort = by_name[name]
        official_ids = sorted(registration_sources.get(name, set()))
        slug = WHO_SLUGS.get(name, who.lower().replace(" ", "-").replace("'", "-")) if who else ""
        rows.append({
            "player_name_zh": name,
            "player_id_sofascore_existing": cohort["player_id"],
            "decision_cohort_member_2026-09-27": cohort["decision_cohort_member"],
            "registration_scopes": cohort["registration_scopes"],
            "registration_source_ids": ";".join(official_ids),
            "registration_source_urls": ";".join(source_urls[source_id] for source_id in official_ids),
            "transfermarkt_name_as_listed": tm,
            "transfermarkt_source_url": TM_PROFILE_URLS.get(name, TM_URL if tm else ""),
            "sofascore_name_as_listed": sofa,
            "sofascore_source_url": SOFA_URL if sofa else "",
            "whoscored_name_as_listed": who,
            "whoscored_player_url": f"https://www.whoscored.com/players/{who_id}/show/{slug}" if who_id else "",
            "whoscored_team_source_url": WHO_URL if who else "",
            "retrieved_on": "2026-09-30",
            "evidence_scope": "provider_name_presence_only;not_decision_date_membership_proof",
        })
    write_csv(OUT, rows, list(rows[0]))
    if any(not (r["transfermarkt_name_as_listed"] or r["sofascore_name_as_listed"] or r["whoscored_name_as_listed"]) for r in rows):
        raise SystemExit("One or more candidate identities have no provider cross-check")
    write_csv(UNMATCHED, [
        {"provider": "Sofascore", "name_as_listed": name, "source_url": SOFA_URL,
         "retrieved_on": "2026-09-30", "resolution_status": "unmatched_or_ambiguous",
         "note": note} for name, note in UNMATCHED_SOFA
    ], ["provider", "name_as_listed", "source_url", "retrieved_on", "resolution_status", "note"])
    counts = {site: sum(bool(r[site]) for r in rows) for site in
              ("transfermarkt_name_as_listed", "sofascore_name_as_listed", "whoscored_name_as_listed")}
    print(f"45 candidate identities; source presences: {counts}; 4 unmatched Sofascore strings")


if __name__ == "__main__":
    main()
