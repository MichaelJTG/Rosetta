"""Funciones de dependencia FastAPI para inyección de componentes de ROSETTA.

Todas las dependencias leen de app.state, que se inicializa en el lifespan
de main.py. El uso de cast() es necesario porque starlette.State es Any.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from rosetta.core.control_store import ControlStore
from rosetta.core.diff_analyzer import DiffAnalyzer
from rosetta.core.session_store import SessionStore
from rosetta.core.traductor import TraductorSimbiotico


def get_traductor(request: Request) -> TraductorSimbiotico:
    """Devuelve el TraductorSimbiotico inicializado en lifespan."""
    return cast(TraductorSimbiotico, request.app.state.traductor)


def get_grafo(request: Request) -> object | None:
    """Devuelve el GrafoCorrelacion si Neo4j está disponible, o None."""
    return cast("object | None", request.app.state.grafo)


def get_session_findings(request: Request) -> SessionStore:
    """Devuelve el SessionStore (SQLite) de hallazgos de la sesión."""
    return cast(SessionStore, request.app.state.session_findings)


def get_diff_analyzer(request: Request) -> DiffAnalyzer:
    """Devuelve un DiffAnalyzer compartiendo LLM y RAG del Traductor."""
    traductor = get_traductor(request)
    return DiffAnalyzer(llm=traductor.llm, rag=traductor.rag)


def get_control_store(request: Request) -> ControlStore:
    """Devuelve el ControlStore (SQLite) de estados de controles."""
    return cast(ControlStore, request.app.state.control_store)


TraductorDep = Annotated[TraductorSimbiotico, Depends(get_traductor)]
GrafoDep = Annotated[object | None, Depends(get_grafo)]
FindingsDep = Annotated[SessionStore, Depends(get_session_findings)]
DiffAnalyzerDep = Annotated[DiffAnalyzer, Depends(get_diff_analyzer)]
ControlStoreDep = Annotated[ControlStore, Depends(get_control_store)]
