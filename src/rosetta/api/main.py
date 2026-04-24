"""Servidor FastAPI de ROSETTA — MVP-6: API REST + dashboard visual."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from rosetta import __version__
from rosetta.api.dashboard import HTML_DASHBOARD
from rosetta.api.deps import DiffAnalyzerDep, FindingsDep, GrafoDep, TraductorDep
from rosetta.api.schemas import (
    AlertaBlueItem,
    AuditStartRequest,
    AuditStartResponse,
    AuditStatusResponse,
    BlueIngestRequest,
    BlueIngestResponse,
    ComplianceStateResponse,
    ControlSummary,
    CopilotApiResponse,
    CopilotRequest,
    DiffAnalysisRequest,
    DiffAnalysisResponse,
    DiffViolationItem,
    FindingItem,
    FindingsResponse,
    IngestPdfResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    TranslateRequest,
)
from rosetta.core.diff_analyzer import DiffAnalysisResult, DiffViolation
from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    FuenteRedTeam,
    HallazgoMaestro,
    MarcoNormativo,
    Severidad,
)
from rosetta.core.orchestrator import (
    AlcanceAuditoria,
    Orchestrator,
    ProgresoAuditoria,
    ResultadoAuditoria,
)
from rosetta.core.rag import NormativaRAG
from rosetta.core.traductor import TraductorSimbiotico
from rosetta.llm.factory import get_llm_client

load_dotenv()

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
    _app.state.audits = {}  # dict[str, ResultadoAuditoria]
    _app.state.audit_queues = {}  # dict[str, asyncio.Queue[ProgresoAuditoria | None]]
    _app.state.audit_events = {}  # dict[str, list[dict[str, Any]]]

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
        try:
            return _state_from_graph(grafo, marco_str)
        except Exception as exc:
            logger.warning("neo4j_query_failed_fallback_to_memory", error=str(exc))

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


# ---------------------------------------------------------------------------
# CI/CD Gate
# ---------------------------------------------------------------------------


@app.post("/analyze-diff", response_model=DiffAnalysisResponse, tags=["ci-gate"])
async def analyze_diff(
    body: DiffAnalysisRequest,
    analyzer: DiffAnalyzerDep,
    grafo: GrafoDep,
    findings: FindingsDep,
) -> DiffAnalysisResponse:
    """Gate de CI/CD: analiza el diff de un PR y detecta incumplimientos normativos.

    Diseñado para ser llamado desde una GitHub Action. Devuelve `bloquear: true`
    si se detectan violaciones cuya severidad supera el umbral configurado.

    El campo `resumen_pr` contiene un comentario Markdown listo para publicar en el PR.
    """
    try:
        bloquear_si = Severidad(body.bloquear_si)
    except ValueError:
        bloquear_si = Severidad.ALTA

    try:
        result = await analyzer.analizar(
            diff_text=body.diff,
            marcos=body.marcos,
            bloquear_si=bloquear_si,
            exclude_paths=body.exclude_paths,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Persistir cada violación como HallazgoMaestro (best-effort)
    for violacion in result.violaciones:
        _persist_violation(violacion, result, findings, grafo)

    resumen = _generar_resumen_pr(result)

    return DiffAnalysisResponse(
        bloquear=result.bloquear,
        total_hunks_analizados=result.total_hunks_analizados,
        total_violaciones=len(result.violaciones),
        marcos_usados=[m.value for m in result.marcos_usados],
        violaciones=[
            DiffViolationItem(
                archivo=v.archivo,
                linea_inicio=v.linea_inicio,
                lineas_afectadas=list(v.lineas_afectadas),
                controles_incumplidos=list(v.controles_incumplidos),
                cita_normativa=v.cita_normativa,
                justificacion=v.justificacion,
                impacto_legal=v.impacto_legal.value,
                accion_mitigacion=v.accion_mitigacion,
                evidencia_auditoria=v.evidencia_auditoria,
            )
            for v in result.violaciones
        ],
        resumen_pr=resumen,
    )


def _persist_violation(
    violacion: DiffViolation,
    result: DiffAnalysisResult,
    findings: list[HallazgoMaestro],
    grafo: Any,
) -> None:
    """Persiste una violación de diff como HallazgoMaestro en sesión y Neo4j."""
    datos_red = DatosRedTeam(
        origen=FuenteRedTeam.MANUAL,
        activo_detectado=f"{violacion.archivo}:{violacion.linea_inicio}",
        evidencia="\n".join(list(violacion.lineas_afectadas)[:5]),
        vector_ataque="Cambio de código en PR con incumplimiento normativo detectado por Gate CI/CD",
        dificultad_explotacion=violacion.impacto_legal,
    )
    compliance = DatosCompliance(
        marcos_aplicables=result.marcos_usados,
        controles_incumplidos=list(violacion.controles_incumplidos),
        cita_normativa=violacion.cita_normativa,
        justificacion=violacion.justificacion,
        impacto_legal=violacion.impacto_legal,
        accion_mitigacion=violacion.accion_mitigacion,
        evidencia_auditoria=violacion.evidencia_auditoria,
    )
    hallazgo_id = f"SEC-{uuid.uuid4().hex[:8].upper()}"
    maestro = HallazgoMaestro(
        id_hallazgo=hallazgo_id,
        red_team_data=datos_red,
        compliance_data=compliance,
    )
    findings.append(maestro)
    if grafo is not None:
        _persist_to_graph(grafo, maestro, compliance)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@app.post("/reports/generate", response_model=ReportGenerateResponse, tags=["reports"])
async def generate_report(
    body: ReportGenerateRequest,
    findings: FindingsDep,
) -> ReportGenerateResponse:
    """Genera un informe de auditoría en formato Markdown y PDF.

    Incluye todos los hallazgos de la sesión actual o un subconjunto si se
    especifican `hallazgo_ids`. El PDF lleva marca ROSETTA y, opcionalmente,
    nombre e información del cliente.
    """
    from pathlib import Path

    from rosetta.core.report_generator import ReportConfig, ReportGenerator

    # Filtrar hallazgos si se especifican IDs
    if body.hallazgo_ids is not None:
        ids_set = set(body.hallazgo_ids)
        hallazgos_seleccionados = [h for h in findings if h.id_hallazgo in ids_set]
    else:
        hallazgos_seleccionados = list(findings)

    config = ReportConfig(
        nombre_cliente=body.nombre_cliente,
        autor=body.autor,
        confidencialidad=body.confidencialidad,
    )
    gen = ReportGenerator(config)

    ruta_reports = Path("reports")
    try:
        md_path, pdf_path = gen.generar(
            hallazgos_seleccionados,
            ruta_salida=ruta_reports,
            nombre_base=body.nombre_base,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generando informe: {exc}") from exc

    nombre_base = md_path.stem
    return ReportGenerateResponse(
        md_path=str(md_path),
        pdf_path=str(pdf_path),
        total_hallazgos=len(hallazgos_seleccionados),
        nombre_base=nombre_base,
    )


@app.post("/ingest/pdf", response_model=IngestPdfResponse, tags=["ingestion"])
async def ingest_pdf(
    file: UploadFile,
    traductor: TraductorDep,
    findings: FindingsDep,
) -> IngestPdfResponse:
    """Ingesta un PDF de informe de auditoría humano y extrae hallazgos.

    Acepta un PDF con informe de auditoría de seguridad. Extrae el texto de
    cada página con pdfplumber; en páginas escaneadas recurre a visión LLM
    (pypdfium2 + Claude). Cada hallazgo extraído se registra como HallazgoMaestro
    en la sesión con ``origen=MANUAL`` y se traduce al marco ISO 27001:2022
    por defecto.
    """
    from pathlib import Path

    from rosetta.core.pdf_ingestion import PdfAuditorIngester

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF (.pdf).")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo PDF está vacío.")

    # Guardar en fichero temporal para que pdfplumber/pypdfium2 puedan abrirlo
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        ingester = PdfAuditorIngester(llm_client=traductor.llm)
        result = await ingester.ingestar(tmp_path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    # Registrar cada hallazgo extraído como HallazgoMaestro en sesión
    hallazgo_ids: list[str] = []
    for dato in result.hallazgos:
        hallazgo_id = f"PDF-{uuid.uuid4().hex[:8].upper()}"
        maestro = HallazgoMaestro(
            id_hallazgo=hallazgo_id,
            red_team_data=dato,
            compliance_data=None,
        )
        findings.append(maestro)
        hallazgo_ids.append(hallazgo_id)

    return IngestPdfResponse(
        total_hallazgos=len(result.hallazgos),
        paginas_procesadas=result.paginas_procesadas,
        paginas_con_hallazgos=result.paginas_con_hallazgos,
        modo_extraccion=result.modo_extraccion,
        hallazgo_ids=hallazgo_ids,
    )


# ---------------------------------------------------------------------------
# Audit — Modo A
# ---------------------------------------------------------------------------


@app.post("/audit/start", response_model=AuditStartResponse, tags=["audit"])
async def audit_start(
    body: AuditStartRequest,
    findings: FindingsDep,
    request: Any,
) -> AuditStartResponse:
    """Inicia una auditoría automática Red Team en segundo plano.

    Valida el alcance (declaración de autorización, lista negra, IPs privadas)
    y lanza la ejecución en un asyncio.Task. Devuelve el `audit_id` para
    conectar el WebSocket de progreso en `WS /audit/ws/{audit_id}`.
    """
    audit_id = uuid.uuid4().hex[:12]
    alcance = AlcanceAuditoria(
        objetivos=body.objetivos,
        adaptadores=body.adaptadores,
        max_concurrencia=body.max_concurrencia,
        lista_negra=body.lista_negra,
        declaracion_alcance=body.declaracion_alcance,
    )

    orchestrator = Orchestrator()
    try:
        orchestrator._validar_alcance(alcance)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    queue: asyncio.Queue[ProgresoAuditoria | None] = asyncio.Queue()
    request.app.state.audit_queues[audit_id] = queue
    request.app.state.audit_events[audit_id] = []

    resultado_placeholder = ResultadoAuditoria(
        audit_id=audit_id,
        estado="en_curso",
        objetivos_procesados=[],
        hallazgos=[],
        errores=[],
        inicio=__import__("datetime").datetime.utcnow(),
    )
    request.app.state.audits[audit_id] = resultado_placeholder

    async def run_audit() -> None:
        async def on_progreso(evento: ProgresoAuditoria) -> None:
            evento_dict = evento.to_dict()
            request.app.state.audit_events[audit_id].append(evento_dict)
            await queue.put(evento)

        try:
            resultado = await orchestrator.ejecutar(
                alcance, on_progreso=on_progreso, audit_id=audit_id
            )
        except Exception as exc:  # noqa: BLE001
            resultado = ResultadoAuditoria(
                audit_id=audit_id,
                estado="error",
                objetivos_procesados=[],
                hallazgos=[],
                errores=[str(exc)],
                inicio=resultado_placeholder.inicio,
                fin=__import__("datetime").datetime.utcnow(),
            )

        request.app.state.audits[audit_id] = resultado

        # Registrar hallazgos como HallazgoMaestro en sesión
        for dato in resultado.hallazgos:
            hid = f"AUD-{uuid.uuid4().hex[:8].upper()}"
            maestro = HallazgoMaestro(
                id_hallazgo=hid,
                red_team_data=dato,
                compliance_data=None,
            )
            findings.append(maestro)

        await queue.put(None)  # sentinel: fin del stream

    asyncio.create_task(run_audit())

    return AuditStartResponse(
        audit_id=audit_id,
        objetivos=len(body.objetivos),
        adaptadores=body.adaptadores,
        ws_url=f"/audit/ws/{audit_id}",
    )


@app.websocket("/audit/ws/{audit_id}")
async def audit_ws(websocket: WebSocket, audit_id: str) -> None:
    """WebSocket de progreso de auditoría.

    Emite eventos JSON conforme el orquestador avanza. Cierra automáticamente
    cuando la auditoría termina (evento tipo 'fin') o si el cliente desconecta.
    Los eventos pasados se replayan al conectar (útil ante reconexiones).
    """
    await websocket.accept()

    # Replay de eventos ya ocurridos (reconexión tardía)
    past_events: list[dict[str, Any]] = websocket.app.state.audit_events.get(audit_id, [])
    for evt in past_events:
        try:
            await websocket.send_text(json.dumps(evt))
        except WebSocketDisconnect:
            return

    queue: asyncio.Queue[ProgresoAuditoria | None] | None = websocket.app.state.audit_queues.get(
        audit_id
    )
    if queue is None:
        await websocket.send_text(json.dumps({"error": f"audit_id {audit_id!r} no encontrado"}))
        await websocket.close()
        return

    try:
        while True:
            evento = await queue.get()
            if evento is None:  # sentinel — fin del stream
                await websocket.close()
                return
            await websocket.send_text(json.dumps(evento.to_dict()))
    except WebSocketDisconnect:
        pass


@app.get("/audit/{audit_id}", response_model=AuditStatusResponse, tags=["audit"])
async def audit_status(audit_id: str, request: Any) -> AuditStatusResponse:
    """Consulta el estado y resultados de una auditoría por su ID."""
    resultado: ResultadoAuditoria | None = request.app.state.audits.get(audit_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Auditoría '{audit_id}' no encontrada.")

    hallazgo_ids = [
        m.id_hallazgo
        for m in request.app.state.session_findings
        if m.id_hallazgo.startswith("AUD-")
    ]

    return AuditStatusResponse(
        audit_id=resultado.audit_id,
        estado=resultado.estado,
        objetivos_procesados=len(resultado.objetivos_procesados),
        total_hallazgos=resultado.total_hallazgos,
        errores=resultado.errores,
        inicio=resultado.inicio.isoformat(),
        fin=resultado.fin.isoformat() if resultado.fin else None,
        hallazgo_ids=hallazgo_ids,
    )


def _generar_resumen_pr(result: DiffAnalysisResult) -> str:
    """Genera el comentario Markdown del Gate para publicar en el PR."""
    marcos_str = ", ".join(f"`{m.value}`" for m in result.marcos_usados)
    footer = f"\n\n*Marcos: {marcos_str} · Hunks analizados: {result.total_hunks_analizados} · [ROSETTA](https://github.com/tu-org/rosetta)*"

    if not result.violaciones:
        return (
            "## ROSETTA · Gate de Cumplimiento Normativo\n\n"
            "✅ **Sin incumplimientos detectados** — El diff no introduce violaciones "
            "normativas conocidas. El PR puede continuar." + footer
        )

    estado = "🔴 BLOQUEADO" if result.bloquear else "🟡 ADVERTENCIA"
    n = len(result.violaciones)
    lines = [
        "## ROSETTA · Gate de Cumplimiento Normativo\n",
        f"**Estado: {estado}** — {n} violación{'es' if n > 1 else ''} detectada{'s' if n > 1 else ''}\n",
        "| Archivo | Línea | Controles | Severidad | Acción recomendada |",
        "|---------|-------|-----------|-----------|-------------------|",
    ]
    for v in result.violaciones:
        controles = ", ".join(f"`{c}`" for c in v.controles_incumplidos)
        accion = v.accion_mitigacion
        if len(accion) > 90:
            accion = accion[:87] + "…"
        lines.append(
            f"| `{v.archivo}` | {v.linea_inicio} | {controles} "
            f"| **{v.impacto_legal.value}** | {accion} |"
        )

    if result.violaciones:
        lines.append("\n### Detalle de violaciones\n")
        for i, v in enumerate(result.violaciones, 1):
            lines.append(f"**{i}. `{v.archivo}:{v.linea_inicio}`** — {v.cita_normativa}")
            lines.append(f"> {v.justificacion}")
            lines.append("")

    return "\n".join(lines) + footer


# ---------------------------------------------------------------------------
# Blue Team — POST /blue/ingest
# ---------------------------------------------------------------------------


@app.post("/blue/ingest", response_model=BlueIngestResponse, tags=["blue-team"])
async def blue_ingest(
    body: BlueIngestRequest,
    findings: FindingsDep,
) -> BlueIngestResponse:
    """Ingesta offline de alertas Wazuh en formato JSON o CSV.

    Parsea el payload, normaliza las alertas al formato interno y calcula
    la cobertura defensiva Red↔Blue cruzando con los hallazgos de la sesión.

    Formatos soportados:
      - ``json``: lista de objetos alerta Wazuh o wrapper ``{"data": {"affected_items": [...]}}``
      - ``csv``: texto CSV con columnas estándar de export Wazuh
    """
    from rosetta.adapters.blue.wazuh import WazuhAdapter
    from rosetta.core.blue_enrichment import enriquecer, resumen_cobertura

    if body.formato == "csv":
        if not body.datos_csv:
            raise HTTPException(status_code=400, detail="Se requiere 'datos_csv' para formato csv.")
        alertas = WazuhAdapter.ingestar_csv(body.datos_csv)
    else:
        if body.datos_json is None:
            raise HTTPException(
                status_code=400, detail="Se requiere 'datos_json' para formato json."
            )
        alertas = WazuhAdapter.ingestar_json(body.datos_json)

    # Enriquecer con hallazgos Red Team de la sesión
    hallazgos_dict = [
        {
            "activo_detectado": m.red_team_data.activo_detectado,
            "vector_ataque": m.red_team_data.vector_ataque,
            "dificultad_explotacion": m.red_team_data.dificultad_explotacion,
        }
        for m in findings
    ]
    enriquecidos = enriquecer(hallazgos_dict, alertas)
    cobertura = resumen_cobertura(enriquecidos)

    alertas_response = [
        AlertaBlueItem(
            id=a["id"],
            timestamp=a["timestamp"],
            nivel=a["nivel"],
            regla_id=a["regla_id"],
            regla_descripcion=a["regla_descripcion"],
            agente_id=a["agente_id"],
            agente_nombre=a["agente_nombre"],
            activo=a["activo"],
        )
        for a in alertas
    ]

    return BlueIngestResponse(
        total_alertas=len(alertas),
        alertas=alertas_response,
        resumen_cobertura=cobertura,
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


# ---------------------------------------------------------------------------
# Copilot — POST /copilot/ask
# ---------------------------------------------------------------------------


@app.post("/copilot/ask", response_model=CopilotApiResponse, tags=["copilot"])
async def copilot_ask(request: CopilotRequest) -> CopilotApiResponse:
    """Consulta al Copilot normativo en lenguaje natural.

    Recibe una pregunta libre, recupera contexto RAG del corpus normativo
    y genera una respuesta fundamentada. No requiere hallazgo previo.

    Returns:
        Respuesta con fuentes y nivel de confianza.
    """
    from rosetta.core.copilot import CopilotQuery, consultar_copilot

    llm = get_llm_client()
    chroma_path = os.getenv("CHROMADB_PATH", ".chroma")
    rag = NormativaRAG(chromadb_path=chroma_path)

    query = CopilotQuery(pregunta=request.pregunta, contexto=request.contexto)

    try:
        response = await consultar_copilot(query=query, llm=llm, rag=rag)
    except Exception as exc:
        logger.error("copilot_error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Error en Copilot: {exc}") from exc

    return CopilotApiResponse(
        respuesta=response.respuesta,
        fuentes=response.fuentes,
        confianza=response.confianza,
    )
