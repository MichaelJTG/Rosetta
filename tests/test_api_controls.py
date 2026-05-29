"""Tests de integración para endpoints de cumplimiento.

Cubre: controles, roadmap, evidencias, gap-analysis, plan-director, assets, risk-analysis.
Usa httpx.AsyncClient + ASGITransport igual que test_api.py.
ControlStore se instancia con BD temporal (tmp_path). LLM mockeado.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from rosetta.api.deps import get_control_store, get_grafo, get_session_findings, get_traductor
from rosetta.api.main import app
from rosetta.core.control_store import ControlStore
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
    controles_incumplidos=["A.8.15", "A.8.16"],
    cita_normativa="A.8.15 Logging: ...",
    justificacion="Logs no configurados.",
    impacto_legal=Severidad.ALTA,
    accion_mitigacion="Activar logging centralizado.",
    evidencia_auditoria="Detectado via Wazuh.",
)


def _make_finding(
    activo: str = "srv-test",
    origen: FuenteRedTeam = FuenteRedTeam.NUCLEI,
) -> HallazgoMaestro:
    datos = DatosRedTeam(
        origen=origen,
        activo_detectado=activo,
        evidencia="https://example.com/finding",
        vector_ataque="SQLi en param id",
        dificultad_explotacion=Severidad.MEDIA,
    )
    tag = activo[:6].upper().replace("-", "")
    return HallazgoMaestro(
        id_hallazgo=f"SEC-TEST-{tag}",
        timestamp=datetime(2026, 5, 1, 10, 0, 0),
        red_team_data=datos,
        compliance_data=_COMPLIANCE,
    )


def _llm_mock(response_text: str = "[]") -> Any:
    from rosetta.llm.base import CompletionResult

    result = CompletionResult(content=response_text, stop_reason="end_turn")
    llm = MagicMock()
    llm.completar = AsyncMock(return_value=result)
    return llm


def _make_traductor(llm_response: str = "[]") -> Any:
    mock = MagicMock()
    mock.traducir = AsyncMock(return_value=_COMPLIANCE)
    mock.marcos_activos = [MarcoNormativo.ISO_27001_2022]
    mock.rag = MagicMock()
    mock.llm = _llm_mock(llm_response)
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def ctrl_client(tmp_path: Path) -> AsyncGenerator[tuple[AsyncClient, ControlStore], None]:
    """Cliente vacio + ControlStore temporal."""
    db_path = str(tmp_path / "ctrl_test.db")
    ctrl_store = ControlStore(db_path=db_path)
    session_findings: list[HallazgoMaestro] = []

    app.dependency_overrides[get_traductor] = lambda: _make_traductor()
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    app.dependency_overrides[get_control_store] = lambda: ctrl_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, ctrl_store

    app.dependency_overrides.clear()
    ctrl_store.close()


@pytest_asyncio.fixture
async def ctrl_client_with_findings(
    tmp_path: Path,
) -> AsyncGenerator[tuple[AsyncClient, ControlStore], None]:
    """Cliente con 3 hallazgos pre-cargados + ControlStore temporal."""
    db_path = str(tmp_path / "ctrl_findings_test.db")
    ctrl_store = ControlStore(db_path=db_path)
    session_findings = [
        _make_finding("srv-web", FuenteRedTeam.NUCLEI),
        _make_finding("srv-db", FuenteRedTeam.MANUAL),
        _make_finding("firewall", FuenteRedTeam.NMAP),
    ]

    gap_resp = json.dumps(
        [
            {
                "control_id": "A.8.15",
                "respuesta": "no_cumple",
                "confianza": 0.9,
                "justificacion": "Logs no activos.",
                "evidencia_base": [],
            },
            {
                "control_id": "A.8.16",
                "respuesta": "parcial",
                "confianza": 0.7,
                "justificacion": "Monitoreo parcial.",
                "evidencia_base": ["A.8.15"],
            },
        ]
    )
    plan_resp = json.dumps(
        {
            "resumen_ejecutivo": "Se deben remediar 2 controles.",
            "acciones": [
                {
                    "titulo": "Activar logging",
                    "descripcion": "Configurar rsyslog.",
                    "categoria": "tecnico",
                    "prioridad": "alta",
                    "personas_dia": 2.0,
                    "controles_relacionados": ["A.8.15"],
                    "cubierto_por_herramienta": "WAZUH",
                },
            ],
        }
    )
    risk_resp = json.dumps(
        [
            {
                "activo": "srv-web",
                "amenazas": ["SQLi", "XSS"],
                "probabilidad": 4,
                "impacto": 4,
                "tratamiento": "Parchear dependencias.",
                "controles_relacionados": ["A.8.15"],
            },
        ]
    )

    responses = [gap_resp, plan_resp, risk_resp]
    call_idx = [0]

    async def _side_effect(**_kw: Any) -> Any:
        from rosetta.llm.base import CompletionResult

        idx = min(call_idx[0], len(responses) - 1)
        call_idx[0] += 1
        return CompletionResult(content=responses[idx], stop_reason="end_turn")

    traductor = MagicMock()
    traductor.traducir = AsyncMock(return_value=_COMPLIANCE)
    traductor.marcos_activos = [MarcoNormativo.ISO_27001_2022]
    traductor.rag = MagicMock()
    traductor.llm = MagicMock()
    traductor.llm.completar = AsyncMock(side_effect=_side_effect)

    app.dependency_overrides[get_traductor] = lambda: traductor
    app.dependency_overrides[get_grafo] = lambda: None
    app.dependency_overrides[get_session_findings] = lambda: session_findings
    app.dependency_overrides[get_control_store] = lambda: ctrl_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, ctrl_store

    app.dependency_overrides.clear()
    ctrl_store.close()


# ---------------------------------------------------------------------------
# Controls catalog
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_controls_iso_200(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /controls/iso_27001_2022 devuelve 200 con lista de controles."""
    c, _ = ctrl_client
    r = await c.get("/controls/iso_27001_2022")
    assert r.status_code == 200
    data = r.json()
    assert data["marco"] == "iso_27001_2022"
    assert data["total"] >= 10
    assert len(data["controles"]) >= 10


