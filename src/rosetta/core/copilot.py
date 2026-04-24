"""copilot — interfaz de consulta en lenguaje natural al corpus normativo.

El Copilot recibe una pregunta libre, recupera contexto RAG relevante
y genera una respuesta fundamentada en los controles del corpus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

from rosetta.core.models import MarcoNormativo
from rosetta.llm.base import Message

if TYPE_CHECKING:
    from rosetta.core.rag import NormativaRAG
    from rosetta.llm.base import LLMClient

_TODOS_MARCOS: list[MarcoNormativo] = list(MarcoNormativo)

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = (
    "Eres el Copilot de ROSETTA, un asistente experto en normativa de ciberseguridad "
    "(ISO 27001:2022, ENS 2022, NIS2, DORA, RGPD). "
    "Responde preguntas usando ÚNICAMENTE los controles y artículos del contexto RAG "
    "proporcionado. Si el contexto no contiene información suficiente, indícalo "
    "explícitamente — nunca inventes controles o artículos.\n\n"
    "Formato de respuesta: claro, conciso, con referencias a controles (ID + nombre)."
)


class CopilotQuery(BaseModel):
    """Consulta al Copilot normativo."""

    pregunta: str = Field(..., description="Pregunta en lenguaje natural sobre normativa.")
    contexto: str = Field(
        "",
        description="Contexto operativo adicional (ej: tipo de sistema, sector).",
    )


class CopilotResponse(BaseModel):
    """Respuesta del Copilot normativo."""

    respuesta: str = Field(..., description="Respuesta fundamentada en el corpus RAG.")
    fuentes: list[str] = Field(
        default_factory=list,
        description="IDs de controles usados como fuente.",
    )
    confianza: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confianza proporcional al número de fragmentos RAG recuperados.",
    )


async def consultar_copilot(
    query: CopilotQuery,
    llm: LLMClient,
    rag: NormativaRAG,
) -> CopilotResponse:
    """Responde una consulta normativa usando RAG + LLM.

    Args:
        query: Pregunta y contexto del usuario.
        llm: Cliente LLM para generar la respuesta.
        rag: Motor RAG para recuperar fragmentos del corpus.

    Returns:
        CopilotResponse con la respuesta y las fuentes utilizadas.
        La confianza es proporcional a los fragmentos RAG disponibles.
    """
    fragmentos = rag.recuperar(query.pregunta, marcos=_TODOS_MARCOS, top_k=5)
    fuentes = [f.control_id for f in fragmentos]

    if fragmentos:
        lineas = ["## Contexto normativo relevante\n"]
        for f in fragmentos:
            lineas.append(f"### {f.control_id} — {f.nombre} ({f.marco})")
            lineas.append(f.texto)
            lineas.append("")
        contexto_rag = "\n".join(lineas)
        confianza = min(1.0, len(fragmentos) / 5.0)
    else:
        contexto_rag = "No se encontraron controles relevantes en el corpus para esta consulta."
        confianza = 0.3

    prompt_parts = [f"# Pregunta\n\n{query.pregunta}"]
    if query.contexto:
        prompt_parts.append(f"\n# Contexto adicional\n\n{query.contexto}")
    prompt_parts.append(f"\n{contexto_rag}")
    prompt_parts.append("\nResponde basándote únicamente en el contexto normativo proporcionado.")
    prompt = "\n".join(prompt_parts)

    resultado = await llm.completar(
        system=_SYSTEM_PROMPT,
        messages=[Message(role="user", content=prompt)],
        tools=[],
    )

    respuesta = resultado.content or "No se pudo generar una respuesta."

    logger.info(
        "copilot_respondido",
        fragmentos=len(fragmentos),
        confianza=confianza,
    )
    return CopilotResponse(
        respuesta=respuesta,
        fuentes=fuentes,
        confianza=confianza,
    )
