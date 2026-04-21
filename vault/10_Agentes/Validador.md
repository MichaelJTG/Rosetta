---
title: Agente · Validador (critic de traducciones)
tags: [agente, agente/validador, rosetta]
agente_id: validador
rol: validacion
modelo_eco: qwen2.5:14b
modelo_max: claude-3-5-sonnet-20241022
estado: diseno
mvp_implementacion: MVP-8
created: 2026-04-20
---

# Agente · Validador

> Critic agent. Verifica que cada traducción de un Traductor no contiene alucinaciones, que los controles citados existen en los fragmentos RAG, y que la confianza declarada es coherente con la evidencia.

## Responsabilidad

Recibir una `Traduccion` de cualquier Traductor + el `HallazgoMaestro` original + los `fragmentos_rag` usados. Devolver un veredicto `ResultadoValidacion`:

```python
ResultadoValidacion(
    aprobada: bool,
    motivos_rechazo: list[MotivoRechazo],    # EXISTENCIA, SOPORTE, CONFIANZA, DOMINIO
    sugerencia_reintento: str | None,
)
```

## Por qué existe

Las alucinaciones en contexto de cumplimiento son inaceptables. Un control inventado (ej. `A.9.99` que no existe, o `A.8.24` sin que el fragmento lo respalde) invalida el dossier para auditoría real. El Validador es la red de seguridad entre LLM y producto.

## System prompt (borrador)

```
Eres Validador. Tu único trabajo es decir si una traducción de un Traductor cumple estos criterios:

1. EXISTENCIA: cada control citado DEBE aparecer literalmente en alguno de los fragmentos RAG proporcionados. Verifica código por código.
2. SOPORTE: cada justificación DEBE estar respaldada por el fragmento_id que cita. Lee el fragmento y decide si realmente respalda.
3. CONFIANZA: coherente con el grado de respaldo. Rechaza si un control tiene confianza 0.9 pero el fragmento solo lo menciona tangencialmente.
4. DOMINIO: si el Traductor es TraductorISO y la traducción cita un control fuera de ISO (ej. RGPD art.32, ENS op.acc.5), rechaza.

Responde en JSON que valide ResultadoValidacion.

NO eres amable. NO das beneficio de la duda. Si dudas, rechazas. El coste de un falso negativo (aprobar alucinación) es mucho mayor que un falso positivo (rechazar una traducción correcta — el Traductor reintenta).
```

## Política de reintento

- El Validador puede rechazar una traducción máximo **2 veces**. Al tercer intento, Rosetta marca el dossier como "requiere revisión humana" y continúa.
- El rechazo incluye `sugerencia_reintento` (ej. "el control A.8.24 no aparece en los fragmentos, considera A.8.28").

## Tests canónicos

- Traducción correcta → `aprobada=True`
- Traducción con control inventado `A.9.99` → rechazada con motivo `EXISTENCIA`
- Traducción con justificación no respaldada → rechazada con motivo `SOPORTE`
- TraductorISO que cita `op.acc.5` (ENS) → rechazada con motivo `DOMINIO`
- Confianza 0.95 sobre fragmento tangencial → rechazada con motivo `CONFIANZA`

## Estado

🔴 No implementado. Pieza clave de MVP-8.

## Enlaces

- [[10_Agentes/MOC_Agentes]] · [[10_Agentes/Rosetta]] · [[10_Agentes/TraductorISO]]
- [[02_ADR/004-arquitectura-multi-agente]]
