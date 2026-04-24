"""Tests para SessionStore (core/session_store.py).

Verifica:
- append persiste en SQLite
- len refleja los hallazgos almacenados
- __getitem__ con índice positivo y negativo
- slicing básico
- __iter__ devuelve todos los hallazgos en orden
- insert() es append-only (ignora índice)
- setitem / delitem lanzan NotImplementedError
- close() cierra la conexión
- reinicializar SessionStore sobre el mismo fichero recupera los datos previos
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    FuenteRedTeam,
    HallazgoMaestro,
    MarcoNormativo,
    Severidad,
)
from rosetta.core.session_store import SessionStore


def _make_hallazgo(suffix: str = "01") -> HallazgoMaestro:
    datos_red = DatosRedTeam(
        origen=FuenteRedTeam.MANUAL,
        activo_detectado=f"activo-{suffix}",
        evidencia=f"evidencia-{suffix}",
        vector_ataque="vector",
        dificultad_explotacion=Severidad.MEDIA,
    )
    compliance = DatosCompliance(
        marcos_aplicables=[MarcoNormativo.ISO_27001_2022],
        controles_incumplidos=["A.8.24"],
        cita_normativa="ISO 27001:2022 A.8.24",
        justificacion="test",
        impacto_legal=Severidad.MEDIA,
        accion_mitigacion="test action",
        evidencia_auditoria="test evidence",
    )
    return HallazgoMaestro(
        id_hallazgo=f"SEC-TEST{suffix}",
        red_team_data=datos_red,
        compliance_data=compliance,
        timestamp=datetime(2026, 4, 24, 10, 0, 0, tzinfo=UTC),
    )


@pytest.fixture()
def store() -> SessionStore:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    s = SessionStore(db_path=path)
    yield s
    s.close()
    Path(path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# append y len
# ---------------------------------------------------------------------------


def test_empty_store_has_len_zero(store: SessionStore) -> None:
    assert len(store) == 0


def test_append_increases_len(store: SessionStore) -> None:
    store.append(_make_hallazgo("01"))
    assert len(store) == 1
    store.append(_make_hallazgo("02"))
    assert len(store) == 2


def test_append_wrong_type_raises(store: SessionStore) -> None:
    with pytest.raises(TypeError):
        store.append("not a hallazgo")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# __getitem__
# ---------------------------------------------------------------------------


def test_getitem_positive_index(store: SessionStore) -> None:
    h = _make_hallazgo("01")
    store.append(h)
    retrieved = store[0]
    assert retrieved.id_hallazgo == "SEC-TEST01"


def test_getitem_negative_index(store: SessionStore) -> None:
    store.append(_make_hallazgo("01"))
    store.append(_make_hallazgo("02"))
    assert store[-1].id_hallazgo == "SEC-TEST02"
    assert store[-2].id_hallazgo == "SEC-TEST01"


def test_getitem_out_of_range_raises(store: SessionStore) -> None:
    with pytest.raises(IndexError):
        _ = store[0]


def test_getitem_slice(store: SessionStore) -> None:
    for i in range(5):
        store.append(_make_hallazgo(f"0{i}"))
    sliced = store[1:3]
    assert len(sliced) == 2
    assert sliced[0].id_hallazgo == "SEC-TEST01"
    assert sliced[1].id_hallazgo == "SEC-TEST02"


def test_getitem_empty_slice(store: SessionStore) -> None:
    store.append(_make_hallazgo("01"))
    assert store[5:10] == []


def test_getitem_invalid_type_raises(store: SessionStore) -> None:
    with pytest.raises(TypeError):
        _ = store["bad"]  # type: ignore[index]


# ---------------------------------------------------------------------------
# insert (append-only)
# ---------------------------------------------------------------------------


def test_insert_appends_regardless_of_index(store: SessionStore) -> None:
    h = _make_hallazgo("01")
    store.insert(999, h)
    assert len(store) == 1
    assert store[0].id_hallazgo == "SEC-TEST01"


# ---------------------------------------------------------------------------
# __iter__
# ---------------------------------------------------------------------------


def test_iter_returns_all_in_order(store: SessionStore) -> None:
    ids = ["A1", "A2", "A3"]
    for suffix in ids:
        store.append(_make_hallazgo(suffix))
    retrieved = [h.id_hallazgo for h in store]
    assert retrieved == [f"SEC-TEST{s}" for s in ids]


# ---------------------------------------------------------------------------
# Mutabilidad prohibida
# ---------------------------------------------------------------------------


def test_setitem_raises(store: SessionStore) -> None:
    store.append(_make_hallazgo("01"))
    with pytest.raises(NotImplementedError):
        store[0] = _make_hallazgo("02")  # type: ignore[index]


def test_delitem_raises(store: SessionStore) -> None:
    store.append(_make_hallazgo("01"))
    with pytest.raises(NotImplementedError):
        del store[0]


# ---------------------------------------------------------------------------
# Persistencia entre instancias
# ---------------------------------------------------------------------------


def test_data_survives_reopen() -> None:
    """Los hallazgos persisten al crear una nueva instancia sobre el mismo fichero."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        s1 = SessionStore(db_path=path)
        s1.append(_make_hallazgo("01"))
        s1.close()

        s2 = SessionStore(db_path=path)
        assert len(s2) == 1
        assert s2[0].id_hallazgo == "SEC-TEST01"
        s2.close()
    finally:
        Path(path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# INSERT OR REPLACE (id duplicado)
# ---------------------------------------------------------------------------


def test_duplicate_id_replaces(store: SessionStore) -> None:
    """INSERT OR REPLACE: un hallazgo con el mismo id sobreescribe el anterior."""
    h = _make_hallazgo("DUP")
    store.append(h)
    store.append(h)  # misma clave primaria
    assert len(store) == 1
