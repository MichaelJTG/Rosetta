# docs/P3_SEGURIDAD.md — Seguridad del propio producto ROSETTA (Práctica 3)

> Documento vivo. Recoge los incidentes detectados en el propio repositorio,
> los riesgos aceptados de forma explícita y el modelo de amenazas (STRIDE).
> **No contiene secretos**: las credenciales se citan por su función, nunca por su valor.

---

## 1. Incidentes

### INC-01 · Credenciales escritas en el código de un repositorio público

| Campo | Valor |
|---|---|
| Severidad | Alta (acceso al panel de producción) |
| Estado | **Contenido y corregido** el 2026-10-04 |
| Requisitos afectados | RNF-06 (cero secretos), RF-15 (autenticación) |

**Qué pasó.** Para dar acceso al profesor se añadió una cuenta adicional
(`ROSETTA_USERS_EXTRA`). Su contraseña real se escribió como literal en
`tests/test_auth.py` (commit `0fafee1`, 2026-05-30) y se publicó en GitHub.
Durante la auditoría de estado del 2026-10-04 aparecieron además:

- la misma contraseña citada en `docs/P3_REQUISITOS.md` y en el mensaje de un
  commit local todavía no publicado;
- la contraseña de la cuenta principal escrita en `docs/informe/_shots.py`
  (script de capturas), también en un commit local no publicado.

El escáner gitleaks del CI no lo detectó: las contraseñas de texto libre no
siguen un patrón reconocible como las claves de API.

**Contención (2026-10-04).** En el servidor de producción:

1. Copia de seguridad del `.env` (permisos 600, solo en el servidor).
2. Contraseñas nuevas para la cuenta principal y la del profesor y un
   `ROSETTA_JWT_SECRET` nuevo de 64 caracteres, generados con el módulo
   `secrets` de Python y guardados fuera del repositorio.
3. Recreado **solo** el contenedor `app`, con la misma imagen
   (`docker compose up -d --no-deps --no-build --force-recreate app`).
   Cambiar el secreto JWT invalida también cualquier sesión abierta.

**Verificación.** `/health` responde 200, tanto directo como a través de nginx.
Las credenciales nuevas dan 200 en `/auth/login` y las antiguas 401, en las dos
cuentas. La contraseña que había en `_shots.py` también da 401.

**Corrección.**

- Los dos commits locales se sanearon **antes** de publicarlos (`5eb5abd`,
  `4942403`): sin el literal ni en el contenido ni en el mensaje.
- `_shots.py` lee la URL y las credenciales de variables de entorno
  (`ROSETTA_SHOTS_*`).
- Los tests usan una contraseña de prueba ficticia (`TEST_EXTRA_USER_PASS`).

**Limpieza del historial (2026-10-06).** Se ejecutó `git filter-repo
--replace-text` sobre un clon `--mirror` temporal para reemplazar el literal
de la contraseña en el contenido de los commits y en los mensajes.
Verificación: `git log -p --all` — 0 apariciones del literal original;
gitleaks sobre el historial completo (`fetch-depth: 0`) — 0 hallazgos; CI en
verde tras el force-push (`f50957f` → `4aeef3b`).

El commit original `e2819f0` sigue siendo accesible en GitHub por su hash
(confirmado HTTP 200 el 2026-10-06): es un objeto huérfano que la purga del
grafo de objetos de GitHub no ha eliminado todavía. **Pendiente:** purga
solicitada a GitHub Support (sin respuesta aún).

**Lecciones y controles añadidos.**

- Las credenciales de prueba **siempre** salen de variables de entorno o son
  ficticias.
- Toda credencial que se comparta con terceros se rota al terminar el uso.
- Copias locales del informe de la Práctica 1 (`.html` y `.docx`, sin
  versionar) contienen la contraseña antigua del profesor. Ya está invalidada,
  pero conviene revisarlas antes de reenviarlas.

---

## 2. Riesgos aceptados

