import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "tests" / "fixtures" / "synthetic_conversation.json"


@pytest.fixture
def conversation_payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def fixture_path():
    return FIXTURE


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in [
        "LLM_PROVIDER", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "AWS_REGION",
        "BEDROCK_MODEL_ID", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "DEEPSEEK_BASE_URL", "GITHUB_TOKEN", "GITHUB_REPO", "BEE_BIN",
    ]:
        monkeypatch.delenv(name, raising=False)
