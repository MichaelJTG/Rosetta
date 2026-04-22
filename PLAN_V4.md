# PLAN V4 — Instrucciones de ejecución para Claude Code

> **MODO: EJECUCIÓN AUTÓNOMA SILENCIOSA**
> - NO preguntes al usuario salvo los 8 checkpoints de MISSION.md
> - NO expliques lo que vas a hacer, solo hazlo
> - Reporta SOLO al terminar cada FASE completa
> - Optimiza tokens: sin resúmenes intermedios, sin repetir contexto

---

## Estado actual del proyecto

El código actual tiene: Traductor Simbiótico, RAG ChromaDB, Grafo Neo4j, Procedure Drift,
Diff Analyzer, LLM multi-proveedor (Claude/Ollama/OpenAI), API REST (6 endpoints),
Dashboard básico (3 paneles con bugs). Todo funcional pero incompleto.

**La visión ha cambiado.** El plan anterior (mejorar el dashboard) queda OBSOLETO.
Sigue SOLO este plan v4.

---

## VISIÓN REAL

ROSETTA = plataforma de auditoría de seguridad con IA.
- MODO A: auditor automático (configura alcance → ejecuta herramientas Red Team)
- MODO B: importar PDF de auditor humano (extrae hallazgos con LLM visión)
- Blue Team opcional (Wazuh)
- SIEMPRE genera informe MD + PDF (marca ROSETTA + opción marca cliente)
- 7 marcos normativos europeos
- 16 agentes especializados (1 por marco + orquestador + validador + etc.)
- 4 killer features: Attack Chain, Remediation Validator, Compliance Timeline, Copilot

---

## FASES DE CONSTRUCCIÓN (ejecutar en orden)

### FASE 1 — Fundaciones
1. Cargar corpus ISO 27001 en ChromaDB (PDF en `corpus/iso27001/`)
2. Cargar corpus ENS (descargar del BOE, público)
3. Cargar corpus NIS2 (descargar de EUR-Lex, público)
4. `core/report_generator.py`: genera MD + PDF (WeasyPrint)
5. Marca ROSETTA por defecto + campo opcional logo/nombre cliente
6. Endpoint `POST /reports/generate`
7. Tests de cada componente

### FASE 2 — Modo B: PDF de auditor
1. `core/pdf_ingestion.py` con `pdfplumber` + `pdf2image` (MIT, NO usar PyMuPDF/AGPL)
2. LLM con visión extrae hallazgos → `DatosRedTeam`
3. Endpoint `POST /ingest/pdf`
4. Pantalla upload en dashboard con preview
5. Tests

### FASE 3 — Modo A: Auditor automático
1. `core/orchestrator.py`: alcance configurable, ejecución paralela asyncio
2. Completar `adapters/red/nuclei.py` + crear `adapters/red/nmap.py`
3. Pantalla configuración auditoría en dashboard
4. WebSocket para progreso en tiempo real
5. Controles: declaración alcance autorizado, rate limiting, lista negra
6. Tests

### FASE 4 — Blue Team
1. `adapters/blue/wazuh.py` completo (API automática + upload manual JSON/CSV)
2. Lógica enriquecimiento Red ↔ Blue en informe
3. Pantalla Blue Team en dashboard (opcional/skip)
4. Tests

### FASE 5 — Killer Features + Multi-Agente
1. Refactor Traductor monolítico → 16 agentes (ver `vault/10_Agentes/MOC_Agentes.md`)
   - ADR-004 PRIMERO (`vault/02_ADR/004-arquitectura-multi-agente.md`)
   - 7 Traductores (ISO, ENS, NIS2, DORA, RGPD, NIST, PCI)
   - Rosetta orquestador + Soundwave scheduler
   - Validador + Crucero + Dossiero + Gatemaster + Reconocedor + Vigilante + Deriva
   - LiteLLM gateway (eco/max/test por agente)
2. `core/attack_chain.py`: encadenar vulns con MITRE ATT&CK + Neo4j
3. `core/remediation_validator.py`: re-test para verificar fix
4. `core/compliance_timeline.py`: snapshots históricos + gráficos Chart.js
5. `core/copilot.py`: chat LN sobre estado compliance (endpoint `POST /copilot/ask`)
6. Tests de todo

### FASE 6 — Corpus adicionales
1. Cargar DORA, RGPD, NIST CSF 2.0 (todos públicos)
2. PCI-DSS 4.0
3. Tests multi-marco cruzados

### FASE 7 — Polish
1. Dashboard responsive
2. Autenticación básica
3. Historial sesiones persistente (SQLite)
4. Visualización grafo Neo4j en dashboard (vis.js)
5. Procedure Drift panel en dashboard

---

## REGLAS DE EJECUCIÓN

1. **Tests primero (TDD)**: Red → Green → Refactor
2. **ADR antes de cambio de arquitectura** (obligatorio en Fase 5)
3. **`ruff check` + `mypy` + `pytest`** verdes antes de cerrar cada fase
4. **Bitácora** (`vault/00_Bitacora.md`): entrada al inicio y cierre de cada fase
5. **Dashboard** (`vault/00_Dashboard.md`): actualizar al cerrar cada fase
6. **Commits atómicos**: Conventional Commits
7. **NO preguntar** salvo checkpoints de MISSION.md §3
8. **Reportar** solo al terminar cada FASE con: qué se hizo, tests pasados, próximo paso

---

## DEPENDENCIAS A INSTALAR

```
pdfplumber pdf2image weasyprint litellm
```

CDN (solo en HTML del dashboard): `chart.js`, `vis.js`

No instalar PyMuPDF (AGPL). Poppler necesario para pdf2image (system dep).

---

## CONFIGURACIÓN LOCAL (UNSLOTH / QWEN)
Para pruebas locales con **Unsloth (Qwen 3.5)**, Claude Code debe dejar preparado el `.env.example` con:
`LLM_PROVIDER=openai` (usando LiteLLM)
`OPENAI_BASE_URL=http://localhost:8000/v1` (puerto por defecto de Unsloth/vLLM)
`OPENAI_API_KEY=unsloth`