### R-01 · Vulnerabilidades de chromadb sin parche publicado

| Campo | Valor |
|---|---|
| Paquete | `chromadb` 1.5.9 (última versión publicada a 2026-10-04) |
| Avisos | PYSEC-2026-311 (CVE-2026-45829), PYSEC-2026-3813 (CVE-2026-45830), PYSEC-2026-3814 (CVE-2026-45833), PYSEC-2026-3815 (CVE-2026-45831) |
| Parche | Ninguno publicado |
| Decisión | Riesgo aceptado, con revisión en cada nueva versión de chromadb |

**Qué dicen los avisos.** Los cuatro afectan al **modo servidor HTTP** de ChromaDB:

- ejecución de código enviando un repositorio de modelo con `trust_remote_code`
  a la API `/api/v2/...`;
- autorización RBAC que no comprueba tenant, base de datos ni colección;
- acceso a colecciones de otros tenants.

**Por qué no aplica a ROSETTA** (verificado con `grep` en `src/` y `docker-compose.yml`):

- ROSETTA usa ChromaDB **embebido en el proceso**
  (`chromadb.PersistentClient`, `src/rosetta/core/rag.py:82`). No arranca
  ningún servidor Chroma y no hay ningún servicio ni puerto Chroma en
  `docker-compose.yml`.
- El modelo de embeddings es una constante del código
  (`paraphrase-multilingual-MiniLM-L12-v2`). No se usa `trust_remote_code` en
  ningún sitio, y ninguna entrada de usuario llega a la configuración de la
  colección.
- La persistencia vive en un volumen Docker interno (`rosetta_chroma`), al que
  no se accede desde fuera del contenedor.

**Control en CI.** El job `dependency-audit` ignora **solo** esos cuatro
identificadores, de forma explícita y comentada. Cualquier CVE nuevo, de
chromadb o de otro paquete, rompe el CI.

---

## 3. Auditoría de dependencias (RNF-12)

| Fecha | Herramienta | Resultado |
|---|---|---|
| 2026-09-22 | `uv tool run pip-audit` (CI) | "0 CVE", **falso**: auditaba los 28 paquetes de la propia herramienta, no el proyecto |
| 2026-10-04 | `pip-audit -r` sobre `uv.lock` exportado | 19 paquetes, 140 vulnerabilidades |
| 2026-10-04 | Tras 9 tandas de actualización | 1 paquete (chromadb), 4 avisos sin parche (R-01); CI en verde |
| 2026-10-06 | CI rojo post-commit `1291d3f`: job `dependency-audit` falla | CVE-2026-104851 en `fsspec 2026.3.0` no estaba en ignore list; parche existe → actualizado a `2026.9.0` (`uv add --upgrade fsspec`); 515 tests OK; commit `26e63e5` |

Las actualizaciones se hicieron por tandas, priorizando lo expuesto a peticiones
HTTP: python-multipart, starlette/fastapi, pypdf, pyjwt, pillow, pila HTTP/TLS,
pila de embeddings, weasyprint y herramientas de desarrollo. Tras cada tanda se
ejecutaron la suite completa, ruff y `mypy --strict`. En la pila de embeddings
(cambio de versión mayor) se verificó además el RAG con el modelo real.

**CVE-2026-104851 (fsspec).** `ReferenceFileSystem.parse()` procesaba JSON
Kerchunk sin validación de referencias arbitrarias. ROSETTA no usa
`ReferenceFileSystem` directamente; fsspec es dependencia transitiva de
`torch`/`huggingface-hub`/`sentence-transformers`. Upgrade defensivo: 0 cambios
de código. Parche publicado en PyPI el 2026-09-18.

---

## 3b. B-4 en producción (2026-10-06)

El default anterior de `ROSETTA_TRUSTED_PROXIES` incluía `10.0.0.0/8` y
`172.17.0.0/16` (eliminados en commit `f06f726`). Para aplicar el cambio en el
servidor de producción (Hetzner):

