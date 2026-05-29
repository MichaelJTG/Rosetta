"""Tests para ControlStore (core/control_store.py).

Usa tmp_path de pytest para crear una BD SQLite temporal por test.
Verifica estados de controles, caché de plantillas y vuln-timeline.
"""

from __future__ import annotations

import pytest

from rosetta.core.control_store import ControlStore


@pytest.fixture
def store(tmp_path: pytest.TempPathFactory) -> ControlStore:
    """ControlStore con BD temporal aislada."""
    db = str(tmp_path / "test_controls.db")
    s = ControlStore(db_path=db)
    yield s
    s.close()


# ---------------------------------------------------------------------------
# estado de controles
# ---------------------------------------------------------------------------


def test_get_estado_defaults_when_empty(store: ControlStore) -> None:
    """Control no registrado devuelve valores por defecto."""
    result = store.get_estado("iso_27001_2022", "A.8.15")
    assert result["estado"] == "no_aplica"
    assert result["responsable"] == ""
    assert result["comentarios"] == ""
    assert result["updated_at"] == ""


def test_set_and_get_estado(store: ControlStore) -> None:
    """set_estado persiste y get_estado recupera correctamente."""
    store.set_estado("iso_27001_2022", "A.8.15", "cumple", "Ana Garcia", "Logs configurados.")
    result = store.get_estado("iso_27001_2022", "A.8.15")
    assert result["estado"] == "cumple"
    assert result["responsable"] == "Ana Garcia"
    assert result["comentarios"] == "Logs configurados."
    assert result["updated_at"] != ""


def test_set_estado_updates_existing(store: ControlStore) -> None:
    """Segunda llamada a set_estado actualiza el registro."""
    store.set_estado("ens_2022", "op.mon.1", "parcial", "Pedro", "Primera nota.")
    store.set_estado("ens_2022", "op.mon.1", "cumple", "Pedro", "Nota actualizada.")
    result = store.get_estado("ens_2022", "op.mon.1")
    assert result["estado"] == "cumple"
    assert result["comentarios"] == "Nota actualizada."


def test_set_estado_invalid_raises(store: ControlStore) -> None:
    """Estado invalido lanza ValueError."""
    with pytest.raises(ValueError, match="desconocido"):
        store.set_estado("iso_27001_2022", "A.8.15", "desconocido")


def test_get_all_estados_empty(store: ControlStore) -> None:
    """get_all_estados devuelve dict vacio si no hay registros."""
    result = store.get_all_estados("iso_27001_2022")
    assert result == {}


def test_get_all_estados_multiple(store: ControlStore) -> None:
    """get_all_estados devuelve todos los controles del marco."""
    store.set_estado("iso_27001_2022", "A.8.15", "cumple", "Ana", "")
    store.set_estado("iso_27001_2022", "A.8.16", "no_cumple", "Pedro", "Pendiente.")
    store.set_estado("ens_2022", "op.mon.1", "parcial", "Luis", "")  # otro marco

    result = store.get_all_estados("iso_27001_2022")
    assert len(result) == 2
    assert result["A.8.15"]["estado"] == "cumple"
    assert result["A.8.16"]["estado"] == "no_cumple"
    assert "op.mon.1" not in result  # no mezcla marcos


def test_all_valid_estados(store: ControlStore) -> None:
    """Todos los estados validos se aceptan sin error."""
    for estado in ("cumple", "parcial", "no_cumple", "no_aplica"):
        store.set_estado("iso_27001_2022", f"A.8.TEST.{estado}", estado)
        assert store.get_estado("iso_27001_2022", f"A.8.TEST.{estado}")["estado"] == estado


# ---------------------------------------------------------------------------
# cache de plantillas
# ---------------------------------------------------------------------------


def test_get_plantilla_returns_none_when_missing(store: ControlStore) -> None:
    """get_plantilla devuelve None si no existe cache."""
    assert store.get_plantilla("iso_27001_2022", "A.8.15") is None


def test_set_and_get_plantilla(store: ControlStore) -> None:
    """set_plantilla persiste y get_plantilla recupera."""
    plantilla = "# Objetivo\n\nDescripcion del procedimiento."
    store.set_plantilla("iso_27001_2022", "A.8.15", plantilla)
    result = store.get_plantilla("iso_27001_2022", "A.8.15")
    assert result == plantilla


def test_set_plantilla_overwrites(store: ControlStore) -> None:
    """Segunda llamada a set_plantilla sobreescribe la anterior."""
    store.set_plantilla("iso_27001_2022", "A.8.16", "version 1")
    store.set_plantilla("iso_27001_2022", "A.8.16", "version 2")
    assert store.get_plantilla("iso_27001_2022", "A.8.16") == "version 2"


# ---------------------------------------------------------------------------
# vuln timeline
# ---------------------------------------------------------------------------


def test_get_timeline_defaults_when_missing(store: ControlStore) -> None:
    """get_timeline devuelve defaults si no existe registro."""
    result = store.get_timeline("SEC-AAAAAAAA")
    assert result["fecha_limite"] is None
    assert result["propietario"] == ""


def test_set_and_get_timeline(store: ControlStore) -> None:
    """set_timeline persiste y get_timeline recupera."""
    store.set_timeline("SEC-00000001", "2026-12-31", "Carlos Lopez")
    result = store.get_timeline("SEC-00000001")
    assert result["fecha_limite"] == "2026-12-31"
    assert result["propietario"] == "Carlos Lopez"


def test_set_timeline_updates_existing(store: ControlStore) -> None:
    """Segunda llamada a set_timeline actualiza el registro."""
    store.set_timeline("SEC-00000002", "2026-06-01", "Ana")
    store.set_timeline("SEC-00000002", "2026-09-01", "Pedro")
    result = store.get_timeline("SEC-00000002")
    assert result["fecha_limite"] == "2026-09-01"
    assert result["propietario"] == "Pedro"


def test_get_all_timelines_empty(store: ControlStore) -> None:
    """get_all_timelines devuelve dict vacio si no hay registros."""
    assert store.get_all_timelines() == {}


def test_get_all_timelines_multiple(store: ControlStore) -> None:
    """get_all_timelines devuelve todos los hallazgos registrados."""
    store.set_timeline("SEC-A", "2026-07-01", "Ana")
    store.set_timeline("SEC-B", None, "Pedro")
    result = store.get_all_timelines()
    assert len(result) == 2
    assert result["SEC-A"]["fecha_limite"] == "2026-07-01"
    assert result["SEC-B"]["fecha_limite"] is None


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


def test_close_does_not_raise(tmp_path: pytest.TempPathFactory) -> None:
    """close() no lanza excepcion."""
    db = str(tmp_path / "close_test.db")
    s = ControlStore(db_path=db)
    s.close()  # no exception
