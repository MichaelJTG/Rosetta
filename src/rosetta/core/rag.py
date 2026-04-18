"""RAG sobre el corpus normativo.

Capa de recuperación semántica para que el Traductor Simbiótico tenga
contexto fundamentado (grounded) al razonar sobre una norma concreta.

Usa ChromaDB como vectorstore local por defecto. En despliegues mayores
se puede sustituir por Pinecone, Weaviate o Qdrant con la misma interfaz.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from rosetta.core.models import MarcoNormativo

logger = structlog.get_logger(__name__)


class NormativaRAG:
    """Recuperador semántico sobre el corpus normativo multi-marco.

    Cada fragmento indexado lleva el marco como metadato (framework_id),
    lo que permite filtrar por marcos activos en cada auditoría.
    """

    def __init__(
        self,
        chromadb_path: str | Path,
        collection_name: str = "rosetta_normativa",
    ) -> None:
        self.chromadb_path = Path(chromadb_path)
        self.collection_name = collection_name
        logger.info(
            "rag_initialized",
            path=str(self.chromadb_path),
            collection=collection_name,
        )
        # TODO [MVP-1]: Inicializar cliente ChromaDB persistente.

    def ingestar_corpus(
        self,
        marco: MarcoNormativo,
        ruta_corpus: str | Path,
    ) -> int:
        """Ingesta el corpus de un marco normativo al vectorstore.

        Args:
            marco: Marco normativo (ISO 27001, ENS, etc.).
            ruta_corpus: Carpeta con los PDFs/MD de la norma.

        Returns:
            Número de fragmentos indexados.
        """
        # TODO [MVP-1]:
        #   1. Parsear PDFs con pypdf o markdown con markdown-it-py.
        #   2. Segmentar por control/artículo (no por tamaño fijo).
        #   3. Enriquecer metadatos: marco, control_id, sección.
        #   4. Embedding con sentence-transformers (all-MiniLM o e5).
        #   5. Upsert en ChromaDB con ids estables (marco:control_id).
        raise NotImplementedError(
            "Ingesta de corpus pendiente. Ver docs/ROADMAP.md#mvp-1"
        )

    def recuperar(
        self,
        query: str,
        marcos: list[MarcoNormativo],
        top_k: int = 5,
    ) -> list[dict[str, str]]:
        """Recupera los k fragmentos más relevantes para la consulta.

        Args:
            query: Consulta semántica (hallazgo técnico reformulado).
            marcos: Marcos a consultar (filtro por metadato).
            top_k: Número de fragmentos a recuperar.

        Returns:
            Lista de dicts con keys: control_id, marco, texto, score.
        """
        # TODO [MVP-1]: Query a ChromaDB con where filter por marco.
        raise NotImplementedError(
            "Recuperación RAG pendiente. Ver docs/ROADMAP.md#mvp-1"
        )
