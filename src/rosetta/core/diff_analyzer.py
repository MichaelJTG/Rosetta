"""Analizador de diffs de Git para detección de incumplimientos normativos — MVP-7.

Parsea un diff unificado (formato unified diff) en hunks por archivo,
convierte cada hunk con líneas añadidas en un DatosRedTeam y usa el LLM
con un prompt especializado para determinar si el cambio introduce
incumplimientos normativos REALES (no todos los cambios los tienen).

Integración:
  DiffParser.parse(diff_text)  →  list[DiffHunk]
  DiffAnalyzer.analizar(...)   →  DiffAnalysisResult
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

from rosetta.core.models import (
    MarcoNormativo,
    Severidad,
)
from rosetta.llm.base import Message, Tool, ToolInputSchema

if TYPE_CHECKING:
    from rosetta.core.rag import FragmentoRecuperado, NormativaRAG
    from rosetta.llm.base import LLMClient

logger = structlog.get_logger(__name__)

# --- Regex para parsear unified diff ---
_FILE_HEADER_RE = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

# Archivos que nunca se analizan (binarios, ficheros de lock)
_ALWAYS_SKIP_NAMES = frozenset(
    {"package-lock.json", "yarn.lock", "poetry.lock", "uv.lock", "Cargo.lock", "go.sum"}
)
_ALWAYS_SKIP_EXTS = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip", ".tar", ".gz", ".whl"}
)

# Orden numérico de severidades para comparación ≥
_SEVERIDAD_ORDER: dict[Severidad, int] = {
    Severidad.INFORMATIVA: 0,
    Severidad.BAJA: 1,
    Severidad.MEDIA: 2,
    Severidad.ALTA: 3,
    Severidad.CRITICA: 4,
}

# System prompt especializado para análisis de diffs de código
_SYSTEM_PROMPT_DIFF = """\
Eres el Analizador de Diff de ROSETTA. Recibes fragmentos de código \
añadidos en un PR de GitHub y debes determinar si introducen \
incumplimientos normativos REALES y CONCRETOS.

