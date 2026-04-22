"""Orquestador de auditoría automática — Modo A de ROSETTA.

Coordina la ejecución paralela de adaptadores Red Team contra un conjunto
de objetivos autorizados. Incluye controles de seguridad obligatorios:

  - Declaración de alcance autorizado (campo obligatorio, mínimo 10 chars).
  - Lista negra global (IPs privadas, localhost) y lista negra personalizada.
  - Rate limiting por semáforo asyncio (max_concurrencia).
  - Callback de progreso en tiempo real para alimentar WebSocket.
"""

from __future__ import annotations

import asyncio
import ipaddress
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from rosetta.adapters.base import RedTeamAdapter
from rosetta.adapters.red.nmap import NmapAdapter
from rosetta.adapters.red.nuclei import NucleiAdapter
from rosetta.core.models import DatosRedTeam

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Lista negra global — objetivos que NUNCA se deben escanear
# ---------------------------------------------------------------------------

_RANGOS_PROHIBIDOS: list[str] = [
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "169.254.0.0/16",
    "::1/128",
    "fc00::/7",
]

_REDES_PROHIBIDAS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network(r) for r in _RANGOS_PROHIBIDOS
]

_HOSTS_PROHIBIDOS: frozenset[str] = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


# ---------------------------------------------------------------------------
# Tipos de datos
# ---------------------------------------------------------------------------


@dataclass
class AlcanceAuditoria:
    """Configuración del alcance de una auditoría automática.

    Atributos:
        objetivos: Lista de URLs, IPs o dominios a auditar.
        adaptadores: Nombres de los adaptadores a usar ("nuclei", "nmap").
        max_concurrencia: Máximo de tareas concurrentes (rate limiting).
        lista_negra: Términos adicionales excluidos (substring match).
        declaracion_alcance: Texto obligatorio de autorización para el escaneo.
    """

    objetivos: list[str]
    adaptadores: list[str] = field(default_factory=lambda: ["nuclei"])
    max_concurrencia: int = 3
    lista_negra: list[str] = field(default_factory=list)
    declaracion_alcance: str = ""


@dataclass
class ProgresoAuditoria:
    """Evento de progreso emitido durante la ejecución de la auditoría."""

    audit_id: str
    tipo: str  # "inicio" | "escaneo_inicio" | "escaneo_fin" | "error" | "fin"
    mensaje: str
    objetivo: str | None = None
    adaptador: str | None = None
    hallazgos_acumulados: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "tipo": self.tipo,
            "mensaje": self.mensaje,
            "objetivo": self.objetivo,
            "adaptador": self.adaptador,
            "hallazgos_acumulados": self.hallazgos_acumulados,
            "timestamp": self.timestamp,
        }


@dataclass
class ResultadoAuditoria:
    """Resultado completo de la auditoría automática."""

    audit_id: str
    estado: str  # "en_curso" | "completado" | "error"
    objetivos_procesados: list[str]
    hallazgos: list[DatosRedTeam]
    errores: list[str]
    inicio: datetime
    fin: datetime | None = None

    @property
    def total_hallazgos(self) -> int:
        return len(self.hallazgos)


# ---------------------------------------------------------------------------
# Tipo del callback de progreso
# ---------------------------------------------------------------------------

