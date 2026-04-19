---
title: MOC · Sprints
tags: [moc, sprint, rosetta]
created: 2026-04-18
---

# MOC · Sprints

> Histórico de sprints. Cada sprint cierra un MVP o un sub-hito.
> Plantilla: [[99_Templates/Sprint_template]]

## Sprints completados

### [[07_Sprints/2026-04-18_sprint-0|Sprint 0 · 2026-04-18]]
- **MVP**: [[MOC_Roadmap#MVP-0]]
- **Resultado**: ✅ Scaffold completo del proyecto
- **Aprendizaje clave**: la decisión de orquestar (no forkear) condiciona toda la arquitectura → [[02_ADR/001-orquestacion-sobre-fork]]

## Sprint actual

### [[07_Sprints/2026-04-18_sprint-1|Sprint 1 · pendiente de abrir]]
- **MVP objetivo**: [[MOC_Roadmap#MVP-1|MVP-1 · Traductor Simbiótico ISO 27001:2022]]
- **Estado**: 🟡 pendiente de arrancar
- **Pre-requisitos**: aprobar [[02_ADR/002-abstraccion-llm|ADR-002]], conseguir corpus ISO 27001:2022

## Cómo abrir un sprint

1. Crear `vault/07_Sprints/YYYY-MM-DD_sprint-N.md` desde [[99_Templates/Sprint_template]].
2. Definir objetivo (un MVP del [[MOC_Roadmap]]) y criterio de aceptación.
3. Listar tareas con checkboxes.
4. Anotar diariamente en [[00_Bitacora]] con tag `#sprint/N`.

## Cómo cerrar un sprint

1. Marcar todas las tareas (✅ hecho · 🟡 parcial · 🔴 bloqueado).
2. Sección "Aprendizajes" con al menos 2 líneas.
3. Sección "Bloqueos" con bloqueos pendientes y a quién escalan.
4. Sección "Próximo sprint" con el siguiente objetivo del roadmap.
5. Actualizar [[00_Dashboard]] con el nuevo estado.
6. Commit con mensaje `chore(sprint-N): cierre`.
