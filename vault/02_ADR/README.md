---
title: Architecture Decision Records
tags: [adr, indice]
---

# ADR — Architecture Decision Records

Las decisiones de arquitectura oficiales viven en `docs/adr/` del repositorio (Markdown versionado con el código). Aquí en el vault mantenemos una **copia resumida y con tags de Obsidian** para poder enlazar bidireccionalmente con el resto de notas (reuniones, sprints, normativa).

## Regla

Cada ADR nuevo creado en `docs/adr/NNN-titulo.md` debe tener su contraparte aquí en `vault/02_ADR/NNN-titulo.md` con frontmatter y links a notas relacionadas.

## Índice

- [[001-orquestacion-sobre-fork]] · Decidimos orquestar open source, no forkear.
- [[002-abstraccion-del-proveedor-llm]] · Interfaz LLMClient: Claude / Ollama / OpenAI intercambiables.
