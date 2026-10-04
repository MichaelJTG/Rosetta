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
import os
import time
from pathlib import Path

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import rosetta.api.auth as auth_module
from rosetta.api.auth import BasicAuthMiddleware, validar_configuracion_auth

# Contraseña del usuario extra usada en tests.
# Sobreescribir con TEST_EXTRA_USER_PASS en CI para evitar literales en el código.
_EXTRA_PASS = os.getenv("TEST_EXTRA_USER_PASS", "test-extra-pass-fixture")


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
    """Modo desarrollo explícito (ROSETTA_AUTH_DISABLED=1) y sin credenciales: pasa."""
    monkeypatch.delenv("ROSETTA_USER", raising=False)
    monkeypatch.setenv("ROSETTA_AUTH_DISABLED", "1")
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


# ---------------------------------------------------------------------------
# Credenciales adicionales vía ROSETTA_USERS_EXTRA
# ---------------------------------------------------------------------------


def test_extra_user_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    """ROSETTA_USERS_EXTRA permite cuentas adicionales (formato user:pass,user:pass)."""
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "main-pass")
    monkeypatch.setenv("ROSETTA_USERS_EXTRA", f"profesor:{_EXTRA_PASS},otro:abc123")
    client = TestClient(_make_app())

    # Cuenta principal sigue funcionando
    r = client.get("/protected", headers={"Authorization": _basic_header("admin", "main-pass")})
    assert r.status_code == 200

    # Cuentas extra funcionan
    r = client.get(
        "/protected",
        headers={"Authorization": _basic_header("profesor", _EXTRA_PASS)},
    )
    assert r.status_code == 200

    r = client.get("/protected", headers={"Authorization": _basic_header("otro", "abc123")})
    assert r.status_code == 200


def test_extra_user_wrong_password_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "main-pass")
    monkeypatch.setenv("ROSETTA_USERS_EXTRA", "profesor:correct")
    client = TestClient(_make_app())
    r = client.get("/protected", headers={"Authorization": _basic_header("profesor", "wrong")})
    assert r.status_code == 401


def test_extra_user_malformed_entry_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entradas sin ':' o vacías en USERS_EXTRA se ignoran sin romper auth."""
    monkeypatch.setenv("ROSETTA_USER", "admin")
    monkeypatch.setenv("ROSETTA_PASSWORD", "main-pass")
    monkeypatch.setenv("ROSETTA_USERS_EXTRA", ",sin_dos_puntos, , profesor:ok ")
    client = TestClient(_make_app())
    # La cuenta válida sigue funcionando (con espacios trimados)
    r = client.get("/protected", headers={"Authorization": _basic_header("profesor", "ok")})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# B-5 · Autenticación fail-closed y secreto JWT obligatorio
# ---------------------------------------------------------------------------

# Secreto que estuvo escrito en el código de un repositorio público: cualquiera
# podía firmar tokens con él si producción no definía el suyo.
_SECRETO_PUBLICO_ANTIGUO = "rosetta-dev-secret-" + "CHANGE-ME-in-production-32+chars"


def _config_valida(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSETTA_USER", "auditor-demo")
    monkeypatch.setenv("ROSETTA_PASSWORD", "clave-ficticia-larga")
    monkeypatch.setenv("ROSETTA_JWT_SECRET", "s" * 32)


def test_sin_credenciales_ni_modo_desarrollo_responde_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-closed: sin usuarios y sin modo desarrollo explícito no se sirve nada."""
    monkeypatch.delenv("ROSETTA_USER", raising=False)
    monkeypatch.delenv("ROSETTA_AUTH_DISABLED", raising=False)
    r = TestClient(_make_app()).get("/protected")
    assert r.status_code == 503


def test_solo_cuentas_extra_tambien_activa_la_autenticacion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Antes, sin ROSETTA_USER la API quedaba abierta aunque hubiera cuentas extra."""
    monkeypatch.delenv("ROSETTA_USER", raising=False)
    monkeypatch.setenv("ROSETTA_AUTH_DISABLED", "1")  # se ignora: hay credenciales
    monkeypatch.setenv("ROSETTA_USERS_EXTRA", f"evaluador:{_EXTRA_PASS}")
    client = TestClient(_make_app())
    assert client.get("/protected").status_code == 401
    ok = client.get(
        "/protected", headers={"Authorization": _basic_header("evaluador", _EXTRA_PASS)}
    )
    assert ok.status_code == 200


def test_configuracion_valida_activa_la_autenticacion(monkeypatch: pytest.MonkeyPatch) -> None:
    _config_valida(monkeypatch)
    assert validar_configuracion_auth() == "activa"


def test_arranque_falla_sin_secreto_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    _config_valida(monkeypatch)
    monkeypatch.delenv("ROSETTA_JWT_SECRET")
    with pytest.raises(RuntimeError, match="ROSETTA_JWT_SECRET"):
        validar_configuracion_auth()


def test_arranque_falla_con_secreto_jwt_corto(monkeypatch: pytest.MonkeyPatch) -> None:
    _config_valida(monkeypatch)
    monkeypatch.setenv("ROSETTA_JWT_SECRET", "s" * 31)
    with pytest.raises(RuntimeError, match="32"):
        validar_configuracion_auth()


def test_arranque_falla_con_password_corta(monkeypatch: pytest.MonkeyPatch) -> None:
    _config_valida(monkeypatch)
    monkeypatch.setenv("ROSETTA_PASSWORD", "corta")
    with pytest.raises(RuntimeError, match="12"):
        validar_configuracion_auth()


def test_arranque_falla_sin_credenciales_ni_modo_desarrollo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ROSETTA_USER", raising=False)
    monkeypatch.delenv("ROSETTA_AUTH_DISABLED", raising=False)
    with pytest.raises(RuntimeError, match="ROSETTA_AUTH_DISABLED"):
        validar_configuracion_auth()


def test_modo_desarrollo_solo_con_variable_explicita(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROSETTA_USER", raising=False)
    monkeypatch.setenv("ROSETTA_AUTH_DISABLED", "1")
    assert validar_configuracion_auth() == "desactivada"


def test_no_queda_ningun_secreto_jwt_escrito_en_el_codigo() -> None:
    fuente = Path(auth_module.__file__).read_text(encoding="utf-8")
    assert "CHANGE-ME" not in fuente
    assert _SECRETO_PUBLICO_ANTIGUO not in fuente


def test_token_firmado_con_el_antiguo_secreto_publico_se_rechaza(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un atacante que firme con el secreto que estuvo en el repo no entra."""
    _config_valida(monkeypatch)
    ahora = int(time.time())
    falso = jwt.encode(
        {"sub": "auditor-demo", "type": "access", "iat": ahora, "exp": ahora + 600},
        _SECRETO_PUBLICO_ANTIGUO,
        algorithm="HS256",
    )
    r = TestClient(_make_app()).get("/protected", headers={"Authorization": f"Bearer {falso}"})
    assert r.status_code == 401
