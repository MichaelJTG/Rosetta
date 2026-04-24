"""RosettaOrchestrator — orquestador principal de la arquitectura multi-agente.

Despacha hallazgos a los traductores especializados vía Soundwave,
valida cada traducción con el Validador crítico y ensambla el DossierMultimarco.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

from rosetta.core.models import (
    DatosRedTeam,
    DossierMultimarco,
    MarcoNormativo,
    Traduccion,
    ValidacionResult,
)

if TYPE_CHECKING:
    from rosetta.agents.soundwave import Soundwave
    from rosetta.agents.translator.base import BaseTranslator
    from rosetta.agents.validator import Validador

logger = structlog.get_logger(__name__)


class RosettaOrchestrator:
    """Orquestador principal del pipeline multi-agente de ROSETTA.

    Coordina:
    1. Selección de traductores según marcos solicitados.
    2. Ejecución paralela vía Soundwave con tolerancia a fallos.
    3. Validación crítica individual de cada traducción.
    4. Ensamblado del DossierMultimarco con estado auditado.

    Atributos:
        traductores: Mapa marco → agente traductor especialista.
        soundwave: Scheduler de ejecución paralela.
        validador: Agente crítico de validación.
    """

    def __init__(
        self,
        traductores: dict[MarcoNormativo, BaseTranslator],
        soundwave: Soundwave,
        validador: Validador,
    ) -> None:
        self.traductores = traductores
        self.soundwave = soundwave
        self.validador = validador
        logger.info(
            "orquestador_initialized",
            marcos_disponibles=[m.value for m in traductores],
        )

    async def traducir(
        self,
        hallazgo: DatosRedTeam,
        hallazgo_id: str | None = None,
        marcos: list[MarcoNormativo] | None = None,
    ) -> DossierMultimarco:
        """Orquesta la traducción completa de un hallazgo a múltiples marcos.

        Args:
            hallazgo: Hallazgo técnico a traducir.
            hallazgo_id: Identificador del hallazgo (generado si no se provee).
            marcos: Marcos normativos a procesar. Por defecto: todos disponibles.

        Returns:
            DossierMultimarco con traducciones validadas y estado de cada marco.
        """
        hid = hallazgo_id or str(uuid.uuid4())
        marcos_solicitados = marcos or list(self.traductores.keys())

        traductores_activos: list[BaseTranslator] = []
        marcos_fallidos: list[MarcoNormativo] = []

        for marco in marcos_solicitados:
            if marco in self.traductores:
                traductores_activos.append(self.traductores[marco])
            else:
                logger.warning("marco_sin_traductor", marco=marco.value, hallazgo_id=hid)
                marcos_fallidos.append(marco)

        traducciones: list[Traduccion] = await self.soundwave.ejecutar_paralelo(
            traductores_activos, hallazgo
        )

        marcos_traducidos = {t.marco for t in traducciones}
        for marco in marcos_solicitados:
            if marco not in marcos_fallidos and marco not in marcos_traducidos:
                marcos_fallidos.append(marco)

        validaciones: list[ValidacionResult] = []
        for traduccion in traducciones:
            try:
                vr = await self.validador.validar(traduccion, hallazgo)
                validaciones.append(vr)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "validacion_fallo",
                    traduccion_id=f"{traduccion.agente_id}:{traduccion.marco.value}",
                    error=str(exc),
                )
                validaciones.append(
                    ValidacionResult(
                        traduccion_id=f"{traduccion.agente_id}:{traduccion.marco.value}",
                        valida=False,
                        problemas=[f"Error en validación: {exc}"],
                        confianza=0.0,
                        razonamiento="Validación fallida por excepción interna.",
                    )
                )

        dossier = DossierMultimarco(
            hallazgo_id=hid,
            traducciones=traducciones,
            validaciones=validaciones,
            marcos_procesados=list(marcos_traducidos),
            marcos_fallidos=marcos_fallidos,
        )

        logger.info(
            "dossier_completado",
            hallazgo_id=hid,
            marcos_ok=len(marcos_traducidos),
            marcos_fallidos=len(marcos_fallidos),
            traducciones_validas=len(dossier.traducciones_validas),
        )
        return dossier
