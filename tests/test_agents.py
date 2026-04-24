"""Tests para la arquitectura multi-agente de ROSETTA (FASE 5).

Cubre:
  - BaseTranslator y subclases especialistas (ISO, ENS, NIS2)
  - Soundwave scheduler (paralelismo asyncio)
  - Validador critic agent
  - RosettaOrchestrator (integración completa)

Sin llamadas reales a LLM ni a ChromaDB — todo mockeado.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    DossierMultimarco,
    FuenteRedTeam,
    MarcoNormativo,
    ModelProfile,
    Severidad,
    Traduccion,
    ValidacionResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_datos_compliance(marco: MarcoNormativo) -> DatosCompliance:
    return DatosCompliance(
        marcos_aplicables=[marco],
        controles_incumplidos=["A.8.24"],
        cita_normativa="A.8.24 Uso de la criptografía",
        justificacion="Credencial expuesta incumple A.8.24",
        impacto_legal=Severidad.ALTA,
        accion_mitigacion="Rotar credencial y activar rotación automática",
    )


def _make_traduccion(marco: MarcoNormativo, agente_id: str = "test-agent") -> Traduccion:
    return Traduccion(
        marco=marco,
        datos=_make_datos_compliance(marco),
        agente_id=agente_id,
        fragmentos_usados=["A.8.24"],
        confianza=0.9,
    )


def _make_llm_mock(tool_input: dict[str, Any]) -> MagicMock:
    from rosetta.llm.base import CompletionResult, ToolCallResult

    tool_call = ToolCallResult(tool_name="registrar_traduccion", tool_input=tool_input)
    result = CompletionResult(
        content=None,
        tool_calls=[tool_call],
        stop_reason="tool_use",
        raw={},
    )
    mock = MagicMock()
    mock.completar = AsyncMock(return_value=result)
    return mock


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


@pytest.fixture
def hallazgo_aws() -> DatosRedTeam:
    return DatosRedTeam(
        origen=FuenteRedTeam.GITHUB_SECRETS,
        activo_detectado="AWS_KEY en repo público",
        evidencia="https://github.com/org/repo/commit/abc",
        vector_ataque="Credencial cloud expuesta",
        dificultad_explotacion=Severidad.BAJA,
    )


# ---------------------------------------------------------------------------
# Tests — ModelProfile
# ---------------------------------------------------------------------------


def test_model_profile_values() -> None:
    assert ModelProfile.ECO == "eco"
    assert ModelProfile.MAX == "max"
    assert ModelProfile.TEST == "test"


# ---------------------------------------------------------------------------
# Tests — Traduccion / DossierMultimarco
# ---------------------------------------------------------------------------


def test_traduccion_campos() -> None:
    t = _make_traduccion(MarcoNormativo.ISO_27001_2022, "translator-iso")
    assert t.marco == MarcoNormativo.ISO_27001_2022
    assert t.agente_id == "translator-iso"
    assert "A.8.24" in t.fragmentos_usados
    assert 0.0 <= t.confianza <= 1.0


def test_dossier_traducciones_validas() -> None:
    t_iso = _make_traduccion(MarcoNormativo.ISO_27001_2022, "translator-iso")
    t_ens = _make_traduccion(MarcoNormativo.ENS_2022, "translator-ens")

    v_iso = ValidacionResult(
        traduccion_id="translator-iso:iso_27001_2022",
        valida=True,
        confianza=0.9,
    )
    v_ens = ValidacionResult(
        traduccion_id="translator-ens:ens_2022",
        valida=False,
        problemas=["control no existe en ENS"],
        confianza=0.2,
    )

    dossier = DossierMultimarco(
        hallazgo_id="SEC-001",
        traducciones=[t_iso, t_ens],
        validaciones=[v_iso, v_ens],
        marcos_procesados=[MarcoNormativo.ISO_27001_2022, MarcoNormativo.ENS_2022],
    )

    validas = dossier.traducciones_validas
    assert len(validas) == 1
    assert validas[0].marco == MarcoNormativo.ISO_27001_2022


def test_dossier_controles_unicos_deduplica() -> None:
    t_iso = _make_traduccion(MarcoNormativo.ISO_27001_2022)
    t_ens = Traduccion(
        marco=MarcoNormativo.ENS_2022,
        datos=DatosCompliance(
            marcos_aplicables=[MarcoNormativo.ENS_2022],
            controles_incumplidos=["A.8.24", "op.acc.5"],
            cita_normativa="op.acc.5 Control de acceso",
            justificacion="Incumple op.acc.5",
            impacto_legal=Severidad.MEDIA,
            accion_mitigacion="Revisar política de acceso",
        ),
        agente_id="translator-ens",
    )

    dossier = DossierMultimarco(
        hallazgo_id="SEC-001",
        traducciones=[t_iso, t_ens],
    )

    unicos = dossier.controles_unicos
    assert len(unicos) == 2
    assert "A.8.24" in unicos
    assert "op.acc.5" in unicos


# ---------------------------------------------------------------------------
# Tests — BaseTranslator abstracto
# ---------------------------------------------------------------------------


def test_base_translator_es_abstracto() -> None:
    from rosetta.agents.translator.base import BaseTranslator

    with pytest.raises(TypeError):
        BaseTranslator(llm=MagicMock(), rag=MagicMock(), profile=ModelProfile.TEST)  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Tests — TraductorISO
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_iso_translator_traducir(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.iso import TraductorISO

    tool_input = {
        "marcos_aplicables": ["iso_27001_2022"],
        "controles_incumplidos": ["A.8.24"],
        "cita_normativa": "A.8.24 Uso de la criptografía",
        "justificacion": "Credencial expuesta incumple A.8.24",
        "impacto_legal": "alta",
        "accion_mitigacion": "Rotar credencial AWS",
    }

    agente = TraductorISO(
        llm=_make_llm_mock(tool_input),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    t = await agente.traducir(hallazgo_aws)

    assert isinstance(t, Traduccion)
    assert t.marco == MarcoNormativo.ISO_27001_2022
    assert "A.8.24" in t.datos.controles_incumplidos
    assert t.agente_id == agente.agente_id


@pytest.mark.asyncio
async def test_iso_translator_llm_sin_toolcall_lanza_error(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.iso import TraductorISO
    from rosetta.llm.base import CompletionResult

    result = CompletionResult(
        content="respuesta libre", tool_calls=[], stop_reason="end_turn", raw={}
    )
    llm = MagicMock()
    llm.completar = AsyncMock(return_value=result)

    agente = TraductorISO(llm=llm, rag=_make_rag_mock(), profile=ModelProfile.TEST)

    with pytest.raises(ValueError, match="registrar_traduccion"):
        await agente.traducir(hallazgo_aws)


# ---------------------------------------------------------------------------
# Tests — TraductorENS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ens_translator_marco_correcto(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.ens import TraductorENS

    tool_input = {
        "marcos_aplicables": ["ens_2022"],
        "controles_incumplidos": ["op.acc.5"],
        "cita_normativa": "op.acc.5 Control de acceso",
        "justificacion": "Credencial expuesta incumple op.acc.5",
        "impacto_legal": "alta",
        "accion_mitigacion": "Revisar política de acceso ENS",
    }

    agente = TraductorENS(
        llm=_make_llm_mock(tool_input),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    t = await agente.traducir(hallazgo_aws)
    assert t.marco == MarcoNormativo.ENS_2022


# ---------------------------------------------------------------------------
# Tests — TraductorNIS2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nis2_translator_marco_correcto(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.nis2 import TraductorNIS2

    tool_input = {
        "marcos_aplicables": ["nis2"],
        "controles_incumplidos": ["Art.21.2.h"],
        "cita_normativa": "Art.21.2.h Seguridad en la cadena de suministro",
        "justificacion": "Credencial expuesta afecta cadena de suministro NIS2",
        "impacto_legal": "alta",
        "accion_mitigacion": "Notificar incidente a ENISA en 72h",
    }

    agente = TraductorNIS2(
        llm=_make_llm_mock(tool_input),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    t = await agente.traducir(hallazgo_aws)
    assert t.marco == MarcoNormativo.NIS2


# ---------------------------------------------------------------------------
# Tests — Soundwave scheduler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_soundwave_ejecuta_en_paralelo(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.soundwave import Soundwave
    from rosetta.agents.translator.ens import TraductorENS
    from rosetta.agents.translator.iso import TraductorISO

    base_input = {
        "controles_incumplidos": ["A.8.24"],
        "cita_normativa": "A.8.24",
        "justificacion": "J",
        "impacto_legal": "alta",
        "accion_mitigacion": "Rotar",
    }

    t_iso = TraductorISO(
        llm=_make_llm_mock({**base_input, "marcos_aplicables": ["iso_27001_2022"]}),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )
    t_ens = TraductorENS(
        llm=_make_llm_mock({**base_input, "marcos_aplicables": ["ens_2022"]}),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    soundwave = Soundwave(max_concurrencia=4)
    traducciones = await soundwave.ejecutar_paralelo([t_iso, t_ens], hallazgo_aws)

    assert len(traducciones) == 2
    marcos = {t.marco for t in traducciones}
    assert MarcoNormativo.ISO_27001_2022 in marcos
    assert MarcoNormativo.ENS_2022 in marcos


@pytest.mark.asyncio
async def test_soundwave_maneja_errores_parciales(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.soundwave import Soundwave
    from rosetta.agents.translator.ens import TraductorENS
    from rosetta.agents.translator.iso import TraductorISO

    llm_falla = MagicMock()
    llm_falla.completar = AsyncMock(side_effect=RuntimeError("LLM timeout"))

    t_iso = TraductorISO(
        llm=_make_llm_mock(
            {
                "marcos_aplicables": ["iso_27001_2022"],
                "controles_incumplidos": ["A.8.24"],
                "cita_normativa": "A.8.24",
                "justificacion": "J",
                "impacto_legal": "alta",
                "accion_mitigacion": "Rotar",
            }
        ),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )
    t_ens = TraductorENS(llm=llm_falla, rag=_make_rag_mock(), profile=ModelProfile.TEST)

    soundwave = Soundwave(max_concurrencia=4)
    traducciones = await soundwave.ejecutar_paralelo([t_iso, t_ens], hallazgo_aws)

    assert len(traducciones) == 1
    assert traducciones[0].marco == MarcoNormativo.ISO_27001_2022


@pytest.mark.asyncio
async def test_soundwave_lista_vacia(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.soundwave import Soundwave

    soundwave = Soundwave(max_concurrencia=4)
    traducciones = await soundwave.ejecutar_paralelo([], hallazgo_aws)
    assert traducciones == []


# ---------------------------------------------------------------------------
# Tests — Validador
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validador_aprueba_traduccion_correcta(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.validator import Validador
    from rosetta.llm.base import CompletionResult, ToolCallResult

    val_input = {
        "valida": True,
        "problemas": [],
        "confianza": 0.95,
        "razonamiento": "Traducción correcta, controles fundamentados en RAG.",
    }
    tc = ToolCallResult(tool_name="registrar_validacion", tool_input=val_input)
    result = CompletionResult(content=None, tool_calls=[tc], stop_reason="tool_use", raw={})
    llm_mock = MagicMock()
    llm_mock.completar = AsyncMock(return_value=result)

    validador = Validador(llm=llm_mock, profile=ModelProfile.TEST)
    traduccion = _make_traduccion(MarcoNormativo.ISO_27001_2022)

    vr = await validador.validar(traduccion, hallazgo_aws)

    assert isinstance(vr, ValidacionResult)
    assert vr.valida is True
    assert vr.confianza > 0.8


@pytest.mark.asyncio
async def test_validador_rechaza_alucinacion(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.validator import Validador
    from rosetta.llm.base import CompletionResult, ToolCallResult

    val_input = {
        "valida": False,
        "problemas": ["Control A.99.99 no existe en corpus ISO"],
        "confianza": 0.1,
        "razonamiento": "Control inventado.",
    }
    tc = ToolCallResult(tool_name="registrar_validacion", tool_input=val_input)
    result = CompletionResult(content=None, tool_calls=[tc], stop_reason="tool_use", raw={})
    llm_mock = MagicMock()
    llm_mock.completar = AsyncMock(return_value=result)

    validador = Validador(llm=llm_mock, profile=ModelProfile.TEST)
    traduccion = Traduccion(
        marco=MarcoNormativo.ISO_27001_2022,
        datos=DatosCompliance(
            marcos_aplicables=[MarcoNormativo.ISO_27001_2022],
            controles_incumplidos=["A.99.99"],
            cita_normativa="A.99.99 Control inventado",
            justificacion="J",
            impacto_legal=Severidad.ALTA,
            accion_mitigacion="M",
        ),
        agente_id="translator-iso",
    )

    vr = await validador.validar(traduccion, hallazgo_aws)
    assert vr.valida is False
    assert len(vr.problemas) > 0


@pytest.mark.asyncio
async def test_validador_sin_toolcall_devuelve_invalido(hallazgo_aws: DatosRedTeam) -> None:
    """Si el LLM no invoca la tool, el validador devuelve resultado inválido seguro."""
    from rosetta.agents.validator import Validador
    from rosetta.llm.base import CompletionResult

    result = CompletionResult(
        content="no puedo validar", tool_calls=[], stop_reason="end_turn", raw={}
    )
    llm_mock = MagicMock()
    llm_mock.completar = AsyncMock(return_value=result)

    validador = Validador(llm=llm_mock, profile=ModelProfile.TEST)
    traduccion = _make_traduccion(MarcoNormativo.ISO_27001_2022)

    vr = await validador.validar(traduccion, hallazgo_aws)
    assert vr.valida is False
    assert "LLM no invocó" in vr.problemas[0]


# ---------------------------------------------------------------------------
# Tests — RosettaOrchestrator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_orquestador_produce_dossier(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.orchestrator import RosettaOrchestrator
    from rosetta.agents.soundwave import Soundwave
    from rosetta.agents.translator.iso import TraductorISO
    from rosetta.agents.validator import Validador
    from rosetta.llm.base import CompletionResult, ToolCallResult

    trad_input = {
        "marcos_aplicables": ["iso_27001_2022"],
        "controles_incumplidos": ["A.8.24"],
        "cita_normativa": "A.8.24",
        "justificacion": "J",
        "impacto_legal": "alta",
        "accion_mitigacion": "Rotar",
    }
    t_iso = TraductorISO(
        llm=_make_llm_mock(trad_input), rag=_make_rag_mock(), profile=ModelProfile.TEST
    )

    val_tc = ToolCallResult(
        tool_name="registrar_validacion",
        tool_input={"valida": True, "problemas": [], "confianza": 0.9, "razonamiento": "OK"},
    )
    val_result = CompletionResult(content=None, tool_calls=[val_tc], stop_reason="tool_use", raw={})
    val_llm = MagicMock()
    val_llm.completar = AsyncMock(return_value=val_result)
    validador = Validador(llm=val_llm, profile=ModelProfile.TEST)

    orquestador = RosettaOrchestrator(
        traductores={MarcoNormativo.ISO_27001_2022: t_iso},
        soundwave=Soundwave(max_concurrencia=4),
        validador=validador,
    )

    dossier = await orquestador.traducir(
        hallazgo=hallazgo_aws,
        hallazgo_id="SEC-TEST-001",
        marcos=[MarcoNormativo.ISO_27001_2022],
    )

    assert isinstance(dossier, DossierMultimarco)
    assert dossier.hallazgo_id == "SEC-TEST-001"
    assert len(dossier.traducciones) == 1
    assert len(dossier.validaciones) == 1
    assert MarcoNormativo.ISO_27001_2022 in dossier.marcos_procesados


@pytest.mark.asyncio
async def test_orquestador_marca_fallos_sin_traductor(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.orchestrator import RosettaOrchestrator
    from rosetta.agents.soundwave import Soundwave
    from rosetta.agents.validator import Validador

    orquestador = RosettaOrchestrator(
        traductores={},
        soundwave=Soundwave(max_concurrencia=4),
        validador=Validador(llm=MagicMock(), profile=ModelProfile.TEST),
    )

    dossier = await orquestador.traducir(
        hallazgo=hallazgo_aws,
        hallazgo_id="SEC-TEST-002",
        marcos=[MarcoNormativo.ISO_27001_2022],
    )

    assert MarcoNormativo.ISO_27001_2022 in dossier.marcos_fallidos
    assert len(dossier.traducciones) == 0


# ---------------------------------------------------------------------------
# Tests — Traductores DORA, RGPD, NIST, PCI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dora_translator_marco_correcto(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.dora import TraductorDORA

    tool_input = {
        "marcos_aplicables": ["dora"],
        "controles_incumplidos": ["Art.9.2"],
        "cita_normativa": "Art.9.2 Gestión de riesgos TIC",
        "justificacion": "Credencial expuesta afecta continuidad operativa bajo DORA",
        "impacto_legal": "alta",
        "accion_mitigacion": "Revocar credencial y notificar si impacta operativa",
    }

    agente = TraductorDORA(
        llm=_make_llm_mock(tool_input),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    t = await agente.traducir(hallazgo_aws)
    assert t.marco == MarcoNormativo.DORA
    assert "Art.9.2" in t.datos.controles_incumplidos


@pytest.mark.asyncio
async def test_rgpd_translator_marco_correcto(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.rgpd import TraductorRGPD

    tool_input = {
        "marcos_aplicables": ["rgpd"],
        "controles_incumplidos": ["Art.32.1"],
        "cita_normativa": "Art.32.1 Seguridad del tratamiento",
        "justificacion": "Credencial expuesta puede comprometer datos personales",
        "impacto_legal": "alta",
        "accion_mitigacion": "Evaluar brecha y notificar a AEPD si afecta datos personales",
    }

    agente = TraductorRGPD(
        llm=_make_llm_mock(tool_input),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    t = await agente.traducir(hallazgo_aws)
    assert t.marco == MarcoNormativo.RGPD
    assert "Art.32.1" in t.datos.controles_incumplidos


@pytest.mark.asyncio
async def test_nist_translator_marco_correcto(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.nist import TraductorNIST

    tool_input = {
        "marcos_aplicables": ["nist_csf_2"],
        "controles_incumplidos": ["PR.AA-02"],
        "cita_normativa": "PR.AA-02 Identities are proactively managed",
        "justificacion": "Credencial expuesta viola PR.AA-02 (gestión de identidades)",
        "impacto_legal": "alta",
        "accion_mitigacion": "Rotar credencial y activar MFA en identidades cloud",
    }

    agente = TraductorNIST(
        llm=_make_llm_mock(tool_input),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    t = await agente.traducir(hallazgo_aws)
    assert t.marco == MarcoNormativo.NIST_CSF_2
    assert "PR.AA-02" in t.datos.controles_incumplidos


@pytest.mark.asyncio
async def test_pci_translator_marco_correcto(hallazgo_aws: DatosRedTeam) -> None:
    from rosetta.agents.translator.pci import TraductorPCI

    tool_input = {
        "marcos_aplicables": ["pci_dss_4"],
        "controles_incumplidos": ["Req.8.3.9"],
        "cita_normativa": "Req.8.3.9 All user accounts and access privileges are reviewed",
        "justificacion": "Credencial cloud expuesta viola Req.8.3.9 si accede a CDE",
        "impacto_legal": "alta",
        "accion_mitigacion": "Revocar credencial y documentar incidente según Req.12.10",
    }

    agente = TraductorPCI(
        llm=_make_llm_mock(tool_input),
        rag=_make_rag_mock(),
        profile=ModelProfile.TEST,
    )

    t = await agente.traducir(hallazgo_aws)
    assert t.marco == MarcoNormativo.PCI_DSS_4
    assert "Req.8.3.9" in t.datos.controles_incumplidos
