"""Modo B — Ingesta de PDF de auditor humano.

Extrae hallazgos de un informe de auditoría en PDF y los convierte en
DatosRedTeam mediante un pipeline de dos fases:

  Fase 1 — Extracción de texto: pdfplumber (MIT) extrae el texto de cada
    página. Si el texto está vacío (PDF escaneado), se intenta renderizar
    la página como imagen con pypdfium2 (Apache 2.0, incluido con weasyprint)
    para enviarla al LLM con visión.

  Fase 2 — Extracción de hallazgos con LLM: Claude claude-sonnet-4-6 recibe el
    texto/imagen de cada página con un prompt especializado en auditoría de
    seguridad. Responde con tool-use forzado usando el schema
    ``extraer_hallazgos`` → lista de DatosRedTeam normalizados.

Licencias de las herramientas usadas:
  - pdfplumber: MIT
  - pypdfium2: Apache 2.0 (bindings para PDFium de Google)
  - pdf2image: MIT (requiere Poppler del sistema)
  NO se usa PyMuPDF (AGPL) — ver CLAUDE.md §7.
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import pdfplumber
import structlog

from rosetta.core.models import DatosRedTeam, FuenteRedTeam, Severidad

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """Eres un experto en auditoría de seguridad y cumplimiento normativo.
Se te proporciona el contenido de una página de un informe de auditoría de seguridad.
Tu tarea es extraer TODOS los hallazgos de seguridad presentes en esa página.

Para cada hallazgo encontrado, debes identificar:
- El activo afectado (sistema, URL, IP, servicio, componente de software, etc.)
- La evidencia del hallazgo (CVE, captura, log, referencia)
- El vector de ataque o tipo de vulnerabilidad
- La dificultad de explotación estimada (informativa/baja/media/alta/critica)
- El CVE relacionado si se menciona

Si la página no contiene hallazgos de seguridad (es portada, índice, glosario, etc.),
devuelve una lista vacía.