REGLAS DURAS:
1. Solo señala incumplimientos si el código AÑADIDO introduce EXPLÍCITAMENTE una \
violación normativa (secret hardcodeado, cifrado ausente donde hay datos sensibles, \
endpoint sin autenticación, inyección SQL, credenciales en código fuente, etc.).
2. NO señales incumplimientos por código neutral: refactorizaciones, comentarios, \
imports, cambios de estilo, tests unitarios, o documentación.
3. Si el cambio NO introduce incumplimientos, invoca la herramienta con \
tiene_violacion=false y controles_incumplidos=[].
4. Solo usa controles del contexto RAG proporcionado. NUNCA inventes IDs de controles.
5. La accion_mitigacion debe ser CONCRETA: qué línea cambiar, qué librería usar, \
qué variable de entorno usar.
6. Responde SIEMPRE usando la herramienta registrar_analisis_diff. Nunca texto libre.
"""

# Tool schema que admite "sin violación" explícito
_TOOL_ANALISIS_DIFF = Tool(
    name="registrar_analisis_diff",
    description=(
        "Registra el análisis de cumplimiento del fragmento de código añadido en el PR. "
        "Usa tiene_violacion=false si el cambio es seguro o normativamente neutro."
    ),
    input_schema=ToolInputSchema(
        type="object",
        properties={
            "tiene_violacion": {
                "type": "boolean",
                "description": (
                    "True si el código introducido viola un control normativo concreto. "
                    "False si el cambio es neutral, un refactor, un comentario o similar."
                ),
            },
            "controles_incumplidos": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de controles incumplidos (lista vacía si tiene_violacion=false).",
            },
            "cita_normativa": {
                "type": "string",
                "description": "Cita del control con ID y descripción. Vacío si no hay violación.",
            },
            "justificacion": {
                "type": "string",
                "description": "Qué línea o patrón específico del diff viola el control y por qué.",
            },
            "impacto_legal": {
                "type": "string",
                "enum": ["informativa", "baja", "media", "alta", "critica"],
                "description": "Severidad del incumplimiento. 'informativa' si tiene_violacion=false.",
            },
            "accion_mitigacion": {
                "type": "string",
                "description": "Cambio concreto a aplicar en el código para remediar. Vacío si no hay violación.",
            },
            "evidencia_auditoria": {
                "type": "string",
                "description": "Texto listo para incluir en el comentario del PR y el dossier.",
            },
        },
        required=[
            "tiene_violacion",
            "controles_incumplidos",
            "cita_normativa",
            "justificacion",
            "impacto_legal",
            "accion_mitigacion",
        ],
    ),
)


# ---------------------------------------------------------------------------
# Modelos de datos del analizador
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiffHunk:
    """Un hunk de un diff unificado con las líneas añadidas."""

    archivo: str
    """Ruta del archivo relativa a la raíz del repositorio."""

    linea_inicio: int
    """Número de línea (en el archivo nuevo) donde empieza el hunk."""

    lineas_anadidas: tuple[str, ...]
    """Líneas añadidas (sin el prefijo '+')."""

    contexto_raw: str
    """Texto raw del hunk completo para dar contexto al LLM."""

    @property
    def tiene_contenido(self) -> bool:
        """True si hay al menos una línea añadida no vacía."""
        return any(line.strip() for line in self.lineas_anadidas)

    @property
    def contenido_anadido(self) -> str:
        """Líneas añadidas unidas en un solo bloque de texto."""
        return "\n".join(self.lineas_anadidas)


@dataclass(frozen=True)
class DiffViolation:
    """Una violación normativa detectada en un hunk del diff."""

    archivo: str
    linea_inicio: int
    lineas_afectadas: tuple[str, ...]
    controles_incumplidos: tuple[str, ...]
    cita_normativa: str
    justificacion: str
    impacto_legal: Severidad
    accion_mitigacion: str
    evidencia_auditoria: str


@dataclass
class DiffAnalysisResult:
    """Resultado del análisis de cumplimiento de un diff completo."""

    violaciones: list[DiffViolation]
    total_hunks_analizados: int
    marcos_usados: list[MarcoNormativo]
    bloquear_si: Severidad

    @property
    def bloquear(self) -> bool:
        """True si alguna violación alcanza o supera el umbral de bloqueo."""
        umbral = _SEVERIDAD_ORDER.get(self.bloquear_si, 3)
        return any(_SEVERIDAD_ORDER.get(v.impacto_legal, 0) >= umbral for v in self.violaciones)


# ---------------------------------------------------------------------------
# Parser de diff unificado
# ---------------------------------------------------------------------------


class DiffParser:
    """Parsea un diff unificado (salida de `git diff`) en DiffHunks analizables."""

    @staticmethod
    def parse(diff_text: str, exclude_paths: list[str] | None = None) -> list[DiffHunk]:
        """Parsea el diff y devuelve hunks con líneas añadidas.

        Args:
            diff_text: Texto del diff en formato unified diff estándar.
            exclude_paths: Patrones glob de rutas a ignorar (ej. ["tests/**", "*.lock"]).

        Returns:
            Lista de DiffHunk filtrados: con contenido real y no excluidos.
        """
        exclude_patterns = list(exclude_paths or [])
        hunks: list[DiffHunk] = []

        current_file: str = ""
        current_start: int = 0
        current_added: list[str] = []
        current_raw_lines: list[str] = []
        in_hunk: bool = False

        for line in diff_text.splitlines():
            # Nueva cabecera de archivo (+++ b/ruta)
            file_match = _FILE_HEADER_RE.match(line)
            if file_match:
                if in_hunk and current_added and current_file:
                    hunk = _make_hunk(current_file, current_start, current_added, current_raw_lines)
                    if _should_include(hunk, exclude_patterns):
                        hunks.append(hunk)
                current_file = file_match.group(1).strip()
                current_added = []
                current_raw_lines = []
                in_hunk = False
                continue

            # Cabecera de hunk (@@ -N,M +P,Q @@)
            hunk_match = _HUNK_HEADER_RE.match(line)
            if hunk_match:
                if in_hunk and current_added and current_file:
                    hunk = _make_hunk(current_file, current_start, current_added, current_raw_lines)
                    if _should_include(hunk, exclude_patterns):
                        hunks.append(hunk)
                current_start = int(hunk_match.group(1))
                current_added = []
                current_raw_lines = [line]
                in_hunk = True
                continue

            if not in_hunk:
                continue

            current_raw_lines.append(line)

            # Líneas añadidas (prefijo '+', pero no la cabecera '+++')
            if line.startswith("+") and not line.startswith("+++"):
                current_added.append(line[1:])  # eliminar el prefijo '+'

        # Guardar el último hunk pendiente
        if in_hunk and current_added and current_file:
            hunk = _make_hunk(current_file, current_start, current_added, current_raw_lines)
            if _should_include(hunk, exclude_patterns):
                hunks.append(hunk)

        return hunks


def _make_hunk(
    archivo: str,
    linea_inicio: int,
    lineas_anadidas: list[str],
    raw_lines: list[str],
) -> DiffHunk:
    return DiffHunk(
        archivo=archivo,
        linea_inicio=linea_inicio,
        lineas_anadidas=tuple(lineas_anadidas),
        contexto_raw="\n".join(raw_lines),
    )


def _should_include(hunk: DiffHunk, exclude_patterns: list[str]) -> bool:
    """True si el hunk tiene contenido real y no está en rutas excluidas."""
    if not hunk.tiene_contenido:
        return False
    # Nombres exactos siempre omitidos (lock files, etc.)
    basename = hunk.archivo.split("/")[-1]
    if basename in _ALWAYS_SKIP_NAMES:
        return False
    # Extensiones binarias
    lower = hunk.archivo.lower()
    if any(lower.endswith(ext) for ext in _ALWAYS_SKIP_EXTS):
        return False
    # Patrones de exclusión del usuario
    return all(not fnmatch.fnmatch(hunk.archivo, pattern) for pattern in exclude_patterns)


def _formatear_contexto_rag(fragmentos: list[FragmentoRecuperado]) -> str:
    """Formatea los fragmentos RAG como contexto legible para el LLM."""
    if not fragmentos:
        return "No se encontraron controles relevantes en el corpus."
    lines = ["## Controles normativos relevantes (contexto RAG)\n"]
    for f in fragmentos:
        lines.append(f"### {f.control_id} — {f.nombre}")
        lines.append(f.texto)
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Analizador principal
# ---------------------------------------------------------------------------


class DiffAnalyzer:
    """Analiza un diff de Git buscando incumplimientos normativos.

    Usa el LLM + RAG para determinar si cada hunk introduce una violación
    real (no falsos positivos). El resultado indica si el PR debe bloquearse.
    """

    MAX_HUNKS: int = 20
    """Máximo de hunks que se analizan por diff (coste LLM acotado)."""

    def __init__(self, llm: LLMClient, rag: NormativaRAG) -> None:
        self.llm = llm
        self.rag = rag

    async def analizar(
        self,
        diff_text: str,
        marcos: list[MarcoNormativo],
        bloquear_si: Severidad = Severidad.ALTA,
        exclude_paths: list[str] | None = None,
    ) -> DiffAnalysisResult:
        """Analiza un diff completo y devuelve violaciones normativas.

        Args:
            diff_text: Texto del diff en formato unified diff.
            marcos: Marcos normativos a usar para el análisis.
            bloquear_si: Severidad mínima para marcar el PR como bloqueado.
            exclude_paths: Patrones glob de rutas a ignorar.

        Returns:
            DiffAnalysisResult con las violaciones detectadas y la decisión de bloqueo.
        """
        hunks = DiffParser.parse(diff_text, exclude_paths)
        hunks = hunks[: self.MAX_HUNKS]

        logger.info(
            "diff_analysis_start",
            total_hunks=len(hunks),
            marcos=[m.value for m in marcos],
        )

        violaciones: list[DiffViolation] = []
        for hunk in hunks:
            violacion = await self._analizar_hunk(hunk, marcos)
            if violacion is not None:
                violaciones.append(violacion)
                logger.info(
                    "diff_violation_found",
                    archivo=violacion.archivo,
                    controles=list(violacion.controles_incumplidos),
                    impacto=violacion.impacto_legal.value,
                )

        return DiffAnalysisResult(
            violaciones=violaciones,
            total_hunks_analizados=len(hunks),
            marcos_usados=marcos,
            bloquear_si=bloquear_si,
        )

    async def _analizar_hunk(
        self, hunk: DiffHunk, marcos: list[MarcoNormativo]
    ) -> DiffViolation | None:
        """Analiza un hunk individual con el LLM. Devuelve None si no hay violación."""
        query = f"código añadido en {hunk.archivo}. " f"Contenido: {hunk.contenido_anadido[:400]}"
        fragmentos = self.rag.recuperar(query, marcos, top_k=4)
        contexto_rag = _formatear_contexto_rag(fragmentos)

        prompt = self._construir_prompt(hunk, contexto_rag)

        resultado = await self.llm.completar(
            system=_SYSTEM_PROMPT_DIFF,
            messages=[Message(role="user", content=prompt)],
            tools=[_TOOL_ANALISIS_DIFF],
        )

        if not resultado.tool_calls:
            logger.warning(
                "diff_analyzer_no_tool_call",
                archivo=hunk.archivo,
                respuesta=resultado.content,
            )
            return None

        tool_input: dict[str, Any] = resultado.tool_calls[0].tool_input
        return self._parsear_resultado(hunk, tool_input)

    def _construir_prompt(self, hunk: DiffHunk, contexto_rag: str) -> str:
        """Construye el prompt de análisis con el hunk y el contexto RAG."""
        return (
            f"# Cambio de código en PR a analizar\n\n"
            f"**Archivo:** `{hunk.archivo}` · **Línea de inicio:** {hunk.linea_inicio}\n\n"
            f"```diff\n{hunk.contexto_raw}\n```\n\n"
            f"{contexto_rag}\n\n"
            f"Analiza si las líneas AÑADIDAS (marcadas con `+`) introducen un incumplimiento "
            f"normativo concreto según los controles del contexto RAG. "
            f"Si el cambio es neutral o seguro, invoca la herramienta con `tiene_violacion=false`."
        )

    def _parsear_resultado(
        self, hunk: DiffHunk, tool_input: dict[str, Any]
    ) -> DiffViolation | None:
        """Convierte el tool_input del LLM en una DiffViolation o None."""
        if not tool_input.get("tiene_violacion", False):
            return None

        controles: list[str] = tool_input.get("controles_incumplidos", [])
        if not controles:
            return None

        impacto_raw: str = tool_input.get("impacto_legal", "media")
        try:
            impacto = Severidad(impacto_raw)
        except ValueError:
            impacto = Severidad.MEDIA

        return DiffViolation(
            archivo=hunk.archivo,
            linea_inicio=hunk.linea_inicio,
            lineas_afectadas=hunk.lineas_anadidas,
            controles_incumplidos=tuple(controles),
            cita_normativa=tool_input.get("cita_normativa", ""),
            justificacion=tool_input.get("justificacion", ""),
            impacto_legal=impacto,
            accion_mitigacion=tool_input.get("accion_mitigacion", ""),
            evidencia_auditoria=tool_input.get("evidencia_auditoria", ""),
        )
