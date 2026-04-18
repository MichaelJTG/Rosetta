---
title: Procedimientos y procedure drift
tags: [procedimiento, indice, mentor/carlos]
---

# Procedimientos y procedure drift

Esta sección existe por el **insight crítico de Carlos Gómez Pintado**: el gran dolor real de las empresas no es detectar vulnerabilidades, es que los procedimientos internos escritos divergen de la realidad operativa y nadie los actualiza.

## Objetivo

Documentar el diseño del módulo de procedure drift detection (MVP-5 en el roadmap): cómo ROSETTA compara "lo que el procedimiento dice" contra "lo que los sensores observan" y propone actualizaciones automáticas.

## Fases previstas

1. Ingesta de procedimientos internos al RAG con metadato `tipo: procedimiento`.
2. Función `detectar_drift(procedimiento_id, observaciones)`.
3. Comparación semántica LLM entre redacción escrita y realidad.
4. Propuesta de diff redacción actualizada.

## Notas

- [[insight-carlos-procedure-drift]] · Apunte original del mentor y su implicación en el diseño.
