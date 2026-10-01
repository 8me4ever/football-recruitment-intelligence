"""Extract visible lineup and substitute cards from a Scrapling page snapshot.

Only rendered DOM is read. The source HTML must be a saved match page whose
Lineups tab was visibly loaded; no embedded state or network API is parsed.
"""

import argparse
import json
import re
from pathlib import Path

from lxml import html


PLAYER_ID = re.compile(r"/player/(\d+)/image")


def text(element):
    return " ".join(element.text_content().split())


def image_player_id(element):
    for image in element.xpath('.//img[contains(@src, "/player/")]'):
        match = PLAYER_ID.search(image.get("src", ""))
        if match:
            return match.group(1)
    return None


def timeline_substitutions(tree):
    """Read substitution icons and adjacent player links from visible event cards."""
    events = []
    cards = tree.xpath('//div[contains(@class,"hover:bg_surface.s2") and '
                       'contains(@class,"cursor_pointer")][.//bdi and '
                       './/a[contains(@href,"/football/player/")]]')
    for card in cards:
        links = card.xpath('.//a[contains(@href,"/football/player/")]')
        if len(links) != 2:
            continue
        fills = card.xpath('.//path/@fill')
        is_substitution = (any("status-error" in fill for fill in fills) and
                           any("status-success" in fill for fill in fills))
        is_substitution |= "Substitution" in text(card)
        if not is_substitution:
            continue
        minute_nodes = card.xpath('.//bdi[1]')
        if len(minute_nodes) != 1:
            continue
        minute_display = text(minute_nodes[0])
        minute_match = re.fullmatch(r"(\d+)'(?:\s*\+(\d+))?", minute_display)
        if not minute_match:
            continue
        events.append({
            "incoming_player_id": links[0].get("href", "").rstrip("/").split("/")[-1],
            "outgoing_player_id": links[1].get("href", "").rstrip("/").split("/")[-1],
            "incoming_timeline_name": text(links[0]),
            "outgoing_timeline_name": text(links[1]),
            "minute_timeline_display": minute_display,
            "minute_base": int(minute_match.group(1)),
            "stoppage_minute": int(minute_match.group(2)) if minute_match.group(2) else 0,
        })
    return events


