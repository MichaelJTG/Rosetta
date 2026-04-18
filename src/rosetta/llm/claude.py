"""Cliente Claude API para el Traductor Simbiótico."""

from __future__ import annotations

import os

import structlog
from anthropic import AsyncAnthropic

logger = structlog.get_logger(__name__)


class ClaudeClient:
    """Wrapper ligero sobre Anthropic Python SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY no definida. Rellénala en .env o pásala explícitamente."
            )
        self.model = model
        self.max_tokens = max_tokens
        self._client = AsyncAnthropic(api_key=self.api_key)
        logger.info("claude_client_initialized", model=model)

    async def completar(
        self,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        """Llama a Claude con un system prompt + conversación.

        Para el Traductor usaremos tool-use para forzar que la respuesta
        siga el schema DatosCompliance exactamente.
        """
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,  # type: ignore[arg-type]
            tools=tools or [],  # type: ignore[arg-type]
        )
        return response.model_dump()
