---
description: Ejecuta el Traductor Simbiótico sobre un fichero JSON y valida que el DatosCompliance es correcto
argument-hint: "<ruta/al/fichero.json>"
model: claude-sonnet-4-6
---

Vas a ejecutar el Traductor Simbiótico de ROSETTA sobre un hallazgo de ejemplo y validar el resultado.

El fichero a traducir es: **$ARGUMENTS**

## Pasos

1. **Verifica que el fichero existe** antes de ejecutar nada. Si no existe, informa al usuario con el path exacto que proporcionó.

2. **Ejecuta el comando**:
```bash
uv run rosetta translate $ARGUMENTS --marco iso_27001_2022
```

3. **Valida el resultado** como `DatosCompliance` (Pydantic). Comprueba que:
   - El JSON de salida es válido y parseable.
   - Contiene el campo `controles` con al menos 1 entrada.
   - Cada control tiene: `id_control`, `titulo`, `cita_textual` (no vacío), `nivel_confianza`.
   - No hay controles con identificadores inventados (deben coincidir con el patrón `A.\d+\.\d+` para ISO 27001).
   - El campo `hallazgo_id` referencia el hallazgo de entrada.

4. **Muestra el resultado formateado**:
```
╔══════════════════════════════════════════════╗
║     ROSETTA — Resultado de Traducción        ║
╠══════════════════════════════════════════════╣
║ Fichero:   <nombre>                          ║
║ Marco:     ISO 27001:2022                    ║
║ Controles: N encontrados                     ║
╚══════════════════════════════════════════════╝

Control top-1:
  ID:         A.X.YY
  Título:     <título del control>
  Confianza:  XX%
  Cita:       "<cita textual del Anexo A>"

[resto de controles si hay más de 1]
```

5. **Veredicto de validación**:
   - ✓ PASS: si hay al menos 1 control con cita textual no vacía y ID con formato correcto.
   - ✗ FAIL: si el JSON es inválido, no hay controles, o los IDs no coinciden con el patrón esperado. Muestra el error concreto.

6. **Si el comando falla** (error de importación, API key faltante, etc.):
   - Muestra el error completo.
   - Sugiere el paso de diagnóstico más probable (ej. `uv sync`, verificar `ANTHROPIC_API_KEY` en `.env`, cargar corpus primero).
