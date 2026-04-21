"""Tests del ReportGenerator: generación de informes MD y PDF.

Cobertura objetivo: 80% de core/report_generator.py
Tests unitarios — no requieren LLM ni ChromaDB ni Neo4j.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from rosetta.core.models import (
    DatosCompliance,
    DatosRedTeam,
    FuenteRedTeam,
    HallazgoMaestro,
    MarcoNormativo,
    Severidad,
)
from rosetta.core.report_generator import ReportConfig, ReportGenerator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _hacer_hallazgo(
    idx: int = 1,
    severidad: Severidad = Severidad.ALTA,
) -> HallazgoMaestro:
    """Construye un HallazgoMaestro sintético para tests."""
    red = DatosRedTeam(
        origen=FuenteRedTeam.NUCLEI,
        activo_detectado=f"https://example{idx}.com/login",
        evidencia=f"https://evidence{idx}.internal/screenshot.png",
        vector_ataque="Credencial expuesta en respuesta HTTP 200",
        dificultad_explotacion=Severidad.BAJA,
        cve_relacionado=None,
    )
    compliance = DatosCompliance(
        marcos_aplicables=[MarcoNormativo.ISO_27001_2022, MarcoNormativo.ENS_2022],
        controles_incumplidos=["A.8.24", "A.8.5", "mp.si.2"],
        cita_normativa=(
            "ISO 27001:2022 A.8.24 — Se deben definir y aplicar reglas sobre "
            "el uso de controles criptograficos."
        ),
        justificacion="La credencial viaja en texto plano sin cifrado TLS adecuado.",
        impacto_legal=severidad,
        accion_mitigacion="Habilitar HSTS, revisar configuracion TLS, rotar credenciales.",
        evidencia_auditoria=f"Screenshot capturado el {datetime.now().isoformat()}",
    )
    return HallazgoMaestro(
        id_hallazgo=f"SEC-TEST{idx:04d}",
        red_team_data=red,
        compliance_data=compliance,
    )


@pytest.fixture
def hallazgos_basicos() -> list[HallazgoMaestro]:
    return [
        _hacer_hallazgo(1, Severidad.CRITICA),
        _hacer_hallazgo(2, Severidad.ALTA),
        _hacer_hallazgo(3, Severidad.MEDIA),
    ]


@pytest.fixture
def generador_default() -> ReportGenerator:
    return ReportGenerator()


@pytest.fixture
def generador_con_cliente() -> ReportGenerator:
    config = ReportConfig(
        nombre_cliente="Acme Corp S.A.",
        autor="Equipo de Auditoria ROSETTA",
        confidencialidad="ESTRICTAMENTE CONFIDENCIAL",
    )
    return ReportGenerator(config)


# ---------------------------------------------------------------------------
# Tests ReportConfig
# ---------------------------------------------------------------------------


def test_config_defaults() -> None:
    """ReportConfig sin parámetros usa valores ROSETTA por defecto."""
    cfg = ReportConfig()
    assert cfg.nombre_cliente is None
    assert cfg.autor == "ROSETTA Audit Platform"
    assert cfg.confidencialidad == "CONFIDENCIAL"
    assert cfg.logo_cliente is None


def test_config_con_cliente() -> None:
    """ReportConfig acepta nombre de cliente y confidencialidad personalizados."""
    cfg = ReportConfig(nombre_cliente="Empresa X", confidencialidad="SECRETO")
    assert cfg.nombre_cliente == "Empresa X"
    assert cfg.confidencialidad == "SECRETO"


def test_config_logo_como_path(tmp_path: Path) -> None:
    """El logo se convierte automáticamente a Path."""
    logo = tmp_path / "logo.png"
    logo.touch()
    cfg = ReportConfig(logo_cliente=str(logo))
    assert isinstance(cfg.logo_cliente, Path)
    assert cfg.logo_cliente == logo


# ---------------------------------------------------------------------------
# Tests generación Markdown
# ---------------------------------------------------------------------------


def test_markdown_crea_archivo(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """generar_markdown crea el archivo .md en la ruta indicada."""
    md = generador_default.generar_markdown(hallazgos_basicos, tmp_path)
    assert md.exists()
    assert md.suffix == ".md"


def test_markdown_contiene_ids_hallazgos(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """El informe Markdown incluye los IDs de todos los hallazgos."""
    md = generador_default.generar_markdown(hallazgos_basicos, tmp_path)
    contenido = md.read_text(encoding="utf-8")
    for h in hallazgos_basicos:
        assert h.id_hallazgo in contenido


def test_markdown_incluye_marca_rosetta(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """El informe Markdown menciona ROSETTA."""
    md = generador_default.generar_markdown(hallazgos_basicos, tmp_path)
    contenido = md.read_text(encoding="utf-8")
    assert "ROSETTA" in contenido


def test_markdown_incluye_nombre_cliente(
    generador_con_cliente: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """Cuando hay cliente configurado, aparece en el informe."""
    md = generador_con_cliente.generar_markdown(hallazgos_basicos, tmp_path)
    contenido = md.read_text(encoding="utf-8")
    assert "Acme Corp S.A." in contenido


def test_markdown_incluye_confidencialidad(
    generador_con_cliente: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """La clasificación de confidencialidad aparece en el informe."""
    md = generador_con_cliente.generar_markdown(hallazgos_basicos, tmp_path)
    contenido = md.read_text(encoding="utf-8")
    assert "ESTRICTAMENTE CONFIDENCIAL" in contenido


def test_markdown_incluye_citas_normativas(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """El detalle de hallazgos incluye citas normativas."""
    md = generador_default.generar_markdown(hallazgos_basicos, tmp_path)
    contenido = md.read_text(encoding="utf-8")
    assert "A.8.24" in contenido


def test_markdown_lista_vacia(
    generador_default: ReportGenerator,
    tmp_path: Path,
) -> None:
    """Con lista vacía de hallazgos se genera un informe válido."""
    md = generador_default.generar_markdown([], tmp_path)
    assert md.exists()
    contenido = md.read_text(encoding="utf-8")
    assert "ROSETTA" in contenido
    assert "Total hallazgos | **0**" in contenido


def test_markdown_nombre_base_personalizado(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """Se respeta el nombre_base personalizado."""
    md = generador_default.generar_markdown(hallazgos_basicos, tmp_path, nombre_base="mi_informe")
    assert md.name == "mi_informe.md"


# ---------------------------------------------------------------------------
# Tests generación PDF
# ---------------------------------------------------------------------------


def test_pdf_crea_archivo(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """generar() crea el archivo .pdf."""
    _, pdf = generador_default.generar(hallazgos_basicos, tmp_path)
    assert pdf.exists()
    assert pdf.suffix == ".pdf"


def test_pdf_no_vacio(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """El PDF generado no está vacío."""
    _, pdf = generador_default.generar(hallazgos_basicos, tmp_path)
    assert pdf.stat().st_size > 0


def test_pdf_empieza_con_magic_number(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """El PDF generado empieza con el magic number %PDF."""
    _, pdf = generador_default.generar(hallazgos_basicos, tmp_path)
    assert pdf.read_bytes()[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Tests generar() — retorna ambos paths
# ---------------------------------------------------------------------------


def test_generar_devuelve_dos_paths(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """generar() retorna una tupla (md_path, pdf_path)."""
    result = generador_default.generar(hallazgos_basicos, tmp_path)
    assert len(result) == 2
    md, pdf = result
    assert md.suffix == ".md"
    assert pdf.suffix == ".pdf"


def test_generar_crea_directorio(
    generador_default: ReportGenerator,
    hallazgos_basicos: list[HallazgoMaestro],
    tmp_path: Path,
) -> None:
    """generar() crea el directorio de salida si no existe."""
    nueva_ruta = tmp_path / "subdir" / "reports"
    assert not nueva_ruta.exists()
    generador_default.generar(hallazgos_basicos, nueva_ruta)
    assert nueva_ruta.exists()


# ---------------------------------------------------------------------------
# Tests métricas (via markdown)
# ---------------------------------------------------------------------------


def test_metricas_severidad_en_markdown(
    generador_default: ReportGenerator,
    tmp_path: Path,
) -> None:
    """Las métricas de severidad se reflejan correctamente en el resumen."""
    hallazgos = [
        _hacer_hallazgo(1, Severidad.CRITICA),
        _hacer_hallazgo(2, Severidad.CRITICA),
        _hacer_hallazgo(3, Severidad.ALTA),
    ]
    md = generador_default.generar_markdown(hallazgos, tmp_path)
    contenido = md.read_text(encoding="utf-8")
    assert "Total hallazgos | **3**" in contenido
    assert "Críticos | **2**" in contenido
    assert "Altos | **1**" in contenido


def test_metricas_marcos_afectados(
    generador_default: ReportGenerator,
    tmp_path: Path,
) -> None:
    """El número de marcos afectados se calcula correctamente."""
    hallazgos = [_hacer_hallazgo(1), _hacer_hallazgo(2)]
    md = generador_default.generar_markdown(hallazgos, tmp_path)
    contenido = md.read_text(encoding="utf-8")
    # Ambos hallazgos usan ISO_27001_2022 + ENS_2022 → 2 marcos únicos
    assert "Marcos afectados | **2**" in contenido
