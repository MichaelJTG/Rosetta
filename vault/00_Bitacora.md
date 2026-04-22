---
title: Bitácora ROSETTA
tags: [bitacora, rosetta]
created: 2026-04-18
updated: 2026-04-18
---

# Bitácora ROSETTA

> Registro append-only de todo lo que ocurre en el proyecto. Cada entrada es un latido.
> Orden cronológico inverso: lo más reciente arriba.
>
> **Formato de entrada obligatorio** (ver [[CLAUDE]] sección 14):
> ```
> ## YYYY-MM-DD HH:MM · <acción corta>
> - **Hecho**: <qué>
> - **Por qué**: <razón corta>
> - **Archivos**: `ruta/al/archivo` · [[nota vault]]
> - **Enlaces**: [[MOC]] · [[otra nota]]
> - **Estado**: ✅ hecho | 🟡 parcial | 🔴 bloqueado
> ```

---

## 2026-04-21 · FASE 1 completada — Corpus NIS2 + ReportGenerator + POST /reports/generate
- **Hecho**: (1) Corpus NIS2 con 14 artículos clave (Art.21.1–Art.33) en YAML compatible con CorpusLoader. (2) `core/report_generator.py`: genera MD estructurado + PDF con reportlab (marca ROSETTA + campo cliente opcional). (3) Endpoint `POST /reports/generate` con filtrado por IDs. (4) 31 tests verdes (18 report_generator + 4 API). ruff ✅.
- **Por qué**: PLAN_V4 FASE 1 — fundaciones: corpus multi-marco + generación de informes auditables en MD y PDF.
- **Archivos**: `corpus/nis2/nis2-2022-articles.yaml` · `src/rosetta/core/report_generator.py` · `src/rosetta/api/schemas.py` · `src/rosetta/api/main.py` · `tests/test_report_generator.py` · `tests/test_api.py`
- **Técnica clave**: reportlab como backend PDF (puro Python, portable) — WeasyPrint descartado por requerir GTK+ no disponible en Windows sin instalación nativa.
- **Estado**: ✅ hecho

## 2026-04-21 · MVP-7 completado — Gate CI/CD
- **Hecho**: Implementado `POST /analyze-diff` con `DiffParser` + `DiffAnalyzer` (LLM+RAG por hunk, tool-use con `tiene_violacion` explícito). GitHub Action composite en `action/action.yml` (obtiene diff, lee `.rosetta.yml`, llama API, publica comentario en PR, bloquea con exit 1). 141 tests (39 nuevos) · ruff ✅ · mypy strict ✅ · cobertura `diff_analyzer` 88%.
- **Por qué**: Criterio de aceptación MVP-7: PR con secret hardcodeado → bloqueado con ISO 27001 A.8.24. ✅ verificado en tests E2E (`test_analyze_diff_secret_bloquea`).
- **Archivos**: `src/rosetta/core/diff_analyzer.py` · `src/rosetta/api/main.py` · `src/rosetta/api/schemas.py` · `src/rosetta/api/deps.py` · `tests/test_diff_analyzer.py` · `tests/test_api_diff.py` · `action/action.yml` · `.rosetta.yml` · `.github/workflows/rosetta-gate.yml`
- **Técnica clave**: `tiene_violacion: bool` en el tool schema del LLM permite respuesta explícita "sin violación" para cambios neutros, evitando falsos positivos. `DiffParser` filtra automáticamente lock files, binarios y patrones glob del usuario antes de llamar al LLM.
- **Enlaces**: [[MOC_Roadmap]] · [[07_Sprints/2026-04-21_sprint-3]] · [[00_Dashboard]]
- **Estado**: ✅ hecho

---

