"""Almacén persistente de hallazgos de sesión — SQLite.

Reemplaza la lista en memoria de ``app.state.session_findings`` con un
backend SQLite que sobrevive a reinicios del servidor. La interfaz
implementa ``MutableSequence[HallazgoMaestro]`` para que el resto del
código de la API no requiera cambios.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator, MutableSequence
from pathlib import Path
from typing import Any, overload

import structlog

from rosetta.core.models import HallazgoMaestro

logger = structlog.get_logger(__name__)


class SessionStore(MutableSequence):  # type: ignore[type-arg]
    """Lista persistente de HallazgoMaestro respaldada por SQLite.

    Soporta append, slicing y len tal como la lista en memoria original.
    No soporta eliminación ni asignación posicional (append-only).

    Args:
        db_path: Ruta al fichero SQLite. Por defecto ``.rosetta_sessions.db``
                 en el directorio de trabajo.
    """

    def __init__(self, db_path: str = ".rosetta_sessions.db") -> None:
        self._path = Path(db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._init_schema()
        logger.info("session_store_iniciado", db_path=str(self._path))

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hallazgos (
                    id_hallazgo TEXT PRIMARY KEY,
                    timestamp   TEXT NOT NULL,
                    datos_json  TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # MutableSequence interface
    # ------------------------------------------------------------------

    def insert(self, _index: int, value: HallazgoMaestro) -> None:
        """Append-only: el índice se ignora, el hallazgo se añade al final."""
        self._write(value)

    def append(self, value: object) -> None:
        """Persiste un HallazgoMaestro en SQLite."""
        if not isinstance(value, HallazgoMaestro):
            raise TypeError(f"Se esperaba HallazgoMaestro, se recibió {type(value)}")
        self._write(value)

    def __len__(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM hallazgos").fetchone()
        return int(row[0]) if row else 0

    @overload
    def __getitem__(self, key: int) -> HallazgoMaestro: ...

    @overload
    def __getitem__(self, key: slice) -> list[HallazgoMaestro]: ...

    def __getitem__(self, key: int | slice) -> HallazgoMaestro | list[HallazgoMaestro]:
        if isinstance(key, int):
            n = len(self)
            idx = key if key >= 0 else n + key
            if idx < 0 or idx >= n:
                raise IndexError("session store index out of range")
            rows = self._conn.execute(
                "SELECT datos_json FROM hallazgos ORDER BY timestamp ASC LIMIT 1 OFFSET ?",
                (idx,),
            ).fetchall()
            if not rows:
                raise IndexError("session store index out of range")
            return HallazgoMaestro.model_validate_json(rows[0][0])

        if isinstance(key, slice):
            n = len(self)
            start, stop, step = key.indices(n)
            limit = stop - start
            if limit <= 0:
                return []
            rows = self._conn.execute(
                "SELECT datos_json FROM hallazgos ORDER BY timestamp ASC LIMIT ? OFFSET ?",
                (limit, start),
            ).fetchall()
            result = [HallazgoMaestro.model_validate_json(r[0]) for r in rows]
            if step and step != 1:
                result = result[::step]
            return result

        raise TypeError(f"Índice inválido: {type(key)}")

    def __setitem__(self, key: Any, value: Any) -> None:
        raise NotImplementedError("SessionStore es append-only")

    def __delitem__(self, key: Any) -> None:
        raise NotImplementedError("SessionStore es append-only")

    def __iter__(self) -> Iterator[HallazgoMaestro]:
        rows = self._conn.execute(
            "SELECT datos_json FROM hallazgos ORDER BY timestamp ASC"
        ).fetchall()
        for (json_str,) in rows:
            yield HallazgoMaestro.model_validate_json(json_str)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write(self, value: HallazgoMaestro) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO hallazgos (id_hallazgo, timestamp, datos_json) "
                "VALUES (?, ?, ?)",
                (value.id_hallazgo, value.timestamp.isoformat(), value.model_dump_json()),
            )
            self._conn.commit()

    def close(self) -> None:
        """Cierra la conexión SQLite."""
        self._conn.close()
        logger.info("session_store_cerrado", db_path=str(self._path))
