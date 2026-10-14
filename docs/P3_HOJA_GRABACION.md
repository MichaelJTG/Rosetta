# Hoja de grabación · vídeo P3 (13 min)

Guion completo y narración: `docs/P3_VIDEO_SCRIPT.md`. Tiempos medidos en el ensayo
automático del 2026-10-14 contra `a7d1abd` (GPU de 16 GB, Ollama `qwen2.5:14b`).

## Antes de pulsar REC

1. PowerShell en la raíz del repo: `$env:COMPOSE_FILE = "docker-compose.yml;$HOME\.rosetta\compose.grabacion.yml"`
   (override local, fuera del repo: usuario de demo, secreto JWT, allowlist del laboratorio).
2. `docker compose --profile lab ps` → app y neo4j `healthy`, lab-objetivo `Up`. Si no: `up -d`.
3. **Calentar el modelo**: una traducción cualquiera desde el panel. La primera en frío tarda ~60 s.
4. Terminal 1 (curl): `TOKEN` ya obtenido; `/tmp/fake.pdf` y `/tmp/large_test.pdf` (21 MB) creados.
5. Terminal 2: los 3 informes abiertos en `less` (04/10 correspondencia, 04/10 hallazgos, 11/10 Validador).
6. Terminal 3: salida de `pytest --cov` ya ejecutada (tarda ~75 s).

## Pestañas del navegador, en este orden

1. Diapositiva / diagrama de tres capas
2. `http://localhost:8000/dashboard` (en la pantalla de login)
3. `http://localhost:8000/docs`
4. `https://github.com/MichaelJTG/Rosetta/actions`
5. `https://github.com/MichaelJTG/Rosetta` (badge CI)

## Bloques

| # | Bloque · objetivo | Pantalla | Qué escribir / pulsar | Espera medida |
|---|---|---|---|---|
| 1 | Contexto · 1:00 | Pestaña 1 | — | — |
| 2 | Login · 0:45 | Pestaña 2 (y 3 un instante) | Usuario `auditor-demo`, clave `cambia-esta-clave-de-prueba` → Inicio → señalar los 16 paneles | 4 s |
| 3 | Traducción · 1:45 | Panel «Traducir» → «+ Traducir hallazgo» | Origen `manual` · dificultad `baja` · activo `fw-perimetral.techserv.example` · evidencia «CVE-2024-3400: RCE sin autenticación en PAN-OS (GlobalProtect). CVSS 10. Explotación activa en el firewall perimetral de TechServ.» · vector «Petición HTTP manipulada contra el portal GlobalProtect expuesto a Internet» · marcos ISO 27001 + ENS → «Traducir hallazgo» | 12 s |
|   |   | Terminal 1 | curl de `/translate` con `"validar": true` (sección 3 del guion) | 30 s |
| 4 | Corpus · 0:45 | Terminal 1 | `docker compose exec app rosetta load-corpus all corpus` → 229 fragmentos | 25 s |
| 5 | Evaluación · 2:45 | Terminal 2 | Pasar por los 3 informes; no leerlos en directo | — |
| 6 | Seguridad · 2:00 | Terminal 1 | Bucle de 6 logins fallidos (**≥ 1 min después del último login**) → `401 ×5, 429`; `fake.pdf` → 400; `large_test.pdf` → 413 | 2 s |
| 7 | Dosier, auditoría, drift · 1:30 | Panel «Auditoría» | Objetivo `http://lab-objetivo` · Nuclei y Nmap · alcance «Laboratorio propio local, contenedor lab-objetivo, autorizado por el autor para la demo de la P3» → «Iniciar auditoría», y narrar mientras corre | 45 s (18 hallazgos) |
|   |   | Panel «Hallazgos» | Organización «TechServ (caso ficticio)» → «Generar dosier» → «↓ Descargar PDF» | 1 s |
|   |   | Panel «Drift» | Pegar `PROCEDIMIENTO_DRIFT` y `OBSERVACIONES_DRIFT` de `scripts/seed_demo.py` (copiarlos antes a un bloc) → «Detectar drift» | 14 s |
| 8 | CI y calidad · 1:15 | Pestaña 4 + terminal 3 | Job verde (ruff, mypy, pytest, gitleaks, pip-audit) · `556 passed`, 85 % · INC-01 | — |
| 9 | Cierre · 1:15 | Pestaña 5 | — | — |

Esperas de LLM y escáneres: ~2 min de los 13. El bloque 7 es el más justo: lanzar la
auditoría primero y explicar el dosier mientras corre.

**No hacer en directo:** `rosetta translate "texto"` (el CLI espera un JSON);
`mypy` en local (falla con el Python 3.13 del `.venv`; mostrarlo en la CI).
