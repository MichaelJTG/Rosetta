"""Comportamiento ante errores de la API real (A-8 · RNF-01 · RF-15).

Cubre los tres escenarios que se demuestran en el vídeo:
- Neo4j caído (al arrancar o a mitad de uso): la API degrada, no se cae.
- Entrada inválida: 422 con detalle de validación, sin trazas internas.
- Usuario sin credenciales o con credenciales erróneas: 401.
"""

from __future__ import annotations

import base64
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

import rosetta.api.main as api_main
from rosetta.api.deps import get_grafo, get_session_findings, get_traductor
from rosetta.api.main import app
from rosetta.core.models import DatosCompliance, MarcoNormativo, Severidad

_HALLAZGO = {
    "origen": "nuclei",
    "activo_detectado": "portal-citas.techserv.example",
    "evidencia": "https://portal-citas.techserv.example/.env",
    "vector_ataque": "Fichero .env con credenciales expuesto públicamente",
    "dificultad_explotacion": "baja",
}

_COMPLIANCE = DatosCompliance(
    marcos_aplicables=[MarcoNormativo.ENS_2022],
    controles_incumplidos=["mp.info.3"],
    cita_normativa="mp.info.3 Cifrado de la información",
    justificacion="Credenciales expuestas sin protección.",
    impacto_legal=Severidad.ALTA,
    accion_mitigacion="Retirar el fichero y rotar las credenciales.",
    evidencia_auditoria="Detectado por Nuclei.",
)


class _RagFalso:
    """Sustituye a NormativaRAG para que el lifespan no cargue el modelo."""

    def __init__(self, **_: Any) -> None:
        pass


def _grafo_caido() -> MagicMock:
    """Grafo cuyo driver falla en cualquier operación (Neo4j apagado)."""
    grafo = MagicMock()
    error = ConnectionError("Neo4j no disponible")
    grafo.registrar_hallazgo.side_effect = error
    grafo.hallazgos_por_marco.side_effect = error
    grafo.controles_mas_incumplidos.side_effect = error
    return grafo


@pytest.fixture
def cliente_neo4j_caido() -> Iterator[TestClient]:
    """API con dependencias de dominio falsas y un grafo que no responde."""
    traductor = MagicMock()
    traductor.traducir = AsyncMock(return_value=_COMPLIANCE)
    traductor.marcos_activos = [MarcoNormativo.ENS_2022]
    hallazgos: list[Any] = []
    app.dependency_overrides[get_traductor] = lambda: traductor
    app.dependency_overrides[get_grafo] = _grafo_caido
    app.dependency_overrides[get_session_findings] = lambda: hallazgos
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Neo4j caído (RNF-01)
# ---------------------------------------------------------------------------


def test_api_arranca_con_neo4j_inaccesible(monkeypatch: pytest.MonkeyPatch) -> None:
    """Si Neo4j no responde al arrancar, la API arranca en modo memoria."""
    monkeypatch.setattr(api_main, "NormativaRAG", _RagFalso)
    monkeypatch.setenv("NEO4J_URI", "bolt://127.0.0.1:9")  # puerto sin servicio

    with TestClient(app) as cliente:
        assert app.state.grafo is None
        assert cliente.get("/health").status_code == 200


def test_translate_responde_aunque_neo4j_caiga(cliente_neo4j_caido: TestClient) -> None:
    """Persistir en el grafo es opcional: un fallo de Neo4j no rompe /translate."""
    r = cliente_neo4j_caido.post("/translate", json={"hallazgo": _HALLAZGO, "marcos": ["ens_2022"]})
    assert r.status_code == 200
    assert r.json()["controles_incumplidos"] == ["mp.info.3"]


def test_estado_cumplimiento_cae_a_memoria_si_neo4j_falla(
    cliente_neo4j_caido: TestClient,
) -> None:
    """El panel de cumplimiento se calcula en memoria si la consulta a Neo4j falla."""
    r = cliente_neo4j_caido.get("/compliance/state/ens_2022")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Entrada inválida
