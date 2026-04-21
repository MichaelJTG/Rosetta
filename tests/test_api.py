"""Tests de la capa API FastAPI — MVP-6.

Usa httpx.AsyncClient con ASGITransport para probar los endpoints sin
levantar un servidor real. Los componentes de dominio (LLM, RAG, grafo)
se mockean mediante app.dependency_overrides.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from rosetta.api.deps import get_grafo, get_session_findings, get_traductor
from rosetta.api.main import app
from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    FuenteRedTeam,
    HallazgoMaestro,
    MarcoNormativo,
    Severidad,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_DATOS_RED_TEAM = DatosRedTeam(
    origen=FuenteRedTeam.GITHUB_SECRETS,
    activo_detectado="AWS_ACCESS_KEY_ID en repo público",
    evidencia="https://github.com/org/repo/commit/abc123",
    vector_ataque="Exposición de credencial cloud en código fuente",
    dificultad_explotacion=Severidad.BAJA,
)

_COMPLIANCE = DatosCompliance(
    marcos_aplicables=[MarcoNormativo.ISO_27001_2022],
    controles_incumplidos=["A.8.24", "A.5.15"],
    cita_normativa="A.8.24 Uso de la criptografía: ...",
    justificacion="La clave AWS expuesta compromete la gestión de secretos.",
    impacto_legal=Severidad.ALTA,
    accion_mitigacion="Revocar la clave inmediatamente y activar rotación automática.",
    evidencia_auditoria="Hallazgo detectado vía GitHub Secrets scan.",
)


def _make_traductor(compliance: DatosCompliance | None = None) -> Any:
    """Devuelve un mock de TraductorSimbiotico."""
    mock = MagicMock()
    mock.traducir = AsyncMock(return_value=compliance or _COMPLIANCE)
    mock.marcos_activos = [MarcoNormativo.ISO_27001_2022]
    mock.llm = MagicMock()
    mock.rag = MagicMock()
    return mock


def _make_finding(activo: str = "activo-test") -> HallazgoMaestro:
    """Construye un HallazgoMaestro de prueba."""
    datos = DatosRedTeam(
        origen=FuenteRedTeam.NUCLEI,
        activo_detectado=activo,
        evidencia="https://example.com",
        vector_ataque="SQLi en parámetro id",
        dificultad_explotacion=Severidad.MEDIA,
    )
    return HallazgoMaestro(
        id_hallazgo=f"SEC-TEST-{activo[:4].upper()}",
        timestamp=datetime(2026, 4, 19, 10, 0, 0),
        red_team_data=datos,
        compliance_data=_COMPLIANCE,
    )


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP con dependencias mockeadas (sin LLM, RAG ni Neo4j)."""
    session_findings: list[HallazgoMaestro] = []

    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_with_findings() -> AsyncGenerator[AsyncClient, None]:
    """Cliente pre-cargado con 5 hallazgos en sesión."""
    session_findings = [_make_finding(f"activo-{i}") for i in range(5)]

    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests meta
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    """GET /health devuelve 200 y status ok."""
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_dashboard_html(client: AsyncClient) -> None:
    """GET /dashboard devuelve HTML con la palabra ROSETTA."""
    r = await client.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "ROSETTA" in r.text


