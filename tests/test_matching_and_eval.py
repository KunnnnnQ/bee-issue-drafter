from bee_issues.evaluate import evaluate
from bee_issues.matching import find_duplicate, similarity


def test_similarity_ignores_case_and_punctuation():
    assert similarity("Fix login: timeout!", "fix LOGIN timeout") == 1.0
    assert similarity("Add CSV export", "Upgrade database driver") < 0.5
    assert similarity("", "anything") == 0.0


def test_similarity_catches_reworded_titles_but_not_related_ones():
    # Same issue drafted twice from one Bee recording, with different wording.
    assert similarity(
        "Decide whether Internet Explorer must be supported",
        "Decide whether to support Internet Explorer",
    ) >= 0.75
    # Seen live during the demo recording (issues #9 and #12 in the test repo).
    assert similarity(
        "Dark mode toggle resets after refreshing settings page",
        "Fix dark mode toggle resetting on settings page refresh",
    ) >= 0.75
    assert similarity("Add CSV export", "Fix CSV export crash on large reports") < 0.75
    assert similarity("Add keyboard shortcut to submit the form", "Fix form submit error") < 0.75


def test_find_duplicate_returns_best_match_above_threshold():
    existing = [
        {"number": 1, "title": "Add CSV export"},
        {"number": 2, "title": "Login page times out on staging"},
    ]
    issue, score = find_duplicate("Login page timing out on staging", existing)
    assert issue["number"] == 2 and score > 0.75
    assert find_duplicate("Write onboarding docs", existing) is None


def test_evaluate_prefers_keyword_in_title_over_mention_in_details():
    drafts = [
        {"title": "Create tests for the demo", "type": "task", "details": "Mentions the Safari bug."},
        {"title": "Fix blank login page on Safari", "type": "bug"},
    ]
    result = evaluate(drafts, [{"type": "bug", "keywords": ["safari"]}])
    assert result.matched[0][1]["title"] == "Fix blank login page on Safari"
    assert [d["title"] for d in result.extra] == ["Create tests for the demo"]


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
