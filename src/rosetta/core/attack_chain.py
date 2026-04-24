"""attack_chain — análisis de cadena de ataque MITRE ATT&CK.

Dado un hallazgo técnico, el LLM construye la cadena de ataque probable
usando técnicas MITRE ATT&CK, identificando pasos, tácticas e impacto máximo.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel

from rosetta.core.models import DatosRedTeam, Severidad
from rosetta.llm.base import Message, Tool, ToolInputSchema

if TYPE_CHECKING:
    from rosetta.llm.base import LLMClient

logger = structlog.get_logger(__name__)

_TOOL_CADENA = Tool(
    name="registrar_cadena",
    description=(
        "Registra la cadena de ataque MITRE ATT&CK inferida del hallazgo. "
        "Usa técnicas reales del framework MITRE ATT&CK."
    ),
    input_schema=ToolInputSchema(
        type="object",
        properties={
            "pasos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tecnica_mitre": {"type": "string"},
                        "descripcion": {"type": "string"},
                    },
                    "required": ["tecnica_mitre", "descripcion"],
                },
                "description": "Pasos ordenados de la cadena de ataque.",
            },
            "tacticas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tácticas MITRE ATT&CK involucradas (ej: 'Credential Access').",
            },
            "impacto_maximo": {
                "type": "string",
                "enum": ["informativa", "baja", "media", "alta", "critica"],
                "description": "Severidad del impacto máximo de la cadena.",
            },
        },
        required=["pasos", "tacticas", "impacto_maximo"],
    ),
)

_SYSTEM_PROMPT = (
    "Eres un analista de amenazas especializado en MITRE ATT&CK. "
    "Dado un hallazgo técnico, construyes la cadena de ataque probable "
    "usando técnicas reales del framework MITRE ATT&CK Enterprise.\n\n"
    "REGLAS:\n"
    "1. Solo cita técnicas MITRE ATT&CK reales (formato TXXXx o TXXX.XXX).\n"
    "2. Ordena los pasos cronológicamente.\n"
    "3. El impacto_maximo refleja el peor escenario plausible.\n"
    "4. Invoca SIEMPRE registrar_cadena con tu análisis.\n"
)


class Paso(BaseModel):
    """Un paso en la cadena de ataque con su técnica MITRE."""

    tecnica_mitre: str
    descripcion: str


class AtaqueEncadenado(BaseModel):
    """Cadena de ataque MITRE ATT&CK inferida de un hallazgo técnico."""

    hallazgo_origen: str = ""
    pasos: list[Paso] = []
    tacticas: list[str] = []
    impacto_maximo: Severidad = Severidad.INFORMATIVA


async def analizar_cadena(
    hallazgo: DatosRedTeam,
    llm: LLMClient,
) -> AtaqueEncadenado:
    """Analiza un hallazgo y construye la cadena de ataque MITRE ATT&CK.

    Args:
        hallazgo: Hallazgo técnico a analizar.
        llm: Cliente LLM para el análisis.

    Returns:
        AtaqueEncadenado con pasos y tácticas. Si el LLM no invoca la
        herramienta, retorna una cadena vacía con impacto informativo.
    """
    hallazgo_json = json.dumps(hallazgo.model_dump(), ensure_ascii=False, indent=2)
    prompt = (
        f"# Hallazgo técnico\n\n```json\n{hallazgo_json}\n```\n\n"
        f"Construye la cadena de ataque MITRE ATT&CK para este hallazgo. "
        f"Invoca registrar_cadena con tu análisis."
    )

    resultado = await llm.completar(
        system=_SYSTEM_PROMPT,
        messages=[Message(role="user", content=prompt)],
        tools=[_TOOL_CADENA],
    )

    if not resultado.tool_calls:
        logger.warning("attack_chain_sin_toolcall", activo=hallazgo.activo_detectado)
        return AtaqueEncadenado(hallazgo_origen=hallazgo.activo_detectado)

    tool_input = resultado.tool_calls[0].tool_input
    cadena = _parsear_cadena(hallazgo.activo_detectado, tool_input)

    logger.info(
        "attack_chain_completado",
        activo=hallazgo.activo_detectado,
        num_pasos=len(cadena.pasos),
        impacto=cadena.impacto_maximo,
    )
    return cadena


def _parsear_cadena(hallazgo_origen: str, tool_input: dict[str, Any]) -> AtaqueEncadenado:
    pasos_raw: list[dict[str, Any]] = tool_input.get("pasos", [])
    pasos = [
        Paso(
            tecnica_mitre=p.get("tecnica_mitre", ""),
            descripcion=p.get("descripcion", ""),
        )
        for p in pasos_raw
        if isinstance(p, dict)
    ]

    try:
        impacto = Severidad(tool_input.get("impacto_maximo", "informativa"))
    except ValueError:
        impacto = Severidad.INFORMATIVA

    return AtaqueEncadenado(
        hallazgo_origen=hallazgo_origen,
        pasos=pasos,
        tacticas=list(tool_input.get("tacticas", [])),
        impacto_maximo=impacto,
    )
