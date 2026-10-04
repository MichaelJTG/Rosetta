# docs/P3_BITACORA.md — Bitácora de cambios de la Práctica 3

Cada entrada explica, en lenguaje llano:
- **qué** se cambió;
- **por qué** (el problema que había);
- **en qué commit**;
- **qué requisito** cubre;
- **cómo se comprobó**.

Los IDs de tarea (A-x, B-x…) son los del plan de cierre de la P3. Los
requisitos (RF/RNF) son los de `docs/P3_REQUISITOS.md`.

---

## 2026-10-04 · Punto de partida: estado real

Antes de tocar nada se midió el estado del repositorio:
- **Clon limpio sin claves:** 384 tests pasaban y 5 fallaban por necesitar
  `ANTHROPIC_API_KEY`.
- **CI:** rojo desde el 20 de mayo.
- **Dependencias:** `pip-audit` sobre `uv.lock` daba 19 paquetes con 140
  vulnerabilidades. El "0 CVE" anterior era falso.
- **Formato:** `ruff format` fallaba.
- **Secretos:** la contraseña de la cuenta del profesor estaba publicada en el
  repositorio.

Seis requisitos marcados como ✅ no lo estaban (ver más abajo).

---

## Incidente de credenciales (INC-01) · RNF-06, RF-15

| | |
|---|---|
| **Qué** | Rotación en producción de las contraseñas de la cuenta principal y de la del profesor, y del secreto JWT (64 caracteres, generados con `secrets`). Saneado de dos commits locales antes de publicarlos. |
| **Por qué** | La contraseña del profesor estaba escrita en `tests/test_auth.py`, publicado en GitHub. Además, `docs/informe/_shots.py` contenía la contraseña de la cuenta principal. |
| **Commits** | `ea3f1f1`, `04b9c7e` (commits saneados), `1ff29ad` (documentación del incidente) |
| **Comprobación** | `/health` 200. Las credenciales nuevas dan 200 en `/auth/login` y las antiguas 401, en ambas cuentas. La contraseña de `_shots.py` también da 401. 0 apariciones del literal en el árbol y en los mensajes de commit. |
| **Decisión** | El historial público no se reescribe; la credencial antigua ya no sirve. Detalle en `docs/P3_SEGURIDAD.md` §1. |
| **Efecto colateral** | Al recrear el contenedor se perdió el estado del catálogo de controles de producción: su base vivía en la capa del contenedor. Era un fallo de configuración previo y se corrige en `2d9397b`. |

---

## A-0 · CI de vuelta a verde · RNF-04, RNF-10, RNF-12

| | |
|---|---|
| **Qué** | `setup-uv` v3 → v7.6.0. Actions fijadas por SHA. Matriz real Python 3.11/3.12. `uv sync --locked`. Permisos del token de solo lectura. pip-audit sobre el lockfile del proyecto. ruff/mypy de pre-commit alineados con `uv.lock`. |
| **Por qué** | Todos los runs fallaban en «Install uv» y nunca llegaban a los tests. El job de pip-audit auditaba la propia herramienta, no el proyecto. Pre-commit (ruff 0.7.4) y el lockfile (ruff 0.15.11) formateaban distinto. |
| **Commits** | `5ea2d2d`, `a4cb5c4`, `57d9497` |
| **Comprobación** | CI run 37203612212 en verde (lint, formato, mypy, tests en 3.11 y 3.12, gitleaks y pip-audit). |

## A-6 · Tests aislados del entorno · RNF-02

| | |
|---|---|
| **Qué** | Fixture automático en `conftest.py`: proveedor LLM de prueba con clave falsa, se eliminan las variables de la máquina y ChromaDB, SQLite e informes van a una carpeta temporal. `PYTHON_DOTENV_DISABLED` impide que se cargue el `.env` local. |
| **Por qué** | En una máquina ajena fallaban 5 tests, y la suite escribía en `reports/` y `.chroma` del repositorio. |
| **Commit** | `1a1726e` |
| **Comprobación** | Clon limpio sin `ANTHROPIC_API_KEY`, sin `LLM_PROVIDER` y sin Ollama: 389 passed, 0 errores. |

## Dependencias (pasan a imprescindibles) · RNF-12

