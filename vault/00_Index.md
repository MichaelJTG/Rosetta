---
title: Índice del vault — ROSETTA
tags: [indice, rosetta]
created: 2026-04-18
---

# ROSETTA Vault — Segundo Cerebro del Proyecto

Este vault es el segundo cerebro del proyecto. Aquí queda registrado todo lo que no vive en código: decisiones, aprendizajes, notas de reuniones, interpretaciones normativas, bloqueos, ideas en crudo. Es la memoria del proyecto.

## Estructura

- [[01_Inbox]] · Captura rápida sin procesar. Todo entra aquí primero.
- [[02_ADR]] · Architecture Decision Records enlazadas con `docs/adr/` del repo.
- [[03_Normativa]] · Notas sobre controles, interpretaciones, excepciones.
- [[04_Controles]] · Fichas por control normativo con ejemplos de hallazgos que los incumplen.
- [[05_Hallazgos]] · Patrones de hallazgos canónicos y su traducción.
- [[06_Procedimientos]] · Plantillas y notas sobre procedure drift (insight de Carlos Gómez Pintado).
- [[07_Sprints]] · Log por sprint: qué se hizo, aprendizajes, bloqueos.
- [[08_Reuniones]] · Notas de reuniones con mentor, profesores, potenciales clientes.
- [[99_Templates]] · Plantillas con YAML frontmatter para que Obsidian indexe correctamente.

## Convenciones mínimas

1. **Frontmatter obligatorio** en toda nota nueva. Usar plantilla de `99_Templates/`.
2. **Tags jerárquicos** con barras: `#normativa/iso27001`, `#sprint/1`, `#decision/pendiente`.
3. **Links bidireccionales**: usar `[[nota]]` siempre que se mencione otra entidad.
4. **Inbox primero**: si no sabes dónde va, créalo en `01_Inbox/` y ya lo reorganizarás.
5. **Nada sensible aquí**: este vault se versiona en git. Claves, secretos, datos de clientes reales nunca.

## Tags canónicos

`#adr` `#normativa/iso27001` `#normativa/ens` `#normativa/nis2` `#normativa/dora` `#normativa/rgpd` `#sprint/N` `#hallazgo` `#control` `#procedimiento` `#decision/pendiente` `#decision/aprobada` `#riesgo` `#mentor/carlos` `#idea` `#bloqueo`

## Estado actual

- Sprint actual: **MVP-0 · Scaffold**
- Próximo hito: MVP-1 Traductor Simbiótico sobre ISO 27001:2022 (ver `docs/ROADMAP.md`)
- Último ADR aprobado: [[02_ADR/001-orquestacion-sobre-fork]]
