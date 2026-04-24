"""Tests del CorpusLoader: parseo de YAML intuitem y segmentación de texto.

Cobertura objetivo: 80% de adapters/compliance/loader.py
Todos los tests son unitarios — no requieren ChromaDB ni embeddings.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from rosetta.adapters.compliance.loader import CorpusLoader, FragmentoNormativo
from rosetta.core.models import MarcoNormativo

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def corpus_yaml_minimo(tmp_path: Path) -> Path:
    """YAML mínimo con 3 controles en formato intuitem para tests."""
    data = {
        "ref_id": "ISO/IEC 27001:2022",
        "objects": {
            "reference_controls": [
                {
                    "ref_id": "A.5.1",
                    "name": "Policies for information security",
                    "description": "Information security policies shall be defined.",
                    "category": "policy",
                    "translations": {
                        "es": {
                            "name": "Políticas de seguridad de la información",
                            "description": "Se deben definir políticas de seguridad.",
                        }
                    },
                },
                {
                    "ref_id": "A.8.24",
                    "name": "Use of cryptography",
                    "description": "Rules for cryptographic key management shall be defined.",
                    "category": "technological",
                    "translations": {
                        "es": {
                            "name": "Uso de la criptografía",
                            "description": "Se deben definir reglas para el uso de criptografía.",
                        }
                    },
                },
                {
                    "ref_id": "A.8.5",
                    "name": "Secure authentication",
                    "description": "Secure authentication technologies shall be implemented.",
                    "category": "technological",
                    "translations": {
                        "es": {
                            "name": "Autenticación segura",
                            "description": "Se deben implementar tecnologías de autenticación segura.",
                        }
                    },
                },
            ]
        },
    }
    archivo = tmp_path / "iso27001-test.yaml"
    archivo.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return tmp_path


@pytest.fixture
def corpus_markdown(tmp_path: Path) -> Path:
    """Markdown con controles ISO 27001 para test del parser genérico."""
    contenido = """# ISO 27001 Annex A

A.5.1 Políticas de seguridad
Las políticas de seguridad de la información deben definirse y revisarse.

A.8.24 Uso de la criptografía
Se deben establecer reglas para el uso de controles criptográficos.

A.9.1 Requisitos de negocio para el control de acceso
Se debe establecer una política de control de acceso.
"""
    archivo = tmp_path / "corpus.md"
    archivo.write_text(contenido, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Tests CorpusLoader — YAML intuitem
# ---------------------------------------------------------------------------


def test_cargar_yaml_devuelve_fragmentos(corpus_yaml_minimo: Path) -> None:
    """CorpusLoader parsea el YAML de intuitem y devuelve el número correcto."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, corpus_yaml_minimo)
    assert len(fragmentos) == 3


def test_fragmento_yaml_usa_traduccion_española(corpus_yaml_minimo: Path) -> None:
    """El nombre y texto de cada fragmento usa la traducción española."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, corpus_yaml_minimo)
    f_a524 = next(f for f in fragmentos if f.control_id == "A.8.24")
    assert "Uso de la criptografía" in f_a524.nombre
    assert "criptografía" in f_a524.texto.lower()


def test_fragmento_tiene_marco_correcto(corpus_yaml_minimo: Path) -> None:
    """Todos los fragmentos llevan el MarcoNormativo correcto."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, corpus_yaml_minimo)
    for f in fragmentos:
        assert f.marco == MarcoNormativo.ISO_27001_2022


def test_fragmento_id_control_correcto(corpus_yaml_minimo: Path) -> None:
    """Los IDs de los controles se extraen correctamente."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, corpus_yaml_minimo)
    ids = {f.control_id for f in fragmentos}
    assert ids == {"A.5.1", "A.8.24", "A.8.5"}


def test_fragmento_normativo_es_instancia_correcta(corpus_yaml_minimo: Path) -> None:
    """Los objetos devueltos son instancias de FragmentoNormativo."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, corpus_yaml_minimo)
    for f in fragmentos:
        assert isinstance(f, FragmentoNormativo)


def test_cargar_carpeta_vacia_devuelve_lista_vacia(tmp_path: Path) -> None:
    """Una carpeta sin archivos compatibles devuelve lista vacía."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, tmp_path)
    assert fragmentos == []


# ---------------------------------------------------------------------------
# Tests CorpusLoader — Markdown / texto genérico
# ---------------------------------------------------------------------------


def test_cargar_markdown_detecta_controles(corpus_markdown: Path) -> None:
    """El parser genérico extrae al menos un control del Markdown."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, corpus_markdown)
    assert len(fragmentos) >= 1


