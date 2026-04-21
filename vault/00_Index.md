---
title: Índice del vault — ROSETTA
tags: [indice, rosetta]
created: 2026-04-18
updated: 2026-04-19
---

# ROSETTA Vault — Segundo Cerebro del Proyecto

> Si solo lees una nota, que sea [[00_Dashboard]]. Si quieres ver el día a día, [[00_Bitacora]].

## Puntos de entrada

- **[[00_Dashboard]]** · estado actual del proyecto (MVP, LLM, marcos, adapters)
- **[[00_Bitacora]]** · histórico cronológico de acciones con enlaces
- **MOCs (Maps of Content)**:
  - [[MOC_Roadmap]] · los 8 MVPs y los 9 problemas base — **MVP-1→6 completados, MVP-7 en diseño**
  - [[MOC_ADRs]] · decisiones de arquitectura — ADR-001 ✅ ADR-002 ✅
  - [[MOC_Normativas]] · marcos normativos — ISO ✅ ENS ✅ (corpus) · NIS2/DORA/RGPD pendientes
  - [[MOC_Sprints]] · Sprint 0 ✅ Sprint 1 ✅ Sprint 2 ✅ Sprint 3 🟢
  - [[MOC_Hallazgos]] · hallazgos canónicos para validar el Traductor

## Carpetas del vault

- [[01_Inbox]] · Captura rápida sin procesar. Todo entra aquí primero.
- [[02_ADR]] · Architecture Decision Records enlazadas con `docs/adr/` del repo.
- [[03_Normativa]] · Notas sobre marcos, controles, interpretaciones, excepciones.
- [[04_Controles]] · Fichas por control normativo concreto.
- [[05_Hallazgos]] · Patrones de hallazgos canónicos y su traducción esperada.
- [[06_Procedimientos]] · Notas sobre procedure drift (insight de Carlos Gómez Pintado).
- [[07_Sprints]] · Log por sprint: qué se hizo, aprendizajes, bloqueos.
- [[08_Reuniones]] · Reuniones con mentor, profesores, potenciales clientes.
- [[99_Templates]] · Plantillas con YAML frontmatter.

## Convenciones mínimas

1. **Frontmatter obligatorio** en toda nota nueva (ver [[99_Templates]]).
2. **Tags jerárquicos** con barras: `#normativa/iso27001`, `#sprint/1`, `#decision/pendiente`.
3. **Links bidireccionales**: usar `[[nota]]` siempre que se mencione otra entidad.
4. **Inbox primero** si dudas dónde va.
5. **Nada sensible**: el vault se versiona en git. Claves, secretos, datos reales nunca.
6. **Bitácora viva**: ver `CLAUDE.md` sección 14. Toda acción significativa deja entrada en [[00_Bitacora]].

## Tags canónicos

`#adr` `#normativa/iso27001` `#normativa/ens` `#normativa/nis2` `#normativa/dora` `#normativa/rgpd` `#normativa/nist` `#normativa/pci` `#sprint/N` `#hallazgo` `#control` `#procedimiento` `#decision/pendiente` `#decision/aprobada` `#riesgo` `#mentor/carlos` `#idea` `#bloqueo`

## Estado actual · 2026-04-19

- **MVP actual**: MVP-7 🟡 en diseño (Gate CI/CD)
- **Último completado**: [[MOC_Roadmap#MVP-6|MVP-6 · API REST + dashboard]] ✅ 102 tests
- **LLM activo**: Ollama qwen2.5:14b (local, sin coste, 16GB RAM)
- **Corpus activos**: ISO 27001 ✅ (93 controles) · ENS 🟡 (pendiente cargar)
- **Sprint activo**: [[MOC_Sprints|Sprint 3]] 🟢
- **ADR pendiente de proponer**: ADR-003 · Ingestión de PDF
