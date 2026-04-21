---
title: Agente · Rosetta (orquestador principal)
tags: [agente, agente/orquestador, rosetta]
agente_id: rosetta
rol: orquestacion
modelo_eco: qwen2.5:14b
modelo_max: claude-3-5-sonnet-20241022
estado: proto-monolitico
mvp_refactor: MVP-8
created: 2026-04-20
---

# Agente · Rosetta

> Orquestador principal. Entry point del núcleo cognitivo.

## Responsabilidad

Recibir un `HallazgoMaestro` y producir un `DossierMultimarco` coordinando al resto de agentes. NO traduce por sí mismo — **delega** en los Traductores especialistas.

## Input

```python
HallazgoMaestro(
    id: UUID,
    tipo: TipoHallazgo,
    severidad: Severidad,
    fuente: FuenteHallazgo,      # qué adapter lo produjo
    evidencia: dict,
    contexto_tecnico: str,
    marcos_solicitados: list[MarcoNormativo] | None,
)
```

## Output

```python
DossierMultimarco(
    hallazgo_id: UUID,
    traducciones: list[Traduccion],    # una por marco
    conflictos: list[Conflicto],
    intersecciones: list[Interseccion],
    estado_validacion: EstadoValidacion,
    metadata: dict,
)
```

## Flujo interno

1. Determinar qué marcos aplican: si `marcos_solicitados` es `None`, usar `ROSETTA_MARCOS` de config (hoy `iso_27001_2022,ens_2022`).
2. Para cada marco, invocar `Soundwave.schedule(traductor_id, hallazgo)` en paralelo.
3. Recoger `Traduccion` de cada Traductor.
4. Para cada traducción, invocar `Validador.validate(traduccion, hallazgo, fragmentos_rag)`. Si rechaza, reintentar Traductor una vez con temperatura ligeramente distinta.
5. Invocar `Crucero.analizar(traducciones)` → conflictos + intersecciones.
6. Invocar `Dossiero.compilar(...)` → `DossierMultimarco`.
7. Persistir en Neo4j y devolver.

## System prompt (borrador)

```
Eres Rosetta, el orquestador de un sistema de traducción de hallazgos técnicos a evidencia de cumplimiento multi-marco.

Tu trabajo NO es traducir. Tu trabajo es decidir qué agentes especialistas deben intervenir dado un hallazgo y un conjunto de marcos aplicables, y sintetizar sus salidas.

Reglas:
- NUNCA respondas un control normativo tú mismo. Delega siempre al Traductor del marco correspondiente.
- Si un hallazgo es ambiguo, PRIMERO pregunta al usuario antes de disparar agentes (evita desperdiciar tokens).
- Si el Validador rechaza una traducción dos veces seguidas, marca el dossier como "requiere revisión humana" y continúa con el resto.
- Responde en JSON que valide DossierMultimarco.
```

## Herramientas disponibles

- `soundwave.schedule(agent_id, payload)` — única forma de invocar otros agentes.
- `neo4j.persist_dossier(dossier)` — persistencia final.
- **Sin** acceso a ChromaDB ni a corpus directamente (eso es trabajo de Traductores).

## Estado actual

🟡 Proto-monolítico: hoy el "orquestador" es la función `traducir_hallazgo()` en `src/rosetta/core/traductor.py` que hace todo (routing + traducción + validación implícita). Funciona para 1-2 marcos.

🎯 Refactor previsto en MVP-8 con [[02_ADR/004-arquitectura-multi-agente]].

## Enlaces

- [[10_Agentes/MOC_Agentes]] · [[02_ADR/004-arquitectura-multi-agente]]
- Dependencias: [[10_Agentes/TraductorISO]] · [[10_Agentes/Validador]] · Crucero · Dossiero
