"""Factory para instanciar el LLMClient correcto según el entorno.

Lee LLM_PROVIDER del entorno (valores: claude, ollama, openai).
Por defecto usa Claude (API de Anthropic).

Ejemplo de uso:
    from rosetta.llm.factory import get_llm_client

    llm = get_llm_client()           # usa LLM_PROVIDER del entorno
    llm = get_llm_client("ollama")   # fuerza Ollama independiente del entorno
"""

from __future__ import annotations

import os

from rosetta.llm.base import LLMClient

_SUPPORTED: tuple[str, ...] = ("claude", "ollama", "openai")


def get_llm_client(provider: str | None = None) -> LLMClient:
    """Devuelve la implementación de LLMClient correspondiente al proveedor.

    Args:
        provider: Nombre del proveedor ("claude", "ollama", "openai").
            Si es None, se lee la variable de entorno LLM_PROVIDER.
            Si LLM_PROVIDER tampoco está definida, se usa "claude".

    Returns:
        Instancia configurada del cliente LLM solicitado.

    Raises:
        ValueError: Si el proveedor no está entre los soportados.
    """
    resolved = provider or os.getenv("LLM_PROVIDER", "claude")

    if resolved == "claude":
        from rosetta.llm.claude import ClaudeClient

        return ClaudeClient()

    if resolved == "ollama":
        from rosetta.llm.ollama import OllamaClient

        return OllamaClient()

    if resolved == "openai":
        from rosetta.llm.openai import OpenAIClient

        return OpenAIClient()

    raise ValueError(
        f"Proveedor LLM no soportado: '{resolved}'. Opciones válidas: {', '.join(_SUPPORTED)}"
    )
