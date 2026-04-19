# MISSION.md — Misión de largo alcance para Claude Code

> Este archivo es la **brújula autónoma** del proyecto. Claude Code lo lee al principio de cada sesión
> (junto con `CLAUDE.md` y `docs/ROADMAP.md`) y lo usa como referencia para avanzar sin supervisión
> constante del usuario. Complementa a `CLAUDE.md`, no lo sustituye.

---

## 0. Contrato de autonomía

Claude Code opera ROSETTA con **autonomía supervisada**: avanza solo por el roadmap, pero existen checkpoints explícitos donde **para y espera** al usuario. Fuera de esos checkpoints, puede implementar, refactorizar, probar, documentar y commitear libremente siempre que:

1. Cada acción significativa quede registrada en `vault/00_Bitacora.md` (ver `CLAUDE.md` sección 14).
2. No se viole ninguna regla de `CLAUDE.md` sección 11.
3. El criterio de aceptación del MVP actual esté claramente definido antes de empezar.
4. Los tests + lint + types pasen antes de dar una tarea por terminada.

Si cualquiera de esas cuatro condiciones falla, se detiene y escala al usuario.

## 1. Objetivo final del proyecto

Construir ROSETTA: un orquestador de cumplimiento continuo que toma hallazgos técnicos de cualquier fuente (Red Team, Blue Team, observaciones de sensores) y los **traduce en tiempo real** a evidencia normativa multi-marco con el Traductor Simbiótico (LLM + RAG + grafo).

El valor diferencial está en dos sitios:

- **Núcleo:** el Traductor Simbiótico (IP propietaria).
- **Procedure drift:** detección de desviación entre procedimientos escritos y realidad operativa (MVP-5, killer feature según el mentor Carlos Gómez Pintado — ver `vault/06_Procedimientos/insight-carlos-procedure-drift.md`).

## 2. Roadmap autónomo secuencial

Claude Code avanza por los MVPs en orden. **No salta.** Cada MVP tiene criterio de aceptación; sin cumplirlo no se pasa al siguiente.

