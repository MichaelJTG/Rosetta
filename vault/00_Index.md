---
title: Índice del vault — ROSETTA
tags: [indice, rosetta]
created: 2026-04-18
updated: 2026-04-18
---

# ROSETTA Vault — Segundo Cerebro del Proyecto

> Si solo lees una nota, que sea [[00_Dashboard]]. Si quieres ver el día a día, [[00_Bitacora]].

## Puntos de entrada

- **[[00_Dashboard]]** · estado actual del proyecto (MVP, LLM, marcos, adapters)
- **[[00_Bitacora]]** · histórico cronológico de acciones con enlaces
- **MOCs (Maps of Content)**:
  - [[MOC_Roadmap]] · los 8 MVPs y los 9 problemas base
  - [[MOC_ADRs]] · decisiones de arquitectura
  - [[MOC_Normativas]] · los 7 marcos normativos objetivo
  - [[MOC_Sprints]] · histórico de sprints
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

## Estado actual

Para datos siempre frescos consulta [[00_Dashboard]]. Referencia rápida:

- MVP actual: MVP-0 ✅ completado
- Próximo: [[MOC_Roadmap#MVP-1|MVP-1 · Traductor sobre ISO 27001:2022]]
- ADR pendiente: [[02_ADR/002-abstraccion-llm|ADR-002 · Abstracción LLM]]
- Insight vivo: [[06_Procedimientos/insight-carlos-procedure-drift|Procedure drift · MVP-5]]
