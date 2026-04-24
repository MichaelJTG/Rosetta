"""remediation_validator — verificación de remediaciones contra un dossier normativo.

Dado un DossierMultimarco y evidencias de remediación, el LLM determina
qué controles han sido efectivamente cerrados y cuáles siguen pendientes.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel

from rosetta.core.models import DossierMultimarco
from rosetta.llm.base import Message, Tool, ToolInputSchema

if TYPE_CHECKING:
    from rosetta.llm.base import LLMClient

logger = structlog.get_logger(__name__)

_TOOL_REMEDIACION = Tool(
    name="registrar_remediacion",
    description=(
        "Registra el resultado de la verificación de remediación. "
        "Indica qué controles han sido cerrados y cuáles siguen abiertos."
    ),
    input_schema=ToolInputSchema(
        type="object",
        properties={
            "remediado": {
                "type": "boolean",
                "description": "True si todos los controles críticos han sido cerrados.",
            },
            "evidencias_validacion": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Evidencias que respaldan el veredicto.",
            },
            "controles_cerrados": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de controles verificados como cerrados.",
            },
            "controles_pendientes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de controles que siguen sin remediar.",
            },
            "comentario": {
                "type": "string",
                "description": "Comentario técnico sobre el estado de la remediación.",
            },
        },
        required=[
            "remediado",
            "evidencias_validacion",
            "controles_cerrados",
            "controles_pendientes",
        ],
    ),
)

_SYSTEM_PROMPT = (
    "Eres un auditor técnico especializado en verificación de remediaciones. "
    "Tu función es revisar si las evidencias proporcionadas demuestran que los "
    "controles normativos incumplidos han sido efectivamente remediados.\n\n"
    "REGLAS:\n"
    "1. Verifica cada control incumplido contra las evidencias disponibles.\n"
    "2. Un control solo se considera cerrado si hay evidencia concreta.\n"
    "3. La duda beneficia al estado 'pendiente', no a 'cerrado'.\n"
    "4. Invoca SIEMPRE registrar_remediacion con tu veredicto.\n"
)


class RemediacionResult(BaseModel):
    """Resultado de la verificación de remediación de un dossier normativo."""

    hallazgo_id: str = ""
    remediado: bool = False
    evidencias_validacion: list[str] = []
    controles_cerrados: list[str] = []
    controles_pendientes: list[str] = []
    comentario: str = ""


async def verificar_remediacion(
    dossier: DossierMultimarco,
    evidencias: list[str],
    llm: LLMClient,
) -> RemediacionResult:
    """Verifica si las evidencias cierran los controles del dossier.

    Args:
        dossier: Dossier multi-marco con los controles incumplidos.
        evidencias: Lista de evidencias de remediación aportadas.
        llm: Cliente LLM para el análisis.

    Returns:
        RemediacionResult con el estado de cada control. Si el LLM no
        invoca la herramienta, retorna resultado no remediado seguro.
    """
    controles_pendientes = dossier.controles_unicos

    dossier_resumen = {
        "hallazgo_id": dossier.hallazgo_id,
        "controles_incumplidos": controles_pendientes,
        "marcos": [m.value for m in dossier.marcos_procesados],
        "traducciones_validas": len(dossier.traducciones_validas),
    }

    prompt = (
        f"# Dossier normativo\n\n"
        f"```json\n{json.dumps(dossier_resumen, ensure_ascii=False, indent=2)}\n```\n\n"
        f"# Evidencias de remediación aportadas\n\n"
        + "\n".join(f"- {e}" for e in evidencias)
        + "\n\nVerifica si las evidencias cierran los controles incumplidos. "
        "Invoca registrar_remediacion con tu veredicto."
    )

    resultado = await llm.completar(
        system=_SYSTEM_PROMPT,
        messages=[Message(role="user", content=prompt)],
        tools=[_TOOL_REMEDIACION],
    )

    if not resultado.tool_calls:
        logger.warning("remediacion_sin_toolcall", hallazgo_id=dossier.hallazgo_id)
        return RemediacionResult(
            hallazgo_id=dossier.hallazgo_id,
            remediado=False,
            controles_pendientes=controles_pendientes,
            comentario="LLM no emitió veredicto de remediación.",
        )

    tool_input = resultado.tool_calls[0].tool_input
    rm = _parsear_resultado(dossier.hallazgo_id, tool_input)

    logger.info(
        "remediacion_verificada",
        hallazgo_id=dossier.hallazgo_id,
        remediado=rm.remediado,
        controles_cerrados=len(rm.controles_cerrados),
        controles_pendientes=len(rm.controles_pendientes),
    )
    return rm


def _parsear_resultado(hallazgo_id: str, tool_input: dict[str, Any]) -> RemediacionResult:
    return RemediacionResult(
        hallazgo_id=hallazgo_id,
        remediado=bool(tool_input.get("remediado", False)),
        evidencias_validacion=list(tool_input.get("evidencias_validacion", [])),
        controles_cerrados=list(tool_input.get("controles_cerrados", [])),
        controles_pendientes=list(tool_input.get("controles_pendientes", [])),
        comentario=str(tool_input.get("comentario", "")),
    )
