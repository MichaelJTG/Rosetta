---
title: NIST Cybersecurity Framework 2.0
tags: [normativa, normativa/nist, rosetta]
marco_id: nist_csf_2
created: 2026-04-18
estado_corpus: no_cargado
prioridad: media
mvp: MVP-8
---

# NIST Cybersecurity Framework 2.0

> Marco voluntario del NIST. Referencia técnica de uso global, no obligatorio en UE pero ampliamente adoptado.

## Datos rápidos

- **Publicador**: NIST (EE. UU.)
- **Versión**: 2.0 (febrero 2024)
- **Acceso al corpus**: público, NIST.gov
- **Naturaleza**: voluntario · best practices

## Las 6 funciones del CSF 2.0

1. **GOVERN** (nuevo en 2.0) · gobernanza, contexto organizacional, supervisión
2. **IDENTIFY** · activos, riesgos, política
3. **PROTECT** · controles preventivos
4. **DETECT** · monitorización y detección
5. **RESPOND** · respuesta a incidentes
6. **RECOVER** · recuperación y lecciones aprendidas

Cada función se descompone en categorías y subcategorías con código (`PR.AA-01`, `DE.CM-09`…).

## Por qué incluirlo

- Es la "lengua común" de la ciberseguridad técnica en EE. UU. y multinacionales.
- Sus subcategorías son las **piezas más pequeñas y unívocas** del panorama normativo → ideal como pivote para mapeos cruzados.
- Permite a ROSETTA trabajar con clientes que no usan ISO sino "NIST puro".

## Particularidad para el RAG

Las subcategorías del CSF 2.0 son muy específicas y cortas (1-3 frases). Esto las hace **ideales para embeddings**: alta precisión semántica con poco contexto.

## Enlaces

- [[MOC_Normativas]] · [[03_Normativa/ISO_27001_2022]]
- NIST: https://www.nist.gov/cyberframework
