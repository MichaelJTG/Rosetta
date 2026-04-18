"""Adaptador para Nuclei — escáner de vulnerabilidades basado en templates.

Nuclei es MIT, orquestable vía CLI, output JSON estable. Ideal para
integrar sin tocar su código.

Requisitos: binario `nuclei` disponible en PATH.
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
"""

from __future__ import annotations

from typing import Any

from rosetta.adapters.base import RedTeamAdapter
from rosetta.core.models import DatosRedTeam


class NucleiAdapter(RedTeamAdapter):
    """Wrapper que ejecuta `nuclei` como subproceso y parsea su JSON."""

    nombre = "nuclei"

    def __init__(self, binario: str = "nuclei") -> None:
        self.binario = binario

    async def escanear(self, objetivo: str, **kwargs: Any) -> list[DatosRedTeam]:
        """Ejecuta `nuclei -u <objetivo> -jsonl` y normaliza salida."""
        # TODO [MVP-3]:
        #   1. Subprocess asyncio con `nuclei -u {objetivo} -jsonl -silent`.
        #   2. Parsear cada línea JSON.
        #   3. Mapear a DatosRedTeam (origen=NUCLEI, evidencia, severidad).
        #   4. Devolver lista.
        raise NotImplementedError("NucleiAdapter pendiente. Ver docs/ROADMAP.md#mvp-3")
