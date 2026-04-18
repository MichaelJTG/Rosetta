"""Cargador de corpus normativo a ChromaDB.

Admite marcos en PDF, Markdown o texto plano. Segmenta por control
(no por tamaño fijo) para preservar el contexto semántico del artículo.
"""

from __future__ import annotations

from pathlib import Path

from rosetta.core.models import MarcoNormativo


class CorpusLoader:
    """Pipeline de ingesta de corpus normativo al RAG."""

    def cargar(self, marco: MarcoNormativo, ruta: Path) -> int:
        """Carga los documentos de un marco al vectorstore.

        Args:
            marco: Marco normativo a cargar.
            ruta: Carpeta con PDFs o MDs del marco.

        Returns:
            Número de fragmentos ingestados.
        """
        # TODO [MVP-1]:
        #   1. Detectar extensión (.pdf, .md, .txt).
        #   2. Extraer texto (pypdf para PDF).
        #   3. Segmentar por control/artículo (regex sobre "A.X.Y" o "Artículo N").
        #   4. Generar embeddings y upsert.
        raise NotImplementedError(
            "CorpusLoader pendiente. Ver docs/ROADMAP.md#mvp-1"
        )
