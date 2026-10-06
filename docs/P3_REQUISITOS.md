# docs/P3_REQUISITOS.md — Tabla de requisitos ROSETTA (Práctica 3)

> Generado en Fase 0 y corregido con rutas verificadas con `ls`/`grep`.
> Base: informe P1 + commits del repo (46 commits, 389 tests, cobertura 77%).
> **Pendiente validación por el autor** antes de incorporar a la memoria.

---

## Leyenda de estado

| Símbolo | Significado |
|---------|-------------|
| ✅ Cumplido | Implementado, testado, demostrable |
| 🟡 Parcial | Implementado pero incompleto, sin tests suficientes o sin benchmark |
| ❌ Descartado | Prometido en P1 como requisito y eliminado del alcance P3 (con justificación) |
| ➕ Añadido | No estaba en P1; incorporado durante el desarrollo |

---

## Requisitos Funcionales

| ID | Descripción | Endpoint / Módulo | Estado | Notas |
|----|-------------|-------------------|--------|-------|
| RF-01 | Traducir hallazgo técnico a controles normativos con cita literal y justificación | `POST /translate` | ✅ Cumplido | Tool-use forzado con esquema Pydantic. E2E en Docker con Ollama (2026-10-04): 200 en 7,3 s con el corpus cargado. **No pasa por el agente Validador** (ver RF-09) |
| RF-02 | Soporte multi-marco: ISO 27001:2022, ENS 2022, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0 | `POST /translate` + `corpus/` | ✅ Cumplido | Corpus indexado en ChromaDB con `framework_id` |
| RF-03 | Pipeline RAG con ChromaDB para recuperación semántica del corpus normativo | `src/rosetta/core/rag.py` | ✅ Cumplido | 100 % de cobertura; embeddings multilingües y filtro por marco. 197 fragmentos indexados en la instalación limpia. La API debe reiniciarse tras indexar desde otro proceso (limitación de ChromaDB, documentada en el README) |
| RF-04 | Generación de dosier de auditoría en Markdown y PDF | `POST /reports/generate` · `src/rosetta/core/report_generator.py` | ✅ Cumplido | Bajado a 🟡 el 2026-10-04 (rutas internas, sin descarga). **Vuelve a ✅**: commit `60d437a` (descarga autenticada `GET /reports/download/{filename}` + botón en el dashboard, 9 tests) y E2E en Docker (MD y PDF descargados). El PDF lo genera ReportLab |
| RF-05 | Ingesta de PDF de auditoría humana (extracción de hallazgos) | `POST /ingest/pdf` · `src/rosetta/core/pdf_ingestion.py` | ✅ Cumplido | pdfplumber + respaldo visión LLM para páginas escaneadas |
| RF-06 | Modo Auditoría automática Red Team (Nmap, Nuclei) con progreso WebSocket | `POST /audit/start` · `WS /audit/ws/{audit_id}` · `src/rosetta/adapters/red/` | 🟡 Parcial | Nmap 7.95 y Nuclei 3.11.1 instalados en la imagen (amd64/arm64, `2339813`). Validación de alcance con DNS y allowlist (B-8). Pendiente: demo contra el laboratorio local |
| RF-07 | Integración Blue Team — ingesta de alertas Wazuh (JSON/CSV) | `POST /blue/ingest` · `src/rosetta/adapters/blue/wazuh.py` | ✅ Cumplido | |
| RF-08 | Correlación Red↔Blue: cruzar alertas defensivas con hallazgos ofensivos | `src/rosetta/core/blue_enrichment.py` | ✅ Cumplido | 96% cobertura |
| RF-09 | Arquitectura multi-agente con scheduler Soundwave + agente Validador crítico | `src/rosetta/agents/orchestrator.py` · `src/rosetta/agents/soundwave.py` · `src/rosetta/agents/validator.py` · `POST /translate?validar=true` | 🟡 Parcial | `RosettaOrchestrator` + `Validador` implementados y testeados. **Bloque D**: `POST /translate` acepta `validar=true` (por defecto `false`) para invocar el Validador como segunda opinión (commit `4ebeade`); 3 tests en `tests/test_security.py`. Benchmark: aprobados avg F1=0.352, rechazados avg F1=0.267, rejection_precision@F1<0.5=1.0 (10 casos piloto). El scheduler Soundwave no está expuesto en ningún endpoint de producción. |
| RF-10 | Copilot normativo: preguntas en lenguaje natural con citas y nivel de confianza | `POST /copilot/ask` · `src/rosetta/core/copilot.py` | ✅ Cumplido | 94% cobertura |
| RF-11 | Detección de procedure drift: comparar procedimiento escrito vs. comportamiento observado | `POST /drift/analyze` · `src/rosetta/core/drift.py` | ✅ Cumplido | 95% cobertura; panel dedicado en dashboard |
| RF-12 | Dashboard SPA con 10 paneles servido desde el backend | `GET /dashboard` · `src/rosetta/api/dashboard.py` | ✅ Cumplido | 16 paneles: Inicio, Traducir, Cumplimiento, Auditoría, PDF, Blue Team, Grafo, Drift, Copilot, Hallazgos (con dosier), Controles, Roadmap, Evidencias, Gap, Plan director, Riesgos |
| RF-13 | API REST documentada con OpenAPI (Swagger UI) | `GET /docs` · `GET /openapi.json` | ✅ Cumplido | 30 endpoints HTTP + 1 WebSocket |
| RF-14 | Gate CI/CD: analizar diff de PR y bloquear si introduce incumplimientos normativos | `POST /analyze-diff` · `src/rosetta/core/diff_analyzer.py` · `.github/workflows/rosetta-gate.yml` | ✅ Cumplido | 88% cobertura |
| RF-15 | Autenticación JWT (Bearer) como esquema principal; HTTP Basic como fallback para clientes heredados y `/docs` | `POST /auth/login` · `POST /auth/refresh` · `src/rosetta/api/auth.py` | ✅ Cumplido | Rate limiting con slowapi; cuentas extra vía `ROSETTA_USERS_EXTRA`. Fail-closed y secreto JWT obligatorio desde `5cf5aac` (B-5) |
| RF-16 | Historial de hallazgos persistente en SQLite con ciclo de vida (activo / en progreso / solucionado) | `src/rosetta/core/session_store.py` | ✅ Cumplido | Append-only, seguro ante concurrencia; 82% cobertura |
| RF-17 | Grafo de correlación interactivo activo↔control (Neo4j + vis.js) | `GET /graph/data` · `src/rosetta/core/graph.py` | ✅ Cumplido | Degrada a modo memoria si Neo4j no disponible; 86% cobertura |
| RF-18 | CLI Typer: `rosetta translate`, `rosetta load-corpus`, `rosetta version` | `src/rosetta/cli/main.py` | ✅ Cumplido | Bajado a 🟡 el 2026-10-04 (0 % de cobertura; el comando es `load-corpus`, no `indexar-corpus`). **Vuelve a ✅**: commit `06bffda`, 20 tests de los 6 comandos (version, translate, load-corpus, dossier, scan, detect-drift); cobertura de `cli/main.py` 87 % |
| RF-19 | Panel de Cumplimiento: estado agregado por marco y controles más incumplidos | `GET /controls/{marco}` · `src/rosetta/core/control_store.py` | ✅ Cumplido | 100% cobertura |
| RF-20a | Catálogo de controles por marco con detalle y estado | `GET /controls/{marco}` · `GET /controls/{marco}/{control_id}` | ✅ Cumplido | |
| RF-20b | Roadmap de vulnerabilidades con trazabilidad temporal de hallazgos | `GET /vuln-roadmap` · `PATCH /findings/{id}/timeline` | ✅ Cumplido | |
| RF-20c | Panel de evidencias: evidencias ligadas a controles y hallazgos | `GET /evidence-panel` | ✅ Cumplido | |
| RF-20d | Análisis de brechas (gap analysis) por marco normativo | `POST /gap-analysis/{marco}` | ✅ Cumplido | |
| RF-20e | Plan director de seguridad generado automáticamente | `POST /plan-director/{marco}` | ✅ Cumplido | |
| RF-20f | Análisis de riesgos sobre activos detectados | `POST /risk-analysis` · `GET /assets` | ✅ Cumplido | |

