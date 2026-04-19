"""Cargador de corpus normativo al RAG.

Soporta:
  - YAML de intuitem/ciso-assistant-community (formato preferido para ISO 27001:2022)
  - PDF con pypdf (fallback para otros marcos)
  - Markdown (para ENS, NIS2, DORA obtenidos de EUR-Lex/BOE en texto)

El YAML de intuitem contiene 93 controles con descripciones propias (no texto
verbatim ISO) y traducciones al español. Es el corpus de desarrollo para MVP-1.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import structlog
import yaml

from rosetta.core.models import MarcoNormativo

logger = structlog.get_logger(__name__)


class FragmentoNormativo:
    """Un fragmento de corpus listo para ingestar al vectorstore.

    Atributos:
        control_id: Identificador del control, ej. "A.5.1" o "art.32".
        texto: Texto que se embedizará (nombre + descripción del control).
        marco: Marco normativo al que pertenece.
        nombre: Nombre corto del control.
        metadatos: Campos extra para filtrado en ChromaDB.
    """

    __slots__ = ("control_id", "texto", "marco", "nombre", "metadatos")

    def __init__(
        self,
        control_id: str,
        texto: str,
        marco: MarcoNormativo,
        nombre: str,
        metadatos: dict[str, Any] | None = None,
    ) -> None:
        self.control_id = control_id
        self.texto = texto
        self.marco = marco
        self.nombre = nombre
        self.metadatos = metadatos or {}


class CorpusLoader:
    """Pipeline de ingesta de corpus normativo al RAG.

    Detecta automáticamente el formato del archivo (.yaml, .pdf, .md)
    y devuelve fragmentos estructurados para que NormativaRAG los indexe.
    """

    def cargar(self, marco: MarcoNormativo, ruta: Path) -> list[FragmentoNormativo]:
        """Carga todos los archivos de una carpeta de corpus.

        Args:
            marco: Marco normativo que se está cargando.
            ruta: Carpeta con los archivos del marco.

        Returns:
            Lista de FragmentoNormativo listos para indexar en ChromaDB.
        """
        ruta = Path(ruta)
        fragmentos: list[FragmentoNormativo] = []

        archivos = sorted(
            f
            for f in ruta.iterdir()
            if f.suffix.lower() in {".yaml", ".yml", ".pdf", ".md", ".txt"}
        )

        if not archivos:
            logger.warning("corpus_vacio", ruta=str(ruta), marco=marco.value)
            return fragmentos

        for archivo in archivos:
            logger.info("cargando_archivo", archivo=archivo.name, marco=marco.value)
            sufijo = archivo.suffix.lower()
            if sufijo in {".yaml", ".yml"}:
                fragmentos.extend(self._cargar_yaml_intuitem(archivo, marco))
            elif sufijo == ".pdf":
                fragmentos.extend(self._cargar_pdf(archivo, marco))
            elif sufijo in {".md", ".txt"}:
                fragmentos.extend(self._cargar_markdown(archivo, marco))

        logger.info(
            "corpus_cargado",
            marco=marco.value,
            total_fragmentos=len(fragmentos),
        )
        return fragmentos

    # ------------------------------------------------------------------
    # Parsers por formato
    # ------------------------------------------------------------------

    def _cargar_yaml_intuitem(
        self, archivo: Path, marco: MarcoNormativo
    ) -> list[FragmentoNormativo]:
        """Parsea el YAML de intuitem/ciso-assistant-community.

        Extrae los 93 controles ISO 27001:2022 con sus descripciones en
        español (translations.es) y construye un fragmento por control.
        """
        with archivo.open(encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)

        controls: list[dict[str, Any]] = data.get("objects", {}).get("reference_controls", [])
        if not controls:
            logger.warning("yaml_sin_controles", archivo=str(archivo))
            return []

        fragmentos: list[FragmentoNormativo] = []
        for ctrl in controls:
            ref_id: str = ctrl.get("ref_id", "")
            if not ref_id:
                continue

            # Preferir traducción española si está disponible
            es = ctrl.get("translations", {}).get("es", {})
            nombre: str = es.get("name") or ctrl.get("name", ref_id)
            descripcion: str = es.get("description") or ctrl.get("description", "")

            # Texto que se embedizará: ID + nombre + descripción
            texto = f"{ref_id} {nombre}. {descripcion}".strip()

            fragmentos.append(
                FragmentoNormativo(
                    control_id=ref_id,
                    texto=texto,
                    marco=marco,
                    nombre=nombre,
                    metadatos={
                        "categoria": ctrl.get("category", ""),
                        "fuente": "intuitem-ciso-assistant",
                    },
                )
            )

        logger.info(
            "yaml_parseado",
            archivo=archivo.name,
            controles=len(fragmentos),
        )
        return fragmentos

    def _cargar_pdf(self, archivo: Path, marco: MarcoNormativo) -> list[FragmentoNormativo]:
        """Extrae controles de un PDF normativo usando pypdf.

        Usa heurística de regex para segmentar por ID de control
        (patrones: "A.X.Y", "Artículo N", "mp.X.Y" para ENS).
        """
        import pypdf  # lazy import — no siempre se necesita

        fragmentos: list[FragmentoNormativo] = []
        texto_completo = ""

        with archivo.open("rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                texto_completo += (page.extract_text() or "") + "\n"

        fragmentos.extend(self._segmentar_por_control(texto_completo, marco, str(archivo.name)))
        return fragmentos

    def _cargar_markdown(self, archivo: Path, marco: MarcoNormativo) -> list[FragmentoNormativo]:
        """Segmenta un Markdown normativo por controles/artículos."""
        texto = archivo.read_text(encoding="utf-8")
        return self._segmentar_por_control(texto, marco, str(archivo.name))

    def _segmentar_por_control(
        self, texto: str, marco: MarcoNormativo, fuente: str
    ) -> list[FragmentoNormativo]:
        """Segmenta texto en fragmentos por ID de control.

        Patrones reconocidos:
          ISO 27001/27002: A.5.1, A.8.24 …
          ENS: mp.s.1, op.acc.1 …
          NIS2/DORA: Artículo 21, Article 9 …
        """
        # Patrón compuesto: ISO Annex A, ENS, artículos numerados
        patron = re.compile(
            r"(?:^|\n)"
            r"((?:A\.\d+(?:\.\d+)*)|(?:[a-z]{2,4}\.[a-z]+\.\d+)|(?:(?:Art[íi]culo|Article)\s+\d+))"
            r"[.\s]+"
            r"(.+?)(?=(?:\n(?:A\.\d+(?:\.\d+)*)|(?:[a-z]{2,4}\.[a-z]+\.\d+)|"
            r"(?:Art[íi]culo|Article)\s+\d+)|\Z)",
            re.DOTALL | re.IGNORECASE,
        )

        fragmentos: list[FragmentoNormativo] = []
        for match in patron.finditer(texto):
            control_id = match.group(1).strip()
            contenido = match.group(2).strip()
            if len(contenido) < 20:  # demasiado corto para ser útil
                continue
            # Primera línea del contenido como nombre
            nombre = contenido.split("\n")[0][:120]
            fragmentos.append(
                FragmentoNormativo(
                    control_id=control_id,
                    texto=f"{control_id} {contenido[:800]}",
                    marco=marco,
                    nombre=nombre,
                    metadatos={"fuente": fuente},
                )
            )

        if not fragmentos:
            logger.warning(
                "sin_controles_detectados",
                fuente=fuente,
                marco=marco.value,
                hint="Verifica el formato del corpus o añade un parser específico.",
            )

        return fragmentos
