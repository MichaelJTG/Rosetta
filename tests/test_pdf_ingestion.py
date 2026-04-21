"""Tests de pdf_ingestion.py y el endpoint POST /ingest/pdf.

Estrategia:
- PdfAuditorIngester se testea con mocks de pdfplumber y del LLM client.
- El endpoint /ingest/pdf se testea con httpx AsyncClient y dependency_overrides.
- No se usa ningún PDF real — toda la I/O con archivos se mockea o se usa
  un PDF mínimo válido creado en memoria con el magic header %PDF.
"""

from __future__ import annotations

import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from rosetta.api.deps import get_session_findings, get_traductor
from rosetta.api.main import app
from rosetta.core.models import DatosRedTeam, FuenteRedTeam, HallazgoMaestro, Severidad
from rosetta.core.pdf_ingestion import (
    PdfAuditorIngester,
    PdfIngestionResult,
    _parse_tool_result,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_HALLAZGO_RAW = {
    "activo_detectado": "192.168.1.1",
    "evidencia": "CVE-2023-1234 detectado en banner SSH",
    "vector_ataque": "Servicio SSH desactualizado expuesto a internet",
    "dificultad_explotacion": "alta",
    "cve_relacionado": "CVE-2023-1234",
}


def _make_tool_result(hallazgos: list[dict[str, Any]]) -> MagicMock:
    """Simula el objeto result devuelto por LLMClient.completar()."""
    call = MagicMock()
    call.tool_name = "extraer_hallazgos"
    call.tool_input = {"hallazgos": hallazgos}
    result = MagicMock()
    result.tool_calls = [call]
    return result


def _make_llm_client(hallazgos: list[dict[str, Any]] | None = None) -> Any:
    """Crea un mock de LLMClient que devuelve hallazgos predefinidos."""
    client = MagicMock()
    client.completar = AsyncMock(return_value=_make_tool_result(hallazgos or [_FAKE_HALLAZGO_RAW]))
    return client


# ---------------------------------------------------------------------------
# Tests de PdfIngestionResult
# ---------------------------------------------------------------------------


def test_pdf_ingestion_result_attrs() -> None:
    """PdfIngestionResult expone los 4 atributos esperados."""
    resultado = PdfIngestionResult(
        hallazgos=[],
        paginas_procesadas=3,
        paginas_con_hallazgos=1,
        modo_extraccion="texto",
    )
    assert resultado.paginas_procesadas == 3
    assert resultado.paginas_con_hallazgos == 1
    assert resultado.modo_extraccion == "texto"
    assert resultado.hallazgos == []


# ---------------------------------------------------------------------------
# Tests de _parse_tool_result
# ---------------------------------------------------------------------------


def test_parse_tool_result_hallazgo_valido() -> None:
    """_parse_tool_result construye DatosRedTeam correctamente."""
    result = _make_tool_result([_FAKE_HALLAZGO_RAW])
    hallazgos = _parse_tool_result(result, n_pagina=1, nombre_pdf="test.pdf")
    assert len(hallazgos) == 1
    h = hallazgos[0]
    assert isinstance(h, DatosRedTeam)
    assert h.activo_detectado == "192.168.1.1"
    assert h.dificultad_explotacion == Severidad.ALTA
    assert h.cve_relacionado == "CVE-2023-1234"
    assert h.origen == FuenteRedTeam.MANUAL
    assert h.metadatos["pagina"] == 1
    assert h.metadatos["fuente_pdf"] == "test.pdf"


def test_parse_tool_result_severidad_desconocida_fallback() -> None:
    """Severidad no reconocida cae al valor media."""
    raw = {**_FAKE_HALLAZGO_RAW, "dificultad_explotacion": "desconocido_xyz"}
    result = _make_tool_result([raw])
    hallazgos = _parse_tool_result(result, n_pagina=1, nombre_pdf="test.pdf")
    assert hallazgos[0].dificultad_explotacion == Severidad.MEDIA


def test_parse_tool_result_sin_tool_calls() -> None:
    """Si no hay tool_calls devuelve lista vacía."""
    result = MagicMock()
    result.tool_calls = []
    assert _parse_tool_result(result, 1, "test.pdf") == []


def test_parse_tool_result_tool_name_incorrecto() -> None:
    """Tool calls con nombre distinto a extraer_hallazgos se ignoran."""
    call = MagicMock()
    call.tool_name = "otra_herramienta"
    call.tool_input = {"hallazgos": [_FAKE_HALLAZGO_RAW]}
    result = MagicMock()
    result.tool_calls = [call]
    assert _parse_tool_result(result, 1, "test.pdf") == []


def test_parse_tool_result_cve_none() -> None:
    """cve_relacionado ausente o null se convierte en None."""
    raw = {**_FAKE_HALLAZGO_RAW, "cve_relacionado": None}
    result = _make_tool_result([raw])
    hallazgos = _parse_tool_result(result, 1, "test.pdf")
    assert hallazgos[0].cve_relacionado is None


# ---------------------------------------------------------------------------
# Tests de PdfAuditorIngester.ingestar()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingestar_archivo_no_existe() -> None:
    """ingestar() lanza FileNotFoundError si el PDF no existe."""
    ingester = PdfAuditorIngester()
    with pytest.raises(FileNotFoundError):
        await ingester.ingestar(Path("/ruta/inexistente/informe.pdf"))


@pytest.mark.asyncio
async def test_ingestar_sin_llm_client_devuelve_vacio() -> None:
    """Sin LLM client, ingestar() extrae texto pero devuelve 0 hallazgos."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 placeholder")
        tmp_path = Path(tmp.name)

    try:
        with patch("pdfplumber.open") as mock_open:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Texto de prueba con hallazgo de seguridad."
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [mock_page]
            mock_open.return_value = mock_pdf

            ingester = PdfAuditorIngester(llm_client=None)
            result = await ingester.ingestar(tmp_path)

        assert result.paginas_procesadas == 1
        assert len(result.hallazgos) == 0
    finally:
        tmp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_ingestar_con_texto_llama_llm() -> None:
    """Con texto suficiente y LLM, ingestar() extrae hallazgos correctamente."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 placeholder")
        tmp_path = Path(tmp.name)

    try:
        with patch("pdfplumber.open") as mock_open:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "A" * 200
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [mock_page]
            mock_open.return_value = mock_pdf

            llm = _make_llm_client([_FAKE_HALLAZGO_RAW])
            ingester = PdfAuditorIngester(llm_client=llm)
            result = await ingester.ingestar(tmp_path)

        assert result.paginas_procesadas == 1
        assert result.paginas_con_hallazgos == 1
        assert len(result.hallazgos) == 1
        assert result.modo_extraccion == "texto"
    finally:
        tmp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_ingestar_pagina_sin_texto_intenta_imagen() -> None:
    """Página sin texto intenta renderizado a imagen; si falla, se salta."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 placeholder")
        tmp_path = Path(tmp.name)

    try:
        with patch("pdfplumber.open") as mock_open:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [mock_page]
            mock_open.return_value = mock_pdf

            llm = _make_llm_client([])
            ingester = PdfAuditorIngester(llm_client=llm)
            with patch.object(ingester, "_renderizar_pagina_b64", return_value=None):
                result = await ingester.ingestar(tmp_path)

        assert result.paginas_procesadas == 1  # la página se cuenta en el slice
        assert result.hallazgos == []
    finally:
        tmp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_ingestar_max_paginas_limita_procesado() -> None:
    """max_paginas=1 procesa solo la primera de dos páginas."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 placeholder")
        tmp_path = Path(tmp.name)

    try:
        with patch("pdfplumber.open") as mock_open:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "B" * 200
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [mock_page, mock_page]
            mock_open.return_value = mock_pdf

            llm = _make_llm_client([_FAKE_HALLAZGO_RAW])
            ingester = PdfAuditorIngester(llm_client=llm, max_paginas=1)
            result = await ingester.ingestar(tmp_path)

        assert result.paginas_procesadas == 1
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Tests del endpoint POST /ingest/pdf
# ---------------------------------------------------------------------------


