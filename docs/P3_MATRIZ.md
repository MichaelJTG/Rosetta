# docs/P3_MATRIZ.md — Matriz de trazabilidad P3

> Relaciona cada RF/RNF con el commit que lo implementa, los tests que lo verifican y la evidencia demostrable.
> Generado: 2026-10-04 · Bloque D · Última actualización: 2026-10-06

---

## Leyenda

| Columna | Descripción |
|---------|-------------|
| RF/RNF | Identificador del requisito en `P3_REQUISITOS.md` |
| Commit principal | Hash corto del commit que implementa o cierra el requisito |
| Tests | Fichero(s) de test que verifican el comportamiento |
| Evidencia | Cómo demostrar el cumplimiento |

---

## Requisitos Funcionales

| RF | Descripción breve | Commit | Tests | Evidencia |
|----|-------------------|--------|-------|-----------|
| RF-01 | Traducir hallazgo → controles normativos con cita y justificación | `92d4b83` | `tests/test_traductor.py` | `POST /translate` → JSON con `controles_incumplidos`, `cita_normativa`. Demo en vídeo. |
| RF-02 | Multi-marco: ISO 27001, ENS, NIS2, DORA, RGPD, NIST CSF, PCI-DSS | `f29cbde` | `tests/test_rag.py` | `rosetta load-corpus all corpus/` → 166 fragmentos en 7 marcos. ChromaDB filtro por `framework_id`. |
| RF-03 | Pipeline RAG con ChromaDB | `f29cbde` | `tests/test_rag.py` | 100 % cobertura. `NormativaRAG.recuperar()` retorna fragmentos filtrados. |
| RF-04 | Dosier de auditoría Markdown + PDF | `60d437a` | `tests/test_report_generator.py` | `POST /reports/generate` + `GET /reports/download/{filename}`. Descarga MD y PDF en demo. |
| RF-05 | Ingesta de PDF de auditoría | `b64dd2b` | `tests/test_pdf_ingestion.py` | `POST /ingest/pdf` → hallazgos extraídos. pdfplumber + fallback visión LLM. |
| RF-06 | Modo Auditoría Red Team (Nmap, Nuclei) + WebSocket | `419b737` | `tests/test_orchestrator.py` | `POST /audit/start` → `WS /audit/ws/{id}`. Nmap 7.95 + Nuclei 3.11.1 en imagen Docker. |
| RF-07 | Ingesta de alertas Wazuh (JSON/CSV) | `b64dd2b` | `tests/test_wazuh.py` | `POST /blue/ingest` → alertas normalizadas a `DatosBlue`. |
| RF-08 | Correlación Red↔Blue | `b64dd2b` | `tests/test_blue_enrichment.py` | `BlueEnrichment.enriquecer()` cruza hallazgos. 96 % cobertura. |
| RF-09 | Arquitectura multi-agente (Soundwave + Validador) | `4ebeade` | `tests/test_agents.py` · `tests/test_security.py` (RF-09) | `RosettaOrchestrator` + `Validador` implementados. `POST /translate?validar=true` invoca Validador (por defecto `false`). Benchmark: rejection_precision@F1<0.5=1.0 (10 casos piloto). |
| RF-10 | Copilot normativo con citas y confianza | `b64dd2b` | `tests/test_copilot.py` | `POST /copilot/ask` → respuesta con campo `confianza`. 94 % cobertura. |
| RF-11 | Detección de procedure drift | `b64dd2b` | `tests/test_drift.py` | `POST /drift/analyze` → `drift_score`, diferencias detectadas. 95 % cobertura. |
| RF-12 | Dashboard SPA 16 paneles | `92a5989` | `tests/test_security.py` (XSS) | `GET /dashboard` → HTML con los 16 paneles. Todos los `innerHTML` con `esc()`. |
| RF-13 | OpenAPI / Swagger UI | (base del proyecto) | `tests/test_api.py` | `GET /docs` → 200. `GET /openapi.json` → 30 endpoints documentados. |
| RF-14 | Gate CI/CD: bloquear PRs que incumplen controles | `b64dd2b` | `tests/test_diff_analyzer.py` | `POST /analyze-diff` → decisión `block/warn`. `.github/workflows/rosetta-gate.yml`. 88 % cobertura. |
| RF-15 | Auth JWT Bearer + HTTP Basic fallback | `5cf5aac` | `tests/test_auth.py` | `POST /auth/login` → JWT. Bearer en endpoints protegidos. Rate limiting `slowapi`. |
| RF-16 | Historial SQLite append-only | `b64dd2b` | `tests/test_session_store.py` | `SessionStore.guardar()` → registro permanente. 82 % cobertura. |
| RF-17 | Grafo Neo4j + vis.js con degradación | `1c567c4` | `tests/test_degradacion.py` | `GET /graph/data` → 200 sin Neo4j (modo memoria). 4 tests específicos de degradación. |
| RF-18 | CLI Typer: translate, load-corpus, version, dossier, scan, detect-drift | `06bffda` | `tests/test_cli.py` | `rosetta version` → semver. 6 comandos, 20 tests, 87 % cobertura CLI. |
| RF-19 | Panel Cumplimiento por marco | `b64dd2b` | `tests/test_control_store.py` | `GET /controls/{marco}` → controles agrupados. 100 % cobertura. |
| RF-20a | Catálogo de controles con detalle | `b64dd2b` | `tests/test_control_store.py` | `GET /controls/{marco}/{control_id}` → detalle con estado. |
| RF-20b | Roadmap de vulnerabilidades | `b64dd2b` | `tests/test_api.py` | `GET /vuln-roadmap` → lista con trazabilidad temporal. |
| RF-20c | Panel de evidencias | `b64dd2b` | `tests/test_api.py` | `GET /evidence-panel` → evidencias ligadas a controles. |
| RF-20d | Gap analysis por marco | `b64dd2b` | `tests/test_api.py` | `POST /gap-analysis/{marco}` → brechas con severidad. |
| RF-20e | Plan director automático | `b64dd2b` | `tests/test_api.py` | `POST /plan-director/{marco}` → plan ordenado por prioridad. |
| RF-20f | Análisis de riesgos | `b64dd2b` | `tests/test_api.py` | `POST /risk-analysis` → activos con scoring de riesgo. |

