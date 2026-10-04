"""Autenticación de la API de ROSETTA — JWT con HTTP Basic como fallback.

La autenticación está activa en cuanto hay credenciales configuradas
(``ROSETTA_USER`` / ``ROSETTA_PASSWORD`` o ``ROSETTA_USERS_EXTRA``). Acepta dos
esquemas en el encabezado ``Authorization``:

  - ``Bearer <token JWT>`` — esquema recomendado, emitido por ``POST /auth/login``
  - ``Basic <base64(user:pass)>`` — fallback heredado para clientes y la
    integración OAuth2 de ``/docs``

Política fail-closed (B-5):
  - Con autenticación activa la aplicación no arranca sin un
    ``ROSETTA_JWT_SECRET`` de al menos 32 caracteres ni con contraseñas de
    menos de 12 (``validar_configuracion_auth``, llamada en el lifespan).
  - Sin credenciales, la API solo queda abierta si se declara de forma
    explícita ``ROSETTA_AUTH_DISABLED=1`` (modo desarrollo). Si no, responde
    503 a todo lo que no sea público.
  - No existe ningún secreto JWT escrito en el código.

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

# Requisitos mínimos de configuración con autenticación activa (B-5).
_MIN_LONGITUD_SECRETO = 32
_MIN_LONGITUD_PASSWORD = 12
_VALORES_VERDADEROS = frozenset({"1", "true", "yes", "si", "sí", "on"})

# Solo en modo desarrollo (sin credenciales): secreto aleatorio por proceso.
_SECRETO_EFIMERO = secrets.token_hex(32)


# ---------------------------------------------------------------------------
# Configuración (fail-closed)
# ---------------------------------------------------------------------------


def auth_desactivada_explicitamente() -> bool:
    """True si se ha declarado el modo desarrollo con ``ROSETTA_AUTH_DISABLED``."""
    return os.getenv("ROSETTA_AUTH_DISABLED", "").strip().lower() in _VALORES_VERDADEROS


def auth_activa() -> bool:
    """La autenticación está activa si hay al menos una credencial configurada."""
    return bool(_all_credentials())


def validar_configuracion_auth() -> str:
    """Comprueba al arrancar que la autenticación está bien configurada.

    Returns:
        ``"activa"`` o ``"desactivada"`` (modo desarrollo explícito).

    Raises:
        RuntimeError: Si la configuración permitiría un acceso inseguro.
    """
    credenciales = _all_credentials()
    if not credenciales:
        if auth_desactivada_explicitamente():
            return "desactivada"
        raise RuntimeError(
            "No hay credenciales configuradas (ROSETTA_USER / ROSETTA_PASSWORD). "
            "Defínelas o, solo para desarrollo local, declara ROSETTA_AUTH_DISABLED=1."
        )
    if len(os.getenv("ROSETTA_JWT_SECRET", "")) < _MIN_LONGITUD_SECRETO:
        raise RuntimeError(
            f"ROSETTA_JWT_SECRET debe tener al menos {_MIN_LONGITUD_SECRETO} caracteres "
            'aleatorios. Genera uno con: python -c "import secrets; '
            'print(secrets.token_hex(32))"'
        )
    cortas = sum(1 for _, password in credenciales if len(password) < _MIN_LONGITUD_PASSWORD)
    if cortas:
        raise RuntimeError(
            f"{cortas} cuenta(s) con contraseña de menos de {_MIN_LONGITUD_PASSWORD} caracteres."
        )
    return "activa"


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _jwt_secret() -> str:
    """Devuelve el secreto con el que se firman y verifican los JWT.

    Con autenticación activa es obligatorio ``ROSETTA_JWT_SECRET`` (>= 32
    caracteres). Sin credenciales (modo desarrollo) se usa un secreto aleatorio
    por proceso, que nadie más conoce.

    Raises:
        RuntimeError: Si la autenticación está activa y el secreto no es válido.
    """
    secreto = os.getenv("ROSETTA_JWT_SECRET", "")
    if len(secreto) >= _MIN_LONGITUD_SECRETO:
        return secreto
    if not auth_activa():
        return _SECRETO_EFIMERO
    raise RuntimeError("ROSETTA_JWT_SECRET ausente o con menos de 32 caracteres.")


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

        if not auth_activa():
            if auth_desactivada_explicitamente():
                return await call_next(request)  # modo desarrollo declarado
            return _no_configurada()  # fail-closed

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


def _no_configurada() -> Response:
    """503: la API no tiene autenticación configurada y no está en modo desarrollo."""
    import json

    return Response(
        content=json.dumps({"detail": "Autenticación no configurada en el servidor."}),
        status_code=503,
        headers={"Content-Type": "application/json"},
    )


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
