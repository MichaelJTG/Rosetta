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

from rosetta.api.deps import get_grafo, get_session_findings, get_traductor, get_validador
from rosetta.api.main import _client_ip, _is_trusted_proxy, app
from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    FuenteRedTeam,
    HallazgoMaestro,
    MarcoNormativo,
    Severidad,
    ValidacionResult,
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


def _directive(csp: str, name: str) -> str:
    """Devuelve el valor de una directiva CSP (cadena vacía si no está)."""
    for part in csp.split(";"):
        tokens = part.strip().split(" ", 1)
        if tokens[0] == name:
            return tokens[1] if len(tokens) > 1 else ""
    return ""


@pytest.mark.asyncio
async def test_b3_csp_docs_allows_swagger_ui_assets(client: AsyncClient) -> None:
    """/docs recibe una CSP que permite los recursos de Swagger UI (cdn.jsdelivr.net)."""
    r = await client.get("/docs")
    assert r.status_code == 200
    assert "cdn.jsdelivr.net/npm/swagger-ui-dist" in r.text
    csp = r.headers.get("content-security-policy", "")
    assert "https://cdn.jsdelivr.net" in _directive(csp, "script-src")
    assert "https://cdn.jsdelivr.net" in _directive(csp, "style-src")
    assert _directive(csp, "frame-ancestors") == "'none'"
    assert _directive(csp, "object-src") == "'none'"


@pytest.mark.asyncio
async def test_b3_csp_redoc_allows_redoc_worker(client: AsyncClient) -> None:
    """/redoc permite el bundle de ReDoc y su web worker (blob:)."""
    r = await client.get("/redoc")
    assert r.status_code == 200
    csp = r.headers.get("content-security-policy", "")
    assert "https://cdn.jsdelivr.net" in _directive(csp, "script-src")
    assert "blob:" in _directive(csp, "worker-src")


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/health", "/dashboard", "/openapi.json"])
async def test_b3_csp_strict_outside_docs(client: AsyncClient, path: str) -> None:
    """Fuera de /docs y /redoc la CSP sigue siendo la estricta: sin cdn.jsdelivr.net."""
    r = await client.get(path)
    csp = r.headers.get("content-security-policy", "")
    assert "cdn.jsdelivr.net" not in csp
    assert "blob:" not in csp


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


def _make_mock_request(peer_host: str, x_real_ip: str | None = None) -> Any:
    """Crea un Request mock con client.host y cabecera X-Real-IP."""
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = peer_host
    headers: dict[str, str] = {}
    if x_real_ip is not None:
        headers["x-real-ip"] = x_real_ip
    req.headers = headers
    return req


def test_b4_trusted_proxy_localhost_is_trusted() -> None:
    """127.0.0.1 está en la lista de proxies de confianza."""
    req = _make_mock_request("127.0.0.1")
    assert _is_trusted_proxy(req) is True


def test_b4_default_only_loopback_trusted() -> None:
    """Por defecto, solo loopback (127.0.0.1/::1) está en la lista de confianza.
    172.17.x.x y 10.x.x.x ya no están en el default (rangos amplios eliminados B-4)."""
    assert _is_trusted_proxy(_make_mock_request("172.17.0.5")) is False
    assert _is_trusted_proxy(_make_mock_request("10.1.2.3")) is False
    assert _is_trusted_proxy(_make_mock_request("::1")) is True


def test_b4_untrusted_peer_not_trusted() -> None:
    """203.0.113.1 (IP pública) NO está en la lista de confianza."""
    req = _make_mock_request("203.0.113.1")
    assert _is_trusted_proxy(req) is False


def test_b4_xrealip_ignored_from_untrusted_origin() -> None:
    """X-Real-IP desde origen no confiable se ignora; se usa la IP del peer."""
    req = _make_mock_request("203.0.113.1", x_real_ip="10.0.0.1")
    with patch("rosetta.api.main.get_remote_address", return_value="203.0.113.1"):
        result = _client_ip(req)
    assert result == "203.0.113.1"


def test_b4_xrealip_used_from_trusted_proxy() -> None:
    """X-Real-IP desde proxy de confianza (127.0.0.1) es aceptado."""
    req = _make_mock_request("127.0.0.1", x_real_ip="192.0.2.99")
    result = _client_ip(req)
    assert result == "192.0.2.99"


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


# ---------------------------------------------------------------------------
# RF-09 · Validador opcional en /translate
# ---------------------------------------------------------------------------


