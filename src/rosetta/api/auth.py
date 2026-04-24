"""Middleware de autenticación básica HTTP para la API de ROSETTA.

Activa la autenticación HTTP Basic si las variables de entorno
``ROSETTA_USER`` y ``ROSETTA_PASSWORD`` están definidas. Si no están
definidas, todas las peticiones pasan sin autenticar (modo desarrollo).

Rutas públicas que nunca requieren auth:
  /health, /dashboard, /, /docs, /openapi.json, /redoc
"""

from __future__ import annotations

import base64
import os
import secrets
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_PUBLIC_PATHS = frozenset({"/health", "/dashboard", "/", "/docs", "/openapi.json", "/redoc"})


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Middleware de HTTP Basic Auth opcional.

    Se activa solo si ``ROSETTA_USER`` está definida en el entorno.
    Devuelve 401 con encabezado ``WWW-Authenticate: Basic`` si las
    credenciales son incorrectas o están ausentes.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        expected_user = os.getenv("ROSETTA_USER", "")
        if not expected_user:
            # Auth desactivada en desarrollo
            return await call_next(request)

        expected_pass = os.getenv("ROSETTA_PASSWORD", "")

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return _unauthorized()

        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            user, _, password = decoded.partition(":")
        except Exception:
            return _unauthorized()

        ok_user = secrets.compare_digest(user.encode(), expected_user.encode())
        ok_pass = secrets.compare_digest(password.encode(), expected_pass.encode())

        if not (ok_user and ok_pass):
            return _unauthorized()

        return await call_next(request)


def _unauthorized() -> Response:
    return Response(
        content='{"detail":"Authentication required"}',
        status_code=401,
        headers={
            "WWW-Authenticate": 'Basic realm="ROSETTA"',
            "Content-Type": "application/json",
        },
    )
