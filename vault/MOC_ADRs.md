---
title: MOC · ADRs
tags: [moc, adr, rosetta]
created: 2026-04-18
---

# MOC · Architecture Decision Records

> Toda decisión de arquitectura significativa vive aquí, espejada con `docs/adr/` del repo.
> Convención numérica MADR. Estados: 🟡 propuesta · ✅ aprobada · ⛔ rechazada · 🔄 superseded.

## Aprobadas

### [[02_ADR/001-orquestacion-sobre-fork]]
- ✅ Aprobada · 2026-04-18
- **Decisión**: orquestar herramientas open source vía CLI/API; no forkear ni embeber.
- **Motivo**: licencias GPL/AGPL imponen contagio; mantenimiento divergente insostenible para proyecto de un autor; el valor diferencial está en el [[03_Normativa/ISO_27001_2022|Traductor]], no en los sensores.
- **Repo**: `docs/adr/001-orquestacion-sobre-fork.md`

## Pendientes / propuestas

### [[02_ADR/002-abstraccion-llm]]
- 🟡 Propuesta · 2026-04-18
- **Decisión a tomar**: introducir interfaz `LLMClient` con implementaciones Claude / OpenAI / Ollama, en vez de acoplarnos solo a Anthropic.
- **Motivo**: desarrollo sin coste con Ollama local; soberanía de datos para clientes europeos (ENS / NIS2 / DORA); resiliencia ante caídas de un proveedor; benchmark comparativo Claude vs GPT-4 vs Llama como activo de investigación.
- **Riesgo**: prompts pueden necesitar ajustes por proveedor (modelos pequeños responden peor a tool-use estructurado).
- **Pendiente**: aprobación del usuario y refactor de `src/rosetta/llm/`.

## Plantilla y convenciones

- Plantilla: [[99_Templates/ADR_template]]
- Numeración: NNN secuencial. No se reutiliza un número aunque el ADR sea rechazado.
- Cada ADR tiene un **archivo técnico** en `docs/adr/NNN-titulo.md` y un **resumen vault** en `vault/02_ADR/NNN-titulo.md` con enlaces bidireccionales.
- Tags: `#adr` siempre + uno de `#decision/pendiente` `#decision/aprobada` `#decision/rechazada` `#decision/superseded`.