def _make_validador(valida: bool = True) -> Any:
    from rosetta.agents.validator import Validador  # noqa: PLC0415

    mock = MagicMock(spec=Validador)
    mock.validar = AsyncMock(
        return_value=ValidacionResult(
            traduccion_id="test-001",
            valida=valida,
            problemas=[] if valida else ["Control 8.99 no existe"],
            confianza=0.9,
            razonamiento="Test.",
        )
    )
    return mock


@pytest_asyncio.fixture
async def client_validador() -> AsyncGenerator[AsyncClient, None]:
    """Cliente con Validador mockeado (valida=True)."""
    session_findings: list[HallazgoMaestro] = []
    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    app.dependency_overrides[get_validador] = lambda: _make_validador()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


_HALLAZGO_BODY = {
    "origen": "nuclei",
    "activo_detectado": "api.techserv.local",
    "evidencia": "https://example.com",
    "vector_ataque": "CVE-2024-1234 RCE en el servicio X",
    "dificultad_explotacion": "alta",
}


@pytest.mark.asyncio
async def test_rf09_translate_without_validar_returns_no_validacion(
    client_validador: AsyncClient,
) -> None:
    """validar=false (default): campo validacion ausente o None."""
    r = await client_validador.post(
        "/translate",
        json={"hallazgo": _HALLAZGO_BODY},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("validacion") is None


@pytest.mark.asyncio
async def test_rf09_translate_with_validar_true_returns_validacion(
    client_validador: AsyncClient,
) -> None:
    """validar=true: campo validacion presente con campos esperados."""
    r = await client_validador.post(
        "/translate",
        json={"hallazgo": _HALLAZGO_BODY, "validar": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["validacion"] is not None
    assert "valida" in data["validacion"]
    assert "confianza" in data["validacion"]


@pytest.mark.asyncio
async def test_rf09_translate_validar_true_valida_false(
    client_with_finding: AsyncClient,
) -> None:
    """validar=true con Validador que rechaza: respuesta 200 con validacion.valida=false."""
    app.dependency_overrides[get_validador] = lambda: _make_validador(valida=False)
    r = await client_with_finding.post(
        "/translate",
        json={"hallazgo": _HALLAZGO_BODY, "validar": True},
    )
    app.dependency_overrides.pop(get_validador, None)
    assert r.status_code == 200
    data = r.json()
    assert data["validacion"]["valida"] is False
    assert len(data["validacion"]["problemas"]) > 0


# ---------------------------------------------------------------------------
# B-9 · Validaciones de seguridad en POST /ingest/pdf
# ---------------------------------------------------------------------------

_MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
    b"xref\n0 3\n"
    b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
    b"trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n110\n%%EOF"
)


@pytest.mark.asyncio
async def test_b9_wrong_magic_bytes_rejected(client: AsyncClient) -> None:
    """Archivo sin magic bytes %PDF → 400."""
    fake_content = b"NOTPDF" + b"\x00" * 50
    r = await client.post(
        "/ingest/pdf",
        files={"file": ("report.pdf", fake_content, "application/pdf")},
    )
    assert r.status_code == 400
    assert "magic bytes" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_b9_oversized_pdf_rejected(client: AsyncClient) -> None:
    """PDF que supera ROSETTA_PDF_MAX_SIZE_MB → 413."""
    import os
    from unittest.mock import patch

    with patch.dict(os.environ, {"ROSETTA_PDF_MAX_SIZE_MB": "0"}):
        r = await client.post(
            "/ingest/pdf",
            files={"file": ("report.pdf", _MINIMAL_PDF, "application/pdf")},
        )
    assert r.status_code == 413
    assert "mb" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_b9_too_many_pages_rejected(client: AsyncClient) -> None:
    """PDF con páginas > ROSETTA_PDF_MAX_PAGES → 422."""
    import os
    from unittest.mock import patch

    mock_pdf = MagicMock()
    mock_pdf.pages = [MagicMock()] * 501
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_pdf)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with (
        patch.dict(os.environ, {"ROSETTA_PDF_MAX_PAGES": "500"}),
        patch("pdfplumber.open", return_value=mock_ctx),
    ):
        r = await client.post(
            "/ingest/pdf",
            files={"file": ("report.pdf", _MINIMAL_PDF, "application/pdf")},
        )
    assert r.status_code == 422
    assert "páginas" in r.json()["detail"]


@pytest.mark.asyncio
async def test_b9_non_pdf_extension_rejected(client: AsyncClient) -> None:
    """Fichero con extensión .exe (no .pdf) → 400."""
    r = await client.post(
        "/ingest/pdf",
        files={"file": ("malware.exe", _MINIMAL_PDF, "application/pdf")},
    )
    assert r.status_code == 400
