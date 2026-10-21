"""Fuzzy title matching, shared by duplicate detection and evaluation."""
from __future__ import annotations

import re
from difflib import SequenceMatcher

DUPLICATE_THRESHOLD = 0.75


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


STOPWORDS = {
    "a", "an", "the", "to", "of", "for", "in", "on", "at", "and", "or", "is", "be", "must",
    "should", "whether", "when", "while", "with", "it", "we", "if", "after", "before",
    "every", "time", "from", "by", "vs", "versus", "not", "just", "as", "well",
    # Leading verbs differ between drafts of the same item ("Fix X" / "X resets").
    "fix", "add", "decide", "show", "create", "implement", "make", "update", "confirm",
    "clarify", "determine", "investigate", "consider", "check", "ensure",
}


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            word = word[: -len(suffix)]
            if len(word) > 3 and word[-1] == word[-2]:
                word = word[:-1]  # resetting -> resett -> reset
            return word
    return word


def _keywords(text: str) -> set[str]:
    return {_stem(w) for w in text.split() if w not in STOPWORDS}


def similarity(a: str, b: str) -> float:
    """0.0-1.0 similarity of two titles, ignoring case and punctuation.

    The higher of character similarity and keyword overlap, so a reworded title
    ("Decide whether IE must be supported" / "Decide whether to support IE") still matches.
    Keyword overlap averages Jaccard with containment, so extra detail in one title
    ("... with backend team") lowers the score less than a different subject does.
    """
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    chars = SequenceMatcher(None, a, b).ratio()
    ka, kb = _keywords(a), _keywords(b)
    if not ka or not kb:
        return chars
    shared = len(ka & kb)
    words = (shared / len(ka | kb) + shared / min(len(ka), len(kb))) / 2
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
