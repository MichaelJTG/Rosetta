"""Cliente OpenAI para el Traductor Simbiótico.

Licencia de la herramienta: Propietaria (servicio cloud) — sin restricciones de
  uso como API. Compatible con cualquier endpoint OpenAI-like (Azure OpenAI,
  Together AI, vLLM, LM Studio, etc.) cambiando OPENAI_API_BASE.

Usa httpx directamente (sin SDK de OpenAI) para minimizar dependencias y
mantener control total sobre los tipos.
"""

from __future__ import annotations

import json as json_lib
import os
from typing import Any, cast

import httpx
import structlog

from rosetta.llm.base import CompletionResult, Message, Tool, ToolCallResult

logger = structlog.get_logger(__name__)

_OPENAI_API_BASE = "https://api.openai.com/v1"
_DEFAULT_OPENAI_MODEL = "gpt-4o"


class OpenAIClient:
    """Cliente httpx para la API de OpenAI (o compatible).

    Compatible con:
    - OpenAI (api.openai.com)
    - Azure OpenAI (cambiar OPENAI_API_BASE)
    - Cualquier endpoint OpenAI-compatible (vLLM, LM Studio, Together AI...)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        api_base: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        resolved_key: str = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "OPENAI_API_KEY no definida. Rellénala en .env o pásala explícitamente."
            )
        self.api_key = resolved_key
        self.model = (
            model if model is not None else os.getenv("OPENAI_MODEL", _DEFAULT_OPENAI_MODEL)
        )
        resolved_base: str = (
            api_base if api_base is not None else os.getenv("OPENAI_API_BASE", _OPENAI_API_BASE)
        )
        self.api_base = resolved_base.rstrip("/")
        self.timeout = timeout
        logger.info("openai_client_initialized", model=self.model, api_base=self.api_base)

    async def completar(
        self,
        system: str,
        messages: list[Message],
        tools: list[Tool] | None = None,
    ) -> CompletionResult:
        """Envía la conversación a OpenAI y normaliza la respuesta.

        Construye el payload en el formato estándar de OpenAI Chat Completions.
        Si se proveen tools, las convierte al formato function-calling de OpenAI.
        """
        openai_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        openai_messages += [{"role": m.role, "content": m.content} for m in messages]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        raw_data = cast(dict[str, Any], response.json())
        choices = cast(list[dict[str, Any]], raw_data.get("choices", []))
        choice = choices[0] if choices else cast(dict[str, Any], {})
        msg = cast(dict[str, Any], choice.get("message", {}))
        content: str | None = cast(str | None, msg.get("content"))

        tool_calls: list[ToolCallResult] = []
        for tc in cast(list[dict[str, Any]], msg.get("tool_calls", [])):
            fn = cast(dict[str, Any], tc.get("function", {}))
            raw_args = fn.get("arguments", {})
            if isinstance(raw_args, str):
                try:
                    args: dict[str, Any] = json_lib.loads(raw_args)
                except json_lib.JSONDecodeError:
                    args = {}
            else:
                args = cast(dict[str, Any], raw_args)
            tool_calls.append(
                ToolCallResult(
                    tool_name=cast(str, fn.get("name", "")),
                    tool_input=args,
                )
            )

        return CompletionResult(
            content=content,
            tool_calls=tool_calls,
            stop_reason=cast(str, choice.get("finish_reason", "stop")),
            raw=raw_data,
        )