def _make_traductor_mock() -> Any:
    mock = MagicMock()
    mock.llm = MagicMock()
    mock.marcos_activos = []
    return mock


@pytest_asyncio.fixture
async def pdf_client() -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP con dependencias mockeadas para /ingest/pdf."""
    session_findings: list[HallazgoMaestro] = []
    app.dependency_overrides[get_traductor] = lambda: _make_traductor_mock()
    app.dependency_overrides[get_session_findings] = lambda: session_findings

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_pdf_no_file_returns_422(pdf_client: AsyncClient) -> None:
    """POST /ingest/pdf sin archivo devuelve 422."""
    r = await pdf_client.post("/ingest/pdf")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_pdf_not_pdf_extension_400(pdf_client: AsyncClient) -> None:
    """POST /ingest/pdf con archivo .txt devuelve 400."""
    r = await pdf_client.post(
        "/ingest/pdf",
        files={"file": ("informe.txt", b"contenido", "text/plain")},
    )
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_pdf_empty_file_400(pdf_client: AsyncClient) -> None:
    """POST /ingest/pdf con PDF vacío devuelve 400."""
    r = await pdf_client.post(
        "/ingest/pdf",
        files={"file": ("informe.pdf", b"", "application/pdf")},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_ingest_pdf_ok_zero_hallazgos(pdf_client: AsyncClient) -> None:
    """POST /ingest/pdf con PDF válido (sin hallazgos) devuelve 200 y total=0."""
    fake_result = PdfIngestionResult(
        hallazgos=[],
        paginas_procesadas=2,
        paginas_con_hallazgos=0,
        modo_extraccion="texto",
    )
    with patch("rosetta.core.pdf_ingestion.PdfAuditorIngester") as MockIngester:
        MockIngester.return_value.ingestar = AsyncMock(return_value=fake_result)
        r = await pdf_client.post(
            "/ingest/pdf",
            files={"file": ("informe.pdf", b"%PDF-1.4 content", "application/pdf")},
        )

    assert r.status_code == 200
    data = r.json()
    assert data["total_hallazgos"] == 0
    assert data["paginas_procesadas"] == 2
    assert data["paginas_con_hallazgos"] == 0
    assert data["modo_extraccion"] == "texto"
    assert data["hallazgo_ids"] == []


@pytest.mark.asyncio
async def test_ingest_pdf_ok_con_hallazgos(pdf_client: AsyncClient) -> None:
    """POST /ingest/pdf con 2 hallazgos registra IDs y devuelve total=2."""
    datos = [
        DatosRedTeam(
            origen=FuenteRedTeam.MANUAL,
            activo_detectado=f"activo-{i}",
            evidencia="evidencia",
            vector_ataque="SQLi",
            dificultad_explotacion=Severidad.MEDIA,
        )
        for i in range(2)
    ]
    fake_result = PdfIngestionResult(
        hallazgos=datos,
        paginas_procesadas=1,
        paginas_con_hallazgos=1,
        modo_extraccion="texto",
    )
    with patch("rosetta.core.pdf_ingestion.PdfAuditorIngester") as MockIngester:
        MockIngester.return_value.ingestar = AsyncMock(return_value=fake_result)
        r = await pdf_client.post(
            "/ingest/pdf",
            files={"file": ("informe.pdf", b"%PDF-1.4 content", "application/pdf")},
        )

    assert r.status_code == 200
    data = r.json()
    assert data["total_hallazgos"] == 2
    assert len(data["hallazgo_ids"]) == 2
    for hid in data["hallazgo_ids"]:
        assert hid.startswith("PDF-")


@pytest.mark.asyncio
async def test_ingest_pdf_invalid_pdf_returns_422(pdf_client: AsyncClient) -> None:
    """POST /ingest/pdf con PDF corrupto que lanza ValueError devuelve 422."""
    with patch("rosetta.core.pdf_ingestion.PdfAuditorIngester") as MockIngester:
        MockIngester.return_value.ingestar = AsyncMock(
            side_effect=ValueError("PDF inválido o no legible")
        )
        r = await pdf_client.post(
            "/ingest/pdf",
            files={"file": ("informe.pdf", b"%PDF-1.4 corrupto", "application/pdf")},
        )

    assert r.status_code == 422
