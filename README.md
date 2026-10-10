# ROSETTA — Orquestador de cumplimiento continuo multi-marco con IA

> **Real-time Orchestrator for Semantic Evidence, Translation & Traceability of Audit-findings**

ROSETTA toma hallazgos técnicos (de un escáner, de un SOC, de un informe de
auditoría en PDF o de un diff de código) y los **traduce a evidencia de
cumplimiento normativo**: qué control incumplen, con qué cita, por qué y cómo se
mitiga. El núcleo es un *Traductor Simbiótico* (LLM + RAG sobre el corpus
normativo + agente validador) servido por una API FastAPI y un dashboard web.

**Qué no es:** ni un escáner de vulnerabilidades, ni un SIEM, ni una herramienta
ofensiva. Orquesta herramientas open source (Nuclei, Nmap, Wazuh) como sensores
y aporta la capa de traducción a normativa. **Acelera al auditor, no lo
sustituye**: la evidencia generada por IA la revisa siempre una persona.

---

## Alcance multi-marco (honesto)

Los siete marcos funcionan, pero **no tienen la misma profundidad**:

| Marco | Corpus | Validación |
|---|---|---|
| **ENS (RD 311/2022)** | Medidas del Anexo II | Profundidad de producción; evaluación contra *ground truth* ENS↔ISO validado por un auditor (`eval/`) |
| **ISO/IEC 27001:2022** | *Outline* del Anexo A (intuitem), no el texto completo de la norma | Ídem (equivalencias ENS↔ISO) |
| NIS2 · DORA · RGPD · NIST CSF 2.0 · PCI-DSS 4.0 | Corpus base (artículos / subcategorías / requisitos) | Operativos, **sin** *ground truth* humano: no se presentan con métricas de acierto |

ISO 27002 no tiene corpus propio: sus controles se cubren a través del Anexo A
de ISO 27001.

En los paneles conviene distinguir el origen de cada dato:
- `/translate`, Copilot, drift y los análisis avanzados: **los genera la IA**.
- `/evidence-panel`: **mapeo determinista** herramienta → control
  (`core/tool_control_map.py`), sin LLM, para que la trazabilidad sea
  reproducible.

---

## Requisitos previos

