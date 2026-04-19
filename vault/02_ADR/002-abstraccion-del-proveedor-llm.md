---
title: ADR-002 · Abstracción del proveedor LLM
tags: [adr, decision/aprobada, arquitectura, llm]
adr_id: 002
status: aprobado
created: 2026-04-18
source: docs/adr/002-abstraccion-del-proveedor-llm.md
mvp_relevante: MVP-1
---

# ADR-002 · Abstracción del proveedor LLM

> Versión canónica y completa en `docs/adr/002-abstraccion-del-proveedor-llm.md`.

## Decisión

Introducimos `LLMClient` como Protocol en `src/rosetta/llm/base.py`. Tres implementaciones: `ClaudeClient` (producción), `OllamaClient` (dev local / on-premise), `OpenAIClient` (alternativa comercial). La activa se selecciona con `LLM_PROVIDER` en `.env`.

## Motivación clave

- **Desarrollo sin coste**: Ollama local elimina gasto de API mientras se itera sobre RAG y prompts.
- **Soberanía de datos**: clientes ENS/NIS2 del sector público europeo pueden exigir LLM on-premise.
- **Testabilidad**: el Traductor recibe `LLMClient` por inyección, los tests usan mocks simples.

## Riesgo principal

Modelos pequeños de Ollama (7B–8B) responden peor a `tool_use` estructurado. Los prompts del Traductor pueden necesitar ramas por proveedor en el futuro.

## Relacionado con

- [[001-orquestacion-sobre-fork]] — misma filosofía: orquestar, no reimplementar.
- [[../07_Sprints/2026-04-18_sprint-0]] — sprint donde se implementó.
- Roadmap: MVP-1 (Traductor Simbiótico).

## Estado

Implementado en `src/rosetta/llm/`. Tests en `tests/test_llm.py`.
