---
description: Crea un nuevo ADR (Architecture Decision Record) en docs/adr/ y su nota enlazada en vault/02_ADR/
argument-hint: "<título del ADR en español>"
model: claude-sonnet-4-6
---

Vas a crear un nuevo Architecture Decision Record para el proyecto ROSETTA.

## Pasos

1. **Determina el número siguiente** mirando los archivos existentes en `docs/adr/`. Busca el patrón `NNN-*.md` y usa el siguiente número disponible con cero-padding a 3 dígitos (ej. `001`, `002`...). Si no existe ninguno, empieza por `001`.

2. **Genera el slug** del título: convierte el argumento a minúsculas, reemplaza espacios y caracteres especiales por guiones, elimina acentos (ej. "Decisión de Base de Datos" → `decision-de-base-de-datos`).

3. **Crea `docs/adr/NNN-<slug>.md`** con esta plantilla MADR:

```markdown
---
fecha: YYYY-MM-DD
estado: pendiente
---

# NNN. <Título>

## Contexto

<!-- Describe el problema o situación que motiva esta decisión. Qué restricciones existen, qué está en juego. -->

## Decisión

<!-- La decisión tomada, enunciada de forma afirmativa: "Usaremos X porque Y." -->

## Consecuencias

### Positivas
-

### Negativas
-

### Neutras
-

## Alternativas consideradas

### Alternativa A: <nombre>
<!-- Por qué se descartó -->

### Alternativa B: <nombre>
<!-- Por qué se descartó -->

## Referencias
-
```

4. **Crea `vault/02_ADR/NNN-<slug>.md`** con este frontmatter y cuerpo:

```markdown
---
titulo: "<Título>"
numero: NNN
fecha: YYYY-MM-DD
estado: pendiente
tags:
  - adr
  - decision/pendiente
adr_tecnico: "[[docs/adr/NNN-<slug>]]"
---

# ADR-NNN: <Título>

> Resumen enlazado al ADR técnico: `docs/adr/NNN-<slug>.md`

## Resumen en una línea

<!-- Una frase que capture la esencia de la decisión -->

## Impacto en el proyecto

<!-- Cómo afecta esta decisión a la arquitectura de ROSETTA (capas afectadas, MVP relevante) -->

## Enlace

[[docs/adr/NNN-<slug>|Ver ADR técnico completo]]
```

5. **Informa al usuario** qué archivos creaste y pídele que rellene los campos marcados con `<!-- -->` en ambos archivos.

Usa la fecha de hoy: 2026-04-18.

El título del ADR es: $ARGUMENTS
