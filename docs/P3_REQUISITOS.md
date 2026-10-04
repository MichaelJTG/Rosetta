# docs/P3_REQUISITOS.md — Tabla de requisitos ROSETTA (Práctica 3)

> Generado en Fase 0 para validar con el tutor antes de continuar.
> Base: informe P1 + commits del repo (46 commits, 389 tests).
> **Pendiente validación por el autor** — marcar cambios antes de usar en la memoria.

---

## Leyenda de estado

| Símbolo | Significado |
|---------|-------------|
| ✅ Cumplido | Implementado, testado, demostrable |
| 🟡 Parcial | Implementado pero incompleto o sin tests suficientes |
| ❌ Descartado | Prometido en P1, eliminado del alcance P3 (con justificación) |
| ➕ Añadido | No estaba en P1; incorporado durante el desarrollo |

---

## Requisitos Funcionales

| ID | Descripción | Endpoint / Módulo | Estado | Notas |
|----|-------------|-------------------|--------|-------|
| RF-01 | Traducir hallazgo técnico a controles normativos con cita literal y justificación | `POST /translate` | ✅ Cumplido | Tool-use forzado con Pydantic; agente Validador crítico |
| RF-02 | Soporte multi-marco: ISO 27001:2022, ENS 2022, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0 (7 marcos) | `POST /translate` + corpus | ✅ Cumplido | Corpus indexado en ChromaDB con `framework_id` |
| RF-03 | Pipeline RAG con ChromaDB para recuperación semántica del corpus normativo | `src/rosetta/rag/` | ✅ Cumplido | Embeddings multilingües, filtro por marco |
| RF-04 | Generación de dosier de auditoría en Markdown y PDF | `POST /reports/generate` | ✅ Cumplido | WeasyPrint para PDF; degrada a MD si WeasyPrint no disponible |
| RF-05 | Ingesta de PDF de auditoría humana (extracción de hallazgos) | `POST /ingest/pdf` | ✅ Cumplido | pdfplumber + respaldo de visión LLM para páginas escaneadas |
| RF-06 | Modo Auditoría automática Red Team (Nmap, Nuclei) con progreso WebSocket | `POST /audit/start` · `WS /audit/ws/{id}` | 🟡 Parcial | Nmap/Nuclei requieren instalación externa; tests con mocks |
| RF-07 | Integración Blue Team — ingesta de alertas Wazuh (JSON/CSV) | `POST /blue/ingest` | ✅ Cumplido | |
| RF-08 | Correlación Red↔Blue: cruzar alertas defensivas con hallazgos ofensivos | `src/rosetta/core/` | ✅ Cumplido | |
| RF-09 | Arquitectura multi-agente con scheduler Soundwave + agente Validador crítico | `src/rosetta/agents/` | ✅ Cumplido | Traductores especializados por marco, ejecución paralela |
| RF-10 | Copilot normativo: preguntas en lenguaje natural con citas y nivel de confianza | `POST /copilot/ask` | ✅ Cumplido | |
| RF-11 | Detección de procedure drift: comparar procedimiento escrito vs. comportamiento observado | `POST /drift/analyze` | ✅ Cumplido | Panel dedicado en dashboard |
| RF-12 | Dashboard SPA con 10 paneles servido desde el backend | `GET /dashboard` | ✅ Cumplido | Inicio, Traducir, PDF, Auditoría, Drift, Cumplimiento, Blue Team, Grafo, Copilot, Hallazgos |
| RF-13 | API REST documentada con OpenAPI (Swagger UI) | `GET /docs` | ✅ Cumplido | 20+ endpoints |
| RF-14 | Gate CI/CD: analizar diff de PR y bloquear si introduce incumplimientos | `POST /analyze-diff` · `.github/workflows/rosetta-gate.yml` | ✅ Cumplido | |
| RF-15 | Autenticación HTTP Basic opcional con soporte de cuentas adicionales (ROSETTA_USERS_EXTRA) | `src/rosetta/api/auth.py` | ✅ Cumplido | JWT con refresh + rate limiting (slowapi) |
| RF-16 | Historial de hallazgos persistente en SQLite con ciclo de vida (activo / en progreso / solucionado) | `src/rosetta/core/session_store.py` | ✅ Cumplido | Append-only, seguro ante concurrencia |
| RF-17 | Grafo de correlación interactivo activo↔control (Neo4j + vis.js) | `GET /graph/data` + panel Grafo | ✅ Cumplido | Degrada a modo memoria si Neo4j no disponible |
| RF-18 | CLI Typer: `rosetta translate`, `rosetta indexar-corpus` | `src/rosetta/cli/` | ✅ Cumplido | |
| RF-19 | Panel de Cumplimiento: estado agregado por marco y controles más incumplidos | `GET /controls/{marco}` | ✅ Cumplido | |
| RF-20 | Panel de gestión avanzada: catálogo de controles, roadmap de vulnerabilidades, evidencias, análisis de gaps, plan director, análisis de riesgos | `GET /vuln-roadmap` · `GET /evidence-panel` · `POST /gap-analysis/{marco}` · `POST /plan-director/{marco}` · `POST /risk-analysis` | ➕ Añadido | No en P1; incorporado en fases 6-7 como mejora del dashboard |
| RF-21 | Adaptadores Shodan/HIBP (sensores OSINT externos) | `src/rosetta/adapters/` | 🟡 Parcial | Código presente; integración real pendiente de keys en producción |
| RF-22 | ~~Integración Jira/ServiceNow~~ | — | ❌ Descartado | Roadmap P1 ítem F3; feature a medias puntúa menos que funcionalidad completa |
| RF-23 | ~~Modo SaaS multi-tenant~~ | — | ❌ Descartado | Roadmap P1 ítem F5; requiere migración PostgreSQL; fuera de alcance temporal |

