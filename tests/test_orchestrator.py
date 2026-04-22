"""Tests para core/orchestrator.py y adapters/red/nmap.py — FASE 3 Modo A."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rosetta.adapters.red.nmap import NmapAdapter
from rosetta.core.models import DatosRedTeam, FuenteRedTeam, Severidad
from rosetta.core.orchestrator import (
    AlcanceAuditoria,
    Orchestrator,
    ProgresoAuditoria,
    ResultadoAuditoria,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_alcance(
    objetivos: list[str] | None = None,
    adaptadores: list[str] | None = None,
    declaracion: str = "Autorizado por CISO para pruebas de staging 2026",
    lista_negra: list[str] | None = None,
) -> AlcanceAuditoria:
    return AlcanceAuditoria(
        objetivos=objetivos or ["https://ejemplo.com"],
        adaptadores=adaptadores or ["nuclei"],
        declaracion_alcance=declaracion,
        lista_negra=lista_negra or [],
    )


def _make_dato_red() -> DatosRedTeam:
    return DatosRedTeam(
        origen=FuenteRedTeam.NMAP,
        activo_detectado="1.2.3.4:22/tcp",
        evidencia="nmap:port:22/tcp:ssh",
        vector_ataque="Puerto 22/tcp abierto: servicio ssh.",
        dificultad_explotacion=Severidad.MEDIA,
    )


# ---------------------------------------------------------------------------
# AlcanceAuditoria — validación de seguridad
# ---------------------------------------------------------------------------


class TestValidarAlcance:
    def test_declaracion_vacia_rechazada(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="declaraci"):
            orch._validar_alcance(_make_alcance(declaracion=""))

    def test_declaracion_corta_rechazada(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="10 caracteres"):
            orch._validar_alcance(_make_alcance(declaracion="test"))

    def test_sin_objetivos_rechazado(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        alcance = AlcanceAuditoria(
            objetivos=[],
            adaptadores=["nuclei"],
            declaracion_alcance="Autorizado por CISO para pruebas de staging 2026",
        )
        with pytest.raises(ValueError, match="al menos un objetivo"):
            orch._validar_alcance(alcance)

    def test_adaptador_desconocido_rechazado(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="burpsuite"):
            orch._validar_alcance(_make_alcance(adaptadores=["nuclei", "burpsuite"]))

    def test_ip_privada_clase_c_rechazada(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="privada"):
            orch._validar_alcance(_make_alcance(objetivos=["192.168.1.1"]))

    def test_ip_privada_clase_a_rechazada(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="privada"):
            orch._validar_alcance(_make_alcance(objetivos=["10.0.0.1"]))

    def test_ip_loopback_rechazada(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="lista negra"):
            orch._validar_alcance(_make_alcance(objetivos=["127.0.0.1"]))

    def test_localhost_en_url_rechazado(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="lista negra"):
            orch._validar_alcance(_make_alcance(objetivos=["http://localhost/app"]))

    def test_lista_negra_personalizada_bloquea(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="lista negra"):
            orch._validar_alcance(
                _make_alcance(
                    objetivos=["https://interno.empresa.com"],
                    lista_negra=["interno.empresa.com"],
                )
            )

    def test_objetivo_publico_valido(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        orch._validar_alcance(_make_alcance(objetivos=["https://ejemplo.com"]))

    def test_ip_publica_valida(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        orch._validar_alcance(_make_alcance(objetivos=["8.8.8.8"]))

    def test_url_con_ip_privada_en_path_rechazada(self) -> None:
        orch = Orchestrator(adaptadores={"nuclei": MagicMock()})
        with pytest.raises(ValueError, match="privada"):
            orch._validar_alcance(_make_alcance(objetivos=["https://172.16.0.1/api"]))


# ---------------------------------------------------------------------------
# Orchestrator.ejecutar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOrchestratorEjecutar:
    async def test_retorna_resultado_completado(self) -> None:
        mock_adapter = AsyncMock()
        mock_adapter.escanear.return_value = [_make_dato_red()]
        orch = Orchestrator(adaptadores={"nuclei": mock_adapter})

        resultado = await orch.ejecutar(_make_alcance())

        assert isinstance(resultado, ResultadoAuditoria)
        assert resultado.estado == "completado"
        assert resultado.total_hallazgos == 1
        assert resultado.fin is not None

    async def test_multiples_objetivos_llama_adapter_por_cada_uno(self) -> None:
        mock_adapter = AsyncMock()
        mock_adapter.escanear.return_value = [_make_dato_red()]
        orch = Orchestrator(adaptadores={"nuclei": mock_adapter})
        alcance = _make_alcance(objetivos=["https://a.com", "https://b.com"])

        resultado = await orch.ejecutar(alcance)

        assert resultado.total_hallazgos == 2
        assert mock_adapter.escanear.call_count == 2

    async def test_callback_progreso_recibe_inicio_y_fin(self) -> None:
        mock_adapter = AsyncMock()
        mock_adapter.escanear.return_value = []
        orch = Orchestrator(adaptadores={"nuclei": mock_adapter})
        eventos: list[ProgresoAuditoria] = []

        async def capturar(e: ProgresoAuditoria) -> None:
            eventos.append(e)

        await orch.ejecutar(_make_alcance(), on_progreso=capturar)

        tipos = {e.tipo for e in eventos}
        assert "inicio" in tipos
        assert "fin" in tipos

    async def test_sin_callback_no_falla(self) -> None:
        mock_adapter = AsyncMock()
        mock_adapter.escanear.return_value = []
        orch = Orchestrator(adaptadores={"nuclei": mock_adapter})

        resultado = await orch.ejecutar(_make_alcance(), on_progreso=None)

        assert resultado.estado == "completado"

    async def test_error_en_adapter_va_a_errores_no_aborta(self) -> None:
        mock_adapter = AsyncMock()
        mock_adapter.escanear.side_effect = RuntimeError("timeout de red")
        orch = Orchestrator(adaptadores={"nuclei": mock_adapter})

        resultado = await orch.ejecutar(_make_alcance())

        assert resultado.estado == "completado"
        assert len(resultado.errores) == 1
        assert "timeout de red" in resultado.errores[0]

    async def test_alcance_invalido_lanza_antes_de_escanear(self) -> None:
        mock_adapter = AsyncMock()
        orch = Orchestrator(adaptadores={"nuclei": mock_adapter})
        with pytest.raises(ValueError):
            await orch.ejecutar(_make_alcance(declaracion="corta"))
        mock_adapter.escanear.assert_not_called()

    async def test_audit_id_personalizado_se_preserva(self) -> None:
        mock_adapter = AsyncMock()
        mock_adapter.escanear.return_value = []
        orch = Orchestrator(adaptadores={"nuclei": mock_adapter})

        resultado = await orch.ejecutar(_make_alcance(), audit_id="mi-audit-abc")

        assert resultado.audit_id == "mi-audit-abc"

    async def test_multiples_adaptadores_acumulan_hallazgos(self) -> None:
        nmap_mock = AsyncMock()
        nmap_mock.escanear.return_value = [_make_dato_red()]
        nuclei_mock = AsyncMock()
        nuclei_mock.escanear.return_value = [_make_dato_red(), _make_dato_red()]
        orch = Orchestrator(adaptadores={"nmap": nmap_mock, "nuclei": nuclei_mock})

        resultado = await orch.ejecutar(_make_alcance(adaptadores=["nmap", "nuclei"]))

        assert resultado.total_hallazgos == 3

    async def test_adaptador_no_en_lista_ignorado_sin_error(self) -> None:
        nuclei_mock = AsyncMock()
        nuclei_mock.escanear.return_value = [_make_dato_red()]
        orch = Orchestrator(adaptadores={"nuclei": nuclei_mock})
        # "nmap" está en ADAPTADORES_SOPORTADOS pero no en _adaptadores
        alcance = _make_alcance(adaptadores=["nuclei", "nmap"])

        resultado = await orch.ejecutar(alcance)

        assert resultado.total_hallazgos == 1  # solo nuclei ejecutó


# ---------------------------------------------------------------------------
# NmapAdapter._parsear_xml
# ---------------------------------------------------------------------------

_XML_UN_PUERTO = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="1.2.3.4" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="8.9"/>
      </port>
    </ports>
  </host>
</nmaprun>"""

