"""Agente Traductor especialista en NIST CSF 2.0."""

from __future__ import annotations

from rosetta.agents.translator.base import BaseTranslator
from rosetta.core.models import MarcoNormativo


class TraductorNIST(BaseTranslator):
    """Especialista en NIST CSF 2.0 — Cybersecurity Framework (dominio público, NIST).

    6 funciones: GOVERN (GV), IDENTIFY (ID), PROTECT (PR), DETECT (DE),
    RESPOND (RS), RECOVER (RC). Cada función tiene categorías y subcategorías.
    IDs formato FUNCION-CAT.NN (ej: PR.DS-01, DE.CM-09, RS.CO-02).
    """

    MARCO = MarcoNormativo.NIST_CSF_2

    def _system_prompt_extra(self) -> str:
        return (
            "\nCONTEXTO NIST CSF 2.0:\n"
            "- 6 funciones: GOVERN (GV), IDENTIFY (ID), PROTECT (PR), "
            "DETECT (DE), RESPOND (RS), RECOVER (RC).\n"
            "- IDs formato FUNCIÓN-CAT.NN (ej: PR.DS-01, DE.CM-09, RS.CO-02, GV.OC-01).\n"
            "- GOVERN (nuevo en v2.0): estrategia, políticas, roles, supervisión, "
            "gestión de riesgos.\n"
            "- IDENTIFY: activos, riesgos, cadena de suministro.\n"
            "- PROTECT: controles de acceso, cifrado, formación, actualizaciones.\n"
            "- DETECT: monitorización, detección de anomalías.\n"
            "- RESPOND: respuesta a incidentes, comunicación, mitigación.\n"
            "- RECOVER: recuperación, mejoras post-incidente.\n"
            "- Cita función, categoría y subcategoría exactas.\n"
        )
