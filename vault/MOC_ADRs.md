---
title: MOC · ADRs
tags: [moc, adr, rosetta]
created: 2026-04-18
updated: 2026-04-19
---

# MOC · Architecture Decision Records

> Toda decisión de arquitectura significativa vive aquí, espejada con `docs/adr/` del repo.
> Convención numérica MADR. Estados: 🟡 propuesta · ✅ aprobada · ⛔ rechazada · 🔄 superseded.

## Aprobadas

### [[02_ADR/001-orquestacion-sobre-fork]]
- ✅ Aprobada · 2026-04-18
- **Decisión**: orquestar herramientas open source vía CLI/API; no forkear ni embeber.
- **Motivo**: licencias GPL/AGPL imponen contagio; mantenimiento divergente insostenible; el valor diferencial está en el Traductor, no en los sensores.
- **Repo**: `docs/adr/001-orquestacion-sobre-fork.md`

### [[02_ADR/002-abstraccion-llm]]
- ✅ Aprobada e implementada · 2026-04-18
- **Decisión**: interfaz `LLMClient` (Protocol) con implementaciones `ClaudeClient` / `OllamaClient` / `OpenAIClient`. Factory `get_llm_client(provider)` lee `LLM_PROVIDER` del entorno.
- **Motivo**: desarrollo sin coste con Ollama local; soberanía de datos para clientes ENS/NIS2/DORA; resiliencia ante caídas de proveedor.
- **Validado en producción**: Ollama qwen2.5:14b · 2026-04-19 · traducción AWS key → ISO A.5.23 + A.8.4 ✅
- **Riesgo confirmado**: modelos pequeños responden peor a tool-use — qwen2.5:14b es el mínimo recomendado en 16GB RAM.
- **Repo**: `docs/adr/002-abstraccion-del-proveedor-llm.md`

## Pendientes de proponer

### ADR-003 · Ingestión de PDF (hallazgos de herramientas externas)
- 🟡 Pendiente · identificada en sesión 2026-04-19
- **Problema**: herramientas Red Team como Nessus, Burp Suite y reportes manuales solo generan PDF. El flujo actual solo acepta JSON `DatosRedTeam`.
- **Opciones a evaluar**: `pdfplumber` vs `pymupdf` + LLM para estructurar → `DatosRedTeam`.
- **MVP destino**: MVP-8+

## Plantilla y convenciones

- Plantilla: [[99_Templates/ADR_template]]
- Numeración: NNN secuencial. No se reutiliza un número aunque el ADR sea rechazado.
- Cada ADR tiene un **archivo técnico** en `docs/adr/NNN-titulo.md` y un **resumen vault** en `vault/02_ADR/NNN-titulo.md` con enlaces bidireccionales.
- Tags: `#adr` siempre + uno de `#decision/pendiente` `#decision/aprobada` `#decision/rechazada` `#decision/superseded`.
