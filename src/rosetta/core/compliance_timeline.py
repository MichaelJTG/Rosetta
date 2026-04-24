"""compliance_timeline — seguimiento temporal del estado de cumplimiento.

Permite registrar snapshots del estado compliance de un hallazgo a lo largo
del tiempo y detectar la tendencia (mejorando / estable / empeorando).
No requiere LLM — es lógica determinista de análisis de series temporales.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from rosetta.core.models import MarcoNormativo


class SnapshotCompliance(BaseModel):
    """Estado de cumplimiento de un hallazgo en un instante de tiempo."""

    hallazgo_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    marcos: list[MarcoNormativo] = Field(default_factory=list)
    controles_ok: list[str] = Field(
        default_factory=list,
        description="Controles verificados como cumplidos en este snapshot.",
    )
    controles_ko: list[str] = Field(
        default_factory=list,
        description="Controles pendientes de remediar en este snapshot.",
    )

    @property
    def ratio_cumplimiento(self) -> float:
        """Proporción de controles cumplidos sobre el total. 1.0 = 100%."""
        total = len(self.controles_ok) + len(self.controles_ko)
        if total == 0:
            return 1.0
        return len(self.controles_ok) / total


class ComplianceTimeline(BaseModel):
    """Serie temporal de snapshots de cumplimiento para un hallazgo."""

    hallazgo_id: str
    snapshots: list[SnapshotCompliance] = Field(default_factory=list)

    def ultimo_snapshot(self) -> SnapshotCompliance | None:
        """Devuelve el snapshot más reciente, o None si no hay ninguno."""
        if not self.snapshots:
            return None
        return max(self.snapshots, key=lambda s: s.timestamp)

    def tendencia(self) -> str:
        """Calcula la tendencia comparando el primer y último snapshot.

        Returns:
            'mejorando' si el ratio de cumplimiento aumentó,
            'empeorando' si disminuyó,
            'estable' si no cambió o solo hay un snapshot.
        """
        if len(self.snapshots) < 2:
            return "estable"

        ordenados = sorted(self.snapshots, key=lambda s: s.timestamp)
        ratio_inicial = ordenados[0].ratio_cumplimiento
        ratio_final = ordenados[-1].ratio_cumplimiento

        if ratio_final > ratio_inicial:
            return "mejorando"
        if ratio_final < ratio_inicial:
            return "empeorando"
        return "estable"
