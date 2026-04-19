---
description: Añade un nuevo adaptador de sensor (Red o Blue Team) siguiendo los 5 pasos de CLAUDE.md sección 7
argument-hint: "<red|blue> <nombre-herramienta>"
model: claude-sonnet-4-6
---

Vas a añadir un nuevo adaptador de sensor en ROSETTA siguiendo exactamente los 5 pasos de CLAUDE.md §7.

Los argumentos recibidos son: **$ARGUMENTS**

Extrae de ellos: el tipo (`red` o `blue`) y el nombre de la herramienta (ej. `nuclei`, `wazuh`, `amass`).

## Paso 1 — Crear el archivo del adaptador

Lee `src/rosetta/adapters/base.py` para entender las clases base `RedTeamAdapter` y `BlueTeamAdapter`.

Crea `src/rosetta/adapters/<tipo>/<herramienta>.py` con:
- Docstring de módulo que incluya: propósito, **licencia de la herramienta** (ver paso 4), URL del proyecto.
- Clase que herede de la base correcta.
- Implementación esquelética del método principal (`escanear()` para Red Team, `consultar_alertas()` para Blue Team) que lance `NotImplementedError` con un mensaje descriptivo.
- Type hints completos en todas las funciones públicas (Pydantic v2, mypy strict).

## Paso 2 — Heredar de la clase base correcta

Asegúrate de que:
- Red Team → hereda de `RedTeamAdapter`, implementa `escanear() -> DatosRedTeam`.
- Blue Team → hereda de `BlueTeamAdapter`, implementa `consultar_alertas() -> list[HallazgoMaestro]`.
- Importa los modelos correctos desde `rosetta.core.models`.

## Paso 3 — Esqueleto del método principal

El método debe:
- Aceptar los parámetros mínimos necesarios (target, config, etc.).
- Incluir comentarios `# TODO:` marcando los puntos de implementación real.
- Documentar el formato de output esperado de la herramienta orquestada.

## Paso 4 — Verificar y documentar la licencia

**Pregunta al usuario**: "¿Cuál es la licencia de <herramienta>? (MIT, Apache 2.0, GPL, AGPL, etc.)"

Según la respuesta:
- **MIT / Apache 2.0 / BSD**: libre uso, documenta en docstring: `# Licencia: MIT/Apache — uso libre como dependencia`.
- **GPL / LGPL**: orquestación vía subprocess/API únicamente, nunca importar como librería. Documenta: `# Licencia: GPL — SOLO orquestación via CLI, no importar como módulo`.
- **AGPL**: igual que GPL, más estricto en contexto de red. Documenta con advertencia.
- **Propietaria / comercial**: documenta restricciones específicas.

Añade la licencia al docstring del módulo con esta estructura:
```python
"""
Adaptador para <Herramienta>.

Licencia de la herramienta: <LICENCIA>
Restricciones: <ninguna | solo CLI/API | ver nota>
URL: <proyecto>
"""
```

## Paso 5 — Crear tests con mocks

Lee `tests/test_models.py` y cualquier test de adaptador existente para seguir el mismo estilo.

Crea `tests/adapters/test_<herramienta>.py` con:
- Mock del output típico de la herramienta (JSON/texto que devolvería en real).
- Test que verifica que el adaptador parsea el mock y devuelve el tipo correcto.
- Test que verifica que los campos obligatorios de `HallazgoMaestro` se rellenan.
- `pytest.mark.skip` en tests que requieran la herramienta real instalada.
- Cobertura objetivo: 60% (adaptadores, según CLAUDE.md §10).

## Al terminar

Lista todos los archivos creados. Recuérdale al usuario que debe:
1. Implementar el cuerpo real del método principal.
2. Revisar la licencia documentada.
3. Añadir la herramienta a `pyproject.toml` si se importa como librería (solo si licencia lo permite).
