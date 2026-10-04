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
`tests/test_auth.py` (commit `e2819f0`, 2026-05-30) y se publicó en GitHub.
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

- Los dos commits locales se sanearon **antes** de publicarlos (`ea3f1f1`,
  `04b9c7e`): sin el literal ni en el contenido ni en el mensaje.
- `_shots.py` lee la URL y las credenciales de variables de entorno
  (`ROSETTA_SHOTS_*`).
- Los tests usan una contraseña de prueba ficticia (`TEST_EXTRA_USER_PASS`).

**Decisión sobre el historial público.** No se reescribe (`git filter-repo` /
force-push). La contraseña antigua sigue en el historial de GitHub, pero ya no
sirve: se ha rotado y se ha comprobado que el servidor la rechaza.

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

Las actualizaciones se hicieron por tandas, priorizando lo expuesto a peticiones
HTTP: python-multipart, starlette/fastapi, pypdf, pyjwt, pillow, pila HTTP/TLS,
pila de embeddings, weasyprint y herramientas de desarrollo. Tras cada tanda se
ejecutaron la suite completa, ruff y `mypy --strict`. En la pila de embeddings
(cambio de versión mayor) se verificó además el RAG con el modelo real.

---

## 4. Pendientes que requieren al autor

- Revisar tres coincidencias con patrón de clave en el commit antiguo
  `4324141` (`tests/test_api_diff.py`, `tests/test_diff_analyzer.py`,
  `vault/MOC_Roadmap.md`). Probablemente son claves ficticias de los tests del
  Gate CI/CD; si alguna fuera una clave real de un servicio externo, hay que
  revocarla en ese servicio.
- El nombre `rosetta.aegiscores.com` no resuelve en DNS (NXDOMAIN, comprobado
  el 2026-10-04 contra 1.1.1.1), aunque el servidor y nginx funcionan. Hay que
  revisar el registro DNS del dominio.
