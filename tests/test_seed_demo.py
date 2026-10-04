"""Tests del script de datos de demostración (A-4).

Garantizan las reglas del seed: solo habla con la API pública de ROSETTA
(nunca escribe en las bases de datos), autentica cada llamada, cubre los siete
marcos con corpus y no se detiene si un paso falla.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest

_RUTA = Path(__file__).resolve().parents[1] / "scripts" / "seed_demo.py"
_ENDPOINTS_PERMITIDOS = {
    "/auth/login",
    "/translate",
    "/analyze-diff",
    "/blue/ingest",
    "/drift/analyze",
    "/ingest/pdf",
    "/reports/generate",
}
_MARCOS_CON_CORPUS = {
    "iso_27001_2022",
    "ens_2022",
    "nis2",
    "dora",
    "rgpd",
    "nist_csf_2",
    "pci_dss_4",
}


def _cargar_seed() -> ModuleType:
    spec = importlib.util.spec_from_file_location("seed_demo", _RUTA)
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["seed_demo"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


seed = _cargar_seed()


class _ApiFalsa:
    """Registra cada petición y responde como lo haría la API."""

    def __init__(self, fallar_en: str | None = None) -> None:
        self.peticiones: list[httpx.Request] = []
        self.fallar_en = fallar_en

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        ruta = request.url.path
        if ruta == self.fallar_en:
            return httpx.Response(502, json={"detail": "LLM no disponible"})
        respuestas: dict[str, Any] = {
            "/auth/login": {"access_token": "tok-prueba", "refresh_token": "ref"},
            "/translate": {"controles_incumplidos": ["mp.info.3"]},
            "/reports/generate": {
                "md_url": "/reports/download/x.md",
                "pdf_url": "/reports/download/x.pdf",
            },
        }
        return httpx.Response(200, json=respuestas.get(ruta, {}))


def _cliente(api: _ApiFalsa) -> httpx.Client:
    return httpx.Client(base_url="http://rosetta.test", transport=httpx.MockTransport(api))


def test_solo_usa_endpoints_de_la_api_y_autentica_cada_llamada() -> None:
    api = _ApiFalsa()
    with _cliente(api) as cliente:
        seed.autenticar(cliente, "auditor-demo", "clave-ficticia")
        resumen = seed.ejecutar(cliente)

    rutas = {p.url.path for p in api.peticiones}
    assert rutas <= _ENDPOINTS_PERMITIDOS
    assert rutas == _ENDPOINTS_PERMITIDOS  # recorre todos los pasos
    for p in api.peticiones[1:]:  # todas salvo el propio login
        assert p.headers["Authorization"] == "Bearer tok-prueba"
    assert not resumen.errores


def test_los_hallazgos_cubren_los_siete_marcos_con_corpus() -> None:
    api = _ApiFalsa()
    with _cliente(api) as cliente:
        seed.ejecutar(cliente, con_pdf=False)

    marcos: set[str] = set()
    for p in api.peticiones:
        if p.url.path == "/translate":
            marcos.update(json.loads(p.content)["marcos"])
    assert marcos == _MARCOS_CON_CORPUS


def test_datos_ficticios_usan_dominios_y_ips_de_documentacion() -> None:
    """Ningún activo apunta a un dominio o IP real (RFC 2606 / RFC 5737)."""
    for item in seed.HALLAZGOS:
        activo = item["hallazgo"]["activo_detectado"]
        assert activo.endswith(".example") or activo.startswith(("203.0.113.", "198.51.100."))
    for alerta in seed.ALERTAS_WAZUH:
        assert alerta["agent"]["ip"].startswith(("203.0.113.", "198.51.100.", "192.0.2."))


def test_un_paso_fallido_se_registra_y_el_resto_continua() -> None:
    api = _ApiFalsa(fallar_en="/drift/analyze")
    with _cliente(api) as cliente:
        resumen = seed.ejecutar(cliente, con_pdf=False)

    assert resumen.errores == ["drift/analyze: HTTP 502"]
    assert "reports/generate" in resumen.correctos


def test_login_fallido_detiene_el_seed() -> None:
    def api(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Authentication required"})

    transporte = httpx.MockTransport(api)
    with (
        httpx.Client(base_url="http://rosetta.test", transport=transporte) as c,
        pytest.raises(SystemExit),
    ):
        seed.autenticar(c, "auditor-demo", "mala")


def test_sin_credenciales_no_intenta_login() -> None:
    api = _ApiFalsa()
    with _cliente(api) as cliente:
        seed.autenticar(cliente, None, None)
    assert api.peticiones == []


def test_el_pdf_de_entrada_es_un_pdf_valido() -> None:
    assert seed._pdf_informe().startswith(b"%PDF")


def test_el_script_no_accede_a_las_bases_de_datos() -> None:
    """El seed no importa sqlite3 ni los almacenes internos de ROSETTA."""
    fuente = _RUTA.read_text(encoding="utf-8")
    for prohibido in ("sqlite3", "SessionStore", "ControlStore", "chromadb", "neo4j"):
        assert prohibido not in fuente.replace("ChromaDB, Neo4j", "")
