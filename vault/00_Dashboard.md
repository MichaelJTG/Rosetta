---
title: Dashboard ROSETTA
tags: [dashboard, rosetta]
created: 2026-04-18
updated: 2026-04-19
sprint_actual: 2
mvp_actual: MVP-2
mvp_estado: en-curso
proximo_mvp: MVP-3
llm_proveedor: ollama (desarrollo) / claude (validación)
marcos_cargados: []
adapters_activos: []
---

# Dashboard ROSETTA

> Fuente única de verdad del estado del proyecto. Se actualiza conforme avanza la obra.
> El resto del vault es contexto; este archivo es el "salpicadero".

## Estado actual

- **MVP en curso**: MVP-2 🟢 en curso · [[MOC_Roadmap#MVP-2|Grafo Neo4j y trazabilidad]]
- **MVP anterior**: MVP-1 ✅ completado (Traductor Simbiótico ISO 27001:2022, 5 hallazgos canónicos)
- **Sprint activo**: [[07_Sprints/2026-04-19_sprint-2|Sprint 2]] 🟢 GrafoCorrelacion implementado
- **LLM provider**: [[02_ADR/002-abstraccion-llm|ADR-002]] 🟡 pendiente aprobación · ollama (dev) / claude (validación)

## Marcos normativos

- [[03_Normativa/ISO_27001_2022]] · 🟡 corpus descargado (93 controles, pendiente ingesta ChromaDB)
- [[03_Normativa/ENS_2022]] · 🔴 corpus no cargado
- [[03_Normativa/NIS2]] · 🔴 corpus no cargado
- [[03_Normativa/DORA]] · 🔴 corpus no cargado
- [[03_Normativa/RGPD]] · 🔴 corpus no cargado
- [[03_Normativa/NIST_CSF_2]] · 🔴 corpus no cargado
- [[03_Normativa/PCI_DSS_4]] · 🔴 corpus no cargado

## Adaptadores

### Red Team
- Nuclei · 🟡 esqueleto sin implementar
- Amass · 🟡 esqueleto sin implementar
- Subfinder · ⚪ no empezado
- theHarvester · ⚪ no empezado
- Shodan · ⚪ no empezado
- HIBP · ⚪ no empezado

### Blue Team
- Wazuh · 🟡 esqueleto sin implementar
- OpenSearch · ⚪ no empezado
- Velociraptor · ⚪ no empezado

## Decisiones clave

- [[02_ADR/001-orquestacion-sobre-fork|ADR-001]] · ✅ aprobada · Orquestación sobre fork
- [[02_ADR/002-abstraccion-llm|ADR-002]] · ✅ aprobada · Abstracción de proveedor LLM

## Navegación rápida

- [[00_Bitacora]] · Histórico de acciones
- [[00_Index]] · Índice del vault
- [[MOC_Roadmap]] · Mapa de contenidos del roadmap
- [[MOC_ADRs]] · Mapa de ADRs
- [[MOC_Normativas]] · Mapa de marcos normativos
- [[MOC_Sprints]] · Mapa de sprints
- [[MOC_Hallazgos]] · Mapa de hallazgos canónicos

## Mentoría

- [[08_Reuniones/pendiente-carlos-gomez|Reunión pendiente con Carlos]]
- [[06_Procedimientos/insight-carlos-procedure-drift|Insight de Carlos · Procedure drift]]

## Leyenda de estados

- ✅ completado · 🟢 en curso · 🟡 parcial / pendiente · 🔴 bloqueado / no empezado · ⚪ no planificado aún
