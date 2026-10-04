"""Fixtures compartidas de pytest para ROSETTA."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

# Antes de que ningún test importe rosetta.api.main (que llama a load_dotenv()):
# el .env local del desarrollador no debe filtrarse en la suite (A-6).
os.environ["PYTHON_DOTENV_DISABLED"] = "1"

import pytest  # noqa: E402

from rosetta.core.models import (  # noqa: E402
    DatosRedTeam,
    FuenteRedTeam,
    Severidad,
)

# Variables de la máquina que nunca deben influir en un test.
_VARS_DE_MAQUINA = (
    "ROSETTA_USER",
    "ROSETTA_PASSWORD",
    "ROSETTA_USERS_EXTRA",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "OLLAMA_URL",
    "OLLAMA_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "SHODAN_API_KEY",
    "HIBP_API_KEY",
    "WAZUH_API_URL",
    "WAZUH_API_USER",
    "WAZUH_API_PASSWORD",
)


@pytest.fixture(autouse=True)
def _entorno_aislado(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Aísla cada test del entorno de la máquina (A-6).

    Ningún test necesita una API key real ni un LLM: se fija el proveedor
    Claude con una clave de prueba no válida (si un test llamase de verdad a la
    API, fallaría de forma visible). Los almacenes persistentes (ChromaDB,
    SQLite) y los informes se redirigen a un directorio temporal para no
    ensuciar el repositorio.
    """
    for var in _VARS_DE_MAQUINA:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-no-real")
    monkeypatch.setenv("CHROMADB_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("ROSETTA_SESSION_DB", str(tmp_path / "sessions.db"))
    monkeypatch.setenv("ROSETTA_CONTROLS_DB", str(tmp_path / "controls.db"))
    monkeypatch.setenv("ROSETTA_REPORTS_DIR", str(tmp_path / "reports"))
    yield


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
