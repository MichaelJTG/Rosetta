"""Validador — agente crítico que valida las traducciones de los especialistas.

Actúa como second-opinion sobre cada Traduccion generada, detectando
alucinaciones, controles inexistentes o mapeos incorrectos.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog

from rosetta.core.models import DatosRedTeam, ModelProfile, Traduccion, ValidacionResult
from rosetta.llm.base import Message, Tool, ToolInputSchema

if TYPE_CHECKING:
    from rosetta.llm.base import LLMClient

logger = structlog.get_logger(__name__)

_TOOL_VALIDACION = Tool(
    name="registrar_validacion",
    description=(
        "Registra el resultado de tu validación crítica de la traducción normativa. "
        "Llama a esta herramienta siempre con tu veredicto final."
    ),
    input_schema=ToolInputSchema(
        type="object",
        properties={
            "valida": {
                "type": "boolean",
                "description": "True si la traducción es correcta y auditable.",
            },
            "problemas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de problemas detectados (vacía si es válida).",
            },
            "confianza": {
                "type": "number",
                "description": "Nivel de confianza en el veredicto (0.0–1.0).",
            },
            "razonamiento": {
                "type": "string",
                "description": "Razonamiento detallado del veredicto.",
            },
        },
        required=["valida", "problemas", "confianza", "razonamiento"],
    ),
)

_SYSTEM_PROMPT = (
    "Eres el Validador Crítico de ROSETTA. Tu función es revisar traducciones "
    "normativas generadas por otros agentes y detectar:\n"
    "1. Controles inventados que no existen en el marco normativo real.\n"
    "2. Mapeos incorrectos donde el control no se aplica al hallazgo.\n"
    "3. Justificaciones circulares o vacías sin razonamiento real.\n"
    "4. Citas normativas erróneas (ID mal formado, versión incorrecta).\n\n"
    "REGLAS DURAS:\n"
    "- Sé estricto. La duda beneficia al rechazo, no a la aprobación.\n"
    "- Razona explícitamente por qué apruebas o rechazas.\n"
    "- Invoca SIEMPRE registrar_validacion con tu veredicto.\n"
)


class Validador:
    """Agente crítico que valida traducciones normativas de los especialistas.

    No tiene acceso a RAG — valida el razonamiento estructural y la coherencia
    interna de la traducción frente al hallazgo original.

    Atributos:
        agente_id: Identificador único del agente validador.
    """

    agente_id: str = "validador"

    def __init__(
        self,
        llm: LLMClient,
        profile: ModelProfile = ModelProfile.ECO,
    ) -> None:
        self.llm = llm
        self.profile = profile
        logger.info("validador_initialized", agente_id=self.agente_id, profile=profile)

    async def validar(
        self,
        traduccion: Traduccion,
        hallazgo: DatosRedTeam,
    ) -> ValidacionResult:
        """Valida una traducción normativa contra el hallazgo original.

        Args:
            traduccion: La Traduccion generada por un agente especialista.
            hallazgo: El hallazgo técnico original.

        Returns:
            ValidacionResult con el veredicto del validador. Si el LLM no
            invoca la herramienta, retorna un resultado inválido seguro.
        """
        traduccion_id = f"{traduccion.agente_id}:{traduccion.marco.value}"

        hallazgo_json = json.dumps(hallazgo.model_dump(), ensure_ascii=False, indent=2)
        traduccion_json = json.dumps(
            {
                "marco": traduccion.marco.value,
                "controles_incumplidos": traduccion.datos.controles_incumplidos,
                "cita_normativa": traduccion.datos.cita_normativa,
                "justificacion": traduccion.datos.justificacion,
                "impacto_legal": traduccion.datos.impacto_legal.value,
                "accion_mitigacion": traduccion.datos.accion_mitigacion,
                "fragmentos_usados": traduccion.fragmentos_usados,
                "confianza_original": traduccion.confianza,
            },
            ensure_ascii=False,
            indent=2,
        )

        prompt = (
            f"# Hallazgo técnico original\n\n```json\n{hallazgo_json}\n```\n\n"
            f"# Traducción normativa a validar\n\n```json\n{traduccion_json}\n```\n\n"
            f"Revisa críticamente esta traducción. ¿Los controles existen realmente "
            f"en {traduccion.marco.value}? ¿La justificación es sólida? "
            f"Invoca registrar_validacion con tu veredicto."
        )

        resultado = await self.llm.completar(
            system=_SYSTEM_PROMPT,
            messages=[Message(role="user", content=prompt)],
            tools=[_TOOL_VALIDACION],
        )

        if not resultado.tool_calls:
            logger.warning(
                "validador_sin_toolcall",
                agente_id=self.agente_id,
                traduccion_id=traduccion_id,
            )
            return ValidacionResult(
                traduccion_id=traduccion_id,
                valida=False,
                problemas=["LLM no invocó herramienta registrar_validacion"],
                confianza=0.0,
                razonamiento="El validador no pudo emitir veredicto: LLM no respondió con tool_use.",
            )

        tool_input = resultado.tool_calls[0].tool_input
        vr = self._parsear_resultado(traduccion_id, tool_input)

        logger.info(
            "validacion_completada",
            traduccion_id=traduccion_id,
            valida=vr.valida,
            confianza=vr.confianza,
        )
        return vr

    def _parsear_resultado(
        self, traduccion_id: str, tool_input: dict[str, Any]
    ) -> ValidacionResult:
        try:
            confianza = float(tool_input.get("confianza", 0.0))
            confianza = max(0.0, min(1.0, confianza))
        except (TypeError, ValueError):
            confianza = 0.0

        return ValidacionResult(
            traduccion_id=traduccion_id,
            valida=bool(tool_input.get("valida", False)),
            problemas=list(tool_input.get("problemas", [])),
            confianza=confianza,
            razonamiento=str(tool_input.get("razonamiento", "")),
        )
