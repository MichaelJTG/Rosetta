"""Agente Traductor especialista en PCI-DSS 4.0."""

from __future__ import annotations

from rosetta.agents.translator.base import BaseTranslator
from rosetta.core.models import MarcoNormativo


class TraductorPCI(BaseTranslator):
    """Especialista en PCI-DSS 4.0 — Payment Card Industry Data Security Standard.

    12 requisitos principales organizados en 6 objetivos de control.
    Ámbito: cualquier entidad que procese, almacene o transmita datos de tarjetas de pago.
    IDs formato Req.N o Req.N.N.N (ej: Req.6.2.4, Req.8.3.9, Req.12.10.2).
    """

    MARCO = MarcoNormativo.PCI_DSS_4

    def _system_prompt_extra(self) -> str:
        return (
            "\nCONTEXTO PCI-DSS 4.0:\n"
            "- 12 requisitos: (1) Red segura, (2) No usar defaults de vendedor, "
            "(3) Proteger datos de tarjeta, (4) Cifrar transmisión, "
            "(5) Proteger contra malware, (6) Desarrollar sistemas seguros, "
            "(7) Restringir acceso a datos, (8) Identificar y autenticar acceso, "
            "(9) Restringir acceso físico, (10) Registrar y monitorizar acceso, "
            "(11) Probar sistemas de seguridad, (12) Política de seguridad.\n"
            "- IDs formato Req.N o Req.N.N.N (ej: Req.6.2.4, Req.8.3.9, Req.10.2.1).\n"
            "- Aplica solo si el hallazgo afecta a datos de tarjetas de pago (CHD/SAD) "
            "o a sistemas del entorno CDE.\n"
            "- Cita el requisito y subpunto exacto de PCI-DSS 4.0.\n"
        )
