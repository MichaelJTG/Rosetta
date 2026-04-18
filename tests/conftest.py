"""Fixtures compartidas de pytest para ROSETTA."""

from __future__ import annotations

import pytest

from rosetta.core.models import (
    DatosRedTeam,
    FuenteRedTeam,
    Severidad,
)


@pytest.fixture
def hallazgo_aws_key_filtrada() -> DatosRedTeam:
    """Hallazgo canónico: AWS access key filtrada en repo público."""
    return DatosRedTeam(
        origen=FuenteRedTeam.GITHUB_SECRETS,
        activo_detectado="AWS_ACCESS_KEY_ID en repo público",
        evidencia="https://github.com/org/repo/commit/abc123",
        vector_ataque="Exposición de credencial cloud en código fuente",
        dificultad_explotacion=Severidad.BAJA,
    )
