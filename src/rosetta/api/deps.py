"""Funciones de dependencia FastAPI para inyección de componentes de ROSETTA.

Todas las dependencias leen de app.state, que se inicializa en el lifespan
de main.py. El uso de cast() es necesario porque starlette.State es Any.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from rosetta.core.models import HallazgoMaestro
from rosetta.core.traductor import TraductorSimbiotico


def get_traductor(request: Request) -> TraductorSimbiotico:
    """Devuelve el TraductorSimbiotico inicializado en lifespan."""
    return cast(TraductorSimbiotico, request.app.state.traductor)


def get_grafo(request: Request) -> object | None:
    """Devuelve el GrafoCorrelacion si Neo4j está disponible, o None."""
    return cast("object | None", request.app.state.grafo)


def get_session_findings(request: Request) -> list[HallazgoMaestro]:
    """Devuelve la lista de hallazgos de la sesión actual."""
    return cast("list[HallazgoMaestro]", request.app.state.session_findings)


TraductorDep = Annotated[TraductorSimbiotico, Depends(get_traductor)]
GrafoDep = Annotated[object | None, Depends(get_grafo)]
FindingsDep = Annotated[list[HallazgoMaestro], Depends(get_session_findings)]