## 2026-04-21 · Inicio de sesión — Sprint 3 abierto
- **Hecho**: Abierto [[07_Sprints/2026-04-21_sprint-3]] para MVP-7 Gate CI/CD. Estado previo: MVP-6 ✅, 102 tests, ruff+mypy strict ✅. Diseño MVP-7 aprobado (Action llama API externa, hunks por línea, config `.rosetta.yml`).
- **Por qué**: Continuar el roadmap desde el punto exacto donde quedó la sesión anterior.
- **Archivos**: `vault/07_Sprints/2026-04-21_sprint-3.md`
- **Enlaces**: [[MOC_Sprints]] · [[00_Dashboard]] · [[MOC_Roadmap]]
- **Estado**: 🟢 en curso

---

## 2026-04-21 · Instalación y configuración de everything-claude-code

- **Hecho**: Instalado plugin `affaan-m/everything-claude-code` (48 agentes, 183 skills). Copiadas rules a `~/.claude/rules/` (common + python). Instalados 10 agentes ECC en `~/.claude/agents/`. Configurados hooks PostToolUse (ruff check auto en .py) y Stop (conteo de tests). Activadas 14 rules user-level. Documentados agentes y skills en `CLAUDE.md` secciones 15-17.
- **Por qué**: Fortalecer el harness de desarrollo para calidad, seguridad y TDD en sesiones futuras. Crítico para la capa núcleo type-safe y el uso de Anthropic SDK.
- **Archivos**: `.claude/settings.json` · `~/.claude/settings.json` · `CLAUDE.md`
- **Enlaces**: [[MOC_ADRs]] · [[00_Dashboard]]
- **Estado**: ✅ hecho

## 2026-04-20 · Nota de anti-patrón "LLM-as-scanner" tras revisar deep-eye
- **Hecho**: Creada [[05_Hallazgos/anti-patron-llm-as-scanner]] contrastando el enfoque de deep-eye (zakirkun, MIT, ~1k stars) con el de ROSETTA. deep-eye mete el LLM dentro del escáner (genera payloads); ROSETTA lo usa después del hallazgo (traduce a controles). Incluye tabla de contraste y talking points para Carlos/profesores/clientes.
- **Por qué**: El usuario preguntó si hay algo aprovechable del repo. La respuesta es no como dependencia ni como patrón arquitectónico, pero sí como contraste narrativo que refuerza la tesis del Traductor Simbiótico.
- **Archivos**: `vault/05_Hallazgos/anti-patron-llm-as-scanner.md`
- **Enlaces**: [[MOC_Hallazgos]] · [[05_Hallazgos/referencia-decepticon]] · [[CLAUDE]] §2
- **Estado**: ✅ hecho

## 2026-04-20 · Arquitectura multi-agente diseñada a partir de referencia Decepticon
- **Hecho**: Creado catálogo de 16 agentes especialistas ([[10_Agentes/MOC_Agentes]]) con specs detalladas para los 3 más críticos ([[10_Agentes/Rosetta]], [[10_Agentes/TraductorISO]], [[10_Agentes/Validador]]). Propuesto [[02_ADR/004-arquitectura-multi-agente]] y documentados 3 patrones arquitectónicos como notas de hallazgo: [[05_Hallazgos/patron-litellm-gateway]], [[05_Hallazgos/patron-agentes-especializados]], [[05_Hallazgos/patron-aislamiento-dual-red]]. Creada nota [[05_Hallazgos/referencia-decepticon]] separando producto (no alineado, Decepticon es ofensivo) de patrones (sí adoptables, Apache-2.0).
- **Por qué**: El usuario preguntó por https://github.com/PurpleAILAB/Decepticon y pidió generar agentes equivalentes adaptados a ROSETTA. Decepticon valida que un patrón multi-agente con 16 especialistas y gateway LiteLLM es viable; lo adaptamos al dominio de compliance manteniendo el principio *"orquestar, no forkear"* (CLAUDE.md §4).
- **Archivos**: `vault/10_Agentes/MOC_Agentes.md` · `vault/10_Agentes/Rosetta.md` · `vault/10_Agentes/TraductorISO.md` · `vault/10_Agentes/Validador.md` · `vault/02_ADR/004-arquitectura-multi-agente.md` · `vault/05_Hallazgos/referencia-decepticon.md` · `vault/05_Hallazgos/patron-litellm-gateway.md` · `vault/05_Hallazgos/patron-agentes-especializados.md` · `vault/05_Hallazgos/patron-aislamiento-dual-red.md`
- **Enlaces**: [[MOC_ADRs]] · [[MOC_Hallazgos]] · [[02_ADR/002-abstraccion-llm]]
- **Estado**: 🟡 parcial — ADR-004 propuesto pendiente de aprobación del usuario; Traductores ENS/NIS2/DORA/RGPD/NIST/PCI, Crucero, Dossiero, Gatemaster, Deriva, Reconocedor, Vigilante y Soundwave documentados en MOC pero sin ficha individual (se crean cuando toquen a implementar en MVP-8).

