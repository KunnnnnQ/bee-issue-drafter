"""Fuzzy title matching, shared by duplicate detection and evaluation."""
from __future__ import annotations

import re
from difflib import SequenceMatcher

DUPLICATE_THRESHOLD = 0.75


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def similarity(a: str, b: str) -> float:
    """0.0-1.0 similarity of two titles, ignoring case and punctuation."""
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def find_duplicate(
    title: str, existing: list[dict], threshold: float = DUPLICATE_THRESHOLD
) -> tuple[dict, float] | None:
    """Return (issue, score) for the existing issue whose title is most similar, if above threshold."""
    best: tuple[dict, float] | None = None
    for issue in existing:
        score = similarity(title, str(issue.get("title") or ""))
        if score >= threshold and (best is None or score > best[1]):
            best = (issue, score)
    return best
