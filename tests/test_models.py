"""Tests básicos de los modelos Pydantic."""

from __future__ import annotations

from rosetta.core.models import (
    DatosRedTeam,
    FuenteRedTeam,
    HallazgoMaestro,
    MarcoNormativo,
    Severidad,
)


def test_hallazgo_maestro_minimo(hallazgo_aws_key_filtrada: DatosRedTeam) -> None:
    """Un hallazgo mínimo solo necesita red_team_data."""
    hallazgo = HallazgoMaestro(
        id_hallazgo="SEC-2026-0001",
        red_team_data=hallazgo_aws_key_filtrada,
    )
    assert hallazgo.id_hallazgo == "SEC-2026-0001"
    assert hallazgo.blue_team_data is None
    assert hallazgo.compliance_data is None


def test_marcos_normativos_soportados() -> None:
    """El enum expone todos los marcos del MVP."""
    assert MarcoNormativo.ISO_27001_2022
    assert MarcoNormativo.ENS_2022
    assert MarcoNormativo.NIS2
    assert MarcoNormativo.DORA


def test_fuente_redteam_tiene_github_secrets() -> None:
    """GitHub secrets es fuente canónica para el caso de uso MVP."""
    assert FuenteRedTeam.GITHUB_SECRETS.value == "github_secrets"


def test_severidad_orden_semantico() -> None:
    """Severidades existen en orden ascendente de gravedad."""
    severidades = [
        Severidad.INFORMATIVA,
        Severidad.BAJA,
        Severidad.MEDIA,
        Severidad.ALTA,
        Severidad.CRITICA,
    ]
    assert len(severidades) == 5
