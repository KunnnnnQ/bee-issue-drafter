"""Settings loaded from environment variables and an optional .env file.

All secrets (API keys, tokens) are read from the environment only.
Copy .env.example to .env and fill in the values there.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # python-dotenv is listed in requirements.txt, but stay usable without it.
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"
DEFAULT_BEDROCK_MODEL_ID = "anthropic.claude-sonnet-5-5"
SUPPORTED_PROVIDERS = ("anthropic", "bedrock")


@dataclass
class Settings:
    llm_provider: str = "anthropic"
    anthropic_api_key: str | None = None
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL
    aws_region: str | None = None
    bedrock_model_id: str = DEFAULT_BEDROCK_MODEL_ID
    github_token: str | None = None
    github_repo: str | None = None
    bee_bin: str | None = None

    def status(self) -> dict[str, str]:
        """Which settings are present, without revealing secret values."""

        def mark(value: str | None) -> str:
            return "set" if value else "MISSING"

        return {
            "LLM_PROVIDER": self.llm_provider,
            "ANTHROPIC_API_KEY": mark(self.anthropic_api_key),
            "ANTHROPIC_MODEL": self.anthropic_model,
            "AWS_REGION": self.aws_region or "(not set)",
            "BEDROCK_MODEL_ID": self.bedrock_model_id,
            "GITHUB_TOKEN": mark(self.github_token),
            "GITHUB_REPO": self.github_repo or "MISSING",
            "BEE_BIN": self.bee_bin or "(auto: find `bee` on PATH)",
        }


def _get(name: str, default: str | None = None) -> str | None:
    value = (os.environ.get(name) or "").strip()
    return value or default


def load_settings(env_file: str | os.PathLike | None = ".env") -> Settings:
    if load_dotenv is not None and env_file and Path(env_file).exists():
        load_dotenv(env_file, override=False)
    return Settings(
        llm_provider=(_get("LLM_PROVIDER", "anthropic") or "anthropic").lower(),
        anthropic_api_key=_get("ANTHROPIC_API_KEY"),
        anthropic_model=_get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL),
        aws_region=_get("AWS_REGION"),
        bedrock_model_id=_get("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID),
        github_token=_get("GITHUB_TOKEN"),
        github_repo=_get("GITHUB_REPO"),
        bee_bin=_get("BEE_BIN"),
    )
