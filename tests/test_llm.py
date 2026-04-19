"""Tests de la capa LLM: interfaz, factory y clientes individuales.

Cobertura objetivo (CLAUDE.md §10): 80% para core/, 60% para llm/.
Todos los tests usan mocks — no realizan llamadas reales a ninguna API.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import TextBlock, ToolUseBlock

from rosetta.llm.base import (
    CompletionResult,
    Message,
    Tool,
    ToolCallResult,
    ToolInputSchema,
)
from rosetta.llm.claude import ClaudeClient
from rosetta.llm.factory import get_llm_client
from rosetta.llm.ollama import OllamaClient
from rosetta.llm.openai import OpenAIClient

# ---------------------------------------------------------------------------
# Fixtures compartidas
# ---------------------------------------------------------------------------


@pytest.fixture
def mensaje_usuario() -> Message:
    """Mensaje de usuario mínimo para los tests."""
    return Message(role="user", content="Traduce este hallazgo técnico.")


@pytest.fixture
def tool_traducir() -> Tool:
    """Tool de traducción normativa de ejemplo."""
    return Tool(
        name="registrar_traduccion",
        description="Registra la traducción normativa del hallazgo.",
        input_schema=ToolInputSchema(
            properties={"controles": {"type": "array", "items": {"type": "string"}}},
            required=["controles"],
        ),
    )


# ---------------------------------------------------------------------------
# Tests de la factory
# ---------------------------------------------------------------------------


def test_factory_devuelve_implementacion_correcta_claude(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La factory devuelve ClaudeClient cuando el proveedor es 'claude'."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-claude")
    client = get_llm_client("claude")
    assert isinstance(client, ClaudeClient)


def test_factory_devuelve_implementacion_correcta_ollama() -> None:
    """La factory devuelve OllamaClient cuando el proveedor es 'ollama'."""
    client = get_llm_client("ollama")
    assert isinstance(client, OllamaClient)


def test_factory_devuelve_implementacion_correcta_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La factory devuelve OpenAIClient cuando el proveedor es 'openai'."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-openai")
    client = get_llm_client("openai")
    assert isinstance(client, OpenAIClient)


def test_factory_usa_variable_de_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """La factory lee LLM_PROVIDER del entorno cuando no se pasa argumento."""
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    client = get_llm_client()
    assert isinstance(client, OllamaClient)


def test_factory_proveedor_invalido_lanza_valueerror() -> None:
    """Un proveedor desconocido lanza ValueError con el mensaje apropiado."""
    with pytest.raises(ValueError, match="no soportado"):
        get_llm_client("proveedor_inventado")


# ---------------------------------------------------------------------------
# Tests de ClaudeClient
# ---------------------------------------------------------------------------


async def test_claude_client_envuelve_anthropic_sdk_correctamente(
    monkeypatch: pytest.MonkeyPatch,
    mensaje_usuario: Message,
    tool_traducir: Tool,
) -> None:
    """ClaudeClient convierte Message→dict, invoca el SDK y mapea la respuesta."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    # Prepara respuesta mock del SDK de Anthropic con un ToolUseBlock real
    # (debe pasar isinstance check en claude.py)
    mock_tool_block = MagicMock(spec=ToolUseBlock)
    mock_tool_block.name = "registrar_traduccion"
    mock_tool_block.input = {"controles": ["A.8.24", "A.5.15"]}

    mock_response = MagicMock()
    mock_response.stop_reason = "tool_use"
    mock_response.content = [mock_tool_block]
    mock_response.model_dump.return_value = {"stop_reason": "tool_use", "content": []}

    with patch("rosetta.llm.claude.AsyncAnthropic") as MockAnthropic:
        mock_sdk = MagicMock()
        mock_sdk.messages.create = AsyncMock(return_value=mock_response)
        MockAnthropic.return_value = mock_sdk

        client = ClaudeClient()
        result = await client.completar(
            system="Eres un experto normativo.",
            messages=[mensaje_usuario],
            tools=[tool_traducir],
        )

    assert isinstance(result, CompletionResult)
    assert result.stop_reason == "tool_use"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "registrar_traduccion"
    assert result.tool_calls[0].tool_input["controles"] == ["A.8.24", "A.5.15"]
    mock_sdk.messages.create.assert_called_once()


