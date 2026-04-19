"""Interfaz LLMClient y tipos de datos compartidos para la capa LLM de ROSETTA.

Define el contrato que deben cumplir todos los proveedores de LLM
(Claude, Ollama, OpenAI) y los modelos de datos que viajan entre
el Traductor Simbiótico y cada implementación.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Mensaje en la conversación con el LLM."""

    role: str
    content: str


class ToolInputSchema(BaseModel):
    """Schema JSON del parámetro de entrada de una tool (subconjunto de JSON Schema)."""

    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class Tool(BaseModel):
    """Definición de una herramienta que el LLM puede invocar (tool-use / function calling)."""

    name: str
    description: str
    input_schema: ToolInputSchema = Field(default_factory=ToolInputSchema)


class ToolCallResult(BaseModel):
    """Resultado de una llamada a tool incluida en la respuesta del LLM."""

    tool_name: str
    tool_input: dict[str, Any] = Field(default_factory=dict)


class CompletionResult(BaseModel):
    """Respuesta normalizada del LLM, independiente del proveedor.

    Atributos:
        content: Texto libre generado por el modelo (puede ser None si solo hay tool_calls).
        tool_calls: Lista de invocaciones a herramientas incluidas en la respuesta.
        stop_reason: Razón de parada tal como la reporta el proveedor.
        raw: Respuesta original del proveedor para trazabilidad y debugging.
    """

    content: str | None = None
    tool_calls: list[ToolCallResult] = Field(default_factory=list)
    stop_reason: str
    raw: dict[str, Any] = Field(default_factory=dict)


class LLMClient(Protocol):
    """Interfaz que deben implementar todos los clientes LLM de ROSETTA.

    Cada implementación (ClaudeClient, OllamaClient, OpenAIClient) satisface
    este Protocol estructuralmente — no es necesario heredar explícitamente.
    """

    async def completar(
        self,
        system: str,
        messages: list[Message],
        tools: list[Tool] | None = None,
    ) -> CompletionResult:
        """Envía una conversación al LLM y devuelve la respuesta normalizada.

        Args:
            system: System prompt con instrucciones globales del modelo.
            messages: Historial de la conversación en orden cronológico.
            tools: Herramientas disponibles para tool-use / function calling.

        Returns:
            CompletionResult con contenido, tool_calls y metadatos normalizados.
        """
        ...
