"""Tests de la CLI Typer de ROSETTA (RF-18).

Los componentes caros o externos (LLM, RAG con modelo de embeddings, Neo4j,
binario de Nuclei) se sustituyen por dobles: la CLI se prueba como
orquestador de esos componentes, no los componentes en sí.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from rosetta import __version__
from rosetta.cli.main import app
from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    FuenteRedTeam,
    MarcoNormativo,
    Severidad,
)

runner = CliRunner()

_HALLAZGO = DatosRedTeam(
    origen=FuenteRedTeam.NUCLEI,
    activo_detectado="portal-citas.techserv.example",
    evidencia="https://portal-citas.techserv.example/.env",
    vector_ataque="Fichero .env expuesto",
    dificultad_explotacion=Severidad.BAJA,
)

_COMPLIANCE = DatosCompliance(
    marcos_aplicables=[MarcoNormativo.ENS_2022],
    controles_incumplidos=["mp.info.3"],
    cita_normativa="mp.info.3 Cifrado de la información",
    justificacion="Credenciales expuestas.",
    impacto_legal=Severidad.ALTA,
    accion_mitigacion="Retirar el fichero y rotar credenciales.",
    evidencia_auditoria="Nuclei.",
)


class _RagFalso:
    def __init__(self, **_: Any) -> None:
        self.ingestados: list[Any] = []

    def contar(self, _marco: Any = None) -> int:
        return 0

    def ingestar_corpus(self, fragmentos: list[Any]) -> int:
        self.ingestados = fragmentos
        return len(fragmentos)


class _TraductorFalso:
    fallar = False

    def __init__(self, **_: Any) -> None:
        pass

    async def traducir(self, _hallazgo: Any) -> DatosCompliance:
        if self.fallar:
            raise ValueError("el LLM no invocó la tool")
        return _COMPLIANCE


@pytest.fixture(autouse=True)
def _dobles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sustituye RAG, LLM y Traductor en sus módulos de origen."""
    monkeypatch.setattr("rosetta.core.rag.NormativaRAG", _RagFalso)
    monkeypatch.setattr("rosetta.llm.factory.get_llm_client", lambda: MagicMock())
    monkeypatch.setattr("rosetta.core.traductor.TraductorSimbiotico", _TraductorFalso)
    _TraductorFalso.fallar = False


@pytest.fixture
def hallazgo_json(tmp_path: Path) -> Path:
    ruta = tmp_path / "hallazgo.json"
    ruta.write_text(_HALLAZGO.model_dump_json(), encoding="utf-8")
    return ruta


def _grafo_falso() -> MagicMock:
    grafo = MagicMock()
    grafo.exportar_dossier.return_value = "# Dossier de prueba\n"
    return grafo


# ---------------------------------------------------------------------------
# version / translate
# ---------------------------------------------------------------------------


def test_version() -> None:
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0
    assert __version__ in r.output


def test_translate_ok(hallazgo_json: Path) -> None:
    r = runner.invoke(app, ["translate", str(hallazgo_json), "--marco", "ens_2022"])
    assert r.exit_code == 0, r.output
    assert "mp.info.3" in r.output


def test_translate_archivo_inexistente(tmp_path: Path) -> None:
    r = runner.invoke(app, ["translate", str(tmp_path / "no.json")])
    assert r.exit_code == 1
    assert "No se encontr" in r.output


def test_translate_json_invalido(tmp_path: Path) -> None:
    ruta = tmp_path / "malo.json"
    ruta.write_text(json.dumps({"origen": "nuclei"}), encoding="utf-8")
    r = runner.invoke(app, ["translate", str(ruta)])
    assert r.exit_code == 1
    assert "parsear" in r.output


def test_translate_marco_desconocido(hallazgo_json: Path) -> None:
    r = runner.invoke(app, ["translate", str(hallazgo_json), "--marco", "iso_9001"])
    assert r.exit_code == 1
    assert "Marco desconocido" in r.output


def test_translate_error_del_llm(hallazgo_json: Path) -> None:
    _TraductorFalso.fallar = True
    r = runner.invoke(app, ["translate", str(hallazgo_json), "--marco", "ens_2022"])
    assert r.exit_code == 1
    assert "Error en la traducci" in r.output


# ---------------------------------------------------------------------------
# load-corpus
# ---------------------------------------------------------------------------


def test_load_corpus_ens_indexa_las_medidas(tmp_path: Path) -> None:
    r = runner.invoke(app, ["load-corpus", "ens_2022", "corpus/ens", "--chroma", str(tmp_path)])
    assert r.exit_code == 0, r.output
    assert "fragmentos" in r.output


def test_load_corpus_marco_desconocido() -> None:
    r = runner.invoke(app, ["load-corpus", "iso_9001", "corpus/ens"])
    assert r.exit_code == 1


def test_load_corpus_carpeta_inexistente(tmp_path: Path) -> None:
    r = runner.invoke(app, ["load-corpus", "ens_2022", str(tmp_path / "nada")])
    assert r.exit_code == 1


def test_load_corpus_carpeta_vacia(tmp_path: Path) -> None:
    r = runner.invoke(app, ["load-corpus", "ens_2022", str(tmp_path)])
    assert r.exit_code == 1


