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
| **Commits** | `5eb5abd`, `4942403` (commits saneados), `1ef7438` (documentación del incidente) |
| **Comprobación** | `/health` 200. Las credenciales nuevas dan 200 en `/auth/login` y las antiguas 401, en ambas cuentas. La contraseña de `_shots.py` también da 401. 0 apariciones del literal en el árbol y en los mensajes de commit. |
| **Decisión** | El historial público no se reescribe; la credencial antigua ya no sirve. Detalle en `docs/P3_SEGURIDAD.md` §1. |
| **Efecto colateral** | Al recrear el contenedor se perdió el estado del catálogo de controles de producción: su base vivía en la capa del contenedor. Era un fallo de configuración previo y se corrige en `d485245`. |

---

## A-0 · CI de vuelta a verde · RNF-04, RNF-10, RNF-12

| | |
|---|---|
| **Qué** | `setup-uv` v3 → v7.6.0. Actions fijadas por SHA. Matriz real Python 3.11/3.12. `uv sync --locked`. Permisos del token de solo lectura. pip-audit sobre el lockfile del proyecto. ruff/mypy de pre-commit alineados con `uv.lock`. |
| **Por qué** | Todos los runs fallaban en «Install uv» y nunca llegaban a los tests. El job de pip-audit auditaba la propia herramienta, no el proyecto. Pre-commit (ruff 0.7.4) y el lockfile (ruff 0.15.11) formateaban distinto. |
| **Commits** | `2e7792d`, `7ec6b66`, `c03c1db` |
| **Comprobación** | CI run 37203612212 en verde (lint, formato, mypy, tests en 3.11 y 3.12, gitleaks y pip-audit). |

## A-6 · Tests aislados del entorno · RNF-02

| | |
|---|---|
| **Qué** | Fixture automático en `conftest.py`: proveedor LLM de prueba con clave falsa, se eliminan las variables de la máquina y ChromaDB, SQLite e informes van a una carpeta temporal. `PYTHON_DOTENV_DISABLED` impide que se cargue el `.env` local. |
| **Por qué** | En una máquina ajena fallaban 5 tests, y la suite escribía en `reports/` y `.chroma` del repositorio. |
| **Commit** | `3e8a0ed` |
| **Comprobación** | Clon limpio sin `ANTHROPIC_API_KEY`, sin `LLM_PROVIDER` y sin Ollama: 389 passed, 0 errores. |

## Dependencias (pasan a imprescindibles) · RNF-12

| | |
|---|---|
| **Qué** | 9 tandas de actualización con la suite completa, ruff y `mypy --strict` tras cada una: python-multipart, fastapi/starlette, pypdf, pyjwt, pillow, pila HTTP/TLS, pila de embeddings, weasyprint y herramientas de desarrollo. La pila de embeddings se verificó además con el modelo real, por ser un cambio de versión mayor. |
| **Por qué** | 140 vulnerabilidades conocidas en las dependencias bloqueadas. |
| **Commits** | `2cb138f` … `1739bbf`, `9a611d7` |
| **Resultado** | Queda solo chromadb, con 4 avisos sin parche publicado que afectan a su modo servidor HTTP, que ROSETTA no usa. Se documenta como **riesgo aceptado R-01**, ignorado de forma explícita en CI (`docs/P3_SEGURIDAD.md` §2). |

---

## Bloque A · Producto funcional e instalable

### A-1 · Instalación limpia · RNF-05

| | |
|---|---|
| **Qué** | Dockerfile reescrito: dependencias desde `uv.lock`, torch en versión CPU, Nuclei 3.11.1 verificado por SHA-256, modelo de embeddings precargado, usuario sin root, y solo se copian `src/`, `corpus/` y `scripts/`. Las bases de datos y los informes pasan a volúmenes persistentes. Nuevo comando `rosetta load-corpus all corpus`. |
| **Por qué** | Fallos de la instalación limpia con el Dockerfile antiguo: sin `.env`, compose abortaba; la build tardaba 10 min 53 s y la imagen ocupaba 10,3 GB (pila CUDA innecesaria); el proceso corría como root; Nuclei no estaba; se copiaba todo el repositorio; no se usaba el lockfile; y la base de controles se perdía en cada despliegue. |
| **Commits** | `2339813`, `d485245`, `f29cbde` |
| **Comprobación** | Clon limpio siguiendo el README: build en 165 s, imagen de 3,85 GB, contenedores *healthy*, 197 fragmentos indexados de los 7 marcos, proceso con uid 10001 y Ollama alcanzable desde el contenedor. |

