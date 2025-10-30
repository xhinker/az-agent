"""
Helpers for invoking LLM endpoints via the OpenAI Python client.

The goal of this module is to isolate all communication with the LLM so the
HTTP server can focus on request handling.  The helpers below provide simple
entry points for both standard and streaming chat completions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterable, Optional

from openai import AsyncOpenAI


class LLMServiceError(RuntimeError):
    """Raised when the LLM service reports an error."""


@dataclass
class LLMSettings:
    """Configuration describing how to talk to the target LLM."""

    model_name: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    default_request_options: Dict[str, Any] = field(default_factory=dict)


def derive_base_url(llm_api_url: Optional[str]) -> Optional[str]:
    """
    Convert a full chat completion URL to a base URL understood by the OpenAI client.

    The OpenAI client expects the `base_url` to exclude the resource path.
    For common OpenAI-compatible servers this is the portion ending in `/v1`.
    """
    if not llm_api_url:
        return None

    trimmed = llm_api_url.rstrip("/")
    for suffix in ("/chat/completions", "/completions"):
        if trimmed.endswith(suffix):
            return trimmed[: -len(suffix)]
    return trimmed


def load_settings_from_config(config: Dict[str, Any], model_key: str) -> LLMSettings:
    """
    Build `LLMSettings` from the application's configuration dictionary.

    The config is expected to have a `llm_models` mapping with entries that look like:
    {
        "model_name": "...",
        "llm_api_url": "...",
        "llm_api_key": "...",
        "llm_options": {...}  # optional kwargs forwarded to the LLM call
    }
    """
    llm_models = config.get("llm_models") or {}
    if model_key not in llm_models:
        available = ", ".join(sorted(llm_models.keys()))
        raise KeyError(f"Model '{model_key}' not found. Available models: {available}")

    model_config = llm_models[model_key]
    model_name = model_config.get("model_name") or model_key
    api_key = model_config.get("llm_api_key")

    api_base_url = model_config.get("llm_api_base")
    if not api_base_url:
        api_base_url = derive_base_url(model_config.get("llm_api_url"))

    default_request_options = model_config.get("llm_options") or {}

    return LLMSettings(
        model_name=model_name,
        api_key=api_key,
        api_base_url=api_base_url,
        default_request_options=default_request_options,
    )


class LLMService:
    """Thin wrapper around the AsyncOpenAI client."""

    def __init__(self, settings: LLMSettings):
        self._settings = settings
        client_kwargs: Dict[str, Any] = {}
        if settings.api_key:
            client_kwargs["api_key"] = settings.api_key
        if settings.api_base_url:
            client_kwargs["base_url"] = settings.api_base_url.rstrip("/")
        self._client = AsyncOpenAI(**client_kwargs)
        self._default_request_options = dict(settings.default_request_options)

    @property
    def model_name(self) -> str:
        return self._settings.model_name

    def _prepare_request_options(self, overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge default request options with any overrides from the caller."""
        request_options = dict(self._default_request_options)
        if overrides:
            request_options.update(overrides)
        # These keys are handled explicitly by the service
        request_options.pop("messages", None)
        request_options.pop("model", None)
        request_options.pop("stream", None)
        return request_options

    async def chat_completion(
        self, messages: Iterable[Dict[str, Any]], **request_overrides: Any
    ) -> Dict[str, Any]:
        """
        Execute a non-streaming chat completion request.

        Returns the OpenAI response converted to a plain dictionary for easier
        serialization by callers.
        """
        options = self._prepare_request_options(request_overrides)

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=list(messages),
                **options,
            )
        except Exception as exc:
            raise LLMServiceError(f"Chat completion failed: {exc}") from exc

        return response.model_dump()

    async def stream_chat_completion(
        self, messages: Iterable[Dict[str, Any]], **request_overrides: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a streaming chat completion request.

        Yields chunk dictionaries compatible with the OpenAI streaming wire format.
        """
        options = self._prepare_request_options(request_overrides)

        try:
            stream = await self._client.chat.completions.create(
                model=self.model_name,
                messages=list(messages),
                stream=True,
                **options,
            )
        except Exception as exc:
            raise LLMServiceError(f"Chat completion stream failed to start: {exc}") from exc

        async for chunk in stream:
            yield chunk.model_dump()