| | |
|---|---|
| **Qué** | 9 tandas de actualización con la suite completa, ruff y `mypy --strict` tras cada una: python-multipart, fastapi/starlette, pypdf, pyjwt, pillow, pila HTTP/TLS, pila de embeddings, weasyprint y herramientas de desarrollo. La pila de embeddings se verificó además con el modelo real, por ser un cambio de versión mayor. |
| **Por qué** | 140 vulnerabilidades conocidas en las dependencias bloqueadas. |
| **Commits** | `d5b8cf7` … `8dc0a57`, `b822427` |
| **Resultado** | Queda solo chromadb, con 4 avisos sin parche publicado que afectan a su modo servidor HTTP, que ROSETTA no usa. Se documenta como **riesgo aceptado R-01**, ignorado de forma explícita en CI (`docs/P3_SEGURIDAD.md` §2). |

---

## Bloque A · Producto funcional e instalable

### A-1 · Instalación limpia · RNF-05

| | |
|---|---|
| **Qué** | Dockerfile reescrito: dependencias desde `uv.lock`, torch en versión CPU, Nuclei 3.11.1 verificado por SHA-256, modelo de embeddings precargado, usuario sin root, y solo se copian `src/`, `corpus/` y `scripts/`. Las bases de datos y los informes pasan a volúmenes persistentes. Nuevo comando `rosetta load-corpus all corpus`. |
| **Por qué** | Fallos de la instalación limpia con el Dockerfile antiguo: sin `.env`, compose abortaba; la build tardaba 10 min 53 s y la imagen ocupaba 10,3 GB (pila CUDA innecesaria); el proceso corría como root; Nuclei no estaba; se copiaba todo el repositorio; no se usaba el lockfile; y la base de controles se perdía en cada despliegue. |
| **Commits** | `6c5485b`, `2d9397b`, `927e45a` |
| **Comprobación** | Clon limpio siguiendo el README: build en 165 s, imagen de 3,85 GB, contenedores *healthy*, 197 fragmentos indexados de los 7 marcos, proceso con uid 10001 y Ollama alcanzable desde el contenedor. |

### A-2 · Flujo end-to-end real · RF-01, RF-04

| | |
|---|---|
| **Qué** | Prueba sin maquetas, con Ollama `qwen2.5:14b`: login → `/translate` → hallazgo visible en el dashboard → dosier MD y PDF descargados desde el botón. |
| **Hallazgo** | Tras indexar con `load-corpus` (otro proceso), la API seguía viendo el índice vacío porque ChromaDB no admite dos procesos. El Traductor trabajó sin contexto y el LLM citó un control inexistente (`A.8.2.2`, de la versión 2013). Tras `docker compose restart app` recupera 10 fragmentos y cita `A.8.12`. Se documenta el reinicio en el README (`bd8ae61`). |
| **Comprobación** | Navegador real (Chromium headless): login, 12 hallazgos en pantalla, dosier generado, PDF de 12 KB y MD descargados y 0 errores de JS en 6 pestañas. |

### A-3 · Descarga del dosier · RF-04

| | |
|---|---|
| **Qué** | `POST /reports/generate` devuelve URLs de la API en vez de rutas del servidor. Nuevo `GET /reports/download/{filename}`, autenticado, con lista blanca de nombres y comprobación de que la ruta no sale del directorio de informes. Botón «Generar dosier» en el dashboard. |
| **Por qué** | El endpoint devolvía rutas internas del servidor y desde el dashboard no se podía generar ni descargar el informe. |
| **Commit** | `51428da` |
| **Pruebas** | 9 tests: sin rutas internas, descarga real de MD y PDF, 404, 5 nombres no válidos dan 400, *path traversal* codificado y 401 sin credenciales. |

### A-4 · Datos de demostración · todos los paneles

| | |
|---|---|
| **Qué** | `scripts/seed_demo.py`: caso ficticio TechServ (tres consejerías, categoría ALTA, datos de salud). Envía solo **datos de entrada** a la API real: 7 hallazgos que cubren los 7 marcos, un diff para el Gate CI/CD, alertas Wazuh, un procedimiento para drift y un PDF. Dominios `.example` e IP de documentación. |
| **Commit** | `db2399a` |
| **Comprobación** | 8 tests: solo usa la API, autentica cada llamada, cubre los 7 marcos, datos ficticios, sigue si un paso falla. Ejecución real con Ollama: 12/12 pasos en 90 s. |

### A-5 · README probado · RNF-05

| | |
|---|---|
| **Qué** | README reescrito a partir de la instalación real: requisitos (incluida la memoria de `qwen2.5:14b`), pasos numerados, `.env` explicado, uso sin API key, credenciales de prueba ficticias y alcance multi-marco honesto. |
| **Por qué** | El anterior no explicaba Docker. Citaba un comando inexistente (`indexar-corpus`) y métricas que nunca se midieron (tasa de alucinación, confianza, latencia, cobertura del 80 %). También daba datos falsos: 15 endpoints, 3 adaptadores Red Team y WeasyPrint como generador del PDF. |
| **Commits** | `9ed2e0f`, `bd8ae61` |
| **Comprobación** | Los pasos del README se ejecutaron tal cual en un clon limpio (`readme_e2e.sh`). |

