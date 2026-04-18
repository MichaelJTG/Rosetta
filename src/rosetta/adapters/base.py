"""Interfaces base para los adaptadores de ROSETTA.

Filosofía: orquestamos herramientas open source, no las forkeamos.
Cada adaptador wrapea CLI/API de una herramienta externa y normaliza
su salida al formato interno del Hallazgo Maestro.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from rosetta.core.models import DatosRedTeam


class RedTeamAdapter(ABC):
    """Interfaz para sensores Red Team / OSINT."""

    nombre: str

    @abstractmethod
    async def escanear(self, objetivo: str, **kwargs: Any) -> list[DatosRedTeam]:
        """Ejecuta el escaneo contra un objetivo autorizado.

        Args:
            objetivo: Dominio, IP, URL o identificador del activo a auditar.
            **kwargs: Parámetros específicos del sensor.

        Returns:
            Lista de hallazgos normalizados al formato DatosRedTeam.
        """


class BlueTeamAdapter(ABC):
    """Interfaz para sensores Blue Team (SIEM, EDR, logs)."""

    nombre: str

    @abstractmethod
    async def consultar_alertas(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Consulta alertas/eventos del sistema de detección."""

    @abstractmethod
    async def estado_activo(self, activo_id: str) -> dict[str, Any]:
        """Consulta el estado defensivo de un activo concreto."""
