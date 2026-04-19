# START_HERE — Arranque del proyecto ROSETTA

> Un archivo, una acción. A partir de aquí el proyecto vive en Claude Code + Obsidian.

---

## Paso 1 · Obsidian

Abre Obsidian → **Open folder as vault** → selecciona:

```
C:\Users\WorkStation\Desktop\Rosetta\vault
```

Abre `00_Dashboard.md`. Activa el grafo con **Ctrl+G**. Deja Obsidian abierto en una mitad de la pantalla.

## Paso 2 · Claude Code

En la otra mitad, PowerShell:

```powershell
cd C:\Users\WorkStation\Desktop\Rosetta
claude
```

## Paso 3 · El único prompt que necesitas

Pega esto y déjalo trabajar:

```
Lee HANDOFF.md y luego arranca la primera sesión autónoma siguiendo MISSION.md.
```

Ya está. Claude Code tiene todo el contexto del proyecto (historia, decisiones, scope, roadmap,
límites, artefactos) en `HANDOFF.md` y las reglas de operación autónoma en `MISSION.md`. Avanzará
solo hasta alcanzar los checkpoints definidos (ADR-002, corpus ISO, cierre). En cada checkpoint
te pregunta.

## Para sesiones posteriores

El prompt de arranque siempre es uno de estos tres, según lo que quieras:

- `sigue` · continúa donde quedó la última sesión, según bitácora.
- `arranca MVP-N` · salta al MVP N si el anterior ya cumplió criterio de aceptación.
- `revisa el estado y dime por dónde vamos` · lee dashboard + bitácora y resume.

## Si Claude Code se pierde

Un único remedio:

```
Para. Vuelve a leer HANDOFF.md, MISSION.md y vault/00_Bitacora.md. Luego dime dónde estabas.
```

## Archivos clave del proyecto

- `CLAUDE.md` · contexto y reglas
- `MISSION.md` · misión autónoma con checkpoints
- `HANDOFF.md` · historia completa y estado del proyecto
- `docs/ROADMAP.md` · 8 MVPs con criterios
- `vault/00_Dashboard.md` · estado actual
- `vault/00_Bitacora.md` · histórico vivo
