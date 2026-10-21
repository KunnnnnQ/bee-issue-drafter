"""Fuzzy title matching, shared by duplicate detection and evaluation."""
from __future__ import annotations

import re
from difflib import SequenceMatcher

DUPLICATE_THRESHOLD = 0.75


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


STOPWORDS = {
    "a", "an", "the", "to", "of", "for", "in", "on", "at", "and", "or", "is", "be", "must",
    "should", "whether", "when", "while", "with", "it", "we", "if",
}


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _keywords(text: str) -> set[str]:
    return {_stem(w) for w in text.split() if w not in STOPWORDS}


def similarity(a: str, b: str) -> float:
    """0.0-1.0 similarity of two titles, ignoring case and punctuation.

    The higher of character similarity and keyword overlap, so a reworded title
    ("Decide whether IE must be supported" / "Decide whether to support IE") still matches.
    """
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    chars = SequenceMatcher(None, a, b).ratio()
    ka, kb = _keywords(a), _keywords(b)
    words = len(ka & kb) / len(ka | kb) if ka and kb else 0.0
    return max(chars, words)


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
