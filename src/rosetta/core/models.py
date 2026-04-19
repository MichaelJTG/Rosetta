"""Modelos de datos unificados de ROSETTA.

El "Hallazgo Maestro" es el objeto central que atraviesa todo el sistema.
Red Team, Blue Team y Normativa se comunican mediante instancias de este
modelo, lo que elimina la desincronización entre silos.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Severidad(StrEnum):
    """Severidad del hallazgo, independiente del marco normativo."""

    INFORMATIVA = "informativa"
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class FuenteRedTeam(StrEnum):
    """Sensor del Red Team que originó el hallazgo."""

    NUCLEI = "nuclei"
    AMASS = "amass"
    SUBFINDER = "subfinder"
    THEHARVESTER = "theharvester"
    SHODAN = "shodan"
    HIBP = "hibp"
    GITHUB_SECRETS = "github_secrets"
    NMAP = "nmap"
    MANUAL = "manual"
    OTRO = "otro"


class MarcoNormativo(StrEnum):
    """Marcos normativos soportados por ROSETTA."""

    ISO_27001_2022 = "iso_27001_2022"
    ISO_27002_2022 = "iso_27002_2022"
    ENS_2022 = "ens_2022"
    NIS2 = "nis2"
    DORA = "dora"
    RGPD = "rgpd"
    NIST_CSF_2 = "nist_csf_2"
    PCI_DSS_4 = "pci_dss_4"


class DatosRedTeam(BaseModel):
    """Datos provenientes del módulo Red Team / OSINT."""

    origen: FuenteRedTeam
    activo_detectado: str = Field(
        ..., description="Identificador del activo: URL, IP, subdominio, nombre, etc."
    )
    evidencia: str = Field(
        ..., description="Enlace o snapshot a la evidencia técnica (URL, hash, log)."
    )
    vector_ataque: str = Field(
        ..., description="Descripción breve del vector de ataque o exposición."
    )
    dificultad_explotacion: Severidad
    cve_relacionado: str | None = None
    metadatos: dict[str, Any] = Field(default_factory=dict)


class DatosBlueTeam(BaseModel):
    """Datos relativos al estado defensivo del activo afectado."""

    id_activo_interno: str | None = Field(
        None,
        description="ID del activo en inventario interno. None si es Shadow IT.",
    )
    shadow_it: bool = Field(
        False,
        description="True si el activo no está en el inventario oficial.",
    )
    estado_defensa: str = Field(
        ..., description="Ej: 'Sin EDR', 'WAF configurado', 'Logs habilitados'."
    )
    honeypot_id: str | None = None
    contexto: str = Field(
        "", description="Contexto operativo: a qué sistemas está vinculado el activo."
    )


class DatosCompliance(BaseModel):
    """Traducción normativa del hallazgo — output del Traductor Simbiótico."""

    marcos_aplicables: list[MarcoNormativo]
    controles_incumplidos: list[str] = Field(
        ..., description="IDs de controles incumplidos, ej: ['A.8.28', 'A.8.15']."
    )
    cita_normativa: str = Field(..., description="Cita textual del artículo/control aplicable.")
    justificacion: str = Field(
        ..., description="Razonamiento de la IA que conecta hallazgo con control."
    )
    impacto_legal: Severidad
    accion_mitigacion: str = Field(
        ..., description="Acción técnica concreta recomendada para remediar."
    )
    evidencia_auditoria: str = Field(
        "", description="Texto listo para dossier de auditoría externa."
    )


class ResultadoDrift(BaseModel):
    """Resultado del análisis de desviación procedimiento ↔ realidad operativa."""

    procedimiento_id: str = Field(..., description="Identificador del procedimiento analizado.")
    drift_detectado: bool = Field(..., description="True si se detecta desviación significativa.")
    descripcion_drift: str = Field("", description="Descripción de la desviación detectada.")
    fragmento_afectado: str = Field(
        "", description="Fragmento del procedimiento que diverge de la realidad."
    )
    redaccion_propuesta: str = Field(
        "", description="Nueva redacción propuesta para el fragmento afectado."
    )
    evidencias: list[str] = Field(
        default_factory=list, description="Lista de evidencias observadas que evidencian el drift."
    )
    controles_afectados: list[str] = Field(
        default_factory=list,
        description="IDs de controles normativos (ISO/ENS) que podrían verse comprometidos.",
    )
    impacto: Severidad = Field(
        Severidad.MEDIA, description="Severidad del drift desde perspectiva normativa."
    )


class HallazgoMaestro(BaseModel):
    """El Hallazgo Maestro: objeto unificado que atraviesa todo ROSETTA.

    Un Hallazgo Maestro reúne en un solo registro la perspectiva Red Team
    (qué se encontró), Blue Team (cómo está protegido) y Compliance
    (qué norma se incumple y qué hacer). Este es el corazón del diseño.
    """

    id_hallazgo: str = Field(
        ..., description="Identificador único del hallazgo, ej: 'SEC-2026-0001'."
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    red_team_data: DatosRedTeam
    blue_team_data: DatosBlueTeam | None = None
    compliance_data: DatosCompliance | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_hallazgo": "SEC-2026-0001",
                "timestamp": "2026-04-18T10:30:00Z",
                "red_team_data": {
                    "origen": "github_secrets",
                    "activo_detectado": "AWS_ACCESS_KEY_ID en repo público",
                    "evidencia": "https://github.com/org/repo/commit/abc123",
                    "vector_ataque": "Exposición de credencial cloud en código fuente",
                    "dificultad_explotacion": "baja",
                },
                "blue_team_data": {
                    "id_activo_interno": None,
                    "shadow_it": True,
                    "estado_defensa": "Sin rotación automática de claves",
                    "contexto": "Credencial con permisos sobre bucket de producción",
                },
            }
        }
    }
