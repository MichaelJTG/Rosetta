"""Adaptador Wazuh — SIEM open source.

Wazuh es AGPLv3. Orquestamos vía su API REST, no modificamos su código.
Esta es la vía legalmente limpia: consumir outputs de Wazuh sin forkear.
"""

from __future__ import annotations

from typing import Any

import httpx

from rosetta.adapters.base import BlueTeamAdapter


class WazuhAdapter(BlueTeamAdapter):
    """Cliente REST de Wazuh para consumir alertas y estado de activos."""

    nombre = "wazuh"

    def __init__(self, api_url: str, user: str, password: str) -> None:
        self.api_url = api_url.rstrip("/")
        self.user = user
        self._password = password
        self._token: str | None = None
        self._client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def consultar_alertas(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Consulta alertas activas en Wazuh."""
        # TODO [MVP-4]: Auth + GET /security/alerts con filtros.
        raise NotImplementedError("WazuhAdapter pendiente. Ver docs/ROADMAP.md#mvp-4")

    async def estado_activo(self, activo_id: str) -> dict[str, Any]:
        """Consulta el estado de un agente/activo en Wazuh."""
        # TODO [MVP-4]: GET /agents/{agent_id}.
        raise NotImplementedError("WazuhAdapter pendiente. Ver docs/ROADMAP.md#mvp-4")
