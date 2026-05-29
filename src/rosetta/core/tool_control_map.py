"""Mapping estático herramienta → controles normativos que evidencia.

Cada fuente de datos (Wazuh, Nuclei, NMAP, etc.) genera evidencia que
demuestra cumplimiento de controles concretos. Este módulo centraliza
ese mapping para que el panel de evidencias pueda mostrar qué controles
están cubiertos por qué herramientas.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Mapping: FuenteRedTeam / "WAZUH" → lista de (control_id, título)
# ---------------------------------------------------------------------------

TOOL_CONTROL_MAP: dict[str, list[tuple[str, str]]] = {
    "WAZUH": [
        ("ISO_27001_A.8.15", "Logging"),
        ("ISO_27001_A.8.16", "Monitoring activities"),
        ("ISO_27001_A.8.17", "Clock synchronisation"),
        ("ISO_27001_A.5.25", "Assessment of information security events"),
        ("ISO_27001_A.5.26", "Response to information security incidents"),
        ("ENS_op.mon.1", "Detección de intrusiones"),
        ("ENS_op.exp.10", "Protección de los registros de actividad"),
        ("NIS2_Art.21.2.b", "Gestión de incidentes"),
    ],
    "NUCLEI": [
        ("ISO_27001_A.8.8", "Management of technical vulnerabilities"),
        ("ISO_27001_A.8.9", "Configuration management"),
        ("ISO_27001_A.8.25", "Secure development life cycle"),
        ("ENS_op.pl.2", "Análisis de riesgos"),
        ("ENS_mp.sw.1", "Desarrollo de aplicaciones"),
        ("NIS2_Art.21.2.e", "Seguridad en adquisición, desarrollo y mantenimiento"),
    ],
    "NMAP": [
        ("ISO_27001_A.8.20", "Networks security"),
        ("ISO_27001_A.8.21", "Security of network services"),
        ("ISO_27001_A.8.22", "Segregation of networks"),
        ("ENS_mp.com.1", "Perímetro seguro"),
        ("ENS_mp.com.2", "Protección de la confidencialidad"),
        ("NIS2_Art.21.2.h", "Seguridad de redes e infraestructuras"),
    ],
    "AMASS": [
        ("ISO_27001_A.5.9", "Inventory of information and other associated assets"),
        ("ISO_27001_A.8.20", "Networks security"),
        ("ENS_op.pl.1", "Análisis de riesgos"),
        ("ENS_mp.com.1", "Perímetro seguro"),
    ],
    "SUBFINDER": [
        ("ISO_27001_A.5.9", "Inventory of information and other associated assets"),
        ("ISO_27001_A.8.20", "Networks security"),
        ("ENS_mp.com.1", "Perímetro seguro"),
    ],
    "THEHARVESTER": [
        ("ISO_27001_A.5.9", "Inventory of information and other associated assets"),
        ("ISO_27001_A.5.14", "Information transfer"),
        ("ENS_op.pl.1", "Análisis de riesgos"),
    ],
    "SHODAN": [
        ("ISO_27001_A.8.8", "Management of technical vulnerabilities"),
        ("ISO_27001_A.8.20", "Networks security"),
        ("ISO_27001_A.8.21", "Security of network services"),
        ("ENS_mp.com.1", "Perímetro seguro"),
    ],
    "HIBP": [
        ("ISO_27001_A.5.17", "Authentication information"),
        ("ISO_27001_A.8.5", "Secure authentication"),
        ("ENS_mp.s.1", "Protección del correo electrónico"),
        ("NIS2_Art.21.2.i", "Políticas de contraseñas"),
    ],
    "GITHUB_SECRETS": [
        ("ISO_27001_A.5.17", "Authentication information"),
        ("ISO_27001_A.8.9", "Configuration management"),
        ("ISO_27001_A.8.25", "Secure development life cycle"),
        ("ENS_mp.sw.1", "Desarrollo de aplicaciones"),
    ],
    "MANUAL": [
        ("ISO_27001_A.5.35", "Independent review of information security"),
        ("ENS_op.pl.5", "Arquitectura de seguridad"),
    ],
    "OTRO": [],
}


def get_controls_for_tool(fuente: str) -> list[tuple[str, str]]:
    """Devuelve lista de (control_id, título) para una fuente dada."""
    return TOOL_CONTROL_MAP.get(fuente.upper(), [])


def get_all_covered_controls() -> dict[str, list[str]]:
    """Devuelve mapping control_id → lista de fuentes que lo evidencian."""
    result: dict[str, list[str]] = {}
    for fuente, controles in TOOL_CONTROL_MAP.items():
        for ctrl_id, _ in controles:
            result.setdefault(ctrl_id, []).append(fuente)
    return result


def get_control_title(control_id: str) -> str:
    """Devuelve el título de un control por su ID, o el ID si no está mapeado."""
    for controles in TOOL_CONTROL_MAP.values():
        for ctrl_id, titulo in controles:
            if ctrl_id == control_id:
                return titulo
    return control_id


# ---------------------------------------------------------------------------
# Catálogo mínimo de controles ISO 27001:2022 y ENS para el dashboard
# ---------------------------------------------------------------------------

ISO_27001_CONTROLS: list[dict[str, str]] = [
    {
        "id": "A.5.1",
        "titulo": "Policies for information security",
        "descripcion": "Políticas de seguridad de la información definidas, aprobadas por la dirección, publicadas y comunicadas.",
    },
    {
        "id": "A.5.2",
        "titulo": "Information security roles and responsibilities",
        "descripcion": "Roles y responsabilidades de seguridad de la información asignados y comunicados.",
    },
    {
        "id": "A.5.9",
        "titulo": "Inventory of information and other associated assets",
        "descripcion": "Inventario de activos de información y otros activos asociados, mantenido y actualizado.",
    },
    {
        "id": "A.5.14",
        "titulo": "Information transfer",
        "descripcion": "Controles para la transferencia de información establecidos para todos los tipos de medios.",
    },
    {
        "id": "A.5.17",
        "titulo": "Authentication information",
        "descripcion": "Gestión de la información de autenticación: contraseñas, certificados, tokens.",
    },
    {
        "id": "A.5.25",
        "titulo": "Assessment of information security events",
        "descripcion": "Evaluación de eventos de seguridad para determinar si deben clasificarse como incidentes.",
    },
    {
        "id": "A.5.26",
        "titulo": "Response to information security incidents",
        "descripcion": "Respuesta a incidentes de seguridad conforme a procedimientos documentados.",
    },
    {
        "id": "A.5.35",
        "titulo": "Independent review of information security",
        "descripcion": "Revisión independiente del enfoque de gestión de la seguridad de la información.",
    },
    {
        "id": "A.8.5",
        "titulo": "Secure authentication",
        "descripcion": "Tecnologías y procedimientos de autenticación segura implementados.",
    },
    {
        "id": "A.8.8",
        "titulo": "Management of technical vulnerabilities",
        "descripcion": "Gestión de vulnerabilidades técnicas: identificación, evaluación, remediación y seguimiento.",
    },
    {
        "id": "A.8.9",
        "titulo": "Configuration management",
        "descripcion": "Configuraciones de hardware, software y redes establecidas, documentadas y aplicadas.",
    },
    {
        "id": "A.8.15",
        "titulo": "Logging",
        "descripcion": "Registros de actividad generados, protegidos y analizados regularmente.",
    },
    {
        "id": "A.8.16",
        "titulo": "Monitoring activities",
        "descripcion": "Redes, sistemas y aplicaciones monitorizados para detectar comportamientos anómalos.",
    },
    {
        "id": "A.8.17",
        "titulo": "Clock synchronisation",
        "descripcion": "Relojes de sistemas sincronizados con fuentes de tiempo de referencia aprobadas.",
    },
    {
        "id": "A.8.20",
        "titulo": "Networks security",
        "descripcion": "Redes gestionadas y controladas para proteger sistemas e información.",
    },
    {
        "id": "A.8.21",
        "titulo": "Security of network services",
        "descripcion": "Mecanismos de seguridad y niveles de servicio de red identificados e implementados.",
    },
    {
        "id": "A.8.22",
        "titulo": "Segregation of networks",
        "descripcion": "Grupos de servicios de información, usuarios y sistemas segregados en redes.",
    },
    {
        "id": "A.8.25",
        "titulo": "Secure development life cycle",
        "descripcion": "Principios de ingeniería de sistemas seguros aplicados al desarrollo.",
    },
]

ENS_CONTROLS: list[dict[str, str]] = [
    {
        "id": "op.pl.1",
        "titulo": "Análisis de riesgos",
        "descripcion": "Análisis de riesgos realizado y actualizado periódicamente conforme al ENS.",
    },
    {
        "id": "op.pl.2",
        "titulo": "Arquitectura de seguridad",
        "descripcion": "Arquitectura de seguridad documentada con líneas de defensa definidas.",
    },
    {
        "id": "op.pl.5",
        "titulo": "Gestión de cambios",
        "descripcion": "Proceso formal de gestión de cambios que garantiza la seguridad del sistema.",
    },
    {
        "id": "op.mon.1",
        "titulo": "Detección de intrusiones",
        "descripcion": "Sistema de detección de intrusiones activo y configurado para el entorno.",
    },
    {
        "id": "op.exp.10",
        "titulo": "Protección de los registros de actividad",
        "descripcion": "Registros de actividad protegidos contra acceso no autorizado y manipulación.",
    },
    {
        "id": "mp.com.1",
        "titulo": "Perímetro seguro",
        "descripcion": "Perímetro de red delimitado con controles de acceso y filtrado adecuados.",
    },
    {
        "id": "mp.com.2",
        "titulo": "Protección de la confidencialidad",
        "descripcion": "Comunicaciones cifradas para proteger la confidencialidad de la información.",
    },
    {
        "id": "mp.s.1",
        "titulo": "Protección del correo electrónico",
        "descripcion": "Correo electrónico protegido contra spam, phishing y malware.",
    },
    {
        "id": "mp.sw.1",
        "titulo": "Desarrollo de aplicaciones",
        "descripcion": "Ciclo de desarrollo seguro aplicado a todas las aplicaciones del sistema.",
    },
]

CONTROLS_BY_MARCO: dict[str, list[dict[str, str]]] = {
    "iso_27001_2022": ISO_27001_CONTROLS,
    "ISO_27001_2022": ISO_27001_CONTROLS,
    "ens_2022": ENS_CONTROLS,
    "ENS_2022": ENS_CONTROLS,
}


def get_controls_catalog(marco: str) -> list[dict[str, str]]:
    """Devuelve el catálogo de controles para un marco normativo.

    Returns:
        Lista de dicts con 'id', 'titulo', 'descripcion'. Vacía si no hay catálogo.
    """
    return CONTROLS_BY_MARCO.get(marco, [])