- **MVP-0** · Scaffold — ✅ completado.
- **MVP-1** · Traductor Simbiótico sobre ISO 27001:2022 — **próximo, foco actual.**
- **MVP-2** · Grafo Neo4j y trazabilidad.
- **MVP-3** · Segundo marco: ENS.
- **MVP-4** · Primer adaptador Red Team real: Nuclei.
- **MVP-5** · Procedure drift (Carlos's killer feature).
- **MVP-6** · API REST y dashboard.
- **MVP-7** · Gate de CI/CD.
- **MVP-8+** · NIS2, DORA, NIST CSF 2, PCI-DSS, firma criptográfica, multi-tenant.

Detalle completo y criterios de aceptación en `docs/ROADMAP.md` y en el espejo enlazable del vault `vault/MOC_Roadmap.md`.

## 3. Checkpoints obligatorios (STOP AND ASK)

Claude Code **detiene la ejecución autónoma y pregunta al usuario** antes de:

1. **Crear o aprobar un ADR.** El ADR se puede redactar, pero no se marca como "aprobado" sin aprobación explícita del usuario.
2. **Adquirir o ingestar un corpus normativo con dudas de licencia.** Si el texto es del BOE u otra fuente pública, adelante; si hay duda (ISO 27001, PCI-DSS), para.
3. **Cambiar la elección de proveedor LLM** una vez fijada en `.env`.
4. **Introducir una dependencia nueva pesada** (> 50 MB, o con licencia GPL/AGPL/SSPL, o con implicaciones de telemetría).
5. **Tomar una decisión de producto** (nombre de endpoint público, formato de dossier externo, política de versionado de API).
6. **Tocar nada en `vault/.obsidian/workspace.json`, `.env`, claves API o corpus con copyright.**
7. **Alcanzar el criterio de aceptación de un MVP** — el siguiente MVP se arranca solo tras "luz verde" del usuario.
8. **Detectar un conflicto entre CLAUDE.md, MISSION.md y la petición actual del usuario.** Siempre gana la petición explícita del usuario, pero se documenta la divergencia en la bitácora.

Formato del stop: mensaje corto al usuario con "🛑 CHECKPOINT · <motivo>" + pregunta concreta con opciones si es posible.

## 4. Rutinas de sesión

### Al iniciar sesión (cada vez que el usuario abra Claude Code)

1. Leer en este orden: `CLAUDE.md`, `MISSION.md`, `docs/ROADMAP.md`, `vault/00_Dashboard.md`, últimas 10 entradas de `vault/00_Bitacora.md`.
2. Anexar entrada a `vault/00_Bitacora.md`:

   ```markdown
   ## YYYY-MM-DD HH:MM · Inicio de sesión
   - **Objetivo**: <qué MVP/tarea voy a trabajar>
   - **Estado previo**: leído [[00_Dashboard]]. MVP en curso: <...>.
   - **Checkpoints esperados**: <lista>
   ```

3. Si hay sprint abierto, confirmarlo. Si no, abrir sprint nuevo siguiendo [[99_Templates/Sprint_template]].
4. Resumir al usuario en una frase dónde se está y qué se va a hacer. Esperar go/no-go.

### Durante la sesión

- Cada 20-30 min o al completar cualquier unidad con sentido → entrada en `vault/00_Bitacora.md`.
- Tras cada refactor / ADR / módulo nuevo / corpus cargado → actualizar `vault/00_Dashboard.md`.
- Tests / lint / mypy verdes antes de afirmar "listo".
- Commits atómicos siguiendo Conventional Commits.

### Al cerrar sesión

1. Cerrar el sprint o actualizar nota del sprint en `vault/07_Sprints/`.
2. Entrada final en `vault/00_Bitacora.md` con `### Cierre de sesión` + resumen.
3. Actualizar `vault/00_Dashboard.md` con el estado nuevo.
4. Último commit con mensaje claro.
5. Dejar al usuario un mensaje de una línea: "Sesión cerrada. Próximo paso: <x>".

## 5. Reglas de oro

1. **La bitácora no es opcional.** Sin bitácora el trabajo no existe.
2. **Una cosa bien antes que tres a medias.** No dejes módulos a medio implementar para "arrancar el siguiente".
3. **Tests siempre.** Cobertura mínima: 80% core, 60% adapters.
4. **ADR primero, código después** para cualquier decisión de arquitectura.
5. **Si dudas, pregunta.** Mejor un checkpoint de más que un ADR silencioso.
6. **El vault refleja el proyecto.** Si abres Obsidian y no entiendes el estado → el vault está mal, arréglalo antes de seguir.

## 6. Qué NO hacer nunca

- Implementar un scanner o motor de detección desde cero (siempre orquestar open source).
- Forkear herramientas de terceros (solo orquestación vía CLI/API).
- Commitear secretos, claves, dumps, o `.obsidian/workspace.json`.
- Avanzar a un MVP siguiente sin cumplir el criterio de aceptación del anterior.
- Ocultar al usuario un bloqueo o una duda importante "para no molestar".

## 7. Referencia rápida de rutas

- Contexto general · `CLAUDE.md`
- Misión (este archivo) · `MISSION.md`
- Roadmap detallado · `docs/ROADMAP.md`
- Dashboard · `vault/00_Dashboard.md`
- Bitácora · `vault/00_Bitacora.md`
- ADRs · `docs/adr/` + espejos en `vault/02_ADR/`
- MOCs · `vault/MOC_*.md`
- Plantillas · `vault/99_Templates/`

## 8. Si algo se rompe

- Pregunta al usuario antes de hacer rollback destructivo.
- Si el vault queda inconsistente (enlaces rotos, frontmatter mal), dedica 10 minutos a arreglarlo **antes** de seguir con código.
- Si falla el test de algo que implementaste hace 3 sesiones, para y reproduce — probablemente haya una regresión que merece ADR de por qué el diseño no aguantó.

---

Esta misión es estable. Cambios mayores requieren ADR.
