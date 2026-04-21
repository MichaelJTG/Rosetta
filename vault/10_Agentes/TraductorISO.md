---
title: Agente · TraductorISO (especialista ISO 27001:2022)
tags: [agente, agente/traductor, normativa/iso27001, rosetta]
agente_id: traductor_iso
rol: traduccion
marco: iso_27001_2022
modelo_eco: qwen2.5:14b
modelo_max: claude-3-5-sonnet-20241022
estado: diseno
mvp_implementacion: MVP-8
created: 2026-04-20
---

# Agente · TraductorISO

> Especialista en ISO/IEC 27001:2022. Traduce hallazgos técnicos a controles del Anexo A con justificación y confianza.

## Responsabilidad

Dado un `HallazgoMaestro` y fragmentos RAG filtrados al corpus ISO, producir una `Traduccion` con los controles del Anexo A aplicables, su justificación basada en los fragmentos (nunca alucinada), y una confianza [0.0-1.0] por control.

## Input

```python
InputTraductor(
    hallazgo: HallazgoMaestro,
    fragmentos_rag: list[FragmentoNormativa],   # top-k de ChromaDB, SOLO corpus ISO
    contexto: ContextoSesion | None,
)
```

## Output

```python
Traduccion(
    marco: MarcoNormativo.ISO_27001_2022,
    hallazgo_id: UUID,
    controles_aplicables: list[ControlAplicable],
    # ControlAplicable = (id, justificacion, confianza, fragmento_id)
    notas: str | None,
    timestamp: datetime,
)
```

## System prompt (borrador)

```
Eres TraductorISO, un especialista en ISO/IEC 27001:2022 Anexo A.

Conoces la estructura: 93 controles en 4 dominios
- A.5 organizacionales (37)
- A.6 personas (8)
- A.7 físicos (14)
- A.8 tecnológicos (34)

Tu trabajo: dado un hallazgo técnico y fragmentos del Anexo A recuperados por RAG, identificar los controles aplicables.

REGLAS DURAS:
- SOLO puedes citar controles que aparezcan en los fragmentos proporcionados. Nunca inventes códigos.
- Cada control propuesto DEBE ir con fragmento_id que lo respalda.
- Confianza refleja ambigüedad real: 1.0 solo si el fragmento dice literalmente el mismo caso; 0.6-0.8 si es análogo claro; <0.5 si es interpretación.
- NO hagas cross-framework: si el hallazgo podría mapear a ENS/RGPD/NIS2, NO lo menciones — no es tu trabajo.
- Responde SIEMPRE en formato JSON que valide contra Traduccion.
```

## Herramientas disponibles

- Lectura de fragmentos pre-recuperados (no llama a ChromaDB directamente).
- **Sin** acceso a otros marcos, Neo4j ni adapters.

## Controles que más aparecerán

Ver [[03_Normativa/ISO_27001_2022]]: A.5.15, A.5.16, A.5.17, A.8.8, A.8.15, A.8.16, A.8.20, A.8.22, A.8.24, A.8.28.

## Tests canónicos

Ver [[MOC_Hallazgos]]. Al menos estos 5 deben pasar:

- [[05_Hallazgos/aws-key-leak]] → A.8.24 + A.5.15 (hoy valida con A.5.23 + A.8.4 vía qwen2.5:14b, aceptable)
- [[05_Hallazgos/puerto-rdp-expuesto]] → A.8.20 + A.8.22
- [[05_Hallazgos/sin-mfa]] → A.5.16 + A.5.17
- [[05_Hallazgos/sin-cifrado-en-transito]] → A.8.24
- [[05_Hallazgos/logs-no-centralizados]] → A.8.15 + A.8.16

## Estado

🔴 No implementado como agente independiente. Hoy la lógica vive dentro del Traductor monolítico. Refactor previsto con [[02_ADR/004-arquitectura-multi-agente]].

## Enlaces

- [[10_Agentes/MOC_Agentes]] · [[10_Agentes/Rosetta]] · [[10_Agentes/Validador]]
- [[03_Normativa/ISO_27001_2022]] · [[MOC_Normativas]]
- [[02_ADR/004-arquitectura-multi-agente]]
