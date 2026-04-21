---
title: Patrón · LiteLLM como gateway multi-proveedor con fallback
tags: [hallazgo, patron, arquitectura, rosetta]
categoria: patron-arquitectura
created: 2026-04-20
origen: [[05_Hallazgos/referencia-decepticon]]
---

# Patrón · LiteLLM como gateway multi-proveedor con fallback

## Qué es

`LiteLLM` es una librería (y opcional proxy) que expone un único SDK (`litellm.completion(...)`) capaz de hablar con Anthropic, OpenAI, Google, Ollama, Azure, Bedrock, Groq y ~50 proveedores más. Dos capacidades clave:

1. **Normalización**: request/response en formato OpenAI-compatible — el código no sabe qué proveedor está detrás.
2. **Router con fallback**: lista de modelos por alias lógico (`rosetta-translator` → `[claude-sonnet, qwen2.5:14b-local, gpt-4]`); si falla uno, pasa al siguiente transparentemente.

## Origen

Observado en [[referencia-decepticon]]. Implementan perfiles `eco` / `max` / `test` vía LiteLLM con fallback automático. Es el gateway entre sus 16 agentes y los proveedores físicos.

## Cómo lo aplicamos a ROSETTA

**Colapsa ADR-002 en una sola implementación.** El ADR-002 aprobado propuso tres clases `ClaudeProvider`, `OpenAIProvider`, `OllamaProvider` tras una interfaz `LLMProvider`. LiteLLM **es** esa abstracción — lo que ROSETTA programa es una única clase `LiteLLMProvider` que delega al router.

```python
# src/rosetta/llm/litellm_provider.py (esqueleto)
from litellm import Router
from rosetta.llm.base import LLMProvider

class LiteLLMProvider(LLMProvider):
    def __init__(self, profile: str = "eco"):
        self.router = Router(model_list=self._load_profile(profile))

    async def generate(self, prompt: str, agent_id: str) -> str:
        resp = await self.router.acompletion(
            model=f"rosetta-{agent_id}",   # alias lógico, no modelo físico
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
```

Perfiles definidos en `config/llm_profiles.yaml`:

```yaml
eco:   # desarrollo local, sin coste
  rosetta-translator:
    - model: ollama/qwen2.5:14b
      api_base: http://localhost:11434

max:   # demo con Carlos, producción
  rosetta-translator:
    - model: claude-3-5-sonnet-20241022
      api_key: env/ANTHROPIC_API_KEY
    - model: ollama/qwen2.5:14b       # fallback si Claude 5xx

test:
  rosetta-translator:
    - model: ollama/qwen2.5:14b-stub-determinista
```

## Por qué importa hoy

- Si qwen2.5:14b se cae por RAM durante la demo con Carlos, el Traductor NO se cae — pasa a Claude Haiku.
- El día que llegue un cliente on-prem que exija privacidad, se cambia un YAML.
- Rate limiting, retry con backoff y budget tracking vienen de serie — menos código propio que mantener.

## Cuándo introducirlo

**Oportunidad post-MVP-7**: al proponer [[02_ADR/004-arquitectura-multi-agente]], aprovechar para materializar este gateway en una sola refactor. Propuesta: **ADR-005 · Gateway LLM vía LiteLLM**, que complementa ADR-002 (mantiene principio de abstracción, cambia implementación).

## Riesgos y mitigación

- **Dependencia externa**: LiteLLM evoluciona rápido. Mitigación: pin de versión en `pyproject.toml`, tests smoke en CI.
- **Fuga a proveedores cloud**: un mal fallback puede mandar prompt a modelo cloud no autorizado. Mitigación: perfil por defecto `eco` (Ollama local), `max` requiere env explícita.
- **Debugging con fallback**: no es obvio qué modelo respondió. Mitigación: structlog con `model_used`.

## Enlaces

- [[05_Hallazgos/referencia-decepticon]] · [[02_ADR/002-abstraccion-llm]] · [[02_ADR/004-arquitectura-multi-agente]]
- [[10_Agentes/MOC_Agentes]] · [[MOC_Hallazgos]]
- Docs externas: https://docs.litellm.ai/
