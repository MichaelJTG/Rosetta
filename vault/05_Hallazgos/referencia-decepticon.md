---
title: Referencia externa · Decepticon (PurpleAILAB)
tags: [hallazgo, referencia, externa, rosetta]
categoria: referencia-externa
created: 2026-04-20
url: https://github.com/PurpleAILAB/Decepticon
licencia: Apache-2.0
stars_observados: 2300
---

# Referencia externa · Decepticon

> Repo ofensivo autónomo (PurpleAILAB, Apache-2.0) del que ROSETTA extrae **patrones arquitectónicos**, NO funcionalidad ni código.

## Qué es Decepticon

*"Autonomous Hacking Agent for Red Team Testing"*. Ejecuta kill chains completas (recon, exploit, priv-esc, lateral, C2) como adversario real. Se autodenomina *"Offensive Vaccine"*.

Arquitectura observada:
- **16 agentes especializados** orquestados con **LangGraph**.
- Gateway multi-LLM vía **LiteLLM** (perfiles `eco`/`max`/`test`, fallback entre proveedores).
- Grafo de conocimiento en **Neo4j**.
- Sandbox **Kali dockerizado** con dos redes aisladas (`decepticon-net` management vs `sandbox-net` operations).
- Sesiones tmux persistentes con detección de prompt para shells interactivos.
- Python 72% + TypeScript 23% (dashboard web).

Tracción: ~2.3k stars, ~400 forks, v1.0.6 activa (abr-2026).

## Alineación con ROSETTA: negativa a nivel de producto

Decepticon **ejecuta** ataques. ROSETTA **traduce** hallazgos a cumplimiento. Son capas ortogonales. No es competidor, no es adaptador candidato. Si Carlos pregunta: "son capas distintas del stack de seguridad, y confundirlas debilita el pitch del Traductor Simbiótico".

Meter un agente autónomo ofensivo como sensor de ROSETTA violaría el principio *"orquestar herramientas deterministas"* de CLAUDE.md §4.

## Alineación con ROSETTA: positiva a nivel de patrones

Tres patrones arquitectónicos que ROSETTA adopta (derivados, no copiados):

1. [[patron-litellm-gateway]] — gateway multi-proveedor con fallback.
2. [[patron-agentes-especializados]] — contexto fresco por agente.
3. [[patron-aislamiento-dual-red]] — management vs operations.

Cada uno documentado como nota independiente de patrón.

## Qué NO copiamos de Decepticon

- **El kill chain ofensivo**. ROSETTA no ejecuta ataques. CLAUDE.md §2 explícito.
- **LangGraph**. ROSETTA puede orquestar con código plano Python + asyncio si no necesita DAGs dinámicos. Evaluación pendiente en MVP-8 — decisión en el ADR.
- **El sandbox Kali**. No aplica.
- **Su dashboard TypeScript**. ROSETTA tiene dashboard propio en MVP-6.

## Recomendación firme

- **No referenciar en ADRs nucleares** (distorsiona el enfoque de compliance).
- **Sí citar como origen** en las 3 notas de patrón que sí adoptamos.
- **Sí admitir la inspiración** si un auditor o Carlos pregunta — es Apache-2.0 y los patrones no son propiedad de nadie.
- **No usar código** de Decepticon. Reimplementar los patrones en Python propio para mantener el principio de "orquestar, no forkear".

## Enlaces

- [[patron-litellm-gateway]] · [[patron-agentes-especializados]] · [[patron-aislamiento-dual-red]]
- [[10_Agentes/MOC_Agentes]] · [[MOC_Hallazgos]]
- [[02_ADR/004-arquitectura-multi-agente]]
- URL: https://github.com/PurpleAILAB/Decepticon
