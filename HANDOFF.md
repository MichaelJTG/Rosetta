# HANDOFF.md — Traspaso completo de ROSETTA a Claude Code

> Este archivo documenta **todo el contexto** que Claude Code necesita para operar ROSETTA de forma
> autónoma. Recoge la historia del proyecto, las decisiones estratégicas ya tomadas, los artefactos
> producidos, los límites firmes del scope, y la directiva de autonomía.
>
> **Claude Code leerá este archivo al principio de la primera sesión autónoma y luego una vez por
> semana como refresh.** Después se gobierna por `CLAUDE.md` + `MISSION.md` + la bitácora viva
> en `vault/00_Bitacora.md`.

---

## 1. Estado del traspaso

A partir de este punto, **el usuario (Mj) deja de usar la interfaz Cowork para este proyecto**. Toda
la gestión, planificación y ejecución se hace **exclusivamente desde Claude Code** en el repositorio
`C:\Users\WorkStation\Desktop\Rosetta`. No volverá a haber una "sesión Cowork" que planifique y un
"Claude Code" que ejecute; Claude Code se encarga de ambas fases.

Si el usuario pregunta algo, lo hace dentro de Claude Code. Si el proyecto necesita documentación,
artefactos, mensajes para el mentor, o planificación de sprints, Claude Code los produce desde
dentro del repo, con soporte en el vault.

## 2. Qué es ROSETTA (una frase)

Una plataforma de **Normativa** que toma hallazgos técnicos arbitrarios y los traduce en tiempo real
a evidencia de cumplimiento multi-marco (ISO 27001, ENS, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS v4.0),
usando IA como el "Traductor Simbiótico" entre lo técnico y lo legal.

Para definición completa y reglas de operación ver `CLAUDE.md`. Para roadmap detallado ver
`docs/ROADMAP.md` y su espejo enlazable `vault/MOC_Roadmap.md`. Para la misión autónoma leer
`MISSION.md`.

## 3. Historia condensada del proyecto

### 3.1 Origen (pre-Cowork)

El proyecto nació de una conversación con Gemini en la que el usuario exploró una idea inicial
llamada "Ecosistema Total" — una plataforma que fusionaba Red Team + Blue Team + Normativa. La
conversación desembocó en el concepto de "Traductor Simbiótico" como núcleo diferencial.

### 3.2 Iteración en Cowork (sesiones previas)

El usuario trajo la idea a Cowork para materializarla. Durante las sesiones se tomaron las
siguientes decisiones de fondo, todas ellas vinculantes a menos que un ADR posterior las anule:

**Decisión 1 · Enfoque exclusivo en Normativa.** De las tres opciones de itinerario de clase (Red
Team, Blue Team, Normativa), se eligió Normativa. Todo lo Red/Blue en ROSETTA existe **al servicio**
del Traductor, no como disciplina propia. Consecuencia: si un feature no resuelve uno de los
"9 problemas base" (ver `docs/ROADMAP.md`), no se hace.

**Decisión 2 · Orquestar, no forkear.** Las herramientas open source (Nuclei, Amass, Wazuh,
theHarvester, Shodan, HIBP…) se consumen vía CLI/API. No se forkea, no se embebe, no se modifica
código de terceros. Formalizado en [[02_ADR/001-orquestacion-sobre-fork]] · ✅ aprobada.

**Decisión 3 · BAS en vez de desarrollo ofensivo propio.** El usuario preguntó si ROSETTA podía
integrar evasión de EDRs al estilo Cobalt Strike. Se rechazó por ser desarrollo de malware. La
alternativa aceptada es Breach and Attack Simulation con MITRE ATT&CK: orquestar Caldera o Atomic
Red Team como adaptadores para ejercicios BAS legítimos.

**Decisión 4 · No competir con Vanta/Drata, complementarlos.** Vanta y Drata automatizan la
recogida de evidencia **predecible y estructurada** sobre integraciones conocidas (AWS, GitHub,
Okta…). ROSETTA **razona sobre hallazgos arbitrarios y nuevos** que ellos no cubren. El Traductor
Simbiótico es el diferencial.

