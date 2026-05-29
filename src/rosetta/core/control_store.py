"""Almacén persistente de estados de controles normativos — SQLite.

Guarda el estado de cumplimiento (cumple/parcial/no_cumple/no_aplica),
responsable y comentarios de cada control, indexados por (marco, control_id).
También cachea plantillas de procedimiento generadas por LLM y los datos de
timeline (fecha límite + propietario) de los hallazgos del vuln-roadmap.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


class ControlStore:
    """Store SQLite para estados de controles, plantillas y vuln-timeline.

    Args:
        db_path: Ruta al fichero SQLite. Por defecto ``.rosetta_controls.db``.
    """

    ESTADOS_VALIDOS = {"cumple", "parcial", "no_cumple", "no_aplica"}

    def __init__(self, db_path: str = ".rosetta_controls.db") -> None:
        self._path = Path(db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._init_schema()
        logger.info("control_store_iniciado", db_path=str(self._path))

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS control_estados (
                    marco       TEXT NOT NULL,
                    control_id  TEXT NOT NULL,
                    estado      TEXT NOT NULL DEFAULT 'no_aplica',
                    responsable TEXT NOT NULL DEFAULT '',
                    comentarios TEXT NOT NULL DEFAULT '',
                    updated_at  TEXT NOT NULL,
                    PRIMARY KEY (marco, control_id)
                );
                CREATE TABLE IF NOT EXISTS control_plantillas (
                    marco       TEXT NOT NULL,
                    control_id  TEXT NOT NULL,
                    plantilla   TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    PRIMARY KEY (marco, control_id)
                );
                CREATE TABLE IF NOT EXISTS vuln_timeline (
                    id_hallazgo  TEXT PRIMARY KEY,
                    fecha_limite TEXT,
                    propietario  TEXT NOT NULL DEFAULT '',
                    updated_at   TEXT NOT NULL
                );
                """
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Estado de controles
    # ------------------------------------------------------------------

    def set_estado(
        self,
        marco: str,
        control_id: str,
        estado: str,
        responsable: str = "",
        comentarios: str = "",
    ) -> None:
        """Guarda o actualiza el estado de un control."""
        if estado not in self.ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido: {estado!r}. Válidos: {self.ESTADOS_VALIDOS}")
        ts = datetime.utcnow().isoformat()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO control_estados
                    (marco, control_id, estado, responsable, comentarios, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(marco, control_id) DO UPDATE SET
                    estado      = excluded.estado,
                    responsable = excluded.responsable,
                    comentarios = excluded.comentarios,
                    updated_at  = excluded.updated_at
                """,
                (marco, control_id, estado, responsable, comentarios, ts),
            )
            self._conn.commit()

    def get_estado(self, marco: str, control_id: str) -> dict[str, str]:
        """Devuelve el estado de un control o valores por defecto."""
        row = self._conn.execute(
            "SELECT estado, responsable, comentarios, updated_at "
            "FROM control_estados WHERE marco = ? AND control_id = ?",
            (marco, control_id),
        ).fetchone()
        if row:
            return {
                "estado": row[0],
                "responsable": row[1],
                "comentarios": row[2],
                "updated_at": row[3],
            }
        return {"estado": "no_aplica", "responsable": "", "comentarios": "", "updated_at": ""}

    def get_all_estados(self, marco: str) -> dict[str, dict[str, str]]:
        """Devuelve todos los controles con estado registrado para un marco."""
        rows = self._conn.execute(
            "SELECT control_id, estado, responsable, comentarios, updated_at "
            "FROM control_estados WHERE marco = ?",
            (marco,),
        ).fetchall()
        return {
            r[0]: {
                "estado": r[1],
                "responsable": r[2],
                "comentarios": r[3],
                "updated_at": r[4],
            }
            for r in rows
        }

    # ------------------------------------------------------------------
    # Caché de plantillas de procedimiento
    # ------------------------------------------------------------------

    def get_plantilla(self, marco: str, control_id: str) -> str | None:
        """Devuelve la plantilla cacheada o None si no existe."""
        row = self._conn.execute(
            "SELECT plantilla FROM control_plantillas WHERE marco = ? AND control_id = ?",
            (marco, control_id),
        ).fetchone()
        return str(row[0]) if row else None

    def set_plantilla(self, marco: str, control_id: str, plantilla: str) -> None:
        """Guarda una plantilla generada por LLM en caché."""
        ts = datetime.utcnow().isoformat()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO control_plantillas (marco, control_id, plantilla, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(marco, control_id) DO UPDATE SET
                    plantilla  = excluded.plantilla,
                    created_at = excluded.created_at
                """,
                (marco, control_id, plantilla, ts),
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Vuln roadmap — fecha límite + propietario por hallazgo
    # ------------------------------------------------------------------

    def set_timeline(
        self,
        id_hallazgo: str,
        fecha_limite: str | None,
        propietario: str,
    ) -> None:
        """Guarda la fecha límite de resolución y propietario de un hallazgo."""
        ts = datetime.utcnow().isoformat()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO vuln_timeline (id_hallazgo, fecha_limite, propietario, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id_hallazgo) DO UPDATE SET
                    fecha_limite = excluded.fecha_limite,
                    propietario  = excluded.propietario,
                    updated_at   = excluded.updated_at
                """,
                (id_hallazgo, fecha_limite, propietario, ts),
            )
            self._conn.commit()

    def get_timeline(self, id_hallazgo: str) -> dict[str, str | None]:
        """Devuelve datos de timeline de un hallazgo."""
        row = self._conn.execute(
            "SELECT fecha_limite, propietario FROM vuln_timeline WHERE id_hallazgo = ?",
            (id_hallazgo,),
        ).fetchone()
        if row:
            return {"fecha_limite": row[0], "propietario": row[1]}
        return {"fecha_limite": None, "propietario": ""}

    def get_all_timelines(self) -> dict[str, dict[str, str | None]]:
        """Devuelve todos los timelines registrados."""
        rows = self._conn.execute(
            "SELECT id_hallazgo, fecha_limite, propietario FROM vuln_timeline"
        ).fetchall()
        return {r[0]: {"fecha_limite": r[1], "propietario": r[2]} for r in rows}

    def close(self) -> None:
        """Cierra la conexión SQLite."""
        self._conn.close()
        logger.info("control_store_cerrado", db_path=str(self._path))
