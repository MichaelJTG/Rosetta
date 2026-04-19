"""Grafo de correlación Neo4j.

El grafo une (Activo)-[AFECTADO_POR]->(Hallazgo)-[INCUMPLE]->(Control)
-[PERTENECE_A]->(Marco). Esto permite consultas como:

- ¿Qué controles de ISO 27001 están en riesgo hoy?
- ¿Qué activos tienen hallazgos críticos abiertos?
- ¿Qué procedimientos internos mencionan controles con hallazgos abiertos?
  (base para la capa de procedure-drift — ver vault/06_Procedimientos/)
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Cypher queries
# ---------------------------------------------------------------------------

_MERGE_HALLAZGO = """
MERGE (marco:Marco {nombre: $marco})
MERGE (control:Control {id: $control_id, marco: $marco})
  ON CREATE SET control.nombre = $control_nombre
MERGE (activo:Activo {nombre: $activo})
MERGE (hallazgo:Hallazgo {id: $hallazgo_id})
  ON CREATE SET
    hallazgo.timestamp    = $timestamp,
    hallazgo.severidad    = $severidad,
    hallazgo.origen       = $origen,
    hallazgo.evidencia    = $evidencia,
    hallazgo.justificacion = $justificacion,
    hallazgo.mitigacion   = $mitigacion
MERGE (activo)-[:AFECTADO_POR]->(hallazgo)
MERGE (hallazgo)-[:INCUMPLE]->(control)
MERGE (control)-[:PERTENECE_A]->(marco)
"""

_QUERY_POR_MARCO = """
MATCH (h:Hallazgo)-[:INCUMPLE]->(c:Control)-[:PERTENECE_A]->(m:Marco {nombre: $marco})
OPTIONAL MATCH (a:Activo)-[:AFECTADO_POR]->(h)
RETURN
  h.id          AS hallazgo_id,
  h.severidad   AS severidad,
  h.origen      AS origen,
  h.timestamp   AS timestamp,
  c.id          AS control_id,
  c.nombre      AS control_nombre,
  a.nombre      AS activo
ORDER BY h.timestamp DESC
"""

_QUERY_CONTROLES_TOP = """
MATCH (h:Hallazgo)-[:INCUMPLE]->(c:Control)-[:PERTENECE_A]->(m:Marco {nombre: $marco})
WITH c, count(h) AS total, collect(h.severidad) AS severidades
RETURN c.id AS control_id, c.nombre AS control_nombre, total
ORDER BY total DESC
LIMIT $top_n
"""

_QUERY_POR_ACTIVO = """
MATCH (a:Activo {nombre: $activo})-[:AFECTADO_POR]->(h:Hallazgo)
OPTIONAL MATCH (h)-[:INCUMPLE]->(c:Control)
RETURN
  h.id        AS hallazgo_id,
  h.severidad AS severidad,
  h.timestamp AS timestamp,
  c.id        AS control_id
ORDER BY h.timestamp DESC
"""


class GrafoCorrelacion:
    """Cliente Neo4j para el grafo de correlación de ROSETTA.

    El driver se inyecta por constructor para facilitar mocks en tests.
    En producción se crea con `GrafoCorrelacion.desde_env()`.
    """

    def __init__(self, driver: Any) -> None:
        self._driver = driver
        logger.info("grafo_initialized")

    @classmethod
    def desde_uri(cls, uri: str, user: str, password: str) -> GrafoCorrelacion:
        """Construye el grafo abriendo un driver Neo4j desde credenciales."""
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(uri, auth=(user, password))
        return cls(driver)

    def registrar_hallazgo(
        self,
        hallazgo_id: str,
        activo: str,
        marco: str,
        control_id: str,
        control_nombre: str,
        severidad: str,
        origen: str,
        evidencia: str,
        justificacion: str,
        mitigacion: str,
        timestamp: str,
    ) -> None:
        """Persiste un hallazgo en el grafo via MERGE idempotente.

        Argumentos extraídos de HallazgoMaestro + DatosCompliance para
        evitar importar el modelo aquí (evita dependencia circular).
        """
        with self._driver.session() as session:
            session.run(
                _MERGE_HALLAZGO,
                marco=marco,
                control_id=control_id,
                control_nombre=control_nombre,
                activo=activo,
                hallazgo_id=hallazgo_id,
                timestamp=timestamp,
                severidad=severidad,
                origen=origen,
                evidencia=evidencia,
                justificacion=justificacion,
                mitigacion=mitigacion,
            )
        logger.info("hallazgo_registrado", id=hallazgo_id, control=control_id, marco=marco)

    def hallazgos_por_marco(self, marco: str) -> list[dict[str, Any]]:
        """Devuelve todos los hallazgos registrados bajo un marco normativo."""
        with self._driver.session() as session:
            result = session.run(_QUERY_POR_MARCO, marco=marco)
            return [dict(r) for r in result]

    def controles_mas_incumplidos(self, marco: str, top_n: int = 10) -> list[dict[str, Any]]:
        """Devuelve los top-N controles con más hallazgos asociados."""
        with self._driver.session() as session:
            result = session.run(_QUERY_CONTROLES_TOP, marco=marco, top_n=top_n)
            return [dict(r) for r in result]

    def hallazgos_por_activo(self, activo: str) -> list[dict[str, Any]]:
        """Devuelve todos los hallazgos que afectan a un activo concreto."""
        with self._driver.session() as session:
            result = session.run(_QUERY_POR_ACTIVO, activo=activo)
            return [dict(r) for r in result]

    def exportar_dossier(self, marco: str, titulo: str | None = None) -> str:
        """Genera un dossier de auditoría en Markdown a partir del grafo.

        El dossier incluye:
        - Resumen: controles más incumplidos (top-10)
        - Detalle de cada hallazgo con activo, severidad y acción de mitigación

        Args:
            marco: Valor del MarcoNormativo a consultar (ej. 'iso_27001_2022').
            titulo: Título opcional del dossier.

        Returns:
            Cadena Markdown lista para guardar o imprimir.
        """
        top_controles = self.controles_mas_incumplidos(marco, top_n=10)
        hallazgos = self.hallazgos_por_marco(marco)

        titulo_real = titulo or f"Dossier de auditoría — {marco}"
        lines: list[str] = [
            f"# {titulo_real}",
            "",
            f"> Generado por ROSETTA · Marco: `{marco}` · Hallazgos: {len(hallazgos)}",
            "",
            "---",
            "",
            "## Controles más incumplidos",
            "",
            "| Control | Nombre | Hallazgos |",
            "|---------|--------|-----------|",
        ]
        for c in top_controles:
            lines.append(
                f"| `{c.get('control_id', '')}` | {c.get('control_nombre', '')} | {c.get('total', 0)} |"
            )

        lines += [
            "",
            "---",
            "",
            "## Detalle de hallazgos",
            "",
        ]
        for h in hallazgos:
            lines += [
                f"### {h.get('hallazgo_id', 'Sin ID')}",
                "",
                f"- **Activo**: `{h.get('activo', 'desconocido')}`",
                f"- **Control**: `{h.get('control_id', '')}` — {h.get('control_nombre', '')}",
                f"- **Severidad**: {h.get('severidad', '')}",
                f"- **Origen**: {h.get('origen', '')}",
                f"- **Fecha**: {h.get('timestamp', '')}",
                "",
            ]

        return "\n".join(lines)

    def cerrar(self) -> None:
        """Cierra el driver Neo4j."""
        self._driver.close()
        logger.info("grafo_driver_cerrado")