Extrae TODOS los hallazgos visibles — no omitas ninguno aunque sea menor."""

_TOOL_SCHEMA: dict[str, Any] = {
    "name": "extraer_hallazgos",
    "description": (
        "Registra los hallazgos de seguridad encontrados en la página del informe de auditoría."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "hallazgos": {
                "type": "array",
                "description": "Lista de hallazgos extraídos (vacía si la página no tiene hallazgos).",
                "items": {
                    "type": "object",
                    "properties": {
                        "activo_detectado": {
                            "type": "string",
                            "description": "Identificador del activo afectado: URL, IP, servicio, componente.",
                        },
                        "evidencia": {
                            "type": "string",
                            "description": "Referencia o descripción de la evidencia del hallazgo.",
                        },
                        "vector_ataque": {
                            "type": "string",
                            "description": "Tipo de vulnerabilidad o vector de ataque detectado.",
                        },
                        "dificultad_explotacion": {
                            "type": "string",
                            "enum": ["informativa", "baja", "media", "alta", "critica"],
                            "description": "Severidad/dificultad de explotación.",
                        },
                        "cve_relacionado": {
                            "type": "string",
                            "description": "CVE relacionado (ej. CVE-2023-1234). null si no se menciona.",
                        },
                    },
                    "required": [
                        "activo_detectado",
                        "evidencia",
                        "vector_ataque",
                        "dificultad_explotacion",
                    ],
                },
            }
        },
        "required": ["hallazgos"],
    },
}

# DPI para renderizar páginas PDF a imagen (balance calidad/velocidad)
_RENDER_DPI = 150


class PdfIngestionResult:
    """Resultado de la ingesta de un PDF de auditor.

    Atributos:
        hallazgos: Lista de DatosRedTeam extraídos del PDF.
        paginas_procesadas: Número de páginas procesadas.
        paginas_con_hallazgos: Páginas de las que se extrajeron hallazgos.
        modo_extraccion: 'texto' si pdfplumber extrajo texto; 'imagen' si se usó visión LLM.
    """

    __slots__ = ("hallazgos", "paginas_procesadas", "paginas_con_hallazgos", "modo_extraccion")

    def __init__(
        self,
        hallazgos: list[DatosRedTeam],
        paginas_procesadas: int,
        paginas_con_hallazgos: int,
        modo_extraccion: str,
    ) -> None:
        self.hallazgos = hallazgos
        self.paginas_procesadas = paginas_procesadas
        self.paginas_con_hallazgos = paginas_con_hallazgos
        self.modo_extraccion = modo_extraccion


class PdfAuditorIngester:
    """Extrae hallazgos de un PDF de informe de auditoría humano.

    Combina pdfplumber (texto) + pypdfium2 (visión) + LLM Claude para
    convertir páginas de un informe en DatosRedTeam normalizados.

    Args:
        llm_client: Cliente LLM con método `completar(system, messages, tools)`.
            Si None, solo se extrae el texto (sin análisis LLM).
        max_paginas: Máximo de páginas a procesar. None = todas.
        min_texto_chars: Mínimo de caracteres para considerar que una página
            tiene texto extraíble. Por debajo del umbral se intenta renderizar
            como imagen.
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        max_paginas: int | None = None,
        min_texto_chars: int = 50,
    ) -> None:
        self.llm_client = llm_client
        self.max_paginas = max_paginas
        self.min_texto_chars = min_texto_chars

    async def ingestar(self, pdf_path: Path | str) -> PdfIngestionResult:
        """Procesa un PDF y extrae todos los hallazgos de seguridad.

        Args:
            pdf_path: Ruta al PDF de informe de auditoría.

        Returns:
            PdfIngestionResult con la lista de DatosRedTeam extraídos.

        Raises:
            FileNotFoundError: Si el PDF no existe.
            ValueError: Si el archivo no es un PDF válido.
        """
        ruta = Path(pdf_path)
        if not ruta.exists():
            raise FileNotFoundError(f"PDF no encontrado: {ruta}")

        logger.info("pdf_ingestion_inicio", pdf=ruta.name)

        paginas_texto = self._extraer_texto_por_pagina(ruta)
        modo = "texto"
        todos_los_hallazgos: list[DatosRedTeam] = []
        paginas_con_hallazgos = 0

        limite = self.max_paginas if self.max_paginas else len(paginas_texto)
        paginas_a_procesar = paginas_texto[:limite]

        for n_pagina, texto in enumerate(paginas_a_procesar, 1):
            tiene_texto = len(texto.strip()) >= self.min_texto_chars

            if not tiene_texto:
                imagen_b64 = self._renderizar_pagina_b64(ruta, n_pagina - 1)
                if imagen_b64:
                    modo = "imagen"
                    hallazgos_pagina = await self._extraer_con_vision(
                        imagen_b64, n_pagina, ruta.name
                    )
                else:
                    logger.warning(
                        "pagina_sin_texto_ni_imagen",
                        pagina=n_pagina,
                        pdf=ruta.name,
                    )
                    continue
            else:
                hallazgos_pagina = await self._extraer_con_texto(texto, n_pagina, ruta.name)

            if hallazgos_pagina:
                paginas_con_hallazgos += 1
                todos_los_hallazgos.extend(hallazgos_pagina)

            logger.info(
                "pagina_procesada",
                pagina=n_pagina,
                hallazgos=len(hallazgos_pagina),
                pdf=ruta.name,
            )

        logger.info(
            "pdf_ingestion_completa",
            pdf=ruta.name,
            total_hallazgos=len(todos_los_hallazgos),
            paginas_procesadas=len(paginas_a_procesar),
            paginas_con_hallazgos=paginas_con_hallazgos,
            modo=modo,
        )

        return PdfIngestionResult(
            hallazgos=todos_los_hallazgos,
            paginas_procesadas=len(paginas_a_procesar),
            paginas_con_hallazgos=paginas_con_hallazgos,
            modo_extraccion=modo,
        )

    # ------------------------------------------------------------------
    # Extracción de texto
    # ------------------------------------------------------------------

    def _extraer_texto_por_pagina(self, ruta: Path) -> list[str]:
        """Extrae el texto de cada página del PDF usando pdfplumber."""
        paginas: list[str] = []
        try:
            with pdfplumber.open(str(ruta)) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text() or ""
                    paginas.append(texto)
        except Exception as exc:
            raise ValueError(f"PDF inválido o no legible: {exc}") from exc
        return paginas

    # ------------------------------------------------------------------
    # Renderizado a imagen (pypdfium2, sin Poppler)
    # ------------------------------------------------------------------

    def _renderizar_pagina_b64(self, ruta: Path, idx: int) -> str | None:
        """Renderiza una página del PDF a PNG base64 usando pypdfium2.

        Args:
            ruta: Ruta al PDF.
            idx: Índice de página base-0.

        Returns:
            Imagen en base64 (PNG) o None si falla.
        """
        try:
            import pypdfium2 as pdfium

            doc = pdfium.PdfDocument(str(ruta))
            pagina = doc[idx]
            escala = _RENDER_DPI / 72  # 72 DPI es la resolución base de PDF
            bitmap = pagina.render(scale=escala, rotation=0)
            pil_img = bitmap.to_pil()
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            doc.close()
            return base64.b64encode(img_bytes).decode("ascii")
        except Exception as exc:
            logger.warning("renderizado_pagina_fallido", pagina=idx, error=str(exc))
            return None

    # ------------------------------------------------------------------
    # Extracción via LLM — texto
    # ------------------------------------------------------------------

    async def _extraer_con_texto(
        self, texto: str, n_pagina: int, nombre_pdf: str
    ) -> list[DatosRedTeam]:
        """Envía texto de página al LLM y extrae hallazgos."""
        if self.llm_client is None:
            return []

        contenido_usuario = (
            f"Página {n_pagina} del informe '{nombre_pdf}':\n\n"
            f"---\n{texto[:6000]}\n---\n\n"
            "Extrae todos los hallazgos de seguridad presentes."
        )
        return await self._llamar_llm_tool(contenido_usuario, n_pagina, nombre_pdf)

    # ------------------------------------------------------------------
    # Extracción via LLM — visión (imagen base64)
    # ------------------------------------------------------------------

    async def _extraer_con_vision(
        self, imagen_b64: str, n_pagina: int, nombre_pdf: str
    ) -> list[DatosRedTeam]:
        """Envía imagen de página al LLM con visión y extrae hallazgos."""
        if self.llm_client is None:
            return []

        mensaje_vision: list[dict[str, Any]] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": imagen_b64,
                },
            },
            {
                "type": "text",
                "text": (
                    f"Esta es la página {n_pagina} del informe '{nombre_pdf}'. "
                    "Extrae todos los hallazgos de seguridad visibles en la imagen."
                ),
            },
        ]

        from rosetta.llm.base import Message  # noqa: PLC0415

        try:
            result = await self.llm_client.completar(
                system=_SYSTEM_PROMPT,
                messages=[Message(role="user", content=mensaje_vision)],  # type: ignore[arg-type]
                tools=[_build_tool()],
            )
        except Exception as exc:
            logger.warning(
                "llm_vision_error",
                pagina=n_pagina,
                pdf=nombre_pdf,
                error=str(exc),
            )
            return []

        return _parse_tool_result(result, n_pagina, nombre_pdf)

    async def _llamar_llm_tool(
        self, contenido: str, n_pagina: int, nombre_pdf: str
    ) -> list[DatosRedTeam]:
        """Llama al LLM con tool-use forzado para extraer hallazgos del texto."""
        from rosetta.llm.base import Message  # noqa: PLC0415

        try:
            result = await self.llm_client.completar(  # type: ignore[union-attr]
                system=_SYSTEM_PROMPT,
                messages=[Message(role="user", content=contenido)],
                tools=[_build_tool()],
            )
        except Exception as exc:
            logger.warning(
                "llm_texto_error",
                pagina=n_pagina,
                pdf=nombre_pdf,
                error=str(exc),
            )
            return []

        return _parse_tool_result(result, n_pagina, nombre_pdf)


