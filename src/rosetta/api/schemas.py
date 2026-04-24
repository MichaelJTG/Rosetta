"""Esquemas Pydantic de la capa API — distintos de los modelos de dominio.

Los modelos de dominio (core/models.py) representan el lenguaje interno de
ROSETTA. Estos esquemas representan el contrato del transporte HTTP: cuerpos
de petición, proyecciones de respuesta y paginación.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from rosetta.core.models import DatosRedTeam, MarcoNormativo


class TranslateRequest(BaseModel):
    """Cuerpo de la petición POST /translate."""

    hallazgo: DatosRedTeam
    marcos: list[MarcoNormativo] = Field(
        default=[MarcoNormativo.ISO_27001_2022],
        description="Marcos normativos contra los que traducir el hallazgo.",
    )


class ControlSummary(BaseModel):
    """Resumen de un control normativo en el estado de cumplimiento."""

    control_id: str
    total_hallazgos: int


class FindingItem(BaseModel):
    """Proyección plana de un HallazgoMaestro para la respuesta GET /findings."""

    id_hallazgo: str
    timestamp: datetime
    activo_detectado: str
    origen: str
    marcos_aplicables: list[str]
    controles_incumplidos: list[str]
    impacto_legal: str


class FindingsResponse(BaseModel):
    """Respuesta paginada de GET /findings."""

    total: int
    offset: int
    limit: int
    items: list[FindingItem]


class ComplianceStateResponse(BaseModel):
    """Respuesta de GET /compliance/state/{marco}."""

    marco: str
    total_hallazgos: int
    controles_incumplidos: list[ControlSummary]
    severidad_distribution: dict[str, int]


# ---------------------------------------------------------------------------
# CI/CD Gate — POST /analyze-diff
# ---------------------------------------------------------------------------


class DiffAnalysisRequest(BaseModel):
    """Cuerpo de la petición POST /analyze-diff."""

    diff: str = Field(
        ...,
        description="Diff unificado completo del PR (salida de `git diff origin/main...HEAD`).",
    )
    marcos: list[MarcoNormativo] = Field(
        default=[MarcoNormativo.ISO_27001_2022],
        description="Marcos normativos contra los que analizar el diff.",
    )
    bloquear_si: str = Field(
        default="alta",
        description="Severidad mínima para bloquear el PR (baja | media | alta | critica).",
    )
    exclude_paths: list[str] = Field(
        default_factory=list,
        description="Patrones glob de rutas a ignorar (ej. ['tests/**', '*.lock']).",
    )


class DiffViolationItem(BaseModel):
    """Una violación normativa detectada en el diff — ítem de la respuesta."""

    archivo: str = Field(..., description="Ruta del archivo con la violación.")
    linea_inicio: int = Field(..., description="Línea de inicio del hunk afectado.")
    lineas_afectadas: list[str] = Field(
        ..., description="Líneas añadidas que contienen la violación."
    )
    controles_incumplidos: list[str] = Field(
        ..., description="IDs de controles normativo incumplidos."
    )
    cita_normativa: str
    justificacion: str
    impacto_legal: str
    accion_mitigacion: str
    evidencia_auditoria: str


class DiffAnalysisResponse(BaseModel):
    """Respuesta de POST /analyze-diff."""

    bloquear: bool = Field(
        ...,
        description="True si el PR debe ser bloqueado por incumplimientos normativos.",
    )
    total_hunks_analizados: int = Field(..., description="Número de hunks analizados.")
    total_violaciones: int = Field(..., description="Número de violaciones detectadas.")
    marcos_usados: list[str] = Field(..., description="Marcos normativos usados en el análisis.")
    violaciones: list[DiffViolationItem]
    resumen_pr: str = Field(
        ...,
        description="Comentario Markdown listo para publicar como comentario en el PR.",
    )


# ---------------------------------------------------------------------------
# Report Generator — POST /reports/generate
# ---------------------------------------------------------------------------


class ReportGenerateRequest(BaseModel):
    """Cuerpo de la petición POST /reports/generate."""

    nombre_cliente: str | None = Field(
        default=None,
        description="Nombre de la organización auditada (aparece en portada y pie).",
    )
    autor: str = Field(
        default="ROSETTA Audit Platform",
        description="Nombre del auditor o equipo que firma el informe.",
    )
    confidencialidad: str = Field(
        default="CONFIDENCIAL",
        description="Nivel de confidencialidad impreso en cabecera y pie.",
    )
    nombre_base: str | None = Field(
        default=None,
        description="Nombre base para los archivos (sin extensión). "
        "Por defecto: rosetta_report_YYYYMMDD_HHMMSS.",
    )
    hallazgo_ids: list[str] | None = Field(
        default=None,
        description="IDs de hallazgos a incluir. Si None, se incluyen todos los de la sesión.",
    )


class ReportGenerateResponse(BaseModel):
    """Respuesta de POST /reports/generate."""

    md_path: str = Field(..., description="Ruta al informe Markdown generado.")
    pdf_path: str = Field(..., description="Ruta al informe PDF generado.")
    total_hallazgos: int = Field(..., description="Número de hallazgos incluidos.")
    nombre_base: str = Field(..., description="Nombre base usado para los archivos.")


# ---------------------------------------------------------------------------
# PDF Ingestion — POST /ingest/pdf
# ---------------------------------------------------------------------------


class IngestPdfResponse(BaseModel):
    """Respuesta de POST /ingest/pdf."""

    total_hallazgos: int = Field(..., description="Número de hallazgos extraídos del PDF.")
    paginas_procesadas: int = Field(..., description="Número de páginas procesadas.")
    paginas_con_hallazgos: int = Field(
        ..., description="Páginas de las que se extrajeron hallazgos."
    )
    modo_extraccion: str = Field(
        ..., description="'texto' si pdfplumber extrajo texto; 'imagen' si se usó visión LLM."
    )
    hallazgo_ids: list[str] = Field(
        ..., description="IDs de los HallazgoMaestro registrados en la sesión."
    )


# ---------------------------------------------------------------------------
# Audit — POST /audit/start  ·  GET /audit/{audit_id}
# ---------------------------------------------------------------------------


class AuditStartRequest(BaseModel):
    """Cuerpo de la petición POST /audit/start."""

    objetivos: list[str] = Field(
        ...,
        min_length=1,
        description="URLs, IPs o dominios del alcance autorizado.",
    )
    adaptadores: list[str] = Field(
        default=["nuclei"],
        description="Adaptadores a usar: 'nuclei', 'nmap'.",
    )
    max_concurrencia: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Máximo de tareas paralelas (rate limiting).",
    )
    lista_negra: list[str] = Field(
        default_factory=list,
        description="Objetivos adicionales excluidos del escaneo.",
    )
    declaracion_alcance: str = Field(
        ...,
        min_length=10,
        description=(
            "Declaración explícita de autorización para escanear los objetivos. "
            "Campo obligatorio — mínimo 10 caracteres."
        ),
    )


class AuditStartResponse(BaseModel):
    """Respuesta de POST /audit/start."""

    audit_id: str = Field(..., description="Identificador único de la auditoría.")
    objetivos: int = Field(..., description="Número de objetivos en el alcance.")
    adaptadores: list[str] = Field(..., description="Adaptadores activos.")
    ws_url: str = Field(
        ..., description="URL relativa del WebSocket de progreso: /audit/ws/{audit_id}"
    )


class AuditStatusResponse(BaseModel):
    """Respuesta de GET /audit/{audit_id}."""

    audit_id: str
    estado: str = Field(..., description="'en_curso' | 'completado' | 'error'")
    objetivos_procesados: int
    total_hallazgos: int
    errores: list[str]
    inicio: str = Field(..., description="ISO-8601 UTC")
    fin: str | None = Field(None, description="ISO-8601 UTC, None si en curso")
    hallazgo_ids: list[str] = Field(
        ..., description="IDs de HallazgoMaestro registrados en la sesión."
    )


# ---------------------------------------------------------------------------
# Blue Team — POST /blue/ingest
# ---------------------------------------------------------------------------


class AlertaBlueItem(BaseModel):
    """Alerta Blue Team normalizada para la respuesta."""

    id: str
    timestamp: str
    nivel: int
    regla_id: str
    regla_descripcion: str
    agente_id: str
    agente_nombre: str
    activo: str


class BlueIngestRequest(BaseModel):
    """Cuerpo de POST /blue/ingest — ingesta offline de alertas Wazuh."""

    formato: str = Field(
        default="json",
        description="Formato del payload: 'json' o 'csv'.",
    )
    datos_json: list[dict[str, object]] | None = Field(
        default=None,
        description="Alertas Wazuh en formato JSON (lista o wrapper API).",
    )
    datos_csv: str | None = Field(
        default=None,
        description="Alertas Wazuh en formato CSV (texto completo del fichero).",
    )


class BlueIngestResponse(BaseModel):
    """Respuesta de POST /blue/ingest."""

    total_alertas: int = Field(..., description="Número de alertas ingestadas.")
    alertas: list[AlertaBlueItem] = Field(..., description="Alertas normalizadas.")
    resumen_cobertura: dict[str, object] = Field(
        ...,
        description="Cobertura Red↔Blue: total, con_cobertura, sin_cobertura, porcentaje.",
    )


# ---------------------------------------------------------------------------
# Copilot — POST /copilot/ask
# ---------------------------------------------------------------------------


class CopilotRequest(BaseModel):
    """Cuerpo de la petición POST /copilot/ask."""

    pregunta: str = Field(..., description="Pregunta en lenguaje natural sobre normativa.")
    contexto: str = Field(
        "",
        description="Contexto operativo adicional (tipo de sistema, sector, etc.).",
    )


class CopilotApiResponse(BaseModel):
    """Respuesta de POST /copilot/ask."""

    respuesta: str = Field(..., description="Respuesta fundamentada en el corpus normativo.")
    fuentes: list[str] = Field(
        default_factory=list,
        description="IDs de controles usados como fuente RAG.",
    )
    confianza: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Nivel de confianza (0-1) proporcional a fragmentos RAG disponibles.",
    )


# ---------------------------------------------------------------------------
# Procedure Drift — POST /drift/analyze
# ---------------------------------------------------------------------------


class DriftRequest(BaseModel):
    """Cuerpo de la petición POST /drift/analyze."""

    procedimiento: str = Field(
        ...,
        description="Texto del procedimiento interno de seguridad a analizar.",
    )
    observaciones: list[str] = Field(
        ...,
        min_length=1,
        description="Observaciones reales del entorno (logs, alertas, hallazgos).",
    )


class DriftResponse(BaseModel):
    """Respuesta de POST /drift/analyze."""

    drift_detectado: bool = Field(..., description="True si existe desviación significativa.")
    descripcion_drift: str = Field(..., description="Descripción del drift detectado.")
    fragmento_afectado: str = Field(
        ..., description="Fragmento del procedimiento que diverge de la realidad."
    )
    redaccion_propuesta: str = Field(
        ..., description="Propuesta de actualización del procedimiento."
    )
    controles_afectados: list[str] = Field(
        default_factory=list,
        description="IDs de controles normativos afectados por el drift.",
    )
    severidad: str = Field(
        ..., description="Severidad del drift: informativa/baja/media/alta/critica."
    )