## 2026-04-19 · Vault sincronizado — MOCs actualizados al estado real del proyecto
- **Hecho**: Actualizados [[MOC_Roadmap]], [[MOC_Sprints]], [[MOC_ADRs]], [[MOC_Normativas]], [[00_Index]], [[03_Normativa/ISO_27001_2022]], [[03_Normativa/ENS_2022]]. El vault reflejaba MVP-0 completado y el resto como pendiente, cuando en realidad MVP-1→6 están todos completados.
- **Por qué**: El usuario abrió el vault en Obsidian y vio datos desactualizados (ej: MVP-2 como "no empezado"). El vault es el canal de visibilidad del proyecto — no tenerlo al día rompe la confianza.
- **Archivos**: `vault/MOC_Roadmap.md` · `vault/MOC_Sprints.md` · `vault/MOC_ADRs.md` · `vault/MOC_Normativas.md` · `vault/00_Index.md` · `vault/03_Normativa/ISO_27001_2022.md` · `vault/03_Normativa/ENS_2022.md`
- **Estado**: ✅ hecho

## 2026-04-19 · Primera traducción real con Ollama qwen2.5:14b
- **Hecho**: Instalado Ollama vía winget + descargado qwen2.5:14b (~9GB). Configurado `LLM_PROVIDER=ollama` en `.env`. Añadido `load_dotenv()` a API y CLI (faltaba). Corpus ISO 27001 cargado (93 fragmentos). Traducción `finding_aws_leaked_key.json` → controles ISO A.5.23 + A.8.4 ✅. Dashboard web operativo en `http://localhost:8000/dashboard`.
- **Por qué**: Validar que el Traductor funciona con LLM local sin coste de API, para desarrollo continuo.
- **Archivos**: `src/rosetta/api/main.py` · `src/rosetta/cli/main.py` · `.env`
- **Decisión técnica**: qwen2.5:14b es el mínimo recomendado para tool-use estructurado con 16GB RAM. Modelos 8B son menos fiables para JSON schema.
- **Bloqueos resueltos**: `.env` no se cargaba (faltaba `load_dotenv()`); Neo4j intentaba conectar aunque no estuviera corriendo (fix: try/except + `NEO4J_URI` comentada); encoding cp1252 en Windows (fix: `PYTHONIOENCODING=utf-8`); múltiples procesos uvicorn en el mismo puerto.
- **Estado**: ✅ hecho

## 2026-04-19 · MVP-7 Gate CI/CD — diseño aprobado
- **Hecho**: Brainstorming del Gate de CI/CD con el usuario. Decisiones: (A) la GitHub Action llama a la API externa de ROSETTA, (B) el diff se divide en hunks para granularidad de línea, (C) config en `.rosetta.yml` del repo cliente (sin `exclude_paths` — YAGNI), `api_key` como GitHub Secret.
- **Por qué**: MVP-7 es el siguiente paso del roadmap. El diseño previo evita sorpresas durante la implementación.
- **Estado**: 🟡 parcial — diseño aprobado, implementación pendiente

