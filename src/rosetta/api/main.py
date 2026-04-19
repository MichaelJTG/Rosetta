"""Servidor FastAPI de ROSETTA — MVP-6: API REST + dashboard visual."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from rosetta import __version__
from rosetta.api.dashboard import HTML_DASHBOARD
from rosetta.api.deps import FindingsDep, GrafoDep, TraductorDep
from rosetta.api.schemas import (
    ComplianceStateResponse,
    ControlSummary,
    FindingItem,
    FindingsResponse,
    TranslateRequest,
)
from rosetta.core.models import (
    DatosCompliance,
    HallazgoMaestro,
    MarcoNormativo,
    Severidad,
)
from rosetta.core.rag import NormativaRAG
from rosetta.core.traductor import TraductorSimbiotico
from rosetta.llm.factory import get_llm_client

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Inicializa recursos al arrancar y los cierra al parar."""
    logger.info("rosetta_api_starting", version=__version__)

    chroma_path = os.getenv("CHROMADB_PATH", ".chroma")
    marcos_raw = os.getenv("ROSETTA_MARCOS", "iso_27001_2022").split(",")
    marcos = [MarcoNormativo(m.strip()) for m in marcos_raw if m.strip()]
    if not marcos:
        marcos = [MarcoNormativo.ISO_27001_2022]

    llm = get_llm_client()
    rag = NormativaRAG(chromadb_path=chroma_path)
    _app.state.traductor = TraductorSimbiotico(llm=llm, rag=rag, marcos_activos=marcos)
    _app.state.session_findings = []  # list[HallazgoMaestro]

    # Neo4j es opcional — si no está configurado la API sigue funcionando
    neo_uri = os.getenv("NEO4J_URI")
    if neo_uri:
        try:
            from rosetta.core.graph import GrafoCorrelacion

            _app.state.grafo = GrafoCorrelacion.desde_uri(
                neo_uri,
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "rosetta_dev"),
            )
            logger.info("neo4j_connected", uri=neo_uri)
        except Exception as exc:
            logger.warning("neo4j_unavailable_api_continues", error=str(exc))
            _app.state.grafo = None
    else:
        _app.state.grafo = None

    yield

    if _app.state.grafo is not None:
        _app.state.grafo.cerrar()
    logger.info("rosetta_api_stopping")


