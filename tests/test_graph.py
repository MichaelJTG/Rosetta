"""Tests del GrafoCorrelacion con driver Neo4j mockeado.

Cobertura objetivo: ≥80% de core/graph.py.
Sin conexión real a Neo4j — el driver se inyecta como mock.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from rosetta.core.graph import GrafoCorrelacion

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_driver() -> MagicMock:
    """Crea un mock del driver Neo4j con session context manager."""
    session = MagicMock()
    session.run.return_value = []  # iterable vacío → [dict(r) for r in []] = []
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)

    driver = MagicMock()
    driver.session.return_value = session
    return driver


# ---------------------------------------------------------------------------
# Tests de construcción
# ---------------------------------------------------------------------------


def test_grafo_inicializa_con_driver() -> None:
    """GrafoCorrelacion acepta un driver inyectado."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    assert grafo._driver is driver


def test_grafo_cerrar_llama_driver_close() -> None:
    """cerrar() delega en driver.close()."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    grafo.cerrar()
    driver.close.assert_called_once()


# ---------------------------------------------------------------------------
# Tests de registrar_hallazgo
# ---------------------------------------------------------------------------


def test_registrar_hallazgo_llama_session_run() -> None:
    """registrar_hallazgo ejecuta una query en el driver."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)

    grafo.registrar_hallazgo(
        hallazgo_id="SEC-2026-0001",
        activo="servidor-web-01",
        marco="iso_27001_2022",
        control_id="A.8.24",
        control_nombre="Uso de la criptografía",
        severidad="alta",
        origen="github_secrets",
        evidencia="https://github.com/org/repo/commit/abc",
        justificacion="Credencial expuesta en código fuente.",
        mitigacion="Rotar la clave AWS inmediatamente.",
        timestamp="2026-04-19T10:00:00",
    )

    session = driver.session.return_value.__enter__.return_value
    session.run.assert_called_once()
    call_kwargs = session.run.call_args[1]
    assert call_kwargs["hallazgo_id"] == "SEC-2026-0001"
    assert call_kwargs["control_id"] == "A.8.24"


# ---------------------------------------------------------------------------
# Tests de consultas
# ---------------------------------------------------------------------------


def test_hallazgos_por_marco_devuelve_lista() -> None:
    """hallazgos_por_marco devuelve una lista."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    resultado = grafo.hallazgos_por_marco("iso_27001_2022")
    assert isinstance(resultado, list)


def test_controles_mas_incumplidos_pasa_top_n() -> None:
    """controles_mas_incumplidos pasa top_n al driver."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    grafo.controles_mas_incumplidos("iso_27001_2022", top_n=5)

    session = driver.session.return_value.__enter__.return_value
    call_kwargs = session.run.call_args[1]
    assert call_kwargs["top_n"] == 5


def test_hallazgos_por_activo_pasa_nombre() -> None:
    """hallazgos_por_activo pasa el nombre del activo al driver."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    grafo.hallazgos_por_activo("servidor-web-01")

    session = driver.session.return_value.__enter__.return_value
    call_kwargs = session.run.call_args[1]
    assert call_kwargs["activo"] == "servidor-web-01"


# ---------------------------------------------------------------------------
# Tests de exportar_dossier
# ---------------------------------------------------------------------------


def test_exportar_dossier_contiene_encabezado() -> None:
    """exportar_dossier devuelve Markdown con encabezado del marco."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    md = grafo.exportar_dossier("iso_27001_2022")

    assert "iso_27001_2022" in md
    assert "Dossier" in md
    assert "Controles más incumplidos" in md
    assert "Detalle de hallazgos" in md


def test_exportar_dossier_titulo_personalizado() -> None:
    """exportar_dossier usa el título personalizado si se pasa."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    md = grafo.exportar_dossier("iso_27001_2022", titulo="Auditoría Q1 2026")

    assert "Auditoría Q1 2026" in md


def test_exportar_dossier_llama_ambas_queries() -> None:
    """exportar_dossier consulta controles_mas_incumplidos y hallazgos_por_marco."""
    driver = _make_driver()
    grafo = GrafoCorrelacion(driver)
    grafo.exportar_dossier("iso_27001_2022")

    session = driver.session.return_value.__enter__.return_value
    assert session.run.call_count >= 2


# ---------------------------------------------------------------------------
# Conexión (RNF-01): timeouts cortos y verificación al construir
# ---------------------------------------------------------------------------


def test_desde_uri_usa_timeouts_cortos_y_verifica_conexion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El driver se crea con timeouts de pocos segundos y se verifica la conexión."""
    driver = _make_driver()
    kwargs_recibidos: dict[str, object] = {}

    def driver_falso(_uri: str, **kwargs: object) -> MagicMock:
        kwargs_recibidos.update(kwargs)
        return driver

    monkeypatch.setattr("neo4j.GraphDatabase.driver", driver_falso)
    grafo = GrafoCorrelacion.desde_uri("bolt://neo4j:7687", "neo4j", "clave-ficticia")

    assert grafo._driver is driver
    driver.verify_connectivity.assert_called_once()
    assert kwargs_recibidos["connection_timeout"] <= 5  # type: ignore[operator]
    assert kwargs_recibidos["connection_acquisition_timeout"] <= 5  # type: ignore[operator]


def test_desde_uri_cierra_driver_y_propaga_si_neo4j_no_responde(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si Neo4j no responde, se libera el driver y el error llega al lifespan."""
    driver = _make_driver()
    driver.verify_connectivity.side_effect = ConnectionError("Neo4j apagado")
    monkeypatch.setattr("neo4j.GraphDatabase.driver", lambda *_a, **_k: driver)

    with pytest.raises(ConnectionError):
        GrafoCorrelacion.desde_uri("bolt://neo4j:7687", "neo4j", "clave-ficticia")
    driver.close.assert_called_once()