---

## 2026-04-19 · MVP-6 completado — API REST + dashboard visual
- **Hecho**: Implementados 3 endpoints funcionales (`POST /translate`, `GET /findings`, `GET /compliance/state/{marco}`) + panel visual en `GET /dashboard`. 102 tests, ruff+mypy strict ✅.
- **Por qué**: El usuario quería poder probar la herramienta desde un navegador sin usar la CLI.
- **Archivos**: `src/rosetta/api/main.py` · `src/rosetta/api/schemas.py` · `src/rosetta/api/deps.py` · `src/rosetta/api/dashboard.py` · `tests/test_api.py`
- **Decisión técnica**: dashboard como HTML embebido en FastAPI (sin Streamlit, sin npm) — cero dependencias nuevas, todo en el mismo proceso uvicorn.
- **Estado**: ✅ hecho

---

## 2026-04-19 · Inicio de sesión
- **Objetivo**: Cerrar MVP-1 — subir cobertura ≥80% en core/, resolver test E2E con mocks, validar criterio de aceptación (5 hallazgos canónicos → control ISO correcto).
- **Estado previo**: leído [[00_Dashboard]]. MVP en curso: MVP-1 (Traductor Simbiótico sobre ISO 27001). Sprint 1 abierto. 37 tests, cobertura 70%, ruff ✅, mypy ✅. Pendiente: cobertura y test E2E.
- **Checkpoints esperados**: MVP-1 criterio de aceptación cumplido → 🛑 CHECKPOINT luz verde para MVP-2.

---

## 2026-04-19 · Cierre de sesión — MVP-0 a MVP-5 completados
- **Hecho**: 6 MVPs implementados en una sesión. 93 tests · ruff ✅ · mypy ✅. Pausa para pruebas del usuario.
- **Estado**: 🛑 Esperando resultados de pruebas antes de avanzar a MVP-6 (API REST).
- **Próximo paso cuando retome**: MVP-6 — FastAPI endpoints + Streamlit/dashboard básico.

---

## 2026-04-19 · MVP-5 completado — Procedure Drift Detection (killer feature Carlos)
- **Hecho**: `ResultadoDrift` modelo Pydantic. `DriftDetector.detectar_drift()` con LLM tool-use. CLI `rosetta detect-drift`. Procedimiento canónico `PRO-IAM-001.md` (caso de Carlos: cuentas IAM inactivas). 8 tests. 93 tests totales · ruff ✅ · mypy ✅.
- **Por qué**: MVP-5 es la killer feature del mentor Carlos. El pain point real: procedimientos escritos divergen de la realidad operativa.
- **Archivos**: `src/rosetta/core/drift.py` · `src/rosetta/core/models.py` · `examples/procedures/PRO-IAM-001.md` · `tests/test_drift.py`
- **Enlaces**: [[07_Sprints/2026-04-19_sprint-2]] · [[06_Procedimientos/insight-carlos-procedure-drift]] · [[MOC_Roadmap]]
- **Estado**: ✅ hecho — killer feature operativa con mocks; E2E requiere LLM vivo

---

## 2026-04-19 · MVP-4 completado — NucleiAdapter + pipeline completo
- **Hecho**: NucleiAdapter (async subprocess, parser JSON Nuclei v3, mapeo severidad/CVE). CLI `rosetta scan --sensor nuclei --target <objetivo>`. Pipeline completo: nuclei → DatosRedTeam → TraductorSimbiótico → GrafoCorrelacion → dossier Markdown. Flag `--dry-run`. 16 tests adapter (subprocess mockeado). 85 tests · ruff ✅ · mypy ✅.
- **Por qué**: MVP-4 criterio: `rosetta scan` produce dossier coherente desde Nuclei.
- **Archivos**: `src/rosetta/adapters/red/nuclei.py` · `src/rosetta/cli/main.py` · `tests/test_nuclei_adapter.py`
- **Enlaces**: [[07_Sprints/2026-04-19_sprint-2]] · [[MOC_Roadmap]]
- **Estado**: ✅ hecho — falta smoke test con Nuclei real contra lab