---

## Requisitos No Funcionales

| ID | Descripción | Módulo / Mecanismo | Estado | Notas |
|----|-------------|-------------------|--------|-------|
| RNF-01 | Degradación grácil ante Neo4j caído (no debe crashear) | `src/rosetta/core/graph.py` | ✅ Cumplido | Fallback a agregación en memoria. Hasta el 2026-10-04 no tenía tests de API y Neo4j caído al arrancar no se detectaba; corregido en `1c567c4` (verify_connectivity + timeouts de 5 s, 4 tests en `test_degradacion.py`) |
| RNF-02 | Cobertura de tests ≥ 80 % en capa core (`src/rosetta/core/`) | pytest-cov | 🟡 Parcial | **Total medido: 77 %**. Core/ entre 76–100 % (pdf_ingestion.py a 76 %, resto ≥ 82 %). ROADMAP exige 80 % core / 60 % adapters. |
| RNF-03 | Sin errores `mypy --strict` en `src/` | mypy | ✅ Cumplido | 56 ficheros, 0 errores |
| RNF-04 | Sin violaciones `ruff check` ni `ruff format` | ruff | ✅ Cumplido | Bajado a 🟡 el 2026-10-04 (`ruff format --check` fallaba en 2 tests por desajuste ruff 0.7.4/0.15.11). **Vuelve a ✅**: commit `7ec6b66` alinea pre-commit con `uv.lock`; CI run 37203612212 (2026-10-04) en verde |
| RNF-05 | Instalable desde cero con `uv sync` + `docker compose up -d --build` | Dockerfile · docker-compose.yml | ✅ Cumplido | Verificado el 2026-10-04 en un clon limpio siguiendo el README: build en 165 s, imagen de 3,85 GB, app y neo4j *healthy*, 197 fragmentos indexados, login con las credenciales de prueba. Dependencias desde `uv.lock` (`2339813`) |
| RNF-06 | Cero secretos reales en el repositorio | gitleaks · pre-commit detect-private-key | ✅ Cumplido | Incidente INC-01 (`docs/P3_SEGURIDAD.md`): credenciales rotadas el 2026-10-04 (antiguas dan 401). Historial limpiado el 2026-10-06 con `git filter-repo` (`f50957f` → `4aeef3b`): 0 apariciones del literal, gitleaks CI en verde. Commit huérfano `e2819f0` accesible en GitHub; purga a GitHub Support pendiente. |
| RNF-07 | Rate limiting en endpoints sensibles (slowapi) | `src/rosetta/api/main.py` | ✅ Cumplido | |
| RNF-08 | Validación de alcance en Modo Auditoría: bloquear IPs privadas/localhost sin declaración explícita | `src/rosetta/core/orchestrator.py:314 _validar_alcance()` | ✅ Cumplido | Bajado a 🟡 el 2026-10-04 (un hostname esquivaba el bloqueo). **Vuelve a ✅**: commit `810812d` (resolución DNS de todas las IP, `is_global`, allowlist de servidor `ROSETTA_AUDIT_ALLOWLIST`, 11 tests) |
| RNF-09 | Tiempo de respuesta del Traductor < 30 s con LLM externo | Pipeline RAG + Claude API | 🟡 Parcial | **Benchmark D-2 (2026-10-04, Ollama qwen2.5:14b, n=5):** p50=8.2s · avg=16.6s · max=41.3s. 4/5 casos bajo el umbral. 1 caso excedió 30 s (41.3s) por generación verbosa + advertencias `marco_desconocido`. Con Claude API (latencia de red ~10-20 s/llamada) el caso típico también cumple; el tail depende de la longitud de la respuesta LLM. El umbrales p50 y promedio están muy por debajo del límite. |
| RNF-10 | Build de CI reproducible (lockfile versionado) | `uv.lock` · `ci.yml` | ✅ Cumplido | Bajado a 🟡 el 2026-10-04 (CI rojo desde el 20/05 en «Install uv»). **Vuelve a ✅**: commit `2e7792d` (setup-uv v7.6.0, actions fijadas por SHA, `uv sync --locked`, matriz real 3.11/3.12); CI run 37203612212 (2026-10-04) en verde |
| RNF-11 | Cabeceras de seguridad HTTP (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) | `SecurityHeadersMiddleware` en `src/rosetta/api/main.py` | ✅ Cumplido | **B-3 implementado**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, CSP con unpkg.com + Google Fonts + `unsafe-inline`. 3 tests en `tests/test_security.py`. |
| RNF-12 | Audit CVE de dependencias en CI (pip-audit) | `ci.yml` job `dependency-audit` | ✅ Cumplido | Bajado a 🟡 el 2026-10-04 (el job auditaba la herramienta, no el proyecto: 140 vulnerabilidades reales). **Vuelve a ✅**: job sobre `uv.lock` (`2e7792d`), 9 tandas de actualización (`2cb138f`…`9a611d7`), solo 4 avisos de chromadb sin parche como riesgo aceptado R-01; CI run 37203612212 (2026-10-04) en verde |

