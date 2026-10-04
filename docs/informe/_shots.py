"""Capturas de evidencia del dashboard ROSETTA en producción.

Autentica vía /auth/login, inyecta el JWT en localStorage y captura los
paneles clave del SPA. Salida en docs/informe/img/*.png.
"""

from __future__ import annotations

import json
import os
import pathlib
import urllib.request

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROSETTA_SHOTS_BASE", "http://127.0.0.1:8000")
USER = os.environ["ROSETTA_SHOTS_USER"]
PASS = os.environ["ROSETTA_SHOTS_PASS"]
OUT = pathlib.Path(__file__).parent / "img"
OUT.mkdir(exist_ok=True)


def get_tokens() -> dict[str, str]:
    body = json.dumps({"username": USER, "password": PASS}).encode()
    req = urllib.request.Request(
        BASE + "/auth/login", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def main() -> None:
    tok = get_tokens()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1480, "height": 940}, device_scale_factor=2)

        # 1. Pantalla de login (sin token en localStorage)
        page.goto(BASE + "/dashboard", wait_until="networkidle")
        page.wait_for_timeout(1400)
        page.screenshot(path=str(OUT / "01_login.png"))
        print("01_login OK")

        # Inyectar JWT y recargar como sesion autenticada
        page.evaluate(
            "([a, r]) => { localStorage.setItem('rosetta:access', a);"
            " localStorage.setItem('rosetta:refresh', r); }",
            [tok["access_token"], tok["refresh_token"]],
        )
        page.goto(BASE + "/dashboard", wait_until="networkidle")
        page.wait_for_timeout(1800)
        page.screenshot(path=str(OUT / "02_inicio.png"))
        print("02_inicio OK")

        # 3. Cumplimiento - consulta agregada de todos los marcos
        page.evaluate("switchTab('cumplimiento')")
        page.wait_for_timeout(500)
        page.evaluate("doComplianceAll()")
        page.wait_for_timeout(2800)
        page.screenshot(path=str(OUT / "03_cumplimiento.png"))
        print("03_cumplimiento OK")

        browser.close()


if __name__ == "__main__":
    main()
