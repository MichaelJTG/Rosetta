"""Agente Traductor especialista en ISO/IEC 27001:2022."""

from __future__ import annotations

from rosetta.agents.translator.base import BaseTranslator
from rosetta.core.models import MarcoNormativo


class TraductorISO(BaseTranslator):
    """Especialista en ISO 27001:2022 — Anexo A completo (93 controles, 4 dominios).

    Licencia del corpus: resúmenes intuitem (Apache-2.0) en corpus/iso27001/.
    """

    MARCO = MarcoNormativo.ISO_27001_2022

    def _system_prompt_extra(self) -> str:
        return (
            "\nCONTEXTO ISO 27001:2022:\n"
            "- 4 dominios: Organizacional (A.5), Personal (A.6), "
            "Físico (A.7), Tecnológico (A.8).\n"
            "- IDs formato A.X.YY (ej: A.8.24, A.5.15).\n"
            "- Cita dominio y número exacto. Nunca inventes controles.\n"
        )
