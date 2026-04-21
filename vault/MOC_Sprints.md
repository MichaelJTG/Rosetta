---
title: MOC · Sprints
tags: [moc, sprint, rosetta]
created: 2026-04-18
updated: 2026-04-19
---

# MOC · Sprints

> Histórico de sprints. Cada sprint cierra un MVP o un sub-hito.
> Plantilla: [[99_Templates/Sprint_template]]

## Sprints completados

### [[07_Sprints/2026-04-18_sprint-0|Sprint 0 · 2026-04-18]]
- **MVP**: [[MOC_Roadmap#MVP-0|MVP-0 · Scaffold]]
- **Resultado**: ✅ Proyecto instalable, estructura modular, modelos Pydantic, esqueletos, tests base.
- **Aprendizaje clave**: la decisión de orquestar (no forkear) condiciona toda la arquitectura → [[02_ADR/001-orquestacion-sobre-fork]]

### [[07_Sprints/2026-04-18_sprint-1|Sprint 1 · 2026-04-18]]
- **MVP**: [[MOC_Roadmap#MVP-1|MVP-1 · Traductor Simbiótico ISO 27001]]
- **Resultado**: ✅ Corpus 93 controles · RAG ChromaDB · TraductorSimbiótico · CLI translate · 49 tests · cobertura core 99%
- **Aprendizaje clave**: ChromaDB stubs mypy strict requieren `# type: ignore[arg-type]`; origen `wazuh` → normalizar a `otro` para hallazgos sin adaptador activo.

### [[07_Sprints/2026-04-19_sprint-2|Sprint 2 · 2026-04-19]]
- **MVPs**: [[MOC_Roadmap#MVP-2|MVP-2]] → [[MOC_Roadmap#MVP-6|MVP-6]] (5 MVPs en una sesión)
- **Resultado**: ✅ GrafoCorrelacion · ENS corpus · NucleiAdapter · DriftDetector · API REST + dashboard
- **Tests**: 102 · ruff ✅ · mypy strict ✅
- **Aprendizaje clave**: Neo4j como hard dependency bloquea pruebas → store in-memory primero, Neo4j opcional; dashboard embebido HTML+JS = cero dependencias nuevas.

### [[07_Sprints/2026-04-21_sprint-3|Sprint 3 · 2026-04-21]]
- **MVP**: [[MOC_Roadmap#MVP-7|MVP-7 · Gate CI/CD]]
- **Resultado**: ✅ `DiffParser` + `DiffAnalyzer` + `POST /analyze-diff` + GitHub Action + `.rosetta.yml`
- **Tests**: 141 (+39 nuevos) · ruff ✅ · mypy strict ✅ · cobertura `diff_analyzer` 88%
- **Aprendizaje clave**: tool-use con `tiene_violacion: bool` explícito evita falsos positivos del LLM; `per-file-ignores` en ruff.toml para el patrón `load_dotenv()` pre-import.

## Sprint actual

### Sprint 4 · próximo — MVP-8 Ampliación de marcos
- **Objetivo**: NIS2 corpus + DORA corpus + NIST CSF 2
- **Estado**: ⚪ no iniciado

## Cómo abrir un sprint

1. Crear `vault/07_Sprints/YYYY-MM-DD_sprint-N.md` con el skill `/sprint-open`.
2. Definir objetivo (un MVP del [[MOC_Roadmap]]) y criterio de aceptación.
3. Anotar en [[00_Bitacora]] con tag `#sprint/N`.

## Cómo cerrar un sprint

1. Usar el skill `/sprint-close`.
2. Marcar tareas (✅ hecho · 🟡 parcial · 🔴 bloqueado).
3. Sección "Aprendizajes" (mínimo 2).
4. Actualizar [[00_Dashboard]] y [[MOC_Roadmap]].
