---
description: Cierra el sprint activo registrando lo hecho, aprendizajes y bloqueos, y sugiere mensaje de commit
model: claude-sonnet-4-6
---

Vas a cerrar el sprint activo del proyecto ROSETTA.

## Pasos

1. **Detecta el sprint abierto** buscando en `vault/07_Sprints/` el archivo más reciente que tenga `estado: abierto` en su frontmatter YAML.

2. **Recopila lo hecho en esta sesión**:
   - Ejecuta `git log --oneline -20` para ver los commits recientes.
   - Ejecuta `git diff HEAD~1 --stat` (o `git diff --stat` si no hay commits nuevos) para ver qué archivos cambiaron.
   - Revisa mentalmente los cambios discutidos en esta conversación.

3. **Rellena las secciones** del archivo de sprint detectado:
   - **Hecho**: lista los cambios concretos realizados (archivos creados/modificados, features implementadas, bugs resueltos).
   - **Aprendizajes**: insights técnicos, decisiones de diseño, cosas que funcionaron o no.
   - **Bloqueos / Próximos pasos**: qué queda pendiente, qué necesita resolverse antes del siguiente sprint.

4. **Actualiza el frontmatter** del archivo de sprint:
   - Cambia `estado: abierto` a `estado: cerrado`.
   - Añade `fecha_cierre: 2026-04-18`.

5. **Sugiere un mensaje de commit** siguiendo Conventional Commits:
   - Formato: `<tipo>(<scope>): <descripción imperativa en español>`
   - Tipos válidos: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`
   - Ejemplo: `chore(scaffold): añadir estructura .claude/ con commands y agents para ROSETTA`
   - Incluye en el cuerpo del commit un resumen de los cambios principales.

6. **Informa al usuario** qué archivo de sprint actualizaste y muéstrale el mensaje de commit sugerido.

**Nota**: No hagas el commit automáticamente. Solo sugiere el mensaje y espera confirmación del usuario.
