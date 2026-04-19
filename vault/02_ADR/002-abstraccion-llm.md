---
title: ADR-002 · Abstracción del proveedor LLM
tags: [adr, decision/pendiente, rosetta]
created: 2026-04-18
estado: aprobado
adr_numero: 002
adr_repo: docs/adr/002-abstraccion-del-proveedor-llm.md
---

# ADR-002 · Abstracción del proveedor LLM

> ✅ Aprobada · 2026-04-18.
> Espejo vault del ADR técnico en `docs/adr/002-abstraccion-del-proveedor-llm.md`.

## Contexto

ROSETTA nació acoplado a la API de Anthropic (Claude). El usuario no dispone de clave de Anthropic en el momento de arrancar el desarrollo y plantea dos preguntas: ¿se puede avanzar sin API? ¿se debería cambiar de proveedor? Esto abre una decisión de arquitectura que conviene fijar ahora antes de que el acoplamiento se haga profundo.

## Decisión propuesta

Introducir una interfaz `LLMClient` en `src/rosetta/llm/base.py` con método asíncrono `completar(system, messages, tools) -> CompletionResult`. Tres implementaciones iniciales: `ClaudeClient`, `OpenAIClient`, `OllamaClient`. Un factory `get_llm_client(provider)` en `src/rosetta/llm/factory.py` lee `LLM_PROVIDER` de entorno y devuelve la implementación adecuada.

`TraductorSimbiotico` pasa a recibir un `LLMClient` por constructor (inyección de dependencia), no instancia Claude directamente. Esto habilita tests unitarios con mocks.

## Consecuencias positivas

- **Desarrollo sin coste**: Ollama local con `llama3.1:8b` o `qwen2.5:7b` permite iterar el pipeline sin API key.
- **Soberanía de datos**: clientes europeos bajo [[03_Normativa/ENS_2022|ENS]], [[03_Normativa/NIS2|NIS2]] o [[03_Normativa/DORA|DORA]] pueden exigir LLM on-premise. La abstracción lo habilita.
- **Resiliencia**: caída de un proveedor no tumba la plataforma.
- **Activo de investigación**: benchmark comparativo Claude vs GPT-4 vs Llama en la tarea específica de traducción técnico→normativa.
- **Testeabilidad**: mocks limpios sobre una interfaz en vez de monkey-patching del SDK de Anthropic.

## Consecuencias negativas

- Complejidad extra de mantener 3 implementaciones.
- Prompts pueden necesitar ajustes por proveedor (modelos pequeños de Ollama responden peor a tool-use estructurado).
- Schema JSON de salida no siempre se respeta en modelos locales → necesidad de validación defensiva con Pydantic y fallback a re-prompt.

## Alternativas descartadas

- **Dependencia dura de Anthropic**: descartada por los argumentos de soberanía y coste.
- **LiteLLM** como wrapper externo: descartada por introducir una dependencia pesada y mágica cuando podemos implementar la abstracción en 100 líneas de código propio.
- **Un solo proveedor con "switch" hardcoded**: no escala.

## Plan de implementación

1. Crear interfaz `LLMClient` y tipos comunes (`Message`, `Tool`, `CompletionResult`) en `base.py`.
2. Mover la lógica actual de `src/rosetta/llm/claude.py` detrás de la interfaz.
3. Implementar `OllamaClient` (httpx contra `http://localhost:11434/api/chat`).
4. Implementar `OpenAIClient`.
5. Factory con switch por `LLM_PROVIDER` en `.env`.
6. Tests unitarios con mocks de las 3 implementaciones (sin llamadas reales).
7. Actualizar `TraductorSimbiotico` para recibir `LLMClient` por constructor.
8. Actualizar `.env.example` con las variables de los 3 proveedores.
9. Documentar setup de Ollama en `NEXT_STEPS.md`.

## Enlaces

- [[MOC_ADRs]] · [[02_ADR/001-orquestacion-sobre-fork]] · [[00_Dashboard]]
- Archivo técnico: `docs/adr/002-abstraccion-llm.md` (pendiente de crear)
