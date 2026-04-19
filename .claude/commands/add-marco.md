---
description: Añade soporte para un nuevo marco normativo siguiendo los 5 pasos de CLAUDE.md sección 6
argument-hint: "<nombre del marco, ej: nis2, dora, nist_csf>"
model: claude-sonnet-4-6
---

Vas a añadir soporte para un nuevo marco normativo en ROSETTA siguiendo exactamente los 5 pasos de CLAUDE.md §6.

El marco a añadir es: **$ARGUMENTS**

## Paso 1 — Actualizar el enum `MarcoNormativo`

Lee `src/rosetta/core/models.py`. Localiza el enum `MarcoNormativo` y añade el nuevo valor. Usa SCREAMING_SNAKE_CASE para el nombre del enum (ej. `NIS2 = "nis2"`). Mantén los type hints y el estilo existente.

## Paso 2 — Crear la carpeta del corpus

Crea la carpeta `corpus/$ARGUMENTS/` con un archivo `README.md` mínimo que indique:
- Nombre completo del marco.
- Dónde conseguir el texto oficial.
- Nota: "Los PDFs/textos fuente van en este directorio y están en .gitignore."

## Paso 3 — Sugerir el comando load-corpus

Muestra al usuario el comando que deberá ejecutar cuando tenga el corpus:
```bash
uv run rosetta load-corpus $ARGUMENTS corpus/$ARGUMENTS/
```
Explica brevemente qué hace este comando.

## Paso 4 — Crear esqueleto de tests

Crea `tests/test_$ARGUMENTS.md` — **espera**: primero lee `tests/test_models.py` y `tests/conftest.py` si existe, para seguir el mismo estilo. Luego crea `tests/test_$ARGUMENTS.py` con:
- 3 hallazgos canónicos placeholder con `pytest.mark.skip(reason="requiere corpus cargado")`.
- Un comentario explicando qué controles debería mapear cada hallazgo.
- Estructura de fixtures consistente con los tests existentes.

## Paso 5 — Crear nota en el vault

Crea `vault/03_Normativa/$ARGUMENTS.md` con:

```markdown
---
marco: "$ARGUMENTS"
nombre_completo: ""
fecha_publicacion: ""
ambito: ""
estado_implementacion: pendiente
tags:
  - normativa/$ARGUMENTS
  - decision/pendiente
---

# Marco: $ARGUMENTS

## Descripción

<!-- Qué regula, a quién aplica, cuál es su alcance geográfico/sectorial -->

## Estructura del marco

<!-- Cómo se organiza: anexos, artículos, dominios de control -->

## Controles clave (top 10)

<!-- Los controles más relevantes para el perfil de ROSETTA -->

## Intersección con otros marcos

<!-- Equivalencias con ISO 27001, ENS, NIS2, etc. -->

## Notas de implementación

<!-- Particularidades a tener en cuenta al implementar el CorpusLoader y el prompt del Traductor -->

## Fuentes

- Texto oficial:
- Guía de implementación:
```

## Al terminar

Informa al usuario de todos los archivos creados o modificados. Recuérdale que debe:
1. Conseguir el corpus oficial y colocarlo en `corpus/$ARGUMENTS/`.
2. Rellenar los campos vacíos en la nota del vault.
3. Completar los 3 hallazgos canónicos en el archivo de tests.