1. `docker network inspect rosetta_default` → gateway `172.18.0.1`.
2. Verificado que `/etc/nginx/sites-enabled/rosetta` contiene
   `proxy_set_header X-Real-IP $remote_addr` (nginx pone la IP del cliente; el
   cliente no puede sobrescribirla).
3. Añadida al `.env` del servidor:
   `ROSETTA_TRUSTED_PROXIES=127.0.0.1/32,::1/128,172.18.0.1/32`
4. Reiniciado solo el contenedor `app`
   (`docker compose up -d --no-deps --no-build --force-recreate app`).
5. Verificación: dos clientes con `X-Real-IP` distintos (`203.0.113.1` y
   `198.51.100.2`) desde `127.0.0.1` (proxy confiable) muestran contadores
   separados en `/auth/login` — el segundo cliente recibe 401, no 429, tras
   los intentos fallidos del primero.

---

## 4. Modelo de amenazas STRIDE (B-7)

### Activos

| Activo | Descripción | Confidencialidad | Integridad | Disponibilidad |
|--------|-------------|-----------------|-----------|----------------|
| Corpus normativo | Fragmentos indexados de ISO 27001, ENS, NIS2, DORA, RGPD, NIST CSF 2.0, PCI-DSS 4.0 en ChromaDB | Media | Alta | Alta |
| Historial de hallazgos | SQLite con todos los `HallazgoMaestro` de las sesiones | Alta | Alta | Alta |
| Credenciales de usuario | Hashes bcrypt en variables de entorno; secreto JWT en `.env` | Crítica | Alta | — |
| Catálogo de controles | SQLite con estado de cumplimiento por marco | Alta | Alta | Alta |
| Informes generados | Dosiers MD/PDF en volumen Docker `rosetta_reports` | Alta | Alta | Media |
| Clave API de Anthropic | Variable de entorno `ANTHROPIC_API_KEY` | Crítica | — | — |
| Acceso al LLM (Ollama/Claude) | Canal HTTP interno (Ollama) o HTTPS (Claude API) | Media | Alta | Alta |

### Actores

| Actor | Descripción | Nivel de confianza |
|-------|-------------|-------------------|
| Auditor autenticado | Usuario con JWT o Basic válido | Confianza total sobre sus propios hallazgos |
| Atacante externo | Sin credenciales; accede solo a la API pública | Sin confianza |
| Atacante interno | Sesión activa conseguida por robo de credencial o JWT | Confianza limitada |
| LLM externo | Claude API (Anthropic); puede devolver contenido generado | Datos no confiables (ver amenazas LLM) |
| Herramientas de terceros | Nuclei, Nmap, Wazuh; controlados por el servidor | Confianza media (outputs validados) |

### Amenazas por categoría STRIDE

#### S — Spoofing (suplantación)

| ID | Amenaza | Componente afectado | Control existente | Riesgo residual |
|----|---------|--------------------|--------------------|-----------------|
| S-1 | Robo de JWT para suplantar sesión | `POST /auth/login` · `src/rosetta/api/auth.py` | Secreto JWT ≥ 32 chars obligatorio (B-5); tokens con expiración configurable | Bajo |
| S-2 | Fuerza bruta de credenciales | `POST /auth/login` · `POST /auth/basic` | Rate limiting slowapi (120 req/min por IP, con X-Real-IP como clave) | Medio — sin bloqueo permanente por cuenta |
| S-3 | Inyección de IP para eludir rate limiting via XFF | `_client_ip` en `main.py` | **B-4 corregido**: se usa X-Real-IP (nginx), XFF se descarta | Bajo |

#### T — Tampering (manipulación)

