"""E2E: Swagger UI (/docs) se renderiza en un navegador real (RF-13, B-3).

Requiere una instancia de ROSETTA en marcha y Playwright con Chromium. Se salta
si falta cualquiera de los dos, así que no corre en la CI:

    ROSETTA_E2E_URL=http://127.0.0.1:8000 uv run --with playwright \
        pytest tests/e2e --confcutdir=tests/e2e --no-cov

``ROSETTA_E2E_CHROMIUM`` permite indicar el ejecutable de Chromium si el que
espera la versión instalada de Playwright no está descargado.
"""

from __future__ import annotations

import os

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")

BASE_URL = os.getenv("ROSETTA_E2E_URL", "")

pytestmark = pytest.mark.skipif(not BASE_URL, reason="ROSETTA_E2E_URL no definida")


def test_docs_swagger_ui_renders() -> None:
    """/docs carga Swagger UI sin errores de CSP y lista las operaciones de la API."""
    errores: list[str] = []
    executable = os.getenv("ROSETTA_E2E_CHROMIUM") or None
    with playwright_api.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=executable)
        page = browser.new_page()
        page.on("pageerror", lambda exc: errores.append(str(exc)))
        page.on(
            "console",
            lambda msg: (
                errores.append(msg.text)
                if msg.type == "error" and "Content Security Policy" in msg.text
                else None
            ),
        )
        page.goto(f"{BASE_URL}/docs")
        page.wait_for_selector(".opblock", timeout=30_000)
        operaciones = page.locator(".opblock").count()
        browser.close()

    assert not errores, errores
    assert operaciones >= 20