def extract(path, event_id):
    tree = html.fromstring(path.read_text(encoding="utf-8"))
    title = text(tree.xpath("//title")[0]) if tree.xpath("//title") else ""
    if "verification" in title.lower() or "captcha" in title.lower():
        raise ValueError("Verification page; stop collection")

    formation_nodes = tree.xpath('//span[re:match(normalize-space(.), "^[3-5]-[0-9-]+$")]',
                                 namespaces={"re": "http://exslt.org/regular-expressions"})
    lineup = None
    for node in formation_nodes:
        ancestor = node.xpath('ancestor::div[contains(@class, "flex-wrap_wrap")][1]')
        if ancestor and len(ancestor[0].xpath('./div[contains(@class, "FootballTerrainHalf__root")]')) == 2:
            lineup = ancestor[0]
            break
    if lineup is None:
        raise ValueError("Rendered Lineups terrain is absent")

    headers = [child for child in lineup if "FootballTerrainHalf__root" not in child.get("class", "")]
    terrains = [child for child in lineup if "FootballTerrainHalf__root" in child.get("class", "")]
    if len(headers) != 2 or len(terrains) != 2:
        raise ValueError("Expected two team headers and two visible lineup terrains")

    # The visible page renders header, terrain, terrain, header in left/right order.
    teams = []
    for header, terrain in zip(headers, terrains):
        labels = [text(x) for x in header.xpath('.//span') if text(x)]
        formation = next((x for x in labels if re.fullmatch(r"[3-5](?:-\d+)+", x)), None)
        team_name = labels[0] if labels else None
        jersey_urls = header.xpath('.//img[contains(@src, "/event/")]/@src')
        if not jersey_urls or not all(f"/event/{event_id}/" in url for url in jersey_urls):
            raise ValueError(f"Visible lineup jersey does not match requested event {event_id}")
        if not team_name or not formation:
            raise ValueError(f"Could not read team and formation from visible header: {labels}")
        players = []
        inner = terrain.xpath('./div[contains(@class, "FootballTerrainHalf__inner")]')
        if len(inner) != 1:
            raise ValueError(f"No visible formation lines for {team_name}")
        for line_index, line in enumerate(inner[0], start=1):
            cards = line.xpath('./div/div')
            for slot_index, card in enumerate(cards, start=1):
                player_id = image_player_id(card)
                name_nodes = card.xpath('.//span[contains(@class, "c_onColor.primary") and contains(@class, "ta_center")]')
                if not player_id or not name_nodes:
                    raise ValueError(f"Unresolved starter card in {team_name} line {line_index}")
                name_node = name_nodes[-1]
                shirt = "".join(name_node.xpath('./span/text()')).strip()
                display_name = "".join(name_node.xpath('./text()')).strip()
                captain = display_name.startswith("(c) ")
                display_name = display_name.removeprefix("(c) ")
                players.append({"player_id": player_id, "display_name": display_name,
                                "shirt_number": shirt, "captain": captain, "formation_line": line_index,
                                "slot_in_line": slot_index,
                                "position_semantics": "nominal_visible_formation_slot"})
        if len(players) != 11 or len({p["player_id"] for p in players}) != 11:
            raise ValueError(f"Expected 11 unique starters for {team_name}; got {len(players)}")
        teams.append({"team": team_name, "formation": formation, "starters": players})

    headings = tree.xpath('//*[normalize-space(text())="Substitutions"]')
    if len(headings) != 1:
        raise ValueError("Expected one visible Substitutions heading")
    section = headings[0].xpath('ancestor::div[contains(@class, "card-component")][1]')[0]
    columns = section.xpath('./div[contains(@class, "d_flex")]/div[contains(@class, "flex-b_1/2")]')
    if len(columns) != 2:
        raise ValueError("Expected two substitute columns")
    for team, column in zip(teams, columns):
        bench = []
        for anchor in column.xpath('./a[contains(@href, "/football/player/")]'):
            player_id = anchor.get("href", "").rstrip("/").split("/")[-1]
            named = anchor.xpath('.//div[@title]')
            if len(named) != 1:
                raise ValueError(f"Ambiguous bench name in {team['team']}")
            name = named[0].get("title")
            shirt = "".join(named[0].xpath('.//bdi/text()')).strip()
            minute = anchor.xpath('.//span[contains(@class, "c_secondary.default")]/text()')
            out = anchor.xpath('.//span[contains(@class, "c_neutrals.nLv3") and contains(text(), "Out:")]/text()')
            bench.append({"player_id": player_id, "display_name": name,
                          "shirt_number": shirt, "substitution_minute_display": minute[0].strip() if minute else None,
                          "out_display_name": out[0].replace("Out:", "").strip() if out else None,
                          "appeared_as_substitute": bool(minute)})
        if not bench or len({p["player_id"] for p in bench}) != len(bench):
            raise ValueError(f"Missing or duplicate bench players for {team['team']}")
        team["bench"] = bench

    timeline_events = timeline_substitutions(tree)
    for team in teams:
        roster_ids = {player["player_id"] for player in team["starters"] + team["bench"]}
        substitutions = []
        for player in team["bench"]:
            if not player["appeared_as_substitute"]:
                continue
            candidates = [event for event in timeline_events
                          if event["incoming_player_id"] == player["player_id"]
                          and event["outgoing_player_id"] in roster_ids]
            if len(candidates) != 1:
                raise ValueError(f"Expected one visible timeline event for {team['team']} "
                                 f"substitute {player['display_name']}; got {len(candidates)}")
            event = dict(candidates[0])
            event["minute_card_display"] = player["substitution_minute_display"]
            event["minute_surfaces_differ"] = (
                event["minute_card_display"] != event["minute_timeline_display"])
            substitutions.append(event)
        team["substitution_events"] = substitutions
    return {"event_id": event_id, "source_html": str(path), "page_title": title,
            "source_method": "Scrapling-rendered visible DOM snapshot", "teams": teams}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = extract(args.html, args.event_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "teams": [t["team"] for t in result["teams"]],
                      "starters": [len(t["starters"]) for t in result["teams"]],
                      "bench": [len(t["bench"]) for t in result["teams"]],
                      "substitution_events": [len(t["substitution_events"])
                                              for t in result["teams"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