### A-2 · Flujo end-to-end real · RF-01, RF-04

| | |
|---|---|
| **Qué** | Prueba sin maquetas, con Ollama `qwen2.5:14b`: login → `/translate` → hallazgo visible en el dashboard → dosier MD y PDF descargados desde el botón. |
| **Hallazgo** | Tras indexar con `load-corpus` (otro proceso), la API seguía viendo el índice vacío porque ChromaDB no admite dos procesos. El Traductor trabajó sin contexto y el LLM citó un control inexistente (`A.8.2.2`, de la versión 2013). Tras `docker compose restart app` recupera 10 fragmentos y cita `A.8.12`. Se documenta el reinicio en el README (`7e608e8`). |
| **Comprobación** | Navegador real (Chromium headless): login, 12 hallazgos en pantalla, dosier generado, PDF de 12 KB y MD descargados y 0 errores de JS en 6 pestañas. |

### A-3 · Descarga del dosier · RF-04

| | |
|---|---|
| **Qué** | `POST /reports/generate` devuelve URLs de la API en vez de rutas del servidor. Nuevo `GET /reports/download/{filename}`, autenticado, con lista blanca de nombres y comprobación de que la ruta no sale del directorio de informes. Botón «Generar dosier» en el dashboard. |
| **Por qué** | El endpoint devolvía rutas internas del servidor y desde el dashboard no se podía generar ni descargar el informe. |
| **Commit** | `60d437a` |
| **Pruebas** | 9 tests: sin rutas internas, descarga real de MD y PDF, 404, 5 nombres no válidos dan 400, *path traversal* codificado y 401 sin credenciales. |

### A-4 · Datos de demostración · todos los paneles

| | |
|---|---|
| **Qué** | `scripts/seed_demo.py`: caso ficticio TechServ (tres consejerías, categoría ALTA, datos de salud). Envía solo **datos de entrada** a la API real: 7 hallazgos que cubren los 7 marcos, un diff para el Gate CI/CD, alertas Wazuh, un procedimiento para drift y un PDF. Dominios `.example` e IP de documentación. |
| **Commit** | `6c7bd13` |
| **Comprobación** | 8 tests: solo usa la API, autentica cada llamada, cubre los 7 marcos, datos ficticios, sigue si un paso falla. Ejecución real con Ollama: 12/12 pasos en 90 s. |

### A-5 · README probado · RNF-05

| | |
|---|---|
| **Qué** | README reescrito a partir de la instalación real: requisitos (incluida la memoria de `qwen2.5:14b`), pasos numerados, `.env` explicado, uso sin API key, credenciales de prueba ficticias y alcance multi-marco honesto. |
| **Por qué** | El anterior no explicaba Docker. Citaba un comando inexistente (`indexar-corpus`) y métricas que nunca se midieron (tasa de alucinación, confianza, latencia, cobertura del 80 %). También daba datos falsos: 15 endpoints, 3 adaptadores Red Team y WeasyPrint como generador del PDF. |
| **Commits** | `283a6ba`, `7e608e8` |
| **Comprobación** | Los pasos del README se ejecutaron tal cual en un clon limpio (`readme_e2e.sh`). |

### A-7 · `.env.example`

| | |
|---|---|
| **Qué** | Todas las variables con valores ficticios. `OLLAMA_MODEL=qwen2.5:14b` y Ollama como proveedor por defecto. `ROSETTA_JWT_SECRET` vacío a propósito. `SHODAN_API_KEY` vacío. |
| **Por qué** | Faltaban variables y el modelo no era el decidido. Un secreto JWT de ejemplo habría sido un secreto conocido por cualquiera: gitleaks lo detectó en pre-commit. |
| **Commit** | `3168cd5` (más las variables nuevas de B-5 y B-8) |

