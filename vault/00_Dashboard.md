---
title: Dashboard ROSETTA
tags: [dashboard, rosetta]
created: 2026-04-18
updated: 2026-04-19
sprint_actual: 3
mvp_actual: MVP-7
mvp_estado: completado
proximo_mvp: MVP-8
llm_proveedor: ollama (desarrollo) / claude (validación)
marcos_cargados: []
adapters_activos: []
---

# Dashboard ROSETTA

> Fuente única de verdad del estado del proyecto. Se actualiza conforme avanza la obra.
> El resto del vault es contexto; este archivo es el "salpicadero".

## Estado actual

- **MVP en curso**: MVP-8 ⚪ próximo (NIS2, DORA, NIST CSF 2)
- **MVP anterior**: MVP-7 ✅ completado (`POST /analyze-diff` · GitHub Action · 141 tests)
- **Sprint activo**: [[07_Sprints/2026-04-21_sprint-3|Sprint 3]] ✅ Gate CI/CD completo
- **LLM provider**: [[02_ADR/002-abstraccion-llm|ADR-002]] ✅ aprobada · ollama (dev) / claude (validación)

## Marcos normativos

- [[03_Normativa/ISO_27001_2022]] · ✅ corpus cargado (93 controles intuitem)
- [[03_Normativa/ENS_2022]] · ✅ corpus cargado (41 controles RD 311/2022, BOE)
- [[03_Normativa/NIS2]] · 🔴 corpus no cargado
- [[03_Normativa/DORA]] · 🔴 corpus no cargado
- [[03_Normativa/RGPD]] · 🔴 corpus no cargado
- [[03_Normativa/NIST_CSF_2]] · 🔴 corpus no cargado
- [[03_Normativa/PCI_DSS_4]] · 🔴 corpus no cargado

## Adaptadores

### Red Team
- Nuclei · ✅ implementado (async subprocess, parser JSON v3)
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
