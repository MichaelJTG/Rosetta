"""Tests del DriftDetector — MVP-5.

Cobertura objetivo: ≥80% de core/drift.py.
Sin llamadas reales al LLM — todo mockeado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from rosetta.core.drift import DriftDetector
from rosetta.core.models import ResultadoDrift, Severidad
from rosetta.llm.base import CompletionResult, ToolCallResult

PROCEDURES_DIR = Path(__file__).parent.parent / "examples" / "procedures"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _llm_mock(tool_input: dict[str, Any]) -> MagicMock:
    llm = MagicMock()
    llm.completar = AsyncMock(
        return_value=CompletionResult(
            content=None,
            tool_calls=[ToolCallResult(tool_name="registrar_drift", tool_input=tool_input)],
            stop_reason="tool_use",
            raw={},
        )
    )
    return llm


def _llm_sin_tool() -> MagicMock:
    llm = MagicMock()
    llm.completar = AsyncMock(
        return_value=CompletionResult(
            content="No puedo analizar.",
            tool_calls=[],
            stop_reason="end_turn",
            raw={},
        )
    )
    return llm


# ---------------------------------------------------------------------------
# Caso canónico: PRO-IAM-001 con drift real
# ---------------------------------------------------------------------------


async def test_drift_iam_detecta_cuentas_inactivas() -> None:
    """Caso canónico del mentor Carlos: PRO-IAM-001 vs cuentas inactivas sin desactivar."""
    texto_proc = (PROCEDURES_DIR / "PRO-IAM-001.md").read_text(encoding="utf-8")
    observaciones = [
        "12 cuentas de usuario con más de 90 días sin actividad y estado 'activo'",
        "3 cuentas con perfil de administrador sin actividad en 45 días",
        "Tarea programada de desactivación automática no ejecutada en los últimos 60 días",
    ]

    llm = _llm_mock(
        {
            "drift_detectado": True,
            "descripcion_drift": (
                "El procedimiento establece desactivación automática a los 30 días de inactividad "
                "(punto 4.2) y a los 15 días para administradores (4.3). "
                "Se observan 12 cuentas con >90 días inactivas sin desactivar y 3 administradores "
                "con >45 días inactivos. La tarea programada no ha funcionado en 60 días."
            ),
            "fragmento_afectado": (
                "4.2. Las cuentas sin actividad durante más de 30 días se desactivan "
                "automáticamente mediante tarea programada en Active Directory."
            ),
            "redaccion_propuesta": (
                "4.2. Las cuentas sin actividad durante más de 30 días se desactivan "
                "automáticamente. Se verificará semanalmente el correcto funcionamiento "
                "de la tarea programada mediante alertas al equipo de IT. "
                "El incumplimiento de la desactivación se tratará como incidente de seguridad."
            ),
            "evidencias": [
                "12 cuentas activas con último login > 90 días",
                "3 cuentas admin activas con último login > 45 días",
                "Tarea programada sin ejecución en 60 días",
            ],
            "controles_afectados": ["A.5.18", "op.acc.4", "A.5.15"],
            "impacto": "alta",
        }
    )

    detector = DriftDetector(llm=llm)
    resultado = await detector.detectar_drift("PRO-IAM-001", texto_proc, observaciones)

    assert isinstance(resultado, ResultadoDrift)
    assert resultado.drift_detectado is True
    assert resultado.impacto == Severidad.ALTA
    assert "A.5.18" in resultado.controles_afectados
    assert "op.acc.4" in resultado.controles_afectados
    assert len(resultado.evidencias) >= 2
    assert resultado.fragmento_afectado != ""
    assert resultado.redaccion_propuesta != ""


async def test_drift_sin_desviacion_devuelve_false() -> None:
    """Si la práctica real cumple el procedimiento, drift_detectado=False."""
    llm = _llm_mock(
        {
            "drift_detectado": False,
            "descripcion_drift": "Las observaciones son consistentes con el procedimiento PRO-IAM-001.",
            "fragmento_afectado": "",
            "redaccion_propuesta": "",
            "evidencias": [],
            "controles_afectados": [],
            "impacto": "informativa",
        }
    )

    detector = DriftDetector(llm=llm)
    resultado = await detector.detectar_drift(
        "PRO-IAM-001",
        "Las cuentas inactivas >30 días se desactivan automáticamente.",
        ["Todas las cuentas inactivas >30 días están desactivadas. Tarea programada: OK."],
    )

    assert resultado.drift_detectado is False
    assert resultado.impacto == Severidad.INFORMATIVA


# ---------------------------------------------------------------------------
# Tests de pipeline y estructura
# ---------------------------------------------------------------------------


async def test_drift_llm_sin_tool_call_lanza_error() -> None:
    """Si el LLM no invoca registrar_drift, se lanza ValueError."""
    detector = DriftDetector(llm=_llm_sin_tool())
    with pytest.raises(ValueError, match="registrar_drift"):
        await detector.detectar_drift("PRO-TEST-001", "Texto del procedimiento.", ["Observación."])


def test_drift_constructor_sin_llm_lanza_error() -> None:
    """DriftDetector sin LLM lanza ValueError."""
    with pytest.raises((ValueError, TypeError)):
        DriftDetector(llm=None)  # type: ignore[arg-type]


async def test_drift_impacto_invalido_usa_media() -> None:
    """Impacto desconocido del LLM cae a Severidad.MEDIA."""
    llm = _llm_mock(
        {
            "drift_detectado": True,
            "descripcion_drift": "Hay drift.",
            "impacto": "valor_xyz_desconocido",
        }
    )
    detector = DriftDetector(llm=llm)
    resultado = await detector.detectar_drift("PRO-X", "Texto.", ["Obs."])
    assert resultado.impacto == Severidad.MEDIA


async def test_drift_llm_llamado_con_prompt_correcto() -> None:
    """El LLM recibe el procedimiento_id y las observaciones en el prompt."""
    llm = _llm_mock({"drift_detectado": False, "descripcion_drift": "Sin drift."})
    detector = DriftDetector(llm=llm)
    await detector.detectar_drift(
        "PRO-IAM-001",
        "Texto del procedimiento aquí.",
        ["Obs 1", "Obs 2"],
    )

    llm.completar.assert_called_once()
    call_kwargs = llm.completar.call_args[1]
    mensajes = call_kwargs.get("messages") or llm.completar.call_args[0][1]
    prompt_usuario = mensajes[0].content
    assert "PRO-IAM-001" in prompt_usuario
    assert "Obs 1" in prompt_usuario
    assert "Texto del procedimiento aquí." in prompt_usuario


async def test_drift_resultado_incluye_procedimiento_id() -> None:
    """El ResultadoDrift siempre incluye el procedimiento_id."""
    llm = _llm_mock({"drift_detectado": False, "descripcion_drift": "Sin drift."})
    detector = DriftDetector(llm=llm)
    resultado = await detector.detectar_drift("PRO-CUSTOM-999", "Texto.", ["Obs."])
    assert resultado.procedimiento_id == "PRO-CUSTOM-999"


# ---------------------------------------------------------------------------
# Tests de carga del procedimiento canónico
# ---------------------------------------------------------------------------


def test_procedimiento_iam_existe_y_es_legible() -> None:
    """El procedimiento canónico PRO-IAM-001.md existe y contiene secciones clave."""
    proc_path = PROCEDURES_DIR / "PRO-IAM-001.md"
    assert proc_path.exists(), "examples/procedures/PRO-IAM-001.md debe existir"
    texto = proc_path.read_text(encoding="utf-8")
    assert "30 días" in texto
    assert "op.acc.4" in texto
    assert "A.5.18" in texto
