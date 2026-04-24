---
title: Dashboard ROSETTA
tags: [dashboard, rosetta]
created: 2026-04-18
updated: 2026-04-19
sprint_actual: 7
mvp_actual: MVP-9
mvp_estado: completado
proximo_mvp: MVP-10
llm_proveedor: ollama (desarrollo) / claude (validación)
marcos_cargados: [iso_27001_2022, ens_2022, nis2, dora, rgpd, nist_csf_2, pci_dss_4]
adapters_activos: [nuclei, nmap, wazuh]
---

# Dashboard ROSETTA

> Fuente única de verdad del estado del proyecto. Se actualiza conforme avanza la obra.
> El resto del vault es contexto; este archivo es el "salpicadero".

## Estado actual

- **MVP en curso**: MVP-9 ✅ (FASE 7 polish completada — auth, SQLite, vis.js, Drift panel · 332 tests)
- **MVP anterior**: MVP-8 ✅ (corpus DORA, RGPD, NIST CSF 2, PCI-DSS 4 — FASE 6)
- **Sprint activo**: Sprint 7 🟢 FASE 7 cerrada · PLAN_V4 completo · próximo: hardening/comercialización
- **LLM provider**: [[02_ADR/002-abstraccion-llm|ADR-002]] ✅ · [[02_ADR/004-arquitectura-multi-agente|ADR-004]] ✅ aprobada

## Marcos normativos

- [[03_Normativa/ISO_27001_2022]] · ✅ corpus cargado (93 controles intuitem)
- [[03_Normativa/ENS_2022]] · ✅ corpus cargado (41 controles RD 311/2022, BOE)
- [[03_Normativa/NIS2]] · ✅ corpus cargado (NIS2-2022 articles)
- [[03_Normativa/DORA]] · ✅ corpus cargado (13 artículos DORA-2022/2554)
- [[03_Normativa/RGPD]] · ✅ corpus cargado (9 artículos RGPD-2016/679)
- [[03_Normativa/NIST_CSF_2]] · ✅ corpus cargado (14 subcategorías NIST CSF 2.0)
- [[03_Normativa/PCI_DSS_4]] · ✅ corpus cargado (12 requisitos PCI-DSS 4.0)

## Adaptadores

### Red Team
- Nuclei · ✅ implementado (async subprocess, parser JSON v3)
- Amass · 🟡 esqueleto sin implementar
- Subfinder · ⚪ no empezado
- theHarvester · ⚪ no empezado
- Shodan · ⚪ no empezado
- HIBP · ⚪ no empezado

### Blue Team
- Wazuh · ✅ implementado (JWT auth, ingestar JSON/CSV, correlación Red↔Blue)
- OpenSearch · ⚪ no empezado
- Velociraptor · ⚪ no empezado

## Decisiones clave

- [[02_ADR/001-orquestacion-sobre-fork|ADR-001]] · ✅ aprobada · Orquestación sobre fork
- [[02_ADR/002-abstraccion-llm|ADR-002]] · ✅ aprobada · Abstracción de proveedor LLM
- [[02_ADR/004-arquitectura-multi-agente|ADR-004]] · ✅ aprobada · Arquitectura multi-agente (FASE 5)

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
