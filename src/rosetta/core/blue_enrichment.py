"""Enriquecimiento Red Team ↔ Blue Team para informes de auditoría.

Correlaciona hallazgos Red Team (DatosRedTeam) con alertas Blue Team (Wazuh)
usando coincidencia de activo/IP. El resultado enriquecido alimenta al
ReportGenerator para producir un informe de auditoría cruzado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HallazgoEnriquecido:
    """Hallazgo Red Team con alertas Blue Team correlacionadas.

    Attributes:
        activo: Activo detectado por el sensor Red Team.
        vector_ataque: Descripción del vector de ataque.
        severidad: Nivel de severidad del hallazgo Red Team.
        alertas_blue: Alertas Wazuh correlacionadas con este activo.
        score_correlacion: Número de alertas Blue coincidentes (0 = sin cobertura).
    """

    activo: str
    vector_ataque: str
    severidad: str
    alertas_blue: list[dict[str, Any]] = field(default_factory=list)
    score_correlacion: int = 0


def enriquecer(
    hallazgos_red: list[dict[str, Any]],
    alertas_blue: list[dict[str, Any]],
) -> list[HallazgoEnriquecido]:
    """Correlaciona hallazgos Red Team con alertas Blue Team por coincidencia de activo.

    Estrategia de matching:
      1. Extrae la IP/hostname del campo ``activo_detectado`` del hallazgo Red.
      2. Busca alertas Blue cuyo campo ``activo`` contenga esa IP/hostname (substring).
      3. Hallazgos sin coincidencia quedan con ``alertas_blue=[]``.

    Args:
        hallazgos_red: Lista de dicts con campos ``activo_detectado``, ``vector_ataque``,
            ``dificultad_explotacion`` (o ``severidad``).
        alertas_blue: Lista de alertas normalizadas por WazuhAdapter con campo ``activo``.

    Returns:
        Lista de HallazgoEnriquecido, uno por hallazgo Red Team.
    """
    resultado: list[HallazgoEnriquecido] = []

    for h in hallazgos_red:
        activo_red = str(h.get("activo_detectado", ""))
        ip_red = _extraer_ip(activo_red)

        alertas_match = _buscar_alertas(ip_red, alertas_blue) if ip_red else []

        severidad_raw = h.get("dificultad_explotacion", h.get("severidad", "media"))
        # Compatibilidad con enums Pydantic (tienen .value)
        severidad = str(getattr(severidad_raw, "value", severidad_raw))

        resultado.append(
            HallazgoEnriquecido(
                activo=activo_red,
                vector_ataque=str(h.get("vector_ataque", "")),
                severidad=severidad,
                alertas_blue=alertas_match,
                score_correlacion=len(alertas_match),
            )
        )

    return resultado


def _extraer_ip(activo: str) -> str:
    """Extrae la IP o hostname de un campo activo_detectado.

    Ejemplos:
        "1.2.3.4:22/tcp"          → "1.2.3.4"
        "https://ejemplo.com/ruta" → "ejemplo.com"
        "ejemplo.com"              → "ejemplo.com"
    """
    candidato = activo.strip()
    for prefix in ("https://", "http://"):
        if candidato.startswith(prefix):
            candidato = candidato[len(prefix) :]
    candidato = candidato.split("/")[0]
    candidato = candidato.split(":")[0]
    return candidato.strip()


def _buscar_alertas(ip_red: str, alertas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Devuelve alertas cuyo campo 'activo' coincide con la IP del hallazgo Red."""
    if not ip_red:
        return []
    return [
        a
        for a in alertas
        if ip_red in str(a.get("activo", "")) or str(a.get("activo", "")) in ip_red
    ]


def resumen_cobertura(enriquecidos: list[HallazgoEnriquecido]) -> dict[str, Any]:
    """Genera un resumen estadístico de la cobertura defensiva Blue Team.

    Returns:
        Dict con: total_hallazgos, con_cobertura, sin_cobertura,
        porcentaje_cobertura, total_alertas_correlacionadas.
    """
    total = len(enriquecidos)
    con_cobertura = sum(1 for h in enriquecidos if h.score_correlacion > 0)
    sin_cobertura = total - con_cobertura
    pct = round(con_cobertura / total * 100, 1) if total > 0 else 0.0
    total_alertas = sum(h.score_correlacion for h in enriquecidos)

    return {
        "total_hallazgos": total,
        "con_cobertura": con_cobertura,
        "sin_cobertura": sin_cobertura,
        "porcentaje_cobertura": pct,
        "total_alertas_correlacionadas": total_alertas,
    }
