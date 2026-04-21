---
title: MOC · Agentes de ROSETTA
tags: [moc, agentes, rosetta, arquitectura]
created: 2026-04-20
updated: 2026-04-20
---

# MOC · Arquitectura Multi-Agente de ROSETTA

> Catálogo de los 16 agentes especializados que compondrán el núcleo cognitivo de ROSETTA a partir de MVP-8. Inspirado en el patrón de Decepticon (PurpleAILAB, Apache-2.0), adaptado al dominio de cumplimiento normativo.

## Contexto

Ver [[05_Hallazgos/patron-agentes-especializados]] para el porqué del patrón y [[02_ADR/004-arquitectura-multi-agente]] para la decisión formal. Cada agente tiene:

- **Contexto fresco**: no hereda historial conversacional de otros agentes.
- **Input/output contractual**: tipado con Pydantic (`HallazgoMaestro`, `FragmentoNormativa`, `Traduccion`, `DossierMultimarco`).
- **Modelo asignado** por perfil `eco` / `max` / `test` vía LiteLLM (ver [[05_Hallazgos/patron-litellm-gateway]]).
- **Herramientas limitadas**: solo las estrictamente necesarias para su función.

## Los 16 agentes

### Capa de orquestación (2)

#### [[10_Agentes/Rosetta]]
Orquestador principal. Recibe `HallazgoMaestro`, decide qué marcos aplican, dispara los Traductores vía Soundwave, recoge respuestas, invoca Validador y Crucero, pasa a Dossiero. Modelo: `max`.

#### Soundwave
Scheduler y router interno. Gestiona ejecución paralela, rate limiting al gateway LLM, backpressure, retry con backoff exponencial. No llama al LLM — es puro código asyncio. Modelo: N/A.

### Traductores especialistas por marco (7)

#### [[10_Agentes/TraductorISO]]
Especialista en ISO/IEC 27001:2022. Anexo A completo (93 controles, 4 dominios). Modelo: `max` en demo, `eco` en CI.

#### TraductorENS
Especialista en ENS 2022 (RD 311/2022). Marco org/op/mp, niveles Bajo/Medio/Alto, códigos tipo `op.acc.5`. Devuelve controles aplicables con nivel mínimo requerido.

#### TraductorNIS2
Especialista en Directiva UE 2022/2555. Artículos 20-23, sector esencial/importante, obligaciones de reporte.

#### TraductorDORA
Especialista en Reglamento UE 2022/2554. Enfoque financiero, resiliencia operativa digital, TLPT, terceros TIC.

#### TraductorRGPD
Especialista en Reglamento UE 2016/679. Base jurídica, artículos, considerandos, principios de minimización.

#### TraductorNIST
Especialista en NIST CSF 2.0. Funciones Govern/Identify/Protect/Detect/Respond/Recover.

#### TraductorPCI
Especialista en PCI DSS v4.0. Requisitos 1-12, SAQ aplicables, scope CDE.

### Validación y análisis (2)

#### [[10_Agentes/Validador]]
Critic agent. Recibe traducción + hallazgo original + fragmentos RAG usados. Verifica que la justificación está soportada por fragmentos reales (no alucinados), que la confianza declarada es coherente, que no hay controles inventados. Puede rechazar y devolver a reintentar. Modelo: `max` siempre — la precisión aquí es crítica.

#### Crucero
Analista de cruces. Dado el dossier parcial con N traducciones, detecta: (a) **conflictos** (marco A exige X, marco B exige lo contrario), (b) **intersecciones** (misma evidencia satisface controles de varios marcos — oportunidad de ahorro). Enriquece el dossier.

### Dossier y gate (2)

#### Dossiero
Compilador final. Recibe traducciones validadas + análisis de cruces. Produce `DossierMultimarco` exportable en JSON, PDF (skill pdf) y DOCX (skill docx) con formato de auditoría. Sin LLM — plantillas deterministas.

#### Gatemaster
Compliance gate para CI/CD. Recibe conjunto de hallazgos de un pipeline y una política (p.ej. "bloquea si hay hallazgos que mapean a A.8.24 sin evidencia compensatoria"). Devuelve exit code 0/1 y comentario para PR. Modelo: `eco` (debe ser rápido).

### Procedimientos y drift (1 — insight de Carlos)

#### Deriva
Detector de procedure drift. Entradas: (a) procedimiento escrito (MD/PDF ingerido), (b) secuencia de eventos reales observados por Vigilante. Compara y propone actualización o investigación del desvío. Ver [[06_Procedimientos]] y [[05_Hallazgos/insight-carlos-procedure-drift]]. MVP-5.

### Coordinación de sensores (2)

#### Reconocedor
Coordinador de adapters Red Team. Conoce Nuclei, Amass, Subfinder, theHarvester, Shodan, HIBP. Decide qué correr, normaliza outputs a `DatosRedTeam`. LLM solo si necesita decidir herramienta óptima.

#### Vigilante
Coordinador de adapters Blue Team. Conoce Wazuh, OpenSearch, Velociraptor, syslog. Consume alertas, normaliza a `DatosBlueTeam`, entrega a Deriva y/o Rosetta.

## Flujo canónico

```
HallazgoMaestro (de Reconocedor/Vigilante)
    ↓
Rosetta (decide marcos aplicables)
    ↓
Soundwave (paraleliza)
    ↓
[TraductorISO] [TraductorENS] [TraductorNIS2] ... (N traductores en paralelo)
    ↓
Validador (N veces, uno por traducción)
    ↓
Crucero (conflictos + intersecciones entre las N)
    ↓
Dossiero (compila y exporta)
    ↓
DossierMultimarco → API / Dashboard / Gatemaster
```

## Asignación de modelos por perfil

| Agente | eco (dev) | max (demo/prod) | test (CI) |
|--------|-----------|-----------------|-----------|
| Rosetta | qwen2.5:14b | claude-sonnet | stub |
| Traductores (7) | qwen2.5:14b | claude-sonnet | stub |
| Validador | qwen2.5:14b | claude-sonnet | stub |
| Crucero | qwen2.5:14b | claude-sonnet | stub |
| Deriva | qwen2.5:14b | claude-sonnet | stub |
| Gatemaster | llama3.1:8b | claude-haiku | stub |
| Dossiero, Soundwave, Reconocedor, Vigilante | N/A | N/A | N/A |

## Estado de implementación

- 🟡 **Rosetta**: existe versión proto-monolítica actual (Traductor único). Refactor previsto MVP-8.
- 🔴 **Traductores especialistas** (7): diseño, sin código.
- 🔴 **Validador**: diseño — pieza crítica MVP-8.
- 🔴 **Crucero**: diseño.
- 🟡 **Dossiero**: parcial en MVP-6 (export dashboard).
- 🟢 **Gatemaster**: en curso (MVP-7).
- 🔴 **Deriva**: previsto MVP-5, pendiente de reanudar.
- 🟢 **Reconocedor**: adapter Nuclei funcionando (MVP-2).
- 🔴 **Vigilante**: pendiente (MVP-4).
- 🔴 **Soundwave**: pendiente (entra con refactor MVP-8).

## Enlaces

- [[02_ADR/004-arquitectura-multi-agente]] · [[MOC_ADRs]]
- [[05_Hallazgos/patron-agentes-especializados]] · [[05_Hallazgos/patron-litellm-gateway]] · [[05_Hallazgos/patron-aislamiento-dual-red]]
- Inspiración externa: [[05_Hallazgos/referencia-decepticon]]
- [[MOC_Normativas]] · [[MOC_Roadmap]] · [[00_Dashboard]]
