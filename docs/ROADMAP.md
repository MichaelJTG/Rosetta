# Roadmap de ROSETTA

> Fases MVP numeradas. Cada fase tiene criterio de aceptación claro. No se avanza a la siguiente sin haber completado la anterior.

---

## MVP-0 · Scaffold (✅ en curso)

**Objetivo:** Proyecto inicial instalable con `uv sync --extra dev`, estructura modular, modelos Pydantic, esqueletos de todos los módulos con `NotImplementedError`.

Criterio de aceptación: `uv run pytest` pasa con los tests de `test_models.py`; `uv run ruff check .` pasa; `uv run mypy src/` pasa.

## MVP-1 · Traductor Simbiótico funcional sobre ISO 27001:2022

**Objetivo:** Dado un JSON con un `DatosRedTeam`, ROSETTA devuelve un `DatosCompliance` válido con controles ISO 27001:2022 citando el texto del Anexo A. Sin API, solo vía CLI.

Tareas:
1. Implementar `CorpusLoader` para parsear ISO 27001:2022 Anexo A a fragmentos por control.
2. Implementar `NormativaRAG` con ChromaDB persistente y filtro por `framework_id`.
3. Implementar `TraductorSimbiotico.traducir()` con pipeline completo RAG + Claude tool-use.
4. CLI `rosetta translate <hallazgo.json> --marco iso_27001_2022` funcional.
5. Tests E2E con 5 hallazgos canónicos (AWS key leak, puerto expuesto, sin MFA, sin logs, RDP abierto a internet).

Criterio de aceptación: los 5 tests E2E devuelven el control correcto top-1 (o top-3) sin alucinar artículos inexistentes.

## MVP-2 · Grafo de correlación y trazabilidad

**Objetivo:** Cada traducción queda persistida en Neo4j con sus relaciones.

Tareas:
1. Docker-compose con Neo4j Community.
2. `GrafoCorrelacion.registrar_hallazgo()` con Cypher MERGE.
3. Consultas básicas: hallazgos por marco, hallazgos por activo, controles más incumplidos.
4. Exportación de dossier de auditoría en Markdown a partir de consulta al grafo.

Criterio de aceptación: tras traducir 10 hallazgos, consulta Cypher puede listar controles ISO afectados en orden de criticidad.

## MVP-3 · Segundo marco: ENS

**Objetivo:** ROSETTA razona simultáneamente sobre ISO 27001 + ENS y detecta intersecciones.

Tareas:
1. Ingesta del corpus ENS (RD 311/2022).
2. Prompt engineering multi-marco: el LLM debe identificar cuándo un hallazgo incumple ambos marcos y citar los dos.
3. Tests con hallazgos que afectan solo a ISO, solo a ENS, y a ambos.

Criterio de aceptación: 90% de aciertos en 10 casos canónicos multi-marco.

## MVP-4 · Primer adaptador Red Team real: Nuclei

**Objetivo:** Ejecutar Nuclei contra un objetivo autorizado, capturar output JSON, generar `HallazgoMaestro`, traducir, persistir.

Tareas:
1. `NucleiAdapter.escanear()` con subprocess async.
2. Smoke test contra un servidor de laboratorio propio (vagrant/docker).
3. Pipeline completo sensor → traductor → grafo → dossier.

Criterio de aceptación: `rosetta scan --sensor nuclei --target <lab.local>` produce dossier de auditoría coherente.

## MVP-5 · Procedure Drift Detection (insight de Carlos Gómez Pintado)

**Objetivo:** ROSETTA detecta cuando un procedimiento interno escrito no coincide con el comportamiento observado por los sensores, y propone actualización del documento.

Tareas:
1. Ingestión de procedimientos internos (docx/md/pdf) a ChromaDB con metadato `tipo: procedimiento`.
2. Nueva función `detectar_drift(procedimiento_id, observaciones)` en core.
3. LLM compara redacción del procedimiento con realidad observada y propone diff.
4. Integración con el dossier: los procedimientos obsoletos aparecen como no-conformidad operativa.

Criterio de aceptación: dado un procedimiento de IAM y logs de Wazuh que muestran cuentas inactivas no desactivadas, el sistema señala drift y propone redacción actualizada.

## MVP-6 · API REST y dashboard básico

**Objetivo:** Exponer el núcleo como servicio consumible.

Tareas:
1. Endpoint `POST /translate` funcional.
2. Endpoint `GET /findings` con paginación.
3. Endpoint `GET /compliance/state/{marco}` con estado global.
4. Dashboard mínimo (Next.js o Streamlit) con los 3 endpoints.

Criterio de aceptación: un auditor puede consultar estado de cumplimiento desde navegador sin tocar CLI.

## MVP-7 · Gate de CI/CD

**Objetivo:** GitHub Action que ejecute un subconjunto del Traductor sobre el diff de un PR y bloquee si introduce incumplimientos.

Tareas:
1. Action reusable que llame a la API de ROSETTA.
2. Formato de comentario en PR con control incumplido + línea de código + sugerencia.
3. Configurable por marco activo en el repo (`.rosetta.yml`).

Criterio de aceptación: un PR que introduce un secret hardcodeado queda bloqueado con el motivo ISO 27001 A.8.24.

## MVP-8+ · Ampliación de marcos, hardening, comercialización

NIS2, DORA, NIST CSF 2, PCI-DSS v4, HIPAA, TISAX. Firma criptográfica de evidencias (RFC 3161). Multi-tenant. Packaging para despliegue cliente.

---

## Los 9 problemas base que ROSETTA debe resolver

Checklist que usamos para validar que cada feature aporta valor real:

### Red Team
- [ ] R1 · Detección por comportamiento (evasión de EDR) — parcial, vía BAS y MITRE ATT&CK, no por malware propio.
- [ ] R2 · Fatiga del reconocimiento (OSINT manual) — resuelto vía adaptadores.
- [ ] R3 · Mantenimiento de infraestructura ofensiva — N/A (ROSETTA es defensivo).

### Blue Team
- [ ] B1 · Shadow IT — resuelto vía cruce OSINT/inventario en grafo.
- [ ] B2 · Alert fatigue — resuelto vía filtrado por relevancia normativa.
- [ ] B3 · Falta de contexto en el incidente — resuelto vía enriquecimiento con grafo.

### Normativa
- [ ] N1 · Gap técnico-legal — **núcleo del proyecto**. Traductor Simbiótico.
- [ ] N2 · Cumplimiento estático vs dinámico — resuelto vía ejecución continua y persistencia en grafo.
- [ ] N3 · Cadena de suministro — parcial vía ingesta de hallazgos sobre terceros.
