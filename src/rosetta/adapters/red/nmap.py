"""Adaptador para Nmap — escáner de puertos y servicios.

Orquesta el binario oficial de Nmap vía asyncio subprocess y parsea
su salida XML estándar. No se modifica el código de Nmap.

Licencia de Nmap: GPL-2.0 con excepción de uso comercial (orquestamos
  via CLI — no se linkea ni se embebe el código).
Requisito: binario `nmap` disponible en PATH.
"""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from typing import Any

import structlog

from rosetta.adapters.base import RedTeamAdapter
from rosetta.core.models import DatosRedTeam, FuenteRedTeam, Severidad

logger = structlog.get_logger(__name__)

# Puertos con exposición inherentemente crítica o alta
_PUERTOS_RIESGO: dict[int, Severidad] = {
    21: Severidad.ALTA,  # FTP — sin cifrado
    23: Severidad.CRITICA,  # Telnet — sin cifrado, obsoleto
    25: Severidad.ALTA,  # SMTP sin autenticación
    110: Severidad.ALTA,  # POP3 — sin cifrado
    111: Severidad.ALTA,  # RPCBind
    135: Severidad.ALTA,  # MSRPC
    139: Severidad.ALTA,  # NetBIOS Session
    445: Severidad.CRITICA,  # SMB — vector principal de ransomware
    512: Severidad.CRITICA,  # rexec
    513: Severidad.CRITICA,  # rlogin
    514: Severidad.CRITICA,  # rsh
    1433: Severidad.ALTA,  # MSSQL
    1521: Severidad.ALTA,  # Oracle DB
    3306: Severidad.ALTA,  # MySQL
    3389: Severidad.ALTA,  # RDP
    5432: Severidad.ALTA,  # PostgreSQL
    5900: Severidad.ALTA,  # VNC
    6379: Severidad.CRITICA,  # Redis (sin auth por defecto)
    27017: Severidad.CRITICA,  # MongoDB (sin auth por defecto)
}

# Puertos de administración expuestos a internet → media
_PUERTOS_ADMIN: set[int] = {22, 80, 443, 8080, 8443, 9090, 9200, 9300}


class NmapAdapter(RedTeamAdapter):
    """Wrapper que ejecuta `nmap` como subproceso y parsea su XML.

    Estrategia:
        - `-sV`: detecta versiones de servicios.
        - `--open`: solo reporta puertos abiertos.
        - `-oX -`: output XML a stdout.
        - `--top-ports N`: limita el número de puertos escaneados.

    Cada puerto abierto detectado se convierte en un DatosRedTeam,
    con severidad derivada del número de puerto y nombre de servicio.
    """

    nombre = "nmap"

    def __init__(
        self,
        binario: str = "nmap",
        timeout_segundos: int = 120,
        top_ports: int = 100,
    ) -> None:
        """
        Args:
            binario: Ruta al ejecutable de Nmap (por defecto "nmap" en PATH).
            timeout_segundos: Timeout máximo para el escaneo.
            top_ports: Número de puertos más comunes a escanear.
        """
        self.binario = binario
        self.timeout = timeout_segundos
        self.top_ports = top_ports

    async def escanear(self, objetivo: str, **_kwargs: Any) -> list[DatosRedTeam]:
        """Ejecuta nmap -sV --open -oX - <objetivo> y normaliza los resultados.

        Args:
            objetivo: IP, dominio o rango CIDR del activo autorizado a escanear.

        Returns:
            Lista de DatosRedTeam, uno por puerto abierto detectado.

        Raises:
            FileNotFoundError: Si el binario nmap no está en PATH.
            RuntimeError: Si nmap termina con código de error inesperado.
        """
        cmd = [
            self.binario,
            "-sV",
            "--open",
            f"--top-ports={self.top_ports}",
            "-oX",
            "-",
            "--host-timeout",
            f"{self.timeout}s",
            objetivo,
        ]
        logger.info("nmap_escaneo_inicio", objetivo=objetivo, top_ports=self.top_ports)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=float(self.timeout),
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Binario '{self.binario}' no encontrado en PATH. "
                "Instala Nmap: https://nmap.org/download.html"
            ) from exc
        except TimeoutError as exc:
            proc.kill()
            raise RuntimeError(
                f"Nmap superó el timeout de {self.timeout}s contra {objetivo}"
            ) from exc

        if proc.returncode not in (0, 1):
            raise RuntimeError(
                f"Nmap terminó con código {proc.returncode}. "
                f"stderr: {stderr.decode('utf-8', errors='replace')[:300]}"
            )

        xml_text = stdout.decode("utf-8", errors="replace")
        hallazgos = self._parsear_xml(xml_text, objetivo)
        logger.info("nmap_escaneo_fin", objetivo=objetivo, hallazgos=len(hallazgos))
        return hallazgos

    def _parsear_xml(self, xml_text: str, objetivo: str) -> list[DatosRedTeam]:
        """Parsea el XML de nmap y devuelve una lista de DatosRedTeam."""
        hallazgos: list[DatosRedTeam] = []
        if not xml_text.strip():
            return hallazgos

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("nmap_xml_parse_error", error=str(exc))
            return hallazgos

        for host_elem in root.findall("host"):
            host_ip = self._extraer_ip(host_elem, objetivo)
            ports_elem = host_elem.find("ports")
            if ports_elem is None:
                continue
            for port_elem in ports_elem.findall("port"):
                hallazgo = self._port_a_hallazgo(host_ip, port_elem)
                if hallazgo is not None:
                    hallazgos.append(hallazgo)

        return hallazgos

    def _extraer_ip(self, host_elem: ET.Element, fallback: str) -> str:
        """Extrae la dirección IP del elemento <host>."""
        for addr in host_elem.findall("address"):
            addr_type = addr.get("addrtype", "")
            if addr_type in ("ipv4", "ipv6"):
                return addr.get("addr", fallback)
        return fallback

    def _port_a_hallazgo(self, host_ip: str, port_elem: ET.Element) -> DatosRedTeam | None:
        """Convierte un elemento <port> de nmap en DatosRedTeam."""
        state_elem = port_elem.find("state")
        if state_elem is None or state_elem.get("state") != "open":
            return None

        portid = int(port_elem.get("portid", "0"))
        protocol = port_elem.get("protocol", "tcp")
        service_elem = port_elem.find("service")

        service_name = "desconocido"
        product = ""
        version = ""
        if service_elem is not None:
            service_name = service_elem.get("name", "desconocido")
            product = service_elem.get("product", "")
            version = service_elem.get("version", "")

        severidad = _PUERTOS_RIESGO.get(portid, Severidad.BAJA)
        if portid in _PUERTOS_ADMIN and severidad == Severidad.BAJA:
            severidad = Severidad.MEDIA

        version_str = f" {product} {version}".strip()
        vector = (
            f"Puerto {portid}/{protocol} abierto: servicio {service_name}{version_str}. "
            f"Exposición de servicio {service_name} en {host_ip}."
        )

        try:
            return DatosRedTeam(
                origen=FuenteRedTeam.NMAP,
                activo_detectado=f"{host_ip}:{portid}/{protocol}",
                evidencia=f"nmap:port:{portid}/{protocol}:{service_name}",
                vector_ataque=vector[:300],
                dificultad_explotacion=severidad,
                metadatos={
                    "port": portid,
                    "protocol": protocol,
                    "service": service_name,
                    "product": product,
                    "version": version,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("nmap_port_normalizar_error", port=portid, error=str(exc))
            return None