_XML_PUERTO_CRITICO_SMB = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="1.2.3.4" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="445">
        <state state="open"/>
        <service name="microsoft-ds"/>
      </port>
    </ports>
  </host>
</nmaprun>"""

_XML_PUERTO_CERRADO = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="1.2.3.4" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="closed"/>
        <service name="http"/>
      </port>
    </ports>
  </host>
</nmaprun>"""

_XML_VACIO = """<?xml version="1.0"?><nmaprun></nmaprun>"""


class TestNmapAdapterParsearXml:
    def test_un_puerto_abierto_genera_hallazgo(self) -> None:
        adapter = NmapAdapter()
        hallazgos = adapter._parsear_xml(_XML_UN_PUERTO, "1.2.3.4")

        assert len(hallazgos) == 1
        h = hallazgos[0]
        assert h.origen == FuenteRedTeam.NMAP
        assert "22" in h.activo_detectado
        assert h.metadatos["port"] == 22
        assert h.metadatos["service"] == "ssh"
        assert h.metadatos["product"] == "OpenSSH"

    def test_puerto_445_severidad_critica(self) -> None:
        adapter = NmapAdapter()
        hallazgos = adapter._parsear_xml(_XML_PUERTO_CRITICO_SMB, "1.2.3.4")

        assert len(hallazgos) == 1
        assert hallazgos[0].dificultad_explotacion == Severidad.CRITICA

    def test_puerto_cerrado_ignorado(self) -> None:
        adapter = NmapAdapter()
        hallazgos = adapter._parsear_xml(_XML_PUERTO_CERRADO, "1.2.3.4")

        assert hallazgos == []

    def test_xml_vacio_retorna_lista_vacia(self) -> None:
        adapter = NmapAdapter()
        assert adapter._parsear_xml(_XML_VACIO, "1.2.3.4") == []

    def test_xml_invalido_retorna_lista_vacia(self) -> None:
        adapter = NmapAdapter()
        assert adapter._parsear_xml("esto no es xml <<<", "1.2.3.4") == []

    def test_texto_vacio_retorna_lista_vacia(self) -> None:
        adapter = NmapAdapter()
        assert adapter._parsear_xml("", "objetivo") == []

    def test_fallback_a_objetivo_cuando_no_hay_address(self) -> None:
        xml = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http"/>
      </port>
    </ports>
  </host>
