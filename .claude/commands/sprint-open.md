---
description: Abre una nota de sprint en el vault de Obsidian para la sesión de trabajo actual
argument-hint: "<número de sprint>"
model: claude-sonnet-4-6
---

Vas a abrir una nueva nota de sprint en el vault de Obsidian de ROSETTA.

## Pasos

1. **Lee la plantilla** en `vault/99_Templates/Sprint_template.md` si existe. Si no existe, usa la plantilla por defecto de abajo.

2. **Determina la fase MVP activa** leyendo `docs/ROADMAP.md` — identifica qué MVP está marcado como "en curso" o cuál es el siguiente no completado.

3. **Crea el archivo** `vault/07_Sprints/2026-04-18_sprint-$ARGUMENTS.md` con el siguiente contenido (adapta según la plantilla si existe):

```markdown
---
fecha_inicio: 2026-04-18
sprint: $ARGUMENTS
mvp_activo: MVP-X
estado: abierto
tags:
  - sprint/$ARGUMENTS
  - mvp/X
---

# Sprint $ARGUMENTS — 2026-04-18

## Objetivo del sprint

<!-- Define en 1-3 frases qué quieres conseguir hoy. Vincula a un criterio de aceptación del ROADMAP. -->

## Tareas planificadas

- [ ]
- [ ]
- [ ]

## Contexto de inicio

<!-- Estado del proyecto al abrir este sprint: último commit, tests en verde/rojo, bloqueos previos -->

---

## Hecho

<!-- Rellena al cerrar con /sprint-close -->

## Aprendizajes

<!-- Rellena al cerrar con /sprint-close -->

## Bloqueos / Próximos pasos

<!-- Rellena al cerrar con /sprint-close -->
```

4. **Informa al usuario** que la nota fue creada y recuérdale que al terminar use `/sprint-close` para registrar lo hecho.

El número de sprint es: $ARGUMENTS
