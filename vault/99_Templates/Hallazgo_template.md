---
title: Hallazgo canónico · <nombre-corto>
tags: [hallazgo, normativa/<marco>]
hallazgo_id: <slug>
origen: <fuente-redteam>
severidad: <informativa|baja|media|alta|critica>
marcos_aplicables: [<marco1>, <marco2>]
controles_esperados: [<control1>, <control2>]
example_json: examples/<archivo>.json
created: YYYY-MM-DD
---

# Hallazgo · <nombre>

## Descripción

Descripción en lenguaje natural de la situación técnica.

## Vector de ataque

Qué hace un atacante con esto. Por qué es peligroso.

## Ejemplo JSON

Ver `examples/<archivo>.json`.

## Traducción esperada

### Marco <marco1>

- Controles incumplidos: `<ID>`, `<ID>`.
- Cita textual esperada del RAG: "…"
- Acción de mitigación: …

### Marco <marco2>

- Controles incumplidos: `<ID>`.
- Cita textual esperada: "…"
- Acción de mitigación: …

## Gotchas

Cosas que pueden hacer fallar al Traductor en este caso: ambigüedades, controles que se confunden con otros similares, falsos positivos típicos.

## Relacionado con

- [[05_Hallazgos]]
- [[04_Controles/<control>]]
