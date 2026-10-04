"""Tests del Bloque B — hardening de seguridad del producto.

B-1  Path traversal en nombre_base (POST /reports/generate).
B-3  Cabeceras de seguridad HTTP en todas las respuestas.
B-4  X-Real-IP como fuente de IP confiable; XFF ignorado para rate limiting.
B-6  Los mensajes de error 500 no exponen detalles internos.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

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
# Helpers
# ---------------------------------------------------------------------------

_COMPLIANCE = DatosCompliance(
    marcos_aplicables=[MarcoNormativo.ISO_27001_2022],
    controles_incumplidos=["A.8.24"],
    cita_normativa="A.8.24 Uso de la criptografía.",
    justificacion="Test.",
    impacto_legal=Severidad.ALTA,
    accion_mitigacion="Mitigar.",
    evidencia_auditoria="Test.",
)


def _make_finding() -> HallazgoMaestro:
    datos = DatosRedTeam(
        origen=FuenteRedTeam.NUCLEI,
        activo_detectado="activo-test",
        evidencia="https://example.com",
        vector_ataque="SQLi",
        dificultad_explotacion=Severidad.MEDIA,
    )
    return HallazgoMaestro(
        id_hallazgo="SEC-TEST-0001",
        timestamp=datetime(2026, 4, 19, 10, 0, 0),
        red_team_data=datos,
        compliance_data=_COMPLIANCE,
    )


def _make_traductor() -> Any:
    mock = MagicMock()
    mock.traducir = AsyncMock(return_value=_COMPLIANCE)
    mock.marcos_activos = [MarcoNormativo.ISO_27001_2022]
    mock.llm = MagicMock()
    mock.rag = MagicMock()
    return mock


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    session_findings: list[HallazgoMaestro] = []
    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_with_finding() -> AsyncGenerator[AsyncClient, None]:
    session_findings = [_make_finding()]
    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# B-1 · Path traversal — nombre_base
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_b1_path_traversal_rejected(client_with_finding: AsyncClient) -> None:
    """nombre_base con separadores de ruta → 422 (validación Pydantic)."""
    r = await client_with_finding.post(
        "/reports/generate",
        json={"nombre_base": "../../etc/x"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_b1_path_traversal_backslash_rejected(client_with_finding: AsyncClient) -> None:
    """nombre_base con barra invertida → 422."""
    r = await client_with_finding.post(
        "/reports/generate",
        json={"nombre_base": "..\\..\\windows\\system32\\x"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_b1_nombre_base_dot_rejected(client_with_finding: AsyncClient) -> None:
    """nombre_base con punto → 422 (los puntos no están en la lista blanca)."""
    r = await client_with_finding.post(
        "/reports/generate",
        json={"nombre_base": "informe.malicioso"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_b1_nombre_base_too_long_rejected(client_with_finding: AsyncClient) -> None:
    """nombre_base de 65 caracteres → 422."""
    r = await client_with_finding.post(
        "/reports/generate",
        json={"nombre_base": "a" * 65},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_b1_nombre_base_space_rejected(client_with_finding: AsyncClient) -> None:
    """nombre_base con espacio → 422."""
    r = await client_with_finding.post(
        "/reports/generate",
        json={"nombre_base": "informe malicioso"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_b1_valid_nombre_base_accepted(client_with_finding: AsyncClient) -> None:
    """nombre_base alfanumérico válido no es rechazado en la capa de validación."""
    with patch("rosetta.core.report_generator.ReportGenerator.generar") as mock_gen:
        from pathlib import Path

        mock_gen.return_value = (
            Path("/tmp/informe-2026.md"),
            Path("/tmp/informe-2026.pdf"),
        )
        r = await client_with_finding.post(
            "/reports/generate",
            json={"nombre_base": "informe-2026"},
        )
    assert r.status_code != 422


# ---------------------------------------------------------------------------
# B-3 · Cabeceras de seguridad HTTP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_b3_security_headers_present(client: AsyncClient) -> None:
    """Todas las cabeceras de seguridad obligatorias aparecen en /health."""
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "content-security-policy" in r.headers


@pytest.mark.asyncio
async def test_b3_csp_contains_required_directives(client: AsyncClient) -> None:
    """CSP incluye default-src, script-src, frame-ancestors y object-src none."""
    r = await client.get("/health")
    csp = r.headers.get("content-security-policy", "")
    assert "default-src" in csp
    assert "script-src" in csp
    assert "frame-ancestors" in csp
    assert "object-src 'none'" in csp


@pytest.mark.asyncio
async def test_b3_csp_allows_unpkg_and_fonts(client: AsyncClient) -> None:
    """CSP permite unpkg.com (vis-network) y Google Fonts."""
    r = await client.get("/health")
    csp = r.headers.get("content-security-policy", "")
    assert "unpkg.com" in csp
    assert "fonts.googleapis.com" in csp


# ---------------------------------------------------------------------------
# B-4 · X-Real-IP — XFF no controla la clave de rate limiting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_b4_xff_does_not_rotate_rate_limit_key(client: AsyncClient) -> None:
    """XFF distinto en cada petición no produce 429 (no es la clave de rate limit).

    Si XFF fuera la clave, cada petición parecería una IP distinta y nunca
    se alcanzaría el límite.  Aquí solo verificamos que el servidor responde
    sin error con variación de XFF — el comportamiento correcto es que use
    la IP real de la conexión TCP, no XFF.
    """
    for i in range(5):
        r = await client.get(
            "/health",
            headers={"X-Forwarded-For": f"1.2.3.{i}"},
        )
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_b4_xrealip_accepted(client: AsyncClient) -> None:
    """Servidor acepta petición con X-Real-IP sin error."""
    r = await client.get("/health", headers={"X-Real-IP": "203.0.113.42"})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# B-6 · Mensajes de error 500 sin detalles internos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_b6_report_error_no_internal_detail(client_with_finding: AsyncClient) -> None:
    """POST /reports/generate con excepción interna no expone traceback."""
    with patch("rosetta.core.report_generator.ReportGenerator.generar") as mock_gen:
        mock_gen.side_effect = RuntimeError("Internal path: /var/data/secret_key.pem")
        r = await client_with_finding.post("/reports/generate", json={})
    assert r.status_code == 500
    body = r.text
    assert "secret_key" not in body
    assert "/var/data" not in body
    assert "RuntimeError" not in body


@pytest.mark.asyncio
async def test_b6_copilot_error_no_internal_detail(client: AsyncClient) -> None:
    """POST /copilot/ask con excepción interna no expone detalles."""
    with patch("rosetta.core.copilot.consultar_copilot") as mock_cop:
        mock_cop.side_effect = RuntimeError("DB password: s3cr3t!")
        r = await client.post(
            "/copilot/ask",
            json={"pregunta": "¿Qué es ISO 27001?"},
        )
    assert r.status_code == 500
    body = r.text
    assert "s3cr3t" not in body
    assert "DB password" not in body
