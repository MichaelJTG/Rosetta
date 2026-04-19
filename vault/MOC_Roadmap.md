---
title: MOC · Roadmap
tags: [moc, roadmap, rosetta]
created: 2026-04-18
---

# MOC · Roadmap ROSETTA

> Map of Content del roadmap. Cada MVP tiene su anchor para poder enlazar desde cualquier nota.
> Fuente canónica: `docs/ROADMAP.md` en el repo. Este MOC es espejo enlazable.

## MVP-0 · Scaffold
Estado: ✅ completado · [[07_Sprints/2026-04-18_sprint-0|Sprint 0]]

Proyecto instalable con `uv sync --extra dev`. Estructura modular. Modelos Pydantic. Esqueletos de todos los módulos con `NotImplementedError`. Tests de modelos pasan.

## MVP-1 · Traductor Simbiótico sobre ISO 27001:2022
Estado: 🟡 pendiente · próximo · ver [[03_Normativa/ISO_27001_2022]]

Dado un `DatosRedTeam`, ROSETTA devuelve un `DatosCompliance` válido citando controles del Anexo A de [[03_Normativa/ISO_27001_2022|ISO 27001:2022]]. Sin API, solo CLI.

**Tareas:**
1. `CorpusLoader` · parsear ISO 27001:2022 Anexo A → fragmentos por control.
2. `NormativaRAG` · ChromaDB persistente, filtro por `framework_id`.
3. `TraductorSimbiotico.traducir()` · pipeline completo RAG + LLM tool-use.
4. CLI `rosetta translate <hallazgo.json> --marco iso_27001_2022`.
5. Tests E2E con 5 hallazgos canónicos.

**Criterio de aceptación:** 5/5 hallazgos devuelven control correcto top-1 o top-3 sin alucinar artículos.

## MVP-2 · Grafo y trazabilidad
Estado: ⚪ no empezado

Cada traducción persiste en Neo4j. Docker-compose con Neo4j Community. Consultas Cypher básicas. Exportación de dossier Markdown.

## MVP-3 · Segundo marco: ENS
Estado: ⚪ no empezado · ver [[03_Normativa/ENS_2022]]

Ingesta corpus ENS (RD 311/2022). Prompt multi-marco. Tests con hallazgos que afectan a uno, otro, o ambos.

## MVP-4 · Primer adaptador Red Team real: Nuclei
Estado: ⚪ no empezado

`NucleiAdapter.escanear()` con subprocess async. Pipeline completo sensor → traductor → grafo → dossier.

## MVP-5 · Procedure Drift
Estado: ⚪ no empezado · ver [[06_Procedimientos/insight-carlos-procedure-drift]]

Insight de Carlos Gómez Pintado. Comparar procedimiento escrito ↔ comportamiento observado por sensores → proponer actualización. El **killer feature** del proyecto en la visión del mentor.

## MVP-6 · API REST y dashboard
Estado: ⚪ no empezado

Endpoint `POST /translate`, `GET /findings`, `GET /compliance/state/{marco}`. Dashboard mínimo Next.js o Streamlit.

## MVP-7 · Gate de CI/CD
Estado: ⚪ no empezado

GitHub Action que ejecuta ROSETTA sobre diff de un PR y bloquea si introduce incumplimientos. Comentario en PR con control incumplido + línea + sugerencia.

## MVP-8+ · Ampliación
NIS2, DORA, NIST CSF 2, PCI-DSS v4, HIPAA, TISAX. Firma criptográfica RFC 3161. Multi-tenant. Packaging despliegue cliente.

---

## Los 9 problemas base

Checklist de validación: cada feature debe resolver uno de estos. Si no, se descarta.

- R1 · Detección por comportamiento (evasión EDR) — vía BAS + MITRE ATT&CK
- R2 · Fatiga del reconocimiento OSINT — vía adaptadores
- R3 · Mantenimiento infraestructura ofensiva — N/A (ROSETTA es defensivo)
- B1 · Shadow IT — cruce OSINT/inventario en grafo
- B2 · Alert fatigue — filtrado por relevancia normativa
- B3 · Falta de contexto en incidente — enriquecimiento con grafo
- **N1 · Gap técnico-legal** — núcleo del proyecto, [[02_ADR/001-orquestacion-sobre-fork|Traductor Simbiótico]]
- N2 · Cumplimiento estático vs dinámico — ejecución continua + grafo
- N3 · Cadena de suministro — ingesta de hallazgos sobre terceros
