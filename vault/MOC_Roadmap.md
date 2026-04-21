---
title: MOC · Roadmap
tags: [moc, roadmap, rosetta]
created: 2026-04-18
updated: 2026-04-19
---

# MOC · Roadmap ROSETTA

> Map of Content del roadmap. Cada MVP tiene su anchor para poder enlazar desde cualquier nota.
> Fuente canónica: `docs/ROADMAP.md` en el repo. Este MOC es espejo enlazable.

## MVP-0 · Scaffold
Estado: ✅ completado · [[07_Sprints/2026-04-18_sprint-0|Sprint 0]]

Proyecto instalable con `uv sync --extra dev`. Estructura modular. Modelos Pydantic. Esqueletos de todos los módulos. Tests de modelos pasan. ruff ✅ mypy ✅.

## MVP-1 · Traductor Simbiótico sobre ISO 27001:2022
Estado: ✅ completado · [[07_Sprints/2026-04-18_sprint-1|Sprint 1]]

`CorpusLoader` + `NormativaRAG` (ChromaDB, 93 controles indexados) + `TraductorSimbiotico` con RAG + LLM tool-use. CLI `rosetta translate`. 5 hallazgos canónicos → control correcto top-1. Cobertura core ≥99%. 49 tests · ruff ✅ · mypy strict ✅.

**Corpus**: [[03_Normativa/ISO_27001_2022]] · 93 fragmentos en ChromaDB ✅
**LLM**: [[02_ADR/002-abstraccion-llm|ADR-002]] · abstracción multi-proveedor (Claude / Ollama / OpenAI) ✅

## MVP-2 · Grafo de correlación y trazabilidad
Estado: ✅ completado · [[07_Sprints/2026-04-19_sprint-2|Sprint 2]]

`GrafoCorrelacion` con Cypher MERGE idempotente. Consultas: hallazgos por marco, por activo, controles más incumplidos. CLI `rosetta dossier`. `docker-compose.yml` Neo4j 5.18 Community. 56 tests · ruff ✅ · mypy strict ✅.

**Nota**: Neo4j es opcional en la API — sin él los hallazgos se guardan en memoria de sesión.

## MVP-3 · Segundo marco: ENS
Estado: ✅ completado · [[07_Sprints/2026-04-19_sprint-2|Sprint 2]]

Corpus ENS RD 311/2022 (41 controles, BOE público). Traductor multi-marco ISO+ENS simultáneo. 13 tests (3 corpus + 5 canónicos ISO+ENS + 5 edge cases). 69 tests · ruff ✅ · mypy strict ✅.

**Corpus**: [[03_Normativa/ENS_2022]] · 41 fragmentos en ChromaDB ✅ (requiere `load-corpus ens_2022` al arrancar)

## MVP-4 · Primer adaptador Red Team real: Nuclei
Estado: ✅ completado · [[07_Sprints/2026-04-19_sprint-2|Sprint 2]]

`NucleiAdapter` async subprocess · parser JSON Nuclei v3 · mapeo severidad/CVE. CLI `rosetta scan --sensor nuclei --target <objetivo>`. Pipeline completo: nuclei → DatosRedTeam → Traductor → Grafo → dossier Markdown. Flag `--dry-run`. 16 tests (subprocess mockeado). 85 tests · ruff ✅ · mypy strict ✅.

**Pendiente**: smoke test con Nuclei real contra laboratorio.

## MVP-5 · Procedure Drift Detection
Estado: ✅ completado · [[07_Sprints/2026-04-19_sprint-2|Sprint 2]]

Killer feature del mentor [[08_Reuniones/pendiente-carlos-gomez|Carlos Gómez Pintado]]. `DriftDetector.detectar_drift()` con LLM tool-use. CLI `rosetta detect-drift`. Procedimiento canónico `PRO-IAM-001.md` (cuentas IAM inactivas). 8 tests. 93 tests · ruff ✅ · mypy strict ✅.