**Decisión 5 · CI/CD como feature baseline, no añadido.** Con la normalización del vibe coding
y la IA generando código, el gate de cumplimiento en CI/CD ya no es "nice to have" — es
**obligatorio de base**. Se integra desde el MVP-0 (CI básico con ruff+mypy+pytest+gitleaks) y
llega a gate completo en MVP-7.

**Decisión 6 · Procedure Drift como killer feature (insight de Carlos).** Carlos Gómez Pintado
(CEO Cyberxia, mentor informal del proyecto) señaló que el gran dolor real de las empresas es
**la revisión y mantenimiento de procedimientos** — los procedimientos escritos divergen de la
realidad operativa y nadie los actualiza. ROSETTA extiende el Traductor para detectar **procedure
drift**: comparar procedimiento escrito ↔ comportamiento observado por sensores ↔ proponer
actualización. Es el [[MOC_Roadmap#MVP-5|MVP-5]] y el diferenciador estratégico frente a Vanta/
Drata. Ver nota dedicada: [[06_Procedimientos/insight-carlos-procedure-drift]].

**Decisión 7 · Vault Obsidian como segundo cerebro.** Todo el "porqué" del proyecto se registra
en `vault/` como notas con frontmatter YAML y enlaces bidireccionales. El usuario abre Obsidian
sobre el vault y espera ver el proyecto "vivo". Protocolo de bitácora obligatorio en
`CLAUDE.md` sección 14. Ruptura del protocolo = pérdida de confianza del proyecto.

**Decisión 8 · Abstracción de proveedor LLM.** Ante la situación de que el usuario no tiene
clave de Anthropic, se propuso abstraer `LLMClient` detrás de interfaz común con implementaciones
Claude / OpenAI / Ollama. Motivos: desarrollo sin coste (Ollama local), soberanía de datos para
clientes europeos (ENS/NIS2/DORA), resiliencia, testeabilidad. Propuesta como
[[02_ADR/002-abstraccion-llm]] · 🟡 pendiente de aprobación del usuario.

### 3.3 Scaffold inicial (Sprint 0)

Se construyó el esqueleto completo del proyecto (61 archivos): `src/rosetta/` con core, adapters,
llm, api, cli; `tests/` con test_models; `docs/` con ARCHITECTURE y ROADMAP; `docs/adr/` con
ADR-001; vault Obsidian con 9 carpetas y plantillas; CI en `.github/workflows/ci.yml`; pre-commit;
`pyproject.toml` con uv; LICENSE proprietary provisional; README.

Sprint 0 documentado en `vault/07_Sprints/2026-04-18_sprint-0.md`.

### 3.4 Preparación para autonomía (última sesión Cowork)

En la sesión final se preparó el terreno para que Claude Code operara autónomamente:

- Añadida sección 14 a `CLAUDE.md` (Protocolo de bitácora · CRÍTICO).
- Creado `MISSION.md` (brújula autónoma con checkpoints y rutinas de sesión).
- Poblado vault con `00_Dashboard.md`, `00_Bitacora.md` y cinco MOCs (`MOC_Roadmap`, `MOC_ADRs`,
  `MOC_Normativas`, `MOC_Sprints`, `MOC_Hallazgos`).
- Creadas notas semilla para las 7 normativas del roadmap en `vault/03_Normativa/`.
- Movidos los artefactos de comunicación (mensaje LinkedIn para Carlos, presentación de clase) al
  vault en `vault/09_Comunicacion/`.
- Creado este `HANDOFF.md` y actualizado el primer-arranque (`START_HERE.md`).

## 4. Artefactos ya producidos (referencia rápida)

### Documentos raíz del repo
- `README.md` · descripción pública del proyecto
- `CLAUDE.md` · contexto y reglas para Claude Code (14 secciones)
- `MISSION.md` · misión autónoma con checkpoints (lee siempre al iniciar sesión)
- `HANDOFF.md` · este archivo (lee una vez, refresca semanalmente)
- `START_HERE.md` · arranque de una línea para el usuario
- `NEXT_STEPS.md` · guía operativa del primer sprint técnico
- `LICENSE` · proprietary provisional

### Documentación técnica
- `docs/ROADMAP.md` · 8 MVPs con criterios de aceptación
- `docs/ARCHITECTURE.md` · arquitectura de tres capas
- `docs/adr/001-orquestacion-sobre-fork.md` · ADR-001 ✅ aprobada

### Código (scaffold, pendiente de implementar)
- `src/rosetta/core/` · Traductor, RAG, grafo, modelos Pydantic
- `src/rosetta/llm/` · cliente Claude (pendiente de refactor a abstracción multi-proveedor según ADR-002)
- `src/rosetta/adapters/` · Red Team (Nuclei, Amass) y Blue Team (Wazuh) esqueletos
- `src/rosetta/api/` · FastAPI con `/health`
- `src/rosetta/cli/` · Typer CLI con `version`, `translate`, `load-corpus`
- `tests/` · test_models.py con los 4 tests de los modelos Pydantic

### Vault Obsidian
- `vault/00_Index.md` · índice hub
- `vault/00_Dashboard.md` · salpicadero del proyecto
- `vault/00_Bitacora.md` · bitácora viva (append only)
- `vault/MOC_*.md` · 5 mapas de contenidos
- `vault/03_Normativa/*.md` · 7 notas de marcos normativos
- `vault/02_ADR/*.md` · espejos de ADRs
- `vault/06_Procedimientos/insight-carlos-procedure-drift.md` · MVP-5
- `vault/07_Sprints/2026-04-18_sprint-0.md` · Sprint 0 documentado
- `vault/08_Reuniones/pendiente-carlos-gomez.md` · reunión pendiente
- `vault/09_Comunicacion/mensaje-linkedin-carlos.md` · mensaje entregado
- `vault/09_Comunicacion/presentacion-proyecto-clase.md` · presentación de clase
- `vault/99_Templates/*.md` · plantillas con frontmatter

### CI / tooling
- `.github/workflows/ci.yml` · ruff + mypy + pytest + gitleaks sobre Python 3.11 y 3.12
- `.pre-commit-config.yaml` · ruff + mypy + gitleaks + detect-private-key
- `pyproject.toml` · dependencias vía uv
- `.env.example` · variables de entorno
- `.gitignore` · Python + uv + Obsidian workspace + corpus PDFs + .env

## 5. Límites firmes (nunca cruzar)

1. **Desarrollo ofensivo propio**: no. Nada de malware, evasión EDR, ransomware, exploits nuevos,
   C2 propios. BAS vía orquestación de Caldera / Atomic Red Team es la alternativa aceptada.
2. **Modificación de herramientas open source**: no. Solo orquestación vía CLI/API.
3. **Commit de secretos**: no. `.env`, claves API, dumps, `.obsidian/workspace.json` nunca.
4. **Corpus con copyright sin licencia**: no. ISO cobra; para desarrollo se usan resúmenes o
   versiones comentadas. Para producción se adquiere licencia. ENS (BOE), NIS2/DORA/RGPD
   (EUR-Lex), NIST (NIST.gov) son públicos.
5. **Decisiones de arquitectura sin ADR**: no. Toda decisión de peso → ADR primero.
6. **Avanzar a un MVP siguiente sin cumplir el anterior**: no. Si hay que romper esta regla, se
   pregunta al usuario.

## 6. Directiva de autonomía

A partir del siguiente prompt del usuario, Claude Code opera según `MISSION.md`:

- **Arranque de sesión** → rutina de `MISSION.md` sección 4 (leer contexto, anotar en bitácora,
  confirmar estado al usuario).
- **Durante la sesión** → avanza por el roadmap, deja rastro cada 20-30 min en la bitácora,
  actualiza dashboard cuando cambie el estado, commits atómicos.
- **Checkpoints** → para y pregunta en los 8 casos listados en `MISSION.md` sección 3.
- **Cierre de sesión** → rutina de `MISSION.md` sección 4 (cerrar sprint, actualizar dashboard,
  entrada de cierre en bitácora, proponer commit).

El usuario ya no necesita pegar prompts detallados cada vez. Un "sigue" o "arranca el MVP-1" debería
ser suficiente: Claude Code lee la bitácora, el dashboard y el roadmap para saber dónde está y qué
toca.

## 7. Próximos pasos esperados (sin prompts adicionales)

Arrancando desde el estado actual, Claude Code debe (en orden):

1. Leer `CLAUDE.md`, `MISSION.md`, este `HANDOFF.md`, `docs/ROADMAP.md`, `vault/00_Dashboard.md` y
   últimas entradas de `vault/00_Bitacora.md`.
2. Resolver el conflicto de git pendiente en `README.md` (marcadores `<<<<<<< HEAD`, `=======`,
   `>>>>>>> 2eb38836…` visibles en el archivo): quedarse con la versión completa en español de
   ROSETTA.
3. Crear la estructura `.claude/` con commands y agents del proyecto (spec detallada en la entrada
   "Crear `.claude/` con commands y agents del proyecto" de cualquier versión previa del playbook;
   si no disponible, crear mínimo viable: `settings.json`, slash commands para `/adr`,
   `/sprint-open`, `/sprint-close`, `/bitacora`, `/add-marco`, `/add-adapter`; y tres sub-agents:
   `rosetta-architect`, `rosetta-compliance-researcher`, `rosetta-test-writer`).
4. Materializar ADR-002 (abstracción LLM): crear `docs/adr/002-abstraccion-llm.md`, refactorizar
   `src/rosetta/llm/` con `LLMClient` interface + Claude/Ollama/OpenAI, tests con mocks,
   `.env.example` actualizado, `NEXT_STEPS.md` ampliado con sección Ollama. 🛑 **CHECKPOINT**:
   pedir aprobación al usuario antes de marcar el ADR como ✅ aprobada.
5. Abrir Sprint 1 en `vault/07_Sprints/2026-04-18_sprint-1.md` con objetivo MVP-1 y declarar
   bloqueo "pendiente de corpus ISO 27001:2022". 🛑 **CHECKPOINT**: preguntar al usuario cómo
   obtener el corpus (opciones: resúmenes públicos + comentarios propios con disclaimer educativo,
   PDF oficial de pago, MD generado por LLM con fuente declarada).
6. Cerrar sesión según `MISSION.md`: actualizar dashboard, entrada de cierre en bitácora, proponer
   mensaje de commit Conventional Commits, **no hacer push**.

## 8. Cómo hablar con el usuario desde Claude Code

- Español, tono directo sin relleno.
- Frases cortas. No bullet points si se puede evitar.
- Cuando se alcance un 🛑 CHECKPOINT: mensaje al usuario con el motivo y pregunta concreta con
  opciones si es posible. Esperar respuesta antes de continuar.
- Cuando se termine una subtarea: confirmar en una línea ("✅ ADR-002 materializado. Siguiente:
  crear Sprint 1.") y seguir.
- Al final de la sesión: resumen corto + próximo paso + propuesta de commit.

## 9. Referencias externas útiles

- Claude Code docs: https://docs.claude.com/en/docs/claude-code
- Anthropic Console (API keys): https://console.anthropic.com/
- Ollama: https://ollama.com/
- Obsidian: https://obsidian.md/
- BOE (ENS RD 311/2022): https://www.boe.es/buscar/act.php?id=BOE-A-2022-7191
- EUR-Lex NIS2: https://eur-lex.europa.eu/eli/dir/2022/2555/oj
- EUR-Lex DORA: https://eur-lex.europa.eu/eli/reg/2022/2554/oj
- NIST CSF 2.0: https://www.nist.gov/cyberframework
- PCI Security Standards Council: https://www.pcisecuritystandards.org/

## 10. Autor y contacto

- Autor: Mj · michael.jt.pro@gmail.com
- Contexto académico: Trabajo de clase · itinerario Normativa

---

**Fin del handoff. A partir de aquí el proyecto vive en Claude Code + Obsidian. Buena suerte.**
