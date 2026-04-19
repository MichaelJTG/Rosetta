"""Servidor FastAPI de ROSETTA — endpoint del Traductor Simbiótico y orquestación."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException

from rosetta import __version__
from rosetta.core.models import DatosCompliance, DatosRedTeam, MarcoNormativo

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Inicializa recursos al arrancar y los cierra al parar."""
    logger.info("rosetta_api_starting", version=__version__)
    # TODO [MVP-1]: Inicializar ClaudeClient, NormativaRAG, GrafoCorrelacion.
    yield
    logger.info("rosetta_api_stopping")


app = FastAPI(
    title="ROSETTA API",
    description=(
        "Orquestador de cumplimiento continuo. Traduce hallazgos técnicos a "
        "evidencia normativa multi-marco (ISO 27001, ENS, NIS2, DORA)."
    ),
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Endpoint de salud para smoke tests."""
    return {"status": "ok", "version": __version__}


@app.post("/translate", response_model=DatosCompliance, tags=["traductor"])
async def translate(
    hallazgo: DatosRedTeam,  # noqa: ARG001
    marcos: list[MarcoNormativo],  # noqa: ARG001
) -> DatosCompliance:
    """Traduce un hallazgo técnico a evidencia normativa multi-marco."""
    # TODO [MVP-1]: Inyectar TraductorSimbiotico y delegar.
    raise HTTPException(
        status_code=501,
        detail="Traductor no implementado todavía. Ver docs/ROADMAP.md#mvp-1",
    )
