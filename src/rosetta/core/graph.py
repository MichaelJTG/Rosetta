"""Grafo de correlación Neo4j.

El grafo une (Activo)-[AFECTADO_POR]->(Hallazgo)-[INCUMPLE]->(Control)
-[PERTENECE_A]->(Marco). Esto permite consultas como:

- ¿Qué controles de ISO 27001 están en riesgo hoy?
- ¿Qué activos son Shadow IT y tienen hallazgos críticos?
- ¿Qué procedimientos internos mencionan controles con hallazgos abiertos?
  (para la capa de procedure-drift que sugirió Carlos Gómez Pintado)
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class GrafoCorrelacion:
    """Cliente Neo4j para el grafo de correlación de ROSETTA."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.uri = uri
        self.user = user
        self._password = password
        logger.info("grafo_initialized", uri=uri)
        # TODO [MVP-2]: Inicializar driver Neo4j.

    def registrar_hallazgo(self, *args: object, **kwargs: object) -> None:
        """Persiste un Hallazgo Maestro en el grafo."""
        # TODO [MVP-2]: Cypher para MERGE de nodos y relaciones.
        raise NotImplementedError(
            "Registro en grafo pendiente. Ver docs/ROADMAP.md#mvp-2"
        )
