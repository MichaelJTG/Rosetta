"""Adaptador Wazuh — SIEM open source (AGPLv3).

Orquestamos vía REST API de Wazuh 4.x — no se modifica ni embebe el código.
Soporta dos modos:
  - Modo API: autenticación JWT, consulta de alertas y estado de agentes.
  - Modo offline: ingesta de exports JSON o CSV sin conectividad al SIEM.

Licencia Wazuh: AGPLv3. Solo orquestación vía API/CLI — nunca fork embebido.
Documentación API: https://documentation.wazuh.com/current/user-manual/api/reference.html
"""

from __future__ import annotations

import csv
import io
from typing import Any

import httpx
import structlog

from rosetta.adapters.base import BlueTeamAdapter

logger = structlog.get_logger(__name__)

# Campos normalizados de una alerta Wazuh (valores por defecto)
_ALERTA_DEFAULTS: dict[str, Any] = {
    "id": "",
    "timestamp": "",
    "nivel": 0,
    "regla_id": "",
    "regla_descripcion": "",
    "agente_id": "",
    "agente_nombre": "",
    "activo": "",
    "datos": {},
}


class WazuhAdapter(BlueTeamAdapter):
    """Cliente REST de Wazuh 4.x para consumir alertas y estado de activos.

    Flujo de autenticación:
        1. POST /security/user/authenticate (Basic auth) → JWT token.
        2. Todas las llamadas posteriores usan Authorization: Bearer <token>.
        3. Si el servidor devuelve 401 (token expirado) se reautentica una vez.

    Args:
        api_url: URL base de la API (ej. "https://wazuh.ejemplo.com:55000").
        user: Usuario de la API de Wazuh.
        password: Contraseña del usuario.
        verify_ssl: Si False, ignora el certificado TLS (útil en lab/staging).
        timeout: Timeout en segundos para cada petición HTTP.
    """

    nombre = "wazuh"

    def __init__(
        self,
        api_url: str,
        user: str,
        password: str,
        verify_ssl: bool = False,
        timeout: float = 30.0,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self._user = user
        self._password = password
        self._token: str | None = None
        self._client = httpx.AsyncClient(verify=verify_ssl, timeout=timeout)

    # ------------------------------------------------------------------
    # BlueTeamAdapter — interfaz requerida
    # ------------------------------------------------------------------

    async def consultar_alertas(
        self,
        limit: int = 100,
        offset: int = 0,
        nivel_min: int = 3,
        activo: str | None = None,
        **_kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Consulta alertas activas en Wazuh vía API REST.

        Args:
            limit: Número máximo de alertas a recuperar (1-500).
            offset: Desplazamiento para paginación.
            nivel_min: Nivel mínimo de alerta Wazuh (1-15). Por defecto 3.
            activo: Si se indica, filtra por nombre o ID del agente.

        Returns:
            Lista de alertas normalizadas al formato interno de ROSETTA.
        """
        await self._ensure_token()
        params: dict[str, Any] = {
            "limit": min(limit, 500),
            "offset": offset,
            "level": nivel_min,
            "sort": "-timestamp",
        }
        if activo:
            params["agents_list"] = activo

        resp = await self._get("/security/events", params=params)
        items = resp.get("data", {}).get("affected_items", [])
        return [self._normalizar_alerta(item) for item in items]

    async def estado_activo(self, activo_id: str) -> dict[str, Any]:
        """Consulta el estado defensivo de un agente Wazuh por su ID.

        Args:
            activo_id: ID numérico del agente Wazuh (ej. "001").

        Returns:
            Dict con campos: id, nombre, ip, estado, version, ultimo_keepalive.
        """
        await self._ensure_token()
        resp = await self._get(f"/agents/{activo_id}")
        items = resp.get("data", {}).get("affected_items", [])
        if not items:
            return {"id": activo_id, "estado": "no_encontrado"}
        agente = items[0]
        return {
            "id": str(agente.get("id", activo_id)),
            "nombre": agente.get("name", ""),
            "ip": agente.get("ip", ""),
            "estado": agente.get("status", "desconocido"),
            "version": agente.get("version", ""),
            "ultimo_keepalive": agente.get("lastKeepAlive", ""),
        }

    # ------------------------------------------------------------------
    # Modo offline — ingesta de exports sin conectividad al SIEM
    # ------------------------------------------------------------------

    @staticmethod
    def ingestar_json(data: list[dict[str, Any]] | dict[str, Any]) -> list[dict[str, Any]]:
        """Parsea un export JSON de Wazuh.

        Compatible con:
          - Lista directa de objetos alerta.
          - Respuesta de API: ``{"data": {"affected_items": [...]}}``.

        Args:
            data: Datos JSON ya parseados (dict o lista).

        Returns:
            Lista de alertas normalizadas al formato ROSETTA.
        """
        if isinstance(data, dict):
            items = data.get("data", {}).get("affected_items", data.get("items", []))
        elif isinstance(data, list):
            items = data
        else:
            items = []

        return [WazuhAdapter._normalizar_alerta(item) for item in items if isinstance(item, dict)]

    @staticmethod
    def ingestar_csv(texto_csv: str) -> list[dict[str, Any]]:
        """Parsea un export CSV de Wazuh.

        Columnas esperadas (en cualquier orden, nombres con punto o guión bajo):
          id, timestamp, level, rule.id / rule_id, rule.description / rule_description,
          agent.id / agent_id, agent.name / agent_name, agent.ip / agent_ip

        Args:
            texto_csv: Contenido del fichero CSV como string.

        Returns:
            Lista de alertas normalizadas.
        """
        alertas: list[dict[str, Any]] = []
        reader = csv.DictReader(io.StringIO(texto_csv.strip()))
        for fila in reader:
            alerta = {**_ALERTA_DEFAULTS}
            alerta["id"] = fila.get("id", "")
            alerta["timestamp"] = fila.get("timestamp", "")
            try:
                alerta["nivel"] = int(fila.get("level", 0) or 0)
            except (ValueError, TypeError):
                alerta["nivel"] = 0
            alerta["regla_id"] = fila.get("rule.id", fila.get("rule_id", ""))
            alerta["regla_descripcion"] = fila.get(
                "rule.description", fila.get("rule_description", "")
            )
            alerta["agente_id"] = fila.get("agent.id", fila.get("agent_id", ""))
            alerta["agente_nombre"] = fila.get("agent.name", fila.get("agent_name", ""))
            alerta["activo"] = fila.get("agent.ip", fila.get("agent_ip", ""))
            alertas.append(alerta)
        return alertas

    # ------------------------------------------------------------------
    # Autenticación interna
    # ------------------------------------------------------------------

    async def _ensure_token(self) -> None:
        """Obtiene un nuevo token JWT si no hay uno activo."""
        if self._token:
            return
        await self._autenticar()

    async def _autenticar(self) -> None:
        """Autenticación Basic → JWT contra la API de Wazuh."""
        url = f"{self.api_url}/security/user/authenticate"
        try:
            resp = await self._client.post(url, auth=(self._user, self._password))
            resp.raise_for_status()
            body = resp.json()
            token = body.get("data", {}).get("token", "")
            if not token:
                raise RuntimeError("Wazuh no devolvió token JWT en la respuesta.")
            self._token = token
            logger.info("wazuh_autenticado", url=self.api_url)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Error autenticando con Wazuh en {self.api_url}: {exc}") from exc

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET autenticado contra la API de Wazuh con reintento por token expirado."""
        url = f"{self.api_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            resp = await self._client.get(url, headers=headers, params=params)
            if resp.status_code == 401:
                # Token expirado — reautenticar una vez
                self._token = None
                await self._autenticar()
                headers = {"Authorization": f"Bearer {self._token}"}
                resp = await self._client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Error consultando Wazuh {path}: {exc}") from exc

    # ------------------------------------------------------------------
    # Normalización interna
    # ------------------------------------------------------------------

    @staticmethod
    def _normalizar_alerta(item: dict[str, Any]) -> dict[str, Any]:
        """Normaliza un objeto alerta de la API de Wazuh al formato ROSETTA."""
        regla = item.get("rule", {})
        agente = item.get("agent", {})
        return {
            "id": str(item.get("id", "")),
            "timestamp": str(item.get("timestamp", "")),
            "nivel": int(regla.get("level", 0)),
            "regla_id": str(regla.get("id", "")),
            "regla_descripcion": str(regla.get("description", "")),
            "agente_id": str(agente.get("id", "")),
            "agente_nombre": str(agente.get("name", "")),
            "activo": str(agente.get("ip", agente.get("name", ""))),
            "datos": item,
        }

    async def aclose(self) -> None:
        """Cierra el cliente HTTP subyacente."""
        await self._client.aclose()
