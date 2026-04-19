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
