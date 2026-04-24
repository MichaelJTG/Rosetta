"""Tests para attack_chain — análisis de cadena de ataque MITRE ATT&CK."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from rosetta.core.models import DatosRedTeam, FuenteRedTeam, Severidad


@pytest.fixture
def hallazgo_aws() -> DatosRedTeam:
    return DatosRedTeam(
        origen=FuenteRedTeam.GITHUB_SECRETS,
        activo_detectado="AWS_KEY en repo público",
        evidencia="https://github.com/org/repo/commit/abc",
        vector_ataque="Credencial cloud expuesta en código fuente",
        dificultad_explotacion=Severidad.BAJA,
    )


def _make_llm_mock_cadena(tool_input: dict) -> MagicMock:
    from rosetta.llm.base import CompletionResult, ToolCallResult

    tc = ToolCallResult(tool_name="registrar_cadena", tool_input=tool_input)
    result = CompletionResult(content=None, tool_calls=[tc], stop_reason="tool_use", raw={})
    mock = MagicMock()
    mock.completar = AsyncMock(return_value=result)
    return mock


@pytest.mark.asyncio
async def test_analizar_cadena_devuelve_ataque_encadenado(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.core.attack_chain import AtaqueEncadenado, analizar_cadena

    tool_input = {
        "pasos": [
            {"tecnica_mitre": "T1552.001", "descripcion": "Acceso a credencial en código fuente"},
            {"tecnica_mitre": "T1078.004", "descripcion": "Uso de credencial cloud válida"},
            {"tecnica_mitre": "T1530", "descripcion": "Acceso a datos en bucket S3"},
        ],
        "tacticas": ["Credential Access", "Persistence", "Collection"],
        "impacto_maximo": "alta",
    }

    resultado = await analizar_cadena(hallazgo=hallazgo_aws, llm=_make_llm_mock_cadena(tool_input))

    assert isinstance(resultado, AtaqueEncadenado)
    assert len(resultado.pasos) == 3
    assert "T1552.001" in [p.tecnica_mitre for p in resultado.pasos]
    assert "Credential Access" in resultado.tacticas
    assert resultado.impacto_maximo == Severidad.ALTA


@pytest.mark.asyncio
async def test_analizar_cadena_sin_toolcall_devuelve_cadena_vacia(
    hallazgo_aws: DatosRedTeam,
) -> None:
    from rosetta.core.attack_chain import AtaqueEncadenado, analizar_cadena
    from rosetta.llm.base import CompletionResult

    result = CompletionResult(
        content="no puedo analizar", tool_calls=[], stop_reason="end_turn", raw={}
    )
    llm = MagicMock()
    llm.completar = AsyncMock(return_value=result)

    resultado = await analizar_cadena(hallazgo=hallazgo_aws, llm=llm)

    assert isinstance(resultado, AtaqueEncadenado)
    assert len(resultado.pasos) == 0
    assert resultado.impacto_maximo == Severidad.INFORMATIVA


@pytest.mark.asyncio
async def test_analizar_cadena_paso_tiene_campos(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.core.attack_chain import Paso, analizar_cadena

    tool_input = {
        "pasos": [{"tecnica_mitre": "T1059.001", "descripcion": "Ejecución PowerShell"}],
        "tacticas": ["Execution"],
        "impacto_maximo": "media",
    }

    resultado = await analizar_cadena(hallazgo=hallazgo_aws, llm=_make_llm_mock_cadena(tool_input))
    paso = resultado.pasos[0]
    assert isinstance(paso, Paso)
    assert paso.tecnica_mitre == "T1059.001"
    assert "PowerShell" in paso.descripcion
