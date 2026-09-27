from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collection_failure import classify_collection_failure  # noqa: E402


def test_failure_statuses_cover_c0_taxonomy() -> None:
    assert classify_collection_failure("wrong tournament season") == "identity_mismatch"
    assert classify_collection_failure("locator timeout", phase="player_stats") == "player_stats_missing"
    assert classify_collection_failure("header did not render", phase="category") == "category_missing"
    assert classify_collection_failure(TimeoutError("navigation timed out")) == "load_timeout"
    assert classify_collection_failure("empty page", body_text="Loading...") == "page_shell_only"
    assert classify_collection_failure("KeyError: player_id") == "parse_failure"
    assert classify_collection_failure("timeout", body_text="Verify you are human") == "manual_verification_required"
