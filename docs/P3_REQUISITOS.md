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
| RF-01 | Traducir hallazgo técnico a controles normativos con cita literal y justificación | `POST /translate` | ✅ Cumplido | Tool-use forzado con Pydantic; agente Validador crítico |
| RF-02 | Soporte multi-marco: ISO 27001:2022, ENS 2022, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0 | `POST /translate` + `corpus/` | ✅ Cumplido | Corpus indexado en ChromaDB con `framework_id` |
| RF-03 | Pipeline RAG con ChromaDB para recuperación semántica del corpus normativo | `src/rosetta/core/rag.py` | ✅ Cumplido | 100% cobertura; embeddings multilingües, filtro por marco |
| RF-04 | Generación de dosier de auditoría en Markdown y PDF | `POST /reports/generate` · `src/rosetta/core/report_generator.py` | ✅ Cumplido | WeasyPrint para PDF; degrada a MD si WeasyPrint no disponible |
| RF-05 | Ingesta de PDF de auditoría humana (extracción de hallazgos) | `POST /ingest/pdf` · `src/rosetta/core/pdf_ingestion.py` | ✅ Cumplido | pdfplumber + respaldo visión LLM para páginas escaneadas |
| RF-06 | Modo Auditoría automática Red Team (Nmap, Nuclei) con progreso WebSocket | `POST /audit/start` · `WS /audit/ws/{audit_id}` · `src/rosetta/adapters/red/` | 🟡 Parcial | Nmap/Nuclei requieren instalación externa; tests con mocks |
| RF-07 | Integración Blue Team — ingesta de alertas Wazuh (JSON/CSV) | `POST /blue/ingest` · `src/rosetta/adapters/blue/wazuh.py` | ✅ Cumplido | |
| RF-08 | Correlación Red↔Blue: cruzar alertas defensivas con hallazgos ofensivos | `src/rosetta/core/blue_enrichment.py` | ✅ Cumplido | 96% cobertura |
| RF-09 | Arquitectura multi-agente con scheduler Soundwave + agente Validador crítico | `src/rosetta/agents/orchestrator.py` · `src/rosetta/agents/soundwave.py` · `src/rosetta/agents/validator.py` | ✅ Cumplido | Traductores especializados por marco (`agents/translator/`), ejecución paralela |
| RF-10 | Copilot normativo: preguntas en lenguaje natural con citas y nivel de confianza | `POST /copilot/ask` · `src/rosetta/core/copilot.py` | ✅ Cumplido | 94% cobertura |
| RF-11 | Detección de procedure drift: comparar procedimiento escrito vs. comportamiento observado | `POST /drift/analyze` · `src/rosetta/core/drift.py` | ✅ Cumplido | 95% cobertura; panel dedicado en dashboard |
| RF-12 | Dashboard SPA con 10 paneles servido desde el backend | `GET /dashboard` · `src/rosetta/api/dashboard.py` | ✅ Cumplido | Inicio, Traducir, PDF, Auditoría, Drift, Cumplimiento, Blue Team, Grafo, Copilot, Hallazgos |
| RF-13 | API REST documentada con OpenAPI (Swagger UI) | `GET /docs` · `GET /openapi.json` | ✅ Cumplido | 20+ endpoints |
| RF-14 | Gate CI/CD: analizar diff de PR y bloquear si introduce incumplimientos normativos | `POST /analyze-diff` · `src/rosetta/core/diff_analyzer.py` · `.github/workflows/rosetta-gate.yml` | ✅ Cumplido | 88% cobertura |
| RF-15 | Autenticación JWT (Bearer) como esquema principal; HTTP Basic como fallback para clientes heredados y `/docs` | `POST /auth/login` · `POST /auth/refresh` · `src/rosetta/api/auth.py` | ✅ Cumplido | Rate limiting con slowapi; cuentas adicionales vía `ROSETTA_USERS_EXTRA` |
| RF-16 | Historial de hallazgos persistente en SQLite con ciclo de vida (activo / en progreso / solucionado) | `src/rosetta/core/session_store.py` | ✅ Cumplido | Append-only, seguro ante concurrencia; 82% cobertura |
| RF-17 | Grafo de correlación interactivo activo↔control (Neo4j + vis.js) | `GET /graph/data` · `src/rosetta/core/graph.py` | ✅ Cumplido | Degrada a modo memoria si Neo4j no disponible; 86% cobertura |
| RF-18 | CLI Typer: `rosetta translate`, `rosetta indexar-corpus` | `src/rosetta/cli/main.py` | ✅ Cumplido | |
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
| RNF-01 | Degradación grácil ante Neo4j caído (no debe crashear) | `src/rosetta/core/graph.py` | ✅ Cumplido | Fallback a agregación en memoria |
| RNF-02 | Cobertura de tests ≥ 80 % en capa core (`src/rosetta/core/`) | pytest-cov | 🟡 Parcial | **Total medido: 77 %**. Core/ entre 76–100 % (pdf_ingestion.py a 76 %, resto ≥ 82 %). ROADMAP exige 80 % core / 60 % adapters. |
| RNF-03 | Sin errores `mypy --strict` en `src/` | mypy | ✅ Cumplido | 56 ficheros, 0 errores |
| RNF-04 | Sin violaciones `ruff check` ni `ruff format` | ruff | ✅ Cumplido | 5 archivos corregidos en Fase 0 |
| RNF-05 | Instalable desde cero con `uv sync` + `docker compose up -d --build` | Dockerfile · docker-compose.yml | 🟡 Parcial | A verificar en Fase 1 con instalación limpia |
| RNF-06 | Cero secretos reales en el repositorio | gitleaks · pre-commit detect-private-key | 🟡 Parcial | Literal de la contraseña del evaluador eliminado en Fase 0; historial pendiente de decisión filter-repo |
| RNF-07 | Rate limiting en endpoints sensibles (slowapi) | `src/rosetta/api/main.py` | ✅ Cumplido | |
| RNF-08 | Validación de alcance en Modo Auditoría: bloquear IPs privadas/localhost sin declaración explícita | `src/rosetta/core/orchestrator.py:314 _validar_alcance()` | ✅ Cumplido | Lista negra de redes RFC1918 + `_HOSTS_PROHIBIDOS`; declaración mínima 10 chars |
| RNF-09 | Tiempo de respuesta del Traductor < 30 s con LLM externo | Pipeline RAG + Claude API | 🟡 Pendiente benchmark | Valor no medido formalmente; depende de latencia Anthropic; Ollama local sin límite |
| RNF-10 | Build de CI reproducible (lockfile versionado) | `uv.lock` · `ci.yml` | ✅ Cumplido | Resuelto en B3 (Fase 0) |
| RNF-11 | Cabeceras de seguridad HTTP (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) | Middleware FastAPI | ❌ Pendiente | A implementar en Fase 2 |
| RNF-12 | Audit CVE de dependencias en CI (pip-audit) | `ci.yml` job `dependency-audit` | ✅ Cumplido | Añadido en B5 (Fase 0); 0 CVEs en baseline |

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
