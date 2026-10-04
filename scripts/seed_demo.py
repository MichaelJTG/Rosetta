"""Puebla una instancia de ROSETTA con el caso ficticio TechServ (A-4).

El script SOLO envía **datos de entrada** a la API real de ROSETTA
(``/translate``, ``/analyze-diff``, ``/blue/ingest``, ``/drift/analyze``,
``/ingest/pdf`` y ``/reports/generate``). Todos los resultados (traducciones
normativas, correlaciones, dosier) los genera el sistema en ese momento con su
LLM. El script nunca escribe en SQLite, ChromaDB ni Neo4j.

Caso TechServ (ficticio, basado en el caso docente): proveedor TIC que presta
servicio a tres consejerías autonómicas (Sanidad, Educación y Hacienda), sistema
de categoría ALTA según el ENS y con tratamiento de datos de salud. Para que
todos los paneles tengan contenido se añade un cliente financiero también
ficticio (DORA) y una pasarela de pago de tasas (PCI-DSS).

Todos los nombres usan el dominio reservado ``.example`` y las IP pertenecen a
los rangos de documentación del RFC 5737. Ningún dato es real.

Uso (con la aplicación arrancada)::

    uv run python scripts/seed_demo.py --url http://127.0.0.1:8000

Credenciales: ``ROSETTA_USER`` / ``ROSETTA_PASSWORD`` del entorno o del ``.env``.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

ORGANIZACION = "TechServ (caso ficticio)"

# Cada hallazgo se traduce contra 2-3 marcos; entre todos cubren los 7 marcos
# con corpus propio (ISO 27002 se cubre vía el Anexo A de ISO 27001).
HALLAZGOS: list[dict[str, Any]] = [
    {
        "hallazgo": {
            "origen": "nuclei",
            "activo_detectado": "citas.techserv.example",
            "evidencia": "https://citas.techserv.example/.env (HTTP 200, 1,2 KB)",
            "vector_ataque": (
                "Fichero .env publicado en el portal de cita previa sanitaria con la "
                "cadena de conexión a la base de datos de agenda de pacientes"
            ),
            "dificultad_explotacion": "baja",
        },
        "marcos": ["ens_2022", "iso_27001_2022", "rgpd"],
    },
    {
        "hallazgo": {
            "origen": "nmap",
            "activo_detectado": "hce.techserv.example",
            "evidencia": "nmap --script ssl-enum-ciphers -p 443: TLSv1.0 y TLSv1.1 habilitados",
            "vector_ataque": (
                "El servidor de historia clínica electrónica acepta TLS 1.0/1.1 y "
                "cifrados débiles: riesgo de interceptación de datos de salud"
            ),
            "dificultad_explotacion": "media",
        },
        "marcos": ["ens_2022", "iso_27001_2022", "nist_csf_2"],
    },
    {
        "hallazgo": {
            "origen": "manual",
            "activo_detectado": "vpn.techserv.example",
            "evidencia": "Revisión de configuración: 4 cuentas de administración sin MFA",
            "vector_ataque": (
                "Acceso remoto de administradores de la Consejería de Hacienda a la "
                "VPN solo con usuario y contraseña, sin segundo factor"
            ),
            "dificultad_explotacion": "media",
        },
        "marcos": ["ens_2022", "nis2", "iso_27001_2022"],
    },
    {
        "hallazgo": {
            "origen": "nmap",
            "activo_detectado": "203.0.113.24",
            "evidencia": "nmap -sV -p 3389: ms-wbt-server abierto a Internet",
            "vector_ataque": (
                "Servidor de salto de la Consejería de Educación con RDP expuesto a "
                "Internet sin restricción de origen"
            ),
            "dificultad_explotacion": "media",
        },
        "marcos": ["ens_2022", "nist_csf_2"],
    },
    {
        "hallazgo": {
            "origen": "manual",
            "activo_detectado": "backup.techserv.example",
            "evidencia": "Inspección del NAS: volcados .sql de pacientes sin cifrar",
            "vector_ataque": (
                "Copias de seguridad de la base de datos de pacientes almacenadas sin "
                "cifrar en un recurso compartido accesible por toda la red interna"
            ),
            "dificultad_explotacion": "baja",
        },
        "marcos": ["ens_2022", "rgpd", "iso_27001_2022"],
    },
    {
        "hallazgo": {
            "origen": "nuclei",
            "activo_detectado": "pagos.techserv.example",
            "evidencia": "https://pagos.techserv.example/checkout carga 3 scripts externos sin SRI",
            "vector_ataque": (
                "La página de pago de tasas sanitarias con tarjeta carga scripts de "
                "terceros sin integridad verificada ni inventario autorizado"
            ),
            "dificultad_explotacion": "media",
        },
        "marcos": ["pci_dss_4", "iso_27001_2022"],
    },
    {
        "hallazgo": {
            "origen": "manual",
            "activo_detectado": "plataforma-banca.techserv.example",
            "evidencia": "Entrevista y revisión documental: último simulacro de continuidad en 2023",
            "vector_ataque": (
                "TechServ presta como proveedor TIC la plataforma de banca de una caja "
                "rural (ficticia) sin pruebas de resiliencia ni procedimiento de "
                "notificación de incidentes TIC graves"
            ),
            "dificultad_explotacion": "alta",
        },
        "marcos": ["dora", "nis2"],
    },
]

DIFF_GATE = """\
diff --git a/config/settings.py b/config/settings.py
--- a/config/settings.py
+++ b/config/settings.py
@@ -10,3 +10,6 @@
 DEBUG = False
