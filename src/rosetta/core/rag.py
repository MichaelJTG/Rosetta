"""RAG sobre el corpus normativo.

Capa de recuperación semántica para que el Traductor Simbiótico tenga
contexto fundamentado (grounded) al razonar sobre una norma concreta.

Usa ChromaDB como vectorstore local persistente. Los embeddings se generan
con sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) — modelo
ligero (~117 MB) con soporte para español e inglés, sin necesidad de API key.

En despliegues mayores se puede sustituir por Pinecone, Weaviate o Qdrant
con la misma interfaz pública (ingestar_corpus / recuperar).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
import structlog
from chromadb.utils import embedding_functions

from rosetta.core.models import MarcoNormativo

logger = structlog.get_logger(__name__)

# Modelo de embedding multilingüe ligero (~117 MB, soporta español + inglés)
_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class FragmentoRecuperado:
    """Fragmento normativo devuelto por el RAG.

    Atributos:
        control_id: ID del control, ej. "A.8.24".
        marco: Marco normativo.
        nombre: Nombre corto del control.
        texto: Texto completo del fragmento.
        score: Distancia al embedding de la query (menor = más relevante).
    """

    __slots__ = ("control_id", "marco", "nombre", "texto", "score")

    def __init__(
        self,
        control_id: str,
        marco: str,
        nombre: str,
        texto: str,
        score: float,
    ) -> None:
        self.control_id = control_id
        self.marco = marco
        self.nombre = nombre
        self.texto = texto
        self.score = score

    def __repr__(self) -> str:
        return f"FragmentoRecuperado({self.control_id}, score={self.score:.3f})"


class NormativaRAG:
    """Recuperador semántico sobre el corpus normativo multi-marco.

    Cada fragmento indexado lleva el marco como metadato (framework_id),
    lo que permite filtrar por marcos activos en cada auditoría sin mezclar
    artículos de normas distintas en una misma respuesta.
    """

    def __init__(
        self,
        chromadb_path: str | Path,
        collection_name: str = "rosetta_normativa",
    ) -> None:
        self.chromadb_path = Path(chromadb_path)
        self.collection_name = collection_name
        self.chromadb_path.mkdir(parents=True, exist_ok=True)

        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=_EMBEDDING_MODEL
        )
        self._client = chromadb.PersistentClient(path=str(self.chromadb_path))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "rag_initialized",
            path=str(self.chromadb_path),
            collection=collection_name,
            model=_EMBEDDING_MODEL,
            docs_en_coleccion=self._collection.count(),
        )

    def ingestar_corpus(
        self,
        fragmentos: list[Any],  # list[FragmentoNormativo] — lazy import para evitar ciclo
    ) -> int:
        """Indexa fragmentos normativos en ChromaDB.

        Usa upsert con IDs estables (marco:control_id) para que reindexar
        el corpus sea idempotente — no crea duplicados.

        Args:
            fragmentos: Lista de FragmentoNormativo del CorpusLoader.

        Returns:
            Número de fragmentos indexados.
        """
        if not fragmentos:
            logger.warning("ingestar_corpus_vacio")
            return 0

        ids: list[str] = []
        textos: list[str] = []
        metadatos: list[dict[str, Any]] = []

        for f in fragmentos:
            doc_id = f"{f.marco.value}:{f.control_id}"
            ids.append(doc_id)
            textos.append(f.texto)
            metadatos.append(
                {
                    "framework_id": f.marco.value,
                    "control_id": f.control_id,
                    "nombre": f.nombre,
                    **{k: str(v) for k, v in f.metadatos.items()},
                }
            )

        # Upsert en lotes de 100 para no saturar ChromaDB
        lote = 100
        for i in range(0, len(ids), lote):
            self._collection.upsert(
                ids=ids[i : i + lote],
                documents=textos[i : i + lote],
                metadatas=metadatos[i : i + lote],
            )

        logger.info(
            "corpus_ingestado",
            fragmentos=len(ids),
            coleccion=self.collection_name,
        )
        return len(ids)

    def recuperar(
        self,
        query: str,
        marcos: list[MarcoNormativo],
        top_k: int = 5,
    ) -> list[FragmentoRecuperado]:
        """Recupera los k fragmentos más relevantes para la consulta.

        Filtra por marco normativo para no mezclar controles de ISO con ENS
        en la misma consulta al LLM.

        Args:
            query: Consulta semántica (hallazgo técnico reformulado).
            marcos: Marcos a consultar — se usa como filtro de metadatos.
            top_k: Número de fragmentos a recuperar por marco.

        Returns:
            Lista de FragmentoRecuperado ordenada por relevancia (score asc).
        """
        if self._collection.count() == 0:
            logger.warning("rag_coleccion_vacia", hint="Ejecuta 'rosetta load-corpus' primero.")
            return []

        resultados: list[FragmentoRecuperado] = []

        for marco in marcos:
            where: dict[str, Any] = {"framework_id": marco.value}
            try:
                resp = self._collection.query(
                    query_texts=[query],
                    n_results=min(top_k, self._collection.count()),
                    where=where,
                    include=["documents", "metadatas", "distances"],
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("rag_query_error", marco=marco.value, error=str(exc))
                continue

            raw_docs = resp.get("documents") or [[]]
            raw_metas = resp.get("metadatas") or [[]]
            raw_dists = resp.get("distances") or [[]]
            docs: list[str] = raw_docs[0] if raw_docs else []
            metas: list[dict[str, Any]] = raw_metas[0] if raw_metas else []
            dists: list[float] = raw_dists[0] if raw_dists else []

            for doc, meta, dist in zip(docs, metas, dists, strict=False):
                resultados.append(
                    FragmentoRecuperado(
                        control_id=meta.get("control_id", ""),
                        marco=meta.get("framework_id", marco.value),
                        nombre=meta.get("nombre", ""),
                        texto=doc,
                        score=float(dist),
                    )
                )

        resultados.sort(key=lambda r: r.score)
        logger.info("rag_recuperado", query_len=len(query), resultados=len(resultados))
        return resultados

    def contar(self, marco: MarcoNormativo | None = None) -> int:
        """Devuelve el número de fragmentos indexados, opcionalmente por marco."""
        if marco is None:
            return int(self._collection.count())
        try:
            resp = self._collection.get(where={"framework_id": marco.value})
            ids: list[str] = resp.get("ids") or []
            return len(ids)
        except Exception:  # noqa: BLE001
            return 0