### A-8 · Comportamiento ante errores · RNF-01, RF-15

| | |
|---|---|
| **Qué** | `GrafoCorrelacion.desde_uri` verifica la conexión con timeouts de 5 s. Nuevo `tests/test_degradacion.py`. |
| **Por qué** | El driver de Neo4j conecta de forma perezosa: con Neo4j caído al arrancar, la API no lo detectaba y cada petición esperaba unos 30 s. RNF-01 no tenía ningún test de API. |
| **Commit** | `1c567c4` |
| **Pruebas** | 11 tests: arranque con Neo4j inaccesible; `/translate` y el panel de cumplimiento con Neo4j caído; 4 tipos de entrada inválida dan 422 sin trazas; sin credenciales, Basic erróneo, JWT falsificado y login erróneo dan 401. |

### A-9 · Modo Auditoría coherente · RF-06

| | |
|---|---|
| **Amass** | Verificado: el panel de Auditoría **solo ofrece Nuclei y Nmap**, igual que el orquestador. El `amass` que señalaba la auditoría está en el formulario del Traductor como **origen de un hallazgo**, junto a subfinder, shodan y hibp, y no promete ningún escaneo. No se quita. El error real estaba en el README («3 adaptadores»), ya corregido. |
| **Nuclei** | Instalado en la imagen para amd64 y arm64, la arquitectura de producción (`2339813`). |
| **Laboratorio** | `lab/` con un nginx propio, sin puertos publicados y con fallos intencionados. Solo se puede escanear si el servidor lo autoriza con `ROSETTA_AUDIT_ALLOWLIST` (`419b737`). |
| **Comprobación** | Sin la allowlist, el objetivo `http://lab-objetivo` se rechaza con 400 porque resuelve a una IP privada. Con la allowlist: *(resultado de la auditoría real más abajo)*. |

### RF-18 · CLI con tests

| | |
|---|---|
| **Qué** | 20 tests de los 6 comandos de la CLI. |
| **Por qué** | `cli/main.py` estaba al 0 % de cobertura aunque RF-18 figuraba como cumplido. |
| **Commit** | `06bffda` |
| **Resultado** | Cobertura del 87 %. |

### Adelantados del Bloque B (porque cambiaban la instalación)

- **B-5 · Autenticación *fail-closed*** (`5cf5aac`, RF-15). Problemas: sin
  `ROSETTA_USER` la API quedaba abierta (aunque hubiera cuentas extra) y había
  un secreto JWT escrito en el código público. Cambios: ahora la app no arranca
  sin un secreto de 32 caracteres o más ni con contraseñas de menos de 12; sin
  credenciales solo arranca con `ROSETTA_AUTH_DISABLED=1`. 11 tests, entre
  ellos uno que comprueba que un token firmado con el antiguo secreto público
  se rechaza.
- **B-8 · Alcance con DNS y allowlist** (`810812d`, RNF-08). Problema: un nombre
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
  contrario y se ha corregido (`db71de5`).

---

## Bloque B · Hardening de seguridad del producto

### B-1 · Path traversal en `nombre_base` · RNF-07

