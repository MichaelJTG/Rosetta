"""Clase base abstracta para todos los agentes Traductores especialistas.

Cada subclase declara el marco normativo que domina y hereda el pipeline
RAG + LLM + tool-use. El contrato de salida es siempre `Traduccion`.
"""

from __future__ import annotations

import contextlib
import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import structlog

from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    MarcoNormativo,
    ModelProfile,
    Severidad,
    Traduccion,
)
from rosetta.llm.base import Message, Tool, ToolInputSchema

if TYPE_CHECKING:
    from rosetta.core.rag import NormativaRAG
    from rosetta.llm.base import LLMClient

logger = structlog.get_logger(__name__)

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
                "description": "Lista de marcos normativos aplicables.",
            },
            "controles_incumplidos": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de controles incumplidos.",
            },
            "cita_normativa": {
                "type": "string",
                "description": "Cita del control con ID y descripción.",
            },
            "justificacion": {
                "type": "string",
                "description": "Razonamiento que conecta hallazgo con control.",
            },
            "impacto_legal": {
                "type": "string",
                "enum": ["informativa", "baja", "media", "alta", "critica"],
                "description": "Severidad del impacto legal.",
            },
            "accion_mitigacion": {
                "type": "string",
                "description": "Acción técnica concreta para remediar.",
            },
            "evidencia_auditoria": {
                "type": "string",
                "description": "Texto listo para dossier de auditoría.",
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


class BaseTranslator(ABC):
    """Agente traductor especialista en un marco normativo concreto.

    Subclases deben declarar el atributo de clase `MARCO`.
    """

    MARCO: MarcoNormativo  # declarado por cada subclase

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "MARCO"):
            raise TypeError(f"{cls.__name__} debe declarar el atributo de clase MARCO")

    def __init__(
        self,
        llm: LLMClient,
        rag: NormativaRAG,
        profile: ModelProfile = ModelProfile.ECO,
    ) -> None:
        self.llm = llm
        self.rag = rag
        self.profile = profile
        self.agente_id = f"translator-{self.MARCO.value}"
        logger.info("translator_initialized", agente_id=self.agente_id, profile=profile)

    @property
    def system_prompt(self) -> str:
        return (
            f"Eres el Traductor especialista en {self.MARCO.value.upper()} de ROSETTA. "
            f"Tu ÚNICA función es mapear hallazgos técnicos a controles de "
            f"{self.MARCO.value} de forma rigurosa y auditable.\n\n"
            "REGLAS DURAS:\n"
            "1. NUNCA inventes controles. Solo usa los del contexto RAG proporcionado.\n"
            "2. Incluye el ID exacto del control en cita_normativa.\n"
            "3. La justificación conecta hallazgo ↔ control con razonamiento explícito.\n"
            "4. La acción de mitigación es TÉCNICA y CONCRETA.\n"
            "5. Responde SIEMPRE usando registrar_traduccion.\n" + self._system_prompt_extra()
        )

    @abstractmethod
    def _system_prompt_extra(self) -> str:
        """Override en subclases para añadir contexto de dominio."""

    async def traducir(self, hallazgo: DatosRedTeam) -> Traduccion:
        """Traduce un hallazgo al marco normativo de este agente."""
        query = (
            f"{hallazgo.vector_ataque}. "
            f"Activo: {hallazgo.activo_detectado}. "
            f"Evidencia: {hallazgo.evidencia}"
        )
        fragmentos = self.rag.recuperar(query, [self.MARCO], top_k=5)

        if not fragmentos:
            contexto = "No se encontraron controles relevantes en el corpus."
        else:
            lines = [f"## Controles {self.MARCO.value} relevantes\n"]
            for f in fragmentos:
                lines.append(f"### {f.control_id} — {f.nombre}")
                lines.append(f.texto)
                lines.append("")
            contexto = "\n".join(lines)

        hallazgo_json = json.dumps(hallazgo.model_dump(), ensure_ascii=False, indent=2)
        prompt = (
            f"# Hallazgo técnico\n\n```json\n{hallazgo_json}\n```\n\n"
            f"{contexto}\n\n"
            f"Traduce el hallazgo a controles de {self.MARCO.value}. "
            f"Usa SOLO los controles del contexto RAG. "
            f"Invoca registrar_traduccion con tu análisis."
        )

        resultado = await self.llm.completar(
            system=self.system_prompt,
            messages=[Message(role="user", content=prompt)],
            tools=[_TOOL_TRADUCCION],
        )

        if not resultado.tool_calls:
            raise ValueError(
                f"[{self.agente_id}] El LLM no invocó registrar_traduccion. "
                f"Respuesta: {resultado.content!r}"
            )

        tool_input = resultado.tool_calls[0].tool_input
        datos = self._parsear_resultado(tool_input)
        fragmentos_ids = [f.control_id for f in fragmentos]

        logger.info(
            "traduccion_completada",
            agente_id=self.agente_id,
            controles=datos.controles_incumplidos,
        )
        return Traduccion(
            marco=self.MARCO,
            datos=datos,
            agente_id=self.agente_id,
            fragmentos_usados=fragmentos_ids,
        )

    def _parsear_resultado(self, tool_input: dict[str, Any]) -> DatosCompliance:
        marcos_raw: list[str] = tool_input.get("marcos_aplicables", [self.MARCO.value])
        marcos = []
        for m in marcos_raw:
            with contextlib.suppress(ValueError):
                marcos.append(MarcoNormativo(m))
        if not marcos:
            marcos = [self.MARCO]

        try:
            impacto = Severidad(tool_input.get("impacto_legal", "media"))
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


# Necesario para que ABC detecte la clase como abstracta si no tiene MARCO
# (la verificación real es en __init_subclass__)
def _require_marco(cls: type) -> None:  # pragma: no cover
    pass