# ---------------------------------------------------------------------------


def test_translate_sin_hallazgo_devuelve_422(cliente_neo4j_caido: TestClient) -> None:
    """Un cuerpo sin el hallazgo obligatorio se rechaza en la validación Pydantic."""
    r = cliente_neo4j_caido.post("/translate", json={"marcos": ["ens_2022"]})
    assert r.status_code == 422
    assert "Traceback" not in r.text


def test_translate_marco_inexistente_devuelve_422(cliente_neo4j_caido: TestClient) -> None:
    """Un marco normativo que no existe se rechaza antes de llamar al LLM."""
    r = cliente_neo4j_caido.post("/translate", json={"hallazgo": _HALLAZGO, "marcos": ["iso_9001"]})
    assert r.status_code == 422


def test_translate_severidad_invalida_devuelve_422(cliente_neo4j_caido: TestClient) -> None:
    """Los enums del Hallazgo Maestro se validan: una severidad inventada es un 422."""
    malo = {**_HALLAZGO, "dificultad_explotacion": "apocaliptica"}
    r = cliente_neo4j_caido.post("/translate", json={"hallazgo": malo})
    assert r.status_code == 422


def test_json_mal_formado_devuelve_422(cliente_neo4j_caido: TestClient) -> None:
    """Un cuerpo que no es JSON válido no provoca un 500."""
    r = cliente_neo4j_caido.post(
        "/translate", content=b"{no es json", headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Credenciales (RF-15)
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_activa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "auditor-demo")
    monkeypatch.setenv("ROSETTA_PASSWORD", "clave-ficticia-de-prueba")
    monkeypatch.setenv("ROSETTA_JWT_SECRET", "x" * 40)


@pytest.mark.usefixtures("auth_activa")
def test_sin_credenciales_devuelve_401(cliente_neo4j_caido: TestClient) -> None:
    r = cliente_neo4j_caido.get("/findings")
    assert r.status_code == 401


@pytest.mark.usefixtures("auth_activa")
def test_basic_con_password_erronea_devuelve_401(cliente_neo4j_caido: TestClient) -> None:
    cred = base64.b64encode(b"auditor-demo:no-es-esta").decode()
    r = cliente_neo4j_caido.get("/findings", headers={"Authorization": f"Basic {cred}"})
    assert r.status_code == 401


@pytest.mark.usefixtures("auth_activa")
def test_token_jwt_falsificado_devuelve_401(cliente_neo4j_caido: TestClient) -> None:
    r = cliente_neo4j_caido.get("/findings", headers={"Authorization": "Bearer eyJhbGciOi.falso.x"})
    assert r.status_code == 401


@pytest.mark.usefixtures("auth_activa")
def test_login_erroneo_devuelve_401_y_correcto_da_token_valido(
    cliente_neo4j_caido: TestClient,
) -> None:
    malo = cliente_neo4j_caido.post(
        "/auth/login", json={"username": "auditor-demo", "password": "incorrecta"}
    )
    assert malo.status_code == 401

    bueno = cliente_neo4j_caido.post(
        "/auth/login",
        json={"username": "auditor-demo", "password": "clave-ficticia-de-prueba"},
    )
    assert bueno.status_code == 200
    token = bueno.json()["access_token"]
    r = cliente_neo4j_caido.get("/findings", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_api_no_arranca_con_autenticacion_mal_configurada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B-5: con usuarios definidos y sin ROSETTA_JWT_SECRET la API se niega a arrancar."""
    monkeypatch.setattr(api_main, "NormativaRAG", _RagFalso)
    monkeypatch.setenv("ROSETTA_USER", "auditor-demo")
    monkeypatch.setenv("ROSETTA_PASSWORD", "clave-ficticia-de-prueba")
    monkeypatch.delenv("ROSETTA_JWT_SECRET")

    with pytest.raises(RuntimeError, match="ROSETTA_JWT_SECRET"), TestClient(app):
        pass