| ID | Amenaza | Componente afectado | Control existente | Riesgo residual |
|----|---------|--------------------|--------------------|-----------------|
| T-1 | Modificación de informe en disco antes de descarga | `GET /reports/download/{filename}` | Nombre en lista blanca `[A-Za-z0-9][A-Za-z0-9_-]{0,99}.(md\|pdf)`; ruta restringida al directorio de informes (A-3) | Bajo |
| T-2 | Path traversal en `nombre_base` de generación | `POST /reports/generate` | **B-1 corregido**: Pydantic v2 `pattern=` rechaza cualquier carácter fuera de `[A-Za-z0-9_-]` (máx. 64 chars) → 422 | Bajo |
| T-3 | Manipulación del estado de un control por otro usuario | `PATCH /controls/{marco}/{id}` | Autenticación JWT obligatoria; en MVP-6 no hay RBAC multi-usuario (todos los usuarios autenticados comparten el mismo catálogo) | Medio — pendiente RBAC si hay varios auditores |
| T-4 | Envenenamiento del corpus (corpus poisoning) | `rosetta load-corpus` · ChromaDB | Comando CLI restringido a operadores; corpus cargado desde archivos locales validados | Bajo |

#### R — Repudiation (repudio)

| ID | Amenaza | Componente afectado | Control existente | Riesgo residual |
|----|---------|--------------------|--------------------|-----------------|
| R-1 | Un auditor niega haber creado un hallazgo | `POST /translate` · `session_store.py` | Los hallazgos son append-only con timestamp; JWT identifica al emisor en el log de structlog | Medio — no hay firma criptográfica por usuario en cada hallazgo |
| R-2 | Un auditor niega haber cambiado el estado de un control | `PATCH /controls/{marco}/{id}` | Log de structlog con timestamp e IP real | Medio — no hay audit trail persistido por operación |

#### I — Information Disclosure (divulgación)

| ID | Amenaza | Componente afectado | Control existente | Riesgo residual |
|----|---------|--------------------|--------------------|-----------------|
| I-1 | Exposición de detalles internos en errores 500 | API REST | **B-6 corregido**: mensajes genéricos; excepción solo en log structlog interno | Bajo |
| I-2 | XSS almacenado via datos del LLM o del controlador | Dashboard JS (`dashboard.py`) | **B-2 corregido**: `esc()` en todos los contextos `innerHTML` con datos de usuario/LLM | Bajo |
| I-3 | Filtración de secretos en el repositorio | Codebase · CI | gitleaks en pre-commit y CI; incidente INC-01 documentado y credenciales rotadas | Bajo (historial antiguo, ya inválido) |
| I-4 | Acceso a informes sin autenticar | `GET /reports/download/{filename}` | Endpoint autenticado: sin JWT/Basic válido → 401 (A-3) | Bajo |
| I-5 | Headers HTTP revelan tecnología de implementación | Todas las respuestas | **B-3**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP añadidos | Bajo |

#### D — Denial of Service (denegación de servicio)

| ID | Amenaza | Componente afectado | Control existente | Riesgo residual |
|----|---------|--------------------|--------------------|-----------------|
| D-1 | Abuso de `/translate` para agotar cuota del LLM | `POST /translate` | Rate limiting (120 req/min por IP); autenticación obligatoria | Medio — economic DoS si la clave API se filtra |
| D-2 | Subida de PDF gigante para agotar memoria | `POST /ingest/pdf` | **B-9 implementado**: comprobación de magic bytes `%PDF` (fast-fail antes de leer el fichero completo), límite configurable vía `ROSETTA_PDF_MAX_SIZE_MB` (20 MB por defecto, rechazo 413 antes del read completo), tope de páginas configurable vía `ROSETTA_PDF_MAX_PAGES` (500 por defecto, rechazo 422). 4 tests en `tests/test_security.py` | Bajo |
| D-3 | Bucle de agente LLM que no termina | Pipeline RAG + LLM | Timeout del cliente HTTP (aiohttp/httpx) configurado en el SDK | Medio — no hay circuit breaker explícito |
| D-4 | Escaneo masivo de activos internos via Modo Auditoría | `POST /audit/start` | Validación de alcance con DNS + `is_global` + allowlist de servidor (B-8) | Bajo |

