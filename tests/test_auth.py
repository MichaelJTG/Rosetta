"""Tests para BasicAuthMiddleware (api/auth.py).

Verifica:
- Rutas públicas pasan sin credenciales
- Cuando ROSETTA_USER no está definida, pasa sin auth (dev mode)
- Credenciales correctas conceden acceso
- Credenciales incorrectas devuelven 401
- Header ausente devuelve 401
- Base64 malformado devuelve 401
"""

from __future__ import annotations

import base64

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rosetta.api.auth import BasicAuthMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BasicAuthMiddleware)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/protected")
    async def protected() -> dict[str, str]:
        return {"secret": "data"}

    return app


def _basic_header(user: str, password: str) -> str:
    raw = f"{user}:{password}"
    return "Basic " + base64.b64encode(raw.encode()).decode()


# ---------------------------------------------------------------------------
# Sin variable de entorno → modo desarrollo (sin auth)
# ---------------------------------------------------------------------------


def test_dev_mode_no_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sin ROSETTA_USER definida todas las rutas pasan."""
    monkeypatch.delenv("ROSETTA_USER", raising=False)
    client = TestClient(_make_app())
    r = client.get("/protected")
    assert r.status_code == 200


def test_public_path_health_always_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    """La ruta /health es pública incluso con auth activada."""
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "secret")
    client = TestClient(_make_app())
    r = client.get("/health")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Auth activada (ROSETTA_USER definida)
# ---------------------------------------------------------------------------


def test_correct_credentials_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "s3cret!")
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Authorization": _basic_header("admin", "s3cret!")})
    assert r.status_code == 200
    assert r.json() == {"secret": "data"}


def test_wrong_password_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "correct")
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Authorization": _basic_header("admin", "wrong")})
    assert r.status_code == 401
    assert 'Basic realm="ROSETTA"' in r.headers["WWW-Authenticate"]


def test_wrong_user_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "correct")
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Authorization": _basic_header("hacker", "correct")})
    assert r.status_code == 401


def test_missing_auth_header_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "correct")
    client = TestClient(_make_app())
    r = client.get("/protected")
    assert r.status_code == 401


def test_malformed_base64_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "correct")
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Authorization": "Basic not-valid-base64!!!"})
    assert r.status_code == 401


def test_non_basic_scheme_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "correct")
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Authorization": "Bearer sometoken"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Rutas públicas completas
# ---------------------------------------------------------------------------

PUBLIC_PATHS = ["/health", "/dashboard", "/", "/docs", "/openapi.json", "/redoc"]


@pytest.mark.parametrize("path", PUBLIC_PATHS)
def test_all_public_paths_bypass_auth(monkeypatch: pytest.MonkeyPatch, path: str) -> None:
    """Todas las rutas públicas bypasan auth aunque ROSETTA_USER esté definida."""
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "secret")

    app = FastAPI()
    app.add_middleware(BasicAuthMiddleware)

    @app.get(path)
    async def public_route() -> dict[str, str]:
        return {"public": "true"}

    client = TestClient(app)
    r = client.get(path)
    # No debe devolver 401
    assert r.status_code != 401
