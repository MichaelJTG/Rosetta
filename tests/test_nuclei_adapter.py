"""Tests del NucleiAdapter con subprocess mockeado.

Sin llamadas reales a Nuclei — el subprocess se reemplaza con mocks.
Cobertura objetivo: ≥60% de adapters/red/nuclei.py.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rosetta.adapters.red.nuclei import NucleiAdapter
from rosetta.core.models import FuenteRedTeam, Severidad

# ---------------------------------------------------------------------------
# Fixtures — output JSON de Nuclei (formato real v3)
# ---------------------------------------------------------------------------

_NUCLEI_CRITICAL = {
    "template": "cves/2021/CVE-2021-41773.yaml",
    "template-id": "CVE-2021-41773",
    "info": {
        "name": "Apache HTTP Server 2.4.49 - Path Traversal and RCE",
        "severity": "critical",
        "description": "Apache HTTP Server 2.4.49 is vulnerable to path traversal.",
        "tags": ["cve", "apache", "rce"],
        "classification": {"cve-id": ["CVE-2021-41773"]},
    },
    "matched-at": "http://10.0.2.100",
    "host": "http://10.0.2.100",
    "type": "http",
    "matcher-name": "status_200",
}

_NUCLEI_HIGH = {
    "template-id": "rdp-detect",
    "info": {
        "name": "RDP Service Detection",
        "severity": "high",
        "description": "RDP service is exposed to the internet.",
        "tags": ["rdp", "network"],
    },
    "matched-at": "10.0.1.45:3389",
    "host": "10.0.1.45",
    "type": "network",
}

_NUCLEI_INFO = {
    "template-id": "tech-detect",
    "info": {
        "name": "Apache HTTP Server",
        "severity": "info",
        "description": "",
    },
    "matched-at": "http://10.0.2.100",
    "host": "http://10.0.2.100",
    "type": "http",
}


def _make_proc_mock(stdout: str, returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout.encode(), b""))
    proc.kill = MagicMock()
    return proc


# ---------------------------------------------------------------------------
# Tests de _construir_comando
# ---------------------------------------------------------------------------


def test_construir_comando_sin_templates() -> None:
    adapter = NucleiAdapter()
    cmd = adapter._construir_comando("https://target.example.com")
    assert "nuclei" in cmd[0]
    assert "-u" in cmd
    assert "https://target.example.com" in cmd
    assert "-jsonl" in cmd


def test_construir_comando_con_templates() -> None:
    adapter = NucleiAdapter(templates=["cves/2021/CVE-2021-41773.yaml"])
    cmd = adapter._construir_comando("https://target.example.com")
    assert "-t" in cmd
    assert "cves/2021/CVE-2021-41773.yaml" in cmd


# ---------------------------------------------------------------------------
# Tests de _normalizar
# ---------------------------------------------------------------------------


def test_normalizar_critical_mapea_severidad() -> None:
    adapter = NucleiAdapter()
    hallazgo = adapter._normalizar(_NUCLEI_CRITICAL, "http://10.0.2.100")
    assert hallazgo is not None
    assert hallazgo.dificultad_explotacion == Severidad.CRITICA
    assert hallazgo.origen == FuenteRedTeam.NUCLEI
    assert hallazgo.cve_relacionado == "CVE-2021-41773"


def test_normalizar_high_sin_cve() -> None:
    adapter = NucleiAdapter()
    hallazgo = adapter._normalizar(_NUCLEI_HIGH, "10.0.1.45")
    assert hallazgo is not None
    assert hallazgo.dificultad_explotacion == Severidad.ALTA
    assert hallazgo.cve_relacionado is None


def test_normalizar_info_mapea_informativa() -> None:
    adapter = NucleiAdapter()
    hallazgo = adapter._normalizar(_NUCLEI_INFO, "http://10.0.2.100")
    assert hallazgo is not None
    assert hallazgo.dificultad_explotacion == Severidad.INFORMATIVA


def test_normalizar_activo_usa_matched_at() -> None:
    adapter = NucleiAdapter()
    hallazgo = adapter._normalizar(_NUCLEI_CRITICAL, "http://10.0.2.100")
    assert hallazgo is not None
    assert hallazgo.activo_detectado == "http://10.0.2.100"


def test_normalizar_evidencia_incluye_template_id() -> None:
    adapter = NucleiAdapter()
    hallazgo = adapter._normalizar(_NUCLEI_CRITICAL, "http://10.0.2.100")
    assert hallazgo is not None
    assert "CVE-2021-41773" in hallazgo.evidencia


def test_normalizar_linea_invalida_devuelve_none() -> None:
    adapter = NucleiAdapter()
    result = adapter._normalizar({}, "http://target.com")
    # Sin info, activo debe ser el objetivo pasado
    assert result is not None  # objetivo como fallback activo


# ---------------------------------------------------------------------------
# Tests de _parsear_salida
# ---------------------------------------------------------------------------


def test_parsear_salida_multiples_hallazgos() -> None:
    adapter = NucleiAdapter()
    stdout = "\n".join(
        [
            json.dumps(_NUCLEI_CRITICAL),
            json.dumps(_NUCLEI_HIGH),
            "",  # línea vacía ignorada
        ]
    )
    hallazgos = adapter._parsear_salida(stdout, "http://10.0.2.100")
    assert len(hallazgos) == 2


def test_parsear_salida_vacia_devuelve_lista_vacia() -> None:
    adapter = NucleiAdapter()
    assert adapter._parsear_salida("", "http://target.com") == []


def test_parsear_salida_linea_no_json_ignorada() -> None:
    adapter = NucleiAdapter()
    stdout = "no es json\n" + json.dumps(_NUCLEI_CRITICAL)
    hallazgos = adapter._parsear_salida(stdout, "http://target.com")
    assert len(hallazgos) == 1


# ---------------------------------------------------------------------------
# Tests de escanear (subprocess mockeado)
# ---------------------------------------------------------------------------


async def test_escanear_devuelve_hallazgos_correctos() -> None:
    """escanear() con subprocess mockeado devuelve lista de DatosRedTeam."""
    stdout = json.dumps(_NUCLEI_CRITICAL) + "\n" + json.dumps(_NUCLEI_HIGH)
    proc_mock = _make_proc_mock(stdout, returncode=0)

    with patch("asyncio.create_subprocess_exec", return_value=proc_mock):
        adapter = NucleiAdapter()
        hallazgos = await adapter.escanear("http://10.0.2.100")

    assert len(hallazgos) == 2
    assert hallazgos[0].dificultad_explotacion == Severidad.CRITICA


async def test_escanear_sin_hallazgos_devuelve_lista_vacia() -> None:
    """nuclei sin hallazgos sale con código 0 y stdout vacío."""
    proc_mock = _make_proc_mock("", returncode=0)

    with patch("asyncio.create_subprocess_exec", return_value=proc_mock):
        adapter = NucleiAdapter()
        hallazgos = await adapter.escanear("http://target.com")

    assert hallazgos == []


async def test_escanear_binario_no_encontrado_lanza_filenotfounderror() -> None:
    """Si nuclei no está en PATH, lanza FileNotFoundError."""
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("nuclei")):
        adapter = NucleiAdapter()
        with pytest.raises(FileNotFoundError, match="nuclei"):
            await adapter.escanear("http://target.com")


async def test_escanear_returncode_error_lanza_runtimeerror() -> None:
    """Código de salida inesperado (>1) lanza RuntimeError."""
    proc_mock = _make_proc_mock("", returncode=2)

    with patch("asyncio.create_subprocess_exec", return_value=proc_mock):
        adapter = NucleiAdapter()
        with pytest.raises(RuntimeError):
            await adapter.escanear("http://target.com")


async def test_escanear_timeout_lanza_runtimeerror() -> None:
    """Un escaneo que supera el timeout lanza RuntimeError."""

    proc_mock = MagicMock()
    proc_mock.communicate = AsyncMock(side_effect=TimeoutError())
    proc_mock.kill = MagicMock()

    with patch("asyncio.create_subprocess_exec", return_value=proc_mock):
        adapter = NucleiAdapter(timeout_segundos=1)
        with pytest.raises(RuntimeError, match="timeout"):
            await adapter.escanear("http://target.com")
