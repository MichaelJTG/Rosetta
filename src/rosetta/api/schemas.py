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
