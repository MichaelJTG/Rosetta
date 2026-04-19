"""Cliente Ollama para el Traductor Simbiótico (modelos locales y on-premise).

Licencia de la herramienta: MIT — uso libre como dependencia
URL: https://github.com/ollama/ollama

Orquesta Ollama vía su API REST HTTP. No requiere SDK adicional: usa httpx.
Útil para:
  - Iteración de desarrollo sin gasto de API.
  - Despliegues on-premise exigidos por clientes ENS/NIS2.
"""

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import structlog

from rosetta.llm.base import CompletionResult, Message, Tool, ToolCallResult

logger = structlog.get_logger(__name__)

_DEFAULT_OLLAMA_URL = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "llama3.1:8b"


class OllamaClient:
    """Cliente httpx para la API de Ollama.

    Limitación conocida: los modelos pequeños (7B-8B) responden peor a
    tool-use estructurado que Claude Sonnet. Si la tasa de error en
    DatosCompliance es alta, considera aumentar el modelo o simplificar el
    schema de la tool.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        resolved_url: str = (
            base_url if base_url is not None else os.getenv("OLLAMA_URL", _DEFAULT_OLLAMA_URL)
        )
        self.base_url = resolved_url.rstrip("/")
        self.model = (
            model if model is not None else os.getenv("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
        )
        self.timeout = timeout
        logger.info("ollama_client_initialized", model=self.model, base_url=self.base_url)

    async def completar(
        self,
        system: str,
        messages: list[Message],
        tools: list[Tool] | None = None,
    ) -> CompletionResult:
        """Envía la conversación a Ollama y normaliza la respuesta.

        Construye el payload en formato de Ollama (compatible con OpenAI /chat).
        Si se proveen tools, las convierte al formato OpenAI function-calling
        que Ollama acepta en modelos compatibles.
        """
        ollama_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        ollama_messages += [{"role": m.role, "content": m.content} for m in messages]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
        }

        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema.model_dump(),
                    },
                }
                for t in tools
            ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()

        raw_data = cast(dict[str, Any], response.json())
        msg = cast(dict[str, Any], raw_data.get("message", {}))
        content: str | None = cast(str | None, msg.get("content"))

        tool_calls: list[ToolCallResult] = []
        for tc in cast(list[dict[str, Any]], msg.get("tool_calls", [])):
            fn = cast(dict[str, Any], tc.get("function", {}))
            tool_calls.append(
                ToolCallResult(
                    tool_name=cast(str, fn.get("name", "")),
                    tool_input=cast(dict[str, Any], fn.get("arguments", {})),
                )
            )

        return CompletionResult(
            content=content,
            tool_calls=tool_calls,
            stop_reason=cast(str, raw_data.get("done_reason", "stop")),
            raw=raw_data,
        )
