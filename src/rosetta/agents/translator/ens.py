"""Agente Traductor especialista en ENS 2022 (RD 311/2022)."""

from __future__ import annotations

from rosetta.agents.translator.base import BaseTranslator
from rosetta.core.models import MarcoNormativo


class TraductorENS(BaseTranslator):
    """Especialista en ENS 2022 — Esquema Nacional de Seguridad (BOE, dominio público).

    Estructura: medidas org/op/mp, niveles Bajo/Medio/Alto.
    Códigos tipo org.1, op.acc.5, mp.si.3.
    """

    MARCO = MarcoNormativo.ENS_2022

    def _system_prompt_extra(self) -> str:
        return (
            "\nCONTEXTO ENS 2022:\n"
            "- 3 categorías: org (organizativas), op (operacionales), "
            "mp (medidas de protección).\n"
            "- Niveles: Básico / Medio / Alto.\n"
            "- IDs formato categoria.subcategoria.N (ej: op.acc.5, mp.si.3).\n"
            "- Cita categoría, subcategoría y nivel requerido.\n"
        )
