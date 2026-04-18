"""Adaptador para Amass — descubrimiento de subdominios y ASM.

Apache 2.0, orquestable vía CLI.
"""

from __future__ import annotations

from typing import Any

from rosetta.adapters.base import RedTeamAdapter
from rosetta.core.models import DatosRedTeam


class AmassAdapter(RedTeamAdapter):
    """Wrapper que ejecuta `amass enum` y normaliza resultados."""

    nombre = "amass"

    def __init__(self, binario: str = "amass") -> None:
        self.binario = binario

    async def escanear(self, objetivo: str, **kwargs: Any) -> list[DatosRedTeam]:
        """Ejecuta `amass enum -d <dominio> -json -` y normaliza salida."""
        # TODO [MVP-3]: Similar a Nuclei, pero descubriendo subdominios.
        raise NotImplementedError("AmassAdapter pendiente. Ver docs/ROADMAP.md#mvp-3")