+DB_HOST = "hce-db.techserv.example"
+DB_PASSWORD = "valor-ficticio-demo"
+VERIFY_TLS = False
"""

ALERTAS_WAZUH: list[dict[str, Any]] = [
    {
        "id": "ts-0001",
        "timestamp": "2026-10-01T08:12:00",
        "rule": {"id": "60122", "level": 10, "description": "RDP: múltiples fallos de login"},
        "agent": {"id": "014", "name": "salto-educacion", "ip": "203.0.113.24"},
    },
    {
        "id": "ts-0002",
        "timestamp": "2026-10-01T08:14:30",
        "rule": {
            "id": "60204",
            "level": 12,
            "description": "RDP: login correcto tras fuerza bruta",
        },
        "agent": {"id": "014", "name": "salto-educacion", "ip": "203.0.113.24"},
    },
    {
        "id": "ts-0003",
        "timestamp": "2026-10-02T23:40:00",
        "rule": {"id": "5710", "level": 7, "description": "SSH: intento con usuario inexistente"},
        "agent": {"id": "021", "name": "sftp-hacienda", "ip": "198.51.100.17"},
    },
]

PROCEDIMIENTO_DRIFT = """\
PRO-IAM-001 · Gestión de cuentas de usuario (TechServ, ficticio)
1. Las cuentas sin uso durante 90 días se deshabilitan automáticamente.
2. Las cuentas de administración requieren doble factor de autenticación.
3. Las bajas de personal se tramitan en 24 horas desde la comunicación de RR. HH.
"""

OBSERVACIONES_DRIFT = [
    "Wazuh: 37 cuentas de dominio sin login desde hace más de 180 días siguen habilitadas",
    "Revisión VPN: 4 cuentas de administración sin segundo factor",
    "2 cuentas de personal dado de baja hace 3 semanas siguen activas",
]

INFORME_PDF = [
    "Informe de auditoría externa — TechServ (caso ficticio)",
    "Hallazgo 1. El portal de empleados (empleados.techserv.example) permite contraseñas "
    "de 6 caracteres sin bloqueo tras intentos fallidos. Severidad: media.",
    "Hallazgo 2. No existe registro de actividad de los administradores en el servidor "
    "de historia clínica (hce.techserv.example). Severidad: alta.",
]


@dataclass
class Resumen:
    """Resultado de una ejecución del seed: pasos correctos y errores."""

    correctos: list[str] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)


def _pdf_informe() -> bytes:
    """Genera en memoria un PDF ficticio de informe de auditoría (entrada de RF-05)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    estilos = getSampleStyleSheet()
    elementos: list[Any] = [Paragraph(INFORME_PDF[0], estilos["Title"]), Spacer(1, 12)]
    elementos += [Paragraph(texto, estilos["BodyText"]) for texto in INFORME_PDF[1:]]
    SimpleDocTemplate(buffer, pagesize=A4).build(elementos)
    return buffer.getvalue()


def _paso(resumen: Resumen, nombre: str, respuesta: httpx.Response) -> dict[str, Any] | None:
    """Registra el resultado de una llamada y devuelve el JSON si fue correcta."""
    if respuesta.is_success:
        resumen.correctos.append(nombre)
        print(f"  [ok] {nombre}")
        cuerpo: dict[str, Any] = respuesta.json()
        return cuerpo
    resumen.errores.append(f"{nombre}: HTTP {respuesta.status_code}")
    print(f"  [error] {nombre}: HTTP {respuesta.status_code} {respuesta.text[:200]}")
    return None


