---
title: Patrón · Contexto fresco por agente especializado
tags: [hallazgo, patron, arquitectura, rosetta]
categoria: patron-arquitectura
created: 2026-04-20
origen: [[05_Hallazgos/referencia-decepticon]]
---

# Patrón · Contexto fresco por agente especializado

## Qué es

Diseño de sistema multi-agente donde cada agente:

1. Arranca con **su propio system prompt** y sus propias herramientas.
2. Tiene **ventana de contexto vacía** al inicio de cada invocación.
3. Recibe del orquestador solo **datos estructurados** (Pydantic, JSON) — nunca el historial conversacional de otros agentes.
4. Devuelve al orquestador un objeto estructurado, no texto libre.

## Origen

Observado en [[referencia-decepticon]]: 16 agentes (Recon, Exploit, Defender, AD Specialist, Cloud Specialist, etc.), cada uno con contexto fresco. El orquestador coordina y nunca mezcla historiales.

## Por qué funciona

Evita dos patologías conocidas:
- **Contaminación de razonamiento**: un agente se ve arrastrado por el prompt-engineering de otro.
- **Saturación de contexto**: conforme crece la sesión, el contexto relevante se diluye en conversación irrelevante.

Beneficios operativos:
- **Paralelismo real**: agentes sin estado compartido corren concurrentes.
- **Testeo unitario**: cada agente se testea con fixtures propias.
- **Precisión del modelo**: prompt de 5k tokens focalizado supera a 30k tokens genérico.

## Cómo lo aplicamos a ROSETTA

Hoy existe **un** Traductor monolítico que conoce todos los marcos. Cuando lleguen NIS2 + DORA + RGPD + NIST + PCI, el prompt engordará y la precisión caerá — el modelo hace *switching* mental entre jerarquías muy distintas (`op.acc.5` del ENS vs art.32 del RGPD no comparten forma).

Aplicación directa: **un agente especialista por marco normativo**.

- `TraductorISO` — prompt centrado en Anexo A, 4 dominios, 93 controles
- `TraductorENS` — prompt centrado en org/op/mp, niveles B/M/A
- `TraductorRGPD` — prompt centrado en artículos, considerandos, bases jurídicas
- (etc., uno por marco)

Cada especialista recibe el `HallazgoMaestro` (contrato Pydantic) y los fragmentos RAG **filtrados a su marco** (no los de otros). Devuelve `Traduccion` con controles aplicables, justificación y confianza. El orquestador (`Rosetta`) los dispara en paralelo vía `Soundwave`, recoge respuestas, y pasa al `Validador`.

Catálogo completo en [[10_Agentes/MOC_Agentes]] y decisión formal en [[02_ADR/004-arquitectura-multi-agente]].

## Ventajas medibles esperadas

| Métrica | Monolítico hoy | Multi-agente esperado |
|---------|----------------|-----------------------|
| Precisión por marco | ~70% (estimado) | >85% |
| Latencia 7 marcos | ~30s secuencial | ~7s paralelo |
| Tokens por llamada | ~30k | ~5k × 7 (cacheable) |
| Coste Sonnet por demo | alto | moderado (eco por defecto) |

## Cuándo introducirlo

**No ahora**. MVP-7 es Gate CI/CD y solo tienes ISO + ENS operativos. Riesgo de over-engineering prematuro.

**Activar en MVP-8**, cuando cargues NIS2/DORA/RGPD. El Traductor monolítico empezará a crujir y será el momento natural de proponer [[02_ADR/004-arquitectura-multi-agente]].

## Riesgos y mitigación

- **Coste inicial de refactor**: 3-5 días. Mitigación: mantener el monolítico como fallback durante la transición.
- **Complejidad operativa**: observabilidad por agente. Mitigación: structlog con `agent_id` obligatorio.
- **Explosión combinatoria de prompts**: 16 prompts que mantener. Mitigación: base class con plantilla, solo el "cuerpo específico del marco" cambia.

## Enlaces

- [[05_Hallazgos/referencia-decepticon]] · [[10_Agentes/MOC_Agentes]] · [[02_ADR/004-arquitectura-multi-agente]]
- [[05_Hallazgos/patron-litellm-gateway]] (complementario)
- [[MOC_Hallazgos]]
