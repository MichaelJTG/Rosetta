---
title: MOC · Normativas
tags: [moc, normativa, rosetta]
created: 2026-04-18
---

# MOC · Marcos normativos

> Mapa de todos los marcos que ROSETTA aspira a cubrir.
> Ver [[MOC_Roadmap]] para saber en qué MVP entra cada uno.

## Prioridad · en roadmap activo

### [[03_Normativa/ISO_27001_2022]]
- Estándar internacional · ISO/IEC 27001:2022
- Prioridad: **máxima** (núcleo del MVP-1)
- Obtener corpus: licencia ISO (costosa) o versiones comentadas públicas
- Integrado en MVP: [[MOC_Roadmap#MVP-1|MVP-1]]

### [[03_Normativa/ENS_2022]]
- Esquema Nacional de Seguridad · España · Real Decreto 311/2022
- Prioridad: **alta** (diferenciador ibérico)
- Obtener corpus: [BOE-A-2022-7191](https://www.boe.es/buscar/act.php?id=BOE-A-2022-7191) · público
- Integrado en MVP: [[MOC_Roadmap#MVP-3|MVP-3]]

## Prioridad · en roadmap medio

### [[03_Normativa/NIS2]]
- Directiva europea · NIS2 · DIR 2022/2555
- Prioridad: **alta** (obligatoria en UE 2024+)
- Corpus: EUR-Lex, público
- Integrado en: MVP-8+

### [[03_Normativa/DORA]]
- Digital Operational Resilience Act · Reglamento UE 2022/2554
- Prioridad: **alta** (sector financiero)
- Corpus: EUR-Lex, público
- Integrado en: MVP-8+

### [[03_Normativa/RGPD]]
- Reglamento General de Protección de Datos · UE 2016/679
- Prioridad: **alta** (transversal a todo dato personal)
- Corpus: EUR-Lex, público
- Integrado en: MVP-8+

## Prioridad · en roadmap largo

### [[03_Normativa/NIST_CSF_2]]
- NIST Cybersecurity Framework 2.0
- Prioridad: media (referencia técnica, no obligatoria en UE)
- Corpus: NIST, público
- Integrado en: MVP-8+

### [[03_Normativa/PCI_DSS_4]]
- Payment Card Industry Data Security Standard v4.0
- Prioridad: media (solo clientes con tarjeta)
- Corpus: PCI Council, requiere registro
- Integrado en: MVP-8+

## Intersecciones conocidas

Este mapa se irá completando conforme se analicen controles concretos. Ejemplos esperados:

- **Cifrado at-rest**: ISO A.8.24 ∧ ENS op.mon.1 ∧ RGPD art.32 ∧ PCI 3.5
- **MFA para acceso administrativo**: ISO A.5.16 ∧ ENS op.acc.5 ∧ NIS2 art.21.2.j
- **Gestión de parches**: ISO A.8.8 ∧ ENS op.exp.4 ∧ NIS2 art.21.2.e

Cada intersección descubierta va como nota en [[04_Controles]] con enlaces a los marcos afectados.