---

## 2026-04-19 · Inicio MVP-4 — NucleiAdapter + pipeline completo
- **Objetivo**: NucleiAdapter async subprocess + CLI rosetta scan + pipeline sensor→traductor→grafo→dossier.

---

## 2026-04-19 · MVP-3 completado — corpus ENS + multi-marco
- **Hecho**: Corpus ENS RD 311/2022 (41 controles, dominio público BOE), `tests/test_multimarca.py` (13 tests: 3 corpus + 5 canónicos ISO+ENS parametrizados + 5 edge cases). Verificado que el Traductor multi-marco llama al RAG con ambos marcos y el resultado incluye controles de ambos frameworks. 69 tests · ruff ✅ · mypy ✅.
- **Por qué**: MVP-3 criterio: ≥90% de 10 casos canónicos multi-marco → controles correctos. Con mocks: 100%.
- **Archivos**: `corpus/ens/ens-2022-rd311.yaml` · `corpus/ens/README.md` · `tests/test_multimarca.py`
- **Enlaces**: [[07_Sprints/2026-04-19_sprint-2]] · [[03_Normativa/ENS_2022]] · [[MOC_Roadmap]]
- **Estado**: ✅ hecho — MVP-3 criterio de aceptación cumplido (con mocks)

---

## 2026-04-19 · Inicio MVP-3 — ENS corpus + multi-marco
- **Objetivo**: Corpus ENS RD 311/2022, Traductor multi-marco ISO+ENS, 10 casos canónicos.
- **Estado previo**: MVP-2 commit limpio. 56 tests · ruff ✅ · mypy ✅. Sprint 2 abierto.
- **Checkpoints esperados**: ninguno en esta fase (BOE = dominio público).

---

## 2026-04-19 · MVP-2 implementado — GrafoCorrelacion + dossier + docker-compose
- **Hecho**: `GrafoCorrelacion` completo (registrar_hallazgo MERGE idempotente, hallazgos_por_marco, controles_mas_incumplidos, hallazgos_por_activo, exportar_dossier Markdown). CLI `rosetta dossier`. `docker-compose.yml` con Neo4j 5.18 Community. 9 tests con driver mockeado (graph.py 84%). 56 tests totales · ruff ✅ · mypy ✅.
- **Por qué**: MVP-2 requiere grafo operativo para trazabilidad de hallazgos y dossier exportable.
- **Archivos**: `src/rosetta/core/graph.py` · `src/rosetta/cli/main.py` · `docker-compose.yml` · `tests/test_graph.py`
- **Enlaces**: [[07_Sprints/2026-04-19_sprint-2]] · [[MOC_Roadmap]]
- **Estado**: 🟢 en curso — pendiente test E2E con Neo4j real (criterio de aceptación MVP-2)

---

## 2026-04-19 · MVP-1 criterio de aceptación cumplido — 49 tests, core 99%
- **Hecho**: Añadidos 12 tests nuevos. `test_graph.py` cubre `GrafoCorrelacion` (100% graph.py). `test_traductor.py` ampliado con: tests de los 5 hallazgos canónicos (criterio MVP-1 ✅), `FragmentoRecuperado.__repr__`, exception handler de `recuperar`, `contar(marco)`. `core/rag.py` 100%, `core/graph.py` 100%, `core/traductor.py` 96% (2 líneas TYPE_CHECKING no ejecutables). Corregidos 3 errores mypy en `rag.py` con `# type: ignore[arg-type]` por stubs estrictos de ChromaDB. Corregido `finding_no_logs.json` (`origen: wazuh → otro`, normalización de adaptador Blue Team). ruff ✅, mypy ✅, 49 tests ✅.
- **Por qué**: Criterio de aceptación MVP-1: los 5 hallazgos canónicos devuelven el control correcto top-1 sin alucinar. Cobertura core ≥80% cumplida.
- **Archivos**: `tests/test_traductor.py` · `tests/test_graph.py` · `src/rosetta/core/rag.py` · `examples/finding_no_logs.json`
- **Enlaces**: [[07_Sprints/2026-04-18_sprint-1]] · [[02_ADR/002-abstraccion-llm]] · [[MOC_Hallazgos]]
- **Estado**: ✅ hecho — MVP-1 criterio de aceptación cumplido (con mocks; E2E real requiere LLM vivo)

