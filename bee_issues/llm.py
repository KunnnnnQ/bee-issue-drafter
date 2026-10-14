"""Minimal LLM client: Anthropic Claude API (default), Claude on Amazon Bedrock, or DeepSeek."""
from __future__ import annotations

import time

import requests

from bee_issues.config import SUPPORTED_PROVIDERS, Settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MAX_OUTPUT_TOKENS = 4096


class LLMError(RuntimeError):
    pass


RETRY_STATUS = {429, 500, 502, 503, 504}


def _post(url: str, attempts: int = 3, backoff: float = 2.0, **kwargs) -> requests.Response:
    """requests.post with retries on network errors, rate limits and server errors."""
    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(url, **kwargs)
        except requests.RequestException as exc:
            if attempt == attempts:
                raise LLMError(f"Network error calling {url}: {exc}") from exc
        else:
            if response.status_code not in RETRY_STATUS or attempt == attempts:
                return response
        time.sleep(backoff * attempt)
    raise AssertionError("unreachable")


def model_name(settings: Settings) -> str:
    if settings.llm_provider == "bedrock":
        return settings.bedrock_model_id
    if settings.llm_provider == "deepseek":
        return settings.deepseek_model
    return settings.anthropic_model


def complete(system: str, user: str, settings: Settings, timeout: int = 120) -> str:
    """Send one system + user message and return the model's text reply."""
    if settings.llm_provider == "anthropic":
        return _anthropic(system, user, settings, timeout)
    if settings.llm_provider == "bedrock":
        return _bedrock(system, user, settings)
    if settings.llm_provider == "deepseek":
        return _deepseek(system, user, settings, timeout)
    raise LLMError(
        f"Unknown LLM_PROVIDER {settings.llm_provider!r}; use one of {SUPPORTED_PROVIDERS}."
    )


def _anthropic(system: str, user: str, settings: Settings, timeout: int) -> str:
    if not settings.anthropic_api_key:
        raise LLMError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    response = _post(
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


def _deepseek(system: str, user: str, settings: Settings, timeout: int) -> str:
    """DeepSeek's OpenAI-compatible chat completions API, in JSON mode."""
    if not settings.deepseek_api_key:
        raise LLMError("DEEPSEEK_API_KEY is not set. Add it to your .env file.")
    response = _post(
        f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.deepseek_model,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=timeout,
    )
    if response.status_code != 200:
        raise LLMError(f"DeepSeek API error {response.status_code}: {response.text[:300]}")
    choices = response.json().get("choices") or []
    if not choices:
        raise LLMError("DeepSeek API returned no choices.")
    return choices[0].get("message", {}).get("content") or ""


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
