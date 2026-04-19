"""Clientes de LLM para ROSETTA.

Exporta la interfaz pública: LLMClient Protocol, tipos de datos compartidos
y la factory get_llm_client() para obtener la implementación activa.

Uso rápido:
    from rosetta.llm import get_llm_client, LLMClient

    llm = get_llm_client()   # usa LLM_PROVIDER del entorno
"""

from rosetta.llm.base import (
    CompletionResult,
    LLMClient,
    Message,
    Tool,
    ToolCallResult,
    ToolInputSchema,
)
from rosetta.llm.factory import get_llm_client

__all__ = [
    "CompletionResult",
    "LLMClient",
    "Message",
    "Tool",
    "ToolCallResult",
    "ToolInputSchema",
    "get_llm_client",
]
