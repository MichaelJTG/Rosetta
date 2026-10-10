"""Índice control → marco normativo construido desde el corpus (RF-19).

El Traductor devuelve los controles incumplidos como identificadores sueltos
(``A.8.12``, ``op.ext.4``, ``Req.6.4``) y una lista de marcos aplicables que el
LLM no siempre completa. Para agregar por marco hay que saber a qué marco
pertenece cada control; la fuente de verdad es el propio corpus indexado.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

import structlog

from rosetta.adapters.compliance.loader import CorpusLoader
from rosetta.core.models import MarcoNormativo

logger = structlog.get_logger(__name__)

# Carpeta de corpus/ de cada marco con corpus propio (ISO 27002 comparte el Anexo A).
CARPETAS_CORPUS: dict[str, str] = {
    "iso_27001_2022": "iso27001",
    "ens_2022": "ens",
    "nis2": "nis2",
    "dora": "dora",
    "rgpd": "rgpd",
    "nist_csf_2": "nist_csf_2",
    "pci_dss_4": "pci_dss_4",
}


def _normalizar(control_id: str) -> str:
    return control_id.strip().lower()


@lru_cache(maxsize=1)
def indice_controles() -> dict[str, frozenset[MarcoNormativo]]:
    """Mapa control (normalizado) → marcos en cuyo corpus aparece.

    El corpus se lee de ``ROSETTA_CORPUS_DIR`` (por defecto ``corpus`` relativo
    al directorio de trabajo, que es ``/app`` en la imagen Docker).
    """
    base = Path(os.getenv("ROSETTA_CORPUS_DIR", "corpus"))
    loader = CorpusLoader()
    indice: dict[str, set[MarcoNormativo]] = {}
    for valor, carpeta in CARPETAS_CORPUS.items():
        ruta = base / carpeta
        if not ruta.is_dir():
            logger.warning("indice_controles_sin_corpus", marco=valor, ruta=str(ruta))
            continue
        for fragmento in loader.cargar(MarcoNormativo(valor), ruta):
            indice.setdefault(_normalizar(fragmento.control_id), set()).add(fragmento.marco)
    return {control: frozenset(marcos) for control, marcos in indice.items()}


def marcos_de_control(
    control_id: str, declarados: Sequence[MarcoNormativo]
) -> list[MarcoNormativo]:
    """Marcos a los que pertenece ``control_id``.

    - Si el control está en el corpus: los marcos declarados que lo contienen o,
      si ninguno lo contiene, todos los marcos del corpus donde aparece.
    - Si no está en el corpus: el marco declarado solo cuando hay uno; con varios
      no se puede saber y no se asigna a ninguno.
    """
    en_corpus = indice_controles().get(_normalizar(control_id), frozenset())
    if en_corpus:
        preferidos = [m for m in declarados if m in en_corpus]
        return preferidos or sorted(en_corpus, key=lambda m: m.value)
    return list(declarados) if len(declarados) == 1 else []
