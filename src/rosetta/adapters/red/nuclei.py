"""Adaptador para Nuclei — escáner de vulnerabilidades basado en templates.

Nuclei es MIT, orquestable vía CLI, output JSON estable. Ideal para
integrar sin tocar su código.

Licencia: MIT (projectdiscovery/nuclei)
Requisito: binario `nuclei` disponible en PATH.
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

import structlog

from rosetta.adapters.base import RedTeamAdapter
from rosetta.core.models import DatosRedTeam, FuenteRedTeam, Severidad

logger = structlog.get_logger(__name__)

# Mapeo de severidades Nuclei → Severidad ROSETTA
_SEVERIDAD_MAP: dict[str, Severidad] = {
    "info": Severidad.INFORMATIVA,
    "low": Severidad.BAJA,
    "medium": Severidad.MEDIA,
    "high": Severidad.ALTA,
    "critical": Severidad.CRITICA,
    "unknown": Severidad.MEDIA,
}

# Default selection covers what an audit of a web asset needs (exposed files,
# misconfigurations, technology/version disclosure) without the ~11k templates.
_DEFAULT_TAGS = "exposure,misconfig,tech"
_DEFAULT_SEVERIDADES = "info,low,medium,high,critical"
_TAG_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


def _lista_env(variable: str, defecto: str) -> list[str]:
    """Lee una lista separada por comas de una variable de entorno."""
    raw = os.getenv(variable, defecto)
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _validar_tags(tags: list[str], origen: str) -> list[str]:
    for tag in tags:
        if not _TAG_RE.match(tag):
            raise ValueError(f"{origen}: tag de Nuclei no válido {tag!r}.")
    return tags


def _validar_severidades(severidades: list[str], origen: str) -> list[str]:
    for sev in severidades:
        if sev not in _SEVERIDAD_MAP:
            raise ValueError(
                f"{origen}: severidad {sev!r} no válida; usa {', '.join(_SEVERIDAD_MAP)}."
            )
    return severidades


class NucleiAdapter(RedTeamAdapter):
    """Wrapper que ejecuta `nuclei` como subproceso y parsea su JSON.

    Orquesta el binario oficial de Nuclei vía asyncio subprocess.
    No modifica Nuclei — sólo consume su output JSON.

    Uso típico:
        adapter = NucleiAdapter()
        hallazgos = await adapter.escanear("https://objetivo.example.com")
    """

    nombre = "nuclei"

    def __init__(
        self,
        binario: str = "nuclei",
        templates: list[str] | None = None,
        timeout_segundos: int = 300,
        tags: list[str] | None = None,
        severidades: list[str] | None = None,
    ) -> None:
        """
        Args:
            binario: Ruta al ejecutable de Nuclei (por defecto "nuclei" en PATH).
            templates: Lista de IDs de templates a usar (None = todos los instalados).
            timeout_segundos: Timeout máximo para el escaneo completo.
            tags: Tags de plantillas a ejecutar. None = ``ROSETTA_NUCLEI_TAGS``
                (por defecto ``exposure,misconfig,tech``); lista vacía = sin filtro.
            severidades: Severidades a reportar. None = ``ROSETTA_NUCLEI_SEVERITY``
                (por defecto todas).

        Raises:
            ValueError: Si un tag o una severidad no son válidos.
        """
        self.binario = binario
        self.templates = templates
        self.timeout = timeout_segundos
        self.tags = _validar_tags(
            tags if tags is not None else _lista_env("ROSETTA_NUCLEI_TAGS", _DEFAULT_TAGS),
            "ROSETTA_NUCLEI_TAGS",
        )
        self.severidades = _validar_severidades(
            severidades
            if severidades is not None
            else _lista_env("ROSETTA_NUCLEI_SEVERITY", _DEFAULT_SEVERIDADES),
            "ROSETTA_NUCLEI_SEVERITY",
        )

    async def escanear(self, objetivo: str, **_kwargs: Any) -> list[DatosRedTeam]:
        """Ejecuta `nuclei -u <objetivo> -jsonl -silent` y normaliza la salida.

        Args:
            objetivo: URL, IP o dominio del activo autorizado a escanear.
            **kwargs: Ignorados — reservados para compatibilidad futura.

        Returns:
            Lista de DatosRedTeam, uno por hallazgo encontrado por Nuclei.

        Raises:
            FileNotFoundError: Si el binario nuclei no está disponible en PATH.
            RuntimeError: Si nuclei termina con código de error inesperado.
        """
        cmd = self._construir_comando(objetivo)
        logger.info("nuclei_escaneo_inicio", objetivo=objetivo, cmd=" ".join(cmd))

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
                "Instala Nuclei: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
            ) from exc
        except TimeoutError as exc:
            proc.kill()
            raise RuntimeError(
                f"Nuclei superó el timeout de {self.timeout}s contra {objetivo}"
            ) from exc

        if proc.returncode not in (0, 1):
            # Nuclei sale con 1 si no encuentra hallazgos; >1 es error real
            raise RuntimeError(
                f"Nuclei terminó con código {proc.returncode}. "
                f"stderr: {stderr.decode('utf-8', errors='replace')[:500]}"
            )

        hallazgos = self._parsear_salida(stdout.decode("utf-8", errors="replace"), objetivo)
        logger.info(
            "nuclei_escaneo_fin",
            objetivo=objetivo,
            hallazgos=len(hallazgos),
        )
        return hallazgos

    def _construir_comando(self, objetivo: str) -> list[str]:
        """Construye el comando CLI de Nuclei.

        - ``-nmhe``: sin ella, unos pocos fallos de DNS con nombres internos
          (``lab-objetivo`` en Docker) marcaban el host como caído y Nuclei se
          saltaba el resto de plantillas: 0 hallazgos contra el laboratorio.
        - ``-ni``: sin interactsh; las pruebas out-of-band contactan servidores
          externos, y el Modo Auditoría solo debe tocar el objetivo autorizado.
        - ``-duc``: sin comprobación de versiones contra GitHub en cada escaneo.
        """
        cmd = [self.binario, "-u", objetivo, "-jsonl", "-silent", "-nc", "-nmhe", "-ni", "-duc"]
        if self.tags:
            cmd += ["-tags", ",".join(self.tags)]
        if self.severidades:
            cmd += ["-severity", ",".join(self.severidades)]
        if self.templates:
            for tmpl in self.templates:
                cmd += ["-t", tmpl]
        return cmd

    def _parsear_salida(self, stdout: str, objetivo: str) -> list[DatosRedTeam]:
        """Parsea las líneas JSON del output de Nuclei en DatosRedTeam."""
        hallazgos: list[DatosRedTeam] = []

        for linea in stdout.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            try:
                resultado = json.loads(linea)
            except json.JSONDecodeError:
                logger.warning("nuclei_linea_no_json", linea=linea[:100])
                continue

            hallazgo = self._normalizar(resultado, objetivo)
            if hallazgo is not None:
                hallazgos.append(hallazgo)

        return hallazgos

    def _normalizar(self, resultado: dict[str, Any], objetivo: str) -> DatosRedTeam | None:
        """Convierte un resultado Nuclei a DatosRedTeam.

        Mapeo de campos:
            host / matched-at → activo_detectado
            info.name + info.description → vector_ataque
            template-id → evidencia (referencia al template)
            info.severity → dificultad_explotacion
            info.classification.cve-id → cve_relacionado
        """
        info: dict[str, Any] = resultado.get("info", {})
        nombre: str = info.get("name", "Sin nombre")
        descripcion: str = info.get("description", "")
        severidad_str: str = info.get("severity", "unknown").lower()
        template_id: str = resultado.get("template-id", resultado.get("template", ""))
        host: str = resultado.get("matched-at") or resultado.get("host") or objetivo

        # CVE si está disponible
        cve_raw = info.get("classification", {}).get("cve-id") or []
        cve: str | None = cve_raw[0] if isinstance(cve_raw, list) and cve_raw else None

        severidad = _SEVERIDAD_MAP.get(severidad_str, Severidad.MEDIA)

        # Construir vector de ataque desde nombre + descripción del template
        vector = f"{nombre}."
        if descripcion:
            vector += f" {descripcion[:300]}"

        try:
            return DatosRedTeam(
                origen=FuenteRedTeam.NUCLEI,
                activo_detectado=host,
                evidencia=f"nuclei:{template_id}",
                vector_ataque=vector,
                dificultad_explotacion=severidad,
                cve_relacionado=cve,
                metadatos={
                    "template_id": template_id,
                    "tags": info.get("tags", []),
                    "tipo": resultado.get("type", ""),
                    "matcher": resultado.get("matcher-name", ""),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "nuclei_normalizar_error", error=str(exc), resultado=str(resultado)[:200]
            )
            return None
