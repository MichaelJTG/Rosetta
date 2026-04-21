# CLAUDE.md — Contexto del proyecto ROSETTA para Claude Code

> Este archivo lo lee Claude Code automáticamente al abrir el repositorio. Define la visión, las convenciones y las reglas que Claude debe seguir al trabajar en ROSETTA. **Mantén este archivo actualizado conforme el proyecto evoluciona**.

---

## 1. Qué es ROSETTA en una frase

Una plataforma de Normativa que toma hallazgos técnicos arbitrarios y los traduce en tiempo real a evidencia de cumplimiento multi-marco (ISO 27001, ENS, NIS2, DORA), usando IA como el "Traductor Simbiótico" entre lo técnico y lo legal.

## 2. Qué NO es ROSETTA

Para evitar que derive: ROSETTA **no** es un escáner de vulnerabilidades, **no** es un SIEM, **no** es una herramienta ofensiva, **no** compite con Vanta/Drata (ellos automatizan checklists, ROSETTA traduce hallazgos dinámicos a controles).

## 3. Arquitectura en tres capas

**Capa de sensores (commodity):** adaptadores a herramientas open source consumidas vía API/CLI. No se forkean, no se modifican. Red Team (Nuclei, Amass, Subfinder, theHarvester, Shodan, HIBP) y Blue Team (Wazuh, OpenSearch, Velociraptor, syslog).

**Capa núcleo (IP propietaria de ROSETTA):** Traductor Simbiótico (LLM + RAG), grafo de correlación Neo4j, motor de inferencia multi-marco, generador de dossier de auditoría, orquestador FastAPI. Esta capa es donde se concentra el valor diferencial.

**Capa de salida:** API REST, CLI, dashboard de cumplimiento continuo, informes exportables en formato de auditoría, gate de CI/CD para bloquear PRs que incumplen controles.

## 4. Filosofía de desarrollo

**Orquestar, no reinventar.** Cada vez que te plantees escribir un escáner o un motor de detección desde cero, para y pregúntate si puedes orquestar una herramienta open source madura. La respuesta casi siempre es sí. El valor está en el Traductor, no en los sensores.

**Modular y type-safe.** Todo el código usa Pydantic para validación y mypy en modo strict. Cualquier función pública debe tener type hints completos. El Hallazgo Maestro (`rosetta.core.models.HallazgoMaestro`) es el lenguaje común entre capas.

**Documentar decisiones.** Cada decisión de arquitectura importante se registra como ADR en `docs/adr/` y además como nota en el vault de Obsidian. No tomar decisiones de peso sin ADR.

**Cumplimiento primero, código después.** Si una feature no resuelve uno de los 9 problemas base (ver `docs/ROADMAP.md`), no se hace.

## 5. Cómo trabajar con el vault de Obsidian

El directorio `vault/` es el "segundo cerebro" del proyecto. Claude Code **debe**:

1. **Al implementar una decisión de arquitectura significativa**: crear un ADR en `docs/adr/NNN-titulo.md` y un resumen enlazado en `vault/02_ADR/`.
2. **Al terminar un sprint o hito**: dejar una nota en `vault/07_Sprints/YYYY-MM-DD_sprint-N.md` con lo hecho, aprendizajes y bloqueos.
3. **Al aprender algo útil sobre una norma** (interpretación de un control, conflicto entre marcos, excepción aplicable): crear o actualizar la nota en `vault/03_Normativa/`.
4. **Al diseñar un nuevo adaptador**: dejar nota con pros/cons, licencia, limitaciones conocidas en `vault/05_Hallazgos/` (categoría "patrones").
5. **Usar YAML frontmatter siempre** para que Obsidian pueda indexar y enlazar bidireccionalmente. Ver plantillas en `vault/99_Templates/`.
6. **No tocar `vault/.obsidian/workspace.json`** — es config local del usuario y está en .gitignore.

Convención de tags: `#adr`, `#normativa/iso27001`, `#normativa/ens`, `#sprint/N`, `#hallazgo`, `#decision/pendiente`, `#decision/aprobada`, `#riesgo`, `#mentor/carlos`.

## 6. Cómo añadir un marco normativo nuevo

1. Añadir valor al enum `MarcoNormativo` en `src/rosetta/core/models.py`.
2. Crear carpeta `corpus/<marco>/` con el texto fuente (PDF o MD).
3. Ejecutar `rosetta load-corpus <marco> corpus/<marco>/`.
4. Añadir tests en `tests/test_<marco>.py` con al menos 3 hallazgos canónicos y su control esperado.
5. Documentar particularidades del marco en `vault/03_Normativa/<marco>.md`.

## 7. Cómo añadir un adaptador nuevo

1. Crear archivo en `src/rosetta/adapters/<red|blue>/<herramienta>.py`.
2. Heredar de `RedTeamAdapter` o `BlueTeamAdapter` (ver `adapters/base.py`).
3. Implementar `escanear()` o `consultar_alertas()` devolviendo `DatosRedTeam` normalizados.
4. **Verificar licencia de la herramienta**: MIT/Apache = libre; GPL/AGPL = solo orquestación vía CLI/API, nunca fork embebido. Documentar la licencia en docstring del módulo.
5. Añadir tests de integración con mocks del output de la herramienta.

