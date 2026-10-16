# docs/P3_MATRIZ.md — Matriz de trazabilidad P3

> Relaciona cada RF/RNF con el commit que lo implementa, los tests que lo verifican y la evidencia demostrable.
> Generado: 2026-10-04 · Bloque D · Última actualización: 2026-10-16 (minutos del vídeo)

---

## Leyenda

| Columna | Descripción |
|---------|-------------|
| RF/RNF | Identificador del requisito en `P3_REQUISITOS.md` |
| Commit principal | Hash corto del commit que implementa o cierra el requisito |
| Tests | Fichero(s) de test que verifican el comportamiento |
| Evidencia | Minuto del vídeo («Vídeo mm:ss») o, si no aparece en él, la prueba (PR-XX, Anexo E de la memoria) y cómo demostrar el cumplimiento |

---

## Requisitos Funcionales

| RF | Descripción breve | Commit | Tests | Evidencia |
|----|-------------------|--------|-------|-----------|
| RF-01 | Traducir hallazgo → controles normativos con cita y justificación | `92d4b83` | `tests/test_traductor.py` | Vídeo 06:00. `POST /translate` → JSON con `controles_incumplidos`, `cita_normativa`. Demo en vídeo. |
| RF-02 | Multi-marco: ISO 27001, ENS, NIS2, DORA, RGPD, NIST CSF, PCI-DSS | `f29cbde` | `tests/test_rag.py` | Vídeo 06:00. `rosetta load-corpus all corpus/` → 229 fragmentos en 7 marcos. ChromaDB filtro por `framework_id`. |
| RF-03 | Pipeline RAG con ChromaDB | `f29cbde` | `tests/test_rag.py` | Vídeo 06:00. 100 % cobertura. `NormativaRAG.recuperar()` retorna fragmentos filtrados. |
| RF-04 | Dosier de auditoría Markdown + PDF | `60d437a` | `tests/test_report_generator.py` | Vídeo 07:01. `POST /reports/generate` + `GET /reports/download/{filename}`. Descarga MD y PDF en demo. |
| RF-05 | Ingesta de PDF de auditoría | `b64dd2b` | `tests/test_pdf_ingestion.py` | Vídeo 08:01. `POST /ingest/pdf` → hallazgos extraídos. pdfplumber + fallback visión LLM. |
| RF-06 | Modo Auditoría Red Team (Nmap, Nuclei) + WebSocket | `419b737` | `tests/test_orchestrator.py` | Vídeo 10:31. `POST /audit/start` → `WS /audit/ws/{id}`. Nmap 7.95 + Nuclei 3.11.1 en imagen Docker. |
| RF-07 | Ingesta de alertas Wazuh (JSON/CSV) | `b64dd2b` | `tests/test_wazuh.py` | Vídeo 10:20. `POST /blue/ingest` → alertas normalizadas a `DatosBlue`. |
| RF-08 | Correlación Red↔Blue | `b64dd2b` | `tests/test_blue_enrichment.py` | Vídeo 10:20. `BlueEnrichment.enriquecer()` cruza hallazgos. 96 % cobertura. |
| RF-09 | Arquitectura multi-agente (Soundwave + Validador) | `4ebeade` | `tests/test_agents.py` · `tests/test_security.py` (RF-09) | Vídeo 12:42. `RosettaOrchestrator` + `Validador` implementados. `POST /translate` con `"validar": true` en el cuerpo invoca Validador (por defecto `false`). Eval 2026-10-11, 73 casos: precisión de rechazo @F1<0.5 = 0.82; F1 medio 0.36 en aprobados frente a 0.17 en rechazados; aprueba 23 de 51 traducciones con F1 < 0.5. |
| RF-10 | Copilot normativo con citas y confianza | `b64dd2b` | `tests/test_copilot.py` | Vídeo 13:24. `POST /copilot/ask` → respuesta con campo `confianza`. 94 % cobertura. |
| RF-11 | Detección de procedure drift | `b64dd2b` | `tests/test_drift.py` | No aparece en el vídeo (por tiempo). PR-11; figura 8 y apartado 6.9 de la memoria. `POST /drift/analyze` → `drift_score`, diferencias detectadas. 95 % cobertura. |
| RF-12 | Dashboard SPA 16 paneles | `92a5989` | `tests/test_security.py` (XSS) | Vídeo 03:55. `GET /dashboard` → HTML con los 16 paneles. Todos los `innerHTML` con `esc()`. |
| RF-13 | OpenAPI / Swagger UI | (base del proyecto) | `tests/test_api.py` | Vídeo 14:28. `GET /docs` → 200 y Swagger UI carga en navegador (`tests/e2e/test_docs_ui.py`, tras `c78a0c7`). `GET /openapi.json` → 30 operaciones documentadas. |
| RF-14 | Gate CI/CD: bloquear PRs que incumplen controles | `b64dd2b` | `tests/test_diff_analyzer.py` | No aparece en el vídeo (por tiempo). PR-14; apartado 6.15 de la memoria. `POST /analyze-diff` → decisión `block/warn`. `.github/workflows/rosetta-gate.yml`. 88 % cobertura. |
| RF-15 | Auth JWT Bearer + HTTP Basic fallback | `5cf5aac` | `tests/test_auth.py` | No aparece en el vídeo (por tiempo). PR-15; apartado 6.11 de la memoria. `POST /auth/login` → JWT. Bearer en endpoints protegidos. Rate limiting `slowapi`. |
| RF-16 | Historial SQLite append-only | `b64dd2b` | `tests/test_session_store.py` | Vídeo 15:09. `SessionStore.guardar()` → registro permanente. 82 % cobertura. |
| RF-17 | Grafo Neo4j + vis.js con degradación | `1c567c4` | `tests/test_degradacion.py` | Vídeo 16:31. `GET /graph/data` → 200 sin Neo4j (modo memoria). 4 tests específicos de degradación. |
| RF-18 | CLI Typer: translate, load-corpus, version, dossier, scan, detect-drift | `06bffda` | `tests/test_cli.py` | No aparece en el vídeo (por tiempo). PR-18; apartado 6.13 de la memoria. `rosetta version` → semver. 6 comandos, 20 tests, 87 % cobertura CLI. |
| RF-19 | Panel Cumplimiento por marco | `b64dd2b` | `tests/test_control_store.py` | Vídeo 17:53. `GET /controls/{marco}` → controles agrupados. 100 % cobertura. |
| RF-20a | Catálogo de controles con detalle | `b64dd2b` | `tests/test_control_store.py` | Vídeo 17:56. `GET /controls/{marco}/{control_id}` → detalle con estado. |
| RF-20b | Roadmap de vulnerabilidades | `b64dd2b` · `81e76fa` | `tests/test_api.py` | Vídeo 17:57. `GET /vuln-roadmap` → lista con trazabilidad temporal. El panel salía vacío (ensayo del 15/10) porque `estado=all` no se reconocía; corregido en `81e76fa` con un test. |
| RF-20c | Panel de evidencias | `b64dd2b` | `tests/test_api.py` | Vídeo 17:59. `GET /evidence-panel` → evidencias ligadas a controles. |
| RF-20d | Gap analysis por marco | `b64dd2b` | `tests/test_api.py` | Vídeo 19:26. `POST /gap-analysis/{marco}` → brechas con severidad. |
| RF-20e | Plan director automático | `b64dd2b` | `tests/test_api.py` | Vídeo 19:53. `POST /plan-director/{marco}` → plan ordenado por prioridad. |
| RF-20f | Análisis de riesgos | `b64dd2b` | `tests/test_api.py` | Vídeo 19:54. `POST /risk-analysis` → activos con scoring de riesgo. |