async def test_claude_client_devuelve_texto_sin_tool_use(
    monkeypatch: pytest.MonkeyPatch,
    mensaje_usuario: Message,
) -> None:
    """ClaudeClient extrae el texto cuando la respuesta no incluye tool_calls."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_text_block = MagicMock(spec=TextBlock)
    mock_text_block.text = "No se encontró control aplicable."

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [mock_text_block]
    mock_response.model_dump.return_value = {}

    with patch("rosetta.llm.claude.AsyncAnthropic") as MockAnthropic:
        mock_sdk = MagicMock()
        mock_sdk.messages.create = AsyncMock(return_value=mock_response)
        MockAnthropic.return_value = mock_sdk

        client = ClaudeClient()
        result = await client.completar(system="Eres un experto.", messages=[mensaje_usuario])

    assert result.content == "No se encontró control aplicable."
    assert result.tool_calls == []


def test_claude_client_lanza_error_sin_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ClaudeClient lanza ValueError si no hay ANTHROPIC_API_KEY."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        ClaudeClient()


# ---------------------------------------------------------------------------
# Tests de OllamaClient
# ---------------------------------------------------------------------------


async def test_ollama_client_envia_request_esperado(
    mensaje_usuario: Message,
) -> None:
    """OllamaClient construye el payload correcto y normaliza la respuesta."""
    mock_response_data: dict[str, Any] = {
        "model": "llama3.1:8b",
        "message": {
            "role": "assistant",
            "content": "Control encontrado: A.8.24",
            "tool_calls": [],
        },
        "done": True,
        "done_reason": "stop",
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_resp)

    with patch("rosetta.llm.ollama.httpx.AsyncClient") as MockHttpx:
        MockHttpx.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
        MockHttpx.return_value.__aexit__ = AsyncMock(return_value=False)

        client = OllamaClient(base_url="http://localhost:11434", model="llama3.1:8b")
        result = await client.completar(
            system="Eres un experto normativo.", messages=[mensaje_usuario]
        )

    assert isinstance(result, CompletionResult)
    assert result.content == "Control encontrado: A.8.24"
    assert result.stop_reason == "stop"
    assert result.tool_calls == []

    _, call_kwargs = mock_http_client.post.call_args
    payload = call_kwargs["json"]
    assert payload["model"] == "llama3.1:8b"
    assert payload["stream"] is False
    assert any(m["role"] == "system" for m in payload["messages"])


async def test_ollama_client_normaliza_tool_calls(
    mensaje_usuario: Message,
    tool_traducir: Tool,
) -> None:
    """OllamaClient parsea tool_calls del mensaje de Ollama correctamente."""
    mock_response_data: dict[str, Any] = {
        "message": {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "function": {
                        "name": "registrar_traduccion",
                        "arguments": {"controles": ["A.8.24"]},
                    }
                }
            ],
        },
        "done_reason": "tool_calls",
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_resp)

    with patch("rosetta.llm.ollama.httpx.AsyncClient") as MockHttpx:
        MockHttpx.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
        MockHttpx.return_value.__aexit__ = AsyncMock(return_value=False)

        client = OllamaClient()
        result = await client.completar(
            system="System.", messages=[mensaje_usuario], tools=[tool_traducir]
        )

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "registrar_traduccion"
    assert result.tool_calls[0].tool_input["controles"] == ["A.8.24"]


# ---------------------------------------------------------------------------
# Tests de OpenAIClient
# ---------------------------------------------------------------------------


async def test_openai_client_envia_request_esperado(
    monkeypatch: pytest.MonkeyPatch,
    mensaje_usuario: Message,
) -> None:
    """OpenAIClient construye el payload correcto y normaliza la respuesta."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key")

    mock_response_data: dict[str, Any] = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Respuesta normativa de GPT.",
                    "tool_calls": [],
                },
                "finish_reason": "stop",
            }
        ],
        "model": "gpt-4o",
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_resp)

    with patch("rosetta.llm.openai.httpx.AsyncClient") as MockHttpx:
        MockHttpx.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
        MockHttpx.return_value.__aexit__ = AsyncMock(return_value=False)

        client = OpenAIClient(model="gpt-4o")
        result = await client.completar(
            system="Eres un experto normativo.", messages=[mensaje_usuario]
        )

    assert isinstance(result, CompletionResult)
    assert result.content == "Respuesta normativa de GPT."
    assert result.stop_reason == "stop"

    _, call_kwargs = mock_http_client.post.call_args
    payload = call_kwargs["json"]
    assert payload["model"] == "gpt-4o"
    assert any(m["role"] == "system" for m in payload["messages"])


async def test_openai_client_parsea_tool_calls_con_args_string(
    monkeypatch: pytest.MonkeyPatch,
    mensaje_usuario: Message,
    tool_traducir: Tool,
) -> None:
    """OpenAIClient parsea correctamente tool_calls con arguments como string JSON."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_response_data: dict[str, Any] = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "registrar_traduccion",
                                "arguments": '{"controles": ["A.8.24", "A.5.15"]}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_resp)

    with patch("rosetta.llm.openai.httpx.AsyncClient") as MockHttpx:
        MockHttpx.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
        MockHttpx.return_value.__aexit__ = AsyncMock(return_value=False)

        client = OpenAIClient()
        result = await client.completar(
            system="System.", messages=[mensaje_usuario], tools=[tool_traducir]
        )

    assert len(result.tool_calls) == 1
    tc: ToolCallResult = result.tool_calls[0]
    assert tc.tool_name == "registrar_traduccion"
    assert tc.tool_input["controles"] == ["A.8.24", "A.5.15"]


def test_openai_client_lanza_error_sin_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAIClient lanza ValueError si no hay OPENAI_API_KEY."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIClient()
