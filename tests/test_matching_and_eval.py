from bee_issues.evaluate import evaluate
from bee_issues.matching import find_duplicate, similarity


def test_similarity_ignores_case_and_punctuation():
    assert similarity("Fix login: timeout!", "fix LOGIN timeout") == 1.0
    assert similarity("Add CSV export", "Upgrade database driver") < 0.5
    assert similarity("", "anything") == 0.0


def test_find_duplicate_returns_best_match_above_threshold():
    existing = [
        {"number": 1, "title": "Add CSV export"},
        {"number": 2, "title": "Login page times out on staging"},
    ]
    issue, score = find_duplicate("Login page timing out on staging", existing)
    assert issue["number"] == 2 and score > 0.75
    assert find_duplicate("Write onboarding docs", existing) is None


def test_evaluate_one_to_one_matching_and_type_accuracy():
    drafts = [
        {"title": "Validate empty email on login", "type": "bug", "summary": "500 error"},
        {"title": "Add upload spinner", "type": "task"},
        {"title": "Order lunch", "type": "task"},
    ]
    expected = [
        {"type": "bug", "keywords": ["login", "email"]},
        {"type": "feature", "keywords": ["spinner"]},
        {"type": "question", "title": "Decide upload size limit"},
    ]
    result = evaluate(drafts, expected)
    assert len(result.matched) == 2
    assert [e["title"] for e in result.missed] == ["Decide upload size limit"]
    assert [d["title"] for d in result.extra] == ["Order lunch"]
    assert round(result.precision, 2) == 0.67 and round(result.recall, 2) == 0.67
    assert result.type_accuracy == 0.5
