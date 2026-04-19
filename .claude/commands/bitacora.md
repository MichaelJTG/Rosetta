---
description: Añade una entrada a vault/00_Bitacora.md con el formato exacto de CLAUDE.md sección 14.6
argument-hint: "<acción corta, ej: refactor CorpusLoader, tests MVP-1 en verde>"
model: claude-sonnet-4-6
---

Vas a añadir una nueva entrada a la bitácora del proyecto ROSETTA siguiendo el formato exacto de CLAUDE.md §14.6.

## Pasos

1. **Lee las últimas entradas** de `vault/00_Bitacora.md` para entender el contexto inmediato y evitar duplicados.

2. **Determina la acción corta** a partir del argumento recibido: `$ARGUMENTS`. Si no se proporciona argumento, infiere la acción más relevante del contexto de la conversación actual.

3. **Construye la entrada** siguiendo este formato EXACTO (copia y adapta — no cambies la estructura):

```markdown
## 2026-04-18 HH:MM · <acción corta>
- **Hecho**: <qué se hizo, específico y verificable>
- **Por qué**: <razón corta — decisión, hallazgo, bloqueo>
- **Archivos**: `ruta/al/archivo.py` · [[nota-vault-si-aplica]]
- **Enlaces**: [[MOC_relevante]] · [[otra-nota]]
- **Estado**: ✅ hecho | 🟡 parcial | 🔴 bloqueado
```

Reglas para rellenar cada campo:
- **Hecho**: describe QUÉ cambió (módulo creado, test que pasa, ADR redactado). No digas "trabajé en X", di "X implementado y cubierto con N tests".
- **Por qué**: una frase. Menciona la motivación (MVP-N, criterio de aceptación, decisión del usuario, bloqueo externo).
- **Archivos**: lista los archivos de código o vault más relevantes. Usa `` `ruta` `` para archivos del repo y `[[enlace]]` para notas del vault.
- **Enlaces**: los MOCs y notas más relacionadas con esta entrada (ej. [[MOC_ADRs]], [[07_Sprints/2026-04-18_sprint-1]]).
- **Estado**: elige solo uno de los tres.

4. **Inserta la entrada al principio** del cuerpo de `vault/00_Bitacora.md`, justo después del bloque `---` (separador del frontmatter / bloque de formato). Mantén el orden cronológico inverso: lo más reciente arriba.

5. **Confirma** al usuario que la entrada fue añadida y muéstrale el texto insertado.

La acción de esta entrada es: $ARGUMENTS
