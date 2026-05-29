"""Tests para tool_control_map.py — funciones puras de mapping herramienta->control."""

from __future__ import annotations

from rosetta.core.tool_control_map import (
    get_all_covered_controls,
    get_control_title,
    get_controls_catalog,
    get_controls_for_tool,
)

# ---------------------------------------------------------------------------
# get_controls_for_tool
# ---------------------------------------------------------------------------


def test_wazuh_returns_controls() -> None:
    """WAZUH tiene controles mapeados."""
    result = get_controls_for_tool("WAZUH")
    assert len(result) > 0
    ids = [c[0] for c in result]
    assert any("ISO_27001" in i or "ENS" in i or "NIS2" in i for i in ids)


def test_nuclei_returns_controls() -> None:
    """NUCLEI tiene controles mapeados."""
    result = get_controls_for_tool("NUCLEI")
    assert len(result) > 0


def test_nmap_returns_controls() -> None:
    """NMAP tiene controles mapeados."""
    result = get_controls_for_tool("NMAP")
    assert len(result) > 0


def test_unknown_tool_returns_empty() -> None:
    """Herramienta desconocida devuelve lista vacia."""
    assert get_controls_for_tool("HERRAMIENTA_INEXISTENTE") == []


def test_case_insensitive_lookup() -> None:
    """La busqueda es insensible a mayusculas."""
    upper = get_controls_for_tool("WAZUH")
    lower = get_controls_for_tool("wazuh")
    assert upper == lower


def test_each_result_is_tuple_of_two_strings() -> None:
    """Cada elemento del resultado es (control_id: str, titulo: str)."""
    for item in get_controls_for_tool("NUCLEI"):
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], str)
        assert isinstance(item[1], str)


# ---------------------------------------------------------------------------
# get_all_covered_controls
# ---------------------------------------------------------------------------


def test_get_all_covered_controls_not_empty() -> None:
    """get_all_covered_controls devuelve al menos un control."""
    result = get_all_covered_controls()
    assert len(result) > 0


def test_covered_control_has_at_least_one_source() -> None:
    """Cada control cubierto tiene al menos una fuente."""
    for ctrl_id, fuentes in get_all_covered_controls().items():
        assert len(fuentes) >= 1, f"{ctrl_id} sin fuentes"


def test_wazuh_appears_in_covered_controls() -> None:
    """Al menos un control aparece con WAZUH como fuente."""
    covered = get_all_covered_controls()
    wazuh_controls = [k for k, v in covered.items() if "WAZUH" in v]
    assert len(wazuh_controls) > 0


# ---------------------------------------------------------------------------
# get_control_title
# ---------------------------------------------------------------------------


def test_known_control_returns_title() -> None:
    """Control conocido devuelve su titulo."""
    title = get_control_title("ISO_27001_A.8.15")
    assert title == "Logging"


def test_monitoring_control_title() -> None:
    """Otro control conocido devuelve titulo correcto."""
    title = get_control_title("ISO_27001_A.8.16")
    assert title == "Monitoring activities"


def test_unknown_control_returns_id() -> None:
    """Control desconocido devuelve el propio ID."""
    assert get_control_title("CONTROL_INEXISTENTE") == "CONTROL_INEXISTENTE"


# ---------------------------------------------------------------------------
# get_controls_catalog
# ---------------------------------------------------------------------------


def test_iso_27001_catalog_has_controls() -> None:
    """Catalogo ISO 27001:2022 tiene al menos 10 controles."""
    result = get_controls_catalog("iso_27001_2022")
    assert len(result) >= 10


def test_iso_27001_uppercase_alias() -> None:
    """Alias en mayusculas tambien funciona."""
    result = get_controls_catalog("ISO_27001_2022")
    assert len(result) >= 10


def test_ens_catalog_has_controls() -> None:
    """Catalogo ENS 2022 tiene al menos 5 controles."""
    result = get_controls_catalog("ens_2022")
    assert len(result) >= 5


def test_catalog_items_have_required_fields() -> None:
    """Cada item del catalogo tiene id, titulo y descripcion."""
    for item in get_controls_catalog("iso_27001_2022"):
        assert "id" in item
        assert "titulo" in item
        assert "descripcion" in item
        assert item["id"] != ""
        assert item["titulo"] != ""


def test_unknown_marco_returns_empty() -> None:
    """Marco no existente devuelve lista vacia."""
    assert get_controls_catalog("marco_inexistente") == []
