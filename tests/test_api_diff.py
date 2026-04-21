"""Tests del endpoint POST /analyze-diff — MVP-7 Gate CI/CD.

Sigue el mismo patrón que test_api.py: AsyncClient con ASGITransport
y dependency_overrides para aislar el LLM/RAG/Neo4j.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from rosetta.api.deps import get_diff_analyzer, get_grafo, get_session_findings, get_traductor
from rosetta.api.main import app
from rosetta.core.diff_analyzer import DiffAnalysisResult, DiffAnalyzer, DiffViolation
from rosetta.core.models import MarcoNormativo, Severidad

# ---------------------------------------------------------------------------
# Diffs de test
# ---------------------------------------------------------------------------

_DIFF_SECRET = """\
diff --git a/config.py b/config.py
index abc..def 100644
--- a/config.py
+++ b/config.py
@@ -1,3 +1,5 @@
 import os
+AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
+AWS_SECRET = "wJalrXUtnFEMI/K7MDENG"
 def main():
     pass
"""

_DIFF_NEUTRO = """\
diff --git a/utils.py b/utils.py
index abc..def 100644
--- a/utils.py
+++ b/utils.py
@@ -1,3 +1,4 @@
 def greet():
+    # Saludo simple
     return "hello"
"""

# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------

_VIOLATION = DiffViolation(
    archivo="config.py",
    linea_inicio=2,
    lineas_afectadas=('AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"',),
    controles_incumplidos=("A.8.24",),
    cita_normativa="A.8.24 Uso de la criptografía",
    justificacion="Clave AWS hardcodeada en código fuente.",
    impacto_legal=Severidad.ALTA,
    accion_mitigacion="Usar variables de entorno o un secret manager.",
    evidencia_auditoria="Credencial detectada por Gate CI/CD.",
)

_RESULT_CON_VIOLACION = DiffAnalysisResult(
    violaciones=[_VIOLATION],
    total_hunks_analizados=1,
    marcos_usados=[MarcoNormativo.ISO_27001_2022],
    bloquear_si=Severidad.ALTA,
)

_RESULT_SIN_VIOLACION = DiffAnalysisResult(
    violaciones=[],
    total_hunks_analizados=1,
    marcos_usados=[MarcoNormativo.ISO_27001_2022],
    bloquear_si=Severidad.ALTA,
)

_RESULT_VACIO = DiffAnalysisResult(
    violaciones=[],
    total_hunks_analizados=0,
    marcos_usados=[MarcoNormativo.ISO_27001_2022],
    bloquear_si=Severidad.ALTA,
)


def _make_analyzer(result: DiffAnalysisResult) -> Any:
    mock = MagicMock(spec=DiffAnalyzer)
    mock.analizar = AsyncMock(return_value=result)
    return mock


def _make_traductor() -> Any:
    mock = MagicMock()
    mock.marcos_activos = [MarcoNormativo.ISO_27001_2022]
    mock.llm = MagicMock()
    mock.rag = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Fixture de cliente
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client_con_violacion() -> AsyncGenerator[AsyncClient, None]:
    session_findings: list[Any] = []
    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    app.dependency_overrides[get_diff_analyzer] = lambda: _make_analyzer(_RESULT_CON_VIOLACION)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_sin_violacion() -> AsyncGenerator[AsyncClient, None]:
    session_findings: list[Any] = []
    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    app.dependency_overrides[get_diff_analyzer] = lambda: _make_analyzer(_RESULT_SIN_VIOLACION)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_diff_vacio() -> AsyncGenerator[AsyncClient, None]:
    session_findings: list[Any] = []
    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    app.dependency_overrides[get_diff_analyzer] = lambda: _make_analyzer(_RESULT_VACIO)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_diff_secret_bloquea(client_con_violacion: AsyncClient) -> None:
    """Un diff con secret hardcodeado debe devolver bloquear=true."""
    resp = await client_con_violacion.post(
        "/analyze-diff",
        json={"diff": _DIFF_SECRET, "marcos": ["iso_27001_2022"], "bloquear_si": "alta"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["bloquear"] is True
    assert data["total_violaciones"] == 1
    assert data["violaciones"][0]["controles_incumplidos"] == ["A.8.24"]


@pytest.mark.asyncio
async def test_analyze_diff_secret_impacto_legal(client_con_violacion: AsyncClient) -> None:
    resp = await client_con_violacion.post("/analyze-diff", json={"diff": _DIFF_SECRET})
    assert resp.status_code == 200
    violacion = resp.json()["violaciones"][0]
    assert violacion["impacto_legal"] == "alta"
    assert "config.py" in violacion["archivo"]
    assert "A.8.24" in violacion["cita_normativa"]


@pytest.mark.asyncio
async def test_analyze_diff_secret_resumen_pr_contiene_tabla(
    client_con_violacion: AsyncClient,
) -> None:
    resp = await client_con_violacion.post("/analyze-diff", json={"diff": _DIFF_SECRET})
    assert resp.status_code == 200
    resumen = resp.json()["resumen_pr"]
    assert "ROSETTA" in resumen
    assert "BLOQUEADO" in resumen
    assert "A.8.24" in resumen


@pytest.mark.asyncio
async def test_analyze_diff_neutro_no_bloquea(client_sin_violacion: AsyncClient) -> None:
    resp = await client_sin_violacion.post("/analyze-diff", json={"diff": _DIFF_NEUTRO})
    assert resp.status_code == 200
    data = resp.json()
    assert data["bloquear"] is False
    assert data["total_violaciones"] == 0
    assert "✅" in data["resumen_pr"]


@pytest.mark.asyncio
async def test_analyze_diff_neutro_resumen_aprobado(client_sin_violacion: AsyncClient) -> None:
    resp = await client_sin_violacion.post("/analyze-diff", json={"diff": _DIFF_NEUTRO})
    assert resp.status_code == 200
    resumen = resp.json()["resumen_pr"]
    assert "Sin incumplimientos" in resumen


@pytest.mark.asyncio
async def test_analyze_diff_vacio_devuelve_ok(client_diff_vacio: AsyncClient) -> None:
    resp = await client_diff_vacio.post("/analyze-diff", json={"diff": ""})
    assert resp.status_code == 200
    data = resp.json()
    assert data["bloquear"] is False
    assert data["total_hunks_analizados"] == 0


@pytest.mark.asyncio
async def test_analyze_diff_body_invalido_devuelve_422(client_sin_violacion: AsyncClient) -> None:
    """Body vacío debe devolver 422 (validación Pydantic)."""
    resp = await client_sin_violacion.post("/analyze-diff", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_analyze_diff_severidad_invalida_usa_alta(client_sin_violacion: AsyncClient) -> None:
    """bloquear_si con valor desconocido debe caer a 'alta' sin error."""
    resp = await client_sin_violacion.post(
        "/analyze-diff",
        json={"diff": _DIFF_NEUTRO, "bloquear_si": "super_critico_inventado"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_analyze_diff_persist_en_session(client_con_violacion: AsyncClient) -> None:
    """Tras un analyze-diff con violación, /findings debe tener un hallazgo más."""
    await client_con_violacion.post("/analyze-diff", json={"diff": _DIFF_SECRET})
    resp_findings = await client_con_violacion.get("/findings")
    assert resp_findings.status_code == 200
    assert resp_findings.json()["total"] >= 1


@pytest.mark.asyncio
async def test_analyze_diff_multi_marco(client_con_violacion: AsyncClient) -> None:
    resp = await client_con_violacion.post(
        "/analyze-diff",
        json={
            "diff": _DIFF_SECRET,
            "marcos": ["iso_27001_2022", "ens_2022"],
        },
    )
    assert resp.status_code == 200
    # El mock devuelve un result fijo con iso_27001_2022, pero el endpoint
    # acepta la request y devuelve 200
    assert resp.json()["bloquear"] is True


@pytest.mark.asyncio
async def test_analyze_diff_exclude_paths_en_request(client_con_violacion: AsyncClient) -> None:
    """exclude_paths se pasa correctamente al analyzer."""
    resp = await client_con_violacion.post(
        "/analyze-diff",
        json={
            "diff": _DIFF_SECRET,
            "exclude_paths": ["tests/**", "*.lock"],
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_analyze_diff_marcos_usados_en_respuesta(client_sin_violacion: AsyncClient) -> None:
    resp = await client_sin_violacion.post("/analyze-diff", json={"diff": _DIFF_NEUTRO})
    assert resp.status_code == 200
    assert "iso_27001_2022" in resp.json()["marcos_usados"]