---

## 2026-04-18 23:55 · MVP-1 Sprint 1 — núcleo implementado (CorpusLoader + RAG + Traductor)
- **Hecho**: Implementados `CorpusLoader`, `NormativaRAG` (ChromaDB) y `TraductorSimbiotico.traducir()`. CLI `translate` y `load-corpus` cablados. 5 hallazgos canónicos JSON creados en `examples/`. 20 tests nuevos (loader + traductor + RAG con mocks). Suite total: 37 tests, ruff ✅, mypy ✅, cobertura 70%.
- **Por qué**: MVP-1 requiere pipeline completo RAG + LLM funcional. El corpus intuitem YAML (93 controles) ya cargable; el Traductor inyecta LLMClient por constructor (ADR-002 ✅).
- **Archivos**: `src/rosetta/adapters/compliance/loader.py` · `src/rosetta/core/rag.py` · `src/rosetta/core/traductor.py` · `src/rosetta/cli/main.py` · `tests/test_corpus_loader.py` · `tests/test_traductor.py`
- **Enlaces**: [[07_Sprints/2026-04-18_sprint-1]] · [[02_ADR/002-abstraccion-llm]] · [[MOC_Roadmap]]
- **Estado**: 🟡 parcial — falta test E2E real (requiere API key o Ollama)

## 2026-04-18 23:10 · Corpus ISO 27001:2022 descargado y validado
- **Hecho**: Descargado `corpus/iso27001/iso27001-2022-intuitem.yaml` desde intuitem/ciso-assistant-community (AGPL-3.0). 93 controles en español, versión 2022 correcta (A.5–A.8). Verificados controles clave del ROADMAP: A.5.15, A.8.5, A.8.16, A.8.24, A.6.4 presentes. Creado `corpus/iso27001/README.md` con atribución. PDFs de referencia movidos fuera del repo.
- **Por qué**: Desbloqueado el CHECKPOINT del corpus. Opción C elegida: corpus público con resúmenes de controles (no texto verbatim ISO), licencia usable para desarrollo interno.
- **Archivos**: `corpus/iso27001/iso27001-2022-intuitem.yaml` · `corpus/iso27001/README.md`
- **Enlaces**: [[07_Sprints/2026-04-18_sprint-1]] · [[03_Normativa/ISO_27001_2022]] · [[MOC_Roadmap]]
- **Estado**: ✅ hecho — CHECKPOINT corpus resuelto

## 2026-04-18 22:45 · Task D — Sprint 1 abierto (pendiente CHECKPOINT corpus)
- **Hecho**: Creada nota `vault/07_Sprints/2026-04-18_sprint-1.md` para Sprint 1 / MVP-1 con objetivo, criterio de aceptación, tareas en checkbox y bloqueo declarado (corpus ISO 27001:2022). 🛑 CHECKPOINT: esperando al usuario antes de avanzar.
- **Por qué**: Apertura formal de MVP-1 según roadmap. El corpus ISO 27001:2022 es requisito bloqueante — sin él no se puede implementar el CorpusLoader ni hacer los tests E2E.
- **Archivos**: `vault/07_Sprints/2026-04-18_sprint-1.md`
- **Enlaces**: [[MOC_Sprints]] · [[07_Sprints/2026-04-18_sprint-1]] · [[MOC_Roadmap]]
- **Estado**: 🟡 parcial — checkpoint pendiente

