"""Agente Traductor especialista en NIS2 (Directiva UE 2022/2555)."""

from __future__ import annotations

from rosetta.agents.translator.base import BaseTranslator
from rosetta.core.models import MarcoNormativo


class TraductorNIS2(BaseTranslator):
    """Especialista en NIS2 — Directiva UE 2022/2555 (EUR-Lex, dominio público).

    Cubre Art.20-23 (seguridad y notificación), sectores esenciales/importantes,
    plazos: alerta 24h, notificación 72h, informe final 1 mes.
    """

    MARCO = MarcoNormativo.NIS2

    def _system_prompt_extra(self) -> str:
        return (
            "\nCONTEXTO NIS2 (Directiva UE 2022/2555):\n"
            "- Art.20: gobernanza y responsabilidad de la dirección.\n"
            "- Art.21: medidas de gestión del riesgo (10 categorías a-j).\n"
            "- Art.23: notificación de incidentes significativos.\n"
            "- Art.24: uso de esquemas de certificación.\n"
            "- IDs formato Art.NN o Art.NN.N (ej: Art.21.2.h, Art.23.1).\n"
            "- Indica si aplica a entidades esenciales, importantes o ambas.\n"
            "- Incluye plazos de notificación si el hallazgo implica incidente.\n"
        )