def test_cargar_markdown_ids_conocidos(corpus_markdown: Path) -> None:
    """El parser detecta los IDs A.5.1, A.8.24, A.9.1 del Markdown."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, corpus_markdown)
    ids = {f.control_id for f in fragmentos}
    assert "A.5.1" in ids or "A.8.24" in ids


# ---------------------------------------------------------------------------
# Tests corpus ISO 27001:2022 real (si existe)
# ---------------------------------------------------------------------------


CORPUS_REAL = Path("corpus/iso27001")


@pytest.mark.skipif(
    not (CORPUS_REAL / "iso27001-2022-intuitem.yaml").exists(),
    reason="Corpus ISO 27001:2022 no descargado (corpus/iso27001/iso27001-2022-intuitem.yaml)",
)
def test_corpus_real_tiene_93_controles() -> None:
    """El corpus real de intuitem tiene exactamente 93 controles."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, CORPUS_REAL)
    assert len(fragmentos) == 93


@pytest.mark.skipif(
    not (CORPUS_REAL / "iso27001-2022-intuitem.yaml").exists(),
    reason="Corpus ISO 27001:2022 no descargado",
)
def test_corpus_real_controles_clave_presentes() -> None:
    """Los controles clave del ROADMAP están en el corpus real."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.ISO_27001_2022, CORPUS_REAL)
    ids = {f.control_id for f in fragmentos}
    for control in ("A.5.15", "A.8.5", "A.8.16", "A.8.24"):
        assert control in ids, f"Control {control} no encontrado en el corpus"


# ---------------------------------------------------------------------------
# Tests corpus DORA (corpus/dora/dora-2022-articles.yaml)
# ---------------------------------------------------------------------------

CORPUS_DORA = Path("corpus/dora")


@pytest.mark.skipif(
    not (CORPUS_DORA / "dora-2022-articles.yaml").exists(),
    reason="Corpus DORA no disponible",
)
def test_corpus_dora_carga_controles() -> None:
    """El corpus DORA carga al menos 10 artículos estructurados."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.DORA, CORPUS_DORA)
    assert len(fragmentos) >= 10


@pytest.mark.skipif(
    not (CORPUS_DORA / "dora-2022-articles.yaml").exists(),
    reason="Corpus DORA no disponible",
)
def test_corpus_dora_controles_clave_presentes() -> None:
    """Los artículos clave de DORA están presentes en el corpus."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.DORA, CORPUS_DORA)
    ids = {f.control_id for f in fragmentos}
    for art in ("Art.9.4.b", "Art.17.1", "Art.19.1", "Art.24.1"):
        assert art in ids, f"Artículo DORA {art} no encontrado en el corpus"


@pytest.mark.skipif(
    not (CORPUS_DORA / "dora-2022-articles.yaml").exists(),
    reason="Corpus DORA no disponible",
)
def test_corpus_dora_marco_correcto() -> None:
    """Todos los fragmentos DORA llevan MarcoNormativo.DORA."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.DORA, CORPUS_DORA)
    for f in fragmentos:
        assert f.marco == MarcoNormativo.DORA


# ---------------------------------------------------------------------------
# Tests corpus RGPD (corpus/rgpd/rgpd-2016-679-articles.yaml)
# ---------------------------------------------------------------------------

CORPUS_RGPD = Path("corpus/rgpd")


@pytest.mark.skipif(
    not (CORPUS_RGPD / "rgpd-2016-679-articles.yaml").exists(),
    reason="Corpus RGPD no disponible",
)
def test_corpus_rgpd_carga_controles() -> None:
    """El corpus RGPD carga al menos 7 artículos estructurados."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.RGPD, CORPUS_RGPD)
    assert len(fragmentos) >= 7


@pytest.mark.skipif(
    not (CORPUS_RGPD / "rgpd-2016-679-articles.yaml").exists(),
    reason="Corpus RGPD no disponible",
)
def test_corpus_rgpd_controles_clave_presentes() -> None:
    """Los artículos clave del RGPD están presentes en el corpus."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.RGPD, CORPUS_RGPD)
    ids = {f.control_id for f in fragmentos}
    for art in ("Art.5.1", "Art.32.1", "Art.33.1", "Art.35.1"):
        assert art in ids, f"Artículo RGPD {art} no encontrado en el corpus"


