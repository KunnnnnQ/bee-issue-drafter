"""Minimal LLM client: Anthropic Claude API (default) or Claude on Amazon Bedrock."""
from __future__ import annotations

import requests

from bee_issues.config import SUPPORTED_PROVIDERS, Settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MAX_OUTPUT_TOKENS = 4096


class LLMError(RuntimeError):
    pass


def model_name(settings: Settings) -> str:
    if settings.llm_provider == "bedrock":
        return settings.bedrock_model_id
    return settings.anthropic_model


def complete(system: str, user: str, settings: Settings, timeout: int = 120) -> str:
    """Send one system + user message and return the model's text reply."""
    if settings.llm_provider == "anthropic":
        return _anthropic(system, user, settings, timeout)
    if settings.llm_provider == "bedrock":
        return _bedrock(system, user, settings)
    raise LLMError(
        f"Unknown LLM_PROVIDER {settings.llm_provider!r}; use one of {SUPPORTED_PROVIDERS}."
    )


def _anthropic(system: str, user: str, settings: Settings, timeout: int) -> str:
    if not settings.anthropic_api_key:
        raise LLMError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    response = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.anthropic_model,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=timeout,
    )
    if response.status_code != 200:
        raise LLMError(f"Anthropic API error {response.status_code}: {response.text[:300]}")
    blocks = response.json().get("content") or []
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def _bedrock(system: str, user: str, settings: Settings) -> str:
    try:
        import boto3  # optional dependency, only needed for LLM_PROVIDER=bedrock
    except ImportError as exc:
        raise LLMError("LLM_PROVIDER=bedrock needs boto3: pip install boto3") from exc
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    try:
        response = client.converse(
            modelId=settings.bedrock_model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"maxTokens": MAX_OUTPUT_TOKENS},
        )
    except Exception as exc:  # botocore raises many error types
        raise LLMError(f"Bedrock error: {exc}") from exc
    content = response["output"]["message"]["content"]
    return "".join(part.get("text", "") for part in content)
