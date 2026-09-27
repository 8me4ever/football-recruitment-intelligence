"""Stable failure labels for rendered-page collection attempts."""
from __future__ import annotations

from typing import Literal

FailureStatus = Literal[
    "identity_mismatch",
    "player_stats_missing",
    "category_missing",
    "load_timeout",
    "page_shell_only",
    "parse_failure",
    "manual_verification_required",
]


def classify_collection_failure(
    error: BaseException | str,
    *,
    body_text: str = "",
    phase: str | None = None,
) -> FailureStatus:
    """Map a failed attempt to a stable, auditable status.

    An explicit phase takes priority because a timeout while waiting for a
    category table means something different from a timeout opening a page.
    """
    error_type = type(error).__name__ if isinstance(error, BaseException) else ""
    message = str(error).lower()
    body = " ".join(body_text.lower().split())
    combined = f"{message} {body}"

    if any(token in combined for token in (
        "verify you are human", "captcha", "checking your browser",
        "manual verification", "challenge page",
    )):
        return "manual_verification_required"

    if phase in {"identity", "identity_validation"} or any(token in message for token in (
        "identity mismatch", "date/competition/status/score mismatch", "team names mismatch",
        "teamset", "wrong tournament season", "wrong afc season", "wrong selected round",
        "wrong selected afc matchday", "not visibly finished", "exact fixture card",
        "fixture card missing", "url event id mismatch", "heading does not match",
    )):
        return "identity_mismatch"

    if phase in {"player_stats", "player_stats_tab"} or "player stats" in message or "player_stats_missing" in message:
        return "player_stats_missing"

    if phase in {"category", "table"} or "category_missing" in message or "expected one player table" in message:
        return "category_missing"

    if "page shell only" in message or (body and
        len(body) < 180 and not any(token in body for token in ("player stats", "finished", "lineups"))
    ):
        return "page_shell_only"

    if phase in {"load", "navigation"} or error_type in {"TimeoutError", "PlaywrightTimeoutError"} or any(
        token in message for token in ("timeout", "timed out", "target closed")
    ):
        return "load_timeout"

    return "parse_failure"