---

## Requisitos No Funcionales

| RNF | Descripción breve | Commit | Tests / Mecanismo | Evidencia |
|-----|-------------------|--------|-------------------|-----------|
| RNF-01 | Degradación grácil sin Neo4j | `1c567c4` | `tests/test_degradacion.py` | No aparece en el vídeo. PR-26. 4 tests: Neo4j caído al arrancar → 200 en todos los endpoints. Timeouts 5 s. |
| RNF-02 | Cobertura ≥ 80 % core | `3e8a0ed` | `pytest --cov=rosetta --cov-branch` | No aparece en el vídeo. PR-27. 2026-10-10: 92 % en `core/`, 85 % global (556 tests); `pdf_ingestion.py` a 76 %. |
| RNF-03 | Sin errores `mypy --strict` | (lint continuo) | `mypy src/` | No aparece en el vídeo. PR-28. 0 errores en 56 ficheros. Pre-commit activo. |
| RNF-04 | Sin violaciones `ruff` | `7ec6b66` | `ruff check . && ruff format --check` | No aparece en el vídeo. PR-29. CI run 37203612212 verde. Pre-commit alineado con `uv.lock`. |
| RNF-05 | Instalable: `uv sync` + `docker compose up` | `2339813` | Instalación limpia documentada | No aparece en el vídeo. PR-30 y PR-31. Build 165 s, imagen 3.85 GB, 197 fragmentos indexados, tests en verde. PR-31: un amigo del autor, ajeno al proyecto, lo instaló siguiendo el README el 15/10/2026, sin incidencias según su feedback. |
| RNF-06 | Cero secretos en el repositorio | `1ef7438`·`4aeef3b` | `gitleaks`, `detect-private-key` | No aparece en el vídeo. PR-32. INC-01: credenciales rotadas 2026-10-04 (dan 401). Historial limpiado 2026-10-06 (`git filter-repo`, `f50957f`→`4aeef3b`): 0 apariciones literal, gitleaks CI verde. Commit huérfano `e2819f0` en GitHub; purga pendiente. |
| RNF-07 | Rate limiting en endpoints sensibles | `5cf5aac` | `tests/test_auth.py` | No aparece en el vídeo. PR-33. `slowapi` activo. `POST /auth/login`: 5 logins por minuto; 5 respuestas 401 y la sexta 429. |
| RNF-08 | Validación alcance Modo Auditoría | `810812d` | `tests/test_orchestrator.py` | No aparece en el vídeo. PR-34. 11 tests: IPs privadas/localhost bloqueadas. DNS resolution + `is_global` + allowlist. |
| RNF-09 | Tiempo Traductor < 30 s | benchmark 2026-10-11 | `eval/bench_latency.py` | No aparece en el vídeo. PR-35. Benchmark 2026-10-11: p50=6.95 s, p95=11.02 s, max=59.88 s (n=20, Ollama qwen2.5:14b, 1 marco). 19/20 bajo umbral; la que lo supera es la primera, en frío (32.9 s de carga del modelo). `eval/reports/2026-10-11T15-28-12_bench_latency_ollama.json` |
| RNF-10 | Build CI reproducible | `2e7792d` | CI workflow `.github/workflows/ci.yml` | No aparece en el vídeo. PR-36. CI run 37203612212 verde. `setup-uv v7.6.0`, `uv sync --locked`, matriz 3.11/3.12. |
| RNF-11 | Cabeceras de seguridad HTTP | `c552729` | `tests/test_security.py` | No aparece en el vídeo. PR-37. `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP. 3 tests. |
| RNF-12 | Audit CVE dependencias en CI | `2e7792d`·`26e63e5` | CI job `dependency-audit` | No aparece en el vídeo. PR-38. Sobre `uv.lock`. 4 avisos chromadb sin parche → R-01. CVE-2026-104851 (fsspec) parchado en `26e63e5`. CI verde. |

---

## Cobertura de Bloques

| Bloque | Ítems | Commits | Estado |
|--------|-------|---------|--------|
| Bloque A (CI, infraestructura, demos) | A-0, A-1, A-3, A-4, A-5, A-6, A-7, A-8, A-9 | `2e7792d`…`419b737` | ✅ Completo |
| Bloque B (seguridad) | B-1…B-10 (B-11 pendiente, fuera del alcance MVP) | `5ca3ca8`…`f06f726` | ✅ Completo (B-4: default loopback-only + verificado en el servidor propio el 2026-10-06 `172.18.0.1/32`; B-9: magic bytes + límite 20 MB + tope páginas + 4 tests) |
| Bloque C (eval + corpus ENS) | C-1, C-2, C-3, C-4 | `92d4b83` · `86a5e91` | ✅ Completo |
| Bloque D (cierre P3) | D-1, D-2, D-3, D-4, D-5 | `bb8fc2a` · `86a5e91` | ✅ Completo |
| Bloque E (memoria de insumos) | `docs/P3_MEMORIA_INSUMOS.md` · atribución corpus/ground truth | este commit | ✅ Completo |

---

## Tests totales por módulo (snapshot 2026-10-04)

| Módulo / fichero | Tests | Cobertura |
|------------------|-------|-----------|
| `eval/run_eval.py` — funciones puras | 27 (D-1) | fuera de scope `--cov` |
| `src/rosetta/core/rag.py` | 8 | 100 % |
| `src/rosetta/core/traductor.py` | 6 | 86 % |
| `src/rosetta/core/blue_enrichment.py` | 5 | 96 % |
| `src/rosetta/core/report_generator.py` | 12 | 87 % |
| `src/rosetta/core/drift.py` | 4 | 95 % |
| `src/rosetta/core/copilot.py` | 5 | 94 % |
| `src/rosetta/api/auth.py` | 18 | 82 % |
| `src/rosetta/cli/main.py` | 20 | 87 % |
| `src/rosetta/core/graph.py` + degradación | 8 | 86 % |
| **Total acumulado** | **≥ 503** | **~77 % global** |

> Snapshot del 2026-10-04. El 2026-10-10: 556 tests, 85 % global y 92 % en `core/` (RNF-02 ✅).
> Tag de entrega: `v1.0-practica3`.
