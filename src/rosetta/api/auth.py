"""Autenticación de la API de ROSETTA — JWT con HTTP Basic como fallback.

Activa autenticación si ``ROSETTA_USER`` está definida en el entorno.
Acepta dos esquemas en el encabezado ``Authorization``:

  - ``Bearer <token JWT>`` — esquema recomendado, emitido por ``POST /auth/login``
  - ``Basic <base64(user:pass)>`` — fallback heredado para clientes y la
    integración OAuth2 de ``/docs``

Si ``ROSETTA_USER`` está vacío, todas las peticiones pasan sin autenticar
(modo desarrollo).

Rutas públicas que nunca requieren auth:
  /health, /dashboard, /, /docs, /openapi.json, /redoc, /auth/login, /auth/refresh
"""

from __future__ import annotations

import base64
import os
import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/dashboard",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/auth/login",
        "/auth/refresh",
    }
)

# TTLs (segundos)
_ACCESS_TTL = 30 * 60  # 30 min
_REFRESH_TTL = 7 * 24 * 60 * 60  # 7 días
_JWT_ALGO = "HS256"


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _jwt_secret() -> str:
    """Devuelve el secreto JWT desde el entorno o un fallback dev poco seguro.

    En producción ROSETTA_JWT_SECRET DEBE estar definido (>= 32 caracteres).
    """
    s = os.getenv("ROSETTA_JWT_SECRET", "")
    if not s:
        # Fallback de desarrollo. NUNCA usar en producción.
        s = "rosetta-dev-secret-CHANGE-ME-in-production-32+chars"
    return s


def create_access_token(username: str) -> str:
    """Genera un access token JWT con TTL corto."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": username,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=_ACCESS_TTL)).timestamp()),
    }
    return str(jwt.encode(payload, _jwt_secret(), algorithm=_JWT_ALGO))


def create_refresh_token(username: str) -> str:
    """Genera un refresh token JWT con TTL largo."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": username,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=_REFRESH_TTL)).timestamp()),
    }
    return str(jwt.encode(payload, _jwt_secret(), algorithm=_JWT_ALGO))


def decode_token(token: str, expected_type: str) -> dict[str, Any] | None:
    """Decodifica y valida un JWT. Devuelve el payload o None si inválido."""
    try:
        payload: dict[str, Any] = jwt.decode(token, _jwt_secret(), algorithms=[_JWT_ALGO])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    if not payload.get("sub"):
        return None
    return payload


def _all_credentials() -> list[tuple[str, str]]:
    """Lista de pares (usuario, contraseña) admitidos.

    Combina la credencial principal (``ROSETTA_USER`` / ``ROSETTA_PASSWORD``)
    con cero o más credenciales adicionales declaradas en
    ``ROSETTA_USERS_EXTRA`` con formato ``user1:pass1,user2:pass2``.
    """
    creds: list[tuple[str, str]] = []
    main_u = os.getenv("ROSETTA_USER", "")
    main_p = os.getenv("ROSETTA_PASSWORD", "")
    if main_u:
        creds.append((main_u, main_p))
    extra = os.getenv("ROSETTA_USERS_EXTRA", "")
    for raw in extra.split(","):
        pair = raw.strip()
        if not pair or ":" not in pair:
            continue
        u, _, p = pair.partition(":")
        u, p = u.strip(), p.strip()
        if u:
            creds.append((u, p))
    return creds


def verify_credentials(username: str, password: str) -> bool:
    """Verifica usuario/password contra el conjunto de credenciales (timing-safe).

    Recorre todas las credenciales sin atajos para evitar fugas de timing por
    salida temprana cuando el username coincide con alguna entrada.
    """
    creds = _all_credentials()
    if not creds:
        return False
    matched = False
    for expected_user, expected_pass in creds:
        ok_u = secrets.compare_digest(username.encode(), expected_user.encode())
        ok_p = secrets.compare_digest(password.encode(), expected_pass.encode())
        if ok_u and ok_p:
            matched = True
    return matched


def access_ttl_seconds() -> int:
    return _ACCESS_TTL


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Middleware de autenticación combinada (JWT Bearer + HTTP Basic).

    Conserva el nombre por compatibilidad con la importación previa en main.py.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)
        # WebSocket: middleware HTTP no aplica. La conexión se autentica con el
        # audit_id (UUID), que actúa como capability token de un solo uso.
        if request.url.path.startswith("/audit/ws/"):
            return await call_next(request)

        expected_user = os.getenv("ROSETTA_USER", "")
        if not expected_user:
            # Auth desactivada en desarrollo
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")

        # 1. JWT Bearer (preferido)
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            payload = decode_token(token, expected_type="access")
            if payload is None:
                return _unauthorized("Token JWT inválido o expirado")
            return await call_next(request)

        # 2. HTTP Basic (fallback heredado)
        if auth_header.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                user, _, password = decoded.partition(":")
            except Exception:
                return _unauthorized()
            if not verify_credentials(user, password):
                return _unauthorized()
            return await call_next(request)

        return _unauthorized()


def _unauthorized(detail: str = "Authentication required") -> Response:
    import json

    return Response(
        content=json.dumps({"detail": detail}),
        status_code=401,
        headers={
            "WWW-Authenticate": 'Bearer realm="ROSETTA", Basic realm="ROSETTA"',
            "Content-Type": "application/json",
        },
    )
