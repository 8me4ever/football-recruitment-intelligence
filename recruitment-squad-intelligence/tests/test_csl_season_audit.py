import unittest

from scripts.audit_csl_season import audit


def fixture(match_id="m1"):
    return {"match_id": match_id, "match_date": "2025-02-22", "home_team": "A", "away_team": "B",
            "home_goals": "0", "away_goals": "0", "round": "1", "status": "finished",
            "source": "licensed_export", "source_url": "https://example.test/m1", "observed_on": "2026-09-25"}


def appearance(match_id="m1", player_id="p1"):
    return {"source": "licensed_export", "match_id": match_id, "player_id": player_id}


class SeasonAuditTests(unittest.TestCase):
    def test_complete_fixture_and_player_coverage(self):
        result = audit([fixture()], [appearance()], expected_matches=1)
        self.assertTrue(result["complete"])
        self.assertEqual(result["matches_with_player_rows"], 1)

    def test_empty_player_match_is_reported(self):
        result = audit([fixture()], [], expected_matches=1)
        self.assertFalse(result["complete"])
        self.assertEqual(result["matches_without_player_rows"], 1)

    def test_duplicate_and_orphan_rows_fail(self):
        result = audit([fixture()], [appearance(), appearance(), appearance("unknown", "p2")], expected_matches=1)
        self.assertFalse(result["complete"])
        self.assertTrue(any("duplicate source/match/player" in issue for issue in result["issues"]))
        self.assertTrue(any("absent from manifest" in issue for issue in result["issues"]))

    def test_missing_expected_fixture_count_fails(self):
        result = audit([fixture()], [appearance()], expected_matches=2)
        self.assertFalse(result["complete"])
        self.assertTrue(any("expected 2" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
