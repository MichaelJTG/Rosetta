"""Soundwave — scheduler de agentes traductores (sin LLM).

Gestiona ejecución paralela con semáforo asyncio, aislando errores
individuales para que un traductor fallido no bloquee al resto.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog

from rosetta.core.models import DatosRedTeam, Traduccion

if TYPE_CHECKING:
    from rosetta.agents.translator.base import BaseTranslator

logger = structlog.get_logger(__name__)


class Soundwave:
    """Scheduler de agentes traductores.

    Ejecuta múltiples traductores en paralelo usando asyncio.gather con
    return_exceptions=True. El semáforo limita la concurrencia máxima
    simultánea al gateway LLM.

    Atributos:
        max_concurrencia: Número máximo de llamadas LLM simultáneas.
    """

    def __init__(self, max_concurrencia: int = 7) -> None:
        self.max_concurrencia = max_concurrencia

    async def ejecutar_paralelo(
        self,
        traductores: list[BaseTranslator],
        hallazgo: DatosRedTeam,
    ) -> list[Traduccion]:
        """Ejecuta todos los traductores en paralelo y recoge resultados válidos.

        Args:
            traductores: Lista de agentes traductores a ejecutar.
            hallazgo: Hallazgo técnico a traducir.

        Returns:
            Lista de Traduccion exitosas. Los fallos se excluyen y se loguean.
        """
        if not traductores:
            return []

        semaforo = asyncio.Semaphore(self.max_concurrencia)

        async def _ejecutar_uno(t: BaseTranslator) -> Traduccion | BaseException:
            async with semaforo:
                try:
                    return await t.traducir(hallazgo)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "traductor_fallo",
                        agente_id=t.agente_id,
                        error=str(exc),
                    )
                    return exc

        resultados = await asyncio.gather(*[_ejecutar_uno(t) for t in traductores])

        traducciones: list[Traduccion] = [r for r in resultados if isinstance(r, Traduccion)]

        logger.info(
            "soundwave_completado",
            total=len(traductores),
            exitosos=len(traducciones),
            fallidos=len(traductores) - len(traducciones),
        )
        return traducciones