# ------------------------------------------------------------------
# Helpers privados
# ------------------------------------------------------------------


class _ToolSchema:
    """Schema compatible con LLMClient.completar()."""

    def model_dump(self) -> dict[str, Any]:
        return dict(_TOOL_SCHEMA["input_schema"])


class _Tool:
    """Tool object compatible con LLMClient.completar()."""

    name: str = _TOOL_SCHEMA["name"]
    description: str = _TOOL_SCHEMA["description"]
    input_schema = _ToolSchema()


def _build_tool() -> _Tool:
    return _Tool()


def _parse_tool_result(result: Any, n_pagina: int, nombre_pdf: str) -> list[DatosRedTeam]:
    """Parsea el resultado del tool-use del LLM en DatosRedTeam."""
    hallazgos: list[DatosRedTeam] = []

    if not result.tool_calls:
        return hallazgos

    for call in result.tool_calls:
        if call.tool_name != "extraer_hallazgos":
            continue

        raw_hallazgos = call.tool_input.get("hallazgos", [])
        if not isinstance(raw_hallazgos, list):
            continue

        for raw in raw_hallazgos:
            if not isinstance(raw, dict):
                continue
            try:
                sev_raw = raw.get("dificultad_explotacion", "media")
                try:
                    severidad = Severidad(sev_raw)
                except ValueError:
                    severidad = Severidad.MEDIA

                hallazgo = DatosRedTeam(
                    origen=FuenteRedTeam.MANUAL,
                    activo_detectado=str(raw.get("activo_detectado", "desconocido"))[:200],
                    evidencia=str(raw.get("evidencia", f"PDF {nombre_pdf} p.{n_pagina}"))[:500],
                    vector_ataque=str(raw.get("vector_ataque", "no especificado"))[:300],
                    dificultad_explotacion=severidad,
                    cve_relacionado=raw.get("cve_relacionado") or None,
                    metadatos={
                        "fuente_pdf": nombre_pdf,
                        "pagina": n_pagina,
                        "modo_extraccion": "llm_tool_use",
                    },
                )
                hallazgos.append(hallazgo)
            except Exception as exc:
                logger.warning(
                    "hallazgo_parse_error",
                    pagina=n_pagina,
                    pdf=nombre_pdf,
                    raw=json.dumps(raw)[:200],
                    error=str(exc),
                )

    return hallazgos
