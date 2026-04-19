"""Detector de procedure drift — MVP-5.

Compara el texto de un procedimiento interno con observaciones de sensores
(logs, alertas, hallazgos) y detecta si la práctica real diverge del
procedimiento escrito.

Insight del mentor Carlos Gómez Pintado (CEO Cyberxia):
    "Es importante la revisión de procedimientos y mantenimiento de los
    mismos, que es el gran problema de las empresas."

El pain point: los procedimientos se escriben para pasar auditorías y luego
quedan estáticos mientras la realidad operativa evoluciona. ROSETTA detecta
esa desviación y propone la actualización del texto.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from rosetta.core.models import ResultadoDrift, Severidad
from rosetta.llm.base import Message, Tool, ToolInputSchema

if TYPE_CHECKING:
    from rosetta.llm.base import LLMClient

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """Eres el módulo de Procedure Drift de ROSETTA, especializado en
detectar desviaciones entre procedimientos de seguridad escritos y el comportamiento
real observado por sensores.

Tu función es analizar:
1. El texto de un procedimiento interno de seguridad.
2. Las observaciones reales del entorno (logs, alertas, hallazgos de sensores).

Y determinar si existe drift: si la práctica real diverge del procedimiento escrito.

REGLAS:
1. Si el procedimiento NO se puede evaluar con las observaciones dadas, di drift_detectado=false.
2. Sé concreto: cita el fragmento exacto del procedimiento que diverge.
3. La redacción propuesta debe ser pragmática — si la práctica real es correcta,
   actualiza el procedimiento para reflejarla; si no lo es, mantén el procedimiento
   y señala la no-conformidad.
4. Los controles_afectados deben ser IDs reales (A.5.1, op.acc.4…), no inventados.
5. Responde SIEMPRE usando la herramienta registrar_drift.
"""

_TOOL_DRIFT = Tool(
    name="registrar_drift",
    description="Registra el resultado del análisis de procedure drift.",
    input_schema=ToolInputSchema(
        type="object",
        properties={
            "drift_detectado": {
                "type": "boolean",
                "description": "True si existe desviación significativa entre procedimiento y realidad.",
            },
            "descripcion_drift": {
                "type": "string",
                "description": "Descripción clara de la desviación detectada.",
            },
            "fragmento_afectado": {
                "type": "string",
                "description": "Cita textual del fragmento del procedimiento que diverge.",
            },
            "redaccion_propuesta": {
                "type": "string",
                "description": "Nueva redacción propuesta para el fragmento afectado.",
            },
            "evidencias": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de evidencias observadas que demuestran el drift.",
            },
            "controles_afectados": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de controles normativos comprometidos (ej: A.5.18, op.acc.4).",
            },
            "impacto": {
                "type": "string",
                "enum": ["informativa", "baja", "media", "alta", "critica"],
                "description": "Severidad normativa del drift.",
            },
        },
        required=["drift_detectado", "descripcion_drift"],
    ),
)


class DriftDetector:
    """Detecta desviaciones entre procedimientos escritos y realidad observada.

    Usa el LLM con tool-use para forzar un análisis estructurado y reproducible.
    """

    def __init__(self, llm: LLMClient) -> None:
        if llm is None:
            raise ValueError("DriftDetector requiere un LLMClient.")
        self.llm = llm

    async def detectar_drift(
        self,
        procedimiento_id: str,
        texto_procedimiento: str,
        observaciones: list[str],
    ) -> ResultadoDrift:
        """Analiza si las observaciones reales divergen del procedimiento escrito.

        Args:
            procedimiento_id: Identificador único del procedimiento (ej. "PRO-IAM-001").
            texto_procedimiento: Texto completo o extracto relevante del procedimiento.
            observaciones: Lista de observaciones de sensores que describen la realidad
                operativa actual (logs, alertas, hallazgos).

        Returns:
            ResultadoDrift con el análisis estructurado.

        Raises:
            ValueError: Si el LLM no invoca la herramienta registrar_drift.
        """
        logger.info(
            "detectando_drift",
            procedimiento_id=procedimiento_id,
            observaciones=len(observaciones),
        )

        prompt = self._construir_prompt(procedimiento_id, texto_procedimiento, observaciones)

        resultado = await self.llm.completar(
            system=_SYSTEM_PROMPT,
            messages=[Message(role="user", content=prompt)],
            tools=[_TOOL_DRIFT],
        )

        if not resultado.tool_calls:
            raise ValueError(f"El LLM no invocó registrar_drift. Respuesta: {resultado.content!r}")

        return self._parsear(procedimiento_id, resultado.tool_calls[0].tool_input)

    def _construir_prompt(
        self,
        procedimiento_id: str,
        texto_procedimiento: str,
        observaciones: list[str],
    ) -> str:
        obs_texto = "\n".join(f"  - {o}" for o in observaciones)
        return (
            f"# Procedimiento a analizar: {procedimiento_id}\n\n"
            f"```\n{texto_procedimiento}\n```\n\n"
            f"# Observaciones reales del entorno\n\n"
            f"{obs_texto}\n\n"
            f"Analiza si existe drift entre el procedimiento y las observaciones. "
            f"Usa la herramienta registrar_drift con tu análisis."
        )

    def _parsear(self, procedimiento_id: str, tool_input: dict[str, Any]) -> ResultadoDrift:
        impacto_raw = tool_input.get("impacto", "media")
        try:
            impacto = Severidad(impacto_raw)
        except ValueError:
            impacto = Severidad.MEDIA

        return ResultadoDrift(
            procedimiento_id=procedimiento_id,
            drift_detectado=bool(tool_input.get("drift_detectado", False)),
            descripcion_drift=tool_input.get("descripcion_drift", ""),
            fragmento_afectado=tool_input.get("fragmento_afectado", ""),
            redaccion_propuesta=tool_input.get("redaccion_propuesta", ""),
            evidencias=tool_input.get("evidencias", []),
            controles_afectados=tool_input.get("controles_afectados", []),
            impacto=impacto,
        )