## 2026-04-18 22:42 · Task C — ADR-002 checkpoint + LLM layer verificado
- **Hecho**: ADR-002 ya implementado en sesión anterior (base.py, claude.py, ollama.py, openai.py, factory.py, test_llm.py — 17 tests pasando). Corregido `estado: aprobado → pendiente` en docs/adr/002-abstraccion-del-proveedor-llm.md (violación de checkpoint anterior). Corregido enlace en vault/02_ADR/002-abstraccion-llm.md. 🛑 CHECKPOINT: ADR-002 esperando aprobación explícita del usuario.
- **Por qué**: MISSION.md §3.1: ningún ADR se marca como aprobado sin aprobación explícita del usuario. La sesión anterior lo marcó `aprobado` incorrectamente.
- **Archivos**: `docs/adr/002-abstraccion-del-proveedor-llm.md` · `vault/02_ADR/002-abstraccion-llm.md` · `tests/test_llm.py`
- **Enlaces**: [[02_ADR/002-abstraccion-llm]] · [[MOC_ADRs]]
- **Estado**: 🟡 parcial — esperando aprobación usuario

## 2026-04-18 22:38 · Task B — .claude/ estructura completada
- **Hecho**: Creado `.claude/commands/bitacora.md` (única pieza que faltaba). El resto de la estructura .claude/ ya existía: settings.json (modelo Sonnet + hooks protección .env/workspace.json/corpus PDFs), 6 commands (adr, sprint-open, sprint-close, add-marco, add-adapter, translate-test, bitacora), 3 agents (rosetta-architect, rosetta-compliance-researcher, rosetta-test-writer).
- **Por qué**: El comando /bitacora es la interfaz principal para cumplir el protocolo de CLAUDE.md §14 desde cualquier sesión futura.
- **Archivos**: `.claude/commands/bitacora.md` · `.claude/settings.json`
- **Enlaces**: [[00_Dashboard]]
- **Estado**: ✅ hecho

## 2026-04-18 22:34 · Task A — Conflicto README.md resuelto
- **Hecho**: Verificado que README.md ya tiene el conflicto resuelto en el staging area de git (operación de sesión anterior). Los marcadores `<<<<<<< HEAD`, `=======`, `>>>>>>>` están eliminados; la versión española completa de ROSETTA es la que queda. Sin cambios adicionales necesarios.
- **Por qué**: El conflicto fue introducido al crear la rama de LLM abstraction y ya fue resuelto correctamente manteniendo la versión española con el párrafo multi-LLM.
- **Archivos**: `README.md`
- **Enlaces**: [[00_Dashboard]]
- **Estado**: ✅ hecho

## 2026-04-18 22:30 · Inicio de sesión
- **Objetivo**: Cerrar MVP-0 (conflicto README, .claude/ structure, ADR-002 checkpoint) y abrir formalmente MVP-1 / Sprint 1.
- **Estado previo**: leído [[00_Dashboard]]. MVP en curso: MVP-0 (scaffold completado, pendiente cierre formal). ADR-002 pendiente de aprobación. Sprint 0 activo.
- **Checkpoints esperados**: ADR-002 (aprobación del usuario), corpus ISO 27001:2022 (fuente), arranque formal Sprint 1.

---

