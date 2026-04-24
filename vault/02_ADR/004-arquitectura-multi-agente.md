---
title: ADR-004 · Arquitectura multi-agente por marco normativo
tags: [adr, arquitectura, decision/aprobada, rosetta]
adr_id: 004
estado: aprobada
fecha_propuesta: 2026-04-20
fecha_aprobacion: 2026-04-23
supersede: N/A
relacionados: [ADR-002]
---

# ADR-004 · Arquitectura multi-agente por marco normativo

## Estado

**Aprobada** · 2026-04-24 · implementada en FASE 5.

## Contexto

MVP-1→6 implementaron un Traductor monolítico: un único agente LLM recibe el `HallazgoMaestro` junto con el RAG de todos los marcos cargados (hoy ISO + ENS) y produce traducciones multi-marco en una sola pasada. Funciona mientras hay 1-2 marcos pequeños.

Problemas que anticipamos conforme sumemos NIS2, DORA, RGPD, NIST y PCI (MVP-8+):

1. **Prompt saturado**: meter jerarquías de 7 marcos en un system prompt degrada precisión (estructuras muy distintas: artículos, controles numerados, funciones, requisitos).
2. **Context switching del modelo**: responder sobre ISO A.8.24 y acto seguido sobre RGPD art.32 obliga al modelo a cambiar dominio simbólico.
3. **Imposibilidad de paralelizar**: todo va en una sola llamada secuencial.
4. **Coste y latencia**: un prompt de 30k tokens cuesta más y tarda más que 7 de 5k en paralelo.
5. **Testabilidad**: fallos intermitentes difíciles de atribuir a un marco concreto.
6. **Alucinaciones cruzadas**: el modelo confunde códigos de marcos similares (inventa `op.acc.5` cuando el hallazgo era solo ISO).

Adicionalmente, [[05_Hallazgos/referencia-decepticon]] (PurpleAILAB, Apache-2.0) muestra que un patrón multi-agente bien acotado con 16 agentes especialistas es viable técnicamente con un gateway LLM multi-proveedor.

## Decisión propuesta

Refactorizar el núcleo a **arquitectura multi-agente con 16 agentes especialistas** (catálogo en [[10_Agentes/MOC_Agentes]]). Puntos clave:

1. **Un agente especialista por marco normativo** con contexto fresco y RAG filtrado al corpus de ese marco.
2. **Orquestador (`Rosetta`) + scheduler (`Soundwave`)** para routing, paralelismo y recopilación.
3. **Agente `Validador`** como critic para rechazar traducciones con alucinaciones.
4. **Agente `Crucero`** para detectar conflictos e intersecciones entre marcos.
5. **Agente `Dossiero`** determinista (sin LLM) para compilar dossier final.
6. **Contrato Pydantic** `Traduccion` entre Traductor y el resto. Ningún agente comparte conversación; todo pasa por estructuras tipadas.
7. **Gateway LLM vía LiteLLM** (ver [[05_Hallazgos/patron-litellm-gateway]]) con perfiles `eco`/`max`/`test`, complementando ADR-002.

## Alternativas consideradas

### A. Mantener Traductor monolítico con prompt más largo
- **Pro**: no hay refactor.
- **Contra**: los 6 problemas se agravan con cada marco nuevo. Rompe a 4-5 marcos.
- **Decisión**: descartada.

### B. Dos niveles: Router + Traductor único por llamada
- Router decide qué marco aplica y llama a un Traductor genérico con RAG filtrado.
- **Pro**: menos agentes.
- **Contra**: un solo Traductor sigue cargando prompt de 7 estructuras. Context switching persiste. No paraleliza.
- **Decisión**: descartada como solución final; aceptable como **paso intermedio** en MVP-7.

### C. Multi-agente con agente por marco (la decisión)
- **Pro**: aísla dominios, paraleliza, testeable, escalable. Alineado con patrón validado por Decepticon.
- **Contra**: más código, más config, más coste si se usan modelos `max` en todos. Mitigación: `eco` por defecto, `max` solo en demo/producción.
- **Decisión**: **adoptada**.

## Consecuencias

### Positivas
- Paralelismo real (latencia ≈ marco más lento, no la suma).
- Precisión superior por aislamiento de contexto.
- Fácil añadir marco nuevo: crear `TraductorXYZ` + registrar en Rosetta, sin tocar otros.
- Testeo por agente independiente.
- El Validador reduce riesgo de alucinaciones en producción (crítico para auditoría).
- El Gatemaster hereda un núcleo más fiable para el Gate CI/CD.

### Negativas
- ~3-5 días de refactor entre MVP-7 y MVP-8.
- Más complejidad operativa: observabilidad por agente necesaria (structlog con `agent_id`).
- Coste potencial superior si se abusa del perfil `max`.

### Neutras
- El contrato `HallazgoMaestro` sobrevive intacto (no hay migración de datos).
- Los adapters (Reconocedor, Vigilante) no se tocan.

## Plan de implementación (si se aprueba)

1. Introducir `src/rosetta/agents/` con clase base `Agent`.
2. Migrar Traductor actual a `agents/translator/base.py` + subclase `iso.py`.
3. Portar ENS como segundo especialista.
4. Introducir `Rosetta` + `Soundwave` mínimos (orquestador serial, paralelismo después).
5. Añadir `Validador` y activarlo en el flujo.
6. Tests: uno por agente + uno de integración end-to-end.
7. Dejar Crucero, Dossiero y Gatemaster para iteraciones posteriores.
8. Gateway LiteLLM en **ADR-005** complementario.

## Enlaces

- [[02_ADR/002-abstraccion-llm]] (principio sobrevive)
- [[10_Agentes/MOC_Agentes]] (catálogo completo)
- [[05_Hallazgos/patron-agentes-especializados]] · [[05_Hallazgos/patron-litellm-gateway]]
- [[05_Hallazgos/referencia-decepticon]] (inspiración)
- [[MOC_ADRs]] · [[MOC_Roadmap#MVP-8]]
