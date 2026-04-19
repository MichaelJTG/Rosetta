---
fecha: 2026-04-18
estado: aprobado
---

# ADR-002. Abstracción del proveedor LLM detrás de una interfaz común

## Contexto

El Traductor Simbiótico depende directamente de `ClaudeClient` (Anthropic SDK). Esto crea cuatro fricciones concretas:

1. **Coste de desarrollo**: iterar sobre prompts y pipeline RAG consume tokens de la API de producción. No hay opción de iterar localmente sin coste.
2. **Soberanía de datos**: clientes del sector público europeo (especialmente bajo ENS y NIS2) pueden exigir que el LLM no salga de su infraestructura. Un LLM on-premise (Ollama) sería el requisito.
3. **Resiliencia**: una caída de la API de Anthropic tumba toda la plataforma. Sin fallback, el SLA de ROSETTA queda sujeto al SLA de un proveedor externo.
4. **Benchmark comparativo**: evaluar Claude vs GPT-4 vs Llama en la tarea específica de traducción técnico→normativa es un activo de investigación valioso para el roadmap de producto.

La dependencia dura también dificulta los tests unitarios del Traductor: sin abstracción, cualquier test necesita mockear internals del SDK de Anthropic.

## Decisión

Introducimos la interfaz `LLMClient` (Python `Protocol`) en `src/rosetta/llm/base.py` con tres implementaciones:

- `ClaudeClient` — producción por defecto. Usa el SDK oficial de Anthropic.
- `OllamaClient` — desarrollo local y despliegues on-premise. Usa `httpx` contra `http://localhost:11434/api/chat`.
- `OpenAIClient` — alternativa comercial y compatible con OpenAI-like APIs. Usa `httpx` directamente (sin SDK de OpenAI).

La implementación activa se selecciona mediante la variable de entorno `LLM_PROVIDER` (valores: `claude`, `ollama`, `openai`). El valor por defecto es `claude`.

`TraductorSimbiotico` recibe un `LLMClient` por inyección de dependencia en el constructor, en lugar de instanciar `ClaudeClient` internamente.

## Consecuencias

### Positivas

- Iteración local sin coste con `ollama` + `llama3.1:8b` o `qwen2.5:7b`.
- Tests unitarios del Traductor con mocks simples que implementen el Protocol.
- Posibilidad de ofrecer a clientes ENS/NIS2 un despliegue 100% on-premise.
- Infraestructura para comparar modelos en la tarea específica de traducción.
- Resiliencia: fallback manual a Ollama o OpenAI si Anthropic no está disponible.

### Negativas

- Complejidad adicional: mantener tres implementaciones en vez de una.
- Los modelos pequeños de Ollama (7B–8B) responden peor a `tool_use` estructurado; los prompts pueden necesitar ajustes por proveedor.
- `OllamaClient` y `OpenAIClient` requieren tests con mocks de httpx, más frágiles que el SDK tipado de Anthropic.

### Neutras

- La interfaz normaliza la respuesta a `CompletionResult`, lo que oculta diferencias entre APIs (formatos de tool_calls, stop_reason, etc.).
- Se añaden `OLLAMA_URL`, `OLLAMA_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL` a `.env.example`.

## Alternativas descartadas

### Dependencia dura de Anthropic

Descartada por las razones enumeradas en el contexto. Mantener el status quo bloquea el desarrollo económico, la soberanía de datos y los tests.

### LiteLLM como wrapper universal

Descartada en esta fase. LiteLLM unifica >100 proveedores y añade ~20 dependencias transitivas. El valor diferencial llega cuando hay ≥4 proveedores activos. Con tres implementaciones propias en ~150 líneas totales, el coste de mantenimiento es asumible y el control sobre los tipos es total. Se puede reconsiderar en MVP-6+ si se añaden más proveedores.

## Referencias

- Implementación: `src/rosetta/llm/` (base.py, claude.py, ollama.py, openai.py, factory.py)
- Tests: `tests/test_llm.py`
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