---

## Requisitos No Funcionales

| RNF | Descripción breve | Commit | Tests / Mecanismo | Evidencia |
|-----|-------------------|--------|-------------------|-----------|
| RNF-01 | Degradación grácil sin Neo4j | `1c567c4` | `tests/test_degradacion.py` | 4 tests: Neo4j caído al arrancar → 200 en todos los endpoints. Timeouts 5 s. |
| RNF-02 | Cobertura ≥ 80 % core | `3e8a0ed` | `pytest --cov` | 77 % total medido. Core entre 76–100 %; `pdf_ingestion.py` a 76 %. |
| RNF-03 | Sin errores `mypy --strict` | (lint continuo) | `mypy src/` | 0 errores en 56 ficheros. Pre-commit activo. |
| RNF-04 | Sin violaciones `ruff` | `7ec6b66` | `ruff check . && ruff format --check` | CI run 37203612212 verde. Pre-commit alineado con `uv.lock`. |
| RNF-05 | Instalable: `uv sync` + `docker compose up` | `2339813` | Instalación limpia documentada | Build 165 s, imagen 3.85 GB, 197 fragmentos indexados, tests en verde. |
| RNF-06 | Cero secretos en el repositorio | `1ef7438` | `gitleaks`, `detect-private-key` | INC-01: credenciales antiguas rotadas (dan 401). Historial no reescrito (decisión del autor). |
| RNF-07 | Rate limiting en endpoints sensibles | `5cf5aac` | `tests/test_auth.py` | `slowapi` activo. `POST /auth/login` → 429 al exceder límite. |
| RNF-08 | Validación alcance Modo Auditoría | `810812d` | `tests/test_orchestrator.py` | 11 tests: IPs privadas/localhost bloqueadas. DNS resolution + `is_global` + allowlist. |
| RNF-09 | Tiempo Traductor < 30 s | benchmark D-2 | `eval/run_eval.py` (latency_s) | Benchmark 2026-10-04: p50=8.2s, avg=16.6s, max=41.3s (n=5, Ollama qwen2.5:14b). 4/5 bajo umbral. |
| RNF-10 | Build CI reproducible | `2e7792d` | CI workflow `.github/workflows/ci.yml` | CI run 37203612212 verde. `setup-uv v7.6.0`, `uv sync --locked`, matriz 3.11/3.12. |
| RNF-11 | Cabeceras de seguridad HTTP | `c552729` | `tests/test_security.py` | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP. 3 tests. |
| RNF-12 | Audit CVE dependencias en CI | `2e7792d`·`26e63e5` | CI job `dependency-audit` | Sobre `uv.lock`. 4 avisos chromadb sin parche → R-01. CVE-2026-104851 (fsspec) parchado en `26e63e5`. CI verde. |

---

## Cobertura de Bloques

| Bloque | Ítems | Commits | Estado |
|--------|-------|---------|--------|
| Bloque A (CI, infraestructura, demos) | A-0, A-1, A-3, A-4, A-5, A-6, A-7, A-8, A-9 | `2e7792d`…`419b737` | ✅ Completo |
| Bloque B (seguridad) | B-1…B-10 (B-11 pendiente, fuera del alcance MVP) | `5ca3ca8`…`f06f726` | ✅ Completo (B-4: default loopback-only + verificado en producción `172.18.0.1/32`; B-9: magic bytes + límite 20 MB + tope páginas + 4 tests) |
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

> Cobertura global 77 %; objetivo ≥ 80 % en `core/` (RNF-02 en 🟡).
> Tag de entrega: `v1.0-practica3` (pendiente de crear por el autor).