# ---------------------------------------------------------------------------
# dossier
# ---------------------------------------------------------------------------


def test_dossier_exporta_a_fichero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    grafo = _grafo_falso()
    monkeypatch.setattr(
        "rosetta.core.graph.GrafoCorrelacion.desde_uri", classmethod(lambda _cls, *_a: grafo)
    )
    salida = tmp_path / "dossier.md"
    r = runner.invoke(app, ["dossier", "--marco", "ens_2022", "--salida", str(salida)])
    assert r.exit_code == 0, r.output
    assert salida.read_text(encoding="utf-8").startswith("# Dossier de prueba")
    grafo.cerrar.assert_called_once()


def test_dossier_sin_neo4j_sale_con_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _caido(_cls: Any, *_a: Any) -> Any:
        raise ConnectionError("Neo4j apagado")

    monkeypatch.setattr("rosetta.core.graph.GrafoCorrelacion.desde_uri", classmethod(_caido))
    r = runner.invoke(app, ["dossier"])
    assert r.exit_code == 1
    assert "Neo4j" in r.output


# ---------------------------------------------------------------------------
# scan (Nuclei sustituido por un doble)
# ---------------------------------------------------------------------------


def _nuclei_falso(resultado: list[DatosRedTeam] | Exception) -> type:
    class _Nuclei:
        def __init__(self, **_: Any) -> None:
            pass

        async def escanear(self, _objetivo: str) -> list[DatosRedTeam]:
            if isinstance(resultado, Exception):
                raise resultado
            return resultado

    return _Nuclei


def test_scan_dry_run_lista_hallazgos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("rosetta.adapters.red.nuclei.NucleiAdapter", _nuclei_falso([_HALLAZGO]))
    r = runner.invoke(app, ["scan", "lab.techserv.example", "--dry-run"])
    assert r.exit_code == 0, r.output
    assert "1 hallazgos" in r.output


def test_scan_completo_traduce_y_exporta(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    grafo = _grafo_falso()
    monkeypatch.setattr("rosetta.adapters.red.nuclei.NucleiAdapter", _nuclei_falso([_HALLAZGO]))
    monkeypatch.setattr(
        "rosetta.core.graph.GrafoCorrelacion.desde_uri", classmethod(lambda _cls, *_a: grafo)
    )
    salida = tmp_path / "scan.md"
    r = runner.invoke(
        app, ["scan", "lab.techserv.example", "--marco", "ens_2022", "--salida", str(salida)]
    )
    assert r.exit_code == 0, r.output
    assert "1/1" in r.output
    grafo.registrar_hallazgo.assert_called_once()
    assert salida.exists()


def test_scan_sin_hallazgos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("rosetta.adapters.red.nuclei.NucleiAdapter", _nuclei_falso([]))
    r = runner.invoke(app, ["scan", "lab.techserv.example"])
    assert r.exit_code == 0
    assert "No se encontraron" in r.output


def test_scan_sin_binario_nuclei(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "rosetta.adapters.red.nuclei.NucleiAdapter",
        _nuclei_falso(FileNotFoundError("Binario 'nuclei' no encontrado")),
    )
    r = runner.invoke(app, ["scan", "lab.techserv.example"])
    assert r.exit_code == 1


def test_scan_sensor_desconocido() -> None:
    r = runner.invoke(app, ["scan", "lab.techserv.example", "--sensor", "amass"])
    assert r.exit_code == 1
    assert "Sensor desconocido" in r.output


def test_scan_marco_desconocido() -> None:
    r = runner.invoke(app, ["scan", "lab.techserv.example", "--marco", "iso_9001"])
    assert r.exit_code == 1


# ---------------------------------------------------------------------------
# detect-drift
# ---------------------------------------------------------------------------


def test_detect_drift_con_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    resultado = SimpleNamespace(
        drift_detectado=True,
        impacto=Severidad.ALTA,
        descripcion_drift="Las cuentas inactivas no se desactivan a los 90 días.",
        fragmento_afectado="Las cuentas se revisan trimestralmente.",
        redaccion_propuesta="Desactivación automática a los 90 días.",
        controles_afectados=["op.acc.1"],
    )

    class _Detector:
        def __init__(self, **_: Any) -> None:
            pass

        async def detectar_drift(self, *_a: Any) -> Any:
            return resultado

    monkeypatch.setattr("rosetta.core.drift.DriftDetector", _Detector)
    proc = tmp_path / "PRO-IAM-001.md"
    proc.write_text("Las cuentas se revisan trimestralmente.", encoding="utf-8")
    r = runner.invoke(app, ["detect-drift", str(proc), "-o", "12 cuentas inactivas|3 admins"])
    assert r.exit_code == 0, r.output
    assert "DRIFT DETECTADO" in r.output
    assert "op.acc.1" in r.output


def test_detect_drift_procedimiento_inexistente(tmp_path: Path) -> None:
    r = runner.invoke(app, ["detect-drift", str(tmp_path / "no.md"), "-o", "obs"])
    assert r.exit_code == 1