def autenticar(cliente: httpx.Client, usuario: str | None, password: str | None) -> None:
    """Obtiene un JWT y lo fija en las cabeceras del cliente (si hay credenciales)."""
    if not usuario:
        print("Sin credenciales: se asume la autenticación desactivada (modo desarrollo).")
        return
    r = cliente.post("/auth/login", json={"username": usuario, "password": password or ""})
    if r.status_code != 200:
        raise SystemExit(f"Login fallido (HTTP {r.status_code}). Revisa ROSETTA_USER/PASSWORD.")
    cliente.headers["Authorization"] = f"Bearer {r.json()['access_token']}"


def ejecutar(cliente: httpx.Client, *, con_pdf: bool = True) -> Resumen:
    """Envía todo el caso TechServ a la API y devuelve el resumen."""
    resumen = Resumen()

    print(f"1/6 Traduciendo {len(HALLAZGOS)} hallazgos (el LLM genera la evidencia)...")
    for item in HALLAZGOS:
        r = cliente.post("/translate", json=item)
        datos = _paso(resumen, f"translate {item['hallazgo']['activo_detectado']}", r)
        if datos:
            print(f"       controles: {', '.join(datos.get('controles_incumplidos', []))}")

    print("2/6 Gate CI/CD: analizando un diff ficticio...")
    _paso(
        resumen,
        "analyze-diff",
        cliente.post(
            "/analyze-diff",
            json={"diff": DIFF_GATE, "marcos": ["ens_2022", "iso_27001_2022"]},
        ),
    )

    print("3/6 Blue Team: ingiriendo alertas Wazuh ficticias...")
    _paso(
        resumen,
        "blue/ingest",
        cliente.post("/blue/ingest", json={"formato": "json", "datos_json": ALERTAS_WAZUH}),
    )

    print("4/6 Procedure drift: procedimiento PRO-IAM-001 frente a lo observado...")
    _paso(
        resumen,
        "drift/analyze",
        cliente.post(
            "/drift/analyze",
            json={"procedimiento": PROCEDIMIENTO_DRIFT, "observaciones": OBSERVACIONES_DRIFT},
        ),
    )

    if con_pdf:
        print("5/6 Ingesta de un informe PDF ficticio de auditoría humana...")
        _paso(
            resumen,
            "ingest/pdf",
            cliente.post(
                "/ingest/pdf",
                files={
                    "file": ("informe_techserv_ficticio.pdf", _pdf_informe(), "application/pdf")
                },
            ),
        )
    else:
        print("5/6 Ingesta de PDF omitida (--sin-pdf).")

    print("6/6 Generando el dosier de auditoría...")
    dosier = _paso(
        resumen,
        "reports/generate",
        cliente.post("/reports/generate", json={"nombre_cliente": ORGANIZACION}),
    )
    if dosier:
        print(f"       descarga: {dosier['md_url']} · {dosier['pdf_url']}")
    return resumen


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--url", default=os.getenv("ROSETTA_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--usuario", default=None, help="Por defecto ROSETTA_USER.")
    parser.add_argument("--password", default=None, help="Por defecto ROSETTA_PASSWORD.")
    parser.add_argument("--sin-pdf", action="store_true", help="Omite la ingesta de PDF.")
    args = parser.parse_args(argv)

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:  # pragma: no cover - python-dotenv es dependencia del proyecto
        pass
    usuario = args.usuario or os.getenv("ROSETTA_USER") or None
    password = args.password or os.getenv("ROSETTA_PASSWORD")

    inicio = time.monotonic()
    timeout = httpx.Timeout(900.0, connect=10.0)  # un LLM local puede tardar minutos
    with httpx.Client(base_url=args.url, timeout=timeout) as cliente:
        autenticar(cliente, usuario, password)
        resumen = ejecutar(cliente, con_pdf=not args.sin_pdf)

    duracion = time.monotonic() - inicio
    print(
        f"\nSeed terminado en {duracion:.0f} s: {len(resumen.correctos)} pasos correctos, "
        f"{len(resumen.errores)} con error."
    )
    for error in resumen.errores:
        print(f"  - {error}")
    return 1 if resumen.errores else 0


if __name__ == "__main__":
    sys.exit(main())
