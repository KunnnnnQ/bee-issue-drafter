"""Create and list GitHub issues through the REST API."""
from __future__ import annotations

import requests

API_ROOT = "https://api.github.com"


class GitHubError(RuntimeError):
    pass


def _check_args(repo: str, token: str) -> None:
    if not repo or "/" not in repo:
        raise GitHubError("GITHUB_REPO must look like owner/name.")
    if not token:
        raise GitHubError("GITHUB_TOKEN is not set. Add it to your .env file.")


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_repo(
    repo: str, token: str, session: requests.Session | None = None, timeout: int = 30
) -> dict:
    """Return the repository JSON; used by `check` to confirm the token works."""
    _check_args(repo, token)
    http = session or requests.Session()
    response = http.get(f"{API_ROOT}/repos/{repo}", headers=_headers(token), timeout=timeout)
    if response.status_code != 200:
        raise GitHubError(f"GitHub API error {response.status_code}: {response.text[:300]}")
    return response.json()


def list_issues(
    repo: str,
    token: str,
    max_pages: int = 5,
    session: requests.Session | None = None,
    timeout: int = 30,
) -> list[dict]:
    """Return open and closed issues (not pull requests), newest first, up to 100 * max_pages."""
    _check_args(repo, token)
    http = session or requests.Session()
    issues: list[dict] = []
    for page in range(1, max_pages + 1):
        response = http.get(
            f"{API_ROOT}/repos/{repo}/issues",
            headers=_headers(token),
            params={"state": "all", "per_page": 100, "page": page},
            timeout=timeout,
        )
        if response.status_code != 200:
            raise GitHubError(f"GitHub API error {response.status_code}: {response.text[:300]}")
        batch = response.json()
        issues += [item for item in batch if "pull_request" not in item]
        if len(batch) < 100:
            break
    return issues


def create_issue(
    repo: str,
    token: str,
    title: str,
    body: str,
    labels: list[str] | None = None,
    session: requests.Session | None = None,
    timeout: int = 30,
) -> dict:
    """Create one issue in `owner/name` and return GitHub's JSON (includes html_url).

    If GitHub rejects the labels (HTTP 422), retry once without labels.
    """
    _check_args(repo, token)
    http = session or requests.Session()
    url = f"{API_ROOT}/repos/{repo}/issues"
    payload: dict = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    response = http.post(url, headers=_headers(token), json=payload, timeout=timeout)
    if response.status_code == 422 and labels:
        payload.pop("labels")
        response = http.post(url, headers=_headers(token), json=payload, timeout=timeout)
    if response.status_code != 201:
        raise GitHubError(f"GitHub API error {response.status_code}: {response.text[:300]}")
    return response.json()