</nmaprun>"""
        adapter = NmapAdapter()
        hallazgos = adapter._parsear_xml(xml, "mi-objetivo")

        assert len(hallazgos) == 1
        assert "mi-objetivo" in hallazgos[0].activo_detectado

    def test_vector_ataque_truncado_a_300_chars(self) -> None:
        xml = _XML_UN_PUERTO
        adapter = NmapAdapter()
        hallazgos = adapter._parsear_xml(xml, "1.2.3.4")

        assert len(hallazgos[0].vector_ataque) <= 300


# ---------------------------------------------------------------------------
# NmapAdapter.escanear — subprocess mock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestNmapAdapterEscanear:
    async def test_escanear_llama_nmap_y_parsea_xml(self) -> None:
        adapter = NmapAdapter()
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(_XML_UN_PUERTO.encode(), b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            hallazgos = await adapter.escanear("1.2.3.4")

        assert len(hallazgos) == 1
        assert hallazgos[0].metadatos["port"] == 22

    async def test_escanear_binario_no_encontrado_lanza(self) -> None:
        adapter = NmapAdapter(binario="nmap-no-existe")
        with (
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=FileNotFoundError("not found"),
            ),
            pytest.raises(FileNotFoundError, match="nmap-no-existe"),
        ):
            await adapter.escanear("1.2.3.4")

    async def test_escanear_timeout_lanza_runtime(self) -> None:
        adapter = NmapAdapter(timeout_segundos=1)
        mock_proc = AsyncMock()
        mock_proc.kill = MagicMock()
        mock_proc.communicate = AsyncMock(side_effect=TimeoutError())

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(RuntimeError, match="timeout"),
        ):
            await adapter.escanear("1.2.3.4")

    async def test_escanear_codigo_5_lanza_runtime(self) -> None:
        adapter = NmapAdapter()
        mock_proc = AsyncMock()
        mock_proc.returncode = 5
        mock_proc.communicate = AsyncMock(return_value=(b"", b"nmap error"))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(RuntimeError, match="código 5"),
        ):
            await adapter.escanear("1.2.3.4")

    async def test_escanear_codigo_1_valido_sin_hosts(self) -> None:
        """Código 1 = nmap sin hosts activos — no es error."""
        adapter = NmapAdapter()
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(_XML_VACIO.encode(), b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            hallazgos = await adapter.escanear("192.0.2.1")

        assert hallazgos == []