Ver: [[06_Procedimientos/insight-carlos-procedure-drift]]

## MVP-6 · API REST y dashboard visual
Estado: ✅ completado · [[07_Sprints/2026-04-19_sprint-2|Sprint 2]]

FastAPI con 5 endpoints: `GET /health` · `POST /translate` · `GET /findings` · `GET /compliance/state/{marco}` · `GET /dashboard`. Dashboard HTML embebido (sin dependencias frontend). 102 tests · ruff ✅ · mypy strict ✅.

**Probado con Ollama qwen2.5:14b** (2026-04-19) · traducción real de hallazgo AWS key → controles ISO A.5.23 + A.8.4.

**Arrancar**:
```bash
 $env:PYTHONIOENCODING="utf-8"; uv run uvicorn src.rosetta.api.main:app --reload
# → http://localhost:8000/dashboard
```

## MVP-7 · Gate de CI/CD
Estado: ✅ completado · [[07_Sprints/2026-04-21_sprint-3|Sprint 3]]

GitHub Action reutilizable que llama a la API de ROSETTA sobre el diff de un PR y bloquea si introduce incumplimientos normativos. Comentario en PR con tabla de violaciones (control + archivo + línea + acción).

**Implementado**:
- `POST /analyze-diff` — endpoint FastAPI con `DiffAnalysisRequest` / `DiffAnalysisResponse`.
- `DiffParser` — parsea unified diff en `DiffHunk` (archivos excluidos: lock files, binarios, patrones glob del usuario).
- `DiffAnalyzer` — LLM + RAG por hunk, tool-use con `tiene_violacion` explícito para evitar falsos positivos.
- `action/action.yml` — GitHub Action composite: obtiene diff, lee `.rosetta.yml`, llama API, publica comentario, bloquea PR.
- `.rosetta.yml` — config del repo cliente (marco, bloquear_si, exclude_paths).
- `.github/workflows/rosetta-gate.yml` — workflow de ejemplo.
- **141 tests · ruff ✅ · mypy strict ✅** (39 nuevos en MVP-7).

**Criterio de aceptación cumplido**: PR con `AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"` → bloqueado con ISO A.8.24.

**Archivos**: `src/rosetta/core/diff_analyzer.py` · `src/rosetta/api/main.py` · `src/rosetta/api/schemas.py` · `src/rosetta/api/deps.py` · `action/action.yml` · `.rosetta.yml` · `.github/workflows/rosetta-gate.yml`.

## MVP-8+ · Ampliación de marcos y hardening
Estado: ⚪ no planificado aún

NIS2 · DORA · NIST CSF 2 · PCI-DSS v4 · RGPD · HIPAA · TISAX. Ingestión de PDF (Nessus, Burp Suite, reportes manuales) vía `PDFAdapter`. Firma criptográfica de evidencias (RFC 3161). Multi-tenant. Packaging para despliegue cliente.

---

## Los 9 problemas base

Checklist de validación: cada feature debe resolver uno de estos. Si no, se descarta.

- ✅ R1 · Detección por comportamiento (evasión EDR) — vía BAS + MITRE ATT&CK (parcial)
- ✅ R2 · Fatiga del reconocimiento OSINT — vía adaptadores (NucleiAdapter operativo)
- N/A R3 · Mantenimiento infraestructura ofensiva — ROSETTA es defensivo
- ✅ B1 · Shadow IT — cruce OSINT/inventario en grafo
- ✅ B2 · Alert fatigue — filtrado por relevancia normativa en Traductor
- ✅ B3 · Falta de contexto en incidente — enriquecimiento con grafo Neo4j
- ✅ **N1 · Gap técnico-legal** — núcleo del proyecto, [[02_ADR/001-orquestacion-sobre-fork|Traductor Simbiótico]] · OPERATIVO
- ✅ N2 · Cumplimiento estático vs dinámico — ejecución continua + grafo
- 🟡 N3 · Cadena de suministro — parcial vía hallazgos sobre terceros
