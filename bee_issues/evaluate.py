"""Compare generated drafts with a hand-written list of expected issues.

Expected file format (JSON):

    {"conversation_id": 4242,
     "expected": [
        {"type": "bug", "keywords": ["login", "timeout"]},
        {"type": "feature", "title": "Add CSV export to the reports page"}
     ]}

A draft matches an expected item when every keyword appears in the draft's
title/summary/details, or (if no keywords are given) when the titles are
similar enough. Each draft and each expected item is matched at most once.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from bee_issues.matching import normalize, similarity

TITLE_MATCH_THRESHOLD = 0.5


@dataclass
class EvalResult:
    conversation_id: int | None
    matched: list[tuple[dict, dict]] = field(default_factory=list)  # (expected, draft)
    missed: list[dict] = field(default_factory=list)
    extra: list[dict] = field(default_factory=list)

    @property
    def precision(self) -> float:
        found = len(self.matched) + len(self.extra)
        return len(self.matched) / found if found else 1.0

    @property
    def recall(self) -> float:
        wanted = len(self.matched) + len(self.missed)
        return len(self.matched) / wanted if wanted else 1.0

    @property
    def type_accuracy(self) -> float:
        if not self.matched:
            return 1.0
        same = sum(1 for exp, got in self.matched if not exp.get("type") or exp["type"] == got.get("type"))
        return same / len(self.matched)


def _score(expected: dict, draft: dict) -> float:
    keywords = [normalize(k) for k in expected.get("keywords") or [] if normalize(k)]
    if keywords:
        # Substring match, so "timeout" also matches "timeouts".
        haystack = normalize(" ".join(str(draft.get(k) or "") for k in ("title", "summary", "details")))
        return 1.0 if all(k in haystack for k in keywords) else 0.0
    score = similarity(str(expected.get("title") or ""), str(draft.get("title") or ""))
    return score if score >= TITLE_MATCH_THRESHOLD else 0.0


def evaluate(drafts: list[dict], expected: list[dict], conversation_id: int | None = None) -> EvalResult:
    pairs = sorted(
        ((_score(exp, got), i, j) for i, exp in enumerate(expected) for j, got in enumerate(drafts)),
        reverse=True,
    )
    used_exp: set[int] = set()
    used_got: set[int] = set()
    result = EvalResult(conversation_id)
    for score, i, j in pairs:
        if score <= 0 or i in used_exp or j in used_got:
            continue
        used_exp.add(i)
        used_got.add(j)
        result.matched.append((expected[i], drafts[j]))
    result.missed = [exp for i, exp in enumerate(expected) if i not in used_exp]
    result.extra = [got for j, got in enumerate(drafts) if j not in used_got]
    return result


def describe(expected: dict) -> str:
    if expected.get("title"):
        return str(expected["title"])
    return "keywords: " + ", ".join(expected.get("keywords") or [])