| | |
|---|---|
| **Qué** | Validación Pydantic en `POST /reports/generate`: `nombre_base` solo acepta `[a-zA-Z0-9_-]`, máximo 64 caracteres. Cualquier separador de ruta o punto devuelve 422 antes de tocar el sistema de ficheros. |
| **Por qué** | Sin validación era posible escribir el informe en rutas arbitrarias del contenedor con un nombre como `../../etc/x`. |
| **Commit** | `5ca3ca8` |
| **Tests** | 5 tests en `tests/test_security.py` (traversal con `/`, con `\`, con punto, demasiado largo, espacio; más 1 caso válido). |

### B-2 · XSS en el dashboard · RNF-07

| | |
|---|---|
| **Qué** | Función `esc()` en `src/rosetta/api/dashboard.py` que aplica `html.escape()` a cualquier cadena antes de insertarla en el HTML del panel. Reemplaza todos los `innerHTML =` con datos de usuario o de salida del LLM. |
| **Por qué** | El dashboard construía el HTML concatenando strings crudos. Un hallazgo con `<script>` en el campo `evidencia` o en la justificación del LLM ejecutaba JS en el navegador del auditor. |
| **Commit** | `92a5989` |

### B-3 · Cabeceras de seguridad HTTP · RNF-07

| | |
|---|---|
| **Qué** | Middleware `SecurityHeadersMiddleware` en `src/rosetta/api/main.py`: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy` con directivas obligatorias y `object-src 'none'`. |
| **Por qué** | Sin cabeceras, el navegador no aplica ninguna política de origen. Requerimiento explícito de hardening del enunciado. |
| **Commit** | `c552729` |
| **Tests** | 3 tests en `tests/test_security.py`: cabeceras presentes, CSP con directivas obligatorias, CSP permite unpkg y Google Fonts. |

### B-4 · X-Real-IP con proxies de confianza · RNF-07

| | |
|---|---|
| **Qué** | `ROSETTA_TRUSTED_PROXIES` (por defecto `127.0.0.1` y `172.16.0.0/12`). Solo se acepta `X-Real-IP` si el peer TCP está en esa lista. `X-Forwarded-For` nunca se usa para la clave de rate limiting. |
| **Por qué** | Sin validación del origen, cualquier cliente podía enviar `X-Real-IP: 1.2.3.4` para rotar la clave de rate limit o suplantar una IP. La primera versión usaba `X-Real-IP` incondicionalmente. |
| **Commits** | `c552729` (implementación inicial) · `4ebeade` (revisión: proxies de confianza estrictos) |
| **Tests** | 6 tests en `tests/test_security.py`: localhost y red Docker son de confianza; IP pública no lo es; X-Real-IP desde origen no confiable se ignora; desde proxy de confianza se acepta. |

### B-6 · Errores 500 sin detalles internos · RNF-07

| | |
|---|---|
| **Qué** | Handler global en FastAPI que captura cualquier excepción no controlada y devuelve `{"detail": "Error interno del servidor"}` sin traza ni mensajes de sistema. `structlog` registra el traceback completo en los logs del contenedor. |
| **Por qué** | Las excepciones sin capturar exponían rutas internas, nombres de variables y mensajes de librerías en la respuesta JSON. |
| **Commit** | `c552729` |
| **Tests** | 2 tests en `tests/test_security.py`: excepción en `ReportGenerator` y en `consultar_copilot` no filtran la cadena interna. |

### B-7 · Modelo de amenazas STRIDE · RNF-11

| | |
|---|---|
| **Qué** | Sección 4 de `docs/P3_SEGURIDAD.md`: tabla STRIDE completa (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege) sobre los activos de ROSETTA, con referencia a los controles B-1..B-8 que los mitigan. Tabla adicional de amenazas específicas de LLM: prompt injection, XSS vía LLM, economic DoS, alucinaciones, corpus poisoning. Diagrama de superficie de ataque. |
| **Por qué** | RNF-11 exige modelo de amenazas documentado. El Bloque B implementó controles; este ítem los mapea formalmente. |
| **Commit** | `05e58d5` |
| **Resultado** | RNF-11 pasa de Pendiente a ✅. |

### B-9 · Límite de tamaño y magic bytes en PDF — NO HECHO

B-9 no está implementado. `POST /ingest/pdf` no tiene límite de tamaño ni comprobación de magic bytes. La amenaza D-2 del modelo STRIDE (subida de PDF gigante para agotar memoria) figura como **Alto — sin mitigar** en `docs/P3_SEGURIDAD.md`. Queda fuera del alcance del MVP-1.

### B-10 · Imagen Docker reproducible y sin root · RNF-12

| | |
|---|---|
| **Qué** | Dockerfile reescrito: build desde `uv.lock` (reproducible), torch CPU (2,1 GB vs 10,3 GB), Nuclei instalado para amd64 y arm64, proceso como usuario `rosetta` sin privilegios, solo `src/` y `scripts/` copiados. |
| **Por qué** | La imagen anterior tardaba 10 min, pesaba 10,3 GB, corría como root y no incluía Nuclei. Proceso como root viola el principio de mínimo privilegio. |
| **Commit** | `2339813` |

### B-11 · Secretos fuera del historial — NO HECHO (pendiente decisión)

B-11 (limpieza del historial con `git filter-repo`) no se ejecutó. Decisión documentada en INC-01 (`docs/P3_SEGURIDAD.md`): la contraseña antigua del profesor sigue en el historial de GitHub, pero ya está rotada y verificada como rechazada en producción. La limpieza con force-push la decide el autor antes del jueves 8. No ejecutar sin autorización explícita.

---

## Bloque C · Corpus ENS y harness de evaluación

### C-1 · Corpus ENS enriquecido

| | |
|---|---|
| **Qué** | `corpus/ens/ens-2022-anexo-ii.yaml` ampliado: descripciones cortas y completas, referencias cruzadas ISO 27001:2022 y NIS2 por medida, etiquetas de categoría ENS. Fuentes: texto del Anexo II del RD 311/2022 (BOE-A-2022-7191) y mapeo CCN-STIC 825. |
| **Por qué** | El corpus anterior era un esqueleto sin descripciones. Sin texto real el RAG no produce contexto útil para el Traductor. |
| **Commit** | `92d4b83` |

### C-2 · Harness de evaluación · `eval/run_eval.py`

| | |
|---|---|
| **Qué** | Script de evaluación automatizada con dos modos: `correspondencia` (ENS→ISO, ground truth del SoA del caso TechServ del equipo docente) y `hallazgo` (hallazgo técnico→ISO, ground truth provisional). Métricas por caso y por familia: Precision, Recall, F1, tasa de alucinación (control inventado) y tasa de discrepancia (control real con mapeo diferente). |
| **Por qué** | Sin métricas objetivas no hay forma de comparar el Traductor solo frente al Traductor + Validador. Requerimiento explícito del plan de cierre. |
| **Commits** | `92d4b83` (base) · `86a5e91` (separación alucinación/discrepancia, modo hallazgo, Validador) |

### C-3 · Ground truth ENS↔ISO

| | |
|---|---|
| **Qué** | `eval/ground_truth/ens_iso.json`: 73 casos (uno por medida ENS), fuente = SoA del caso TechServ del equipo docente. `eval/ground_truth/ens_hallazgos_tecnicos.json`: 16 casos ficticios (TechServ S.A.), uno por familia ENS, con hallazgos técnicos sintéticos y anotación `revision: pendiente`. **El mapeo no se generó con IA** — sería medir el modelo contra sí mismo. |
| **Por qué** | La única fuente válida de ground truth es el criterio humano (SoA del docente o revisión manual). Los 16 casos de hallazgo son provisionales hasta revisión. |
| **Commits** | `92d4b83` (`ens_iso.json`) · `86a5e91` (`ens_hallazgos_tecnicos.json`) |

### C-4 · Ejecución del eval con Ollama · resultados

| | |
|---|---|
| **Qué** | Ejecución de los 73 casos de correspondencia y los 16 de hallazgo con `qwen2.5:14b` vía Ollama. Comparativa Traductor solo vs. Traductor + Validador (10 casos piloto). |
| **Resultados (correspondencia, 73 casos)** | P=0.408 · R=0.216 · F1=0.265 · alucinación=0.000 · discrepancia=0.625 |
| **Resultados (hallazgo, 16 casos)** | P=0.313 · R=0.281 · F1=0.281 · alucinación=0.000 · discrepancia=0.757 |
| **Validador piloto (10 casos)** | aprobados avg F1=0.352 · rechazados avg F1=0.267 · rejection_precision@F1<0.5=1.0 |
| **Hallazgo clave** | `alucinacion_rate = 0.000` en ambos modos. El modelo nunca inventa controles inexistentes; todas las equivocaciones son controles ISO reales con mapeo diferente al de CCN-STIC 825. El Validador rechazó correctamente el 100 % de los casos con F1 < 0.5. |
| **Commit** | `86a5e91` |

---

## Bloque D · Cierre P3

### D-1 · Tests del eval harness · C-2

| | |
|---|---|
| **Qué** | 27 tests unitarios en `tests/test_eval_harness.py` para las funciones puras de `eval/run_eval.py`: `_normalize_iso_id` (12 tests), `extract_iso_ids` (7 tests), `score_case` (8 tests). Sin llamadas al LLM. |
| **Por qué** | El harness de evaluación del Bloque C no tenía tests. Las funciones de normalización y scoring son la parte más crítica del pipeline: un bug ahí invalida todas las métricas. |
| **Commit** | este bloque D |
| **Comprobación** | `uv run pytest tests/test_eval_harness.py -v` → 27 passed en 3 s. |

### D-2 · Benchmark RNF-09 · latencia del Traductor

| | |
|---|---|
| **Qué** | Benchmark formal de 5 llamadas al Traductor Simbiótico con Ollama qwen2.5:14b. Métricas: p50=8.2 s, avg=16.6 s, max=41.3 s. 4/5 casos bajo el umbral de 30 s. Un caso excedió el límite (41.3 s) por generación LLM verbosa con advertencias `marco_desconocido`. |
| **Por qué** | RNF-09 estaba pendiente de benchmark formal desde el enunciado. |
| **Commit** | este bloque D |
| **Resultado** | `P3_REQUISITOS.md` RNF-09 actualizado con los valores medidos. Estado: 🟡 (p50 y avg cumplen; tail puede exceder con hallazgos complejos). |

### D-3 · Matriz de trazabilidad · docs/P3_MATRIZ.md

| | |
|---|---|
| **Qué** | Nuevo fichero `docs/P3_MATRIZ.md`: tabla RF/RNF → commit → tests → evidencia para los 26 RF y 12 RNF. Incluye resumen por bloque y snapshot de tests/cobertura. |
| **Por qué** | Requerimiento explícito del plan de cierre P3. Permite al evaluador trazar cualquier requisito hasta el código en segundos. |
| **Commit** | este bloque D |

### D-4 · Incoherencias entre el informe P1 y el estado real · docs/P3_MEMORIA_INSUMOS.md

| | |
|---|---|
| **Qué** | Análisis de divergencias entre lo que afirma `docs/informe/informe_rosetta_practica1.html` y lo que implementa el código en la rama `main` tras el Bloque A de P3. |

**Incoherencias detectadas:**

| Afirmación en el informe P1 | Realidad en P3 | Gravedad |
|-----------------------------|----------------|----------|
| «FastAPI expone **15 endpoints REST** y un WebSocket» | La API tiene **~30 rutas REST** + 1 WebSocket en `src/rosetta/api/main.py`. | Menor — el número real es mayor, no menor. |
| «**WeasyPrint**» como generador de PDF (píldora de tecnología y lista de dependencias) | El PDF se genera con **reportlab** (MIT puro Python). `src/rosetta/core/report_generator.py` línea 7: _«WeasyPrint requiere GTK+; reportlab es el backend»_. WeasyPrint no está en `pyproject.toml`. | Media — dependencia incorrecta en el informe. |
| «**tasa de alucinación**» como métrica ya medida en P1 | La métrica no existía. El harness de evaluación (`eval/run_eval.py`) se creó en el Bloque C de P3. Los datos reales: `alucinacion_rate = 0.000`, `discrepancia_rate = 0.625` (correspondencia, 73 casos). | Media — métrica prometida sin base empírica. |
| Adaptadores Red Team: **Nuclei, Nmap, Amass** | Amass tiene adapter (`src/rosetta/adapters/red/amass.py`) pero **no está instalado** en la imagen Docker ni aparece en el orquestador de auditoría. El panel de Auditoría solo ofrece Nuclei y Nmap. Amass actúa como valor de `origen` en el formulario del Traductor, no como scanner activo. | Menor — el adapter existe pero no está operativo. |
| Credenciales del profesor en texto claro | Credencial rotada y reemplazada por `[credencial invalidada — ver P3_SEGURIDAD.md §1]` en el HTML (commit `5eb5abd` saneado). Sigue en el `.docx` (binario, edición manual pendiente). | Alta — ya gestionado como INC-01. |

**Origen del análisis**: revisión manual del HTML contra los commits del Bloque A. Ver `docs/P3_MEMORIA_INSUMOS.md` para el inventario completo de fuentes y datos de P3.

### D-5 · Guión de vídeo · docs/P3_VIDEO_SCRIPT.md

| | |
|---|---|
| **Qué** | Nuevo fichero `docs/P3_VIDEO_SCRIPT.md`: guión de 7–9 minutos con 9 secciones (contexto, login, traducción, multi-marco, dosier, Red Team, eval metrics, copilot, cierre), tiempos, comandos exactos y notas técnicas. |
| **Por qué** | D-5 del plan de cierre. El autor necesita un guión estructurado para grabar la demo. |
| **Commit** | este bloque D |

---

## Bloque F · Correcciones antes de la congelación (2026-10-10)

Fallos encontrados al hacer las capturas de la memoria con el stack local (Docker + Ollama `qwen2.5:14b`). Afectan a requisitos que salen en el vídeo, así que se corrigen; no se declaran como limitación. Un commit por fallo, cada uno con su test.

### F-1 · Swagger UI en blanco por la CSP · RF-13, RNF-11

| | |
|---|---|
| **Qué** | La CSP de B-3 (`c552729`) solo admitía scripts de `https://unpkg.com`, y FastAPI carga Swagger UI y ReDoc desde `cdn.jsdelivr.net`: `/docs` salía en blanco (`SwaggerUIBundle is not defined`). Ahora `/docs`, `/docs/oauth2-redirect` y `/redoc` reciben `_CSP_DOCS` (jsDelivr para scripts y estilos, `blob:` para el worker de ReDoc, favicon de FastAPI); el resto de rutas mantiene la CSP estricta. |
| **Test** | `tests/test_security.py`: CSP de `/docs` y `/redoc`, y CSP estricta en `/health`, `/dashboard` y `/openapi.json`. `tests/e2e/test_docs_ui.py` (Playwright, fuera de la CI): falla contra la imagen anterior (timeout esperando `.opblock`) y pasa con la nueva. |
| **Commit** | este commit |

### F-2 · Ollama recortaba los prompts largos · RF-10, RF-01

| | |
|---|---|
| **Qué** | `OllamaClient` no enviaba `num_ctx` y Ollama usaba su ventana por defecto (4096 tokens): cuando el prompt la supera, conserva solo la segunda mitad (log de Ollama: `truncating input prompt limit=2050 prompt=5129`). Ahora cada llamada envía `options.num_ctx`, configurable con `OLLAMA_NUM_CTX` (por defecto 16384; un valor no entero o no positivo impide arrancar). Documentado en `.env.example` y en el README. |
| **Medición antes** (`prompt_eval_count`, mismo código que la API) | Copilot (7 marcos): **2050** de 5099 → recortado; el modelo no veía la pregunta y respondió sobre XSS. `/translate` con 1 marco (modo del eval y del benchmark RNF-09): 1189, sin recorte. Con 3 marcos (seed): 3635, sin recorte. Con los 7 marcos: 5655 → recortado a 2050 y el LLM no llamó a la herramienta (`ValueError`). |
| **Medición después** | Copilot 5078 · 1 marco 1189 · 3 marcos 3635 · 7 marcos 5637; ningún aviso de recorte. Memoria de `qwen2.5:14b` (`ollama ps`): 9,47 GB con 4096 → 11,9 GB con 16384. |
| **Eval** | No se repite: sus prompts (1 marco, ~1200 tokens) nunca superaron la ventana, así que el eval del 2026-10-04 y el benchmark RNF-09 no se hicieron con prompts recortados. |
| **Test** | `tests/test_llm.py`: `num_ctx` por defecto 16384, valor desde `OLLAMA_NUM_CTX` y error con valores inválidos. |
| **Commit** | este commit |

### F-3 · Modo Auditoría: 0 hallazgos contra el laboratorio · RF-06, RNF-08

| | |
|---|---|
| **Qué** | Dos causas. (1) Nuclei: con el nombre interno `lab-objetivo`, algunas peticiones fallaban con `no address found for host` y, al acumular errores, Nuclei marcaba el host como caído y se saltaba las 11 144 plantillas restantes. (2) Nmap recibía la URL `http://lab-objetivo` tal cual y escaneaba 0 hosts. |
| **Cambio** | `NucleiAdapter` añade `-nmhe` (no descartar el host), `-ni` (sin interactsh: ningún tráfico fuera del objetivo), `-duc`, y tags y severidades configurables (`ROSETTA_NUCLEI_TAGS`, por defecto `exposure,misconfig,tech`; `ROSETTA_NUCLEI_SEVERITY`, por defecto todas), validados al crear el adaptador. `NmapAdapter` pasa a Nmap el host de la URL. |
| **Prueba real** | Auditoría `33b77c5f9e30` contra el laboratorio: 18 hallazgos (17 de Nuclei, 1 de Nmap: `172.24.0.3:80/tcp`) en 42 s, 0 errores. Detecta el `.env` publicado (high), la versión de nginx y las cabeceras ausentes. El listado de `/backups/` no lo detecta ninguna plantilla pública; documentado en `lab/README.md`. |
| **Test** | `tests/test_nuclei_adapter.py`: comando por defecto, tags y severidades desde entorno y por parámetro, configuración inválida, invocación simulada con salida del laboratorio. `tests/test_orchestrator.py`: Nmap recibe el host, no la URL. |
| **Commit** | este commit |

### F-4 · `/compliance/state/{marco}` no filtraba por marco · RF-19

| | |
|---|---|
| **Qué** | `_persist_to_graph` registraba cada control incumplido bajo **cada** marco aplicable (producto cartesiano), y el cálculo en memoria contaba todos los controles de cualquier hallazgo que incluyera el marco. Con `iso_27001_2022` aparecían `Req.6.4` (PCI-DSS), `Art.32.1` (RGPD) o `mp.info.1` (ENS). Además el LLM no siempre declara todos los marcos: en la demo, un hallazgo con controles ENS solo declaraba ISO. |
| **Cambio** | Nuevo `core/control_marcos.py`: índice control → marco construido desde el corpus (226 identificadores; solo `Art.5.1`, `Art.6.1` y `Art.28.1` están a la vez en DORA y en el RGPD). Cada control se registra y se cuenta solo en su marco; si es ambiguo, en los marcos declarados que lo contienen; si no está en el corpus, solo cuando hay un único marco declarado. |
| **Pendiente operativo** | Los hallazgos ya guardados en Neo4j antes de este cambio conservan las relaciones erróneas; en local se regeneran vaciando el volumen y repitiendo el seed. En producción habría que hacer lo mismo con los datos de demo. |
| **Test** | `tests/test_api.py`: estado por marco en memoria (ISO, ENS, PCI-DSS, NIS2) y persistencia en el grafo con cada control en su marco. `tests/test_control_marcos.py`: control no declarado, ambiguo, desconocido y normalización. |
| **Commit** | este commit |

### F-5 · `GET /audit/{audit_id}` respondía siempre 422 · RF-06

| | |
|---|---|
| **Qué** | Encontrado al verificar F-3: el parámetro `request` estaba anotado como `Any`, así que FastAPI lo trataba como parámetro de query obligatorio y la consulta del estado de una auditoría devolvía 422 (`missing query request`). El dashboard no lo notaba porque sigue la auditoría por WebSocket. |
| **Cambio** | `request: Request` y los hallazgos por la dependencia `FindingsDep`. |
| **Test** | `tests/test_api.py`: estado de una auditoría existente (200) y de una inexistente (404); los dos fallaban con 422. |
| **Commit** | este commit |
