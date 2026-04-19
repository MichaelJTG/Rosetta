"""Traductor Simbiótico — núcleo del razonamiento normativo de ROSETTA.

Recibe un hallazgo técnico (DatosRedTeam) y devuelve su traducción normativa
(DatosCompliance) consultando el RAG sobre el corpus normativo elegido.

Este módulo es el componente de mayor valor del producto: donde Vanta
recoge evidencia de señales conocidas, el Traductor razona sobre
hallazgos arbitrarios y los mapea semánticamente a controles normativos
multi-marco con cita textual y acción de mitigación concreta.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog

from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    MarcoNormativo,
    Severidad,
)
from rosetta.llm.base import Message, Tool, ToolInputSchema

if TYPE_CHECKING:
    from rosetta.core.rag import FragmentoRecuperado, NormativaRAG
    from rosetta.llm.base import LLMClient

logger = structlog.get_logger(__name__)


SYSTEM_PROMPT = """Eres el Traductor Simbiótico de ROSETTA, un sistema experto en \
cumplimiento normativo de ciberseguridad. Tu única función es tomar un hallazgo \
técnico y traducirlo a la norma seleccionada de forma rigurosa, auditable y \
trazable.

REGLAS DURAS:
1. NUNCA inventes controles. Solo usa los controles del contexto RAG proporcionado.
2. Cada control citado debe incluir su ID exacto (ej. A.8.24) y el nombre del control.
3. La justificación debe conectar hallazgo técnico ↔ control normativo con \
razonamiento explícito, no vago.
4. La acción de mitigación debe ser TÉCNICA y CONCRETA (regla, configuración, \
comando), no genérica.
5. Si el hallazgo afecta a varios marcos, indícalos todos en marcos_aplicables.
6. Responde SIEMPRE usando la herramienta registrar_traduccion. Nunca respondas \
en texto libre.
"""

# Schema de la tool que fuerza la respuesta a DatosCompliance
_TOOL_TRADUCCION = Tool(
    name="registrar_traduccion",
    description=(
        "Registra la traducción normativa del hallazgo técnico. "
        "Llama a esta herramienta con el resultado de tu análisis."
    ),
    input_schema=ToolInputSchema(
        type="object",
        properties={
            "marcos_aplicables": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de marcos normativos aplicables, ej: ['iso_27001_2022']",
            },
            "controles_incumplidos": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de controles incumplidos, ej: ['A.8.24', 'A.5.15']",
            },
            "cita_normativa": {
                "type": "string",
                "description": "Cita del control con ID y descripción, ej: 'A.8.24 Uso de la criptografía: ...'",
            },
            "justificacion": {
                "type": "string",
                "description": "Razonamiento que conecta el hallazgo técnico con el control incumplido.",
            },
            "impacto_legal": {
                "type": "string",
                "enum": ["informativa", "baja", "media", "alta", "critica"],
                "description": "Severidad del impacto legal del incumplimiento.",
            },
            "accion_mitigacion": {
                "type": "string",
                "description": "Acción técnica concreta para remediar (comando, política, configuración).",
            },
            "evidencia_auditoria": {
                "type": "string",
                "description": "Texto listo para dossier de auditoría externa.",
            },
        },
        required=[
            "marcos_aplicables",
            "controles_incumplidos",
            "cita_normativa",
            "justificacion",
            "impacto_legal",
            "accion_mitigacion",
        ],
    ),
)


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


class TraductorSimbiotico:
    """El cerebro normativo de ROSETTA.

    Atributos:
        llm: Cliente para el LLM (Claude / Ollama / OpenAI).
        rag: Recuperador del corpus normativo.
        marcos_activos: Qué marcos consultar en cada auditoría.
    """

    def __init__(
        self,
        llm: LLMClient,
        rag: NormativaRAG,
        marcos_activos: list[MarcoNormativo],
    ) -> None:
        if not marcos_activos:
            raise ValueError("Debe activarse al menos un marco normativo para el Traductor.")
        self.llm = llm
        self.rag = rag
        self.marcos_activos = marcos_activos
        logger.info(
            "traductor_initialized",
            marcos=[m.value for m in marcos_activos],
        )

    async def traducir(self, hallazgo: DatosRedTeam) -> DatosCompliance:
        """Traduce un hallazgo técnico a su representación normativa.

        Pipeline:
          1. Construir query semántica del hallazgo.
          2. Recuperar top-5 fragmentos normativos de cada marco activo (RAG).
          3. Construir prompt con contexto RAG + hallazgo.
          4. Llamar al LLM con tool-use para forzar schema DatosCompliance.
          5. Parsear y validar la respuesta.

        Args:
            hallazgo: Datos del hallazgo técnico.

        Returns:
            DatosCompliance con controles incumplidos, cita, justificación
            y acción de mitigación.

        Raises:
            ValueError: Si el LLM no devuelve un tool_call válido.
        """
        query = self._construir_query(hallazgo)
        logger.info("traduciendo_hallazgo", activo=hallazgo.activo_detectado, query=query[:80])

        fragmentos = self.rag.recuperar(query, self.marcos_activos, top_k=5)
        contexto_rag = _formatear_contexto_rag(fragmentos)

        prompt_usuario = self._construir_prompt(hallazgo, contexto_rag)

        resultado = await self.llm.completar(
            system=SYSTEM_PROMPT,
            messages=[Message(role="user", content=prompt_usuario)],
            tools=[_TOOL_TRADUCCION],
        )

        if not resultado.tool_calls:
            raise ValueError(
                f"El LLM no invocó la herramienta registrar_traduccion. "
                f"Respuesta: {resultado.content!r}"
            )

        tool_input: dict[str, Any] = resultado.tool_calls[0].tool_input
        return self._parsear_resultado(tool_input)

    def _construir_query(self, hallazgo: DatosRedTeam) -> str:
        """Convierte un hallazgo en consulta semántica para el RAG."""
        return (
            f"{hallazgo.vector_ataque}. "
            f"Activo afectado: {hallazgo.activo_detectado}. "
            f"Evidencia: {hallazgo.evidencia}"
        )

    def _construir_prompt(self, hallazgo: DatosRedTeam, contexto_rag: str) -> str:
        """Construye el mensaje de usuario con el hallazgo y el contexto RAG."""
        hallazgo_json = json.dumps(hallazgo.model_dump(), ensure_ascii=False, indent=2)
        return (
            f"# Hallazgo técnico a traducir\n\n"
            f"```json\n{hallazgo_json}\n```\n\n"
            f"{contexto_rag}\n\n"
            f"Analiza el hallazgo técnico anterior y usa los controles del contexto RAG "
            f"para identificar los incumplimientos normativos. "
            f"Invoca la herramienta registrar_traduccion con tu análisis."
        )

    def _parsear_resultado(self, tool_input: dict[str, Any]) -> DatosCompliance:
        """Convierte el tool_input del LLM en un DatosCompliance validado."""
        marcos_raw: list[str] = tool_input.get("marcos_aplicables", [])
        marcos: list[MarcoNormativo] = []
        for m in marcos_raw:
            try:
                marcos.append(MarcoNormativo(m))
            except ValueError:
                logger.warning("marco_desconocido", valor=m)

        if not marcos:
            marcos = list(self.marcos_activos)

        impacto_raw: str = tool_input.get("impacto_legal", "media")
        try:
            impacto = Severidad(impacto_raw)
        except ValueError:
            impacto = Severidad.MEDIA

        return DatosCompliance(
            marcos_aplicables=marcos,
            controles_incumplidos=tool_input.get("controles_incumplidos", []),
            cita_normativa=tool_input.get("cita_normativa", ""),
            justificacion=tool_input.get("justificacion", ""),
            impacto_legal=impacto,
            accion_mitigacion=tool_input.get("accion_mitigacion", ""),
            evidencia_auditoria=tool_input.get("evidencia_auditoria", ""),
        )