## 8. Stack y dependencias clave

Python 3.11+, uv para gestión de paquetes, Pydantic v2, FastAPI, Typer (CLI), ChromaDB (RAG), Neo4j (grafo), Anthropic SDK (Claude), structlog (logs), pytest + pytest-asyncio + pytest-cov (tests), ruff (lint+format), mypy (types), pre-commit. Ver `pyproject.toml` para versiones exactas.

## 9. Variables de entorno

Ver `.env.example`. Mínimo necesario para MVP: `ANTHROPIC_API_KEY`. Opcionales según sensores activos: `SHODAN_API_KEY`, `HIBP_API_KEY`, `WAZUH_API_URL`/`WAZUH_API_USER`/`WAZUH_API_PASSWORD`.

## 10. Tests y CI

Todo nuevo módulo viene con tests. Cobertura mínima aceptable: 80% en la capa núcleo (core/), 60% en adaptadores. `pytest` ejecuta todo. `ruff check . && mypy src/` se ejecuta en pre-commit.

## 11. Reglas duras para Claude Code

1. **No modifiques el código de herramientas open source de terceros**. Solo las orquestamos vía CLI o API.
2. **No commitees `.env`, claves API, dumps de base de datos, ni el directorio `.obsidian/workspace.json`**.
3. **No tomes decisiones de arquitectura sin ADR**. Si el usuario pide algo que cambia una capa, propón primero un ADR.
4. **Idioma del código**: inglés para nombres y comentarios técnicos; español para docstrings extensos, documentación de producto y notas del vault (el usuario trabaja en español y el proyecto se enfocará a mercado hispanohablante y europeo).
5. **Al empezar una sesión nueva**: lee en este orden antes de tocar código — `CLAUDE.md` (este archivo) · `MISSION.md` · `HANDOFF.md` (primera sesión y refresh semanal) · `docs/ROADMAP.md` · `vault/00_Dashboard.md` · últimas entradas de `vault/00_Bitacora.md`.
6. **Al terminar una sesión**: deja una nota en `vault/07_Sprints/`, actualiza `vault/00_Dashboard.md`, añade entrada de cierre a `vault/00_Bitacora.md`.

## 12. Contacto y contexto del autor

Autor: Mj (michael.jt.pro@gmail.com). Proyecto desarrollado como Trabajo de clase bajo la mentoría (informal) de Carlos Gómez Pintado (CEO de Cyberxia). Iteración del proyecto guiada conjuntamente con un asistente Claude en Cowork — ese es el origen de las decisiones de diseño previas al primer commit.

## 13. Insight crítico del mentor (incorporar al roadmap)

Carlos Gómez Pintado señaló que el gran dolor real de las empresas es **la revisión y mantenimiento de procedimientos**. Los procedimientos escritos divergen de la realidad operativa y nadie los actualiza. ROSETTA debe extender el Traductor para detectar **procedure drift**: comparar procedimiento escrito ↔ comportamiento observado por los sensores y proponer actualización. Ver fase MVP-5 en `docs/ROADMAP.md`.

## 14. Protocolo de bitácora en Obsidian (CRÍTICO)

El usuario abre Obsidian sobre `vault/` y espera ver el proyecto "vivo" — notas apareciendo, enlaces creándose, grafo creciendo — conforme trabajas. **No basta con crear código y callar**. Tras cada acción significativa, dejas rastro en el vault. Reglas:

1. **Bitácora principal**: `vault/00_Bitacora.md`. Al iniciar sesión añades una entrada con fecha+hora y el objetivo de la sesión. Al terminar cada subtarea, añades una entrada con lo hecho y enlaces `[[]]` a las notas o archivos creados. **Append always**, nunca sobrescribes el histórico.

2. **Dashboard**: `vault/00_Dashboard.md`. Cuando cambie el estado del proyecto (sprint activo, MVP completado, ADR aprobado, módulo terminado), actualizas los campos del frontmatter YAML y las secciones correspondientes.

3. **Crear notas enlazadas, no texto plano**. Si encuentras una decisión, un aprendizaje, una interpretación normativa, una limitación de una herramienta — cada cosa es una nota en su carpeta con frontmatter YAML y tags. Usa siempre `[[enlaces bidireccionales]]` a entidades existentes.

4. **Frecuencia mínima**: cada 20-30 minutos de trabajo real, o al completar cualquier unidad con sentido (un módulo, un test pasando, un refactor, un ADR, un fragmento de corpus). Si vas más de 30 min sin anexar nada a `00_Bitacora.md`, estás violando este protocolo.

5. **Qué NO va al vault**: código fuente. Para código está el repo. En el vault va el **porqué**, el **aprendí**, el **decidí**, el **encontré**, el **descarté**. Si una nota tiene más de 20 líneas de código, se está usando mal.

