"""Tests para remediation_validator — verificación de remediaciones."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from rosetta.core.models import (
    DatosCompliance,
    DossierMultimarco,
    MarcoNormativo,
    Severidad,
    Traduccion,
    ValidacionResult,
)


@pytest.fixture
def dossier_iso() -> DossierMultimarco:
    datos = DatosCompliance(
        marcos_aplicables=[MarcoNormativo.ISO_27001_2022],
        controles_incumplidos=["A.8.24"],
        cita_normativa="A.8.24 Uso de la criptografía",
        justificacion="Credencial expuesta",
        impacto_legal=Severidad.ALTA,
        accion_mitigacion="Rotar credencial y activar rotación automática",
    )
    t = Traduccion(
        marco=MarcoNormativo.ISO_27001_2022,
        datos=datos,
        agente_id="translator-iso",
        fragmentos_usados=["A.8.24"],
        confianza=0.9,
    )
    v = ValidacionResult(
        traduccion_id="translator-iso:iso_27001_2022",
        valida=True,
        confianza=0.9,
    )
    return DossierMultimarco(
        hallazgo_id="SEC-001",
        traducciones=[t],
        validaciones=[v],
        marcos_procesados=[MarcoNormativo.ISO_27001_2022],
    )


def _llm_remediacion(tool_input: dict) -> MagicMock:
    from rosetta.llm.base import CompletionResult, ToolCallResult

    tc = ToolCallResult(tool_name="registrar_remediacion", tool_input=tool_input)
    result = CompletionResult(content=None, tool_calls=[tc], stop_reason="tool_use", raw={})
    mock = MagicMock()
    mock.completar = AsyncMock(return_value=result)
    return mock


@pytest.mark.asyncio
async def test_verificar_remediacion_aprobada(dossier_iso: DossierMultimarco) -> None:
    from rosetta.core.remediation_validator import RemediacionResult, verificar_remediacion

    tool_input = {
        "remediado": True,
        "evidencias_validacion": ["Credencial rotada el 2026-04-23", "MFA activado"],
        "controles_cerrados": ["A.8.24"],
        "controles_pendientes": [],
        "comentario": "Remediación completa verificada.",
    }

    resultado = await verificar_remediacion(
        dossier=dossier_iso,
        evidencias=["Ticket JIRA-123 cerrado", "Log rotación disponible"],
        llm=_llm_remediacion(tool_input),
    )

    assert isinstance(resultado, RemediacionResult)
    assert resultado.remediado is True
    assert "A.8.24" in resultado.controles_cerrados
    assert len(resultado.controles_pendientes) == 0


@pytest.mark.asyncio
async def test_verificar_remediacion_parcial(dossier_iso: DossierMultimarco) -> None:
    from rosetta.core.remediation_validator import verificar_remediacion

    tool_input = {
        "remediado": False,
        "evidencias_validacion": ["Credencial rotada pero sin MFA"],
        "controles_cerrados": [],
        "controles_pendientes": ["A.8.24"],
        "comentario": "Falta configurar MFA.",
    }

    resultado = await verificar_remediacion(
        dossier=dossier_iso,
        evidencias=["Solo rotada la key"],
        llm=_llm_remediacion(tool_input),
    )

    assert resultado.remediado is False
    assert "A.8.24" in resultado.controles_pendientes


@pytest.mark.asyncio
async def test_verificar_remediacion_sin_toolcall_devuelve_no_remediado(
    dossier_iso: DossierMultimarco,
) -> None:
    from rosetta.core.remediation_validator import RemediacionResult, verificar_remediacion
    from rosetta.llm.base import CompletionResult

    result = CompletionResult(content="no sé", tool_calls=[], stop_reason="end_turn", raw={})
    llm = MagicMock()
    llm.completar = AsyncMock(return_value=result)

    resultado = await verificar_remediacion(dossier=dossier_iso, evidencias=[], llm=llm)

    assert isinstance(resultado, RemediacionResult)
    assert resultado.remediado is False
