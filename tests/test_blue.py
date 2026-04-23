"""Tests para FASE 4 Blue Team: WazuhAdapter + blue_enrichment + endpoint /blue/ingest."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rosetta.adapters.blue.wazuh import WazuhAdapter  # noqa: E402
from rosetta.core.blue_enrichment import (
    HallazgoEnriquecido,
    _extraer_ip,
    enriquecer,
    resumen_cobertura,
)

# ---------------------------------------------------------------------------
# Fixtures de datos
# ---------------------------------------------------------------------------

_ALERTA_API = {
    "id": "abc123",
    "timestamp": "2026-04-22T10:00:00",
    "rule": {"id": "5710", "level": 7, "description": "SSH brute force attempt"},
    "agent": {"id": "001", "name": "srv-web", "ip": "1.2.3.4"},
}

_ALERTA_NORMALIZADA = {
    "id": "abc123",
    "timestamp": "2026-04-22T10:00:00",
    "nivel": 7,
    "regla_id": "5710",
    "regla_descripcion": "SSH brute force attempt",
    "agente_id": "001",
    "agente_nombre": "srv-web",
    "activo": "1.2.3.4",
    "datos": _ALERTA_API,
}

_CSV_ALERTAS = """id,timestamp,level,rule.id,rule.description,agent.id,agent.name,agent.ip
1,2026-04-22T10:00:00,7,5710,SSH brute force,001,srv-web,1.2.3.4
2,2026-04-22T10:01:00,5,5503,Login failed,002,srv-db,2.2.2.2
"""


# ---------------------------------------------------------------------------
# WazuhAdapter._normalizar_alerta
# ---------------------------------------------------------------------------


class TestNormalizarAlerta:
    def test_campos_mapeados_correctamente(self) -> None:
        resultado = WazuhAdapter._normalizar_alerta(_ALERTA_API)

        assert resultado["id"] == "abc123"
        assert resultado["nivel"] == 7
        assert resultado["regla_id"] == "5710"
        assert resultado["regla_descripcion"] == "SSH brute force attempt"
        assert resultado["agente_id"] == "001"
        assert resultado["agente_nombre"] == "srv-web"
        assert resultado["activo"] == "1.2.3.4"
        assert resultado["datos"] is _ALERTA_API

    def test_campos_faltantes_usan_defaults(self) -> None:
        resultado = WazuhAdapter._normalizar_alerta({})

        assert resultado["id"] == ""
        assert resultado["nivel"] == 0
        assert resultado["activo"] == ""

    def test_ip_fallback_a_nombre_agente(self) -> None:
        item = {**_ALERTA_API, "agent": {"id": "001", "name": "mi-servidor"}}
        resultado = WazuhAdapter._normalizar_alerta(item)

        assert resultado["activo"] == "mi-servidor"


# ---------------------------------------------------------------------------
# WazuhAdapter.ingestar_json
# ---------------------------------------------------------------------------


class TestIngestarJson:
    def test_lista_directa(self) -> None:
        alertas = WazuhAdapter.ingestar_json([_ALERTA_API])

        assert len(alertas) == 1
        assert alertas[0]["nivel"] == 7

    def test_wrapper_api_affected_items(self) -> None:
        payload = {"data": {"affected_items": [_ALERTA_API, _ALERTA_API]}}
        alertas = WazuhAdapter.ingestar_json(payload)

        assert len(alertas) == 2

    def test_wrapper_items(self) -> None:
        payload = {"items": [_ALERTA_API]}
        alertas = WazuhAdapter.ingestar_json(payload)

        assert len(alertas) == 1

    def test_lista_vacia(self) -> None:
        assert WazuhAdapter.ingestar_json([]) == []

    def test_tipo_invalido_retorna_vacio(self) -> None:
        assert WazuhAdapter.ingestar_json("cadena") == []  # type: ignore[arg-type]

    def test_ignora_elementos_no_dict(self) -> None:
        alertas = WazuhAdapter.ingestar_json([_ALERTA_API, "string", 42])  # type: ignore[list-item]

        assert len(alertas) == 1


# ---------------------------------------------------------------------------
# WazuhAdapter.ingestar_csv
# ---------------------------------------------------------------------------


class TestIngestarCsv:
    def test_parsea_dos_filas(self) -> None:
        alertas = WazuhAdapter.ingestar_csv(_CSV_ALERTAS)

        assert len(alertas) == 2

    def test_campos_mapeados(self) -> None:
        alertas = WazuhAdapter.ingestar_csv(_CSV_ALERTAS)
        primera = alertas[0]

        assert primera["id"] == "1"
        assert primera["nivel"] == 7
        assert primera["regla_id"] == "5710"
        assert primera["agente_nombre"] == "srv-web"
        assert primera["activo"] == "1.2.3.4"

    def test_nivel_invalido_cero(self) -> None:
        csv_malo = (
            "id,timestamp,level,rule.id,rule.description,agent.id,agent.name,agent.ip\n"
            "1,ts,no-es-num,r,d,a,n,ip\n"
        )
        alertas = WazuhAdapter.ingestar_csv(csv_malo)

        assert alertas[0]["nivel"] == 0

    def test_csv_vacio_retorna_lista_vacia(self) -> None:
        assert WazuhAdapter.ingestar_csv("") == []

    def test_columnas_con_guion_bajo(self) -> None:
        csv_alt = (
            "id,timestamp,level,rule_id,rule_description,agent_id,agent_name,agent_ip\n"
            "1,ts,5,R001,Desc,a01,host,3.3.3.3\n"
        )
        alertas = WazuhAdapter.ingestar_csv(csv_alt)

        assert alertas[0]["regla_id"] == "R001"
        assert alertas[0]["activo"] == "3.3.3.3"


# ---------------------------------------------------------------------------
# WazuhAdapter — autenticación y API (httpx mock)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestWazuhAdapterApi:
    async def test_autenticar_obtiene_token(self) -> None:
        adapter = WazuhAdapter("https://wazuh.test:55000", "user", "pass")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"token": "mi-jwt-token"}}
        mock_resp.raise_for_status = MagicMock()

        with patch.object(adapter._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            await adapter._autenticar()

        assert adapter._token == "mi-jwt-token"

    async def test_autenticar_sin_token_lanza(self) -> None:
        adapter = WazuhAdapter("https://wazuh.test:55000", "user", "pass")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {}}
        mock_resp.raise_for_status = MagicMock()

        with (
            patch.object(adapter._client, "post", new_callable=AsyncMock, return_value=mock_resp),
            pytest.raises(RuntimeError, match="token JWT"),
        ):
            await adapter._autenticar()

    async def test_ensure_token_no_reautentica_si_hay_token(self) -> None:
        adapter = WazuhAdapter("https://wazuh.test:55000", "user", "pass")
        adapter._token = "token-existente"

        with patch.object(adapter, "_autenticar", new_callable=AsyncMock) as mock_auth:
            await adapter._ensure_token()

        mock_auth.assert_not_called()

    async def test_consultar_alertas_llama_endpoint(self) -> None:
        adapter = WazuhAdapter("https://wazuh.test:55000", "user", "pass")
        adapter._token = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"affected_items": [_ALERTA_API]}}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        with patch.object(adapter._client, "get", new_callable=AsyncMock, return_value=mock_resp):
            alertas = await adapter.consultar_alertas(limit=10, nivel_min=5)

        assert len(alertas) == 1
        assert alertas[0]["nivel"] == 7

    async def test_estado_activo_retorna_campos(self) -> None:
        adapter = WazuhAdapter("https://wazuh.test:55000", "user", "pass")
        adapter._token = "tok"

        agente = {
            "id": "001",
            "name": "srv-web",
            "ip": "1.2.3.4",
            "status": "active",
            "version": "4.7.0",
            "lastKeepAlive": "2026-04-22T10:00:00",
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"affected_items": [agente]}}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        with patch.object(adapter._client, "get", new_callable=AsyncMock, return_value=mock_resp):
            estado = await adapter.estado_activo("001")

        assert estado["id"] == "001"
        assert estado["estado"] == "active"
        assert estado["ip"] == "1.2.3.4"

    async def test_estado_activo_no_encontrado(self) -> None:
        adapter = WazuhAdapter("https://wazuh.test:55000", "user", "pass")
        adapter._token = "tok"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"affected_items": []}}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        with patch.object(adapter._client, "get", new_callable=AsyncMock, return_value=mock_resp):
            estado = await adapter.estado_activo("999")

        assert estado["estado"] == "no_encontrado"


# ---------------------------------------------------------------------------
# blue_enrichment — _extraer_ip
# ---------------------------------------------------------------------------


class TestExtraerIp:
    def test_ip_con_puerto_y_protocolo(self) -> None:
        assert _extraer_ip("1.2.3.4:22/tcp") == "1.2.3.4"

    def test_url_https(self) -> None:
        assert _extraer_ip("https://ejemplo.com/ruta") == "ejemplo.com"

    def test_url_http_con_puerto(self) -> None:
        assert _extraer_ip("http://10.0.0.1:8080/api") == "10.0.0.1"

    def test_hostname_simple(self) -> None:
        assert _extraer_ip("mi-servidor") == "mi-servidor"

    def test_vacio(self) -> None:
        assert _extraer_ip("") == ""


# ---------------------------------------------------------------------------
# blue_enrichment — enriquecer
# ---------------------------------------------------------------------------


class TestEnriquecer:
    def test_coincidencia_por_ip(self) -> None:
        hallazgos = [
            {
                "activo_detectado": "1.2.3.4:22/tcp",
                "vector_ataque": "SSH expuesto",
                "dificultad_explotacion": "alta",
            }
        ]
        resultado = enriquecer(hallazgos, [_ALERTA_NORMALIZADA])

        assert resultado[0].score_correlacion == 1
        assert len(resultado[0].alertas_blue) == 1

    def test_sin_coincidencia(self) -> None:
        hallazgos = [
            {
                "activo_detectado": "9.9.9.9:80/tcp",
                "vector_ataque": "HTTP expuesto",
                "dificultad_explotacion": "baja",
            }
        ]
        resultado = enriquecer(hallazgos, [_ALERTA_NORMALIZADA])

        assert resultado[0].score_correlacion == 0
        assert resultado[0].alertas_blue == []

    def test_multiples_hallazgos_selectivos(self) -> None:
        hallazgos = [
            {
                "activo_detectado": "1.2.3.4:22/tcp",
                "vector_ataque": "SSH",
                "dificultad_explotacion": "alta",
            },
            {
                "activo_detectado": "5.5.5.5:80/tcp",
                "vector_ataque": "HTTP",
                "dificultad_explotacion": "baja",
            },
        ]
        resultado = enriquecer(hallazgos, [_ALERTA_NORMALIZADA])

        assert resultado[0].score_correlacion == 1
        assert resultado[1].score_correlacion == 0

    def test_lista_vacia_hallazgos(self) -> None:
        assert enriquecer([], [_ALERTA_NORMALIZADA]) == []

    def test_lista_vacia_alertas(self) -> None:
        hallazgos = [
            {
                "activo_detectado": "1.2.3.4:22/tcp",
                "vector_ataque": "x",
                "dificultad_explotacion": "alta",
            }
        ]
        assert enriquecer(hallazgos, [])[0].score_correlacion == 0

    def test_severidad_preservada(self) -> None:
        hallazgos = [
            {"activo_detectado": "x", "vector_ataque": "y", "dificultad_explotacion": "critica"}
        ]
        assert enriquecer(hallazgos, [])[0].severidad == "critica"


# ---------------------------------------------------------------------------
# blue_enrichment — resumen_cobertura
# ---------------------------------------------------------------------------


class TestResumenCobertura:
    def test_con_y_sin_cobertura(self) -> None:
        enriquecidos = [
            HallazgoEnriquecido("a", "v", "alta", alertas_blue=[{}], score_correlacion=1),
            HallazgoEnriquecido("b", "v", "baja", alertas_blue=[], score_correlacion=0),
        ]
        resumen = resumen_cobertura(enriquecidos)

        assert resumen["total_hallazgos"] == 2
        assert resumen["con_cobertura"] == 1
        assert resumen["sin_cobertura"] == 1
        assert resumen["porcentaje_cobertura"] == 50.0
        assert resumen["total_alertas_correlacionadas"] == 1

    def test_lista_vacia(self) -> None:
        resumen = resumen_cobertura([])

        assert resumen["total_hallazgos"] == 0
        assert resumen["porcentaje_cobertura"] == 0.0

    def test_cobertura_total(self) -> None:
        enriquecidos = [
            HallazgoEnriquecido("a", "v", "alta", alertas_blue=[{}], score_correlacion=2),
            HallazgoEnriquecido("b", "v", "alta", alertas_blue=[{}], score_correlacion=1),
        ]
        resumen = resumen_cobertura(enriquecidos)

        assert resumen["porcentaje_cobertura"] == 100.0
        assert resumen["total_alertas_correlacionadas"] == 3


# ---------------------------------------------------------------------------
# Endpoint POST /blue/ingest
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from rosetta.api.main import app

    with TestClient(app) as c:
        yield c


class TestBlueIngestEndpoint:
    def test_ingest_json_retorna_alertas(self, client) -> None:
        r = client.post("/blue/ingest", json={"formato": "json", "datos_json": [_ALERTA_API]})

        assert r.status_code == 200
        body = r.json()
        assert body["total_alertas"] == 1
        assert body["alertas"][0]["nivel"] == 7
        assert "resumen_cobertura" in body

    def test_ingest_csv_retorna_alertas(self, client) -> None:
        r = client.post("/blue/ingest", json={"formato": "csv", "datos_csv": _CSV_ALERTAS})

        assert r.status_code == 200
        assert r.json()["total_alertas"] == 2

    def test_ingest_json_sin_datos_400(self, client) -> None:
        r = client.post("/blue/ingest", json={"formato": "json"})
        assert r.status_code == 400

    def test_ingest_csv_sin_datos_400(self, client) -> None:
        r = client.post("/blue/ingest", json={"formato": "csv"})
        assert r.status_code == 400

    def test_ingest_lista_vacia_ok(self, client) -> None:
        r = client.post("/blue/ingest", json={"formato": "json", "datos_json": []})

        assert r.status_code == 200
        assert r.json()["total_alertas"] == 0
