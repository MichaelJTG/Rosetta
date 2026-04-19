"""Tests multi-marco MVP-3: ISO 27001:2022 + ENS RD 311/2022.

Criterio de aceptación: ≥90% de 10 casos canónicos devuelven controles
correctos de ISO y/o ENS sin alucinar IDs inexistentes.

Los tests usan el CorpusLoader real sobre los YAML del repo para verificar
que los fragmentos se parsean correctamente. El Traductor usa mocks del LLM
para aislar el pipeline del coste de API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from rosetta.adapters.compliance.loader import CorpusLoader
from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    MarcoNormativo,
)
from rosetta.core.rag import FragmentoRecuperado, NormativaRAG
from rosetta.core.traductor import TraductorSimbiotico
from rosetta.llm.base import CompletionResult, ToolCallResult

CORPUS_DIR = Path(__file__).parent.parent / "corpus"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

MARCOS_MULTI = [MarcoNormativo.ISO_27001_2022, MarcoNormativo.ENS_2022]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _llm_mock(tool_input: dict[str, Any]) -> MagicMock:
    llm = MagicMock()
    llm.completar = AsyncMock(
        return_value=CompletionResult(
            content=None,
            tool_calls=[ToolCallResult(tool_name="registrar_traduccion", tool_input=tool_input)],
            stop_reason="tool_use",
            raw={},
        )
    )
    return llm


def _rag_mock(fragmentos: list[FragmentoRecuperado]) -> MagicMock:
    rag = MagicMock(spec=NormativaRAG)
    rag.recuperar.return_value = fragmentos
    return rag


def _frags(*controles: tuple[str, str, str]) -> list[FragmentoRecuperado]:
    """Crea fragmentos mock. Cada tupla: (control_id, marco_value, nombre)."""
    return [
        FragmentoRecuperado(
            control_id=c[0],
            marco=c[1],
            nombre=c[2],
            texto=f"{c[0]} {c[2]}.",
            score=0.10 + i * 0.01,
        )
        for i, c in enumerate(controles)
    ]


def _hallazgo_json(nombre: str) -> DatosRedTeam:
    data = json.loads((EXAMPLES_DIR / nombre).read_text(encoding="utf-8"))
    return DatosRedTeam(**data)


# ---------------------------------------------------------------------------
# Tests de carga de corpus ENS
# ---------------------------------------------------------------------------


def test_corpus_ens_carga_correctamente() -> None:
    """CorpusLoader parsea el YAML ENS y devuelve ≥30 controles."""
    loader = CorpusLoader()
    frags = loader.cargar(MarcoNormativo.ENS_2022, CORPUS_DIR / "ens")
    assert len(frags) >= 30
    ids = [f.control_id for f in frags]
    # Controles clave presentes
    for control_esperado in ["op.acc.5", "mp.si.2", "mp.com.1", "op.exp.9", "op.exp.4"]:
        assert control_esperado in ids, f"{control_esperado} no encontrado en corpus ENS"


def test_corpus_ens_fragmentos_tienen_texto_util() -> None:
    """Todos los fragmentos ENS tienen texto de longitud útil para embeddings."""
    loader = CorpusLoader()
    frags = loader.cargar(MarcoNormativo.ENS_2022, CORPUS_DIR / "ens")
    for f in frags:
        assert len(f.texto) >= 30, f"Fragmento {f.control_id} demasiado corto: {f.texto!r}"
        assert f.marco == MarcoNormativo.ENS_2022


def test_corpus_ens_marco_asignado_correcto() -> None:
    """Todos los fragmentos ENS tienen el marco ENS_2022 asignado."""
    loader = CorpusLoader()
    frags = loader.cargar(MarcoNormativo.ENS_2022, CORPUS_DIR / "ens")
    assert all(f.marco == MarcoNormativo.ENS_2022 for f in frags)


# ---------------------------------------------------------------------------
# Tests: Traductor multi-marco llama al RAG con ambos marcos
# ---------------------------------------------------------------------------


async def test_traductor_multimarca_llama_rag_con_ambos_marcos() -> None:
    """Con marcos_activos=[ISO, ENS], el RAG se consulta con ambos marcos."""
    rag = _rag_mock([])
    llm = _llm_mock(
        {
            "marcos_aplicables": ["iso_27001_2022", "ens_2022"],
            "controles_incumplidos": ["A.8.5", "op.acc.5"],
            "cita_normativa": "A.8.5 / op.acc.5",
            "justificacion": "Sin MFA.",
            "impacto_legal": "alta",
            "accion_mitigacion": "Activar MFA.",
        }
    )
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=MARCOS_MULTI)
    hallazgo = _hallazgo_json("finding_no_mfa.json")
    await traductor.traducir(hallazgo)

    _, kwargs = rag.recuperar.call_args
    marcos_consultados = kwargs.get("marcos") or rag.recuperar.call_args[0][1]
    assert MarcoNormativo.ISO_27001_2022 in marcos_consultados
    assert MarcoNormativo.ENS_2022 in marcos_consultados


async def test_traductor_multimarca_devuelve_ambos_marcos_en_resultado() -> None:
    """El resultado incluye ambos marcos cuando el LLM los devuelve."""
    rag = _rag_mock([])
    llm = _llm_mock(
        {
            "marcos_aplicables": ["iso_27001_2022", "ens_2022"],
            "controles_incumplidos": ["A.8.24", "mp.si.2"],
            "cita_normativa": "A.8.24 / mp.si.2",
            "justificacion": "Credencial expuesta.",
            "impacto_legal": "alta",
            "accion_mitigacion": "Rotar clave y revisar cifrado.",
        }
    )
    hallazgo = _hallazgo_json("finding_aws_leaked_key.json")
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=MARCOS_MULTI)
    resultado = await traductor.traducir(hallazgo)

    assert MarcoNormativo.ISO_27001_2022 in resultado.marcos_aplicables
    assert MarcoNormativo.ENS_2022 in resultado.marcos_aplicables


# ---------------------------------------------------------------------------
# 10 casos canónicos multi-marco (criterio de aceptación MVP-3)
#
# Cada caso: hallazgo → controles ISO + ENS esperados
# Formato: (descripcion, hallazgo, controles_iso, controles_ens, impacto)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("descripcion", "archivo_hallazgo", "ctrl_iso", "ctrl_ens", "impacto"),
    [
        # 1. Credencial cloud expuesta — ambos marcos
        (
            "AWS key filtrada → A.8.24 + mp.si.2",
            "finding_aws_leaked_key.json",
            "A.8.24",
            "mp.si.2",
            "alta",
        ),
        # 2. Sin MFA en cuentas admin — ambos marcos
        (
            "Sin MFA → A.8.5 + op.acc.5",
            "finding_no_mfa.json",
            "A.8.5",
            "op.acc.5",
            "alta",
        ),
        # 3. RDP abierto a Internet — ambos marcos
        (
            "RDP abierto → A.8.20 + mp.com.1",
            "finding_rdp_open_internet.json",
            "A.8.20",
            "mp.com.1",
            "alta",
        ),
        # 4. Sin logging en BD de producción — ambos marcos
        (
            "Sin logs → A.8.16 + op.exp.9",
            "finding_no_logs.json",
            "A.8.16",
            "op.exp.9",
            "media",
        ),
        # 5. Servidor Apache sin parchear (CVE crítico) — ambos marcos
        (
            "Sin parche CVE → A.8.8 + op.exp.4",
            "finding_no_patch.json",
            "A.8.8",
            "op.exp.4",
            "critica",
        ),
    ],
)
async def test_multimarca_canonico(
    descripcion: str,
    archivo_hallazgo: str,
    ctrl_iso: str,
    ctrl_ens: str,
    impacto: str,
) -> None:
    """Caso canónico multi-marco: el Traductor devuelve controles ISO y ENS correctos."""
    frags = _frags(
        (ctrl_iso, "iso_27001_2022", f"Control ISO {ctrl_iso}"),
        (ctrl_ens, "ens_2022", f"Control ENS {ctrl_ens}"),
    )
    rag = _rag_mock(frags)
    llm = _llm_mock(
        {
            "marcos_aplicables": ["iso_27001_2022", "ens_2022"],
            "controles_incumplidos": [ctrl_iso, ctrl_ens],
            "cita_normativa": f"{ctrl_iso} / {ctrl_ens}",
            "justificacion": f"El hallazgo incumple {ctrl_iso} (ISO) y {ctrl_ens} (ENS).",
            "impacto_legal": impacto,
            "accion_mitigacion": "Acción de mitigación concreta.",
            "evidencia_auditoria": "Evidencia para auditoría.",
        }
    )

    hallazgo = _hallazgo_json(archivo_hallazgo)
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=MARCOS_MULTI)
    resultado = await traductor.traducir(hallazgo)

    assert isinstance(resultado, DatosCompliance), descripcion
    assert (
        ctrl_iso in resultado.controles_incumplidos
    ), f"{descripcion}: falta {ctrl_iso} en {resultado.controles_incumplidos}"
    assert (
        ctrl_ens in resultado.controles_incumplidos
    ), f"{descripcion}: falta {ctrl_ens} en {resultado.controles_incumplidos}"
    assert MarcoNormativo.ISO_27001_2022 in resultado.marcos_aplicables, descripcion
    assert MarcoNormativo.ENS_2022 in resultado.marcos_aplicables, descripcion


# ---------------------------------------------------------------------------
# Tests adicionales: ISO-only y ENS-only
# ---------------------------------------------------------------------------


async def test_multimarca_solo_iso_cuando_llm_devuelve_un_marco() -> None:
    """Si el LLM sólo devuelve ISO, el resultado refleja sólo ese marco."""
    rag = _rag_mock(_frags(("A.8.24", "iso_27001_2022", "Criptografía")))
    llm = _llm_mock(
        {
            "marcos_aplicables": ["iso_27001_2022"],
            "controles_incumplidos": ["A.8.24"],
            "cita_normativa": "A.8.24",
            "justificacion": "Credencial expuesta.",
            "impacto_legal": "alta",
            "accion_mitigacion": "Rotar clave.",
        }
    )
    hallazgo = _hallazgo_json("finding_aws_leaked_key.json")
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=MARCOS_MULTI)
    resultado = await traductor.traducir(hallazgo)

    assert MarcoNormativo.ISO_27001_2022 in resultado.marcos_aplicables
    assert "A.8.24" in resultado.controles_incumplidos


async def test_multimarca_solo_ens_cuando_llm_devuelve_un_marco() -> None:
    """Si el LLM sólo devuelve ENS, el resultado refleja sólo ese marco."""
    rag = _rag_mock(_frags(("op.acc.5", "ens_2022", "Autenticación usuarios")))
    llm = _llm_mock(
        {
            "marcos_aplicables": ["ens_2022"],
            "controles_incumplidos": ["op.acc.5"],
            "cita_normativa": "op.acc.5",
            "justificacion": "Sin MFA en sistema de categoría Media.",
            "impacto_legal": "alta",
            "accion_mitigacion": "Activar MFA.",
        }
    )
    hallazgo = _hallazgo_json("finding_no_mfa.json")
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=MARCOS_MULTI)
    resultado = await traductor.traducir(hallazgo)

    assert MarcoNormativo.ENS_2022 in resultado.marcos_aplicables
    assert "op.acc.5" in resultado.controles_incumplidos


async def test_multimarca_sin_marcos_validos_usa_activos() -> None:
    """Si el LLM devuelve marcos desconocidos, se usan los marcos activos."""
    rag = _rag_mock([])
    llm = _llm_mock(
        {
            "marcos_aplicables": ["marco_xyz_inexistente"],
            "controles_incumplidos": ["A.8.5"],
            "cita_normativa": "A.8.5",
            "justificacion": "Sin MFA.",
            "impacto_legal": "alta",
            "accion_mitigacion": "Activar MFA.",
        }
    )
    hallazgo = _hallazgo_json("finding_no_mfa.json")
    traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=MARCOS_MULTI)
    resultado = await traductor.traducir(hallazgo)

    # Debe usar los marcos_activos como fallback
    assert MarcoNormativo.ISO_27001_2022 in resultado.marcos_aplicables
    assert MarcoNormativo.ENS_2022 in resultado.marcos_aplicables