---

## Requisitos No Funcionales

| ID | Descripción | Módulo / Mecanismo | Estado | Notas |
|----|-------------|-------------------|--------|-------|
| RNF-01 | Degradación grácil ante Neo4j caído (no debe crashear) | `src/rosetta/graph/` | ✅ Cumplido | Fallback a agregación en memoria |
| RNF-02 | Cobertura de tests ≥ 80 % en capa core (`src/rosetta/core/`) | pytest-cov | ✅ Cumplido | 389 tests pasando en Fase 0 |
| RNF-03 | Sin errores `mypy --strict` en `src/` | mypy | ✅ Cumplido | 56 ficheros, 0 errores |
| RNF-04 | Sin violaciones `ruff check` ni `ruff format` | ruff | ✅ Cumplido | 5 archivos corregidos en Fase 0 |
| RNF-05 | Instalable desde cero con `uv sync` + `docker compose up -d --build` | Dockerfile · docker-compose.yml | 🟡 Parcial | A verificar en Fase 1 con instalación limpia |
| RNF-06 | Cero secretos reales en el repositorio | gitleaks · pre-commit detect-private-key | 🟡 Parcial | B1 resuelto en Fase 0; historial pendiente de decisión filter-repo |
| RNF-07 | Rate limiting en endpoints sensibles (slowapi) | `src/rosetta/api/main.py` | ✅ Cumplido | |
| RNF-08 | Validación de alcance en Modo Auditoría (bloquear IPs privadas/localhost sin declaración explícita) | `src/rosetta/core/audit_engine.py` | ✅ Cumplido | Declaración de objetivo obligatoria |
| RNF-09 | Tiempo de respuesta del Traductor < 30 s con LLM externo | Pipeline RAG + Claude API | ✅ Cumplido (en prod) | Dependiente de latencia Anthropic; Ollama local sin límite |
| RNF-10 | Build de CI reproducible (lockfile versionado) | `uv.lock` · `ci.yml` | ✅ Cumplido | Resuelto en B3 (Fase 0) |
| RNF-11 | Cabeceras de seguridad HTTP (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) | Middleware FastAPI | ❌ Pendiente | A implementar en Fase 2 |
| RNF-12 | Audit CVE de dependencias en CI (pip-audit) | `ci.yml` job `dependency-audit` | ✅ Cumplido | Añadido en B5 (Fase 0) |

---

## Requisitos modificados o descartados respecto a P1

| RF/RNF | Versión P1 | Versión P3 | Justificación |
|--------|-----------|-----------|---------------|
| RF-22 | Integración Jira/ServiceNow (roadmap F3) | **Descartado** | Feature a medias puntúa menos que menos features que funcionan |
| RF-23 | Modo SaaS multi-tenant (roadmap F5) | **Descartado** | Requiere migración PostgreSQL; complejidad desproporcionada para el plazo |
| RF-20 | No existía en P1 | **Añadido** | Implementado orgánicamente en fases 6-7; mejora real del producto |
| RNF-10 | `uv.lock` en `.gitignore` | **Corregido** | Build irreproducible detectado en Fase 0; resuelto con B3 |
| RNF-11 | No mencionado en P1 | **Nuevo RNF** | Requisito de seguridad identificado en Fase 0; pendiente Fase 2 |

---

> **⚠️ Pendiente de validación** — Revisar con el autor antes de incorporar a la memoria técnica.
> Generado: 2026-09-22 · Fase 0, P3
