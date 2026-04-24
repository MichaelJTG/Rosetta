"""Agente Traductor especialista en DORA (Reglamento UE 2022/2554)."""

from __future__ import annotations

from rosetta.agents.translator.base import BaseTranslator
from rosetta.core.models import MarcoNormativo


class TraductorDORA(BaseTranslator):
    """Especialista en DORA — Digital Operational Resilience Act (EUR-Lex, dominio público).

    Ámbito: entidades financieras UE. 5 pilares: gestión de riesgos TIC,
    gestión de incidentes, pruebas de resiliencia, riesgos de terceros, intercambio de info.
    Artículos clave: Art.5-16 (gestión riesgos), Art.17-23 (incidentes),
    Art.24-27 (pruebas), Art.28-44 (terceros).
    """

    MARCO = MarcoNormativo.DORA

    def _system_prompt_extra(self) -> str:
        return (
            "\nCONTEXTO DORA (Reglamento UE 2022/2554):\n"
            "- 5 pilares: gestión de riesgos TIC (Art.5-16), gestión de incidentes "
            "(Art.17-23), pruebas de resiliencia operativa digital (Art.24-27), "
            "riesgos de terceros proveedores TIC (Art.28-44), "
            "intercambio de información (Art.45).\n"
            "- IDs formato Art.NN o Art.NN.N (ej: Art.9.2, Art.17.1).\n"
            "- Aplica a entidades financieras: bancos, aseguradoras, gestoras, "
            "proveedores TIC críticos.\n"
            "- Cita artículo y apartado exacto del texto del Reglamento.\n"
        )