ProgresoCallback = Callable[[ProgresoAuditoria], Awaitable[None]]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class Orchestrator:
    """Orquestador de auditoría Red Team — Modo A.

    Ejecuta adaptadores en paralelo usando asyncio.Semaphore para rate limiting.
    Valida el alcance antes de comenzar y reporta progreso via callback.

    Args:
        adaptadores: Dict {nombre → instancia} de adaptadores disponibles.
            Si None, se crean instancias por defecto de nuclei y nmap.
        nuclei_bin: Ruta al binario nuclei (usado si adaptadores es None).
        nmap_bin: Ruta al binario nmap (usado si adaptadores es None).
    """

    ADAPTADORES_SOPORTADOS: frozenset[str] = frozenset({"nuclei", "nmap"})

    def __init__(
        self,
        adaptadores: dict[str, RedTeamAdapter] | None = None,
        nuclei_bin: str = "nuclei",
        nmap_bin: str = "nmap",
    ) -> None:
        if adaptadores is not None:
            self._adaptadores = adaptadores
        else:
            self._adaptadores = {
                "nuclei": NucleiAdapter(binario=nuclei_bin),
                "nmap": NmapAdapter(binario=nmap_bin),
            }

    async def ejecutar(
        self,
        alcance: AlcanceAuditoria,
        on_progreso: ProgresoCallback | None = None,
        audit_id: str | None = None,
    ) -> ResultadoAuditoria:
        """Ejecuta la auditoría según el alcance configurado.

        Args:
            alcance: Configuración del alcance (objetivos, adaptadores, etc.).
            on_progreso: Callback async llamado en cada evento de progreso.
            audit_id: ID de la auditoría (se genera si no se proporciona).

        Returns:
            ResultadoAuditoria con todos los hallazgos y errores.

        Raises:
            ValueError: Si el alcance no pasa la validación de seguridad.
        """
        audit_id = audit_id or uuid.uuid4().hex[:12]
        self._validar_alcance(alcance)

        resultado = ResultadoAuditoria(
            audit_id=audit_id,
            estado="en_curso",
            objetivos_procesados=[],
            hallazgos=[],
            errores=[],
            inicio=datetime.utcnow(),
        )

        await self._emit(
            on_progreso,
            ProgresoAuditoria(
                audit_id=audit_id,
                tipo="inicio",
                mensaje=(
                    f"Auditoría iniciada: {len(alcance.objetivos)} objetivo(s), "
                    f"adaptadores: {', '.join(alcance.adaptadores)}"
                ),
            ),
        )

        sem = asyncio.Semaphore(alcance.max_concurrencia)
        tareas = [
            self._escanear_con_semaforo(sem, objetivo, adaptador_nombre, audit_id, on_progreso)
            for objetivo in alcance.objetivos
            for adaptador_nombre in alcance.adaptadores
            if adaptador_nombre in self._adaptadores
        ]

        resultados_tareas = await asyncio.gather(*tareas, return_exceptions=True)

        for tarea_resultado in resultados_tareas:
            if isinstance(tarea_resultado, Exception):
                resultado.errores.append(str(tarea_resultado))
            elif isinstance(tarea_resultado, tuple):
                objetivo_ok, hallazgos_tarea, errores_tarea = tarea_resultado
                resultado.hallazgos.extend(hallazgos_tarea)
                resultado.errores.extend(errores_tarea)
                if objetivo_ok not in resultado.objetivos_procesados:
                    resultado.objetivos_procesados.append(objetivo_ok)

        resultado.estado = "completado"
        resultado.fin = datetime.utcnow()

        await self._emit(
            on_progreso,
            ProgresoAuditoria(
                audit_id=audit_id,
                tipo="fin",
                mensaje=(
                    f"Auditoría completada: {resultado.total_hallazgos} hallazgo(s), "
                    f"{len(resultado.errores)} error(es)."
                ),
                hallazgos_acumulados=resultado.total_hallazgos,
            ),
        )

        logger.info(
            "auditoria_completada",
            audit_id=audit_id,
            hallazgos=resultado.total_hallazgos,
            errores=len(resultado.errores),
        )
        return resultado

    async def _escanear_con_semaforo(
        self,
        sem: asyncio.Semaphore,
        objetivo: str,
        adaptador_nombre: str,
        audit_id: str,
        on_progreso: ProgresoCallback | None,
    ) -> tuple[str, list[DatosRedTeam], list[str]]:
        """Ejecuta un escaneo dentro del semáforo de rate limiting."""
        async with sem:
            return await self._escanear_objetivo(objetivo, adaptador_nombre, audit_id, on_progreso)

    async def _escanear_objetivo(
        self,
        objetivo: str,
        adaptador_nombre: str,
        audit_id: str,
        on_progreso: ProgresoCallback | None,
    ) -> tuple[str, list[DatosRedTeam], list[str]]:
        """Ejecuta un adaptador contra un objetivo y emite progreso."""
        adaptador = self._adaptadores[adaptador_nombre]
        errores: list[str] = []

        await self._emit(
            on_progreso,
            ProgresoAuditoria(
                audit_id=audit_id,
                tipo="escaneo_inicio",
                mensaje=f"[{adaptador_nombre}] Iniciando escaneo de {objetivo}",
                objetivo=objetivo,
                adaptador=adaptador_nombre,
            ),
        )

        hallazgos: list[DatosRedTeam] = []
        try:
            hallazgos = await adaptador.escanear(objetivo)
        except Exception as exc:  # noqa: BLE001
            msg = f"[{adaptador_nombre}] Error en {objetivo}: {exc}"
            errores.append(msg)
            logger.warning(
                "orchestrator_adapter_error",
                adaptador=adaptador_nombre,
                objetivo=objetivo,
                error=str(exc),
            )

        await self._emit(
            on_progreso,
            ProgresoAuditoria(
                audit_id=audit_id,
                tipo="escaneo_fin" if not errores else "error",
                mensaje=(
                    f"[{adaptador_nombre}] {objetivo}: {len(hallazgos)} hallazgo(s)"
                    if not errores
                    else errores[-1]
                ),
                objetivo=objetivo,
                adaptador=adaptador_nombre,
                hallazgos_acumulados=len(hallazgos),
            ),
        )

        return objetivo, hallazgos, errores

    # ------------------------------------------------------------------
    # Validación de alcance
    # ------------------------------------------------------------------

    def _validar_alcance(self, alcance: AlcanceAuditoria) -> None:
        """Valida el alcance antes de iniciar cualquier escaneo.

        Raises:
            ValueError: Con descripción del problema de seguridad detectado.
        """
        if len(alcance.declaracion_alcance.strip()) < 10:
            raise ValueError(
                "La declaración de alcance autorizado es obligatoria y debe tener "
                "al menos 10 caracteres."
            )

        if not alcance.objetivos:
            raise ValueError("El alcance debe incluir al menos un objetivo.")

        desconocidos = set(alcance.adaptadores) - self.ADAPTADORES_SOPORTADOS
        if desconocidos:
            raise ValueError(f"Adaptadores no soportados: {', '.join(sorted(desconocidos))}")

        lista_negra_efectiva = list(_HOSTS_PROHIBIDOS) + [lb.lower() for lb in alcance.lista_negra]

        for objetivo in alcance.objetivos:
            objetivo_limpio = objetivo.lower().strip()
            for prohibido in lista_negra_efectiva:
                if prohibido in objetivo_limpio:
                    raise ValueError(f"El objetivo '{objetivo}' está en la lista negra.")
            self._validar_no_ip_privada(objetivo_limpio, objetivo)

    def _validar_no_ip_privada(self, objetivo_limpio: str, objetivo_original: str) -> None:
        """Comprueba que el objetivo no sea una dirección IP privada/reservada."""
        candidato = objetivo_limpio
        for prefix in ("http://", "https://"):
            if candidato.startswith(prefix):
                candidato = candidato[len(prefix) :]
        candidato = candidato.split("/")[0].split(":")[0]

        try:
            addr = ipaddress.ip_address(candidato)
        except ValueError:
            return  # No es una IP — es un hostname, dejarlo pasar

        for red in _REDES_PROHIBIDAS:
            if isinstance(red, ipaddress.IPv4Network) and isinstance(addr, ipaddress.IPv4Address):
                if addr in red:
                    raise ValueError(
                        f"El objetivo '{objetivo_original}' es una dirección IP "
                        "privada/reservada y no puede ser escaneado."
                    )
            elif (
                isinstance(red, ipaddress.IPv6Network)
                and isinstance(addr, ipaddress.IPv6Address)
                and addr in red
            ):
                raise ValueError(
                    f"El objetivo '{objetivo_original}' es una dirección IPv6 "
                    "privada/reservada y no puede ser escaneado."
                )

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    async def _emit(callback: ProgresoCallback | None, evento: ProgresoAuditoria) -> None:
        """Llama al callback de progreso de forma segura (best-effort)."""
        if callback is None:
            return
        try:
            await callback(evento)
        except Exception as exc:  # noqa: BLE001
            logger.warning("orchestrator_callback_error", error=str(exc))
