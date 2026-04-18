"""Traductor Simbiótico — núcleo del razonamiento normativo de ROSETTA.

Recibe un hallazgo técnico (DatosRedTeam) y devuelve su traducción normativa
(DatosCompliance) consultando el RAG sobre el corpus normativo elegido.

Este módulo es el componente de mayor valor del producto: donde Vanta
recoge evidencia de señales conocidas, el Traductor razona sobre
hallazgos arbitrarios y los mapea semánticamente a controles normativos
multi-marco con cita textual y acción de mitigación concreta.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    MarcoNormativo,
)

if TYPE_CHECKING:
    from rosetta.core.rag import NormativaRAG
    from rosetta.llm.claude import ClaudeClient

logger = structlog.get_logger(__name__)


SYSTEM_PROMPT = """Eres el Traductor Simbiótico de ROSETTA, un sistema experto en \
cumplimiento normativo de ciberseguridad. Tu única función es tomar un hallazgo \
técnico y traducirlo a la norma seleccionada de forma rigurosa, auditable y \
trazable.

REGLAS DURAS:
1. NUNCA inventes controles. Si el RAG no devuelve un control aplicable, \
dilo explícitamente.
2. Cada control citado debe incluir su ID exacto y cita textual del corpus.
3. La justificación debe conectar hallazgo técnico ↔ control normativo con \
razonamiento explícito, no vago.
4. La acción de mitigación debe ser TÉCNICA y CONCRETA (regla, configuración, \
comando), no genérica.
5. Si el hallazgo afecta a varios marcos, indícalos todos en marcos_aplicables.
6. El output debe ser JSON válido conforme al schema DatosCompliance.
"""


class TraductorSimbiotico:
    """El cerebro normativo de ROSETTA.

    Atributos:
        llm: Cliente para el LLM (por defecto Claude).
        rag: Recuperador del corpus normativo.
        marcos_activos: Qué marcos consultar en cada auditoría.
    """

    def __init__(
        self,
        llm: ClaudeClient,
        rag: NormativaRAG,
        marcos_activos: list[MarcoNormativo],
    ) -> None:
        if not marcos_activos:
            raise ValueError(
                "Debe activarse al menos un marco normativo para el Traductor."
            )
        self.llm = llm
        self.rag = rag
        self.marcos_activos = marcos_activos
        logger.info(
            "traductor_initialized",
            marcos=[m.value for m in marcos_activos],
        )

    async def traducir(self, hallazgo: DatosRedTeam) -> DatosCompliance:
        """Traduce un hallazgo técnico a su representación normativa.

        Args:
            hallazgo: Datos del hallazgo técnico (Red Team / OSINT).

        Returns:
            DatosCompliance con controles incumplidos, cita, justificación
            y acción de mitigación.

        Raises:
            NotImplementedError: Pendiente de implementación en MVP.
        """
        # TODO [MVP-1]: Implementar pipeline
        #   1. Extraer query semántica del hallazgo (vector de ataque +
        #      tipo de activo + evidencia).
        #   2. Recuperar top-k fragmentos normativos de cada marco activo
        #      en ChromaDB.
        #   3. Construir prompt con RAG context + hallazgo + schema DatosCompliance.
        #   4. Llamar al LLM con tool use para forzar JSON schema.
        #   5. Validar respuesta contra DatosCompliance.
        #   6. Registrar razonamiento en grafo Neo4j para trazabilidad.
        raise NotImplementedError(
            "Traductor Simbiótico pendiente de implementación. Ver docs/ROADMAP.md#mvp-1"
        )

    def _construir_query(self, hallazgo: DatosRedTeam) -> str:
        """Convierte un hallazgo en consulta semántica para el RAG."""
        return (
            f"{hallazgo.vector_ataque}. "
            f"Activo afectado: {hallazgo.activo_detectado}. "
            f"Evidencia: {hallazgo.evidencia}"
        )