---

## Roadmap P1 no abordado en P3

Estos ítems aparecían en el roadmap futuro del informe P1 pero **nunca fueron requisitos confirmados de P1** ni se incluyen en P3.

| Ítem P1 | Descripción | Decisión P3 | Justificación |
|---------|-------------|-------------|---------------|
| Roadmap F3 | Integración Jira / ServiceNow | No abordado | Feature a medias puntúa menos que menos features que funcionan; fuera del alcance del enunciado |
| Roadmap F5 | Modo SaaS multi-tenant + migración PostgreSQL | No abordado | Requiere rediseño del modelo de datos; complejidad desproporcionada para el plazo |
| Roadmap F4 | Adaptadores Shodan / HIBP contra API real | Trabajo futuro | Solo existe enum (`OrigenHallazgo.SHODAN/HIBP`) + mapa de controles; ningún adaptador implementado. No es RF parcial, es trabajo futuro |
| Roadmap F2 | Versionado del corpus | No abordado | Sin impacto en la demostración de P3 |

---

## Requisitos modificados respecto a P1

| RF/RNF | Versión P1 | Versión P3 | Justificación |
|--------|-----------|-----------|---------------|
| RF-15 | "Autenticación HTTP Basic con ROSETTA_USERS_EXTRA" | **JWT Bearer como principal + HTTP Basic como fallback** | Auth.py declara Bearer como esquema recomendado; Basic solo para clientes heredados y `/docs` |
| RF-20 | Un único ítem de panel avanzado | **Desglosado en RF-20a … RF-20f** | Necesario para trazar cada sub-funcionalidad en la matriz y el vídeo |
| RNF-02 | "≥ 80 % a ojo" | **77 % medido; pdf_ingestion.py a 76 %** | Medición real en Fase 0; objetivo ≥ 80 % core a cerrar en Fase 3 |
| RNF-10 | `uv.lock` en `.gitignore` (build no reproducible) | **Lockfile versionado** | Corregido en B3 (Fase 0) |

---

> **⚠️ Pendiente de validación** — Revisar con el autor antes de incorporar a la memoria técnica.
> Generado: 2026-09-22 · Corregido: 2026-09-22 · Fase 0, P3
