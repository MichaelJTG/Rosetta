"""Cliente Claude API para el Traductor Simbiótico.

Licencia de la herramienta: Propietaria (servicio cloud Anthropic) — sin
  restricciones de uso como API.
URL: https://docs.anthropic.com/

Implementa LLMClient usando el SDK oficial anthropic-python.
"""

from __future__ import annotations

import os
from typing import Any, cast

import structlog
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock, ToolUseBlock

from rosetta.llm.base import CompletionResult, Message, Tool, ToolCallResult

logger = structlog.get_logger(__name__)


class ClaudeClient:
    """Wrapper sobre Anthropic Python SDK que implementa LLMClient."""

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
        messages: list[Message],
        tools: list[Tool] | None = None,
    ) -> CompletionResult:
        """Llama a Claude con un system prompt + conversación.

        Para el Traductor usaremos tool-use para forzar que la respuesta
        siga el schema DatosCompliance exactamente.

        Args:
            system: System prompt con instrucciones globales.
            messages: Historial de la conversación.
            tools: Herramientas disponibles para tool-use forzado.

        Returns:
            CompletionResult normalizado.
        """
        anthropic_messages = [{"role": m.role, "content": m.content} for m in messages]
        anthropic_tools: list[dict[str, Any]] = []
        if tools:
            for t in tools:
                anthropic_tools.append(
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema.model_dump(),
                    }
                )

        response = await self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=anthropic_messages,  # type: ignore[arg-type]
            tools=anthropic_tools,  # type: ignore[arg-type]
        )

        raw: dict[str, Any] = response.model_dump()
        tool_calls: list[ToolCallResult] = []
        text_content: str | None = None

        for block in response.content:
            if isinstance(block, ToolUseBlock):
                tool_calls.append(
                    ToolCallResult(
                        tool_name=block.name,
                        tool_input=cast(dict[str, Any], block.input),
                    )
                )
            elif isinstance(block, TextBlock):
                text_content = block.text

        return CompletionResult(
            content=text_content,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "end_turn",
            raw=raw,
        )