#### E — Elevation of Privilege (elevación de privilegios)

| ID | Amenaza | Componente afectado | Control existente | Riesgo residual |
|----|---------|--------------------|--------------------|-----------------|
| E-1 | Proceso app corriendo como root en el contenedor | Dockerfile | uid 10001 (`USER rosetta`), sin `CAP_NET_ADMIN` (A-1) | Bajo |
| E-2 | Nuclei o Nmap ejecutados con privilegios de red ampliados | `src/rosetta/adapters/red/` | Proceso normal sin NET_RAW; Nmap SYN scan requiere root → modo TCP connect fallback | Bajo |
| E-3 | Inyección de comandos via parámetros de escaneo | `POST /audit/start` | Parámetros pasados como lista (no como shell string); Pydantic valida tipos | Bajo |

### Amenazas específicas de sistemas LLM

| ID | Amenaza | Descripción | Control existente | Riesgo residual |
|----|---------|-------------|-------------------|-----------------|
| LLM-1 | Prompt injection directa | Un hallazgo o consulta al Copilot contiene instrucciones que modifican el comportamiento del LLM | Tool-use forzado con esquema Pydantic — el LLM solo puede rellenar campos predefinidos, no ejecutar texto libre | Medio |
| LLM-2 | XSS via salida del LLM | El LLM genera `<script>` o atributos `onerror=` en `justificacion`, `cita_normativa` u otros campos de texto renderizados en el dashboard | **B-2 corregido**: todos los campos LLM pasan por `esc()` antes de `innerHTML` | Bajo |
| LLM-3 | Economic DoS (agotamiento de cuota) | Un atacante autenticado lanza miles de traducciones para agotar la cuota de la API de Anthropic | Rate limiting + autenticación; sin cuota explícita en código | Medio |
| LLM-4 | Alucinación de controles | El LLM cita un control inexistente o de una versión antigua del estándar | RAG sobre corpus verificado limita el espacio de respuesta; tool-use fuerza IDs reales de controles | Medio — sin verificador automático de IDs en esta versión |
| LLM-5 | Corpus poisoning via PDF malicioso | Un PDF enviado a `/ingest/pdf` contiene texto que envenena el corpus | El endpoint extrae hallazgos, no modifica el corpus ChromaDB directamente; `load-corpus` es CLI, no API | Bajo |

### Superficie de ataque resumida

```
Internet → nginx (TLS) → FastAPI (JWT + BasicAuth) → Core (RAG + LLM)
                                                    → Neo4j (red interna)
                                                    → ChromaDB (embebido)
                                                    → SQLite (volumen)
                                                    → Nuclei/Nmap (CLI, solo con allowlist)
```

El perímetro externo es nginx. La API nunca está expuesta directamente a Internet. Neo4j, ChromaDB y SQLite no tienen puertos publicados.

---

## 5. Resincronización del servidor de producción tras el filter-repo

Tras el force-push del 2026-10-06, el servidor de producción (Hetzner) apunta
al historial antiguo. Para resincronizarlo:

```bash
git fetch origin
git reset --hard origin/main
# NO hacer git push desde el servidor; solo recibir.
```

El servidor de producción **nunca es origen de commits ni de push**. Toda
actualización fluye de GitHub al servidor, nunca al revés.

---

## 6. Pendientes que requieren al autor

- Revisar tres coincidencias con patrón de clave en el commit antiguo
  `be2428c` (`tests/test_api_diff.py`, `tests/test_diff_analyzer.py`,
  `vault/MOC_Roadmap.md`). Probablemente son claves ficticias de los tests del
  Gate CI/CD; si alguna fuera una clave real de un servicio externo, hay que
  revocarla en ese servicio.
- El nombre `rosetta.aegiscores.com` no resuelve en DNS (NXDOMAIN, comprobado
  el 2026-10-04 contra 1.1.1.1), aunque el servidor y nginx funcionan. Hay que
  revisar el registro DNS del dominio.
