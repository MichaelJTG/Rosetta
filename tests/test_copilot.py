"""Tests para copilot — consultas en lenguaje natural al corpus normativo."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_rag_mock() -> MagicMock:
    from rosetta.core.rag import FragmentoRecuperado

    fragmento = FragmentoRecuperado(
        control_id="A.8.24",
        marco="iso_27001_2022",
        nombre="Uso de la criptografía",
        texto="A.8.24: Se deben definir reglas para el uso de criptografía.",
        score=0.1,
    )
    mock = MagicMock()
    mock.recuperar = MagicMock(return_value=[fragmento])
    return mock


def _make_llm_mock(respuesta: str) -> MagicMock:
    from rosetta.llm.base import CompletionResult

    result = CompletionResult(content=respuesta, tool_calls=[], stop_reason="end_turn", raw={})
    mock = MagicMock()
    mock.completar = AsyncMock(return_value=result)
    return mock


@pytest.mark.asyncio
async def test_consultar_copilot_devuelve_response() -> None:
    from rosetta.core.copilot import CopilotQuery, CopilotResponse, consultar_copilot

    query = CopilotQuery(
        pregunta="¿Qué control ISO aplica cuando se expone una clave de cifrado?",
        contexto="Sistema de pagos en producción",
    )

    resultado = await consultar_copilot(
        query=query,
        llm=_make_llm_mock("El control A.8.24 aplica porque..."),
        rag=_make_rag_mock(),
    )

    assert isinstance(resultado, CopilotResponse)
    assert len(resultado.respuesta) > 0
    assert isinstance(resultado.fuentes, list)
    assert 0.0 <= resultado.confianza <= 1.0


@pytest.mark.asyncio
async def test_consultar_copilot_incluye_fuentes_rag() -> None:
    from rosetta.core.copilot import CopilotQuery, consultar_copilot

    query = CopilotQuery(pregunta="¿Qué es A.8.24?")

    resultado = await consultar_copilot(
        query=query,
        llm=_make_llm_mock("A.8.24 regula el uso de criptografía en la organización."),
        rag=_make_rag_mock(),
    )

    assert "A.8.24" in resultado.fuentes


@pytest.mark.asyncio
async def test_consultar_copilot_sin_rag_sin_fuentes() -> None:
    from rosetta.core.copilot import CopilotQuery, consultar_copilot

    rag_vacio = MagicMock()
    rag_vacio.recuperar = MagicMock(return_value=[])

    query = CopilotQuery(pregunta="¿Qué es DORA?")

    resultado = await consultar_copilot(
        query=query,
        llm=_make_llm_mock("DORA es el reglamento europeo de resiliencia digital."),
        rag=rag_vacio,
    )

    assert resultado.fuentes == []


@pytest.mark.asyncio
async def test_consultar_copilot_confianza_baja_sin_contexto() -> None:
    from rosetta.core.copilot import CopilotQuery, consultar_copilot

    rag_vacio = MagicMock()
    rag_vacio.recuperar = MagicMock(return_value=[])

    query = CopilotQuery(pregunta="¿Cuántos controles tiene ISO 27001?")

    resultado = await consultar_copilot(
        query=query,
        llm=_make_llm_mock("ISO 27001:2022 tiene 93 controles."),
        rag=rag_vacio,
    )

    assert resultado.confianza < 1.0
