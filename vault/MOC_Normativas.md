---
title: MOC · Normativas
tags: [moc, normativa, rosetta]
created: 2026-04-18
updated: 2026-04-19
---

# MOC · Marcos normativos

> Mapa de todos los marcos que ROSETTA aspira a cubrir.
> Ver [[MOC_Roadmap]] para saber en qué MVP entra cada uno.

## Operativos — corpus cargado en ChromaDB

### [[03_Normativa/ISO_27001_2022]]
- Estándar internacional · ISO/IEC 27001:2022
- **Estado**: ✅ corpus cargado · 93 controles indexados en ChromaDB
- **Cómo cargar**: `PYTHONIOENCODING=utf-8 uv run rosetta load-corpus iso_27001_2022 corpus/iso27001/`
- **Completado en**: [[MOC_Roadmap#MVP-1|MVP-1]] · [[07_Sprints/2026-04-18_sprint-1|Sprint 1]]
- **Probado con**: Ollama qwen2.5:14b · 2026-04-19

### [[03_Normativa/ENS_2022]]
- Esquema Nacional de Seguridad · España · Real Decreto 311/2022
- **Estado**: ✅ corpus preparado · 41 controles · pendiente cargar en ChromaDB de sesión actual
- **Cómo cargar**: `PYTHONIOENCODING=utf-8 uv run rosetta load-corpus ens_2022 corpus/ens/`
- **Completado en**: [[MOC_Roadmap#MVP-3|MVP-3]] · [[07_Sprints/2026-04-19_sprint-2|Sprint 2]]
- **Diferenciador**: único marco en español → ventaja competitiva en mercado ibérico

## En roadmap — corpus no cargado

### [[03_Normativa/NIS2]]
- Directiva europea · NIS2 · DIR 2022/2555
- **Estado**: 🔴 corpus no cargado
- **Prioridad**: alta (obligatoria en UE desde 2024)
- **Corpus**: EUR-Lex, público
- **MVP destino**: MVP-8+
- **Pasos**: añadir `MarcoNormativo.NIS2` al enum → descargar corpus → `load-corpus` → tests → nota vault

### [[03_Normativa/DORA]]
- Digital Operational Resilience Act · Reglamento UE 2022/2554
- **Estado**: 🔴 corpus no cargado
- **Prioridad**: alta (sector financiero, obligatorio)
- **Corpus**: EUR-Lex, público
- **MVP destino**: MVP-8+

### [[03_Normativa/RGPD]]
- Reglamento General de Protección de Datos · UE 2016/679
- **Estado**: 🔴 corpus no cargado
- **Prioridad**: alta (transversal a todo dato personal)
- **Corpus**: EUR-Lex, público
- **MVP destino**: MVP-8+

### [[03_Normativa/NIST_CSF_2]]
- NIST Cybersecurity Framework 2.0
- **Estado**: 🔴 corpus no cargado
- **Prioridad**: media (referencia técnica, no obligatoria en UE)
- **Corpus**: NIST, público
- **MVP destino**: MVP-8+

### [[03_Normativa/PCI_DSS_4]]
- Payment Card Industry Data Security Standard v4.0
- **Estado**: 🔴 corpus no cargado
- **Prioridad**: media (solo clientes con tarjeta)
- **MVP destino**: MVP-8+

## Cómo añadir un marco nuevo

Ver `CLAUDE.md §6`. En resumen:

1. Añadir valor al enum `MarcoNormativo` en `src/rosetta/core/models.py`
2. Crear `corpus/<marco>/` con texto fuente (PDF o MD)
3. `PYTHONIOENCODING=utf-8 uv run rosetta load-corpus <marco> corpus/<marco>/`
4. Tests en `tests/test_<marco>.py` con ≥3 hallazgos canónicos
5. Actualizar esta nota y [[00_Dashboard]]

## Intersecciones conocidas

Controles que se solapan entre marcos — cada intersección es una ventaja del Traductor multi-marco:

| Tema | ISO 27001 | ENS | NIS2 | RGPD |
|------|-----------|-----|------|------|
| Autenticación/MFA | A.5.16 | op.acc.5 | art.21.2.j | — |
| Cifrado en tránsito | A.8.24 | mp.com.2 | art.21.2.h | art.32 |
| Registro de eventos | A.8.15 | op.mon.1 | art.21.2.g | art.5.2 |
| Gestión de parches | A.8.8 | op.exp.4 | art.21.2.e | — |

Cada intersección descubierta puede ir como nota en [[04_Controles]] con enlaces a los marcos afectados.