@pytest.mark.asyncio
async def test_list_controls_ens_200(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /controls/ens_2022 devuelve 200 con controles ENS."""
    c, _ = ctrl_client
    r = await c.get("/controls/ens_2022")
    assert r.status_code == 200
    assert r.json()["total"] >= 5


@pytest.mark.asyncio
async def test_list_controls_unknown_marco_404(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /controls/marco_inexistente devuelve 404."""
    c, _ = ctrl_client
    r = await c.get("/controls/marco_inexistente")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_control_200(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /controls/iso_27001_2022/A.8.15 devuelve 200 con datos del control."""
    c, _ = ctrl_client
    r = await c.get("/controls/iso_27001_2022/A.8.15")
    assert r.status_code == 200
    data = r.json()
    assert data["control_id"] == "A.8.15"
    assert data["titulo"] == "Logging"
    assert data["estado"] == "no_aplica"


@pytest.mark.asyncio
async def test_get_control_unknown_404(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET control inexistente devuelve 404."""
    c, _ = ctrl_client
    r = await c.get("/controls/iso_27001_2022/A.NOEXISTE")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_control_cumple_200(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """PATCH /controls/iso_27001_2022/A.8.15 con estado cumple devuelve 200."""
    c, _ = ctrl_client
    r = await c.patch(
        "/controls/iso_27001_2022/A.8.15",
        json={"estado": "cumple", "responsable": "Ana", "comentarios": "OK"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["estado"] == "cumple"
    assert data["responsable"] == "Ana"


@pytest.mark.asyncio
async def test_patch_control_invalid_estado_422(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """PATCH con estado invalido devuelve 422 (validacion Pydantic)."""
    c, _ = ctrl_client
    r = await c.patch(
        "/controls/iso_27001_2022/A.8.15",
        json={"estado": "invalido"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_control_unknown_404(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """PATCH control inexistente devuelve 404."""
    c, _ = ctrl_client
    r = await c.patch("/controls/iso_27001_2022/A.NOEXISTE", json={"estado": "cumple"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Vuln roadmap
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vuln_roadmap_empty(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /vuln-roadmap sin hallazgos devuelve total 0."""
    c, _ = ctrl_client
    r = await c.get("/vuln-roadmap")
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_vuln_roadmap_with_findings(
    ctrl_client_with_findings: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /vuln-roadmap con hallazgos devuelve items con campos esperados."""
    c, _ = ctrl_client_with_findings
    r = await c.get("/vuln-roadmap")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    item = data["items"][0]
    assert "id_hallazgo" in item
    assert "criticidad" in item
    assert "estado" in item


@pytest.mark.asyncio
async def test_vuln_roadmap_filter_by_estado(
    ctrl_client_with_findings: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /vuln-roadmap?estado=activo filtra por estado correctamente."""
    c, _ = ctrl_client_with_findings
    r = await c.get("/vuln-roadmap?estado=activo")
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["estado"] == "activo"


# ---------------------------------------------------------------------------
# Evidence panel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_panel_empty(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /evidence-panel sin hallazgos devuelve estructura valida."""
    c, _ = ctrl_client
    r = await c.get("/evidence-panel")
    assert r.status_code == 200
    data = r.json()
    assert "total_controles" in data
    assert "cards" in data


@pytest.mark.asyncio
async def test_evidence_panel_with_findings(
    ctrl_client_with_findings: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /evidence-panel con hallazgos devuelve cards con cobertura valida."""
    c, _ = ctrl_client_with_findings
    r = await c.get("/evidence-panel")
    assert r.status_code == 200
    data = r.json()
    assert data["total_controles"] > 0
    for card in data["cards"]:
        assert card["cobertura"] in ("verde", "amarillo", "rojo", "sin_datos")


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gap_analysis_unknown_marco_404(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """POST /gap-analysis/marco_inexistente devuelve 404."""
    c, _ = ctrl_client
    r = await c.post("/gap-analysis/marco_inexistente")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_gap_analysis_iso_200(
    ctrl_client_with_findings: tuple[AsyncClient, ControlStore],
) -> None:
    """POST /gap-analysis/iso_27001_2022 devuelve analisis con controles."""
    c, _ = ctrl_client_with_findings
    r = await c.post("/gap-analysis/iso_27001_2022")
    assert r.status_code == 200
    data = r.json()
    assert data["marco"] == "iso_27001_2022"
    assert data["total_controles"] >= 1
    assert "porcentaje_cumplimiento" in data
    assert isinstance(data["controles"], list)


# ---------------------------------------------------------------------------
# Plan director
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plan_director_unknown_marco_404(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """POST /plan-director/marco_inexistente devuelve 404."""
    c, _ = ctrl_client
    r = await c.post("/plan-director/marco_inexistente")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_plan_director_iso_200(
    ctrl_client_with_findings: tuple[AsyncClient, ControlStore],
) -> None:
    """POST /plan-director/iso_27001_2022 devuelve plan con acciones."""
    c, _ = ctrl_client_with_findings
    r = await c.post("/plan-director/iso_27001_2022")
    assert r.status_code == 200
    data = r.json()
    assert data["marco"] == "iso_27001_2022"
    assert "total_acciones" in data
    assert "total_coste_eur" in data
    assert "resumen_ejecutivo" in data
    assert isinstance(data["acciones"], list)


# ---------------------------------------------------------------------------
# Assets + Risk analysis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assets_empty(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /assets sin hallazgos devuelve total 0."""
    c, _ = ctrl_client
    r = await c.get("/assets")
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_assets_with_findings(
    ctrl_client_with_findings: tuple[AsyncClient, ControlStore],
) -> None:
    """GET /assets con hallazgos devuelve activos detectados."""
    c, _ = ctrl_client_with_findings
    r = await c.get("/assets")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    nombres = [a["nombre"] for a in data["activos"]]
    assert "srv-web" in nombres


@pytest.mark.asyncio
async def test_risk_analysis_empty_returns_zero(
    ctrl_client: tuple[AsyncClient, ControlStore],
) -> None:
    """POST /risk-analysis sin hallazgos devuelve total_activos 0."""
    c, _ = ctrl_client
    r = await c.post("/risk-analysis")
    assert r.status_code == 200
    assert r.json()["total_activos"] == 0


@pytest.mark.asyncio
async def test_risk_analysis_with_findings(
    ctrl_client_with_findings: tuple[AsyncClient, ControlStore],
) -> None:
    """POST /risk-analysis con hallazgos devuelve entradas de riesgo."""
    c, _ = ctrl_client_with_findings
    r = await c.post("/risk-analysis")
    assert r.status_code == 200
    data = r.json()
    assert data["total_activos"] >= 1
    assert "riesgo_promedio" in data
    assert isinstance(data["entradas"], list)