6. **Formato de entrada en la bitácora** (copia exacta):
   ```markdown
   ## 2026-04-18 14:32 · <acción corta>
   - **Hecho**: <qué>
   - **Por qué**: <razón corta>
   - **Archivos**: `src/rosetta/llm/base.py` · [[02_ADR/002-llm-abstraction]]
   - **Enlaces**: [[MOC_ADRs]] · [[03_Normativa/ISO_27001_2022]]
   - **Estado**: ✅ hecho | 🟡 parcial | 🔴 bloqueado
   ```

7. **Si el usuario pregunta "¿en qué punto estamos?"**: no improvisas. Lees `vault/00_Dashboard.md` y las últimas entradas de `vault/00_Bitacora.md` y respondes desde esa fuente única de verdad.

8. **MISSION.md es tu brújula**. Antes de empezar cualquier tarea de fondo, relees `MISSION.md` y compruebas dónde estás en el roadmap. Nunca avanzas a un MVP siguiente sin haber cumplido el criterio de aceptación del anterior. Si tienes que romper esta regla, paras y preguntas al usuario.

Este protocolo existe porque el vault es el único canal por el que el usuario ve el trabajo sin tener que leer código. Romperlo = romper la confianza del proyecto.

---

## 15. Agentes disponibles (everything-claude-code)

El proyecto tiene configurados agentes especializados de [everything-claude-code](https://github.com/affaan-m/everything-claude-code) en `~/.claude/agents/`. Úsalos proactivamente:

### Agentes de calidad de código
| Agente | Cuándo usarlo |
|--------|--------------|
| `python-reviewer` | Después de cualquier cambio en `.py`. Verifica PEP8, type hints, seguridad, FastAPI patterns. |
| `code-reviewer` | Revisión general de calidad tras escribir código. |
| `tdd-guide` | Antes de implementar cualquier feature o bugfix. Enforce Red-Green-Refactor. |
| `type-design-analyzer` | Al diseñar modelos Pydantic, dataclasses, o Protocols. |
| `refactor-cleaner` | Para limpiar código muerto, duplicados o módulos que crecieron demasiado. |

### Agentes de seguridad y rendimiento
| Agente | Cuándo usarlo |
|--------|--------------|
| `security-reviewer` | Antes de cualquier commit que toque endpoints FastAPI, autenticación, o manejo de secretos. |
| `performance-optimizer` | Al optimizar el pipeline LLM/RAG o queries Neo4j/ChromaDB. |
| `silent-failure-hunter` | En código async de FastAPI donde los errores se pueden tragar silenciosamente. |
| `database-reviewer` | Al escribir queries Cypher (Neo4j) o accesos a ChromaDB. |

### Agentes de resolución de problemas
| Agente | Cuándo usarlo |
|--------|--------------|
| `build-error-resolver` | Cuando fallen imports, dependencias o el entorno uv. |

### Agentes ROSETTA propios (`.claude/agents/`)
| Agente | Cuándo usarlo |
|--------|--------------|
| `rosetta-architect` | Ante cualquier cambio de arquitectura que afecte capas. Propone ADR primero. |
| `rosetta-compliance-researcher` | Para buscar controles normativos exactos (ISO 27001, ENS, NIS2). |
| `rosetta-test-writer` | Para escribir tests de nuevos módulos siguiendo las convenciones del proyecto. |

## 16. Skills disponibles (everything-claude-code)

Skills instaladas y accesibles vía herramienta `Skill`:

| Skill | Propósito en ROSETTA |
|-------|---------------------|
| `python-patterns` | Patrones Python idiomáticos: Protocol, dataclasses, generadores, concurrencia |
| `python-testing` | Pytest fixtures, mocks, parametrize para tests de adaptadores |
| `tdd-workflow` | Flujo completo Red-Green-Refactor con coverage 80%+ |
| `security-review` | Proceso de revisión de seguridad para endpoints de la API REST |
| `security-scan` | Escaneo estático con bandit + revisión de dependencias |
| `verification-loop` | Loop de verificación antes de declarar una tarea completa |
| `claude-api` | Optimización del uso de Anthropic SDK con prompt caching (crítico para el Traductor) |
| `backend-patterns` | Patrones de API REST, Repository pattern, manejo de errores |
| `agentic-engineering` | Diseño de pipelines LLM/RAG para el Traductor Simbiótico |
| `api-design` | Diseño de endpoints FastAPI con Pydantic response models |

## 17. Hooks automáticos configurados

Los siguientes hooks están activos en `.claude/settings.json`:

- **PreToolUse (Write/Edit)**: Bloquea escritura en `.env`, `workspace.json` de Obsidian, y PDFs del corpus.
- **PostToolUse (Write/Edit)**: Ejecuta `ruff check` automáticamente al editar archivos `.py`. Los warnings aparecen en el terminal.
- **Stop**: Al terminar sesión, muestra el número de tests recopilados como recordatorio de cobertura.