## 2026-04-18 Cowork · Traspaso completo a Claude Code
- **Hecho**: Creado `HANDOFF.md` con toda la historia del proyecto (origen, 8 decisiones estratégicas, límites firmes, artefactos producidos, directiva de autonomía). Consolidados al vault los artefactos que vivían en Cowork outputs: [[09_Comunicacion/mensaje-linkedin-carlos]] y [[09_Comunicacion/presentacion-proyecto-clase]]. Actualizado `CLAUDE.md` sección 11.5 para incluir `MISSION.md` y `HANDOFF.md` como lectura obligatoria al iniciar sesión. Reemplazado `PLAYBOOK_SESION_1.md` por `START_HERE.md` (arranque de una línea).
- **Por qué**: El usuario (Mj) deja de usar Cowork para este proyecto. A partir de aquí Claude Code asume planificación + ejecución + comunicación desde dentro del repo. Todo el contexto que antes vivía en Cowork ahora es persistente en `HANDOFF.md` + vault.
- **Archivos**: `HANDOFF.md` · `START_HERE.md` · `CLAUDE.md` · [[09_Comunicacion/mensaje-linkedin-carlos]] · [[09_Comunicacion/presentacion-proyecto-clase]]
- **Enlaces**: [[00_Dashboard]] · [[MOC_Roadmap]] · [[08_Reuniones/pendiente-carlos-gomez]]
- **Estado**: ✅ hecho — siguiente sesión: Claude Code arranca solo desde `START_HERE.md`

## 2026-04-18 Cowork · Preparación autonomía + visibilidad Obsidian
- **Hecho**: Añadida sección 14 al [[CLAUDE]] (protocolo de bitácora). Creado [[00_Dashboard]]. Creada esta bitácora. Creados MOCs y notas semilla para las 7 normativas del roadmap.
- **Por qué**: El usuario no veía avance en Obsidian y quería que Claude Code operara con mayor autonomía. Esta preparación es la rampa de lanzamiento para que Claude Code tire solo del roadmap dejando rastro aquí.
- **Archivos**: `MISSION.md` · `CLAUDE.md` · [[00_Dashboard]] · [[00_Bitacora]]
- **Enlaces**: [[MOC_Roadmap]] · [[MOC_ADRs]] · [[MOC_Normativas]]
- **Estado**: ✅ hecho

## 2026-04-18 Sprint 0 · Scaffold inicial
- **Hecho**: Scaffold completo del proyecto ROSETTA (61 archivos): `src/rosetta/` con core, adapters, llm, api, cli; `tests/` con test_models; `docs/` con ARCHITECTURE y ROADMAP; `docs/adr/001-orquestacion-sobre-fork.md`; vault Obsidian con 9 carpetas y plantillas; CI en `.github/workflows/ci.yml`; pre-commit; pyproject.toml con uv; LICENSE proprietary provisional.
- **Por qué**: Arrancar el proyecto con estructura modular, type-safe y con CI/CD desde el minuto uno. Cumple MVP-0.
- **Archivos**: `pyproject.toml` · `src/rosetta/**` · `docs/adr/001-orquestacion-sobre-fork.md` · [[02_ADR/001-orquestacion-sobre-fork]] · [[07_Sprints/2026-04-18_sprint-0]]
- **Enlaces**: [[MOC_Roadmap#MVP-0]] · [[02_ADR/001-orquestacion-sobre-fork]]
- **Estado**: ✅ hecho

## 2026-04-22 · FASE 2 completada — Ingesta de PDF de auditor humano
- **Hecho**: Implementado pipeline completo de ingesta de informes PDF.
  `PdfAuditorIngester` extrae texto con pdfplumber; en páginas escaneadas
  renderiza a imagen con pypdfium2 y usa visión LLM (Claude). Extracción
  estructurada via tool-use (`extraer_hallazgos`) → `DatosRedTeam`.
  Endpoint `POST /ingest/pdf` (multipart) + panel de upload en dashboard.
  17 tests nuevos; 180 passed en suite completa; mypy clean.
- **Por qué**: PLAN_V4 FASE 2 — Modo B de entrada de datos (auditor humano con PDF).
- **Archivos**: `src/rosetta/core/pdf_ingestion.py` · `src/rosetta/api/main.py` · `src/rosetta/api/schemas.py` · `src/rosetta/api/dashboard.py` · `tests/test_pdf_ingestion.py`
- **Estado**: ✅ hecho — commit feat(mvp-8): FASE 2