# ---------------------------------------------------------------------------
# Tests traductor
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_translate_success(client: AsyncClient) -> None:
    """POST /translate con body válido devuelve DatosCompliance."""
    body = {
        "hallazgo": {
            "origen": "github_secrets",
            "activo_detectado": "AWS_ACCESS_KEY_ID en repo público",
            "evidencia": "https://github.com/org/repo/commit/abc123",
            "vector_ataque": "Exposición de credencial cloud en código fuente",
            "dificultad_explotacion": "baja",
        },
        "marcos": ["iso_27001_2022"],
    }
    r = await client.post("/translate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "controles_incumplidos" in data
    assert "impacto_legal" in data


@pytest.mark.asyncio
async def test_translate_invalid_body_422(client: AsyncClient) -> None:
    """POST /translate sin campos requeridos devuelve 422."""
    r = await client.post("/translate", json={"hallazgo": {}, "marcos": []})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_translate_stores_in_session() -> None:
    """Después de POST /translate, GET /findings devuelve total=1."""
    session_findings: list[HallazgoMaestro] = []
    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        body = {
            "hallazgo": {
                "origen": "nuclei",
                "activo_detectado": "app.example.com",
                "evidencia": "https://app.example.com/vuln",
                "vector_ataque": "XSS reflejado",
                "dificultad_explotacion": "media",
            },
            "marcos": ["iso_27001_2022"],
        }
        await c.post("/translate", json=body)
        r = await c.get("/findings")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_translate_llm_error_502() -> None:
    """POST /translate con LLM que lanza ValueError devuelve 502."""
    mock = _make_traductor()
    mock.traducir = AsyncMock(side_effect=ValueError("LLM no invocó la tool"))

    app.dependency_overrides[get_traductor] = lambda: mock
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: []

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        body = {
            "hallazgo": {
                "origen": "nmap",
                "activo_detectado": "192.168.1.1",
                "evidencia": "nmap scan output",
                "vector_ataque": "Puerto RDP expuesto a internet",
                "dificultad_explotacion": "alta",
            },
            "marcos": ["iso_27001_2022"],
        }
        r = await c.post("/translate", json=body)
        assert r.status_code == 502

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests findings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_findings_pagination(client_with_findings: AsyncClient) -> None:
    """GET /findings con offset=2&limit=2 devuelve 2 items y total=5."""
    r = await client_with_findings.get("/findings?offset=2&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["offset"] == 2
    assert data["limit"] == 2


# ---------------------------------------------------------------------------
# Tests compliance state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_compliance_state_in_memory(client_with_findings: AsyncClient) -> None:
    """GET /compliance/state/iso_27001_2022 devuelve total_hallazgos >= 1."""
    r = await client_with_findings.get("/compliance/state/iso_27001_2022")
    assert r.status_code == 200
    data = r.json()
    assert data["marco"] == "iso_27001_2022"
    assert data["total_hallazgos"] >= 1


@pytest.mark.asyncio
async def test_compliance_state_invalid_marco_422(client: AsyncClient) -> None:
    """GET /compliance/state/marco_falso devuelve 422."""
    r = await client.get("/compliance/state/marco_falso")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Tests reports
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_report_sin_hallazgos(client: AsyncClient) -> None:
    """POST /reports/generate con sesión vacía devuelve 200 y total_hallazgos=0."""
    r = await client.post("/reports/generate", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["total_hallazgos"] == 0
    assert data["md_path"].endswith(".md")
    assert data["pdf_path"].endswith(".pdf")
    assert "nombre_base" in data


@pytest.mark.asyncio
async def test_generate_report_con_hallazgos(client_with_findings: AsyncClient) -> None:
    """POST /reports/generate incluye todos los hallazgos de la sesión."""
    r = await client_with_findings.post(
        "/reports/generate",
        json={"nombre_cliente": "Test Corp", "confidencialidad": "CONFIDENCIAL"},
    )
    assert r.status_code == 200
    assert r.json()["total_hallazgos"] == 5


@pytest.mark.asyncio
async def test_generate_report_filtrado_por_ids_inexistentes(
    client_with_findings: AsyncClient,
) -> None:
    """POST /reports/generate con IDs que no existen devuelve 0 hallazgos."""
    r = await client_with_findings.post(
        "/reports/generate",
        json={"hallazgo_ids": ["SEC-NOEXI-0001", "SEC-NOEXI-0002"]},
    )
    assert r.status_code == 200
    assert r.json()["total_hallazgos"] == 0


@pytest.mark.asyncio
async def test_generate_report_nombre_base_personalizado(client: AsyncClient) -> None:
    """POST /reports/generate con nombre_base personalizado lo refleja en la respuesta."""
    r = await client.post(
        "/reports/generate",
        json={"nombre_base": "informe_acme_2026"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nombre_base"] == "informe_acme_2026"
