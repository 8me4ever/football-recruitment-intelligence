"""Regression checks for observed source-format hazards; standard library only."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("csl_pilot", ROOT / "scripts/validate_csl_pilot.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "data/csl/pilot/general_table_samples.json").read_text(encoding="utf-8"))

    def test_blank_is_not_zero(self):
        self.assertIsNone(module.count(""))
        self.assertEqual(module.count("0"), 0)
        self.assertEqual(module.pair("0 (0)"), {"total": 0, "successful": 0})
        self.assertIsNone(module.pair("")["total"])

    def test_attempts_successes_and_rounding(self):
        self.assertEqual(module.passes("29/32 (91%)")["completed"], 29)
        self.assertEqual(module.pair("23 (10)")["successful"], 10)
        self.assertIsNone(module.pair("1")["successful"])
        for value in ["33/32 (100%)", "29/32 (70%)"]:
            with self.assertRaises(ValueError):
                module.passes(value)
        with self.assertRaises(ValueError):
            module.pair("2 (3)")

    def test_preserve_provider_minutes_and_position_changes(self):
        rows = module.normalize(self.data)
        self.assertEqual(len(rows), 12)
        sub = next(r for r in rows if r["match_id"] == "13400350" and r["player_id"] == "828227")
        self.assertEqual(sub["minutes_provider"], 18)
        self.assertEqual(sub["minutes_convention"], "unverified")
        self.assertEqual({r["position_coarse"] for r in rows if r["player_id"] == "817886"}, {"F", "M"})

    def test_duplicate_rejected(self):
        self.data["matches"][0]["rows"].append(copy.deepcopy(self.data["matches"][0]["rows"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            module.normalize(self.data)

    def test_wrong_match_url_rejected(self):
        self.data["matches"][0]["match_id"] = "999"
        with self.assertRaisesRegex(ValueError, "identity"):
            module.normalize(self.data)

    def test_schema_drift_rejected(self):
        self.data["columns"][2:4] = ["assists", "goals"]
        with self.assertRaisesRegex(ValueError, "schema"):
            module.normalize(self.data)


if __name__ == "__main__":
    unittest.main()