app = FastAPI(
    title="ROSETTA API",
    description=(
        "Orquestador de cumplimiento continuo. Traduce hallazgos técnicos a "
        "evidencia normativa multi-marco (ISO 27001, ENS, NIS2, DORA)."
    ),
    version=__version__,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Endpoint de salud para smoke tests."""
    return {"status": "ok", "version": __version__}


@app.get("/dashboard", response_class=HTMLResponse, tags=["ui"], include_in_schema=False)
async def dashboard() -> str:
    """Panel visual para auditor — interfaz web sin CLI."""
    return HTML_DASHBOARD


# ---------------------------------------------------------------------------
# Traductor
# ---------------------------------------------------------------------------


@app.post("/translate", response_model=DatosCompliance, tags=["traductor"])
async def translate(
    body: TranslateRequest,
    traductor: TraductorDep,
    grafo: GrafoDep,
    findings: FindingsDep,
) -> DatosCompliance:
    """Traduce un hallazgo técnico a evidencia normativa multi-marco.

    Si los marcos del body difieren de los marcos activos del servidor, se
    crea un traductor local con los marcos solicitados (LLM y RAG compartidos).
    """
    try:
        if body.marcos != traductor.marcos_activos:
            traductor_local: TraductorSimbiotico = TraductorSimbiotico(
                llm=traductor.llm,
                rag=traductor.rag,
                marcos_activos=body.marcos,
            )
        else:
            traductor_local = traductor

        compliance: DatosCompliance = await traductor_local.traducir(body.hallazgo)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    hallazgo_id = f"SEC-{uuid.uuid4().hex[:8].upper()}"
    maestro = HallazgoMaestro(
        id_hallazgo=hallazgo_id,
        red_team_data=body.hallazgo,
        compliance_data=compliance,
    )
    findings.append(maestro)

    # Persistir en Neo4j si está disponible (best-effort, no bloquea la respuesta)
    if grafo is not None:
        _persist_to_graph(grafo, maestro, compliance)

    return compliance


def _persist_to_graph(grafo: Any, maestro: HallazgoMaestro, compliance: DatosCompliance) -> None:
    """Persiste el hallazgo en Neo4j para cada control incumplido."""
    try:
        for marco in compliance.marcos_aplicables:
            for ctrl_id in compliance.controles_incumplidos:
                grafo.registrar_hallazgo(
                    hallazgo_id=maestro.id_hallazgo,
                    activo=maestro.red_team_data.activo_detectado,
                    marco=marco.value,
                    control_id=ctrl_id,
                    control_nombre=ctrl_id,
                    severidad=compliance.impacto_legal.value,
                    origen=maestro.red_team_data.origen.value,
                    evidencia=maestro.red_team_data.evidencia,
                    justificacion=compliance.justificacion,
                    mitigacion=compliance.accion_mitigacion,
                    timestamp=maestro.timestamp.isoformat(),
                )
    except Exception as exc:
        logger.warning("neo4j_persist_error", error=str(exc))


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@app.get("/findings", response_model=FindingsResponse, tags=["findings"])
async def list_findings(
    findings: FindingsDep,
    offset: int = Query(0, ge=0, description="Número de hallazgos a saltar."),
    limit: int = Query(20, ge=1, le=100, description="Máximo de hallazgos a devolver."),
) -> FindingsResponse:
    """Lista los hallazgos traducidos en la sesión actual con paginación."""
    total = len(findings)
    page = findings[offset : offset + limit]
    items = [_maestro_to_item(m) for m in page]
    return FindingsResponse(total=total, offset=offset, limit=limit, items=items)


def _maestro_to_item(m: HallazgoMaestro) -> FindingItem:
    """Convierte un HallazgoMaestro en la proyección plana FindingItem."""
    compliance = m.compliance_data
    return FindingItem(
        id_hallazgo=m.id_hallazgo,
        timestamp=m.timestamp,
        activo_detectado=m.red_team_data.activo_detectado,
        origen=m.red_team_data.origen.value,
        marcos_aplicables=[mm.value for mm in compliance.marcos_aplicables] if compliance else [],
        controles_incumplidos=compliance.controles_incumplidos if compliance else [],
        impacto_legal=compliance.impacto_legal.value if compliance else Severidad.MEDIA.value,
    )


# ---------------------------------------------------------------------------
# Compliance state
# ---------------------------------------------------------------------------


@app.get(
    "/compliance/state/{marco}",
    response_model=ComplianceStateResponse,
    tags=["compliance"],
)
async def compliance_state(
    marco: MarcoNormativo,
    grafo: GrafoDep,
    findings: FindingsDep,
) -> ComplianceStateResponse:
    """Estado de cumplimiento global para un marco normativo.

    Si Neo4j está conectado consulta el grafo; de lo contrario agrega desde
    los hallazgos de la sesión en memoria.
    """
    marco_str = marco.value

    if grafo is not None:
        return _state_from_graph(grafo, marco_str)

    return _state_from_memory(findings, marco)


def _state_from_graph(grafo: Any, marco_str: str) -> ComplianceStateResponse:
    """Calcula el estado de cumplimiento consultando Neo4j."""
    hallazgos_raw: list[dict[str, Any]] = grafo.hallazgos_por_marco(marco_str)
    top_raw: list[dict[str, Any]] = grafo.controles_mas_incumplidos(marco_str, top_n=10)

    sev_dist: dict[str, int] = {}
    for h in hallazgos_raw:
        sev = str(h.get("severidad") or "media")
        sev_dist[sev] = sev_dist.get(sev, 0) + 1

    controles = [
        ControlSummary(
            control_id=str(c.get("control_id") or ""),
            total_hallazgos=int(c.get("total") or 0),
        )
        for c in top_raw
    ]

    return ComplianceStateResponse(
        marco=marco_str,
        total_hallazgos=len(hallazgos_raw),
        controles_incumplidos=controles,
        severidad_distribution=sev_dist,
    )


def _state_from_memory(
    findings: list[HallazgoMaestro], marco: MarcoNormativo
) -> ComplianceStateResponse:
    """Calcula el estado de cumplimiento desde los hallazgos en sesión."""
    relevant = [
        m for m in findings if m.compliance_data and marco in m.compliance_data.marcos_aplicables
    ]

    ctrl_counts: dict[str, int] = {}
    sev_dist: dict[str, int] = {}

    for m in relevant:
        compliance = m.compliance_data
        if compliance is None:
            continue
        sev = compliance.impacto_legal.value
        sev_dist[sev] = sev_dist.get(sev, 0) + 1
        for ctrl in compliance.controles_incumplidos:
            ctrl_counts[ctrl] = ctrl_counts.get(ctrl, 0) + 1

    top_controles = sorted(ctrl_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    controles = [ControlSummary(control_id=cid, total_hallazgos=cnt) for cid, cnt in top_controles]

    return ComplianceStateResponse(
        marco=marco.value,
        total_hallazgos=len(relevant),
        controles_incumplidos=controles,
        severidad_distribution=sev_dist,
    )
