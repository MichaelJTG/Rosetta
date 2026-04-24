"""Agente Traductor especialista en RGPD (Reglamento UE 2016/679)."""

from __future__ import annotations

from rosetta.agents.translator.base import BaseTranslator
from rosetta.core.models import MarcoNormativo


class TraductorRGPD(BaseTranslator):
    """Especialista en RGPD — Reglamento General de Protección de Datos (EUR-Lex, dominio público).

    Artículos de seguridad clave: Art.5 (principios), Art.25 (privacy by design),
    Art.32 (seguridad del tratamiento), Art.33 (notificación de brechas a autoridad),
    Art.34 (comunicación a interesados), Art.35 (EIPD), Art.37-39 (DPO).
    """

    MARCO = MarcoNormativo.RGPD

    def _system_prompt_extra(self) -> str:
        return (
            "\nCONTEXTO RGPD (Reglamento UE 2016/679):\n"
            "- Artículos de seguridad principales: Art.5 (principios), "
            "Art.25 (privacidad por diseño y por defecto), "
            "Art.32 (seguridad del tratamiento — medidas técnicas/organizativas), "
            "Art.33 (notificación brecha a autoridad de control en 72h), "
            "Art.34 (comunicación a interesados), Art.35 (EIPD/DPIA), "
            "Art.37-39 (Delegado de Protección de Datos).\n"
            "- IDs formato Art.NN o Art.NN.N (ej: Art.32.1, Art.33.1).\n"
            "- Considera siempre si hay datos personales implicados en el hallazgo.\n"
            "- Cita artículo y apartado exacto del Reglamento.\n"
        )