### A-7 · `.env.example`

| | |
|---|---|
| **Qué** | Todas las variables con valores ficticios. `OLLAMA_MODEL=qwen2.5:14b` y Ollama como proveedor por defecto. `ROSETTA_JWT_SECRET` vacío a propósito. `SHODAN_API_KEY` vacío. |
| **Por qué** | Faltaban variables y el modelo no era el decidido. Un secreto JWT de ejemplo habría sido un secreto conocido por cualquiera: gitleaks lo detectó en pre-commit. |
| **Commit** | `4833405` (más las variables nuevas de B-5 y B-8) |

### A-8 · Comportamiento ante errores · RNF-01, RF-15

| | |
|---|---|
| **Qué** | `GrafoCorrelacion.desde_uri` verifica la conexión con timeouts de 5 s. Nuevo `tests/test_degradacion.py`. |
| **Por qué** | El driver de Neo4j conecta de forma perezosa: con Neo4j caído al arrancar, la API no lo detectaba y cada petición esperaba unos 30 s. RNF-01 no tenía ningún test de API. |
| **Commit** | `b976da4` |
| **Pruebas** | 11 tests: arranque con Neo4j inaccesible; `/translate` y el panel de cumplimiento con Neo4j caído; 4 tipos de entrada inválida dan 422 sin trazas; sin credenciales, Basic erróneo, JWT falsificado y login erróneo dan 401. |

### A-9 · Modo Auditoría coherente · RF-06

| | |
|---|---|
| **Amass** | Verificado: el panel de Auditoría **solo ofrece Nuclei y Nmap**, igual que el orquestador. El `amass` que señalaba la auditoría está en el formulario del Traductor como **origen de un hallazgo**, junto a subfinder, shodan y hibp, y no promete ningún escaneo. No se quita. El error real estaba en el README («3 adaptadores»), ya corregido. |
| **Nuclei** | Instalado en la imagen para amd64 y arm64, la arquitectura de producción (`6c5485b`). |
| **Laboratorio** | `lab/` con un nginx propio, sin puertos publicados y con fallos intencionados. Solo se puede escanear si el servidor lo autoriza con `ROSETTA_AUDIT_ALLOWLIST` (`f89cb28`). |
| **Comprobación** | Sin la allowlist, el objetivo `http://lab-objetivo` se rechaza con 400 porque resuelve a una IP privada. Con la allowlist: *(resultado de la auditoría real más abajo)*. |

### RF-18 · CLI con tests

| | |
|---|---|
| **Qué** | 20 tests de los 6 comandos de la CLI. |
| **Por qué** | `cli/main.py` estaba al 0 % de cobertura aunque RF-18 figuraba como cumplido. |
| **Commit** | `ade8d09` |
| **Resultado** | Cobertura del 87 %. |

### Adelantados del Bloque B (porque cambiaban la instalación)

- **B-5 · Autenticación *fail-closed*** (`0454652`, RF-15). Problemas: sin
  `ROSETTA_USER` la API quedaba abierta (aunque hubiera cuentas extra) y había
  un secreto JWT escrito en el código público. Cambios: ahora la app no arranca
  sin un secreto de 32 caracteres o más ni con contraseñas de menos de 12; sin
  credenciales solo arranca con `ROSETTA_AUTH_DISABLED=1`. 11 tests, entre
  ellos uno que comprueba que un token firmado con el antiguo secreto público
  se rechaza.
- **B-8 · Alcance con DNS y allowlist** (`4f3d908`, RNF-08). Problema: un nombre
  que resolvía a una IP interna esquivaba el bloqueo. Cambio: ahora se resuelven
  todas sus IP, se usa `is_global` y hay allowlist de servidor. 11 tests sin
  salir a la red.

### Hallazgos sobre el producto, para decidir

- **RF-09 baja a 🟡.** El orquestador multi-agente y el **Validador** existen y
  tienen tests, pero **ningún endpoint los usa**: `/translate` llama
  directamente al Traductor. Conectar el Validador supone una segunda llamada al
  LLM por traducción (unos 140 s en lugar de unos 70 s con Ollama en frío). El
  eval del Bloque C medirá «Traductor solo» frente a «Traductor + Validador»
  para que la decisión se tome con datos.
- **`/ingest/pdf` extrae hallazgos pero no los traduce.** El docstring decía lo
  contrario y se ha corregido (`6da7871`).