| Para | Necesitas |
|---|---|
| Ejecutar ROSETTA | **Git** y **Docker** con Compose v2 (Docker Desktop en Windows/macOS). Unos 8 GB de disco para la imagen y los volúmenes, y 4 GB de RAM para los contenedores. |
| Usar IA **sin API key** | **[Ollama](https://ollama.com)** en el equipo con el modelo `qwen2.5:14b`: ~9 GB de disco y **~12 GB de RAM (o VRAM) libres** al traducir con la ventana de contexto por defecto de ROSETTA (`OLLAMA_NUM_CTX=16384`: 11,9 GB medidos). En CPU, mejor 16 GB de RAM o más; con GPU, 12 GB de VRAM o más. |
| Usar Claude (opcional) | Una API key de Anthropic |
| Desarrollar o pasar los tests (opcional) | Python 3.11+ y [uv](https://docs.astral.sh/uv/) |

La imagen se construye para **amd64 y arm64**. Producción corre en ARM64.

---

## Instalación desde cero (Docker)

### 1. Clonar y crear el `.env`

```bash
git clone https://github.com/MichaelJTG/Rosetta.git
cd Rosetta
cp .env.example .env            # PowerShell: Copy-Item .env.example .env
```

### 2. Generar el secreto JWT (obligatorio)

La aplicación **no arranca** con autenticación activa si `ROSETTA_JWT_SECRET`
no tiene al menos 32 caracteres aleatorios. Esto lo escribe en tu `.env`:

```bash
python -c "import pathlib,re,secrets; p=pathlib.Path('.env'); p.write_text(re.sub(r'(?m)^ROSETTA_JWT_SECRET=.*$', 'ROSETTA_JWT_SECRET='+secrets.token_hex(32), p.read_text()))"
```

Si no tienes Python, genera el valor con `openssl rand -hex 32` y pégalo a mano
en `ROSETTA_JWT_SECRET=`.

### 3. Elegir el LLM

- **Sin API key, opción por defecto (Ollama):** descarga el modelo una vez con
  `ollama pull qwen2.5:14b` y deja Ollama abierto. El `.env` ya apunta a
  `http://host.docker.internal:11434`. En **Linux**, arranca Ollama escuchando
  en todas las interfaces (`OLLAMA_HOST=0.0.0.0 ollama serve`) para que el
  contenedor llegue a él.
- **Con Claude:** en `.env`, pon `LLM_PROVIDER=claude` y tu `ANTHROPIC_API_KEY`.

### 4. Construir y arrancar

```bash
docker compose up -d --build     # primera vez: ~4 min (imagen ~3,9 GB)
docker compose ps                # espera a que app y neo4j estén "healthy"
```

### 5. Indexar el corpus normativo (una vez)

```bash
docker compose exec app rosetta load-corpus all corpus
docker compose restart app
```

El primer comando indexa en ChromaDB los siete marcos con corpus propio (229
fragmentos). El reinicio es **necesario**: ChromaDB no admite que dos procesos
compartan la base, y la API solo ve un índice creado por otro proceso cuando
vuelve a arrancar. Sin reiniciar, el Traductor trabaja sin contexto normativo.
Comprobado en la instalación limpia: recuperaba 0 fragmentos y el LLM citaba un
control inexistente.

### 6. Cargar los datos de demostración (opcional)

```bash
docker compose exec app python scripts/seed_demo.py
```

Envía a la API **solo datos de entrada ficticios** del caso TechServ: un
proveedor TIC de tres consejerías, sistema de categoría ALTA con datos de
salud. Son 7 hallazgos que cubren los 7 marcos, más un diff para el Gate
CI/CD, alertas Wazuh, un procedimiento para el análisis de drift y un informe
PDF. Todos los resultados los genera ROSETTA en el momento. Con Ollama en CPU
puede tardar bastantes minutos; `--sin-pdf` omite la ingesta de PDF.

### 7. Entrar

- Dashboard: <http://localhost:8000/dashboard>
- API (OpenAPI): <http://localhost:8000/docs>
- Credenciales de **prueba, ficticias**, definidas en `.env`: usuario
  `auditor-demo`, contraseña `cambia-esta-clave-de-prueba`. **Cámbialas** antes
  de exponer la aplicación fuera de tu equipo.

Para parar: `docker compose down`. Para borrar también los datos:
`docker compose down -v`.

---

## Uso básico

**Desde el dashboard:**
- **Traducir:** introduce un hallazgo y elige los marcos.
- **Hallazgos:** historial y botón «Generar dosier», que descarga el informe en
  Markdown o PDF.
- **Cumplimiento, Grafo, Roadmap, Evidencias, Gap, Plan director y Riesgos:**
  se calculan a partir de los hallazgos.

**Desde la API** (con un token de `POST /auth/login`):

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"auditor-demo","password":"cambia-esta-clave-de-prueba"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -X POST localhost:8000/translate -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{
    "hallazgo": {"origen": "nuclei", "activo_detectado": "citas.techserv.example",
                 "evidencia": "https://citas.techserv.example/.env",
                 "vector_ataque": "Fichero .env con credenciales expuesto",
                 "dificultad_explotacion": "baja"},
    "marcos": ["ens_2022", "iso_27001_2022"]}'
```

**Desde la CLI** (dentro del contenedor):
- `docker compose exec app rosetta --help`
- comandos: `translate`, `load-corpus`, `dossier`, `scan` y `detect-drift`

**Modo Auditoría (Nuclei/Nmap):** úsalo **solo contra sistemas propios o un
laboratorio autorizado**. La API exige una declaración de alcance y rechaza
IP privadas y `localhost`.

---

## Variables de entorno (`.env`)

`.env.example` documenta cada variable, con valores ficticios. Las importantes:

| Variable | Para qué | Valor por defecto en el ejemplo |
|---|---|---|
| `LLM_PROVIDER` | `ollama`, `claude` u `openai` | `ollama` |
| `OLLAMA_URL` / `OLLAMA_MODEL` | Ollama local | `http://host.docker.internal:11434` / `qwen2.5:14b` |
| `ROSETTA_NUCLEI_TAGS` / `ROSETTA_NUCLEI_SEVERITY` | Plantillas de Nuclei (por tag) y severidades del Modo Auditoría | `exposure,misconfig,tech` / todas |
| `OLLAMA_NUM_CTX` | Ventana de contexto pedida a Ollama en cada llamada. Con `qwen2.5:14b`, 16384 ocupa 11,9 GB y 4096 ocupa 9,5 GB, pero con 4096 Ollama recorta el prompt del Copilot y las traducciones contra muchos marcos | `16384` |
| `ANTHROPIC_API_KEY` | Solo con `LLM_PROVIDER=claude` | placeholder no válido |
| `ROSETTA_MARCOS` | Marcos por defecto del Traductor | `iso_27001_2022,ens_2022` |
| `ROSETTA_USER` / `ROSETTA_PASSWORD` | Cuenta del panel (contraseña de 12 caracteres o más) | credenciales de prueba ficticias |
| `ROSETTA_USERS_EXTRA` | Cuentas adicionales `user:clave,user:clave` | vacío |
| `ROSETTA_JWT_SECRET` | Firma de los JWT (32 caracteres o más, **obligatorio**) | vacío, se genera en el paso 2 |
| `ROSETTA_AUTH_DISABLED` | `1` = sin autenticación, **solo en desarrollo local** y sin usuarios definidos | vacío |
| `NEO4J_*` | Grafo de correlación (opcional: si Neo4j cae, la API sigue en modo memoria) | servicio `neo4j` del compose |
| `SHODAN_API_KEY` / `HIBP_API_KEY` | Sensores no integrados en esta versión | vacío |

En Docker, las rutas de las bases de datos, ChromaDB e informes las fija
`docker-compose.yml`, en volúmenes persistentes.

---

## Desarrollo sin Docker

```bash
uv sync --extra dev
uv run pytest                    # 452 tests; no necesitan API key ni LLM
uv run ruff check . && uv run ruff format --check . && uv run mypy --strict src/
uv run rosetta load-corpus all corpus
uv run uvicorn rosetta.api.main:app --reload
```

Fuera de Docker, en `.env`, `OLLAMA_URL` debe ser `http://localhost:11434` y
Neo4j es opcional (`docker compose up -d neo4j`).

---

## Arquitectura

```
Sensores (orquestados, nunca modificados)
  Red Team: Nuclei · Nmap        Blue Team: Wazuh (JSON/CSV)
  Entrada manual · PDF de auditoría · diff de PR (Gate CI/CD)
                 │  HallazgoMaestro (Pydantic)
                 ▼
Núcleo — Traductor Simbiótico
  LLM (Claude · Ollama · OpenAI, intercambiable por LLM_PROVIDER)
  RAG ChromaDB sobre el corpus normativo · agente Validador crítico
  Grafo de correlación Neo4j (degrada a memoria si no está disponible)
                 │  DatosCompliance
                 ▼
Salida
  API REST (31 endpoints + 1 WebSocket) · Dashboard SPA · CLI
  Dosier MD/PDF descargable · Gate CI/CD (GitHub Action)
```

Más detalle en `docs/ARCHITECTURE.md` y en las decisiones de `docs/adr/`.

---

## Estructura del repositorio

```
Rosetta/
├── src/rosetta/
│   ├── api/        # FastAPI: endpoints, autenticación JWT, dashboard SPA
│   ├── agents/     # Orquestador multi-agente, traductores por marco, validador
│   ├── core/       # Traductor, RAG, grafo, drift, copilot, informes, modelos
│   ├── adapters/   # Sensores Red/Blue y cargador de corpus
│   ├── llm/        # Abstracción de proveedores LLM
│   └── cli/        # CLI Typer (rosetta ...)
├── corpus/         # Corpus normativo indexable (YAML)
├── scripts/        # seed_demo.py — datos ficticios de demostración
├── tests/          # pytest (aislados del entorno: sin claves ni LLM)
├── docs/           # Arquitectura, ADR, requisitos, seguridad y matriz de la P3
├── Dockerfile · docker-compose.yml · .env.example
└── pyproject.toml · uv.lock
```

---

## Seguridad

- **Autenticación JWT con refresh** y HTTP Basic de respaldo. Es *fail-closed*:
  no arranca sin secreto y no queda abierta sin una declaración explícita.
- **Rate limiting** en el login y en los endpoints que llaman al LLM.
- **Contenedor sin root.**
- **Dependencias auditadas en CI** con pip-audit sobre `uv.lock`.
- **Escaneo de secretos** con gitleaks en CI y en pre-commit.

Modelo de amenazas, incidentes y riesgos aceptados en `docs/P3_SEGURIDAD.md`.

## Limitaciones

- La evidencia generada por IA **requiere revisión humana**. ROSETTA no
  sustituye al auditor.
- Solo ENS e ISO 27001 se evalúan contra un *ground truth* humano; la
  evaluación de los otros cinco marcos queda pendiente.
- El corpus ISO es el *outline* de intuitem, no la norma completa (la norma es
  de pago).
- Shodan y HIBP aparecen en el modelo de datos, pero no tienen adaptador
  integrado. Amass tiene un adaptador experimental que no está conectado al
  Modo Auditoría.

## Licencia y autoría

Proprietary provisional, ver [LICENSE](./LICENSE). Proyecto individual de **Mj**
(michael.jt.pro@gmail.com) para el Máster en Ciberseguridad & IA de Evolve
Academy.
