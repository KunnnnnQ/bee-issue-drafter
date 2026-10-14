import pytest

from bee_issues.github_client import GitHubError, create_issue


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}
        self.text = str(self._data)

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": dict(json)})
        return self.responses.pop(0)


def test_create_issue_posts_to_repo():
    session = FakeSession([FakeResponse(201, {"html_url": "https://github.com/o/r/issues/1"})])
    result = create_issue("o/r", "tok", "Title", "Body", ["bug"], session=session)
    assert result["html_url"].endswith("/issues/1")
    call = session.calls[0]
    assert call["url"] == "https://api.github.com/repos/o/r/issues"
    assert call["headers"]["Authorization"] == "Bearer tok"
    assert call["json"] == {"title": "Title", "body": "Body", "labels": ["bug"]}


def test_retries_without_labels_on_422():
    session = FakeSession([FakeResponse(422, {"message": "bad labels"}), FakeResponse(201, {"html_url": "u"})])
    create_issue("o/r", "tok", "T", "B", ["x"], session=session)
    assert "labels" not in session.calls[1]["json"]


def test_errors():
    with pytest.raises(GitHubError, match="owner/name"):
        create_issue("bad", "tok", "T", "B")
    with pytest.raises(GitHubError, match="GITHUB_TOKEN"):
        create_issue("o/r", "", "T", "B")
    session = FakeSession([FakeResponse(401, {"message": "Bad credentials"})])
    with pytest.raises(GitHubError, match="401"):
        create_issue("o/r", "tok", "T", "B", session=session)


class FakeGetSession:
    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "params": params})
        return self.pages.pop(0)


def test_list_issues_skips_pull_requests_and_paginates():
    from bee_issues.github_client import list_issues

    full_page = [{"number": n, "title": f"t{n}"} for n in range(100)]
    last_page = [{"number": 200, "title": "pr", "pull_request": {}}, {"number": 201, "title": "x"}]
    session = FakeGetSession([FakeResponse(200, full_page), FakeResponse(200, last_page)])
    issues = list_issues("o/r", "tok", session=session)
    assert len(issues) == 101
    assert all("pull_request" not in i for i in issues)
    assert [c["params"]["page"] for c in session.calls] == [1, 2]
    assert session.calls[0]["params"]["state"] == "all"