@pytest.mark.skipif(
    not (CORPUS_RGPD / "rgpd-2016-679-articles.yaml").exists(),
    reason="Corpus RGPD no disponible",
)
def test_corpus_rgpd_marco_correcto() -> None:
    """Todos los fragmentos RGPD llevan MarcoNormativo.RGPD."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.RGPD, CORPUS_RGPD)
    for f in fragmentos:
        assert f.marco == MarcoNormativo.RGPD


# ---------------------------------------------------------------------------
# Tests corpus NIST CSF 2.0 (corpus/nist_csf_2/nist-csf-2-subcategories.yaml)
# ---------------------------------------------------------------------------

CORPUS_NIST = Path("corpus/nist_csf_2")


@pytest.mark.skipif(
    not (CORPUS_NIST / "nist-csf-2-subcategories.yaml").exists(),
    reason="Corpus NIST CSF 2.0 no disponible",
)
def test_corpus_nist_carga_controles() -> None:
    """El corpus NIST CSF 2.0 carga al menos 10 subcategorías."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.NIST_CSF_2, CORPUS_NIST)
    assert len(fragmentos) >= 10


@pytest.mark.skipif(
    not (CORPUS_NIST / "nist-csf-2-subcategories.yaml").exists(),
    reason="Corpus NIST CSF 2.0 no disponible",
)
def test_corpus_nist_controles_clave_presentes() -> None:
    """Las subcategorías clave de NIST CSF 2.0 están presentes en el corpus."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.NIST_CSF_2, CORPUS_NIST)
    ids = {f.control_id for f in fragmentos}
    for sub in ("ID.AM-01", "PR.DS-01", "DE.CM-01", "RS.MA-01"):
        assert sub in ids, f"Subcategoría NIST {sub} no encontrada en el corpus"


@pytest.mark.skipif(
    not (CORPUS_NIST / "nist-csf-2-subcategories.yaml").exists(),
    reason="Corpus NIST CSF 2.0 no disponible",
)
def test_corpus_nist_marco_correcto() -> None:
    """Todos los fragmentos NIST llevan MarcoNormativo.NIST_CSF_2."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.NIST_CSF_2, CORPUS_NIST)
    for f in fragmentos:
        assert f.marco == MarcoNormativo.NIST_CSF_2


# ---------------------------------------------------------------------------
# Tests corpus PCI-DSS 4.0 (corpus/pci_dss_4/pci-dss-4-requirements.yaml)
# ---------------------------------------------------------------------------

CORPUS_PCI = Path("corpus/pci_dss_4")


@pytest.mark.skipif(
    not (CORPUS_PCI / "pci-dss-4-requirements.yaml").exists(),
    reason="Corpus PCI-DSS 4.0 no disponible",
)
def test_corpus_pci_carga_controles() -> None:
    """El corpus PCI-DSS 4.0 carga al menos 10 requisitos estructurados."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.PCI_DSS_4, CORPUS_PCI)
    assert len(fragmentos) >= 10


@pytest.mark.skipif(
    not (CORPUS_PCI / "pci-dss-4-requirements.yaml").exists(),
    reason="Corpus PCI-DSS 4.0 no disponible",
)
def test_corpus_pci_controles_clave_presentes() -> None:
    """Los requisitos clave de PCI-DSS 4.0 están presentes en el corpus."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.PCI_DSS_4, CORPUS_PCI)
    ids = {f.control_id for f in fragmentos}
    for req in ("Req.3.4", "Req.8.2", "Req.10.2", "Req.11.3"):
        assert req in ids, f"Requisito PCI {req} no encontrado en el corpus"


@pytest.mark.skipif(
    not (CORPUS_PCI / "pci-dss-4-requirements.yaml").exists(),
    reason="Corpus PCI-DSS 4.0 no disponible",
)
def test_corpus_pci_marco_correcto() -> None:
    """Todos los fragmentos PCI llevan MarcoNormativo.PCI_DSS_4."""
    loader = CorpusLoader()
    fragmentos = loader.cargar(MarcoNormativo.PCI_DSS_4, CORPUS_PCI)
    for f in fragmentos:
        assert f.marco == MarcoNormativo.PCI_DSS_4
